"""
The creeks shown on the kiosk's Creeks tab, the phone page (Creeks.html) and the home page, and the alert
levels drawn on the site map. FLOOD THRESHOLDS ARE IN thresholds.csv (top of the repo), not here. The pages
read everything from the published data file, so changes here show up everywhere on the next data run
(about 5 minutes after you commit).

Each creek has:
  id      short code used in links, e.g. Creeks.html#atherton
  name    shown on headings and the alert strip
  short   shown on the creek buttons (keep it to one or two short words)
  rain_windows   the rain totals shown, in minutes (60 = 1 hr, 1440 = 24 hr); match the creek's OneRain dashboard
  rain_running   optional: a graph of the running rain total over "minutes", with a line at "line" inches
  intro   one sentence under the creek's name
  tide    NOAA station shown under the creek: "9414750" Alameda or "9414523" Redwood City
  note    optional text shown with the graphs (e.g. what the threshold colors mean)
  stages  creek water-level gauges, upstream first
  rain    rain gauges, upper watershed first
  (flood thresholds and rain triggers for every gauge are in thresholds.csv)

Each gauge needs its OneRain sensor link details: open the sensor's page on OneRain (Sites > site > sensor)
and copy site_id, site, device_id and device from the address bar.

"""

import csv
import os

LEVEL_COLORS = {1: "#e6c200", 2: "#e07b00", 3: "#c62828", 4: "#9c27b0"}
THRESHOLDS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "thresholds.csv")


CREEKS = [
    {
        "id": "sanbruno",
        "name": "San Bruno Creek",
        "short": "San Bruno",
        "rain_windows": [15, 30, 60, 180, 1440],   # flashy creek: short windows too (Summer, Oct 13)
        "intro": "Creek level at First Avenue in South San Francisco / San Bruno, rain in the upper and lower "
                 "watershed, and the Bay tide at Alameda. The creek at First Avenue rises and falls with the tide.",
        "tide": "9414750",
        "note": "",
        "stages": [
            {"key": "stage", "label": "First Avenue", "site_name": "San Bruno Creek at First Avenue", "number": "41102",
             "site_id": 11, "site": "fe06588c-e5e6-4016-8a8f-2ba1f040636e",
             "device_id": 3, "device": "e481d107-65bb-4107-89ab-48484eb0e188",
             "reports": "on change",   # reports only when the level changes, so silence isn't always an outage
             "note": ""},
        ],
        "rain": [
            {"key": "rain_mountain", "label": "San Bruno Mountain", "where": "upper watershed", "number": "41200",
             "site_id": 3, "site": "e5d4db4f-0a98-4825-aa98-fa327ed9cfa8",
             "device_id": 2, "device": "2a34c20c-eb4e-4337-801c-5341296fcb30"},
            {"key": "rain_first_ave", "label": "First Avenue", "where": "lower watershed", "number": "41102",
             "site_id": 11, "site": "fe06588c-e5e6-4016-8a8f-2ba1f040636e",
             "device_id": 5, "device": "410fdb23-37d0-43aa-8a67-616e08323774"},
        ],
    },
    {
        "id": "atherton",
        "name": "Atherton Channel",
        "short": "Atherton",
        "rain_windows": [30, 60, 1440],
        "intro": "Channel levels at Alameda de las Pulgas and just upstream of the Caltrain crossing, rain at "
                 "Caltrain, and the Bay tide at Redwood City. Thresholds are for the community downstream of "
                 "the Caltrain crossing.",
        "tide": "9414523",
        "note": "Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; "
                "Flood Warning = 100% (flooding likely).",
        "stages": [
            {"key": "ath_alameda", "label": "Alameda de las Pulgas", "site_name": "Atherton Channel at Alameda de las Pulgas",
             "number": "41107", "site_id": 48, "site": "222db05c-ef0a-4720-b2c1-aaba882205f8",
             "device_id": 5, "device": "24188afc-3ba7-498b-b865-c186ddd1f7f5",
             "reports": "interval",
             "note": ""},
            {"key": "ath_caltrain", "label": "Upstream of Caltrain", "site_name": "Atherton Channel upstream of CalTrain",
             "number": "41106", "site_id": 14, "site": "a63a9e54-703b-43b1-8286-6cabbaae7fa1",
             "device_id": 4, "device": "b1b9cc5f-9ad6-498b-96cb-fc299b4eab79",
             "reports": "on change",
             "note": "The probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow."},
        ],
        "rain": [
            {"key": "ath_rain", "label": "Caltrain", "where": "upstream of Caltrain", "number": "41106",
             "site_id": 14, "site": "a63a9e54-703b-43b1-8286-6cabbaae7fa1",
             "device_id": 3, "device": "d301732b-ca6b-44d6-a1d6-ffb421967266"},
        ],
    },
]


CREEKS.append({
    "id": "belmont",
    "name": "Belmont Creek",
    "short": "Belmont",
    "rain_windows": [30, 60, 240, 1440],
    "rain_running": {"gauge": "bel_rain", "minutes": 240, "label": "4-hour rain (in)"},   # trigger line comes from thresholds.csv
    "intro": "Creek level at Old County Road, rain at Old County Road, and the Bay tide at Redwood City. Thresholds "
             "are for the Harbor Industrial Area community downstream of the Caltrain crossing. Flooding is likely "
             "if 30-minute rain exceeds 0.20 inches, or if 4-hour rain exceeds 0.42 inches and the tide is high.",
    "tide": "9414523",
    "note": "Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; "
            "Flood Warning = 100% (flooding likely).",
    "stages": [
        {"key": "bel_stage", "label": "Old County Road", "site_name": "Belmont Creek at Old County Rd", "number": "41104",
         "site_id": 2, "site": "25fd9d56-e3ea-4ff9-a067-b3e99cc5c1fe",
         "device_id": 1, "device": "5c101ccb-75e1-4c68-a983-4b8c78913c03",
         "reports": "on change",
         "note": ""},
    ],
    "rain": [
        {"key": "bel_rain", "label": "Old County Road", "where": "lower watershed", "number": "41104",
         "site_id": 2, "site": "25fd9d56-e3ea-4ff9-a067-b3e99cc5c1fe",
         "device_id": 4, "device": "4002d654-cd0a-4e0f-a178-83ea5ea84566"},
    ],
})


CREEKS.append({
    "id": "colma",
    "name": "Colma Creek",
    "short": "Colma",
    "rain_windows": [60, 360, 1440],
    "intro": "Creek level and rain at Orange Memorial Park in South San Francisco, and the Bay tide at Alameda. "
             "Thresholds are for the community downstream of Orange Memorial Park.",
    "tide": "9414750",
    "note": "Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; "
            "Flood Warning = 100% (flooding likely).",
    "stages": [
        {"key": "col_stage", "label": "Orange Memorial Park", "site_name": "Colma Creek at Orange Memorial Park",
         "number": "41101", "site_id": 12, "site": "32e8ebb1-4c9c-460a-a4cd-58903b96f347",
         "device_id": 5, "device": "dbbbcf6d-6a38-44a5-a90b-7077db13c5c2",
         "reports": "interval",
         "note": ""},
    ],
    "rain": [
        {"key": "col_rain", "label": "Orange Memorial Park", "where": "lower watershed", "number": "41101",
         "site_id": 12, "site": "32e8ebb1-4c9c-460a-a4cd-58903b96f347",
         "device_id": 4, "device": "cc7e3be8-a663-4bb9-9137-fe252166c71f"},
    ],
})

# Order of the creek buttons: north to south
_ORDER = ["colma", "sanbruno", "belmont", "atherton"]
CREEKS.sort(key=lambda c: _ORDER.index(c["id"]) if c["id"] in _ORDER else len(_ORDER))


def _window(minutes):
    return f"{minutes}-minute" if minutes < 60 else f"{minutes // 60}-hour"


def load_thresholds(path=THRESHOLDS_CSV):
    """Read thresholds.csv into CREEKS. Returns a list of problems; if there are any, nothing is applied
    (the data job then keeps the last good thresholds, so a typo can't blank or mis-color the screens)."""
    gauges = {}
    for c in CREEKS:
        for g in c["stages"]:
            gauges[g["key"]] = (c, "stage", g)
        for g in c["rain"]:
            gauges[g["key"]] = (c, "rain", g)
    stage, triggers, errors = {}, {}, []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        return [f"can't read thresholds.csv: {e}"]
    for n, r in enumerate(rows, start=2):   # row 1 is the header
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if not any(r.values()):
            continue
        where = f"thresholds.csv row {n}"
        c_id, key, typ = r.get("creek", ""), r.get("gauge", ""), r.get("type", "").lower()
        if key not in gauges:
            errors.append(f"{where}: unknown gauge '{key}' (see the gauge keys in scripts/creek_config.py)"); continue
        creek, kind, _ = gauges[key]
        if c_id != creek["id"]:
            errors.append(f"{where}: gauge '{key}' belongs to creek '{creek['id']}', not '{c_id}'"); continue
        if typ not in ("stage", "rain") or (typ == "stage") != (kind == "stage"):
            errors.append(f"{where}: type should be '{kind}' for gauge '{key}'"); continue
        try:
            level = int(r.get("level", ""))
            value = float(r.get("value", ""))
            assert level in LEVEL_COLORS and value > 0
        except (ValueError, AssertionError):
            errors.append(f"{where}: level must be 1-4 and value a positive number"); continue
        name = r.get("name") or {1: "Flood Monitoring", 2: "Flood Watch", 3: "Flood Warning", 4: "Above Flood Warning"}[level]
        item = {"value": value, "name": name, "level": level, "color": LEVEL_COLORS[level]}
        if r.get("notes"):
            item["note"] = r["notes"]
        if typ == "stage":
            stage.setdefault(key, []).append(item)
            continue
        try:
            minutes = int(r.get("minutes", ""))
            assert minutes > 0
        except (ValueError, AssertionError):
            errors.append(f"{where}: rain thresholds need 'minutes' (e.g. 30 or 240)"); continue
        tide_txt = r.get("tide_at_least_navd88", "")
        high_tide = bool(tide_txt) or r.get("high_tide", "").lower() in ("yes", "y", "true", "1")
        item.update({"gauge": key, "minutes": minutes, "high_tide": high_tide,
                     "label": _window(minutes) + " rain" + (" + high tide" if high_tide else "")})
        if tide_txt:   # high tide = the creek's NOAA tide station at or above this level, in ft NAVD88
            try:
                item["tide_min"] = float(tide_txt)
            except ValueError:
                errors.append(f"{where}: tide_at_least_navd88 must be a number (ft NAVD88)"); continue
        triggers.setdefault(creek["id"], []).append(item)
    if errors:
        return errors
    for c in CREEKS:
        for g in c["stages"]:
            g["thresholds"] = sorted(stage.get(g["key"], []), key=lambda x: x["value"])
        c["rain_triggers"] = sorted(triggers.get(c["id"], []), key=lambda x: (x["minutes"], x["value"]))
        run = c.get("rain_running")
        if run and "line" not in run:   # the running-total graph's line: that gauge's threshold for the same window
            match = [x for x in c["rain_triggers"] if x["gauge"] == run["gauge"] and x["minutes"] == run["minutes"]]
            if match:
                run["line"] = min(x["value"] for x in match)
    return []


THRESHOLD_ERRORS = load_thresholds()


def map_thresholds():
    """Thresholds for the site map, by site number: {"41102": {"stage": [...]}}."""
    out = {}
    for c in CREEKS:
        for g in c["stages"]:
            if g.get("thresholds"):
                out.setdefault(g["number"], {})["stage"] = g["thresholds"]
    return out
