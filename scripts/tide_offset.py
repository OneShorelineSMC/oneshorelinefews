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

Also, once a week, the outlook the calendars use after the next 6 weeks (outlook(); lookups/THRESHOLDS_BASIS.md §4b):
from NOAA's monthly means at San Francisco (9414290, the Bay's long record) over the last OUTLOOK_YEARS years, how far
the Bay usually runs above the tide table in each calendar month (a sea level trend plus a seasonal part), how quickly
a month's departure from that fades into the next months (lag-1 autocorrelation, for damped persistence), and how
much higher winter months run per degree of the Oceanic Nino Index (NOAA CPC), with the latest ONI.

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
OUTLOOK_STATION = "9414290"   # San Francisco: the Bay's long record; its month-to-month departures stand for the Bay
OUTLOOK_YEARS = 20            # years of monthly means used
OUTLOOK_EVERY_DAYS = 7        # recomputed this often (monthly data changes once a month)
OUTLOOK_AHEAD_MONTHS = 9      # usual height above the tide table given for this month and the next 8
WINTER = (11, 12, 1, 2, 3)    # the months El Nino raises the Bay most (Nov-Mar)
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ONI_SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]   # centred on Jan..Dec


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


# ---------------------------------------------------------------- outlook (weekly)
def day_url(product, station, begin, end, **extra):
    q = dict(product=product, station=station, begin_date=begin.strftime("%Y%m%d"), end_date=end.strftime("%Y%m%d"),
             datum="MLLW", time_zone="lst_ldt", units="english", format="json", application="OneShorelineFEWS", **extra)
    return NOAA + "?" + urllib.parse.urlencode(q)


def monthly_residuals(station, first_year, last_year, fetch=get_json):
    """{(year, month): NOAA monthly mean sea level minus the month's mean tide table (hourly)}, ft."""
    j = fetch(day_url("monthly_mean", station, dt.date(first_year, 1, 1), dt.date(last_year, 12, 31)))
    if j.get("error"):
        raise ValueError(str(j["error"].get("message", j["error"]))[:150])
    msl = {}
    for r in j.get("data") or []:
        try:
            msl[(int(r["year"]), int(r["month"]))] = float(r["MSL"])
        except (KeyError, TypeError, ValueError):
            continue
    out = {}
    for y in range(first_year, last_year + 1):
        pred = series(fetch(day_url("predictions", station, dt.date(y, 1, 1), dt.date(y, 12, 31), interval="h")))
        by = {}
        for t, v in pred.items():
            by.setdefault((int(t[:4]), int(t[5:7])), []).append(v)
        for k, vs in by.items():
            if k in msl and len(vs) >= 24 * 25:
                out[k] = msl[k] - sum(vs) / len(vs)
    return out


def _t(y, m):
    return y + (m - 0.5) / 12


def fit_months(res):
    """Trend plus a seasonal part, and what is left: (a, b, t0, {month: s}, {(y, m): departure})."""
    keys = sorted(res)
    t0 = sum(_t(*k) for k in keys) / len(keys)
    s = {m: 0.0 for m in range(1, 13)}
    a = b = 0.0
    for _ in range(10):   # trend and seasonal part, each fitted with the other taken out (converges in a few rounds)
        xs = [_t(*k) - t0 for k in keys]
        ys = [res[k] - s[k[1]] for k in keys]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        b = sum((x - mx) * (yv - my) for x, yv in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
        a = my - b * mx
        for m in range(1, 13):
            d = [res[k] - a - b * (_t(*k) - t0) for k in keys if k[1] == m]
            s[m] = sum(d) / len(d) if d else 0.0
        mean_s = sum(s.values()) / 12
        s = {m: v - mean_s for m, v in s.items()}
        a += mean_s
    dep = {k: res[k] - (a + b * (_t(*k) - t0) + s[k[1]]) for k in keys}
    return a, b, t0, s, dep


def lag_corr(dep, lag):
    pairs = []
    for (y, m), v in dep.items():
        y2, m2 = y + (m - 1 + lag) // 12, (m - 1 + lag) % 12 + 1
        if (y2, m2) in dep:
            pairs.append((v, dep[(y2, m2)]))
    return corr(pairs)


def corr(pairs):
    if len(pairs) < 6:
        return None
    xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs)); sy = math.sqrt(sum((v - my) ** 2 for v in ys))
    return None if not sx or not sy else sum((x - mx) * (v - my) for x, v in zip(xs, ys)) / (sx * sy)


def parse_oni(text):
    """{(year, centre month): ONI} from CPC's oni.ascii.txt ("SEAS YR TOTAL ANOM"), and the latest (season, year, value)."""
    out, last = {}, None
    for line in text.splitlines():
        f = line.split()
        if len(f) >= 4 and f[0] in ONI_SEASONS:
            try:
                y, v = int(f[1]), float(f[3])
            except ValueError:
                continue
            m = ONI_SEASONS.index(f[0]) + 1
            out[(y, m)] = v
            last = (f[0], y, v)
    return out, last


def get_text(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def outlook(now_local, fetch=get_json, fetch_text=get_text, station=OUTLOOK_STATION, years=OUTLOOK_YEARS):
    """The calendar outlook (see the top of this file). Raises if NOAA can't be read; the El Nino part is left out
    (enso: null) if CPC can't."""
    last_year = now_local.year - 1
    res = monthly_residuals(station, last_year - years + 1, last_year, fetch)
    if len(res) < 12 * years * 0.6:
        raise ValueError(f"only {len(res)} months of data")
    a, b, t0, s, dep = fit_months(res)
    normal = {}
    for k in range(OUTLOOK_AHEAD_MONTHS):
        y, m = now_local.year + (now_local.month - 1 + k) // 12, (now_local.month - 1 + k) % 12 + 1
        normal[f"{y:04d}-{m:02d}"] = round(a + b * (_t(y, m) - t0) + s[m], 2)
    out = {"station": station, "years": [last_year - years + 1, last_year], "months_used": len(res),
           "trend_ft_per_year": round(b, 4), "seasonal_ft": {str(m): round(v, 2) for m, v in s.items()},
           "normal_ft": normal, "r1": round(lag_corr(dep, 1), 2), "r2": round(lag_corr(dep, 2), 2),
           "departure_sd_ft": round(math.sqrt(sum(v * v for v in dep.values()) / len(dep)), 2), "enso": None}
    try:
        oni, latest = parse_oni(fetch_text(ONI_URL))
        pairs = [(oni[k], v) for k, v in dep.items() if k[1] in WINTER and k in oni]
        r = corr(pairs)
        if r is not None and latest:
            mx = sum(p[0] for p in pairs) / len(pairs)
            my = sum(p[1] for p in pairs) / len(pairs)
            slope = sum((x - mx) * (v - my) for x, v in pairs) / sum((x - mx) ** 2 for x, _ in pairs)
            out["enso"] = {"slope_ft_per_c": round(slope, 3), "r": round(r, 2), "n": len(pairs),
                           "significant": abs(r) > 2 / math.sqrt(len(pairs)), "oni": latest[2], "oni_season": f"{latest[0]} {latest[1]}",
                           "months": list(WINTER)}
    except Exception as e:  # noqa: BLE001 - CPC down: the outlook still has the usual monthly heights
        out["enso_error"] = f"{type(e).__name__}: {e}"[:150]
    return out


def _utc(s):
    try:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError):
        return None


def update(previous, now_utc, stations, days, fetch=get_json, outlook_fn=None):
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
    # the calendar outlook, once a week (kept as it was when NOAA can't be reached)
    ol = (previous or {}).get("outlook") or {}
    olt = _utc(ol.get("computed_utc")) or _utc(ol.get("attempt_utc"))
    if outlook_fn is None:   # (tests of the offset alone)
        if ol:
            out["outlook"] = ol
    elif olt and now_utc - olt < dt.timedelta(days=OUTLOOK_EVERY_DAYS) and (ol.get("computed_utc") or now_utc - olt < dt.timedelta(minutes=RETRY_MIN)):
        out["outlook"] = ol
    else:
        try:
            out["outlook"] = dict(outlook_fn(local), computed_utc=stamp, attempt_utc=stamp, error=None)
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {e}"[:200]
            problems.append(f"outlook: {msg}")
            out["outlook"] = dict({k: v for k, v in ol.items() if k not in ("attempt_utc", "error")}, attempt_utc=stamp, error=msg)
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
    result, problems = update(previous, dt.datetime.now(dt.timezone.utc), stations, settings["BAY_OFFSET_DAYS"], outlook_fn=outlook)
    for p in problems:
        print(f"tide offset: {p}", file=sys.stderr)
    ol = result.get("outlook") or {}
    if ol.get("normal_ft"):
        en = ol.get("enso") or {}
        print(f"outlook ({ol.get('station')} {ol.get('years')}): usual above the tide table {ol['normal_ft']}; r1 {ol.get('r1')}, "
              f"r2 {ol.get('r2')}; El Nino {en.get('slope_ft_per_c')} ft per C (r {en.get('r')}, n {en.get('n')}), "
              f"ONI {en.get('oni')} ({en.get('oni_season')})" + (f" · last attempt failed: {ol['error']}" if ol.get("error") else ""))
    for sid, r in result["stations"].items():
        print(f"{sid} {r.get('name')}: offset {r.get('offset_ft')} ft over {r.get('days_used')} of {r.get('days')} days "
              f"({r.get('from')} to {r.get('to')})" + (f" · last attempt failed: {r['error']}" if r.get("error") else ""))
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
