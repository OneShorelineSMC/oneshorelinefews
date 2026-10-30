"""Checks for scripts/tide_tracker.py with made-up NOAA replies (no network). Run: python scripts/test_tide_tracker.py"""

import datetime as dt
import math
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tide_tracker as T

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
    if prod == "high_low":
        if a.year < 1990:
            return {"error": {"message": "No data was found. This product may not be offered at this station at the requested time."}}
        if st == "9414290" and a.year == 1995:
            return {"error": {"message": "The requested datum NAVD is not available for this period"}}
        out, t = [], a
        while t <= b:   # one high a day at noon: higher in winter, a bit higher each year
            v = 6.0 + 1.5 * math.cos(2 * math.pi * (t.timetuple().tm_yday - 15) / 365) + 0.01 * (t.year - 1990)
            out.append({"t": t.strftime("%Y-%m-%d 12:00"), "v": "%.3f" % v, "ty": "HH"})
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
d = r["days"]["2026-10-20"]
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
for _ in range(40):
    out = T.run(out, hist, NOW, fetch=fetch, log=lambda *a: None, budget_s=8, clock=clock, extra=extra)
check("history complete after enough runs", len(hist["9414290"]) == 2026 - 1898 + 1)
check("a year NOAA can't give in NAVD88 is noted and skipped", hist["9414290"]["1995"]["d"] == {} and "datum" in hist["9414290"]["1995"]["err"])
r = {x["id"]: x for x in out["stations"]}["9414523"]
hs = r["history"]
check("history: years with data from 1990 (made-up record)", hs["first_year"] == 1990 and hs["last_year"] == 2026)
check("usual October days at MHHW are a count per month", 0 <= hs["usual"]["10"]["days"]["mhhw"] <= 31 and hs["usual"]["10"]["years"] == 19)
check("usual range by date: 366 entries with low <= median <= high", len(hs["band"]) == 366 and all(b is None or b[0] <= b[1] <= b[2] for b in hs["band"]))
check("base = the last 19 complete water years", hs["base"] == [2008, 2026])
rk = r["ranks"]["2026-10"]
check("October 2026 ranks first (the made-up history tops out lower)", rk["rank"] == 1 and rk["of"] == 2026 - 1990 + 1)
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

# the real levels file
lv = T.load_extra_levels()
check("levels file loads", [x["ft"] for x in lv.get("9414523", [])] == [8.3, 8.5] and lv.get("9413450"))

print("tide_tracker: %d checks, %d failed" % (checks, fails))
sys.exit(1 if fails else 0)
