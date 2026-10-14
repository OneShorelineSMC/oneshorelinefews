"""
Checks for scripts/creek_signals.py (creek status layer). Run from the repo:  python scripts/test_creek_signals.py
Uses the real lookups/rain_frequency.csv (Atherton Channel rain gauge 41106: 1-hr storms 0.383 / 0.483 / 0.618 in;
3-hr 0.712 / 0.893 / 1.13 in).
"""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import SETTINGS, load_rain_frequency, load_settings, rain_signals, stage_signals, storm_years

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

vals, prob = load_settings()
check(not prob, f"settings.csv values the data job uses are valid: {prob}")
print(f"creek_signals: {checks} checks passed")
