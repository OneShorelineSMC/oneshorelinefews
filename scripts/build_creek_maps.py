#!/usr/bin/env python3
"""
Static creek maps for the Creeks page, and watershed boundaries for the sensor map's "Watersheds" switch.

Writes
  img/creekmaps/<creek>.svg   one small map per creek in lookups/creeks.csv: the creek line, the area draining to its
                              level gauge (USGS NLDI; or data/creek_watersheds.geojson when it has the creek), the creek's
                              gauges (creek level, rain, supporting rain) labeled as on the Creeks page, a north arrow and
                              a scale bar, over Esri's World Topographic Map (streets, the Bay and place names come from
                              it). If the base map can't be had, a plain map instead: the Bay, ocean and reservoirs and
                              the main highways (Census). No city limits or names. Shown at the bottom of each creek's page;
                              tapping it opens SiteMap.html zoomed to that creek.
  data/watersheds.geojson     USGS Watershed Boundary Dataset subwatersheds (HUC-12) covering San Mateo County, simplified,
                              with their names (SiteMap.html "Watersheds" switch; not the kiosk).

Sources (public, no keys; read when the script runs, so it runs on GitHub, not in the browser)
  Creek lines   USGS National Hydrography Dataset, Flowline - Large Scale (hydro.nationalmap.gov nhd/MapServer/6),
                matched by GNIS name (NHD_NAMES below); styled by NHD feature type (FType/FCode): flowing all year
                solid, intermittent or ephemeral dashed, canal or ditch thinner, underground conduit or pipeline
                (culverted) dotted and faded. San Mateo County's Streams and Creeks layer when NHD has no line
  Watersheds    USGS Watershed Boundary Dataset, 12-digit HU (hydro.nationalmap.gov wbd/FeatureServer/6)
  Highways      US Census TIGERweb, Census2020/Transportation: Primary Roads (2) and Secondary Roads (5)
  Water         US Census TIGERweb, Census2020/Hydro: Areal Hydrography (1): bays, ocean, lakes and reservoirs
  Base map      Esri World Topographic Map (services.arcgisonline.com World_Topo_Map, a static export per map;
                credited on the map and on the Creeks page)
  Gauges        OneRain sites in sites.json (data branch) by OneRain number; USGS gauges from USGS Water Services

Usage:  python scripts/build_creek_maps.py SITES_JSON     (GitHub: .github/workflows/creek_maps.yml, run by hand)
Only rebuild when a gauge is added or moved, or a creek is added. A creek whose name isn't in NHD gets a map without
the creek line (the script says so).
"""
import heapq
import json
import math
import time
import os
import sys
import urllib.parse
import urllib.request
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_config import CREEKS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "img", "creekmaps")
WATERSHEDS = os.path.join(ROOT, "data", "watersheds.geojson")
UA = {"User-Agent": "OneShoreline FEWS creek maps (github.com/OneShorelineSMC/oneshorelinefews)"}

COUNTY_BBOX = (-122.56, 37.10, -122.08, 37.72)   # San Mateo County plus a margin (lon, lat)
# San Mateo County's own watershed layer (the Flows to Bay watershed map; C/CAG's countywide stormwater program):
# creek-level watersheds, far finer than HUC-12. Public feature services on the County's ArcGIS Online.
COUNTY_WS = "https://services.arcgis.com/yq3FgOI44hYHAFVZ/arcgis/rest/services/Watersheds_Public_View/FeatureServer/0/query"
COUNTY_STREAMS = "https://services.arcgis.com/yq3FgOI44hYHAFVZ/arcgis/rest/services/Streams_Watersheds/FeatureServer/0/query"
WBD = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/FeatureServer/6/query"
NHD = "https://hydro.nationalmap.gov/arcgis/rest/services/nhd/MapServer/6/query"
ROADS = "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Transportation/MapServer/{}/query"
WATER = "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Hydro/MapServer/1/query"
PLACES = "https://tigerweb.geo.census.gov/arcgis/rest/services/Census2020/Places_CouSub_ConCity_SubMCD/MapServer/{}/query"
# bays and estuaries, ocean, lakes and ponds, reservoirs: big enough to see (square meters of water)
WATER_WHERE = "MTFCC IN ('H2051','H2053','H2030','H2040') AND AREAWATER > 40000"
# Esri World Topographic Map (a static export per creek map; credit on the map and on the Creeks page)
BASEMAP = "https://services.arcgisonline.com/arcgis/rest/services/World_Topo_Map/MapServer"
NWIS = "https://waterservices.usgs.gov/nwis/site/?format=rdb&siteStatus=all&sites={}"

# Creek names as NHD spells them (GNIS names). Add a name here if a creek's map comes out without its line.
NHD_NAMES = {
    "colma": ["Colma Creek"],
    # the upper creek is El Zanjon Creek in the County layers (staff, 2026-10-22)
    "sanbruno": ["San Bruno Creek", "El Zanjon Creek"],
    "belmont": ["Belmont Creek"],
    "atherton": ["Atherton Creek", "Atherton Channel"],
    "sanfrancisquito": ["San Francisquito Creek"],
    "sanmateo": ["San Mateo Creek"],
    # Green Hills Creek isn't named in NHD, the County layers or Millbrae's 2018 Storm Drain Master Plan; it runs
    # through Green Hills Country Club into storm drains at the course's east corner (42- and 48-inch, Master Plan
    # flooding problem #3) and on to Highline Canal / Highline Creek (County watershed HIGHLINE CREEK)
    "greenhills": ["Green Hills Creek", "Highline Creek", "Highline Canal"],
    "pilarcitos": ["Pilarcitos Creek"],
    "sangregorio": ["San Gregorio Creek"],
    "pescadero": ["Pescadero Creek"],
    "butano": ["Butano Creek"],
}
# Words to look for in the County streams layer's NAME when NHD has no line (default: the creek's name without "Creek")
COUNTY_STREAM_NAMES = {"greenhills": ["Green Hills", "Highline"], "sanbruno": ["San Bruno", "El Zanjon"]}
# County watersheds (WATERSHED names) that together drain to a creek's level gauge, when the one the gauge sits in isn't
# all of it. San Bruno Creek's First Avenue gauge sits on the line between SAN BRUNO CREEK and EL ZANJON CREEK (the
# upper creek), so the gauge's own watershed alone showed only part of the creek.
COUNTY_WATERSHEDS = {"sanbruno": ["SAN BRUNO CREEK", "EL ZANJON CREEK"]}


# ---------------------------------------------------------------- downloads
def get(url, params=None, tries=4):
    """GET with retries: the USGS map services sometimes drop a connection or time out."""
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read().decode("utf-8")
        except Exception as e:   # noqa: BLE001
            if k == tries - 1:
                raise
            wait = 10 * (k + 1)
            print(f"    (retrying in {wait} s: {type(e).__name__}: {str(e)[:80]})")
            time.sleep(wait)


def arcgis(url, where, fields, offset_deg, bbox=COUNTY_BBOX):
    """All features in the box (default: the county) as GeoJSON (lon/lat), simplified on the server, paging if needed."""
    feats, start = [], 0
    while True:
        p = {"where": where, "geometry": ",".join(map(str, bbox)), "geometryType": "esriGeometryEnvelope",
             "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": fields, "returnGeometry": "true",
             "outSR": 4326, "maxAllowableOffset": offset_deg, "geometryPrecision": 5, "resultOffset": start,
             "resultRecordCount": 1000, "f": "geojson"}
        d = json.loads(get(url, p))
        if "error" in d:
            raise RuntimeError(f"{url}: {d['error']}")
        feats += [f for f in d.get("features", []) if f.get("geometry") and (f["geometry"].get("coordinates"))]   # skip shapeless rows
        if not d.get("exceededTransferLimit") and not (d.get("properties") or {}).get("exceededTransferLimit"):
            return feats
        start += len(d.get("features", []))
        if not d.get("features"):
            return feats


def parse_rdb(text):
    """USGS RDB table -> list of dicts."""
    rows, head = [], None
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        if head is None:
            head = f
            continue
        if f and f[0].endswith("s") and f[0][:-1].isdigit():   # the "5s 15s ..." format line
            continue
        rows.append(dict(zip(head, f)))
    return rows


# ---------------------------------------------------------------- geometry helpers (lon, lat; no extra packages)
def lines_of(geom):
    geom = geom or {}
    t, c = geom.get("type"), geom.get("coordinates") or []
    return [c] if t == "LineString" else c if t == "MultiLineString" else []


def rings_of(geom):
    geom = geom or {}
    t, c = geom.get("type"), geom.get("coordinates") or []
    return c if t == "Polygon" else [r for poly in c for r in poly] if t == "MultiPolygon" else []


def polys_of(geom):
    geom = geom or {}
    t, c = geom.get("type"), geom.get("coordinates") or []
    return [c] if t == "Polygon" else c if t == "MultiPolygon" else []


def inside(pt, poly):
    """Point in a polygon with holes (even-odd over all rings)."""
    x, y, hit = pt[0], pt[1], False
    for ring in poly:
        for i in range(len(ring)):
            (x1, y1), (x2, y2) = ring[i - 1][:2], ring[i][:2]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                hit = not hit
    return hit


def simplify(pts, tol):
    """Douglas-Peucker on screen points."""
    if len(pts) < 3:
        return pts
    keep, stack = [False] * len(pts), [(0, len(pts) - 1)]
    keep[0] = keep[-1] = True
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by), dmax, idx = pts[a], pts[b], 0, None
        L = math.hypot(bx - ax, by - ay) or 1e-9
        for i in range(a + 1, b):
            d = abs((bx - ax) * (ay - pts[i][1]) - (ax - pts[i][0]) * (by - ay)) / L
            if d > dmax:
                dmax, idx = d, i
        if idx is not None and dmax > tol:
            keep[idx] = True
            stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]


# ---------------------------------------------------------------- one creek's map
W = 420   # drawn at about phone width, so its text stays readable (labels 14 px)
COL = {"water": "#cfe2f3", "wtx": "#3d6f9c", "city": "#8d96a0", "ctx": "#5d6b79", "bg": "#f4f7fa", "ws": "#e2eedf", "wsl": "#7fa278", "hu": "#c6d0da", "road": "#a3adb8", "road1": "#8a95a1",
       "creek": "#1e6fd9", "ink": "#16324a", "halo": "#ffffff", "stage": "#0A5587", "rain": "#5b6b7c"}
DARK = """@media (prefers-color-scheme: dark){.bg{fill:#121a22}.hu{stroke:#3a4652}.ws{fill:#1d2c22;stroke:#5f8a5a}
.rd{stroke:#5c6773}.rd1{stroke:#77828e}.ck{stroke:#6ea8fe}.t{fill:#e6edf5}.h{stroke:#121a22}.gs{fill:#6ea8fe;stroke:#121a22}
.gr{fill:#a3b0bd;stroke:#121a22}.wa{fill:#173049}.wt{fill:#86b2dc}.cl{stroke:#6c7783}.ct{fill:#a9b5c1}.gp{fill:#121a22;stroke:#a3b0bd}.na{fill:#e6edf5}.sb{stroke:#e6edf5}}"""


def basemap_image(lo0, la0, lo1, la1, w, h, fetch=None):
    """Esri World Topographic Map for this extent as a JPEG data URI, or None. Asked for in Web Mercator (the service's
    own projection) at twice the map's size and 192 dpi, so its labels stay sharp and readable; the image's shape
    matches the map's, so it lines up when stretched over it."""
    import base64
    def merc(lon, lat):
        return lon * 20037508.34 / 180, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137
    x0, y0 = merc(lo0, la0)
    x1, y1 = merc(lo1, la1)
    pw = 2 * w
    ph = max(1, round(pw * (y1 - y0) / (x1 - x0)))
    p = {"bbox": f"{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}", "bboxSR": 3857, "imageSR": 3857, "size": f"{pw},{ph}",
         "dpi": 192, "format": "jpg", "f": "image"}
    url = BASEMAP + "/export?" + urllib.parse.urlencode(p)
    try:
        if fetch:
            data = fetch(url)
        else:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                data = r.read()
    except Exception as e:   # noqa: BLE001
        print(f"    base map unavailable ({type(e).__name__}); the plain map instead")
        return None
    if not data or data[:3] != b"\xff\xd8\xff":   # not a JPEG (an error message)
        print("    base map service didn't return an image; the plain map instead")
        return None
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")


def build_svg(creek, line_feats, hu_feats, road_feats, gauges, basins=None, water=None, places=None, basemap=None):
    """creek: {"id","name"}; line_feats/hu_feats/road_feats: GeoJSON features (lon/lat);
    gauges: [{"label","kind": stage|rain|support,"lon","lat"}]; basins: GeoJSON polygons of the area draining to the
    creek's level gauges (NLDI or data/creek_watersheds.geojson), used instead of the HUC-12 units when given.
    water: Census areal water polygons (properties NAME); places: Census places (properties NAME, and "city": True for
    an incorporated city, whose limits are drawn; other places are only named).
    basemap: basemap_image-like function (lo0, la0, lo1, la1, w, h) -> data URI or None: when it gives an image, the map
    is drawn over it (Esri World Topographic Map) and the Bay, highways and their names come from it instead.
    Returns (svg text, watershed names)."""
    water, places = water or [], places or []
    styled = [(line_kind(f), ln) for f in line_feats for ln in lines_of(f["geometry"])]
    lines = [ln for _, ln in styled]
    probe = [p for ln in lines for p in ln[::3]] + [(g["lon"], g["lat"]) for g in gauges if g["kind"] != "support"]
    if basins:
        mine, hu_feats = basins, []   # the gauge's own drainage area; the HUC-12 units stay off the map
    else:   # the creek's subwatersheds: the ones its line or gauges are in, leaving out the open-Bay units (they span the Bay)
        mine = [f for f in hu_feats if not open_water(f) and
                any(any(inside(p, poly) for poly in polys_of(f["geometry"])) for p in probe)]
    # the map shows the creek and its gauges, plus the gauge's own drainage area when we have it
    # (a HUC-12 subwatershed can be much bigger than a small urban creek, so it never sets the extent)
    pts = [p for ln in lines for p in ln] + [(g["lon"], g["lat"]) for g in gauges] + \
          ([p for f in basins for r in rings_of(f["geometry"]) for p in r] if basins else [])
    if not pts:
        return None, []
    lo0, lo1 = min(p[0] for p in pts), max(p[0] for p in pts)
    la0, la1 = min(p[1] for p in pts), max(p[1] for p in pts)
    kx = math.cos(math.radians((la0 + la1) / 2))
    cx, cy, MIN = (lo0 + lo1) / 2, (la0 + la1) / 2, 0.04   # at least ~2.5 mi across (0.04 degrees of latitude)
    if (la1 - la0) < MIN:
        la0, la1 = cy - MIN / 2, cy + MIN / 2
    if (lo1 - lo0) * kx < MIN:
        lo0, lo1 = cx - MIN / 2 / kx, cx + MIN / 2 / kx
    wdeg, hdeg = (lo1 - lo0) * kx, la1 - la0
    pad = 0.15
    lo0, lo1 = lo0 - pad * wdeg / kx, lo1 + pad * wdeg / kx
    la0, la1 = la0 - pad * hdeg, la1 + pad * hdeg
    wdeg, hdeg = (lo1 - lo0) * kx, la1 - la0
    s = W / wdeg
    H = int(min(max(hdeg * s, 240), 520))
    if hdeg * s > 520:   # tall watershed: fit the height instead
        s = 520 / hdeg
    ox, oy = (W - wdeg * s) / 2, (H - hdeg * s) / 2

    def xy(p):
        return (ox + (p[0] - lo0) * kx * s, oy + (la1 - p[1]) * s)

    img = basemap(lo0 - ox / (kx * s), la1 - H / s + oy / s, lo0 + (W - ox) / (kx * s), la1 + oy / s, W, H) if basemap else None
    if img:   # the base map shows the Bay, roads and names itself
        water, road_feats, hu_feats = [], [], []

    def path(coords, closed=False, tol=0.6):
        q = [xy(p) for p in coords]
        if closed and len(q) > 3:   # a ring starts and ends on the same point: simplify its two halves
            m = len(q) // 2
            q = simplify(q[:m + 1], tol)[:-1] + simplify(q[m:], tol)
        else:
            q = simplify(q, tol)
        if len(q) < 2:
            return ""
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in q) + ("Z" if closed else "")

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
           f'aria-labelledby="t" font-family="Arial, Helvetica, sans-serif">',
           f"<title id=\"t\">{escape(creek['name'])}: creek, watershed and gauges</title>",
           f"<style>.t{{fill:{COL['ink']}}}.h{{stroke:{COL['halo']};stroke-width:3.5;stroke-linejoin:round;paint-order:stroke}}{'' if img else DARK}</style>",
           f'<defs><clipPath id="c"><rect width="{W}" height="{H}"/></clipPath></defs>',
           f'<rect class="bg" width="{W}" height="{H}" fill="{COL["bg"]}"/>', '<g clip-path="url(#c)">']
    if img:   # light in dark mode too: the photo-like base map stays as it is, so the drawing on it does as well
        out.append(f'<image href="{img}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="none"/>')
    # neighbouring subwatersheds (context), then this creek's, filled
    for f in hu_feats:
        if f in mine:
            continue
        d = "".join(path(r, True) for r in rings_of(f["geometry"]))
        if d:
            out.append(f'<path class="hu" d="{d}" fill="none" stroke="{COL["hu"]}" stroke-width="1"/>')
    for f in mine:
        d = "".join(path(r, True) for r in rings_of(f["geometry"]))
        if d:
            if img:   # see-through, so the streets and the Bay show; a darker green edge
                out.append(f'<path class="ws" d="{d}" fill="#4f9a45" fill-opacity="0.18" fill-rule="evenodd" stroke="#3f7a37" stroke-width="2"/>')
            else:
                out.append(f'<path class="ws" d="{d}" fill="{COL["ws"]}" fill-rule="evenodd" stroke="{COL["wsl"]}" stroke-width="1.2"/>')
    # the Bay, ocean and reservoirs, over the watershed shading so the shoreline shows
    for f in water:
        d = "".join(path(r, True, 0.5) for r in rings_of(f["geometry"]))
        if d:
            out.append(f'<path class="wa" d="{d}" fill="{COL["water"]}" fill-rule="evenodd"/>')
    # city limits (dashed)
    cities_drawn = False
    for f in places:
        if not f.get("city"):
            continue
        for r in rings_of(f["geometry"]):
            q = [xy(p) for p in r]
            if max(x for x, _ in q) < 0 or min(x for x, _ in q) > W or max(y for _, y in q) < 0 or min(y for _, y in q) > H:
                continue
            d = path(r, True, 0.6)
            if d:
                cities_drawn = True
                out.append(f'<path class="cl" d="{d}" fill="none" stroke="{COL["city"]}" stroke-width="1.2" stroke-dasharray="5 3"/>')
    # highways, then their labels (once per name, at the middle of its longest piece in view)
    best = {}
    for f in road_feats:
        primary = f.get("_primary")
        for ln in lines_of(f["geometry"]):
            d = path(ln, tol=0.8)
            if not d:
                continue
            cls, col, wd = ("rd1", COL["road1"], 2.4) if primary else ("rd", COL["road"], 1.5)
            out.append(f'<path class="{cls}" d="{d}" fill="none" stroke="{col}" stroke-width="{wd}" stroke-linecap="round"/>')
            name = road_label((f.get("properties") or {}).get("NAME") or "")
            if not primary and not (name.startswith("Hwy ") or name in ("El Camino Real", "Skyline Blvd", "Cabrillo Hwy")):
                name = ""   # other secondary roads: drawn, not labeled
            q = dense([xy(p) for p in ln], 8)
            vis = [p for p in q if 30 < p[0] < W - 30 and 30 < p[1] < H - 30]
            if name and len(vis) >= 2:
                L = sum(math.hypot(vis[i][0] - vis[i - 1][0], vis[i][1] - vis[i - 1][1]) for i in range(1, len(vis)))
                if L > best.get(name, (0,))[0] and L > 60:
                    best[name] = (L, vis[len(vis) // 2])
    # the creek
    kinds_drawn = set()
    for k in ("ug", "int", "chan", "per"):   # underground first, so the open creek draws over it
        for kk, ln in styled:
            if kk != k:
                continue
            d = path(ln, tol=0.5)
            if d:
                kinds_drawn.add(k)
                out.append(f'<path class="ck" d="{d}" fill="none" stroke="{COL["creek"]}" {LINE_STYLE[k]} stroke-linejoin="round"/>')
    out.append("</g>")
    # gauges: creek level = circle, rain = square, supporting rain = open square; a rain gauge at a creek gauge's spot
    # (same site) shows as a small square beside the circle, with one label
    # legend: only the symbols this map uses, in whichever corner covers the fewest gauges and least creek
    kinds = {g["kind"] for g in gauges}
    leg = [("ck", LINE_LABEL[k], k) for k in ("per", "int", "chan", "ug") if k in kinds_drawn]
    src = (mine[0].get("properties") or {}).get("source", "") if mine else ""
    leg += [("ws", "Watershed (San Mateo County)" if src == "county" else "Drains to the creek gauge" if basins else "Watershed (USGS HUC-12)", "w")] if mine else []
    leg += [("cl", "City limit", "l")] if cities_drawn else []
    leg += [("gs", "Creek level gauge", "c")] if "stage" in kinds else []
    leg += [("gr", "Rain gauge", "r")] if "rain" in kinds else []
    leg += [("gp", "Hillside rain gauge", "p")] if "support" in kinds else []
    lh = 16 * len(leg) + 6
    lwid = max(176, 32 + 6.4 * max((len(t) for _, t, _ in leg), default=0))   # fits the longest entry
    gpts = [xy((g["lon"], g["lat"])) for g in gauges]
    cpts = [xy(p) for ln in lines for p in ln]
    corners = [(14, 22), (int(W - lwid - 40), 22), (14, H - lh - 26), (int(W - lwid - 8), H - lh + 6)]   # TL, TR (clear of the N arrow), BL (above the scale), BR

    def cost(c):
        x0, y0, x1, y1 = c[0] - 8, c[1] - 13, c[0] - 8 + lwid, c[1] - 13 + lh
        x0 -= 10; x1 += 10   # gauge labels run beside their markers
        return 25 * sum(1 for x, y in gpts if x0 - 150 < x < x1 and y0 - 10 < y < y1 + 10) + sum(1 for x, y in cpts if x0 < x < x1 and y0 < y < y1)
    lx, ly = min(corners, key=cost)
    placed, spots = [], {}
    legend_box = (lx - 8, ly - 13, lx - 8 + lwid + 14, ly - 13 + lh)   # labels move off it
    for g in sorted(gauges, key=lambda g: {"stage": 0, "rain": 1, "support": 2}[g["kind"]]):
        spots.setdefault((round(g["lon"], 4), round(g["lat"], 4)), []).append(g)
    for gs in spots.values():
        g, kinds = gs[0], {x["kind"] for x in gs}
        x, y = xy((g["lon"], g["lat"]))
        if not (0 <= x <= W and 0 <= y <= H):
            continue
        if "stage" in kinds and kinds & {"rain", "support"}:
            out.append(f'<rect class="gr" x="{x - 15:.1f}" y="{y + 2:.1f}" width="10" height="10" fill="{COL["rain"]}" stroke="#fff" stroke-width="2"/>')
        if "stage" in kinds:
            out.append(f'<circle class="gs" cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{COL["stage"]}" stroke="#fff" stroke-width="2"/>')
        elif "rain" in kinds:
            out.append(f'<rect class="gr" x="{x - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" fill="{COL["rain"]}" stroke="#fff" stroke-width="2"/>')
        else:
            out.append(f'<rect class="gp" x="{x - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" fill="#fff" stroke="{COL["rain"]}" stroke-width="2.5"/>')
        lw = 7.6 * len(g["label"])
        # where the label can start: beside the marker (right, then left), or, when neither side has room, under
        # or over it, slid in from the map's edge
        under = min(max(4, x - lw / 2), W - 4 - lw)
        starts = [x + 11, x - 11 - lw]
        if not (x + 11 + lw < W - 4) and x - 11 - lw > 4:
            starts.reverse()

        def box(x0, ty):
            return (x0, ty - 13, x0 + lw, ty + 4)

        def free(x0, ty, others=True):   # inside the map and clear of the legend and earlier labels
            b = box(x0, ty)
            if b[0] < 2 or b[2] > W - 2 or b[1] < 2 or b[3] > H - 2:
                return False
            return not others or not any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in placed + [legend_box])
        tries = [(x0, y + 4 + dy) for dy in (0, 16, -16, 32, -32, 48, -48, 64) for x0 in starts]   # beside it, then nudged
        tries += [(under, y + 24), (under, y - 12), (under, y + 40), (under, y - 28)]
        x0, ty = next((t for t in tries if free(*t)), next((t for t in tries if free(*t, False)), tries[0]))   # never off the edge
        placed.append(box(x0, ty))
        out.append(f'<text class="t h" x="{x0:.1f}" y="{ty:.1f}" font-size="14" font-weight="700" '
                   f'text-anchor="start">{escape(g["label"])}</text>')
    # highway labels last, skipping any that would sit on another label
    boxes = [(b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3) for b in placed] + [legend_box]
    for name, (L, (x, y)) in sorted(best.items(), key=lambda kv: -kv[1][0]):
        w = 7.2 * len(name)
        b = (x - w / 2 - 3, y - 9, x + w / 2 + 3, y + 7)
        if any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in boxes):
            continue
        boxes.append(b)
        out.append(f'<text class="t h" x="{x:.0f}" y="{y:.0f}" font-size="12.5" font-weight="700" text-anchor="middle" dy="4">{escape(name)}</text>')
    # water and town names last, where they fit: inside their shape, clear of every other label, marker,
    # the legend, north arrow and scale bar
    boxes += [(x - 9, y - 9, x + 9, y + 9) for x, y in gpts]
    boxes += [legend_box, (W - 40, 6, W - 10, 54), (10, H - 32, 110, H - 6)]

    def spots_in(f):
        rings = [[xy(p) for p in r] for r in rings_of(f["geometry"])]
        polys = []
        for r in rings:   # outer rings with the holes that follow them
            if polys and inside(r[0], [polys[-1][0]]):
                polys[-1].append(r)
            else:
                polys.append([r])
        return [(x, y) for x in range(24, W - 23, 12) for y in range(20, H - 19, 12)
                if any(inside((x, y), pl) for pl in polys)]

    def area_label(spots, text, cls, col, size, italic):
        if len(spots) < 4:
            return
        mx, my = sum(p[0] for p in spots) / len(spots), sum(p[1] for p in spots) / len(spots)
        w = (6.4 if italic else 7.4) * len(text) * size / 12
        for x, y in sorted(spots, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2):
            b = (x - w / 2 - 3, y - size, x + w / 2 + 3, y + 5)
            if b[0] < 4 or b[2] > W - 4:
                continue
            if any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in boxes):
                continue
            if italic and not all(any(abs(sx - px) < 12 and abs(sy - py) < 12 for sx, sy in spots)
                                  for px, py in ((b[0] + 6, y - 3), (b[2] - 6, y - 3))):
                continue   # a water name stays on the water
            boxes.append(b)
            style = ' font-style="italic"' if italic else ' letter-spacing="0.6"'
            out.append(f'<text class="{cls} h" x="{x}" y="{y}" font-size="{size}" font-weight="700"{style} '
                       f'text-anchor="middle" fill="{col}">{escape(text)}</text>')
            return

    named = {}
    for f in water:   # one label per water body (the Bay comes in many pieces)
        n = ((f.get("properties") or {}).get("NAME") or "").strip()
        if n:
            named.setdefault(n, []).extend(spots_in(f))
    for n, sp in sorted(named.items(), key=lambda kv: -len(kv[1])):
        area_label(sp, n, "wt", COL["wtx"], 12.5 if len(sp) > 60 else 11.5, True)
    named = {}
    for f in places:
        n = ((f.get("properties") or {}).get("NAME") or "").strip()
        if n:
            named.setdefault(n, []).extend(spots_in(f))
    for n, sp in sorted(named.items(), key=lambda kv: -len(kv[1])):
        area_label(sp, n.upper(), "ct", COL["ctx"], 11, False)
    # north arrow and scale bar
    out.append(f'<g transform="translate({W - 26},26)"><path class="na" d="M0,-14 L7,8 L0,3 L-7,8Z" fill="{COL["ink"]}"/>'
               f'<text class="t" y="22" font-size="11" font-weight="700" text-anchor="middle">N</text></g>')
    mi_px = s / 69.0   # pixels per mile (1 degree of latitude ~ 69 mi)
    miles = next(m for m in (0.25, 0.5, 1, 2, 5, 10, 20) if m * mi_px >= 40)
    bx, by = 16, H - 16
    out.append(f'<g class="sb" stroke="{COL["ink"]}" stroke-width="2"><path class="sb" d="M{bx},{by - 5} V{by} H{bx + miles * mi_px:.0f} V{by - 5}" fill="none"/></g>'
               f'<text class="t h" x="{bx + miles * mi_px + 6:.0f}" y="{by}" font-size="12">{miles:g} mi</text>')
    # legend (placed above, in the emptiest corner)
    if leg:
        out.append(f'<rect class="bg" x="{lx - 8}" y="{ly - 13}" width="{lwid:.0f}" height="{lh}" rx="6" fill="{COL["bg"]}" opacity="0.92"/>')
    for i, (cls, txt, sym) in enumerate(leg):
        y = ly + 16 * i
        if sym in LINE_STYLE:
            out.append(f'<path class="ck" d="M{lx},{y - 4} h17" fill="none" stroke="{COL["creek"]}" {LINE_STYLE[sym]}/>')
        elif sym == "l":
            out.append(f'<path class="cl" d="M{lx},{y - 4} h16" stroke="{COL["city"]}" stroke-width="1.5" stroke-dasharray="5 3"/>')
        elif sym == "w":
            out.append(f'<rect class="ws" x="{lx + 2}" y="{y - 10}" width="13" height="12" fill="{"#d3e5cf" if img else COL["ws"]}" stroke="{"#3f7a37" if img else COL["wsl"]}" stroke-width="{2 if img else 1.2}"/>')
        elif sym == "c":
            out.append(f'<circle class="gs" cx="{lx + 8}" cy="{y - 4}" r="5.5" fill="{COL["stage"]}" stroke="#fff" stroke-width="1.5"/>')
        elif sym == "r":
            out.append(f'<rect class="gr" x="{lx + 3}" y="{y - 9}" width="10" height="10" fill="{COL["rain"]}" stroke="#fff" stroke-width="1.5"/>')
        else:
            out.append(f'<rect class="gp" x="{lx + 3}" y="{y - 9}" width="10" height="10" fill="#fff" stroke="{COL["rain"]}" stroke-width="2"/>')
        out.append(f'<text class="t" x="{lx + 22}" y="{y}" font-size="12">{txt}</text>')
    if img:
        out.append(f'<text class="t h" x="{W - 6}" y="{H - 6}" font-size="10" text-anchor="end">Base map: Esri</text>')
    out.append("</svg>")
    names = sorted({(f.get("properties") or {}).get("name") for f in mine} - {None, ""})
    return "\n".join(out) + "\n", names


# ---------------------------------------------------------------- gaps in a creek line
GAP_SNAP_M = 150    # a creek line's end this close to an NHD line joins it
GAP_MAX_M = 5000    # longest stretch of NHD line used to join two pieces of a creek


def _m(a, b):
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * 110540)


def pieces_of(line_feats, join_m=30):
    """The creek line's connected pieces: [[line coords, ...], ...] (ends within join_m count as joined)."""
    lines = [ln for f in line_feats for ln in lines_of(f.get("geometry")) if len(ln) >= 2]
    group = list(range(len(lines)))

    def root(i):
        while group[i] != i:
            group[i] = group[group[i]]
            i = group[i]
        return i
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            if any(_m(a, b) <= join_m for a in (lines[i][0], lines[i][-1]) for b in (lines[j][0], lines[j][-1])):
                group[root(i)] = root(j)
    out = {}
    for i, ln in enumerate(lines):
        out.setdefault(root(i), []).append(ln)
    return list(out.values())


def bridge_gaps(line_feats, nhd_feats, snap_m=GAP_SNAP_M, max_m=GAP_MAX_M):
    """Where a creek line comes in pieces (it goes underground, or the named lines stop), the NHD lines that join the
    pieces: often the culvert or pipe (NHD FType 420/428, usually unnamed). Shortest way along NHD lines from an end of
    one piece to an end of another; kept if no longer than max_m. Returns GeoJSON features (with NHD ftype/fcode, so the
    map styles a culvert as underground), [] if nothing joins."""
    parts = pieces_of(line_feats)
    if len(parts) < 2 or not nhd_feats:
        return []
    # NHD as a graph: every vertex a node (rounded to about 1 m), consecutive vertices an edge
    node = {}
    xy = []
    adj = {}
    edge_props = {}

    def nid(p):
        k = (round(p[0], 5), round(p[1], 5))
        if k not in node:
            node[k] = len(xy)
            xy.append(k)
        return node[k]
    for f in nhd_feats:
        pr = f.get("properties") or {}
        for ln in lines_of(f.get("geometry")):
            for a, b in zip(ln, ln[1:]):
                i, j = nid(a), nid(b)
                if i == j:
                    continue
                d = _m(a, b)
                adj.setdefault(i, []).append((j, d))
                adj.setdefault(j, []).append((i, d))
                edge_props[(min(i, j), max(i, j))] = pr
    if not xy:
        return []

    def nearest(p):
        i = min(range(len(xy)), key=lambda k: _m(p, xy[k]))
        return i if _m(p, xy[i]) <= snap_m else None
    ends = [[(nearest(p), p) for ln in part for p in (ln[0], ln[-1])] for part in parts]

    def shortest(src, dst_set):
        dist, prev, q = {src: 0.0}, {}, [(0.0, src)]
        while q:
            d, u = heapq.heappop(q)
            if u in dst_set:
                path = [u]
                while path[-1] != src:
                    path.append(prev[path[-1]])
                return d, path[::-1]
            if d > dist.get(u, 1e18) or d > max_m:
                continue
            for v, w in adj.get(u, []):
                if d + w < dist.get(v, 1e18):
                    dist[v], prev[v] = d + w, u
                    heapq.heappush(q, (d + w, v))
        return None
    # join the pieces one at a time, each time by the shortest NHD stretch between a joined piece and a new one
    joined, out = {0}, []
    while len(joined) < len(parts):
        best = None
        for a in joined:
            for b in range(len(parts)):
                if b in joined:
                    continue
                targets = {e: p for e, p in ends[b] if e is not None}
                for s, sp in ends[a]:
                    if s is None or not targets:
                        continue
                    r = shortest(s, set(targets))
                    if r:
                        d = r[0] + _m(sp, xy[s]) + _m(targets[r[1][-1]], xy[r[1][-1]])   # with the hops on and off NHD
                        if best is None or d < best[0]:
                            best = (d, r[1], b, sp, targets[r[1][-1]])
        if not best:
            break
        _, path, b, sp, tp = best
        joined.add(b)
        run, run_pr = [list(sp[:2])], None   # from the creek's end, one feature per stretch of the same NHD properties
        for u, v in zip(path, path[1:]):
            pr = edge_props.get((min(u, v), max(u, v)), {})
            if run_pr is not None and pr is not run_pr:
                out.append({"type": "Feature", "properties": dict(run_pr or {}, gap=True), "geometry": {"type": "LineString", "coordinates": run}})
                run = [run[-1]]
            if len(run) == 1 and run[0] != list(xy[u]):
                run.append(list(xy[u]))
            run.append(list(xy[v]))
            run_pr = pr
        run.append(list(tp[:2]))   # on to the other piece's end
        if len(run) >= 2:
            out.append({"type": "Feature", "properties": dict(run_pr or {}, gap=True), "geometry": {"type": "LineString", "coordinates": run}})
    return out


# Creeks whose named line stops short of the upper creek: NHD's main stem above it is added (often unnamed in NHD,
# with the culvert that joins it). San Bruno Creek: the upper creek in Crestmoor Canyon runs underground to the
# lower creek (staff, 2026-10-23).
EXTEND_UPSTREAM = {"sanbruno"}


def _seg_m(p, a, b):
    """Metres from point p to segment a-b (lon/lat)."""
    kx = 111320 * math.cos(math.radians(p[1]))
    px, py, ax, ay, bx, by = p[0] * kx, p[1] * 110540, a[0] * kx, a[1] * 110540, b[0] * kx, b[1] * 110540
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def _near_line(p, lines, m):
    return any(_seg_m(p, a, b) <= m for ln in lines for a, b in zip(ln, ln[1:]))


def extend_upstream(line_feats, nhd_feats, polys, near_m=60, skip_m=60, min_m=300):
    """NHD's longest way upstream from the creek line, inside the creek's watershed (polys) and away from the line
    already drawn: the upper creek, with any culvert on the way (NHD lines are drawn in the direction of flow).
    Returns GeoJSON features (with NHD ftype/fcode), [] if there is none at least min_m long."""
    lines = [ln for f in line_feats for ln in lines_of(f.get("geometry")) if len(ln) >= 2]
    if not lines or not nhd_feats:
        return []
    node, xy, up = {}, [], {}

    def nid(p):
        k = (round(p[0], 5), round(p[1], 5))
        if k not in node:
            node[k] = len(xy)
            xy.append(k)
        return node[k]
    ok = {}

    def inside_ws(i):
        if i not in ok:
            ok[i] = any(inside(xy[i], poly) for poly in polys)
        return ok[i]
    for f in nhd_feats:
        pr = f.get("properties") or {}
        for ln in lines_of(f.get("geometry")):
            for a, b in zip(ln, ln[1:]):
                i, j = nid(a), nid(b)
                if i != j:
                    up.setdefault(j, []).append((i, _m(a, b), pr))   # flows i -> j
    near = {i: _near_line(xy[i], lines, skip_m) for i in range(len(xy))}
    best_len, best_up = {}, {}

    def longest(v):   # longest way up from v (iterative, NHD has no loops but guard anyway)
        stack, seen = [(v, False)], set()
        while stack:
            u, done = stack.pop()
            if u in best_len:
                continue
            ups = [(w, d, pr) for w, d, pr in up.get(u, []) if inside_ws(w) and not (near[w] and near[u])]
            if not done:
                if u in seen:
                    best_len[u] = 0.0
                    continue
                seen.add(u)
                stack.append((u, True))
                stack += [(w, False) for w, _, _ in ups if w not in best_len]
                continue
            b = (0.0, None)
            for w, d, pr in ups:
                L = d + best_len.get(w, 0.0)
                if L > b[0]:
                    b = (L, (w, pr))
            best_len[u], best_up[u] = b
        return best_len[v]
    starts = [i for i in range(len(xy)) if inside_ws(i) and _near_line(xy[i], lines, near_m)]
    if not starts:
        return []
    s0 = max(starts, key=longest)
    if best_len[s0] < min_m:
        return []
    out, run, run_pr, u = [], [list(xy[s0])], None, s0
    while best_up.get(u):
        w, pr = best_up[u]
        if run_pr is not None and pr is not run_pr:
            out.append({"type": "Feature", "properties": dict(run_pr, upper=True), "geometry": {"type": "LineString", "coordinates": run}})
            run = [run[-1]]
        run.append(list(xy[w]))
        run_pr, u = pr, w
    if len(run) >= 2:
        out.append({"type": "Feature", "properties": dict(run_pr or {}, upper=True), "geometry": {"type": "LineString", "coordinates": run}})
    return out


# creek line styles by NHD feature type
LINE_STYLE = {"per": 'stroke-width="3" stroke-linecap="round"',
              "int": 'stroke-width="2.6" stroke-dasharray="7 4" stroke-linecap="butt"',
              "chan": 'stroke-width="2" stroke-linecap="round"',
              "ug": 'stroke-width="2.4" stroke-dasharray="0.1 5" stroke-linecap="round" opacity="0.6"'}
LINE_LABEL = {"per": "Creek", "int": "Creek, dry part of the year", "chan": "Canal or ditch",
              "ug": "Creek underground (culvert or pipe)"}


def line_kind(f):
    """NHD FType/FCode -> line style. Lines without them (County streams) draw as a creek."""
    pr = f.get("properties") or {}
    ft, fc = pr.get("ftype"), pr.get("fcode")
    try:
        ft, fc = int(ft), int(fc or 0)
    except (TypeError, ValueError):
        return "per"
    if ft in (420, 428):
        return "ug"
    if ft == 336:
        return "chan"
    if ft == 460 and fc in (46003, 46007):
        return "int"
    return "per"   # flowing all year, artificial paths through lakes and wide channels, connectors


def dense(q, step):
    """Points every `step` pixels along a screen line (so a long straight road still has points in view)."""
    out = q[:1]
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        out += [(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) for i in range(1, n + 1)]
    return out


def open_water(f):
    """The open-Bay subwatersheds ('San Francisco Bay Estuaries-Frontal San Francisco Bay', 'Oakland Inner Harbor-...')."""
    n = ((f.get("properties") or {}).get("name") or "")
    return n.startswith("San Francisco Bay") or "Inner Harbor" in n


def road_label(n):
    """TIGER names -> what people call them: 'US Hwy 101' -> '101', 'I- 280' -> 'I-280', 'State Rte 92' -> 'Hwy 92',
    'S el Camino Real' -> 'El Camino Real'."""
    n = n.strip()
    n = n[2:] if n[:2] in ("N ", "S ", "E ", "W ") else n
    n = n[:1].upper() + n[1:]
    if n.startswith("US Hwy "):
        return n[7:]
    if n.startswith("I- "):
        return "I-" + n[3:]
    if n.startswith("State Rte "):
        return "Hwy " + n[10:]
    return n


# ---------------------------------------------------------------- drainage area above each creek level gauge
NLDI = "https://api.water.usgs.gov/nldi/linked-data"
OVERRIDE = os.path.join(ROOT, "data", "creek_watersheds.geojson")   # optional: {"creek": "<id>"} per polygon, wins over NLDI


def nldi_basin(g):
    """The area draining to a gauge, from USGS NLDI: a USGS gauge by its site number, otherwise the NHDPlus flowline
    nearest the gauge, with the catchment split at the gauge. Returns a GeoJSON feature or None."""
    if g.get("usgs_site"):
        src = f"nwissite/USGS-{g['usgs_site']}"
    else:
        d = json.loads(get(f"{NLDI}/comid/position", {"coords": f"POINT({g['lon']} {g['lat']})"}, tries=2))
        feats = d.get("features") or []
        if not feats:
            return None
        src = "comid/" + str((feats[0].get("properties") or {}).get("identifier") or feats[0]["properties"].get("comid"))
    d = json.loads(get(f"{NLDI}/{src}/basin", {"simplified": "false", "splitCatchment": "true"}, tries=2))
    feats = d.get("features") or []
    if not feats or not feats[0].get("geometry"):
        return None
    f = feats[0]
    f["properties"] = {"name": g.get("label") or "", "source": "USGS NLDI", "gauge": g.get("usgs_site") or g.get("number")}
    return f


def basins_for(c, override, county=()):
    """Polygons to shade for a creek, first that works: data/creek_watersheds.geojson if it has this creek; the County
    watersheds named in COUNTY_WATERSHEDS; the County watershed(s) a creek level gauge sits in; NLDI's drainage area above each level gauge (biggest first, so nested
    areas draw in order). [] if none works; the map then falls back to HUC-12."""
    mine = [f for f in override if (f.get("properties") or {}).get("creek") == c["id"]]
    if mine:
        return mine
    want = {n.upper() for n in COUNTY_WATERSHEDS.get(c["id"], [])}
    mine = [f for f in county if ((f.get("properties") or {}).get("name") or "").upper() in want]
    if mine:
        return mine
    pts = [(g["lon"], g["lat"]) for g in c.get("stages", []) if "lon" in g]
    mine = [f for f in county if any(any(inside(p, poly) for poly in polys_of(f["geometry"])) for p in pts)]
    if mine:
        return mine
    out = []
    for g in c.get("stages", []):
        if "lon" not in g and not g.get("usgs_site"):
            continue
        try:
            f = nldi_basin(g)
        except Exception as e:   # noqa: BLE001
            print(f"  {c['id']}: NLDI failed for {g.get('label')}: {e}")
            continue
        if f:
            out.append(f)
        else:
            print(f"  {c['id']}: NLDI has no basin for {g.get('label')} ({g.get('usgs_site') or g.get('number')})")
    def area(f):
        return sum(abs(sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1))) for r in rings_of(f["geometry"]))
    return sorted(out, key=area, reverse=True)


# ---------------------------------------------------------------- main
def gauges_for(c, onerain, usgs):
    out, seen = [], set()
    roles = [("stage", g) for g in c.get("stages", [])] + [("rain", g) for g in c.get("rain", [])] + \
            [("support", g) for g in c.get("rain_support", [])]
    for kind, g in roles:
        pt = None
        if g.get("source") == "usgs" and g.get("usgs_site") in usgs:
            pt = usgs[g["usgs_site"]]
        elif str(g.get("number")) in onerain:
            pt = onerain[str(g["number"])]
        if not pt:
            print(f"  {c['id']}: no location for {g.get('label')} ({g.get('number') or g.get('usgs_site')})")
            continue
        key = (round(pt[0], 4), round(pt[1], 4), kind if kind == "stage" else "rain")
        if key in seen:
            continue
        seen.add(key)
        out.append({"label": g.get("label") or g.get("site_name"), "kind": kind, "lon": pt[0], "lat": pt[1]})
    return out


def main():
    sites_path = sys.argv[1] if len(sys.argv) > 1 else "sites.json"
    with open(sites_path) as f:
        onerain = {str(s["number"]): (s["lon"], s["lat"]) for s in json.load(f).get("sites", []) if s.get("lat") is not None}
    usgs_ids = {g["usgs_site"] for c in CREEKS for g in c.get("stages", []) + c.get("rain", []) + c.get("rain_support", [])
                if g.get("usgs_site")}
    usgs = {}
    if usgs_ids:
        for r in parse_rdb(get(NWIS.format(",".join(sorted(usgs_ids))))):
            try:
                usgs[r["site_no"]] = (float(r["dec_long_va"]), float(r["dec_lat_va"]))
            except (KeyError, ValueError):
                pass
    print(f"{len(onerain)} OneRain sites, {len(usgs)} of {len(usgs_ids)} USGS gauges located")

    county = []
    try:   # the County's creek-level watersheds (Flows to Bay map); names in WATERSHED
        for f in arcgis(COUNTY_WS, "1=1", "WATERSHED", 0.0002):
            f["properties"] = {"name": (f.get("properties") or {}).get("WATERSHED") or "", "source": "county"}
            county.append(f)
        print(f"{len(county)} County watersheds (San Mateo County / C/CAG)")
    except Exception as e:   # noqa: BLE001
        print(f"County watershed layer unavailable ({e}); using USGS")
    try:
        hu = arcgis(WBD, "1=1", "huc12,name", 0.0004)
        print(f"{len(hu)} subwatersheds (HUC-12)")
    except Exception as e:   # noqa: BLE001
        hu = []
        print(f"USGS HUC-12 unavailable ({type(e).__name__}); not needed where the County layer covers the gauge")
    names = sorted({n for v in NHD_NAMES.values() for n in v})
    where = "gnis_name IN (" + ",".join("'" + n.replace("'", "''") + "'" for n in names) + ")"
    nhd_ok = True
    try:
        flow = arcgis(NHD, where, "gnis_name,ftype,fcode", 0.00015)
        print(f"{len(flow)} creek line pieces (USGS NHD)")
    except Exception as e:   # noqa: BLE001
        flow, nhd_ok = [], False
        print(f"USGS NHD unavailable ({type(e).__name__}); creek lines from the County streams layer instead")
    roads = []
    for layer, primary in ((2, True), (5, False)):
        try:
            for f in arcgis(ROADS.format(layer), "1=1", "NAME,MTFCC", 0.0004):
                f["_primary"] = primary
                roads.append(f)
        except Exception as e:   # noqa: BLE001
            print(f"Census highways (layer {layer}) unavailable ({type(e).__name__}); maps without them")
    print(f"{len(roads)} highway pieces")
    water = []
    try:
        water = arcgis(WATER, WATER_WHERE, "NAME,MTFCC", 0.0002)
    except Exception as e:   # noqa: BLE001
        print(f"Census water layer unavailable ({type(e).__name__}); maps without the Bay")
    print(f"{len(water)} water polygons (Bay, ocean, reservoirs)")
    places = []
    for layer, city in ((4, True), (5, False)):
        try:
            for f in arcgis(PLACES.format(layer), "1=1", "BASENAME", 0.0002):
                f["properties"] = {"NAME": (f.get("properties") or {}).get("BASENAME") or ""}
                f["city"] = city
                places.append(f)
        except Exception as e:   # noqa: BLE001
            print(f"Census places (layer {layer}) unavailable ({type(e).__name__}); maps without them")
    print(f"{sum(1 for f in places if f['city'])} cities, {sum(1 for f in places if not f['city'])} unincorporated places")

    override = []
    if os.path.exists(OVERRIDE):
        with open(OVERRIDE) as f:
            override = json.load(f).get("features", [])
        print(f"data/creek_watersheds.geojson: {len(override)} polygons (used before NLDI)")

    os.makedirs(OUT_DIR, exist_ok=True)
    failed = []
    for c in CREEKS:
        try:   # one creek's problem never stops the others (or the watershed file)
            want = set(NHD_NAMES.get(c["id"], []))
            line = [f for f in flow if (f.get("properties") or {}).get("gnis_name") in want]
            if not line:   # County streams layer by name (Flows to Bay map)
                try:
                    words = COUNTY_STREAM_NAMES.get(c["id"]) or [c["name"].replace(" Channel", "").replace(" Creek", "")]
                    q = " OR ".join("NAME LIKE '%" + w.replace("'", "''") + "%'" for w in words)
                    line = arcgis(COUNTY_STREAMS, q, "NAME", 0.00015)
                    if not line:   # the named stream closest to the creek's level gauges (within about 400 m)
                        near = {}
                        for g in gauges_for(c, onerain, usgs):
                            if g["kind"] != "stage":
                                continue
                            d = 0.004
                            for f in arcgis(COUNTY_STREAMS, "NAME IS NOT NULL AND NAME <> ''", "NAME", 0.0002,
                                            (g["lon"] - d, g["lat"] - d, g["lon"] + d, g["lat"] + d)):
                                n = (f.get("properties") or {}).get("NAME")
                                gd = min(math.hypot(p[0] - g["lon"], p[1] - g["lat"]) for ln in lines_of(f["geometry"]) for p in ln)
                                near[n] = min(near.get(n, 9), gd)
                        if near:
                            pick = min(near, key=near.get)
                            print(f"  {c['id']}: County streams has no {words}; the stream nearest its gauge is '{pick}'"
                                  " (add it to COUNTY_STREAM_NAMES)")
                            line = arcgis(COUNTY_STREAMS, "NAME = '" + pick.replace("'", "''") + "'", "NAME", 0.00015)
                    if line:
                        print(f"  {c['id']}: creek line from the County streams layer ({len(line)} pieces)")
                except Exception as e:   # noqa: BLE001
                    print(f"  {c['id']}: County streams lookup failed: {e}")
            if not line and nhd_ok:   # NHD spells it differently: use the named stream(s) right at the creek's level gauges
                near = {}
                for g in gauges_for(c, onerain, usgs):
                    if g["kind"] != "stage":
                        continue
                    d = 0.0025   # about 250 m
                    box = (g["lon"] - d, g["lat"] - d, g["lon"] + d, g["lat"] + d)
                    try:
                        for f in arcgis(NHD, "gnis_name IS NOT NULL", "gnis_name", 0.0002, box):
                            n = (f.get("properties") or {}).get("gnis_name")
                            if n:
                                near[n] = near.get(n, 0) + 1
                    except Exception as e:   # noqa: BLE001
                        print(f"  {c['id']}: NHD lookup near {g['label']} failed: {e}")
                if near:
                    pick = max(near, key=near.get)
                    print(f"  {c['id']}: NHD has no {sorted(want)}; the stream at its gauge is '{pick}' (add it to NHD_NAMES)")
                    q = "gnis_name = '" + pick.replace("'", "''") + "'"
                    line = arcgis(NHD, q, "gnis_name,ftype,fcode", 0.00015)
            if not line:
                print(f"  {c['id']}: no NHD creek line for {sorted(want) or '(no name set)'}; map without it")
            if line and nhd_ok and c["id"] in EXTEND_UPSTREAM:   # the upper creek from NHD (EXTEND_UPSTREAM)
                try:
                    ws_polys = [poly for f in basins_for(c, override, county) for poly in polys_of(f["geometry"])]
                    pts = [p for poly in ws_polys for p in poly[0]] or [p for f in line for ln in lines_of(f["geometry"]) for p in ln]
                    box = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
                    upper = extend_upstream(line, arcgis(NHD, "1=1", "gnis_name,ftype,fcode", 0.00005, box), ws_polys)
                    if upper:
                        L = sum(_m(a, b) for f in upper for a, b in zip(f["geometry"]["coordinates"], f["geometry"]["coordinates"][1:]))
                        ug = sum(_m(a, b) for f in upper if line_kind(f) == "ug" for a, b in zip(f["geometry"]["coordinates"], f["geometry"]["coordinates"][1:]))
                        names = sorted({(f["properties"].get("gnis_name") or "(unnamed)") for f in upper})
                        print(f"  {c['id']}: upper creek from NHD, {L / 1000:.1f} km ({ug / 1000:.1f} km underground): {', '.join(names)}")
                        line = line + upper
                    else:
                        print(f"  {c['id']}: no NHD line above the creek line inside its watershed")
                except Exception as e:   # noqa: BLE001
                    print(f"  {c['id']}: upper creek lookup failed ({type(e).__name__}: {e})")
            if line and len(pieces_of(line)) > 1 and nhd_ok:   # in pieces: join them along NHD (the culverts, mostly unnamed)
                try:
                    pts = [p for f in line for ln in lines_of(f["geometry"]) for p in ln]
                    d = 0.01
                    box = (min(p[0] for p in pts) - d, min(p[1] for p in pts) - d, max(p[0] for p in pts) + d, max(p[1] for p in pts) + d)
                    gap = bridge_gaps(line, arcgis(NHD, "1=1", "gnis_name,ftype,fcode", 0.00005, box))
                    if gap:
                        line = line + gap
                        ug = sum(1 for f in gap if line_kind(f) == "ug")
                        print(f"  {c['id']}: {len(pieces_of(line))} piece(s) after joining gaps along NHD ({len(gap)} NHD lines, {ug} underground)")
                    else:
                        print(f"  {c['id']}: creek line in {len(pieces_of(line))} pieces; no NHD line joins them")
                except Exception as e:   # noqa: BLE001
                    print(f"  {c['id']}: joining the creek line's gaps failed ({type(e).__name__}: {e})")
            gs = gauges_for(c, onerain, usgs)
            for g in c.get("stages", []):   # NLDI needs each level gauge's location
                for x in gs:
                    if x["kind"] == "stage" and x["label"] == (g.get("label") or g.get("site_name")):
                        g["lon"], g["lat"] = x["lon"], x["lat"]
            basins = basins_for(c, override, county)
            svg, ws = build_svg(c, line, hu, roads, gs, basins, water, [], basemap=basemap_image)   # no city limits or names (staff, 2026-10-23)
            if not svg:
                print(f"  {c['id']}: nothing to draw; skipped")
                continue
            with open(os.path.join(OUT_DIR, c["id"] + ".svg"), "w", encoding="utf-8") as f:
                f.write(svg)
            how = "" if not basins else (basins[0].get("properties") or {}).get("source", "")
            print(f"  {c['id']}: {len(svg) // 1024} KB; " + ("County watershed: " if how == "county" else "drains to gauge (NLDI): " if how == "USGS NLDI" else "creek_watersheds.geojson: " if basins else "HUC-12: ") + (", ".join(ws) or "-"))

        except Exception as e:   # noqa: BLE001
            failed.append(c["id"])
            print(f"  {c['id']}: FAILED ({type(e).__name__}: {e}); its old map is kept")
    # watershed boundaries for the sensor map switch: the County's creek watersheds when available, else HUC-12
    os.makedirs(os.path.dirname(WATERSHEDS), exist_ok=True)
    use = county or hu
    if not use:
        print("No watershed boundaries this run; data/watersheds.geojson left as it was")
        return
    fc = {"type": "FeatureCollection", "source": "San Mateo County watersheds (C/CAG, Flows to Bay)" if county else "USGS Watershed Boundary Dataset (WBD), 12-digit HU",
          "features": [{"type": "Feature", "properties": {"name": (f.get("properties") or {}).get("name"),
                                                          "huc12": (f.get("properties") or {}).get("huc12")},
                        "geometry": f["geometry"]} for f in use]}
    with open(WATERSHEDS, "w", encoding="utf-8") as f:
        json.dump(fc, f, separators=(",", ":"))
    print(f"data/watersheds.geojson: {len(use)} watersheds ({fc['source']}), {os.path.getsize(WATERSHEDS) // 1024} KB")
    if failed:
        print(f"Maps not rebuilt: {', '.join(failed)} (see above)")


if __name__ == "__main__":
    main()
