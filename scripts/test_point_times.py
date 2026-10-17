"""
Checks for the UTC time on each creek point, USGS qualifier codes and creeks_7day.json (scripts/fetch_onerain.py).
Run from the repo:  python scripts/test_point_times.py     (no network)
"""
import datetime as dt
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_onerain as F  # noqa: E402

checks = 0


def check(cond, msg):
    global checks
    checks += 1
    assert cond, msg


T = lambda s: dt.datetime.strptime(s, "%Y-%m-%d %H:%M")  # noqa: E731

# Daylight saving ends Sun Nov 1, 2026: 1:00-1:59 AM happens twice (PDT, then PST)
PAGE = [(T("2026-11-01 02:15"), 0.04), (T("2026-11-01 01:45"), 0.03), (T("2026-11-01 01:15"), 0.02),   # PST
        (T("2026-11-01 01:45"), 0.01), (T("2026-11-01 01:15"), 0.00), (T("2026-11-01 00:45"), 0.05)]   # PDT


class FakeSession:
    def get(self, url):
        return url


def run(pages, start="2026-10-31 12:00", end="2026-11-01 03:00"):
    """fetch_sensor with the page reader replaced: each 'page' is a list of (time, value) in page order."""
    it = iter(pages)
    F.parse_latest = lambda page: None
    F.parse_readings = lambda page: next(it, [])
    nxt = iter(range(1, 100))
    F.next_page = lambda page: f"https://example/p{next(nxt)}"
    return F.fetch_sensor(FakeSession(), {"site_id": 1, "site": "s", "device_id": 2, "device": "d"},
                          T(start), T(end))[0]


want = [("2026-11-01 00:45", "2026-11-01T07:45Z"), ("2026-11-01 01:15", "2026-11-01T08:15Z"),
        ("2026-11-01 01:45", "2026-11-01T08:45Z"), ("2026-11-01 01:15", "2026-11-01T09:15Z"),
        ("2026-11-01 01:45", "2026-11-01T09:45Z"), ("2026-11-01 02:15", "2026-11-01T10:15Z")]
pts = run([PAGE])
check([(p[0], p[2]) for p in pts] == want, f"newest-first page, repeated hour kept twice, in order: {pts}")
check([p[1] for p in pts] == [0.05, 0.0, 0.01, 0.02, 0.03, 0.04], f"values stay with their readings: {pts}")
pts = run([PAGE[:2], PAGE[2:4], PAGE[4:]])
check([(p[0], p[2]) for p in pts] == want, f"same across several pages: {pts}")
pts = run([PAGE[::-1]])
check([(p[0], p[2]) for p in pts] == want, f"oldest-first page works too: {pts}")
pts = run([[(T("2026-11-01 01:30"), 0.1)]])
check(pts[0][2] == "2026-11-01T09:30Z", f"a lone 1:30 AM on a newest-first page is the later (PST) one: {pts}")
pts = run([[(T("2026-10-15 09:00"), 1.0), (T("2026-10-15 08:45"), 1.1)]], "2026-10-15 00:00", "2026-10-15 10:00")
check([p[2] for p in pts] == ["2026-10-15T15:45Z", "2026-10-15T16:00Z"] and len(pts[0]) == 3, f"ordinary day, PDT: {pts}")
check(F.utc_str(T("2026-12-01 09:00").replace(tzinfo=F.TZ)) == "2026-12-01T17:00Z", "winter, PST")

# USGS qualifier codes
check(F.usgs_codes("Provisional", "") == "P", "provisional")
check(F.usgs_codes("Approved", "") == "A", "approved")
check(F.usgs_codes("Provisional", "P e") == "P e", "WaterServices codes kept as they are")
check(F.usgs_codes("Provisional", "Eqp") == "P Eqp", "Water Data API: status + qualifier")
check(F.usgs_codes("", "") == "", "nothing known = empty")

import fetch_usgs as U  # noqa: E402
U.pull_ogc = lambda site, t0, t1: {"00065": [("2026-11-01T08:45:00Z", "3.70", "ft", "Provisional", ""),
                                             ("2026-11-01T09:45:00Z", "3.72", "ft", "Provisional", "e")]}
pts, latest, _ = F.fetch_usgs_gauge({"usgs_site": "11162570"}, T("2026-10-31 12:00"), T("2026-11-01 03:00"))
check(pts == [["2026-11-01 01:45", 3.7, "2026-11-01T08:45Z", "P"], ["2026-11-01 01:45", 3.72, "2026-11-01T09:45Z", "P e"]],
      f"USGS: both 1:45 AMs kept, UTC and codes: {pts}")
check(latest == ["2026-11-01 01:45", 3.72, "2026-11-01T09:45Z"], f"latest is [time, value, UTC] (Oct 17, 2026), no codes: {latest}")

# creeks_7day.json
with tempfile.TemporaryDirectory() as d:
    path = os.path.join(d, "creeks_7day.json")
    now = dt.datetime(2026, 10, 15, 16, 0, tzinfo=dt.timezone.utc)
    old_t = (now - dt.timedelta(days=8)).strftime("%Y-%m-%dT%H:%MZ")
    mid_t = (now - dt.timedelta(days=3)).strftime("%Y-%m-%dT%H:%MZ")
    with open(path, "w") as f:
        json.dump({"sensors": {"col_stage": {"name": "Stage", "kind": "stage", "unit": "ft",
                                             "points": [["x", 1.0, old_t], ["y", 2.0, mid_t], ["2026-10-15 08:00", 3.0]]},
                               "gone": {"name": "Old", "kind": "stage", "unit": "ft", "points": [["z", 9.0, mid_t]]}}}, f)
    result = {"generated": "2026-10-15 09:00:00", "generated_utc": "2026-10-15T16:00:00Z",
              "sensors": {"col_stage": {"name": "Stage", "kind": "stage", "unit": "ft", "points": [
                  ["2026-10-15 08:00", 3.5, "2026-10-15T15:00Z"], ["2026-10-15 08:15", 3.6, "2026-10-15T15:15Z"]]},
                  "new": {"name": "New", "kind": "rain_increment", "unit": "in", "points": []}}}
    F.write_history(result, path, now=now)
    h = json.load(open(path))
    cs = h["sensors"]["col_stage"]["points"]
    check([p[1] for p in cs] == [2.0, 3.5, 3.6],
          f"older than 7 days dropped; a point with the same UTC time takes the newest value: {cs}")
    check(cs[0][1] == 2.0 and all(len(p) >= 3 or p[0] == "2026-10-15 08:00" for p in cs), f"{cs}")
    check("gone" in h["sensors"] and "new" not in h["sensors"], "sensors with points kept for the 7 days; empty ones left out")
    check(h["days"] == 7 and h["generated_utc"] == "2026-10-15T16:00:00Z", f"{ {k: h[k] for k in h if k != 'sensors'} }")

# 'latest' carries its UTC time (Oct 17, 2026): from the reading with the same Pacific time (the second 1:45 AM in
# November is PST), otherwise from its Pacific time; an old 2-element 'latest' gets one; None stays None
pts = [["2026-11-01 01:45", 0.01, "2026-11-01T08:45Z"], ["2026-11-01 01:45", 0.03, "2026-11-01T09:45Z"]]
check(F.latest_utc(["2026-11-01 01:45", 0.03], pts) == ["2026-11-01 01:45", 0.03, "2026-11-01T09:45Z"], "latest takes the newest matching point's UTC")
check(F.latest_utc(["2026-10-17 07:45", 0.17], []) == ["2026-10-17 07:45", 0.17, "2026-10-17T14:45Z"], "latest without a matching point: Pacific time converted")
check(F.latest_utc(["2026-10-17 07:45", 0.17, "2026-10-17T14:45Z"], []) == ["2026-10-17 07:45", 0.17, "2026-10-17T14:45Z"], "UTC kept")
check(F.latest_utc(None, pts) is None, "no latest")
import creek_signals as CSg  # noqa: E402
ser, ok = CSg.utc_series([["2026-11-01 01:15", 0.0, "2026-11-01T08:15Z"]], ["2026-11-01 01:05", 0.5, "2026-11-01T09:05Z"])
check(ok and ser[-1][0] == dt.datetime(2026, 11, 1, 9, 5) and ser[-1][1] == 0.5,
      f"utc_series uses latest's own UTC (1:05 AM PST after 1:15 AM PDT is newer, not older): {ser}")

print(f"point times: {checks} checks passed")
