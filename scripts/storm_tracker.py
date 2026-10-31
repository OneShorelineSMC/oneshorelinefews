"""
Storm tracker (staff page StormTracker.html): each rain event at each creek, and a season summary per creek.

Runs in the data job after fetch_onerain.py, reading the fresh creeks.json (the last 50 hours of every creek gauge).
creeks.json only reaches back 50 hours, so this keeps its own record in storm_tracker.json on the data branch:

  ledger    the last KEEP_DAYS days, hour by hour: rain at each rain gauge (inches in the hour, raw reports summed),
            each creek level gauge's highest reading in the hour.
  days      the water year (from Oct 1), day by day: rain at each rain gauge, each level gauge's highest reading, each
            creek's highest status, and how often each gauge was reporting.
  storms    finished storms, written once and then kept as they are (with their hourly series, for the graphs).
  open      storms still going (or ended less than STORM_DRY_HOURS + STORM_RESPONSE_HOURS ago), redone every run.

A storm at a creek (the same rules for every creek, and for the history the archive fills in later):
  - an hour is wet when any of the creek's rain gauges (its own and its supporting gauges) has at least STORM_WET_IN;
  - wet hours less than STORM_DRY_HOURS apart belong to the same storm; it starts at its first wet hour and ends at
    its last;
  - it counts when one of the creek's gauges has at least STORM_MIN_IN in it;
  - the creek's response is read from the storm's start to STORM_RESPONSE_HOURS after its end (the creek peaks after
    the rain), and a storm is closed (frozen) once that time has passed and no new rain has joined it.
For each rain gauge: total and the peak 15 min, 30 min, 1, 3, 6, 12 and 24 hr amounts, each rated against NOAA Atlas 14
at that gauge (lookups/rain_frequency.csv: level 1-3 = Heavy / Very heavy / Intense, and a rough storm size in years).
15 and 30 minutes come from the data job's own rolling totals, sampled every run while the storm is open.
For each level gauge: peak and when, hours at or above each flood level, rising fast seen, and the lag from the
heaviest hour of rain to the peak. For the creek: its highest status during the storm, and gauges that went quiet.

Settings (lookups/settings.csv; the same ranges as lookups.js): STORM_DRY_HOURS, STORM_MIN_IN, STORM_WET_IN,
STORM_RESPONSE_HOURS. Basis: lookups/THRESHOLDS_BASIS.md §12.

Usage: python storm_tracker.py CREEKS.json STORM_TRACKER.json
"""

import csv
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import load_rain_frequency, storm_years   # noqa: E402

LOOKUPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups")
SETTINGS = {"STORM_DRY_HOURS": [6, 1, 48], "STORM_MIN_IN": [0.1, 0.01, 2], "STORM_WET_IN": [0.01, 0.01, 0.2],
            "STORM_RESPONSE_HOURS": [12, 0, 48]}
KEEP_DAYS = 10                          # hourly record kept (a storm can't be longer than this and still be found)
PEAK_HOURS = [1, 3, 6, 12, 24]          # peak rain windows read from the hourly record
SUB_HOURLY = ["15", "30"]               # and from the data job's rolling totals (minutes)
STATUS_RANK = {"none": 0, "alert": 1, "ready": 2, "likely": 3}   # offline / delayed don't count
HFMT = "%Y-%m-%d %H:00"


def load_settings(path=os.path.join(LOOKUPS, "settings.csv")):
    vals = {k: v[0] for k, v in SETTINGS.items()}
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                k = (r.get("key") or "").strip()
                if k in SETTINGS:
                    try:
                        v = float((r.get("value") or "").strip())
                    except ValueError:
                        continue
                    if SETTINGS[k][1] <= v <= SETTINGS[k][2]:
                        vals[k] = v
    except OSError:
        pass
    return vals


def parse_t(s):
    return dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def hkey(t):
    return t.strftime(HFMT)


def water_year_start(d):
    return dt.date(d.year if d.month >= 10 else d.year - 1, 10, 1)


def wy_label(start):
    return "WY%d" % (start.year + 1)


def creek_gauges(c):
    """(rain gauges, level gauges) of a creek: [{"key", "label", "number", ...}]."""
    rain = [dict(g, support=False) for g in c.get("rain", [])] + [dict(g, support=True) for g in c.get("rain_support", [])]
    return rain, list(c.get("stages", []))


# --------------------------------------------------------------------------------------------- the hourly record
def merge_ledger(ledger, sensors, now):
    """Adds the hours creeks.json covers to the record: rain summed per hour, levels the highest per hour. creeks.json
    covers every hour after its first reading fully, so those hours are replaced (a late report fixes an hour, and a
    rain hour with no reports is dry); the first, partial hour only adds to what the record has."""
    for key, e in sensors.items():
        pts = [(parse_t(p[0]), p[1]) for p in e.get("points") or [] if p and p[1] is not None]
        lt = e.get("latest")
        if lt and lt[0] and lt[1] is not None and (not pts or parse_t(lt[0]) > pts[-1][0]):
            pts.append((parse_t(lt[0]), lt[1]))
        pts = sorted(p for p in pts if p[0] <= now + dt.timedelta(minutes=10))
        if not pts:
            continue
        rain = str(e.get("kind", "")).startswith("rain")
        rec = ledger.setdefault(key, {"kind": "rain" if rain else "level", "h": {}})
        hours = {}
        for t, v in pts:
            # a rain report at 10:00 is the rain of 9:00-10:00; one at 10:05 is in the 10:00 hour
            h = (t - dt.timedelta(minutes=1) if rain else t).replace(minute=0, second=0)
            v = float(v)
            hours[h] = hours.get(h, 0.0) + max(v, 0.0) if rain else max(hours.get(h, v), v)
        first = min(hours)
        if rain:   # hours after the first: replaced (no reports = dry)
            for k in [k for k in rec["h"] if parse_t(k) > first]:
                del rec["h"][k]
        for h, v in hours.items():
            k, v = hkey(h), round(v, 3 if rain else 2)
            if h == first and k in rec["h"]:
                v = max(v, rec["h"][k])
            if rain and v <= 0:
                rec["h"].pop(k, None)   # dry hours aren't stored
            else:
                rec["h"][k] = v
    cut = hkey(now - dt.timedelta(days=KEEP_DAYS))
    for rec in ledger.values():
        rec["h"] = {k: v for k, v in rec["h"].items() if k >= cut}
    return ledger


def hours_of(ledger, key):
    return {parse_t(k): v for k, v in (ledger.get(key) or {}).get("h", {}).items()}


# --------------------------------------------------------------------------------------------- storms
def find_storms(rain_series, S):
    """[(first wet hour, last wet hour)] from the creek's rain gauges' hourly rain."""
    wet = sorted({h for s in rain_series for h, v in s.items() if v >= S["STORM_WET_IN"] - 1e-9})
    out, gap = [], dt.timedelta(hours=S["STORM_DRY_HOURS"])
    for h in wet:
        if out and h - out[-1][1] < gap:
            out[-1][1] = h
        else:
            out.append([h, h])
    return [tuple(x) for x in out]


def window_peak(series, start, end, hours):
    """Largest rain in any `hours` consecutive hours within [start, end], and the hour that window ends."""
    best, best_end, h = 0.0, None, start
    while h <= end + dt.timedelta(hours=hours - 1):
        s = sum(series.get(h - dt.timedelta(hours=i), 0) for i in range(hours) if start <= h - dt.timedelta(hours=i) <= end)
        if s > best + 1e-9:
            best, best_end = s, h
        h += dt.timedelta(hours=1)
    return round(best, 2), best_end


def rate(freq, minutes, depth):
    """{"level": 0-3, "years": rough storm size} for a depth over `minutes` at a gauge (None without Atlas 14 values)."""
    if not freq or depth is None:
        return None
    lv = freq.get("levels", {}).get(minutes)
    by = freq.get("minutes", {}).get(minutes)
    if not lv:
        return None
    level = 3 if depth >= lv[2] else 2 if depth >= lv[1] else 1 if depth >= lv[0] else 0
    return {"level": level, "years": storm_years(by, depth) if by and depth > 0 else None}


def build_storm(c, start, end, ledger, S, freq, now, track):
    rain_g, stage_g = creek_gauges(c)
    resp_end = min(end + dt.timedelta(hours=S["STORM_RESPONSE_HOURS"]), now.replace(minute=0, second=0))
    st = {"creek": c["id"], "name": c["name"], "start": hkey(start), "end": hkey(end),
          "hours": int((end - start).total_seconds() // 3600) + 1, "rain": [], "levels": [],
          "status": None, "quiet": sorted(track.get("quiet", [])), "rising_fast": bool(track.get("rising_fast"))}
    rank = track.get("status_rank")
    if rank is not None:
        st["status"] = [k for k, v in STATUS_RANK.items() if v == rank][0]
    peak_hour = None
    for g in rain_g:
        s = hours_of(ledger, g["key"])
        total = round(sum(v for h, v in s.items() if start <= h <= end), 2)
        f = freq.get(str(g.get("number"))) if freq else None
        peaks, best = {}, None
        for m in SUB_HOURLY:   # sampled every run while the storm was open
            v = (track.get("sub") or {}).get(g["key"], {}).get(m)
            if v is not None:
                peaks[m] = {"in": round(v, 2), "rate": rate(f, int(m), v)}
        for hrs in PEAK_HOURS:
            v, at = window_peak(s, start, end, hrs)
            peaks[str(hrs * 60)] = {"in": v, "rate": rate(f, hrs * 60, v)}
            if hrs == 1 and v > 0 and not g["support"] and (peak_hour is None or v > peak_hour[1]):
                peak_hour = (at, v)
        for m, p in peaks.items():
            r = p["rate"]
            if r and r["level"] and (best is None or (r["level"], p["in"] / max(f["levels"][int(m)][0], 1e-6)) >
                                     (best[0], best[2])):
                best = (r["level"], m, p["in"] / max(f["levels"][int(m)][0], 1e-6), r["years"])
        st["rain"].append({"key": g["key"], "label": g.get("label"), "number": g.get("number"), "support": g["support"],
                           "total": total, "peaks": peaks,
                           "rarest": {"level": best[0], "minutes": int(best[1]), "years": best[3]} if best else None,
                           "series": [[hkey(h), round(v, 2)] for h, v in sorted(s.items()) if start <= h <= end]})
    for g in stage_g:
        s = {h: v for h, v in hours_of(ledger, g["key"]).items() if start - dt.timedelta(hours=6) <= h <= resp_end}
        inside = {h: v for h, v in s.items() if start <= h <= resp_end}
        if not inside:
            st["levels"].append({"key": g["key"], "label": g.get("label"), "number": g.get("number"), "peak": None})
            continue
        ph = max(inside, key=lambda h: (inside[h], -h.timestamp()))
        lv = []
        for t in g.get("thresholds") or []:
            n = sum(1 for v in inside.values() if v >= t["value"])
            lv.append({"name": t["name"], "level": t.get("level"), "value": t["value"], "hours": n})
        reached = max([t["level"] or 0 for t in lv if t["hours"]] or [0])
        # the lag means something only when the creek rose after the heaviest rain
        base = s.get(start, min(inside.values()))
        lag = (ph - peak_hour[0]).total_seconds() / 3600 if peak_hour and peak_hour[0] else None
        if lag is not None and (lag < 0 or inside[ph] - base < 0.1):
            lag = None
        st["levels"].append({"key": g["key"], "label": g.get("label"), "number": g.get("number"), "tidal": bool(g.get("tidal")),
                             "start_value": s.get(start), "peak": inside[ph], "peak_at": hkey(ph), "reached": reached, "thresholds": lv,
                             "lag_hours": round(lag, 1) if lag is not None else None,
                             "series": [[hkey(h), v] for h, v in sorted(s.items())]})
    main = [r for r in st["rain"] if not r["support"]] or st["rain"]
    st["total"] = max([r["total"] for r in main] or [0])
    tops = [r["rarest"]["level"] for r in st["rain"] if r["rarest"]]
    st["rain_level"] = max(tops) if tops else (0 if any(freq.get(str(r["number"])) for r in st["rain"]) else None)
    st["reached"] = max([x.get("reached") or 0 for x in st["levels"]] or [0])
    return st


# --------------------------------------------------------------------------------------------- the season
def season_summary(c, days, storms, wy0):
    rain_g, stage_g = creek_gauges(c)
    mine = [s for s in storms if s["creek"] == c["id"]]
    out = {"creek": c["id"], "name": c["name"], "storms": len(mine), "rain": [], "levels": [], "status_days": {},
           "watch": sum(1 for s in mine if s.get("reached", 0) >= 2), "warning": sum(1 for s in mine if s.get("reached", 0) >= 3)}
    for g in rain_g:
        d = days.get("rain", {}).get(g["key"], {})
        rep = days.get("report", {}).get(g["key"], {})
        runs, fresh = sum(v[1] for v in rep.values()), sum(v[0] for v in rep.values())
        out["rain"].append({"key": g["key"], "label": g.get("label"), "support": g["support"], "total": round(sum(d.values()), 2),
                            "wet_days": sum(1 for v in d.values() if v >= 0.01), "reporting": round(fresh / runs, 3) if runs else None})
    for g in stage_g:
        d = days.get("level", {}).get(g["key"], {})
        rep = days.get("report", {}).get(g["key"], {})
        runs, fresh = sum(v[1] for v in rep.values()), sum(v[0] for v in rep.values())
        top = max(d.items(), key=lambda kv: kv[1]) if d else None
        out["levels"].append({"key": g["key"], "label": g.get("label"), "max": top[1] if top else None, "max_day": top[0] if top else None,
                              "reporting": round(fresh / runs, 3) if runs else None})
    sd = days.get("status", {}).get(c["id"], {})
    for k, v in STATUS_RANK.items():
        out["status_days"][k] = sum(1 for x in sd.values() if x == v)
    if mine:
        big = max(mine, key=lambda s: ((s.get("rain_level") or 0), s.get("total") or 0))
        out["biggest"] = {"start": big["start"], "total": big["total"], "rain_level": big.get("rain_level"), "reached": big.get("reached")}
    return out


def update_days(days, ledger, creeks, sensors, now):
    """Day totals for the water year, redone from the hourly record for the days it covers; older days are kept."""
    covered = {}
    for key, rec in ledger.items():
        for k, v in rec["h"].items():
            covered.setdefault(key, {}).setdefault(k[:10], []).append(v)
    first = (now - dt.timedelta(days=KEEP_DAYS - 1)).strftime("%Y-%m-%d")   # the oldest record day may be partial
    for key, by_day in covered.items():
        kind = ledger[key]["kind"]
        tgt = days.setdefault("rain" if kind == "rain" else "level", {}).setdefault(key, {})
        for d, vals in by_day.items():
            if d >= first:
                tgt[d] = round(sum(vals), 2) if kind == "rain" else max(vals)
    today = now.strftime("%Y-%m-%d")
    for key, e in sensors.items():   # how often each gauge was reporting (each run counts once)
        r = days.setdefault("report", {}).setdefault(key, {}).setdefault(today, [0, 0])
        r[1] += 1
        sig = e.get("signals") or {}
        if (sig.get("fresh") if "fresh" in sig else bool(sig.get("trend"))) and not e.get("error"):
            r[0] += 1
    for c in creeks:
        k = (c.get("status") or {}).get("key")
        if k in STATUS_RANK:
            sd = days.setdefault("status", {}).setdefault(c["id"], {})
            sd[today] = max(sd.get(today, 0), STATUS_RANK[k])
    return days


def run(creeks_json, previous, now, S=None, freq=None):
    S = S or load_settings()
    if freq is None:
        freq, _ = load_rain_frequency()
        freq = freq or {}
    wy0 = water_year_start(now.date())
    prev = previous or {}
    out = {"generated": now.strftime("%Y-%m-%d %H:%M"), "water_year": wy_label(wy0), "wy_start": wy0.isoformat(),
           "rules": {k: S[k] for k in SETTINGS}, "ledger": prev.get("ledger", {}), "days": prev.get("days", {}),
           "storms": prev.get("storms", []), "track": prev.get("track", {}), "previous": prev.get("previous"),
           # the first day this record covers (creeks.json reaches back about two days when it starts); the archive's
           # history can fill in earlier days later in the same format
           "since": prev.get("since") or max(wy0, (now - dt.timedelta(hours=48)).date()).isoformat()}
    if prev.get("water_year") and prev["water_year"] != out["water_year"]:   # a new water year: last season is kept as "previous"
        out["previous"] = {"water_year": prev["water_year"], "summary": prev.get("summary"), "storms": prev.get("storms", [])}
        out["days"], out["storms"] = {}, [s for s in prev.get("storms", []) if s["end"] >= hkey(dt.datetime.combine(wy0, dt.time()))]
        out["since"] = wy0.isoformat()
    sensors = creeks_json.get("sensors") or {}
    creeks = (creeks_json.get("creeks") or []) + (creeks_json.get("creeks_preview") or [])
    merge_ledger(out["ledger"], sensors, now)
    update_days(out["days"], out["ledger"], creeks, sensors, now)
    done = {(s["creek"], s["start"]) for s in out["storms"]}
    track, opened = out["track"], []
    hold = dt.timedelta(hours=S["STORM_DRY_HOURS"] + S["STORM_RESPONSE_HOURS"])
    for c in creeks:
        rain_g, stage_g = creek_gauges(c)
        series = [hours_of(out["ledger"], g["key"]) for g in rain_g]
        for start, end in find_storms(series, S):
            if (c["id"], hkey(start)) in done:
                continue
            total = max([round(sum(v for h, v in s.items() if start <= h <= end), 2) for s in series] or [0])
            if total < S["STORM_MIN_IN"] - 1e-9:
                continue
            # what this run sees for the storm (kept between runs while it is open): the 15- and 30-minute peaks,
            # rising fast, the creek's highest status and gauges that went quiet
            tk = next((v for k, v in track.items() if v.get("creek") == c["id"] and v.get("start", "") <= hkey(end)
                       and v.get("end", "") >= hkey(start - dt.timedelta(hours=S["STORM_DRY_HOURS"]))), None)
            tk = dict(tk or {}, creek=c["id"])
            if now - end < hold + dt.timedelta(hours=1):   # still open: sample this run
                for g in rain_g:
                    tot = ((sensors.get(g["key"]) or {}).get("signals") or {}).get("totals") or {}
                    sub = tk.setdefault("sub", {}).setdefault(g["key"], {})
                    for m in SUB_HOURLY:
                        if tot.get(m) is not None:
                            sub[m] = max(sub.get(m, 0), tot[m])
                for g in rain_g + stage_g:
                    sig = (sensors.get(g["key"]) or {}).get("signals") or {}
                    if sig.get("rising_fast"):
                        tk["rising_fast"] = True
                    if "fresh" in sig and not sig["fresh"]:
                        tk["quiet"] = sorted(set(tk.get("quiet", [])) | {g.get("label") or g["key"]})
                k = (c.get("status") or {}).get("key")
                if k in STATUS_RANK:
                    tk["status_rank"] = max(tk.get("status_rank", 0), STATUS_RANK[k])
            tk["start"], tk["end"] = hkey(start), hkey(end)
            st = build_storm(c, start, end, out["ledger"], S, freq, now, tk)
            if now - end >= hold:   # closed: written once, kept as it is
                st["closed"] = now.strftime("%Y-%m-%d %H:%M")
                out["storms"].append(st)
                done.add((c["id"], st["start"]))
            else:
                opened.append(st)
                track["%s|%s" % (c["id"], hkey(start))] = tk
    # tracking for storms that are still open only
    keep = {"%s|%s" % (s["creek"], s["start"]) for s in opened}
    out["track"] = {k: v for k, v in track.items() if k in keep}
    out["open"] = opened
    out["storms"].sort(key=lambda s: (s["start"], s["creek"]))
    out["summary"] = [season_summary(c, out["days"], out["storms"] + opened, wy0) for c in creeks]
    out["creeks"] = [{"id": c["id"], "name": c["name"], "short": c.get("short"), "preview_only": bool(c.get("preview_only")),
                      "status": (c.get("status") or {}).get("key")} for c in creeks]
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    creeks_path, out_path = args[0], args[1]
    with open(creeks_path) as f:
        cj = json.load(f)
    try:
        with open(out_path) as f:
            previous = json.load(f)
    except (OSError, ValueError):
        previous = {}
    gen = cj.get("generated")
    now = parse_t(gen) if gen else dt.datetime.now()
    out = run(cj, previous, now)
    with open(out_path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print("Storm tracker %s: %d storms closed, %d open; %d gauges in the hourly record" %
          (out["water_year"], len(out["storms"]), len(out["open"]), len(out["ledger"])))
    for s in out["open"]:
        print("  open: %s from %s, %.2f in so far" % (s["name"], s["start"], s["total"]))


if __name__ == "__main__":
    main()
