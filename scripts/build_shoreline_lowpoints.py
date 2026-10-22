"""Shoreline low points: the stretches of San Mateo County's Bay shoreline where BCDC's Adapting to Rising Tides (ART)
"shoreline overtopping" layer shows the Bay coming over the shoreline at 12, 24 and 36 inches above MHHW.
The Shoreline tab compares each stretch's level with the coming tides (lookups/THRESHOLDS_BASIS.md §4c).

Input (read when the build runs): SFEI's San Francisco Bay Shore Inventory lines for San Mateo County (as published in
BCDC's RSAP open data, SHORE; wetland and channel lines left out) checked every 10 m against BCDC's ART flooded areas at
12, 24 and 36 in (Caltrans map service): where the shoreline is under water, the Bay comes over it at that level, which
is what ART's overtopping layer shows. If this file is there, BCDC's own overtopping lines (a GIS export) are used instead:
  data/shoreline_overtopping.geojson   the overtopping lines for 12, 24 and 36 in, WGS84 (lon/lat), each with a
                                       level_in field (12, 24 or 36); an overtopping-depth field is kept if there is
                                       one (any field with "depth" in its name, in feet)
Writes, for staff review (the same files the Shoreline tab already reads):
  lookups/proposed/shoreline_hotspots.csv           one row per low point, include = review
  data/shoreline_hotspots_candidates.geojson        the overtopped shoreline of each row (lines), for the map

Each low point: the shoreline that first overtops at that level (a stretch already overtopped at a lower level belongs to
that lower level), stretches within MERGE_M of each other joined, at least MIN_LEN_M long, in or next to a San Mateo
County watershed (C/CAG), named after its Census city and watershed. Run by hand: Actions > Build shoreline hotspots.

Usage: python scripts/build_shoreline_lowpoints.py
"""

import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_creek_maps as M  # noqa: E402  (arcgis, polys_of, inside, PLACES)

ROOT = os.path.dirname(HERE)
INPUT = os.path.join(ROOT, "data", "shoreline_overtopping.geojson")
OUT_CSV = os.path.join(ROOT, "lookups", "proposed", "shoreline_hotspots.csv")
OUT_GEO = os.path.join(ROOT, "data", "shoreline_hotspots_candidates.geojson")
WATERSHEDS = os.path.join(ROOT, "data", "watersheds.geojson")
LEVELS_IN = (12, 24, 36)
STEP_M = 10          # lines are checked at points this far apart
SAME_M = 15          # a point this close to shoreline already overtopped lower down belongs to the lower level
MERGE_M = 200        # stretches at one level closer than this are one low point
MIN_LEN_M = 20       # shorter overtopped stretches are left out
WS_NEAR_M = 600      # this close to a San Mateo County watershed counts as in the county
RSAP_MAP = "7535792221cb4ae5a9f022ff5dbaf94a"   # RSAP Open Data: Physical Conditions Vector (web map)
# SFEI San Francisco Bay Shore Inventory (2016), as published in that RSAP map: the shoreline as lines, by class
SHORE = "https://services2.arcgis.com/4Z9x989NrBVrvFwm/arcgis/rest/services/Physical_Conditions_Vector/FeatureServer/217"
SHORE_SKIP = {"Wetland", "Channel or Opening"}   # marsh edges and creek mouths: water there at high tide is normal
INSIDE_M = 3          # a shoreline point counts as under water only if at least this far inside BCDC's flooded area
BAY_BOX = (-122.53, 37.44, -122.08, 37.72)      # San Mateo County's Bay side, with a margin (lon, lat)
COLUMNS = ["id", "name", "city", "watershed", "lat", "lon", "level_in", "length_m", "max_depth_ft", "stretches",
           "include", "notes", "source", "checked_by", "checked_on"]
SOURCE = "BCDC Adapting to Rising Tides (2017), shoreline overtopping"


def m_per_deg(lat):
    return 111320 * math.cos(math.radians(lat)), 110540


def dist_m(a, b):
    kx, ky = m_per_deg((a[1] + b[1]) / 2)
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * ky)


def lines_of(geom):
    t, c = (geom or {}).get("type"), (geom or {}).get("coordinates") or []
    return [c] if t == "LineString" else c if t == "MultiLineString" else []


def sample(line, step=STEP_M):
    """Points every `step` metres along a line (its own vertices kept), as [(lon, lat)]."""
    pts = [tuple(line[0][:2])]
    for a, b in zip(line, line[1:]):
        d = dist_m(a, b)
        n = max(1, int(d // step))
        pts += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return pts


def level_of(props):
    p = {k.lower(): v for k, v in (props or {}).items()}
    for k in ("level_in", "levelin", "level", "twl_in"):
        if p.get(k) not in (None, ""):
            try:
                return int(round(float(re.findall(r"\d+(?:\.\d+)?", str(p[k]))[0])))
            except (IndexError, ValueError):
                return None
    return None


def depth_of(props):
    for k, v in (props or {}).items():
        if "depth" in k.lower():
            try:
                return float(re.findall(r"-?\d+(?:\.\d+)?", str(v))[-1])
            except (IndexError, ValueError):
                return None
    return None


def level_from_text(t):
    """Inches from a layer name or value: "12 in", "24-inch", "1 ft", "2.0 ft (24 in)", "36"."""
    t = str(t or "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:in\b|inch|\")", t, re.I)
    if m:
        return int(round(float(m.group(1))))
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ft\b|feet|foot|')", t, re.I)
    if m:
        return int(round(float(m.group(1)) * 12))
    return None


def from_rsap(get, box=BAY_BOX):
    """{inches: [(sampled points, depth)]} from the overtopping layers of the RSAP "Physical Conditions Vector" map,
    or None if it has none. Lists every layer it finds."""
    import shoreline_exposure as E   # shapely; only needed here
    info, layers = E.item_layers(RSAP_MAP, get)
    print(f"RSAP map '{info.get('title')}': {len(layers)} layers", flush=True)
    for t, u in layers:
        print(f"  {t} · {u}", flush=True)
    ot = [(t, u) for t, u in layers if re.search(r"overtop", t or "", re.I)]
    if not ot:
        print("No layer with 'overtop' in its name.", flush=True)
        return None
    out = {x: [] for x in LEVELS_IN}
    for t, u in ot:
        fs = E.layer_features(u, box, get)
        fields = sorted({k for _, a in fs for k in a})
        print(f"Using '{t}': {len(fs)} features in the box; fields: {', '.join(fields[:25])}", flush=True)
        lv_name = level_from_text(t)
        for g, a in fs:
            lv = lv_name
            if lv is None:   # one layer for all levels: a level field
                for k, v in a.items():
                    if re.search(r"level|twl|slr|scen|wl\b|water", k, re.I):
                        lv = level_from_text(v) if not isinstance(v, (int, float)) else (int(round(v * 12)) if v <= 10 else int(round(v)))
                        if lv:
                            break
            if lv not in out:
                continue
            for ln in E.lines_only(g):
                c = list(ln.coords)
                if len(c) >= 2:
                    out[lv].append((sample(c), depth_of(a)))
    return out


def from_shore_and_art(get, box=BAY_BOX, log=print):
    """{inches: [(runs of points, depth)]}: San Mateo County's Shore Inventory lines (not wetland or channel), checked
    every STEP_M against BCDC's ART flooded areas at each level (Caltrans map service); a run of points inside the
    flooded area is shoreline the Bay comes over at that level."""
    import shapely
    import shoreline_exposure as E
    import build_shoreline_hotspots as H   # ART layers from the Caltrans service (layers(), features())
    fs = E.layer_features(SHORE, box, get)
    lines, classes = [], {}
    for g, a in fs:
        cls = (a.get("Class") or "").strip()
        if "san mateo" not in str(a.get("Geographic_County") or "").lower():
            continue
        classes[cls] = classes.get(cls, 0) + 1
        if cls in SHORE_SKIP:
            continue
        for ln in E.lines_only(g):
            c = list(ln.coords)
            if len(c) >= 2:
                lines.append((sample(c), cls))
    log("Shore Inventory, San Mateo County: " + ", ".join(f"{k or '(blank)'} {n}" for k, n in sorted(classes.items())) +
        f"; {len(lines)} lines used ({', '.join(sorted(SHORE_SKIP))} left out)")
    lay = H.layers()
    if not all(x in lay for x in LEVELS_IN):
        raise RuntimeError("the ART layers for 12, 24 and 36 in weren't found")
    xs = [p[0] for pts, _ in lines for p in pts]
    ys = [p[1] for pts, _ in lines for p in pts]
    import numpy as np
    X, Y = np.array(xs), np.array(ys)
    out = {}
    for lv in LEVELS_IN:
        feats = H.features(lay[lv])
        hit = np.zeros(len(X), dtype=bool)
        for f in feats:
            for part in E.polygons_only(shapely.geometry.shape(f["geometry"])):
                x0, y0, x1, y1 = part.bounds
                idx = np.nonzero((X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1) & ~hit)[0]
                if not len(idx):
                    continue
                shapely.prepare(part)
                # inside, and still inside INSIDE_M east, west, north and south: not just grazing the edge of the
                # flooded area (the outlines are simplified by a few metres)
                dx, dy = INSIDE_M / (111320 * math.cos(math.radians(37.55))), INSIDE_M / 110540
                ok = shapely.contains_xy(part, X[idx], Y[idx])
                for ox, oy in ((dx, 0), (-dx, 0), (0, dy), (0, -dy)):
                    ok &= shapely.contains_xy(part, X[idx] + ox, Y[idx] + oy)
                hit[idx[ok]] = True
        runs, k = [], 0
        for pts, cls in lines:
            cur = []
            for p in pts:
                if hit[k]:
                    cur.append(p)
                elif cur:
                    runs.append((cur, None)); cur = []
                k += 1
            if cur:
                runs.append((cur, None))
        out[lv] = [(r, d) for r, d in runs if len(r) >= 2]
        log(f"{lv} in: {len(feats)} ART flooded areas; {int(hit.sum())} of {len(X)} shoreline points under water, in {len(out[lv])} stretches")
    return out


def load(path=INPUT):
    """{inches: [(sampled points, depth)]} from the GIS export."""
    with open(path) as f:
        feats = json.load(f).get("features", [])
    out, skipped = {x: [] for x in LEVELS_IN}, 0
    for ft in feats:
        lv = level_of(ft.get("properties"))
        if lv not in out:
            skipped += 1
            continue
        for ln in lines_of(ft.get("geometry")):
            if len(ln) >= 2:
                out[lv].append((sample(ln), depth_of(ft.get("properties"))))
    return out, skipped


class Grid:
    """Points in grid cells, to find the ones near a point quickly."""

    def __init__(self, cell_m):
        self.c, self.cells = cell_m / 111000, {}

    def key(self, p):
        return int(p[0] // self.c), int(p[1] // self.c)

    def add(self, p, v):
        self.cells.setdefault(self.key(p), []).append((p, v))

    def near(self, p, within_m):
        kx, ky = self.key(p)
        r = int(within_m / 111000 / self.c) + 1
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for q, v in self.cells.get((kx + dx, ky + dy), []):
                    if dist_m(p, q) <= within_m:
                        yield q, v


def new_runs(by_level):
    """For each level, the runs of points not already overtopped at a lower level: {inches: [(points, depth)]}."""
    lower, out = Grid(SAME_M * 2), {}
    for lv in sorted(by_level):
        runs = []
        for pts, dep in by_level[lv]:
            cur = []
            for p in pts:
                if next(lower.near(p, SAME_M), None) is None:
                    cur.append(p)
                elif cur:
                    runs.append((cur, dep)); cur = []
            if cur:
                runs.append((cur, dep))
        for pts, _ in by_level[lv]:
            for p in pts:
                lower.add(p, lv)
        out[lv] = [(r, d) for r, d in runs if len(r) >= 2]
    return out


def run_len(r):
    return sum(dist_m(a, b) for a, b in zip(r, r[1:]))


def group(runs):
    """Runs within MERGE_M of each other -> groups (lists of runs)."""
    parent = list(range(len(runs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    g = Grid(MERGE_M)
    for i, (r, _) in enumerate(runs):
        for p in r[:: max(1, len(r) // 20)] + [r[-1]]:
            for _, j in g.near(p, MERGE_M):
                parent[find(i)] = find(j)
        for p in r[:: max(1, len(r) // 20)] + [r[-1]]:
            g.add(p, i)
    out = {}
    for i, run in enumerate(runs):
        out.setdefault(find(i), []).append(run)
    return list(out.values())


def near_poly(pt, poly, within_m):
    return M.inside(pt, poly) or any(dist_m(pt, q) <= within_m for q in poly[0][:: max(1, len(poly[0]) // 400)])


def low_points(by_level, watersheds, places):
    rows = []
    for lv, runs in sorted(new_runs(by_level).items()):
        for g in group(runs):
            length = sum(run_len(r) for r, _ in g)
            if length < MIN_LEN_M:
                continue
            allp = [p for r, _ in g for p in r]
            mx, my = sum(p[0] for p in allp) / len(allp), sum(p[1] for p in allp) / len(allp)
            c = min(allp, key=lambda p: dist_m(p, (mx, my)))   # a point on the shoreline itself
            ws = next((w["name"] for w in watersheds if any(M.inside(c, poly) for poly in w["polys"])), None) or \
                next((w["name"] for w in watersheds if any(near_poly(c, poly, WS_NEAR_M) for poly in w["polys"])), None)
            if not ws:
                continue   # not San Mateo County's shoreline
            city = next((pl["name"] for pl in places if any(M.inside(c, poly) for poly in pl["polys"])), None)
            if not city and places:
                city = min(places, key=lambda pl: min(dist_m(c, q) for poly in pl["polys"] for q in poly[0][::25]))["name"] + " (nearest)"
            deps = [d for _, d in g if d is not None]
            rows.append({"lat": round(c[1], 5), "lon": round(c[0], 5), "level_in": lv, "length_m": round(length),
                         "max_depth_ft": round(max(deps), 1) if deps else "", "stretches": len(g), "city": city or "",
                         "watershed": ws.title(), "_lines": [r for r, _ in g]})
    rows.sort(key=lambda r: (r["level_in"], -r["length_m"]))
    for k, r in enumerate(rows, start=1):
        r.update(id=f"SH-{k:03d}", name=f"{r['city'].replace(' (nearest)', '')} shoreline, {r['watershed']} watershed",
                 include="review", notes="", source=SOURCE)
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
    feats = [{"type": "Feature", "properties": {k: r[k] for k in ("id", "name", "level_in", "length_m")},
              "geometry": {"type": "MultiLineString", "coordinates": [[[round(x, 5), round(y, 5)] for x, y in ln] for ln in r["_lines"]]}}
             for r in rows]
    os.makedirs(os.path.dirname(geo_path), exist_ok=True)
    with open(geo_path, "w") as f:
        json.dump({"type": "FeatureCollection", "source": SOURCE, "features": feats}, f, separators=(",", ":"))


def main():
    if os.path.exists(INPUT):
        by_level, skipped = load()
    else:
        skipped = 0
        try:
            by_level = from_shore_and_art(lambda u: M.get(u, tries=2), log=lambda m: print(m, flush=True))
        except Exception as e:   # noqa: BLE001
            print(f"Shore Inventory or ART layers unavailable: {type(e).__name__}: {str(e)[:300]}", flush=True)
            by_level = None
        if not by_level or not any(by_level.values()):
            print(f"No overtopping lines found. Export the ART shoreline overtopping lines for 12, 24 and 36 in from GIS "
                  f"(WGS84 GeoJSON, a level_in field) as {os.path.relpath(INPUT, ROOT)}. Nothing written.", flush=True)
            return 1
    print("Overtopping lines: " + ", ".join(f"{x} in = {len(by_level[x])}" for x in LEVELS_IN) +
          (f" ({skipped} features without a level_in of 12, 24 or 36 left out)" if skipped else ""), flush=True)
    places = []
    for layer in (4, 5):   # Census cities, then unincorporated places
        try:
            for f in M.arcgis(M.PLACES.format(layer), "1=1", "BASENAME", 0.0002):
                places.append({"name": (f.get("properties") or {}).get("BASENAME") or "", "polys": M.polys_of(f["geometry"])})
        except Exception as e:   # noqa: BLE001
            print(f"Census places (layer {layer}) unavailable ({type(e).__name__}); names without them", flush=True)
    rows = low_points(by_level, load_watersheds(), places)
    write(rows)
    for x in LEVELS_IN:
        sel = [r for r in rows if r["level_in"] == x]
        print(f"{x} in: {len(sel)} low points, {sum(r['length_m'] for r in sel) / 1000:.1f} km of shoreline", flush=True)
    print(f"Wrote {OUT_CSV} ({len(rows)} rows) and {OUT_GEO}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
