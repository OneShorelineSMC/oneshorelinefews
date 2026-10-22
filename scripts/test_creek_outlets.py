"""Checks for scripts/build_creek_outlets.py with made-up watersheds, shoreline and creek lines (no network).
Run: python scripts/test_creek_outlets.py"""

import csv
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_creek_outlets as B
from shapely.geometry import LineString

fails = 0


def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


def box(x0, y0, x1, y1):
    return {"type": "Polygon", "coordinates": [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}


def nhd(name, *pts):
    return {"type": "Feature", "properties": {"gnis_name": name}, "geometry": {"type": "LineString", "coordinates": [list(p) for p in pts]}}


SM = {"Geographic_County": "San Mateo"}
SHORE_X = -122.250   # the Bay shoreline runs north-south here; the Bay is to the east
shore = [(LineString([(SHORE_X, 37.40), (SHORE_X, 37.535)]), dict(SM, Class="Engineered Levee")),
         (LineString([(SHORE_X, 37.535), (SHORE_X, 37.545)]), dict(SM, Class="Channel or Opening")),
         (LineString([(SHORE_X, 37.545), (SHORE_X, 37.70)]), dict(SM, Class="Wetland")),
         (LineString([(-122.10, 37.40), (-122.10, 37.70)]), {"Geographic_County": "Alameda", "Class": "Engineered Levee"})]
ws = [{"name": "COLMA CREEK", "geometry": box(-122.30, 37.60, -122.249, 37.65)},
      {"name": "HIGHLINE CREEK", "geometry": box(-122.30, 37.56, -122.249, 37.60)},
      {"name": "SEAL SLOUGH", "geometry": box(-122.30, 37.52, -122.249, 37.56)},
      {"name": "INLAND CREEK", "geometry": box(-122.40, 37.45, -122.33, 37.50)},       # 7 km from the shoreline
      {"name": "PILARCITOS CREEK", "geometry": box(-122.50, 37.45, -122.44, 37.50)}]  # Coastside
flow = [nhd("Colma Creek", (-122.29, 37.62), (-122.27, 37.62)),          # upper piece flows into the lower one
        nhd("Colma Creek", (-122.27, 37.62), (-122.24, 37.62)),          # crosses the shoreline, ends in the Bay
        nhd("Highline Canal", (-122.29, 37.58), (-122.2525, 37.58)),     # ends about 220 m short of the shoreline
        nhd("Inland Creek", (-122.39, 37.47), (-122.34, 37.47))]
rows = B.build(ws, shore, flow)
by = {r["watershed"]: r for r in rows}
check("Bay-side watersheds only (inland and Coastside left out), north to south",
      [r["watershed"] for r in rows] == ["Colma Creek", "Highline Creek", "Seal Slough"])
c = by["Colma Creek"]
check("Colma: where the creek line crosses the shoreline", c["lat"] == 37.62 and c["lon"] == SHORE_X and c["method"].startswith("creek line crosses"))
check("Colma: distance from the creek's downstream end to the outlet (about 880 m)", 850 <= c["end_to_outlet_m"] <= 900)
check("Colma: FEWS creek id and shoreline class", c["fews_creek"] == "colma" and c["shore_class"] == "Wetland")
h = by["Highline Creek"]
check("Highline: NHD name from the FEWS aliases; creek end used when it doesn't reach the shoreline",
      h["creek"] == "Highline Canal" and h["fews_creek"] == "greenhills" and h["lon"] == -122.2525 and "ends 22" in h["method"])
s = by["Seal Slough"]
check("Seal Slough: no NHD line, the shoreline opening next to it, flagged",
      s["method"].startswith("no creek line in NHD: shoreline opening") and s["lat"] == 37.54 and s["shore_class"] == "Channel or Opening")
with tempfile.TemporaryDirectory() as d:
    B.write(rows, os.path.join(d, "o.csv"), os.path.join(d, "o.geojson"))
    raw = open(os.path.join(d, "o.csv"), "rb").read()
    got = list(csv.DictReader(open(os.path.join(d, "o.csv"), newline="")))
    g = json.load(open(os.path.join(d, "o.geojson")))
    check("CSV: CRLF, the review columns, ids CO-001..", raw.startswith(b"id,creek,watershed,fews_creek,city,lat,lon") and b"\r\n" in raw
          and [r["id"] for r in got] == ["CO-001", "CO-002", "CO-003"] and got[0]["include"] == "review")
    check("map file: a point per row plus the creek lines used", sum(f["geometry"]["type"] == "Point" for f in g["features"]) == 3
          and sum(f["geometry"]["type"] == "MultiLineString" for f in g["features"]) == 2)
print("\n" + ("All passed" if not fails else f"{fails} FAILED"))
sys.exit(1 if fails else 0)
