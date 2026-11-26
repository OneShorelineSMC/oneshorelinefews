"""AQPI / RRFS rain forecast vs the rain gauges (staff, 2026-11-21; Storm Tracker card "Rain forecast vs measured").

rrfs.py logs every RRFS run (AQPI / CW3E) in rrfs_log.csv: each creek's watershed-average rain, hour by hour, out to 3.5
days. After a storm, this step looks up the forecasts that were out ahead of it and checks them against the creek's main
rain gauge, the way the forecast is used on the staff pages:

  For each storm in storm_tracker.json (each creek, its own storm rules) and each lead time in LEADS (6 and 24 hours):
    the forecast   the newest hourly run issued at least that long before the storm's first wet hour, over the storm
                   plus PAD_H hours either side (so a forecast a little early or late still counts)
    measured       the creek's main rain gauge over the storm (storm_tracker.json)
    compared       total rain; the wettest 1, 3 and 6 hours (12 and 24 hours too for creeks rated over 24 hours,
                   creeks.csv rating_max_min) rated against NOAA Atlas 14 at that gauge, the same ratings as the rain
                   gauges and the forecast pages (Heavy, Very heavy, Intense); and when the wettest hour came
    verdict        caught (Heavy or more forecast and measured), missed (measured, not forecast), over-forecast
                   (forecast, not measured), or no Heavy (neither)
  Heavy forecast with no storm: every run at 00, 06, 12 and 18 UTC whose forecast reaches Heavy 6 to 24 hours ahead at a
  creek where the gauge then measured nothing Heavy (and no storm covers it), so over-forecasting shows up even when it
  stayed dry.

Hourly windows only: the forecast is hourly, so the gauges' 15- and 30-minute bursts aren't compared. The forecast is
a watershed average and the gauge is one point, so totals are expected to differ; the ratings and timing matter more.
Results for closed storms are kept as they are (rrfs_log.csv keeps 60 days), and dropped at the new water year.

Creeks with no gauge of their own (WATCH, staff 2026-11-24): the same check for a watershed in the RRFS log, against
the average of nearby rain gauges in the hourly record, rated against NOAA Atlas 14 at the watershed's center. Its storms
come from that average with the Storm Tracker's own rules (STORM_DRY_HOURS, STORM_MIN_IN). Cordilleras Creek: Belmont
and Pulgas (Pulgas alone has no Dec 2022 record; until the hourly record has Pulgas, Belmont x 1.1, the Atlas 14 ratio of
the watershed's center to Belmont). Basis: lookups/CORDILLERAS_BASIS.md.

Writes rrfs_review.json (the Storm Tracker shows it) and rrfs_review.csv (one row per storm and lead time).

Usage: python rrfs_review.py out/storm_tracker.json out/rrfs_log.csv out/rrfs_review.json [--creeks out/creeks.json]
"""

import csv
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import load_rain_frequency   # noqa: E402
from storm_tracker import rate, window_peak, hkey, parse_t, water_year_start, drop_repeats   # noqa: E402

LOOKUPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups")
PAC, UTC = ZoneInfo("America/Los_Angeles"), dt.timezone.utc
LEADS = [6, 24]          # hours ahead of the storm's first wet hour
PAD_H = 3                # the forecast is read over the storm plus this many hours either side
HORIZON_H = 84           # the hourly product's reach (3.5 days)
FA_RUN_HOURS = (0, 6, 12, 18)   # runs checked for "Heavy forecast with no storm" (UTC)
FA_FROM_H, FA_TO_H = 6, 24      # ... over this stretch after the run
H = dt.timedelta(hours=1)
# The review starts here (Pacific): runs logged before it lacked the full AQPI datasets, so their forecasts, the storms they
# would be checked against and "Heavy forecast with no storm" from them are left out, including any already kept in
# rrfs_review.json (staff, 2026-11-22: reset). None = from the start of the log.
REVIEW_FROM = "2026-11-22 07:00"
# Watersheds with no creek gauge, checked against nearby rain gauges (see the docstring). freq: NOAA Atlas 14 (PDS,
# inches) at the watershed's center, {minutes: {years: depth}}; Heavy, Very heavy and Intense are the 1-, 2- and 5-year
# depths, as for the gauges in rain_frequency.csv.
WATCH = [{
    "id": "ws:CORDILLERAS CREEK", "name": "Cordilleras Creek (no gauge)", "gauges": ["bel_rain", "pul_rain"], "one_scale": 1.1,
    "label": "Belmont + Pulgas", "minutes": [60, 180, 360, 720, 1440],
    "freq": {60: {1: 0.472, 2: 0.577, 5: 0.717, 10: 0.834, 25: 0.998, 100: 1.26},
             180: {1: 0.868, 2: 1.05, 5: 1.30, 10: 1.51, 25: 1.80, 100: 2.26},
             360: {1: 1.23, 2: 1.50, 5: 1.87, 10: 2.18, 25: 2.60, 100: 3.29},
             720: {1: 1.61, 2: 2.00, 5: 2.53, 10: 2.98, 25: 3.60, 100: 4.60},
             1440: {1: 1.97, 2: 2.50, 5: 3.21, 10: 3.80, 25: 4.63, 100: 5.97}}}]


def watch_freq(w):
    return {"minutes": {m: dict(v) for m, v in w["freq"].items()}, "levels": {m: [v[1], v[2], v[5]] for m, v in w["freq"].items()}}


def watch_series(ledger, w):
    """{hour: inches} for a watershed: the average of its gauges over the hours each has a record for (a gauge's record
    starts at its first logged hour); an hour with one gauge only is that gauge times one_scale (Belmont alone x 1.1)."""
    recs = {}
    for k in w["gauges"]:
        h = {parse_t(t): float(v) for t, v in ((ledger.get(k) or {}).get("h") or {}).items()}
        if h:
            recs[k] = (min(h), h)
    out = {}
    for hr in sorted({t for _, h in recs.values() for t in h}):
        vals = [h.get(hr, 0.0) for t0, h in recs.values() if hr >= t0]
        if not vals:
            continue
        out[hr] = (sum(vals) / len(vals)) if len(vals) > 1 else vals[0] * w.get("one_scale", 1.0)
    return out


def watch_storms(ledger, rules, now, w):
    """Storms in a watershed's average series, by the Storm Tracker's rules, in the shape check_storm reads."""
    dry, mn, wet = int(rules.get("STORM_DRY_HOURS", 6)), float(rules.get("STORM_MIN_IN", 0.1)), float(rules.get("STORM_WET_IN", 0.01))
    ser = watch_series(ledger, w)
    hrs = [t for t in sorted(ser) if ser[t] >= wet]
    groups, cur = [], []
    for t in hrs:
        if cur and (t - cur[-1]) > dry * H:
            groups.append(cur); cur = []
        cur.append(t)
    if cur:
        groups.append(cur)
    out = []
    for g in groups:
        a, b = g[0], g[-1]
        part = {t: v for t, v in ser.items() if a <= t <= b}
        tot = round(sum(part.values()), 2)
        if tot < mn:
            continue
        gauge = {"label": w["label"], "number": w["id"], "total": tot, "series": [[hkey(t), round(v, 3)] for t, v in sorted(part.items())],
                 "peaks": {str(m): {"in": window_peak(part, a, b, m // 60)[0]} for m in w["minutes"]}}
        out.append(({"creek": w["id"], "name": w["name"], "start": hkey(a), "end": hkey(b), "rain": [gauge]}, b <= now - dry * H))
    return out


def to_local(s):
    """'2026-11-20T16:00Z' (UTC) -> naive Pacific datetime."""
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ").replace(tzinfo=UTC).astimezone(PAC).replace(tzinfo=None)


def read_log(path):
    """{run (Pacific): {creek: {hour (Pacific, period-beginning like the storm ledger): (avg, max)}}} for the hourly
    product. A step ending 10:00 is the rain of 9:00-10:00, the ledger's 9:00 hour."""
    runs = {}
    try:
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                if r.get("product_min") != "60":
                    continue
                run = to_local(r["run_utc"])
                byc = runs.setdefault(run, {})
                if not r.get("creek") or not r.get("step_end_utc"):
                    continue
                h = to_local(r["step_end_utc"]) - H
                byc.setdefault(r["creek"], {})[h] = (float(r["in_avg"] or 0), float(r["in_max"] or 0))
    except OSError:
        pass
    return runs


def rating_windows(path=os.path.join(LOOKUPS, "creeks.csv")):
    """{creek: [minutes compared]}: 1, 3, 6 hours; 12 and 24 too where creeks.csv rating_max_min is 1440 or more."""
    out = {}
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                try:
                    mx = int(float(r.get("rating_max_min") or 360))
                except ValueError:
                    mx = 360
                out[r.get("creek") or r.get("id")] = [m for m in (60, 180, 360, 720, 1440) if m <= max(mx, 360)]
    except OSError:
        pass
    return out


def best_level(freq, mins, depth_of):
    """(level 0-3 or None, minutes, inches, years) of the rarest window; depth_of(minutes) gives inches."""
    best = None
    for m in mins:
        d = depth_of(m)
        r = rate(freq, m, d)
        if r is None:
            continue
        key = (r["level"], d / max(freq["levels"][m][0], 1e-6))
        if best is None or key > best[0]:
            best = (key, m, d, r["years"])
    if best is None:
        return None, None, None, None
    return best[0][0], best[1], round(best[2], 2), best[3]


def verdict(fl, ml):
    if fl is None or ml is None:
        return "not rated"
    if ml >= 1 and fl >= 1:
        return "caught"
    if ml >= 1:
        return "missed"
    if fl >= 1:
        return "over-forecast"
    return "no Heavy"


def main_gauge(st):
    main = [g for g in st.get("rain", []) if not g.get("support")] or st.get("rain", [])
    return main[0] if main else None


def check_storm(st, runs, freq, mins):
    g = main_gauge(st)
    if not g:
        return None
    start, end = parse_t(st["start"]), parse_t(st["end"])
    f = freq.get(str(g.get("number"))) if freq else None
    series = {parse_t(t): v for t, v in g.get("series", [])}
    m_lv, m_min, m_in, m_yr = best_level(f, mins, lambda m: (g.get("peaks", {}).get(str(m)) or {}).get("in") or 0.0) if f else (None,) * 4
    m_wet = max(series.items(), key=lambda x: (x[1], -x[0].timestamp())) if series else None
    out = {"creek": st["creek"], "name": st.get("name"), "start": st["start"], "end": st["end"], "gauge": g.get("label"),
           "measured": {"total": g.get("total"), "level": m_lv, "minutes": m_min, "in": m_in, "years": m_yr,
                        "wettest": {"at": hkey(m_wet[0]), "in": m_wet[1]} if m_wet and m_wet[1] > 0 else None},
           "leads": {}}
    w0, w1 = start - PAD_H * H, end + PAD_H * H
    for L in LEADS:
        cut = start - L * H
        cands = [r for r in runs if r <= cut]
        if not cands:
            out["leads"][str(L)] = None
            continue
        run = max(cands)
        if run < cut - dt.timedelta(hours=6):   # the log has a gap: no run near that lead time
            out["leads"][str(L)] = None
            continue
        fc = runs[run].get(st["creek"], {})
        avg = {h: v[0] for h, v in fc.items() if w0 <= h <= w1}
        mx = {h: v[1] for h, v in fc.items() if w0 <= h <= w1}
        covers = run + HORIZON_H * H >= w1
        f_lv, f_min, f_in, f_yr = best_level(f, mins, lambda m: window_peak(avg, w0, w1, m // 60)[0]) if f else (None,) * 4
        f_wet = max(avg.items(), key=lambda x: (x[1], -x[0].timestamp())) if avg else None
        timing = None
        if f_wet and f_wet[1] > 0.01 and out["measured"]["wettest"]:
            timing = round((f_wet[0] - m_wet[0]).total_seconds() / 3600)
        out["leads"][str(L)] = {"run": hkey(run), "hours_ahead": round((start - run).total_seconds() / 3600),
                                "covers": covers, "total": round(sum(avg.values()), 2), "total_max": round(sum(mx.values()), 2),
                                "level": f_lv, "minutes": f_min, "in": f_in, "years": f_yr,
                                "wettest": {"at": hkey(f_wet[0]), "in": round(f_wet[1], 2)} if f_wet and f_wet[1] > 0 else None,
                                "timing_h": timing, "verdict": verdict(f_lv, m_lv)}
    return out


def heavy_no_storm(runs, ledger, creeks, storms, freq, mins_of, now, done):
    """Runs (00/06/12/18 UTC) whose forecast reaches Heavy 6-24 hours ahead at a creek with no storm then and nothing
    Heavy at its main gauge. done: {(creek, run)} already checked."""
    out = []
    by_creek = {}
    for st in storms:
        by_creek.setdefault(st["creek"], []).append((parse_t(st["start"]), parse_t(st["end"])))
    for run in sorted(runs):
        if run.replace(tzinfo=PAC).astimezone(UTC).hour not in FA_RUN_HOURS:
            continue
        a, b = run + FA_FROM_H * H, run + FA_TO_H * H
        if b > now - 2 * H:
            continue
        for c in creeks:
            cid = c["id"]
            if (cid, hkey(run)) in done or not c.get("rain"):
                continue
            g = c["rain"][0]
            f = freq.get(str(g.get("number"))) if freq else None
            if not f:
                continue
            mins = mins_of.get(cid, [60, 180, 360])
            fc = {h: v[0] for h, v in runs[run].get(cid, {}).items() if a <= h <= b}
            f_lv, f_min, f_in, _ = best_level(f, mins, lambda m: window_peak(fc, a, b, m // 60)[0])
            if not f_lv:
                continue
            if any(s <= b and e >= a for s, e in by_creek.get(cid, [])):
                continue   # a storm covers it: checked with the storm
            rec = (ledger.get(g["key"]) or {}).get("h")
            if rec is None:
                continue   # the hourly record doesn't have this gauge
            meas = {parse_t(t): v for t, v in rec.items() if a <= parse_t(t) <= b}
            m_lv, _, m_in, _ = best_level(f, mins, lambda m: window_peak(meas, a, b, m // 60)[0])
            if m_lv:
                continue
            out.append({"creek": cid, "name": c.get("name"), "run": hkey(run), "from": hkey(a), "to": hkey(b),
                        "level": f_lv, "minutes": f_min, "in": f_in, "measured_total": round(sum(meas.values()), 2)})
    return out


def summarize(storms, fas):
    out = {}
    for s in storms:
        e = out.setdefault(s["creek"], {"name": s.get("name"), "storms": 0, "leads": {}, "heavy_no_storm": 0})
        e["storms"] += 1
        for L, x in s["leads"].items():
            if not x:
                continue
            d = e["leads"].setdefault(L, {"caught": 0, "missed": 0, "over-forecast": 0, "no Heavy": 0, "not rated": 0, "ratios": [], "timing": []})
            d[x["verdict"]] += 1
            if s["measured"]["total"] and s["measured"]["total"] >= 0.1:
                d["ratios"].append(x["total"] / s["measured"]["total"])
            if x["timing_h"] is not None:
                d["timing"].append(x["timing_h"])
    for fa in fas:
        out.setdefault(fa["creek"], {"name": fa.get("name"), "storms": 0, "leads": {}, "heavy_no_storm": 0})["heavy_no_storm"] += 1
    med = lambda v: sorted(v)[len(v) // 2] if v else None
    for e in out.values():
        for d in e["leads"].values():
            r, t = d.pop("ratios"), d.pop("timing")
            d["median_ratio"] = round(med(r), 2) if r else None
            d["median_timing_h"] = med(t)
            d["rated"] = len(r)
    return out


def review(tracker, runs, freq, mins_of, creeks, now, prev=None, since=REVIEW_FROM):
    prev = prev or {}
    wy0 = hkey(dt.datetime.combine(water_year_start(now.date()), dt.time()))
    s0 = wy0   # storms from here: with a reset, the first a run after it could have forecast (the shortest lead)
    if since:   # the reset: nothing before it counts, kept results included
        wy0 = max(wy0, since)
        s0 = max(s0, hkey(parse_t(since) + min(LEADS) * H))
        runs = {r: v for r, v in runs.items() if hkey(r) >= since}
    first = min(runs) if runs else None
    kept = {(s["creek"], s["start"]): s for s in prev.get("storms", []) if s.get("closed") and s["start"] >= s0}
    storms = []
    for st in tracker.get("storms", []) + tracker.get("open", []):
        closed = st in tracker.get("storms", [])
        k = (st["creek"], st["start"])
        if st["start"] < s0:
            continue
        if k in kept:
            storms.append(kept[k]); continue
        if first is None or parse_t(st["start"]) - min(LEADS) * H < first:
            continue   # before the log began: no forecast to check
        s = check_storm(st, runs, freq, mins_of.get(st["creek"], [60, 180, 360]))
        if s:
            s["closed"] = closed
            storms.append(s)
    for w in WATCH:   # watersheds with no creek gauge, against nearby rain gauges
        wf = dict(freq or {}); wf[w["id"]] = watch_freq(w)
        for st, closed in watch_storms(tracker.get("ledger", {}), tracker.get("rules", {}), now, w):
            k = (st["creek"], st["start"])
            if st["start"] < s0:
                continue
            if k in kept:
                storms.append(kept[k]); continue
            if first is None or parse_t(st["start"]) - min(LEADS) * H < first:
                continue
            s = check_storm(st, runs, wf, w["minutes"])
            if s:
                s["closed"] = closed
                storms.append(s)
        # kept results whose hours have left the hourly record (the record keeps about a week; the creeks' own storms stay in
        # storm_tracker.json all year, these don't)
        have = {(x["creek"], x["start"]) for x in storms}
        storms += [v for k, v in kept.items() if k[0] == w["id"] and k not in have]
    fas = [x for x in prev.get("heavy_no_storm", []) if x["run"] >= wy0]
    done = {(x["creek"], x["run"]) for x in fas} | set(tuple(x) for x in prev.get("checked_runs", []))
    new = heavy_no_storm(runs, tracker.get("ledger", {}), creeks, tracker.get("storms", []) + tracker.get("open", []), freq, mins_of, now, done)
    fas += new
    # every run+creek checked (so a run isn't checked again once the ledger has moved on), this water year only
    checked = sorted({(c["id"], hkey(r)) for r in runs for c in creeks
                      if r.replace(tzinfo=PAC).astimezone(UTC).hour in FA_RUN_HOURS and r + FA_TO_H * H <= now - 2 * H} | done)
    checked = [list(x) for x in checked if x[1] >= wy0]
    # a storm whose first hours have left the hourly record is found again starting later: keep the first one only
    storms = drop_repeats(storms)
    storms.sort(key=lambda s: (s["start"], s["creek"]), reverse=True)
    fas.sort(key=lambda x: x["run"], reverse=True)
    return {"generated": hkey(now), "leads": LEADS, "pad_hours": PAD_H, "log_from": max(hkey(first), since or "") if first else since,
            "storms": storms, "heavy_no_storm": fas, "summary": summarize(storms, fas), "checked_runs": checked}


def write_csv(path, out):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["creek", "storm_start", "storm_end", "gauge", "measured_in", "measured_rating", "lead_h", "run",
                    "forecast_in", "forecast_wettest_point_in", "forecast_rating", "timing_h", "verdict"])
        for s in out["storms"]:
            for L, x in s["leads"].items():
                m = s["measured"]
                w.writerow([s["creek"], s["start"], s["end"], s["gauge"], m["total"], m["level"], L,
                            x["run"] if x else "", x["total"] if x else "", x["total_max"] if x else "",
                            x["level"] if x else "", x["timing_h"] if x else "", x["verdict"] if x else "no forecast"])


def main(argv=None):
    a = list(argv if argv is not None else sys.argv)[1:]
    creeks_path = None
    if "--creeks" in a:
        i = a.index("--creeks"); creeks_path = a[i + 1]; del a[i:i + 2]
    tracker_path, log_path, out_path = a
    try:
        tracker = json.load(open(tracker_path))
    except (OSError, ValueError):
        print("rrfs_review: no storm_tracker.json; skipped"); return 0
    try:
        prev = json.load(open(out_path))
    except (OSError, ValueError):
        prev = {}
    creeks = []
    if creeks_path:
        try:
            cj = json.load(open(creeks_path))
            creeks = cj.get("creeks", []) + cj.get("creeks_preview", [])
        except (OSError, ValueError):
            pass
    freq, _ = load_rain_frequency()
    now = parse_t(tracker.get("generated") or hkey(dt.datetime.now(PAC).replace(tzinfo=None)))
    out = review(tracker, read_log(log_path), freq or {}, rating_windows(), creeks, now, prev)
    json.dump(out, open(out_path, "w"), separators=(",", ":"))
    write_csv(out_path.replace(".json", ".csv"), out)
    print("rrfs_review: %d storms checked, %d Heavy forecasts with no storm" % (len(out["storms"]), len(out["heavy_no_storm"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
