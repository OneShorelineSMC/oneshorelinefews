/* High tides for the King Tide line (kiosk), the Tides page card and its calendar, at two NOAA gauges:
 *   window.TIDE_SEASON        Bayside: Redwood City 9414523 (flood level TIDE_RED_FT_RWC, King Tide KING_TIDE_FT_RWC)
 *   window.TIDE_SEASON_COAST  Coastside: Monterey 9413450 (no flood level yet; King Tide KING_TIDE_FT_MRY, 1-year tide, provisional)
 * Redwood City details below; Monterey works the same way without the red level.
 *
 * Everything comes from NOAA at the Redwood City tide gauge (9414523), ft NAVD88, so nothing needs a yearly update:
 *   - the tide table (predicted high tides) from the start of this month through the next 6 months
 *   - the NOAA projection (NOAA's San Francisco Bay model, ofs_water_level: storms, wind, runoff, ocean conditions such as El Niño), about 2 days ahead
 *   - after the projection: the tide table plus the recent offset (tide_offset.json on the data branch, scripts/tide_offset.py):
 *     how much higher than the tide table the water has run on average over the past month (BAY_OFFSET_* in settings.csv).
 *     An assumption ("if the Bay stays this high"), not a forecast: it never changes a day's color, only adds a gray
 *     dotted mark on days it would take to the flood level.
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
  var LK = window.LOOKUPS, MATCH_MIN = 90, MONTHS_AHEAD = 6;
  var OFFSET_URL = "https://raw.githubusercontent.com/OneShorelineSMC/oneshorelinefews/data/tide_offset.json";
  var OFF = { data: null, t: 0, pending: null, listeners: [] };   // one download for both gauges
  function loadOffsetFile() {
    if (OFF.pending) return OFF.pending;
    OFF.pending = fetch(OFFSET_URL + "?t=" + Date.now(), { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { if (j && j.stations) { OFF.data = j; OFF.t = Date.now(); OFF.listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); } })
      .catch(function () {})
      .then(function () { OFF.pending = null; });
    return OFF.pending;
  }
  // cfg: { station, red: settings key or null (no flood level), king: settings key, sfx: wording suffix ("" Bayside, "_coast" Coastside) }
  function make(cfg) {
  var STATION = cfg.station, SFX = cfg.sfx || "";
  var S = { highs: null, tHighs: 0, ofs: null, tOfs: 0, from: null };
  function txt(k, v) { var t = SFX ? LK.text(k + SFX, v) : ""; return t || LK.text(k, v); }   // the Coastside wording where there is one

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
  function get(u) {   // gives up after 30 s so a slow NOAA reply can't hold the calendar forever
    var ac = typeof AbortController !== "undefined" ? new AbortController() : null, tm = ac ? setTimeout(function () { ac.abort(); }, 30000) : 0;
    return fetch(u, ac ? { cache: "no-cache", signal: ac.signal } : { cache: "no-cache" }).finally(function () { clearTimeout(tm); }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then(function (j) { if (j.error) throw new Error(j.error.message || "error"); return j; });
  }
  function pts(arr, onlyHigh) {
    return (arr || []).filter(function (p) { return !onlyHigh || p.type === "H"; })
      .map(function (p) { return { t: parseLocal(p.t), v: parseFloat(p.v) }; }).filter(function (p) { return !isNaN(p.v); });
  }

  /* The tide table: this month and the next MONTHS_AHEAD in one request (NOAA allows a year of high/low tides per request).
     If it fails (NOAA slow or down), try again in 5 minutes until it works, keeping the last good copy meanwhile. */
  var listeners = [], retry = 0, pending = null;
  function changed() { listeners.forEach(function (fn) { try { fn(); } catch (e) {} }); }
  OFF.listeners.push(changed);
  function loadTable() {
    if (pending) return pending;
    var n = nowLocal(), d = new Date(n), y = d.getUTCFullYear(), m = d.getUTCMonth();
    var a = monthStart(y, m), b = monthStart(y, m + MONTHS_AHEAD + 1) - 86400000;
    clearTimeout(retry);
    pending = get(url("predictions", ymd(a), ymd(b), "&interval=hilo")).then(function (j) {
      var all = pts(j.predictions, true).sort(function (p, q) { return p.t - q.t; });
      if (!all.length) throw new Error("empty");
      S.highs = all; S.tHighs = Date.now(); S.from = a; changed();
    }).catch(function () { retry = setTimeout(loadTable, 5 * 60000); })
      .then(function () { pending = null; });
    return pending;
  }
  // The NOAA projection: pages that already download it for their graph hand it over (setModel), so it's fetched once
  function setModel(p, t) { if (p && p.length) { S.ofs = p; S.tOfs = t || Date.now(); changed(); } }
  function loadModel() {
    var n = nowLocal();
    return get(url("ofs_water_level", ymd(n - 86400000), ymd(n + 3 * 86400000)))
      .then(function (j) { setModel(pts(j.data || j.predictions)); }).catch(function () {});
  }
  function modelOK(now) {
    return !!(S.ofs && S.ofs.length && Date.now() - S.tOfs < LK.num("MODEL_MAX_AGE_HOURS") * 3600000 &&
      S.ofs[S.ofs.length - 1].t >= now + LK.num("MODEL_MIN_AHEAD_HOURS") * 3600000);
  }

  /* The recent offset at this gauge: {ft, days, from, to, recent7} or null when it's switched off, too old, missing,
     or smaller than BAY_OFFSET_MIN_FT (only a Bay running higher than the tide table is shown). */
  function offset() {
    var j = OFF.data, r = j && j.stations ? j.stations[STATION] : null;
    if (!r || LK.num("BAY_OFFSET_SHOW") !== 1 || typeof r.offset_ft !== "number" || !r.computed_utc) return null;
    var age = (Date.now() - Date.parse(r.computed_utc.replace(/Z$/, ":00Z"))) / 3600000;
    if (!(age >= 0 && age <= LK.num("BAY_OFFSET_MAX_AGE_HOURS")) || r.offset_ft < LK.num("BAY_OFFSET_MIN_FT")) return null;
    return { ft: r.offset_ft, days: r.days_used || r.days, from: r.from, to: r.to, recent7: r.recent7_ft };
  }
  /* The calendar outlook from the data job (tide_offset.json "outlook", weekly; scripts/tide_offset.py): the usual height
     above the tide table for each month, the month-to-month persistence (r1) and El Niño's winter effect. null when off,
     missing or too old. THRESHOLDS_BASIS.md §4b. */
  function outlookData() {
    var o = OFF.data && OFF.data.outlook;
    if (!o || !o.normal_ft || !o.computed_utc || LK.num("TIDE_OUTLOOK_SHOW") !== 1) return null;
    var age = (Date.now() - Date.parse(o.computed_utc.replace(/Z$/, ":00Z"))) / 86400000;
    return age >= 0 && age <= LK.num("TIDE_OUTLOOK_MAX_AGE_DAYS") ? o : null;
  }
  function usual(o, ms) {   // the usual height above the tide table in that month (ft), or null
    var v = o.normal_ft[iso(ms).slice(0, 7)];
    return typeof v === "number" ? v : null;
  }
  /* Days after the NOAA projection, up to BAY_OFFSET_AHEAD_DAYS (6 weeks): each day's highest tide-table high tide plus
     the recent offset, fading by damped persistence (NOAA's method, Dusek et al. 2022): the usual height for that month,
     plus today's departure from the usual times r1 ^ (days / 30.4). Without the outlook data: the offset as it is.
     {date: {t, v, table, off}}. Only days the projection doesn't cover and high tides still ahead. */
  function offsetDays(now) {
    now = now || nowLocal();
    var o = offset(), ol = outlookData(), out = {};
    if (!o || !S.highs) return out;
    var ex = expected(now), u0 = ol ? usual(ol, now) : null, r1 = ol && typeof ol.r1 === "number" ? Math.max(0, Math.min(0.95, ol.r1)) : null;
    S.highs.forEach(function (h) {
      var d = iso(h.t);
      if (h.t < now - MATCH_MIN * 60000 || ex[d] || h.t > now + LK.num("BAY_OFFSET_AHEAD_DAYS") * 86400000) return;
      if (modelOK(now) && h.t <= S.ofs[S.ofs.length - 1].t) return;   // still inside the projection
      var add = o.ft, u = ol ? usual(ol, h.t) : null;
      if (u0 != null && u != null && r1 != null) add = u + (o.ft - u0) * Math.pow(r1, (h.t - now) / (30.4 * 86400000));
      var x = { t: h.t, v: h.v + add, table: h.v, off: add };
      if (!out[d] || x.v > out[d].v) out[d] = x;
    });
    return out;
  }
  /* Seasonal outlook, after BAY_OFFSET_AHEAD_DAYS to the end of the calendar: the usual height above the tide table for
     each month, plus El Niño (or La Niña) in its months when the latest ONI is at least ENSO_MIN_ONI from 0 and the
     San Francisco record shows a significant effect. Not marks on days: a line under the calendar, with the days that
     would reach the flood level at that height. null without the outlook data. */
  function seasonOutlook(now) {
    now = now || nowLocal();
    var ol = outlookData();
    if (!ol || !S.highs) return null;
    var en = ol.enso, useEnso = !!(en && en.significant && typeof en.oni === "number" && Math.abs(en.oni) >= LK.num("ENSO_MIN_ONI"));
    var from = now + LK.num("BAY_OFFSET_AHEAD_DAYS") * 86400000, days = [], adds = [], last = null;
    S.highs.forEach(function (h) {
      if (h.t <= from) return;
      var u = usual(ol, h.t);
      if (u == null) return;
      var m = new Date(h.t).getUTCMonth() + 1, e = useEnso && en.months.indexOf(m) >= 0 ? en.slope_ft_per_c * en.oni : 0;
      var add = u + e, v = h.v + add, d = iso(h.t);
      adds.push(u); last = h.t;   // the usual part alone (El Niño is given separately)
      if (level(v) === 2 && level(h.v) < 2 && (!days.length || days[days.length - 1].date !== d)) days.push({ date: d, t: h.t, v: v, add: add });
    });
    if (!adds.length) return null;
    return { from: iso(from), to: iso(last), usual: Math.min.apply(null, adds), usualMax: Math.max.apply(null, adds),
      enso: useEnso ? { oni: en.oni, season: en.oni_season, add: en.slope_ft_per_c * en.oni, phase: en.oni > 0 ? "El Niño" : "La Niña", months: en.months } : null,
      days: days, data: ol };
  }

  function mhhw() { return LK.mhhw(STATION); }
  function red() { return cfg.red ? LK.num(cfg.red) : Infinity; }
  function king() { return LK.num(cfg.king); }
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
      sub: [weatherNote(x), level(v) === 1 ? LK.text("tide_level_amber") : ""].filter(Boolean).join(" · "), what: txt("king_tide_what") };
  }

  return { load: function () { return Promise.all([loadTable(), loadModel(), loadOffsetFile()]); }, loadTable: loadTable, loadModel: loadModel, setModel: setModel,
    loadOffset: loadOffsetFile, offset: offset, offsetDays: offsetDays, seasonOutlook: seasonOutlook, outlook: outlookData,
    onUpdate: function (fn) { listeners.push(fn); },
    dayHighs: dayHighs, kingDays: kingDays, expected: expected, level: level, line: line, weatherNote: weatherNote, txt: txt,
    clock: clock, ft: ft, mhhw: mhhw, red: red, king: king, state: S, station: STATION, months: MONTHS_AHEAD, now: nowLocal, iso: iso };
  }
  window.TIDE_SEASON = make({ station: "9414523", red: "TIDE_RED_FT_RWC", king: "KING_TIDE_FT_RWC" });
  window.TIDE_SEASON_COAST = make({ station: "9413450", red: null, king: "KING_TIDE_FT_MRY", sfx: "_coast" });
})();
