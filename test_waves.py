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

print("\n" + ("All passed" if not fails else f"{len(fails)} failed"))
sys.exit(1 if fails else 0)
