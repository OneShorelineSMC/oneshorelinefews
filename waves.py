"""Waves off the San Mateo coast, for the Coastside Tides page and the Coast card (staff, 2026-11-10).

NOAA's tide table and tide projections are still water only: they leave out waves, which on the open coast can run far
higher up a beach than the tide. This adds the two official wave sources the pages can show:
  1. Measured: NOAA NDBC buoys (the Half Moon Bay buoy first), the last 48 hours of significant wave height, dominant
     period and direction, from https://www.ndbc.noaa.gov/data/realtime2/{id}.txt (hourly or better).
  2. Forecast: the National Weather Service Coastal Waters Forecast (CWF) from the San Francisco Bay Area office (MTR),
     the section for the coastal waters off San Mateo County (WAVES_ZONES, Point Reyes to Pigeon Point out 10 nm), from
     api.weather.gov. Each period's text is kept as written, with the largest height in feet it gives (seas or swell).
Both are offshore: breaking waves at the beach can be larger, and sneaker waves run farther up the sand. The pages say so.

The USGS/NOAA Total Water Level and Coastal Change forecast (wave runup at the beach) would be better, but as of its
2023 paper it covers the Atlantic and Gulf coasts only; the Pacific coast was "under development".

Writes waves.json on the data branch. Kept as is when a source can't be read.

Usage: python waves.py OUTPUT.json [--min-age MINUTES]
"""

import datetime as dt
import json
import re
import sys
import urllib.request

UA = "OneShoreline-FEWS/1.0 (https://github.com/OneShorelineSMC/oneshorelinefews)"
BUOYS = [("46012", "Half Moon Bay buoy (24 nm southwest of Half Moon Bay)"),
         ("46026", "San Francisco buoy (18 nm west of San Francisco)")]
NDBC_URL = "https://www.ndbc.noaa.gov/data/realtime2/{}.txt"
CWF_LIST = "https://api.weather.gov/products/types/CWF/locations/MTR"
CWF_ITEM = "https://api.weather.gov/products/{}"
WAVES_ZONES = ["PZZ545"]   # Coastal waters from Point Reyes to Pigeon Point, out 10 nm (off San Mateo County)
HOURS = 48
M_TO_FT = 3.28084
COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def get(url, accept=None, timeout=30):
    h = {"User-Agent": UA}
    if accept:
        h["Accept"] = accept
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def compass(deg):
    return None if deg is None else COMPASS[int((deg % 360) / 22.5 + 0.5) % 16]


def parse_ndbc(text, now_utc, hours=HOURS):
    """NDBC realtime2 standard meteorological file -> [{t (UTC ISO), ft, s, dir_deg, dir}] newest first, last `hours`."""
    lines = [l for l in text.splitlines() if l.strip()]
    head = next((l for l in lines if l.startswith("#YY")), None)
    if not head:
        raise ValueError("no header")
    cols = head.lstrip("#").split()
    idx = {c: i for i, c in enumerate(cols)}
    out, cut = [], now_utc - dt.timedelta(hours=hours)
    for l in lines:
        if l.startswith("#"):
            continue
        f = l.split()
        if len(f) < len(cols):
            continue
        try:
            t = dt.datetime(int(f[idx["YY"]]), int(f[idx["MM"]]), int(f[idx["DD"]]), int(f[idx["hh"]]), int(f[idx["mm"]]), tzinfo=dt.timezone.utc)
        except (KeyError, ValueError):
            continue
        if t < cut:
            break   # newest first in these files
        def num(c):
            v = f[idx[c]] if c in idx else "MM"
            try:
                return None if v == "MM" else float(v)
            except ValueError:
                return None
        h, p, d = num("WVHT"), num("DPD"), num("MWD")
        if h is None:
            continue
        out.append({"t": t.strftime("%Y-%m-%dT%H:%MZ"), "ft": round(h * M_TO_FT, 1), "s": p, "dir_deg": d, "dir": compass(d)})
    return out


FT_RX = re.compile(r"(\d+(?:\.\d+)?)(?:\s*(?:to|-)\s*(\d+(?:\.\d+)?))?\s*(?:ft|feet)\b", re.I)


def parse_cwf(text, zones=WAVES_ZONES):
    """The CWF section for the first of `zones` found -> {zone, zone_name, periods: [{name, text, max_ft}]}."""
    for sec in re.split(r"\n\$\$\s*\n", text):
        if not any(z in sec for z in zones):
            continue
        zone = next(z for z in zones if z in sec)
        body = sec.split("\n")
        # the zone name: the first line after the UGC/time lines that isn't a code, a time or blank
        name = ""
        for l in body:
            s = l.strip()
            if s and not re.match(r"^(PZZ|\d{6}-|\d{3,4} (AM|PM))", s) and not s.startswith("."):
                name = s.rstrip("-").strip()
                break
        periods, cur = [], None
        for l in body:
            m = re.match(r"^\.([A-Z][A-Z .']+?)\.\.\.(.*)$", l.strip())
            if m:
                if cur:
                    periods.append(cur)
                cur = {"name": m.group(1).strip().title(), "text": m.group(2).strip()}
            elif cur and l.strip() and not l.strip().startswith("&&"):
                cur["text"] += " " + l.strip()
        if cur:
            periods.append(cur)
        for p in periods:
            p["text"] = re.sub(r"\s+", " ", p["text"]).strip()
            hs = [float(b or a) for a, b in FT_RX.findall(p["text"])]
            p["max_ft"] = max(hs) if hs else None
        return {"zone": zone, "zone_name": name, "periods": periods}
    raise ValueError("zone not found: " + ",".join(zones))


def update(previous, now_utc, fetch=get):
    out = {"generated_utc": now_utc.strftime("%Y-%m-%dT%H:%MZ"), "buoys": [], "cwf": None, "problems": []}
    prev_b = {b.get("id"): b for b in (previous or {}).get("buoys") or []}
    for bid, name in BUOYS:
        try:
            obs = parse_ndbc(fetch(NDBC_URL.format(bid)), now_utc)
            out["buoys"].append({"id": bid, "name": name, "obs": obs, "latest": obs[0] if obs else None})
        except Exception as e:  # noqa: BLE001 - keep the last good readings
            out["problems"].append(f"buoy {bid}: {type(e).__name__}: {e}"[:200])
            if bid in prev_b:
                out["buoys"].append(prev_b[bid])
    try:
        lst = json.loads(fetch(CWF_LIST, accept="application/ld+json"))
        items = lst.get("@graph") or []
        if not items:
            raise ValueError("no CWF products")
        item = json.loads(fetch(CWF_ITEM.format(items[0]["id"]), accept="application/ld+json"))
        cwf = parse_cwf(item.get("productText") or "")
        cwf["issued"] = item.get("issuanceTime")
        cwf["source"] = "National Weather Service, San Francisco Bay Area office: Coastal Waters Forecast"
        out["cwf"] = cwf
    except Exception as e:  # noqa: BLE001
        out["problems"].append(f"CWF: {type(e).__name__}: {e}"[:200])
        out["cwf"] = (previous or {}).get("cwf")
    return out


def main(argv):
    path = argv[1]
    min_age = float(argv[argv.index("--min-age") + 1]) if "--min-age" in argv else 0
    previous = {}
    try:
        with open(path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        pass
    now = dt.datetime.now(dt.timezone.utc)
    last = previous.get("generated_utc")
    if last and min_age and now - dt.datetime.strptime(last, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc) < dt.timedelta(minutes=min_age):
        print(f"waves: last run {last}, younger than {min_age:g} min; kept")
        return 0
    result = update(previous, now)
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    for b in result["buoys"]:
        lt = b.get("latest")
        print(f"buoy {b['id']}: " + (f"{lt['ft']} ft at {lt['s']} s from {lt['dir']} ({lt['t']})" if lt else "no reading"))
    c = result.get("cwf")
    if c:
        print(f"CWF {c.get('zone')} issued {c.get('issued')}: " + "; ".join(f"{p['name']} {p['max_ft']} ft" for p in c["periods"][:6]))
    for p in result["problems"]:
        print("problem:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
