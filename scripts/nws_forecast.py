"""National Weather Service rain forecast for each creek (read by fetch_onerain.py).

For each creek, one point in its watershed (lookups/forecast_points.csv) is looked up on the NWS API
(api.weather.gov/points), and that grid cell's quantitative precipitation forecast (QPF, 6-hour periods,
the Bay Area office forecast) is added up for the next 6 hours, 24 hours and 3 days. The heaviest 6-hour
period is kept too. The result goes into creeks.json as each creek's "forecast"; the pages show it as
"Rain expected (NWS forecast)". It never changes a creek's status.

The forecast is read at most every FORECAST_EVERY_MIN minutes (lookups/settings.csv); in between, and when NWS
can't be reached, the previous forecast is kept for up to FORECAST_KEEP_HOURS.
"""

import csv
import datetime as dt
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
POINTS_CSV = os.path.join(HERE, "..", "lookups", "forecast_points.csv")
API = "https://api.weather.gov"
UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
MM_PER_IN = 25.4
UTC = dt.timezone.utc


def load_points(path=POINTS_CSV):
    """{creek id: {"lat", "lon", "place"}}; (points, problems)."""
    out, problems = {}, []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for n, r in enumerate(csv.DictReader(f), start=2):
                cid = (r.get("creek") or "").strip()
                if not cid:
                    continue
                try:
                    lat, lon = float(r["lat"]), float(r["lon"])
                except (TypeError, ValueError, KeyError):
                    problems.append(f"forecast_points.csv row {n}: lat/lon must be numbers")
                    continue
                if not (36 < lat < 39 and -124 < lon < -121):
                    problems.append(f"forecast_points.csv row {n}: {lat},{lon} is outside the Bay Area")
                    continue
                out[cid] = {"lat": round(lat, 4), "lon": round(lon, 4), "place": (r.get("place") or "").strip()}
    except OSError as e:
        problems.append(f"forecast_points.csv: {e}")
    return out, problems


_DUR = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$")


def parse_valid_time(s):
    """'2026-10-18T18:00:00+00:00/PT6H' -> (start UTC, end UTC)."""
    start, dur = s.split("/")
    t0 = dt.datetime.fromisoformat(start.replace("Z", "+00:00")).astimezone(UTC)
    m = _DUR.match(dur)
    if not m:
        raise ValueError(f"unknown duration {dur}")
    d, h, mi = (int(x or 0) for x in m.groups())
    return t0, t0 + dt.timedelta(days=d, hours=h, minutes=mi)


def periods(grid):
    """QPF periods from a gridpoints response: [(start, end, inches)], oldest first."""
    q = (grid.get("properties") or {}).get("quantitativePrecipitation") or {}
    uom = q.get("uom", "wmoUnit:mm")
    out = []
    for v in q.get("values") or []:
        if v.get("value") is None:
            continue
        t0, t1 = parse_valid_time(v["validTime"])
        val = float(v["value"])
        inches = val / MM_PER_IN if uom.endswith("mm") else val
        out.append((t0, t1, inches))
    return sorted(out)


def total(pers, a, b):
    """Rain expected between a and b; a period that only partly overlaps counts in proportion."""
    s = 0.0
    for t0, t1, x in pers:
        lo, hi = max(a, t0), min(b, t1)
        if hi > lo and t1 > t0:
            s += x * (hi - lo) / (t1 - t0)
    return s


def summarize(pers, now, issued=None):
    """{"next6", "next24", "next72", "peak_start", "peak_hours", "peak_in", "issued", "until"}: inches, UTC times."""
    if not pers:
        raise ValueError("no precipitation forecast in the response")
    h = dt.timedelta(hours=1)
    fut = [p for p in pers if p[1] > now and p[0] < now + 72 * h]
    peak = max(fut, key=lambda p: total([p], max(now, p[0]), p[1]), default=None)
    out = {"next6": round(total(pers, now, now + 6 * h), 2), "next24": round(total(pers, now, now + 24 * h), 2),
           "next72": round(total(pers, now, now + 72 * h), 2), "peak_start": None, "peak_hours": None, "peak_in": None,
           "until": _iso(pers[-1][1]), "issued": issued}
    if peak and total([peak], max(now, peak[0]), peak[1]) > 0:
        out.update(peak_start=_iso(max(now, peak[0])), peak_hours=round((peak[1] - max(now, peak[0])).total_seconds() / 3600, 1),
                   peak_in=round(total([peak], max(now, peak[0]), peak[1]), 2))
    return out


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%MZ")


def pack(pers, now):
    """Periods kept in creeks.json (so a kept forecast can be re-added up later): [[start, hours, inches]], next 3 days."""
    return [[_iso(a), round((b - a).total_seconds() / 3600, 2), round(x, 3)] for a, b, x in pers
            if b > now and a < now + dt.timedelta(hours=72)]


def unpack(rows):
    return [(_t(a), _t(a) + dt.timedelta(hours=h), x) for a, h, x in rows or []]


def issued_time(grid):
    s = (grid.get("properties") or {}).get("updateTime")
    return _iso(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)) if s else None


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def grid_url(lat, lon, fetch=get_json):
    p = fetch(f"{API}/points/{lat},{lon}")
    u = (p.get("properties") or {}).get("forecastGridData")
    if not (isinstance(u, str) and u.startswith(API + "/gridpoints/")):
        raise ValueError("no forecastGridData for this point")
    return u


def _t(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC) if s else None


def add_forecast(result, previous_file, now, settings, fetch=get_json, points=None):
    """Adds "forecast" to every creek in result (public and preview). now: aware UTC datetime.
    Never raises; problems go into each creek's forecast "error" and the returned list."""
    if points is None:
        points, problems = load_points()
    else:
        problems = []
    every = dt.timedelta(minutes=settings.get("FORECAST_EVERY_MIN", 60))
    keep = dt.timedelta(hours=settings.get("FORECAST_KEEP_HOURS", 12))
    old = {c["id"]: c.get("forecast") for c in (previous_file.get("creeks", []) + previous_file.get("creeks_preview", []))}
    grids = {}   # one request per grid cell, even when creeks share a point
    for c in result.get("creeks", []) + result.get("creeks_preview", []):
        pt, prev = points.get(c["id"]), old.get(c["id"]) or None
        if not pt:
            continue
        same_pt = prev and prev.get("lat") == pt["lat"] and prev.get("lon") == pt["lon"]
        fetched = _t(prev.get("fetched")) if same_pt else None
        fc = {"lat": pt["lat"], "lon": pt["lon"], "place": pt["place"]}
        try:
            if fetched and now - fetched < every and not prev.get("error"):
                fc.update({k: prev[k] for k in ("grid", "fetched", "periods", "issued") if k in prev}, error=None)
            else:
                url = prev.get("grid") if same_pt and prev.get("grid") else grid_url(pt["lat"], pt["lon"], fetch)
                if url not in grids:
                    grids[url] = fetch(url)
                pers = periods(grids[url])
                fc.update(grid=url, fetched=_iso(now), periods=pack(pers, now), issued=issued_time(grids[url]), error=None)
            fc.update(summarize(unpack(fc["periods"]), now, fc.get("issued")))
        except Exception as e:  # noqa: BLE001 - a forecast problem never stops the creek data
            msg = f"{type(e).__name__}: {e}"[:200]
            problems.append(f"{c['id']}: NWS forecast not read ({msg})")
            fc = {"lat": pt["lat"], "lon": pt["lon"], "place": pt["place"], "error": msg}
            if fetched and now - fetched < keep and prev.get("periods"):   # keep the last forecast for a while, marked
                try:
                    fc.update({k: prev[k] for k in ("grid", "fetched", "periods", "issued") if k in prev})
                    fc.update(summarize(unpack(prev["periods"]), now, prev.get("issued")))
                except Exception:  # noqa: BLE001
                    pass
        c["forecast"] = fc
    return problems
