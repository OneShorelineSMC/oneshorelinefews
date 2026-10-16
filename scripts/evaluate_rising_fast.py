"""
Rapidly rising: test the rule (scripts/creek_signals.py rise_check) against gauge history. This produced the
results in lookups/RISING_FAST_BASIS.md; run it again after each winter, or when a setting changes.

    python scripts/evaluate_rising_fast.py --usgs <folder> --onerain <folder>

--usgs     the unzipped "usgs-data" download from the USGS history pull (files <site>_00065.csv)
--onerain  the unzipped download from the archive repo's "OneRain history pull" (files <gauge>.csv); optional

Every stage gauge in lookups/creek_gauges.csv with history in those folders is tested at several thresholds and at
its own rise_ft. Settings come from lookups/settings.csv. Output in out/: rising_fast_eval.csv and .md.

Times are UTC. "Big-storm level" for a gauge: its lowest flood level in thresholds.csv if it has one, otherwise the median of its
water-year peak stages (about a 2-year storm). An alert is one stretch of "rising fast" (readings < 3 h apart).
A crossing made by one reading that jumps at least 1 ft from a steady level (the two readings before it within
0.1 ft) and falls straight back by 80% or more is counted as a sensor spike, not a storm.
"""
import argparse
import bisect
import csv
import datetime as dt
import os
import random
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_config import CREEKS
from creek_signals import HOLD_TOLERANCE_FT, load_settings, rise_check

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S, _problems = load_settings()
RULES = (0.25, 0.5, 0.75, 1.0, 1.5)
EPISODE_GAP_H, LOOK_H = 3, 6
SPIKE_MIN_FT, SPIKE_FALLBACK, SPIKE_STEADY_FT = 1.0, 0.8, 0.1   # sensor spike: see evaluate()


def load(fn):
    """[(UTC time, value)] from a history file (USGS pull or OneRain pull: both have datetime_utc)."""
    T, V = [], []
    for r in csv.DictReader(open(fn)):
        try:
            v = float(r["value"])
        except ValueError:
            continue
        T.append(dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%dT%H:%M"))
        V.append(v)
    return T, V


def active_series(T, V, reports, th, settings=None):
    """rise_check evaluated at each reading (as if the data job ran just after it), in one pass."""
    S_ = settings or S
    n, on_change = len(T), reports != "interval"
    win = dt.timedelta(minutes=S_["RISE_MINUTES"])
    late = dt.timedelta(hours=S_["GAUGE_QUIET_HOURS"]) if on_change else dt.timedelta(minutes=S_["RISE_REF_LATE_MIN"])
    conf, hold = dt.timedelta(minutes=S_["RISE_CONFIRM_MIN"]), dt.timedelta(minutes=S_["RISE_HOLD_MIN"])
    rise = [None] * n
    for i in range(n):
        t0 = T[i] - win
        j = bisect.bisect_right(T, t0) - 1
        if j >= 0 and t0 - T[j] <= late:
            rise[i] = V[i] - V[j]
    meets = [False] * n
    for i in range(n):
        if rise[i] is not None and rise[i] >= th - 1e-9:
            ok = True
            near = i > 0 and T[i] - T[i - 1] <= conf
            if not S_["RISE_CONFIRM_MIN"]:
                pass   # 0 = confirmation off
            elif (on_change and (i == 0 or T[i] - T[i - 1] > win)) or (
                    near and (rise[i - 1] is None or rise[i - 1] < S_["RISE_CONFIRM_FRACTION"] * th - 1e-9)):
                ok = False
            meets[i] = ok
    act, last_met = [False] * n, None
    for i in range(n):
        if meets[i]:
            last_met = i
        k = last_met
        if k is not None and T[k] >= T[i] - hold:
            act[i] = V[i] >= V[k] - HOLD_TOLERANCE_FT
    return act, rise


def wy(t):
    return t.year + 1 if t.month >= 10 else t.year


def evaluate(T, V, act, big):
    eps = []
    for i in range(len(T)):
        if act[i]:
            if eps and T[i] - T[eps[-1][-1]] <= dt.timedelta(hours=EPISODE_GAP_H):
                eps[-1].append(i)
            else:
                eps.append([i])
    cross, lastc, spikes = [], None, 0
    for i in range(1, len(V)):
        if V[i - 1] < big <= V[i] and (lastc is None or T[i] - lastc > dt.timedelta(hours=24)):
            # a single bad reading that jumps at least 1 ft from a steady level and falls straight back (80% or more)
            # isn't a storm. A real rise is already climbing before its peak.
            jump = V[i] - V[i - 1]
            steady = i < 2 or abs(V[i - 1] - V[i - 2]) <= SPIKE_STEADY_FT
            if i + 1 < len(V) and steady and jump >= SPIKE_MIN_FT and V[i] - V[i + 1] >= SPIKE_FALLBACK * jump:
                spikes += 1
                continue
            cross.append(i)
            lastc = T[i]
    hit = 0
    for e in eps:
        j = bisect.bisect_right(T, T[e[0]] + dt.timedelta(hours=LOOK_H))
        if max(V[e[0]:j]) >= big:
            hit += 1
    leads = []
    for c in cross:
        a = bisect.bisect_left(T, T[c] - dt.timedelta(hours=LOOK_H))
        f = [k for k in range(a, c) if act[k]]   # an alert before the crossing reading
        if f:
            leads.append((T[c] - T[f[0]]).total_seconds() / 60)
    starts = [V[e[0]] for e in eps]
    return {"episodes": len(eps), "reached": hit, "crossings": len(cross), "spikes_not_counted": spikes,
            "warned": len(leads),
            "lead_med": round(statistics.median(leads)) if leads else None,
            "start_stage_med": round(statistics.median(starts), 2) if starts else None}


def gauges(usgs_dir, onerain_dir):
    for c in CREEKS:
        for g in c["stages"]:
            fn = (os.path.join(usgs_dir, f"{g['usgs_site']}_00065.csv") if g.get("source") == "usgs" and usgs_dir else
                  os.path.join(onerain_dir, f"{g['key']}.csv") if onerain_dir else None)
            if fn and os.path.exists(fn):
                yield g, fn, f"{c['name']}: {g.get('site_name') or g['label']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--usgs")
    ap.add_argument("--onerain")
    a = ap.parse_args()
    out, md = [], []
    for g, fn, name in gauges(a.usgs, a.onerain):
        key, rep = g["key"], g.get("reports", "interval")
        chosen = None if g.get("rise_off") else g.get("rise_ft") or S["RISE_FT"]
        T, V = load(fn)
        span_y = max(1e-9, (T[-1] - T[0]).days / 365.25)
        years = defaultdict(list)
        for t, v in zip(T, V):
            years[wy(t)].append(v)
        if g.get("thresholds"):
            lv = min(g["thresholds"], key=lambda x: x["value"])
            big, big_note = lv["value"], f"{lv['name']} ({lv['value']:.2f} ft)"
        else:
            if rep == "interval":   # 15-minute USGS-style data: years with at least 80% of readings
                full = [max(vs) for vs in years.values() if len(vs) > 0.8 * 365 * 96]
            else:                   # on-change gauges: years with readings in at least 10 months
                months = defaultdict(set)
                for t in T:
                    months[wy(t)].add(t.month)
                full = [max(vs) for y, vs in years.items() if len(months[y]) >= 10]
            if not full:
                print(f"{key}: skipped (no flood level and no full year of 15-minute data)")
                continue
            big, big_note = statistics.median(full), f"median annual peak ({statistics.median(full):.2f} ft)"
        # consistency: the one-pass simulation must agree with rise_check itself
        act05, rise = active_series(T, V, rep, 0.5)
        random.seed(1)
        for i in random.sample(range(200, len(T)), 300):
            lo = bisect.bisect_left(T, T[i] - dt.timedelta(hours=S["GAUGE_QUIET_HOURS"] + 6))
            r = rise_check(list(zip(T[lo:i + 1], V[lo:i + 1])), {"reports": rep}, T[i], S)
            assert bool(r) == act05[i], (key, T[i], r, act05[i])
        wet = sorted(r for r, t in zip(rise, T) if r is not None and t.month in (11, 12, 1, 2, 3, 4))
        pct = lambda p: wet[min(len(wet) - 1, int(p * len(wet)))]
        md.append(f"\n### {name} (`{key}`)\n\n{T[0]:%Y-%m-%d} to {T[-1]:%Y-%m-%d} ({span_y:.1f} years), "
                  f"reports {rep}. Big-storm level: {big_note}. Wet-season 60-min rise: 99th percentile "
                  f"{pct(.99):.2f} ft, 99.9th {pct(.999):.2f} ft, largest {wet[-1]:.2f} ft. "
                  f"Chosen: **{'off' if chosen is None else f'{chosen} ft'}**.\n\n"
                  "| Rule (ft in 60 min) | Alerts | Alerts / yr | Alerts followed by big-storm level within 6 h | "
                  "Big-storm crossings warned first | Median lead (min) |\n|---|---|---|---|---|---|")
        note = ""
        for th in RULES:
            act = act05 if th == 0.5 else active_series(T, V, rep, th)[0]
            e = evaluate(T, V, act, big)
            mark = " ◀" if th == chosen else ""
            per_year = f"{e['episodes'] / span_y:.1f}" if span_y >= 1 else "–"
            md.append(f"| {th}{mark} | {e['episodes']} | {per_year} | {e['reached']} | "
                      f"{e['warned']} of {e['crossings']} | {e['lead_med'] if e['lead_med'] is not None else '–'} |")
            if th == chosen:
                e0 = evaluate(T, V, active_series(T, V, rep, th, dict(S, RISE_CONFIRM_MIN=0))[0], big)
                note = (f"\nAt the chosen value: alerts began with the creek at a median {e['start_stage_med']} ft. "
                        f"Single-reading spikes through the big-storm level, not counted as storms: {e['spikes_not_counted']}. "
                        f"Without confirmation (RISE_CONFIRM_MIN = 0) there would be {e0['episodes']} alerts "
                          f"({abs(e0['episodes'] - e['episodes'])} {'more' if e0['episodes'] >= e['episodes'] else 'fewer'}), warning first of {e0['warned']} of {e0['crossings']} "
                        f"big-storm crossings (median lead {e0['lead_med']} min).\n")
            out.append(dict(gauge=key, name=name, rule_ft=th, chosen=th == chosen, years=round(span_y, 2),
                            big_storm_level_ft=round(big, 2), **e))
        if note:
            md.append(note)
        print(f"{key}: {len(T)} readings", flush=True)
    od = os.path.join(ROOT, "out")
    os.makedirs(od, exist_ok=True)
    with open(os.path.join(od, "rising_fast_eval.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    open(os.path.join(od, "rising_fast_eval.md"), "w").write("\n".join(md) + "\n")
    print(f"-> {od}/rising_fast_eval.md and .csv")


if __name__ == "__main__":
    main()
