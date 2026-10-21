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

Each candidate: the flooded pieces at one water level that lie within MERGE_M of each other, kept if at least
MIN_ACRES; a piece already flooded at a lower level belongs to that lower level's spot. Named after the Census city
it's in (or nearest) and the County watershed (C/CAG) around it; staff rename, merge, trim and mark include = yes/no.

Usage: python scripts/build_shoreline_hotspots.py
"""

import csv
import json
import math
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creek_maps as M  # noqa: E402  (get, arcgis, polys_of, inside, PLACES; no side effects on import)

ROOT = os.path.dirname(HERE)
SERVICE = "https://caltrans-gis.dot.ca.gov/arcgis/rest/services/CHhqenvi/DEA_BCDC_polygon_SLR/MapServer"
BAY_BOX = (-122.43, 37.44, -122.08, 37.72)    # San Mateo County's Bay side, with a margin (lon, lat)
LEVELS_IN = (12, 24, 36)                       # ART water levels above MHHW used here (the pages only ever reach the lowest)
MIN_ACRES = 0.5                                # smaller flooded patches are left out
MERGE_M = 250                                  # pieces at one level closer than this are one spot
WS_NEAR_M = 600                                # a spot this close to a San Mateo County watershed counts as in the county
OUT_CSV = os.path.join(ROOT, "lookups", "proposed", "shoreline_hotspots.csv")
OUT_GEO = os.path.join(ROOT, "data", "shoreline_hotspots_candidates.geojson")
WATERSHEDS = os.path.join(ROOT, "data", "watersheds.geojson")
COLUMNS = ["id", "name", "city", "watershed", "lat", "lon", "level_in", "area_acres", "max_depth_ft", "pieces",
           "include", "notes", "source", "checked_by", "checked_on"]
SOURCE = "BCDC Adapting to Rising Tides maps (2017), Caltrans DEA_BCDC_polygon_SLR"


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
def layers(get=M.get):
    """{inches: layer id} from the service's layer names ("BCDC SLR 2.0 ft (24 in)")."""
    j = json.loads(get(SERVICE + "?f=json"))
    out = {}
    for lyr in j.get("layers") or []:
        m = re.search(r"\((\d+)\s*in\)", lyr.get("name") or "")
        if m:
            out[int(m.group(1))] = lyr["id"]
    return out


def features(layer_id, get=M.get):
    """Flooded polygons in BAY_BOX for one layer, as GeoJSON features (lon/lat), fetched by object id in batches."""
    q = SERVICE + f"/{layer_id}/query"
    common = {"geometry": ",".join(map(str, BAY_BOX)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
              "spatialRel": "esriSpatialRelIntersects", "where": "1=1"}
    ids = json.loads(get(q + "?" + urllib.parse.urlencode(dict(common, returnIdsOnly="true", f="json")))).get("objectIds") or []
    out = []
    for k in range(0, len(ids), 100):
        p = {"objectIds": ",".join(map(str, ids[k:k + 100])), "outFields": "OBJECTID,DEPTH_FT", "returnGeometry": "true",
             "outSR": 4326, "maxAllowableOffset": 0.00003, "geometryPrecision": 6, "f": "geojson"}
        d = json.loads(get(q + "?" + urllib.parse.urlencode(p)))
        if "error" in d:
            raise RuntimeError(f"layer {layer_id}: {d['error']}")
        out += [f for f in d.get("features", []) if f.get("geometry")]
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
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a, b = pieces[i], pieces[j]
            bx = a["box"]
            if (dist_m(a["c"], b["c"]) <= MERGE_M or
                    (bx[0] <= b["c"][0] <= bx[2] and bx[1] <= b["c"][1] <= bx[3])):
                parent[find(i)] = find(j)
    groups = {}
    for i, p in enumerate(pieces):
        groups.setdefault(find(i), []).append(p)
    return list(groups.values())


def candidates(by_level, watersheds, places):
    """by_level: {inches: [GeoJSON features]} -> rows (dicts) and their polygons, lowest level first."""
    taken, rows = [], []
    for level in sorted(by_level):
        new = [p for p in pieces_of(by_level[level], level)
               if not any(M.inside(p["c"], q) or near_poly(p["c"], q, 30) for q in taken)]
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
        taken += [p["poly"] for p in new]
    rows.sort(key=lambda r: (r["level_in"], -r["area_acres"]))
    for k, r in enumerate(rows, start=1):
        r["id"] = f"SH-{k:03d}"
        r["name"] = f"{r['city'].replace(' (nearest)', '')} shoreline, {r['watershed']} watershed"
        r["include"] = "review"
        r["notes"] = ""
        r["source"] = SOURCE
    return rows


def load_watersheds(path=WATERSHEDS):
    with open(path) as f:
        return [{"name": (ft.get("properties") or {}).get("name") or "", "polys": M.polys_of(ft["geometry"])}
                for ft in json.load(f).get("features", []) if ft.get("geometry")]


def write(rows, csv_path=OUT_CSV, geo_path=OUT_GEO):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    feats = [{"type": "Feature", "properties": {k: r[k] for k in ("id", "name", "level_in", "area_acres")},
              "geometry": {"type": "MultiPolygon", "coordinates": [[[[round(x, 5), round(y, 5)] for x, y, *_ in ring] for ring in poly] for poly in r["_polys"]]}}
             for r in rows]
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    with open(geo_path, "w") as f:
        json.dump({"type": "FeatureCollection", "source": SOURCE, "features": feats}, f, separators=(",", ":"))


def main():
    lay = layers()
    print("ART layers in the service:", ", ".join(f"{k} in = layer {v}" for k, v in sorted(lay.items())))
    missing = [x for x in LEVELS_IN if x not in lay]
    if missing:
        print(f"No layer for {missing} in; the service's layer names may have changed. Nothing written.")
        return 1
    by_level = {}
    for x in LEVELS_IN:
        by_level[x] = features(lay[x])
        print(f"{x} in above MHHW: {len(by_level[x])} flooded polygons in the box")
    places = []
    for layer in (4, 5):   # Census cities, then unincorporated places (as in build_creek_maps.py)
        try:
            for f in M.arcgis(M.PLACES.format(layer), "1=1", "BASENAME", 0.0002):
                places.append({"name": (f.get("properties") or {}).get("BASENAME") or "", "polys": M.polys_of(f["geometry"])})
        except Exception as e:   # noqa: BLE001
            print(f"Census places (layer {layer}) unavailable ({type(e).__name__}); names without them")
    rows = candidates(by_level, load_watersheds(), places)
    write(rows)
    for x in LEVELS_IN:
        sel = [r for r in rows if r["level_in"] == x]
        print(f"{x} in: {len(sel)} spots, {sum(r['area_acres'] for r in sel):.0f} acres")
    print(f"Wrote {OUT_CSV} ({len(rows)} rows) and {OUT_GEO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
