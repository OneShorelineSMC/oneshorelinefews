"""RRFS rain forecast for each creek, from AQPI / CW3E (staff view only; staff, 2026-11-20).

AQPI (Advanced Quantitative Precipitation Information, run by CW3E at UC San Diego) posts the RRFS model's rain
forecast (QPF) for San Mateo County every hour on its datashare, as two CSV files:
  qpf01rrfs/SMCEM_qpf01rrfs.csv        rain in each hour, out to about 3.5 days (the 84-hour run, every 6 hours)
  qpf15minrrfs/SMCEM_qpf15minrrfs.csv  rain in each 15 minutes, out to about 18 hours (the hourly run)
One row per model grid point (3 km apart) with its watershed name, POINT (lon lat) and run time (UTC); then one
column per step, qpf01rrfs_YYYYMMDDHHMM = the rain in the hour (or 15 minutes) ENDING at that UTC time.
Units are not stated in the files. They are inches: on 2026-11-20 the 6 AM run gave about 0.2 in near San Bruno for
4-10 AM, against 0.12 in from the NWS forecast and 0.08-0.32 in measured (in mm it would be 0.01 in). AQPI to confirm.

For each creek this step averages the grid points inside its County watershed (the `watershed` column of
lookups/forecast_points.csv, polygons in data/watersheds.geojson). A watershed with fewer than MIN_POINTS grid points
inside also takes the nearest points to its forecast point. It keeps the average and the wettest point per step, the
totals for the next 6, 24 and 72 hours, the wettest hour and 15 minutes, and a rough storm size against NOAA Atlas 14
at the creek's main rain gauge (as for the NWS forecast; the size is only as good as the forecast).

It never changes a creek's status, and the pages show it only in the staff view (?preview=1), never on the kiosks.

Every new run is also added to rrfs_log.csv (run, product, creek, step, inches; steps with rain only), kept for
LOG_DAYS, so the forecasts can be checked against the gauges after a storm.

Usage: python rrfs.py OUTPUT.json --creeks out/creeks.json [--min-age MINUTES]
"""

import csv
import datetime as dt
import io
import json
import math
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
BASE = "https://cw3e-datashare.ucsd.edu/AQPI/"
PRODUCTS = {"60": "qpf01rrfs/SMCEM_qpf01rrfs.csv", "15": "qpf15minrrfs/SMCEM_qpf15minrrfs.csv"}
UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
MIN_POINTS = 2
LOG_DAYS = 60
UTC = dt.timezone.utc
SIZE_MIN = (15, 30, 60, 180, 360, 1440)   # windows rated against Atlas 14 (15-60 min from the 15-minute product)


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8-sig")


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%MZ")


def parse_iso(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC)


def parse_csv(text):
    """(run_time, [step end times], [(name, lon, lat, [inches or None])])."""
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("empty file")
    head = [h.strip() for h in rows[0]]
    try:
        i_name, i_pt, i_run = head.index("name"), head.index("gridpoint"), head.index("run_time")
    except ValueError:
        raise ValueError("columns name, gridpoint, run_time not found")
    cols = [(i, h) for i, h in enumerate(head) if "_" in h and h.rsplit("_", 1)[1].isdigit() and len(h.rsplit("_", 1)[1]) == 12]
    if not cols:
        raise ValueError("no forecast columns")
    steps = [dt.datetime.strptime(h.rsplit("_", 1)[1], "%Y%m%d%H%M").replace(tzinfo=UTC) for _, h in cols]
    run, pts = None, []
    for r in rows[1:]:
        if len(r) <= i_run:
            continue
        p = r[i_pt].strip()
        if not p.upper().startswith("POINT"):
            continue
        try:
            lon, lat = (float(x) for x in p[p.index("(") + 1:p.index(")")].split())
        except ValueError:
            continue
        run = run or r[i_run].strip()
        vals = []
        for i, _ in cols:
            try:
                v = float(r[i])
                vals.append(v if math.isfinite(v) and 0 <= v < 20 else None)
            except (ValueError, IndexError):
                vals.append(None)
        pts.append((r[i_name].strip(), lon, lat, vals))
    if not pts:
        raise ValueError("no grid points")
    run_t = dt.datetime.strptime(run, "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
    return run_t, steps, pts


# ---------------------------------------------------------------- watersheds

def _in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def in_shape(x, y, geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        if poly and _in_ring(x, y, poly[0]) and not any(_in_ring(x, y, h) for h in poly[1:]):
            return True
    return False


def load_watersheds(path=os.path.join(ROOT, "data", "watersheds.geojson")):
    with open(path) as f:
        gj = json.load(f)
    out = {}
    for ft in gj.get("features", []):
        n = ((ft.get("properties") or {}).get("name") or "").strip().upper()
        if n and ft.get("geometry"):
            out.setdefault(n, []).append(ft["geometry"])
    return out


def load_points(path=os.path.join(ROOT, "lookups", "forecast_points.csv")):
    """{creek: {"lat", "lon", "watersheds": [NAME, ...]}} from forecast_points.csv."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            cid = (r.get("creek") or "").strip()
            if not cid:
                continue
            try:
                lat, lon = float(r["lat"]), float(r["lon"])
            except (TypeError, ValueError, KeyError):
                continue
            ws = [w.strip().upper() for w in (r.get("watershed") or "").split(";") if w.strip()]
            out[cid] = {"lat": lat, "lon": lon, "watersheds": ws}
    return out


def km(lat1, lon1, lat2, lon2):
    x = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2)) * 111.32
    return math.hypot(x, (lat2 - lat1) * 110.57)


def assign(grid, points, sheds, min_points=MIN_POINTS):
    """{creek: {"idx": [grid row numbers], "how": "inside" | "inside+nearest" | "nearest", "inside": n}}."""
    out = {}
    for cid, p in points.items():
        geoms = [g for w in p["watersheds"] for g in sheds.get(w, [])]
        inside = [i for i, (_, lon, lat, _) in enumerate(grid) if any(in_shape(lon, lat, g) for g in geoms)]
        idx = list(inside)
        if len(idx) < min_points:
            near = sorted((km(p["lat"], p["lon"], lat, lon), i) for i, (_, lon, lat, _) in enumerate(grid) if i not in idx)
            idx += [i for _, i in near[:min_points - len(idx)]]
        out[cid] = {"idx": idx, "inside": len(inside),
                    "how": "inside" if len(inside) >= min_points else ("inside+nearest" if inside else "nearest")}
    return out


# ---------------------------------------------------------------- per creek

def series(grid, idx, n):
    """Average and wettest point per step (None where no point has a value)."""
    avg, mx = [], []
    for k in range(n):
        v = [grid[i][3][k] for i in idx if grid[i][3][k] is not None]
        avg.append(round(sum(v) / len(v), 3) if v else None)
        mx.append(round(max(v), 3) if v else None)
    return avg, mx


def window_max(steps, vals, step_min, minutes, now):
    """Wettest total over any `minutes` window of whole steps ending after now: (inches, end time) or None."""
    k = max(1, minutes // step_min)
    best = None
    for j in range(len(steps)):
        if steps[j] <= now:
            continue
        a = j - k + 1
        if a < 0:
            continue
        span = steps[a:j + 1]
        if (span[-1] - span[0]) != dt.timedelta(minutes=step_min * (k - 1)):
            continue   # a gap in the steps (some hours are missing from the files)
        v = vals[a:j + 1]
        if any(x is None for x in v):
            continue
        s = sum(v)
        if best is None or s > best[0]:
            best = (s, steps[j])
    return best


def total(steps, vals, a, b):
    return sum(v for t, v in zip(steps, vals) if v is not None and a < t <= b)


def storm_size(windows, by_min, years_fn):
    """Rarest of the rated windows: {"minutes", "in", "years", "end", "one_year_in"}; None without Atlas 14."""
    best = None
    for m, w in windows.items():
        table = by_min.get(m)
        if not table or not w or w[0] <= 0:
            continue
        one = table[min(table)]
        y = years_fn(table, w[0])
        key = (y or 0, w[0] / one)
        if best is None or key > best[0]:
            best = (key, {"minutes": m, "in": round(w[0], 2), "years": y, "end": iso(w[1]), "one_year_in": round(one, 2)})
    return best[1] if best else None


def creek_freq(c, sensors):
    sys.path.insert(0, HERE)
    from nws_forecast import main_rain_gauge
    g = main_rain_gauge(c)
    freq = ((sensors.get(g["key"]) or {}).get("signals") or {}).get("freq") if g else None
    if not freq:
        return None, g
    return {int(m): {float(a): d for a, d in v.items()} for m, v in (freq.get("minutes") or {}).items()}, g


def build(products, creeks_file, points, sheds, now):
    """products: {"60"|"15": (run, steps, grid)}. Returns the "creeks" part of rrfs.json."""
    sys.path.insert(0, HERE)
    from creek_signals import storm_years
    creeks = (creeks_file.get("creeks") or []) + (creeks_file.get("creeks_preview") or [])
    names = {c["id"]: c for c in creeks}
    sensors = creeks_file.get("sensors") or {}
    out = {}
    for cid in sorted(points, key=lambda k: [c["id"] for c in creeks].index(k) if k in names else 99):
        c = names.get(cid, {"id": cid})
        e = {"name": c.get("name") or cid, "watershed": "; ".join(points[cid]["watersheds"])}
        windows = {}
        for key, (run, steps, grid) in products.items():
            a = assign(grid, {cid: points[cid]}, sheds)[cid]
            avg, mx = series(grid, a["idx"], len(steps))
            sm = int(key)
            e["p" + key] = {"avg": avg, "max": mx, "points": len(a["idx"]), "how": a["how"]}
            for m in SIZE_MIN:
                if (sm == 15 and m <= 60) or (sm == 60 and m > 60):
                    windows[m] = window_max(steps, avg, sm, m, now)
            pk = window_max(steps, avg, sm, sm, now)
            if pk:
                e["peak" + key] = {"in": round(pk[0], 2), "end": iso(pk[1])}
            if key == "60":
                e["totals"] = {str(h): round(total(steps, avg, now, now + dt.timedelta(hours=h)), 2) for h in (6, 24, 72)}
        by_min, g = creek_freq(c, sensors)
        if by_min:
            sz = storm_size(windows, by_min, storm_years)
            if sz:
                sz.update(gauge=g.get("label"), number=g.get("number"))
                e["size"] = sz
        out[cid] = e
    return out


# ---------------------------------------------------------------- log

LOG_HEAD = "run_utc,product_min,creek,step_end_utc,in_avg,in_max"


def append_log(path, products, creeks, now, keep_days=LOG_DAYS):
    """Adds each run not yet in the log (steps with rain only); drops runs older than keep_days."""
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError:
        lines = []
    if not lines or lines[0] != LOG_HEAD:
        lines = [LOG_HEAD]
    have = {(l.split(",")[0], l.split(",")[1]) for l in lines[1:]}
    added = 0
    for key, (run, steps, _) in products.items():
        if (iso(run), key) in have:
            continue
        for cid, e in creeks.items():
            p = e.get("p" + key) or {}
            for t, a, m in zip(steps, p.get("avg") or [], p.get("max") or []):
                if a or m:
                    lines.append(f"{iso(run)},{key},{cid},{iso(t)},{a or 0:g},{m or 0:g}")
                    added += 1
        # a run with no rain anywhere still leaves one row, so it counts as logged
        if not any(l.startswith(f"{iso(run)},{key},") for l in lines[1:]):
            lines.append(f"{iso(run)},{key},,,0,0")
    cut = iso(now - dt.timedelta(days=keep_days))
    lines = [lines[0]] + [l for l in lines[1:] if l[:17] >= cut]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return added


# ---------------------------------------------------------------- main

def main(argv, fetch=get, now=None):
    path = argv[1]
    min_age = float(argv[argv.index("--min-age") + 1]) if "--min-age" in argv else 0
    creeks_path = argv[argv.index("--creeks") + 1] if "--creeks" in argv else os.path.join(os.path.dirname(path) or ".", "creeks.json")
    now = now or dt.datetime.now(UTC)
    previous = {}
    try:
        with open(path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        pass
    last = previous.get("generated_utc")
    if last and min_age and now - parse_iso(last) < dt.timedelta(minutes=min_age):
        print(f"rrfs: last run {last}, younger than {min_age:g} min; kept")
        return 0
    try:
        with open(creeks_path) as f:
            creeks_file = json.load(f)
    except (OSError, ValueError):
        creeks_file = {}
    problems, products = [], {}
    for key, rel in PRODUCTS.items():
        try:
            run, steps, grid = parse_csv(fetch(BASE + rel))
            if now - run > dt.timedelta(hours=30):
                problems.append(f"{rel}: run {iso(run)} is more than 30 hours old; not used")
                continue
            products[key] = (run, steps, grid)
        except Exception as e:  # noqa: BLE001 - one product failing keeps the other
            problems.append(f"{rel}: {type(e).__name__}: {e}"[:200])
    if not products:
        previous.setdefault("problems", [])
        previous["problems"] = problems
        previous["checked_utc"] = iso(now)
        with open(path, "w") as f:
            json.dump(previous, f, separators=(",", ":"))
        for p in problems:
            print("problem:", p)
        return 0
    points, sheds = load_points(), load_watersheds()
    missing = sorted(w for p in points.values() for w in p["watersheds"] if w not in sheds)
    if missing:
        problems.append("watersheds not found in data/watersheds.geojson: " + ", ".join(missing))
    creeks = build(products, creeks_file, points, sheds, now)
    result = {
        "generated_utc": iso(now),
        "source": "AQPI / CW3E RRFS rain forecast (QPF), San Mateo County grid points",
        "units": "in",
        "products": {k: {"run": iso(r), "step_min": int(k), "steps": [iso(t) for t in s], "grid_points": len(g)}
                     for k, (r, s, g) in products.items()},
        "creeks": creeks,
        "problems": problems,
    }
    # keep a product that failed this time from the previous file (only while its run is under 30 hours old)
    for key in PRODUCTS:
        old = (previous.get("products") or {}).get(key)
        if key not in products and old and now - parse_iso(old["run"]) < dt.timedelta(hours=30):
            result["products"][key] = old
            for cid, e in creeks.items():
                pc = (previous.get("creeks") or {}).get(cid) or {}
                for k in ("p" + key, "peak" + key) + (("totals",) if key == "60" else ()):
                    if pc.get(k) is not None:
                        e[k] = pc[k]
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    n = append_log(os.path.join(os.path.dirname(path) or ".", "rrfs_log.csv"), products, creeks, now)
    for k, (r, s, g) in products.items():
        print(f"rrfs {k}-min: run {iso(r)}, {len(s)} steps to {iso(s[-1])}, {len(g)} grid points")
    for cid, e in creeks.items():
        t = e.get("totals") or {}
        print(f"{cid}: {e.get('p60', {}).get('points', e.get('p15', {}).get('points'))} pts ({e.get('p60', e.get('p15', {})).get('how')}) "
              f"6h {t.get('6')} 24h {t.get('24')} 72h {t.get('72')} in" + (f", size {e['size']}" if e.get("size") else ""))
    print(f"rrfs_log.csv: {n} rows added")
    for p in problems:
        print("problem:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
