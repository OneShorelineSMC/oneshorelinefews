"""Tests for storm mode in fetch_onerain.py (no network). Run: python scripts/test_storm_mode.py"""
import datetime as dt
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_onerain as F  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


NOW = dt.datetime(2026, 11, 18, 8, 40)
T = lambda m: (NOW - dt.timedelta(minutes=m)).strftime("%Y-%m-%d %H:%M")
U = lambda m: (NOW - dt.timedelta(minutes=m) + dt.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%MZ")
SB = {"id": "sanbruno", "stages": [{"key": "sb_stage"}], "rain": [{"key": "sb_rain"}], "rain_support": []}
CO = {"id": "colma", "stages": [{"key": "co_stage"}], "rain": [{"key": "co_rain"}], "rain_support": []}


def data(rain_min=None, trend="steady"):
    return {"creeks": [SB, CO], "creeks_preview": [], "sensors": {
        "sb_stage": {"points": [[T(30), 1.3, U(30)]], "latest": [T(30), 1.3, U(30)], "signals": {"trend": trend}},
        "sb_rain": {"points": [[T(rain_min), 0.04, U(rain_min)]] if rain_min is not None else [], "latest": None},
        "co_stage": {"points": [], "signals": {"trend": "fast"}}, "co_rain": {"points": [[T(5), 0.04, U(5)]]}}}


check("rain at San Bruno in the last 30 min: storm mode on", F.storm_active(data(rain_min=10), {"sanbruno"}, NOW))
check("San Bruno rising: storm mode on", F.storm_active(data(trend="rising"), {"sanbruno"}, NOW))
check("rain an hour ago and a steady creek: off", not F.storm_active(data(rain_min=60), {"sanbruno"}, NOW))
check("rain or a rise at another creek doesn't count", not F.storm_active(data(), {"sanbruno"}, NOW))

with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "creeks.json")
    json.dump(data(rain_min=90), open(p, "w"))
    try:
        F.fast_update(p, {"sanbruno"})
        check("dry: exits 3 so the workflow stops its loop", False)
    except SystemExit as e:
        check("dry: exits 3 so the workflow stops its loop", e.code == 3)
    check("dry: the file is left as it was", json.load(open(p)) == data(rain_min=90))

print("\n" + ("All passed" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
