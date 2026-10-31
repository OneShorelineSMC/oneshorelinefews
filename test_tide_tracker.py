"""Checks for scripts/tide_tracker.py with made-up NOAA replies (no network). Run: python scripts/test_tide_tracker.py"""

import datetime as dt
import math
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tide_tracker as T
T.HIST_PAUSE_S = 0
import tide_offset
tide_offset.get_text = lambda url, timeout=30: ""   # no network in tests: CPC's ONI table comes back empty

fails = checks = 0


def check(name, ok):
    global fails, checks
    checks += 1
    if not ok:
        print("FAIL " + name)
        fails += 1


# ---- NOAA's derived minor flooding level: Alameda (MHHW 6.37, MLLW about -0.1) is about 1.9 ft above MHHW (NOAA's outlook)
check("minor level = MHHW + 0.5 m + 4% of the range", abs(T.minor_level(6.37, -0.10) - (6.37 + 1.90)) < 0.03)
check("Redwood City's minor level is about 9.0 ft", abs(T.minor_level(7.02, -1.18) - 9.0) < 0.05)

# ---- water year
check("water year starts Oct 1", T.water_year_start(dt.date(2026, 10, 29)) == dt.date(2026, 10, 1)
      and T.water_year_start(dt.date(2027, 3, 1)) == dt.date(2026, 10, 1) and T.wy_label(dt.date(2026, 10, 1)) == "WY2027")


# ---- a made-up Bay: a 12.42-hour tide of 3.5 ft around 3.5 ft NAVD88, running 1 ft above the table; one surge day
def table_at(t):
    h = (t - dt.datetime(2000, 1, 1)).total_seconds() / 3600
    return 3.5 + 3.5 * math.cos(2 * math.pi * h / 12.42) + 0.6 * math.cos(2 * math.pi * h / 24.84)


SURGE_DAY = dt.date(2026, 10, 20)


def meas_at(t, station):
    v = table_at(t) + 1.0
    if t.date() == SURGE_DAY:
        v += 1.2
    if station == "9413450":
        v -= 1.5
    return v


calls = []
MEAS_TO = [dt.datetime(2026, 10, 29, 17, 0)]


def fetch(url):
    calls.append(url)
    if "datums.json" in url:
        st = url.split("/stations/")[1].split("/")[0]
        mh = {"9414523": 7.02, "9414750": 6.37, "9414290": 5.86, "9413450": 5.48}[st]
        return {"datums": [{"name": "MHHW", "value": mh + 10}, {"name": "MLLW", "value": 10 - 0.1}, {"name": "NAVD88", "value": 10.0}]}
    if "arcgis.com" in url:   # the study's points: one near Redwood City, one far away
        if url.endswith("FeatureServer?f=json"):
            return {"layers": [{"id": 3, "name": "points"}]}
        if url.endswith("/3?f=json"):
            return {"fields": [{"name": "OBJECTID", "type": "esriFieldTypeOID"}, {"name": "PointID", "type": "esriFieldTypeInteger"},
                               {"name": "MHHW", "type": "esriFieldTypeDouble"}] +
                              [{"name": "ET_%dYR" % t, "alias": "%d-yr extreme tide" % t, "type": "esriFieldTypeDouble"} for t in (1, 2, 5, 10, 25, 50, 100, 500)]}
        vals = {1: 8.3, 2: 8.6, 5: 9.0, 10: 9.3, 25: 9.7, 50: 10.0, 100: 10.3, 500: 11.0}
        mk = lambda pid, x, y, add: {"geometry": {"x": x, "y": y}, "attributes": dict({"OBJECTID": pid, "PointID": 760 + pid, "MHHW": 7.1},   # noqa: E731
                                                                                         **{"ET_%dYR" % t: v + add for t, v in vals.items()})}
        return {"features": [mk(1, -122.2120, 37.5080, 0.0), mk(2, -122.2500, 37.5300, 0.5)]}
    if "weather.gov" in url:
        return {"features": [
            {"properties": {"event": "Coastal Flood Advisory", "status": "Actual", "geocode": {"SAME": ["006081"]}, "onset": "2026-10-20T08:00:00-07:00",
                            "ends": "2026-10-20T14:00:00-07:00", "sent": "2026-10-19T15:00:00-07:00", "headline": "Coastal Flood Advisory"}},
            {"properties": {"event": "Coastal Flood Advisory", "status": "Actual", "geocode": {"SAME": ["006001"]}, "onset": "2026-10-20T08:00:00-07:00"}},
            {"properties": {"event": "Wind Advisory", "status": "Actual", "geocode": {"SAME": ["006081"]}}}]}
    q = dict(urllib.parse.parse_qsl(url.split("?", 1)[1]))
    st, prod = q["station"], q["product"]
    a = dt.datetime.strptime(q["begin_date"], "%Y%m%d %H:%M")
    b = dt.datetime.strptime(q["end_date"], "%Y%m%d %H:%M")
    nodata = {"error": {"message": "No data was found. This product may not be offered at this station at the requested time."}}
    if prod == "hourly_height":   # old years: hourly heights on the station datum only (MLLW 0.1 ft below NAVD88 here)
        if a.year >= 1950 or q["datum"] != "MLLW":
            return nodata
        out, t = [], a
        while t <= b:
            v = 6.0 + 1.5 * math.cos(2 * math.pi * (t.timetuple().tm_yday - 15) / 365) + 0.01 * (t.year - 1990)
            out.append({"t": t.strftime("%Y-%m-%d %H:00"), "v": "%.3f" % ((v if t.hour == 12 else v - 2) + 0.1)})
            t += dt.timedelta(hours=1)
        return {"data": out}
    if prod == "high_low":
        if a.year < 1950 or (a.year < 1990 and q["datum"] == "NAVD"):
            return nodata
        mllw = 0.1 if q["datum"] == "MLLW" else 0.0   # on MLLW the same water reads 0.1 ft higher
        if st == "9414290" and a.year == 1995:
            return {"error": {"message": "The requested datum NAVD is not available for this period"}}
        out, t = [], a
        while t <= b:   # one high a day at noon: higher in winter, a bit higher each year
            v = 6.0 + 1.5 * math.cos(2 * math.pi * (t.timetuple().tm_yday - 15) / 365) + 0.01 * (t.year - 1990)
            out.append({"t": t.strftime("%Y-%m-%d 12:00"), "v": "%.3f" % (v + mllw), "ty": "HH"})
            out.append({"t": t.strftime("%Y-%m-%d 05:00"), "v": "%.3f" % (v - 1), "ty": " H"})
            out.append({"t": t.strftime("%Y-%m-%d 18:00"), "v": "0.5", "ty": "LL"})
            t += dt.timedelta(days=1)
        return {"data": out}
    step = dt.timedelta(minutes=6)
    out, t = [], a
    while t <= b:
        if prod == "predictions":
            out.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": "%.3f" % table_at(t)})
        elif prod == "water_level":
            if t <= MEAS_TO[0]:   # measured up to now
                out.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": "%.3f" % meas_at(t, st)})
        elif prod == "ofs_water_level":
            out.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": "%.3f" % (table_at(t) + 1.1)})
        t += step
    return {"data": out} if prod != "predictions" else {"predictions": out}


clock_t = [0.0]


def clock():
    clock_t[0] += 0.5   # each call: half a second
    return clock_t[0]


NOW = dt.datetime(2026, 10, 30, 0, 5, tzinfo=dt.timezone.utc)   # Oct 29, 5:05 PM PDT
extra = {"9414523": [{"key": "oneyear", "ft": 8.3, "label": "1-year tide", "source": "x"}, {"key": "flood", "ft": 8.5, "label": "Flood level", "source": "x"}]}
hist = {}
out = T.run({}, hist, NOW, fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
check("no problems", out["problems"] == [])
check("water year WY2027 from Oct 1", out["water_year"] == "WY2027" and out["wy_start"] == "2026-10-01")
s = {x["id"]: x for x in out["stations"]}
r = s["9414523"]
check("four gauges", len(out["stations"]) == 4)
check("Redwood City levels: MHHW, 1-year, flood, NOAA minor, in order", [l["key"] for l in r["levels"]] == ["mhhw", "oneyear", "flood", "minor"])
check("29 days so far, today partial", len(r["days"]) == 29 and r["days"]["2026-10-29"].get("partial") and not r["days"]["2026-10-28"].get("partial"))
tdy = r["days"]["2026-10-29"]
check("today: the tide table's peak time is kept, and whether it has passed (measured to 5 PM)", tdy.get("table_t") is not None and
      tdy["peak_passed"] == (int(tdy["table_t"][:2]) * 60 + int(tdy["table_t"][3:]) + 60 <= 17 * 60))
check("complete days carry no peak flag", "peak_passed" not in r["days"]["2026-10-28"])
d = r["days"]["2026-10-20"]
check("skew surge on the surge day: 1 + 1.2 ft above each predicted high", abs(d["skew"] - 2.2) < 0.03 and d["skew_t"])
check("skew surge on an ordinary day: about 1 ft", abs(r["days"]["2026-10-10"]["skew"] - 1.0) < 0.03)
# a tide that comes 30 minutes late: the 6-minute residual jumps, the skew surge doesn't
base = dt.datetime(2026, 1, 1)
tbl = [((base + dt.timedelta(minutes=6 * i)).strftime("%Y-%m-%d %H:%M"), 3.5 + 3 * math.cos(2 * math.pi * (i * 6 / 60) / 12.42), "") for i in range(240)]
late = [((base + dt.timedelta(minutes=6 * i)).strftime("%Y-%m-%d %H:%M"), 3.5 + 3 * math.cos(2 * math.pi * ((i * 6 - 30) / 60) / 12.42), "") for i in range(240)]
rr = T.day_stats(late, tbl, [])
check("late tide: skew surge about 0, residual about 0.4 ft", abs(rr["skew"]) < 0.02 and rr["res_max"] > 0.3)
check("surge day: about 2.2 ft above the table at most, averaging about 2.2", abs(d["res_max"] - 2.2) < 0.02 and abs(d["res_mean"] - 2.2) < 0.02)
check("surge day reaches the flood level for some minutes", d["min"]["flood"] > 0 and d["max"] >= 8.5)
check("ordinary day: 1 ft above the table", abs(r["days"]["2026-10-10"]["res_mean"] - 1.0) < 0.02)
m = r["months"]["2026-10"]
check("October summary: highest on the surge day", m["max_date"].startswith("2026-10-20") and m["count"]["flood"] >= 1 and m["days"] == 29)
check("hours counted", m["hours"]["mhhw"] > 0 and m["hours"]["mhhw"] >= m["hours"]["flood"])
mo = s["9413450"]["months"]["2026-10"]
check("Monterey runs lower", mo["max"] < m["max"])

# history comes in a few years per run, newest first
h1 = {st: len(v) for st, v in hist.items()}
check("history: some years fetched within the time budget, not all", 0 < h1["9414523"] < 2026 - 1974 + 1)
check("newest years first", "2026" in hist["9414523"] and hist["9414523"]["2026"]["to"] == "2026-09-30")
for _ in range(80):
    out = T.run(out, hist, NOW, fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
check("history complete after enough runs", len(hist["9414290"]) == 2026 - 1898 + 1)
hs = hist["9414290"]
exp = lambda y, md: round(6.0 + 1.5 * math.cos(2 * math.pi * (dt.date(y, int(md[:2]), int(md[2:])).timetuple().tm_yday - 15) / 365) + 0.01 * (y - 1990), 2)   # noqa: E731
check("before NAVD88 high/lows: high/lows on MLLW, shifted to NAVD88", hs["1960"].get("src") == "hl_mllw" and abs(hs["1960"]["d"]["0115"] - exp(1960, "0115")) < 0.011)
check("older still: hourly heights on MLLW, shifted, daily highest", hs["1920"].get("src") == "hourly_mllw" and abs(hs["1920"]["d"]["0115"] - exp(1920, "0115")) < 0.011
      and len(hs["1920"]["d"]) == 366)
check("NAVD88 high/lows carry no source mark", "src" not in hs["2000"] and hs["2000"]["d"])
hist["9414290"]["1930"] = {"to": "1930-12-31", "d": {}}   # an empty year from before the other sources were tried: asked again
T.update_history(hist, "9414290", 1898, dt.date(2026, 10, 1), fetch, 30, lambda *a: None, clock)
check("old empty years are asked again with the other sources", hist["9414290"]["1930"].get("src") == "hourly_mllw")
check("a year NOAA can't give in NAVD88 is noted and skipped", hist["9414290"]["1995"]["d"] == {} and "datum" in hist["9414290"]["1995"]["err"])
r = {x["id"]: x for x in out["stations"]}["9414523"]
hs = r["history"]
check("history: years with data from 1974 (made-up record; before 1990 from MLLW high/lows)", hs["first_year"] == 1974 and hs["last_year"] == 2026)
check("usual October days at MHHW are a count per month", 0 <= hs["usual"]["10"]["days"]["mhhw"] <= 31 and hs["usual"]["10"]["years"] == 19)
check("usual range by date: 366 entries with low <= median <= high", len(hs["band"]) == 366 and all(b is None or b[0] <= b[1] <= b[2] for b in hs["band"]))
check("base = the last 19 complete water years", hs["base"] == [2008, 2026])
pc = hs["pace"]
check("pace: day of the water year and one entry per past year with data", pc["day"] == 28 and len(pc["years"]) == 2026 - 1975 + 1 and pc["years"][-1]["wy"] == 2026)
yr = pc["years"][-1]
check("pace: by-this-date counts never exceed the year's", all(yr["by"][k] <= yr["all"][k] for k in yr["by"]) and yr["max_by"] <= yr["max"])
rk = r["ranks"]["2026-10"]
check("October 2026 ranks first (the made-up history tops out lower)", rk["rank"] == 1 and rk["of"] == 2026 - 1974 + 1)
check("season so far ranked against past water years over the same dates", r["ranks"]["season"]["rank"] == 1 and r["ranks"]["season"]["of"] > 20)

# projections and NWS
check("projections stored for tomorrow and the day after", set(r["proj"]) >= {"2026-10-30", "2026-10-31"} and r["proj"]["2026-10-30"]["lead_days"] == 1)
check("NWS: only San Mateo County coastal flood products, once", len(out["nws"]) == 1 and out["nws"][0]["event"] == "Coastal Flood Advisory")

# a new day: earlier days are kept, not fetched again
calls.clear()
NOW2 = NOW + dt.timedelta(days=1)
MEAS_TO[0] = dt.datetime(2026, 10, 30, 17, 0)
out2 = T.run(out, hist, NOW2, fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
wl = [u for u in calls if "product=water_level" in u and "9414523" in u]
check("next day: only the last few days fetched (2 complete days + today)", len(wl) == 1 and "begin_date=20261028" in urllib.parse.unquote(wl[0]))
check("next day: all days still there", len({x["id"]: x for x in out2["stations"]}["9414523"]["days"]) == 30)

# a new water year starts fresh
NOW3 = dt.datetime(2027, 10, 1, 19, 0, tzinfo=dt.timezone.utc)
out3 = T.run(out2, hist, NOW3, fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
check("new water year: WY2028, last year's days dropped", out3["water_year"] == "WY2028" and all(k >= "2027-10-01" for k in out3["stations"][0]["days"]))

# NOAA refusing (403) after a while: the season numbers come first and survive; the history stops for the run
import urllib.error
n_ok = [0]


def busy(url):
    if "high_low" in url:
        n_ok[0] += 1
        if n_ok[0] > 3:
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
    return fetch(url)


h4 = {}
calls.clear()
out4 = T.run({}, h4, NOW, fetch=busy, log=lambda *a: None, budget_s=100, clock=clock, extra=extra)
check("403 on history: all four gauges still have this season", len(out4["stations"]) == 4 and all(len(x["days"]) == 29 for x in out4["stations"]) and out4["problems"] == [])
check("403 on history: no more history asked for this run", n_ok[0] == 4 and sum(len(v) for v in h4.values()) == 3)
check("history: no more than the per-run limit", len([u for u in calls if "high_low" in u]) <= T.HIST_MAX_REQUESTS)

# El Nino: CPC's ONI table, once a day; each water year's winter (DJF) value
ONI_TEXT = """ SEAS  YR   TOTAL   ANOM
  DJF 2015  27.66   0.55
  NDJ 2015  29.0    2.64
  DJF 2016  29.05   2.48
  JFM 2016  28.0    2.14
  DJF 2026  26.0   -0.61
  SON 2026  27.5    1.21
"""
got = []
e = T.enso_update(None, dt.date(2026, 10, 30), get_text=lambda u: got.append(u) or ONI_TEXT, log=lambda *a: None)
check("ONI: winters by water year (DJF)", e["winters"] == {"2015": 0.55, "2016": 2.48, "2026": -0.61} and e["latest"] == ["SON", 2026, 1.21])
e2 = T.enso_update(e, dt.date(2026, 10, 30), get_text=lambda u: got.append(u) or ONI_TEXT, log=lambda *a: None)
check("ONI: fetched once a day", len(got) == 1 and e2 is e)
def boom(u):
    raise OSError("down")
e3 = T.enso_update(e, dt.date(2026, 10, 31), get_text=boom, log=lambda *a: None)
check("ONI: CPC down keeps the last values", e3 is e)

# return periods from the study's levels
st = out["study"]
check("study: nearest point to Redwood City, values by return period", st["9414523"]["point"] == 761 and st["9414523"]["values"]["100"] == 10.3 and st["9414523"]["dist_m"] < 200)
check("study: fetched once, then kept for a month", st.get("_fetched") == "2026-10-29")
V = st["9414523"]["values"]
check("return period: below the 1-year level", T.return_period(8.0, V) == 0.0)
check("return period: on a level", T.return_period(9.0, V) == 5.0)
check("return period: between levels, on log scale", 2.0 < T.return_period(8.8, V) < 5.0)
check("return period: beyond the 500-year", T.return_period(11.5, V) > 500)
check("study fields found by alias", T.study_fields([{"name": "a", "alias": "100-yr", "type": "esriFieldTypeDouble"}, {"name": "Yr_5", "type": "esriFieldTypeDouble"}]) == {100: "a", 5: "Yr_5"})
check("staff file wins", T.study_update({}, dt.date(2026, 10, 29), fetch=lambda u: (_ for _ in ()).throw(OSError("x")), log=lambda *a: None,
                                        csv_levels={"9414523": {"values": {"1": 8.2}}})["9414523"]["values"] == {"1": 8.2})
# October closes out once November begins, and stays as recorded
NOW5 = dt.datetime(2026, 11, 2, 19, 0, tzinfo=dt.timezone.utc)
MEAS_TO[0] = dt.datetime(2026, 11, 2, 11, 0)
out5 = T.run(out2, hist, NOW5, fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
co = out5["closeout"]["9414523"]
check("October closed out with its peak and return period", list(co) == ["2026-10"] and co["2026-10"]["max"] == out5["stations"][0]["months"]["2026-10"]["max"] and co["2026-10"]["study"])
co["2026-10"]["max"] = 99
out6 = T.run(out5, hist, NOW5 + dt.timedelta(hours=2), fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
check("a closed month is kept as recorded", out6["closeout"]["9414523"]["2026-10"]["max"] == 99)

# the real levels file
lv = T.load_extra_levels()
check("levels file loads", [x["ft"] for x in lv.get("9414523", [])] == [8.3, 8.5] and lv.get("9413450"))

# the BCDC layer as it really is: SWEL_N fields (still water elevation), in any order, MHHW alongside
swel = [{"name": n, "type": "esriFieldTypeDouble"} for n in "FID OBJECTID_1 Easting Northing MLLW MHHW SWEL_2 SWEL_5 SWEL_1 SWEL_10 SWEL_25 SWEL_100 SWEL_500 SWEL_50 ID".split()]
check("study fields: SWEL_N read as return periods", T.study_fields(swel) == {1: "SWEL_1", 2: "SWEL_2", 5: "SWEL_5", 10: "SWEL_10", 25: "SWEL_25", 50: "SWEL_50", 100: "SWEL_100", 500: "SWEL_500"})
def swel_fetch(metres):
    k = 1 / 3.28084 if metres else 1.0
    def f(url):
        if url.endswith("FeatureServer?f=json"):
            return {"layers": [{"id": 0}]}
        if url.endswith("/0?f=json"):
            return {"fields": swel}
        vals = {1: 8.3, 2: 8.6, 5: 9.0, 10: 9.3, 25: 9.7, 50: 10.0, 100: 10.3, 500: 11.0}
        a = dict({"ID": 761, "MHHW": 7.1 * k, "MLLW": -1.2 * k}, **{"SWEL_%d" % t: str(round(v * k, 3)) if t == 5 else v * k for t, v in vals.items()})
        return {"features": [{"geometry": {"x": -122.2120, "y": 37.5080}, "attributes": a}]}
    return f
for metres in (False, True):
    su = T.study_update(None, dt.date(2026, 10, 31), swel_fetch(metres), lambda *a: None, {})
    v = su.get("9414523", {}).get("values", {})
    check("study read from SWEL fields" + (" in metres, turned into feet" if metres else " in feet") + " (a number kept as text too)",
          "_error" not in su and abs(v.get("1", 0) - 8.3) < 0.02 and abs(v.get("5", 0) - 9.0) < 0.02 and abs(v.get("100", 0) - 10.3) < 0.02)

print("tide_tracker: %d checks, %d failed" % (checks, fails))
sys.exit(1 if fails else 0)
