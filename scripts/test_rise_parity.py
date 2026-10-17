"""
The home page (index.html: utcSeries + riseCheck) and the data job (creek_signals.py: utc_series + rise_check) must
give the same "rapidly rising" answer. Random gauge records, including the repeated hour when daylight saving ends,
readings without a UTC time, gaps, spikes and per-gauge thresholds. Needs Node.js; skipped without it.

    python scripts/test_rise_parity.py
"""
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creek_signals import SETTINGS, rise_check, utc_series

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PT, UTC = ZoneInfo("America/Los_Angeles"), dt.timezone.utc
S = {k: v[0] for k, v in SETTINGS.items()}
N = 6000

if not shutil.which("node"):
    print("rise parity: skipped (Node.js not installed)")
    sys.exit(0)

html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
js = "\n".join(re.search(pat, html).group(0) for pat in (
    r"function parseLocal\(s\)[^\n]*\n",
    r"var HOLD_TOLERANCE_FT[\s\S]*?\nfunction riseCheck[\s\S]*?\n}\n"))

def run(S):
    random.seed(11)
    cases = []
    for n in range(N):
        g = {"reports": random.choice(["interval", "on change"]), "tidal": False}
        x = random.random()
        if x < 0.2:
            g["rise_ft"] = random.choice([0.25, 1.0])
        elif x < 0.25:
            g["rise_off"] = True
        # around the end of daylight saving half the time
        base = dt.datetime(2026, 11, 1, 9, 0, tzinfo=UTC) if n % 2 else dt.datetime(2026, 1, 5, 20, 0, tzinfo=UTC)
        u = base - dt.timedelta(minutes=random.choice([random.randint(120, 600), random.randint(800, 4000)]))
        end = base + dt.timedelta(minutes=random.randint(-60, 120))
        v, pts = random.uniform(0, 3), []
        while u < end:
            lab = u.astimezone(PT).strftime("%Y-%m-%d %H:%M")
            pts.append([lab, round(v, 2)] + ([u.strftime("%Y-%m-%dT%H:%MZ")] if random.random() > 0.05 else []))
            u += dt.timedelta(minutes=random.choice([1, 5, 15, 15, 15, 30, 60, 200, 800, 1500]) if u < end - dt.timedelta(minutes=90)
                              else random.choice([1, 5, 15, 30]))
            v = max(0, v + random.choice([0, 0, 0.02, -0.02, -0.03, -0.08, 0.1, 0.25, -0.3, 0.6, 0.6, 2.5]))
        latest = None
        if random.random() < 0.3:
            latest = [(u.astimezone(PT)).strftime("%Y-%m-%d %H:%M"), round(v + 0.3, 2)]
            if random.random() < 0.5:   # 'latest' with its UTC time (Oct 17, 2026), half the time
                latest.append(u.strftime("%Y-%m-%dT%H:%MZ"))
        now = end + dt.timedelta(minutes=random.randint(0, 100))
        pu, is_utc = utc_series(pts, latest)
        now_u = now.astimezone(UTC).replace(tzinfo=None) if is_utc else now.astimezone(PT).replace(tzinfo=None)
        r = rise_check([(a, b) for a, b, _ in pu], g, now_u, S)
        py = None if r is None else [r["rise_ft"], pu[r["i"]][2].strftime("%Y-%m-%d %H:%M"), r["held"], r["threshold_ft"]]
        cases.append({"g": g, "sensor": {"points": pts, "latest": latest},
                      "now_utc": now.timestamp() * 1000, "now_local": now.astimezone(PT).strftime("%Y-%m-%d %H:%M"), "py": py})

    # targeted: a fast rise, then the level dips slightly (inside or beyond the 0.05 ft "hasn't dropped" allowance)
    for n in range(400):
        g = {"reports": random.choice(["interval", "on change"]), "tidal": False}
        base = dt.datetime(2026, 1, 5, 20, 0, tzinfo=UTC) + dt.timedelta(minutes=random.randint(0, 600))
        pts, v = [], 1.0
        for k in range(-12, 7):
            u = base + dt.timedelta(minutes=15 * k)
            v = 1.0 if k < 0 else (v + 0.2 if k < 5 else v - random.choice([0.01, 0.03, 0.05, 0.06, 0.1]))
            pts.append([u.astimezone(PT).strftime("%Y-%m-%d %H:%M"), round(v, 2), u.strftime("%Y-%m-%dT%H:%MZ")])
        now = base + dt.timedelta(minutes=15 * 6 + random.randint(0, 10))
        pu, is_utc = utc_series(pts, None)
        r = rise_check([(a, b) for a, b, _ in pu], g, now.astimezone(UTC).replace(tzinfo=None), S)
        py = None if r is None else [r["rise_ft"], pu[r["i"]][2].strftime("%Y-%m-%d %H:%M"), r["held"], r["threshold_ft"]]
        cases.append({"g": g, "sensor": {"points": pts, "latest": None}, "now_utc": now.timestamp() * 1000,
                      "now_local": now.astimezone(PT).strftime("%Y-%m-%d %H:%M"), "py": py})

    node = js + """
    var RISE_FT=%s, RISE_MINUTES=%s, RISE_FRESH_MIN=%s, RISE_REF_LATE_MIN=%s, RISE_CONFIRM_MIN=%s, RISE_HOLD_MIN=%s,
        GAUGE_QUIET_HOURS=%s, RISE_CONFIRM_FRACTION=%s;
    function lab(ms) { return new Date(ms).toISOString().slice(0, 16).replace("T", " "); }
    var cases = JSON.parse(require("fs").readFileSync(0, "utf8")), bad = 0, on = 0;
    cases.forEach(function (c, n) {
      var us = utcSeries(c.sensor), r = riseCheck(us.p, c.g, us.utc ? c.now_utc : parseLocal(c.now_local));
      var a = r ? [Math.round(r.rise * 100) / 100, lab(us.p[r.i].lt), r.held, r.th] : null;
      if (c.py) on++;
      if (JSON.stringify(a) !== JSON.stringify(c.py) && bad++ < 5) console.log("MISMATCH " + n + " js=" + JSON.stringify(a) + " py=" + JSON.stringify(c.py));
    });
    console.log(JSON.stringify({ cases: cases.length, rising: on, mismatches: bad }));
    """ % (S["RISE_FT"], S["RISE_MINUTES"], S["RISE_FRESH_MIN"], S["RISE_REF_LATE_MIN"], S["RISE_CONFIRM_MIN"],
           S["RISE_HOLD_MIN"], S["GAUGE_QUIET_HOURS"], S["RISE_CONFIRM_FRACTION"])
    out = subprocess.run(["node", "-e", node], input=json.dumps(cases), capture_output=True, text=True)
    lines = out.stdout.strip().splitlines()
    assert out.returncode == 0 and lines, out.stderr[-800:]
    res = json.loads(lines[-1])
    assert res["mismatches"] == 0, "\n".join(lines)
    assert res["rising"] > N // 40, f"too few rising cases to be a useful test: {res}"
    return res


VARIANTS = [("settings as shipped", {}), ("RISE_CONFIRM_FRACTION 1", {"RISE_CONFIRM_FRACTION": 1.0}),
            ("RISE_CONFIRM_FRACTION 0", {"RISE_CONFIRM_FRACTION": 0.0}), ("confirmation off", {"RISE_CONFIRM_MIN": 0})]
total = 0
for name, change in VARIANTS:
    res = run(dict(S, **change))
    total += res["cases"]
    print(f"  {name}: {res['cases']} cases ({res['rising']} rising fast), agree")
print(f"rise parity: {total} cases in {len(VARIANTS)} setting variants, page and data job agree")
