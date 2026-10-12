#!/usr/bin/env python3
"""
Download recent creek stage and rain readings from OneRain and save them as JSON for the kiosk's Creeks
tab, the phone page (Creeks.html) and the home page. The creeks and gauges are listed in creek_config.py.

OneRain's data export needs a login, but each sensor's public page (the one you see as "Guest")
lists its readings. This script reads those public pages. It runs in a GitHub Action every few
minutes and the result is published for the kiosk (see .github/workflows/onerain.yml).

Usage:  python fetch_onerain.py OUTPUT.json      (the workflow uses creeks.json)
If a sensor can't be read, its previous data in OUTPUT.json (if any) is kept and the error is
recorded, so one bad download never blanks the screen.
"""
import datetime as dt
import html as htmllib
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Los_Angeles")
SITE = "https://oneshorelineearlywarning.onerain.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; OneShoreline-kiosk-data/2.0; +https://github.com/OneShorelineSMC/oneshorelinefews)",
    "Accept": "text/html,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
HOURS = 48          # how much history to keep in the file (the graphs show 36 hours)
MAX_PAGES = 40      # safety limit when a sensor has many readings (the page lists them in batches)

from creek_config import CREEKS, THRESHOLD_ERRORS

# Every gauge listed in creek_config.py, by key
SENSORS = {}
for _c in CREEKS:
    for _g in _c["stages"]:
        SENSORS[_g["key"]] = dict(_g, name=f"{_g['site_name']} ({_g['number']}) – Stage", kind="stage", unit="ft")
    for _g in _c["rain"]:
        SENSORS[_g["key"]] = dict(_g, name=f"{_g['label']} ({_g['number']}) – Rain", kind="rain_increment", unit="in")

STAMP = r"(\d{4}-\d\d-\d\d \d\d:\d\d(?::\d\d)?)"
NUMBER = r"(-?\d+(?:\.\d+)?)"


class Session:
    """A simple signed-out visitor: keeps OneRain's visitor cookie between requests."""

    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def get(self, url):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with self.opener.open(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            body = e.read(300).decode("utf-8", errors="replace")
            print(f"    {e.code} from {url.split('?')[0]} · {' '.join(body.split())[:90]!r}", file=sys.stderr)
            raise


def to_time(stamp):
    return dt.datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S" if len(stamp) > 16 else "%Y-%m-%d %H:%M")


def sensor_page(s, start, end):
    """The sensor's public page, limited to a date range (same as picking a custom range on the page)."""
    return SITE + "/sensor/?" + urllib.parse.urlencode({
        "site_id": s["site_id"], "site": s["site"], "device_id": s["device_id"], "device": s["device"],
        "data_start": start.strftime("%Y-%m-%d %H:%M:%S"), "data_end": end.strftime("%Y-%m-%d %H:%M:%S"),
        "range": "Custom Range", "time_zone": "US/Pacific",
    })


def number_in(fragment):
    """First number in an HTML fragment, ignoring tags (e.g. '0.00&nbsp;in <small>(1664)</small>' -> 0.0)."""
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment))
    m = re.search(NUMBER, text)
    return float(m.group(1)) if m else None


def parse_readings(page):
    """Readings listed on a sensor page: [(datetime, value), ...] in page order."""
    m = re.search(r'id="scrollable-readings"(.*?)</ul>', page, flags=re.S)
    if not m:
        return []
    out = []
    for item in re.split(r'<li class="list-group-item', m.group(1))[1:]:
        t = re.search(r'<span class="text-nowrap">\s*' + STAMP + r"\s*</span>", item)
        heads = re.findall(r'<h4 class="list-group-item-heading">(.*?)</h4>', item, flags=re.S)
        if not t or len(heads) < 2:
            continue
        v = number_in(heads[1])
        if v is not None:
            out.append((to_time(t.group(1)), v))
    return out


def parse_latest(page):
    """The most recent reading shown at the top of the page (even if it's months old)."""
    m = re.search(r'<h4 class="mb-0">([^<]*)</h4>\s*<h6[^>]*>(?:(?!</h6>).)*?<time[^>]*title="' + STAMP + '"',
                  page, flags=re.S)
    if not m:
        return None
    v = number_in(m.group(1))
    return None if v is None else [m.group(2)[:16], v]


def next_page(page):
    """Link to the next batch of readings, if the page has one (used by the page's infinite scroll)."""
    for pat in (r'<a[^>]*class="[^"]*\bnext\b[^"]*"[^>]*href="([^"]+)"',
                r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*\bnext\b',
                r'class="[^"]*\bnext\b[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"'):
        m = re.search(pat, page)
        if m:
            return urllib.parse.urljoin(SITE + "/sensor/", htmllib.unescape(m.group(1)))
    return None


def fetch_sensor(session, s, start, end):
    url, pages, readings, latest, seen = sensor_page(s, start, end), 0, {}, None, set()
    while url and pages < MAX_PAGES and url not in seen:
        seen.add(url)
        page = session.get(url)
        pages += 1
        if latest is None:
            latest = parse_latest(page)
        batch = parse_readings(page)
        for t, v in batch:
            readings[t] = v
        if not batch or min(t for t, _ in batch) < start:
            break
        url = next_page(page)
    points = [[t.strftime("%Y-%m-%d %H:%M"), round(v, 4)] for t, v in sorted(readings.items()) if t >= start]
    return points, latest, pages


def public_config():
    """The creek list for the pages, with a link to each gauge's OneRain page."""
    def gauge(g):
        out = {k: v for k, v in g.items() if k not in ("site_id", "site", "device_id", "device")}
        out["url"] = (f"{SITE}/sensor/?site_id={g['site_id']}&site={g['site']}"
                      f"&device_id={g['device_id']}&device={g['device']}")
        return out
    return [dict(c, stages=[gauge(g) for g in c["stages"]], rain=[gauge(g) for g in c["rain"]]) for c in CREEKS]


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "creeks.json"
    try:
        with open(out_path) as f:
            previous_file = json.load(f)
    except (OSError, ValueError):
        previous_file = {}
    previous = previous_file.get("sensors", {})

    creeks_out = public_config()
    if THRESHOLD_ERRORS:   # a mistake in thresholds.csv: keep the last good thresholds and flag it
        for e in THRESHOLD_ERRORS:
            print(f"::error title=thresholds.csv::{e}", file=sys.stderr)
        old = {c["id"]: c for c in previous_file.get("creeks", [])}
        for c in creeks_out:
            o = old.get(c["id"])
            if o:
                byk = {g["key"]: g for g in o.get("stages", [])}
                for g in c["stages"]:
                    g["thresholds"] = byk.get(g["key"], {}).get("thresholds", [])
                c["rain_triggers"] = o.get("rain_triggers", [])
                if o.get("rain_running") and c.get("rain_running"):
                    c["rain_running"] = o["rain_running"]
        print("thresholds.csv has problems (above); kept the previous thresholds.", file=sys.stderr)

    now = dt.datetime.now(TZ).replace(tzinfo=None, microsecond=0)
    start = now - dt.timedelta(hours=HOURS)
    result = {"generated": now.strftime("%Y-%m-%d %H:%M:%S"), "timezone": "America/Los_Angeles",
              "hours": HOURS, "creeks": creeks_out, "sensors": {}}
    failures = 0
    session = Session()
    for key, s in SENSORS.items():
        entry = {k: s[k] for k in ("name", "kind", "unit")}
        try:
            s_start = now - dt.timedelta(hours=s.get("hours", HOURS))
            entry["points"], entry["latest"], pages = fetch_sensor(session, s, s_start, now + dt.timedelta(minutes=5))
            entry["fetched"] = result["generated"]
            entry["error"] = None
            print(f"{key}: {len(entry['points'])} readings in the last {HOURS} h "
                  f"({pages} page{'s' if pages != 1 else ''}) · latest: {entry['latest']}")
        except Exception as e:  # keep the last good data rather than blanking the screen
            failures += 1
            old = previous.get(key, {})
            entry["points"] = old.get("points", [])
            entry["latest"] = old.get("latest")
            entry["fetched"] = old.get("fetched")
            entry["error"] = f"{type(e).__name__}: {e}"[:300]
            print(f"{key}: FAILED ({entry['error']}); kept {len(entry['points'])} old readings", file=sys.stderr)
        result["sensors"][key] = entry

    with open(out_path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    # Fail the job only if nothing at all could be read, so problems show up in the Actions tab.
    sys.exit(1 if failures == len(SENSORS) or THRESHOLD_ERRORS else 0)


if __name__ == "__main__":
    main()
