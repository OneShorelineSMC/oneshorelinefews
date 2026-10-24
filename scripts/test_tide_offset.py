"""Checks for scripts/tide_offset.py (no network: NOAA replies are made up here).
Run: python scripts/test_tide_offset.py"""

import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tide_offset as T

fails = 0


def check(name, ok):
    global fails
    print(("ok   " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


def steps(first, last):
    t = dt.datetime.combine(first, dt.time(0, 0))
    while t.date() <= last:
        yield t
        t += dt.timedelta(minutes=6)


def fake(offset_by_day, missing_days=(), storm=None, gap=None):
    """A NOAA stand-in: tide table = a 12.42-hour cosine; measured = table + that day's offset (+ a storm spike)."""
    calls = []

    def fetch(url):
        calls.append(url)
        q = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
        b = dt.datetime.strptime(q["begin_date"].replace("+", " ").replace("%3A", ":"), "%Y%m%d %H:%M").date()
        e = dt.datetime.strptime(q["end_date"].replace("+", " ").replace("%3A", ":"), "%Y%m%d %H:%M").date()
        rows = []
        for t in steps(b, e):
            v = 3 + 3 * math.cos(2 * math.pi * (t - dt.datetime(2026, 1, 1)).total_seconds() / 3600 / 12.42)
            if q["product"] == "water_level":
                d = t.date().isoformat()
                if d in missing_days or (gap and gap[0] <= t < gap[1]):
                    continue
                v += offset_by_day.get(d, 0) + (storm[1] if storm and d == storm[0] and 10 <= t.hour < 16 else 0)
            rows.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": f"{v:.3f}"})
        return {"predictions": rows} if q["product"] == "predictions" else {"data": rows}
    fetch.calls = calls
    return fetch


NOW = dt.datetime(2026, 10, 21, 16, 30, tzinfo=dt.timezone.utc)   # 9:30 AM Pacific, Oct 21
ST = {"9414523": {"name": "Redwood City"}}
last = dt.date(2026, 10, 20)
days = [(last - dt.timedelta(days=k)).isoformat() for k in range(30)]

f0 = fake({d: 0.4 for d in days})
r, p = T.update({}, NOW, ST, 30, f0)
s = r["stations"]["9414523"]
check("window is the last 30 whole days, Pacific", s["from"] == "2026-09-21" and s["to"] == "2026-10-20" and s["days"] == 30)
check("steady +0.4 ft gives +0.40", s["offset_ft"] == 0.4 and s["days_used"] == 30 and not p)
check("NOAA asked for MLLW, Pacific clock, 6-minute tide table", len(f0.calls) == 2 and all("datum=MLLW" in u and "time_zone=lst_ldt" in u for u in f0.calls) and "interval=6" in f0.calls[1])

ramp = {d: 0.1 + 0.01 * i for i, d in enumerate(sorted(days))}
s = T.update({}, NOW, ST, 30, fake(ramp))[0]["stations"]["9414523"]
check("offset = average of the daily averages", abs(s["offset_ft"] - round(sum(ramp.values()) / 30, 2)) < 0.006)
check("last-7-days average reported", abs(s["recent7_ft"] - round(sum(sorted(ramp.values())[-7:]) / 7, 2)) < 0.006)

storm = T.update({}, NOW, ST, 30, fake({d: 0.2 for d in days}, storm=("2026-10-15", 2.0)))[0]["stations"]["9414523"]
check("a one-day 2 ft storm surge (6 h) moves the offset only a little", 0.2 < storm["offset_ft"] <= 0.22)

thin = T.update({}, NOW, ST, 30, fake({d: 0.3 for d in days}, missing_days=set(days[:12])))[0]["stations"]["9414523"]
check("too few days: no offset, with a note", thin["offset_ft"] is None and thin["days_used"] == 18 and "only 18" in thin.get("note", ""))

partial = T.update({}, NOW, ST, 30, fake({d: 0.3 for d in days}, gap=(dt.datetime(2026, 10, 18, 0, 0), dt.datetime(2026, 10, 18, 6, 0))))[0]["stations"]["9414523"]
check("a day missing 6 hours (75%) is left out; the rest still count", partial["days_used"] == 29 and partial["offset_ft"] == 0.3)

# caching: same day -> no new downloads; next day -> recomputed
f = fake({d: 0.4 for d in days}); r1 = T.update({}, NOW, ST, 30, f)[0]; n1 = len(f.calls)
r2 = T.update(r1, NOW + dt.timedelta(hours=5), ST, 30, f)[0]
check("same day: kept, no downloads", len(f.calls) == n1 and r2["stations"]["9414523"]["computed_utc"] == r1["stations"]["9414523"]["computed_utc"])
T.update(r1, NOW + dt.timedelta(days=1), ST, 30, f)
check("next day: recomputed", len(f.calls) == n1 + 2)
T.update(r1, NOW + dt.timedelta(hours=1), ST, 14, f)
check("window setting changed: recomputed", len(f.calls) == n1 + 4)


def down(url):
    raise OSError("timed out")


r3, p3 = T.update(r1, NOW + dt.timedelta(days=1), ST, 30, down)
s3 = r3["stations"]["9414523"]
check("NOAA down: last offset kept, with its old time and the error", s3["offset_ft"] == 0.4 and s3["computed_utc"] == r1["stations"]["9414523"]["computed_utc"] and s3["error"] and p3)
calls = []
T.update(r3, NOW + dt.timedelta(days=1, minutes=20), ST, 30, lambda u: calls.append(u) or down(u))
check("after a failure, waits before trying again", not calls)
T.update(r3, NOW + dt.timedelta(days=1, minutes=70), ST, 30, lambda u: calls.append(u) or down(u))
check("...then tries again", len(calls) == 1)
err = T.update({}, NOW, ST, 30, lambda u: {"error": {"message": "No data was found."}})[0]["stations"]["9414523"]
check("NOAA error reply: no offset, error kept", err.get("offset_ft") is None and "No data" in (err.get("error") or ""))

# ---- the calendar outlook: usual height above the tide table by month, damped persistence, El Nino (made-up NOAA/CPC)
import random
rnd = random.Random(4)
SEAS = {1: 0.10, 2: 0.08, 3: 0.02, 4: -0.05, 5: -0.08, 6: -0.09, 7: -0.08, 8: -0.05, 9: -0.02, 10: 0.02, 11: 0.06, 12: 0.09}
ONI, dep, prev = {}, {}, 0.0
for y in range(2004, 2026):
    for m in range(1, 13):
        ONI[(y, m)] = 1.5 * math.sin((y * 12 + m) / 9.0)
        prev = 0.6 * prev + rnd.gauss(0, 0.05)
        dep[(y, m)] = prev + (0.15 * ONI[(y, m)] if m in (11, 12, 1, 2, 3) else 0)


def ol_fetch(url):
    q = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
    b, e = int(q["begin_date"][:4]), int(q["end_date"][:4])
    if q["product"] == "monthly_mean":
        return {"data": [{"year": str(y), "month": str(m), "MSL": str(3.0 + 0.2 + 0.01 * (y + (m - 0.5) / 12 - 2015.5) + SEAS[m] + dep[(y, m)])}
                         for y in range(b, e + 1) for m in range(1, 13)]}
    t, rows = dt.datetime(b, 1, 1), []
    while t.year == b:
        rows.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": "3.0"}); t += dt.timedelta(hours=1)
    return {"predictions": rows}


oni_txt = "SEAS  YR   TOTAL   ANOM\n" + "\n".join(f"{T.ONI_SEASONS[m - 1]} {y} 27.0 {ONI[(y, m)]:.2f}" for y in range(2004, 2026) for m in range(1, 13)) + "\nASO 2026 27.9 1.40\n"
ol = T.outlook(dt.datetime(2026, 10, 23, 12), fetch=ol_fetch, fetch_text=lambda u: oni_txt)
check("outlook: 20 years of San Francisco monthly means, NOAA's monthly_mean and hourly tide table", ol["years"] == [2006, 2025] and ol["months_used"] == 240)
check("outlook: trend about 0.01 ft a year", abs(ol["trend_ft_per_year"] - 0.01) < 0.004)
check("outlook: usual height above the tide table for this month and the next 8 (trend + season)",
      list(ol["normal_ft"])[0] == "2026-10" and len(ol["normal_ft"]) == 9 and abs(ol["normal_ft"]["2026-12"] - (0.2 + 0.01 * 11 + 0.09)) < 0.06)
check("outlook: month-to-month persistence (lag-1 correlation; 0.6 made up, plus the slow El Nino part)", 0.5 <= ol["r1"] <= 0.9 and ol["r2"] < ol["r1"])
check("outlook: El Nino about 0.15 ft per degree in winter, significant, with the latest ONI",
      ol["enso"] and abs(ol["enso"]["slope_ft_per_c"] - 0.15) < 0.04 and ol["enso"]["significant"] and ol["enso"]["oni"] == 1.4 and ol["enso"]["oni_season"] == "ASO 2026")
nocpc = T.outlook(dt.datetime(2026, 10, 23, 12), fetch=ol_fetch, fetch_text=lambda u: (_ for _ in ()).throw(OSError("down")))
check("outlook: CPC down: the monthly heights still, El Nino left out", nocpc["enso"] is None and "down" in nocpc["enso_error"] and nocpc["normal_ft"])
calls = []
fn = lambda local: (calls.append(local), {"normal_ft": {"2026-10": 0.3}})[1]
now0 = dt.datetime(2026, 10, 23, 15, tzinfo=dt.timezone.utc)
r1o, _ = T.update({}, now0, {"9414523": {"name": "Redwood City"}}, 30, fake({}), outlook_fn=fn)
r2o, _ = T.update(r1o, now0 + dt.timedelta(days=3), {"9414523": {"name": "Redwood City"}}, 30, fake({}), outlook_fn=fn)
r3o, _ = T.update(r2o, now0 + dt.timedelta(days=8), {"9414523": {"name": "Redwood City"}}, 30, fake({}), outlook_fn=fn)
check("outlook: computed once a week, kept in between", len(calls) == 2 and r2o["outlook"]["computed_utc"] == r1o["outlook"]["computed_utc"])
bad = lambda local: (_ for _ in ()).throw(ValueError("NOAA down"))
r4o, p4 = T.update(r3o, now0 + dt.timedelta(days=16), {"9414523": {"name": "Redwood City"}}, 30, fake({}), outlook_fn=bad)
check("outlook: NOAA down: last outlook kept with the error", r4o["outlook"]["normal_ft"] == {"2026-10": 0.3} and "NOAA down" in r4o["outlook"]["error"] and any("outlook" in x for x in p4))

print("\n" + ("All passed" if not fails else f"{fails} FAILED"))
sys.exit(1 if fails else 0)
