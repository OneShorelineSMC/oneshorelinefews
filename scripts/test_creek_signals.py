"""
Checks for scripts/creek_signals.py (creek status layer). Run from the repo:  python scripts/test_creek_signals.py
Uses the real lookups/rain_frequency.csv (Atherton Channel rain gauge 41106: 1-hr storms 0.383 / 0.483 / 0.618 in;
3-hr 0.712 / 0.893 / 1.13 in).
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import SETTINGS, creek_status, rise_check, load_rain_frequency, load_settings, rain_signals, stage_signals, storm_years, tide_state

NOW = dt.datetime(2026, 1, 5, 12, 0)
S = {k: v[0] for k, v in SETTINGS.items()}
FREQ, problems = load_rain_frequency()
assert FREQ and not problems, problems
ATH = FREQ["41106"]


def at(minutes_ago):
    return (NOW - dt.timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d %H:%M")


def rain(per_15min, minutes):   # steady rain: an increment every 15 minutes for the last `minutes`
    return [[at(m), per_15min] for m in range(minutes - 15, -1, -15)][::-1] if minutes else []


checks = 0


def check(cond, msg):
    global checks
    checks += 1
    assert cond, msg


# Rain levels
r = rain_signals(rain(0.05, 60) + [[at(600), 0]], None, ATH, NOW, 12)
check(r["level"] == 0 and r["totals"]["60"] == 0.2, f"0.20 in/hr is below the 1-year storm: {r}")
r = rain_signals(rain(0.125, 60), None, ATH, NOW, 12)
check(r["level"] == 2 and r["driver"]["minutes"] == 60, f"0.50 in in 1 hr = Very heavy (2-yr 0.483): {r}")
check(1.9 < r["driver"]["storm_years"] < 2.5, f"about a 2-year storm: {r['driver']}")
r = rain_signals(rain(0.1, 180), None, ATH, NOW, 12)
check(r["level"] == 3 and r["driver"]["minutes"] == 180, f"1.20 in in 3 hr = Severe (5-yr 1.13): {r}")
r = rain_signals([[at(13 * 60), 0.0]], None, ATH, NOW, 12)
check(not r["fresh"], "no report for 13 hours = not fresh")
r = rain_signals([[at(11 * 60), 0.0]], None, ATH, NOW, 12)
check(r["fresh"], "dry-weather report 11 hours ago = still fresh (gauges report every 1-12 h when dry)")
r = rain_signals(rain(0.2, 60), None, None, NOW, 12)
check(r["level"] is None and r["totals"]["60"] == 0.8, "no Atlas 14 values: totals but no level")
check(storm_years(ATH["minutes"][60], 0.30) is None, "below the 1-year storm = no storm size")
check(storm_years(ATH["minutes"][60], 2.0) == 100.0, "beyond the table = 100-year (largest listed)")

# Trends
ivl = {"reports": "interval", "tidal": False, "thresholds": [{"value": 5.0, "name": "Flood Watch"}]}
chg = {"reports": "on change", "tidal": False, "thresholds": []}
fast = [[at(m), 2.0] for m in range(120, 60, -15)] + [[at(m), 2.0 + (60 - m) * 0.012] for m in range(60, -1, -15)]   # steady, then +0.72 ft in 60 min
s = stage_signals(fast, None, ivl, NOW, S, [])
check(s["trend"] == "fast" and s["rising_fast"]["rise_ft"] == 0.72, f"0.72 ft in an hour = rising fast: {s}")
check(s["rising_fast"]["hours_to_next"] is not None, "time to the next flood level is given")
hourly = [[at(120), 1.0], [at(60), 1.3], [at(0), 1.6]]                           # hourly readings, +0.3 ft/hr
s = stage_signals(hourly, None, ivl, NOW, S, [])
check(s["trend"] == "rising" and s["window_min"] == 60 and s["ft_per_hr"] == 0.3, f"hourly gauge widens the window: {s}")
s = stage_signals([[at(600), 0.4]], None, chg, NOW, S, [])
check(s["trend"] == "steady" and s["ft_per_hr"] == 0.0, f"on-change gauge with no report = steady: {s}")
s = stage_signals([[at(90), 3.0], [at(20), 2.8], [at(5), 2.7]], None, chg, NOW, S, [])
check(s["trend"] == "falling", f"falling: {s}")
s = stage_signals([[at(13 * 60), 0.4]], None, chg, NOW, S, [])
check(s["trend"] is None, "offline gauge has no trend")
tidal = dict(ivl, tidal=True)
s = stage_signals(fast, None, tidal, NOW, S, [[]])
check(s["trend"] == "rising" and not s["rising_fast"], f"tidal gauge rising with no rain is not 'rising fast': {s}")
wet = [(NOW - dt.timedelta(minutes=30), 0.2)]
s = stage_signals(fast, None, tidal, NOW, S, [wet])
check(s["trend"] == "fast", "tidal gauge rising fast after rain counts")

# Rapidly rising: rise_check (RISING_FAST_BASIS.md)
def ser(pairs):   # [(minutes ago, ft)] -> [(datetime, ft)] oldest first
    return sorted((NOW - dt.timedelta(minutes=m), v) for m, v in pairs)


usgs = {"reports": "interval", "tidal": False}
steady15 = [(m, 2.0) for m in range(180, 75, -15)]
r = rise_check(ser(steady15 + [(m, 2.0 + (75 - m) * 0.012) for m in range(75, -1, -15)]), usgs, NOW, S)
check(r and r["rise_ft"] == 0.72 and r["threshold_ft"] == 0.5, f"0.72 ft in an hour on a 15-min gauge: {r}")
check(rise_check(ser(steady15 + [(m, 2.0) for m in range(75, 0, -15)] + [(0, 2.8)]), usgs, NOW, S) is None,
      "one jump with the reading 15 min before not rising fast = not confirmed yet (a single bad reading never counts)")
spike = steady15 + [(m, 2.0) for m in range(75, 15, -15)] + [(15, 2.9), (0, 2.0)]
check(rise_check(ser(spike), usgs, NOW, S) is None, "spike that comes straight back = not rising fast")
check(rise_check(ser([(200, 1.0), (0, 1.8)]), usgs, NOW, S) is None,
      "scheduled gauge back after a 3-hour gap: the comparison reading is too old, so no 'rise' (staleness)")
hourly_g = {"reports": "interval", "tidal": False}
r = rise_check(ser([(180, 1.0), (120, 1.0), (60, 1.1), (0, 1.8)]), hourly_g, NOW, S)
check(r and r["rise_ft"] == 0.7, f"hourly gauge: previous reading 60 min earlier is outside RISE_CONFIRM_MIN, so no confirmation needed: {r}")
onchg = {"reports": "on change", "tidal": False}
r = rise_check(ser([(300, 0.8), (40, 1.0), (30, 1.3), (20, 1.5), (10, 1.7), (2, 1.9)]), onchg, NOW, S)
check(r and r["rise_ft"] == 1.1, f"on-change gauge holds its value: compared with 0.8 ft from 5 h ago: {r}")
hold = steady15 + [(m, 2.0 + (105 - m) * 0.012) for m in range(105, 29, -15)] + [(15, 2.85), (0, 2.88)]   # 15 min ago no longer meets it (0.49 ft)
r = rise_check(ser(hold), usgs, NOW, S)
check(r and r["at"] == (NOW - dt.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M"),
      f"rising slows after meeting the rule: stays on (RISE_HOLD_MIN) while the level holds: {r}")
check(rise_check(ser(hold[:-2] + [(15, 2.6), (0, 2.4)]), usgs, NOW, S) is None, "level drops back: rising fast ends")
check(rise_check(ser(hold), usgs, NOW, dict(S, RISE_HOLD_MIN=0)) is None, "RISE_HOLD_MIN 0: off as soon as the rule isn't met")
big = steady15 + [(m, 2.0 + (75 - m) * 0.012) for m in range(75, -1, -15)]
check(rise_check(ser(big), dict(usgs, rise_ft=1.0), NOW, S) is None, "per-gauge rise_ft 1.0: 0.72 ft/hr is not rising fast there")
check(rise_check(ser(big), dict(usgs, rise_ft=0.25), NOW, S)["threshold_ft"] == 0.25, "per-gauge rise_ft 0.25")
check(rise_check(ser(big), dict(usgs, rise_off=True), NOW, S) is None, "rise_ft off: never rising fast")
check(rise_check(ser([(m + 100, v) for m, v in big]), usgs, NOW, S) is None, "newest reading older than RISE_FRESH_MIN")

# fixes from review (RISING_FAST_BASIS.md §2)
check(rise_check(ser([(3 * 24 * 60, 0.12), (0, 5.15)]), onchg, NOW, S) is None,
      "on-change gauge back after 3 days offline: last reading is too old to compare with (was a false +5 ft)")
check(rise_check(ser([(200, 1.0), (65, 1.0), (15, 1.0), (0, 1.8)]), usgs, NOW, S) is None,
      "previous reading within 20 min can't be checked (its own comparison is stale): not confirmed, doesn't count")
quiet = [(300, 0.8), (75, 0.8), (70, 1.0), (60, 1.3), (50, 1.5), (40, 1.7)]
check(rise_check(ser(quiet), onchg, NOW, S) is None,
      "on-change gauge met the rule 40 min ago and has been quiet since (level unchanged): hold has ended")
check(rise_check(ser(quiet), onchg, NOW - dt.timedelta(minutes=15), S)["held"] is False,
      "...but 25 min after that reading it is still on")
r = rise_check(ser([(180, 1.0), (120, 1.0), (110, 1.0), (50, 1.8)]), hourly_g, NOW, S)
check(r is not None, f"scheduled gauge's newest reading counts until the next one arrives: {r}")
r = stage_signals([[at(m), v] for m, v in hold], None, dict(usgs, thresholds=[{"value": 4.0, "name": "Flood Warning"}]), NOW, S, [])
check(r["rising_fast"]["held"] and r["rising_fast"]["hours_to_next"] is None,
      f"while only held, no 'reaches the next level in ...' estimate: {r['rising_fast']}")

check(rise_check(ser([(11 * 60, 0.13), (0, 0.90)]), onchg, NOW, S) is None,
      "on-change gauge, dry weather: one jump after hours without a report isn't confirmed, so it doesn't count")
r = rise_check(ser([(11 * 60, 0.13), (8, 0.90), (3, 0.95)]), onchg, NOW, S)
check(r and r["rise_ft"] == 0.82, f"...the next report minutes later confirms a real rise: {r}")
check(rise_check(ser([(11 * 60, 0.13), (0, 0.90)]), onchg, NOW, dict(S, RISE_CONFIRM_MIN=0)) is not None,
      "RISE_CONFIRM_MIN 0 = confirmation off")
r = rise_check(ser([(180, 1.0), (120, 1.0), (110, 1.0), (50, 1.8)]), hourly_g, NOW, S)
check(r and r["held"], f"scheduled gauge: newest reading that met the rule 50 min ago counts as held (no 'at this rate' estimate): {r}")

# RISE_CONFIRM_FRACTION (0.5): the reading before must have risen at least half the threshold
ramp = steady15 + [(75, 2.0), (60, 2.0), (45, 2.05), (30, 2.1), (15, 2.3), (0, 2.6)]   # prev rose 0.30, newest 0.60
r = rise_check(ser(ramp), usgs, NOW, S)
check(r and r["rise_ft"] == 0.6, f"start of a real rise: the reading before rose 0.30 (over half of 0.5), so it counts now: {r}")
check(rise_check(ser(ramp), usgs, NOW, dict(S, RISE_CONFIRM_FRACTION=1)) is None,
      "with RISE_CONFIRM_FRACTION 1 the reading before must meet the full rule (one reading later)")
glitch = steady15 + [(m, 2.0) for m in range(75, 15, -15)] + [(15, 2.1), (0, 2.7)]      # prev rose 0.10
check(rise_check(ser(glitch), usgs, NOW, S) is None, "reading before rose only 0.10 (under half): a lone jump doesn't count")

# Daylight saving ends Nov 1, 2026: 1:00-1:59 AM happens twice. A 15-min gauge rising a steady 0.3 ft/hr
# must not look like 0.6 ft in an hour in the second 1 AM hour (Pacific clock times are 2 h apart there).
from zoneinfo import ZoneInfo
PTZ, U = ZoneInfo("America/Los_Angeles"), dt.timezone.utc
t0u = dt.datetime(2026, 11, 1, 6, 0, tzinfo=U)                      # 11 PM PDT, Oct 31
dst_pts = []
for k in range(0, 4 * 4 + 1):                                       # every 15 min to 10:00 UTC (2 AM PST)
    u = t0u + dt.timedelta(minutes=15 * k)
    dst_pts.append([u.astimezone(PTZ).strftime("%Y-%m-%d %H:%M"), round(1.0 + 0.075 * k, 3), u.strftime("%Y-%m-%dT%H:%MZ")])
for k in range(5, len(dst_pts)):
    nowd = (t0u + dt.timedelta(minutes=15 * k)).astimezone(PTZ)
    sig = stage_signals(dst_pts[:k + 1], None, usgs, nowd.replace(tzinfo=None), S, [])
    check(not sig["rising_fast"], f"0.3 ft/hr through the repeated hour is not rising fast (at {dst_pts[k][0]}, fold {nowd.fold}): {sig['rising_fast']}")
fast_dst = [[x[0], round(1.0 + 0.2 * k, 3), x[2]] for k, x in enumerate(dst_pts)]   # 0.8 ft/hr
nowd = (t0u + dt.timedelta(minutes=15 * 14)).astimezone(PTZ)                        # 1:30 AM PST (second pass)
sig = stage_signals(fast_dst[:15], None, usgs, nowd.replace(tzinfo=None), S, [])
check(sig["rising_fast"] and sig["rising_fast"]["rise_ft"] == 0.8, f"0.8 ft/hr in the second 1 AM hour is 0.8, not 1.6: {sig['rising_fast']}")

# ---- creek status (THRESHOLDS_BASIS.md §10)
TH = [{"value": 2.0, "name": "Flood Monitoring", "level": 1}, {"value": 3.0, "name": "Flood Watch", "level": 2},
      {"value": 4.0, "name": "Flood Warning", "level": 3}]


def creek(stage_pts, rains, levels=True, tidal=False, triggers=None, settings=None, tide=None):
    """rains: list of point lists, one per rain gauge (the first shown, the rest supporting)."""
    g = {"key": "st", "reports": "interval", "tidal": tidal, "thresholds": TH if levels else []}
    rg = [{"key": f"r{i}", "label": f"Rain {i}", "number": "41106"} for i in range(len(rains))]
    c = {"id": "x", "stages": [g], "rain": rg[:1], "rain_support": rg[1:], "rain_triggers": triggers or []}
    sens = {"st": {"points": stage_pts, "latest": None}}
    for gg, pts in zip(rg, rains):
        sens[gg["key"]] = {"points": pts, "latest": None, "signals": rain_signals(pts, None, ATH, NOW, 12)}
    series = [[(dt.datetime.strptime(t, "%Y-%m-%d %H:%M"), v) for t, v in p] for p in rains]
    sens["st"]["signals"] = stage_signals(stage_pts, None, g, NOW, settings or S, series)
    return creek_status(c, sens, tide or {}, NOW, settings or S)


flat = lambda v: [[at(m), v] for m in range(120, -1, -15)]   # noqa: E731
dry = [[at(300), 0.0]]
codes = lambda st: [r["code"] for r in st["reasons"]]       # noqa: E731
st = creek(flat(4.2), [dry])
check(st["key"] == "likely" and codes(st)[0] == "why_warning", f"Flood Warning = Flooding likely: {st}")
st = creek([[at(m), 2.6] for m in range(120, 60, -15)] + [[at(m), 2.6 + (60 - m) * 0.012] for m in range(60, -1, -15)], [dry])
check(st["key"] == "ready" and st["reasons"][0] == {"code": "why_watch", "rising_fast": True}, f"Watch, rising fast: {st}")
st = creek(flat(1.0), [rain(0.1, 180), rain(0.1, 180)])
check(st["key"] == "alert" and st["rain"]["level"] == 3 and "why_normal_rain" in codes(st), f"severe rain, two gauges, creek Normal = Stay alert: {st}")
st = creek(flat(1.0), [rain(0.1, 180), dry])
check(st["rain"]["level"] == 2 and any("one gauge only" in n for n in st["staff_notes"]), f"severe at one of two gauges = very heavy: {st}")
st = creek(flat(1.0), [rain(0.1, 180)])
check(st["rain"]["level"] == 3 and "only one working rain gauge" in st["staff_notes"], f"one-gauge creek can reach Severe: {st}")
st = creek(fast, [dry], levels=False)
check(st["key"] == "ready" and "why_rising_fast" in codes(st), f"no flood levels + rising fast = Be ready: {st}")
S0 = dict(S, BE_READY_FROM_RAIN=0)
st = creek(fast, [dry], levels=False, settings=S0)
check(st["key"] == "alert", f"...or Stay alert with BE_READY_FROM_RAIN = 0: {st}")
trig = [{"gauge": "r0", "minutes": 240, "value": 0.42, "level": 3, "high_tide": True, "tide_min": 6.32, "label": "4-hour rain + high tide", "name": "Flooding likely"}]
st = creek(flat(1.0), [rain(0.15, 240)], triggers=trig, tide={"ft": 6.5})
check(st["key"] == "likely" and "why_trigger_tide" in codes(st), f"Belmont-style rain + tide trigger met = Flooding likely: {st}")
st = creek(flat(1.0), [rain(0.15, 240)], triggers=trig, tide={"ft": None})
check(st["key"] != "likely" and any("tide unknown" in n for n in st["staff_notes"]), f"tide unknown: trigger not met, flagged: {st}")
st = creek(flat(1.0), [rain(0.1, 60)], tidal=True, tide={"high_soon": True, "next_high": "2026-01-05 13:30"})
check(st["key"] == "alert" and codes(st)[-1] == "tide_rising_line", f"heavy rain + rising tide on a tidal creek = Stay alert: {st}")
st = creek(flat(1.0), [rain(0.1, 60)], tidal=False, tide={"high_soon": True})
check(st["key"] == "none", f"heavy rain alone = No alerts: {st}")
st = creek([[at(14 * 60), 1.0]], [dry])
check(st["key"] == "offline", f"stage gauge offline = Offline: {st}")
st = creek([[at(14 * 60), 1.0]], [rain(0.125, 60)])
check(st["key"] == "alert", f"offline gauge but very heavy rain = Stay alert: {st}")
check(codes(st)[0] == "why_gauge_offline" and "why_normal_rain" not in codes(st), f"...and says the gauge is offline, not 'normal level': {st}")
st = creek(flat(1.0), [rain(0.125, 60), [[at(150), 0.0]]])
check(any(r["code"] == "why_stale" for r in st["reasons"]), f"gauge silent while another records heavy rain: {st}")
st = creek(flat(1.0), [rain(0.05, 60), [[at(150), 0.0]]])
check(not any(r["code"] == "why_stale" for r in st["reasons"]), f"light rain at one gauge only is normal: {st}")
st = creek(flat(1.0), [dry, dry])
check(st["key"] == "none" and not st["reasons"], f"quiet creek = No alerts: {st}")
T = tide_state([(NOW, 5.0)], [(NOW + dt.timedelta(hours=2), 7.2, "H"), (NOW + dt.timedelta(hours=8), 0.5, "L")], [], NOW, 3)
check(T["ft"] == 5.0 and T["source"] == "predicted" and T["rising"] and T["high_soon"], f"tide state: {T}")

vals, prob = load_settings()
check(not prob, f"settings.csv values the data job uses are valid: {prob}")
print(f"creek_signals: {checks} checks passed")
