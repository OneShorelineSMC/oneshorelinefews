"""San Francisquito Creek readings from SFCJPA's Contrail site, for the preview page SanFrancisquito.html (staff, 2026-11-16).

SFCJPA (the San Francisquito Creek Joint Powers Authority) runs its own OneRain site, contrail.onerain.com: the three
lower-creek gauges in Palo Alto and East Palo Alto (Waverley, Pope-Chaucer, West Bayshore) with SFCJPA's channel-capacity
levels, the Mayfield Slough tide, the upper-creek flows, the USGS gauge at Stanford and the Valley Water rain gauges.
SFCJPA agreed to OneShoreline reading it (Nov 16, 2026). The gauges and their levels are in lookups/sfcjpa_gauges.csv.

Contrail needs a sign-in. SFCJPA publishes a shared viewer login on its website for the public; the workflow passes it
in as CONTRAIL_USER and CONTRAIL_PASSWORD (repository variables or secrets; not in the repo's files). The script reads
the sign-in form from the page itself (its fields and where it posts), fills in the login and keeps the session cookie.
Contrail's form (seen Nov 17, 2026): /login/ posts back to itself with username, password, the "login" button, and
hidden "continue" and "csrf_token" fields. Each gauge's readings come from its
graph page, which carries them as [[time in ms (UTC), value], ...].

Writes sfcjpa.json: every gauge with its readings for the last HOURS hours as [Pacific time, value, UTC time], the
latest reading, its levels and camera, and any problems. A gauge that can't be read keeps its previous readings and is
marked with the error. Nothing is published unless at least one gauge was read or kept.

Usage: python fetch_sfcjpa.py OUTPUT.json [--min-age MINUTES]
"""

import csv
import datetime as dt
import html as htmllib
import http.cookiejar
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

BASE = "https://contrail.onerain.com"
TZ = ZoneInfo("America/Los_Angeles")
HOURS = 50
MAX_BYTES = 20_000_000
GAUGES_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lookups", "sfcjpa_gauges.csv")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OneShoreline-FEWS/1.0; +https://github.com/OneShorelineSMC/oneshorelinefews)",
           "Accept": "text/html,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.9"}
KINDS = {"stage", "flow", "tide", "rain_total"}
SERIES_RX = re.compile(r"\[\s*\[\s*1\d{12}\s*,[^\]]*\](?:\s*,\s*\[\s*1\d{12}\s*,[^\]]*\])*\s*\]")


# ---- the gauge list
def read_gauges(path=GAUGES_CSV):
    """[{key, label, where, kind, unit, site_id, device_id, order, levels: [stay alert, ready, likely] or [], camera, note}], problems."""
    out, problems = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for n, r in enumerate(csv.DictReader(f), start=2):
            r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
            if not r.get("key") or r["key"].startswith("#"):
                continue
            w = f"sfcjpa_gauges.csv row {n}"
            if not re.fullmatch(r"[a-z0-9_]{1,40}", r["key"]):
                problems.append(f"{w}: key must be lowercase letters, digits and _"); continue
            if r.get("kind") not in KINDS:
                problems.append(f"{w}: kind must be one of {', '.join(sorted(KINDS))}"); continue
            try:
                site, dev = int(r["site_id"]), int(r["device_id"])
            except (KeyError, ValueError):
                problems.append(f"{w}: site_id and device_id must be whole numbers"); continue
            lv = [r.get(k, "") for k in ("stay_alert_ft", "ready_ft", "likely_ft")]
            try:
                levels = [float(x) for x in lv] if any(lv) else []
            except ValueError:
                problems.append(f"{w}: levels must be numbers"); continue
            if levels and (len(levels) != 3 or not levels[0] < levels[1] < levels[2]):
                problems.append(f"{w}: the three levels must all be given and increase"); continue
            cam = r.get("camera_url", "")
            if cam and not cam.startswith("https://"):
                problems.append(f"{w}: camera_url must be https"); cam = ""
            out.append({"key": r["key"], "label": r.get("label", ""), "where": r.get("where", ""), "kind": r["kind"],
                        "unit": r.get("unit", ""), "site_id": site, "device_id": dev, "order": int(r.get("order") or 99),
                        "levels": levels, "camera": cam, "note": r.get("note", "")})
    out.sort(key=lambda g: g["order"])
    return out, problems


# ---- signing in
class Session:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.last_url = None

    def request(self, url, data=None):
        if not url.startswith(BASE + "/"):
            raise ValueError("only Contrail pages are read")
        body = urllib.parse.urlencode(data).encode() if data is not None else None
        req = urllib.request.Request(url, data=body, headers=dict(HEADERS, **({"Content-Type": "application/x-www-form-urlencoded",
                                                                               "Referer": url} if body else {})))
        with self.opener.open(req, timeout=60) as r:
            self.last_url = r.geturl()
            raw = r.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("page too large")
        return raw.decode("utf-8", "replace")


def login_form(page):
    """The sign-in form on a page: (action, method, {field: value}, user field, password field) or None."""
    for m in re.finditer(r"<form\b([^>]*)>(.*?)</form>", page, flags=re.S | re.I):
        attrs, body = m.group(1), m.group(2)
        inputs = re.findall(r"<input\b([^>]*)>", body, flags=re.I) + [
            'type="submit" ' + a for a in re.findall(r"<button\b([^>]*)>", body, flags=re.I)
            if re.search(r'\bname\s*=', a, flags=re.I) and not re.search(r'\btype\s*=\s*["\']?(button|reset)', a, flags=re.I)]
        fields, user, pw = {}, None, None
        for a in inputs:
            name = re.search(r'\bname\s*=\s*["\']([^"\']+)', a, flags=re.I)
            if not name:
                continue
            name = htmllib.unescape(name.group(1))
            typ = (re.search(r'\btype\s*=\s*["\']?([\w-]+)', a, flags=re.I) or [None, "text"])[1].lower()
            val = re.search(r'\bvalue\s*=\s*["\']([^"\']*)', a, flags=re.I)
            if typ == "password":
                pw = name
            elif typ in ("text", "email") and user is None:
                user = name
            elif typ == "checkbox":
                if re.search(r"remember|keep", name, flags=re.I):
                    fields[name] = val.group(1) if val else "on"
                continue
            elif typ in ("submit", "button", "image", "reset"):
                if typ == "submit" and name not in fields:   # some sign-in pages check that the button was sent (Contrail's is "login")
                    fields[name] = htmllib.unescape(val.group(1)) if val else ""
                continue
            fields[name] = htmllib.unescape(val.group(1)) if val else ""
        if pw:
            action = re.search(r'\baction\s*=\s*["\']([^"\']*)', attrs, flags=re.I)
            method = re.search(r'\bmethod\s*=\s*["\']?(\w+)', attrs, flags=re.I)
            return (htmllib.unescape(action.group(1)) if action else "", (method.group(1) if method else "post").lower(), fields, user, pw)
    return None


def sign_in(session, user, password, log):
    """Signs in when the site asks for it. Returns True when Contrail pages can be read."""
    page = session.request(BASE + "/list/")
    form = login_form(page)
    if not form:
        return True                    # already readable (no sign-in form)
    action, method, fields, ufield, pfield = form
    log(f"sign-in form: posts to {action or '(same page)'} with fields {sorted(set(fields) | {ufield or '?', pfield})}")
    if not (user and password):
        raise RuntimeError("Contrail asks for a sign-in and CONTRAIL_USER / CONTRAIL_PASSWORD aren't set")
    if not ufield:
        raise RuntimeError("the sign-in form has no user name field")
    fields[ufield], fields[pfield] = user, password
    url = urllib.parse.urljoin(session.last_url or BASE + "/", action or session.last_url or BASE + "/")
    if not url.startswith(BASE + "/"):
        raise RuntimeError("the sign-in form posts somewhere other than Contrail; not sent")
    session.request(url, fields if method == "post" else None)
    if login_form(session.request(BASE + "/list/")):
        raise RuntimeError("signed in, but Contrail still shows the sign-in form (wrong login, or the form works differently)")
    return True


# ---- readings
def graph_url(g, start, end):
    return BASE + "/graph/?" + urllib.parse.urlencode({
        "devices[]": f"{g['site_id']}|{g['device_id']}", "frame": "true", "range": "Custom Range", "tz": "US/Pacific",
        "data_start": start.strftime("%Y-%m-%d %H:%M:%S"), "data_end": end.strftime("%Y-%m-%d %H:%M:%S")})


def parse_series(page):
    """The first [[ms, value], ...] series on a graph page: [(UTC datetime, value)], oldest first, numbers only."""
    m = SERIES_RX.search(page)
    if not m:
        return []
    out = []
    for t, v in json.loads(m.group(0)):
        if isinstance(v, (int, float)) and abs(v) < 1e6:
            out.append((dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc), float(v)))
    return sorted(out)


def point(u, v):
    return [u.astimezone(TZ).strftime("%Y-%m-%d %H:%M"), round(v, 3), u.strftime("%Y-%m-%dT%H:%MZ")]


def update(previous, now, fetch_session=None, user=None, password=None, gauges=None, log=print):
    gauges, problems = (gauges, []) if gauges is not None else read_gauges()
    prev = {g["key"]: g for g in (previous or {}).get("gauges") or []}
    out, read_ok = [], 0
    s = fetch_session or Session()
    try:
        sign_in(s, user, password, log)
        signed = True
    except Exception as e:  # noqa: BLE001
        problems.append(f"sign-in: {type(e).__name__}: {e}"[:300])
        signed = False
    start = (now - dt.timedelta(hours=HOURS)).astimezone(TZ).replace(tzinfo=None)
    end = (now + dt.timedelta(minutes=30)).astimezone(TZ).replace(tzinfo=None)
    for g in gauges:
        entry = {k: g[k] for k in ("key", "label", "where", "kind", "unit", "order", "levels", "camera", "note")}
        old = prev.get(g["key"]) or {}
        try:
            if not signed:
                raise RuntimeError("not signed in")
            ser = parse_series(s.request(graph_url(g, start, end)))
            pts = [point(u, v) for u, v in ser if u >= now - dt.timedelta(hours=HOURS)]
            entry.update(points=pts, latest=pts[-1] if pts else old.get("latest"), fetched=now.strftime("%Y-%m-%dT%H:%MZ"), error=None)
            read_ok += 1
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {e}"[:200]
            problems.append(f"{g['key']}: {msg}")
            entry.update(points=[p for p in old.get("points") or [] if p[2] >= (now - dt.timedelta(hours=HOURS)).strftime("%Y-%m-%dT%H:%MZ")],
                         latest=old.get("latest"), fetched=old.get("fetched"), error=msg)
        out.append(entry)
    return {"generated_utc": now.strftime("%Y-%m-%dT%H:%MZ"), "source": BASE, "hours": HOURS,
            "gauges": out, "read": read_ok, "problems": problems}


def main(argv):
    path = argv[1]
    min_age = float(argv[argv.index("--min-age") + 1]) if "--min-age" in argv else 0
    previous = {}
    try:
        with open(path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        pass
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    last = previous.get("generated_utc")
    if last and min_age and now - dt.datetime.strptime(last, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=min_age):
        print(f"sfcjpa: last run {last}, younger than {min_age:g} min; kept")
        return 0
    res = update(previous, now, user=os.environ.get("CONTRAIL_USER"), password=os.environ.get("CONTRAIL_PASSWORD"))
    for g in res["gauges"]:
        print(f"{g['key']}: " + (f"{len(g['points'])} readings, latest {g['latest']}" if not g.get("error") else f"NOT READ ({g['error']}); kept {len(g['points'])}"))
    for p in res["problems"]:
        print("problem:", p)
    if not any(g["points"] or g.get("latest") for g in res["gauges"]):
        print("sfcjpa: nothing read or kept; not written")
        return 0
    with open(path, "w") as f:
        json.dump(res, f, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
