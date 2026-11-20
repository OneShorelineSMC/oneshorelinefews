"""Tests for rrfs.py with made-up AQPI files in their published layout (name, institution, gridpoint, run_time, one
column per step). Real grid points from the 2026-11-20 files are included. Run: python scripts/test_rrfs.py"""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rrfs as R  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


UTC = dt.timezone.utc
NOW = dt.datetime(2026, 11, 20, 15, 50, tzinfo=UTC)


def lattice():
    """A 3 km grid over the county, with 0.1 in/hour from 16 to 18 UTC and 0.4 in in the hour ending 17 UTC near San Bruno."""
    pts = []
    lat = 37.10
    while lat < 37.85:
        lon = -122.55
        while lon < -122.05:
            pts.append((round(lon, 4), round(lat, 4)))
            lon += 0.034
        lat += 0.027
    return pts


def make_csv(prefix, run, steps, value):
    head = "name,institution,gridpoint,run_time," + ",".join(f"{prefix}_{t:%Y%m%d%H%M}" for t in steps)
    rows = [head]
    for lon, lat in lattice():
        vals = ",".join(f"{value(lon, lat, t):g}" for t in steps)
        rows.append(f"San Francisco Bay Estuaries,SMC_EM,POINT ({lon} {lat}),{run:%Y-%m-%d %H:%M},{vals}")
    # one real row (Visitacion, 2026-11-20 12 UTC run) with its exact point text
    return "\n".join(rows) + "\n"


def v60(lon, lat, t):
    near = abs(lat - 37.63) < 0.03 and abs(lon + 122.43) < 0.04
    if t.hour == 17:
        return 0.4 if near else 0.1
    return 0.1 if t.hour in (16, 18) else 0.0


RUN60 = dt.datetime(2026, 11, 20, 12, tzinfo=UTC)
STEPS60 = [RUN60 + dt.timedelta(hours=h) for h in range(1, 85) if not (h > 24 and (RUN60 + dt.timedelta(hours=h)).hour in (12, 13))]
RUN15 = dt.datetime(2026, 11, 20, 15, tzinfo=UTC)
STEPS15 = [RUN15 + dt.timedelta(minutes=15 * k) for k in range(1, 73)]
F60 = make_csv("qpf01rrfs", RUN60, STEPS60, v60)
F15 = make_csv("qpf15minrrfs", RUN15, STEPS15, lambda lon, lat, t: 0.1 if t.hour == 16 and t.minute == 30 else 0.0)

run, steps, grid = R.parse_csv(F60)
check("parse: run time in UTC", run == RUN60)
check("parse: step columns read, missing hours stay missing", len(steps) == len(STEPS60) and steps[0] == RUN60 + dt.timedelta(hours=1))
check("parse: every grid point read with its lon/lat", len(grid) == len(lattice()) and grid[0][1] < -122)

real = 'name,institution,gridpoint,run_time,qpf01rrfs_202611201300,qpf01rrfs_202611201400\r\n' \
       'Visitacion Valley-Frontal San Francisco Bay Estuaries,SMC_EM,POINT (-122.40866604419142 37.65224996367108),2026-11-20 12:00,0.0,0.052\r\n' \
       'bad row,SMC_EM,POINT (x y),2026-11-20 12:00,0.0,0.1\r\n'
r2, s2, g2 = R.parse_csv(real)
check("parse: the real file's layout (CRLF, POINT text); a bad point is skipped", len(g2) == 1 and g2[0][3] == [0.0, 0.052] and abs(g2[0][2] - 37.65225) < 1e-4)
try:
    R.parse_csv("name,gridpoint\n")
    check("parse: a file without run_time is refused", False)
except ValueError:
    check("parse: a file without run_time is refused", True)

sheds = R.load_watersheds()
points = R.load_points()
check("lookups: every creek's watershed is in data/watersheds.geojson", all(w in sheds for p in points.values() for w in p["watersheds"]))
a = R.assign(grid, points, sheds)
check("assign: every creek gets at least 2 grid points", all(len(x["idx"]) >= 2 for x in a.values()))
check("assign: the big watersheds use only points inside", a["sangregorio"]["how"] == "inside" and a["sangregorio"]["inside"] >= 5)
check("assign: Butano (no watershed named) uses the nearest points", a["butano"]["how"] == "nearest")
check("in_shape: a point far offshore is in no watershed", not any(R.in_shape(-123.5, 37.5, g) for gs in sheds.values() for g in gs))

# Heavy-or-more stretches against Atlas 14 (1-year 60 min = 0.5 in, 2-year = 0.7; 1-year 15 min = 0.25 in)
from creek_signals import storm_years  # noqa: E402
T0 = dt.datetime(2026, 11, 20, 16, tzinfo=UTC)
h_steps = [T0 + dt.timedelta(hours=k) for k in range(1, 7)]
q_steps = [T0 + dt.timedelta(minutes=15 * k) for k in range(1, 13)]
by_min = {60: {1.0: 0.5, 2.0: 0.7, 5.0: 1.0}, 15: {1.0: 0.25, 2.0: 0.35, 5.0: 0.5}}
hs = R.heavy_spans({60: (h_steps, [0.1, 0.6, 0.2, 0.0, 0.8, 0.0]), 15: (q_steps, [0.0] * 4 + [0.15] * 4 + [0.0] * 4)}, by_min, storm_years, T0)
check("heavy: each stretch with its level, window and start/end; the 15-minute product up to 19:00, the hourly one after",
      [(h["start"][11:16], h["end"][11:16], h["level"]) for h in hs] == [("17:00", "18:00", 1), ("20:00", "21:00", 2)] and hs[1]["minutes"] == 60)
check("heavy: nothing below the 1-year storm", R.heavy_spans({60: (h_steps, [0.2] * 6)}, by_min, storm_years, T0) == [])
check("heavy: past steps are left out", R.heavy_spans({60: (h_steps, [0.0, 0.6, 0, 0, 0, 0])}, by_min, storm_years, T0 + dt.timedelta(hours=3)) == [])

tmp = tempfile.mkdtemp()
try:
    creeks_file = {}
    try:
        import subprocess
        creeks_file = json.loads(subprocess.run(["git", "show", "origin/data:creeks.json"], capture_output=True, text=True,
                                                cwd=os.path.dirname(os.path.abspath(__file__))).stdout or "{}")
    except Exception:  # noqa: BLE001
        pass
    with open(os.path.join(tmp, "creeks.json"), "w") as f:
        json.dump(creeks_file, f)
    files = {R.BASE + R.PRODUCTS["60"]: F60, R.BASE + R.PRODUCTS["15"]: F15}
    out = os.path.join(tmp, "rrfs.json")
    R.main(["rrfs.py", out], fetch=lambda u: files[u], now=NOW)
    d = json.load(open(out))
    sb = d["creeks"]["sanbruno"]
    check("output: inches, both products, steps listed", d["units"] == "in" and set(d["products"]) == {"60", "15"} and len(d["products"]["15"]["steps"]) == 72)
    check("output: San Bruno's wettest hour is the one ending 17 UTC", sb["peak60"]["end"] == "2026-11-20T17:00Z" and sb["peak60"]["in"] >= 0.1)
    check("output: next 6 hours = 3 rainy hours", 0.29 < sb["totals"]["6"] < 1.3)
    check("output: wettest 15 minutes", sb["peak15"] == {"in": 0.1, "end": "2026-11-20T16:30Z"})
    if creeks_file.get("sensors"):
        check("output: heavy stretches listed for each creek with Atlas 14", isinstance(sb.get("heavy"), list))
    check("output: average never above the wettest point", all(a_ <= m for a_, m in zip(sb["p60"]["avg"], sb["p60"]["max"]) if a_ is not None))
    if creeks_file.get("sensors"):
        check("output: storm size against Atlas 14 at the main gauge", "size" in sb and sb["size"]["number"] in ("41102", 41102))
    log = open(os.path.join(tmp, "rrfs_log.csv")).read().splitlines()
    check("log: header and rows with rain only", log[0] == R.LOG_HEAD and all(float(l.split(",")[5]) > 0 for l in log[1:]))
    n = len(log)
    R.main(["rrfs.py", out], fetch=lambda u: files[u], now=NOW + dt.timedelta(minutes=30))
    check("log: the same run isn't logged twice", len(open(os.path.join(tmp, "rrfs_log.csv")).read().splitlines()) == n)
    R.main(["rrfs.py", out, "--min-age", "20"], fetch=lambda u: (_ for _ in ()).throw(AssertionError("fetched")), now=NOW + dt.timedelta(minutes=40))
    check("--min-age: a recent file is kept without fetching", json.load(open(out))["generated_utc"] == "2026-11-20T16:20Z")

    def half(u):
        if "15min" in u:
            raise OSError("down")
        return files[u]
    R.main(["rrfs.py", out], fetch=half, now=NOW + dt.timedelta(hours=1))
    d2 = json.load(open(out))
    check("one product down: the other is used, the old one kept, problem noted",
          "15" in d2["products"] and d2["creeks"]["sanbruno"].get("p15") and any("15min" in p for p in d2["problems"]))
    R.main(["rrfs.py", out], fetch=lambda u: (_ for _ in ()).throw(OSError("down")), now=NOW + dt.timedelta(hours=2))
    d3 = json.load(open(out))
    check("both down: previous forecast kept with the problems", d3["creeks"]["sanbruno"]["peak60"] and len(d3["problems"]) == 2)
    old = make_csv("qpf01rrfs", RUN60 - dt.timedelta(days=2), STEPS60, v60)
    R.main(["rrfs.py", out], fetch=lambda u: old if "qpf01" in u else F15, now=NOW)
    check("a run over 30 hours old isn't used", any("30 hours" in p for p in json.load(open(out))["problems"]))
finally:
    shutil.rmtree(tmp)

print("\nAll passed" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
