#!/usr/bin/env python3
"""
Download recent creek stage and rain readings from OneRain and save them as JSON for the kiosk's Creeks
tab, the phone page (Creeks.html) and the home page. The creeks and gauges are listed in lookups/creeks.csv
and lookups/creek_gauges.csv (read by creek_config.py).

OneRain's data export needs a login, but each sensor's public page (the one you see as "Guest")
lists its readings. This script reads those public pages. It runs in a GitHub Action every few
minutes and the result is published for the kiosk (see .github/workflows/onerain.yml).

Usage:  python fetch_onerain.py OUTPUT.json      (the workflow uses creeks.json)
If a sensor can't be read, its previous data in OUTPUT.json (if any) is kept and the error is
recorded, so one bad download never blanks the screen. If a lookups/ file has a mistake, the last good
settings in OUTPUT.json are used, readings are still published, and the problems are written to
settings_problems.txt next to OUTPUT.json (the workflow then marks the run as failed after publishing).
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
HOURS = 50          # history kept in the file (graphs show 36 hours; 48-hour rain totals need a little more)
MAX_PAGES = 40      # safety limit when a sensor has many readings (the page lists them in batches)

import os

from creek_config import CREEKS, CONFIG_ERRORS, THRESHOLD_ERRORS, SETTINGS_ERRORS
from creek_signals import load_settings, load_rain_frequency, rain_signals, stage_signals, _series

# Creek status layer (in development): rain levels and creek trends, written into creeks.json for the staff preview
SIGNAL_SETTINGS, _sp = load_settings()
RAIN_FREQ, _fp = load_rain_frequency()
SETTINGS_ERRORS = SETTINGS_ERRORS + _sp + _fp

SENSORS = {}


def set_sensors(creeks):
    """Every gauge in the creek list, by key."""
    SENSORS.clear()
    for c in creeks:
        for g in c["stages"]:
            SENSORS[g["key"]] = dict(g, name=f"{g['site_name']} ({g['number']}) – Stage", kind="stage", unit="ft")
        for g in c["rain"] + c.get("rain_support", []):
            SENSORS[g["key"]] = dict(g, name=f"{g['label']} ({g['number']}) – Rain", kind="rain_increment", unit="in")


def creeks_from_previous(previous_file):
    """The last good creek list, rebuilt from the previous data file (each gauge's link holds its OneRain ids)."""
    out = []
    for c in previous_file.get("creeks", []):
        c = json.loads(json.dumps(c))
        for g in c.get("stages", []) + c.get("rain", []) + c.get("rain_support", []):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(g.get("url", "")).query)
            g.update({"site_id": int(q["site_id"][0]), "site": q["site"][0], "device_id": int(q["device_id"][0]), "device": q["device"][0]})
            g.pop("url", None)
        out.append(c)
    return out


set_sensors(CREEKS)

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
    return [dict(c, stages=[gauge(g) for g in c["stages"]], rain=[gauge(g) for g in c["rain"]],
                 rain_support=[gauge(g) for g in c.get("rain_support", [])]) for c in CREEKS]


def _freq_from_json(f):
    """A gauge's Atlas 14 entry as stored in creeks.json (string keys) back to numbers."""
    if not f:
        return None
    return {"minutes": {int(m): {float(a): d for a, d in v.items()} for m, v in f.get("minutes", {}).items()},
            "levels": {int(m): v for m, v in f.get("levels", {}).items()}}


def add_signals(result, previous, now):
    """Rain level for every rain gauge and trend for every stage gauge (creek status layer; staff preview only).
    If rain_frequency.csv has a mistake, each gauge keeps the Atlas 14 values from the previous data file."""
    sens = result["sensors"]
    for c in result["creeks"]:
        rain_keys = [g["key"] for g in c["rain"] + c.get("rain_support", [])]
        for g in c["rain"] + c.get("rain_support", []):
            e = sens.get(g["key"])
            if not e:
                continue
            if RAIN_FREQ is not None:
                freq = RAIN_FREQ.get(g["number"])
            else:
                freq = _freq_from_json(previous.get(g["key"], {}).get("signals", {}).get("freq"))
            sig = rain_signals(e["points"], e.get("latest"), freq, now, SIGNAL_SETTINGS["GAUGE_QUIET_HOURS"])
            if freq:
                sig["freq"] = {"minutes": {str(m): {str(a): d for a, d in v.items()} for m, v in freq["minutes"].items()},
                               "levels": {str(m): v for m, v in freq["levels"].items()}}
            e["signals"] = sig
        rain_series = [_series(sens[k]["points"], sens[k].get("latest")) for k in rain_keys if k in sens]
        for g in c["stages"]:
            e = sens.get(g["key"])
            if e:
                e["signals"] = stage_signals(e["points"], e.get("latest"), g, now, SIGNAL_SETTINGS, rain_series)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "creeks.json"
    try:
        with open(out_path) as f:
            previous_file = json.load(f)
    except (OSError, ValueError):
        previous_file = {}
    previous = previous_file.get("sensors", {})

    for e in SETTINGS_ERRORS:   # shown as errors in the Actions tab
        print(f"::error title=lookups::{e}", file=sys.stderr)
    problems_path = os.path.join(os.path.dirname(out_path) or ".", "settings_problems.txt")
    with open(problems_path, "w") as f:
        f.write("".join(e + "\n" for e in SETTINGS_ERRORS))
    if not CREEKS:   # creeks.csv / creek_gauges.csv / tide_stations.csv problem: keep the whole last good creek list
        try:
            CREEKS[:] = creeks_from_previous(previous_file)
        except (KeyError, ValueError, IndexError) as e:
            print(f"Previous creek list unusable ({e}).", file=sys.stderr)
        if not CREEKS:
            print("No usable creek settings and no previous data file; nothing to publish.", file=sys.stderr)
            sys.exit(1)
        set_sensors(CREEKS)
        print("lookups/ has problems (above); kept the previous creek list and thresholds.", file=sys.stderr)
    creeks_out = public_config()
    if THRESHOLD_ERRORS and not CONFIG_ERRORS:   # a mistake in thresholds.csv: keep the last good thresholds
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
    add_signals(result, previous, now)

    with open(out_path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    # Fail the job only if nothing at all could be read (then nothing is published, and the pages show the data as
    # delayed). Settings problems are reported by the workflow after publishing, from settings_problems.txt.
    sys.exit(1 if failures == len(SENSORS) else 0)


if __name__ == "__main__":
    main()
