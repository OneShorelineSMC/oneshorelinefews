"""Tests for road_closures.py with made-up Caltrans data in the published LCS format and an ArcGIS layer. Run: python scripts/test_road_closures.py"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import road_closures as R  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


NOW = dt.datetime(2026, 11, 13, 22, 0, tzinfo=dt.timezone.utc)   # 2 PM Pacific
E = lambda h: int((NOW + dt.timedelta(hours=h)).timestamp())


def lcs(idx, county, work, start_h, end_h=4, c97=None, c98=None, c22=False, route="US-101", where="At Holly St", to=""):
    c = {"closureID": idx, "logNumber": "1", "isClosureEndIndefinite": "false", "facility": "Off Ramp", "typeOfClosure": "Ramp",
         "typeOfWork": work, "lanesClosed": "1", "totalExistingLanes": "1",
         "closureTimestamp": {"closureStartEpoch": str(E(start_h)), "closureEndEpoch": str(E(end_h))},
         "code1097": {"isCode1097": "true" if c97 is not None else "false", "code1097Timestamp": {"code1097Epoch": str(E(c97)) if c97 is not None else ""}},
         "code1098": {"isCode1098": "true" if c98 is not None else "false", "code1098Timestamp": {"code1098Epoch": str(E(c98)) if c98 is not None else ""}},
         "code1022": {"isCode1022": "true" if c22 else "false", "code1022Timestamp": {"code1022Epoch": ""}}}
    return {"lcs": {"index": idx + "-1", "location": {"travelFlowDirection": "Southbound",
            "begin": {"beginCounty": county, "beginRoute": route, "beginLocationName": where, "beginNearbyPlace": "San Carlos", "beginLatitude": 37.5, "beginLongitude": -122.26},
            "end": {"endCounty": county, "endLocationName": to}}, "closure": c}}


LCS = {"data": [
    lcs("A1", "San Mateo", "Roadway Flooding", -3, c97=-2.5),                     # flooding, started 2.5 hr ago
    lcs("A2", "San Mateo", "AC Paving", -3, c97=-3),                              # not storm
    lcs("A3", "Santa Clara", "Flooding", -3, c97=-3),                             # other county
    lcs("A4", "San Mateo", "Slide - Mud/Dirt/Rock", -10, c97=-9, c98=-1, route="SR-1", where="Devil's Slide", to="Linda Mar Blvd"),   # ended
    lcs("A5", "San Mateo", "Flooded Areas", 5, c97=None),                         # planned, not started
    lcs("A6", "San Mateo", "Storm Event", -2, c97=-2, c22=True),                  # cancelled
    lcs("A7", "San Mateo", "Snow & Icing Conditions", -2, c97=-2),                # not our kind of storm
    lcs("A8", "San Mateo", "Storm Damage Repairs", -2, c97=-2, route="SR-84"),   # repair
]}
cur, smc = R.lcs_closures(json.dumps(LCS), NOW)
ids = [c["id"] for c in cur]
check("LCS: San Mateo storm closures that started (not paving, other counties, planned, cancelled or snow)", ids == ["lcs:A1-1", "lcs:A4-1", "lcs:A8-1"] and smc == 7)
a1 = cur[0]
check("LCS: flooding tagged flood, Pacific start time from code 1097, still open", a1["kind"] == "flood" and a1["started"] == "2026-11-13 11:30" and a1["ended"] is None and a1["est_end"] == "2026-11-13 18:00")
check("LCS: slide tagged storm, ended from code 1098, where 'from to'", cur[1]["kind"] == "storm" and cur[1]["ended"] == "2026-11-13 13:00" and cur[1]["where"] == "Devil's Slide to Linda Mar Blvd")
check("LCS: storm damage repairs tagged repair", cur[2]["kind"] == "repair")

ITEM = {"id": "c933349c56f640edba968f208063eee0", "url": "https://services.example.com/arcgis/rest/services/EmergencyRoadClosures/FeatureServer"}
ERC = {"fields": [{"name": "OBJECTID", "type": "esriFieldTypeOID"}, {"name": "County", "type": "esriFieldTypeString"}, {"name": "Route", "type": "esriFieldTypeString"},
                  {"name": "Location", "type": "esriFieldTypeString"}, {"name": "RestrictionType", "type": "esriFieldTypeString"},
                  {"name": "Detour", "type": "esriFieldTypeString"}, {"name": "ClosureDate", "type": "esriFieldTypeDate"}, {"name": "EstOpenDate", "type": "esriFieldTypeDate"}],
       "features": [
           {"attributes": {"OBJECTID": 11, "County": "San Mateo", "Route": "SR 92", "Location": "Skyline Blvd to Hwy 35", "RestrictionType": "Flooding",
                           "Detour": "Use I-280", "ClosureDate": E(-4) * 1000, "EstOpenDate": None}, "geometry": {"paths": [[[-122.4, 37.5], [-122.38, 37.51], [-122.36, 37.52]]]}},
           {"attributes": {"OBJECTID": 12, "County": "Marin", "Route": "SR 1", "Location": "Muir Beach", "RestrictionType": "Slides", "ClosureDate": E(-4) * 1000}},
           {"attributes": {"OBJECTID": 13, "County": "San Mateo", "Route": "SR 35", "Location": "Page Mill", "RestrictionType": "Wildfire", "ClosureDate": E(-4) * 1000}}]}
fetched = []
def fetch(url):
    fetched.append(url)
    if "cwwp2" in url:
        return json.dumps(LCS)
    if "sharing/rest/content/items" in url:
        return json.dumps(ITEM)
    if "/FeatureServer/0/query?" in url:
        return json.dumps(ERC)
    raise OSError("unexpected " + url)
r = R.update({}, NOW, fetch)
erc = [c for c in r["log"] if c["id"].startswith("erc:")]
check("ERC: service read from the ArcGIS item (layer 0), fields found by name", r["sources"]["erc"]["service"].endswith("FeatureServer/0") and r["sources"]["erc"]["fields"]["county"] == "County"
      and r["sources"]["erc"]["fields"]["start"] == "ClosureDate" and r["sources"]["erc"]["fields"]["end"] == "EstOpenDate")
check("ERC: San Mateo flooding kept (not Marin, not wildfire), with detour and a point on the line", len(erc) == 1 and erc[0]["kind"] == "flood" and erc[0]["detour"] == "Use I-280"
      and erc[0]["started"] == "2026-11-13 10:00" and erc[0]["lat"] == 37.51)
check("update: active list and both sources ok", sorted(r["active"]) == ["erc:11", "lcs:A1-1", "lcs:A8-1"] and r["sources"]["lcs"]["ok"] and r["sources"]["erc"]["ok"] and not r["problems"])

# next run: the ERC flooding is gone (reopened), A1 still there; the ERC service comes from the cache, not the item
LATER = NOW + dt.timedelta(minutes=10)
ERC2 = dict(ERC, features=ERC["features"][1:])
fetched.clear()
def fetch2(url):
    fetched.append(url)
    return json.dumps(ERC2) if "/query?" in url else fetch(url)
r2 = R.update(r, LATER, fetch2)
g = [c for c in r2["log"] if c["id"] == "erc:11"][0]
check("merge: a closure that leaves the feed is ended at its last sighting", not g["active"] and g["ended"] == "2026-11-13 14:00" and g["gone"])
a1b = [c for c in r2["log"] if c["id"] == "lcs:A1-1"][0]
check("merge: an open one keeps its first sighting, last seen moves on", a1b["active"] and a1b["first_seen"] == "2026-11-13 14:00" and a1b["last_seen"] == "2026-11-13 14:10")
check("ERC: the service address cached (no second item read)", not any("sharing/rest" in u for u in fetched))

# Caltrans down: everything kept, problem noted
r3 = R.update(r2, LATER + dt.timedelta(minutes=10), lambda u: (_ for _ in ()).throw(OSError("offline")))
check("update: Caltrans down: log kept as is, both problems noted, nothing ended", [c.get("active") for c in r3["log"]] == [c.get("active") for c in r2["log"]]
      and len(r3["problems"]) == 2 and not r3["sources"]["lcs"]["ok"])

# water year pruning
old = {"id": "lcs:old", "source": "Caltrans Lane Closure System", "started": "2026-09-20 10:00", "ended": "2026-09-21 10:00", "active": False}
r4 = R.update({"log": [old] + r2["log"], "sources": r2["sources"]}, LATER, fetch2)
check("prune: closures that ended before Oct 1 dropped", not any(c["id"] == "lcs:old" for c in r4["log"]) and r4["water_year_start"] == "2026-10-01 00:00")

# no county field: the San Mateo box decides
ERC3 = {"fields": [{"name": "FID", "type": "esriFieldTypeOID"}, {"name": "Reason", "type": "esriFieldTypeString"}],
        "features": [{"attributes": {"FID": 1, "Reason": "Mud slide"}, "geometry": {"x": -122.49, "y": 37.59}},
                     {"attributes": {"FID": 2, "Reason": "Mud slide"}, "geometry": {"x": -121.9, "y": 37.3}},
                     {"attributes": {"FID": 3, "Reason": "Flooding", "Status": "Reopened"}, "geometry": {"x": -122.3, "y": 37.5}}]}
ERC3["fields"].append({"name": "Status", "type": "esriFieldTypeString"})
c3, fm3, n3 = R.erc_closures(json.dumps(ERC3), NOW)
check("ERC: no county field: only points inside the San Mateo box; a reopened record skipped", [c["id"] for c in c3] == ["erc:1"] and n3 == 2)
check("matching: Storm/Fire Related Repairs counts, Seasonal Road Closure and Police Activity don't",
      R.is_storm("Storm/Fire Related Repairs") and not R.is_storm("Seasonal Road Closure") and not R.is_storm("Police Activity") and R.is_storm("River Overflow/Flood Area"))
try:
    R.erc_closures(json.dumps({"error": {"code": 400, "message": "bad"}}), NOW)
    check("ArcGIS error body raises", False)
except ValueError:
    check("ArcGIS error body raises", True)

print("\n" + ("All passed" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
