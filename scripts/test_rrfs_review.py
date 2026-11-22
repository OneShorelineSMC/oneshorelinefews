"""Tests for rrfs_review.py (RRFS rain forecast vs the rain gauges). Run: python scripts/test_rrfs_review.py"""
import datetime as dt
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rrfs_review as R  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


# Atlas 14 at gauge 100: Heavy / Very heavy / Intense over 1, 3, 6 hours
FREQ = {"100": {"minutes": {60: {1: 0.4, 2: 0.5, 5: 0.65}, 180: {1: 0.8, 2: 1.0, 5: 1.3}, 360: {1: 1.1, 2: 1.4, 5: 1.8}},
                "levels": {60: [0.4, 0.5, 0.65], 180: [0.8, 1.0, 1.3], 360: [1.1, 1.4, 1.8]}}}
MINS = {"sanbruno": [60, 180, 360]}
T = R.parse_t


def run_utc(local):   # Pacific (November: UTC-8) -> the log's UTC text
    return (local + dt.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%MZ")


def log(rows):
    head = "run_utc,product_min,creek,step_end_utc,in_avg,in_max\n"
    return head + "".join("%s,60,%s,%s,%s,%s\n" % (run_utc(r), c, run_utc(h + dt.timedelta(hours=1)), a, m) for r, c, h, a, m in rows)


tmp = tempfile.mkdtemp()
try:
    # a storm 10:00-15:00 at San Bruno, 0.6 in in the 12:00 hour (Very heavy over 1 hour)
    s0 = T("2026-11-22 10:00")
    series = [[R.hkey(s0 + dt.timedelta(hours=i)), v] for i, v in enumerate([0.05, 0.2, 0.6, 0.2, 0.1, 0.05])]
    storm = {"creek": "sanbruno", "name": "San Bruno Creek", "start": "2026-11-22 10:00", "end": "2026-11-22 15:00",
             "rain": [{"key": "r:100", "label": "First Avenue", "number": "100", "support": False, "total": 1.2,
                       "peaks": {"60": {"in": 0.6}, "180": {"in": 1.0}, "360": {"in": 1.2}}, "series": series}]}
    rows = []
    # the run 24 h ahead: 0.45 in at 14:00 (Heavy, 2 hours late); the run 6 h ahead: nothing much
    for i, v in enumerate([0.05, 0.1, 0.2, 0.45, 0.1]):
        rows.append((T("2026-11-21 09:00"), "sanbruno", T("2026-11-22 11:00") + dt.timedelta(hours=i), v, v * 1.5))
    rows.append((T("2026-11-22 04:00"), "sanbruno", T("2026-11-22 12:00"), 0.1, 0.15))
    # a run at 04:00 Pacific (12 UTC) on Nov 23: Heavy forecast for 15:00 that never came (no storm)
    rows.append((T("2026-11-23 04:00"), "sanbruno", T("2026-11-23 15:00"), 0.5, 0.7))
    p = os.path.join(tmp, "rrfs_log.csv")
    open(p, "w").write(log(rows))
    runs = R.read_log(p)
    check("log: UTC steps read as Pacific hours, period-beginning", T("2026-11-22 14:00") in runs[T("2026-11-21 09:00")]["sanbruno"])

    s = R.check_storm(storm, runs, FREQ, MINS["sanbruno"])
    m, l24, l6 = s["measured"], s["leads"]["24"], s["leads"]["6"]
    check("measured: rarest window Very heavy (1 hour, 0.6 in)", m["level"] == 2 and m["minutes"] == 60)
    check("24 h ahead: the run of Nov 21 09:00, Heavy, caught", l24["run"] == "2026-11-21 09:00" and l24["level"] == 1 and l24["verdict"] == "caught")
    check("24 h ahead: wettest hour 2 hours late", l24["timing_h"] == 2)
    check("24 h ahead: totals (average and wettest point)", l24["total"] == 0.9 and l24["total_max"] == 1.35)
    check("6 h ahead: the run of 04:00 (6 h before the start), missed", l6["run"] == "2026-11-22 04:00" and l6["verdict"] == "missed")

    ledger = {"r:100": {"kind": "rain", "h": {"2026-11-23 15:00": 0.05}}}
    creeks = [{"id": "sanbruno", "name": "San Bruno Creek", "rain": [{"key": "r:100", "number": "100"}]}]
    tracker = {"generated": "2026-11-24 12:00", "storms": [storm], "open": [], "ledger": ledger}
    out = R.review(tracker, runs, FREQ, MINS, creeks, T("2026-11-24 12:00"), since=None)
    fa = out["heavy_no_storm"]
    check("Heavy forecast with no storm: listed once, with what fell", len(fa) == 1 and fa[0]["run"] == "2026-11-23 04:00" and fa[0]["measured_total"] == 0.05)
    sm = out["summary"]["sanbruno"]
    check("summary by lead time", sm["leads"]["24"]["caught"] == 1 and sm["leads"]["6"]["missed"] == 1 and sm["heavy_no_storm"] == 1)

    # kept as they are: a closed storm and a checked run aren't redone (the log may have moved on)
    out2 = R.review(tracker, {}, FREQ, MINS, creeks, T("2026-11-24 12:00"), prev=out, since=None)
    check("closed storm kept without the log", out2["storms"] and out2["storms"][0]["leads"]["24"]["verdict"] == "caught")
    out3 = R.review(tracker, runs, FREQ, MINS, creeks, T("2026-11-24 12:00"), prev=out, since=None)
    check("a checked run isn't listed twice", len(out3["heavy_no_storm"]) == 1)
    # the reset: runs, storms and kept results before REVIEW_FROM are left out
    out4 = R.review(tracker, runs, FREQ, MINS, creeks, T("2026-11-24 12:00"), prev=out, since="2026-11-22 07:00")
    check("reset: a storm too soon after it (its 6 h run came before) and its kept result dropped", out4["storms"] == [] and out4["log_from"] == "2026-11-23 04:00")
    check("reset: Heavy-with-no-storm from a run after it still counts", len(out4["heavy_no_storm"]) == 1)
    out5 = R.review(tracker, runs, FREQ, MINS, creeks, T("2026-11-24 12:00"), prev=out, since="2026-11-24 00:00")
    check("reset: nothing after it yet", out5["storms"] == [] and out5["heavy_no_storm"] == [] and out5["log_from"] == "2026-11-24 00:00")
    check("verdicts", R.verdict(1, 0) == "over-forecast" and R.verdict(0, 0) == "no Heavy" and R.verdict(None, 1) == "not rated")
finally:
    shutil.rmtree(tmp)

print("\nAll passed" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
