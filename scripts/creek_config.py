"""
Reads the creek settings that staff check and update, all in the lookups/ folder (see lookups/README.md):

  lookups/creeks.csv         the creeks: names, intro and note text, tide station, rain windows
  lookups/creek_gauges.csv   each creek's stage and rain gauges and their OneRain sensor link details
  lookups/thresholds.csv     flood thresholds for every stage gauge, and rain triggers
  lookups/tide_stations.csv  NOAA tide stations: MHHW and the MLLW-to-NAVD88 difference

Nothing in this file needs editing for a normal change. The pages read everything from the published data
file, so changes show up everywhere on the next data run (about 5 minutes after you commit).

If a file has a mistake, the data job keeps using the last good settings (from the previous data file),
keeps publishing creek readings, and marks the run as failed in the Actions tab with the row and problem.
"""

import csv
import os
import re

LEVEL_COLORS = {1: "#e6c200", 2: "#e07b00", 3: "#c62828", 4: "#9c27b0"}
LEVEL_NAMES = {1: "Flood Monitoring", 2: "Flood Watch", 3: "Flood Warning", 4: "Above Flood Warning"}

_HERE = os.path.dirname(os.path.abspath(__file__))
LOOKUPS = os.path.join(_HERE, "..", "lookups")
CREEKS_CSV = os.path.join(LOOKUPS, "creeks.csv")
GAUGES_CSV = os.path.join(LOOKUPS, "creek_gauges.csv")
THRESHOLDS_CSV = os.path.join(LOOKUPS, "thresholds.csv")
TIDE_CSV = os.path.join(LOOKUPS, "tide_stations.csv")

_SLUG = re.compile(r"^[a-z0-9_]+$")
_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _rows(path, name):
    """Rows of a CSV as dicts with trimmed, lower-case column names; (rows, error)."""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        return [], f"can't read {name}: {e}"
    out = []
    for n, r in enumerate(rows, start=2):   # row 1 is the header
        r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
        if any(r.values()):
            r["_where"] = f"{name} row {n}"
            out.append(r)
    return out, None


def _rise(r):
    """creek_gauges.csv rise_ft for a stage gauge -> ({"rise_ft": x} / {"rise_off": True} / {}, error or None).
    Blank = the RISE_FT default in settings.csv; a number from 0.05 to 10 ft; 'off' = rising fast not used."""
    v = r.get("rise_ft", "").strip().lower()
    if not v:
        return {}, None
    if v == "off":
        return {"rise_off": True}, None
    try:
        x = float(v)
        assert 0.05 <= x <= 10
    except (ValueError, AssertionError):
        return {}, "rise_ft must be blank, 'off', or a number of feet from 0.05 to 10"
    return {"rise_ft": x}, None


def _window(minutes):
    return f"{minutes}-minute" if minutes < 60 else f"{minutes // 60}-hour"


def load_tide_stations(path=TIDE_CSV):
    """{station id: {"name", "mhhw", "mllw_to_navd88"}}, errors."""
    rows, err = _rows(path, "tide_stations.csv")
    if err:
        return {}, [err]
    out, errors = {}, []
    for r in rows:
        w, sid = r["_where"], r.get("station", "")
        if not re.fullmatch(r"\d{7}", sid):
            errors.append(f"{w}: station must be a 7-digit NOAA station number"); continue
        try:
            mhhw = float(r.get("mhhw_navd88_ft", ""))
            assert -5 < mhhw < 20
        except (ValueError, AssertionError):
            errors.append(f"{w}: mhhw_navd88_ft must be a number in ft NAVD88"); continue
        off = None
        if r.get("mllw_to_navd88_ft"):
            try:
                off = float(r["mllw_to_navd88_ft"])
                assert -10 < off < 10
            except (ValueError, AssertionError):
                errors.append(f"{w}: mllw_to_navd88_ft must be a number (ft) or blank"); continue
        out[sid] = {"name": r.get("name") or sid, "mhhw": mhhw, "mllw_to_navd88": off}
    return out, errors


def load_creeks(tides):
    """The creek list from creeks.csv and creek_gauges.csv; (creeks, errors)."""
    crow, err = _rows(CREEKS_CSV, "creeks.csv")
    grow, err2 = _rows(GAUGES_CSV, "creek_gauges.csv")
    errors = [e for e in (err, err2) if e]
    if errors:
        return [], errors
    creeks, order = {}, {}
    for r in crow:
        w, cid = r["_where"], r.get("creek", "")
        if not _SLUG.match(cid):
            errors.append(f"{w}: creek must be a short code of lower-case letters, digits or _ (e.g. sanbruno)"); continue
        if cid in creeks:
            errors.append(f"{w}: creek '{cid}' is listed twice"); continue
        if not r.get("name") or not r.get("short_name"):
            errors.append(f"{w}: name and short_name are required"); continue
        pv = r.get("preview_only", "").lower()
        if pv not in ("", "yes", "no"):
            errors.append(f"{w}: preview_only must be yes, no or blank"); continue
        # preview_only = yes: staff preview only (creek status layer); kept out of the public pages
        if r.get("tide_station") not in tides and not (pv == "yes" and not r.get("tide_station")):
            errors.append(f"{w}: tide_station '{r.get('tide_station')}' is not in tide_stations.csv"); continue
        try:
            wins = sorted({int(x) for x in re.split(r"[\s,;]+", r.get("rain_windows_min", "")) if x})
            assert wins and all(0 < x <= 10080 for x in wins)
        except (ValueError, AssertionError):
            errors.append(f"{w}: rain_windows_min must be minutes separated by spaces, e.g. 15 30 60 1440"); continue
        try:
            order[cid] = float(r.get("order") or 99)
        except ValueError:
            errors.append(f"{w}: order must be a number"); continue
        c = {"id": cid, "name": r["name"], "short": r["short_name"], "rain_windows": wins,
             "intro": r.get("intro", ""), "tide": r.get("tide_station") or None, "note": r.get("note", ""), "stages": [], "rain": [],
             "rain_support": [], "preview_only": pv == "yes"}
        rg, rm, rl = r.get("running_rain_gauge", ""), r.get("running_rain_min", ""), r.get("running_rain_label", "")
        if rg or rm:
            try:
                c["rain_running"] = {"gauge": rg, "minutes": int(rm), "label": rl or f"{_window(int(rm))} rain (in)"}
            except ValueError:
                errors.append(f"{w}: running_rain_min must be whole minutes, e.g. 240"); continue
        creeks[cid] = c
    keys = set()
    for r in grow:
        w, cid, key, typ = r["_where"], r.get("creek", ""), r.get("gauge", ""), r.get("type", "").lower()
        if cid not in creeks:
            errors.append(f"{w}: creek '{cid}' is not in creeks.csv"); continue
        if not _SLUG.match(key) or key in keys:
            errors.append(f"{w}: gauge must be a unique short code (lower-case letters, digits, _)"); continue
        if typ not in ("stage", "rain"):
            errors.append(f"{w}: type must be 'stage' or 'rain'"); continue
        src = r.get("source", "").lower() or "onerain"
        if src not in ("onerain", "usgs"):
            errors.append(f"{w}: source must be onerain, usgs or blank"); continue
        if src == "usgs":   # a USGS stream gauge, read from USGS (gage height, ft)
            if typ != "stage" or not re.fullmatch(r"\d{8,15}", r.get("usgs_site", "")) or not r.get("label"):
                errors.append(f"{w}: a USGS gauge needs type stage, a label and usgs_site (the 8-15 digit USGS number)"); continue
            tid = r.get("tidal", "").lower()
            if tid not in ("", "yes", "no"):
                errors.append(f"{w}: tidal must be yes, no or blank"); continue
            rise, err = _rise(r)
            if err:
                errors.append(f"{w}: {err}"); continue
            g = {"key": key, "label": r["label"], "number": "USGS " + r["usgs_site"], "source": "usgs", "usgs_site": r["usgs_site"],
                 "note": r.get("note", ""), "site_name": r.get("site_name") or r["label"], "reports": "interval", "tidal": tid == "yes", **rise}
            creeks[cid]["stages"].append(g)
            keys.add(key)
            continue
        bad = [col for col, ok in (("label", r.get("label")), ("onerain_number", re.fullmatch(r"[A-Za-z0-9]+", r.get("onerain_number", ""))),
                                   ("site_id", re.fullmatch(r"\d+", r.get("site_id", ""))), ("site", _UUID.match(r.get("site", "").lower())),
                                   ("device_id", re.fullmatch(r"\d+", r.get("device_id", ""))), ("device", _UUID.match(r.get("device", "").lower())))
               if not ok]
        if bad:
            errors.append(f"{w}: missing or malformed {', '.join(bad)} (copy them from the sensor's OneRain page address)"); continue
        g = {"key": key, "label": r["label"], "number": r["onerain_number"], "site_id": int(r["site_id"]), "site": r["site"].lower(),
             "device_id": int(r["device_id"]), "device": r["device"].lower(), "note": r.get("note", "")}
        role = r.get("role", "").lower()
        if typ == "stage":
            rep = r.get("reports", "").lower()
            if rep not in ("on change", "interval"):
                errors.append(f"{w}: reports must be 'on change' or 'interval' for a stage gauge"); continue
            tid = r.get("tidal", "").lower()
            if tid not in ("", "yes", "no"):
                errors.append(f"{w}: tidal must be yes, no or blank"); continue
            rise, err = _rise(r)
            if err:
                errors.append(f"{w}: {err}"); continue
            g.update({"site_name": r.get("site_name") or r["label"], "reports": rep, "tidal": tid == "yes", **rise})
            creeks[cid]["stages"].append(g)
        else:
            # role: blank/primary = shown on the pages; supporting = counts toward the creek's rain level only
            # (creek status layer, staff preview), not in the rain tables or graphs
            if role not in ("", "primary", "supporting"):
                errors.append(f"{w}: role must be primary, supporting or blank for a rain gauge"); continue
            if r.get("rise_ft", "").strip():
                errors.append(f"{w}: rise_ft is for stage gauges only; leave it blank for a rain gauge"); continue
            g["where"] = r.get("where", "")
            creeks[cid]["rain_support" if role == "supporting" else "rain"].append(g)
        keys.add(key)
    for c in creeks.values():
        if not c["stages"]:
            errors.append(f"creeks.csv: creek '{c['id']}' has no stage gauge in creek_gauges.csv")
        rr = c.get("rain_running")
        if rr and rr["gauge"] not in [g["key"] for g in c["rain"]]:
            errors.append(f"creeks.csv: running_rain_gauge '{rr['gauge']}' for '{c['id']}' is not one of its rain gauges")
    if errors:
        return [], errors
    return sorted(creeks.values(), key=lambda c: order[c["id"]]), []


def load_thresholds(creeks, tides, path=THRESHOLDS_CSV):
    """Read thresholds.csv into the creeks. Returns a list of problems; if there are any, nothing is applied
    (the data job then keeps the last good thresholds, so a typo can't blank or mis-color the screens)."""
    gauges = {}
    for c in creeks:
        for g in c["stages"]:
            gauges[g["key"]] = (c, "stage", g)
        for g in c["rain"] + c.get("rain_support", []):
            gauges[g["key"]] = (c, "rain", g)
    rows, err = _rows(path, "thresholds.csv")
    if err:
        return [err]
    stage, triggers, errors = {}, {}, []
    for r in rows:
        where = r["_where"]
        c_id, key, typ = r.get("creek", ""), r.get("gauge", ""), r.get("type", "").lower()
        if key not in gauges:
            errors.append(f"{where}: unknown gauge '{key}' (see the gauge column in lookups/creek_gauges.csv)"); continue
        creek, kind, _ = gauges[key]
        if c_id != creek["id"]:
            errors.append(f"{where}: gauge '{key}' belongs to creek '{creek['id']}', not '{c_id}'"); continue
        if typ not in ("stage", "rain") or (typ == "stage") != (kind == "stage"):
            errors.append(f"{where}: type should be '{kind}' for gauge '{key}'"); continue
        try:
            level = int(r.get("level", ""))
            value = float(r.get("value", ""))
            assert level in LEVEL_COLORS and value > 0
        except (ValueError, AssertionError):
            errors.append(f"{where}: level must be 1-4 and value a positive number"); continue
        name = r.get("name") or LEVEL_NAMES[level]
        item = {"value": value, "name": name, "level": level, "color": LEVEL_COLORS[level]}
        if r.get("notes"):
            item["note"] = r["notes"]
        if typ == "stage":
            stage.setdefault(key, []).append(item)
            continue
        try:
            minutes = int(r.get("minutes", ""))
            assert minutes > 0
        except (ValueError, AssertionError):
            errors.append(f"{where}: rain thresholds need 'minutes' (e.g. 30 or 240)"); continue
        tide_txt = r.get("tide_at_least_navd88", "")
        high_tide = bool(tide_txt) or r.get("high_tide", "").lower() in ("yes", "y", "true", "1")
        item.update({"gauge": key, "minutes": minutes, "high_tide": high_tide,
                     "label": _window(minutes) + " rain" + (" + high tide" if high_tide else "")})
        if tide_txt:   # high tide = the creek's NOAA tide station at or above this level, in ft NAVD88
            try:
                item["tide_min"] = float(tide_txt)
            except ValueError:
                errors.append(f"{where}: tide_at_least_navd88 must be a number (ft NAVD88)"); continue
        triggers.setdefault(creek["id"], []).append(item)
    if errors:
        return errors
    for c in creeks:
        for g in c["stages"]:
            g["thresholds"] = sorted(stage.get(g["key"], []), key=lambda x: x["value"])
        c["rain_triggers"] = sorted(triggers.get(c["id"], []), key=lambda x: (x["minutes"], x["value"]))
        run = c.get("rain_running")
        if run and "line" not in run:   # the running-total graph's line: that gauge's threshold for the same window
            match = [x for x in c["rain_triggers"] if x["gauge"] == run["gauge"] and x["minutes"] == run["minutes"]]
            if match:
                run["line"] = min(x["value"] for x in match)
    return []


TIDE_STATIONS, TIDE_ERRORS = load_tide_stations()
if TIDE_ERRORS:
    CREEKS, CONFIG_ERRORS = [], ["creeks not loaded until tide_stations.csv is fixed"]
else:
    CREEKS, CONFIG_ERRORS = load_creeks(TIDE_STATIONS)
THRESHOLD_ERRORS = load_thresholds(CREEKS, TIDE_STATIONS) if CREEKS else []
SETTINGS_ERRORS = TIDE_ERRORS + CONFIG_ERRORS + THRESHOLD_ERRORS   # everything to report in the Actions tab


def map_thresholds():
    """Thresholds for the site map, by site number: {"41102": {"stage": [...]}}."""
    out = {}
    for c in CREEKS:
        for g in c["stages"]:
            if g.get("thresholds"):
                out.setdefault(g["number"], {})["stage"] = g["thresholds"]
    return out
