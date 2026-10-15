"""
Creek status layer, part 1 (in development): signals computed by the data job for every gauge.
Nothing on the public pages reads these yet; they are written into creeks.json for the staff preview.

  Rain gauges:  rolling totals over 15 min - 48 hr, compared with NOAA Atlas 14 storms at that gauge
                (lookups/rain_frequency.csv) -> level 0-3 (none / Heavy / Very heavy / Severe), the duration
                and depth that set it, and a rough storm size (years) for staff.
  Stage gauges: trend (rising fast / rising / steady / falling) and the rapidly-rising check, using the
                same rule as the home page (RISE_* in lookups/settings.csv).

  Creeks:       one status (creek_status): Flooding likely / Be ready / Stay alert / Offline / No alerts, with
                reason codes the pages turn into words from display_text.csv (THRESHOLDS_BASIS.md §10).

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
    "RAIN_SEVERE_CONFIRM_GAUGES": (2, 1, 5), "RAIN_SILENT_MIN": (60, 15, 720), "TIDE_RISING_LOOKAHEAD_HOURS": (3, 0.5, 12),
    "BE_READY_FROM_RAIN": (1, 0, 1),
    # flood reports (scripts/fetch_community_flood_reports.py)
    "REPORTS_PUBLIC": (0, 0, 1), "REPORTS_MAX_AGE_DAYS": (180, 1, 730), "REPORTS_MAX_PHOTOS": (40, 0, 200),
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
        window = int(W)
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


# ---------------------------------------------------------------- tide (NOAA, ft NAVD88) and creek status

def tide_state(pred, hilo, obs, now, lookahead_h):
    """Tide now at a NOAA station: measured if within the hour, else predicted; whether it is rising; next high tide.
    pred/obs: [(datetime, ft)], hilo: [(datetime, ft, "H"/"L")]. Any of them may be empty (download failed)."""
    out = {"ft": None, "source": None, "rising": None, "next_high": None, "next_high_ft": None, "high_soon": False}
    if obs and now - obs[-1][0] <= dt.timedelta(hours=1):
        out["ft"], out["source"] = round(obs[-1][1], 2), "measured"
    elif pred:
        best = min(pred, key=lambda x: abs(x[0] - now))
        if abs(best[0] - now) <= dt.timedelta(hours=1):
            out["ft"], out["source"] = round(best[1], 2), "predicted"
    nxt = [h for h in hilo if h[0] > now]
    if nxt:
        out["rising"] = nxt[0][2] == "H"
        hi = [h for h in nxt if h[2] == "H"]
        if hi:
            out["next_high"], out["next_high_ft"] = hi[0][0].strftime("%Y-%m-%d %H:%M"), round(hi[0][1], 2)
            out["high_soon"] = bool(out["rising"] and hi[0][0] - now <= dt.timedelta(hours=lookahead_h))
    return out


STATUS_RANK = {"likely": 4, "ready": 3, "alert": 2, "offline": 1, "none": 0}


def creek_status(c, sens, tide, now, S):
    """One status for a creek from its gauges' signals (already in sens[key]["signals"]), its thresholds and
    rain triggers, and the tide at its station. Rules: THRESHOLDS_BASIS.md §10. Flood levels always come first;
    rain and rate of rise never lower a status. Returns a dict for creeks.json; words come from display_text.csv."""
    reasons, staff = [], []
    # Official level: highest threshold passed by any working stage gauge
    level, level_name, working_stages, stage_rows = 0, None, 0, []
    has_levels = any(g.get("thresholds") for g in c["stages"])
    for g in c["stages"]:
        e = sens.get(g["key"], {})
        sig = e.get("signals", {})
        p = _series(e.get("points"), e.get("latest"))
        if sig.get("trend") is None or not p:
            continue
        working_stages += 1
        v = p[-1][1]
        lv = [t for t in g.get("thresholds", []) if v >= t["value"]]
        if lv and lv[-1]["level"] > level:
            level, level_name = lv[-1]["level"], lv[-1]["name"]
        stage_rows.append((g, sig, v))
    # Rain triggers in thresholds.csv (e.g. Belmont): rain over the window, plus a high tide if the trigger needs one
    trigger = None
    for tr in c.get("rain_triggers", []):
        e = sens.get(tr["gauge"], {})
        amt = rain_total(_series(e.get("points"), e.get("latest")), now - dt.timedelta(minutes=tr["minutes"]), now)
        ok = amt >= tr["value"]
        if ok and tr.get("high_tide"):
            need = tr.get("tide_min")
            ok = tide.get("ft") is not None and need is not None and tide["ft"] >= need
            if tide.get("ft") is None:
                staff.append("tide unknown: rain + tide trigger can't be checked")
        if ok and (not trigger or tr["level"] > trigger["level"]):
            trigger = dict(tr, amount=round(amt, 2))
    # Rain level: highest across working rain gauges (shown and supporting); Severe needs confirmation
    rain_gauges = c["rain"] + c.get("rain_support", [])
    working, elevated, best = [], 0, None
    for g in rain_gauges:
        sig = sens.get(g["key"], {}).get("signals", {})
        if not sig.get("fresh") or sig.get("level") is None:
            continue
        working.append((g, sig))
        if sig["level"] >= 2:
            elevated += 1
        if sig["level"] and (not best or sig["level"] > best[1]["level"]):
            best = (g, sig)
    rain = best[1]["level"] if best else 0
    need = min(int(S["RAIN_SEVERE_CONFIRM_GAUGES"]), max(1, len(working)))
    if rain == 3 and elevated < need:
        rain = 2
        staff.append(f"severe rain at one gauge only; treated as very heavy ({elevated} of {len(working)} gauges at very heavy or above)")
    if len(working) == 1 and rain_gauges:
        staff.append("only one working rain gauge")
    # A rain gauge silent while another on the creek records Heavy rain or more (a gauge only reports when its bucket
    # tips, so light rain at one gauge and none at another is normal; heavy rain with no tips is not)
    silent = []
    win = dt.timedelta(minutes=S["RAIN_SILENT_MIN"])
    raining = [g["key"] for g, sig in working if sig["level"] >= 1]
    if raining:
        for g in rain_gauges:
            sig = sens.get(g["key"], {}).get("signals", {})
            last = sig.get("last_report")
            if g["key"] not in raining and (not last or now - _t(last) > win):
                silent.append({"gauge": g["key"], "label": g["label"], "since": last})
    # Creek trend: the most significant among working stage gauges
    order = {"fast": 4, "rising": 3, "falling": 2, "steady": 1}
    trend = max((sig for g, sig, v in stage_rows), key=lambda x: order.get(x.get("trend"), 0), default=None)
    fast = bool(trend and trend.get("trend") == "fast")
    tidal = any(g.get("tidal") for g in c["stages"])
    tide_line = bool(tidal and tide.get("high_soon"))

    # Status, worst first
    trig3 = bool(trigger and trigger["level"] >= 3)
    if level >= 3 or trig3:
        key = "likely"
    elif level == 2 or (not has_levels and (fast or rain == 3) and S["BE_READY_FROM_RAIN"] >= 1):
        key = "ready"
    elif level == 1 or rain >= 2 or fast or (trigger and trigger["level"] >= 1) or (rain == 1 and tide_line):
        key = "alert"
    elif working_stages == 0 and c["stages"]:
        key = "offline"
    else:
        key = "none"

    # Reasons (codes for display_text.csv), most important first
    up = trend.get("trend") if trend else None
    if level >= 3:
        reasons.append({"code": "why_warning"})
    elif level == 2:
        reasons.append({"code": "why_watch", "rising_fast": fast})
    elif level == 1:
        reasons.append({"code": "why_monitoring", "rising": up in ("fast", "rising"), "rising_fast": fast})
    if trig3 or (trigger and level < 3):
        reasons.append({"code": "why_trigger_tide" if trigger.get("high_tide") else "why_trigger",
                        "minutes": trigger["minutes"], "inches": trigger["amount"]})
    if working_stages == 0 and c["stages"] and key in ("likely", "ready", "alert"):
        reasons.append({"code": "why_gauge_offline"})   # status from rain (or a trigger) alone
    if has_levels and level == 0 and working_stages and key in ("ready", "alert") and (rain >= 2 or fast):
        if rain >= 2:
            reasons.append({"code": "why_normal_rain", "rain": rain})
        if fast:
            reasons.append({"code": "why_rising_fast"})
    elif not has_levels and fast:
        reasons.append({"code": "why_rising_fast"})
    if rain >= 1 and key != "none" and not any(r["code"] == "why_normal_rain" for r in reasons):
        reasons.append({"code": "why_rain", "rain": rain})
    for sg in silent:
        reasons.append({"code": "why_stale", "time": sg["since"], "gauge": sg["label"]})
    if tide_line and STATUS_RANK[key] >= 2:
        reasons.append({"code": "tide_rising_line", "time": tide.get("next_high")})

    drv = None
    if best and best[1].get("driver"):
        d = best[1]["driver"]
        drv = dict(d, gauge=best[0]["key"], label=best[0]["label"])
    return {"key": key, "level": level, "level_name": level_name, "has_levels": has_levels,
            "trigger": trigger and {k: trigger[k] for k in ("label", "minutes", "value", "amount", "level", "name") if k in trigger},
            "rain": {"level": rain, "driver": drv, "working": len(working), "of": len(rain_gauges), "elevated": elevated,
                     "silent": silent},
            "trend": trend and {k: trend.get(k) for k in ("trend", "ft_per_hr", "window_min")},
            "tidal": tidal, "tide": tide if tidal else None, "reasons": reasons, "staff_notes": staff}
