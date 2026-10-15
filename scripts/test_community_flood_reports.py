"""
Checks for scripts/fetch_community_flood_reports.py (flood reports). Run from the repo:  python scripts/test_community_flood_reports.py
No network: builds the public reports from made-up ArcGIS records, including forged and hostile ones.
"""
import datetime as dt
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import SETTINGS  # noqa: E402
from fetch_community_flood_reports import PACIFIC, build, clean_summary, reencode  # noqa: E402

NOW = dt.datetime(2026, 12, 23, 9, 0, tzinfo=PACIFIC)
S = {k: v[0] for k, v in SETTINGS.items()}
EDIT = {"editorField": "Editor", "creationDateField": "CreationDate"}
STAFF = {"jdoe_oneshoreline"}
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    assert cond, msg


def ms(t):
    return int(t.timestamp() * 1000)


def feat(n, status="approved", editor="JDoe_OneShoreline", lat=37.5207, lon=-122.2758, hours_ago=3, **kw):
    a = {"objectid": n, "globalid": "{%08d-AAAA-BBBB-CCCC-DDDDDDDDDDDD}" % n, "review_status": status, "editor": editor,
         "observed_at": ms(NOW - dt.timedelta(hours=hours_ago)), "report_type": "street", "depth": "ankle_knee",
         "public_summary": "Water across Old County Rd near the Caltrain crossing.", "publish_photo": "no",
         "note": "my house at 123 Main St, call me 650-555-1212", "contact": "me@example.com", "creationdate": None}
    a.update(kw)
    return {"attributes": a, "geometry": {"x": lon, "y": lat}}


got_photo = []


def photo(oid, gid):
    got_photo.append(oid)
    return "a" * 24 + ".jpg"


feats = [
    feat(1),
    feat(2, editor=None),                                   # forged: public sent review_status=approved
    feat(3, editor=""),                                     # forged, empty editor
    feat(4, editor="someone_else"),                         # approved by an account not on the list
    feat(5, status="new"),
    feat(6, status="Approved ", publish_photo="yes"),       # spacing/case tolerated; photo published
    feat(7, lat=34.05, lon=-118.25),                        # Los Angeles: outside the county
    feat(8, hours_ago=24 * 400),                            # older than REPORTS_MAX_AGE_DAYS
    feat(9, hours_ago=-5),                                  # in the future
    feat(10, report_type="<img src=x onerror=alert(1)>", depth="waist"),
    feat(11, public_summary="See https://evil.example/x or www.evil.example, email a@b.co, call (650) 555-1212.<script>"),
    feat(12, observed_at=None),
    {"attributes": {"objectid": 13, "review_status": "approved", "editor": "jdoe_oneshoreline"}, "geometry": None},
]
reports, skipped = build(feats, EDIT, STAFF, S, NOW, photo=photo)
ids = {r["id"] for r in reports}
check(len(reports) == 4, f"published 1, 6, 10, 11 only: {[r['summary'][:20] for r in reports]} {skipped}")
check(skipped.get("not approved by a listed staff account") == 3, f"forged/other-account approvals rejected: {skipped}")
check(skipped.get("outside San Mateo County") == 1 and skipped.get("too old or in the future") == 2, f"{skipped}")
check(skipped.get("no location") == 1 and skipped.get("no date") == 1, f"{skipped}")
for r in reports:
    check(set(r) == {"id", "observed", "type", "depth", "summary", "lat", "lon", "photo"}, f"only public fields: {r}")
    check("note" not in str(r) and "555" not in str(r) and "@" not in str(r) and "Main St" not in str(r), f"no private text: {r}")
    check(abs(r["lat"] - 37.5207) <= 0.00076 and abs(r["lon"] + 122.2758) <= 0.00076 and (r["lat"], r["lon"]) != (37.5207, -122.2758),
          f"location snapped to the grid: {r}")
    check(len(r["id"]) == 12 and "{" not in r["id"], f"opaque id: {r}")
r10 = [r for r in reports if r["type"] == "other"]
check(len(r10) == 1 and r10[0]["depth"] == "unknown", "unknown type/depth mapped to other/unknown")
r11 = [r for r in reports if "See" in r["summary"]][0]["summary"]
check("http" not in r11 and "www" not in r11 and "@" not in r11 and "555" not in r11, f"links, email, phone removed: {r11}")
check(got_photo == [6] and sum(bool(r["photo"]) for r in reports) == 1, f"photo only where staff said yes: {got_photo}")
check(reports[0]["observed"] >= reports[-1]["observed"], "newest first")
check(reports[0]["observed"] == "2026-12-23 06:00", f"Pacific time: {reports[0]['observed']}")
check(len(clean_summary("x " * 400)) <= 281, "summary capped")
check(clean_summary("Line‮one\x00two") == "Line one two", "control/bidi characters removed")
S2 = dict(S, REPORTS_MAX_PHOTOS=0)
got_photo.clear()
build([feat(6, publish_photo="yes")], EDIT, STAFF, S2, NOW, photo=photo)
check(got_photo == [], "photo limit 0 = no photos")
check(build(feats, {}, STAFF, S, NOW)[0] == [], "no editor tracking = nothing published")
check(build(feats, EDIT, set(), S, NOW)[0] == [], "empty staff list = nothing published")

# Photos: location and camera data removed, size limited
try:
    from PIL import Image
    im = Image.new("RGB", (3000, 2000), (40, 90, 160))
    exif = Image.Exif()
    exif[0x010F] = "PhoneMaker"                           # camera make
    exif[0x0112] = 6                                      # orientation: rotate 90
    gps = {1: "N", 2: (37.0, 31.0, 14.0), 3: "W", 4: (122.0, 16.0, 33.0)}
    exif[0x8825] = gps
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif)
    out = Image.open(io.BytesIO(reencode(buf.getvalue())))
    check(not out.getexif() and "exif" not in out.info, f"no EXIF left: {dict(out.getexif())} {list(out.info)}")
    check(max(out.size) <= 1280 and out.size[1] > out.size[0], f"resized and turned upright: {out.size}")
    try:
        reencode(b"<html>not an image</html>")
        check(False, "non-image accepted")
    except Exception:  # noqa: BLE001
        check(True, "")
except ImportError:
    print("(Pillow not installed: photo checks skipped)")

print(f"fetch_community_flood_reports: {checks} checks passed")
