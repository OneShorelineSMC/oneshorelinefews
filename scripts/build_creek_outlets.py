"""Creek outlets: where each creek on San Mateo County's Bay side reaches the Bay, as a lat/lon for staff to review.
The point is for looking up the tide at a creek (for example from NOAA's San Francisco Bay model) rather than at the
nearest NOAA tide gauge.

Sources (public, read when the build runs, so it runs on GitHub: Actions > Build creek outlets > Run workflow):
  Watersheds    data/watersheds.geojson (San Mateo County / C/CAG watersheds, already in the repo); a watershed is on
                the Bay side if it comes within BAY_NEAR_M of the Bay shoreline
  Bay shoreline SFEI San Francisco Bay Shore Inventory lines for San Mateo County (BCDC RSAP open data), all classes
  Creek lines   USGS National Hydrography Dataset, Flowline - Large Scale, named lines (GNIS name); San Mateo
                County's Streams and Creeks layer (Flows to Bay map) for creeks NHD doesn't name

For each Bay-side watershed:
  1. The creek line: NHD lines named like the watershed (or a FEWS creek's NHD names, build_creek_maps.NHD_NAMES);
     if none, the named NHD stream with the most length in the watershed.
  2. Its downstream end (NHD lines are drawn in the direction of flow: the end of a piece no other piece continues from).
  3. The outlet: where that creek line crosses the Bay shoreline nearest its downstream end (within CROSS_M); if it
     doesn't cross, its downstream end. With no NHD line at all: the shoreline "Channel or Opening" (a creek or slough
     mouth in the Shore Inventory) nearest the watershed, flagged for a closer look.
Writes, for review (include = review; set yes / no, fix lat/lon by hand where needed, then save it as
lookups/creek_outlets.csv):
  lookups/proposed/creek_outlets.csv            one row per Bay-side watershed
  data/creek_outlets_candidates.geojson         the points and the creek lines used, to check in GIS or geojson.io

Usage: python scripts/build_creek_outlets.py
"""

import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creek_maps as M          # noqa: E402  (get, arcgis, NHD, NHD_NAMES, PLACES, polys_of, inside)
import build_shoreline_lowpoints as L  # noqa: E402  (SHORE, BAY_BOX, dist_m)

ROOT = os.path.dirname(HERE)
WATERSHEDS = os.path.join(ROOT, "data", "watersheds.geojson")
OUT_CSV = os.path.join(ROOT, "lookups", "proposed", "creek_outlets.csv")
OUT_GEO = os.path.join(ROOT, "data", "creek_outlets_candidates.geojson")
BAY_NEAR_M = 300     # a watershed this close to the Bay shoreline drains to the Bay
CROSS_M = 1500       # a shoreline crossing this close to the creek's downstream end is its outlet
SNAP_M = 2           # piece ends this close together are joined
OPENING = "Channel or Opening"
COLUMNS = ["id", "creek", "watershed", "fews_creek", "city", "lat", "lon", "method", "nhd_name", "shore_class",
           "end_to_outlet_m", "include", "notes", "source", "checked_by", "checked_on"]
# Watersheds whose creek joins another creek before the Bay: they share that creek's outlet (staff knowledge)
SAME_OUTLET = {"El Zanjon Creek": "San Bruno Creek"}
SOURCE = "USGS NHD flowlines; SFEI Bay Shore Inventory (BCDC RSAP); San Mateo County watersheds"


def title(name):
    return " ".join(w.capitalize() for w in (name or "").split())


def aliases():
    """{lower-case name: (fews creek id, [names])} from build_creek_maps.NHD_NAMES."""
    out = {}
    for cid, names in M.NHD_NAMES.items():
        for n in names:
            out[n.lower()] = (cid, names)
    return out


def bay_side(watersheds, shore_union):
    """Watersheds within BAY_NEAR_M of the Bay shoreline."""
    import shapely
    from shapely.geometry import shape
    deg = BAY_NEAR_M / 111320 / math.cos(math.radians(37.55))
    out = []
    for w in watersheds:
        g = shape(w["geometry"])
        if not g.is_valid:
            g = g.buffer(0)
        if shapely.intersects(g.buffer(deg), shore_union):
            out.append(dict(w, shape=g))
    return out


def county_words(w, alias):
    """Words to look for in the County streams layer's NAME: the watershed's name without Creek / Channel etc., and the
    FEWS creek's (build_creek_maps.COUNTY_STREAM_NAMES)."""
    wname = title(w["name"])
    fews = alias.get(wname.lower(), (None, []))[0]
    words = list(M.COUNTY_STREAM_NAMES.get(fews, []))
    base = wname
    for t in (" Creek", " Channel", " Canal", " Drainage", " Slough"):
        base = base.replace(t, "")
    return [x.lower() for x in words + [base] if len(x.strip()) >= 4]   # not "Bay" (Bay Slough): too common


def creek_pieces(w, flow, alias, county=()):
    """(fews id, name used, [LineString], how) for the watershed's creek; how = "nhd" (NHD line named like the
    watershed), "county" (County streams layer by name; not drawn in the direction of flow) or "main" (the main named
    NHD stream in the watershed)."""
    from shapely.geometry import shape
    wname = title(w["name"])
    fews, names = alias.get(wname.lower(), (None, [wname]))
    want = {n.lower() for n in names}
    pieces = [(shape(f["geometry"]), f["properties"].get("gnis_name") or "") for f in flow
              if (f["properties"].get("gnis_name") or "").lower() in want]
    near = w["shape"].buffer(0.005)
    pieces = [(g, n) for g, n in pieces if g.intersects(near)]
    if not pieces and county:   # San Mateo County's Streams and Creeks layer (Flows to Bay) by name
        words = county_words(w, alias)
        got = [(shape(f["geometry"]), (f.get("properties") or {}).get("NAME") or "") for f in county
               if any(re.search(r"\b" + re.escape(x) + r"\b", ((f.get("properties") or {}).get("NAME") or "").lower()) for x in words)]
        got = [(g, n) for g, n in got if g.intersects(near)]
        if got:
            n = max({n for _, n in got}, key=lambda k: sum(g.intersection(w["shape"]).length for g, m in got if m == k))
            return fews, n, [g for g, m in got if m == n], "county"
    if not pieces:   # the named stream with the most length in the watershed (not an aqueduct or pipeline)
        by = {}
        for f in flow:
            n = f["properties"].get("gnis_name") or ""
            if not_creek(f["properties"]):
                continue
            g = shape(f["geometry"])
            if g.intersects(w["shape"]):
                by.setdefault(n, []).append(g)
        if not by:
            return fews, "", [], ""
        n = max(by, key=lambda k: sum(g.intersection(w["shape"]).length for g in by[k]))
        return fews, n, by[n], "main"
    return fews, pieces[0][1], [g for g, _ in pieces], "nhd"


def not_creek(props):
    """Aqueducts and pipelines (NHD FType 428) carry water across watersheds; they aren't the watershed's creek."""
    n = (props.get("gnis_name") or "").lower()
    return str(props.get("ftype") or "") == "428" or any(w in n for w in ("aqueduct", "pipeline", "tunnel"))


def lines(geoms):
    out = []
    for g in geoms:
        out += list(g.geoms) if g.geom_type == "MultiLineString" else [g] if g.geom_type == "LineString" else []
    return out


def downstream_ends(pieces):
    """Last points of pieces that no other piece starts from (NHD draws lines in the direction of flow)."""
    ls = lines(pieces)
    starts = [ln.coords[0] for ln in ls]
    ends = []
    for ln in ls:
        e = ln.coords[-1]
        if not any(L.dist_m(e, s) <= SNAP_M for s in starts):
            ends.append(e)
    return ends


def nearest_on(pt, geom):
    from shapely.geometry import Point
    from shapely.ops import nearest_points
    q = nearest_points(Point(pt), geom)[1]
    return (q.x, q.y)


def outlet(w, flow, alias, shore, shore_union, openings, county=()):
    """One review row for a Bay-side watershed."""
    from shapely.geometry import Point
    import shapely
    fews, nname, pieces, how = creek_pieces(w, flow, alias, county)
    row = {"creek": title(w["name"]), "watershed": title(w["name"]), "fews_creek": fews or "", "nhd_name": nname}
    if pieces:
        ends = downstream_ends(pieces) if how != "county" else []
        if not ends:   # a loop or odd drawing: the end nearest the shoreline
            ends = [c for ln in lines(pieces) for c in (ln.coords[0], ln.coords[-1])]
        end = min(ends, key=lambda e: L.dist_m(e, nearest_on(e, shore_union)))
        hits = []
        for p in shapely.get_parts(shapely.intersection(shapely.union_all(pieces), shore_union)):
            if p.geom_type == "Point":
                hits.append((p.x, p.y))
            elif not p.is_empty:
                hits += [tuple(c) for c in shapely.get_coordinates(p)]
        hits = [h for h in hits if L.dist_m(h, end) <= CROSS_M]
        if hits:
            pt = min(hits, key=lambda h: L.dist_m(h, end))
            row["method"] = "creek line crosses the Bay shoreline"
        else:
            pt = end
            gap = L.dist_m(end, nearest_on(end, shore_union))
            row["method"] = f"creek line ends {gap:.0f} m from the Bay shoreline"
        row["end_to_outlet_m"] = round(L.dist_m(pt, end))
        if how == "county":
            row["method"] += " (County streams layer; NHD has no line by this name)"
        if how == "main":
            row["method"] += f" (NHD has no {row['creek']}: used {nname}, the main named stream in the watershed; check)"
        row["creek"] = nname or row["creek"]
    else:
        near = [o for o in openings if o[0].distance(w["shape"]) * 111320 * 0.79 <= BAY_NEAR_M]
        if not near:
            row.update(method="no creek line and no shoreline opening nearby: set by hand", lat="", lon="",
                       shore_class="", end_to_outlet_m="")
            return row
        g = max(near, key=lambda o: o[0].intersection(w["shape"].buffer(0.003)).length)[0]
        c = g.interpolate(0.5, normalized=True)
        pt = (c.x, c.y)
        row["method"] = "no creek line in NHD or the County streams layer: shoreline opening next to the watershed (check)"
        row["end_to_outlet_m"] = ""
    cls = min(shore, key=lambda s: s[0].distance(Point(pt)))[1] if shore else ""
    row.update(lat=round(pt[1], 5), lon=round(pt[0], 5), shore_class=cls, _pt=pt, _lines=[list(ln.coords) for ln in lines(pieces)])
    return row


def city_of(pt, places):
    if not pt or not places:
        return ""
    c = next((pl["name"] for pl in places if any(M.inside(pt, poly) for poly in pl["polys"])), None)
    if c:
        return c
    return min(places, key=lambda pl: min(L.dist_m(pt, q) for poly in pl["polys"] for q in poly[0][::25]))["name"] + " (nearest)"


def build(watersheds, shore_feats, flow, places=(), county=()):
    """Rows, north to south. shore_feats: [(shapely line, attributes)]; flow: NHD GeoJSON features."""
    import shapely
    shore = [(g, (a.get("Class") or "").strip()) for g, a in shore_feats
             if "san mateo" in str(a.get("Geographic_County") or "").lower() and not g.is_empty]
    shore_union = shapely.union_all([g for g, _ in shore])
    openings = [(g, c) for g, c in shore if c == OPENING]
    alias = aliases()
    rows = [outlet(w, flow, alias, shore, shore_union, openings, county) for w in bay_side(watersheds, shore_union)]
    by_ws = {r["watershed"]: r for r in rows}
    for r in rows:
        to = by_ws.get(SAME_OUTLET.get(r["watershed"]))
        if to and to.get("lat") != "":
            r.update({k: to.get(k, "") for k in ("lat", "lon", "shore_class", "_pt")}, creek=r["watershed"], nhd_name="",
                     end_to_outlet_m="", _lines=[], method=f"joins {to['watershed']} before the Bay: same outlet")
    rows.sort(key=lambda r: -(r["lat"] or 0))
    for k, r in enumerate(rows, start=1):
        r.update(id=f"CO-{k:03d}", city=city_of(r.get("_pt"), places), include="review", notes="", source=SOURCE,
                 checked_by="", checked_on="")
    return rows


def write(rows, csv_path=OUT_CSV, geo_path=OUT_GEO):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\r\n")
        w.writeheader()
        w.writerows(rows)
    feats = []
    for r in rows:
        props = {k: r[k] for k in ("id", "creek", "method")}
        if r.get("_pt"):
            feats.append({"type": "Feature", "properties": props,
                          "geometry": {"type": "Point", "coordinates": [round(r["_pt"][0], 5), round(r["_pt"][1], 5)]}})
        if r.get("_lines"):
            feats.append({"type": "Feature", "properties": dict(props, part="creek line"),
                          "geometry": {"type": "MultiLineString",
                                       "coordinates": [[[round(x, 5), round(y, 5)] for x, y, *_ in ln] for ln in r["_lines"]]}})
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    with open(geo_path, "w") as f:
        json.dump({"type": "FeatureCollection", "source": SOURCE, "features": feats}, f, separators=(",", ":"))


def county_lines(watersheds, arcgis=None):
    """Named lines from San Mateo County's Streams and Creeks layer, asked watershed by watershed (Bay area only)."""
    arcgis = arcgis or M.arcgis
    out, seen = [], set()
    bx0, by0, bx1, by1 = L.BAY_BOX
    for w in watersheds:
        xs = [p[0] for poly in M.polys_of(w["geometry"]) for p in poly[0]]
        ys = [p[1] for poly in M.polys_of(w["geometry"]) for p in poly[0]]
        if not xs or max(xs) < bx0 or min(xs) > bx1 or max(ys) < by0 or min(ys) > by1:
            continue
        try:
            got = arcgis(M.COUNTY_STREAMS, "NAME IS NOT NULL AND NAME <> ''", "NAME", 0.00003, (min(xs), min(ys), max(xs), max(ys)))
        except Exception as e:   # noqa: BLE001
            print(f"  County streams in {title(w['name'])} unavailable ({type(e).__name__})", flush=True)
            continue
        for f in got:
            key = json.dumps(f["geometry"]["coordinates"][:2])
            if key not in seen:
                seen.add(key)
                out.append(f)
    print(f"{len(out)} named County stream pieces", flush=True)
    return out


def nhd_lines(watersheds, arcgis=None):
    """NHD lines by name (each watershed's name and the FEWS creeks' NHD names), then the named lines in each Bay-area
    watershed's own box. Asked in small pieces: one query for every named line in the Bay side is cut off at the
    service's record limit, which left creeks out the first time."""
    arcgis = arcgis or M.arcgis
    names = sorted({title(w["name"]) for w in watersheds} | {n for v in M.NHD_NAMES.values() for n in v})
    out, seen = [], set()

    def add(feats):
        for f in feats:
            key = json.dumps(f["geometry"]["coordinates"][:2])
            if key not in seen:
                seen.add(key)
                out.append(f)
    for k in range(0, len(names), 20):
        part = names[k:k + 20]
        q = "UPPER(gnis_name) IN (" + ",".join("'" + n.upper().replace("'", "''") + "'" for n in part) + ")"
        add(arcgis(M.NHD, q, "gnis_name,ftype,fcode", 0.00003, L.BAY_BOX))
    print(f"{len(out)} NHD line pieces named like a watershed or FEWS creek", flush=True)
    bx0, by0, bx1, by1 = L.BAY_BOX
    for w in watersheds:
        xs = [p[0] for poly in M.polys_of(w["geometry"]) for p in poly[0]]
        ys = [p[1] for poly in M.polys_of(w["geometry"]) for p in poly[0]]
        if not xs or max(xs) < bx0 or min(xs) > bx1 or max(ys) < by0 or min(ys) > by1:
            continue
        try:
            got = arcgis(M.NHD, "gnis_name IS NOT NULL", "gnis_name,ftype,fcode", 0.00003, (min(xs), min(ys), max(xs), max(ys)))
        except Exception as e:   # noqa: BLE001
            print(f"  NHD lines in {title(w['name'])} unavailable ({type(e).__name__})", flush=True)
            continue
        if len(got) >= 1000:
            print(f"  {title(w['name'])}: {len(got)} NHD lines (may be cut off)", flush=True)
        add(got)
    print(f"{len(out)} NHD line pieces in all", flush=True)
    return out


def main():
    import shoreline_exposure as E
    with open(WATERSHEDS) as f:
        watersheds = [{"name": (ft.get("properties") or {}).get("name") or "", "geometry": ft["geometry"]}
                      for ft in json.load(f).get("features", []) if ft.get("geometry")]
    print(f"{len(watersheds)} watersheds", flush=True)
    shore = E.layer_features(L.SHORE, L.BAY_BOX, lambda u: M.get(u, tries=3))
    print(f"{len(shore)} Shore Inventory lines", flush=True)
    flow = nhd_lines(watersheds)
    places = []
    for layer in (4, 5):
        try:
            for f in M.arcgis(M.PLACES.format(layer), "1=1", "BASENAME", 0.0002):
                places.append({"name": (f.get("properties") or {}).get("BASENAME") or "", "polys": M.polys_of(f["geometry"])})
        except Exception as e:   # noqa: BLE001
            print(f"Census places (layer {layer}) unavailable ({type(e).__name__}); rows without cities", flush=True)
    rows = build(watersheds, shore, flow, places, county_lines(watersheds))
    write(rows)
    for r in rows:
        print(f"  {r['id']} {r['creek']:28s} {r['lat']!s:>9} {r['lon']!s:>10}  {r['method']}", flush=True)
    print(f"Wrote {OUT_CSV} ({len(rows)} rows) and {OUT_GEO}", flush=True)
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
