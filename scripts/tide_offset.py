"""How much higher (or lower) than the tide table the water has been running at each NOAA tide station, over about
the last month: the "Bay offset" the tide pages add to the tide table after the NOAA projection ends (about 48 hours).

Method (persistence of the mean sea level anomaly; see lookups/THRESHOLDS_BASIS.md §4b):
  1. For each of the last BAY_OFFSET_DAYS complete days (Pacific), the day's average of measured minus tide table,
     from NOAA's 6-minute readings and 6-minute tide table at the station. A day counts only if at least 80% of its
     readings are there.
  2. The offset is the average of those daily averages, if at least two thirds of the days count.
Daily averages over a month keep out the short spikes (a storm surge lasts hours to a day or two) and keep the slow
part: seasonal and El Nino-type rises that last weeks to months. The pages show it as an assumption ("if the Bay stays
this high"), never as a forecast, and it never sets a status.

Writes tide_offset.json on the data branch. Recomputed once a day (the window moves by a day); in between, and when
NOAA can't be reached, the last good values are kept (the pages ignore them once they are too old).

Usage: python tide_offset.py OUTPUT.json
"""

import datetime as dt
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import creek_config  # noqa: E402
import creek_signals  # noqa: E402

NOAA = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
TZ = ZoneInfo("America/Los_Angeles")
DAY_COVERAGE = 0.8        # a day counts if at least this share of its 6-minute readings are there
WINDOW_COVERAGE = 2 / 3   # the offset needs at least this share of the days
RETRY_MIN = 60            # after a failed download, try that station again after this many minutes


def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def noaa_url(product, station, begin, end, **extra):
    q = dict(product=product, station=station, begin_date=begin.strftime("%Y%m%d %H:%M"), end_date=end.strftime("%Y%m%d %H:%M"),
             datum="MLLW", time_zone="lst_ldt", units="english", format="json", application="OneShorelineFEWS", **extra)
    return NOAA + "?" + urllib.parse.urlencode(q)


def series(j):
    """{Pacific clock time 'YYYY-MM-DD HH:MM': value} from a NOAA reply; blank or bad values left out."""
    if j.get("error"):
        raise ValueError(str(j["error"].get("message", j["error"]))[:150])
    out = {}
    for p in j.get("data") or j.get("predictions") or []:
        try:
            v = float(p["v"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(v):
            out[p["t"]] = v
    return out


def daily_means(measured, table):
    """[(date, mean measured minus tide table, readings)] for each day, oldest first."""
    days = {}
    for t, v in measured.items():
        p = table.get(t)
        if p is not None:
            days.setdefault(t[:10], []).append(v - p)
    return [(d, sum(x) / len(x), len(x)) for d, x in sorted(days.items())]


def compute(station, first, last, fetch=get_json):
    """Offset for whole days first..last (dates, Pacific). Raises if NOAA can't be read."""
    begin = dt.datetime.combine(first, dt.time(0, 0))
    end = dt.datetime.combine(last, dt.time(23, 54))
    measured = series(fetch(noaa_url("water_level", station, begin, end)))
    table = series(fetch(noaa_url("predictions", station, begin, end, interval="6")))
    if not table:
        raise ValueError("no tide table in the reply")
    n_days = (last - first).days + 1
    rows = daily_means(measured, table)
    good = [(d, m) for d, m, n in rows if n >= DAY_COVERAGE * 240]
    out = {"from": first.isoformat(), "to": last.isoformat(), "days": n_days, "days_used": len(good),
           "daily": [[d, round(m, 3)] for d, m in good], "offset_ft": None, "recent7_ft": None}
    if len(good) >= math.ceil(WINDOW_COVERAGE * n_days):
        out["offset_ft"] = round(sum(m for _, m in good) / len(good), 2)
        last7 = [m for d, m in good if d > (last - dt.timedelta(days=7)).isoformat()]
        if len(last7) >= 4:
            out["recent7_ft"] = round(sum(last7) / len(last7), 2)
    else:
        out["note"] = f"only {len(good)} of {n_days} days have enough readings"
    return out


def _utc(s):
    try:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def update(previous, now_utc, stations, days, fetch=get_json):
    """New tide_offset.json contents from the previous ones. Never raises."""
    local = now_utc.astimezone(TZ)
    last = local.date() - dt.timedelta(days=1)                 # yesterday: the last whole day
    first = last - dt.timedelta(days=int(days) - 1)
    stamp = now_utc.strftime("%Y-%m-%dT%H:%MZ")
    old = (previous or {}).get("stations") or {}
    out = {"generated": local.strftime("%Y-%m-%d %H:%M"), "generated_utc": stamp, "window_days": int(days),
           "method": "average over the window of each day's mean (NOAA measured minus NOAA tide table, 6-minute data)",
           "stations": {}}
    problems = []
    for sid, st in stations.items():
        prev = old.get(sid) or {}
        fresh = prev.get("to") == last.isoformat() and prev.get("days") == int(days) and not prev.get("error")
        tried = _utc(prev.get("attempt_utc"))
        if fresh or (prev.get("error") and tried and now_utc - tried < dt.timedelta(minutes=RETRY_MIN)):
            out["stations"][sid] = prev
            continue
        try:
            r = compute(sid, first, last, fetch)
            r.update(name=st.get("name") or sid, computed_utc=stamp, attempt_utc=stamp, error=None)
            out["stations"][sid] = r
        except Exception as e:  # noqa: BLE001 - one station's problem never stops the others or the data job
            msg = f"{type(e).__name__}: {e}"[:200]
            problems.append(f"{sid}: {msg}")
            keep = {k: prev[k] for k in ("from", "to", "days", "days_used", "daily", "offset_ft", "recent7_ft", "computed_utc") if k in prev}
            out["stations"][sid] = dict(keep, name=st.get("name") or sid, attempt_utc=stamp, error=msg)
    return out, problems


def main(argv):
    path = argv[1] if len(argv) > 1 else "tide_offset.json"
    try:
        with open(path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        previous = {}
    stations, errs = creek_config.load_tide_stations()
    settings, sp = creek_signals.load_settings()
    for p in errs + sp:
        print(f"settings: {p}", file=sys.stderr)
    if not stations:
        print("no tide stations; tide_offset.json left as it was", file=sys.stderr)
        return 0
    result, problems = update(previous, dt.datetime.now(dt.timezone.utc), stations, settings["BAY_OFFSET_DAYS"])
    for p in problems:
        print(f"tide offset: {p}", file=sys.stderr)
    for sid, r in result["stations"].items():
        print(f"{sid} {r.get('name')}: offset {r.get('offset_ft')} ft over {r.get('days_used')} of {r.get('days')} days "
              f"({r.get('from')} to {r.get('to')})" + (f" · last attempt failed: {r['error']}" if r.get("error") else ""))
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
