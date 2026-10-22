"""Shoreline low points: the stretches of San Mateo County's Bay shoreline where BCDC's Adapting to Rising Tides (ART)
"shoreline overtopping" layer shows the Bay coming over the shoreline at 12, 24 and 36 inches above MHHW.
The Shoreline tab compares each stretch's level with the coming tides (lookups/THRESHOLDS_BASIS.md §4c).

Input (made once in GIS from the ART geodatabase, explorer.adaptingtorisingtides.org/download):
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
    if not os.path.exists(INPUT):
        print(f"No {os.path.relpath(INPUT, ROOT)} yet: export the ART shoreline overtopping lines for 12, 24 and 36 in from "
              "GIS (WGS84 GeoJSON, a level_in field) and upload it to the data folder. Nothing written.", flush=True)
        return 1
    by_level, skipped = load()
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
