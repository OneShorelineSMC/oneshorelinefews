"""Shoreline hotspots: a draft list of the places on San Mateo County's Bay shoreline where BCDC's Adapting to Rising
Tides (ART) maps show the Bay coming over the shoreline at the lowest water levels: 12, 24 and 36 inches above MHHW.

Run by hand on GitHub (Actions > Build shoreline hotspots > Run workflow); this workspace can't reach the map services.
Writes, for staff review:
  lookups/proposed/shoreline_hotspots.csv           one row per candidate spot (the Shoreline tab reads it, marked Draft,
                                                     until staff save a reviewed copy as lookups/shoreline_hotspots.csv)
  data/shoreline_hotspots_candidates.geojson        the flooded areas behind each row, simplified (the Shoreline tab's map)

Source: BCDC ART Bay Area Sea Level Rise and Shoreline Analysis Maps (2017; 1 m USGS/NOAA lidar 2010-11, locally
reviewed), as published in Caltrans' public map service DEA_BCDC_polygon_SLR (one layer per water level, e.g.
"BCDC SLR 2.0 ft (24 in)"). ART's water levels are a total water level above *local* MHHW (sea level rise plus a storm
surge, or either alone), so a spot's level is compared with how far the Bay is above MHHW at the tide gauge, not with
a NAVD88 height. Still water only: no waves. See lookups/THRESHOLDS_BASIS.md §4c.

Normally wet land (the Bay, tidal marsh, mudflats, ponds, channels, beaches: SFEI Baylands Habitat Map 2020) is taken
out first: water there at a high tide is normal. Each level's spots are only the land that floods at that level and not
lower down (so a 24 in spot is the ground the water adds between 12 and 24 in). Each candidate: those pieces at one
level that lie within MERGE_M of each other, kept if at least MIN_ACRES. Named after the Census city it's in (or
nearest) and the County watershed (C/CAG) around it; staff rename, merge, trim and mark include = yes/no.

What is in each spot (scripts/shoreline_exposure.py): San Mateo County building footprints and streets (a spot with a
building or a street is "developed", the rest open land), and BCDC's RSAP critical facilities and transportation.
Also writes data/shoreline_exposure.geojson (those buildings, streets and facilities, for the map) and
data/shoreline_baylands.geojson (marsh, mudflats and ponds, drawn faintly on the map).

Usage: python scripts/build_shoreline_hotspots.py
"""

import csv
import functools
import time
import json
import math
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creek_maps as M  # noqa: E402  (get, arcgis, polys_of, inside, PLACES; no side effects on import)
import shoreline_exposure as E  # noqa: E402
import shapely  # noqa: E402

ROOT = os.path.dirname(HERE)
SERVICE = "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHhqenvi/DEA_BCDC_polygon_SLR/MapServer"
BAY_BOX = (-122.43, 37.44, -122.08, 37.72)    # San Mateo County's Bay side, with a margin (lon, lat)
LEVELS_IN = (12, 24, 36)                       # ART water levels above MHHW used here (the pages only ever reach the lowest)
MIN_ACRES = 0.5                                # smaller flooded patches are left out
MERGE_M = 250                                  # pieces at one level closer than this are one spot
OFFSETS = (0.00003, 0.0001, 0.0003)           # outline detail asked for (degrees), simplest last
MIN_PIECE_ACRES = 0.05                         # pieces smaller than this are dropped before grouping
WS_NEAR_M = 600                                # a spot this close to a San Mateo County watershed counts as in the county
OUT_CSV = os.path.join(ROOT, "lookups", "proposed", "shoreline_hotspots.csv")
OUT_GEO = os.path.join(ROOT, "data", "shoreline_hotspots_candidates.geojson")
OUT_EXPO = os.path.join(ROOT, "data", "shoreline_exposure.geojson")
OUT_WET = os.path.join(ROOT, "data", "shoreline_baylands.geojson")
WATERSHEDS = os.path.join(ROOT, "data", "watersheds.geojson")
COLUMNS = ["id", "name", "city", "watershed", "lat", "lon", "level_in", "area_acres", "max_depth_ft", "pieces",
           "developed", "buildings", "street_mi", "streets", "assets", "include", "notes", "source", "checked_by", "checked_on"]
SOURCE = "BCDC Adapting to Rising Tides maps (2017), Caltrans DEA_BCDC_polygon_SLR; wetlands removed (SFEI Baylands Habitat Map 2020)"


# ---------------------------------------------------------------- geometry (lon, lat degrees; small areas)
def _m_per_deg(lat):
    return 111320 * math.cos(math.radians(lat)), 110540


def ring_area_m2(ring):
    if len(ring) < 3:
        return 0.0
    lat0 = sum(p[1] for p in ring) / len(ring)
    kx, ky = _m_per_deg(lat0)
    s = 0.0
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i - 1][:2], ring[i][:2]
        s += (x1 * kx) * (y2 * ky) - (x2 * kx) * (y1 * ky)
    return abs(s) / 2


def poly_area_m2(poly):   # outer ring minus holes
    return max(0.0, ring_area_m2(poly[0]) - sum(ring_area_m2(r) for r in poly[1:]))


def centroid(poly):
    ring = poly[0]
    return (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))


def dist_m(a, b):
    kx, ky = _m_per_deg((a[1] + b[1]) / 2)
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * ky)


def bbox(poly):
    xs = [p[0] for p in poly[0]]
    ys = [p[1] for p in poly[0]]
    return min(xs), min(ys), max(xs), max(ys)


def near_poly(pt, poly, within_m):
    """True if pt is inside the polygon or within_m of one of its outer-ring vertices."""
    if M.inside(pt, poly):
        return True
    return any(dist_m(pt, q) <= within_m for q in poly[0][:: max(1, len(poly[0]) // 400)])


def depth(props):
    try:
        return float(re.findall(r"-?\d+(?:\.\d+)?", str(props.get("DEPTH_FT") or ""))[-1])
    except (IndexError, ValueError):
        return None


# ---------------------------------------------------------------- downloads
# The same Caltrans service answers on two host names; the job tries each until one works.
SERVICES = [SERVICE, "https://geodata.dot.ca.gov/arcgis/rest/services/CHhqenvi/DEA_BCDC_polygon_SLR/MapServer"]


def fetch_json(url, get=M.get):
    """JSON from a map service, with a clear message when it sends an error or a web page instead."""
    text = get(url)
    try:
        d = json.loads(text)
    except ValueError:
        raise RuntimeError(f"not JSON from {url.split('?')[0]}: {text[:200]!r}")
    if isinstance(d, dict) and d.get("error"):
        raise RuntimeError(f"{url.split('?')[0]}: {d['error']}")
    return d


def layers(get=M.get):
    """{inches: layer id} from the service's layer names ("BCDC SLR 2.0 ft (24 in)"); uses the first host that answers."""
    global SERVICE
    for base in SERVICES:
        try:
            j = fetch_json(base + "?f=json", get)
        except Exception as e:   # noqa: BLE001
            print(f"  {base}: {type(e).__name__}: {str(e)[:300]}")
            continue
        out = {}
        for lyr in j.get("layers") or []:
            m = re.search(r"\((\d+)\s*in\)", lyr.get("name") or "")
            if m:
                out[int(m.group(1))] = lyr["id"]
        if out:
            SERVICE = base
            return out
        print(f"  {base}: no layers named like '(24 in)'; its layers are: " + "; ".join(f"{l.get('id')} {l.get('name')}" for l in j.get("layers") or []))
    return {}


def esri_to_geojson(feat):
    """An Esri JSON polygon feature as GeoJSON: clockwise rings are outer rings, the counter-clockwise ones after them holes."""
    polys = []
    for ring in (feat.get("geometry") or {}).get("rings") or []:
        if len(ring) < 4:
            continue
        signed = sum(ring[i - 1][0] * ring[i][1] - ring[i][0] * ring[i - 1][1] for i in range(len(ring)))
        if signed < 0 or not polys:
            polys.append([ring])
        else:
            polys[-1].append(ring)
    return {"type": "Feature", "properties": feat.get("attributes") or {},
            "geometry": {"type": "MultiPolygon", "coordinates": polys} if polys else None}


def features(layer_id, get=M.get):
    """Flooded polygons in BAY_BOX for one layer, as GeoJSON features (lon/lat), fetched by object id in batches.
    Asks for GeoJSON; if the service can't give it, asks for Esri JSON and converts."""
    q = SERVICE + f"/{layer_id}/query"
    common = {"geometry": ",".join(map(str, BAY_BOX)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
              "spatialRel": "esriSpatialRelIntersects", "where": "1=1"}
    ids = fetch_json(q + "?" + urllib.parse.urlencode(dict(common, returnIdsOnly="true", f="json")), get).get("objectIds") or []
    # The layers hold a few very large shapes (about 20 in the box), so each shape is asked for on its own, and when the
    # server can't send it (HTTP 500, too big) it is asked for again with a simpler outline (OFFSETS, degrees: about 3, 10, 30 m).
    out, state = [], {"fmt": "geojson"}
    g1 = (lambda u: M.get(u, tries=1)) if get is M.get else get   # one try per outline; the simpler outline is the retry

    def one(oid, offset):
        p = {"objectIds": str(oid), "outFields": "OBJECTID,DEPTH_FT", "returnGeometry": "true",
             "outSR": 4326, "maxAllowableOffset": offset, "geometryPrecision": 6}
        if state["fmt"] == "geojson":
            try:
                d = fetch_json(q + "?" + urllib.parse.urlencode(dict(p, f="geojson")), g1)
                if d.get("type") != "FeatureCollection":
                    raise RuntimeError("no FeatureCollection")
                return [f for f in d.get("features", []) if f.get("geometry")]
            except RuntimeError as e:   # the service answered but can't do GeoJSON: use Esri JSON from now on
                print(f"  layer {layer_id}: GeoJSON not available ({str(e)[:120]}); using Esri JSON")
                state["fmt"] = "json"
        d = fetch_json(q + "?" + urllib.parse.urlencode(dict(p, f="json")), g1)
        return [g for g in (esri_to_geojson(f) for f in d.get("features", [])) if g["geometry"]]

    for oid in ids:
        last = None
        for offset in OFFSETS:
            try:
                out += one(oid, offset)
                last = None
                break
            except Exception as e:   # noqa: BLE001 - usually HTTP 500 for a shape too big to send in detail
                last = e
                print(f"  layer {layer_id}, shape {oid}: {type(e).__name__} at outline {offset}°; trying simpler")
        if last is not None:
            raise RuntimeError(f"shape {oid} couldn't be read even at the simplest outline: {last}")
    return out


# ---------------------------------------------------------------- candidates
def pieces_of(feats, level):
    out = []
    for f in feats:
        dep = depth(f.get("properties") or {})
        for poly in M.polys_of(f["geometry"]):
            if not poly or len(poly[0]) < 4:
                continue
            a = poly_area_m2(poly)
            if a <= 0:
                continue
            out.append({"poly": poly, "area": a, "c": centroid(poly), "box": bbox(poly), "depth": dep, "level": level})
    return out


def cluster(pieces):
    """Pieces closer than MERGE_M (centroid to centroid, or one inside the other's box) form one group."""
    parent = list(range(len(pieces)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    cell = MERGE_M / 111000 * 1.4   # grid cells about MERGE_M across: only pieces in neighbouring cells can be close
    grid = {}
    for i, p in enumerate(pieces):
        grid.setdefault((int(p["c"][0] // cell), int(p["c"][1] // cell)), []).append(i)
    for i, a in enumerate(pieces):
        gx, gy = int(a["c"][0] // cell), int(a["c"][1] // cell)
        near = [j for dx in (-1, 0, 1) for dy in (-1, 0, 1) for j in grid.get((gx + dx, gy + dy), []) if j > i]
        for j in near:
            if dist_m(a["c"], pieces[j]["c"]) <= MERGE_M:
                parent[find(i)] = find(j)
    # a piece whose centre lies inside another piece's box joins it (big pieces with small ones inside them)
    big = sorted(range(len(pieces)), key=lambda k: -pieces[k]["area"])[:200]
    for i in big:
        bx = pieces[i]["box"]
        for j, b in enumerate(pieces):
            if j != i and bx[0] <= b["c"][0] <= bx[2] and bx[1] <= b["c"][1] <= bx[3]:
                parent[find(i)] = find(j)
    groups = {}
    for i, p in enumerate(pieces):
        groups.setdefault(find(i), []).append(p)
    return list(groups.values())


def _in_box(pt, box, pad_deg=0.0004):
    return box[0] - pad_deg <= pt[0] <= box[2] + pad_deg and box[1] - pad_deg <= pt[1] <= box[3] + pad_deg


def candidates(by_level, watersheds, places):
    """by_level: {inches: [GeoJSON features]}, each level only the land that floods there and not lower (prepare()),
    -> rows (dicts) and their polygons, lowest level first."""
    rows = []
    for level in sorted(by_level):
        new = [p for p in pieces_of(by_level[level], level)
               if p["area"] >= MIN_PIECE_ACRES * 4046.86 and _in_box(p["c"], (BAY_BOX[0], BAY_BOX[1], BAY_BOX[2], BAY_BOX[3]), 0)]
        for g in cluster(new):
            area = sum(p["area"] for p in g)
            if area < MIN_ACRES * 4046.86:
                continue
            c = (sum(p["c"][0] * p["area"] for p in g) / area, sum(p["c"][1] * p["area"] for p in g) / area)
            ws = next((w["name"] for w in watersheds if any(M.inside(c, poly) for poly in w["polys"])), None) or \
                next((w["name"] for w in watersheds if any(near_poly(c, poly, WS_NEAR_M) for poly in w["polys"])), None)
            if not ws:
                continue   # not on San Mateo County's shoreline
            city = next((pl["name"] for pl in places if any(M.inside(c, poly) for poly in pl["polys"])), None)
            if not city and places:
                city = min(places, key=lambda pl: min(dist_m(c, q) for poly in pl["polys"] for q in poly[0][::25]))["name"] + " (nearest)"
            deps = [p["depth"] for p in g if p["depth"] is not None]
            rows.append({"lat": round(c[1], 5), "lon": round(c[0], 5), "level_in": level, "area_acres": round(area / 4046.86, 1),
                         "max_depth_ft": round(max(deps), 1) if deps else "", "pieces": len(g), "city": city or "",
                         "watershed": ws.title(), "_polys": [p["poly"] for p in g]})
    rows.sort(key=lambda r: (r["level_in"], -r["area_acres"]))
    for k, r in enumerate(rows, start=1):
        r["id"] = f"SH-{k:03d}"
        r["name"] = f"{r['city'].replace(' (nearest)', '')} shoreline, {r['watershed']} watershed"
        r["include"] = "review"
        r["notes"] = ""
        r["source"] = SOURCE
    return rows


def prepare(by_level, wet=None, tree=None):
    """Normally wet land cut out of each level, then what already floods at lower levels (tile by tile; see
    shoreline_exposure.cut_levels). Returns ({inches: features}, {inches: acres of wet land removed})."""
    return E.cut_levels(by_level, wet or [], tree, log=step if "step" in globals() else None)


def spot_geom(r):
    return E.fix(shapely.MultiPolygon([shapely.Polygon(p[0], p[1:]) for p in r["_polys"]]))


def add_exposure(rows, dev, assets_by_spot=None):
    """Buildings, streets and RSAP facilities in each spot (columns developed, buildings, street_mi, streets, assets),
    and the map features for the buildings and streets."""
    feats = []
    for r in rows:
        x = dev.in_spot(spot_geom(r))
        r["buildings"] = x["buildings"] if dev.known else ""
        r["street_mi"] = round(x["street_m"] / 1609.34, 2) if dev.known else ""
        r["streets"] = "; ".join(x["streets"][:5])
        r["assets"] = "; ".join((assets_by_spot or {}).get(r["id"], [])[:8])
        r["developed"] = ("yes" if x["buildings"] or x["street_m"] >= E.MIN_STREET_M or r["assets"] else "no") if dev.known else ""
        if x["bpts"]:
            feats.append({"type": "Feature", "properties": {"spot": r["id"], "level_in": r["level_in"], "group": "buildings"},
                          "geometry": {"type": "MultiPoint", "coordinates": [list(p) for p in x["bpts"]]}})
        if x["street_m"] >= E.MIN_STREET_M:
            feats.append({"type": "Feature", "properties": {"spot": r["id"], "level_in": r["level_in"], "group": "streets"},
                          "geometry": E.rounded(E.mapping(E.MultiLineString(x["slines"])))})
    return feats


def load_watersheds(path=WATERSHEDS):
    with open(path) as f:
        return [{"name": (ft.get("properties") or {}).get("name") or "", "polys": M.polys_of(ft["geometry"])}
                for ft in json.load(f).get("features", []) if ft.get("geometry")]


def write(rows, csv_path=OUT_CSV, geo_path=OUT_GEO, exposure=None, wet_map=None, expo_path=OUT_EXPO, wet_path=OUT_WET):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    feats = [{"type": "Feature", "properties": {k: r.get(k, "") for k in ("id", "name", "level_in", "area_acres", "developed", "buildings", "street_mi")},
              "geometry": {"type": "MultiPolygon", "coordinates": [[[[round(x, 5), round(y, 5)] for x, y, *_ in ring] for ring in poly] for poly in r["_polys"]]}}
             for r in rows]
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    with open(geo_path, "w") as f:
        json.dump({"type": "FeatureCollection", "source": SOURCE, "features": feats}, f, separators=(",", ":"))
    if exposure is not None:
        with open(expo_path, "w") as f:
            json.dump({"type": "FeatureCollection", "source": "San Mateo County GIS (buildings, streets); BCDC RSAP open data "
                       "(critical facilities, transportation)", "features": exposure}, f, separators=(",", ":"))
    if wet_map is not None:
        with open(wet_path, "w") as f:
            json.dump(wet_map, f, separators=(",", ":"))


T0 = time.time()
print = functools.partial(print, flush=True)   # noqa: A001  (the Actions log shows each line as it happens, even if the job is stopped)


def step(msg):
    print(f"[{(time.time() - T0) / 60:4.1f} min] {msg}")


def main():
    step("Reading the BCDC Adapting to Rising Tides layers (Caltrans map service)…")
    lay = layers()
    if not lay:
        print("Couldn't read the map service's layer list (messages above). Nothing written.")
        return 1
    print(f"ART layers at {SERVICE}:", ", ".join(f"{k} in = layer {v}" for k, v in sorted(lay.items())))
    missing = [x for x in LEVELS_IN if x not in lay]
    if missing:
        print(f"No layer for {missing} in; the service's layer names may have changed. Nothing written.")
        return 1
    by_level = {}
    for x in LEVELS_IN:
        try:
            by_level[x] = features(lay[x])
        except Exception as e:   # noqa: BLE001
            print(f"Couldn't read the {x} in layer: {type(e).__name__}: {str(e)[:400]}. Nothing written.")
            return 1
        step(f"{x} in above MHHW: {len(by_level[x])} flooded polygons in the box")
    step("Reading the SFEI Baylands Habitat Map (normally wet land, taken out)…")
    try:
        habitats = E.load_baylands(M.arcgis, BAY_BOX)
    except Exception as e:   # noqa: BLE001
        print(f"Couldn't read the Baylands Habitat Map: {type(e).__name__}: {str(e)[:400]}. Nothing written "
              "(without it the list would be mostly marsh and ponds).")
        return 1
    kinds = {}
    for k, _ in habitats:
        kinds[k] = kinds.get(k, 0) + 1
    print(f"  {len(habitats)} habitat polygons: " + ", ".join(f"{k or '(blank)'} {n}" for k, n in sorted(kinds.items())))
    wet, tree = E.wet_mask(habitats)
    step("Taking out the normally wet land…")
    by_level, removed = prepare(by_level, wet, tree)
    for x in LEVELS_IN:
        print(f"{x} in: {removed[x]:.0f} acres of marsh, mudflat, pond and open water taken out")
    places = []
    for layer in (4, 5):   # Census cities, then unincorporated places (as in build_creek_maps.py)
        try:
            for f in M.arcgis(M.PLACES.format(layer), "1=1", "BASENAME", 0.0002):
                places.append({"name": (f.get("properties") or {}).get("BASENAME") or "", "polys": M.polys_of(f["geometry"])})
        except Exception as e:   # noqa: BLE001
            print(f"Census places (layer {layer}) unavailable ({type(e).__name__}); names without them")
    step("Grouping the spots…")
    rows = candidates(by_level, load_watersheds(), places)
    step(f"{len(rows)} spots; reading San Mateo County buildings and streets…")
    dev = E.load_developed(BAY_BOX)
    step("Reading BCDC RSAP critical facilities and transportation (ArcGIS Online)…")
    assets, by_spot = [], {}
    try:
        quick = lambda u: M.get(u, tries=2)   # noqa: E731  optional source: don't wait long on it
        lays = E.find_rsap_layers(quick)
        for g, ls in lays.items():
            print(f"  RSAP {g}: " + ("; ".join(t for t, _ in ls) or "no layers found"))
        assets, by_spot = E.assets_in_spots(lays, [(r["id"], r["level_in"], spot_geom(r)) for r in rows], BAY_BOX, quick)
    except Exception as e:   # noqa: BLE001
        print(f"  RSAP layers unavailable: {type(e).__name__}: {str(e)[:300]}")
    step("Counting buildings and streets in each spot…")
    exposure = add_exposure(rows, dev, by_spot) + assets
    write(rows, exposure=exposure, wet_map=E.map_habitats(habitats))
    for x in LEVELS_IN:
        sel = [r for r in rows if r["level_in"] == x]
        d = [r for r in sel if r.get("developed") == "yes"]
        print(f"{x} in: {len(sel)} spots, {sum(r['area_acres'] for r in sel):.0f} acres; {len(d)} with buildings or streets "
              f"({sum(r['buildings'] or 0 for r in sel)} buildings, {sum(r['street_mi'] or 0 for r in sel):.1f} mi of streets)")
    for r in rows:
        if r.get("assets"):
            print(f"  {r['id']} {r['name']}: {r['assets']}")
    step("Done.")
    for p in (OUT_CSV, OUT_GEO, OUT_EXPO, OUT_WET):
        print(f"Wrote {p} ({os.path.getsize(p) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
