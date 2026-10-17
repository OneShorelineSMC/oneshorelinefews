#!/usr/bin/env python3
"""
Read every public OneShoreline Early Warning (OneRain) site and save a summary for the site maps
(SiteMap.html and the kiosk's Map tab).

For each site it records the location, each sensor's latest reading, and a short recent history for the
little graphs. It reads only what OneRain shows a signed-out visitor ("Guest"), so sites or sensors that
aren't public never appear on the map.

Usage:  python fetch_sites.py OUTPUT.json [--min-age MINUTES]
  --min-age  skip the download if OUTPUT.json is newer than this (lets it share the 5-minute job while
             only running every 15 minutes)

If a site can't be read, its previous entry in OUTPUT.json is kept and marked with the error.
"""
import datetime as dt
import html as htmllib
import json
import re
import sys
import time
import urllib.parse

import os

from creek_config import CREEKS, THRESHOLD_ERRORS, TIDE_STATIONS, map_thresholds
from fetch_onerain import SITE, TZ, Session, parse_readings, sensor_page, to_time

# OneRain's tide stations report in MLLW. The public pages show NAVD88 only, so tide readings are shifted by the
# station's NOAA datum difference (NAVD88 minus MLLW). Redwood City 9414523: NAVD88 is 1.18 ft above MLLW.
# OneRain tide sites numbered like a NOAA station: their readings (ft MLLW) are shown in ft NAVD88 using the
# MLLW-to-NAVD88 difference in lookups/tide_stations.csv
TIDE_MLLW_TO_NAVD88 = {k: v["mllw_to_navd88"] for k, v in TIDE_STATIONS.items() if v["mllw_to_navd88"] is not None}

HISTORY_HOURS = 24   # history kept per sensor for the small graphs and the 24-hour rain total
RAIN_WINDOWS_H = (1, 3, 6)   # shorter rain totals on the sensor map (with rain24)
MAX_POINTS = 96      # graph points kept per sensor (keeps the file small)
PAUSE_SEC = 0.25     # pause between requests, to be gentle on OneRain

# Housekeeping sensors that aren't useful to the public (matched against the sensor name).
SKIP_SENSORS = re.compile(r"batter|volt|signal|rssi|solar|charg|enclosure|door|logger|modem|status"
                          r"|\d+\s*-?\s*h(ou)?r\b", re.I)   # also OneRain's "4 Hr Accumulation"-style roll-ups

# Alert levels drawn on the map come from the creek gauges and thresholds in creek_config.py.
THRESHOLDS = map_thresholds()   # if thresholds.csv has a problem, main() uses the ones in creeks.json instead


def clean(fragment):
    return " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def list_sites(page):
    """Sites on the public Sites list: [(site_id, site_uuid, name, number), ...]."""
    out = []
    for m in re.finditer(r'href="/site/\?site_id=(\d+)&amp;site=([0-9a-f-]+)">([^<]+)</a>\s*(?:<small>\(([^)]*)\)</small>)?', page):
        out.append((int(m.group(1)), m.group(2), clean(m.group(3)), (m.group(4) or "").strip()))
    return out


def parse_site(page):
    """Location and sensor tiles from a site page."""
    lat = re.search(r"var lat\s*=\s*(-?\d+(?:\.\d+)?)", page)
    lon = re.search(r"var lon\s*=\s*(-?\d+(?:\.\d+)?)", page)
    if not (lat and lon):  # fallback: the coordinates printed under the small map
        m = re.search(r'find_site_id=[^"]*">\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*<', page)
        lat, lon = (m.group(1), m.group(2)) if m else (None, None)
    else:
        lat, lon = lat.group(1), lon.group(1)
    sensors = []
    for m in re.finditer(r'<a href="(/sensor/\?[^"]+)"><div class="card tile"(.*?)</div></a>', page, flags=re.S):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(htmllib.unescape(m.group(1))).query)
        body = m.group(2)
        head = re.search(r'class="card-heading[^"]*">(.*?)<span class="float-right', body, flags=re.S)
        name, number = "", ""
        if head:
            h = head.group(1)
            sm = re.search(r"<small>\(([^)]*)\)</small>", h)
            number = sm.group(1) if sm else ""
            name = clean(re.sub(r"<small>.*?</small>", "", h, flags=re.S))
        val = re.search(r'<div class="h3">\s*(.*?)\s*</div>', body, flags=re.S)
        value, unit = None, ""
        if val:
            um = re.search(r"<small>(.*?)</small>", val.group(1), flags=re.S)
            unit = clean(um.group(1)) if um else ""
            num = re.search(r"-?\d+(?:\.\d+)?", clean(re.sub(r"<small>.*?</small>", "", val.group(1), flags=re.S)))
            value = float(num.group(0)) if num else None
        t = re.search(r'<time[^>]*title="(\d{4}-\d\d-\d\d \d\d:\d\d(?::\d\d)?)"', body)
        sensors.append({
            "name": name, "number": number, "unit": unit, "value": value,
            "time": t.group(1)[:16] if t else None,
            "device_id": int(q.get("device_id", ["0"])[0]), "device": q.get("device", [""])[0],
        })
    return (float(lat) if lat else None, float(lon) if lon else None), sensors


def rain_kind(sensor):
    n = sensor["name"].lower()
    if "rain" not in n and "precip" not in n:
        return None
    return "accumulation" if re.search(r"accum|total|cumul", n) else "increment"


def flot_series(session, site_id, site, sensor):
    """Recent readings from the same feed OneRain uses for the small graphs on site pages."""
    url = SITE + "/export/flot/?" + urllib.parse.urlencode({
        "method": "sensor", "site_id": site_id, "device_id": sensor["device_id"], "site": site, "device": sensor["device"]})
    data = json.loads(session.get(url))
    if isinstance(data, list):
        data = data[0] if data and isinstance(data[0], dict) else {"data": data}
    pts = [(float(p[0]), float(p[1])) for p in data.get("data", []) if p and len(p) >= 2 and p[1] is not None]
    if not pts:
        return []
    # Graph times are milliseconds, but whether they're UTC or Pacific isn't documented. Line the newest one
    # up with the "latest reading" time shown on the page (which is Pacific) to find the offset.
    pts.sort()
    newest = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=pts[-1][0])
    offset = dt.timedelta(0)
    if sensor["time"]:
        diff = (to_time(sensor["time"]) - newest).total_seconds() / 3600
        offset = dt.timedelta(hours=round(diff))
    return [(dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=ms) + offset, v) for ms, v in pts]


def sensor_history(session, site_id, site, sensor, start, end):
    try:
        return flot_series(session, site_id, site, sensor), "graph"
    except Exception as e:
        print(f"      graph feed unavailable for {sensor['name']} ({type(e).__name__}); trying sensor page", file=sys.stderr)
    s = {"site_id": site_id, "site": site, "device_id": sensor["device_id"], "device": sensor["device"]}
    return sorted(parse_readings(session.get(sensor_page(s, start, end)))), "page"


def summarize(sensor, hist, start, now):
    hist = [(t, v) for t, v in hist if start <= t <= now + dt.timedelta(minutes=10)]
    kind = rain_kind(sensor)
    sensor["kind"] = kind or "level"
    if kind == "increment":
        hours = {}
        for t, v in hist:
            h = t.replace(minute=0, second=0)
            hours[h] = hours.get(h, 0) + max(v, 0)
        sensor["rain24"] = round(sum(hours.values()), 2) if hist else None
        for h in RAIN_WINDOWS_H:   # rain1, rain3, rain6: the sensor map's 1 / 3 / 6 / 24-hour switch
            sensor[f"rain{h}"] = round(sum(max(v, 0) for t, v in hist if t > now - dt.timedelta(hours=h)), 2) if hist else None
        sensor["hourly"] = [[h.strftime("%Y-%m-%d %H:%M"), round(v, 2)] for h, v in sorted(hours.items())]
        return
    if kind == "accumulation" and len(hist) >= 2:
        sensor["rain24"] = round(max(hist[-1][1] - hist[0][1], 0), 2)
        for h in RAIN_WINDOWS_H:   # running total: now minus the last reading at or before h hours ago
            before = [v for t, v in hist if t <= now - dt.timedelta(hours=h)]
            sensor[f"rain{h}"] = round(max(hist[-1][1] - before[-1], 0), 2) if before else None
    step = max(1, -(-len(hist) // MAX_POINTS))
    keep = hist[::step]
    if hist and keep[-1] != hist[-1]:
        keep.append(hist[-1])
    sensor["points"] = [[t.strftime("%Y-%m-%d %H:%M"), round(v, 3)] for t, v in keep]


def tidy(sensors):
    """Drop repeats (same name, value and time) and, where a gauge has both, the running rain total
    (season accumulation), keeping the rain increment, which gives the 1- and 24-hour totals."""
    seen, out = set(), []
    for s in sensors:
        key = (s["name"].lower(), s["value"], s["time"])
        if key not in seen:
            seen.add(key)
            out.append(s)
    if any(rain_kind(s) == "increment" for s in out):
        out = [s for s in out if rain_kind(s) != "accumulation"]
    return out


def add_thresholds(number, sensor):
    for word, levels in THRESHOLDS.get(number, {}).items():
        if word.lower() in sensor["name"].lower():
            sensor["thresholds"] = levels


def main():
    args = sys.argv[1:]
    out_path = args[0] if args else "sites.json"
    min_age = float(args[args.index("--min-age") + 1]) if "--min-age" in args else 0
    try:
        with open(out_path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        previous = {}
    now = dt.datetime.now(TZ).replace(tzinfo=None, microsecond=0)
    if min_age and previous.get("generated"):
        age = (now - to_time(previous["generated"])).total_seconds() / 60
        if age < min_age:
            print(f"sites.json is {age:.0f} min old (refreshes every {min_age:.0f}); skipping this run.")
            return
    old_sites = {s["site"]: s for s in previous.get("sites", [])}
    if THRESHOLD_ERRORS or not CREEKS:   # use the last good thresholds, which fetch_onerain.py kept in creeks.json
        try:
            with open(os.path.join(os.path.dirname(out_path) or ".", "creeks.json")) as f:
                for c in json.load(f).get("creeks", []):
                    for g in c.get("stages", []):
                        if g.get("thresholds"):
                            THRESHOLDS.setdefault(g["number"], {})["stage"] = g["thresholds"]
        except (OSError, ValueError):
            pass
    start = now - dt.timedelta(hours=HISTORY_HOURS)

    session = Session()
    sites = list_sites(session.get(SITE + "/list/"))
    print(f"{len(sites)} public sites")
    if not sites:
        print("No sites found on the Sites list (page layout changed?)", file=sys.stderr)
        sys.exit(1)

    result, failures = [], 0
    for site_id, uuid, name, number in sites:
        entry = {"name": name, "number": number, "site_id": site_id, "site": uuid,
                 "url": f"{SITE}/site/?site_id={site_id}&site={uuid}"}
        try:
            (lat, lon), sensors = parse_site(session.get(entry["url"]))
            time.sleep(PAUSE_SEC)
            sensors = [s for s in sensors if s["name"] and not SKIP_SENSORS.search(s["name"])]
            sensors = tidy(sensors)
            if lat is None or not sensors:
                print(f"  {name}: skipped ({'no location' if lat is None else 'no public sensors'})")
                continue
            for s in sensors:
                add_thresholds(number, s)
                try:
                    hist, how = sensor_history(session, site_id, uuid, s, start, now + dt.timedelta(minutes=5))
                    summarize(s, hist, start, now)
                except Exception as e:
                    s["kind"] = rain_kind(s) or "level"
                    s["history_error"] = f"{type(e).__name__}: {e}"[:200]
                time.sleep(PAUSE_SEC)
                if number in TIDE_MLLW_TO_NAVD88 and re.search(r"tide", s["name"], re.I) and s["unit"] == "ft":
                    shift = TIDE_MLLW_TO_NAVD88[number]
                    if s["value"] is not None:
                        s["value"] = round(s["value"] + shift, 2)
                    s["points"] = [[t, round(v + shift, 3)] for t, v in s.get("points", [])]
                    s["unit"] = "ft NAVD88"
                s["url"] = (f"{SITE}/sensor/?site_id={site_id}&site={uuid}"
                            f"&device_id={s['device_id']}&device={s['device']}")
                del s["device"]
            entry.update({"lat": lat, "lon": lon, "sensors": sensors, "error": None})
            print(f"  {name}: {len(sensors)} sensors · " + "; ".join(
                f"{s['name']} {s['value']} {s['unit']} @ {s['time']}" for s in sensors))
        except Exception as e:
            failures += 1
            old = old_sites.get(uuid)
            if not old:
                print(f"  {name}: FAILED ({type(e).__name__}: {e})", file=sys.stderr)
                continue
            entry = dict(old, error=f"{type(e).__name__}: {e}"[:300])
            print(f"  {name}: FAILED, kept previous data ({entry['error']})", file=sys.stderr)
        result.append(entry)

    with open(out_path, "w") as f:
        json.dump({"generated": now.strftime("%Y-%m-%d %H:%M:%S"), "timezone": "America/Los_Angeles",
                   "hours": HISTORY_HOURS, "sites": result}, f, separators=(",", ":"))
    print(f"Saved {len(result)} sites ({failures} failed)")
    sys.exit(1 if failures and failures == len(sites) else 0)


if __name__ == "__main__":
    main()
