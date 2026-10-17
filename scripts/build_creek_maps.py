#!/usr/bin/env python3
"""
Static creek maps for the Creeks page, and watershed boundaries for the sensor map's "Watersheds" switch.

Writes
  img/creekmaps/<creek>.svg   one small map per creek in lookups/creeks.csv: the creek line, the area draining to its
                              level gauge (USGS NLDI; or data/creek_watersheds.geojson when it has the creek), the creek's
                              gauges (creek level, rain, supporting rain) labeled as on the Creeks page, the main
                              highways, a north arrow and a scale bar. Shown at the bottom of each creek's page;
                              tapping it opens SiteMap.html zoomed to that creek.
  data/watersheds.geojson     USGS Watershed Boundary Dataset subwatersheds (HUC-12) covering San Mateo County, simplified,
                              with their names (SiteMap.html "Watersheds" switch; not the kiosk).

Sources (public, no keys; read when the script runs, so it runs on GitHub, not in the browser)
  Creek lines   USGS National Hydrography Dataset, Flowline - Large Scale (hydro.nationalmap.gov nhd/MapServer/6),
                matched by GNIS name (NHD_NAMES below)
  Watersheds    USGS Watershed Boundary Dataset, 12-digit HU (hydro.nationalmap.gov wbd/FeatureServer/6)
  Highways      US Census TIGERweb, Census2020/Transportation: Primary Roads (2) and Secondary Roads (5)
  Gauges        OneRain sites in sites.json (data branch) by OneRain number; USGS gauges from USGS Water Services

Usage:  python scripts/build_creek_maps.py SITES_JSON     (GitHub: .github/workflows/creek_maps.yml, run by hand)
Only rebuild when a gauge is added or moved, or a creek is added. A creek whose name isn't in NHD gets a map without
the creek line (the script says so).
"""
import json
import math
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
NWIS = "https://waterservices.usgs.gov/nwis/site/?format=rdb&siteStatus=all&sites={}"

# Creek names as NHD spells them (GNIS names). Add a name here if a creek's map comes out without its line.
NHD_NAMES = {
    "colma": ["Colma Creek"],
    "sanbruno": ["San Bruno Creek"],
    "belmont": ["Belmont Creek"],
    "atherton": ["Atherton Creek", "Atherton Channel"],
    "sanfrancisquito": ["San Francisquito Creek"],
    "sanmateo": ["San Mateo Creek"],
    "greenhills": ["Green Hills Creek"],
    "pilarcitos": ["Pilarcitos Creek"],
    "sangregorio": ["San Gregorio Creek"],
    "pescadero": ["Pescadero Creek"],
}


# ---------------------------------------------------------------- downloads
def get(url, params=None):
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        return r.read().decode("utf-8")


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
        feats += d.get("features", [])
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
    t, c = geom.get("type"), geom.get("coordinates") or []
    return [c] if t == "LineString" else c if t == "MultiLineString" else []


def rings_of(geom):
    t, c = geom.get("type"), geom.get("coordinates") or []
    return c if t == "Polygon" else [r for poly in c for r in poly] if t == "MultiPolygon" else []


def polys_of(geom):
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
COL = {"bg": "#f4f7fa", "ws": "#e2eedf", "wsl": "#7fa278", "hu": "#c6d0da", "road": "#a3adb8", "road1": "#8a95a1",
       "creek": "#1e6fd9", "ink": "#16324a", "halo": "#ffffff", "stage": "#0A5587", "rain": "#5b6b7c"}
DARK = """@media (prefers-color-scheme: dark){.bg{fill:#121a22}.hu{stroke:#3a4652}.ws{fill:#1d2c22;stroke:#5f8a5a}
.rd{stroke:#5c6773}.rd1{stroke:#77828e}.ck{stroke:#6ea8fe}.t{fill:#e6edf5}.h{stroke:#121a22}.gs{fill:#6ea8fe;stroke:#121a22}
.gr{fill:#a3b0bd;stroke:#121a22}.gp{fill:#121a22;stroke:#a3b0bd}.na{fill:#e6edf5}.sb{stroke:#e6edf5}}"""


def build_svg(creek, line_feats, hu_feats, road_feats, gauges, basins=None):
    """creek: {"id","name"}; line_feats/hu_feats/road_feats: GeoJSON features (lon/lat);
    gauges: [{"label","kind": stage|rain|support,"lon","lat"}]; basins: GeoJSON polygons of the area draining to the
    creek's level gauges (NLDI or data/creek_watersheds.geojson), used instead of the HUC-12 units when given.
    Returns (svg text, watershed names)."""
    lines = [ln for f in line_feats for ln in lines_of(f["geometry"])]
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
           f"<style>.t{{fill:{COL['ink']}}}.h{{stroke:{COL['halo']};stroke-width:3.5;stroke-linejoin:round;paint-order:stroke}}{DARK}</style>",
           f'<defs><clipPath id="c"><rect width="{W}" height="{H}"/></clipPath></defs>',
           f'<rect class="bg" width="{W}" height="{H}" fill="{COL["bg"]}"/>', '<g clip-path="url(#c)">']
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
            out.append(f'<path class="ws" d="{d}" fill="{COL["ws"]}" fill-rule="evenodd" stroke="{COL["wsl"]}" stroke-width="1.2"/>')
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
    for ln in lines:
        d = path(ln, tol=0.5)
        if d:
            out.append(f'<path class="ck" d="{d}" fill="none" stroke="{COL["creek"]}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append("</g>")
    # gauges: creek level = circle, rain = square, supporting rain = open square; a rain gauge at a creek gauge's spot
    # (same site) shows as a small square beside the circle, with one label
    placed, spots = [], {}
    legend_box = (0, 0, 190, 22 + 16 * 5)   # the legend (top left) is drawn later; labels move below it
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
        right = x < W - 150
        ty = y + 4
        lx0 = x + 11 if right else x - 11 - 7 * len(g["label"])
        for _ in range(6):   # nudge a label down if another label or the legend sits on top of it
            if any(abs(ty - py) < 15 and abs(x - px) < 150 for px, py in placed) or \
               (ty - 12 < legend_box[3] and lx0 < legend_box[2]):
                ty += 16
        placed.append((x, ty))
        out.append(f'<text class="t h" x="{x + (11 if right else -11):.1f}" y="{ty:.1f}" font-size="14" font-weight="700" '
                   f'text-anchor="{"start" if right else "end"}">{escape(g["label"])}</text>')
    # highway labels last, skipping any that would sit on another label
    boxes = [(px - 4, py - 13, px + 150, py + 4) for px, py in placed]
    for name, (L, (x, y)) in sorted(best.items(), key=lambda kv: -kv[1][0]):
        w = 7.2 * len(name)
        b = (x - w / 2 - 3, y - 9, x + w / 2 + 3, y + 7)
        if any(b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3] for o in boxes):
            continue
        boxes.append(b)
        out.append(f'<text class="t h" x="{x:.0f}" y="{y:.0f}" font-size="12.5" font-weight="700" text-anchor="middle" dy="4">{escape(name)}</text>')
    # north arrow and scale bar
    out.append(f'<g transform="translate({W - 26},26)"><path class="na" d="M0,-14 L7,8 L0,3 L-7,8Z" fill="{COL["ink"]}"/>'
               f'<text class="t" y="22" font-size="11" font-weight="700" text-anchor="middle">N</text></g>')
    mi_px = s / 69.0   # pixels per mile (1 degree of latitude ~ 69 mi)
    miles = next(m for m in (0.25, 0.5, 1, 2, 5, 10, 20) if m * mi_px >= 40)
    bx, by = 16, H - 16
    out.append(f'<g class="sb" stroke="{COL["ink"]}" stroke-width="2"><path class="sb" d="M{bx},{by - 5} V{by} H{bx + miles * mi_px:.0f} V{by - 5}" fill="none"/></g>'
               f'<text class="t h" x="{bx + miles * mi_px + 6:.0f}" y="{by}" font-size="12">{miles:g} mi</text>')
    # legend, bottom right: only the symbols this map uses
    kinds = {g["kind"] for g in gauges}
    leg = [("ck", "Creek", None)] if lines else []
    src = (mine[0].get("properties") or {}).get("source", "") if mine else ""
    leg += [("ws", "Watershed (San Mateo County)" if src == "county" else "Drains to the creek gauge" if basins else "Watershed (USGS HUC-12)", "w")] if mine else []
    leg += [("gs", "Creek level gauge", "c")] if "stage" in kinds else []
    leg += [("gr", "Rain gauge", "r")] if "rain" in kinds else []
    leg += [("gp", "Hillside rain gauge", "p")] if "support" in kinds else []
    lx, ly = 14, 22
    if leg:
        out.append(f'<rect class="bg" x="{lx - 8}" y="{ly - 13}" width="176" height="{16 * len(leg) + 6}" rx="6" fill="{COL["bg"]}" opacity="0.92"/>')
    for i, (cls, txt, sym) in enumerate(leg):
        y = ly + 16 * i
        if sym is None:
            out.append(f'<path class="ck" d="M{lx},{y - 4} h16" stroke="{COL["creek"]}" stroke-width="3" stroke-linecap="round"/>')
        elif sym == "w":
            out.append(f'<rect class="ws" x="{lx + 2}" y="{y - 10}" width="13" height="12" fill="{COL["ws"]}" stroke="{COL["wsl"]}" stroke-width="1.2"/>')
        elif sym == "c":
            out.append(f'<circle class="gs" cx="{lx + 8}" cy="{y - 4}" r="5.5" fill="{COL["stage"]}" stroke="#fff" stroke-width="1.5"/>')
        elif sym == "r":
            out.append(f'<rect class="gr" x="{lx + 3}" y="{y - 9}" width="10" height="10" fill="{COL["rain"]}" stroke="#fff" stroke-width="1.5"/>')
        else:
            out.append(f'<rect class="gp" x="{lx + 3}" y="{y - 9}" width="10" height="10" fill="#fff" stroke="{COL["rain"]}" stroke-width="2"/>')
        out.append(f'<text class="t" x="{lx + 22}" y="{y}" font-size="12">{txt}</text>')
    out.append("</svg>")
    names = sorted({(f.get("properties") or {}).get("name") for f in mine} - {None, ""})
    return "\n".join(out) + "\n", names


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
        d = json.loads(get(f"{NLDI}/comid/position", {"coords": f"POINT({g['lon']} {g['lat']})"}))
        feats = d.get("features") or []
        if not feats:
            return None
        src = "comid/" + str((feats[0].get("properties") or {}).get("identifier") or feats[0]["properties"].get("comid"))
    d = json.loads(get(f"{NLDI}/{src}/basin", {"simplified": "false", "splitCatchment": "true"}))
    feats = d.get("features") or []
    if not feats or not feats[0].get("geometry"):
        return None
    f = feats[0]
    f["properties"] = {"name": g.get("label") or "", "source": "USGS NLDI", "gauge": g.get("usgs_site") or g.get("number")}
    return f


def basins_for(c, override, county=()):
    """Polygons to shade for a creek, first that works: data/creek_watersheds.geojson if it has this creek; the County
    watershed(s) a creek level gauge sits in; NLDI's drainage area above each level gauge (biggest first, so nested
    areas draw in order). [] if none works; the map then falls back to HUC-12."""
    mine = [f for f in override if (f.get("properties") or {}).get("creek") == c["id"]]
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
    hu = arcgis(WBD, "1=1", "huc12,name", 0.0004)
    print(f"{len(hu)} subwatersheds (HUC-12)")
    names = sorted({n for v in NHD_NAMES.values() for n in v})
    where = "gnis_name IN (" + ",".join("'" + n.replace("'", "''") + "'" for n in names) + ")"
    flow = arcgis(NHD, where, "gnis_name", 0.00015)
    print(f"{len(flow)} creek line pieces")
    roads = []
    for layer, primary in ((2, True), (5, False)):
        for f in arcgis(ROADS.format(layer), "1=1", "NAME,MTFCC", 0.0004):
            f["_primary"] = primary
            roads.append(f)
    print(f"{len(roads)} highway pieces")

    override = []
    if os.path.exists(OVERRIDE):
        with open(OVERRIDE) as f:
            override = json.load(f).get("features", [])
        print(f"data/creek_watersheds.geojson: {len(override)} polygons (used before NLDI)")

    os.makedirs(OUT_DIR, exist_ok=True)
    for c in CREEKS:
        want = set(NHD_NAMES.get(c["id"], []))
        line = [f for f in flow if (f.get("properties") or {}).get("gnis_name") in want]
        if not line:   # County streams layer by name (Flows to Bay map)
            try:
                q = "NAME LIKE '%" + c["name"].replace("'", "''").replace(" Channel", "").replace(" Creek", "") + "%'"
                line = arcgis(COUNTY_STREAMS, q, "NAME", 0.00015)
                if line:
                    print(f"  {c['id']}: creek line from the County streams layer ({len(line)} pieces)")
            except Exception as e:   # noqa: BLE001
                print(f"  {c['id']}: County streams lookup failed: {e}")
        if not line:   # NHD spells it differently: use the named stream(s) right at the creek's level gauges
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
                line = arcgis(NHD, q, "gnis_name", 0.00015)
        if not line:
            print(f"  {c['id']}: no NHD creek line for {sorted(want) or '(no name set)'}; map without it")
        gs = gauges_for(c, onerain, usgs)
        for g in c.get("stages", []):   # NLDI needs each level gauge's location
            for x in gs:
                if x["kind"] == "stage" and x["label"] == (g.get("label") or g.get("site_name")):
                    g["lon"], g["lat"] = x["lon"], x["lat"]
        basins = basins_for(c, override, county)
        svg, ws = build_svg(c, line, hu, roads, gs, basins)
        if not svg:
            print(f"  {c['id']}: nothing to draw; skipped")
            continue
        with open(os.path.join(OUT_DIR, c["id"] + ".svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        how = "" if not basins else (basins[0].get("properties") or {}).get("source", "")
        print(f"  {c['id']}: {len(svg) // 1024} KB; " + ("County watershed: " if how == "county" else "drains to gauge (NLDI): " if how == "USGS NLDI" else "creek_watersheds.geojson: " if basins else "HUC-12: ") + (", ".join(ws) or "-"))

    # watershed boundaries for the sensor map switch: the County's creek watersheds when available, else HUC-12
    os.makedirs(os.path.dirname(WATERSHEDS), exist_ok=True)
    use = county or hu
    fc = {"type": "FeatureCollection", "source": "San Mateo County watersheds (C/CAG, Flows to Bay)" if county else "USGS Watershed Boundary Dataset (WBD), 12-digit HU",
          "features": [{"type": "Feature", "properties": {"name": (f.get("properties") or {}).get("name"),
                                                          "huc12": (f.get("properties") or {}).get("huc12")},
                        "geometry": f["geometry"]} for f in use]}
    with open(WATERSHEDS, "w", encoding="utf-8") as f:
        json.dump(fc, f, separators=(",", ":"))
    print(f"data/watersheds.geojson: {len(use)} watersheds ({fc['source']}), {os.path.getsize(WATERSHEDS) // 1024} KB")


if __name__ == "__main__":
    main()
