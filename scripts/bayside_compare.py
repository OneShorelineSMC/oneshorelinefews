"""Bayside rain compared, storm by storm (staff, 2026-11-21; Storm Tracker card "Bayside rain: San Bruno and its neighbors").

Staff asked whether San Bruno gets a disproportionate share of the rain. This step lines up the Bayside creeks' main rain
gauges and NOAA's SFO airport gauge over the same storms, going forward (the hourly record starts Nov 13, 2026):

  Gauges      each Bayside creek's main rain gauge (the first rain gauge in creeks.json for the creeks in BAYSIDE) and
              SFO airport (NWS, sfo:KSFO), an independent gauge about 1.5 miles from First Avenue.
  Storms      Bayside-wide: wet hours (0.01 in or more) at any of these gauges, split by at least STORM_DRY_HOURS dry
              hours at all of them; a storm counts with at least STORM_MIN_IN at one gauge (the Storm Tracker's rules).
              Every gauge is read over the same hours, so the totals compare directly.
  Per gauge   total, wettest 1 hour and 6 hours, and the rarest of those against NOAA Atlas 14 at that gauge (Heavy,
              Very heavy, Intense; SFO has no Atlas 14 row, so it isn't rated).
  San Bruno   its rank among the creek gauges, and its total against the others' average (1.5 = 50% more).
  Season      for each gauge, the storms' rain added up, how often it was the wettest, and San Bruno's median ratio.
  Wind        SFO's wind during the storm's wet hours (NWS observations, sfowind:KSFO in the hourly record), averaged as
              a direction weighted by each hour's rain, and First Avenue's rain against SFO's. Staff 2026-11-21: a gauge
              that reads high would read high whatever the wind; rain piling up where storms come through the San Bruno
              Gap would show mostly in south-southwest to west flow (GAP_FROM). The season splits the ratio that way.

A storm is open until STORM_DRY_HOURS after its last wet hour; then it's kept as it is (the hourly record only holds 10
days). The water year starts over on Oct 1. A gauge that went quiet reads as dry: the card names the gauges' reporting
from the Storm Tracker's season summary.

Writes bayside.json. Usage: python bayside_compare.py out/storm_tracker.json out/bayside.json [--creeks out/creeks.json]
"""

import datetime as dt
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import load_rain_frequency   # noqa: E402
from storm_tracker import rate, window_peak, hkey, parse_t, water_year_start   # noqa: E402

BAYSIDE = ["colma", "sanbruno", "belmont", "atherton"]   # Bayside creeks with a flood status and their own main rain gauge
FOCUS = "sanbruno"
SFO = {"key": "sfo:KSFO", "label": "SFO airport (NWS)", "number": None, "creek": None}
H = dt.timedelta(hours=1)
WIND_KEY = "sfowind:KSFO"
GAP_FROM = (195, 285)   # wind from south-southwest to west (degrees): storms coming through the San Bruno Gap
POINTS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def storm_wind(ledger, keys, a, b):
    """SFO's wind over a storm's wet hours: {deg, from, mph, hours}, the direction averaged as a vector weighted by the hour's
    rain (all gauges); None without wind records."""
    w = {parse_t(t): v for t, v in ((ledger.get(WIND_KEY) or {}).get("h") or {}).items() if a <= parse_t(t) <= b}
    rain = {}
    for k in keys:
        for t, v in ((ledger.get(k) or {}).get("h") or {}).items():
            h = parse_t(t)
            if a <= h <= b:
                rain[h] = rain.get(h, 0) + v
    x = y = sp = wt = 0.0
    n = 0
    for h, r in rain.items():
        d = w.get(h)
        if not d or r <= 0:
            continue
        x += r * math.sin(math.radians(d[0])); y += r * math.cos(math.radians(d[0])); sp += r * d[1]; wt += r; n += 1
    if not n:
        return None
    deg = (math.degrees(math.atan2(x, y)) + 360) % 360
    return {"deg": int(round(deg)), "from": POINTS[int((deg + 11.25) // 22.5) % 16], "mph": round(sp / wt, 1), "hours": n,
            "gap": GAP_FROM[0] <= deg <= GAP_FROM[1]}


def gauges(creeks):
    """[{key, label, number, creek}] in BAYSIDE order, then SFO."""
    by = {c["id"]: c for c in creeks}
    out = []
    for cid in BAYSIDE:
        c = by.get(cid)
        if c and c.get("rain"):
            g = c["rain"][0]
            out.append({"key": g["key"], "label": g.get("label") or g["key"], "number": g.get("number"), "creek": cid, "name": c.get("short") or c.get("name")})
    return out + [dict(SFO, name="SFO")]


def storms(ledger, keys, dry_h, min_in, wet=0.01):
    """[(start, end)] of Bayside-wide storms from the hourly record."""
    hours = sorted({parse_t(t) for k in keys for t, v in ((ledger.get(k) or {}).get("h") or {}).items() if v >= wet})
    runs = []
    for h in hours:
        if runs and h - runs[-1][1] <= (dry_h + 1) * H:
            runs[-1][1] = h
        else:
            runs.append([h, h])
    out = []
    for a, b in runs:
        tot = max(sum(v for t, v in ((ledger.get(k) or {}).get("h") or {}).items() if a <= parse_t(t) <= b) for k in keys)
        if tot >= min_in - 1e-9:
            out.append((a, b))
    return out


def sfo_scaled(ledger, cli):
    """SFO's hourly rain scaled, day by day, to the NWS Daily Climate Report's official total (storm_tracker.json sfo_cli):
    the hourly observations miss some hours (Nov 18, 2026: 2.28 in from the hours, 2.79 official). Days without an
    official total, or without any hourly rain to scale, are left as they are."""
    h = {parse_t(t): v for t, v in ((ledger.get(SFO["key"]) or {}).get("h") or {}).items()}
    by = {}
    for t, v in h.items():
        by[t.strftime("%Y-%m-%d")] = by.get(t.strftime("%Y-%m-%d"), 0) + v
    return {t: v * (cli[d] / by[d] if cli.get(d) is not None and by[d] > 0 else 1) for t, v in h.items() for d in [t.strftime("%Y-%m-%d")]}


def one(ledger, g, a, b, freq, sfo=None):
    src = sfo if (sfo is not None and g["key"] == SFO["key"]) else {parse_t(t): v for t, v in ((ledger.get(g["key"]) or {}).get("h") or {}).items()}
    rec = {t: v for t, v in src.items() if a <= t <= b}
    p1, t1 = window_peak(rec, a, b, 1)
    p6, t6 = window_peak(rec, a, b, 6)
    f = freq.get(str(g["number"])) if freq and g.get("number") else None
    rated = [x for x in ((rate(f, 60, p1), 60), (rate(f, 360, p6), 360)) if x[0]]
    best = max(rated, key=lambda x: (x[0]["level"], x[0]["years"] or 0)) if rated else None
    return {"key": g["key"], "total": round(sum(rec.values()), 2), "p1": p1, "p1_at": hkey(t1) if t1 else None,
            "p6": p6, "level": best[0]["level"] if best else None, "minutes": best[1] if best else None,
            "years": best[0]["years"] if best else None}


def compare(rows, focus_key):
    """San Bruno's rank among the creek gauges (1 = wettest) and its total against their average."""
    creek_rows = [r for r in rows if r["key"] != SFO["key"]]
    f = [r for r in creek_rows if r["key"] == focus_key]
    if not f:
        return None, None
    others = [r["total"] for r in creek_rows if r["key"] != focus_key]
    rank = 1 + sum(1 for r in creek_rows if r["total"] > f[0]["total"] + 1e-9)
    avg = sum(others) / len(others) if others else 0
    return rank, (round(f[0]["total"] / avg, 2) if avg >= 0.05 else None)


def season(events, gs):
    out = {"storms": len(events), "gauges": {}, "focus_wettest": 0, "focus_ratios": []}
    for g in gs:
        out["gauges"][g["key"]] = {"label": g["label"], "name": g["name"], "total": 0.0, "wettest": 0}
    for e in events:
        creek_rows = [r for r in e["gauges"] if r["key"] != SFO["key"]]
        top = max(creek_rows, key=lambda r: r["total"]) if creek_rows else None
        for r in e["gauges"]:
            if r["key"] in out["gauges"] and not r.get("missing"):
                out["gauges"][r["key"]]["total"] = round(out["gauges"][r["key"]]["total"] + r["total"], 2)
        if top and top["total"] > 0:
            out["gauges"][top["key"]]["wettest"] += 1
        if e.get("rank") == 1:
            out["focus_wettest"] += 1
        if e.get("ratio") is not None:
            out["focus_ratios"].append(e["ratio"])
    r = sorted(out.pop("focus_ratios"))
    out["focus_median_ratio"] = r[len(r) // 2] if r else None
    out["focus_rated"] = len(r)
    med = lambda v: sorted(v)[len(v) // 2] if v else None
    by = {"gap": [], "other": [], "all": []}
    for e in events:
        if e.get("vs_sfo") is None:
            continue
        by["all"].append(e["vs_sfo"])
        if e.get("wind"):
            by["gap" if e["wind"]["gap"] else "other"].append(e["vs_sfo"])
    out["vs_sfo"] = {k: {"storms": len(v), "median": med(v)} for k, v in by.items()}
    return out


def build(tracker, creeks, freq, now, prev=None):
    prev = prev or {}
    cli = tracker.get("sfo_cli") or {}
    rules = tracker.get("rules") or {}
    dry_h, min_in = float(rules.get("STORM_DRY_HOURS", 6)), float(rules.get("STORM_MIN_IN", 0.1))
    gs = gauges(creeks)
    focus_key = next((g["key"] for g in gs if g["creek"] == FOCUS), None)
    ledger = tracker.get("ledger") or {}
    wy0 = hkey(dt.datetime.combine(water_year_start(now.date()), dt.time()))
    kept = {e["start"]: e for e in prev.get("storms", []) if e.get("closed") and e["start"] >= wy0}
    events = []
    for a, b in storms(ledger, [g["key"] for g in gs], dry_h, min_in):
        if hkey(a) in kept or any(parse_t(e["start"]) <= b and parse_t(e["end"]) >= a for e in kept.values()):
            continue   # kept as first written (its first hours may since have left the hourly record)
        sfo = sfo_scaled(ledger, cli)
        rows = [dict(one(ledger, g, a, b, freq, sfo), label=g["label"], name=g["name"], creek=g["creek"]) for g in gs]
        for r in rows:   # SFO scaled to the official daily totals where it has them
            if r["key"] == SFO["key"]:
                r["official"] = any(cli.get(d) is not None for d in {(a + i * H).strftime("%Y-%m-%d") for i in range(int((b - a) / H) + 1)})
        # SFO's hourly record began a few days after the creek gauges' (Nov 15, 2026): dry at SFO while the creek
        # gauges were wet, before its first wet hour, means no record rather than no rain
        sfo_first = min(((ledger.get(SFO["key"]) or {}).get("h") or {}).keys(), default=None)
        for r in rows:
            if r["key"] == SFO["key"] and r["total"] == 0 and (sfo_first is None or sfo_first > hkey(b)) and max(x["total"] for x in rows) >= 0.25:
                r["missing"] = True
        rank, ratio = compare(rows, focus_key)
        fr = [r for r in rows if r["key"] == focus_key]
        sr = [r for r in rows if r["key"] == SFO["key"] and not r.get("missing")]
        vs_sfo = round(fr[0]["total"] / sr[0]["total"], 2) if fr and sr and sr[0]["total"] >= 0.1 else None
        events.append({"start": hkey(a), "end": hkey(b), "hours": int((b - a) / H) + 1, "closed": now - b > dry_h * H,
                       "gauges": rows, "rank": rank, "ratio": ratio, "of": sum(1 for g in gs if g["creek"]),
                       "wind": storm_wind(ledger, [g["key"] for g in gs], a, b), "vs_sfo": vs_sfo})
    # a closed storm the hourly record still holds is kept as first written; one it no longer holds is kept from before
    starts = {e["start"] for e in events}
    for k, e in kept.items():
        if k in starts:
            continue
        # storms kept from before the wind was recorded (Nov 21, 2026): wind and First Avenue vs SFO added once, if the
        # hourly record still covers them
        sr0 = [r for r in e["gauges"] if r["key"] == SFO["key"]]
        if sr0 and "official" not in sr0[0] and not sr0[0].get("missing"):
            # kept from before SFO was scaled to its official daily totals (Nov 21, 2026): redone once if the hourly record
            # still covers it
            a0, b0 = parse_t(e["start"]), parse_t(e["end"])
            if any(a0 <= parse_t(t) <= b0 for t in ((ledger.get(SFO["key"]) or {}).get("h") or {})):
                g = [x for x in gs if x["key"] == SFO["key"]][0]
                new = dict(one(ledger, g, a0, b0, freq, sfo_scaled(ledger, cli)), label=g["label"], name=g["name"], creek=None)
                new["official"] = any(cli.get((a0 + i * H).strftime("%Y-%m-%d")) is not None for i in range(int((b0 - a0) / H) + 1))
                e["gauges"] = [new if r["key"] == SFO["key"] else r for r in e["gauges"]]
                e.pop("vs_sfo", None)
        if "vs_sfo" not in e:
            fr = [r for r in e["gauges"] if r["key"] == focus_key]
            sr = [r for r in e["gauges"] if r["key"] == SFO["key"] and not r.get("missing")]
            e["vs_sfo"] = round(fr[0]["total"] / sr[0]["total"], 2) if fr and sr and sr[0]["total"] >= 0.1 else None
        if not e.get("wind"):
            e["wind"] = storm_wind(ledger, [g["key"] for g in gs], parse_t(e["start"]), parse_t(e["end"]))
        events.append(e)
    events.sort(key=lambda e: e["start"], reverse=True)
    return {"generated": hkey(now), "focus": FOCUS, "gauges": gs, "rules": {"dry_hours": dry_h, "min_in": min_in, "gap_from": list(GAP_FROM)},
            "since": prev.get("since") or (min((e["start"] for e in events), default=None)),
            "storms": events, "season": season(events, gs)}


def main(argv=None):
    a = list(argv if argv is not None else sys.argv)[1:]
    creeks_path = None
    if "--creeks" in a:
        i = a.index("--creeks"); creeks_path = a[i + 1]; del a[i:i + 2]
    tracker_path, out_path = a
    try:
        tracker = json.load(open(tracker_path))
    except (OSError, ValueError):
        print("bayside_compare: no storm_tracker.json; skipped"); return 0
    try:
        prev = json.load(open(out_path))
    except (OSError, ValueError):
        prev = {}
    creeks = []
    if creeks_path:
        try:
            creeks = json.load(open(creeks_path)).get("creeks", [])
        except (OSError, ValueError):
            pass
    freq, _ = load_rain_frequency()
    now = parse_t(tracker.get("generated") or hkey(dt.datetime.now()))
    out = build(tracker, creeks, freq or {}, now, prev)
    json.dump(out, open(out_path, "w"), separators=(",", ":"))
    print("bayside_compare: %d storms" % len(out["storms"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
