"""
Pull NOAA Atlas 14 point precipitation frequency estimates (PDS, depth, inches)
for every FEWS site and write them to one CSV.

Run:   python scripts/fetch_atlas14.py
Needs: Python 3.8+ only (no extra packages) and internet access.
Output: out/atlas14_fews_sites.csv (long format:
        one row per site x duration x return period).
"""

import csv
import os
import time
import urllib.request

SITES = [
    ("41107", "Atherton Channel at Alameda de las Pulgas", 37.4373600, -122.2133600),
    ("41106", "Atherton Channel upstream of CalTrain", 37.4619200, -122.1938700),
    ("BCSH", "Bear Creek at Sand Hill Road", 37.4099300, -122.2417800),
    ("41104", "Belmont Creek at Old County Rd", 37.5171911, -122.2712494),
    ("41153", "Butano Creek at Pescadero Road (flasher)", 37.2503003, -122.3943434),
    ("41152", "Butano Creek near Cloverdale Road", 37.2330032, -122.3660306),
    ("41101", "Colma Creek at Orange Memorial Park", 37.6537900, -122.4266900),
    ("CSC", "Crystal Springs Cottage", 37.4960000, -122.3290000),
    ("41201", "Green Hills Creek at Green Hills Country Club", 37.6013000, -122.4093000),
    ("A0835678", "Huddart Park", 37.4397528, -122.2888750),
    ("LAH", "La Honda", 37.3053000, -122.2539000),
    ("A080871E", "Los Trancos", 37.3263100, -122.1784600),
    ("LTAA", "Los Trancos at Arastradero Road", 37.3831200, -122.1929500),
    ("6069", "Mount Umunhum", 37.1583333, -121.9063889),
    ("A08506CA", "Palo Alto", 37.4555556, -122.1005559),
    ("41151", "Pescadero Creek at Stage Road", 37.2546753, -122.3832963),
    ("11162500", "Pescadero Creek near Pescadero", 37.2609650, -122.3289010),
    ("PCCC1", "Pescadero Town Ridge", 37.2876000, -122.2469000),
    ("11162619", "Pilarcitos Creek above Stone Dam", 37.5281400, -122.4001000),
    ("11162630", "Pilarcitos Creek at Half Moon Bay", 37.4666700, -122.4330600),
    ("111626182", "Pilarcitos Creek below Pilarcitos Lake Spillway", 37.5476940, -122.4208900),
    ("11162620", "Pilarcitos Creek below Stone Dam", 37.5246600, -122.3994200),
    ("PLD", "Pilarcitos Dam", 37.5480000, -122.4220000),
    ("PUL", "Pulgas", 37.4750000, -122.2980000),
    ("41105", "Redwood Creek at Johnson St.", 37.4703100, -122.2308400),
    ("41102", "San Bruno Creek at First Avenue", 37.6227300, -122.4067100),
    ("41200", "San Bruno Mountain", 37.6922200, -122.4483330),
    ("SFN", "San Francisco", 37.7705600, -122.4269400),
    ("SFC", "San Francisquito Creek (USGS)", 37.4233120, -122.1892070),
    ("11164500", "San Francisquito Creek at Stanford", 37.4232726, -122.1894095),
    ("11162570", "San Gregorio Creek at San Gregorio", 37.3257800, -122.3866400),
    ("41103", "San Mateo Creek at 3rd Avenue", 37.5696900, -122.3166300),
    ("11162753", "San Mateo Creek Below Crystal Springs Reservoir", 37.5294444, -122.3583333),
    ("SSUC1", "Saratoga Gap", 37.2614250, -122.1324520),
    ("A08204FE", "Trappers Trail (Valley Water)", 37.3461111, -122.1808330),
    ("A0839DB4", "Windy Hill Open Space Preserve", 37.3579900, -122.2399000),
    ("A08363E2", "Wunderlich County Park", 37.4024320, -122.2748610),
]

URL = ("https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new/fe_text_mean.csv"
       "?lat={lat}&lon={lon}&data=depth&units=english&series=pds")


def fetch(lat, lon):
    req = urllib.request.Request(URL.format(lat=lat, lon=lon),
                                 headers={"User-Agent": "FEWS-atlas14-pull"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def parse(text):
    """Return (volume_line, returned_lat, returned_lon, aris, rows)."""
    volume, rlat, rlon, aris, rows = "", None, None, None, []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("NOAA Atlas"):
            volume = s
        elif s.startswith("Latitude:"):
            rlat = float(s.split()[1])
        elif s.startswith("Longitude:"):
            rlon = float(s.split()[1])
        elif s.startswith("by duration for ARI"):
            aris = [int(x) for x in s.split(":,", 1)[1].split(",")]
        elif aris and ":," in s:
            dur, vals = s.split(":,", 1)
            vals = [float(v) for v in vals.split(",")]
            if len(vals) == len(aris):
                rows.append((dur.strip(), vals))
            # stops picking up rows once a different table section starts
        elif aris and rows and s == "":
            break
    return volume, rlat, rlon, aris, rows


def main():
    out_rows, problems = [], []
    for sid, name, lat, lon in SITES:
        try:
            volume, rlat, rlon, aris, rows = parse(fetch(lat, lon))
            if rlat is None or abs(rlat - lat) > 1e-4 or abs(rlon - lon) > 1e-4:
                problems.append(f"{sid}: returned coords {rlat},{rlon} do not match {lat},{lon}")
                continue
            if not rows:
                problems.append(f"{sid}: no table found in response")
                continue
            for dur, vals in rows:
                for ari, depth in zip(aris, vals):
                    out_rows.append([sid, name, lat, lon, volume, dur, ari, depth])
            print(f"ok   {sid:10s} {name}  ({len(rows)} durations)")
        except Exception as e:  # network or parse failure
            problems.append(f"{sid}: {e}")
        time.sleep(1)  # be polite to NOAA's server

    os.makedirs("out", exist_ok=True)
    with open(os.path.join("out", "atlas14_fews_sites.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["site_id", "name", "lat", "lon", "atlas_volume",
                    "duration", "ari_years", "depth_in"])
        w.writerows(out_rows)

    print(f"\nWrote atlas14_fews_sites.csv ({len(out_rows)} rows)")
    if problems:
        print("\nProblems (re-run or check these sites):")
        for p in problems:
            print("  " + p)


if __name__ == "__main__":
    main()
