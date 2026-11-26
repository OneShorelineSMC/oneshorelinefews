"""Checks for scripts/monthly_summary.py: places and their districts, closures joined, storms joined (repeats out), high-tide
runs, and past months kept."""
import datetime as dt
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monthly_summary as M   # noqa: E402

checks = fails = 0


def check(name, ok):
    global checks, fails
    checks += 1
    if not ok:
        fails += 1
    print(("ok   " if ok else "FAIL ") + name)


places, creek_places = M.load_places()
check("places.csv: all 20 cities, each with an AB 825 seat", sum(1 for p in places.values() if p["kind"] == "city" and p["seat"] in ("North", "Central", "South", "Coastal")) == 20)
check("places.csv: split cities carry both districts", places["san bruno"]["districts"] == [1, 5] and places["millbrae"]["districts"] == [1])
check("creek_places: every place is in places.csv", all(p.lower() in places for ps in creek_places.values() for p in ps))

roads = {"creek_side": {"colma": "bay"}, "log": [
    {"kind": "flood", "route": "SR-84", "dir": "East", "where": "A to B", "place": "Menlo Park", "lat": 37.4955, "lon": -122.1328,
     "started": "2026-11-24 10:25", "active": True, "cause": "tide", "facility": "On Ramp"},
    {"kind": "flood", "route": "SR-84", "dir": "West", "where": "C to D", "place": "Menlo Park", "lat": 37.4955, "lon": -122.1328,
     "started": "2026-11-24 10:25", "active": True, "cause": "tide", "facility": "On Ramp"},
    {"kind": "repair", "route": "SR-1", "where": "x to y", "place": "Pescadero", "started": "2026-11-23 08:00"},
    {"kind": "flood", "route": "SR-1", "where": "x to y", "place": "Pacifica", "started": "2026-10-31 08:00"}]}
rd = M.month_roads(roads, "2026-11", places)
check("roads: same route and hour joined (4 ramps = 1 entry, 2 closures); repairs and last month left out",
      len(rd) == 1 and rd[0]["closures"] == 2 and rd[0]["dirs"] == ["East", "West"] and rd[0]["places"][0]["districts"] == [3, 4])


def storm(creek, a, b, total, reached=0, status=None, level=None):
    return {"creek": creek, "name": creek.title() + " Creek", "start": a, "end": b, "status": status,
            "rain": [{"key": creek + "_rain", "label": "G", "support": False, "total": total,
                      "rarest": {"level": level, "minutes": 60, "years": 12.0} if level else None}],
            "levels": [{"label": "L", "peak": 4.0, "peak_at": a, "reached": reached}]}


tracker = {"storms": [storm("colma", "2026-11-18 03:00", "2026-11-19 10:00", 2.4, reached=2, level=3),
                      storm("colma", "2026-11-18 06:00", "2026-11-19 10:00", 2.1, reached=2),          # a repeat
                      storm("sanbruno", "2026-11-18 05:00", "2026-11-19 12:00", 4.4),
                      storm("colma", "2026-11-03 08:00", "2026-11-03 09:00", 0.12)],
           "open": [], "days": {"rain": {"colma_rain": {"2026-11-18": 2.0, "2026-11-19": 0.4, "2026-10-31": 1.0}}}}
rows = [{"time": "2026-11-18 08:00:00", "creek": "colma", "to": "ready", "level": "2", "reasons": "why_watch", "public": ""},
        {"time": "2026-11-18 08:45:00", "creek": "colma", "to": "none", "level": "0", "reasons": "", "public": ""},
        # rising fast raises the full status but not the public one
        {"time": "2026-11-18 09:00:00", "creek": "sanbruno", "to": "ready", "level": "0", "reasons": "why_rising_fast", "public": ""},
        {"time": "2026-11-18 09:30:00", "creek": "sanbruno", "to": "none", "level": "0", "reasons": "", "public": ""}]
tt = {"stations": [{"id": "9414523", "name": "Redwood City", "side": "bay", "mhhw": 7.02,
                    "levels": [{"key": "mhhw", "ft": 7.02, "label": "MHHW"}, {"key": "oneyear", "ft": 8.3, "label": "1-year tide"}],
                    "days": {"2026-11-18": {"max": 8.4, "table": 7.6}, "2026-11-19": {"max": 8.1}, "2026-11-20": {"max": 8.35},
                             "2026-11-24": {"max": 9.5, "table": 8.3}, "2026-11-25": {"max": 9.55, "table": 8.36}},
                    "months": {"2026-11": {"max": 9.55, "max_date": "2026-11-25 11:48", "count": {"oneyear": 4}}},
                    "ranks": {"2026-11": {"rank": 1, "of": 33}}}],
      "nws": [{"event": "Coastal Flood Advisory", "onset": "2026-11-23T06:10:00-08:00", "ends": "2026-11-26T16:00:00-08:00"}]}
hist = {"9414523": {"2026": {"d": {"0103": 9.71}}, "1983": {"d": {"1203": 9.61}}}}
now = dt.datetime(2026, 11, 25, 16, 30)
m = M.build_month("2026-11", now, tt, hist, tracker, rows, roads, None)
s = [x for x in m["storms"] if x["start"].startswith("2026-11-18")][0]
check("storms: creeks joined into one storm, the repeat taken out", len(m["storms"]) == 2 and len(s["creeks"]) == 2 and
      [c["rain"] for c in s["creeks"]] == [4.4, 2.4])
c = [x for x in s["creeks"] if x["creek"] == "colma"][0]
check("storm: Colma reached Flood Watch, Be ready for 45 min", c["reached_label"] == "Flood Watch" and c["status"]["label"] == "Be ready" and c["status"]["minutes"] == 45)
sb = [x for x in s["creeks"] if x["creek"] == "sanbruno"][0]
check("public status only: rising fast alone isn't Be ready; the storm tracker's level isn't used without the status layer's",
      sb["status"] is None and sb["reached"] == 0)
check("public status: a rain trigger counts; a rain rating doesn't; the public column wins when there is one",
      M.public_status({"to": "likely", "level": "0", "reasons": "why_out_of_service why_trigger why_gauge_offline", "public": ""}) == "likely"
      and M.public_status({"to": "ready", "level": "1", "reasons": "why_monitoring why_rain", "public": ""}) == "alert"
      and M.public_status({"to": "ready", "level": "0", "reasons": "why_rising_fast", "public": "none"}) == "none")
check("staff-preview creeks (Green Hills) show rain only", M.storm_events({"storms": [storm("greenhills", "2026-11-18 03:00", "2026-11-18 09:00", 1.2, reached=1)]},
      "2026-11-11"[:7], {}, {}, set(), {"colma"})[0]["creeks"][0]["public"] is False)
check("storm: notable; the small Nov 3 storm isn't", s["notable"] and not [x for x in m["storms"] if x["start"].startswith("2026-11-03")][0]["notable"])
check("high-tide runs: Nov 18 to 20 (a one-day gap allowed) and Nov 24 to 25",
      [(p["first"], p["last"]) for p in m["tide_periods"]] == [("2026-11-18", "2026-11-20"), ("2026-11-24", "2026-11-25")])
check("storm on a high tide: Nov 18", s["on_high_tide"] == ["2026-11-18"])
check("tide closure goes with the Nov 24 to 25 run", m["tide_periods"][1]["roads"] == [0] and s["roads"] == [])
t = m["tides"][0]
check("all-time rank: 3rd highest (Jan 3, 2026 and Dec 3, 1983 were higher)", t["all_time"]["rank"] == 3 and t["all_time"]["higher"][0][0] == "2026-01-03")
check("month rain: only November days counted", m["rain"]["gauges"][0]["in"] == 2.4)
A = {x["place"]: x for x in m["areas"]}
check("by area: Colma Creek under South San Francisco (D1/D5) and Colma (D5); SR-84 under Menlo Park (D3/D4); sorted by district",
      any(i.get("creek") == "Colma Creek" for i in A["South San Francisco"]["items"]) and A["Colma"]["districts"] == [5]
      and A["Menlo Park"]["districts"] == [3, 4] and any(i.get("route") == "SR-84" for i in A["Menlo Park"]["items"])
      and [x["place"] for x in m["areas"]][0] == "South San Francisco")
check("not complete before the month ends", not m["complete"] and m["through"] == "2026-11-25 16:30")
check("the month before is redone through the 3rd only",
      M.months_to_build(dt.datetime(2026, 12, 2, 9)) == ["2026-11", "2026-12"] and M.months_to_build(dt.datetime(2026, 12, 4, 9)) == ["2026-12"])

with tempfile.TemporaryDirectory() as d:
    json.dump({"months": {"2026-10": {"month": "2026-10", "kept": True}}}, open(os.path.join(d, "monthly_summary.json"), "w"))
    json.dump(tt, open(os.path.join(d, "tide_tracker.json"), "w"))
    json.dump(tracker, open(os.path.join(d, "storm_tracker.json"), "w"))
    out = M.run(d, now)
    check("run: past months kept as they were, this month added", out["months"]["2026-10"] == {"month": "2026-10", "kept": True} and "2026-11" in out["months"])

print("monthly_summary: %d checks, %d failed" % (checks, fails))
sys.exit(1 if fails else 0)
