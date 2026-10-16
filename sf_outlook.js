/* San Francisco tide outlook for the King Tide line, card and calendar (ShorelineKiosk.html, Tides.html).
 *
 * The County's King Tide / Elevated days are NOAA astronomical predictions at San Francisco (9414290), ft MLLW
 * (Elevated = high tide 6.0 ft or more, King Tide = 7.0 ft or more). Those labels never change here. Within the next
 * SF_FORECAST_HOURS (48), NOAA's model forecast at the same gauge (SFBOFS, ofs_water_level, datum MLLW) adds a note:
 *   - the forecast high differs from the predicted high by SF_FORECAST_NOTE_FT (0.25 ft) or more: higher / lower
 *   - the forecast reaches the King Tide height (from the County file, 7.0 ft) on a day that isn't a King Tide day.
 * Same freshness rule as the other model forecasts: downloaded within MODEL_MAX_AGE_HOURS and reaching at least
 * MODEL_MIN_AHEAD_HOURS ahead; otherwise no notes (the County labels show as before).
 * Times: Pacific wall clock as UTC milliseconds, like the pages. All wording: lookups/display_text.csv (sf_fcst_*).
 */
(function () {
  "use strict";
  var LK = window.LOOKUPS, STATION = "9414290", MATCH_MIN = 90;
  var S = { highs: null, ofs: null, tOfs: 0, tHighs: 0 };

  function parseLocal(s) { var a = s.split(/[- :]/).map(Number); return Date.UTC(a[0], a[1] - 1, a[2], a[3], a[4] || 0); }
  function nowLocal() {
    var p = {};
    new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
    return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute);
  }
  function ymd(ms) { return new Date(ms).toISOString().slice(0, 10).replace(/-/g, ""); }
  function iso(ms) { return new Date(ms).toISOString().slice(0, 10); }
  function url(product, begin, end, extra) {
    return "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=" + product + "&station=" + STATION +
      "&begin_date=" + begin + "&end_date=" + end + "&datum=MLLW&time_zone=lst_ldt&units=english&format=json&application=OneShorelineFEWS" + (extra || "");
  }
  function get(u) {
    return fetch(u, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { if (j.error) throw new Error(j.error.message || "error"); return j; });
  }
  function pts(arr, onlyHigh) {
    return (arr || []).filter(function (p) { return !onlyHigh || p.type === "H"; })
      .map(function (p) { return { t: parseLocal(p.t), v: parseFloat(p.v) }; }).filter(function (p) { return !isNaN(p.v); });
  }

  // Predicted high tides (today to 3 days ahead) and the model forecast (yesterday to as far as it goes)
  function load() {
    var now = nowLocal();
    return Promise.all([
      get(url("predictions", ymd(now), ymd(now + 3 * 86400000), "&interval=hilo")).then(function (j) { var h = pts(j.predictions, true); if (h.length) { S.highs = h; S.tHighs = Date.now(); } }),
      get(url("ofs_water_level", ymd(now - 86400000), ymd(now + 3 * 86400000))).then(function (j) { var p = pts(j.data || j.predictions); if (p.length) { S.ofs = p; S.tOfs = Date.now(); } })
    ].map(function (p) { return p.catch(function () {}); }));
  }
  function modelOK(now) {
    return !!(S.ofs && S.ofs.length && Date.now() - S.tOfs < LK.num("MODEL_MAX_AGE_HOURS") * 3600000 &&
      S.ofs[S.ofs.length - 1].t >= now + LK.num("MODEL_MIN_AHEAD_HOURS") * 3600000);
  }

  /* The highest forecast high tide of each day in the look-ahead: {date: {t, pred, fcst, diff}} */
  function byDay(now) {
    now = now || nowLocal();
    var out = {};
    if (!S.highs || !modelOK(now)) return out;
    var end = Math.min(now + LK.num("SF_FORECAST_HOURS") * 3600000, S.ofs[S.ofs.length - 1].t - MATCH_MIN * 60000);
    S.highs.forEach(function (h) {
      if (h.t < now - MATCH_MIN * 60000 || h.t > end) return;
      var best = null;
      S.ofs.forEach(function (o) { if (Math.abs(o.t - h.t) <= MATCH_MIN * 60000 && (!best || o.v > best.v)) best = o; });
      if (!best) return;
      var d = iso(h.t), x = { t: best.t, pred: h.v, fcst: best.v, diff: best.v - h.v };
      if (!out[d] || x.fcst > out[d].fcst) out[d] = x;
    });
    return out;
  }

  /* Notes for one day: [{kind: "higher"|"lower"|"reaches", text}], given the County category and the King Tide height */
  function notes(x, category, kingMin) {
    if (!x) return [];
    var out = [], v = { fcst: x.fcst.toFixed(2), diff: Math.abs(x.diff).toFixed(2), level: kingMin != null ? kingMin.toFixed(1) : "" };
    if (kingMin != null && x.fcst >= kingMin && category !== "KING") out.push({ kind: "reaches", text: LK.text("sf_fcst_reaches", v) });
    else if (x.diff >= LK.num("SF_FORECAST_NOTE_FT")) out.push({ kind: "higher", text: LK.text("sf_fcst_higher", v) });
    else if (-x.diff >= LK.num("SF_FORECAST_NOTE_FT")) out.push({ kind: "lower", text: LK.text("sf_fcst_lower", v) });
    return out;
  }

  /* Every forecast note in the look-ahead, earliest day first: [{date, label, kind, text, category}].
     data = the County file (data/tide_days_lookup_*.json); dayName(iso) = the page's "Sat Dec 12" format. */
  function list(data, dayName, now) {
    now = now || nowLocal();
    var fc = byDay(now), by = {}, today = iso(now), tomorrow = iso(now + 86400000);
    var king = data && data.meta && data.meta.categories && data.meta.categories.KING;
    var kingMin = king && typeof king.min_ft_mllw === "number" ? king.min_ft_mllw : null;
    ((data && data.days) || []).forEach(function (x) { by[x.date] = x.category; });
    return Object.keys(fc).sort().reduce(function (acc, d) {
      notes(fc[d], by[d] || "NONE", kingMin).forEach(function (n) {
        acc.push({ date: d, label: d === today ? "Today" : d === tomorrow ? "Tomorrow" : dayName(d), kind: n.kind, text: n.text, category: by[d] || "NONE", x: fc[d] });
      });
      return acc;
    }, []);
  }

  /* The King Tide line/card with forecast notes. st = the page's King Tide status ({cls, main, sub}) or null.
     - King Tide line showing: the first note in the look-ahead goes after the main words.
     - No King Tide line: shown only when the forecast reaches the King Tide height on a non-King day, with its own chip. */
  function decorate(st, data, dayName, now) {
    var ns = list(data, dayName, now);
    if (st) {
      if (!ns.length) return st;
      var n = ns[0], words = (st.main + " " + (st.sub || "")).toLowerCase();
      var same = (n.label === "Today" && /\btoday\b/.test(words)) || (n.label === "Tomorrow" && /\btomorrow\b/.test(words));   // "King Tide today": no second "Today:"
      return { cls: st.cls, chip: null, main: st.main, sub: (same ? "" : n.label + ": ") + n.text + (st.sub ? " · " + st.sub : ""), notes: ns };
    }
    var r = ns.filter(function (n) { return n.kind === "reaches"; })[0];
    if (!r) return null;
    return { cls: "fc", chip: LK.text("sf_fcst_chip"), main: r.label + ": " + r.text, sub: "", notes: ns };
  }

  window.SF_OUTLOOK = { load: load, byDay: byDay, notes: notes, list: list, decorate: decorate, state: S, station: STATION };
})();
