"""
Creek status layer, part 1 (in development): signals computed by the data job for every gauge.
Nothing on the public pages reads these yet; they are written into creeks.json for the staff preview.

  Rain gauges:  rolling totals over 15 min - 48 hr, compared with NOAA Atlas 14 storms at that gauge
                (lookups/rain_frequency.csv) -> level 0-3 (none / Heavy / Very heavy / Severe), the duration
                and depth that set it, and a rough storm size (years) for staff.
  Stage gauges: trend (rising fast / rising / steady / falling) and the rapidly-rising check, using the
                same rule as the home page (RISE_* in lookups/settings.csv).

Times are Pacific clock times as naive datetimes, like the rest of the data job.
See lookups/THRESHOLDS_BASIS.md §8-11.
"""

import csv
import datetime as dt
import math
import os
import re

LOOKUPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups")
DURATIONS = [15, 30, 60, 120, 180, 360, 720, 1440, 2880]   # minutes (rain_frequency.csv)

# Settings the data job uses: built-in value, smallest and largest allowed (same ranges as lookups.js).
# Keys not in lookups/settings.csv yet use the built-in value (the proposed ones live in lookups/proposed/).
SETTINGS = {
    "RISE_FT": (0.5, 0.05, 10), "RISE_MINUTES": (60, 5, 720), "RISE_FRESH_MIN": (90, 5, 720),
    "RISE_TIDAL_RAIN_IN": (0.10, 0, 5), "RISE_TIDAL_RAIN_HOURS": (3, 0.25, 48),
    "GAUGE_QUIET_HOURS": (12, 0.5, 168), "GAUGE_QUIET_HOURS_INTERVAL": (3, 0.25, 168),
    "TREND_WINDOW_MIN": (30, 5, 240), "TREND_MAX_WINDOW_MIN": (120, 15, 360), "TREND_STEADY_FT_PER_HR": (0.1, 0.01, 2),
}


def _num(s):
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s or "") else None


def load_settings(path=os.path.join(LOOKUPS, "settings.csv")):
    """{key: value} for the keys above; (values, problems). Unknown keys are the pages' business."""
    vals = {k: v[0] for k, v in SETTINGS.items()}
    problems = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        return vals, [f"can't read settings.csv: {e}"]
    for n, r in enumerate(rows, start=2):
        k = (r.get("key") or "").strip()
        if k not in SETTINGS:
            continue
        v, (_, lo, hi) = _num((r.get("value") or "").strip()), SETTINGS[k]
        if v is None or not lo <= v <= hi:
            problems.append(f"settings.csv row {n}: {k} must be a number from {lo} to {hi}")
            continue
        vals[k] = v
    return vals, problems


def load_rain_frequency(path=os.path.join(LOOKUPS, "rain_frequency.csv")):
    """Atlas 14 depths by gauge: {onerain_number: {"minutes": {m: {ari: depth}}, "levels": {m: [d1, d2, d3]}}}.
    Returns (table, problems); with any problem the table is None (the job then keeps the last good one)."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        return None, [f"can't read rain_frequency.csv: {e}"]
    out, problems = {}, []
    for n, r in enumerate(rows, start=2):
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if not any(r.values()):
            continue
        w = f"rain_frequency.csv row {n}"
        num = r.get("onerain_number", "")
        m, ari, d = _num(r.get("minutes")), _num(r.get("ari_years")), _num(r.get("value_in"))
        if not re.fullmatch(r"[A-Za-z0-9]+", num):
            problems.append(f"{w}: onerain_number must be letters and digits"); continue
        if m not in DURATIONS:
            problems.append(f"{w}: minutes must be one of {' '.join(map(str, DURATIONS))}"); continue
        if ari is None or ari <= 0 or d is None or not 0 < d < 50:
            problems.append(f"{w}: ari_years and value_in must be positive numbers"); continue
        lvl = r.get("level", "")
        if lvl not in ("", "1", "2", "3"):
            problems.append(f"{w}: level must be 1, 2, 3 or blank"); continue
        g = out.setdefault(num, {"minutes": {}, "levels": {}})
        g["minutes"].setdefault(int(m), {})[ari] = d
        if lvl:
            g["levels"].setdefault(int(m), {})[int(lvl)] = d
    for num, g in out.items():
        for m, by_ari in g["minutes"].items():
            seq = [by_ari[a] for a in sorted(by_ari)]
            if seq != sorted(seq):
                problems.append(f"rain_frequency.csv: {num} {m} min depths must increase with storm size")
        for m in list(g["levels"]):
            lv = g["levels"][m]
            if sorted(lv) != [1, 2, 3] or not lv[1] <= lv[2] <= lv[3]:
                problems.append(f"rain_frequency.csv: {num} {m} min needs levels 1, 2 and 3, increasing")
                continue
            g["levels"][m] = [lv[1], lv[2], lv[3]]
    return (None if problems else out), problems


def _t(s):
    return dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S" if len(s) > 16 else "%Y-%m-%d %H:%M")


def _series(points, latest):
    """[(datetime, value)] sorted, with the sensor's 'latest' reading added if it is newer than the points."""
    p = [(_t(t), v) for t, v in points or []]
    if latest and latest[0] and latest[1] is not None:
        lt = _t(latest[0])
        if not p or lt > p[-1][0]:
            p.append((lt, latest[1]))
    p.sort(key=lambda x: x[0])
    return p


def rain_total(series, start, end):
    """Rain in (start, end], from rain increments."""
    return sum(v for t, v in series if start < t <= end and v > 0)


def storm_years(by_ari, depth):
    """Rough storm size for a depth (log-log interpolation between Atlas 14 values); None below the 1-year storm."""
    aris = sorted(by_ari)
    if depth < by_ari[aris[0]]:
        return None
    for a, b in zip(aris, aris[1:]):
        da, db = by_ari[a], by_ari[b]
        if depth <= db:
            if depth <= da or db <= da:
                return a
            f = (math.log(depth) - math.log(da)) / (math.log(db) - math.log(da))
            return round(math.exp(math.log(a) + f * (math.log(b) - math.log(a))), 1)
    return float(aris[-1])   # at or beyond the largest storm in the table


def rain_signals(points, latest, freq, now, quiet_hours):
    """Rolling totals and the rain level for one rain gauge (freq: this gauge's entry from load_rain_frequency)."""
    s = _series(points, latest)
    last = s[-1][0] if s else None
    out = {"last_report": last.strftime("%Y-%m-%d %H:%M") if last else None,
           # Rain gauges report every 1-12 h in dry weather and on each tip when it rains, so "fresh" means the gauge
           # has reported within the same quiet window as an on-change stage gauge.
           "fresh": bool(last and now - last <= dt.timedelta(hours=quiet_hours)),
           "totals": {str(m): round(rain_total(s, now - dt.timedelta(minutes=m), now), 2) for m in DURATIONS},
           "level": 0, "driver": None}
    if not freq or not freq.get("levels"):
        out["level"] = None   # no Atlas 14 values for this gauge
        return out
    best = None
    for m in DURATIONS:
        cut = freq["levels"].get(m)
        if not cut:
            continue
        depth = out["totals"][str(m)]
        lvl = 3 if depth >= cut[2] else 2 if depth >= cut[1] else 1 if depth >= cut[0] else 0
        ratio = depth / cut[0] if cut[0] else 0
        if lvl and (not best or (lvl, ratio) > (best[0], best[1])):
            best = (lvl, ratio, m, depth)
    if best:
        out["level"] = best[0]
        out["driver"] = {"minutes": best[2], "inches": best[3], "storm_years": storm_years(freq["minutes"][best[2]], best[3])}
    return out


def stage_signals(points, latest, gauge, now, S, creek_rain_series):
    """Trend and rapidly-rising check for one stage gauge.
    S: settings from load_settings; creek_rain_series: [(datetime, value)] lists for the creek's rain gauges."""
    p = _series(points, latest)
    on_change = gauge.get("reports") != "interval"
    quiet_h = S["GAUGE_QUIET_HOURS"] if on_change else S["GAUGE_QUIET_HOURS_INTERVAL"]
    if not p or now - p[-1][0] > dt.timedelta(hours=quiet_h):
        return {"trend": None, "ft_per_hr": None, "window_min": None, "points": 0, "rising_fast": None}
    last_t, last_v = p[-1]

    def value_at(t):   # last reading at or before t (on-change gauges hold their value until the next report)
        v = None
        for x in p:
            if x[0] <= t:
                v = x
            else:
                break
        return v

    # Trend: fitted slope over TREND_WINDOW_MIN. On-change gauges hold their value, so the window runs to now and
    # starts at the value in force then. Interval gauges that report less often than the window (e.g. hourly)
    # widen it to their last two readings, up to TREND_MAX_WINDOW_MIN.
    W = S["TREND_WINDOW_MIN"]
    if on_change:
        start = now - dt.timedelta(minutes=W)
        a = value_at(start)
        pts = ([(start, a[1])] if a else []) + [x for x in p if x[0] > start] + [(now, last_v)]
        window = W
    else:
        pts = [x for x in p if x[0] >= last_t - dt.timedelta(minutes=W)]
        if len(pts) < 2:
            prev = [x for x in p if x[0] < last_t and last_t - x[0] <= dt.timedelta(minutes=S["TREND_MAX_WINDOW_MIN"])]
            pts = prev[-1:] + [(last_t, last_v)] if prev else pts
        window = round((pts[-1][0] - pts[0][0]).total_seconds() / 60) if len(pts) > 1 else 0
    slope = None
    if len(pts) >= 2 and window > 0:
        xs = [(x[0] - pts[0][0]).total_seconds() / 3600 for x in pts]
        ys = [x[1] for x in pts]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        den = sum((x - mx) ** 2 for x in xs)
        slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else None

    # Rapidly rising: same rule as the home page
    fast = None
    if now - last_t <= dt.timedelta(minutes=S["RISE_FRESH_MIN"]):
        ref = value_at(last_t - dt.timedelta(minutes=S["RISE_MINUTES"]))
        rise = last_v - ref[1] if ref else None
        rain = max([rain_total(rs, now - dt.timedelta(hours=S["RISE_TIDAL_RAIN_HOURS"]), now) for rs in creek_rain_series] or [0])
        tidal_ok = not gauge.get("tidal") or rain >= S["RISE_TIDAL_RAIN_IN"]
        if rise is not None and rise >= S["RISE_FT"] and tidal_ok:
            nxt = [t for t in gauge.get("thresholds", []) if t["value"] > last_v]
            rate = rise / (S["RISE_MINUTES"] / 60)
            fast = {"rise_ft": round(rise, 2), "minutes": S["RISE_MINUTES"],
                    "hours_to_next": round((nxt[0]["value"] - last_v) / rate, 2) if nxt and rate > 0 else None,
                    "next": nxt[0]["name"] if nxt else None}
    word = None
    if fast:
        word = "fast"
    elif slope is not None:
        word = "rising" if slope >= S["TREND_STEADY_FT_PER_HR"] else "falling" if slope <= -S["TREND_STEADY_FT_PER_HR"] else "steady"
    return {"trend": word, "ft_per_hr": None if slope is None else round(slope, 2), "window_min": window,
            "points": len(pts), "rising_fast": fast}
