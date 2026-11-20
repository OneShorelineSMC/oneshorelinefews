"""Tests for alert_review.py and the public column of status_log.csv (fetch_onerain.log_status_changes).
Run: python scripts/test_alert_review.py"""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alert_review as A  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


HEAD = "time,creek,from,to,level,rain_level,trend,reasons,public"
LOG = HEAD + """
2026-11-21 08:00:00,sanbruno,none,alert,0,2,rising,why_normal_rain why_rain,none
2026-11-21 09:10:00,sanbruno,alert,alert,1,2,rising,why_monitoring why_rain,alert
2026-11-21 10:00:00,sanbruno,alert,none,0,0,falling,,none
2026-11-21 12:00:00,sanbruno,none,alert,0,0,fast,why_rising_fast,none
2026-11-21 12:40:00,sanbruno,alert,none,0,0,steady,,none
2026-11-21 13:00:00,belmont,none,ready,2,0,rising,why_watch,ready
2026-11-21 13:30:00,belmont,ready,none,0,0,falling,,none
2026-11-21 15:00:00,colma,none,alert,0,1,rising,why_rain,none
2026-11-21 16:00:00,greenhills,none,alert,0,0,fast,why_rising_fast,none
"""
OLD = """time,creek,from,to,level,rain_level,trend,reasons
2026-11-13 12:35:14,belmont,offline,likely,0,0,,why_out_of_service why_trigger_tide why_gauge_offline
2026-11-13 14:25:14,belmont,likely,offline,0,0,,why_out_of_service
2026-11-13 09:10:00,sanbruno,none,alert,0,0,fast,why_rising_fast
2026-11-13 11:30:00,sanbruno,alert,ready,2,0,rising,why_watch
"""

tmp = tempfile.mkdtemp()
try:
    p = os.path.join(tmp, "status_log.csv")
    open(p, "w").write(LOG)
    rows = A.read_log(p)
    now = dt.datetime(2026, 11, 21, 16, 30)
    out, nw = A.review(rows, now, 3, {"greenhills": False})
    sb = out["sanbruno"]["alerts"]
    check("rain alert followed by Flood Monitoring 70 min later", sb[0]["outcome"] == "followed" and sb[0]["lead_min"] == 70 and sb[0]["why"] == ["rain"])
    check("rising-fast alert with no flood level after it: not followed", sb[1]["outcome"] == "not followed" and sb[1]["why"] == ["rising fast"])
    check("summary by cause", out["sanbruno"]["summary"]["by_why"]["rain"] == {"alerts": 1, "followed": 1}
          and out["sanbruno"]["summary"]["by_why"]["rising fast"] == {"alerts": 1, "followed": 0})
    check("a flood level with no alert ahead of it is listed", [x["creek"] for x in nw] == ["belmont"])
    check("an alert under 3 hours old is open", out["colma"]["alerts"][0]["outcome"] == "open")
    check("a creek without flood levels: no flood levels", out["greenhills"]["alerts"][0]["outcome"] == "no flood levels")

    open(p, "w").write(OLD)
    rows = A.read_log(p)
    bl = [r for r in rows if r[1] == "belmont"][0]
    check("older rows: a rain trigger counts as public", bl[3] == "likely" and bl[4])
    out, nw = A.review(rows, dt.datetime(2026, 11, 14), 3)
    a = out["sanbruno"]["alerts"][0]
    check("older rows: public from the flood level; marked approximate", a["outcome"] == "followed" and a["lead_min"] == 140 and a["approx"])
    check("older rows: a trigger isn't counted as an alert", not out.get("belmont", {}).get("alerts"))

    # status_log.csv: the old log gets the public column, rows are kept, and a public-only change is logged
    import fetch_onerain as F
    open(p, "w").write(OLD)
    prev = {"creeks": [{"id": "sanbruno", "status": {"key": "alert", "level": 0, "reasons": [{"code": "why_rising_fast"}]}}]}
    cur = {"generated": "2026-11-21 09:00:00", "creeks": [{"id": "sanbruno", "status": {"key": "alert", "level": 1, "reasons": [{"code": "why_monitoring"}], "rain": {"level": 0}, "trend": {"trend": "rising"}}}]}
    F.log_status_changes(cur, prev, os.path.join(tmp, "creeks.json"))
    lines = open(p).read().splitlines()
    check("log: header gets the public column, old rows kept", lines[0] == HEAD and len(lines) == 6 and lines[1].endswith(","))
    check("log: a change of the public status alone is logged", lines[-1].startswith("2026-11-21 09:00:00,sanbruno,alert,alert,1,") and lines[-1].endswith(",alert"))
    F.log_status_changes(cur, cur, os.path.join(tmp, "creeks.json"))
    check("log: nothing changed, nothing logged", len(open(p).read().splitlines()) == 6)
    check("public_key: trigger and offline", F.public_key({"key": "likely", "level": 0, "trigger": {"level": 3}}) == "likely"
          and F.public_key({"key": "alert", "level": 0, "reasons": [{"code": "why_gauge_offline"}]}) == "offline"
          and F.public_key({"key": "ready", "level": 0, "reasons": [{"code": "why_normal_rain"}]}) == "none")

    open(p, "w").write(LOG)
    json.dump({"generated": "2026-11-21 16:30:00", "creeks": [{"id": "sanbruno", "name": "San Bruno Creek", "status": {"has_levels": True}}],
               "creeks_preview": [{"id": "greenhills", "name": "Green Hills Creek", "status": {"has_levels": False}}]}, open(os.path.join(tmp, "creeks.json"), "w"))
    A.main(["alert_review.py", p, os.path.join(tmp, "alert_review.json")])
    d = json.load(open(os.path.join(tmp, "alert_review.json")))
    csvl = open(os.path.join(tmp, "alert_review.csv")).read().splitlines()
    check("main: json with names, exact_since, and a csv row per alert", d["creeks"]["sanbruno"]["name"] == "San Bruno Creek"
          and d["exact_since"] == "2026-11-21 08:00" and len(csvl) == 1 + sum(len(v["alerts"]) for v in d["creeks"].values()))
finally:
    shutil.rmtree(tmp)

print("\nAll passed" if not fails else f"\n{len(fails)} FAILED")
sys.exit(1 if fails else 0)
