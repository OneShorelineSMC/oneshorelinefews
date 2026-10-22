"""Checks for scripts/build_shoreline_lowpoints.py with made-up overtopping lines (no network).
Run: python scripts/test_shoreline_lowpoints.py"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_shoreline_lowpoints as B

fails = 0


def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


def east(lon, lat, m):   # a straight line m metres long, heading east
    return [[lon, lat], [lon + m / (111320 * 0.79), lat]]


def feat(coords, level, depth="0.4"):
    return {"type": "Feature", "properties": {"LEVEL_IN": level, "OT_Depth": depth}, "geometry": {"type": "LineString", "coordinates": coords}}


WS = [{"name": "BELMONT CREEK", "polys": [[[[-122.30, 37.50], [-122.24, 37.50], [-122.24, 37.54], [-122.30, 37.54], [-122.30, 37.50]]]]},
      {"name": "COLMA CREEK", "polys": [[[[-122.44, 37.63], [-122.38, 37.63], [-122.38, 37.67], [-122.44, 37.67], [-122.44, 37.63]]]]}]
PL = [{"name": "Belmont", "polys": [[[[-122.30, 37.50], [-122.26, 37.50], [-122.26, 37.53], [-122.30, 37.53], [-122.30, 37.50]]]]},
      {"name": "South San Francisco", "polys": [[[[-122.44, 37.63], [-122.39, 37.63], [-122.39, 37.67], [-122.44, 37.67], [-122.44, 37.63]]]]}]

fc = {"type": "FeatureCollection", "features": [
    feat(east(-122.2800, 37.515, 100), 12, "0.3"),          # Belmont, 100 m at 12 in
    feat(east(-122.2785, 37.515, 60), 12, "0.5"),           # 50 m further east, same low point
    feat(east(-122.2800, 37.515, 300), 24, "1.2"),          # the same shoreline at 24 in, longer: only the new part counts
    feat(east(-122.4100, 37.650, 80), 24, "0.6"),           # Colma, new at 24 in
    feat(east(-122.4100, 37.640, 10), 36),                  # too short
    feat(east(-122.1500, 37.700, 200), 36),                 # outside San Mateo County watersheds
    feat(east(-122.2700, 37.520, 50), 66),                  # a level the page doesn't use
]}
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "ot.geojson")
    json.dump(fc, open(p, "w"))
    by, skipped = B.load(p)
    check("levels read from LEVEL_IN (any case); other levels left out", [len(by[x]) for x in B.LEVELS_IN] == [2, 2, 2] and skipped == 1)
    rows = B.low_points(by, WS, PL)
    check("rows: Belmont 12 in, then at 24 in the extra Belmont shoreline and Colma (short and outside dropped)",
          [(r["level_in"], r["watershed"]) for r in rows] == [(12, "Belmont Creek"), (24, "Belmont Creek"), (24, "Colma Creek")])
    b = rows[0]
    check("stretches within 200 m joined into one low point", b["stretches"] == 2 and 135 <= b["length_m"] <= 165)
    check("deepest overtopping kept", b["max_depth_ft"] == 0.5)
    check("named by city and watershed", b["name"] == "Belmont shoreline, Belmont Creek watershed" and b["city"] == "Belmont")
    ext = rows[1]
    check("24 in: only the shoreline beyond what 12 in already overtops (about 300 - 192 - 15 m)", 80 <= ext["length_m"] <= 100)
    check("the point given is on the shoreline", abs(b["lat"] - 37.515) < 1e-4)
    B.write(rows, os.path.join(d, "x.csv"), os.path.join(d, "x.geojson"))
    raw = open(os.path.join(d, "x.csv"), "rb").read()
    g = json.load(open(os.path.join(d, "x.geojson")))
    check("CSV with CRLF and the review columns", raw.startswith(b"id,name,city,watershed,lat,lon,level_in,length_m") and b"\r\n" in raw)
    check("map file: one line feature per row", len(g["features"]) == 3 and g["features"][0]["geometry"]["type"] == "MultiLineString")
    B.INPUT = os.path.join(d, "missing.geojson")
    check("no input file: clear message, nothing written", B.main() == 1)

print("\n" + ("All passed" if not fails else f"{fails} FAILED"))
sys.exit(1 if fails else 0)
