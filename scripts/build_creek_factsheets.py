"""
Creek fact sheets: one Markdown page per creek in lookups/factsheets/, built from the tables the site already uses,
so they never drift from what the pages show. Don't edit the fact sheets by hand; edit the tables and rerun:

    python scripts/build_creek_factsheets.py

Reads (lookups/): creeks.csv, creek_gauges.csv, thresholds.csv, rain_frequency.csv, tide_stations.csv,
settings.csv, creek_facts.csv (cities, outlet, description), gauge_facts.csv (record, reporting, history, quirks),
rising_fast_results.csv (from scripts/evaluate_rising_fast.py), onerain_dashboard_thresholds.csv (OneRain's own
dashboard colors and sensor thresholds, for reference). Coordinates come from the site table in
scripts/fetch_atlas14.py. Writes lookups/factsheets/<creek>.md and lookups/factsheets/README.md (index).
"""

import csv
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LK = os.path.join(ROOT, "lookups")
OUT = os.path.join(LK, "factsheets")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_atlas14 import SITES   # (number, name, lat, lon) for every OneRain and USGS site we use

COORDS = {num.upper(): (name, lat, lon) for num, name, lat, lon in SITES}
ONERAIN_SENSOR = "https://oneshorelineearlywarning.onerain.com/sensor/?site_id={site_id}&site={site}&device_id={device_id}&device={device}"
USGS_PAGE = "https://waterdata.usgs.gov/monitoring-location/USGS-{0}/"
KEY_MINUTES = (60, 1440)   # always shown; plus the windows the creek page and OneRain use


def rows(name):
    p = os.path.join(LK, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8-sig") as f:
        return [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(f)]


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def dur(m):
    m = int(m)
    return f"{m} min" if m < 60 else f"{m // 60} hr"


def lead(m):
    if m in ("", None):
        return "–"
    m = int(float(m))
    return f"{m} min" if m < 90 else f"{m / 60:.1f} h"


GLOSSARY = [
    "> **Words used on this page** (the same words for both systems)",
    ">",
    "> - **Threshold:** any set value that changes a color or a status, in either system.",
    "> - **Flood level** (2026 Update): a threshold on creek height (or a rain amount) tied to an effect downstream, such "
    "as how full the channel is or water on a road. Only flood levels say anything about flooding.",
    "> - **Alert level** (2026 Update): a rain alert (Heavy, Very heavy, Intense: how rare the rain is) or **rising fast** "
    "(the creek rose at least a set amount within an hour). Not tied to flooding.",
    "> - **Status** (2026 Update): the one overall message for a creek: Flooding likely, Be ready, Stay alert or No alerts. "
    "It comes from the flood levels and alert levels.",
    "> - **OneRain threshold:** a named level set on a OneRain sensor (for example Flood Watch, 3.25 ft). It colors that "
    "gauge's readings and graph; it doesn't send a message by itself.",
    "> - **OneRain dashboard color:** the green, orange or red a OneRain dashboard gives a reading. Set separately from "
    "the thresholds.",
    "> - **Notification:** a message sent to people. OneRain sends these through separate *alarm* rules. The 2026 Update "
    "sends none; it only displays.",
    ">",
    "> **Units.** Creek heights are the gauge's own reading in feet (above the gauge's zero), not an elevation. "
    "Tide heights are in feet NAVD88, a survey datum; MHHW = the average daily high tide, MLLW = the average daily low tide. "
    "A 1-, 2- or 5-year storm is rain that heavy at that gauge, with about a 63%, 39% or 18% chance in any year (NOAA Atlas 14). "
    "Water year: October 1 to September 30, named for the year it ends.",
    ">",
    "> **Names.** **OneRain** is the County's existing gauge system and dashboards (what many people call \"FEWS\"). "
    "**FEWS 2026 Update** (\"2026 Update\") is the new public creek and tide status site built on OneRain's data. These "
    "fact sheets describe the 2026 Update and compare it with OneRain.",
]

LINKED = {
    "Yes": "Yes",
    "Partly": "Yes, but what they mean isn't recorded",
    "OneRain": "None in the 2026 Update (OneRain has some; see Thresholds below)",
    "No": "None",
}


def plain_rarity(txt):
    """'41104: between the 2-yr (1.38) and 5-yr (1.69)' -> 'between a 2- and 5-year storm (1.38-1.69 in)'."""
    if not txt:
        return "–"
    if txt.startswith("USGS record"):
        m = re.search(r"reached in (\d+) of (\d+) water years \(highest ([\d.]+) ft\)", txt)
        return f"{m[1]} of {m[2]} years (highest {m[3]} ft)" if m else txt
    if txt.startswith("No NOAA"):
        return "not in the NOAA table used here"
    parts = txt.replace("NOAA Atlas 14 at ", "").split("; ")
    out = []
    for p in parts:
        who, _, t = p.partition(": ")
        m = re.match(r"between the (\d+)-yr \(([\d.]+)\) and (\d+)-yr \(([\d.]+)\)", t)
        if m:
            s = f"between a {m[1]}- and {m[3]}-year storm ({float(m[2]):g}–{float(m[4]):g} in)"
        elif t.startswith("below"):
            m = re.match(r"below the (\d+)-yr \(([\d.]+)\)", t); s = f"less than a {m[1]}-year storm ({float(m[2]):g} in)"
        elif t.startswith("above"):
            m = re.match(r"above the (\d+)-yr \(([\d.]+)\)", t); s = f"more than a {m[1]}-year storm ({float(m[2]):g} in)"
        else:
            s = t
        out.append((f"at {who}: " if len(parts) > 1 else "") + s)
    return "; ".join(out)


def upd(t):
    """Data tables say 'FEWS' for the new site; on the pages it is 'the 2026 Update'."""
    t = re.sub(r"\bFEWS's\b", "the 2026 Update's", t or "")
    t = re.sub(r"\bno FEWS gauge\b", "not a 2026 Update gauge", t)
    t = re.sub(r"\bFEWS\b", "the 2026 Update", t)
    return re.sub(r"(^|[.!?]\s+|:\*\*\s+)the 2026 Update", lambda m: m[1] + "The 2026 Update", t)


def also_fews(note):
    m = re.match(r"(Same as FEWS \(thresholds.csv\)\.|Not used by FEWS\.|Differs from FEWS \(([^)]*)\)\.)\s*", note or "")
    if not m:
        return "No", note or ""
    v = "Yes" if m[1].startswith("Same") else "No" if m[1].startswith("Not") else f"Different: {m[2].replace('FEWS: ', '2026 Update uses ')}"
    return v, note[m.end():]


def main():
    creeks = rows("creeks.csv")
    gauges = rows("creek_gauges.csv")
    thresholds = rows("thresholds.csv")
    tides = {r["station"]: r for r in rows("tide_stations.csv")}
    settings = {r["key"]: r["value"] for r in rows("settings.csv")}
    cfacts = {r["creek"]: r for r in rows("creek_facts.csv")}
    gfacts = {r["gauge"]: r for r in rows("gauge_facts.csv")}
    results = rows("rising_fast_results.csv")
    dash = rows("onerain_dashboard_thresholds.csv")
    freq = {}
    for r in rows("rain_frequency.csv"):
        freq.setdefault(r["onerain_number"].upper(), []).append(r)
    default_rise = settings.get("RISE_FT", "0.5")
    os.makedirs(OUT, exist_ok=True)
    index = []

    for c in creeks:
        cid = c["creek"]
        cf = cfacts.get(cid, {})
        cg = [g for g in gauges if g["creek"] == cid]
        stages = [g for g in cg if g["type"] == "stage"]
        rains = [g for g in cg if g["type"] == "rain"]
        tide = tides.get(c.get("tide_station", ""), {})
        public = c.get("preview_only", "").lower() != "yes"
        cdash = [d for d in dash if d["creek"] == cid]
        dash_tide = [d for d in cdash if d["kind"] == "dashboard tide color"]
        dash_rain = [d for d in cdash if d["units"] == "in" and d["kind"] != "dashboard tide color"]
        dash_stage = [d for d in cdash if d["kind"] == "sensor threshold" and d["units"] == "ft"]
        stage_th = [t for t in thresholds if t["creek"] == cid and t["type"] == "stage"]
        triggers = [t for t in thresholds if t["creek"] == cid and t["type"] == "rain"]
        meaning = c.get("note", "") if stage_th and "No flood levels" not in c.get("note", "") else ""
        or_levels = [d for d in dash_stage if d["from_value"]]
        or_sites = list(dict.fromkeys(d["onerain_site"] for d in or_levels))
        linked = "Yes" if stage_th and meaning else "Partly" if stage_th else "OneRain" if or_levels else "No"
        label = {g["gauge"]: g["label"] for g in cg}

        # ---- what reviewers are asked to check (plain questions), and internal to-dos
        ask, todo = [], []
        if cf.get("status", "").startswith("draft") or not cf:
            ask.append("**Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?")
        ask.append("**Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?")
        if linked == "Yes":
            ask.append("**Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey "
                       "or past flood?")
        elif linked == "Partly":
            descr = "; ".join(f"{d['threshold_name']} = \"{d['description']}\"" for d in or_levels if d["description"])
            ask.append("**Flood levels:** what do these levels mean for people downstream? The 2026 Update has no recorded meaning"
                       + (f"; OneRain describes them as {descr}" if descr else "") + ". Who set them, and from what?")
        elif linked == "OneRain":
            ask.append(f"**Flood levels:** the 2026 Update has none, but OneRain has its own at {', '.join(or_sites)} (see Thresholds on this page). "
                       "Do you know who set them and from what? Should the 2026 Update use them?")
        else:
            ask.append("**Flood levels:** the 2026 Update has none. Do you know a creek height at " + ("any of the gauges" if len(stages) > 1 else "the gauge")
                       + " where the creek leaves its banks or floods a road, or a past flood we could match to a gauge reading?")
        if triggers:
            ask.append("**Rain triggers:** are the amounts and what they show right?")
            for t in triggers:
                tv = t.get("tide_at_least_navd88")
                if tv and tide.get("mhhw_navd88_ft") and float(tv) < float(tide["mhhw_navd88_ft"]):
                    ask.append(f"**{t['name']}:** the tide part ({tv} ft NAVD88) is below the average daily high tide at "
                               f"{tide.get('name', 'the tide station')} (MHHW {tide['mhhw_navd88_ft']} ft), so it is met on most "
                               "days' higher high tide. Is that the intended tide level?")
        for d in cdash:
            q = d.get("to_confirm", "")
            if q.startswith("[internal]"):
                todo.append(q[len("[internal]"):].strip())
            elif q:
                ask.append(esc(upd(q)))
        for g in cg:
            if "To check:" in g.get("note", ""):
                todo.append(f"{g['label']} ({g['type']}): " + esc(g["note"].split("To check:", 1)[1].strip()))
            if g["type"] == "stage" and g["gauge"] not in gfacts:
                todo.append(f"{g['label']}: add record, reporting and history to gauge_facts.csv")
        if not cf:
            todo.append("Add this creek to creek_facts.csv")

        L = [f"# {c['name']}", "",
             "*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to "
             "the review request. Everything else on the page is background.*", "",
             "> **What we need you to check**", ">"]
        L += [f"> - [ ] {a}" for a in ask]
        L += ["", *GLOSSARY, ""]

        # ---- at a glance
        tide_txt = (f"NOAA {c['tide_station']} {esc(tide.get('name', ''))} (average daily high tide, MHHW, "
                    f"{tide.get('mhhw_navd88_ft', '?')} ft NAVD88)" if c.get("tide_station") else
                    "None set for this creek in the 2026 Update (coastal creek)"
                    + (f". OneRain's dashboard uses {esc(dash_tide[0]['onerain_site'])}" if dash_tide else ""))
        L += ["## At a glance", "", "| | |", "|---|---|",
              f"| On the 2026 Update site | {'Public pages' if public else 'Staff preview only (not yet on the public pages)'} |",
              f"| Cities and communities | {esc(cf.get('cities', '')) or '**To add**'}"
              + (" *(draft)*" if cf.get("status", "").startswith("draft") else "") + " |",
              f"| Drains to | {esc(cf.get('drains_to', '')) or '**To add**'} |",
              f"| Description | {esc(cf.get('description', '') or c.get('intro', ''))} |",
              f"| Flood levels set? | {LINKED[linked]}" + ("; plus rain triggers" if triggers else "") + " |",
              f"| Tide station | {tide_txt} |",
              f"| Rain totals on the 2026 Update page | {', '.join(dur(m) for m in c.get('rain_windows_min', '').split() if m.isdigit())} |",
              ""]

        # ---- creek level gauges
        L += ["## Creek level gauges", ""]
        for g in stages:
            usgs = g.get("source", "").lower() == "usgs"
            num = g["usgs_site"] if usgs else g["onerain_number"]
            nm, lat, lon = COORDS.get(num.upper(), (g.get("site_name") or g["label"], None, None))
            link = USGS_PAGE.format(num) if usgs else (ONERAIN_SENSOR.format(**g) if g.get("site_id") else "")
            gf = gfacts.get(g["gauge"], {})
            rise = g.get("rise_ft", "")
            tid = g.get("tidal", "").lower()
            tc = gf.get("tide_check", "")
            tc = tc[0].upper() + tc[1:] if tc else ""
            tidal = ("Yes" if tid == "yes" else "No" if tid == "no" else "Not yet confirmed") + (f". {esc(tc)}" if tc else "")
            note = g.get("note", "").split("To check:", 1)[0].strip(" ·")
            note = "" if note.startswith("No flood levels") or note == gf.get("history_and_issues", "") else note
            rb = re.sub(r"(Flood )?Monitoring crossings", "rises to Flood Monitoring", gf.get("rise_basis", ""))
            rst = gf.get("rise_status", "")
            rst = "Default setting, not yet tested on this gauge" if rst == "Default" else rst
            L += [f"### {esc(g.get('site_name') or nm)}", "", "| | |", "|---|---|",
                  f"| Source and ID | {'USGS' if usgs else 'OneRain'} {num}" + (f" ([gauge page]({link}))" if link else "") + " |",
                  f"| Location | {f'{lat:.5f}, {lon:.5f}' if lat is not None else '**To add**'} |",
                  f"| Reports | {esc(gf.get('reporting', '')) or g.get('reports', '')} |",
                  f"| Record starts | {esc(gf.get('record_start', '')) or '**To add**'} |",
                  f"| Affected by the tide? | {tidal} |",
                  f"| Rising-fast alert | " + ("Off at this gauge" if rise.lower() == "off" else
                                             f"{rise or default_rise} ft within an hour"
                                             + ("" if rise else " (default)")) + (f" · **{esc(rst)}**" if rst else "") + " |"]
            if rb:
                L.append(f"| Why this rising-fast setting | {esc(rb)} |")
            if gf.get("history_and_issues"):
                L.append(f"| History and known issues | {esc(gf['history_and_issues'])} |")
            if note:
                L.append(f"| Note shown on the 2026 Update page | {esc(note)} |")
            L.append("")

            th = sorted([t for t in stage_th if t["gauge"] == g["gauge"]], key=lambda t: float(t["value"]))
            if th:
                L += ["**Flood levels** (gauge height, ft)", "", "| Level | Name | Height (ft) | Source | Notes |", "|---|---|---|---|---|"]
                L += [f"| {t['level']} | {esc(t['name'])} | {t['value']} | {esc(t['source'])} | {esc(t.get('notes', ''))} |" for t in th]
                L += [""]
                if meaning:
                    L += [f"What they mean: {esc(meaning)}"
                          + (" Roadway Flooded = water detected on the road." if any(t["name"] == "Roadway Flooded" for t in th) else "")]
                    if "channel capacity" in meaning:
                        L += ["", "By this definition, Monitoring and Watch mean the water is still in the channel; only Flood "
                              "Warning means flooding is likely."]
                else:
                    L += ["What they mean: **not recorded**."]
                signed = all(t.get("checked_by") for t in th)
                L += ["", "Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026"
                      + ". Who set the heights, and from what study, "
                      "survey or past flood, isn't recorded. " + ("Status: **Confirmed**." if signed else
                      "Status: **From OneRain, basis unknown; not yet signed off.**")]
                L += [""]
            else:
                own = [d for d in or_levels if d["fews_gauge"] == g["gauge"]]
                L += ["**Flood levels:** none in the 2026 Update, so this creek's status comes from alert levels only (rain and rising fast)."
                      + (" OneRain has its own levels for this gauge: see Thresholds below." if own else ""), ""]

            res = [r for r in results if r["gauge"] == g["gauge"]]
            if res:
                y = float(res[0]["years"]); n = int(res[0]["crossings"])
                L += ["<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>", ""]
                L += [(f"Tested on {y:.1f} years of readings, against the lowest flood level ({th[0]['name']}, "
                       f"{res[0]['big_storm_level_ft']} ft): \"warned\" means an alert came before the creek reached it."
                       if th else
                       f"Tested on {y:.1f} years of readings, against {res[0]['big_storm_level_ft']} ft, the creek's typical "
                       "yearly high (about a 2-year event). That is **not** a flood level: \"warned\" means an alert came "
                       "before a typical yearly high, not before flooding.")
                      + (f" Only {n} such rises in the record, so treat these results as rough." if n < 10 else ""), "",
                      f"| Alert setting (ft within an hour) | {'Alerts per year' if y >= 1 else 'Alerts (total)'} | "
                      "Warned before reaching it | Typical warning time |", "|---|---|---|---|"]
                for r in res:
                    mark = " (current setting)" if r["chosen"] == "True" else ""
                    py = f"{int(r['episodes']) / y:.1f}" if y >= 1 else r["episodes"]
                    L.append(f"| {r['rule_ft']}{mark} | {py} | {r['warned']} of {r['crossings']} | {lead(r['lead_med'])} |")
                L += ["", "How settings were chosen: the highest setting that still warned before all, or all but one, of the "
                      "big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. "
                      "Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).", "", "</details>", ""]

        # ---- rain
        L += ["## Rain gauges", ""]
        if not rains:
            L += ["None.", ""]
        else:
            L += ["| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |", "|---|---|---|---|---|"]
            for g in rains:
                nm, lat, lon = COORDS.get(g["onerain_number"].upper(), (g["label"], None, None))
                use = ("Counts toward the creek's rain alert only (not shown on the page)" if g.get("role") == "supporting"
                       else "Shown on the 2026 Update page and counts toward the rain alert")
                L.append(f"| {esc(g['label'])} | {g['onerain_number']} | "
                         f"{f'{lat:.5f}, {lon:.5f}' if lat is not None else '**To add**'} | {esc(g.get('where', ''))} | {use} |")
            L.append("")
            if triggers:
                L += ["**Rain triggers** (flood levels for rain: each one sets the creek to the status shown)", "",
                      "| Gauge | Rain within | Rain (in) | And the tide is at least | Shows | Why this number | Status |",
                      "|---|---|---|---|---|---|---|"]

                def why(t):
                    src = t.get("source", "")
                    if "analysis of" in src:
                        yrs = re.search(r"analysis of ([0-9–-]+ events)", src)
                        return (f"Rain amount from an analysis of {yrs[1] if yrs else 'past events'}; tide level from OneRain alarm "
                                "rule #34 (7.5 ft MLLW, converted to NAVD88)")
                    return f"Copied from {src}; no study recorded"
                L += [f"| {esc(label.get(t['gauge'], t['gauge']))} | {dur(t['minutes'])} | {t['value']} | "
                      f"{(t['tide_at_least_navd88'] + ' ft NAVD88') if t.get('tide_at_least_navd88') else '–'} | "
                      f"{esc(t['name'])} | {esc(why(t))} | {'Confirmed' if t.get('checked_by') else 'From OneRain, not yet signed off'} |"
                      for t in triggers]
                L += [""]
            wins = set(KEY_MINUTES) | {int(m) for m in c.get("rain_windows_min", "").split() if m.isdigit()} \
                | {int(d["window_min"]) for d in dash_rain if d["window_min"]}
            avail = {int(r["minutes"]) for g in rains for r in freq.get(g["onerain_number"].upper(), [])}
            wins = sorted(w for w in wins if w in avail)
            L += ["**Rain alerts** (Heavy, Very heavy, Intense). Why these numbers: they are the 1-, 2- and 5-year storm at each "
                  "gauge from NOAA Atlas 14, a standard way to say how rare rain is at that exact spot. Status: **Provisional**: a "
                  "starting point, not yet checked against past floods on this creek.", ""]
            L += ["<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>", "",
                  "The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, "
                  "Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether "
                  "the creek floods.", "",
                  "| Gauge | Level | " + " | ".join(dur(m) for m in wins) + " |", "|---|---|" + "---|" * len(wins)]
            for g in rains:
                fr = freq.get(g["onerain_number"].upper(), [])
                for lvl, nm in (("1", "Heavy (1-year)"), ("2", "Very heavy (2-year)"), ("3", "Intense (5-year)")):
                    vals = [next((r["value_in"] for r in fr if r["level"] == lvl and r["minutes"] == str(m)), "–") for m in wins]
                    L.append(f"| {esc(g['label'])} | {nm} | " + " | ".join(vals) + " |")
            src = next((r["source"] for g in rains for r in freq.get(g["onerain_number"].upper(), [])), "")
            L += ["", f"Source: {esc(src) or 'NOAA Atlas 14'}.", "", "</details>", ""]

        # ---- FEWS (what the site uses today) compared with OneRain
        L += ["## Thresholds: the 2026 Update compared with OneRain today", "",
              ("The 2026 Update shows this creek's status on its public pages." if public else
               "On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview.")
              + " The **2026 Update** columns are what the new site uses. The **OneRain** columns are what is set in OneRain today "
              "(read Oct 16–17, 2026): *thresholds* set on each sensor, and *dashboard colors*. Neither sends a message by itself; "
              "OneRain sends notifications only through separate alarm rules. The 2026 Update doesn't read any of these; they're "
              "shown so the two systems can be compared.", ""]
        cmp_notes = []

        # creek height
        L += ["**Creek height (ft, gauge height)**", "",
              "| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |", "|---|---|---|---|---|"]
        for g in stages:
            num = g["usgs_site"] if g.get("source", "").lower() == "usgs" else g["onerain_number"]
            name = esc(g.get("site_name") or g["label"])
            fews = {t["name"]: t["value"] for t in stage_th if t["gauge"] == g["gauge"]}
            orn = {d["threshold_name"]: d for d in dash_stage if d["fews_gauge"] == g["gauge"] and d["from_value"]}
            levels = sorted(set(fews) | set(orn), key=lambda k: float(fews.get(k) or orn[k]["from_value"]))
            for k in levels:
                fv, od = fews.get(k), orn.get(k)
                ov = od["from_value"] if od else None
                same = ("Same" if fv and ov and abs(float(fv) - float(ov)) < 0.005 else "Different" if fv and ov else
                        "2026 Update only" if fv else "OneRain only (the 2026 Update doesn't use it)")
                L.append(f"| {name} | {esc(k)} | {fv + ' ft' if fv else '–'} | "
                         + (f"{ov} ft (\"{esc(od['description'])}\")" if od else "–") + f" | {same} |")
            if not levels:
                L.append(f"| {name} | – | none | none | – |")
            rise = g.get("rise_ft", "")
            L.append(f"| {name} | Rising fast | " + ("off" if rise.lower() == "off" else f"{rise or default_rise} ft within an hour")
                     + " | none | 2026 Update only |")
        for d in dash_stage:
            if d["from_value"] and not d["fews_gauge"]:
                L.append(f"| {esc(d['onerain_site'])} (not a 2026 Update gauge) | {esc(d['threshold_name'])} | – | "
                         f"{d['from_value']} ft (\"{esc(d['description'])}\") | OneRain only |")
                n = also_fews(d["notes"])[1]
                if n and n not in cmp_notes: cmp_notes.append(n)
        L.append("")
        for d in dash_stage:
            if "Out of Service" in d.get("notes", "") and "OneRain shows this gauge's creek-level sensor as Out of Service." not in cmp_notes:
                cmp_notes.append("OneRain shows this gauge's creek-level sensor as Out of Service.")
        usgs_hits = [d for d in dash_stage if d["from_value"] and d["atlas14_comparison"].startswith("USGS")]
        if usgs_hits:
            L += ["How often the creek reached OneRain's levels (USGS record, water years 2008–2026): "
                  + "; ".join(f"{d['threshold_name']} {d['from_value']} ft: {plain_rarity(d['atlas14_comparison'])}" for d in usgs_hits) + ".", ""]

        # rain: one row per gauge and time window used by FEWS triggers or by OneRain
        def lvl_text(num, w):
            fr = freq.get(num.upper(), [])
            v = {r["level"]: r["value_in"] for r in fr if r["minutes"] == str(w)}
            return (f"alerts: Heavy {v['1']}, Very heavy {v['2']}, Intense {v['3']} in" if all(k in v for k in "123") else "")
        gauge_rows = {}
        for g in rains:
            num = g["onerain_number"].upper()
            ws = {int(t["minutes"]) for t in triggers if t["gauge"] == g["gauge"]} | \
                 {int(d["window_min"]) for d in dash_rain if d["onerain_number"].upper() == num and d["window_min"] and d["from_value"]}
            gauge_rows[(num, g["label"], True)] = sorted(ws)
        for d in dash_rain:
            num = d["onerain_number"].upper()
            if d["from_value"] and d["window_min"] and not any(k[0] == num for k in gauge_rows):
                gauge_rows.setdefault((num, d["onerain_site"] or "to confirm", False), [])
                if int(d["window_min"]) not in gauge_rows[(num, d["onerain_site"] or "to confirm", False)]:
                    gauge_rows[(num, d["onerain_site"] or "to confirm", False)].append(int(d["window_min"]))
        rrows = []
        for (num, lab, is_fews), ws in gauge_rows.items():
            for w in ws:
                trig = [t for t in triggers if t["gauge"] in [g["gauge"] for g in rains if g["onerain_number"].upper() == num]
                        and int(t["minutes"]) == w]
                fews = "; ".join(f"**{esc(t['name'])}** at {t['value']} in" + (f" (and tide ≥ {t['tide_at_least_navd88']} ft NAVD88)"
                                 if t.get("tide_at_least_navd88") else "") for t in trig)
                if is_fews:
                    lv = lvl_text(num, w)
                    fews = "; ".join(x for x in (fews, lv) if x) or "no rain level for this window"
                else:
                    fews = "– (the 2026 Update doesn't use this gauge)"
                ds = [d for d in dash_rain if d["onerain_number"].upper() == num and d["from_value"] and str(d["window_min"]) == str(w)]
                al = [d for d in ds if d["kind"] == "sensor threshold"]
                co = [d for d in ds if d["kind"] == "dashboard rain color" and d["color"] != "green"]
                al_t = "; ".join(re.sub(r"^(Hourly|30-minute) rainfall intensity ", "", re.sub(r" \(OneRain level: [^)]*\)", "", d["threshold_name"])).capitalize()
                                 + f" {d['from_value']} in" for d in al) or "none"
                co_t = "; ".join(f"{d['color']} from {d['from_value']} in" for d in co) or "none"
                rrows.append(f"| {esc(lab)} | {dur(w)} | {fews} | {al_t} | {co_t} |")
        if rrows:
            L += ["**Rain (inches within the time shown)**", "",
                  "The 2026 Update's rain alerts (Heavy, Very heavy, Intense) are the 1-, 2- and 5-year storm at the gauge, checked over "
                  "windows from 15 minutes to 48 hours; only the windows OneRain or a 2026 Update trigger uses are listed here.", "",
                  "| Gauge | Rain within | 2026 Update uses | OneRain threshold | OneRain dashboard color |", "|---|---|---|---|---|"] + rrows + [""]
        none_r = [d["onerain_site"] for d in dash_rain if not d["from_value"]]
        if none_r:
            L += ["No OneRain rain thresholds or dashboard colors on: " + "; ".join(esc(x) for x in dict.fromkeys(none_r)) + ".", ""]
        for d in dash_rain:
            n = also_fews(d["notes"])[1]
            n = re.sub(r"(Rain (alarms|thresholds) set on the Rain Increment sensor[^.]*\.|Only window on the [^.]*\.|Same values as the gauge[^.]*\.|No rain (alarms|thresholds) on this gauge in OneRain\.|A 4th color row[^.]*\.|San Bruno Mountain \(41200\) has no dashboard colors\.|Pescadero and Butano dashboard; only window\.)\s*", "", n).strip()
            if n and n not in cmp_notes: cmp_notes.append(n)

        # tide
        if c.get("tide_station") or dash_tide:
            L += ["**Tide**", "", "| | 2026 Update uses | OneRain dashboard color |", "|---|---|---|"]
            fews_t = (f"NOAA {c['tide_station']} {esc(tide.get('name', ''))}: tide graph and high-tide lines (MHHW "
                      f"{tide.get('mhhw_navd88_ft', '?')} ft NAVD88)" if c.get("tide_station") else
                      "not linked to this creek" + (f"; the 2026 Update shows {esc(tides[dash_tide[0]['onerain_number']]['name'])} on its "
                      f"{esc(tides[dash_tide[0]['onerain_number']]['used_for'])}" if dash_tide and dash_tide[0]['onerain_number'] in tides else ""))
            co = "; ".join(f"{esc(d['onerain_site'])}: {d['color']} from {d['from_value']} ft (datum not shown; assumed MLLW)"
                           for d in dash_tide if d["color"] != "green") or "none recorded"
            L += [f"| Tide | {fews_t} | {co} |", ""]
            for d in dash_tide:
                n = re.sub(r"^Pescadero and Butano dashboard; ", "", d["notes"]).strip()
                if n and n not in cmp_notes: cmp_notes.append(n[0].upper() + n[1:])
        if cmp_notes:
            L += ["Notes:", ""] + [f"- {esc(upd(n))}" for n in cmp_notes] + [""]

        # ---- internal to-dos
        if todo:
            L += ["<details><summary>Internal to-do for the project team (reviewers can skip)</summary>", ""]
            L += [f"- {t}" for t in dict.fromkeys(todo)] + ["", "</details>", ""]
        L += ["---", "", "*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; "
              "edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*", ""]

        with open(os.path.join(OUT, f"{cid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(L))
        index.append((c, cf, stages, rains, public, linked, len(ask)))

    I = ["# FEWS 2026 Update: creek fact sheets (draft for review)", "",
         "One page per creek in the **FEWS 2026 Update**, the new public creek and tide status site built on OneRain's gauge data "
         "(it is not OneRain's own dashboards; each page compares the two). Each page covers where the creek runs, its gauges, its flood levels and alerts, "
         "and what those are based on. Each page opens with a short **What we need you to check** list; please answer by "
         "replying to the review request. Everything else on a page is background.", "",
         "**Flood levels set?** Yes = creek heights tied to flooding, with a recorded meaning. \"Yes, but what they mean "
         "isn't recorded\" = heights are set but their meaning isn't written down. \"None in the 2026 Update (OneRain has some)\" = the 2026 Update has "
         "none, but OneRain's own system has levels whose basis isn't recorded. None = no creek height is tied to flooding "
         "yet; the creek's status comes from rain and how fast it is rising.", "",
         "| Creek | On the 2026 Update site | Cities and communities | Creek gauges | Rain gauges | Flood levels set? | Questions |",
         "|---|---|---|---|---|---|---|"]
    for c, cf, stages, rains, public, linked, nq in index:
        I.append(f"| [{c['name']}]({c['creek']}.md) | {'Public pages' if public else 'Staff preview only'} | "
                 f"{esc(cf.get('cities', ''))} | {len(stages)} | {len(rains)} | {LINKED[linked]} | {nq} |")
    I += ["", "*Generated from the 2026 Update lookup tables by `scripts/build_creek_factsheets.py`; edit the tables "
          "(`creek_facts.csv`, `gauge_facts.csv`, `thresholds.csv`, `onerain_dashboard_thresholds.csv` and others in `lookups/`), "
          "not these pages.*"]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(I) + "\n")
    print(f"wrote {len(index)} fact sheets to {OUT}")


if __name__ == "__main__":
    main()
