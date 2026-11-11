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

EXPERIMENTAL, staff only (2026-11-11): how far up a few reference beaches the water may reach (lookups/runup_beaches.csv):
tide + wave runup, the method of the USGS/NOAA Total Water Level forecast (which doesn't cover this coast):
  total water level (ft NAVD88) = still water at San Francisco (9414290: NOAA projection, then the tide table plus the
  last week's measured-minus-table) + R2%, the wave runup exceeded by 2% of waves (Stockdon et al. 2006, from the
  offshore wave height H0, the peak period T and the beach's foreshore slope; H0 times the beach's wave_factor).
  Forecast waves: the NWS forecast grid off each beach (hourly waveHeight/wavePeriod), or else the Coastal Waters
  Forecast's "Wave Detail" swells. Hindcast (last 2 days): the Half Moon Bay buoy and the measured tide.
The slopes are placeholders until surveyed, and the formula is for sand beaches, so the numbers are rough. Each day's
peak is kept twice for checking: forecast the day before (fc1) and hindcast (hind), in runup.history.

Writes waves.json on the data branch. Kept as is when a source can't be read.

Usage: python waves.py OUTPUT.json [--min-age MINUTES] [--beaches lookups/runup_beaches.csv]
"""

import csv
import datetime as dt
import json
import math
import os
import re
import sys
import urllib.request
from zoneinfo import ZoneInfo

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


# ---------------------------------------------------------------- runup (experimental, staff only)
PAC = ZoneInfo("America/Los_Angeles")
TIDE_STATION = "9414290"   # San Francisco (Golden Gate): the nearest NOAA gauge with NAVD88, 15-35 km from the beaches
NOAA = ("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station={st}&product={p}&begin_date={b}&end_date={e}"
        "&datum=NAVD&time_zone=gmt&units=english&format=json&application=OneShorelineFEWS{x}")
POINTS = "https://api.weather.gov/points/{:.4f},{:.4f}"
GRID = "https://api.weather.gov/gridpoints/{}/{},{}"
G = 9.81
FC_HOURS = 120
HIST_DAYS = 150


def stockdon_r2(h0_m, t_s, slope):
    """R2% runup (m above still water), Stockdon et al. (2006) eq. 19; dissipative form when the Iribarren number < 0.3."""
    if not h0_m or not t_s or h0_m <= 0 or t_s <= 0:
        return None
    l0 = G * t_s * t_s / (2 * math.pi)
    hl = h0_m * l0
    xi = slope / math.sqrt(h0_m / l0)
    if xi < 0.3:
        return 0.043 * math.sqrt(hl)
    return 1.1 * (0.35 * slope * math.sqrt(hl) + math.sqrt(hl * (0.563 * slope * slope + 0.004)) / 2)


def read_beaches(path):
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                b = {"id": r["id"].strip(), "name": r["name"].strip(), "lat": float(r["lat"]), "lon": float(r["lon"]),
                     "slope": float(r["slope"]), "wave_factor": float(r.get("wave_factor") or 1)}
            except (KeyError, ValueError):
                continue
            fl = (r.get("flag_ft_navd88") or "").strip()
            b["flag_ft"] = float(fl) if fl else None
            b["flag_what"] = (r.get("flag_what") or "").strip()
            b["placeholder"] = "PLACEHOLDER" in (r.get("basis") or "")
            out.append(b)
    return out


def hour(t):
    return t.replace(minute=0, second=0, microsecond=0)


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def noaa_series(fetch, product, b, e, extra=""):
    j = json.loads(fetch(NOAA.format(st=TIDE_STATION, p=product, b=b.strftime("%Y%m%d"), e=e.strftime("%Y%m%d"), x=extra)))
    if "error" in j:
        raise ValueError(j["error"].get("message", "NOAA error"))
    out = {}
    for x in j.get("predictions") or j.get("data") or []:
        try:
            t = dt.datetime.strptime(x["t"], "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc)
            v = float(x["v"])
        except (KeyError, ValueError):
            continue
        if t.minute == 0:
            out[t] = v
    return out


def still_water(fetch, now):
    """Hourly still water at San Francisco, ft NAVD88: {past: measured, ahead: projection then table + anomaly}."""
    h0 = hour(now)
    pred = noaa_series(fetch, "predictions", now - dt.timedelta(days=8), now + dt.timedelta(hours=FC_HOURS + 24), "&interval=h")
    meas = {}
    try:
        meas = noaa_series(fetch, "water_level", now - dt.timedelta(days=7), now)
    except Exception:  # noqa: BLE001
        pass
    diffs = [meas[t] - pred[t] for t in meas if t in pred and t >= now - dt.timedelta(days=7)]
    anom = sum(diffs) / len(diffs) if len(diffs) >= 48 else 0.0
    ofs = {}
    try:
        ofs = noaa_series(fetch, "ofs_water_level", now - dt.timedelta(days=1), now + dt.timedelta(days=3))
    except Exception:  # noqa: BLE001
        pass
    ahead, src = {}, {}
    for t, v in pred.items():
        if h0 <= t <= h0 + dt.timedelta(hours=FC_HOURS):
            if t in ofs:
                ahead[t], src[t] = ofs[t], "projection"
            else:
                ahead[t], src[t] = v + anom, "table"
    past = {t: v for t, v in meas.items() if t >= h0 - dt.timedelta(hours=48)}
    return past, ahead, src, round(anom, 2)


def expand(vals, unit_scale=1.0):
    """NWS grid values [{validTime: '2026-11-11T08:00:00+00:00/PT3H', value}] -> {hour: value}."""
    out = {}
    for x in vals or []:
        if x.get("value") is None:
            continue
        t0, dur = x["validTime"].split("/")
        t = dt.datetime.fromisoformat(t0).astimezone(dt.timezone.utc)
        m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?", dur)
        n = (int(m.group(1) or 0) * 24 + int(m.group(2) or 0)) if m else 1
        for k in range(max(n, 1)):
            out[t + dt.timedelta(hours=k)] = x["value"] * unit_scale
    return out


def grid_waves(fetch, lat, lon):
    """Hourly (H0 m, T s) from the NWS forecast grid: the beach's grid cell, then cells to the west until one has waves."""
    p = json.loads(fetch(POINTS.format(lat, lon), accept="application/geo+json"))["properties"]
    office, x, y = p["gridId"], int(p["gridX"]), int(p["gridY"])
    for k in range(0, 7):
        g = json.loads(fetch(GRID.format(office, x - k, y), accept="application/geo+json"))["properties"]
        def series(name):
            q = g.get(name) or {}
            sc = 0.3048 if "ft" in str(q.get("uom", "")) else 1.0
            return expand(q.get("values"), sc)
        hs, tp = series("waveHeight"), series("wavePeriod")
        if hs and tp:
            return {t: (hs[t], tp[t]) for t in hs if t in tp}, f"{office} {x - k},{y}"
    raise ValueError("no wave values in the grid near the beach")


DETAIL_RX = re.compile(r"\b([NSEW]{1,3})\s+(\d+(?:\.\d+)?)\s*ft\s+at\s+(\d+)\s*seconds", re.I)


def cwf_spans(cwf):
    """Coastal Waters Forecast periods laid end to end from the issue time (day periods end 6 PM, nights 6 AM, a weekday
    with no Night period after it is a whole day) -> [(start, end, H0 m, T s)] with the swell that runs up farthest."""
    if not cwf or not cwf.get("issued"):
        return []
    t = dt.datetime.fromisoformat(cwf["issued"]).astimezone(PAC)
    ps, out = cwf.get("periods") or [], []
    for i, p in enumerate(ps):
        night = re.search(r"night|overnight", p["name"], re.I)
        day0 = t.replace(hour=0, minute=0, second=0, microsecond=0)
        if night:
            end = (day0 + dt.timedelta(days=1 if t.hour >= 6 else 0)).replace(hour=6)
        else:
            nx = ps[i + 1]["name"] if i + 1 < len(ps) else ""
            base = day0 + dt.timedelta(days=1 if t.hour >= 18 else 0)
            if i > 0 and not re.search(r"night", nx, re.I):
                t, end = max(t, base), base + dt.timedelta(days=1)
            else:
                end = base.replace(hour=18)
        if end <= t:
            end = t + dt.timedelta(hours=12)
        best = None
        for _, h, s in DETAIL_RX.findall(p.get("text") or ""):
            h_m, s = float(h) * 0.3048, float(s)
            if not best or h_m * s * s > best[0] * best[1] ** 2:
                best = (h_m, s)
        if best:
            out.append((t.astimezone(dt.timezone.utc), end.astimezone(dt.timezone.utc), best[0], best[1]))
        t = end
    return out


def cwf_waves(cwf):
    out = {}
    for a, b, h, s in cwf_spans(cwf):
        t = hour(a)
        while t < b:
            out[t] = (h, s)
            t += dt.timedelta(hours=1)
    return out


def buoy_waves(buoys):
    out = {}
    for b in buoys or []:
        if b.get("id") != "46012":
            continue
        for o in b.get("obs") or []:
            if o.get("ft") and o.get("s"):
                t = hour(dt.datetime.strptime(o["t"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc))
                out.setdefault(t, (o["ft"] * 0.3048, o["s"]))
    return out


def twl_series(beach, water, waves):
    rows = []
    for t in sorted(water):
        w = waves.get(t)
        if not w:
            continue
        r = stockdon_r2(w[0] * beach["wave_factor"], w[1], beach["slope"])
        if r is None:
            continue
        r_ft = r / 0.3048
        rows.append({"t": iso(t), "tide": round(water[t], 2), "h_ft": round(w[0] / 0.3048, 1), "s": round(w[1]),
                     "runup": round(r_ft, 1), "twl": round(water[t] + r_ft, 1)})
    return rows


def daily_peaks(rows):
    best = {}
    for r in rows:
        d = dt.datetime.strptime(r["t"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc).astimezone(PAC).strftime("%Y-%m-%d")
        if d not in best or r["twl"] > best[d]["twl"]:
            best[d] = dict(r, date=d)
    return [best[d] for d in sorted(best)]


def runup(previous, now, beaches, buoys, cwf, fetch=get):
    out = {"method": "Stockdon et al. (2006) R2% runup + still water at NOAA 9414290 (San Francisco); experimental, staff only",
           "tide_station": TIDE_STATION, "generated_utc": iso(now), "beaches": [], "problems": []}
    try:
        past, ahead, src, anom = still_water(fetch, now)
        out["tide_anomaly_ft"] = anom
        out["tide_projection_hours"] = sum(1 for v in src.values() if v == "projection")
    except Exception as e:  # noqa: BLE001
        out["problems"].append(f"tide: {type(e).__name__}: {e}"[:200])
        prev = (previous or {}).get("runup")
        if prev:
            prev = dict(prev, problems=out["problems"])
        return prev or out
    hind_w = buoy_waves(buoys)
    cw = cwf_waves(cwf)
    prev_hist = ((previous or {}).get("runup") or {}).get("history") or {}
    today = now.astimezone(PAC).date()
    tomorrow = (today + dt.timedelta(days=1)).isoformat()
    keep_from = (today - dt.timedelta(days=HIST_DAYS)).isoformat()
    for b in beaches:
        fw, wsrc = {}, "none"
        try:
            fw, wsrc = grid_waves(fetch, b["lat"], b["lon"])
            wsrc = "NWS forecast grid " + wsrc
        except Exception as e:  # noqa: BLE001
            out["problems"].append(f"{b['id']} grid: {type(e).__name__}: {e}"[:200])
        if not fw and cw:
            fw, wsrc = cw, "NWS Coastal Waters Forecast (wave detail)"
        fc = twl_series(b, ahead, fw)
        hc = twl_series(b, past, hind_w)
        fpk, hpk = daily_peaks(fc), daily_peaks(hc)
        hist = {d: dict(v) for d, v in (prev_hist.get(b["id"]) or {}).items() if d >= keep_from}
        for p in fpk:
            if p["date"] == tomorrow and "fc1" not in hist.get(tomorrow, {}):
                hist.setdefault(tomorrow, {})["fc1"] = p["twl"]
        for p in hpk:
            if p["date"] <= today.isoformat():
                hist.setdefault(p["date"], {})["hind"] = max(p["twl"], hist.get(p["date"], {}).get("hind", -99)) if p["date"] == today.isoformat() else p["twl"]
        out.setdefault("history", {})[b["id"]] = hist
        out["beaches"].append({k: b[k] for k in ("id", "name", "slope", "wave_factor", "flag_ft", "flag_what", "placeholder")} |
                              {"wave_source": wsrc, "forecast": fc, "hindcast": hc, "peaks": fpk, "hind_peaks": hpk})
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
    beaches_path = argv[argv.index("--beaches") + 1] if "--beaches" in argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups", "runup_beaches.csv")
    try:
        result["runup"] = runup(previous, now, read_beaches(beaches_path), result.get("buoys"), result.get("cwf"))
    except Exception as e:  # noqa: BLE001 - never lose the waves over the experiment
        result["problems"].append(f"runup: {type(e).__name__}: {e}"[:200])
        if previous.get("runup"):
            result["runup"] = previous["runup"]
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    for b in result["buoys"]:
        lt = b.get("latest")
        print(f"buoy {b['id']}: " + (f"{lt['ft']} ft at {lt['s']} s from {lt['dir']} ({lt['t']})" if lt else "no reading"))
    c = result.get("cwf")
    if c:
        print(f"CWF {c.get('zone')} issued {c.get('issued')}: " + "; ".join(f"{p['name']} {p['max_ft']} ft" for p in c["periods"][:6]))
    for b in (result.get("runup") or {}).get("beaches") or []:
        print(f"runup {b['id']} ({b['wave_source']}): " + "; ".join(f"{p['date']} {p['twl']} ft NAVD88" for p in b["peaks"][:5]))
    for p in result["problems"] + ((result.get("runup") or {}).get("problems") or []):
        print("problem:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
