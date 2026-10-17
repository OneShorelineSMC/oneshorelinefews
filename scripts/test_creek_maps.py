"""
Checks for the static creek maps (scripts/build_creek_maps.py) with made-up shapes: no network.
Run from the repo:  python scripts/test_creek_maps.py
"""
import math
import os
import sys
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
print(f"creek maps: {checks} checks passed")
