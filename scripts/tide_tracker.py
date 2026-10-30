"""Tide tracker for the water year (staff page TideTracker.html): what the Bay and the ocean actually did this season at
four NOAA tide gauges, against the tide table, the levels staff care about, and the gauges' own history.

Gauges: Redwood City 9414523, Alameda 9414750, San Francisco 9414290 (the Bay's long record, since the 1800s) and
Monterey 9413450 (the Coastside gauge). All heights ft NAVD88, local time (Pacific, daylight time in summer).

Levels at each gauge (lookups/tide_tracker_levels.csv adds staff levels; the first two come from NOAA's datums):
  MHHW                  NOAA's mean higher high water at the gauge
  NOAA minor flooding   NOAA's derived minor high tide flooding level: MHHW + 0.5 m + 4% of the great diurnal tide range
                        (MHHW - MLLW), the national threshold in NOAA's high tide flooding reports (Sweet et al. 2018)
  staff levels          e.g. Redwood City 1-year tide 8.3 and flood level 8.5; Monterey 1-year tide 6.87

This season (since Oct 1, from NOAA's 6-minute measured water level and tide table): for each day the highest water and
when, the tide table's highest, how far above the tide table the water ran (daily average and largest), and the minutes
at or above each level. The last 2 days are recomputed each run; earlier days are kept.

History (NOAA's high and low water record, one calendar year per request, fetched a few years per run until done; kept on
the data branch in tide_tracker_history.json): each day's highest high water. From it:
  - each month's highest water ranked against the same month in every year with enough data
  - this water year's highest so far ranked against every water year over the same dates
  - the usual number of days at or above each level in each month, and the usual range (10th-90th percentile) of the
    day's highest water for each date, over the last BASE_YEARS complete water years (a tidal epoch is 19 years)

Going forward only (no archive to fetch): National Weather Service coastal flood products for San Mateo County, and
NOAA's projection of each day's highest water made before the day began, compared with what happened.

Usage: python tide_tracker.py OUTPUT.json HISTORY.json [--min-age MINUTES]
"""

import csv
import datetime as dt
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEVELS_CSV = os.path.join(ROOT, "lookups", "tide_tracker_levels.csv")
NOAA = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
MDAPI = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{}/datums.json?units=english"
NWS = "https://api.weather.gov/alerts/active?area=CA"
UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
STATIONS = [  # id, name, side, first year to look for in NOAA's high/low record
    ("9414523", "Redwood City", "bay", 1974),
    ("9414750", "Alameda", "bay", 1939),
    ("9414290", "San Francisco", "bay", 1898),
    ("9413450", "Monterey", "coast", 1973),
]
COUNTY_SAME = "006081"          # San Mateo County
BASE_YEARS = 19                 # usual counts and ranges: the last 19 complete water years
MONTH_COVER = 0.8               # a month counts in the history if at least 80% of its days have data
HIST_BUDGET_S = 75              # time for history downloads in one run
HIST_MAX_REQUESTS = 20          # history years asked for in one run (NOAA refused with 403 after about 150 quick requests)
HIST_PAUSE_S = 1.0              # pause before each history request
RECOMPUTE_DAYS = 2              # the last 2 complete days are recomputed each run (NOAA fills gaps late)
FT_PER_M = 3.28084


# ---------------------------------------------------------------------------------------------------- NOAA
def get_json(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json, application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def noaa(product, station, begin, end, fetch=get_json, **extra):
    """[(local 'YYYY-MM-DD HH:MM', value, extra type)] from NOAA, ft NAVD88; [] when NOAA has no data for the dates."""
    q = dict(product=product, station=station, begin_date=begin.strftime("%Y%m%d %H:%M"), end_date=end.strftime("%Y%m%d %H:%M"),
             datum="NAVD", time_zone="lst_ldt", units="english", format="json", application="OneShorelineFEWS", **extra)
    j = fetch(NOAA + "?" + urllib.parse.urlencode(q))
    if j.get("error"):
        msg = str(j["error"].get("message", j["error"]))
        if "no data" in msg.lower():
            return []
        raise ValueError(msg[:150])
    out = []
    for p in j.get("data") or j.get("predictions") or []:
        try:
            v = float(p["v"])
        except (KeyError, TypeError, ValueError):
            continue
        if math.isfinite(v):
            out.append((p["t"], v, p.get("ty", "")))
    return out


def datums(station, fetch=get_json):
    """MHHW and MLLW in ft NAVD88 from NOAA's published datums."""
    d = {x.get("name"): x.get("value") for x in fetch(MDAPI.format(station)).get("datums") or []}
    nv = d.get("NAVD88")
    if nv is None or d.get("MHHW") is None or d.get("MLLW") is None:
        raise ValueError("NOAA datums incomplete for %s" % station)
    return round(float(d["MHHW"]) - float(nv), 2), round(float(d["MLLW"]) - float(nv), 2)


def minor_level(mhhw, mllw):
    """NOAA's derived minor high tide flooding level: MHHW + 0.5 m + 0.04 x great diurnal range (in metres)."""
    gt_m = (mhhw - mllw) / FT_PER_M
    return round(mhhw + (0.5 + 0.04 * gt_m) * FT_PER_M, 2)


def load_extra_levels(path=LEVELS_CSV):
    out = {}
    if not os.path.exists(path):
        return out
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                v = float(r["level_ft"])
            except (KeyError, TypeError, ValueError):
                continue
            out.setdefault(r.get("station", "").strip(), []).append(
                {"key": r.get("key", "").strip() or "level", "ft": v, "label": r.get("label", "").strip(), "source": r.get("source", "").strip()})
    return out


def levels_for(station, mhhw, mllw, extra):
    lv = [{"key": "mhhw", "ft": mhhw, "label": "MHHW (average high tide)", "source": "NOAA datums"},
          {"key": "minor", "ft": minor_level(mhhw, mllw), "label": "NOAA minor flooding (derived)",
           "source": "NOAA high tide flooding threshold: MHHW + 0.5 m + 4% of the tide range"}]
    lv += extra.get(station, [])
    return sorted(lv, key=lambda x: x["ft"])


# ---------------------------------------------------------------------------------------------------- dates
def water_year_start(d):
    return dt.date(d.year if d.month >= 10 else d.year - 1, 10, 1)


def wy_label(start):
    return "WY%d" % (start.year + 1)


def day_of_wy(d):
    return (d - water_year_start(d)).days


def daterange(a, b):
    while a <= b:
        yield a
        a += dt.timedelta(days=1)


# ---------------------------------------------------------------------------------------------------- this season
def day_stats(meas, table, levels):
    """One day's record from its 6-minute measured and tide table values [(time, v)]."""
    if not meas:
        return None
    tm = {t: v for t, v, _ in table}
    mx = max(meas, key=lambda p: p[1])
    res = [(t, v - tm[t]) for t, v, _ in meas if t in tm]
    rec = {"max": round(mx[1], 2), "t": mx[0][11:16], "cover": round(min(1.0, len(meas) / 240), 2),
           "table": round(max(tm.values()), 2) if tm else None,
           "res_mean": round(statistics.mean(r for _, r in res), 2) if res else None,
           "res_max": round(max(r for _, r in res), 2) if res else None,
           "res_t": max(res, key=lambda p: p[1])[0][11:16] if res else None,
           "min": {}}
    for lv in levels:
        rec["min"][lv["key"]] = 6 * sum(1 for _, v, _ in meas if v >= lv["ft"])
    return rec


def update_season(prev_days, station, levels, today, fetch=get_json, log=print):
    """{date: record} for the water year to date; days missing or within RECOMPUTE_DAYS (and today) are fetched."""
    start = water_year_start(today)
    days = {d: r for d, r in (prev_days or {}).items() if d >= start.isoformat()}
    keep_to = today - dt.timedelta(days=RECOMPUTE_DAYS)
    need = [d for d in daterange(start, today) if d >= keep_to or d.isoformat() not in days]
    if not need:
        return days
    a = need[0]
    while a <= need[-1]:
        b = min(need[-1], a + dt.timedelta(days=29))
        t0 = dt.datetime.combine(a, dt.time(0, 0))
        t1 = dt.datetime.combine(b, dt.time(23, 54))
        meas = noaa("water_level", station, t0, t1, fetch)
        table = noaa("predictions", station, t0, t1, fetch)
        by = {}
        for p in meas:
            by.setdefault(p[0][:10], [[], []])[0].append(p)
        for p in table:
            by.setdefault(p[0][:10], [[], []])[1].append(p)
        for d in daterange(a, b):
            k = d.isoformat()
            m, t = by.get(k, [[], []])
            rec = day_stats(m, t, levels)
            if rec:
                if d == today:
                    rec["partial"] = True
                days[k] = rec
        a = b + dt.timedelta(days=1)
    return days


# ---------------------------------------------------------------------------------------------------- history
def year_daily_max(rows):
    """{date: highest high water} from NOAA high/low rows."""
    out = {}
    for t, v, ty in rows:
        if ty and ty.strip().upper() not in ("H", "HH"):
            continue
        d = t[:10]
        if d not in out or v > out[d]:
            out[d] = v
    return out


def update_history(hist, station, first_year, wy_start, fetch=get_json, budget_s=HIST_BUDGET_S, log=print, clock=time.time):
    """Fills hist (station -> {year: {"d": {mmdd: ft}, "to": last date asked}}) newest years first, within the time budget.
    Calendar years up to the day before this water year began; the last one is completed once it has ended."""
    h = hist.setdefault(station, {})
    last_day = wy_start - dt.timedelta(days=1)
    t_end = clock() + budget_s
    for y in range(last_day.year, first_year - 1, -1):
        to = min(dt.date(y, 12, 31), last_day).isoformat()
        cur = h.get(str(y))
        if cur and cur.get("to") == to:
            continue
        if clock() > t_end:
            break
        try:
            rows = noaa("high_low", station, dt.datetime(y, 1, 1), dt.datetime.combine(dt.date.fromisoformat(to), dt.time(23, 59)), fetch)
        except ValueError as e:   # NOAA answered with an error for this year (e.g. no NAVD88 for old data): keep going
            log("  %s %d high/low: %s" % (station, y, e))
            h[str(y)] = {"to": to, "d": {}, "err": str(e)[:120]}
            continue
        except Exception as e:   # noqa: BLE001  (network): try again next run
            log("  %s %d high/low: %s" % (station, y, e))
            break
        dm = year_daily_max(rows)
        h[str(y)] = {"to": to, "d": {k[5:].replace("-", ""): round(v, 2) for k, v in sorted(dm.items())}}
    return h


def history_days(h):
    """{date (datetime.date): highest high water} from one station's history."""
    out = {}
    for y, rec in h.items():
        for md, v in rec.get("d", {}).items():
            try:
                out[dt.date(int(y), int(md[:2]), int(md[2:]))] = v
            except ValueError:
                continue
    return out


def month_key(d):
    return "%04d-%02d" % (d.year, d.month)


def days_in_month(y, m):
    return ((dt.date(y + (m == 12), m % 12 + 1, 1)) - dt.date(y, m, 1)).days


def history_stats(hd, levels, today):
    """Ranks, usual counts and the usual range by date, from the history's daily highs."""
    wy0 = water_year_start(today)
    months = {}
    for d, v in hd.items():
        m = months.setdefault((d.year, d.month), [])
        m.append(v)
    full = {k: v for k, v in months.items() if len(v) >= MONTH_COVER * days_in_month(*k)}
    base_wys = [wy0.year - k for k in range(1, BASE_YEARS + 1)]   # water years starting Oct of these years
    def in_base(y, m):
        return (y if m >= 10 else y - 1) in base_wys
    usual = {}
    for mo in range(1, 13):
        ks = [k for k in full if k[1] == mo and in_base(*k)]
        usual[str(mo)] = {"years": len(ks), "max_median": round(statistics.median([max(full[k]) for k in ks]), 2) if ks else None,
                          "days": {lv["key"]: (round(statistics.mean([sum(1 for v in full[k] if v >= lv["ft"]) for k in ks]), 1) if ks else None)
                                   for lv in levels}}
    month_max = {}
    for (y, mo), vals in full.items():
        month_max.setdefault(str(mo), []).append([y, round(max(vals), 2)])
    # the usual range of the day's highest water for each day of the water year (+/- 3 days), over the base years
    band = []
    by_doy = {}
    for d, v in hd.items():
        if water_year_start(d).year in base_wys:
            by_doy.setdefault(day_of_wy(d), []).append(v)
    for i in range(366):
        vals = [v for j in range(i - 3, i + 4) for v in by_doy.get(j % 366, [])]
        if len(vals) >= 10:
            q = statistics.quantiles(vals, n=10)
            band.append([round(q[0], 2), round(statistics.median(vals), 2), round(q[8], 2)])
        else:
            band.append(None)
    # each past water year's highest over the same dates as this one so far
    n_days = (today - wy0).days
    wy_best = {}
    for d, v in hd.items():
        s = water_year_start(d)
        if (d - s).days <= n_days:
            wy_best[s.year] = max(wy_best.get(s.year, -99), v)
    wy_cover = {}
    for d in hd:
        s = water_year_start(d)
        if (d - s).days <= n_days:
            wy_cover[s.year] = wy_cover.get(s.year, 0) + 1
    wy_same = [[y + 1, round(v, 2)] for y, v in wy_best.items() if wy_cover[y] >= MONTH_COVER * (n_days + 1) and y < wy0.year]
    years = sorted({d.year for d in hd})
    return {"usual": usual, "month_max": month_max, "band": band, "wy_same_dates": sorted(wy_same),
            "base": [min(base_wys) + 1, max(base_wys) + 1], "first_year": years[0] if years else None, "last_year": years[-1] if years else None,
            "years_with_data": len(years)}


# ---------------------------------------------------------------------------------------------------- forward-only logs
def nws_coastal(previous, fetch=get_json, log=print):
    """Coastal flood products for San Mateo County, kept for the water year."""
    keep = {a["id"]: a for a in previous or []}
    try:
        j = fetch(NWS)
    except Exception as e:   # noqa: BLE001
        log("  NWS: %s" % e)
        return list(keep.values())
    for f in j.get("features") or []:
        p = f.get("properties") or {}
        same = (p.get("geocode") or {}).get("SAME") or []
        if not any(str(s)[-6:] == COUNTY_SAME for s in same):
            continue
        if "coastal flood" not in str(p.get("event", "")).lower() or p.get("status") != "Actual":
            continue
        key = "%s|%s" % (p.get("event"), (p.get("ends") or p.get("expires") or "")[:16])
        keep[key] = {"id": key, "event": p.get("event"), "onset": p.get("onset") or p.get("effective"),
                     "ends": p.get("ends") or p.get("expires"), "sent": p.get("sent"), "headline": (p.get("headline") or "")[:200]}
    return sorted(keep.values(), key=lambda a: a.get("onset") or "")


def update_projection(prev, station, today, now_local, fetch=get_json, log=print):
    """{date: projected highest} for tomorrow and the day after, as NOAA projected them before the day began (the last
    run before midnight wins)."""
    out = dict(prev or {})
    try:
        rows = noaa("ofs_water_level", station, dt.datetime.combine(today, dt.time(0, 0)), dt.datetime.combine(today + dt.timedelta(days=3), dt.time(0, 0)), fetch)
    except Exception as e:   # noqa: BLE001
        log("  %s projection: %s" % (station, e))
        return out
    by = {}
    for t, v, _ in rows:
        by[t[:10]] = max(by.get(t[:10], -99), v)
    for k in (1, 2):
        d = (today + dt.timedelta(days=k)).isoformat()
        if d in by and len([1 for t, _, _ in rows if t[:10] == d]) >= 20:   # most of the day covered
            out[d] = {"ft": round(by[d], 2), "made": now_local.strftime("%Y-%m-%d %H:%M"), "lead_days": k}
    return out


# ---------------------------------------------------------------------------------------------------- summaries
def month_summary(days, levels):
    out = {}
    for d, r in sorted(days.items()):
        m = out.setdefault(d[:7], {"days": 0, "max": None, "max_date": None, "table": None, "res": [], "surge": None, "surge_date": None,
                                    "count": {lv["key"]: 0 for lv in levels}, "hours": {lv["key"]: 0 for lv in levels}})
        m["days"] += 1
        if m["max"] is None or r["max"] > m["max"]:
            m["max"], m["max_date"] = r["max"], d + " " + r["t"]
        if r.get("table") is not None and (m["table"] is None or r["table"] > m["table"]):
            m["table"] = r["table"]
        if r.get("res_mean") is not None:
            m["res"].append(r["res_mean"])
        if r.get("res_max") is not None and (m["surge"] is None or r["res_max"] > m["surge"]):
            m["surge"], m["surge_date"] = r["res_max"], d + " " + (r.get("res_t") or "")
        for lv in levels:
            k = lv["key"]
            m["count"][k] += 1 if r["max"] >= lv["ft"] else 0
            m["hours"][k] = round(m["hours"][k] + r["min"].get(k, 0) / 60, 1)
    for m in out.values():
        m["res_mean"] = round(statistics.mean(m["res"]), 2) if m["res"] else None
        del m["res"]
    return out


def rank(value, others):
    """1 = highest; ties share the better rank."""
    return 1 + sum(1 for v in others if v > value)


def fetch_station(sid, prev_st, extra, today, now_local, fetch, log):
    """The parts NOAA must answer this run (datums, this season, the projection), before any history download, so a
    busy NOAA (it refuses with 403 after many requests) never costs the season numbers."""
    try:
        mhhw, mllw = datums(sid, fetch)
    except Exception:   # noqa: BLE001  keep last run's datums if NOAA won't answer
        if not prev_st or prev_st.get("mhhw") is None:
            raise
        mhhw, mllw = prev_st["mhhw"], prev_st["mllw"]
    levels = levels_for(sid, mhhw, mllw, extra)
    days = update_season((prev_st or {}).get("days"), sid, levels, today, fetch, log)
    proj = update_projection((prev_st or {}).get("proj"), sid, today, now_local, fetch, log)
    proj = {d: p for d, p in proj.items() if d >= water_year_start(today).isoformat()}
    return {"mhhw": mhhw, "mllw": mllw, "levels": levels, "days": days, "proj": proj}


def build_station(sid, name, side, part, hist, today):
    levels, days = part["levels"], part["days"]
    months = month_summary(days, levels)
    hd = history_days(hist.get(sid, {}))
    hs = history_stats(hd, levels, today) if hd else None
    ranks = {}
    if hs:
        for mk, m in months.items():
            mo = str(int(mk[5:]))
            past = [v for y, v in hs["month_max"].get(mo, []) if y != int(mk[:4])]
            if past and m["max"] is not None:
                rec = max(hs["month_max"][mo], key=lambda p: p[1]) if hs["month_max"].get(mo) else None
                ranks[mk] = {"rank": rank(m["max"], past), "of": len(past) + 1, "record": rec}
        season_max = max((r["max"] for r in days.values()), default=None)
        past = [v for y, v in hs["wy_same_dates"]]
        if season_max is not None and past:
            ranks["season"] = {"rank": rank(season_max, past), "of": len(past) + 1, "highest": max(hs["wy_same_dates"], key=lambda p: p[1])}
    return {"id": sid, "name": name, "side": side, "mhhw": part["mhhw"], "mllw": part["mllw"], "levels": levels, "days": days,
            "months": months, "history": hs, "ranks": ranks, "proj": part["proj"]}


def run(previous, history, now_utc, fetch=get_json, log=print, budget_s=HIST_BUDGET_S, clock=time.time, extra=None,
        max_requests=None, pause=None, sleep=None):
    from zoneinfo import ZoneInfo
    now_local = now_utc.astimezone(ZoneInfo("America/Los_Angeles")).replace(tzinfo=None)
    today = now_local.date()
    wy0 = water_year_start(today)
    extra = load_extra_levels() if extra is None else extra
    stations, problems = [], []
    prev_st = {s["id"]: s for s in (previous or {}).get("stations", [])} if (previous or {}).get("water_year") == wy_label(wy0) else {}
    # 1. this season at every gauge
    parts = {}
    for sid, name, side, first in STATIONS:
        try:
            parts[sid] = fetch_station(sid, prev_st.get(sid), extra, today, now_local, fetch, log)
        except Exception as e:   # noqa: BLE001
            problems.append("%s: %s" % (name, str(e)[:160]))
            log("  %s: %s" % (name, e))
    # 2. the history, a few years at a time, gently (NOAA refuses after too many quick requests); any refusal ends it for this run
    left = [HIST_MAX_REQUESTS if max_requests is None else max_requests]
    pause = HIST_PAUSE_S if pause is None else pause
    sleep = sleep or time.sleep

    def slow_fetch(url):
        if left[0] <= 0:
            raise RuntimeError("history request limit for this run")
        left[0] -= 1
        if pause:
            sleep(pause)
        try:
            return fetch(url)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):   # NOAA is refusing: no more history this run
                left[0] = 0
            raise
    t_end = clock() + budget_s
    for sid, name, side, first in STATIONS:
        if left[0] <= 0 or clock() > t_end:
            break
        update_history(history, sid, first, wy0, slow_fetch, max(0.0, t_end - clock()), log, clock)
    # 3. the numbers
    for sid, name, side, first in STATIONS:
        if sid in parts:
            stations.append(build_station(sid, name, side, parts[sid], history, today))
        elif sid in prev_st:
            stations.append(prev_st[sid])
    nws = nws_coastal([a for a in (previous or {}).get("nws", []) if (a.get("onset") or "") >= wy0.isoformat()], fetch, log)
    return {"generated": now_local.strftime("%Y-%m-%d %H:%M"), "generated_utc": now_utc.strftime("%Y-%m-%dT%H:%MZ"),
            "water_year": wy_label(wy0), "wy_start": wy0.isoformat(), "stations": stations, "nws": nws, "problems": problems}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_path, hist_path = args[0], args[1]
    min_age = float(sys.argv[sys.argv.index("--min-age") + 1]) if "--min-age" in sys.argv else 0
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)

    def load(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}
    previous, history = load(out_path), load(hist_path)
    last = previous.get("generated_utc")
    if last and min_age and now - dt.datetime.strptime(last, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=min_age):
        print("  updated at %s; not again yet" % last)
        return
    out = run(previous, history, now)
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f, separators=(",", ":"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"))
    for s in out["stations"]:
        h = s.get("history") or {}
        print("  %s: %d days this season, history %s-%s (%s years)" % (s["name"], len(s["days"]), h.get("first_year"), h.get("last_year"), h.get("years_with_data")))
    if out["problems"]:
        print("  problems: " + "; ".join(out["problems"]))


if __name__ == "__main__":
    main()
