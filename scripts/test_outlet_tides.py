"""Checks for scripts/outlet_tides.py with a made-up model run (no network): a small netCDF classic mesh, a fake
NOAA archive listing and fake NOAA gauge replies. Run: python scripts/test_outlet_tides.py"""

import datetime as dt
import json
import math
import os
import struct
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outlet_tides as O

fails = 0
checks = 0


def check(name, ok):
    global fails, checks
    checks += 1
    if not ok:
        print("FAIL " + name)
        fails += 1


def name(s):
    b = s.encode()
    return struct.pack(">i", len(b)) + b + b"\0" * ((4 - len(b) % 4) % 4)


def classic(nodes, recs, ver=1, extra_record=True):
    """A netCDF classic file: lon/lat/h(node), zeta(time, node) [and time(time)]. nodes: [(lat, lon, h)], recs: [[zeta]]"""
    n = len(nodes)
    off = ">i" if ver == 1 else ">q"
    variables = [("lon", [1], [x[1] + 360 for x in nodes]), ("lat", [1], [x[0] for x in nodes]), ("h", [1], [x[2] for x in nodes]),
                 ("zeta", [0, 1], None)] + ([("time", [0], None)] if extra_record else [])

    def header(begins):
        h = b"CDF" + bytes([ver]) + struct.pack(">i", len(recs))
        h += struct.pack(">ii", 0x0A, 2) + name("time") + struct.pack(">i", 0) + name("node") + struct.pack(">i", n)
        h += struct.pack(">ii", 0, 0)
        h += struct.pack(">ii", 0x0B, len(variables))
        for (nm, dims, _), b in zip(variables, begins):
            vsize = 4 * (n if nm != "time" else 1)
            h += name(nm) + struct.pack(">i", len(dims)) + b"".join(struct.pack(">i", d) for d in dims)
            h += struct.pack(">ii", 0, 0) + struct.pack(">i", 5) + struct.pack(">i", vsize) + struct.pack(off, b)
        return h
    hl = len(header([0] * len(variables)))
    begins, pos = [], hl
    for nm, dims, _ in variables[:3]:
        begins.append(pos)
        pos += 4 * n
    rec0 = pos
    begins.append(rec0)
    if extra_record:
        begins.append(rec0 + 4 * n)
    recsize = 4 * n + (4 if extra_record else 0)
    out = header(begins)
    for nm, dims, vals in variables[:3]:
        out += struct.pack(">%df" % n, *vals)
    for r, z in enumerate(recs):
        out += struct.pack(">%df" % n, *z) + (struct.pack(">f", r) if extra_record else b"")
    assert len(out) == rec0 + recsize * len(recs)
    return out


# ---- the netCDF reader, both versions, with and without a second record variable
nodes = [(37.50, -122.20, 3.0), (37.60, -122.30, 0.2), (37.61, -122.31, 2.0), (37.77, -122.30, 5.0)]
for ver in (1, 2):
    for extra in (True, False):
        raw = classic(nodes, [[0.1, 0.2, 0.3, 0.4], [1.1, 1.2, 1.3, 1.4]], ver, extra)
        f = O.HttpFile("x", block=16, fetch=lambda a, b, raw=raw: raw[a:b + 1])
        nc = O.Classic(f)
        check("CDF-%d reads lon (0-360 kept as stored)" % ver, abs(nc.values("lon")[1] - 237.7) < 1e-4)
        check("CDF-%d zeta record 1 at nodes 3, 0" % ver, [round(x, 3) for x in nc.at("zeta", [3, 0], rec=1)] == [1.4, 1.1])
        check("CDF-%d zeta record 0 at node 2 (extra record var %s)" % (ver, extra), round(nc.at("zeta", [2])[0], 3) == 0.3)
try:
    O.Classic(O.HttpFile("x", fetch=lambda a, b: b"\x89HDF\r\n\x1a\n"[a:b + 1]))
    check("HDF5 isn't read as classic", False)
except ValueError:
    check("HDF5 isn't read as classic", True)

# ---- nearest node: deep enough beats nearer but shallow
lats, lons, depth = [x[0] for x in nodes], [x[1] for x in nodes], [x[2] for x in nodes]
i, d, j, dj = O.nearest(37.6001, -122.3001, lats, lons, depth)
check("nearest wet node skips the shallow one", i == 2 and j == 1 and d > dj)
check("distance is in metres", 1300 < d < 1500)

# ---- offsets
o, rms, n = O.offset_from({1: 1.0, 2: 2.0, 3: 3.0}, {1: 4.0, 2: 5.0, 3: 6.1, 9: 0})
check("median offset and spread", o == 3.0 and n == 3 and 0 < rms < 0.1)
refs = [{"lat": 37.5, "lon": -122.2, "offset_ft": 3.0}, {"lat": 37.8, "lon": -122.3, "offset_ft": 4.0}, {"lat": 0, "lon": 0, "offset_ft": None}]
check("offset near a gauge is close to that gauge's", abs(O.idw(37.51, -122.21, refs) - 3.0) < 0.05)
check("offset halfway is between", 3.2 < O.idw(37.65, -122.25, refs) < 3.8)

# ---- file names
c, v, lab = O.parse_key("sfbofs/netcdf/2026/10/29/sfbofs.t03z.20261029.fields.f012.nc")
check("new naming: forecast hour 12", c.hour == 3 and v == c + dt.timedelta(hours=12) and lab == "f012")
c, v, lab = O.parse_key("sfbofs/netcdf/202610/nos.sfbofs.fields.n002.20261029.t09z.nc")
check("old naming: nowcast 2 = cycle - 4 h", c.hour == 9 and v == c - dt.timedelta(hours=4) and lab == "n002")
check("station files ignored", O.parse_key("sfbofs/netcdf/2026/10/29/sfbofs.t03z.20261029.stations.forecast.nc") is None)

# ---- a whole run, made up: the Bay rises 1 m over the run; the model datum is 3.2 ft below NAVD88 everywhere
NOW = dt.datetime(2026, 10, 29, 6, 0, tzinfo=dt.timezone.utc)
CYC = dt.datetime(2026, 10, 29, 3, 0, tzinfo=dt.timezone.utc)
mesh = [(37.6481, -122.3990, 2.0),   # Colma outlet, wet
        (37.64829, -122.40150, 3.0), # right at the outlet, deep, but a closed pond: the level never moves
        (37.6483, -122.4012, 0.1),   # Colma outlet, shallow (marsh)
        (37.8063, -122.4655, 10.0),  # SF gauge
        (37.7722, -122.3005, 6.0),   # Alameda gauge
        (37.5070, -122.2120, 4.0)]   # Redwood City gauge
labels = ["n%03d" % k for k in range(7)] + ["f%03d" % k for k in range(1, 49)]
files, keys = {}, []
for lab in labels:
    h = int(lab[1:]) - 6 if lab[0] == "n" else int(lab[1:])
    z = 0.3 + h / 48.0
    key = "sfbofs/netcdf/2026/10/29/sfbofs.t03z.20261029.fields.%s.nc" % lab
    keys.append(key)
    files[O.BUCKET + "/" + key] = classic(mesh, [[z, 0.0, 9e36, z, z, z + 0.1]])
listing = ('<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">' +
           "".join("<Contents><Key>%s</Key></Contents>" % k for k in keys) + "</ListBucketResult>").encode()
urls = []


def get_list(u):
    urls.append(u)
    return listing if "2026%2F10%2F29" in u else b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"></ListBucketResult>'


current = {}


def fetch_nc_for(url):
    return lambda a, b: files[url][a:b + 1]


orig_open = O.open_nc
O.open_nc = lambda url, fetch=None: orig_open(url, fetch_nc_for(url))


def fetch(u):
    if "datums.json" in u:
        return {"datums": [{"name": "MSL", "value": 6.0}, {"name": "MHHW", "value": 9.0}, {"name": "NAVD88", "value": 2.85}]}
    q = dict(x.split("=", 1) for x in u.split("?", 1)[1].split("&"))
    st = q["station"]
    if st == "9414290" and q["product"] == "ofs_water_level":
        return {"error": {"message": "No data was found"}}
    out = []
    for k in range(-6, 49):
        t = CYC + dt.timedelta(hours=k)
        z = (0.3 + k / 48.0 + (0.1 if st == "9414523" else 0)) * O.FT + 3.2
        out.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": "%.3f" % (z if q["product"] == "ofs_water_level" else z - 0.5)})
    return {"data": out} if q["product"] == "ofs_water_level" else {"predictions": out}


outlets = [{"ids": ["CO-002"], "creeks": ["Colma Creek"], "fews": ["colma"], "city": "South San Francisco", "lat": 37.64829, "lon": -122.40153}]
lows = [{"id": "SH-001", "name": "Test shoreline", "city": "South San Francisco", "lat": 37.6481, "lon": -122.3992, "level_in": 12.0, "developed": True, "length_m": "500"}]
out = O.run(NOW, {}, outlets, "test", get_list=get_list, fetch=fetch, log=lambda *a: None, lowpoints=lows, lp_source="lp")
check("the run was found", out and out["cycle_utc"] == "2026-10-29T03:00Z" and out["hours"] == 55)
r = {x["id"]: x for x in out["refs"]}
check("Alameda offset from NOAA's projection = 3.2 ft", r["9414750"]["offset_ft"] == 3.2 and r["9414750"]["check_rms_ft"] < 0.01)
check("San Francisco falls back to NOAA's datums (MSL 3.15 ft NAVD88)", r["9414290"]["offset_ft"] == 3.15 and "MSL" in r["9414290"]["offset_method"])
o = out["outlets"][0]
check("Colma outlet uses the wet node that moves with the tide, not the pond or the marsh", o["node"]["i"] == 0 and o["node"]["skipped_still"] == 1)
check("...and still reports the nearest point of any depth", o["node"]["nearest_any_m"] < o["node"]["dist_m"])
check("Colma offset between SF's 3.15 and Alameda's 3.2", 3.15 < o["offset_ft"] < 3.2)
check("Colma series: 55 hours, last = 1.3 m + offset", len(o["series"]) == 55 and abs(o["series"][-1][1] - (1.3 * O.FT + o["offset_ft"])) < 0.02)
check("peak is in the future and the highest", o["peak"]["t"] == "2026-10-31T03:00Z")
check("gauge series for the page", len(r["9414523"]["series"]["table"]) == 55 and len(r["9414523"]["series"]["model"]) == 55)
check("bad values (9e36) left out", all(abs(p[1]) < 100 for p in o["series"]))
again = O.run(NOW, out, outlets, "test", get_list=get_list, fetch=fetch, log=lambda *a: None, lowpoints=lows, lp_source="lp")
check("same run again: nothing to do", again is None)
again = O.run(NOW, out, outlets, "test", get_list=get_list, fetch=fetch, log=lambda *a: None, lowpoints=[dict(lows[0], level_in=24.0)], lp_source="lp")
check("a low point's level changed: run again", again is not None)
lp = out["lowpoints"][0]
check("low point: MHHW 6.15 ft NAVD88 (9.0 - 2.85 at every gauge)", lp["mhhw_ft"] == 6.15)
check("low point: overtops at MHHW + 1 ft", lp["overtop_ft"] == 7.15)
check("low point: margin = peak - overtop level", abs(lp["margin_ft"] - (lp["peak"]["ft"] - 7.15)) < 0.011)
check("low point: first hour at or above its level", lp["reaches_utc"] is not None and
      [q[1] for q in lp["series"] if q[0] == lp["reaches_utc"]][0] >= 7.15 and
      all(q[1] < 7.15 for q in lp["series"] if "2026-10-29T06:00Z" <= q[0] < lp["reaches_utc"]))

# ---- the log keeps LOG_DAYS and replaces a run that is written twice
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "log.csv")
    O.write_log(p, O.log_rows(out), NOW)
    O.write_log(p, O.log_rows(out), NOW)
    rows = open(p).read().strip().splitlines()
    check("log: header + one outlet + one low point + three gauges, once", len(rows) == 6 and rows[0].startswith("cycle_utc"))
    json.dumps(out)

# ---- the grid search finds the same nearest points as checking every point
import random
random.seed(4)
pts = [(37.4 + random.random() * 0.4, -122.5 + random.random() * 0.4, random.choice([0.1, 1.0, 3.0])) for _ in range(3000)]
la, lo, de = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
g = O.grid_of(la, lo)
ok = True
for q in [(37.5, -122.3), (37.61, -122.39), (37.79, -122.11), (37.0, -122.0)]:
    brute = min((O.dist_m(q[0], q[1], la[i], lo[i]), i) for i in range(len(pts)) if de[i] >= O.MIN_DEPTH_M)[1]
    ok = ok and O.nearest(q[0], q[1], la, lo, de, grid=g)[0] == brute
check("grid search = brute force (including a point outside the mesh)", ok)

# ---- the real lists load
lp, lsrc = O.load_lowpoints()
check("low point list loads", len(lp) > 50 and lsrc.endswith("shoreline_hotspots.csv") and all(p["level_in"] > 0 for p in lp))

# ---- the real outlet list loads

pts2, src = O.load_outlets()
check("outlet list loads, shared outlets read once", len(pts2) > 10 and len(pts2) < 27 and src.endswith("creek_outlets.csv"))

print("outlet_tides: %d checks, %d failed" % (checks, fails))
sys.exit(1 if fails else 0)
