"""Tests for waves.py with made-up NDBC and NWS text in their published formats. Run: python scripts/test_waves.py"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import waves as W  # noqa: E402

fails = []


def check(name, ok):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


NOW = dt.datetime(2026, 11, 11, 7, 0, tzinfo=dt.timezone.utc)
NDBC = """#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE
#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi  hPa    ft
2026 11 11 06 40 300  8.0 10.0   4.3  17.0  11.2 290 1016.2  13.1  14.0   9.0   MM -0.6    MM
2026 11 11 06 10 300  8.0 10.0    MM    MM    MM  MM 1016.2  13.1  14.0   9.0   MM -0.6    MM
2026 11 11 05 40 300  8.0 10.0   4.0  16.0  11.0 285 1016.2  13.1  14.0   9.0   MM -0.6    MM
2026 11 08 05 40 300  8.0 10.0   1.0   9.0   7.0 285 1016.2  13.1  14.0   9.0   MM -0.6    MM
"""
obs = W.parse_ndbc(NDBC, NOW)
check("buoy: newest first, metres to feet, missing heights skipped, older than 48 h left out", len(obs) == 2 and obs[0]["ft"] == 14.1 and obs[0]["s"] == 17.0)
check("buoy: direction in words", obs[0]["dir"] == "WNW" and obs[1]["dir"] == "WNW")

CWF = """000
FZUS56 KMTR 110330
CWFMTR

Coastal Waters Forecast for California
National Weather Service San Francisco CA
730 PM PST Tue Nov 10 2026

$$

PZZ540-111130-
Coastal Waters from Point Arena to Point Reyes California out 10 NM-
730 PM PST Tue Nov 10 2026

.TONIGHT...NW winds 10 kt. Seas 8 ft.
$$

PZZ545-111130-
Coastal Waters from Point Reyes to Pigeon Point California out
10 NM-
730 PM PST Tue Nov 10 2026

...HIGH SURF WARNING IN EFFECT FROM WEDNESDAY MORNING THROUGH
THURSDAY EVENING...

.TONIGHT...W winds 5 to 10 kt. Seas 9 to 11 ft. W swell 8 to
10 ft at 14 seconds.
.WED...W winds 10 kt. Seas 18 to 22 ft. W swell 20 to 25 ft at
20 seconds.
.THU...NW winds 15 kt. W swell 16 ft at 17 seconds.
$$
"""
c = W.parse_cwf(CWF)
check("CWF: the San Mateo zone, not the one north of it", c["zone"] == "PZZ545" and c["zone_name"].startswith("Coastal Waters from Point Reyes to Pigeon Point"))
check("CWF: periods with their text joined across lines", [p["name"] for p in c["periods"]] == ["Tonight", "Wed", "Thu"] and "20 seconds" in c["periods"][1]["text"])
check("CWF: the largest height in feet each period (kt and seconds ignored)", [p["max_ft"] for p in c["periods"]] == [11.0, 25.0, 16.0])

calls = []
def fetch(url, accept=None):
    calls.append(url)
    if "ndbc" in url:
        if "46026" in url:
            raise OSError("down")
        return NDBC
    if url.endswith("/locations/MTR"):
        return json.dumps({"@graph": [{"id": "abc-123"}]})
    return json.dumps({"productText": CWF, "issuanceTime": "2026-11-11T03:30:00+00:00"})
prev = {"buoys": [{"id": "46026", "name": "x", "obs": [], "latest": {"ft": 9.0}}]}
r = W.update(prev, NOW, fetch)
check("update: both buoys (the one down keeps its last reading), CWF with issue time", [b["id"] for b in r["buoys"]] == ["46012", "46026"] and r["buoys"][1]["latest"] == {"ft": 9.0}
      and r["cwf"]["issued"].startswith("2026-11-11") and any("46026" in p for p in r["problems"]))
r2 = W.update({"cwf": {"zone": "PZZ545", "periods": []}}, NOW, lambda u, accept=None: (_ for _ in ()).throw(OSError("offline")))
check("update: NWS down: the last forecast kept", r2["cwf"] == {"zone": "PZZ545", "periods": []})

# ---- runup (experimental)
r2 = W.stockdon_r2(5.8, 18, 0.05)
check("Stockdon R2%: 19 ft at 18 s on a 1:20 beach is about 3.2 m (10.6 ft)", abs(r2 - 3.23) < 0.03)
check("Stockdon: flat beach uses the dissipative form", abs(W.stockdon_r2(3, 12, 0.01) - 0.043 * (3 * 9.81 * 144 / (2 * 3.14159265)) ** 0.5) < 0.01)
check("Stockdon: no waves, no runup", W.stockdon_r2(0, 10, 0.05) is None)
CW2 = {"issued": "2026-11-11T05:15:00+00:00", "periods": [
    {"name": "Tonight", "text": "Seas 5 to 8 ft. Wave Detail: NW 7 ft at 13 seconds."},
    {"name": "Veterans Day", "text": "Seas 5 to 7 ft. Wave Detail: NW 6 ft at 13 seconds."},
    {"name": "Wed Night", "text": "Wave Detail: W 8 ft at 14 seconds."},
    {"name": "Sat", "text": "Seas 14 to 19 ft. Wave Detail: SW 2 ft at 15 seconds and W 18 ft at 18 seconds."}]}
sp = W.cwf_spans(CW2)
loc = lambda t: t.astimezone(W.PAC).strftime("%a %H")
check("CWF spans: tonight to 6 AM, the holiday to 6 PM, night to 6 AM, a lone weekday a whole day",
      [(loc(a), loc(b)) for a, b, _, _ in sp] == [("Tue 21", "Wed 06"), ("Wed 06", "Wed 18"), ("Wed 18", "Thu 06"), ("Thu 06", "Fri 00")])
check("CWF spans: the swell that runs up farthest (18 ft at 18 s, not 2 ft at 15 s)", abs(sp[3][2] - 18 * 0.3048) < 1e-6 and sp[3][3] == 18)

NOW2 = dt.datetime(2026, 11, 11, 8, 30, tzinfo=dt.timezone.utc)
def tide_json(product, b, e):
    t = dt.datetime.strptime(b, "%Y%m%d").replace(tzinfo=dt.timezone.utc)
    end = dt.datetime.strptime(e, "%Y%m%d").replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=1)
    rows = []
    while t < end:
        if product == "ofs_water_level" and t > NOW2 + dt.timedelta(hours=40):
            break
        if product == "water_level" and t > NOW2:
            break
        v = 3.0 + 3.0 * __import__("math").sin(t.timestamp() / 3600 / 12.42 * 2 * 3.14159265)
        v += {"predictions": 0, "water_level": 0.4, "ofs_water_level": 0.5}[product]
        rows.append({"t": t.strftime("%Y-%m-%d %H:%M"), "v": "%.3f" % v})
        t += dt.timedelta(hours=1)
    return json.dumps({"predictions" if product == "predictions" else "data": rows})
def fetch2(url, accept=None):
    if "tidesandcurrents" in url:
        q = dict(x.split("=") for x in url.split("?")[1].split("&"))
        return tide_json(q["product"], q["begin_date"], q["end_date"])
    if "/points/" in url:
        return json.dumps({"properties": {"gridId": "MTR", "gridX": 80, "gridY": 100}})
    if "/gridpoints/MTR/80,100" in url:   # the beach's own cell: land, no waves
        return json.dumps({"properties": {"waveHeight": {"values": []}, "wavePeriod": {"values": []}}})
    if "/gridpoints/MTR/79,100" in url:
        return json.dumps({"properties": {"waveHeight": {"uom": "wmoUnit:m", "values": [{"validTime": "2026-11-11T08:00:00+00:00/P5D", "value": 5.8}]},
                                          "wavePeriod": {"uom": "wmoUnit:s", "values": [{"validTime": "2026-11-11T08:00:00+00:00/P5D", "value": 18}]}}})
    raise OSError("unexpected " + url)
BEACH = {"id": "b1", "name": "Test Beach", "lat": 37.6, "lon": -122.5, "slope": 0.05, "wave_factor": 1.0, "flag_ft": None, "flag_what": "", "placeholder": True}
BUOYS = [{"id": "46012", "obs": [{"t": (NOW2 - dt.timedelta(hours=k)).strftime("%Y-%m-%dT%H:00Z"), "ft": 10.0, "s": 14.0} for k in range(0, 48)]}]
ru = W.runup({}, NOW2, [BEACH], BUOYS, CW2, fetch2)
b = ru["beaches"][0]
check("runup: grid cell to the west used when the beach's own cell has no waves", b["wave_source"].endswith("79,100") and len(b["forecast"]) > 100)
f0 = b["forecast"][0]
check("runup: total = still water + runup (projection includes surge)", abs(f0["twl"] - (f0["tide"] + f0["runup"])) <= 0.11 and abs(f0["runup"] - 10.6) < 0.2)
check("runup: tide after the projection = table + last week's anomaly (0.4 ft)", ru["tide_anomaly_ft"] == 0.4 and ru["tide_projection_hours"] > 20)
check("runup: hindcast from the buoy and measured tide, daily peaks in Pacific dates", len(b["hindcast"]) >= 40 and b["hind_peaks"][-1]["date"] == "2026-11-11")
h = ru["history"]["b1"]
check("runup: tomorrow's forecast peak kept for checking (fc1), today's hindcast (hind)", "fc1" in h["2026-11-12"] and "hind" in h["2026-11-11"])
ru2 = W.runup({"runup": ru}, NOW2 + dt.timedelta(hours=1), [BEACH], BUOYS, CW2, fetch2)
check("runup: fc1 set once (the first forecast the day before), not overwritten", ru2["history"]["b1"]["2026-11-12"]["fc1"] == h["2026-11-12"]["fc1"])
def fetch3(url, accept=None):
    if "gridpoints" in url or "/points/" in url:
        raise OSError("grid down")
    return fetch2(url, accept)
ru3 = W.runup({}, NOW2, [BEACH], BUOYS, CW2, fetch3)
check("runup: grid down: the Coastal Waters Forecast swells instead", "Coastal Waters" in ru3["beaches"][0]["wave_source"] and len(ru3["beaches"][0]["forecast"]) > 20)
ru4 = W.runup({"runup": ru}, NOW2, [BEACH], BUOYS, CW2, lambda u, accept=None: (_ for _ in ()).throw(OSError("offline")))
check("runup: NOAA down: the last estimate kept, with the problem noted", ru4["beaches"] == ru["beaches"] and ru4["problems"])
import tempfile
bp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups", "runup_beaches.csv")
bs = W.read_beaches(bp)
check("runup_beaches.csv: three beaches read, marked as placeholders until surveyed", len(bs) == 3 and all(x["placeholder"] for x in bs))

print("\n" + ("All passed" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
