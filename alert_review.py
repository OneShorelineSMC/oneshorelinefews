"""Were the rain and rising-fast alerts on point? (staff, 2026-11-20)

Until 2026-11-20 the staff view raised a creek's status for heavy rain (NOAA Atlas 14 ratings) and for a creek rising
fast, on top of the flood levels and rain triggers the public pages use. Since then both views show the flood-level
status, and the data job keeps working out the full status in the background. This step reads status_log.csv (every
change of either status) and, for each time the full status was above the public one (a "rain or rising-fast alert"),
asks: did the creek reach that status by its flood levels (or a rain trigger) within FOLLOW_HOURS?

  followed      the public status reached the alert's level within FOLLOW_HOURS of the alert starting; lead = how much
                earlier the alert came
  not followed  it didn't: the alert went off without the creek reaching that flood level (it may still have been a
                reasonable heads-up; the Storm Tracker graphs show what the creek did)
  open          started less than FOLLOW_HOURS ago and not followed yet
  no flood levels  the creek has no flood levels to check against (creeks in the "More creeks" list)
It also lists each time the public status went up from No alerts with no rain or rising-fast alert running, or ended
within FOLLOW_HOURS before it ("no early alert").

Rows from before 2026-11-20 have no public status in the log; for them the public status is taken from the flood
level in the same row, and the log then recorded only changes of the full status, so a flood level reached while the
full status stayed the same was not logged. Those results are marked approximate.

Writes alert_review.json (the Storm Tracker shows it) and alert_review.csv (one row per alert, for Excel).

Usage: python alert_review.py out/status_log.csv out/alert_review.json [--creeks out/creeks.json] [--follow-hours 3]
"""

import csv
import datetime as dt
import json
import os
import sys

RANK = {"": 0, "none": 0, "offline": 0, "alert": 1, "ready": 2, "likely": 3}
NAME = {1: "alert", 2: "ready", 3: "likely"}
FOLLOW_HOURS = 3


def _t(s):
    return dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def read_log(path):
    """[(time, creek, full_key, public_key, approx, reasons, rain_level)] oldest first."""
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            try:
                t = _t(r["time"])
            except (KeyError, ValueError, TypeError):
                continue
            full = (r.get("to") or "").strip()
            pub = (r.get("public") or "").strip()
            approx = not pub
            if approx:   # older rows: the public status from the flood level in the same row (a rain trigger counts too)
                try:
                    lv = int(float(r.get("level") or 0))
                except ValueError:
                    lv = 0
                codes = (r.get("reasons") or "").split()
                if any(c in ("why_trigger", "why_trigger_tide") for c in codes):
                    pub = full
                else:
                    pub = NAME.get(min(lv, 3), "offline" if full == "offline" or "why_gauge_offline" in codes else "none")
            try:
                rl = int(float(r.get("rain_level") or 0))
            except ValueError:
                rl = 0
            rows.append((t, (r.get("creek") or "").strip(), full, pub, approx, (r.get("reasons") or "").split(), rl))
    rows.sort(key=lambda x: x[0])
    return rows


def why(reasons, rain_level):
    w = []
    if rain_level >= 1 or any(c in ("why_rain", "why_normal_rain") for c in reasons):
        w.append("rain")
    if "why_rising_fast" in reasons:
        w.append("rising fast")
    return w


def review(rows, now, follow_hours=FOLLOW_HOURS, has_levels=None):
    has_levels = has_levels or {}
    win = dt.timedelta(hours=follow_hours)
    by = {}
    for r in rows:
        by.setdefault(r[1], []).append(r)
    out, no_warn = {}, []
    for cid, rs in by.items():
        eps, cur = [], None
        pub_hist = [(r[0], RANK.get(r[3], 0)) for r in rs]
        prev_pub = 0
        for t, _, full, pub, approx, reasons, rl in rs:
            fr, pr = RANK.get(full, 0), RANK.get(pub, 0)
            if fr > pr and fr >= 1:
                if cur is None:
                    cur = {"start": t, "end": None, "staff": fr, "public_at_start": pr, "why": set(), "rain_level": 0, "approx": approx}
                cur["staff"] = max(cur["staff"], fr)
                cur["why"].update(why(reasons, rl))
                cur["rain_level"] = max(cur["rain_level"], rl)
                cur["approx"] = cur["approx"] or approx
            elif cur is not None:
                cur["end"] = t
                eps.append(cur)
                cur = None
            # the public status went up from No alerts with no alert running, or ended within the window before it
            if prev_pub == 0 and pr >= 1 and not any(
                    e["start"] <= t and (e["end"] is None or e["end"] >= t - win)
                    for e in eps[-3:] + ([cur] if cur else [])):
                no_warn.append({"creek": cid, "time": t.strftime("%Y-%m-%d %H:%M"), "public": NAME[pr], "approx": approx})
            prev_pub = pr
        if cur is not None:
            eps.append(cur)
        res = []
        for e in eps:
            reach = next(((t, p) for t, p in pub_hist if e["start"] <= t <= e["start"] + win and p >= e["staff"]), None)
            if has_levels.get(cid) is False:
                outcome = "no flood levels"
            elif reach:
                outcome = "followed"
            elif now - e["start"] < win:
                outcome = "open"
            else:
                outcome = "not followed"
            end = e["end"] or now
            res.append({"start": e["start"].strftime("%Y-%m-%d %H:%M"), "end": e["end"].strftime("%Y-%m-%d %H:%M") if e["end"] else None,
                        "minutes": int((end - e["start"]).total_seconds() // 60), "staff": NAME[e["staff"]],
                        "public_at_start": NAME.get(e["public_at_start"], "none"), "why": sorted(e["why"]), "rain_level": e["rain_level"],
                        "outcome": outcome, "lead_min": int((reach[0] - e["start"]).total_seconds() // 60) if reach else None,
                        "approx": e["approx"]})
        n = lambda o: sum(1 for x in res if x["outcome"] == o)  # noqa: E731
        leads = sorted(x["lead_min"] for x in res if x["lead_min"] is not None and x["lead_min"] > 0)
        out[cid] = {"alerts": res, "summary": {
            "alerts": len(res), "followed": n("followed"), "not_followed": n("not followed"), "open": n("open"),
            "no_levels": n("no flood levels"),
            "by_why": {w: {"alerts": sum(1 for x in res if w in x["why"]),
                           "followed": sum(1 for x in res if w in x["why"] and x["outcome"] == "followed")}
                       for w in ("rain", "rising fast")},
            "median_lead_min": leads[len(leads) // 2] if leads else None,
            "no_early_alert": sum(1 for x in no_warn if x["creek"] == cid)}}
    return out, no_warn


def main(argv, now=None):
    log, path = argv[1], argv[2]
    follow = float(argv[argv.index("--follow-hours") + 1]) if "--follow-hours" in argv else FOLLOW_HOURS
    creeks_path = argv[argv.index("--creeks") + 1] if "--creeks" in argv else os.path.join(os.path.dirname(path) or ".", "creeks.json")
    names, has = {}, {}
    try:
        with open(creeks_path) as f:
            cj = json.load(f)
        for c in (cj.get("creeks") or []) + (cj.get("creeks_preview") or []):
            names[c["id"]] = c.get("name") or c["id"]
            has[c["id"]] = bool((c.get("status") or {}).get("has_levels", True))
        if not now and cj.get("generated"):
            now = _t(cj["generated"])
    except (OSError, ValueError, KeyError):
        pass
    try:
        rows = read_log(log)
    except OSError as e:
        print(f"alert_review: can't read {log}: {e}")
        return 0
    now = now or (rows[-1][0] if rows else dt.datetime.now())
    creeks, no_warn = review(rows, now, follow, has)
    exact = next((r[0] for r in rows if not r[4]), None)
    result = {"generated": now.strftime("%Y-%m-%d %H:%M"), "follow_hours": follow,
              "since": rows[0][0].strftime("%Y-%m-%d %H:%M") if rows else None,
              "exact_since": exact.strftime("%Y-%m-%d %H:%M") if exact else None,
              "creeks": {cid: dict(v, name=names.get(cid, cid)) for cid, v in sorted(creeks.items(), key=lambda kv: list(names).index(kv[0]) if kv[0] in names else 99)},
              "no_early_alert": no_warn}
    with open(path, "w") as f:
        json.dump(result, f, separators=(",", ":"))
    with open(os.path.splitext(path)[0] + ".csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["creek", "start", "end", "minutes", "staff_status", "public_at_start", "why", "rain_level", "outcome", "lead_min", "approximate"])
        for cid, v in result["creeks"].items():
            for a in v["alerts"]:
                w.writerow([cid, a["start"], a["end"] or "", a["minutes"], a["staff"], a["public_at_start"], " + ".join(a["why"]),
                            a["rain_level"], a["outcome"], "" if a["lead_min"] is None else a["lead_min"], "yes" if a["approx"] else ""])
    for cid, v in result["creeks"].items():
        s = v["summary"]
        print(f"{cid}: {s['alerts']} alerts, {s['followed']} followed, {s['not_followed']} not followed, {s['open']} open, "
              f"{s['no_levels']} no flood levels; median lead {s['median_lead_min']} min; {s['no_early_alert']} with no early alert")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
