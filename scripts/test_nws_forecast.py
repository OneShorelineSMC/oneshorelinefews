"""Checks for scripts/nws_forecast.py and the "raining" flag (no network: NWS responses are made up here).
Run: python scripts/test_nws_forecast.py"""

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nws_forecast as N
from creek_signals import rain_signals

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 18, 20, 0, tzinfo=UTC)
fails = 0


def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


def grid(values, uom="wmoUnit:mm"):
    return {"properties": {"updateTime": "2026-10-18T19:40:12+00:00",
                           "quantitativePrecipitation": {"uom": uom, "values": values}}}


# 6-hour periods starting at 18Z: 2.54 mm (0.1 in), 12.7 mm (0.5 in), 25.4 mm (1 in), then zeros
G = grid([{"validTime": "2026-10-18T18:00:00+00:00/PT6H", "value": 2.54},
          {"validTime": "2026-10-19T00:00:00+00:00/PT6H", "value": 12.7},
          {"validTime": "2026-10-19T06:00:00+00:00/PT6H", "value": 25.4},
          {"validTime": "2026-10-19T12:00:00+00:00/P1DT12H", "value": 0},
          {"validTime": "2026-10-21T00:00:00+00:00/PT6H", "value": None}])

t0, t1 = N.parse_valid_time("2026-10-19T12:00:00+00:00/P1DT12H")
check("duration with days", t1 - t0 == dt.timedelta(hours=36))
pers = N.periods(G)
check("null values skipped, mm to inches", len(pers) == 4 and abs(pers[0][2] - 0.1) < 1e-9)
s = N.summarize(pers, NOW, N.issued_time(G))
# now = 20Z: 4 of the first 6 hours are left -> 0.0667 in; next 6 h = that + 2 h of the 0.5 in period (0.1667)
check("next 6 h prorates partial periods", s["next6"] == round(0.1 * 4 / 6 + 0.5 * 2 / 6, 2))
check("next 24 h", s["next24"] == round(0.1 * 4 / 6 + 0.5 + 1.0, 2))
check("next 3 days", s["next72"] == round(0.1 * 4 / 6 + 1.5, 2))
check("heaviest period", s["peak_start"] == "2026-10-19T06:00Z" and s["peak_in"] == 1.0 and s["peak_hours"] == 6)
check("issued time", s["issued"] == "2026-10-18T19:40Z")
dry = N.summarize(N.periods(grid([{"validTime": "2026-10-18T18:00:00+00:00/PT6H", "value": 0}])), NOW)
check("dry forecast has no peak", dry["next24"] == 0 and dry["peak_start"] is None)
check("inches unit kept", N.periods(grid([{"validTime": "2026-10-18T18:00:00+00:00/PT6H", "value": 0.3}], "wmoUnit:in"))[0][2] == 0.3)

# add_forecast with a fake NWS
calls = []


def fake(url):
    calls.append(url)
    if "/points/" in url:
        return {"properties": {"forecastGridData": N.API + "/gridpoints/MTR/90,100"}}
    return G


PTS = {"belmont": {"lat": 37.51, "lon": -122.29, "place": "Belmont Creek watershed"},
       "colma": {"lat": 37.66, "lon": -122.44, "place": "Colma Creek watershed"}}
result = {"creeks": [{"id": "belmont"}, {"id": "colma"}, {"id": "nopoint"}], "creeks_preview": []}
probs = N.add_forecast(result, {}, NOW, {"FORECAST_EVERY_MIN": 60, "FORECAST_KEEP_HOURS": 12}, fetch=fake, points=PTS)
fb = result["creeks"][0]["forecast"]
check("forecast added", fb["next24"] == s["next24"] and fb["error"] is None and fb["place"] == "Belmont Creek watershed")
check("one grid request for a shared grid cell", sum("/gridpoints/" in u for u in calls) == 1)
check("creek without a point gets none", "forecast" not in result["creeks"][2] and not probs)

# within FORECAST_EVERY_MIN: no new requests, totals re-added from the stored periods
calls.clear()
later = NOW + dt.timedelta(minutes=30)
r2 = {"creeks": [{"id": "belmont"}], "creeks_preview": []}
N.add_forecast(r2, result, later, {"FORECAST_EVERY_MIN": 60, "FORECAST_KEEP_HOURS": 12}, fetch=fake, points=PTS)
check("reused within the hour, no requests", not calls and r2["creeks"][0]["forecast"]["fetched"] == fb["fetched"])
check("totals move with the clock", r2["creeks"][0]["forecast"]["next6"] != fb["next6"])

# NWS down: keep the last forecast (marked) for FORECAST_KEEP_HOURS, then drop it


def down(url):
    raise OSError("timed out")


r3 = {"creeks": [{"id": "belmont"}], "creeks_preview": []}
p3 = N.add_forecast(r3, result, NOW + dt.timedelta(hours=2), {"FORECAST_EVERY_MIN": 60, "FORECAST_KEEP_HOURS": 12}, fetch=down, points=PTS)
f3 = r3["creeks"][0]["forecast"]
check("NWS down: last forecast kept, marked", f3.get("error") and f3.get("next24") is not None and p3)
r4 = {"creeks": [{"id": "belmont"}], "creeks_preview": []}
N.add_forecast(r4, result, NOW + dt.timedelta(hours=13), {"FORECAST_EVERY_MIN": 60, "FORECAST_KEEP_HOURS": 12}, fetch=down, points=PTS)
check("NWS down too long: no totals", r4["creeks"][0]["forecast"].get("next24") is None)
bad = {"creeks": [{"id": "belmont"}], "creeks_preview": []}
N.add_forecast(bad, {}, NOW, {}, fetch=lambda u: {"properties": {"forecastGridData": "https://evil.example/x"}}, points=PTS)
check("only api.weather.gov grid URLs are followed", bad["creeks"][0]["forecast"].get("error"))
pts, pr = N.load_points()
import csv as _csv
_ids = {r["creek"] for r in _csv.DictReader(open(os.path.join(os.path.dirname(N.POINTS_CSV), "creeks.csv"), encoding="utf-8-sig"))}
check("lookups/forecast_points.csv has a point for every creek in creeks.csv", set(pts) == _ids and not pr)

# "raining": any rain in the last hour at a fresh gauge
NAIVE = dt.datetime(2026, 10, 18, 13, 0)
at = lambda m: (NAIVE - dt.timedelta(minutes=m)).strftime("%Y-%m-%d %H:%M")
r = rain_signals([[at(30), 0.02]], None, None, NAIVE, 12)
check("raining after 0.02 in in the last hour", r["raining"] is True)
r = rain_signals([[at(90), 0.02], [at(20), 0.0]], None, None, NAIVE, 12)
check("not raining when the last hour is dry", r["raining"] is False)

print("\n" + ("All passed" if not fails else f"{fails} FAILED"))
sys.exit(1 if fails else 0)
