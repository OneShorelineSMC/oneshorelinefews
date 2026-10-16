/* High tides at Redwood City for the King Tide line (kiosk), the Tides page card and its calendar.
 *
 * Everything comes from NOAA at the Redwood City tide gauge (9414523), ft NAVD88, so nothing needs a yearly update:
 *   - the tide table (predicted high tides) from the start of this month through the next 6 months
 *   - the NOAA projection (NOAA's San Francisco Bay model, ofs_water_level: storms, wind, runoff, ocean conditions such as El Niño), about 2 days ahead
 *
 * Levels (the colors) come from the water height, never from the name "King Tide":
 *   below MHHW (tide_stations.csv)            normal
 *   MHHW up to TIDE_RED_FT_RWC (settings.csv)  level 1 (shown blue, information): higher than an average high tide
 *   TIDE_RED_FT_RWC or more (8.5, provisional) red: high enough to flood low areas near the Bay
 * "King Tide" is only a label (the star): a day whose tide-table high tide reaches KING_TIDE_FT_RWC (settings.csv), the 1-year tide
 * (8.3 ft NAVD88, SF Bay Tidal Datums and Extreme Tides Study, 2016). Any month; mostly Nov-Jan.
 * Times: Pacific wall clock as UTC milliseconds, like the pages. Wording: lookups/display_text.csv (tide_*, king_tide_*).
 */
(function () {
  "use strict";
  var LK = window.LOOKUPS, STATION = "9414523", MATCH_MIN = 90, MONTHS_AHEAD = 6;
  var S = { highs: null, tHighs: 0, ofs: null, tOfs: 0, from: null };

  function parseLocal(s) { var a = s.split(/[- :]/).map(Number); return Date.UTC(a[0], a[1] - 1, a[2], a[3], a[4] || 0); }
  function nowLocal() {
    var p = {};
    new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
    return Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour % 24, +p.minute);
  }
  function iso(ms) { return new Date(ms).toISOString().slice(0, 10); }
  function ymd(ms) { return iso(ms).replace(/-/g, ""); }
  function monthStart(y, m) { return Date.UTC(y, m, 1); }   // m: 0-11 (rolls over the year)
  function url(product, begin, end, extra) {
    return "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=" + product + "&station=" + STATION +
      "&begin_date=" + begin + "&end_date=" + end + "&datum=NAVD&time_zone=lst_ldt&units=english&format=json&application=OneShorelineFEWS" + (extra || "");
  }
  function get(u) {
    return fetch(u, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { if (j.error) throw new Error(j.error.message || "error"); return j; });
  }
  function pts(arr, onlyHigh) {
    return (arr || []).filter(function (p) { return !onlyHigh || p.type === "H"; })
      .map(function (p) { return { t: parseLocal(p.t), v: parseFloat(p.v) }; }).filter(function (p) { return !isNaN(p.v); });
  }

  /* The tide table one month per request (keeps each request small), and the model forecast */
  function loadTable() {
    var n = nowLocal(), d = new Date(n), y = d.getUTCFullYear(), m = d.getUTCMonth(), reqs = [];
    for (var k = 0; k <= MONTHS_AHEAD; k++) {
      var a = monthStart(y, m + k), b = monthStart(y, m + k + 1) - 86400000;
      reqs.push(get(url("predictions", ymd(a), ymd(b), "&interval=hilo")).then(function (j) { return pts(j.predictions, true); }));
    }
    return Promise.all(reqs).then(function (parts) {
      var all = [].concat.apply([], parts).sort(function (p, q) { return p.t - q.t; });
      if (all.length) { S.highs = all; S.tHighs = Date.now(); S.from = monthStart(y, m); }
    }).catch(function () { /* keep the last good copy */ });
  }
  function loadModel() {
    var n = nowLocal();
    return get(url("ofs_water_level", ymd(n - 86400000), ymd(n + 3 * 86400000)))
      .then(function (j) { var p = pts(j.data || j.predictions); if (p.length) { S.ofs = p; S.tOfs = Date.now(); } }).catch(function () {});
  }
  function modelOK(now) {
    return !!(S.ofs && S.ofs.length && Date.now() - S.tOfs < LK.num("MODEL_MAX_AGE_HOURS") * 3600000 &&
      S.ofs[S.ofs.length - 1].t >= now + LK.num("MODEL_MIN_AHEAD_HOURS") * 3600000);
  }

  function mhhw() { return LK.mhhw(STATION); }
  function red() { return LK.num("TIDE_RED_FT_RWC"); }
  function king() { return LK.num("KING_TIDE_FT_RWC"); }
  function level(v) { return v == null ? 0 : v >= red() ? 2 : v > mhhw() ? 1 : 0; }

  /* Each day's highest tide-table high tide: {date: {t, v}} */
  function dayHighs() {
    var out = {};
    (S.highs || []).forEach(function (h) { var d = iso(h.t); if (!out[d] || h.v > out[d].v) out[d] = h; });
    return out;
  }
  /* King Tide days: days whose highest tide-table high tide reaches the 1-year tide (KING_TIDE_FT_RWC). The tide table only,
     so the stars are known months ahead and don't come and go with the NOAA projection. */
  function kingDays() {
    var dh = dayHighs(), k = king(), out = {};
    Object.keys(dh).forEach(function (d) { if (dh[d].v >= k) out[d] = dh[d]; });
    return out;
  }
  /* NOAA projection (next TIDE_EXPECTED_HOURS): the model's peak near each tide-table high tide, highest per day */
  function expected(now) {
    now = now || nowLocal();
    var out = {};
    if (!S.highs || !modelOK(now)) return out;
    var end = Math.min(now + LK.num("TIDE_EXPECTED_HOURS") * 3600000, S.ofs[S.ofs.length - 1].t - MATCH_MIN * 60000);
    S.highs.forEach(function (h) {
      if (h.t < now - MATCH_MIN * 60000 || h.t > end) return;
      var best = null;
      S.ofs.forEach(function (o) { if (Math.abs(o.t - h.t) <= MATCH_MIN * 60000 && (!best || o.v > best.v)) best = o; });
      if (!best) return;
      var d = iso(h.t), x = { t: best.t, v: best.v, table: h.v, diff: best.v - h.v };
      if (!out[d] || x.v > out[d].v) out[d] = x;
    });
    return out;
  }

  function clock(ms) { var d = new Date(ms), h = d.getUTCHours(), mi = d.getUTCMinutes(); return (h % 12 || 12) + ":" + String(mi).padStart(2, "0") + (h < 12 ? " AM" : " PM"); }
  function ft(v) { return v.toFixed(1) + " ft"; }
  function weatherNote(x) {   // "NOAA projects about 0.4 ft higher than the tide table", or "" when the difference is small
    if (!x || Math.abs(x.diff) < LK.num("TIDE_WEATHER_NOTE_FT")) return "";
    return LK.text(x.diff > 0 ? "tide_weather_higher" : "tide_weather_lower", { diff: Math.abs(x.diff).toFixed(1) });
  }

  /* The line (kiosk) / card (Tides page), or null. Looks at today and the next 6 days.
     1. Red first: a day expected (or in the tide table) to reach TIDE_RED_FT_RWC.
     2. Otherwise a King Tide day coming up, with the NOAA projection note when it is within the projection window.
     Ordinary days above MHHW are left to the day cards. dayName(iso) = the page's "Sat Dec 12". */
  function line(dayName, now) {
    now = now || nowLocal();
    var today = iso(now), dh = dayHighs(), kd = kingDays(), ex = expected(now), out = null;
    function label(d) { return d === today ? "Today" : d === iso(now + 86400000) ? "Tomorrow" : dayName(d); }
    for (var n = 0; n < 7 && !out; n++) {
      var d = iso(now + n * 86400000), x = ex[d], h = dh[d], v = x ? x.v : h ? h.v : null;
      if (h && h.t < now - MATCH_MIN * 60000 && !x) continue;   // today's highest tide already passed
      if (level(v) === 2) out = { cls: "red", chip: LK.text("tide_red_chip"), date: d,
        main: label(d) + " " + clock(x ? x.t : h.t) + ": " + (x ? LK.text("tide_expected_ft", { ft: ft(v) }) : LK.text("tide_table_ft", { ft: ft(v) })) + ", " + LK.text("tide_level_red"),
        sub: kd[d] ? LK.text("tide_day_king_short") : "", what: LK.text("tide_red_what") };
    }
    if (out) return out;
    var ks = Object.keys(kd).sort().filter(function (d) { return d >= today && d <= iso(now + 6 * 86400000); });
    if (!ks.length) return null;
    var d = ks[0], k = kd[d], x = ex[d], v = x ? x.v : k.v;
    return { cls: "king", chip: LK.text("tide_king_chip"), date: d,
      main: LK.text("tide_king_line", { day: label(d), time: clock(k.t), ft: ft(k.v) }),
      sub: [weatherNote(x), level(v) === 1 ? LK.text("tide_level_amber") : ""].filter(Boolean).join(" · "), what: LK.text("king_tide_what") };
  }

  window.TIDE_SEASON = { load: function () { return Promise.all([loadTable(), loadModel()]); }, loadTable: loadTable, loadModel: loadModel,
    dayHighs: dayHighs, kingDays: kingDays, expected: expected, level: level, line: line, weatherNote: weatherNote,
    clock: clock, ft: ft, mhhw: mhhw, red: red, king: king, state: S, station: STATION, months: MONTHS_AHEAD, now: nowLocal, iso: iso };
})();
