"""Checks for scripts/build_shoreline_hotspots.py with made-up map layers (no network).
Run: python scripts/test_shoreline_hotspots.py"""

import json
import os
import sys
import tempfile
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_shoreline_hotspots as H

fails = 0


def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


def sq(lon, lat, size_m, depth="0.5"):
    """A square flooded patch, size_m on a side, as a GeoJSON feature."""
    dx, dy = size_m / 2 / (111320 * 0.79), size_m / 2 / 110540
    ring = [[lon - dx, lat - dy], [lon + dx, lat - dy], [lon + dx, lat + dy], [lon - dx, lat + dy], [lon - dx, lat - dy]]
    return {"type": "Feature", "properties": {"DEPTH_FT": depth}, "geometry": {"type": "Polygon", "coordinates": [ring]}}


WS = [{"name": "BELMONT CREEK", "polys": [[[[-122.30, 37.50], [-122.24, 37.50], [-122.24, 37.54], [-122.30, 37.54], [-122.30, 37.50]]]]},
      {"name": "COLMA CREEK", "polys": [[[[-122.44, 37.63], [-122.38, 37.63], [-122.38, 37.67], [-122.44, 37.67], [-122.44, 37.63]]]]}]
PL = [{"name": "Belmont", "polys": [[[[-122.30, 37.50], [-122.26, 37.50], [-122.26, 37.53], [-122.30, 37.53], [-122.30, 37.50]]]]},
      {"name": "South San Francisco", "polys": [[[[-122.44, 37.63], [-122.39, 37.63], [-122.39, 37.67], [-122.44, 37.67], [-122.44, 37.63]]]]}]

by = {
    12: [sq(-122.270, 37.515, 120, "0.8"), sq(-122.2685, 37.515, 60, "0.3"),   # two close pieces: one spot
         sq(-122.410, 37.650, 30)],                                                # too small (0.2 acre)
    24: [sq(-122.2700, 37.5150, 200, "1.5"),                                      # same place, bigger: stays the 12-in spot
         sq(-122.410, 37.645, 150, "1.0"),                                        # new at 24 in, Colma
         sq(-122.150, 37.700, 300)],                                              # outside any San Mateo County watershed
    36: [],
}
rows = H.candidates(by, WS, PL)
check("three candidate rows: 12-in Belmont, 24-in South San Francisco (small and outside dropped)", [r["level_in"] for r in rows] == [12, 24] and len(rows) == 2)
b, c = rows[0], rows[1]
check("close pieces merged into one spot", b["pieces"] == 2)
check("named by city and watershed", b["city"] == "Belmont" and b["watershed"] == "Belmont Creek" and b["name"] == "Belmont shoreline, Belmont Creek watershed")
check("area in acres, deepest depth", 4.3 <= b["area_acres"] <= 4.6 and b["max_depth_ft"] == 0.8)
check("a spot already flooded at 12 in isn't repeated at 24 in", sum(1 for r in rows if r["watershed"] == "Belmont Creek") == 1)
check("ids in order, include = review", [r["id"] for r in rows] == ["SH-001", "SH-002"] and all(r["include"] == "review" for r in rows))
check("24-in spot in South San Francisco", c["city"] == "South San Francisco" and c["watershed"] == "Colma Creek")


def fake_get(url, params=None):
    if url.endswith("?f=json"):
        return json.dumps({"layers": [{"id": 0, "name": "BCDC SLR 1.0 ft (12 in)"}, {"id": 1, "name": "BCDC SLR 2.0 ft (24 in)"},
                                      {"id": 2, "name": "BCDC SLR 3.0 ft (36 in)"}, {"id": 5, "name": "BCDC SLR 5.5 ft (66 in)"}]})
    q = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))
    if q.get("returnIdsOnly") == "true":
        return json.dumps({"objectIds": list(range(1, 251))})
    ids = q["objectIds"].split(",")
    return json.dumps({"type": "FeatureCollection", "features": [sq(-122.27, 37.515, 50) for _ in ids]})


lay = H.layers(fake_get)
check("layers found by their names (12, 24, 36, 66 in)", lay == {12: 0, 24: 1, 36: 2, 66: 5})
calls = []
feats = H.features(0, lambda u, p=None: calls.append(u) or fake_get(u))
check("250 shapes fetched one by one by object id, in lon/lat", len(feats) == 250 and len(calls) == 251 and "outSR=4326" in calls[1])


# a shape too big to send in detail (HTTP 500) is asked for again with a simpler outline
def big_500(url, params=None):
    q = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))
    if q.get("returnIdsOnly") == "true":
        return json.dumps({"objectIds": [7]})
    if float(q["maxAllowableOffset"]) < 0.0003:
        raise OSError("HTTP Error 500: Internal Server Error")
    return json.dumps({"type": "FeatureCollection", "features": [sq(-122.27, 37.515, 50)]})


fb = H.features(2, big_500)
check("HTTP 500 at full detail: read with the simplest outline instead", len(fb) == 1)

with tempfile.TemporaryDirectory() as d:
    H.write(rows, os.path.join(d, "x.csv"), os.path.join(d, "x.geojson"))
    raw = open(os.path.join(d, "x.csv"), "rb").read()
    g = json.load(open(os.path.join(d, "x.geojson")))
    check("CSV with CRLF and the review columns", raw.startswith(b"id,name,city,watershed,lat,lon,level_in") and b"\r\n" in raw)
    check("GeoJSON with one feature per row", len(g["features"]) == 2 and g["features"][0]["properties"]["id"] == "SH-001")

# a host that sends a web page, then the second host; GeoJSON refused, Esri JSON instead
def page_then_ok(url, params=None):
    if url.startswith(H.SERVICES[0]):
        return "<html>Access denied</html>"
    if "f=geojson" in url:
        return json.dumps({"error": {"code": 400, "message": "Invalid format"}})
    if url.endswith("?f=json"):
        return fake_get(url)
    q = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))
    if q.get("returnIdsOnly") == "true":
        return json.dumps({"objectIds": [1, 2]})
    ring = [[-122.27, 37.515], [-122.27, 37.516], [-122.269, 37.516], [-122.269, 37.515], [-122.27, 37.515]]   # clockwise
    hole = [[-122.2698, 37.5152], [-122.2692, 37.5152], [-122.2692, 37.5158], [-122.2698, 37.5158], [-122.2698, 37.5152]]
    return json.dumps({"features": [{"attributes": {"DEPTH_FT": "0.4"}, "geometry": {"rings": [ring, hole]}}]})


H.SERVICE = H.SERVICES[0]
lay2 = H.layers(page_then_ok)
check("first host sends a web page: the second host is used", lay2.get(24) == 1 and H.SERVICE == H.SERVICES[1])
f2 = H.features(1, page_then_ok)
g = f2[0]["geometry"]
check("GeoJSON refused: Esri JSON read and converted (outer ring plus its hole)", len(f2) == 2 and g["type"] == "MultiPolygon" and len(g["coordinates"][0]) == 2)
check("depth kept from the Esri attributes", H.depth(f2[0]["properties"]) == 0.4)
try:
    H.fetch_json("https://example.org/x?f=json", lambda u, p=None: "<html>")
    check("a web page instead of JSON gives a clear error", False)
except RuntimeError as e:
    check("a web page instead of JSON gives a clear error", "not JSON" in str(e))
H.SERVICE = H.SERVICES[0]

print("\n" + ("All passed" if not fails else f"{fails} FAILED"))
sys.exit(1 if fails else 0)
