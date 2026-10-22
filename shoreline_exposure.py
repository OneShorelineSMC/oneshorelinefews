"""What is in each shoreline low spot: used by scripts/build_shoreline_hotspots.py (lookups/THRESHOLDS_BASIS.md §4c).

1. Normally wet land is taken out of BCDC's flooded areas: the Bay, tidal marsh, mudflats, tidal and managed ponds,
   channels and beaches (SFEI Baylands Habitat Map 2020, habitat type "Level4", WET below). Water there at a high tide
   is normal, so it isn't a low spot. Diked baylands and levees stay in: that is land behind or on the shoreline.
2. Buildings and streets in each spot: San Mateo County's building footprints and street centerlines (County GIS,
   daily exports). A spot with a building or at least MIN_STREET_M of street is "developed"; the rest is open land.
3. Critical facilities and transportation in each spot: BCDC's Regional Shoreline Adaptation Plan (RSAP) open data
   (ArcGIS Online), the "Critical Infrastructure" map and the transportation / transit maps found next to it.

Geometry with shapely (lon/lat; lengths and areas by a local metres-per-degree scale, fine for spots this small).
Nothing here needs a key. Every source is optional except the habitat map: without it the list would be mostly marsh.
"""

import functools
import io
import json
import math
import os
import re
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile

import shapely
from shapely.geometry import shape, mapping, Point, MultiPoint, MultiLineString, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

print = functools.partial(print, flush=True)   # noqa: A001  (log lines show at once on GitHub)
UA = {"User-Agent": "OneShoreline FEWS shoreline spots (github.com/OneShorelineSMC/oneshorelinefews)"}

BAYLANDS = "https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds3190_fpu/FeatureServer/0/query"
WET = {"Shallow Subtidal", "Deep Subtidal", "Tidal Flat", "Tidal Pond/Panne", "Intertidal Channel", "Tidal Marsh",
       "Beach", "Other Marsh", "Other Open Water", "Dune"}   # kept as land: "Non-Aquatic Diked Bayland", "Levee", blank
MAP_WET = {"Tidal Flat", "Tidal Pond/Panne", "Intertidal Channel", "Tidal Marsh", "Other Marsh", "Other Open Water", "Beach"}
SLIVER_DEG = 0.00002          # about 2 m: thin slivers left along the habitat edges are trimmed off

COUNTY_ZIP = "https://gis-data-downloads.s3-us-west-1.amazonaws.com/{}.zip"
BUILDINGS_ZIP = COUNTY_ZIP.format("BUILDING_FOOTPRINTS")
STREETS_ZIP = COUNTY_ZIP.format("SAN_MATEO_COUNTY_STREETS")
COUNTY_CRS = "EPSG:2227"      # used only if a shapefile has no .prj (California State Plane III, US feet)
STREET_NAME_FIELDS = ("FULLNAME", "FULL_NAME", "FULLSTREET", "STREETNAME", "STREET_NAM", "ST_NAME", "STNAME", "STREET", "NAME")
MIN_STREET_M = 25             # less street than this in a spot is an edge touching it, not a flooded street

AGOL = "https://www.arcgis.com/sharing/rest"
RSAP_ITEMS = {"critical": ["d810ea5515a74cada91ea373b8f23ea0"],   # RSAP Open Data "Critical Infrastructure" (web map)
              "transport": []}                                      # found by searching the same owner (below); pin ids here once known
RSAP_SEARCH = {"transport": ["transportation", "transit", "movement of people"]}
RSAP_SKIP = re.compile(r"exposure|flood|inundation|sea level|slr|groundwater|surge|hazard|boundary|county|jurisdiction|summary", re.I)
NAME_FIELDS = ("NAME", "Name", "name", "FACNAME", "FAC_NAME", "FACILITY_NAME", "FACILITY", "FacilityName", "SITE_NAME",
               "STATION", "STATION_NAME", "Station_Name", "PLANT_NAME", "Plant_Name", "AIRPORT", "PORT_NAME", "ROUTE", "Route",
               "LINE_NAME", "LINENAME", "OPERATOR", "TITLE")


# ---------------------------------------------------------------- small helpers
def m_per_deg(lat):
    return 111320 * math.cos(math.radians(lat)), 110540


def length_m(geom):
    """Length of a (multi)line in metres."""
    if geom is None or geom.is_empty:
        return 0.0
    kx, ky = m_per_deg(geom.centroid.y)
    total = 0.0
    for ln in getattr(geom, "geoms", [geom]):
        if ln.geom_type not in ("LineString", "LinearRing"):
            total += length_m(ln) if hasattr(ln, "geoms") else 0.0
            continue
        c = list(ln.coords)
        total += sum(math.hypot((c[i][0] - c[i - 1][0]) * kx, (c[i][1] - c[i - 1][1]) * ky) for i in range(1, len(c)))
    return total


def area_m2(geom):
    if geom is None or geom.is_empty:
        return 0.0
    kx, ky = m_per_deg(geom.centroid.y)
    return geom.area * kx * ky


def fix(g):
    """A valid geometry (self-touching outlines from the map services otherwise break overlays)."""
    try:
        return g if g.is_valid else shapely.make_valid(g)
    except Exception:   # noqa: BLE001
        return g.buffer(0)


def polygons_only(g):
    """The polygon parts of a geometry (an overlay can leave stray lines and points)."""
    if g is None or g.is_empty:
        return []
    if g.geom_type == "Polygon":
        return [g]
    if g.geom_type == "MultiPolygon":
        return list(g.geoms)
    if hasattr(g, "geoms"):
        return [p for part in g.geoms for p in polygons_only(part)]
    return []


def lines_only(g):
    if g is None or g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    if g.geom_type == "MultiLineString":
        return list(g.geoms)
    if hasattr(g, "geoms"):
        return [p for part in g.geoms for p in lines_only(part)]
    return []


RSAP_BUDGET_S = 600          # RSAP layers are optional: stop reading more of them after 10 minutes


def download(url, tries=2):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
                return r.read()
        except Exception as e:   # noqa: BLE001
            if k == tries - 1:
                raise
            print(f"    (retrying in {10 * (k + 1)} s: {type(e).__name__}: {str(e)[:80]})")
            time.sleep(10 * (k + 1))


# ---------------------------------------------------------------- 1. normally wet land (SFEI Baylands Habitat Map 2020)
def load_baylands(arcgis, box):
    """[(habitat type, shapely polygon)] in the box. arcgis = build_creek_maps.arcgis (paged GeoJSON query)."""
    out = []
    for f in arcgis(BAYLANDS, "1=1", "Level4", 0.00002, bbox=box):
        g = fix(shape(f["geometry"]))
        for p in polygons_only(g):
            out.append(((f.get("properties") or {}).get("Level4") or "", p))
    return out


def wet_mask(habitats):
    """One shapely geometry: every normally wet habitat, plus a tree for quick lookups."""
    wet = [p for kind, p in habitats if kind in WET]
    return wet, STRtree(wet) if wet else None


def remove_wet(feats, wet, tree):
    """The flooded features with the normally wet parts cut out; each keeps its own properties (depth).
    Returns (features, acres removed)."""
    out, removed, every = [], 0.0, []
    for f in feats:
        g = fix(shape(f["geometry"]))
        before = area_m2(g)
        if tree is not None:
            idx = tree.query(g, predicate="intersects")
            if len(idx) > 300:   # a big flooded area touching many habitat patches: cut with all of them at once (built once)
                if not every:
                    every.append(fix(unary_union(wet)))
                g = fix(g.difference(every[0]))
            elif len(idx):
                g = fix(g.difference(unary_union([wet[i] for i in idx])))
        g = trim(g)
        removed += max(0.0, before - area_m2(g))
        polys = polygons_only(g)
        if polys:
            out.append({"type": "Feature", "properties": f.get("properties") or {},
                        "geometry": mapping(shapely.MultiPolygon(polys))})
    return out, removed / 4046.86


def trim(g):
    """Thin slivers (a few metres wide) along a cut edge removed; real areas keep their shape."""
    if g.is_empty:
        return g
    return fix(g.buffer(-SLIVER_DEG, join_style="mitre").buffer(SLIVER_DEG, join_style="mitre").intersection(g))


def minus_lower(feats, lower):
    """Flooded features at one level with what already floods at lower levels cut out: a spot's level is the lowest
    level that floods it, and the area that only floods higher up is a spot of its own."""
    if lower is None or lower.is_empty:
        return feats
    out = []
    lt = STRtree(polygons_only(lower))
    lp = polygons_only(lower)
    for f in feats:
        g = fix(shape(f["geometry"]))
        idx = lt.query(g, predicate="intersects")
        if len(idx):
            g = trim(fix(g.difference(unary_union([lp[i] for i in idx]).buffer(SLIVER_DEG / 2))))
        polys = polygons_only(g)
        if polys:
            out.append({"type": "Feature", "properties": f.get("properties") or {}, "geometry": mapping(shapely.MultiPolygon(polys))})
    return out


def union_of(feats):
    return fix(unary_union([fix(shape(f["geometry"])) for f in feats])) if feats else None


def map_habitats(habitats, simplify_deg=0.00006):
    """GeoJSON for the map: marsh, mudflats and ponds (not open Bay water: the base map already shows it), simplified."""
    by = {}
    for kind, p in habitats:
        if kind in MAP_WET:
            by.setdefault(kind, []).append(p)
    feats = []
    for kind, ps in sorted(by.items()):
        g = unary_union(ps).simplify(simplify_deg, preserve_topology=True)
        polys = [p for p in polygons_only(g) if area_m2(p) > 2000]
        if polys:
            feats.append({"type": "Feature", "properties": {"kind": kind}, "geometry": rounded(mapping(shapely.MultiPolygon(polys)))})
    return {"type": "FeatureCollection", "source": "SFEI Baylands Habitat Map 2020", "features": feats}


def rounded(gj, nd=5):
    def r(c):
        return [round(c[0], nd), round(c[1], nd)] if isinstance(c[0], (int, float)) else [r(x) for x in c]
    return {"type": gj["type"], "coordinates": r(gj["coordinates"])}


# ---------------------------------------------------------------- 2. buildings and streets (San Mateo County GIS)
def read_county_shapefile(zip_bytes, want, box):
    """Shapes from a County GIS zip, in lon/lat, only those in the box: [(shapely geometry, attribute dict)].
    want: a word in the shapefile's name (the zip can hold more than one)."""
    import logging
    import numpy as np
    import shapefile        # pyshp
    logging.getLogger("shapefile").setLevel(logging.ERROR)   # ring-direction notes for every odd footprint: noise in the log
    from pyproj import CRS, Transformer
    with tempfile.TemporaryDirectory() as d:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            z.extractall(d)
        shps = [os.path.join(r, n) for r, _, ns in os.walk(d) for n in ns if n.lower().endswith(".shp")]
        if not shps:
            raise RuntimeError("no shapefile in the zip")
        shp = next((s for s in shps if want.lower() in os.path.basename(s).lower()), max(shps, key=os.path.getsize))
        prj = shp[:-4] + ".prj"
        src = CRS.from_wkt(open(prj).read()) if os.path.exists(prj) else CRS.from_user_input(COUNTY_CRS)
        to_ll = Transformer.from_crs(src, "EPSG:4326", always_xy=True)
        to_src = Transformer.from_crs("EPSG:4326", src, always_xy=True)
        xs, ys = to_src.transform([box[0], box[2], box[0], box[2]], [box[1], box[1], box[3], box[3]])
        sbox = (min(xs), min(ys), max(xs), max(ys))
        r = shapefile.Reader(shp)
        fields = [f[0] for f in r.fields[1:]]
        print(f"  {os.path.basename(shp)}: {len(r)} shapes, fields {', '.join(fields[:30])}")
        out = []
        for n, sr in enumerate(r.iterShapeRecords()):
            if n and n % 100000 == 0:
                print(f"    {n} of {len(r)} read, {len(out)} in the box so far")
            sh = sr.shape
            if not sh.points or not hasattr(sh, "bbox"):
                continue
            b = sh.bbox
            if b[2] < sbox[0] or b[0] > sbox[2] or b[3] < sbox[1] or b[1] > sbox[3]:
                continue
            try:
                g = shape(sh.__geo_interface__)
            except Exception:   # noqa: BLE001
                continue
            g = shapely.transform(g, lambda c: np.column_stack(to_ll.transform(c[:, 0], c[:, 1])))
            out.append((fix(g), dict(zip(fields, sr.record))))
        return out


def street_name(attrs):
    for k in STREET_NAME_FIELDS:
        for a in attrs:
            if a.upper() == k and str(attrs[a] or "").strip():
                return " ".join(str(attrs[a]).split()).title()
    return ""


class Developed:
    """Buildings (polygons) and streets (lines) to count in each spot."""

    def __init__(self, buildings=None, streets=None):
        self.b = [g for g, _ in (buildings or []) if not g.is_empty]
        self.s = [(g, street_name(a)) for g, a in (streets or []) if not g.is_empty]
        self.bt = STRtree(self.b) if self.b else None
        self.st = STRtree([g for g, _ in self.s]) if self.s else None
        self.known = buildings is not None and streets is not None

    def in_spot(self, spot):
        """{'buildings': n, 'street_m': metres, 'streets': [names, longest first], 'bpts': [(lon, lat)], 'slines': geometry}"""
        out = {"buildings": 0, "street_m": 0.0, "streets": [], "bpts": [], "slines": []}
        if self.bt is not None:
            idx = self.bt.query(spot, predicate="intersects")
            out["buildings"] = len(idx)
            out["bpts"] = [(round(self.b[i].representative_point().x, 5), round(self.b[i].representative_point().y, 5)) for i in idx]
        if self.st is not None:
            by = {}
            for i in self.st.query(spot, predicate="intersects"):
                g, name = self.s[i]
                part = g.intersection(spot)
                m = length_m(part)
                if m <= 0:
                    continue
                out["street_m"] += m
                out["slines"] += lines_only(part)
                if name:
                    by[name] = by.get(name, 0) + m
            out["streets"] = [n for n, m in sorted(by.items(), key=lambda kv: -kv[1]) if m >= 10]
        return out


def load_developed(box, fetch=download):
    """Developed(...) from the County's exports; a source that can't be read is left out (and said so)."""
    got = {}
    for key, url, want in (("buildings", BUILDINGS_ZIP, "BUILDING"), ("streets", STREETS_ZIP, "STREET")):
        try:
            print(f"Reading San Mateo County {key} ({url})…")
            got[key] = read_county_shapefile(fetch(url), want, box)
            print(f"  {len(got[key])} {key} in the box")
        except Exception as e:   # noqa: BLE001
            print(f"  County {key} unavailable: {type(e).__name__}: {str(e)[:300]}")
            got[key] = None
    return Developed(got["buildings"], got["streets"])


# ---------------------------------------------------------------- 3. RSAP critical facilities and transportation
def get_json(url, get):
    t = get(url)
    d = json.loads(t)
    if isinstance(d, dict) and d.get("error"):
        raise RuntimeError(f"{url.split('?')[0]}: {d['error']}")
    return d


def web_map_layers(data):
    """[(title, url)] for every layer in a web map's operationalLayers, group layers included."""
    out = []

    def walk(ls, prefix=""):
        for l in ls or []:
            title = l.get("title") or ""
            if l.get("layers") and not l.get("url"):
                walk(l["layers"], title)
            elif l.get("url"):
                out.append((title or prefix, l["url"]))
    walk(data.get("operationalLayers"))
    return out


def service_layers(url, get):
    """A FeatureServer/MapServer url -> [(title, layer url)]; a layer url (ending in a number) as is."""
    if re.search(r"/(Feature|Map)Server/\d+/?$", url):
        return [(None, url.rstrip("/"))]
    d = get_json(url.rstrip("/") + "?f=json", get)
    return [(l.get("name"), url.rstrip("/") + f"/{l['id']}") for l in d.get("layers") or [] if not l.get("subLayerIds")]


def item_layers(item_id, get):
    """[(title, layer url)] for an ArcGIS Online item: a web map, or a feature / map service."""
    info = get_json(f"{AGOL}/content/items/{item_id}?f=json", get)
    kind = info.get("type") or ""
    if kind == "Web Map":
        out = []
        for title, url in web_map_layers(get_json(f"{AGOL}/content/items/{item_id}/data?f=json", get)):
            try:
                out += [(t or title, u) for t, u in service_layers(url, get)]
            except Exception as e:   # noqa: BLE001
                print(f"    {title}: {type(e).__name__}: {str(e)[:150]}")
        return info, out
    if info.get("url"):
        return info, service_layers(info["url"], get)
    return info, []


def find_rsap_layers(get, items=RSAP_ITEMS, search=RSAP_SEARCH):
    """{group: [(title, layer url)]}: the pinned items, plus items by the same owner whose titles match the search words."""
    found, owner = {}, None
    for group, ids in items.items():
        for iid in ids:
            try:
                info, ls = item_layers(iid, get)
                owner = owner or info.get("owner")
                print(f"  RSAP {group}: item {iid} '{info.get('title')}' ({info.get('type')}): {len(ls)} layers")
                found.setdefault(group, []).extend(ls)
            except Exception as e:   # noqa: BLE001
                print(f"  RSAP item {iid}: {type(e).__name__}: {str(e)[:200]}")
    for group, words in search.items():
        if items.get(group) or not owner:
            continue
        q = f'owner:"{owner}" AND (' + " OR ".join(f'title:"{w}"' for w in words) + ")"
        try:
            res = get_json(f"{AGOL}/search?" + urllib.parse.urlencode({"q": q, "num": 50, "f": "json"}), get)
        except Exception as e:   # noqa: BLE001
            print(f"  RSAP search for {group}: {type(e).__name__}: {str(e)[:200]}")
            continue
        for it in res.get("results") or []:
            if it.get("type") not in ("Web Map", "Feature Service", "Map Service"):
                continue
            try:
                info, ls = item_layers(it["id"], get)
                print(f"  RSAP {group}: found item {it['id']} '{it.get('title')}' ({it.get('type')}): {len(ls)} layers")
                found.setdefault(group, []).extend(ls)
            except Exception as e:   # noqa: BLE001
                print(f"  RSAP item {it.get('id')}: {type(e).__name__}: {str(e)[:200]}")
    for group in found:   # one copy of each layer; leave out hazard, exposure-summary and boundary layers
        seen, keep = set(), []
        for title, url in found[group]:
            if url in seen or RSAP_SKIP.search(title or ""):
                continue
            seen.add(url)
            keep.append((title or url.rsplit("/", 2)[-2], url))
        found[group] = keep
    return found


def esri_geom(g):
    if not g:
        return None
    if "x" in g:
        return Point(g["x"], g["y"])
    if "points" in g:
        return MultiPoint(g["points"])
    if "paths" in g:
        return MultiLineString([p for p in g["paths"] if len(p) > 1])
    if "rings" in g:
        return fix(shapely.Polygon(g["rings"][0], g["rings"][1:]) if len(g["rings"]) else shapely.Polygon())
    return None


def layer_features(url, box, get):
    """[(shapely geometry, attributes)] in the box from one layer: GeoJSON, else Esri JSON."""
    out, start = [], 0
    base = {"where": "1=1", "geometry": ",".join(map(str, box)), "geometryType": "esriGeometryEnvelope", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "true", "outSR": 4326,
            "geometryPrecision": 6, "resultRecordCount": 1000}
    fmt = "geojson"
    while True:
        p = dict(base, resultOffset=start, f=fmt)
        try:
            d = get_json(url + "/query?" + urllib.parse.urlencode(p), get)
        except (RuntimeError, ValueError):
            if fmt == "geojson":
                fmt = "json"
                continue
            raise
        if fmt == "geojson":
            feats = [(shape(f["geometry"]), f.get("properties") or {}) for f in d.get("features", []) if f.get("geometry")]
            more = d.get("exceededTransferLimit") or (d.get("properties") or {}).get("exceededTransferLimit")
        else:
            feats = [(esri_geom(f.get("geometry")), f.get("attributes") or {}) for f in d.get("features", [])]
            feats = [(g, a) for g, a in feats if g is not None and not g.is_empty]
            more = d.get("exceededTransferLimit")
        out += feats
        if not more or not d.get("features"):
            return out
        start += len(d["features"])


def asset_name(attrs, fallback):
    for k in NAME_FIELDS:
        v = attrs.get(k)
        if v not in (None, "") and str(v).strip():
            return " ".join(str(v).split())
    for k, v in attrs.items():   # any other text field with "name" in it
        if "name" in k.lower() and isinstance(v, str) and v.strip():
            return " ".join(v.split())
    return fallback


def kind_of(title):
    """A short plain name for a layer ("Wastewater Treatment Facilities" stays; "RSAP_Fire_Stations_2024" -> "Fire Stations")."""
    t = re.sub(r"[_]+", " ", title or "")
    t = re.sub(r"\b(RSAP|BCDC|CEC|HIFLD|MTC|Caltrans|OSHPD|CalOES|Cal EPA|CalEPA)\b", "", t, flags=re.I)
    t = re.sub(r"\b(19|20)\d\d\b", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -·:")
    return t or (title or "Asset")


def assets_in_spots(layers_by_group, spots, box, get):
    """GeoJSON features of the RSAP assets in the spots, and {spot id: ['Kind: name', ...]}.
    spots: [(id, level_in, shapely geometry)]. Points as points; lines (highways, rail) clipped to the spot;
    areas (airports, ports) as a point inside the overlap."""
    geoms = [g for _, _, g in spots]
    tree = STRtree(geoms) if geoms else None
    feats, by_spot, t0 = [], {}, time.time()
    for group, layers in layers_by_group.items():
        for title, url in layers:
            if time.time() - t0 > RSAP_BUDGET_S:
                print(f"    {group} · {title}: skipped (RSAP time limit of {RSAP_BUDGET_S // 60} min reached)")
                continue
            try:
                fs = layer_features(url, box, get)
            except Exception as e:   # noqa: BLE001
                print(f"    {title}: {type(e).__name__}: {str(e)[:150]}")
                continue
            kind, hits = kind_of(title), 0
            for g, attrs in fs:
                if tree is None:
                    break
                g = fix(g)
                for i in tree.query(g, predicate="intersects"):
                    sid, lvl, sg = spots[i]
                    part = g.intersection(sg)
                    if part.is_empty:
                        continue
                    name = asset_name(attrs, kind)
                    props = {"spot": sid, "level_in": lvl, "group": group, "kind": kind, "name": name}
                    if g.geom_type in ("LineString", "MultiLineString"):
                        ls = lines_only(part)
                        m = length_m(MultiLineString(ls)) if ls else 0
                        if m < MIN_STREET_M:
                            continue
                        props["len_m"] = round(m)
                        geom = rounded(mapping(MultiLineString(ls)))
                    elif g.geom_type in ("Polygon", "MultiPolygon"):
                        geom = rounded(mapping(part.representative_point()))
                    else:
                        geom = rounded(mapping(part if part.geom_type == "Point" else part.representative_point()))
                    feats.append({"type": "Feature", "properties": props, "geometry": geom})
                    label = kind if name == kind else f"{kind}: {name}"
                    if label not in by_spot.setdefault(sid, []):
                        by_spot[sid].append(label)
                    hits += 1
            print(f"    {group} · {title}: {len(fs)} in the box, {hits} in a low spot")
    return feats, by_spot
