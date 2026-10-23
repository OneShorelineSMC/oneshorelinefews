"""
Checks for the static creek maps (scripts/build_creek_maps.py) with made-up shapes: no network.
Run from the repo:  python scripts/test_creek_maps.py
"""
import math
import re
import os
import sys
import urllib.parse
import xml.dom.minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_creek_maps as B  # noqa: E402

checks = 0


def check(cond, msg):
    global checks
    checks += 1
    assert cond, msg


def poly(cx, cy, r, name, n=48):
    pts = [[cx + r * 1.3 * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)] for i in range(n)]
    return {"type": "Feature", "properties": {"name": name, "huc12": "180500040000"}, "geometry": {"type": "Polygon", "coordinates": [pts + [pts[0]]]}}


creek = {"id": "test", "name": "Test Creek"}
gauge = (-122.4267, 37.6538)
line = [{"type": "Feature", "properties": {"gnis_name": "Test Creek"},
         "geometry": {"type": "LineString", "coordinates": [[-122.45 + i * 0.002, 37.69 - i * 0.0015] for i in range(30)]}}]
hu = [poly(-122.44, 37.67, 0.02, "Upper Test Creek"), poly(-122.30, 37.50, 0.02, "Far Away Creek")]
roads = [{"type": "Feature", "_primary": True, "properties": {"NAME": "US Hwy 101"},
          "geometry": {"type": "LineString", "coordinates": [[-122.40, 37.80], [-122.41, 37.50]]}}]
gauges = [{"label": "Stage Gauge", "kind": "stage", "lon": gauge[0], "lat": gauge[1]},
          {"label": "Stage Gauge", "kind": "rain", "lon": gauge[0], "lat": gauge[1]},
          {"label": "Hill & Ridge <Rain>", "kind": "support", "lon": -122.448, "lat": 37.692}]
svg, ws = B.build_svg(creek, line, hu, roads, gauges)
dom = xml.dom.minidom.parseString(svg)
check(dom.documentElement.getAttribute("viewBox").startswith("0 0 420 "), "drawn at phone width")
check(ws == ["Upper Test Creek"], f"the watershed is the subwatershed the creek runs through: {ws}")
check(svg.count(">Stage Gauge<") == 1, "a rain gauge at a creek gauge's site shares its one label")
check("Hill &amp; Ridge &lt;Rain&gt;" in svg, "labels are escaped")
check(">101<" in svg, "highway labeled the way people say it")
check(svg.count('class="ck"') >= 2, "creek line drawn (and in the legend)")
check("prefers-color-scheme: dark" in svg, "dark mode colors")
check(B.road_label("I- 280") == "I-280" and B.road_label("State Rte 92") == "Hwy 92" and B.road_label("El Camino Real") == "El Camino Real",
      "highway names")
ring = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
check(B.inside((5, 5), [ring]) and not B.inside((15, 5), [ring]), "point in polygon")
check(len(B.simplify([(0, 0), (5, 0.1), (10, 0)], 1)) == 2, "simplify drops a point within tolerance")
svg2, _ = B.build_svg(creek, [], [], [], [])
check(svg2 is None, "nothing to draw: no map")
svg3, _ = B.build_svg(creek, [], hu, roads, gauges[:1])
check(svg3 and 'class="ck"' not in svg3, "no creek line found: map without it (and no 'Creek' in the legend)")
# drainage area above the gauge (NLDI or data/creek_watersheds.geojson) replaces the HUC-12 shading and sets the extent
basin = poly(-122.44, 37.66, 0.015, "Stage Gauge")
svg4, ws4 = B.build_svg(creek, line, hu, roads, gauges, [basin])
check(ws4 == ["Stage Gauge"] and "Drains to the creek gauge" in svg4 and svg4.count('class="hu"') == 0, "basin shading, no HUC-12 units")
check("Watershed (USGS HUC-12)" in svg, "HUC-12 legend when there is no basin")
B.get = lambda url, params=None, tries=1: ('{"features":[{"properties":{"identifier":"77"}}]}' if "position" in url
                                  else '{"features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[-122.45,37.65],[-122.43,37.65],[-122.43,37.67],[-122.45,37.65]]]}}]}')
got = B.basins_for({"id": "t", "stages": [{"label": "A", "lon": -122.44, "lat": 37.66}, {"label": "B", "usgs_site": "11162630"}, {"label": "C"}]}, [])
check(len(got) == 2 and all(f["properties"]["source"] == "USGS NLDI" for f in got), f"NLDI: one basin per locatable level gauge: {len(got)}")
check(B.basins_for({"id": "t", "stages": []}, [{"type": "Feature", "properties": {"creek": "t"}, "geometry": basin["geometry"]}])[0]["properties"]["creek"] == "t",
      "data/creek_watersheds.geojson wins over NLDI")

cty = poly(-122.44, 37.66, 0.02, "Colma Creek"); cty["properties"]["source"] = "county"
got = B.basins_for({"id": "t", "stages": [{"label": "A", "lon": -122.44, "lat": 37.66}]}, [], [cty, poly(-122.3, 37.5, 0.02, "Elsewhere")])
check(len(got) == 1 and got[0]["properties"]["name"] == "Colma Creek", "County watershed containing the level gauge wins over NLDI")
sb = [poly(-122.42, 37.63, 0.02, "SAN BRUNO CREEK"), poly(-122.40, 37.62, 0.02, "EL ZANJON CREEK")]
got_sb = B.basins_for({"id": "sanbruno", "stages": [{"label": "First Avenue", "lon": -122.40, "lat": 37.62}]}, [], sb + [cty])
check(sorted(f["properties"]["name"] for f in got_sb) == ["EL ZANJON CREEK", "SAN BRUNO CREEK"],
      "COUNTY_WATERSHEDS: San Bruno Creek shades both its County watersheds, not just the one the gauge sits in")
svg5, _ = B.build_svg(creek, line, hu, roads, gauges, got)
check("Watershed (San Mateo County)" in svg5, "County watershed named in the legend")

# the Bay and cities (US Census): water drawn and named on the water, city limits dashed with a legend entry
bay = {"type": "Feature", "properties": {"NAME": "San Francisco Bay"},
       "geometry": {"type": "Polygon", "coordinates": [[[-122.42, 37.80], [-122.30, 37.80], [-122.30, 37.50], [-122.42, 37.50], [-122.42, 37.80]]]}}
city = {"type": "Feature", "city": True, "properties": {"NAME": "South San Francisco"},
        "geometry": {"type": "Polygon", "coordinates": [[[-122.50, 37.67], [-122.30, 37.67], [-122.30, 37.60], [-122.50, 37.60], [-122.50, 37.67]]]}}
town = {"type": "Feature", "city": False, "properties": {"NAME": "Broadmoor"},
        "geometry": {"type": "Polygon", "coordinates": [[[-122.50, 37.72], [-122.30, 37.72], [-122.30, 37.67], [-122.50, 37.67], [-122.50, 37.72]]]}}
svg6, _ = B.build_svg(creek, line, hu, roads, gauges, got, [bay], [city, town])
check('class="wa"' in svg6 and ">San Francisco Bay<" in svg6, "the Bay drawn and named")
check(">SOUTH SAN FRANCISCO<" in svg6 and svg6.count('class="cl"') == 2 and "City limit" in svg6,
      "city limits dashed (and in the legend), city named")
check(">BROADMOOR<" in svg6 and svg6.count('class="cl"') == 2, "an unincorporated town is named, with no boundary")
check("City limit" not in svg, "no city limit in the legend when there are none")

# creek line styles from NHD feature types: underground dotted, intermittent dashed, each in the legend only when drawn
def piece(ft, fc, x0):
    return {"type": "Feature", "properties": {"gnis_name": "Test Creek", "ftype": ft, "fcode": fc},
            "geometry": {"type": "LineString", "coordinates": [[x0 + i * 0.002, 37.66] for i in range(6)]}}
check([B.line_kind(piece(*a, 0)) for a in ((460, 46006), (460, 46003), (420, 42000), (336, 33600), (558, 55800))]
      == ["per", "int", "ug", "chan", "per"] and B.line_kind(line[0]) == "per", "line kinds from NHD FType/FCode")
svg7, _ = B.build_svg(creek, [piece(460, 46006, -122.45), piece(420, 42001, -122.438)], hu, roads, gauges)
check('stroke-dasharray="0.1 5"' in svg7 and "Creek underground (culvert or pipe)" in svg7 and "dry part of the year" not in svg7,
      "underground stretch dotted and in the legend; no dashed entry when none is drawn")
check(svg7.index('stroke-dasharray="0.1 5"') < svg7.index('stroke-width="3" stroke-linecap="round"'), "open creek draws over the culvert")

# a long label that fits on neither side of its marker goes under it, inside the map
lg = [{"label": "Below Crystal Springs Reservoir Spillway", "kind": "stage", "lon": -122.44, "lat": 37.66}]
svg8, _ = B.build_svg(creek, line, [], roads, lg)
m = re.search(r'x="([0-9.]+)" y="[0-9.]+" font-size="14"[^>]*>Below Crystal', svg8)
check(m and float(m.group(1)) >= 2 and float(m.group(1)) + 7.6 * len(lg[0]["label"]) <= 420, "long gauge label stays inside the map")

# over Esri's topographic base map: the image under the drawing, extent in Web Mercator matching the map's shape,
# no Census water or highways, no dark-mode recolouring, credited; a non-image answer means the plain map
asked = []
JPEG = b"\xff\xd8\xff\xe0" + b"0" * 40


def fake(url):
    asked.append(url)
    return JPEG


svg9, _ = B.build_svg(creek, line, hu, roads, gauges, basemap=lambda *a: B.basemap_image(*a, fetch=fake))
q = urllib.parse.parse_qs(urllib.parse.urlparse(asked[0]).query)
x0, y0, x1, y1 = map(float, q["bbox"][0].split(","))
pw, ph = map(int, q["size"][0].split(","))
vb = xml.dom.minidom.parseString(svg9).documentElement.getAttribute("viewBox").split()
check(asked[0].startswith(B.BASEMAP + "/export?") and q["imageSR"] == ["3857"] and q["f"] == ["image"] and pw == 840
      and abs(ph / pw - (y1 - y0) / (x1 - x0)) < 0.005 and abs(ph / pw - float(vb[3]) / float(vb[2])) < 0.01,
      "base map asked for this map's extent, twice its size, same shape")
check('<image href="data:image/jpeg;base64,' in svg9 and ">101<" not in svg9 and "prefers-color-scheme" not in svg9
      and "Base map: Esri" in svg9, "drawn over the base map; its own roads and names, credited")
check(B.basemap_image(-122.5, 37.6, -122.4, 37.7, 420, 320, fetch=lambda u: b'{"error":{"code":400}}') is None
      and "<image" not in B.build_svg(creek, line, hu, roads, gauges, basemap=lambda *a: None)[0], "no base map: the plain map")

# a creek line in two pieces (it goes underground): joined along NHD's unnamed culvert, drawn as underground
def ln(*pts, **pr):
    return {"type": "Feature", "properties": pr, "geometry": {"type": "LineString", "coordinates": [list(p) for p in pts]}}


upper = ln((-122.46, 37.62), (-122.44, 37.62))
lower = ln((-122.42, 37.625), (-122.40, 37.625))
nhd_all = [ln((-122.4399, 37.6201), (-122.43, 37.622), (-122.4201, 37.6249), ftype=420, fcode=42002),   # the culvert
           ln((-122.43, 37.622), (-122.43, 37.64), ftype=460, fcode=46006, gnis_name="Other Creek"),     # a side branch
           ln((-122.4201, 37.6249), (-122.40, 37.6251), ftype=460, fcode=46006)]                          # NHD's lower creek
gap = B.bridge_gaps([upper, lower], nhd_all)
check(len(gap) == 1 and B.line_kind(gap[0]) == "ug" and gap[0]["geometry"]["coordinates"][0] == [-122.44, 37.62]
      and gap[0]["geometry"]["coordinates"][-1] == [-122.42, 37.625] and len(B.pieces_of([upper, lower] + gap)) == 1,
      "a gap in the creek line joined along NHD's culvert, end to end, drawn as underground; the side branch left out")
check(B.bridge_gaps([upper], nhd_all) == [] and B.bridge_gaps([upper, ln((-122.30, 37.50), (-122.29, 37.50))], nhd_all) == [],
      "nothing added for a line in one piece, or pieces NHD doesn't join")
svg10, _ = B.build_svg(creek, [upper, lower] + gap, [], [], gauges)
check("Creek underground (culvert or pipe)" in svg10, "the culvert in the legend")

# NHD_DETAIL: side creeks (NHD and County, named or not) from the creek line, inside the watershed, longest first,
# keeping their own style (culvert = underground); lines outside the watershed and copies of the drawn line left out
wsq = [[[-122.48, 37.60], [-122.38, 37.60], [-122.38, 37.66], [-122.48, 37.66], [-122.48, 37.60]]]
lower_cty = ln((-122.42, 37.62), (-122.39, 37.63))                                         # the named creek
cands = [ln((-122.47, 37.645), (-122.45, 37.64), ftype=460, fcode=46006),                  # upper creek ...
         ln((-122.45, 37.64), (-122.42, 37.6201), ftype=420, fcode=42002),                 # ... down a culvert to the creek
         ln((-122.40, 37.655), (-122.401, 37.6265), NAME="", TYPE="Storm drain pipe", underground=True),   # north side creek (County)
         ln((-122.42, 37.6201), (-122.39, 37.6301), ftype=460, fcode=46006),               # NHD's copy of the drawn creek
         ln((-122.60, 37.70), (-122.47, 37.645), ftype=460, fcode=46006)]                  # from outside the watershed
nhd_net = cands[:2] + [ln((-122.40, 37.655), (-122.401, 37.6265), ftype=420, fcode=42002),   # pipe from the north
                       ln((-122.43, 37.650), (-122.4305, 37.6235), ftype=460, fcode=46006),   # doesn't reach the creek: left out
                       ln((-122.405, 37.652), (-122.40, 37.655), ftype=428, fcode=42800),     # a pipe feeding that pipe
                       ln((-122.46, 37.61), (-122.45, 37.61), ftype=420, fcode=42002)] + cands[3:]   # not connected: left out
ex = B.network_extras([lower_cty], nhd_net, [wsq])
xs = {round(f["geometry"]["coordinates"][0][0], 3) for f in ex}
check(all(f["properties"]["side"] for f in ex) and {B.line_kind(f) for f in ex} == {"ug", "per"} and -122.43 not in xs
      and -122.46 not in xs and -122.405 in xs and -122.6 not in xs,
      "side creeks, culverts and pipes connected to the creek inside the watershed; unconnected and outside lines left out")
svg11, _ = B.build_svg(creek, [lower_cty] + ex, [], [], gauges)
check(re.search(r'stroke-width="1\.4" stroke-dasharray="0\.1 5"', svg11) is not None, "side pipes drawn thinner, dotted")
check(B.county_underground({"NAME": "Pipe Creek", "TYPE": "Open channel"}) is False and B.county_underground({"TYPE": "Culvert"}),
      "County stream underground from its attributes, not its name")
# a stretch of the creek line along an NHD culvert is split off and drawn underground
cl = ln((-122.42, 37.62), (-122.41, 37.62), (-122.40, 37.62))
cv = [ln((-122.4151, 37.6201), (-122.4049, 37.6201), ftype=420, fcode=42002)]
mk, m = B.mark_underground([cl], cv)
check([B.line_kind(f) for f in mk] == ["per", "ug", "per"] and 850 <= m <= 950, f"culverted stretch of the creek line drawn underground ({m:.0f} m)")

print(f"creek maps: {checks} checks passed")
