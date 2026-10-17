"""
Creek fact sheets: one Markdown page per creek in lookups/factsheets/, built from the tables the site already uses,
so they never drift from what the pages show. Don't edit the fact sheets by hand; edit the tables and rerun:

    python scripts/build_creek_factsheets.py

Reads (lookups/): creeks.csv, creek_gauges.csv, thresholds.csv, rain_frequency.csv, tide_stations.csv,
settings.csv, creek_facts.csv (cities, outlet, description), gauge_facts.csv (record, reporting, history, quirks),
rising_fast_results.csv (from scripts/evaluate_rising_fast.py), onerain_dashboard_thresholds.csv (OneRain's own
dashboard colors and gauge alarms, for reference). Coordinates come from the site table in
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
    "> **How to read this page**",
    ">",
    "> - **Flood level:** a creek height (or rain amount) tied to an effect downstream, such as how full the channel is "
    "or water on a road. Only flood levels say anything about flooding.",
    "> - **Alert level:** says how unusual the rain is, or how fast the creek is rising. Not tied to flooding.",
    "> - **Rising fast:** the creek rose at least the set amount (for example 0.5 ft) within an hour.",
    "> - **Creek heights** are the gauge's own reading in feet (height above the gauge's zero), not an elevation. "
    "**Tide heights** are in feet NAVD88, a survey datum. MHHW = the average daily high tide; MLLW = the average daily low tide.",
    "> - **1-year, 2-year, 5-year storm:** rain that heavy at that gauge has about a 63%, 39% or 18% chance in any year "
    "(NOAA Atlas 14).",
    "> - **Water year (WY):** October 1 to September 30, named for the year it ends.",
    "> - **OneRain** is the system that runs the gauges and the County's dashboards; FEWS is the public flood warning site "
    "built on its data.",
]

LINKED = {
    "Yes": "Yes",
    "Partly": "Yes, but what they mean isn't recorded",
    "OneRain": "None in FEWS (OneRain has some; see the appendix)",
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


def also_fews(note):
    m = re.match(r"(Same as FEWS \(thresholds.csv\)\.|Not used by FEWS\.|Differs from FEWS \(([^)]*)\)\.)\s*", note or "")
    if not m:
        return "No", note or ""
    v = "Yes" if m[1].startswith("Same") else "No" if m[1].startswith("Not") else f"Different: {m[2].replace('FEWS: ', 'FEWS uses ')}"
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
        dash_stage = [d for d in cdash if d["kind"] == "gauge alarm threshold" and d["units"] == "ft"]
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
            ask.append("**Flood levels:** what do these levels mean for people downstream? FEWS has no recorded meaning"
                       + (f"; OneRain describes them as {descr}" if descr else "") + ". Who set them, and from what?")
        elif linked == "OneRain":
            ask.append(f"**Flood levels:** FEWS has none, but OneRain has its own at {', '.join(or_sites)} (see the appendix). "
                       "Do you know who set them and from what? Should FEWS use them?")
        else:
            ask.append("**Flood levels:** FEWS has none. Do you know a creek height at " + ("any of the gauges" if len(stages) > 1 else "the gauge")
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
                ask.append(esc(q))
        for g in cg:
            if "To check:" in g.get("note", ""):
                todo.append(f"{g['label']} ({g['type']}): " + esc(g["note"].split("To check:", 1)[1].strip()))
            if g["type"] == "stage" and g["gauge"] not in gfacts:
                todo.append(f"{g['label']}: add record, reporting and history to gauge_facts.csv")
        if not cf:
            todo.append("Add this creek to creek_facts.csv")

        L = [f"# {c['name']}", "",
             "*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to "
             "the review request. Everything else on the page is background.*", "",
             "> **What we need you to check**", ">"]
        L += [f"> - [ ] {a}" for a in ask]
        L += ["", *GLOSSARY, ""]

        # ---- at a glance
        tide_txt = (f"NOAA {c['tide_station']} {esc(tide.get('name', ''))} (average daily high tide, MHHW, "
                    f"{tide.get('mhhw_navd88_ft', '?')} ft NAVD88)" if c.get("tide_station") else
                    "None set for this creek in FEWS (coastal creek)"
                    + (f". OneRain's dashboard uses {esc(dash_tide[0]['onerain_site'])}" if dash_tide else ""))
        L += ["## At a glance", "", "| | |", "|---|---|",
              f"| On the FEWS site | {'Public pages' if public else 'Staff preview only (not yet on the public pages)'} |",
              f"| Cities and communities | {esc(cf.get('cities', '')) or '**To add**'}"
              + (" *(draft)*" if cf.get("status", "").startswith("draft") else "") + " |",
              f"| Drains to | {esc(cf.get('drains_to', '')) or '**To add**'} |",
              f"| Description | {esc(cf.get('description', '') or c.get('intro', ''))} |",
              f"| Flood levels set? | {LINKED[linked]}" + ("; plus rain triggers" if triggers else "") + " |",
              f"| Tide station | {tide_txt} |",
              f"| Rain totals on the FEWS page | {', '.join(dur(m) for m in c.get('rain_windows_min', '').split() if m.isdigit())} |",
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
            L += [f"### {esc(g.get('site_name') or nm)}", "", "| | |", "|---|---|",
                  f"| Source and ID | {'USGS' if usgs else 'OneRain'} {num}" + (f" ([gauge page]({link}))" if link else "") + " |",
                  f"| Location | {f'{lat:.5f}, {lon:.5f}' if lat is not None else '**To add**'} |",
                  f"| Reports | {esc(gf.get('reporting', '')) or g.get('reports', '')} |",
                  f"| Record starts | {esc(gf.get('record_start', '')) or '**To add**'} |",
                  f"| Affected by the tide? | {tidal} |",
                  f"| Rising-fast alert | " + ("Off at this gauge" if rise.lower() == "off" else
                                             f"{rise or default_rise} ft within an hour"
                                             + ("" if rise else " (default; not yet tested on this gauge's history)")) + " |"]
            if gf.get("history_and_issues"):
                L.append(f"| History and known issues | {esc(gf['history_and_issues'])} |")
            if note:
                L.append(f"| Note shown on the FEWS page | {esc(note)} |")
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
                L += [""]
            else:
                own = [d for d in or_levels if d["fews_gauge"] == g["gauge"]]
                L += ["**Flood levels:** none in FEWS, so this creek's status comes from alert levels only (rain and rising fast)."
                      + (" OneRain has its own levels for this gauge: see the appendix." if own else ""), ""]

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
                L += ["", "Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).", "", "</details>", ""]

        # ---- rain
        L += ["## Rain gauges", ""]
        if not rains:
            L += ["None.", ""]
        else:
            L += ["| Gauge | OneRain ID | Location | Where | Use in FEWS |", "|---|---|---|---|---|"]
            for g in rains:
                nm, lat, lon = COORDS.get(g["onerain_number"].upper(), (g["label"], None, None))
                use = ("Counts toward the creek's rain alert only (not shown on the page)" if g.get("role") == "supporting"
                       else "Shown on the FEWS page and counts toward the rain alert")
                L.append(f"| {esc(g['label'])} | {g['onerain_number']} | "
                         f"{f'{lat:.5f}, {lon:.5f}' if lat is not None else '**To add**'} | {esc(g.get('where', ''))} | {use} |")
            L.append("")
            if triggers:
                L += ["**Rain triggers** (flood levels for rain: each one sets the creek to the status shown)", "",
                      "| Gauge | Rain within | Rain (in) | And the tide is at least | Shows | Source |", "|---|---|---|---|---|---|"]
                L += [f"| {esc(label.get(t['gauge'], t['gauge']))} | {dur(t['minutes'])} | {t['value']} | "
                      f"{(t['tide_at_least_navd88'] + ' ft NAVD88') if t.get('tide_at_least_navd88') else '–'} | "
                      f"{esc(t['name'])} | {esc(t['source'])} |" for t in triggers]
                L += [""]
            wins = set(KEY_MINUTES) | {int(m) for m in c.get("rain_windows_min", "").split() if m.isdigit()} \
                | {int(d["window_min"]) for d in dash_rain if d["window_min"]}
            avail = {int(r["minutes"]) for g in rains for r in freq.get(g["onerain_number"].upper(), [])}
            wins = sorted(w for w in wins if w in avail)
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

        # ---- appendix: OneRain's own settings
        L += ["## Appendix: OneRain settings (for comparison only)", "",
              "These are set in OneRain itself, on its dashboards (colors) and on the gauges (alarms). FEWS doesn't use them "
              "unless the \"Also a FEWS level?\" column says Yes. Read from OneRain on Oct 16–17, 2026.", ""]
        notes = []

        def mark(n):
            if not n:
                return ""
            if n not in notes:
                notes.append(n)
            return f" [{notes.index(n) + 1}]"

        rain_rows = [d for d in dash_rain if d["from_value"]]
        none_rain = [d for d in dash_rain if not d["from_value"]]
        if rain_rows:
            L += ["**Rain**", "", "| Gauge | Kind | Rain within | Color | Rain (in) | OneRain name | Also a FEWS level? | "
                  "How rare at this gauge |", "|---|---|---|---|---|---|---|---|"]
            for d in rain_rows:
                yes, rest = also_fews(d["notes"])
                if d["kind"].startswith("dashboard"):
                    yes = "No"
                rng = f"{d['from_value']} and up" if d["to_value"] in ("", "999") else f"{d['from_value']}–{d['to_value']}"
                name = re.sub(r" \(OneRain level: [^)]*\)", "", d["threshold_name"])
                L.append(f"| {esc(d['onerain_site'] or '**to confirm**')}{mark(rest)} | "
                         f"{'Dashboard color' if d['kind'].startswith('dashboard') else 'Alarm'} | "
                         f"{dur(d['window_min']) if d['window_min'] else '–'} | {d['color'].capitalize()} | {rng} | "
                         f"{esc(name) or '–'} | {yes} | {esc(plain_rarity(d['atlas14_comparison']))} |")
            L.append("")
        stage_rows = [d for d in dash_stage if d["from_value"]]
        if stage_rows:
            L += ["**Creek height**", "", "| Gauge | OneRain name | OneRain description | Height (ft) | Also a FEWS level? | "
                  "Years reached, WY2008–2026 (USGS) |", "|---|---|---|---|---|---|"]
            for d in stage_rows:
                yes, rest = also_fews(d["notes"])
                L.append(f"| {esc(d['onerain_site'])}{mark(rest)} | {esc(d['threshold_name'])} | {esc(d['description'])} | "
                         f"{d['from_value']} | {yes} | {esc(plain_rarity(d['atlas14_comparison']))} |")
            L.append("")
        if dash_tide:
            L += ["**Tide**", "", "| Station | Color | Range | Note |", "|---|---|---|---|"]
            for d in dash_tide:
                rng = f"{d['from_value']} ft and up" if d["to_value"] in ("", "999") else f"{d['from_value']} to {d['to_value']} ft"
                L.append(f"| {esc(d['onerain_site'])}{mark(d['notes'])} | {d['color'].capitalize()} | {rng} | "
                         "Datum not shown in OneRain (assumed MLLW) |")
            L.append("")
        nones = list(dict.fromkeys(d["onerain_site"] for d in none_rain + [x for x in dash_stage if not x["from_value"]]))
        if nones:
            L += ["No OneRain alarms are set on: " + "; ".join(esc(x) for x in nones) + ".", ""]
        if not cdash:
            L += ["None recorded yet.", ""]
        if notes:
            L += ["Notes:", ""] + [f"{i + 1}. {esc(n)}" for i, n in enumerate(notes)] + [""]

        # ---- internal to-dos
        if todo:
            L += ["<details><summary>Internal to-do for the FEWS team (reviewers can skip)</summary>", ""]
            L += [f"- {t}" for t in dict.fromkeys(todo)] + ["", "</details>", ""]
        L += ["---", "", "*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; "
              "edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*", ""]

        with open(os.path.join(OUT, f"{cid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(L))
        index.append((c, cf, stages, rains, public, linked, len(ask)))

    I = ["# Creek fact sheets: draft for review", "",
         "One page per creek in the flood early warning system (FEWS): where it runs, its gauges, its flood levels and alerts, "
         "and what those are based on. Each page opens with a short **What we need you to check** list; please answer by "
         "replying to the review request. Everything else on a page is background.", "",
         "**Flood levels set?** Yes = creek heights tied to flooding, with a recorded meaning. \"Yes, but what they mean "
         "isn't recorded\" = heights are set but their meaning isn't written down. \"None in FEWS (OneRain has some)\" = FEWS has "
         "none, but OneRain's own system has levels whose basis isn't recorded. None = no creek height is tied to flooding "
         "yet; the creek's status comes from rain and how fast it is rising.", "",
         "| Creek | On the FEWS site | Cities and communities | Creek gauges | Rain gauges | Flood levels set? | Questions |",
         "|---|---|---|---|---|---|---|"]
    for c, cf, stages, rains, public, linked, nq in index:
        I.append(f"| [{c['name']}]({c['creek']}.md) | {'Public pages' if public else 'Staff preview only'} | "
                 f"{esc(cf.get('cities', ''))} | {len(stages)} | {len(rains)} | {LINKED[linked]} | {nq} |")
    I += ["", "*Generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`; edit the tables "
          "(`creek_facts.csv`, `gauge_facts.csv`, `thresholds.csv`, `onerain_dashboard_thresholds.csv` and others in `lookups/`), "
          "not these pages.*"]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(I) + "\n")
    print(f"wrote {len(index)} fact sheets to {OUT}")


if __name__ == "__main__":
    main()
