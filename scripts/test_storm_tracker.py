"""Checks for scripts/storm_tracker.py: a made-up storm at one creek, run hour by hour as the data job would."""
import copy
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storm_tracker as T   # noqa: E402

checks = fails = 0


def check(name, ok):
    global checks, fails
    checks += 1
    if not ok:
        fails += 1
    print(("ok   " if ok else "FAIL ") + name)


S = {"STORM_DRY_HOURS": 6, "STORM_MIN_IN": 0.1, "STORM_WET_IN": 0.01, "STORM_RESPONSE_HOURS": 12}
# Atlas 14 at the gauge: Heavy / Very heavy / Intense for each window (inches)
FREQ = {"41101": {"levels": {15: [0.24, 0.28, 0.35], 30: [0.32, 0.39, 0.47], 60: [0.46, 0.55, 0.67], 180: [0.83, 0.98, 1.2],
                             360: [1.1, 1.3, 1.6], 720: [1.5, 1.8, 2.2], 1440: [2.0, 2.4, 3.0]},
                  "minutes": {m: {1.0: v[0], 2.0: v[1], 5.0: v[2], 10.0: v[2] * 1.2} for m, v in
                              {15: [0.24, 0.28, 0.35], 30: [0.32, 0.39, 0.47], 60: [0.46, 0.55, 0.67], 180: [0.83, 0.98, 1.2],
                               360: [1.1, 1.3, 1.6], 720: [1.5, 1.8, 2.2], 1440: [2.0, 2.4, 3.0]}.items()}}}
T0 = dt.datetime(2026, 11, 3, 0, 0)
# rain each hour (hour index from T0 -> inches, reported in 4 tips of a quarter each, at :15 :30 :45 :00)
RAIN = {10: 0.05, 11: 0.10, 12: 0.20, 13: 0.40, 14: 0.60, 15: 0.30, 16: 0.10, 17: 0.05,   # storm 1: 1.80 in
        30: 0.02, 31: 0.03,                                                                 # too little: not a storm
        60: 0.10, 61: 0.20, 65: 0.10}                                                       # storm 2 (gap of 4 h: one storm)
SUPPORT = {12: 0.30, 13: 0.50, 14: 0.40}


def level_at(i):   # creek level (ft): rises after the rain, peaks at hour 18, back down by hour 30
    return round(1.0 + max(0, 4.5 - abs(i - 18) * 0.6) if 8 <= i <= 30 else 1.0, 2)


def tips(rain, upto):
    out = []
    for i, v in sorted(rain.items()):
        for q in (15, 30, 45, 60):
            t = T0 + dt.timedelta(hours=i, minutes=q)
            if t <= upto:
                out.append([t.strftime("%Y-%m-%d %H:%M"), round(v / 4, 4), ""])
    return out


def snapshot(now):
    lo = now - dt.timedelta(hours=50)
    pts = [p for p in tips(RAIN, now) if T.parse_t(p[0]) >= lo]
    sup = [p for p in tips(SUPPORT, now) if T.parse_t(p[0]) >= lo]
    if not pts or T.parse_t(pts[0][0]) > lo + dt.timedelta(minutes=30):   # a dry report at the window start
        pts.insert(0, [lo.strftime("%Y-%m-%d %H:%M"), 0.0, ""])
    stage = []
    t = lo
    while t <= now:
        i = (t - T0).total_seconds() / 3600
        stage.append([t.strftime("%Y-%m-%d %H:%M"), level_at(round(i)), ""])
        t += dt.timedelta(minutes=15)
    i = (now - T0).total_seconds() / 3600
    last15 = sum(p[1] for p in pts if T.parse_t(p[0]) > now - dt.timedelta(minutes=15))
    last30 = sum(p[1] for p in pts if T.parse_t(p[0]) > now - dt.timedelta(minutes=30))
    status = "likely" if level_at(round(i)) >= 5.0 else "ready" if level_at(round(i)) >= 3.4 else "none"
    c = {"id": "colma", "name": "Colma Creek", "short": "Colma", "status": {"key": status},
         "rain": [{"key": "col_rain", "label": "Orange Memorial Park", "number": "41101"}],
         "rain_support": [{"key": "col_rain_41200", "label": "San Bruno Mountain", "number": "41200"}],
         "stages": [{"key": "col_stage", "label": "Orange Memorial Park", "number": "41101", "tidal": True,
                     "thresholds": [{"value": 3.4, "name": "Flood Monitoring", "level": 1}, {"value": 5.0, "name": "Flood Watch", "level": 2},
                                    {"value": 6.75, "name": "Flood Warning", "level": 3}]}]}
    sens = {"col_rain": {"kind": "rain_increment", "points": pts, "latest": pts[-1],
                         "signals": {"fresh": True, "totals": {"15": round(last15, 2), "30": round(last30, 2)}}},
            "col_rain_41200": {"kind": "rain_increment", "points": sup or [[lo.strftime("%Y-%m-%d %H:%M"), 0.0, ""]], "latest": None,
                               "signals": {"fresh": not (12 <= i <= 14)}},   # goes quiet in the middle of the storm
            "col_stage": {"kind": "stage", "points": stage, "latest": stage[-1],
                          "signals": {"trend": "fast" if 14 <= i <= 17 else "steady", "rising_fast": {"rise": 0.6} if 14 <= i <= 16 else None}}}
    return {"generated": now.strftime("%Y-%m-%d %H:%M:%S"), "creeks": [c], "sensors": sens}


state, seen_open = {}, []
for hr in range(0, 100):
    for mm in (0, 30):
        now = T0 + dt.timedelta(hours=hr, minutes=mm)
        state = T.run(snapshot(now), copy.deepcopy(state), now, S, FREQ)
        if state["open"]:
            seen_open.append((hr, state["open"][0]["total"]))
        if hr == 40 and mm == 0:
            at40 = copy.deepcopy(state)

check("storm shows as open while it rains, total growing", any(t for h, t in seen_open if h == 12) and
      max(t for h, t in seen_open if h <= 17) > min(t for h, t in seen_open if h <= 17))
s1 = [s for s in at40["storms"]]
check("closed after the rain plus 6 dry hours plus 12 hours for the creek", len(s1) == 1 and not at40["open"])
st = state["storms"][0]
check("two storms in all (light rain at hours 30-31 left out; hours 60-65 one storm)", len(state["storms"]) == 2)
check("storm 1: 10:00 to 17:00, 8 hours", st["start"] == "2026-11-03 10:00" and st["end"] == "2026-11-03 17:00" and st["hours"] == 8)
r = [x for x in st["rain"] if x["key"] == "col_rain"][0]
check("storm 1 total 1.80 in", abs(r["total"] - 1.80) < 0.005 and abs(st["total"] - 1.80) < 0.005)
check("peak hour 0.60 in, 3 hr 1.30 in, 6 hr 1.70 in, 24 hr = the whole storm",
      r["peaks"]["60"]["in"] == 0.6 and r["peaks"]["180"]["in"] == 1.3 and r["peaks"]["360"]["in"] == 1.7 and r["peaks"]["1440"]["in"] == 1.8)
check("15- and 30-minute peaks sampled while open (0.15 / 0.30 in)", r["peaks"]["15"]["in"] == 0.15 and r["peaks"]["30"]["in"] == 0.3)
check("rated against Atlas 14: 1 hr Very heavy, 6 hr Intense; rarest = Intense",
      r["peaks"]["60"]["rate"]["level"] == 2 and r["peaks"]["360"]["rate"]["level"] == 3 and r["rarest"]["level"] == 3 and st["rain_level"] == 3)
check("rough storm size given in years", r["rarest"]["years"] and r["rarest"]["years"] >= 5)
sup = [x for x in st["rain"] if x["key"] == "col_rain_41200"][0]
check("supporting gauge: its own total, no Atlas 14 values (none)", abs(sup["total"] - 1.2) < 0.005 and sup["rarest"] is None)
lv = st["levels"][0]
check("creek level peak 5.5 ft, first reached in the 17:00 hour", lv["peak"] == 5.5 and lv["peak_at"] == "2026-11-03 17:00")
check("lag from the heaviest hour of rain (14:00) to the peak: 3 hours", lv["lag_hours"] == 3.0)
hrs = {t["name"]: t["hours"] for t in lv["thresholds"]}
check("hours at or above each flood level (Monitoring 8, Watch 2, Warning 0)", hrs == {"Flood Monitoring": 8, "Flood Watch": 2, "Flood Warning": 0})
check("reached Flood Watch (level 2)", lv["reached"] == 2 and st["reached"] == 2)
check("rising fast seen; highest status Flooding likely", st["rising_fast"] and st["status"] == "likely")
check("the supporting gauge that went quiet is named", st["quiet"] == ["San Bruno Mountain"])
check("hourly series kept for the graphs", len(r["series"]) == 8 and len(lv["series"]) > 20)
check("frozen: storm 1 unchanged after it closed", at40["storms"][0] == st)
check("no lag while the creek hasn't risen (storm 2)", state["storms"][1]["levels"][0]["lag_hours"] is None)
st2 = state["storms"][1]
check("storm 2: 60:00-65:00 joined across a 3-hour gap, 0.40 in", st2["start"] == "2026-11-05 12:00" and abs(st2["total"] - 0.4) < 0.005)
check("no tracking left once storms close", state["track"] == {})
sm = state["summary"][0]
check("season: 2 storms, one reaching Flood Watch, none Flood Warning", sm["storms"] == 2 and sm["watch"] == 1 and sm["warning"] == 0)
check("season rain at the creek's gauge = all its rain (2.25 in)", abs([x for x in sm["rain"] if x["key"] == "col_rain"][0]["total"] - 2.25) < 0.01)
check("season: days at each status counted", sm["status_days"]["likely"] == 1 and sm["status_days"]["none"] >= 3)
check("season: biggest storm is storm 1", sm["biggest"]["start"] == "2026-11-03 10:00")
check("reporting share for a gauge that went quiet < 1", [x for x in sm["rain"] if x["key"] == "col_rain_41200"][0]["reporting"] < 1)
check("hourly record kept to 10 days", all(k >= T.hkey(T0 + dt.timedelta(hours=99) - dt.timedelta(days=10)) for rec in state["ledger"].values() for k in rec["h"]))
# a late report fixes an hour
L = {}
now = T0 + dt.timedelta(hours=20)
T.merge_ledger(L, {"g": {"kind": "rain_increment", "points": [["2026-11-03 10:00", 0.0, ""], ["2026-11-03 13:00", 0.2, ""]]}}, now)
T.merge_ledger(L, {"g": {"kind": "rain_increment", "points": [["2026-11-03 10:00", 0.0, ""], ["2026-11-03 13:00", 0.2, ""], ["2026-11-03 13:00", 0.1, ""]]}}, now)
check("a late report replaces the hour (0.30 in, not 0.50)", L["g"]["h"] == {"2026-11-03 12:00": 0.3})
T.merge_ledger(L, {"g": {"kind": "rain_increment", "points": [["2026-11-03 10:00", 0.0, ""]]}}, now)
check("an hour with no reports in a later download is dry", L["g"]["h"] == {})
# a new water year: last season kept as "previous"
ny = dt.datetime(2027, 10, 1, 1, 0)
snap = snapshot(T0 + dt.timedelta(hours=99))
snap["generated"] = ny.strftime("%Y-%m-%d %H:%M:%S")
nx = T.run(snap, copy.deepcopy(state), ny, S, FREQ)
check("new water year: WY2028, last season kept under previous, storms cleared",
      nx["water_year"] == "WY2028" and nx["previous"]["water_year"] == "WY2027" and len(nx["previous"]["storms"]) == 2 and nx["storms"] == [])
check("record start date set", state["since"] == "2026-11-01" or state["since"] <= "2026-11-03")

print("storm_tracker: %d checks, %d failed" % (checks, fails))
sys.exit(1 if fails else 0)
