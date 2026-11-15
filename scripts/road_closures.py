"""State highway closures from storms in San Mateo County, from Caltrans, for the Storm Tracker (staff, 2026-11-14).

Two public Caltrans sources, no key needed:
  1. Lane Closure System (LCS), District 4 (CWWP2, updated every 5 minutes): every lane, ramp and road closure Caltrans
     has approved, planned and current. Emergency closures are entered with a type of work such as "Flooding",
     "Roadway Flooding", "Flooded Areas", "River Overflow/Flood Area", "Slide - Mud/Dirt/Rock" or "Storm Event".
     Kept: closures in San Mateo County whose type of work is storm-related (STORM_RX), once they have started
     (code 1097) and not cancelled (code 1022). Ended when Caltrans logs code 1098 or the closure leaves the feed.
     https://cwwp2.dot.ca.gov/documentation/lcs/lcs.htm
  2. Caltrans Emergency Road Closures (Division of Maintenance GIS layer, updated as the HQ Communication Center logs
     closures from slides, flooding, washouts, adverse weather and so on). The layer's address is read from its ArcGIS
     item (ERC_ITEM) and its fields are found by name, since Caltrans doesn't publish them; the fields found are kept in
     road_closures.json ("sources") so they can be checked. Kept: San Mateo County (county field, or else inside
     SMC_BBOX) and storm-related text.
Both cover state highways only (101, 280, 1, 35, 82, 84, 92, 380 and their ramps), not county or city roads.

Where (staff, 2026-11-14): each closure's points (the Lane Closure System's begin and end, or points along the Emergency
Road Closures line) are placed in San Mateo County's watersheds (data/watersheds.geojson, the County's Flows to Bay
watershed layer; a point outside every watershed takes the nearest one). Each closure gets its watersheds, the
monitored creeks they belong to (WS_CREEK) and its side, Bayside or Coastside (BAY_WS). The Storm Tracker lists a
storm's closures in that creek's watershed first, then the rest of the same side. Postmiles aren't needed: both feeds
give coordinates.

Each closure is tagged "flood" (flooding, flooded, overflow), "storm" (slides, washouts, downed trees, weather) or
"repair" (storm damage, slide or washout repairs, often planned days after the storm). Times are Pacific, "YYYY-MM-DD HH:MM", like storm_tracker.json, so the Storm Tracker can list the closures
during each storm. The log keeps the water year (from Oct 1). Kept as is when a source can't be read.

City notices (staff, 2026-11-14): cities' own posts about street closures, which Caltrans' feeds don't have. Each city
in lookups/city_feeds.csv is an RSS or Atom feed (CivicPlus sites such as San Bruno's publish News Flash and Alert
Center feeds). A post counts when its title or text names a closure (CLOSE_RX) and a storm cause (STORM_RX or rain or
water). It's logged as a notice at the time it was posted, with its link, and placed by the city's row (creeks, side),
since a post names streets in words. South San Francisco's site isn't CivicPlus and has no feed found yet; SMC Alert
has no public feed, and the County uses Genasys Protect for evacuations only.

Writes road_closures.json on the data branch.

Usage: python road_closures.py OUTPUT.json [--min-age MINUTES]
"""

import csv
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
PAC = ZoneInfo("America/Los_Angeles")
LCS_URL = "https://cwwp2.dot.ca.gov/data/d4/lcs/lcsStatusD04.json"
ERC_ITEM = "https://www.arcgis.com/sharing/rest/content/items/c933349c56f640edba968f208063eee0?f=json"
COUNTY = "San Mateo"
SMC_BBOX = (-122.53, 37.10, -122.08, 37.71)   # lon/lat box around San Mateo County (only when a record has no county)
FLOOD_RX = re.compile(r"flood|overflow|high water|standing water|water (?:over|on) (?:the )?road", re.I)
STORM_RX = re.compile(r"flood|overflow|high water|standing water|wash.?out|slip.?out|slide|mud|rock ?fall|sink ?hole|storm|"
                      r"inclement|weather related|adverse weather|downed tree|fallen tree|tree down|road damage", re.I)
NOT_STORM_RX = re.compile(r"snow|\bic(?:e|ing)\b|winter|fire|seasonal|chain", re.I)
STRONG_RX = re.compile(r"flood|overflow|storm|wash.?out|slip.?out|mud", re.I)   # storm words that win over NOT_STORM_RX
REPAIR_RX = re.compile(r"repair", re.I)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATERSHEDS = os.path.join(ROOT, "data", "watersheds.geojson")
# County watersheds that drain to each monitored creek (as in build_creek_maps.py: San Bruno Creek's upper creek is
# El Zanjon Creek; Green Hills Creek drains to Highline Creek; Pescadero and Butano share one watershed)
WS_CREEK = {"COLMA CREEK": ["colma"], "SAN BRUNO CREEK": ["sanbruno"], "EL ZANJON CREEK": ["sanbruno"], "BELMONT CREEK": ["belmont"],
            "ATHERTON CREEK": ["atherton"], "SAN FRANCISQUITO CREEK": ["sanfrancisquito"], "SAN MATEO CREEK": ["sanmateo"],
            "HIGHLINE CREEK": ["greenhills"], "PILARCITOS CREEK": ["pilarcitos"], "SAN GREGORIO CREEK": ["sangregorio"],
            "PESCADERO-BUTANO CREEK": ["pescadero", "butano"]}
# the watersheds that drain to the Bay; every other County watershed drains to the ocean
BAY_WS = {"GUADALUPE VALLEY", "COLMA CREEK", "SAN BRUNO CREEK", "EL ZANJON CREEK", "HIGHLINE CREEK", "EL PORTAL CREEK", "MILLS CREEK",
          "EASTON CREEK", "SANCHEZ CREEK", "GUANOLD", "BOREL CREEK", "SEAL CREEK", "SEAL SLOUGH", "BAY SLOUGH", "SAN MATEO CREEK",
          "LAUREL CREEK", "BELMONT SLOUGH", "BELMONT CANAL", "BELMONT CREEK", "STEINBERGER SLOUGH", "PULGAS CREEK", "GREENWOOD DRAINAGE",
          "CORDILLERAS CREEK", "REDWOOD CREEK", "RAVENSWOOD SLOUGH", "ATHERTON CREEK", "SAN FRANCISQUITO CREEK"}
CREEK_SIDE = {"colma": "bay", "sanbruno": "bay", "belmont": "bay", "atherton": "bay", "sanfrancisquito": "bay", "sanmateo": "bay",
              "greenhills": "bay", "pilarcitos": "coast", "sangregorio": "coast", "pescadero": "coast", "butano": "coast"}
NEAREST_MAX_DEG = 0.02   # a point outside every watershed (Bay fill, a beach) takes the nearest one within about 2 km
CITY_FEEDS = os.path.join(ROOT, "lookups", "city_feeds.csv")
CLOSE_RX = re.compile(r"\bclos(?:ed|ure|ures|ing)\b|detour|impassable|avoid the area|shut down|blocked|not passable", re.I)
CITY_STORM_RX = re.compile(r"flood|storm|rain|water|slide|mud|tree|wash.?out|sink ?hole|creek", re.I)
KEEP_DAYS_AFTER_END = 400   # the water year is pruned separately; this is a backstop
MAX_LOG = 600


def get(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def local(t):
    """UTC datetime -> Pacific 'YYYY-MM-DD HH:MM'."""
    return t.astimezone(PAC).strftime("%Y-%m-%d %H:%M") if t else None


def from_epoch(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    if v > 1e11:          # milliseconds (ArcGIS)
        v /= 1000.0
    if v <= 0 or v > 32503000000:   # 2999-12-31 is LCS's "indefinite"
        return None
    return dt.datetime.fromtimestamp(v, dt.timezone.utc)


def truthy(v):
    return v is True or str(v).strip().lower() in ("true", "1", "yes", "y")


def is_storm(text):
    t = text or ""
    return bool(STORM_RX.search(t)) and not (NOT_STORM_RX.search(t) and not STRONG_RX.search(t))


def kind(text):
    """flood (flooding, overflow), repair (storm damage repairs, often planned days later) or storm (slides, washouts...)."""
    t = text or ""
    return "flood" if FLOOD_RX.search(t) else "repair" if REPAIR_RX.search(t) else "storm"


def water_year_start(now):
    p = now.astimezone(PAC)
    y = p.year if p.month >= 10 else p.year - 1
    return f"{y}-10-01 00:00"


# ---- where: watersheds, creeks, Bayside or Coastside
_WS = None


def watersheds(path=WATERSHEDS):
    """[(NAME, [polygons as lists of rings of (lon, lat)], bbox)] from the County watershed GeoJSON."""
    global _WS
    if _WS is None or path != WATERSHEDS:
        with open(path) as f:
            j = json.load(f)
        ws = []
        for ft in j.get("features") or []:
            g = ft.get("geometry") or {}
            polys = [g["coordinates"]] if g.get("type") == "Polygon" else g.get("coordinates") or [] if g.get("type") == "MultiPolygon" else []
            pts = [p for poly in polys for ring in poly for p in ring]
            if not pts:
                continue
            ws.append((str(ft["properties"].get("name") or "").upper(), polys,
                       (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))))
        if path != WATERSHEDS:
            return ws
        _WS = ws
    return _WS


def in_ring(x, y, ring):
    inside = False
    for i in range(len(ring)):
        x1, y1 = ring[i - 1][:2]
        x2, y2 = ring[i][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def watershed_at(lat, lon, ws):
    for name, polys, bb in ws:
        if bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]:
            for poly in polys:
                if poly and in_ring(lon, lat, poly[0]) and not any(in_ring(lon, lat, h) for h in poly[1:]):
                    return name
    best, bd = None, NEAREST_MAX_DEG ** 2
    for name, polys, bb in ws:
        if bb[0] - NEAREST_MAX_DEG <= lon <= bb[2] + NEAREST_MAX_DEG and bb[1] - NEAREST_MAX_DEG <= lat <= bb[3] + NEAREST_MAX_DEG:
            for poly in polys:
                for p in poly[0]:
                    d = (p[0] - lon) ** 2 + ((p[1] - lat) / 1.26) ** 2   # 1 deg of latitude is about 1.26 deg of longitude here
                    if d < bd:
                        best, bd = name, d
    return best


def locate(c, ws=None):
    """Set the closure's watersheds, creeks and side ("bay", "coast", "both" or None) from its points."""
    ws = ws if ws is not None else watersheds()
    names = []
    for p in c.get("pts") or ([[c["lat"], c["lon"]]] if c.get("lat") is not None and c.get("lon") is not None else []):
        try:
            n = watershed_at(float(p[0]), float(p[1]), ws)
        except (TypeError, ValueError):
            n = None
        if n and n not in names:
            names.append(n)
    sides = sorted({"bay" if n in BAY_WS else "coast" for n in names})
    c["watersheds"] = [n.title() for n in names]
    c["creeks"] = [k for n in names for k in WS_CREEK.get(n, [])]
    c["side"] = sides[0] if len(sides) == 1 else "both" if sides else None
    return c


# ---- 1. Lane Closure System, District 4
def lcs_closures(text, now):
    """CWWP2 LCS JSON -> (closures, count of San Mateo records)."""
    j = json.loads(text)
    rows = j.get("data") if isinstance(j, dict) else j
    out, smc = [], 0
    for r in rows or []:
        l = r.get("lcs", r) if isinstance(r, dict) else {}
        loc, cl = l.get("location") or {}, l.get("closure") or {}
        b, e = loc.get("begin") or {}, loc.get("end") or {}
        if COUNTY.lower() not in str(b.get("beginCounty", "")).lower() and COUNTY.lower() not in str(e.get("endCounty", "")).lower():
            continue
        smc += 1
        work = str(cl.get("typeOfWork") or "")
        if not is_storm(work):
            continue
        ts = cl.get("closureTimestamp") or {}
        c97, c98, c22 = cl.get("code1097") or {}, cl.get("code1098") or {}, cl.get("code1022") or {}
        if truthy(c22.get("isCode1022")):
            continue
        started = from_epoch((c97.get("code1097Timestamp") or {}).get("code1097Epoch")) if truthy(c97.get("isCode1097")) else None
        plan_start, plan_end = from_epoch(ts.get("closureStartEpoch")), from_epoch(ts.get("closureEndEpoch"))
        if not started:
            if plan_start and plan_start <= now and (not plan_end or plan_end > now) and "isCode1097" not in c97:
                started = plan_start   # current by its planned times; LCS hasn't logged 1097 (rare for emergencies)
            else:
                continue                # planned, not started
        ended = from_epoch((c98.get("code1098Timestamp") or {}).get("code1098Epoch")) if truthy(c98.get("isCode1098")) else None
        where = b.get("beginLocationName") or b.get("beginFreeFormDescription") or ""
        to = e.get("endLocationName") or ""
        if to and to != where:
            where = f"{where} to {to}"
        route = str(b.get("beginRoute") or "").strip()
        out.append({
            "id": "lcs:" + str(l.get("index") or f"{cl.get('closureID')}-{cl.get('logNumber')}"),
            "source": "Caltrans Lane Closure System",
            "route": route, "dir": loc.get("travelFlowDirection") or b.get("beginDirection") or "",
            "facility": cl.get("facility") or "", "closure": cl.get("typeOfClosure") or "",
            "lanes": f"{cl.get('lanesClosed')} of {cl.get('totalExistingLanes')}" if cl.get("lanesClosed") not in (None, "") else "",
            "where": where.strip(), "place": b.get("beginNearbyPlace") or "",
            "what": work, "kind": kind(work),
            "started": local(started), "ended": local(ended),
            "est_end": None if truthy(cl.get("isClosureEndIndefinite")) else local(plan_end),
            "lat": b.get("beginLatitude"), "lon": b.get("beginLongitude"),
            "pts": [[p.get(k + "Latitude"), p.get(k + "Longitude")] for p, k in ((b, "begin"), (e, "end")) if p.get(k + "Latitude") not in (None, "")],
        })
    return out, smc


# ---- 2. Caltrans Emergency Road Closures (ArcGIS layer)
def erc_service(fetch, cached=None):
    """The layer's query address, from its ArcGIS item (cached in the JSON after the first read)."""
    if cached:
        return cached
    item = json.loads(fetch(ERC_ITEM))
    url = (item.get("url") or "").rstrip("/")
    if not url:
        raise ValueError("ArcGIS item has no service url")
    if not re.search(r"/\d+$", url):
        url += "/0"
    return url


def pick(fields, rx, types=None):
    for f in fields:
        if re.search(rx, f["name"], re.I) and (not types or f.get("type") in types):
            return f["name"]
    return None


def mid_point(g):
    if not g:
        return None, None
    if "x" in g:
        return g.get("y"), g.get("x")
    pts = [p for path in (g.get("paths") or g.get("rings") or []) for p in path] or g.get("points") or []
    if not pts:
        return None, None
    p = pts[len(pts) // 2]
    return p[1], p[0]


def line_points(g, most=25):
    """Up to `most` [lat, lon] points along the closure's line (or its one point)."""
    if not g:
        return []
    if "x" in g:
        return [[g.get("y"), g.get("x")]]
    pts = [p for path in (g.get("paths") or g.get("rings") or []) for p in path] or g.get("points") or []
    step = max(1, len(pts) // most)
    return [[p[1], p[0]] for p in pts[::step]] + ([[pts[-1][1], pts[-1][0]]] if pts and (len(pts) - 1) % step else [])


def erc_closures(text, now):
    """ArcGIS query JSON -> (closures, field map used, count of San Mateo records)."""
    j = json.loads(text)
    if "error" in j:
        raise ValueError(f"ArcGIS error: {j['error']}"[:200])
    fields = j.get("fields") or []
    date_t = ("esriFieldTypeDate", "esriFieldTypeDateOnly", "esriFieldTypeTimestampOffset")
    fm = {
        "county": pick(fields, r"county|cnty"),
        "route": pick(fields, r"^route|rte|hwy|highway"),
        "dir": pick(fields, r"dir"),
        "where": pick(fields, r"locat|descr|between|limits|from"),
        "type": pick(fields, r"restrict|type|cause|reason|incident"),
        "detour": pick(fields, r"detour"),
        "start": pick(fields, r"start|begin|closed|clos.*(date|time)|report", date_t),
        "end": pick(fields, r"open|reopen|end|estim|eto", date_t),
        "id": pick(fields, r"globalid|incident.?(id|num)|closure.?id|objectid|^fid$"),
        "status": pick(fields, r"status", ("esriFieldTypeString",)),
    }
    text_fields = [f["name"] for f in fields if f.get("type") == "esriFieldTypeString"]
    out, smc = [], 0
    for ft in j.get("features") or []:
        a, g = ft.get("attributes") or {}, ft.get("geometry")
        lat, lon = mid_point(g)
        if fm["county"] and a.get(fm["county"]) not in (None, ""):
            cv = str(a.get(fm["county"]))
            if not (COUNTY.lower() in cv.lower() or cv.strip().upper() in ("SM", "SMA")):
                continue
        elif not (lat and lon and SMC_BBOX[1] <= lat <= SMC_BBOX[3] and SMC_BBOX[0] <= lon <= SMC_BBOX[2]):
            continue
        smc += 1
        if fm["status"] and re.search(r"re-?opened?|cleared|lifted|^open$|inactive|ended", str(a.get(fm["status"]) or "").strip(), re.I):
            continue    # the record says the road has reopened: no longer a closure now
        blob = " ".join(str(a.get(n) or "") for n in text_fields)
        what = str(a.get(fm["type"]) or "") if fm["type"] else ""
        if not is_storm(what or blob):
            continue
        started = from_epoch(a.get(fm["start"])) if fm["start"] else None
        rid = a.get(fm["id"]) if fm["id"] else None
        if rid in (None, ""):
            rid = hashlib.sha1(f"{a.get(fm['route'])}|{a.get(fm['where'])}|{started}".encode()).hexdigest()[:12]
        out.append({
            "id": f"erc:{rid}", "source": "Caltrans Emergency Road Closures",
            "route": str(a.get(fm["route"]) or "").strip() if fm["route"] else "",
            "dir": str(a.get(fm["dir"]) or "") if fm["dir"] else "",
            "facility": "", "closure": "Full", "lanes": "",
            "where": str(a.get(fm["where"]) or "").strip() if fm["where"] else "",
            "place": "", "what": what or (STORM_RX.search(blob).group(0).title() if STORM_RX.search(blob) else ""),
            "kind": kind(what or blob),
            "detour": str(a.get(fm["detour"]) or "") if fm["detour"] else "",
            "started": local(started) or local(now), "ended": None,
            "est_end": local(from_epoch(a.get(fm["end"]))) if fm["end"] else None,
            "lat": lat, "lon": lon, "pts": line_points(g),
        })
    return out, fm, smc


# ---- 3. City notices (lookups/city_feeds.csv)
def read_feeds(path=None):
    path = path or CITY_FEEDS
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{"city": r["city"].strip(), "url": r["url"].strip(), "creeks": (r.get("creeks") or "").split(),
                 "side": (r.get("side") or "").strip() or None}
                for r in csv.DictReader(f) if (r.get("city") or "").strip() and (r.get("url") or "").strip() and not r["city"].startswith("#")]


def plain(t):
    return re.sub(r"\s+([.,;:!?])", r"\1", re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t or "")))).strip()


def feed_items(text):
    """RSS 2.0 or Atom -> [{title, link, text, at (UTC datetime or None)}]."""
    root = ET.fromstring(text.encode("utf-8") if isinstance(text, str) else text)
    tag = lambda e: e.tag.split("}")[-1]
    out = []
    for it in root.iter():
        if tag(it) not in ("item", "entry"):
            continue
        d = {}
        for ch in it:
            n = tag(ch)
            if n == "link":
                d["link"] = (ch.text or ch.get("href") or "").strip()
            elif n in ("title", "description", "summary", "content", "pubDate", "published", "updated", "guid"):
                d.setdefault(n, ch.text or "")
        at = None
        for k in ("pubDate", "published", "updated"):
            v = (d.get(k) or "").strip()
            if not v:
                continue
            try:
                at = email.utils.parsedate_to_datetime(v) if k == "pubDate" else dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
                if at.tzinfo is None:
                    at = at.replace(tzinfo=PAC)
                break
            except (TypeError, ValueError):
                pass
        out.append({"title": plain(d.get("title")), "link": d.get("link") or (d.get("guid") or "").strip(),
                    "text": plain(d.get("description") or d.get("summary") or d.get("content")), "at": at})
    return out


def city_notices(text, feed, now):
    out = []
    for it in feed_items(text):
        blob = it["title"] + " " + it["text"]
        if not (CLOSE_RX.search(blob) and CITY_STORM_RX.search(blob)) or NOT_STORM_RX.search(it["title"]) and not STRONG_RX.search(blob):
            continue
        at = it["at"] or now
        snippet = it["text"][:240] + ("…" if len(it["text"]) > 240 else "")
        out.append({
            "id": "city:" + hashlib.sha1(f"{feed['city']}|{it['link'] or it['title']}".encode()).hexdigest()[:14],
            "source": "City of " + feed["city"], "notice": True,
            "route": "", "dir": "", "facility": "", "closure": "", "lanes": "", "place": feed["city"],
            "where": it["title"], "what": snippet, "link": it["link"], "kind": "flood" if FLOOD_RX.search(blob) else "storm",
            "started": local(at), "ended": local(at), "est_end": None, "lat": None, "lon": None, "pts": [],
            "creeks": feed["creeks"], "side": feed["side"], "watersheds": [],
        })
    return out


# ---- the log
def merge(log, current, source, now):
    """Add or refresh `current` (one source's closures now) in `log`; close the source's open ones that left the feed."""
    by = {c["id"]: c for c in log}
    seen = set()
    for c in current:
        seen.add(c["id"])
        old = by.get(c["id"])
        if old:
            keep = {"first_seen": old.get("first_seen"), "started": old.get("started") or c["started"]}
            old.update(c)
            old.update(keep)
            old["last_seen"] = local(now)
            if c.get("ended"):
                old["active"] = False
            else:
                old["active"] = True
                old.pop("gone", None)
        else:
            c = dict(c, first_seen=local(now), last_seen=local(now), active=not c.get("ended"))
            log.append(c)
            by[c["id"]] = c
    for c in log:
        if c.get("source") == source and c.get("active") and c["id"] not in seen:
            c["active"] = False
            c["ended"] = c.get("ended") or c.get("last_seen")
            c["gone"] = True     # left the feed: ended at the last time it was seen (within one run)
    return log


def prune(log, now):
    wy = water_year_start(now)
    cut = local(now - dt.timedelta(days=KEEP_DAYS_AFTER_END))
    log = [c for c in log if c.get("active") or ((c.get("ended") or c.get("last_seen") or "") >= wy and (c.get("ended") or "9") >= cut)]
    log.sort(key=lambda c: c.get("started") or "")
    return log[-MAX_LOG:]


def update(previous, now, fetch=get, feeds=None):
    prev_src = (previous or {}).get("sources") or {}
    log = [dict(c) for c in (previous or {}).get("log") or []]
    sources, problems = {}, []
    try:
        cur, smc = lcs_closures(fetch(LCS_URL), now)
        merge(log, cur, "Caltrans Lane Closure System", now)
        sources["lcs"] = {"ok": True, "url": LCS_URL, "checked": local(now), "san_mateo_records": smc, "storm_now": len(cur)}
    except Exception as e:  # noqa: BLE001
        problems.append(f"Lane Closure System: {type(e).__name__}: {e}"[:200])
        sources["lcs"] = dict(prev_src.get("lcs") or {"url": LCS_URL}, ok=False)
    try:
        svc = erc_service(fetch, (prev_src.get("erc") or {}).get("service"))
        q = svc + "/query?" + urllib.parse.urlencode({"where": "1=1", "outFields": "*", "outSR": "4326", "returnGeometry": "true", "f": "json"})
        cur, fm, smc = erc_closures(fetch(q), now)
        merge(log, cur, "Caltrans Emergency Road Closures", now)
        sources["erc"] = {"ok": True, "service": svc, "checked": local(now), "fields": fm, "san_mateo_records": smc, "storm_now": len(cur)}
    except Exception as e:  # noqa: BLE001
        problems.append(f"Emergency Road Closures: {type(e).__name__}: {e}"[:200])
        sources["erc"] = dict(prev_src.get("erc") or {}, ok=False)
        if "service" in sources["erc"] and "item" in str(e).lower():
            sources["erc"].pop("service")
    for i, fd in enumerate(read_feeds() if feeds is None else feeds):
        key = f"city:{fd['city']}:{i + 1}"
        try:
            cur = city_notices(fetch(fd["url"]), fd, now)
            merge(log, cur, "City of " + fd["city"], now)
            sources[key] = {"ok": True, "url": fd["url"], "checked": local(now), "storm_items": len(cur)}
        except Exception as e:  # noqa: BLE001
            problems.append(f"{fd['city']} feed: {type(e).__name__}: {e}"[:200])
            sources[key] = dict(prev_src.get(key) or {"url": fd["url"]}, ok=False)
    log = prune(log, now)
    try:
        ws = watersheds()
        for c in log:
            if not c.get("notice"):     # a city notice keeps its city's place (lookups/city_feeds.csv)
                locate(c, ws)
    except (OSError, ValueError, KeyError) as e:
        problems.append(f"watersheds: {type(e).__name__}: {e}"[:200])
    return {
        "generated_utc": now.strftime("%Y-%m-%dT%H:%MZ"), "generated": local(now), "county": COUNTY,
        "water_year_start": water_year_start(now), "log_started": (previous or {}).get("log_started") or local(now),
        "active": [c["id"] for c in log if c.get("active")],
        "log": log, "sources": sources, "problems": problems,
        "creek_side": CREEK_SIDE,
    }


def main(argv):
    path = argv[1]
    min_age = float(argv[argv.index("--min-age") + 1]) if "--min-age" in argv else 0
    previous = {}
    try:
        with open(path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        pass
    now = dt.datetime.now(dt.timezone.utc)
    last = previous.get("generated_utc")
    if last and min_age and now - dt.datetime.strptime(last, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=min_age):
        print(f"road closures: last run {last}, younger than {min_age:g} min; kept")
        return 0
    result = update(previous, now)
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    for k, s in result["sources"].items():
        if k.startswith("city:"):
            print(f"{k}: " + ("ok" if s.get("ok") else "NOT READ") + f", {s.get('storm_items', '?')} storm closure posts in the feed")
            continue
        print(f"{k}: " + ("ok" if s.get("ok") else "NOT READ") + f", {s.get('san_mateo_records', '?')} San Mateo records, {s.get('storm_now', '?')} storm closures now"
              + (f", fields {s.get('fields')}" if k == "erc" and s.get("ok") else ""))
    for c in result["log"]:
        if c.get("active"):
            print(f"  active: {c['route']} {c['dir']} {c['where']} - {c['what']} since {c['started']}")
    for p in result["problems"]:
        print("problem:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
