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

Each closure is tagged "flood" (flooding, flooded, overflow), "storm" (slides, washouts, downed trees, weather) or
"repair" (storm damage, slide or washout repairs, often planned days after the storm). Times are Pacific, "YYYY-MM-DD HH:MM", like storm_tracker.json, so the Storm Tracker can list the closures
during each storm. The log keeps the water year (from Oct 1). Kept as is when a source can't be read.

Writes road_closures.json on the data branch.

Usage: python road_closures.py OUTPUT.json [--min-age MINUTES]
"""

import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
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
            "lat": lat, "lon": lon,
        })
    return out, fm, smc


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


def update(previous, now, fetch=get):
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
    log = prune(log, now)
    return {
        "generated_utc": now.strftime("%Y-%m-%dT%H:%MZ"), "generated": local(now), "county": COUNTY,
        "water_year_start": water_year_start(now), "log_started": (previous or {}).get("log_started") or local(now),
        "active": [c["id"] for c in log if c.get("active")],
        "log": log, "sources": sources, "problems": problems,
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
