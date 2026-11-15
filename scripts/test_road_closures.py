"""Tests for road_closures.py with made-up Caltrans data in the published LCS format and an ArcGIS layer. Run: python scripts/test_road_closures.py"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import road_closures as R  # noqa: E402
R.CITY_FEEDS = "/nonexistent/city_feeds.csv"   # the Caltrans tests run without city feeds

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
r = R.update({}, NOW, fetch, erc=[""])
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
r2 = R.update(r, LATER, fetch2, erc=[""])
g = [c for c in r2["log"] if c["id"] == "erc:11"][0]
check("merge: a closure that leaves the feed is ended at its last sighting", not g["active"] and g["ended"] == "2026-11-13 14:00" and g["gone"])
a1b = [c for c in r2["log"] if c["id"] == "lcs:A1-1"][0]
check("merge: an open one keeps its first sighting, last seen moves on", a1b["active"] and a1b["first_seen"] == "2026-11-13 14:00" and a1b["last_seen"] == "2026-11-13 14:10")
check("ERC: the service address cached (no second item read)", not any("sharing/rest" in u for u in fetched))

# Caltrans down: everything kept, problem noted
r3 = R.update(r2, LATER + dt.timedelta(minutes=10), lambda u: (_ for _ in ()).throw(OSError("offline")), erc=[""])
check("update: Caltrans down: log kept as is, both problems noted, nothing ended", [c.get("active") for c in r3["log"]] == [c.get("active") for c in r2["log"]]
      and len(r3["problems"]) == 2 and not r3["sources"]["lcs"]["ok"])

# water year pruning
old = {"id": "lcs:old", "source": "Caltrans Lane Closure System", "started": "2026-09-20 10:00", "ended": "2026-09-21 10:00", "active": False}
r4 = R.update({"log": [old] + r2["log"], "sources": r2["sources"]}, LATER, fetch2, erc=[""])
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

# where: watersheds, creeks, side (the County watershed file in data/)
loc = lambda lat, lon: R.locate({"lat": lat, "lon": lon})
c1, c2, c3 = loc(37.4635, -122.4305), loc(37.66, -122.39), loc(37.5045, -122.2545)
check("where: Hwy 92 in Half Moon Bay is Pilarcitos Creek, Coastside", c1["creeks"] == ["pilarcitos"] and c1["side"] == "coast")
check("where: 101 in South San Francisco is Colma Creek, Bayside", c2["creeks"] == ["colma"] and c2["side"] == "bay")
check("where: 101 at Holly St is Pulgas Creek (no monitored creek), Bayside", c3["watersheds"] == ["Pulgas Creek"] and c3["creeks"] == [] and c3["side"] == "bay")
c4 = R.locate({"pts": [[37.515, -122.37], [37.4635, -122.4305]]})
check("where: Hwy 92 from Skyline to Half Moon Bay spans both sides and both creeks", c4["side"] == "both" and c4["creeks"] == ["sanmateo", "pilarcitos"])
check("where: out at sea (beyond 2 km of any watershed) has no place", loc(37.5, -122.7)["side"] is None)
r5 = R.update({}, NOW, fetch, erc=[""])
check("update: every logged closure placed, and the creeks' sides published", all("side" in c for c in r5["log"]) and r5["creek_side"]["pescadero"] == "coast")
a1 = [c for c in r5["log"] if c["id"] == "lcs:A1-1"][0]
check("LCS: begin and end points kept for placing", a1["pts"] == [[37.5, -122.26]])

# city notices (RSS from a CivicPlus site)
RSS = """<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>City of San Bruno - News Flash</title>
<item><title>Crystal Springs Ave closed at El Camino Real due to flooding</title><link>https://www.sanbruno.ca.gov/CivicAlerts.aspx?AID=901</link>
<description>&lt;p&gt;Crystal Springs Avenue is closed between El Camino Real and Elm Ave due to &lt;b&gt;flooding&lt;/b&gt;. Please avoid the area.&lt;/p&gt;</description>
<pubDate>Fri, 13 Nov 2026 19:05:00 GMT</pubDate></item>
<item><title>Free sandbags at the Corporation Yard</title><link>https://www.sanbruno.ca.gov/CivicAlerts.aspx?AID=900</link>
<description>Sandbags are available ahead of the storm.</description><pubDate>Thu, 12 Nov 2026 17:00:00 GMT</pubDate></item>
<item><title>Library closed for Veterans Day</title><link>https://www.sanbruno.ca.gov/CivicAlerts.aspx?AID=899</link>
<description>All city offices closed.</description><pubDate>Wed, 11 Nov 2026 17:00:00 GMT</pubDate></item>
</channel></rss>"""
FEED = {"city": "San Bruno", "url": "https://www.sanbruno.ca.gov/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml", "creeks": ["sanbruno"], "side": "bay"}
ns = R.city_notices(RSS, FEED, NOW)
check("city: only the post about a closure from flooding (not sandbags, not a holiday closure)", len(ns) == 1 and ns[0]["kind"] == "flood")
n0 = ns[0]
check("city: posted time in Pacific, link and plain text kept, placed by the city's row", n0["started"] == "2026-11-13 11:05" and n0["link"].endswith("AID=901")
      and "<" not in n0["what"] and n0["creeks"] == ["sanbruno"] and n0["side"] == "bay" and n0["notice"])
r6 = R.update({}, NOW, lambda u: RSS if "sanbruno" in u else fetch(u), feeds=[FEED])
c6 = [c for c in r6["log"] if c.get("notice")]
check("update: the notice logged (not active), its place kept (not re-placed by watershed), source ok",
      len(c6) == 1 and not c6[0]["active"] and c6[0]["creeks"] == ["sanbruno"] and r6["sources"]["city:San Bruno:1"]["ok"])
ATOM = """<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Road closed: storm damage on Skyline</title><link href="https://x.example/1"/>
<updated>2026-11-13T20:00:00Z</updated><summary>Tree down after the storm.</summary></entry></feed>"""
na = R.city_notices(ATOM, FEED, NOW)
check("city: Atom feeds too", len(na) == 1 and na[0]["started"] == "2026-11-13 12:00" and na[0]["kind"] == "storm")
r7 = R.update({}, NOW, lambda u: (_ for _ in ()).throw(OSError("down")) if "sanbruno" in u else fetch(u), feeds=[FEED])
check("update: a city feed down is a problem, Caltrans still read", any("San Bruno" in p for p in r7["problems"]) and r7["sources"]["lcs"]["ok"])
check("city_feeds.csv: San Bruno's two CivicPlus feeds", [f["city"] for f in R.read_feeds(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups", "city_feeds.csv"))] == ["San Bruno", "San Bruno"])

# finding the Emergency Road Closures layer when the item has no url
HUB = {"data": {"attributes": {"url": "https://services.example.com/arcgis/rest/services/ERC/FeatureServer", "layer": {"id": 2}}}}
svc = R.erc_service(lambda u: json.dumps({"error": {"code": 403, "message": "You do not have permissions"}}) if "sharing" in u else json.dumps(HUB))
check("ERC: item refused: ArcGIS Hub's record of the dataset gives the layer", svc == "https://services.example.com/arcgis/rest/services/ERC/FeatureServer/2")
WM = {"type": "Web Map"}
svc2 = R.erc_service(lambda u: json.dumps({"operationalLayers": [{"url": "https://s.example/MapServer/3"}]}) if "/data?" in u else json.dumps(WM) if "sharing" in u else "{}")
check("ERC: a web map item: its first layer", svc2 == "https://s.example/MapServer/3")
try:
    R.erc_service(lambda u: json.dumps({"type": "Hub Page"}) if "sharing" in u else "{}")
    check("ERC: no way found: the reasons in the error", False)
except ValueError as e:
    check("ERC: no way found: the reasons in the error", "Hub Page" in str(e) and "hub: no url" in str(e))

r8 = R.update({}, NOW, fetch)
check("Emergency Road Closures off (the dataset is gone): not read, no problem shown", "erc" not in r8["sources"] and not any("Emergency" in p for p in r8["problems"])
      and not any("sharing/rest" in u for u in fetched[-3:]))

print("\n" + ("All passed" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
