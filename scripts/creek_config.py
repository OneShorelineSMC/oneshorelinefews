"""
The creeks shown on the kiosk's Creeks tab, the phone page (Creeks.html) and the home page, and the alert
levels drawn on the site map. THIS IS THE ONE PLACE TO EDIT creeks, gauges and flood thresholds: the pages
read everything from the published data file, so changes here show up everywhere on the next data run
(about 5 minutes after you commit).

Each creek has:
  id      short code used in links, e.g. Creeks.html#atherton
  name    shown on buttons and headings
  intro   one sentence under the creek's name
  tide    NOAA station shown under the creek: "9414750" Alameda or "9414523" Redwood City
  note    optional text shown with the graphs (e.g. what the threshold colors mean)
  stages  creek water-level gauges, upstream first
  rain    rain gauges, upper watershed first
  rain_triggers  optional rain amounts that mean flooding is likely (e.g. Belmont Creek): the rain at one of
          the creek's gauges over "minutes"; with "high_tide": True the trigger also needs the tide at or above
          MHHW (Mean Higher High Water) at the creek's tide station

Each gauge needs its OneRain sensor link details: open the sensor's page on OneRain (Sites > site > sensor)
and copy site_id, site, device_id and device from the address bar.

Thresholds are in feet on that gauge, lowest first. "level" sets the color and how serious it is:
1 = Flood Monitoring (yellow), 2 = Flood Watch (orange), 3 = Flood Warning (red), 4 = beyond warning (purple).
"""

LEVEL_COLORS = {1: "#e6c200", 2: "#e07b00", 3: "#c62828", 4: "#9c27b0"}


def levels(*rows):
    """levels((3.18, "Flood Monitoring", 1), ...) -> threshold list with colors."""
    return [{"value": v, "name": n, "level": l, "color": LEVEL_COLORS[l]} for v, n, l in rows]


CREEKS = [
    {
        "id": "sanbruno",
        "name": "San Bruno Creek",
        "intro": "Creek level at First Avenue in South San Francisco / San Bruno, rain in the upper and lower "
                 "watershed, and the Bay tide at Alameda. The creek at First Avenue rises and falls with the tide.",
        "tide": "9414750",
        "note": "",
        "stages": [
            {"key": "stage", "label": "First Avenue", "site_name": "San Bruno Creek at First Avenue", "number": "41102",
             "site_id": 11, "site": "fe06588c-e5e6-4016-8a8f-2ba1f040636e",
             "device_id": 3, "device": "e481d107-65bb-4107-89ab-48484eb0e188",
             "reports": "on change",   # reports only when the level changes, so silence isn't always an outage
             "thresholds": levels((2.40, "Flood Monitoring", 1), (3.60, "Flood Watch", 2), (4.80, "Flood Warning", 3)),
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
             "thresholds": levels((3.18, "Flood Monitoring", 1), (4.60, "Flood Watch", 2), (5.65, "Flood Warning", 3),
                                  (10.40, "Roadway Flooded", 4)),
             "note": ""},
            {"key": "ath_caltrain", "label": "Upstream of Caltrain", "site_name": "Atherton Channel upstream of CalTrain",
             "number": "41106", "site_id": 14, "site": "a63a9e54-703b-43b1-8286-6cabbaae7fa1",
             "device_id": 4, "device": "b1b9cc5f-9ad6-498b-96cb-fc299b4eab79",
             "reports": "on change",
             "thresholds": levels((2.80, "Flood Monitoring", 1), (4.10, "Flood Watch", 2), (5.50, "Flood Warning", 3)),
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
         "thresholds": levels((2.25, "Flood Monitoring", 1), (3.25, "Flood Watch", 2), (4.00, "Flood Warning", 3)),
         "note": ""},
    ],
    "rain": [
        {"key": "bel_rain", "label": "Old County Road", "where": "lower watershed", "number": "41104",
         "site_id": 2, "site": "25fd9d56-e3ea-4ff9-a067-b3e99cc5c1fe",
         "device_id": 4, "device": "4002d654-cd0a-4e0f-a178-83ea5ea84566"},
    ],
    "rain_triggers": [
        {"gauge": "bel_rain", "minutes": 30, "value": 0.20, "high_tide": False,
         "label": "30-minute rain", "name": "Flooding likely (rain)", "level": 3, "color": LEVEL_COLORS[3]},
        {"gauge": "bel_rain", "minutes": 240, "value": 0.42, "high_tide": True,
         "label": "4-hour rain + high tide", "name": "Flooding likely (rain + tide)", "level": 3, "color": LEVEL_COLORS[3]},
    ],
})


CREEKS.append({
    "id": "colma",
    "name": "Colma Creek",
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
         "thresholds": levels((3.40, "Flood Monitoring", 1), (5.00, "Flood Watch", 2), (6.75, "Flood Warning", 3)),
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


def map_thresholds():
    """Thresholds for the site map, by site number: {"41102": {"stage": [...]}}."""
    out = {}
    for c in CREEKS:
        for g in c["stages"]:
            out.setdefault(g["number"], {})["stage"] = g["thresholds"]
    return out
