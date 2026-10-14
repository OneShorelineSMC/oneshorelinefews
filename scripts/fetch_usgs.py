"""
Pull USGS instantaneous (15-minute) data for the FEWS USGS sites and save one CSV
per site and parameter.

Runs in GitHub Actions (see .github/workflows/usgs_history.yml) or anywhere with Python 3.8+.
No extra packages needed.

Usage:
    python scripts/fetch_usgs.py                         # default: Oct 1, 2020 to now
    python scripts/fetch_usgs.py --start 2022-10-01 --end 2023-04-01
    python scripts/fetch_usgs.py --sites 11164500 11162500

Output:
    out/usgs/<site>_<parameter>.csv   columns: datetime_utc, value, unit, approval, qualifiers
    out/usgs/_summary.csv             one row per site/parameter: rows, first, last, source

Sources, tried in order for each water year:
    1. USGS Water Data API (OGC "continuous" collection), api.waterdata.usgs.gov
    2. Legacy USGS WaterServices "iv" service, waterservices.usgs.gov (expected to be
       retired late 2026 / early 2027)
Set the environment variable USGS_API_KEY to use a free API key with source 1
(higher rate limits); it works without one.
"""

import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SITES = {
    "11164500":  "San Francisquito Creek at Stanford",
    "11162500":  "Pescadero Creek near Pescadero",
    "11162570":  "San Gregorio Creek at San Gregorio",
    "11162619":  "Pilarcitos Creek above Stone Dam",
    "11162620":  "Pilarcitos Creek below Stone Dam",
    "11162630":  "Pilarcitos Creek at Half Moon Bay",
    "111626182": "Pilarcitos Creek below Pilarcitos Lake Spillway",
    "11162753":  "San Mateo Creek below Crystal Springs Reservoir",
    "11162750":  "Lower Crystal Springs Reservoir (level)",
}

# Parameters to keep. Anything else the site reports is ignored.
PARAMS = {
    "00065": "gage_height_ft",
    "00060": "discharge_cfs",
    "00045": "precip_in",
    "00062": "reservoir_elev_ft",
    "62614": "lake_elev_ngvd29_ft",
    "62615": "lake_elev_navd88_ft",
}

OUT = os.path.join("out", "usgs")
UA = {"User-Agent": "OneShoreline-FEWS-data-pull (GitHub Actions)"}
OGC = "https://api.waterdata.usgs.gov/ogcapi/v0/collections/continuous/items"
LEGACY = "https://waterservices.usgs.gov/nwis/iv/"


def get(url, headers=None, tries=4):
    h = dict(UA)
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None                      # no data for this query
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(10 * (i + 1))         # rate-limited or busy: back off
                continue
            raise
        except urllib.error.URLError:
            if i < tries - 1:
                time.sleep(10 * (i + 1))
                continue
            raise


def water_years(start, end):
    """Split [start, end) into chunks at Oct 1 so each request stays a sensible size."""
    cur = start
    while cur < end:
        nxt = dt.datetime(cur.year + (1 if cur.month >= 10 else 0), 10, 1, tzinfo=dt.timezone.utc)
        yield cur, min(nxt, end)
        cur = min(nxt, end)


def iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- Source 1: USGS Water Data API (OGC) ----------
def pull_ogc(site, t0, t1):
    """Return {param: [(utc_iso, value, unit, approval, qualifiers), ...]} or None if unusable."""
    headers = {}
    if os.environ.get("USGS_API_KEY"):
        headers["X-Api-Key"] = os.environ["USGS_API_KEY"]
    q = {"f": "json", "monitoring_location_id": "USGS-" + site,
         "time": iso(t0) + "/" + iso(t1), "limit": "10000"}
    url = OGC + "?" + urllib.parse.urlencode(q)
    out = {}
    pages = 0
    while url:
        body = get(url, headers)
        if body is None:
            return out
        doc = json.loads(body)
        if "features" not in doc:
            return None
        for f in doc["features"]:
            p = f.get("properties", {})
            code = p.get("parameter_code")
            if code not in PARAMS or p.get("value") in (None, ""):
                continue
            qual = p.get("qualifier") or ""
            if isinstance(qual, list):
                qual = " ".join(str(x) for x in qual)
            out.setdefault(code, []).append((
                normalize_iso(p.get("time")), str(p.get("value")), p.get("unit_of_measure") or "",
                p.get("approval_status") or "", qual))
        url = next((l["href"] for l in doc.get("links", []) if l.get("rel") == "next"), None)
        pages += 1
        if pages > 500:
            raise RuntimeError("too many pages; narrow the date range")
    return out


def normalize_iso(s):
    t = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return iso(t.astimezone(dt.timezone.utc))


# ---------- Source 2: legacy WaterServices iv (RDB text) ----------
TZ = {"PST": -8, "PDT": -7, "UTC": 0, "GMT": 0}


def pull_legacy(site, t0, t1):
    q = {"format": "rdb", "sites": site, "parameterCd": ",".join(PARAMS),
         "startDT": iso(t0), "endDT": iso(t1), "siteStatus": "all"}
    body = get(LEGACY + "?" + urllib.parse.urlencode(q))
    return parse_rdb(body) if body else {}


def parse_rdb(body):
    lines = [l for l in body.splitlines() if l and not l.startswith("#")]
    if len(lines) < 2:
        return {}
    head = lines[0].split("\t")
    out = {}
    cols = []
    for i, name in enumerate(head):              # value columns look like "69928_00065"
        parts = name.split("_")
        if len(parts) == 2 and parts[1] in PARAMS and parts[0].isdigit():
            cq = head.index(name + "_cd") if (name + "_cd") in head else None
            cols.append((parts[1], i, cq))
    idt, itz = head.index("datetime"), head.index("tz_cd")
    for line in lines[2:]:                       # lines[1] is the RDB format row
        row = line.split("\t")
        if len(row) < len(head):
            continue
        off = TZ.get(row[itz])
        if off is None:
            continue
        local = dt.datetime.strptime(row[idt], "%Y-%m-%d %H:%M")
        utc = iso((local - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc))
        for code, iv, iq in cols:
            v = row[iv].strip()
            if v == "" or not _num(v):
                continue
            flags = row[iq] if iq is not None else ""
            approval = "Approved" if "A" in flags.split() else "Provisional"
            out.setdefault(code, []).append((utc, v, "", approval, flags))
    return out


def _num(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-10-01", help="YYYY-MM-DD (UTC)")
    ap.add_argument("--end", default=None, help="YYYY-MM-DD (UTC); default now")
    ap.add_argument("--sites", nargs="*", default=list(SITES))
    a = ap.parse_args()

    start = dt.datetime.fromisoformat(a.start).replace(tzinfo=dt.timezone.utc)
    end = (dt.datetime.fromisoformat(a.end).replace(tzinfo=dt.timezone.utc)
           if a.end else dt.datetime.now(dt.timezone.utc))
    os.makedirs(OUT, exist_ok=True)
    summary, problems = [], []

    for site in a.sites:
        name = SITES.get(site, "")
        data, sources = {}, set()
        for t0, t1 in water_years(start, end):
            chunk, src = None, None
            try:
                chunk = pull_ogc(site, t0, t1)
                src = "waterdata-api"
            except Exception as e:
                problems.append(f"{site} {t0:%Y-%m}: Water Data API failed ({e}); trying legacy")
            if not chunk:
                try:
                    chunk = pull_legacy(site, t0, t1)
                    src = "waterservices-iv"
                except Exception as e:
                    problems.append(f"{site} {t0:%Y-%m}: legacy service failed ({e})")
                    chunk = {}
            for code, rows in (chunk or {}).items():
                data.setdefault(code, []).extend(rows)
                sources.add(src)
            time.sleep(1)                         # be polite

        if not data:
            print(f"--   {site:10s} {name}: no data in this period")
            summary.append([site, name, "", "", 0, "", "", ""])
            continue

        for code, rows in sorted(data.items()):
            rows = sorted(set(rows))              # de-duplicate across chunk edges
            path = os.path.join(OUT, f"{site}_{code}.csv")
            with open(path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["datetime_utc", "value", "unit", "approval", "qualifiers"])
                w.writerows(rows)
            summary.append([site, name, code, PARAMS[code], len(rows), rows[0][0], rows[-1][0],
                            "+".join(sorted(sources))])
            print(f"ok   {site:10s} {PARAMS[code]:20s} {len(rows):8d} rows  {rows[0][0]} → {rows[-1][0]}")

    tag = "" if sorted(a.sites) == sorted(SITES) else "_" + "_".join(a.sites)
    with open(os.path.join(OUT, "_summary" + tag + ".csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["site", "name", "parameter", "parameter_name", "rows", "first_utc", "last_utc", "source"])
        w.writerows(summary)

    if problems:
        print("\nNotes:")
        for p in problems:
            print("  " + p)
    if not any(r[4] for r in summary):
        sys.exit("No data was downloaded from any site — check the log above.")


if __name__ == "__main__":
    main()
