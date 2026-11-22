"""Tests for bayside_compare.py (Bayside rain compared storm by storm). Run: python scripts/test_bayside_compare.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bayside_compare as B  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


FREQ = {"2": {"minutes": {60: {1: 0.4, 2: 0.5, 5: 0.65}, 360: {1: 1.1, 2: 1.4, 5: 1.7}},
              "levels": {60: [0.4, 0.5, 0.65], 360: [1.1, 1.4, 1.7]}}}
CREEKS = [{"id": c, "short": c.title(), "rain": [{"key": "r" + str(i), "label": "G" + str(i), "number": str(i)}]}
          for i, c in enumerate(["colma", "sanbruno", "belmont", "atherton"], start=1)]


def led(**k):
    return {key: {"kind": "rain", "h": h} for key, h in k.items()}


# storm 1: Nov 22 10:00-12:00, San Bruno wettest (0.6 in one hour = Very heavy); 8 dry hours, then storm 2 at 21:00
ledger = led(r1={"2026-11-22 10:00": 0.2, "2026-11-22 11:00": 0.1},
             r2={"2026-11-22 10:00": 0.3, "2026-11-22 11:00": 0.6, "2026-11-22 12:00": 0.1, "2026-11-22 21:00": 0.04},
             r3={"2026-11-22 11:00": 0.3}, r4={"2026-11-22 12:00": 0.2, "2026-11-22 21:00": 0.2},
             **{"sfo:KSFO": {"2026-11-22 11:00": 0.5}})
tracker = {"generated": "2026-11-23 12:00", "rules": {"STORM_DRY_HOURS": 6, "STORM_MIN_IN": 0.1}, "ledger": ledger}
out = B.build(tracker, CREEKS, FREQ, B.parse_t("2026-11-23 12:00"))
e = sorted(out["storms"], key=lambda x: x["start"])
check("two Bayside storms, split by 8 dry hours at every gauge", len(e) == 2 and e[0]["start"] == "2026-11-22 10:00" and e[1]["start"] == "2026-11-22 21:00")
sb = [r for r in e[0]["gauges"] if r["creek"] == "sanbruno"][0]
check("San Bruno: total, wettest hour and its rating", sb["total"] == 1.0 and sb["p1"] == 0.6 and sb["level"] == 2 and sb["minutes"] == 60)
check("San Bruno ranked 1st, 3.33 x the others' average", e[0]["rank"] == 1 and e[0]["ratio"] == round(1.0 / ((0.3 + 0.3 + 0.2) / 3), 2))
check("SFO read over the same hours, not rated", [r for r in e[0]["gauges"] if r["key"] == "sfo:KSFO"][0]["total"] == 0.5
      and [r for r in e[0]["gauges"] if r["key"] == "sfo:KSFO"][0]["level"] is None)
check("storm 2: San Bruno 2nd", e[1]["rank"] == 2)
s = out["season"]
check("season: totals and who was wettest", s["gauges"]["r2"]["total"] == 1.04 and s["gauges"]["r2"]["wettest"] == 1 and s["gauges"]["r4"]["wettest"] == 1 and s["focus_wettest"] == 1)

# kept as first written once closed, after the hourly record has moved on
out2 = B.build(dict(tracker, ledger=led()), CREEKS, FREQ, B.parse_t("2026-12-05 12:00"), prev=out)
check("closed storms kept without the hourly record", len(out2["storms"]) == 2)
# an open storm (last wet hour under 6 hours ago) is redone each run
out3 = B.build(tracker, CREEKS, FREQ, B.parse_t("2026-11-22 23:00"))
check("open storm marked open", [x for x in out3["storms"] if x["start"] == "2026-11-22 21:00"][0]["closed"] is False)
# SFO before its record began: no record, not no rain
led4 = led(r1={"2026-11-13 10:00": 0.5}, r2={"2026-11-13 10:00": 0.6}, **{"sfo:KSFO": {"2026-11-15 10:00": 0.1}})
out4 = B.build(dict(tracker, ledger=led4), CREEKS, FREQ, B.parse_t("2026-11-16 12:00"))
x = [r for r in sorted(out4["storms"], key=lambda q: q["start"])[0]["gauges"] if r["key"] == "sfo:KSFO"][0]
check("SFO missing before its record began", x.get("missing") is True)

print("\nAll passed" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
