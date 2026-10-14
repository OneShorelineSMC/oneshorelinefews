"""
Checks for scripts/creek_signals.py (creek status layer). Run from the repo:  python scripts/test_creek_signals.py
Uses the real lookups/rain_frequency.csv (Atherton Channel rain gauge 41106: 1-hr storms 0.383 / 0.483 / 0.618 in;
3-hr 0.712 / 0.893 / 1.13 in).
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import SETTINGS, creek_status, load_rain_frequency, load_settings, rain_signals, stage_signals, storm_years, tide_state

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
fast = [[at(m), 2.0 + (60 - m) * 0.012] for m in range(60, -1, -15)]          # +0.72 ft in 60 min, every 15 min
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
st = creek([[at(m), 2.6 + (60 - m) * 0.012] for m in range(60, -1, -15)], [dry])
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
