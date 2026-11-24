"""Tests for "logged" rain gauges in creek_gauges.csv (read and kept in the hourly record, counted toward nothing;
staff 2026-11-24, Pulgas for the Cordilleras Creek page). Run: python scripts/test_logged_gauges.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import creek_config as C  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


t = C.load_tide_stations()
creeks, errors = C.load_creeks(t[0] if isinstance(t, tuple) else t)
check("the creek list loads with no problems", errors == [])
bel = [c for c in creeks if c["id"] == "belmont"][0]
check("Pulgas is a logged gauge under Belmont", [g["key"] for g in bel["rain_logged"]] == ["pul_rain"])
check("and not one of Belmont's own rain gauges", "pul_rain" not in [g["key"] for g in bel["rain"] + bel["rain_support"]])

import fetch_onerain as F  # noqa: E402
check("the data job reads it", F.SENSORS.get("pul_rain", {}).get("kind") == "rain_increment")
pub, _ = F.public_config()
pb = [c for c in pub if c["id"] == "belmont"][0]
check("the pages get it apart from the rain gauges, with its OneRain link", pb["rain_logged"][0]["url"].startswith(F.SITE) and
      "pul_rain" not in [g["key"] for g in pb["rain"] + pb["rain_support"]])

import storm_tracker as S  # noqa: E402
rain, _ = S.creek_gauges(bel)
check("Belmont's storms don't use it", "pul_rain" not in [g["key"] for g in rain])
led = {}
S.merge_ledger(led, {"pul_rain": {"kind": "rain_increment", "points": [["2026-11-24 10:20", 0.04], ["2026-11-24 10:40", 0.04]]}}, S.parse_t("2026-11-24 11:00"))
check("the hourly record keeps it", abs(led["pul_rain"]["h"]["2026-11-24 10:00"] - 0.08) < 1e-9)

print("\nAll passed" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
