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
prep, _ = H.prepare(by)
rows = H.candidates(prep, WS, PL)
check("candidate rows: 12-in Belmont, then at 24 in the extra ground around it and South San Francisco (small and outside dropped)",
      [r["level_in"] for r in rows] == [12, 24, 24])
b = rows[0]
c = next(r for r in rows if r["watershed"] == "Colma Creek")
ring = next(r for r in rows if r["level_in"] == 24 and r["watershed"] == "Belmont Creek")
check("close pieces merged into one spot", b["pieces"] == 2)
check("named by city and watershed", b["city"] == "Belmont" and b["watershed"] == "Belmont Creek" and b["name"] == "Belmont shoreline, Belmont Creek watershed")
check("area in acres, deepest depth", 4.3 <= b["area_acres"] <= 4.6 and b["max_depth_ft"] == 0.8)
check("at 24 in only the ground added since 12 in (the ring around the 12-in spot, not the whole square again)", 5.0 <= ring["area_acres"] <= 6.5)
check("ids in order, include = review", [r["id"] for r in rows] == ["SH-001", "SH-002", "SH-003"] and all(r["include"] == "review" for r in rows))
check("24-in spot in South San Francisco", c["city"] == "South San Francisco" and c["watershed"] == "Colma Creek")

# Normally wet land comes out: a marsh over the east half of a flooded square, a diked bayland (kept) over the west half
import shoreline_exposure as E
from shapely.geometry import box as sbox, LineString, Point
half_e = sbox(-122.2700, 37.5140, -122.2680, 37.5160)
half_w = sbox(-122.2720, 37.5140, -122.2700, 37.5160)
hab = [("Tidal Marsh", half_e), ("Non-Aquatic Diked Bayland", half_w), ("Deep Subtidal", sbox(-122.20, 37.60, -122.19, 37.61))]
wet, tree = E.wet_mask(hab)
check("wet mask: marsh and Bay water in, diked bayland out", len(wet) == 2)
sq_all = sq(-122.270, 37.515, 150, "1.0")
masked, gone = E.remove_wet([sq_all], wet, tree)
mg = E.union_of(masked)
check("marsh half taken out, depth kept, about half the area left", masked and masked[0]["properties"]["DEPTH_FT"] == "1.0"
      and 0.40 < E.area_m2(mg) / E.area_m2(E.union_of([sq_all])) < 0.60 and 2.0 < gone < 3.6)
check("what's left is the west (land) side", mg.centroid.x < -122.2700)
pm, rm = H.prepare({12: [sq_all]}, wet, tree)
check("prepare(): wetland removed before the spots are made", rm[12] > 2 and E.area_m2(E.union_of(pm[12])) < E.area_m2(E.union_of([sq_all])) * 0.6)
wm = E.map_habitats(hab)
check("map layer: marsh drawn, open Bay water and diked land not", [f["properties"]["kind"] for f in wm["features"]] == ["Tidal Marsh"])

# Buildings and streets in a spot
spot = sbox(-122.2710, 37.5140, -122.2690, 37.5160)
blds = [(sbox(-122.2705, 37.5145, -122.2704, 37.5146), {}), (sbox(-122.2600, 37.5145, -122.2599, 37.5146), {})]
sts = [(LineString([(-122.2720, 37.5150), (-122.2680, 37.5150)]), {"FULLNAME": "MARINE  PKWY"}),
       (LineString([(-122.2600, 37.5100), (-122.2600, 37.5200)]), {"FULLNAME": "ELSEWHERE ST"})]
dv = E.Developed(blds, sts)
x = dv.in_spot(spot)
check("one building and about 177 m of Marine Pkwy in the spot", x["buildings"] == 1 and 170 < x["street_m"] < 185 and x["streets"] == ["Marine Pkwy"])
r0 = dict(b)
fx = H.add_exposure([r0], E.Developed([], []), {})
check("no buildings or streets: open land", r0["developed"] == "no" and r0["buildings"] == 0 and fx == [])
fx = H.add_exposure([r0], E.Developed([(sbox(-122.2701, 37.5149, -122.2700, 37.5150), {})], sts), {"SH-001": ["Fire Stations: Station 5"]})
check("a building and a street: developed, with map features and the facility listed",
      r0["developed"] == "yes" and r0["buildings"] == 1 and r0["street_mi"] > 0 and r0["assets"] == "Fire Stations: Station 5"
      and {f["properties"]["group"] for f in fx} == {"buildings", "streets"})
r1 = dict(b)
H.add_exposure([r1], E.Developed(None, None))
check("County data unavailable: developed left blank (unknown), not 'no'", r1["developed"] == "" and r1["buildings"] == "")


# RSAP: a web map with a group layer and a whole service, and the transport maps found by the owner's other items
def agol(url, params=None):
    u = url.split("?")[0]
    if u.endswith("/content/items/crit"):
        return json.dumps({"id": "crit", "type": "Web Map", "title": "Critical Infrastructure", "owner": "BCDC_GIS"})
    if u.endswith("/content/items/crit/data"):
        return json.dumps({"operationalLayers": [
            {"title": "Facilities", "layers": [{"title": "Fire Stations 2024", "url": "https://x.test/arcgis/rest/services/Fire/FeatureServer/0"},
                                               {"title": "Wastewater Exposure Summary", "url": "https://x.test/arcgis/rest/services/Sum/FeatureServer/0"}]},
            {"title": "Power", "url": "https://x.test/arcgis/rest/services/Power/FeatureServer"}]})
    if u == "https://x.test/arcgis/rest/services/Power/FeatureServer":
        return json.dumps({"layers": [{"id": 0, "name": "Power Plants"}, {"id": 1, "name": "Substations"}]})
    if u.endswith("/search"):
        q = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))["q"]
        assert 'owner:"BCDC_GIS"' in q and 'title:"transit"' in q
        return json.dumps({"results": [{"id": "trans", "type": "Feature Service", "title": "Transportation and Transit"},
                                       {"id": "doc", "type": "PDF", "title": "Transit memo"}]})
    if u.endswith("/content/items/trans"):
        return json.dumps({"id": "trans", "type": "Feature Service", "title": "Transportation and Transit", "owner": "BCDC_GIS",
                           "url": "https://x.test/arcgis/rest/services/Trans/FeatureServer"})
    if u == "https://x.test/arcgis/rest/services/Trans/FeatureServer":
        return json.dumps({"layers": [{"id": 3, "name": "Passenger Rail Lines"}]})
    if u.endswith("/query"):
        lay = u.rsplit("/", 2)[-2]
        if "Fire/FeatureServer" in u:
            return json.dumps({"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"FACNAME": "Station 5"}, "geometry": {"type": "Point", "coordinates": [-122.2705, 37.5150]}},
                {"type": "Feature", "properties": {"FACNAME": "Station 9"}, "geometry": {"type": "Point", "coordinates": [-122.2600, 37.5150]}}]})
        if "Trans/FeatureServer" in u:   # GeoJSON refused: Esri JSON
            if "f=geojson" in url:
                return json.dumps({"error": {"code": 400, "message": "Invalid format"}})
            return json.dumps({"features": [{"attributes": {"LINE_NAME": "Caltrain"}, "geometry": {"paths": [[[-122.2705, 37.5130], [-122.2705, 37.5170]]]}}]})
        return json.dumps({"type": "FeatureCollection", "features": []})
    raise OSError("unexpected " + url)


lays = E.find_rsap_layers(agol, items={"critical": ["crit"], "transport": []})
crit = [t for t, _ in lays["critical"]]
check("RSAP layers: group layers and whole services read, exposure summaries left out",
      crit == ["Fire Stations 2024", "Power Plants", "Substations"])
check("RSAP transport found by searching the same owner's items", [t for t, _ in lays["transport"]] == ["Passenger Rail Lines"])
afeats, by_spot = E.assets_in_spots(lays, [("SH-001", 12, spot)], H.BAY_BOX, agol)
names = sorted((f["properties"]["kind"], f["properties"]["name"]) for f in afeats)
check("facility in the spot kept, the one outside not; rail line clipped to the spot",
      names == [("Fire Stations", "Station 5"), ("Passenger Rail Lines", "Caltrain")]
      and by_spot["SH-001"] == ["Fire Stations: Station 5", "Passenger Rail Lines: Caltrain"])
rail = next(f for f in afeats if f["properties"]["kind"] == "Passenger Rail Lines")
check("rail length inside the spot only (about 222 m of 444 m)", 200 < rail["properties"]["len_m"] < 240)
check("kind_of tidies layer names", E.kind_of("RSAP_Fire_Stations_2024") == "Fire Stations" and E.kind_of("CEC Power Plants") == "Power Plants")

# County shapefile in State Plane feet, zipped (as the County exports it): read, put in lon/lat, only the box kept
import io, zipfile, shapefile
from pyproj import CRS, Transformer
to_sp = Transformer.from_crs("EPSG:4326", "EPSG:2227", always_xy=True)
with tempfile.TemporaryDirectory() as d:
    w = shapefile.Writer(os.path.join(d, "BUILDING_FOOTPRINTS"), shapeType=shapefile.POLYGON)
    w.field("BLDG_ID", "C")
    for lon, lat, bid in ((-122.2705, 37.5145, "in"), (-121.90, 37.30, "out")):
        ring = [to_sp.transform(x, y) for x, y in ((lon, lat), (lon, lat + 0.0001), (lon + 0.0001, lat + 0.0001), (lon + 0.0001, lat), (lon, lat))]
        w.poly([ring])
        w.record(bid)
    w.close()
    open(os.path.join(d, "BUILDING_FOOTPRINTS.prj"), "w").write(CRS.from_epsg(2227).to_wkt("WKT1_ESRI"))
    zb = io.BytesIO()
    with zipfile.ZipFile(zb, "w") as z:
        for ext in ("shp", "shx", "dbf", "prj"):
            z.write(os.path.join(d, "BUILDING_FOOTPRINTS." + ext), "BUILDING_FOOTPRINTS." + ext)
got = E.read_county_shapefile(zb.getvalue(), "BUILDING", H.BAY_BOX)
check("County shapefile (State Plane feet) read into lon/lat, only the shapes in the box",
      len(got) == 1 and got[0][1]["BLDG_ID"] == "in" and abs(got[0][0].centroid.x + 122.27045) < 0.00002)
check("Esri JSON polygon and point read", E.esri_geom({"rings": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}).area == 1 and E.esri_geom({"x": 1, "y": 2}).x == 1)


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
    H.write(rows, os.path.join(d, "x.csv"), os.path.join(d, "x.geojson"), exposure=fx + afeats, wet_map=wm,
            expo_path=os.path.join(d, "e.geojson"), wet_path=os.path.join(d, "w.geojson"))
    raw = open(os.path.join(d, "x.csv"), "rb").read()
    g = json.load(open(os.path.join(d, "x.geojson")))
    e = json.load(open(os.path.join(d, "e.geojson")))
    check("CSV with CRLF and the review and exposure columns", raw.startswith(b"id,name,city,watershed,lat,lon,level_in") and b"\r\n" in raw
          and b"developed,buildings,street_mi,streets,assets,include" in raw)
    check("GeoJSON with one feature per row", len(g["features"]) == 3 and g["features"][0]["properties"]["id"] == "SH-001")
    check("exposure and wetland files written", len(e["features"]) == 4 and os.path.exists(os.path.join(d, "w.geojson")))

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
