"""Bay water level at each creek outlet from NOAA's San Francisco Bay model (SFBOFS), for staff (beta, staff page only).

What it does, each time NOAA publishes a new model run (4 a day: 03, 09, 15, 21 UTC):
  1. The outlets: lookups/creek_outlets.csv once staff have reviewed it, else the draft lookups/proposed/creek_outlets.csv
     (rows with include = no left out; outlets at the same point, like San Bruno and El Zanjon, read once).
  2. The model: SFBOFS (FVCOM, an unstructured mesh of about 100,000 points over the Bay and Delta), from NOAA's public
     archive on Amazon (noaa-nos-ofs-pds). One file per hour: the last 6 hours (nowcast n000-n006) and the next 48
     (forecast f001-f048). Only the water level ("zeta") at the chosen mesh points is read, by byte range; nothing
     else in the files is downloaded.
  3. The mesh point for each outlet: the nearest point at least MIN_DEPTH_M deep (below the model's datum), so the
     point is in water that stays wet at low tide rather than in marsh that dries; the nearest point of any depth is
     reported too. Staff check these on the staff page's map.
  4. The datum. The model's water level is relative to its own datum (about mean sea level), not NAVD88. At three
     NOAA tide gauges (San Francisco, Alameda, Redwood City) the offset is worked out by comparing the model at the
     gauge's nearest mesh point with NOAA's own projection at the gauge in ft NAVD88 (product ofs_water_level, which
     NOAA converts with its datums): the median difference. If that isn't available, NOAA's published MSL above
     NAVD88 at the gauge. Each outlet gets the offset of the gauges weighted by distance (1 / distance squared).
     The comparison also checks this method: the spread left after the offset (check_rms_ft) should be small.
  5. The tide table and NOAA's projection at those three gauges, for comparison on the staff page.

A projection, not a measurement: there are no gauges at the outlets. Nothing here sets a status or shows on the public
pages. Writes outlet_tides.json (latest run) and adds to outlet_tides_log.csv (each run's peak at each outlet, and the
datum check at each gauge; the last LOG_DAYS days), both on the data branch.

Usage: python outlet_tides.py OUTPUT.json LOG.csv [--min-age MINUTES]
  --min-age: look for a new model run only if the last look was at least this many minutes ago (the data job runs
  every 5 minutes; NOAA publishes a run every 6 hours)
"""

import bisect
import csv
import datetime as dt
import json
import math
import os
import re
import statistics
import struct
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUTLETS = os.path.join(ROOT, "lookups", "creek_outlets.csv")
OUTLETS_DRAFT = os.path.join(ROOT, "lookups", "proposed", "creek_outlets.csv")

BUCKET = "https://noaa-nos-ofs-pds.s3.amazonaws.com"
MODEL = "sfbofs"
NOAA = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
MDAPI = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{}/datums.json?units=english"
UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
# NOAA tide gauges used for the datum and for comparison (id, name, lat, lon)
REFS = [("9414290", "San Francisco", 37.8063, -122.4659),
        ("9414750", "Alameda", 37.7720, -122.3003),
        ("9414523", "Redwood City", 37.5068, -122.2119)]
MIN_DEPTH_M = 0.5        # mesh point at least this deep below the model datum (stays wet at low tide)
MAX_NODE_M = 3000        # farther than this from the outlet: flagged
MIN_MATCH = 12           # hours matched with NOAA's projection to use the model-based offset
FT = 3.28084
LOG_DAYS = 60
NEED_FORECAST_HOURS = 48


# ---------------------------------------------------------------------------------------------------- web
def http(url, rng=None, timeout=60, method="GET"):
    h = {"User-Agent": UA}
    if rng:
        h["Range"] = "bytes=%d-%d" % rng
    req = urllib.request.Request(url, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read() if method == "GET" else r.headers


def get_json(url, timeout=30):
    return json.loads(http(url, timeout=timeout))


class HttpFile:
    """A read-only file over HTTP byte ranges, with a block cache (for the netCDF header parser and for h5py)."""

    def __init__(self, url, block=1 << 20, fetch=None):
        self.url, self.block, self.pos, self.cache = url, block, 0, {}
        self.fetch = fetch or (lambda a, b: http(url, (a, b)))
        self.requests = 0
        self.size = None

    def _size(self):
        if self.size is None:
            self.size = int(http(self.url, method="HEAD")["Content-Length"])
        return self.size

    def _blk(self, i):
        if i not in self.cache:
            self.requests += 1
            self.cache[i] = self.fetch(i * self.block, (i + 1) * self.block - 1)
            if len(self.cache) > 64:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[i]

    def pread(self, off, n):
        """n bytes at off; a big read goes in one request."""
        if n > 4 * self.block:
            self.requests += 1
            return self.fetch(off, off + n - 1)
        out, end = [], off + n
        while off < end:
            i = off // self.block
            b = self._blk(i)
            s = off - i * self.block
            take = b[s:s + end - off]
            if not take:
                break
            out.append(take)
            off += len(take)
        return b"".join(out)

    # file-like interface (h5py)
    def read(self, n=-1):
        if n is None or n < 0:
            n = self._size() - self.pos
        d = self.pread(self.pos, n)
        self.pos += len(d)
        return d

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self._size() + off
        return self.pos

    def tell(self):
        return self.pos

    def seekable(self):
        return True

    def readable(self):
        return True


# ---------------------------------------------------------------------------------------------------- netCDF
TYPES = {1: ("b", 1), 2: ("c", 1), 3: ("h", 2), 4: ("i", 4), 5: ("f", 4), 6: ("d", 8),
         7: ("B", 1), 8: ("H", 2), 9: ("I", 4), 10: ("q", 8), 11: ("Q", 8)}


class Classic:
    """Just enough of a netCDF classic (CDF-1, CDF-2, CDF-5) reader: the header, and values at chosen indices."""

    def __init__(self, f):
        self.f = f
        head = f.pread(0, 8)
        if head[:3] != b"CDF" or head[3] not in (1, 2, 5):
            raise ValueError("not a netCDF classic file")
        self.ver = head[3]
        self.big = self.ver == 5
        self.pos = 4
        self.numrecs = self._n()
        self.dims = []
        self._list(0x0A, self._dim)
        self.gatts = {}
        self._list(0x0C, lambda: self._att(self.gatts))
        self.vars = {}
        self._list(0x0B, self._var)
        rec = [v for v in self.vars.values() if v["record"]]
        self.recsize = sum(v["vsize"] for v in rec)
        if len(rec) == 1:   # one record variable: records aren't padded
            v = rec[0]
            self.recsize = v["count"] * TYPES[v["type"]][1]

    def _read(self, n):
        # the header can be large (many attributes): read ahead in 256 KiB pieces
        d = self.f.pread(self.pos, n)
        self.pos += n
        return d

    def _n(self):
        return struct.unpack(">q" if self.big else ">i", self._read(8 if self.big else 4))[0]

    def _i4(self):
        return struct.unpack(">i", self._read(4))[0]

    def _name(self):
        n = self._n()
        s = self._read(n).decode("utf-8", "replace")
        self._read((4 - n % 4) % 4)
        return s

    def _list(self, tag, item):
        t = self._i4()
        n = self._n()
        if t == 0 and n == 0:
            return
        if t != tag:
            raise ValueError("netCDF header: expected tag %d, found %d" % (tag, t))
        for _ in range(n):
            item()

    def _dim(self):
        self.dims.append((self._name(), self._n()))

    def _att(self, into):
        name = self._name()
        typ = self._i4()
        n = self._n()
        code, size = TYPES.get(typ, ("b", 1))
        raw = self._read(n * size)
        self._read((4 - (n * size) % 4) % 4)
        into[name] = raw.decode("utf-8", "replace").rstrip("\x00") if typ == 2 else struct.unpack(">%d%s" % (n, code), raw)

    def _var(self):
        name = self._name()
        nd = self._n()
        ids = [self._n() for _ in range(nd)]
        atts = {}
        self._list(0x0C, lambda: self._att(atts))
        typ = self._i4()
        vsize = self._n() if self.big else struct.unpack(">I", self._read(4))[0]
        begin = struct.unpack(">q" if self.ver in (2, 5) else ">i", self._read(8 if self.ver in (2, 5) else 4))[0]
        shape = [self.dims[i][1] for i in ids]
        record = bool(shape) and shape[0] == 0
        count = 1
        for s in (shape[1:] if record else shape):
            count *= s
        self.vars[name] = {"dims": [self.dims[i][0] for i in ids], "shape": shape, "type": typ, "vsize": vsize,
                           "begin": begin, "record": record, "count": count, "atts": atts}

    def values(self, name, rec=0):
        """All values of a variable (one record of a record variable), as a list."""
        v = self.vars[name]
        code, size = TYPES[v["type"]]
        off = v["begin"] + (rec * self.recsize if v["record"] else 0)
        raw = self.f.pread(off, v["count"] * size)
        return list(struct.unpack(">%d%s" % (v["count"], code), raw))

    def at(self, name, idx, rec=0):
        """Values of a 1-D (per record) variable at the given indices: one read covering them."""
        v = self.vars[name]
        code, size = TYPES[v["type"]]
        base = v["begin"] + (rec * self.recsize if v["record"] else 0)
        lo, hi = min(idx), max(idx)
        raw = self.f.pread(base + lo * size, (hi - lo + 1) * size)
        return [struct.unpack(">" + code, raw[(i - lo) * size:(i - lo + 1) * size])[0] for i in idx]


class H5:
    """The same three calls for a netCDF-4 (HDF5) file, through h5py (installed when first needed)."""

    def __init__(self, f):
        try:
            import h5py
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "h5py"], check=True)
            import h5py
        self.h = h5py.File(f, "r")
        self.vars = {k: {"shape": list(self.h[k].shape)} for k in self.h.keys() if hasattr(self.h[k], "shape")}

    def values(self, name, rec=0):
        d = self.h[name]
        return [float(x) for x in (d[rec] if len(d.shape) == 2 else d[()]).ravel()]

    def at(self, name, idx, rec=0):
        d = self.h[name]
        order = sorted(set(idx))
        got = d[rec, order] if len(d.shape) == 2 else d[order]
        m = dict(zip(order, [float(x) for x in got]))
        return [m[i] for i in idx]


def open_nc(url, fetch=None):
    f = HttpFile(url, fetch=fetch)
    head = f.pread(0, 8)
    if head[:3] == b"CDF":
        return Classic(f), "netCDF classic"
    if head[:8] == b"\x89HDF\r\n\x1a\n":
        return H5(f), "netCDF-4 (HDF5)"
    raise ValueError("unknown file format: %r" % head[:8])


def pick(nc, *names):
    for n in names:
        if n in nc.vars:
            return n
    raise KeyError("none of %s in the file (has: %s)" % (names, ", ".join(sorted(nc.vars))[:300]))


# ---------------------------------------------------------------------------------------------------- the model runs
FILE_RE = [   # (regex, cycle hour group, date group, kind group, hour group): naming since 2024, and the older naming
    (re.compile(r"/sfbofs\.t(\d\d)z\.(\d{8})\.fields\.([nf])(\d{3})\.nc$"), 1, 2, 3, 4),
    (re.compile(r"/nos\.sfbofs\.fields\.([nf])(\d{3})\.(\d{8})\.t(\d\d)z\.nc$"), 4, 3, 1, 2),
]


def parse_key(key):
    """'sfbofs/netcdf/2026/10/29/sfbofs.t03z.20261029.fields.f012.nc' -> (cycle datetime UTC, valid datetime UTC)."""
    for rx, gc, gd, gk, gh in FILE_RE:
        m = rx.search("/" + key)
        if m:
            cyc = dt.datetime.strptime(m.group(gd) + m.group(gc), "%Y%m%d%H").replace(tzinfo=dt.timezone.utc)
            h = int(m.group(gh))
            valid = cyc + dt.timedelta(hours=h) if m.group(gk) == "f" else cyc - dt.timedelta(hours=6 - h)
            return cyc, valid, m.group(gk) + "%03d" % h
    return None


def list_keys(prefix, get=None):
    get = get or (lambda u: http(u, timeout=30))
    keys, token = [], None
    ns = "{http://s3.amazonaws.com/doc/2006-03-01/}"
    while True:
        q = {"list-type": "2", "prefix": prefix}
        if token:
            q["continuation-token"] = token
        root = ET.fromstring(get(BUCKET + "/?" + urllib.parse.urlencode(q)))
        keys += [e.text for e in root.iter(ns + "Key")]
        t = root.find(ns + "NextContinuationToken")
        if t is None or not t.text:
            return keys
        token = t.text


def latest_run(now, get=None):
    """The newest complete model run: {cycle, files: [(valid, label, url)]}, or None."""
    runs = {}
    for back in (0, 1):
        day = now - dt.timedelta(days=back)
        # NOAA's layout since 2024 (a folder per day), then the older one (a folder per month)
        for prefix in (day.strftime(MODEL + "/netcdf/%Y/%m/%d/"),
                       day.strftime(MODEL + "/netcdf/%Y%m/nos." + MODEL + ".fields.")):
            try:
                ks = list_keys(prefix, get)
            except Exception as e:   # noqa: BLE001
                print("  listing %s: %s" % (prefix, e), file=sys.stderr)
                continue
            for k in ks:
                p = parse_key(k)
                if p:
                    runs.setdefault(p[0], {})[p[2]] = (p[1], p[2], BUCKET + "/" + k)
            if ks:
                break
    for cyc in sorted(runs, reverse=True):
        fs = runs[cyc]
        if sum(1 for k in fs if k[0] == "f" and int(k[1:]) >= 1) >= NEED_FORECAST_HOURS:
            return {"cycle": cyc, "files": sorted(fs.values())}
    return None


# ---------------------------------------------------------------------------------------------------- geometry
def dist_m(lat1, lon1, lat2, lon2):
    x = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6371000 * math.hypot(x, math.radians(lat2 - lat1))


def nearest(lat, lon, lats, lons, depth, min_depth=MIN_DEPTH_M):
    """(index of the nearest node at least min_depth deep, its distance; index of the nearest node of any depth,
    its distance). A box search first (about 5 km), then everything if nothing is in the box."""
    best = [None, 1e18, None, 1e18]
    for box in (0.05, 9):
        for i in range(len(lats)):
            if abs(lats[i] - lat) > box or abs(lons[i] - lon) > box:
                continue
            d = dist_m(lat, lon, lats[i], lons[i])
            if d < best[3]:
                best[2], best[3] = i, d
            if depth[i] >= min_depth and d < best[1]:
                best[0], best[1] = i, d
        if best[0] is not None:
            break
    return best


def idw(lat, lon, refs):
    """Offset at a point from the gauges' offsets, weighted by 1 / distance squared."""
    w = s = 0.0
    for r in refs:
        if r.get("offset_ft") is None:
            continue
        d = max(dist_m(lat, lon, r["lat"], r["lon"]), 100.0)
        w += 1 / d ** 2
        s += r["offset_ft"] / d ** 2
    return s / w if w else None


# ---------------------------------------------------------------------------------------------------- NOAA gauges
def iso(t):
    return t.strftime("%Y-%m-%dT%H:%MZ")


def noaa_series(product, station, begin, end, fetch=get_json, **extra):
    q = dict(product=product, station=station, begin_date=begin.strftime("%Y%m%d %H:%M"), end_date=end.strftime("%Y%m%d %H:%M"),
             datum="NAVD", time_zone="gmt", units="english", format="json", application="OneShorelineFEWS", **extra)
    j = fetch(NOAA + "?" + urllib.parse.urlencode(q))
    if j.get("error"):
        raise ValueError(str(j["error"].get("message", j["error"]))[:150])
    out = {}
    for p in j.get("data") or j.get("predictions") or []:
        try:
            v = float(p["v"])
        except (KeyError, TypeError, ValueError):
            continue
        t = dt.datetime.strptime(p["t"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
        out[t] = v
    return out


def msl_navd(station, fetch=get_json):
    """NOAA's mean sea level at the gauge, in ft NAVD88 (from its published datums), or None."""
    j = fetch(MDAPI.format(station))
    d = {x.get("name"): x.get("value") for x in j.get("datums") or []}
    if d.get("MSL") is None or d.get("NAVD88") is None:
        return None
    return round(float(d["MSL"]) - float(d["NAVD88"]), 3)


def offset_from(model, noaa):
    """(median of NOAA's projection minus the model, spread left after it (RMS), hours matched), on the hours both have."""
    diffs = [noaa[t] - v for t, v in model.items() if t in noaa]
    if not diffs:
        return None, None, 0
    off = statistics.median(diffs)
    rms = math.sqrt(sum((d - off) ** 2 for d in diffs) / len(diffs))
    return round(off, 3), round(rms, 3), len(diffs)


# ---------------------------------------------------------------------------------------------------- outlets
def load_outlets(path=None):
    path = path or (OUTLETS if os.path.exists(OUTLETS) else OUTLETS_DRAFT)
    pts = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if (r.get("include") or "").strip().lower() == "no":
                continue
            try:
                lat, lon = float(r["lat"]), float(r["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            k = (round(lat, 5), round(lon, 5))
            p = pts.setdefault(k, {"ids": [], "creeks": [], "fews": [], "city": r.get("city", ""), "lat": lat, "lon": lon})
            p["ids"].append(r.get("id", ""))
            for key, col in (("creeks", "creek"), ("fews", "fews_creek")):
                v = (r.get(col) or "").strip()
                if v and v not in p[key]:
                    p[key].append(v)
    return list(pts.values()), os.path.relpath(path, ROOT)


# ---------------------------------------------------------------------------------------------------- the run
def run(now, previous, outlets, source, get_list=None, fetch_nc=None, fetch=get_json, log=print):
    found = latest_run(now, get_list)
    if not found:
        raise RuntimeError("no complete SFBOFS run found on the NOAA archive for today or yesterday")
    cyc = found["cycle"]
    sig = "|".join("%.5f,%.5f" % (o["lat"], o["lon"]) for o in outlets)
    if previous.get("cycle_utc") == iso(cyc) and previous.get("outlets_sig") == sig:
        log("  model run %s already done" % iso(cyc))
        return None
    files = found["files"]
    log("  model run %s: %d files (%s to %s)" % (iso(cyc), len(files), files[0][1], files[-1][1]))

    # the mesh, from the first file: nodes for the outlets and the gauges
    nc, fmt = open_nc(files[0][2], fetch_nc)
    vlon, vlat, vh = pick(nc, "lon", "longitude"), pick(nc, "lat", "latitude"), pick(nc, "h", "depth")
    vz = pick(nc, "zeta", "zeta_navd", "ssh")
    lons = [x - 360 if x > 180 else x for x in nc.values(vlon)]
    lats, depth = nc.values(vlat), nc.values(vh)
    log("  %s, %d mesh points" % (fmt, len(lats)))
    refs = []
    for sid, name, la, lo in REFS:
        i, d, j, dj = nearest(la, lo, lats, lons, depth)
        refs.append({"id": sid, "name": name, "lat": la, "lon": lo,
                     "node": {"i": i, "lat": round(lats[i], 5), "lon": round(lons[i], 5), "dist_m": round(d), "depth_m": round(depth[i], 2)}})
    outs = []
    for o in outlets:
        i, d, j, dj = nearest(o["lat"], o["lon"], lats, lons, depth)
        outs.append(dict(o, node={"i": i, "lat": round(lats[i], 5), "lon": round(lons[i], 5), "dist_m": round(d),
                                  "depth_m": round(depth[i], 2), "nearest_any_m": round(dj), "far": d > MAX_NODE_M}))
    idx = sorted({x["node"]["i"] for x in outs + refs})

    # the water level at those nodes, hour by hour
    ser = {i: {} for i in idx}
    for valid, label, url in files:
        try:
            f = nc if url == files[0][2] else open_nc(url, fetch_nc)[0]
            vals = f.at(vz, idx)
        except Exception as e:   # noqa: BLE001
            log("  %s: %s" % (label, e))
            continue
        for i, v in zip(idx, vals):
            if v is not None and math.isfinite(v) and abs(v) < 50:
                ser[i][valid] = v * FT
    hours = sorted({t for s in ser.values() for t in s})
    if len(hours) < NEED_FORECAST_HOURS // 2:
        raise RuntimeError("only %d hours read from the model run" % len(hours))

    # the datum at the gauges; the tide table and NOAA's projection there
    t0, t1 = hours[0], hours[-1]
    for r in refs:
        r["series"] = {"model": [], "noaa": [], "table": []}
        noaa = table = {}
        try:
            noaa = noaa_series("ofs_water_level", r["id"], t0, t1, fetch)
        except Exception as e:   # noqa: BLE001
            log("  %s ofs_water_level: %s" % (r["id"], e))
        try:
            table = noaa_series("predictions", r["id"], t0, t1, fetch, interval="h")
        except Exception as e:   # noqa: BLE001
            log("  %s predictions: %s" % (r["id"], e))
        try:
            r["offset_datum_ft"] = msl_navd(r["id"], fetch)
        except Exception as e:   # noqa: BLE001
            r["offset_datum_ft"] = None
            log("  %s datums: %s" % (r["id"], e))
        m = ser[r["node"]["i"]]
        off, rms, n = offset_from(m, noaa)
        r.update(offset_model_ft=off, check_rms_ft=rms, matched_hours=n)
        if off is not None and n >= MIN_MATCH:
            r["offset_ft"], r["offset_method"] = off, "model vs NOAA projection at the gauge"
        elif r["offset_datum_ft"] is not None:
            r["offset_ft"], r["offset_method"] = r["offset_datum_ft"], "NOAA MSL above NAVD88 at the gauge"
        else:
            r["offset_ft"], r["offset_method"] = None, "none"
        if r["offset_ft"] is not None:
            r["series"]["model"] = [[iso(t), round(v + r["offset_ft"], 2)] for t, v in sorted(m.items())]
        r["series"]["noaa"] = [[iso(t), round(v, 2)] for t, v in sorted(noaa.items()) if t.minute == 0]
        r["series"]["table"] = [[iso(t), round(v, 2)] for t, v in sorted(table.items())]
        log("  %s %s: node %d m away, offset %s ft (%s), check %s ft over %d h" % (
            r["id"], r["name"], r["node"]["dist_m"], r["offset_ft"], r["offset_method"], rms, n))

    for o in outs:
        o["offset_ft"] = None if idw(o["lat"], o["lon"], refs) is None else round(idw(o["lat"], o["lon"], refs), 3)
        o["nearest_gauge"] = min(refs, key=lambda r: dist_m(o["lat"], o["lon"], r["lat"], r["lon"]))["id"]
        s = ser[o["node"]["i"]]
        o["series"] = [] if o["offset_ft"] is None else [[iso(t), round(v + o["offset_ft"], 2)] for t, v in sorted(s.items())]
        fut = [p for p in o["series"] if p[0] >= iso(now)]
        o["peak"] = None if not fut else dict(zip(("t", "ft"), max(fut, key=lambda p: p[1])))
    return {"generated_utc": iso(now), "model": "SFBOFS", "cycle_utc": iso(cyc), "format": fmt, "mesh_points": len(lats),
            "outlets_source": source, "outlets_sig": sig, "min_depth_m": MIN_DEPTH_M, "hours": len(hours),
            "refs": refs, "outlets": outs}


def log_rows(out):
    rows = []
    for o in out["outlets"]:
        if o.get("peak"):
            rows.append([out["cycle_utc"], "outlet", " ".join(o["ids"]), "; ".join(o["creeks"]), o["peak"]["ft"], o["peak"]["t"],
                         o["offset_ft"], o["node"]["dist_m"], ""])
    for r in out["refs"]:
        rows.append([out["cycle_utc"], "gauge", r["id"], r["name"], "", "", r.get("offset_ft"), r["node"]["dist_m"], r.get("check_rms_ft")])
    return rows


LOG_HEAD = ["cycle_utc", "kind", "id", "name", "peak_ft_navd88", "peak_utc", "offset_ft", "node_dist_m", "check_rms_ft"]


def write_log(path, rows, now):
    old = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            old = [r for r in csv.reader(f)][1:]
    cut = iso(now - dt.timedelta(days=LOG_DAYS))
    keep = [r for r in old if r and r[0] >= cut and r[0] not in {x[0] for x in rows}] + rows
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(LOG_HEAD)
        w.writerows(keep)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_path, log_path = args[0], args[1]
    min_age = 0
    if "--min-age" in sys.argv:
        min_age = float(sys.argv[sys.argv.index("--min-age") + 1])
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    previous = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, encoding="utf-8") as f:
                previous = json.load(f)
        except ValueError:
            previous = {}
    last = previous.get("checked_utc")
    if last and min_age and now - dt.datetime.strptime(last, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=min_age):
        print("  checked for a new model run at %s; not again yet" % last)
        return
    outlets, source = load_outlets()
    print("  %d outlets from %s" % (len(outlets), source))
    try:
        out = run(now, previous, outlets, source)
    except Exception as e:   # noqa: BLE001
        print("  problem: %s (the last run's values are kept)" % e)
        if previous:
            previous["checked_utc"] = iso(now)
            previous["problem"] = str(e)[:200]
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(previous, f, separators=(",", ":"))
        raise
    if out is None:
        previous["checked_utc"] = iso(now)
        previous.pop("problem", None)
        out = previous
    else:
        out["checked_utc"] = iso(now)
        write_log(log_path, log_rows(out), now)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))


if __name__ == "__main__":
    main()
