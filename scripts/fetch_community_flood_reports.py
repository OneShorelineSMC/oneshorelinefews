"""
Flood reports: publish STAFF-APPROVED reports only, cleaned up for the public map (community_flood_reports.json + community_flood_reports/*.jpg).

People send reports through an ArcGIS Survey123 form (CommunityFloodReports.html). Staff review them in ArcGIS Online and set
review_status = approved and write a short public summary. This script reads the approved-only layer view and
publishes, for each report:
  date and time seen, type, depth (fixed lists only), the STAFF summary (never the reporter's own words),
  the location snapped to a grid of about 150 m, and a photo only if staff set publish_photo = yes
  (re-encoded: no location or camera data, at most 1280 px).
Nothing else from the layer is published: no notes, contact details, exact points, names or ids.

Setup (COMMUNITY_FLOOD_REPORTS_SETUP.md): GitHub repo Settings > Secrets and variables > Actions
  secret   ARCGIS_API_KEY         API key whose credentials can read only the approved-only view
  variable REPORTS_LAYER_URL      https://services….arcgis.com/…/FeatureServer/0 of that view
  variable REPORTS_STAFF_EDITORS  ArcGIS usernames allowed to approve, separated by commas
Not set up yet = nothing happens (the previous community_flood_reports.json, if any, is kept).

Defenses against fake approvals: the public form can only ADD records, but someone could still send
review_status = approved straight to the service. A report is published only if the layer's editor-tracking
"last edited by" field (set by ArcGIS, can't be sent by the public) is one of REPORTS_STAFF_EDITORS.

Usage:  python fetch_community_flood_reports.py OUT_DIR [--min-age MINUTES]
"""
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import load_settings  # noqa: E402

PACIFIC = ZoneInfo("America/Los_Angeles")
TIMEOUT = 30
LAYER_RE = re.compile(r"^https://[a-z0-9-]+(\.[a-z0-9-]+)*\.arcgis\.com/[A-Za-z0-9_./-]+/FeatureServer/\d+$")
# San Mateo County with a little margin; reports outside are dropped
AREA = {"lat": (37.05, 37.75), "lon": (-122.60, -122.05)}
GRID = 0.0015                       # degrees: about 170 m north-south, 130 m east-west
TYPES = {"street", "building", "road_closed", "creek", "shoreline", "other"}
DEPTHS = {"shallow", "ankle_knee", "above_knee", "unknown"}
FIELDS = {"observed": "observed_at", "type": "report_type", "depth": "depth", "status": "review_status",
          "summary": "public_summary", "photo": "publish_photo"}
MAX_SUMMARY = 280
MAX_PHOTO_BYTES = 12 * 1024 * 1024
PHOTO_PX = 1280


def now_pacific():
    return dt.datetime.now(PACIFIC)


def request(url, key, params=None, raw=False):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"X-Esri-Authorization": "Bearer " + key, "User-Agent": "OneShoreline-FEWS"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        body = r.read(MAX_PHOTO_BYTES + 1)
    if raw:
        return body
    data = json.loads(body)
    if isinstance(data, dict) and "error" in data:   # ArcGIS reports errors with HTTP 200
        e = data["error"]
        raise RuntimeError(f"ArcGIS error {e.get('code')}: {e.get('message')}")
    return data


def clean_summary(s):
    """Staff-written summary as plain text: no links, emails or phone numbers, at most MAX_SUMMARY characters."""
    s = unicodedata.normalize("NFC", str(s or ""))
    s = "".join(ch if unicodedata.category(ch)[0] != "C" else " " for ch in s)
    s = re.sub(r"(https?://|www\.)\S+", "", s, flags=re.I)
    s = re.sub(r"\S+@\S+\.\S+", "", s)
    s = re.sub(r"\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > MAX_SUMMARY:
        s = s[:MAX_SUMMARY].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return s


def snap(v):
    return round(round(v / GRID) * GRID, 5)


def yes(v):
    return str(v or "").strip().lower() in ("yes", "true", "1", "y")


def reencode(body):
    """Image bytes -> JPEG bytes with no metadata (no location, camera or time), upright, at most PHOTO_PX."""
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 60_000_000
    im = Image.open(io.BytesIO(body))
    im.verify()
    im = Image.open(io.BytesIO(body))
    im = ImageOps.exif_transpose(im).convert("RGB")   # turn it upright, then drop every tag
    im.thumbnail((PHOTO_PX, PHOTO_PX))
    clean = Image.new("RGB", im.size)
    clean.paste(im)
    buf = io.BytesIO()
    clean.save(buf, "JPEG", quality=80, optimize=True)
    return buf.getvalue()


def photo_file(layer, key, oid, gid, out_dir, have):
    """First image attached to the report, re-encoded without metadata. Returns the file name or None."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("Pillow isn't installed; photos skipped.")
        return None
    info = request(f"{layer}/{oid}/attachments", key, {"f": "json"})
    for a in info.get("attachmentInfos") or []:
        if not str(a.get("contentType", "")).startswith("image/") or (a.get("size") or 0) > MAX_PHOTO_BYTES:
            continue
        name = hashlib.sha256(f"{gid}/{a.get('id')}".encode()).hexdigest()[:24] + ".jpg"
        if name in have:   # published before: don't download again
            return name
        body = request(f"{layer}/{oid}/attachments/{int(a['id'])}", key, raw=True)
        if len(body) > MAX_PHOTO_BYTES:
            continue
        try:
            data = reencode(body)
        except Exception as e:  # noqa: BLE001 - a bad image never stops the rest
            print(f"photo for one report skipped ({type(e).__name__})")
            continue
        with open(os.path.join(out_dir, name), "wb") as f:
            f.write(data)
        return name
    return None


def build(features, edit_fields, staff, settings, now, photo=None):
    """Turn layer features into public reports. photo(oid, gid) -> file name or None. Returns (reports, skipped)."""
    max_age = dt.timedelta(days=settings["REPORTS_MAX_AGE_DAYS"])
    max_photos = int(settings["REPORTS_MAX_PHOTOS"])
    editor_f = (edit_fields.get("editorField") or "").lower()
    created_f = (edit_fields.get("creationDateField") or "").lower()
    out, skipped, photos = [], {}, 0

    def skip(why):
        skipped[why] = skipped.get(why, 0) + 1

    for f in features:
        a, g = f.get("attributes") or {}, f.get("geometry") or {}
        if str(a.get(FIELDS["status"]) or "").strip().lower() != "approved":
            skip("not approved")
            continue
        if not editor_f or str(a.get(editor_f) or "").strip().lower() not in staff:
            skip("not approved by a listed staff account")
            continue
        try:
            lat, lon = float(g["y"]), float(g["x"])
        except (KeyError, TypeError, ValueError):
            skip("no location")
            continue
        if not (AREA["lat"][0] <= lat <= AREA["lat"][1] and AREA["lon"][0] <= lon <= AREA["lon"][1]):
            skip("outside San Mateo County")
            continue
        ms = a.get(FIELDS["observed"]) or (a.get(created_f) if created_f else None)
        if not isinstance(ms, (int, float)):
            skip("no date")
            continue
        seen = dt.datetime.fromtimestamp(ms / 1000, PACIFIC)
        if seen > now + dt.timedelta(hours=1) or now - seen > max_age:
            skip("too old or in the future")
            continue
        typ = str(a.get(FIELDS["type"]) or "").strip().lower()
        depth = str(a.get(FIELDS["depth"]) or "").strip().lower()
        gid, oid = str(a.get("globalid") or a.get("objectid")), a.get("objectid")
        r = {"id": hashlib.sha256(gid.encode()).hexdigest()[:12],
             "observed": seen.strftime("%Y-%m-%d %H:%M"),
             "type": typ if typ in TYPES else "other",
             "depth": depth if depth in DEPTHS else "unknown",
             "summary": clean_summary(a.get(FIELDS["summary"])),
             "lat": snap(lat), "lon": snap(lon), "photo": None}
        if photo and yes(a.get(FIELDS["photo"])) and photos < max_photos and isinstance(oid, int):
            try:
                r["photo"] = photo(oid, gid)
            except Exception as e:  # noqa: BLE001
                print(f"photo lookup failed for one report ({type(e).__name__})")
            photos += bool(r["photo"])
        out.append(r)
    out.sort(key=lambda r: r["observed"], reverse=True)
    return out, skipped


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    out_dir = args[0]
    min_age = float(args[args.index("--min-age") + 1]) if "--min-age" in args else 0
    layer = os.environ.get("REPORTS_LAYER_URL", "").strip().rstrip("/")
    key = os.environ.get("ARCGIS_API_KEY", "").strip()
    staff = {s.strip().lower() for s in os.environ.get("REPORTS_STAFF_EDITORS", "").split(",") if s.strip()}
    if not layer or not key:
        print("Flood reports aren't set up yet (REPORTS_LAYER_URL / ARCGIS_API_KEY); nothing to do.")
        return
    if not LAYER_RE.match(layer):
        sys.exit("REPORTS_LAYER_URL must look like https://services….arcgis.com/…/FeatureServer/0")
    if not staff:
        sys.exit("REPORTS_STAFF_EDITORS is empty: no report can be published until it lists the staff accounts.")

    path = os.path.join(out_dir, "community_flood_reports.json")
    photo_dir = os.path.join(out_dir, "community_flood_reports")
    now = now_pacific()
    try:
        with open(path, encoding="utf-8") as f:
            prev = json.load(f)
        age = (now.replace(tzinfo=None) - dt.datetime.strptime(prev["generated"], "%Y-%m-%d %H:%M")).total_seconds() / 60
        if min_age and age < min_age:
            print(f"community_flood_reports.json is {age:.0f} min old (refreshes every {min_age:.0f}); skipping this run.")
            return
    except (OSError, ValueError, KeyError):
        pass

    settings, problems = load_settings()
    for p in problems:
        print(p)
    info = request(layer, key, {"f": "json"})
    edit_fields = info.get("editFieldsInfo") or {}
    if not edit_fields.get("editorField"):
        sys.exit("The reports layer has no editor tracking, so staff approvals can't be checked. Turn on editor tracking.")
    fields = [FIELDS[k] for k in FIELDS] + [edit_fields["editorField"], "objectid", "globalid"]
    if edit_fields.get("creationDateField"):
        fields.append(edit_fields["creationDateField"])
    names = {fd["name"].lower(): fd["name"] for fd in info.get("fields") or []}
    out_fields = sorted({names.get(f.lower(), f) for f in fields if f.lower() in names})
    missing = [f for f in FIELDS.values() if f.lower() not in names]
    if missing:
        sys.exit("The reports layer is missing fields: " + ", ".join(missing) + " (see COMMUNITY_FLOOD_REPORTS_SETUP.md)")

    feats = request(f"{layer}/query", key, {"where": f"{names[FIELDS['status']]}='approved'", "outFields": ",".join(out_fields),
                                            "returnGeometry": "true", "outSR": "4326", "resultRecordCount": "2000", "f": "json"})
    # Field names come back as the layer spells them; use lower case from here on
    features = [{"attributes": {k.lower(): v for k, v in (f.get("attributes") or {}).items()}, "geometry": f.get("geometry")}
                for f in feats.get("features") or []]

    os.makedirs(photo_dir, exist_ok=True)
    have = set(os.listdir(photo_dir))
    reports, skipped = build(features, edit_fields, staff, settings, now,
                             photo=lambda oid, gid: photo_file(layer, key, oid, gid, photo_dir, have))
    used = {r["photo"] for r in reports if r["photo"]}
    for name in have - used:   # photos of reports that were un-approved or aged out
        os.remove(os.path.join(photo_dir, name))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"generated": now.strftime("%Y-%m-%d %H:%M"), "count": len(reports), "reports": reports}, f, indent=1)
    print(f"Published {len(reports)} approved flood reports ({len(used)} with photos)."
          + ("" if not skipped else " Not published: " + ", ".join(f"{n} {k}" for k, n in skipped.items()) + "."))


if __name__ == "__main__":
    main()
