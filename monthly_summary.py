"""
Monthly summary (staff page MonthlySummary.html, staff, 2026-11-25): each month's high tides, storms and road closures in
one place, for elected officials (the Board of Supervisors and city councils), Bayside and Coastside, with what touched
each city and community, labeled with its supervisorial district.

Runs at the end of the data job and builds the month as it goes. It reads what the job already keeps on the data branch:
  tide_tracker.json          each tide gauge's daily highs, its month (highest, days above each level), its rank among
                             the same month in past years, and NWS Coastal Flood products
  tide_tracker_history.json  each gauge's daily highs back to the start of its record (for the all-time rank)
  storm_tracker.json         each storm at each creek: rain, how rare its heaviest part was, creek levels reached
  status_log.csv             every change of a creek's status (Stay alert / Be ready / Flooding likely)
  waves.json                 each day's highest wave at the Half Moon Bay buoy (from 2026-11-26)
  road_closures.json         flooding closures on San Mateo County state highways, with their cause (tide / rain / both)
  community_flood_reports.json  staff-approved community reports, when there are any
lookups/impacts.csv (what happened on the ground that no feed reports, entered by staff), and two lookups: lookups/places.csv (each city and unincorporated community: side, supervisorial district or districts,
AB 825 seat) and lookups/creek_places.csv (the communities each creek's status is for). A city split between two
districts is labeled with both (staff, 2026-11-25: kept simple on purpose; no district lines).

Writes monthly_summary.json: {"generated", "months": {"YYYY-MM": {...}}}. The current month is redone every run; the
month before is redone through the 3rd (closures and storms that ran over the month's end), then kept as it is, so past
months stay after their days leave the trackers. The words at the top of each month are written by staff in
lookups/monthly/YYYY-MM.md and read by the page, not here.

What counts:
  a high-tide run   days in a row (a one-day gap allowed) when a gauge's highest water reached its tide level of
                    concern: the 1-year tide where there is one (Redwood City, Monterey), else NOAA's minor flooding level
  a storm           storms (storm_tracker.json) at any creek, joined when one starts within JOIN_HOURS of another's end;
                    "on a high tide" when its days fall in a high-tide run
  a creek flag      the creek reached a flood level (Monitoring, Watch, Warning) or its public status reached Be ready or
                    Flooding likely; the communities in creek_places.csv. Public creeks only (creeks.csv preview_only
                    blank) and the public status only (flood levels and rain triggers; rain ratings and rising fast don't
                    count), as the public pages showed it; a gauge marked out of service doesn't count (staff, 2026-11-25)
Usage: python scripts/monthly_summary.py <out dir>   (reads and writes the files above in that folder)
"""
import csv
import datetime as dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOOKUPS = os.path.join(HERE, "..", "lookups")
sys.path.insert(0, HERE)
from storm_tracker import drop_repeats, STATUS_RANK   # noqa: E402

JOIN_HOURS = 12          # storms at different creeks this close together are one storm
REDO_DAYS = 3            # the month before is redone through this day of the new month
MIN_STORM_IN = 0.25      # a storm smaller than this everywhere is listed as "smaller rain" only
NOTABLE_IN = 1.0         # a storm is notable with this much rain at a creek, a flood level reached, or Be ready or higher
STATUS_NAME = {"alert": "Stay alert", "ready": "Be ready", "likely": "Flooding likely"}
LEVEL_NAME = {1: "Flood Monitoring", 2: "Flood Watch", 3: "Flood Warning"}
RAIN_NAME = {1: "Heavy", 2: "Very heavy", 3: "Intense"}


def parse_t(s):
    return dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def read_json(path, default=None):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def read_csv(path):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


# ------------------------------------------------------------------------------------------------ places
def load_places(lookups=LOOKUPS):
    places = {}
    for r in read_csv(os.path.join(lookups, "places.csv")):
        places[r["place"].strip().lower()] = {"place": r["place"].strip(), "kind": r["kind"], "side": r["side"],
                                              "districts": [int(x) for x in r["district"].split()],
                                              "seat": r["ab825_seat"].strip() or None}
    creek_places = {r["creek"]: [p.strip() for p in r["places"].split(";") if p.strip()]
                    for r in read_csv(os.path.join(lookups, "creek_places.csv"))}
    return places, creek_places


def place_entry(name, places):
    p = places.get((name or "").strip().lower())
    if not p:
        return {"place": name, "kind": None, "districts": [], "seat": None}
    return {"place": p["place"], "kind": p["kind"], "districts": p["districts"], "seat": p["seat"]}


# ------------------------------------------------------------------------------------------------ tides
def tide_level(st):
    """The tide level of concern at a gauge: its 1-year tide, else NOAA's minor flooding level."""
    lv = {x["key"]: x for x in st.get("levels") or []}
    return lv.get("oneyear") or lv.get("minor")


def history_daily(hist):
    """{date string: highest high water} from a station's history ({year: {"d": {MMDD: ft}}})."""
    out = {}
    for y, v in (hist or {}).items():
        for md, ft in ((v or {}).get("d") or {}).items():
            if ft is not None:
                out["%s-%s-%s" % (y, md[:2], md[2:])] = ft
    return out


def all_time(st, hist, day, ft):
    """Rank of a day's high among every daily high on record, and the days higher."""
    d = history_daily(hist)
    for k, v in (st.get("days") or {}).items():
        if v.get("max") is not None:
            d[k] = v["max"]
    if not d:
        return None
    higher = sorted(((v, k) for k, v in d.items() if v > ft + 1e-9 and k != day), reverse=True)
    return {"rank": len(higher) + 1, "since": min(d)[:4], "higher": [[k, v] for v, k in higher[:5]]}


def tide_runs(st, month, level_ft):
    """[(first day, last day, [days])] of days in the month at or above the level, a one-day gap allowed."""
    days = sorted(k for k, v in (st.get("days") or {}).items() if k[:7] == month and v.get("max") is not None and v["max"] >= level_ft - 1e-9)
    runs = []
    for k in days:
        d = dt.date.fromisoformat(k)
        if runs and (d - dt.date.fromisoformat(runs[-1][-1])).days <= 2:
            runs[-1].append(k)
        else:
            runs.append([k])
    return runs


def month_tides(tt, hist, month):
    out = []
    for st in tt.get("stations") or []:
        m = (st.get("months") or {}).get(month)
        if not m:
            continue
        lv = tide_level(st)
        day = (m.get("max_date") or "")[:10]
        row = {"id": st["id"], "name": st["name"], "side": st.get("side"), "mhhw": st.get("mhhw"),
               "max": m.get("max"), "max_at": m.get("max_date"), "above_mhhw": round(m["max"] - st["mhhw"], 2) if m.get("max") is not None and st.get("mhhw") is not None else None,
               "table": m.get("table"), "surge": m.get("surge"), "surge_at": m.get("surge_date"),
               "days_above": m.get("count"), "levels": [{"key": x["key"], "label": x["label"], "ft": x["ft"]} for x in st.get("levels") or []],
               "concern": {"key": lv["key"], "label": lv["label"], "ft": lv["ft"]} if lv else None,
               "month_rank": (st.get("ranks") or {}).get(month), "days": len([1 for k in (st.get("days") or {}) if k[:7] == month])}
        if m.get("max") is not None:
            row["all_time"] = all_time(st, (hist or {}).get(st["id"]), day, m["max"])
        dd = st.get("days") or {}
        row["daily"] = [[k, dd[k].get("max"), dd[k].get("table")] for k in sorted(dd) if k[:7] == month]
        out.append(row)
    return out


def nws_products(tt, month):
    """NWS Coastal Flood products in effect at some time in the month, overlapping ones of the same kind joined."""
    rows = []
    for n in tt.get("nws") or []:
        a, b = n.get("onset", "")[:16].replace("T", " "), (n.get("ends") or n.get("onset", ""))[:16].replace("T", " ")
        if a[:7] <= month <= b[:7]:
            rows.append([n["event"], a, b])
    rows.sort(key=lambda r: (r[0], r[1]))
    out = []
    for ev, a, b in rows:
        if out and out[-1]["event"] == ev and a <= out[-1]["ends"]:
            out[-1]["ends"] = max(out[-1]["ends"], b)
        else:
            out.append({"event": ev, "onset": a, "ends": b})
    return sorted(out, key=lambda r: r["onset"])


# ------------------------------------------------------------------------------------------------ creeks
def public_status(r):
    """The public status in a status_log.csv row: its "public" column (since 2026-11-20), or for older rows what the
    public pages would have shown: flood levels (the "level" column, which leaves out gauges marked out of service) and
    rain triggers (when a trigger is among the reasons, the row's status). Rain ratings and rising fast never count."""
    if (r.get("public") or "").strip():
        return r["public"].strip()
    lv = int(r.get("level") or 0) if str(r.get("level") or "0").isdigit() else 0
    st = "likely" if lv >= 3 else "ready" if lv == 2 else "alert" if lv == 1 else "none"
    if any(x.startswith("why_trigger") for x in (r.get("reasons") or "").split()) and STATUS_RANK.get(r.get("to"), 0) > STATUS_RANK.get(st, 0):
        st = r["to"]
    return st


def status_spans(rows, until):
    """{creek: [(public status, from, to, flood level)]} from status_log.csv: every stretch with a public status above
    "none" or a flood level reached."""
    by = {}
    for r in sorted(rows, key=lambda r: r["time"]):
        lv = int(r["level"]) if str(r.get("level") or "").isdigit() else 0
        by.setdefault(r["creek"], []).append((parse_t(r["time"]), public_status(r), lv))
    out = {}
    for c, ch in by.items():
        for i, (t, s, lv) in enumerate(ch):
            if s in STATUS_NAME or lv:
                end = ch[i + 1][0] if i + 1 < len(ch) else until
                out.setdefault(c, []).append((s, t, end, lv))
    return out


def level_reached(spans, a, b):
    """The highest flood level the status layer saw at a creek between a and b (out-of-service gauges left out)."""
    return max([lv for s, t0, t1, lv in spans if min(t1, b) > max(t0, a) or (a <= t0 <= b)] or [0])


def public_creeks(lookups=LOOKUPS):
    """Creeks on the public pages (lookups/creeks.csv, preview_only blank). Staff-preview creeks show rain only."""
    return {r["creek"] for r in read_csv(os.path.join(lookups, "creeks.csv")) if not (r.get("preview_only") or "").strip()}


def creek_status(spans, a, b):
    """Highest status at a creek between a and b, when it first came, and minutes at it or higher."""
    best = None
    for s, t0, t1, _ in spans:
        if s not in STATUS_NAME:
            continue
        lo, hi = max(t0, a), min(t1, b)
        if hi <= lo:
            continue
        r = STATUS_RANK[s]
        if best is None or r > best[0]:
            best = [r, s, lo, 0]
        if r >= best[0]:
            best[3] += (hi - lo).total_seconds() / 60
    if not best:
        return None
    return {"status": best[1], "label": STATUS_NAME[best[1]], "first": best[2].strftime("%Y-%m-%d %H:%M"), "minutes": round(best[3])}


def main_rain(st):
    ok = [r for r in st.get("rain") or [] if not r.get("out_of_service")]   # set-aside readings (gauge_outages.csv) don't count
    rs = [r for r in ok if not r.get("support")] or ok
    return max(rs, key=lambda r: r.get("total") or 0) if rs else None


def storm_events(tracker, month, spans, creek_side, tide_days, public=None):
    storms = [s for s in drop_repeats((tracker.get("storms") or []) + (tracker.get("open") or []))
              if s["start"][:7] == month or s["end"][:7] == month]
    storms.sort(key=lambda s: s["start"])
    groups = []
    for s in storms:
        a, b = parse_t(s["start"]), parse_t(s["end"])
        if groups and a <= groups[-1]["b"] + dt.timedelta(hours=JOIN_HOURS):
            groups[-1]["b"] = max(groups[-1]["b"], b)
            groups[-1]["s"].append(s)
        else:
            groups.append({"a": a, "b": b, "s": [s]})
    open_ids = {(s["creek"], s["start"]) for s in tracker.get("open") or []}
    out = []
    for g in groups:
        creeks = {}
        for s in g["s"]:
            r = main_rain(s)
            row = creeks.setdefault(s["creek"], {"creek": s["creek"], "name": s["name"], "side": creek_side.get(s["creek"]),
                                                 "public": public is None or s["creek"] in public, "levels": [],
                                                 "rain": 0, "gauge": None, "rarest": None, "reached": 0, "peak": None, "status": None})
            if r and (r.get("total") or 0) > row["rain"]:
                row["rain"], row["gauge"] = r["total"], r.get("label")
            for rr in s.get("rain") or []:
                x = rr.get("rarest")
                if x and not rr.get("support") and not rr.get("out_of_service") and (row["rarest"] is None or (x["level"], x.get("years") or 0) > (row["rarest"]["level"], row["rarest"].get("years") or 0)):
                    row["rarest"] = dict(x, gauge=rr.get("label"))
            row["levels"] += [lv for lv in s.get("levels") or [] if lv.get("peak") is not None]
            if s.get("tide") and s["tide"].get("above_mhhw") is not None:
                row["tide_above_mhhw"] = max(row.get("tide_above_mhhw", -9), s["tide"]["above_mhhw"])
        for c, row in creeks.items():
            lvs = row.pop("levels")
            if not row["public"]:
                continue   # staff-preview creek: its rain only (no public flood levels or status yet)
            win = (g["a"], g["b"] + dt.timedelta(hours=12))
            row["status"] = creek_status(spans.get(c, []), *win)
            # the flood level reached is the one the public status saw (a gauge marked out of service doesn't count);
            # its height from the storm tracker's hourly record when a gauge there reached the same level
            row["reached"] = level_reached(spans.get(c, []), *win)
            same = [lv for lv in lvs if (lv.get("reached") or 0) == row["reached"]] if row["reached"] else []
            if same:
                lv = max(same, key=lambda x: x["peak"])
                row["peak"] = {"gauge": lv.get("label"), "ft": lv.get("peak"), "at": lv.get("peak_at")}
            if row["rarest"]:
                row["rarest"]["label"] = RAIN_NAME.get(row["rarest"]["level"])
            if row["reached"]:
                row["reached_label"] = LEVEL_NAME.get(row["reached"])
        cl = sorted(creeks.values(), key=lambda r: -r["rain"])
        days = sorted({(g["a"] + dt.timedelta(days=i)).strftime("%Y-%m-%d") for i in range((g["b"].date() - g["a"].date()).days + 1)})
        out.append({"start": g["a"].strftime("%Y-%m-%d %H:%M"), "end": g["b"].strftime("%Y-%m-%d %H:%M"),
                    "open": any((s["creek"], s["start"]) in open_ids for s in g["s"]),
                    "wettest": {"creek": cl[0]["name"], "gauge": cl[0]["gauge"], "in": cl[0]["rain"]} if cl else None,
                    "sides": sorted({r["side"] for r in cl if r["side"]}),
                    "on_high_tide": sorted(d for d in days if d in tide_days),
                    "notable": any(r["reached"] or (r["status"] and r["status"]["status"] in ("ready", "likely")) or r["rain"] >= NOTABLE_IN for r in cl),
                    "small": max([r["rain"] for r in cl] or [0]) < MIN_STORM_IN,
                    "creeks": cl})
    return out


def month_rain(tracker, month):
    """The month's rain at each creek's main rain gauges (storm_tracker.json days), and SFO's official daily totals."""
    days = (tracker.get("days") or {}).get("rain") or {}
    keys = {}
    for s in tracker.get("storms") or []:
        for r in s.get("rain") or []:
            if not r.get("support"):
                keys.setdefault(r["key"], {"key": r["key"], "label": r.get("label"), "creeks": set()})["creeks"].add(s["name"])
    out = []
    aside = (tracker.get("days") or {}).get("set_aside") or {}
    for k, g in keys.items():
        d = {x: v for x, v in (days.get(k) or {}).items() if x[:7] == month and v is not None}
        sa = aside.get(k) or {}
        sd = {x: v for x, v in (sa.get("read") or {}).items() if x[:7] == month and v is not None}
        if d or sd:
            row = {"key": k, "label": g["label"], "creeks": sorted(g["creeks"]), "in": round(sum(d.values()), 2), "days": len(d),
                   "wettest_day": max(d, key=d.get) if d else None, "wettest_in": round(max(d.values()), 2) if d else None}
            if sd:   # out of service (gauge_outages.csv): the month's total stops the day before; what it read after is kept apart
                row["out_of_service"] = {"since": sa.get("since"), "note": sa.get("note"), "set_aside_in": round(sum(sd.values()), 2)}
            out.append(row)
    cli = {x: v for x, v in (tracker.get("sfo_cli") or {}).items() if x[:7] == month and v is not None}
    sfo = {"in": round(sum(cli.values()), 2), "days": len(cli)} if cli else None
    return {"gauges": sorted(out, key=lambda r: -r["in"]), "sfo": sfo, "since": tracker.get("since")}


# ------------------------------------------------------------------------------------------------ roads
def month_roads(roads, month, places):
    """Flooding and storm closures that started in the month. Closures on one route that began in the same hour (both
    directions of a stretch, or a set of ramps) are one entry, with how many closures it holds."""
    out = {}
    for c in (roads or {}).get("log") or []:
        if c.get("kind") not in ("flood", "storm") or (c.get("started") or "")[:7] != month:
            continue
        k = (c.get("route") or c.get("id"), c.get("started", "")[:13])   # a city notice stands alone
        row = out.get(k)
        stretch = " / ".join(sorted(x.strip() for x in (c.get("where") or "").split(" to ")))
        if row:
            row["dirs"] = sorted(set(row["dirs"]) | {c.get("dir")} - {None})
            row["closures"] += 1
            if stretch not in row["stretches"]:
                row["stretches"].append(stretch)
                row["wheres"].append(c.get("where"))
            if c.get("place") and c["place"] not in [p["place"] for p in row["places"]]:
                row["places"].append(place_entry(c["place"], places))
            row["active"] = row["active"] or bool(c.get("active"))
            continue
        out[k] = {"route": c.get("route"), "notice": bool(c.get("notice")), "source": c.get("source"), "link": c.get("link") if c.get("notice") else None,
                  "where": c.get("where"), "wheres": [c.get("where")], "stretches": [stretch], "closures": 1, "dirs": [c.get("dir")] if c.get("dir") else [], "facility": c.get("facility"),
                  "what": c.get("what"), "kind": c.get("kind"), "started": c.get("started"), "ended": c.get("ended"),
                  "active": bool(c.get("active")), "side": c.get("side"), "cause": c.get("cause"), "why": c.get("why"),
                  "places": [place_entry(c.get("place"), places)] if c.get("place") else []}
    return sorted(out.values(), key=lambda r: r["started"])


# ------------------------------------------------------------------------------------------------ month
def build_month(month, now, tt, hist, tracker, status_rows, roads, reports, lookups=LOOKUPS, waves=None):
    places, creek_places = load_places(lookups)
    first = dt.date.fromisoformat(month + "-01")
    nxt = (first.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    through = min(now, dt.datetime.combine(nxt, dt.time()) - dt.timedelta(minutes=1))
    tides = month_tides(tt or {}, hist or {}, month)
    runs = []
    for st in (tt or {}).get("stations") or []:
        lv = tide_level(st)
        if not lv:
            continue
        for r in tide_runs(st, month, lv["ft"]):
            runs.append({"station": st["name"], "side": st.get("side"), "first": r[0], "last": r[-1], "days": r,
                         "level": lv["label"], "level_ft": lv["ft"],
                         "max": max(st["days"][k]["max"] for k in r),
                         "max_day": max(r, key=lambda k: st["days"][k]["max"])})
    # high-tide runs at any gauge joined into periods (the Bay and the coast often run together)
    periods = []
    for r in sorted(runs, key=lambda r: r["first"]):
        if periods and dt.date.fromisoformat(r["first"]) <= dt.date.fromisoformat(periods[-1]["last"]) + dt.timedelta(days=1):
            periods[-1]["last"] = max(periods[-1]["last"], r["last"])
            periods[-1]["gauges"].append(r)
        else:
            periods.append({"first": r["first"], "last": r["last"], "gauges": [r]})
    tide_days = {d for r in runs for d in r["days"]}
    spans = status_spans(status_rows or [], now)
    storms = storm_events(tracker or {}, month, spans, (roads or {}).get("creek_side") or {}, tide_days, public_creeks(lookups))
    rds = month_roads(roads or {}, month, places)
    nws = nws_products(tt or {}, month)
    for p in periods:
        p["sides"] = sorted({g["side"] for g in p["gauges"] if g["side"]})
        p["nws"] = [n for n in nws if n["onset"][:10] <= p["last"] and n["ends"][:10] >= p["first"]]
        p["roads"] = [i for i, r in enumerate(rds) if r.get("cause") in ("tide", "both") and p["first"] <= r["started"][:10] <= p["last"]]
    for s in storms:
        s["roads"] = [i for i, r in enumerate(rds) if r.get("cause") in ("rain", "both")
                      and parse_t(s["start"]) - dt.timedelta(hours=12) <= parse_t(r["started"]) <= parse_t(s["end"]) + dt.timedelta(hours=12)]
    for s in storms:
        s["notable"] = s["notable"] or bool(s["roads"])
    rain = month_rain(tracker or {}, month)
    # what touched each city and community (labeled with its district or districts)
    areas = {}

    def touch(pl, item):
        p = place_entry(pl, places)
        a = areas.setdefault(p["place"], {"place": p["place"], "kind": p["kind"], "districts": p["districts"], "seat": p["seat"], "items": []})
        if item not in a["items"]:
            a["items"].append(item)

    for s in storms:
        for c in s["creeks"]:
            if c["reached"] or (c["status"] and c["status"]["status"] in ("ready", "likely")):
                for pl in creek_places.get(c["creek"], []):
                    touch(pl, {"type": "creek", "creek": c["name"], "start": s["start"], "reached": c.get("reached_label"),
                               "status": c["status"]["label"] if c["status"] else None})
    for i, r in enumerate(rds):
        for p in r["places"]:
            touch(p["place"], {"type": "road", "road": i, "route": r["route"], "started": r["started"], "cause": r.get("cause")})
    areas = sorted(areas.values(), key=lambda a: (min(a["districts"] or [9]), a["kind"] != "city", a["place"]))
    rep = []
    for x in (reports or {}).get("reports") or []:
        t = x.get("time") or x.get("date") or x.get("reported") or ""
        if str(t)[:7] == month:
            rep.append({"time": t, "place": x.get("city") or x.get("place"), "what": x.get("type") or x.get("what")})
    return {"month": month, "through": through.strftime("%Y-%m-%d %H:%M"), "complete": now >= dt.datetime.combine(nxt, dt.time()),
            "tides": tides, "tide_periods": periods, "rain": rain, "nws": nws, "storms": storms, "roads": rds, "areas": areas,
            "reports": rep, "waves": month_waves(waves, month), "sources": {"tide_tracker": (tt or {}).get("generated"), "storm_tracker": (tracker or {}).get("generated"),
                                        "road_closures": (roads or {}).get("generated"), "status_log_rows": len(status_rows or [])}}


IMPACT_KINDS = {"flooding": "Flooding", "damage": "Damage", "road": "Road closed", "evacuation": "Evacuation", "other": "Reported"}


def read_impacts(lookups=LOOKUPS):
    """lookups/impacts.csv: what happened on the ground that no feed reports (staff, 2026-11-26: the Pacifica Pier's end
    breaking off on Nov 25): date, time, place, side, kind, what, source, link."""
    out = []
    for r in read_csv(os.path.join(lookups, "impacts.csv")):
        d = (r.get("date") or "").strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d) or not (r.get("what") or "").strip():
            continue
        link = (r.get("link") or "").strip()
        out.append({"date": d, "time": (r.get("time") or "").strip()[:5], "place": (r.get("place") or "").strip(),
                    "side": (r.get("side") or "").strip() or None, "kind": (r.get("kind") or "other").strip().lower(),
                    "label": IMPACT_KINDS.get((r.get("kind") or "other").strip().lower(), "Reported"), "what": r["what"].strip(),
                    "source": (r.get("source") or "").strip(), "link": link if link.startswith("https://") else ""})
    return sorted(out, key=lambda x: (x["date"], x["time"]))


def apply_impacts(m, impacts, places):
    """Put the month's impacts on a month (kept months too, so a row added later still shows): with the storm or high-tide
    run on the same days, and under its place."""
    mine = [dict(x) for x in impacts if x["date"][:7] == m["month"]]
    if not mine and "impacts" not in m:
        return m
    for x in mine:
        x["storms"] = [i for i, s in enumerate(m.get("storms") or []) if s["start"][:10] <= x["date"] <= s["end"][:10]]
        x["tide_periods"] = [i for i, p in enumerate(m.get("tide_periods") or []) if p["first"] <= x["date"] <= p["last"]]
    m["impacts"] = mine
    areas = {a["place"]: a for a in m.get("areas") or []}
    for a in areas.values():
        a["items"] = [i for i in a["items"] if i.get("type") != "impact"]
    for k, x in enumerate(mine):
        if not x["place"]:
            continue
        pe = place_entry(x["place"], places)
        a = areas.setdefault(pe["place"], {"place": pe["place"], "kind": pe["kind"], "districts": pe["districts"], "seat": pe["seat"], "items": []})
        a["items"].append({"type": "impact", "impact": k, "date": x["date"], "label": x["label"]})
    m["areas"] = sorted([a for a in areas.values() if a["items"]], key=lambda a: (min(a["districts"] or [9]), a["kind"] != "city", a["place"]))
    return m


def month_waves(waves, month):
    """The month's highest waves at the Half Moon Bay buoy (waves.json "daily", from 2026-11-26)."""
    d = ((waves or {}).get("daily") or {}).get("46012") or {}
    days = {k: v for k, v in d.items() if k[:7] == month and v.get("ft") is not None}
    if not days:
        return None
    top = max(days, key=lambda k: days[k]["ft"])
    return {"buoy": "Half Moon Bay buoy (46012)", "max_ft": days[top]["ft"], "max_day": top, "period_s": days[top].get("s"),
            "days": len(days), "days_15ft": sum(1 for v in days.values() if v["ft"] >= 15), "daily": [[k, days[k]["ft"]] for k in sorted(days)]}


def months_to_build(now):
    m = now.strftime("%Y-%m")
    if now.day <= REDO_DAYS:
        prev = (now.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
        return [prev, m]
    return [m]


def run(folder, now):
    p = lambda n: os.path.join(folder, n)   # noqa: E731
    prev = read_json(p("monthly_summary.json"), {}) or {}
    tt, hist = read_json(p("tide_tracker.json"), {}), read_json(p("tide_tracker_history.json"), {})
    tracker, roads = read_json(p("storm_tracker.json"), {}), read_json(p("road_closures.json"), {})
    reports = read_json(p("community_flood_reports.json"), {})
    waves = read_json(p("waves.json"), {})
    rows = read_csv(p("status_log.csv"))
    months = dict(prev.get("months") or {})
    for m in months_to_build(now):
        months[m] = build_month(m, now, tt, hist, tracker, rows, roads, reports, waves=waves)
    places = load_places()[0]
    impacts = read_impacts()
    for m in months:   # staff-entered impacts go on every kept month, so a row added late still shows
        apply_impacts(months[m], impacts, places)
    out = {"generated": now.strftime("%Y-%m-%d %H:%M"), "months": dict(sorted(months.items()))}
    with open(p("monthly_summary.json"), "w") as f:
        json.dump(out, f, separators=(",", ":"))
    m = out["months"][now.strftime("%Y-%m")]
    print("monthly_summary %s: %d high-tide periods, %d storms, %d road closures" % (m["month"], len(m["tide_periods"]), len(m["storms"]), len(m["roads"])))
    return out


def main(argv=None):
    a = list(argv if argv is not None else sys.argv)[1:]
    if not a:
        print(__doc__)
        return 2
    from zoneinfo import ZoneInfo
    now = dt.datetime.now(ZoneInfo("America/Los_Angeles")).replace(tzinfo=None, second=0, microsecond=0)
    if "--now" in a:
        i = a.index("--now"); now = parse_t(a[i + 1]); del a[i:i + 2]
    run(a[0], now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
