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
HISTORY_DAYS = 7    # creeks_7day.json: rolling 7 days of every creek sensor's points, for the data archive
HOURS = 50          # history kept in the file (graphs show 36 hours; 48-hour rain totals need a little more)
MAX_PAGES = 40      # safety limit when a sensor has many readings (the page lists them in batches)

import os

from creek_config import CREEKS, CONFIG_ERRORS, THRESHOLD_ERRORS, SETTINGS_ERRORS
from creek_signals import load_settings, load_rain_frequency, rain_signals, stage_signals, _series, tide_state, creek_status

# Creek status layer (in development): rain levels and creek trends, written into creeks.json for the staff preview
SIGNAL_SETTINGS, _sp = load_settings()
RAIN_FREQ, _fp = load_rain_frequency()
SETTINGS_ERRORS = SETTINGS_ERRORS + _sp + _fp

SENSORS = {}


def load_gauge_outages(path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lookups", "gauge_outages.csv")):
    """{gauge key: {"since", "note"}} from lookups/gauge_outages.csv: gauges staff have taken out of service (damaged,
    being repaired). Their readings are dropped, so a damaged sensor can't show a false level or set off a false alert;
    the creek's status then comes from rain alone, and the pages say "Out of service" with the note."""
    import csv as _csv
    out = {}
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in _csv.DictReader(f):
                k = (r.get("gauge") or "").strip()
                if k and not k.startswith("#"):
                    out[k] = {"since": (r.get("out_since") or "").strip(), "note": (r.get("note") or "").strip()}
    except FileNotFoundError:
        pass
    return out


GAUGE_OUTAGES = load_gauge_outages()
USGS_PAGE = "https://waterdata.usgs.gov/monitoring-location/USGS-{}/"


def all_creeks(result):
    """Public creeks and staff-preview creeks (preview_only = yes in creeks.csv)."""
    return result.get("creeks", []) + result.get("creeks_preview", [])


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
    for c in all_creeks(previous_file):
        c = json.loads(json.dumps(c))
        for g in c.get("stages", []) + c.get("rain", []) + c.get("rain_support", []):
            if g.get("source") == "usgs":
                g.pop("url", None)
                continue
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


def utc_str(t):
    """Aware datetime -> "YYYY-MM-DDTHH:MMZ" (the third element of every point)."""
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def to_utc(local, prev, descending=True):
    """Pacific wall-clock time -> aware UTC time. In the repeated hour when daylight saving ends (1-2 AM on the first
    Sunday of November) a wall-clock time happens twice; pick the one that keeps the readings in page order
    (newest first: the latest one not after the previous reading; oldest first: the earliest not before it)."""
    # Compare in UTC: Python compares two Pacific times by wall clock and ignores which 1:30 AM they are
    a, b = (local.replace(tzinfo=TZ, fold=f).astimezone(dt.timezone.utc) for f in (0, 1))
    if a == b:   # not ambiguous
        return a
    if descending:
        return b if b <= prev else a
    return a if a >= prev else b


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
    prev = None   # UTC time of the previous reading in page order (for the repeated hour in November)
    while url and pages < MAX_PAGES and url not in seen:
        seen.add(url)
        page = session.get(url)
        pages += 1
        if latest is None:
            latest = parse_latest(page)
        batch = parse_readings(page)
        if prev is None:   # page order, from the first page (OneRain lists newest first; later pages are older)
            desc = len(batch) < 2 or batch[0][0] >= batch[-1][0]
            # "previous reading" before the first one: the end of the range (newest first) or its start (oldest first)
            prev = (end if desc else start).replace(tzinfo=TZ, fold=1 if desc else 0).astimezone(dt.timezone.utc)
        for t, v in batch:
            u = to_utc(t, prev, desc)
            prev = u
            readings[u] = (t, v)   # keyed by UTC: both 1:30 AMs on the November change are kept
        if not batch or min(t for t, _ in batch) < start:
            break
        url = next_page(page)
    points = [[t.strftime("%Y-%m-%d %H:%M"), round(v, 4), utc_str(u)] for u, (t, v) in sorted(readings.items()) if t >= start]
    return points, latest_utc(latest, points), pages


def latest_utc(latest, points):
    """The sensor's latest reading as [Pacific, value, UTC]. Its UTC comes from the reading with the same Pacific time
    (right in the repeated hour in November); otherwise its Pacific time read the usual way."""
    if not latest or latest[0] is None:
        return latest
    if len(latest) > 2 and latest[2]:
        return latest
    same = [p for p in points or [] if p[0] == latest[0] and len(p) > 2 and p[2]]
    return [latest[0], latest[1], same[-1][2] if same else point_utc(latest)]


def public_config():
    """The creek list for the pages, with a link to each gauge's OneRain page."""
    def gauge(g):
        out = {k: v for k, v in g.items() if k not in ("site_id", "site", "device_id", "device")}
        out["url"] = (USGS_PAGE.format(g["usgs_site"]) if g.get("source") == "usgs" else
                      f"{SITE}/sensor/?site_id={g['site_id']}&site={g['site']}&device_id={g['device_id']}&device={g['device']}")
        return out
    out = [dict(c, stages=[gauge(g) for g in c["stages"]], rain=[gauge(g) for g in c["rain"]],
                rain_support=[gauge(g) for g in c.get("rain_support", [])]) for c in CREEKS]
    # Staff-preview creeks go in a separate list, so the public pages never see them
    return [c for c in out if not c.get("preview_only")], [c for c in out if c.get("preview_only")]


def fetch_usgs_gauge(s, start, end):
    """Gage height (ft) at a USGS stream gauge, as [[Pacific time, ft], ...], from the USGS Water Data API
    (or the older WaterServices if that fails). Same reader as the history pull (scripts/fetch_usgs.py)."""
    import fetch_usgs as U
    U.TRIES, U.TIMEOUT = 1, 25
    t0, t1 = (t.replace(tzinfo=TZ).astimezone(dt.timezone.utc) for t in (start, end))
    data = None
    try:
        data = U.pull_ogc(s["usgs_site"], t0, t1)
    except Exception as e:   # noqa: BLE001
        print(f"  USGS Water Data API {s['usgs_site']}: {type(e).__name__}: {e}", file=sys.stderr)
    if not data or "00065" not in data:
        data = U.pull_legacy(s["usgs_site"], t0, t1)
    pts = {}
    for utc, v, _unit, approval, quals in (data or {}).get("00065", []):
        u = dt.datetime.fromisoformat(utc.replace("Z", "+00:00"))
        t = u.astimezone(TZ).replace(tzinfo=None)
        pts[utc_str(u)] = [t.strftime("%Y-%m-%d %H:%M"), round(float(v), 3), utc_str(u), usgs_codes(approval, quals)]
    points = [pts[k] for k in sorted(pts)]
    return points, (points[-1][:3] if points else None), 1


def usgs_codes(approval, quals):
    """USGS qualifier codes for a reading, e.g. "P" (provisional), "A" (approved), "P e" (estimated), "P Eqp"
    (equipment malfunction). WaterServices gives the codes as they are; the Water Data API gives the approval status
    in words, so it is turned into P / A and any qualifiers follow."""
    quals = " ".join(str(quals or "").split())
    codes = quals.split()
    if "A" in codes or "P" in codes:          # already USGS codes (WaterServices)
        return quals
    a = str(approval or "").lower()
    first = "A" if a.startswith("approved") else "P" if a.startswith("provisional") else ""
    return " ".join(x for x in (first, quals) if x)


def _freq_from_json(f):
    """A gauge's Atlas 14 entry as stored in creeks.json (string keys) back to numbers."""
    if not f:
        return None
    return {"minutes": {int(m): {float(a): d for a, d in v.items()} for m, v in f.get("minutes", {}).items()},
            "levels": {int(m): v for m, v in f.get("levels", {}).items()}}


NOAA = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


def noaa_tide(station, now):
    """Predicted (6-min and high/low) and measured tide at a NOAA station, ft NAVD88, Pacific clock time.
    Any part that can't be downloaded comes back empty; the status then skips the tide."""
    def get(product, begin, end, **extra):
        q = dict(product=product, station=station, begin_date=begin.strftime("%Y%m%d %H:%M"), end_date=end.strftime("%Y%m%d %H:%M"),
                 datum="NAVD", time_zone="lst_ldt", units="english", format="json", application="OneShorelineFEWS", **extra)
        req = urllib.request.Request(NOAA + "?" + urllib.parse.urlencode(q), headers={"User-Agent": HEADERS["User-Agent"]})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                j = json.load(resp)
        except Exception as e:   # noqa: BLE001 - a tide problem must never stop the creek data
            print(f"NOAA {product} {station}: {type(e).__name__}: {e}", file=sys.stderr)
            return []
        return j.get("predictions") or j.get("data") or []

    def pts(rows):
        out = []
        for x in rows:
            try:
                out.append((dt.datetime.strptime(x["t"], "%Y-%m-%d %H:%M"), float(x["v"]), x.get("type")))
            except (KeyError, ValueError, TypeError):
                pass
        return out
    pred = [(t, v) for t, v, _ in pts(get("predictions", now - dt.timedelta(hours=2), now + dt.timedelta(hours=2)))]
    hilo = pts(get("predictions", now - dt.timedelta(hours=1), now + dt.timedelta(hours=26), interval="hilo"))
    obs = [(t, v) for t, v, _ in pts(get("water_level", now - dt.timedelta(hours=3), now))]
    return pred, hilo, obs


STATUS_LOG_MAX = 5000   # rows kept in status_log.csv (newest last)


def log_status_changes(result, previous_file, out_path):
    """Append a row to status_log.csv (next to OUTPUT.json) whenever a creek's status changes, for staff review."""
    old = {c["id"]: (c.get("status") or {}).get("key") for c in all_creeks(previous_file)}
    path = os.path.join(os.path.dirname(out_path) or ".", "status_log.csv")
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError:
        lines = []
    head = "time,creek,from,to,level,rain_level,trend,reasons"
    if not lines or lines[0] != head:
        lines = [head]
    for c in all_creeks(result):
        st = c.get("status") or {}
        if st.get("key") != old.get(c["id"]):
            codes = " ".join(x["code"] for x in st.get("reasons", []))
            lines.append(",".join([result["generated"], c["id"], old.get(c["id"]) or "", st.get("key") or "",
                                   str(st.get("level", "")), str((st.get("rain") or {}).get("level", "")),
                                   str((st.get("trend") or {}).get("trend") or ""), codes]))
    lines = [lines[0]] + lines[1:][-STATUS_LOG_MAX:]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def add_status(result, now, previous_file=None):
    """One status per creek (creek status layer; staff preview only), with when it started and what it was before."""
    old = {c["id"]: c.get("status") or {} for c in all_creeks(previous_file or {})}
    tides = {}
    for c in all_creeks(result):
        st = c.get("tide")
        if st and st not in tides:
            pred, hilo, obs = noaa_tide(st, now)
            tides[st] = tide_state(pred, hilo, obs, now, SIGNAL_SETTINGS["TIDE_RISING_LOOKAHEAD_HOURS"])
        c["status"] = creek_status(c, result["sensors"], tides.get(st, {}), now, SIGNAL_SETTINGS)
        o = old.get(c["id"], {})
        if o.get("key") == c["status"]["key"] and o.get("since"):
            c["status"]["since"], c["status"]["prev"] = o["since"], o.get("prev")
        else:
            c["status"]["since"], c["status"]["prev"] = result["generated"][:16], o.get("key")
        print(f"{c['id']}: status {c['status']['key']} · " + ", ".join(x["code"] for x in c["status"]["reasons"]))


def add_signals(result, previous, now):
    """Rain level for every rain gauge and trend for every stage gauge (creek status layer; staff preview only).
    If rain_frequency.csv has a mistake, each gauge keeps the Atlas 14 values from the previous data file."""
    sens = result["sensors"]
    for c in all_creeks(result):
        rain_keys = [g["key"] for g in c["rain"] + c.get("rain_support", [])]
        for g in c["rain"] + c.get("rain_support", []):
            e = sens.get(g["key"])
            if not e:
                continue
            if RAIN_FREQ is not None:
                freq = RAIN_FREQ.get(g["number"])
            else:
                freq = _freq_from_json(previous.get(g["key"], {}).get("signals", {}).get("freq"))
            sig = rain_signals(e["points"], e.get("latest"), freq, now, SIGNAL_SETTINGS["GAUGE_QUIET_HOURS"],
                               SIGNAL_SETTINGS["RAIN_NOW_MIN"], SIGNAL_SETTINGS["RAIN_NOW_IN"])
            if freq:
                sig["freq"] = {"minutes": {str(m): {str(a): d for a, d in v.items()} for m, v in freq["minutes"].items()},
                               "levels": {str(m): v for m, v in freq["levels"].items()}}
            e["signals"] = sig
        rain_series = [_series(sens[k]["points"], sens[k].get("latest")) for k in rain_keys if k in sens]
        for g in c["stages"]:
            e = sens.get(g["key"])
            if e:
                e["signals"] = stage_signals(e["points"], e.get("latest"), g, now, SIGNAL_SETTINGS, rain_series)


def point_utc(p):
    """UTC key for a point: its third element, or (older points without one) its Pacific time read the usual way."""
    if len(p) > 2 and p[2]:
        return p[2]
    return utc_str(to_time(p[0]).replace(tzinfo=TZ))


def with_utc(points):
    """Points from before the UTC change (kept when a download fails) get their UTC time added."""
    return [p if len(p) > 2 else [p[0], p[1], point_utc(p)] for p in points or []]


def write_history(result, path, days=HISTORY_DAYS, now=None):
    """creeks_7day.json: every creek sensor's points for the last `days` days, built up run by run from creeks.json's
    50 hours (no extra downloads), so the data archive loses nothing if it can't run for a few days.
    Newer runs replace a point with the same UTC time (USGS can revise values). Same point format as creeks.json."""
    try:
        with open(path) as f:
            old = json.load(f).get("sensors", {})
    except (OSError, ValueError):
        old = {}
    cutoff = utc_str((now or dt.datetime.now(dt.timezone.utc)) - dt.timedelta(days=days))
    sensors = {}
    for key in set(old) | set(result["sensors"]):
        new = result["sensors"].get(key)
        pts = {p[2]: p for p in with_utc((old.get(key) or {}).get("points"))}
        if new:
            pts.update({p[2]: p for p in with_utc(new.get("points"))})
        keep = [pts[u] for u in sorted(pts) if u >= cutoff]
        if keep:
            meta = new or old[key]
            sensors[key] = {k: meta.get(k) for k in ("name", "kind", "unit")}
            sensors[key]["points"] = keep
    with open(path, "w") as f:
        json.dump({"generated": result["generated"], "generated_utc": result["generated_utc"], "days": days,
                   "timezone": "America/Los_Angeles", "sensors": sensors}, f, separators=(",", ":"))


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
    creeks_out, creeks_preview = public_config()
    if THRESHOLD_ERRORS and not CONFIG_ERRORS:   # a mistake in thresholds.csv: keep the last good thresholds
        old = {c["id"]: c for c in all_creeks(previous_file)}
        for c in creeks_out + creeks_preview:
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
    result = {"generated": now.strftime("%Y-%m-%d %H:%M:%S"),
              "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "timezone": "America/Los_Angeles",
              "hours": HOURS, "creeks": creeks_out, "creeks_preview": creeks_preview, "sensors": {}}
    failures = 0
    session = Session()
    for key, s in SENSORS.items():
        entry = {k: s[k] for k in ("name", "kind", "unit")}
        try:
            s_start = now - dt.timedelta(hours=s.get("hours", HOURS))
            read = fetch_usgs_gauge if s.get("source") == "usgs" else (lambda s_, a, b: fetch_sensor(session, s_, a, b))
            entry["points"], entry["latest"], pages = read(s, s_start, now + dt.timedelta(minutes=5))
            entry["fetched"] = result["generated"]
            entry["error"] = None
            print(f"{key}: {len(entry['points'])} readings in the last {HOURS} h "
                  f"({pages} page{'s' if pages != 1 else ''}) · latest: {entry['latest']}")
        except Exception as e:  # keep the last good data rather than blanking the screen
            failures += 1
            old = previous.get(key, {})
            entry["points"] = with_utc(old.get("points", []))
            entry["latest"] = latest_utc(old.get("latest"), entry["points"])
            entry["fetched"] = old.get("fetched")
            entry["error"] = f"{type(e).__name__}: {e}"[:300]
            print(f"{key}: FAILED ({entry['error']}); kept {len(entry['points'])} old readings", file=sys.stderr)
        if key in GAUGE_OUTAGES:   # out of service: no readings published
            entry["points"], entry["latest"] = [], None
            entry["out_of_service"] = GAUGE_OUTAGES[key]
            print(f"{key}: OUT OF SERVICE since {GAUGE_OUTAGES[key]['since'] or '?'} (gauge_outages.csv); readings not published")
        result["sensors"][key] = entry
    for k in GAUGE_OUTAGES:
        if k not in SENSORS:
            print(f"gauge_outages.csv: '{k}' is not a gauge in creek_gauges.csv (left out)", file=sys.stderr)
    add_signals(result, previous, now)
    add_status(result, now, previous_file)
    try:   # NWS rain forecast per creek; a problem here never stops the creek data
        import nws_forecast
        for p in nws_forecast.add_forecast(result, previous_file, dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0), SIGNAL_SETTINGS):
            print(f"forecast: {p}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"NWS forecast step failed ({type(e).__name__}: {e})", file=sys.stderr)
    log_status_changes(result, previous_file, out_path)

    with open(out_path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    try:
        write_history(result, os.path.join(os.path.dirname(out_path) or ".", "creeks_7day.json"))
    except Exception as e:  # noqa: BLE001 - never stops creeks.json
        print(f"creeks_7day.json not updated ({type(e).__name__}: {e})", file=sys.stderr)
    # Fail the job only if nothing at all could be read (then nothing is published, and the pages show the data as
    # delayed). Settings problems are reported by the workflow after publishing, from settings_problems.txt.
    sys.exit(1 if failures == len(SENSORS) else 0)


if __name__ == "__main__":
    main()
