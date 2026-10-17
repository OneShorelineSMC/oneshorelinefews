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
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LK = os.path.join(ROOT, "lookups")
OUT = os.path.join(LK, "factsheets")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_atlas14 import SITES   # (number, name, lat, lon) for every OneRain and USGS site we use

COORDS = {num.upper(): (name, lat, lon) for num, name, lat, lon in SITES}
ONERAIN_SENSOR = "https://oneshorelineearlywarning.onerain.com/sensor/?site_id={site_id}&site={site}&device_id={device_id}&device={device}"
USGS_PAGE = "https://waterdata.usgs.gov/monitoring-location/USGS-{0}/"
KEY_MINUTES = (15, 60, 180, 1440)


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
        dash_tide = next((d for d in cdash if d["kind"] == "dashboard tide color"), None)
        has_levels = any(t["creek"] == cid and t["type"] == "stage" for t in thresholds)
        has_triggers = any(t["creek"] == cid and t["type"] == "rain" for t in thresholds)
        meaning = c.get("note", "") if has_levels and "No flood levels" not in c.get("note", "") else ""
        linked = "Yes" if has_levels and meaning else "Partly" if has_levels else "No"
        linked_text = {
            "Yes": "**Yes**: flood levels at the creek gauge (what they mean is below)",
            "Partly": "**Partly**: flood levels are set in OneRain, but what they mean isn't recorded",
            "No": "**No**: alert levels only (rain and rising fast). No creek height here is tied to flooding yet",
        }[linked] + ("; rain triggers too" if has_triggers else "")
        L = [f"# {c['name']}", "",
             "*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit "
             "this page; edit the tables and rerun the script.*", "",
             "## At a glance", "", "| | |", "|---|---|",
             f"| Creek id | `{cid}` |",
             f"| On the site | {'Public' if public else 'Staff preview only (`preview_only = yes`)'} |",
             f"| Cities and communities | {esc(cf.get('cities', '')) or '**To add**'}"
             + (f" *({esc(cf['status'])})*" if cf.get("status") else "") + " |",
             f"| Drains to | {esc(cf.get('drains_to', '')) or '**To add**'} |",
             f"| Description | {esc(cf.get('description', '') or c.get('intro', ''))} |",
             f"| Linked to flooding | {linked_text} |",
             f"| Tide station | " + (f"NOAA {c['tide_station']} {esc(tide.get('name', ''))} (MHHW {tide.get('mhhw_navd88_ft', '?')} ft NAVD88)"
                                       if c.get("tide_station") else "None set for this creek in FEWS (coastal creek)"
                                       + (f"; the OneRain dashboard uses {esc(dash_tide['onerain_site'])}" if dash_tide else "")
                                       + (f", which FEWS shows on {esc(tides[dash_tide['onerain_number']]['used_for'])}"
                                          if dash_tide and dash_tide["onerain_number"] in tides else "")) + " |",
             f"| Rain totals shown | {', '.join(dur(m) for m in c.get('rain_windows_min', '').split() if m.isdigit())} |",
             "",
             "**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the "
             "channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; "
             "they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).",
             ""]

        # ---- stage gauges
        L += ["## Creek level gauges", ""]
        for g in stages:
            usgs = g.get("source", "").lower() == "usgs"
            num = g["usgs_site"] if usgs else g["onerain_number"]
            nm, lat, lon = COORDS.get(num.upper(), (g.get("site_name") or g["label"], None, None))
            link = USGS_PAGE.format(num) if usgs else (ONERAIN_SENSOR.format(**g) if g.get("site_id") else "")
            gf = gfacts.get(g["gauge"], {})
            rise = g.get("rise_ft", "")
            L += [f"### {esc(g.get('site_name') or nm)}", "", "| | |", "|---|---|",
                  f"| Gauge key | `{g['gauge']}` |",
                  f"| Source and ID | {'USGS' if usgs else 'OneRain'} {num}" + (f" ([page]({link}))" if link else "") + " |",
                  f"| Location | {f'{lat:.5f}, {lon:.5f}' if lat is not None else '**To add**'} |",
                  f"| Reports | {esc(gf.get('reporting', '')) or g.get('reports', '')} |",
                  f"| Record | {esc(gf.get('record_start', '')) or '**To add**'} |",
                  f"| Tidal | {'Yes' if g.get('tidal', '').lower() == 'yes' else 'No' if g.get('tidal', '').lower() == 'no' else 'To confirm'}"
                  + (f" ({esc(gf['tide_check'])})" if gf.get("tide_check") else "") + " |",
                  f"| Rising fast | " + ("Off at this gauge" if rise.lower() == "off" else
                                        f"{rise or default_rise} ft in {settings.get('RISE_MINUTES', '60')} min"
                                        + ("" if rise else " (default; not calibrated)")) + " |"]
            if gf.get("history_and_issues"):
                L.append(f"| History and known issues | {esc(gf['history_and_issues'])} |")
            if g.get("note"):
                L.append(f"| Note shown on the site | {esc(g['note'])} |")
            L.append("")

            # flood levels
            th = sorted([t for t in thresholds if t["gauge"] == g["gauge"] and t["type"] == "stage"],
                        key=lambda t: float(t["value"]))
            if th:
                L += ["**Flood levels** (gauge height, ft; gauge's own zero, not NAVD88)", "",
                      "| Level | Name | Stage (ft) | Source | Notes |", "|---|---|---|---|---|"]
                L += [f"| {t['level']} | {esc(t['name'])} | {t['value']} | {esc(t['source'])} | {esc(t.get('notes', ''))} |" for t in th]
                L += ["", f"Meaning: {esc(meaning)}" if meaning else "Meaning: **to document**."]
                if "channel capacity" in meaning:
                    L += ["By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning "
                          "means flooding is likely."]
                L += [
                      "Basis and sign-off status: [THRESHOLDS_BASIS.md §1](../THRESHOLDS_BASIS.md).", ""]
            else:
                L += ["**Flood levels:** none. No creek height at this gauge is tied to flooding yet, so the creek's "
                      "status comes from alert levels only: rain and rising fast "
                      "([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).", ""]

            # rising fast results
            res = [r for r in results if r["gauge"] == g["gauge"]]
            if res:
                y = float(res[0]["years"])
                lvl = res[0]["big_storm_level_ft"]
                L += [f"**Rising fast (alert level), tested on {y:.1f} years of history.** "
                      + (f"Tested against the gauge's lowest flood level, {th[0]['name']} at {lvl} ft, so \"warned\" "
                         "means an alert came before the creek reached that level." if th else
                         f"Tested against {lvl} ft, the creek's typical yearly high (the median yearly peak, about a "
                         "2-year event). **This is not a flood level:** \"warned\" means an alert came before a typical "
                         "yearly high, not before flooding."), "",
                      "| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |", "|---|---|---|---|"]
                for r in res:
                    mark = " ◀ current" if r["chosen"] == "True" else ""
                    py = f"{int(r['episodes']) / y:.1f}" if y >= 1 else f"{r['episodes']} total"
                    L.append(f"| {r['rule_ft']}{mark} | {py} | {r['warned']} of {r['crossings']} | {lead(r['lead_med'])} |")
                L += ["", "Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).", ""]
            else:
                L += ["**Rising fast:** not yet tested against this gauge's history.", ""]

        # ---- rain
        L += ["## Rain gauges", ""]
        if not rains:
            L += ["None.", ""]
        else:
            L += ["| Gauge | OneRain ID | Location | Where | Role |", "|---|---|---|---|---|"]
            for g in rains:
                nm, lat, lon = COORDS.get(g["onerain_number"].upper(), (g["label"], None, None))
                role = "Supporting (counts toward the rain level only)" if g.get("role") == "supporting" else "Primary (shown on the pages)"
                L.append(f"| {esc(g['label'])} (`{g['gauge']}`) | {g['onerain_number']} | "
                         f"{f'{lat:.5f}, {lon:.5f}' if lat is not None else '**To add**'} | {esc(g.get('where', ''))} | {role} |")
            L += ["", "**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = "
                  "2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, "
                  "not whether the creek floods.", "",
                  "| Gauge | Level | " + " | ".join(dur(m) for m in KEY_MINUTES) + " |", "|---|---|" + "---|" * len(KEY_MINUTES)]
            for g in rains:
                fr = freq.get(g["onerain_number"].upper(), [])
                for lvl, nm in (("1", "Heavy (1-yr)"), ("2", "Very heavy (2-yr)"), ("3", "Intense (5-yr)")):
                    vals = [next((r["value_in"] for r in fr if r["level"] == lvl and r["minutes"] == str(m)), "–") for m in KEY_MINUTES]
                    L.append(f"| {esc(g['label'])} | {nm} | " + " | ".join(vals) + " |")
            src = next((r["source"] for g in rains for r in freq.get(g["onerain_number"].upper(), [])), "")
            L += ["", f"Source: {esc(src) or 'rain_frequency.csv'}. Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).", ""]
            trig = [t for t in thresholds if t["creek"] == cid and t["type"] == "rain"]
            if trig:
                L += ["**Rain triggers** (flood levels for rain: each one sets the creek to the status shown)", "", "| Gauge | Window | Rain (in) | Tide | Shows | Source |", "|---|---|---|---|---|---|"]
                L += [f"| `{t['gauge']}` | {dur(t['minutes'])} | {t['value']} | "
                      f"{('≥ ' + t['tide_at_least_navd88'] + ' ft NAVD88') if t.get('tide_at_least_navd88') else '–'} | "
                      f"{esc(t['name'])} | {esc(t['source'])} |" for t in trig]
                L += ["", "Basis: [THRESHOLDS_BASIS.md §2](../THRESHOLDS_BASIS.md).", ""]

        # ---- OneRain's own thresholds, for reference
        L += ["## Current OneRain dashboard thresholds", ""]
        if not cdash:
            L += ["None recorded yet (`onerain_dashboard_thresholds.csv`).", ""]
        else:
            L += [f"As set in OneRain on {cdash[0]['captured_on']}; source: {esc(cdash[0]['source'])}. **For reference only:** FEWS "
                  "doesn't use these; its own levels are above. Dashboard colors are what OneRain's dashboard shows; gauge "
                  "alarms are thresholds set on the gauge itself.", "",
                  "| Type | Gauge | Window | Color | Range | Name | Compared with NOAA Atlas 14 (in) |", "|---|---|---|---|---|---|---|"]
            for d in cdash:
                gname = d["onerain_site"] or "**to confirm**"
                if d["onerain_number"] and d["onerain_number"] not in gname:
                    gname += f" ({d['onerain_number']})"
                rng = (f"≥ {d['from_value']}" if d["to_value"] in ("", "999") else f"{d['from_value']} – {d['to_value']}") + f" {d['units']}"
                cmpx = d["atlas14_comparison"].replace("NOAA Atlas 14 at ", "")
                L.append(f"| {d['kind'].replace('dashboard ', 'Dashboard ').replace('gauge alarm threshold', 'Gauge alarm')} | {esc(gname)} | "
                         f"{dur(d['window_min']) if d['window_min'] else '–'} | {d['color'].capitalize()} | {esc(rng)} | "
                         f"{esc(d['threshold_name'])} | {esc(cmpx) or '–'} |")
            notes = [d["notes"] for d in cdash if d["notes"]]
            if notes:
                L += [""] + [f"- {esc(n)}" for n in notes]
            L.append("")

        # ---- open items
        opens = [f"OneRain thresholds: {esc(d['to_confirm'])}" for d in cdash if d["to_confirm"]]
        for g in cg:
            if "To check:" in g.get("note", ""):
                opens.append(f"`{g['gauge']}`: " + esc(g["note"].split("To check:", 1)[1].strip()))
            if g["type"] == "stage" and g["gauge"] not in gfacts:
                opens.append(f"`{g['gauge']}`: add record, reporting and history to gauge_facts.csv")
        if not cf:
            opens.append("Add this creek to creek_facts.csv (cities, outlet, description)")
        elif cf.get("status", "").startswith("draft"):
            opens.append(f"Confirm cities and outlet in creek_facts.csv ({esc(cf['status'])})")
        if has_levels and not meaning:
            opens.append("Document what the flood levels mean (THRESHOLDS_BASIS.md §1)")
        if not has_levels:
            opens.append("Link to flooding: find the creek height at each gauge where the creek leaves its banks or "
                         "floods a road (survey, hydraulic study, or a past flood with gauge readings), then add it to "
                         "thresholds.csv (THRESHOLDS_BASIS.md, Terms)")
        L += ["## Open items", ""] + ([f"- {o}" for o in opens] or ["None recorded."]) + [""]

        with open(os.path.join(OUT, f"{cid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(L))
        index.append((c, cf, stages, rains, public, linked))

    I = ["# Creek fact sheets", "",
         "One page per creek, generated from the lookup tables by `scripts/build_creek_factsheets.py`. To change a "
         "fact sheet, edit the tables (`creeks.csv`, `creek_gauges.csv`, `thresholds.csv`, `rain_frequency.csv`, "
         "`creek_facts.csv`, `gauge_facts.csv`, `onerain_dashboard_thresholds.csv`) and rerun the script.", "",
         "**Linked to flooding:** Yes = flood levels at the creek gauge with a recorded meaning; Partly = flood levels "
         "whose meaning isn't recorded; No = alert levels only (rain and rising fast). See "
         "[THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).", "",
         "| Creek | On the site | Cities and communities | Creek gauges | Rain gauges | Linked to flooding |", "|---|---|---|---|---|---|"]
    for c, cf, stages, rains, public, linked in index:
        I.append(f"| [{c['name']}]({c['creek']}.md) | {'Public' if public else 'Preview'} | {esc(cf.get('cities', ''))} | "
                 f"{len(stages)} | {len(rains)} | {linked} |")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(I) + "\n")
    print(f"wrote {len(index)} fact sheets to {OUT}")


if __name__ == "__main__":
    main()
