/* FEWS creek status layer: public since Oct 16 (STATUS_PUBLIC = 1 in lookups/settings.csv; 0 = staff preview only again).
 * ?preview=1 in the address = staff view: the STAFF PREVIEW badge and the staff table. Creeks other than the four
 * dashboard creeks (preview_only in creeks.csv) carry a "Methodology under review" tag (method_review).
 *
 * The data job works out one status per creek (scripts/creek_signals.py, rules in lookups/THRESHOLDS_BASIS.md §10)
 * and writes it into creeks.json with reason codes. This file turns that into cards, a summary, a staff table and
 * kiosk tiles, using the wording in lookups/display_text.csv (through lookups.js). Everything from the data is
 * shown as text. Colors are the site's own: Warning red, Watch orange, Monitoring yellow, Normal green, gray.
 * Load after lookups.js.
 */
(function () {
  "use strict";
  var LK = window.LOOKUPS;
  var STAFF = /[?&]preview=1\b/.test(location.search);   // staff view
  function shown() { return STAFF || LK.num("STATUS_PUBLIC") === 1; }   // status layer on this page (read each time: settings.csv can switch it off)
  function review(c, short) { return c && c.preview_only ? '<span class="cs-review" title="' + esc(T("method_review")) + '">' + esc(T(short ? "method_review_short" : "method_review")) + "</span>" : ""; }
  var COL = { likely: "#c62828", ready: "#e07b00", alert: "#e6c200", offline: "#66717d", delayed: "#66717d", none: "#66717d" };   // grays dark enough for text (4.5:1)
  var TINT = { likely: "#c62828", ready: "rgba(224,123,0,.16)", alert: "rgba(230,194,0,.20)", offline: "rgba(138,150,163,.14)",
    delayed: "rgba(138,150,163,.14)", none: "rgba(138,150,163,.10)" };
  var RANK = { likely: 4, ready: 3, alert: 2, offline: 1, delayed: 1, none: 0 };
  var LEVEL_COL = ["#2e7d32", "#e6c200", "#e07b00", "#c62828", "#9c27b0"];

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function T(k, v) { return LK.text(k, v); }
  // Pacific clock times kept as plain clock times (same convention as the pages)
  function parse(s) { var a = String(s).split(/[- :]/).map(Number); return Date.UTC(a[0], a[1] - 1, a[2], a[3] || 0, a[4] || 0); }
  function nowLocal() {
    var p = {}; new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", hourCycle: "h23", year: "numeric",
      month: "numeric", day: "numeric", hour: "numeric", minute: "numeric" }).formatToParts(new Date())
      .forEach(function (x) { p[x.type] = +x.value; });
    return Date.UTC(p.year, p.month - 1, p.day, p.hour % 24, p.minute);
  }
  function fmt(ms, o) { return new Date(ms).toLocaleString("en-US", Object.assign({ timeZone: "UTC" }, o)); }
  function clock(s) { return s ? fmt(parse(s), { hour: "numeric", minute: "2-digit" }) : ""; }
  function dated(s) { return s ? fmt(parse(s), { weekday: "short", month: "short", day: "numeric" }) + ", " + clock(s) : ""; }
  // Public creeks and staff-preview creeks (preview_only = yes in creeks.csv; only this preview shows them)
  function allCreeks(data) { return (data.creeks || []).concat(data.creeks_preview || []); }
  function list(a) { return a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1]; }
  function rainWord(l) { return l >= 3 ? T("rain_severe") : l === 2 ? T("rain_vheavy") : l === 1 ? T("rain_heavy") : ""; }
  // "Creek level at Old County Road" / "Creek level below Stone Dam"
  function levelLabel(g) {
    var l = String(g.label || ""), m = /^(below|above|upstream of|downstream of|near)\b\s*/i.exec(l);
    return m ? T("creek_level_word") + " " + l.charAt(0).toLowerCase() + l.slice(1) : T("creek_level_at", { place: l });
  }
  function winLabel(m) { return m < 60 ? m + " min" : m / 60 + " hr"; }

  /* One creek's status as shown: the data job's answer, or Data delayed when the data file is old */
  function view(data, c) {
    var st = c.status || {}, key = st.key || "none";
    var late = !data.generated || nowLocal() - parse(data.generated) > LK.num("CREEK_DATA_LATE_MIN") * 60000;
    if (late) key = "delayed";
    var word = key === "delayed" ? T("verdict_delayed", { time: clock(data.generated) })
      : key === "offline" && (st.out_of_service || []).length ? T("verdict_out_of_service") : T("verdict_" + key);
    var todo = key === "offline" || key === "delayed" ? T("verdict_nodata_todo") : T("verdict_" + key + "_todo");
    var reasons = (st.reasons || []).map(reason).filter(Boolean);
    if (late && st.key && st.key !== "none") reasons.unshift(T("verdict_" + st.key) + " at " + clock(data.generated) + ", the last update.");
    // "Since 1:40 PM · before that: Stay alert" (the data job keeps when each status started)
    var since = key !== "delayed" && key !== "none" && st.since ? T("since_line", { time: clock(st.since) }) +
      (st.prev && st.prev !== st.key ? " · " + T("was_line", { status: T("verdict_" + st.prev) }) : "") : "";
    return { key: key, word: word, todo: todo, reasons: reasons, st: st, rank: RANK[key], color: COL[key], since: since,
      eoc: key === "delayed" || key === "none" ? "" : T("eoc_action_" + key) };
  }
  function reason(r) {
    if (r.code === "why_out_of_service") return T("why_out_of_service", { gauge: r.gauge }) + (r.note ? " " + r.note : "");
    var s = T(r.code, { rain: rainWord(r.rain).toLowerCase(), Rain: rainWord(r.rain), time: clock(r.time) });
    if (!s) return "";
    if (r.code === "why_watch" && r.rising_fast) s = s.replace(/\.$/, " and rising fast.");
    if (r.code === "why_monitoring" && (r.rising || r.rising_fast)) s = s.replace(/\.$/, r.rising_fast ? " and rising fast." : " and rising.");
    return s;
  }

  /* Status icons, so a status can be told apart without color (WCAG 1.4.1): flooding likely = warning triangle,
     be ready = exclamation in a circle, stay alert = eye; no alerts = plain dot; offline / not updated = dashed square.
     Always next to the status word (decoration only, aria-hidden). */
  var ICON = {
    likely: '<path d="M10 2.2 19 17.8H1Z" fill="currentColor"/><path class="x" d="M10 7.5v4.6" stroke-width="2.2" stroke-linecap="round"/><circle class="x" cx="10" cy="14.9" r="1.25"/>',
    ready: '<circle cx="10" cy="10" r="8.6" fill="currentColor"/><path d="M10 5.4v5.5" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/><circle cx="10" cy="14" r="1.3" fill="#fff"/>',
    alert: '<path d="M1.3 10C3.6 6 6.6 4.2 10 4.2S16.4 6 18.7 10C16.4 14 13.4 15.8 10 15.8S3.6 14 1.3 10Z" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="10" cy="10" r="3" fill="currentColor"/>',
    none: '<path d="M4.2 10.4 8.3 14.4 15.8 6.2" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
  };
  function icon(key) {
    var k = ICON[key] ? key : "nodata";
    if (k === "nodata") return '<span class="cs-ic cs-ic-nodata" aria-hidden="true"></span>';
    return '<svg class="cs-ic cs-ic-' + k + '" viewBox="0 0 20 20" width="20" height="20" aria-hidden="true" focusable="false">' + ICON[k] + "</svg>";
  }

  /* Pieces */
  // Rain chip: Heavy / Very heavy / Intense from the Atlas 14 levels; below Heavy, "Raining" if any rain fell in the
  // last hour (RAIN_NOW_MIN, data job) and "No rain" if not
  function chip(level, now, long) {
    if (!level) return now ? '<span class="cs-chip raining">' + esc(T("rain_now")) + "</span>" : '<span class="cs-norain">' + esc(T(long ? "rain_none_card" : "rain_none")) + "</span>";
    var k = level >= 3 ? "severe" : level === 2 ? "vheavy" : "heavy", b = "";
    for (var i = 1; i <= 3; i++) b += "<i" + (i <= level ? ' class="on"' : "") + "></i>";
    return '<span class="cs-chip ' + k + '"><span class="cs-meter" aria-hidden="true">' + b + "</span>" + esc(rainWord(level)) + "</span>";
  }
  function trendText(t, short) {
    if (!t || !t.trend) return "";
    var w = T("trend_" + t.trend), arrow = { fast: "↑↑", rising: "↑", steady: "→", falling: "↓" }[t.trend] || "";
    return '<span aria-hidden="true">' + arrow + "</span> " + esc(w) + (!short && t.ft_per_hr != null && t.trend !== "steady" ? ' <span class="cs-dim">(' + (t.ft_per_hr > 0 ? "+" : "") + t.ft_per_hr.toFixed(1) + " ft/hr)</span>" : "");
  }
  // A gauge's flood levels (1 Monitoring … 4 Major), low to high. A gauge with any level counts as having levels
  // (some have only Watch and Warning, e.g. Pescadero and San Mateo; Pilarcitos and San Gregorio add Major).
  function lvls(g) { return (g.thresholds || []).filter(function (t) { return t.level >= 1 && t.level <= 4; }).sort(function (a, b) { return a.value - b.value; }); }
  function lvName(t) { return t.name.replace(/^Flood /, "").replace(/ Flood Stage$/, ""); }   // "Watch", "Warning", "Major"
  var LV_IC = { 1: "alert", 2: "ready", 3: "likely", 4: "likely" };
  // Normal | each level the gauge has, only the active segment colored, marker at the current stage
  function band(g, e) {
    var th = lvls(g);
    var p = e && e.points && e.points.length ? e.points[e.points.length - 1] : null;
    if (e && e.latest && e.latest[0] && (!p || e.latest[0] > p[0])) p = e.latest;
    var sig = e && e.signals || {};
    if (e && e.out_of_service) return '<div class="cs-row"><span class="cs-lbl">' + esc(levelLabel(g)) + '</span><span class="cs-val"><b>' + esc(T("gauge_out")) + "</b></span></div>";
    if (!p || !sig.trend) return '<div class="cs-row"><span class="cs-lbl">' + esc(levelLabel(g)) + '</span><span class="cs-val cs-dim">' + esc(T("verdict_offline")) + (p ? " · " + esc(dated(p[0])) : "") + "</span></div>";
    var v = p[1];
    if (!th.length) return '<div class="cs-row"><span class="cs-lbl">' + esc(levelLabel(g)) + '</span><span class="cs-val">' + trendText(sig, true) + "</span></div>";
    var n = th.length, last = th[n - 1].value, top = last + Math.max(0.5, n > 1 ? last - th[n - 2].value : last * 0.15);
    var seg = [[0, th[0].value, 35, "Normal", 0]];
    th.forEach(function (t, i) { seg.push([t.value, i + 1 < n ? th[i + 1].value : top, i + 1 < n ? 20 : 25, lvName(t), t.level]); });
    var act = 0; th.forEach(function (t, i) { if (v >= t.value) act = i + 1; });
    var pos = 0, acc = 0, tot = seg.reduce(function (a, s) { return a + s[2]; }, 0);
    seg.forEach(function (s, i) {
      if (i === act) pos = acc + s[2] * Math.max(0, Math.min(1, (v - s[0]) / (s[1] - s[0] || 1)));
      acc += s[2];
    });
    pos = pos / tot * 100;
    var lt = act ? th[act - 1] : null, name = lt ? lt.name : T("status_normal"), lic = lt ? icon(LV_IC[lt.level]) : "";   // levels share the status icons
    return '<div class="cs-band"><div class="cs-bt"><span class="cs-lbl">' + esc(levelLabel(g)) + '</span><span class="cs-now">' + (lic ? '<span class="cs-lvi">' + lic + "</span>" : "") + esc(name) + " · " + trendText(sig, true) + "</span></div>" +
      '<div class="cs-track" role="img" aria-label="' + esc(g.label + ": " + name) + '">' + seg.map(function (s, i) {
        return '<span class="cs-s" style="flex:' + s[2] + (i === act ? ";background:" + LEVEL_COL[Math.min(3, s[4])] : "") + '"></span>'; }).join("") +
      '<span class="cs-mark" style="left:' + pos.toFixed(1) + '%"></span></div>' +
      '<div class="cs-ticks" aria-hidden="true">' + seg.map(function (s, i) {
        return '<span style="flex:' + s[2] + '"' + (i === act ? ' class="on"' : "") + ">" + esc(s[3]) + "</span>"; }).join("") + "</div></div>";
  }

  /* NWS rain forecast (data job: scripts/nws_forecast.py). Shown on creek cards when FORECAST_PUBLIC = 1 (staff view
     always) and at least FORECAST_SHOW_IN inches are expected in the next 3 days; never on the kiosk; never changes a status. */
  function utcMs(s) { return s ? Date.parse(s) : NaN; }   // "2026-10-18T20:00Z"
  function pac(ms, o) { return new Date(ms).toLocaleString("en-US", Object.assign({ timeZone: "America/Los_Angeles" }, o)); }
  function pacTime(ms) { return pac(ms, { hour: "numeric", minute: "2-digit" }); }
  function fc(c) {
    var f = c.forecast;
    if (!f || f.next72 == null || !(STAFF || LK.num("FORECAST_PUBLIC") === 1)) return null;
    if (!(Date.now() - utcMs(f.fetched) < LK.num("FORECAST_KEEP_HOURS") * 3600000)) return null;
    return f;
  }
  function inch(x) { return (x < 0.005 ? "0" : x.toFixed(2)) + " in"; }
  function forecastRow(c) {
    var f = fc(c);
    if (!f || f.next72 < LK.num("FORECAST_SHOW_IN")) return "";
    var pk = f.peak_in && f.peak_start ? T("fc_peak", { inches: f.peak_in.toFixed(2), start: pac(utcMs(f.peak_start), { weekday: "short", hour: "numeric" }),
      end: pac(utcMs(f.peak_start) + f.peak_hours * 3600000, { hour: "numeric" }) }) : "";
    return '<div class="cs-row cs-fc"><span class="cs-lbl">' + esc(T("fc_row")) + '</span><span class="cs-val">' +
      esc(T("fc_value", { d1: inch(f.next24), d3: inch(f.next72) })) +
      '<span class="cs-sm">' + (pk ? esc(pk) + " · " : "") + esc(T("fc_note", { time: f.issued ? pacTime(utcMs(f.issued)) : "" })) +
      (f.error ? " " + esc(T("fc_stale", { time: pacTime(utcMs(f.fetched)) })) : "") + "</span></span></div>";
  }
  function forecastCell(c) {
    var f = fc(c);
    if (!f) return '<span class="cs-dim">' + (c.forecast && c.forecast.error ? "not read" : "—") + "</span>";
    return f.next24.toFixed(2) + " in · 24 hr" + '<span class="cs-sm">' + f.next72.toFixed(2) + " in · 3 days" + (f.error ? " · not updated" : "") + "</span>";
  }

  /* A creek with no alert, in brief (Creeks page): the status once, where the creek is measured, its level and which
     way it is moving in words, rainfall, and one link to its own page (numbers, graphs, levels). No level bar. */
  function levelWords(g, e) {
    var p = e && e.points && e.points.length ? e.points[e.points.length - 1] : null;
    if (e && e.latest && e.latest[0] && (!p || e.latest[0] > p[0])) p = e.latest;
    var sig = e && e.signals || {};
    if (e && e.out_of_service) return "<b>" + esc(T("gauge_out")) + "</b>";
    if (!p || !sig.trend) return esc(T("verdict_offline"));
    var th = lvls(g), at = null;
    th.forEach(function (t) { if (p[1] >= t.value) at = t; });
    var name = !th.length ? T("no_flood_level_title") : at ? at.name : T("status_normal");
    return '<span class="nw">' + esc(name) + '</span> · <span class="nw">' + trendText(sig, true) + "</span>";
  }
  function briefCard(data, c, v, opts) {
    var st = v.st, r = st.rain || {}, gs = c.stages || [], h = "";
    h += '<article class="cs-card cs-brief cs-' + v.key + '" data-creek="' + esc(c.id) + '">';
    h += '<div class="cs-head"><h3>' + esc(c.name) + "</h3>" + review(c) + "</div>";
    h += '<div class="cs-stat"><div class="cs-verdict cs-v-' + v.key + '">' + icon(v.key) + esc(v.word) + "</div></div>";
    h += '<div class="cs-factw"><dl class="cs-facts">';
    if (gs.length === 1) {
      h += "<div><dt>" + esc(T("brief_location")) + "</dt><dd>" + esc(gs[0].label) + "</dd></div>";
      h += "<div><dt>" + esc(T("brief_level")) + "</dt><dd>" + levelWords(gs[0], data.sensors[gs[0].key]) + "</dd></div>";
    } else gs.forEach(function (g) {
      h += "<div><dt>" + esc(levelLabel(g)) + "</dt><dd>" + levelWords(g, data.sensors[g.key]) + "</dd></div>";
    });
    h += "<div><dt>" + esc(T("rain_row")) + "</dt><dd>" + chip(r.level, r.now, true) + "</dd></div></dl>" + forecastRow(c) + "</div>";
    if (opts.link) h += '<div class="cs-foot cs-more"><a href="' + esc(opts.link) + '" aria-label="' + esc(T("card_more_aria", { creek: c.name })) + '">' + esc(T("card_more")) + ' <span aria-hidden="true">→</span></a></div>';
    return h + "</article>";
  }

  /* A creek card: status, reason, What to do, then details. opts.link: where "details" goes; opts.compact: no details */
  function card(data, c, opts) {
    opts = opts || {};
    var v = view(data, c), st = v.st, h = "";
    if (opts.quiet && v.key === "none" && !opts.compact) return briefCard(data, c, v, opts);
    h += '<article class="cs-card cs-' + v.key + '" data-creek="' + esc(c.id) + '">';
    var noLv = (c.stages || []).length && (c.stages || []).every(function (g) {
      return !lvls(g).length; });
    h += '<div class="cs-head"><h3>' + esc(c.name) + "</h3>" + review(c) + (opts.lvlTag && noLv ? '<span class="cs-sm">' + esc(T("no_flood_level_title")) + "</span>" : "") + "</div>";
    h += '<div class="cs-stat"><div class="cs-verdict cs-v-' + v.key + '">' + icon(v.key) + esc(v.word) + "</div>";
    if (v.since) h += '<p class="cs-since">' + esc(v.since) + "</p>";
    v.reasons.forEach(function (r) { h += '<p class="cs-why">' + esc(r) + "</p>"; });
    h += "</div>";
    h += '<div class="cs-body">' + (v.key === "likely" ? '<p class="cs-danger">' + esc(T("e911")) + "</p>" : "") +
      '<p class="cs-todo"><b>What to do:</b> ' + esc(v.todo) + "</p></div>";
    if (!opts.compact) {
      h += '<div class="cs-details cs-stages">';
      // Creeks without flood levels: say so where the level bar would be, then each gauge's trend below it
      var noLevels = (c.stages || []).length && (c.stages || []).every(function (g) {
        return !lvls(g).length; });
      if (noLevels && !opts.lvlTag) h += '<div class="cs-nolvl"><b>' + esc(T("no_flood_level_title")) + "</b> " + esc(T("no_flood_level")) + "</div>";
      (c.stages || []).forEach(function (g) { h += band(g, data.sensors[g.key]); });
      var r = st.rain || {};
      h += '</div><div class="cs-details cs-rainrow"><div class="cs-row"><span class="cs-lbl">' + esc(T("rain_row")) + '</span><span class="cs-val">' + chip(r.level, r.now, true) + "</span></div>" + forecastRow(c) + "</div>";
      h += opts.link ? "<div></div>" : numbers(data, c, opts.numbersOpen);   // (an empty row keeps the cards' rows lined up)
    } else h += "<div></div><div></div><div></div>";
    if (!opts.noAsOf || opts.link) h += '<div class="cs-foot"><span>' + (opts.noAsOf ? "" : "As of " + esc(dated(data.generated)) +
      (opts.compact && st.has_levels === false ? " · " + esc(T("no_flood_level_title")) : "")) + "</span>" +
      (opts.link ? '<a href="' + esc(opts.link) + '" aria-label="' + esc(T("card_more_aria", { creek: c.name })) + '">' + esc(T("card_more")) + ' <span aria-hidden="true">→</span></a>' : "") + "</div>";
    return h + "</article>";
  }

  /* "See the numbers": readings, rates and times behind the card (closed on the public card) */
  function numbers(data, c, open) {
    var st = c.status || {}, rows = "";
    function row(l, v) { rows += '<div class="cs-row"><span class="cs-lbl">' + esc(l) + '</span><span class="cs-val">' + v + "</span></div>"; }
    (c.stages || []).forEach(function (g) {
      var e = data.sensors[g.key] || {}, s = e.signals || {}, p = e.points && e.points.length ? e.points[e.points.length - 1] : null;
      if (e.latest && e.latest[0] && (!p || e.latest[0] > p[0])) p = e.latest;
      row(g.label + " (gauge reading)", p ? p[1].toFixed(2) + " ft" + (s.ft_per_hr != null && s.trend && s.trend !== "steady" ? " · " + (s.ft_per_hr > 0 ? "+" : "") + s.ft_per_hr.toFixed(1) + " ft/hr" : "") +
        '<span class="cs-sm">reading at ' + esc(dated(p[0])) + "</span>" : "—");
    });
    (c.rain || []).concat(c.rain_support || []).forEach(function (g) {
      var s = (data.sensors[g.key] || {}).signals || {};
      row(g.label + " rain gauge", (s.level ? esc(rainWord(s.level)) : esc(T(s.raining ? "rain_now" : "rain_none"))) + (s.driver ? " · " + s.driver.inches.toFixed(2) + " in in " + esc(winLabel(s.driver.minutes)) : "") +
        '<span class="cs-sm">' + (s.last_report ? "last report " + esc(dated(s.last_report)) : "no recent report") + "</span>");
    });
    if (st.trigger) row("Flooding trigger", esc(st.trigger.label) + ": " + st.trigger.amount.toFixed(2) + " of " + st.trigger.value.toFixed(2) + " in · met");
    if (st.tidal && st.tide && st.tide.ft != null) row("Bay tide (ft NAVD88)", st.tide.ft.toFixed(2) + " ft · " + (st.tide.rising ? "rising" : "falling") +
      (st.tide.next_high ? '<span class="cs-sm">next high ' + esc(clock(st.tide.next_high)) + " (" + st.tide.next_high_ft + " ft)</span>" : ""));
    return '<details class="cs-num"' + (open ? " open" : "") + "><summary>" + esc(T("numbers_title")) + '</summary><div class="cs-numb">' + rows +
      '<p class="cs-sm">Gauge readings are heights at the gauge, not water depth.</p></div></details>';
  }

  /* "How to read this page" */
  function howTo() {
    return '<details class="cs-how" id="howto"><summary>' + esc(T("howto_title")) + '</summary><div class="cs-howb">' +
      "<h4>" + esc(T("howto_alerts_h")) + "</h4><ul>" +
      ["likely", "ready", "alert", "none"].map(function (k) {
        return "<li>" + icon(k) + esc(T("howto_" + k)) + "</li>"; }).join("") + "</ul>" +
      "<h4>" + esc(T("howto_levels_h")) + "</h4><p>" + esc(T("howto_levels")) + "</p><ul class=\"cs-howlv\">" +
      [["status_normal", "howto_lv_normal"], ["lv_monitoring", "home_reason_monitoring"], ["lv_watch", "home_reason_watch"], ["lv_warning", "home_reason_warning"]].map(function (x) {
        return "<li><b>" + esc(T(x[0])) + ":</b> " + esc(T(x[1])) + "</li>"; }).join("") + "</ul>" +
      "<p>" + esc(T("howto_band")) + "</p>" +
      "<h4>" + esc(T("howto_trend_h")) + "</h4><p>" + esc(T("howto_trend")) + "</p>" +
      "<h4>" + esc(T("howto_rain_h")) + "</h4><p>" + esc(T("howto_rain")) + "</p>" +
      "<h4>" + esc(T("howto_nws_h")) + "</h4><p>" + esc(T("nws_separate")) + " " + esc(T("summary_caveat")) + "</p></div></details>";
  }

  /* Top of page: one-line summary, red banner when flooding is likely, one evacuation button */
  function summary(data, asOf) {
    // When the data file is old, summarize the last statuses we have, and say so first (never "No creek alerts")
    var by = { likely: [], ready: [], alert: [], nodata: [], out: [] }, late = false;
    allCreeks(data).forEach(function (c) {
      var v = view(data, c), k = v.key;
      if (k === "delayed") { late = true; k = (c.status || {}).key || "none"; }
      if (by[k]) by[k].push(c.name);
      else if (k === "offline") ((c.status || {}).out_of_service || []).length ? by.out.push(c.name) : by.nodata.push(c.name);
    });
    var m = late ? [T("verdict_delayed", { time: dated(data.generated) }) + ". At that time:"] : [];
    if (by.likely.length) m.push(T("summary_likely", { creeks: list(by.likely) }));
    if (by.ready.length) m.push(T("summary_ready", { creeks: list(by.ready) }));
    if (by.alert.length) m.push(by.alert.length <= 3 ? T("summary_alert", { creeks: list(by.alert) }) : T("summary_alert_many", { n: by.alert.length }));
    var calm = m.length === (late ? 1 : 0);
    if (calm) m.push(T("summary_none"));
    var h = "";
    if (by.likely.length) h += '<div class="cs-banner" role="alert">' + (late ? esc("As of " + clock(data.generated) + ": ") : "") + esc(T("banner_likely", { creeks: list(by.likely) })) + "</div>";
    h += '<div class="cs-glance">' + m.map(function (x, i) { return '<p class="cs-main' + (late && i === 0 ? " cs-late" : "") + '">' + esc(x) + "</p>"; }).join("");
    if (by.likely.length || by.ready.length) {
      var u = T("url_evacuation");
      if (/^https:\/\//.test(u)) h += '<a class="cs-evac" href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(T("evac_button")) + " →</a>";
    }
    var odd = (by.nodata.length ? " " + T("summary_nodata", { creeks: list(by.nodata) }) : "") + (by.out.length ? " " + T("summary_out", { creeks: list(by.out) }) : "");
    if (calm && !late) h += '<p class="cs-calm">' + esc(odd ? T("summary_normal_other") + odd : T("summary_normal_line")) + "</p>" +
      '<p class="cs-calm cs-caveat">' + esc(T("summary_caveat")) + "</p>";
    h += (asOf && !late ? '<p class="cs-sub cs-asof">' + esc(T("summary_asof", { time: dated(data.generated) })) + "</p>" : "") +
      '<p class="cs-sub">' + esc(T("nws_separate")) + "</p>" +
      (asOf ? '<p class="cs-new"><a href="#howto" data-howto="1">' + esc(T("howto_link")) + "</a></p>" : "") + "</div>";
    return h;
  }

  /* All creeks for a page: summary, cards for creeks with a status, the rest folded away */
  function page(data, linkFor, opts) {
    opts = opts || {};
    var rows = allCreeks(data).map(function (c) { return { c: c, v: view(data, c) }; });
    rows.sort(function (a, b) { return b.v.rank - a.v.rank; });
    var link = function (c) { return !linkFor || (c.preview_only && !opts.previewLinks) ? null : linkFor(c); };   // preview creeks: detail page on Creeks.html only
    var co = function (c, quiet) { return { link: link(c), lvlTag: !!opts.compactNotes, noAsOf: !!opts.compactNotes, quiet: !!quiet }; };
    var active = rows.filter(function (x) { return x.v.key !== "none"; }), quiet = rows.filter(function (x) { return x.v.key === "none"; });
    var h = badge() + summary(data, !!opts.compactNotes) + '<div id="cpSlot"></div>' + howTo() +   // cpSlot: the page puts its city finder here
      '<div class="cs-grid">' + active.map(function (x) { return card(data, x.c, co(x.c)); }).join("") + "</div>";
    var cards = '<div class="cs-grid">' + quiet.map(function (x) { return card(data, x.c, co(x.c, true)); }).join("") + "</div>";
    if (quiet.length && !active.length) h += '<h2 class="cs-qh">' + esc(T("quiet_title")) + "</h2>" + cards;
    else if (quiet.length) h += '<details class="cs-quiet"><summary>' + esc(T("quiet_some", { n: quiet.length })) + "</summary>" + cards + "</details>";
    return h + (opts.staff === false || !STAFF ? "" : staffTable(data));
  }
  function badge() {
    if (!STAFF) return "";
    return '<div class="cs-badge">STAFF VIEW · ' + (LK.num("STATUS_PUBLIC") === 1 ? "staff table below" : "creek status layer in testing · not shown to the public") + "</div>";
  }

  /* Staff table: everything behind each status */
  function staffTable(data) {
    var rows = allCreeks(data).map(function (c) {
      var v = view(data, c), st = v.st, r = st.rain || {}, d = r.driver, t = st.tide;
      var lvl = v.key === "offline" ? esc(T("status_offline")) : st.level ? esc(st.level_name || "Level " + st.level) : st.has_levels === false ? '<span class="cs-dim">No flood levels</span>' : esc(T("status_normal"));
      var heavy = d ? esc(winLabel(d.minutes)) + ": " + d.inches.toFixed(2) + " in at " + esc(d.label) +
        (d.storm_years ? '<span class="cs-sm">about a ' + (d.storm_years >= 100 ? "100+" : d.storm_years >= 10 ? Math.round(d.storm_years) : d.storm_years) + "-year storm (" + Math.round(100 * (1 - Math.exp(-1 / d.storm_years))) + "% chance in any year)</span>" : "")
        : '<span class="cs-dim">—</span>';
      var notes = (st.staff_notes || []).concat((r.silent || []).map(function (s) { return s.label + " silent since " + (s.since ? dated(s.since) : "?"); }));
      if (st.trigger) notes.unshift("Trigger: " + st.trigger.label + " " + st.trigger.amount + " of " + st.trigger.value + " in");
      return "<tr><td><b>" + esc(c.name) + "</b>" + review(c) + "</td><td><span class=\"cs-tag\"><i style=\"background:" + v.color + "\"></i>" + esc(v.word) + "</span>" +
        (st.since ? '<span class="cs-sm">since ' + esc(dated(st.since)) + (st.prev && st.prev !== st.key ? "; was " + esc(T("verdict_" + st.prev)) : "") + "</span>" : "") +
        (v.eoc ? '<span class="cs-sm"><b>EOC:</b> ' + esc(v.eoc) + "</span>" : "") + "</td>" +
        "<td>" + lvl + '<span class="cs-sm">' + trendText(st.trend) + "</span></td><td>" + chip(r.level, r.now) + "</td><td>" + heavy + "</td>" +
        "<td>" + (r.working || 0) + " of " + (r.of || 0) + '<span class="cs-sm">' + (r.elevated || 0) + " at very heavy+</span></td>" +
        "<td>" + (st.tidal ? (t && t.ft != null ? t.ft.toFixed(2) + " ft · " + (t.rising ? "rising" : "falling") + (t.next_high ? '<span class="cs-sm">high ' + esc(dated(t.next_high)) + " (" + t.next_high_ft + " ft)</span>" : "") : '<span class="cs-dim">no tide data</span>') : '<span class="cs-dim">not tidal</span>') + "</td>" +
        "<td>" + forecastCell(c) + "</td><td>" + esc(notes.join("; ")) + "</td></tr>";
    });
    // Status changes in the hour before this update (from each creek's "since")
    var gen = parse(data.generated), changed = allCreeks(data).filter(function (c) {
      var st = c.status || {}; return st.since && st.prev !== undefined && gen - parse(st.since) <= 3600000 && st.prev !== null;
    }).map(function (c) { var st = c.status; return esc(c.name) + ": " + esc(T("verdict_" + (st.prev || "none"))) + " → <b>" + esc(T("verdict_" + st.key)) + "</b> at " + esc(clock(st.since)); });
    return '<details class="cs-staff"><summary>Staff table: what is behind each status</summary>' +
      '<p class="cs-changed"><b>' + esc(T("changed_title")) + ":</b> " + (changed.length ? changed.join(" · ") : "no changes") + "</p>" +
      '<div class="cs-tw"><table class="cs-tbl"><thead><tr>' +
      "<th>Creek</th><th>Status</th><th>Creek level · trend</th><th>Rain</th><th>Heaviest rain</th><th>Rain gauges</th><th>Tide</th><th>Expected (NWS)</th><th>Notes</th>" +
      "</tr></thead><tbody>" + rows.join("") + "</tbody></table></div><p class=\"cs-sm\">Data as of " + esc(dated(data.generated)) +
      ". Status changes are logged in status_log.csv on the data branch.</p><p class=\"cs-sm\">" + esc(T("staff_legend")) + "</p></details>";
  }

  /* Kiosk: large tiles, nothing to tap */
  function tile(data, c) {
    var v = view(data, c), st = v.st, r = st.rain || {};
    return '<div class="cs-tile cs-' + v.key + '"><div class="cs-tn">' + esc(c.name) + review(c) + "</div>" +
      '<div class="cs-verdict cs-v-' + v.key + '">' + icon(v.key) + esc(v.word) + "</div>" +
      (v.since ? '<div class="cs-ts">' + esc(v.since) + "</div>" : "") +
      (v.reasons[0] ? '<div class="cs-tr">' + esc(v.reasons[0]) + "</div>" : "") +
      '<div class="cs-tm"><span class="cs-dim">Rain</span> ' + chip(r.level, r.now) + (st.trend ? ' &nbsp; <span class="cs-dim">Creek</span> ' + trendText(st.trend, true) : "") + "</div></div>";
  }


  /* ---------- Home page (staff preview): one line per creek, grouped by status ---------- */
  // What the creek is doing, in everyday words (no Flood Watch / Warning names: most people know those as NWS alerts;
  // no staff-only notes such as a silent rain gauge). Wording: home_reason_* in display_text.csv.
  function plain(st) {
    var R = st.reasons || [], has = function (c) { return R.filter(function (r) { return r.code === c; })[0]; };
    var fast = R.some(function (r) { return r.rising_fast || r.code === "why_rising_fast"; }) || (st.trend || {}).trend === "fast";
    var rising = !fast && (R.some(function (r) { return r.rising; }) || (st.trend || {}).trend === "rising");
    var move = fast ? " " + T("home_reason_and_fast") : rising ? " " + T("home_reason_and_rising") : "";
    var rl = (st.rain || {}).level || 0, out = [];
    if (has("why_warning")) out.push(T("home_reason_warning") + move);
    else if (has("why_watch")) out.push(T("home_reason_watch") + move);
    else if (has("why_monitoring")) out.push(T("home_reason_monitoring") + move);
    else if (fast) out.push(T("home_reason_rising_fast"));
    else if (has("why_normal_rain")) out.push(T("home_reason_normal_rain"));
    else if (rising) out.push(T("home_reason_rising"));
    if (has("why_trigger_tide")) out.push(T("home_reason_trigger_tide"));
    else if (has("why_trigger")) out.push(T("home_reason_trigger"));
    else if (rl && !has("why_normal_rain")) out.push(rainWord(rl).toLowerCase() + " rain");
    var t = out.join("; ").replace(/^./, function (c) { return c.toUpperCase(); });
    if (has("why_gauge_offline")) t = t ? t + " (" + T("home_reason_offline") + ")" : T("home_reason_offline").replace(/^./, function (c) { return c.toUpperCase(); });
    return t;
  }
  // { banner, html }: banner = the red "Flooding is likely" box (it carries the 911 line), or "" when nothing is likely
  function home(data, linkFor) {
    var rows = allCreeks(data).map(function (c) {
      var v = view(data, c), k = v.key, late = k === "delayed";
      if (late) k = (c.status || {}).key || "none";
      return { c: c, v: v, k: k, late: late };
    });
    var late = rows.some(function (r) { return r.late; });
    var groups = ["likely", "ready", "alert"].map(function (k) { return { k: k, rows: rows.filter(function (r) { return r.k === k; }) }; })
      .filter(function (g) { return g.rows.length; });
    var likely = rows.filter(function (r) { return r.k === "likely"; });
    var banner = likely.length ? '<div class="cs-banner" role="alert">' + (late ? esc("As of " + clock(data.generated) + ": ") : "") +
      esc(T("banner_likely", { creeks: list(likely.map(function (r) { return r.c.name; })) })) + "</div>" : "";
    // The kiosk's status board, for the web (staff, 2026-10-23): one row per creek with a status, worst first: status,
    // why, rain now, since; the creeks with no alerts in one line under it. Rows link to the creek's page.
    var act = rows.filter(function (r) { return r.k !== "none"; }).sort(function (a, b) { return (RANK[b.k] || 0) - (RANK[a.k] || 0) || allCreeks(data).indexOf(a.c) - allCreeks(data).indexOf(b.c); });
    var nq = rows.filter(function (r) { return r.k === "none"; });
    var h = '<div class="cs-home"><div class="cs-board cs-wboard"><div class="cs-bhead"><b>Creeks</b><span>' +
      (act.length ? act.length + " with a status · " : "") + nq.length + " with no alerts · updated " + esc(clock(data.generated)) + "</span></div>";
    if (late) h += '<div class="cs-blate">⚠ ' + esc(T("verdict_delayed", { time: clock(data.generated) })) + ". Showing each creek’s status at that time.</div>";
    if (!act.length) {   // say only what was measured (not an all-clear), then the scope
      h += '<div class="cs-wnone">' + icon("none") + "<span>" + esc(T("home_none")) + '</span></div><p class="cs-wscope">' + esc(T("home_none_note")) + "</p>";
    } else {
      h += '<div class="cs-bcols cs-wcols" aria-hidden="true"><i></i><span>' + esc(T("board_col_creek")) + "</span><span>" + esc(T("board_col_status")) + "</span><span>" +
        esc(T("board_col_why")) + "</span><span>" + esc(T("board_col_rain")) + '</span><span class="cs-bsince">' + esc(T("board_col_since")) + "</span><i></i></div>";
      h += '<ul class="cs-wrows' + (late ? " cs-dimmed" : "") + '">' + act.map(function (r) {
        var st = r.v.st, rl = (st.rain || {}).level || 0, rn = !!(st.rain || {}).now, off = r.k === "offline", href = linkFor ? linkFor(r.c) : "";
        var word = off && (st.out_of_service || []).length ? T("gauge_out") : T("verdict_" + r.k);
        var label = r.c.name + ": " + word + ". " + brief(st, r.k);
        return "<li>" + (href ? '<a class="cs-brow cs-wrow cs-b-' + r.k + '" href="' + esc(href) + '" aria-label="' + esc(label) + '">' : '<div class="cs-brow cs-wrow cs-b-' + r.k + '">') +
          '<i class="cs-bbar" style="background:' + COL[r.k] + '"></i>' +
          '<span class="cs-bname">' + esc(r.c.short || r.c.name) + "</span>" +
          '<span class="cs-bword cs-v-' + r.k + '">' + icon(r.k) + esc(word) + "</span>" +
          '<span class="cs-bwhy">' + review(r.c, true) + esc(brief(st, r.k)) + "</span>" +
          '<span class="cs-brain">' + (rl || rn ? chip(rl, rn) : '<span class="cs-dim">' + esc(T("rain_none")) + "</span>") + "</span>" +
          '<span class="cs-bsince">' + (st.since && !off ? "since " + esc(clock(st.since)) : "") + "</span>" +
          '<span class="cs-wgo" aria-hidden="true">' + (href ? "›" : "") + "</span>" + (href ? "</a>" : "</div>") + "</li>";
      }).join("") + "</ul>";
    }
    if (nq.length) h += '<div class="cs-bquiet"><b>' + esc(T("verdict_none")) + ":</b> " + nq.map(function (r) {
      var href = linkFor ? linkFor(r.c) : "";
      return href ? '<a href="' + esc(href) + '">' + esc(r.c.short || r.c.name) + "</a>" : esc(r.c.short || r.c.name);
    }).join(" · ") + "</div>";
    h += "</div>";
    if (groups.length) h += '<p class="cs-wdo"><b>What to do:</b> ' + esc(T("verdict_" + groups[0].k + "_todo")) + "</p>";   // for the worst status
    if (groups.some(function (g) { return g.k === "likely" || g.k === "ready"; })) {
      var u = T("url_evacuation");
      if (/^https:\/\//.test(u)) h += '<a class="cs-evac cs-evacb" href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(T("evac_button")) + " →</a>";
    }
    h += '<div class="cs-hmore">';
    h += '<p><a href="SiteMap.html">' + esc(T("home_map_link")) + " ›</a></p>";
    h += '<p class="cs-hsm">' + esc(T("home_updated", { time: clock(data.generated) })) + "</p></div></div>";
    return { banner: banner, html: h };
  }

  /* ---------- EOC kiosk (staff preview): a status board, one row per creek, worst first ---------- */
  // Short reasons, a few words each (staff wording: the Flood Watch / Warning level names are fine here)
  function brief(st, k) {
    if (k === "delayed") return "Data not updated";
    if ((st.out_of_service || []).length && k === "offline") return (st.out_of_service[0] || {}).note || T("why_out_of_service", { gauge: st.out_of_service[0].gauge });
    var out = [];
    (st.reasons || []).forEach(function (r) {
      var t = { why_warning: "At Flood Warning level", why_watch: "At Flood Watch level", why_monitoring: "Higher than usual",
        why_rising_fast: "Rising fast", why_normal_rain: "Normal level, rain could raise it", why_trigger: "Rain trigger met",
        why_trigger_tide: "Rain + high tide trigger met", why_gauge_offline: "Creek gauge offline", why_stale: "A rain gauge is silent",
        tide_rising_line: "Rising tide", why_rain: r.rain ? rainWord(r.rain) + " rain" : "" }[r.code] || "";
      if ((r.code === "why_watch" || r.code === "why_monitoring") && r.rising_fast) t += ", rising fast";
      if (t && out.indexOf(t) < 0) out.push(t);
    });
    if (!out.length && k === "offline") out.push("Creek gauge not reporting");
    var tr = (st.trend || {}).trend, words = { fast: "rising fast", rising: "rising", falling: "falling" };
    if (k !== "offline" && words[tr] && !out.some(function (x) { return /rising|falling/i.test(x); })) out.push("Creek " + words[tr]);
    if (!out.length && (st.rain || {}).level) out.push(rainWord(st.rain.level) + " rain");
    return out.slice(0, 2).join(" · ");
  }
  function board(data) {
    // When the data file is late, the board says so once and shows the last statuses, dimmed
    var late = false;
    var rows = allCreeks(data).map(function (c, i) {
      var v = view(data, c), k = v.key;
      if (k === "delayed") { late = true; k = (c.status || {}).key || "none"; v = Object.assign({}, v, { key: k, word: T("verdict_" + k), rank: RANK[k], color: COL[k] }); }
      return { c: c, v: v, k: k, i: i, dash: i < (data.creeks || []).length };
    });
    var act = rows.filter(function (x) { return x.k !== "none"; }).sort(function (a, b) { return b.v.rank - a.v.rank || a.i - b.i; });
    var quiet = rows.filter(function (x) { return x.k === "none"; });
    var h = '<div class="cs-board"><div class="cs-bhead"><b>Creeks</b><span>' + act.length + " with a status · " + quiet.length + " with no alerts · updated " + esc(clock(data.generated)) + "</span></div>" +
      (late ? '<div class="cs-blate">⚠ ' + esc(T("verdict_delayed", { time: clock(data.generated) })) + ". Showing each creek’s status at that time.</div>" : "");
    if (act.length) h += '<div class="cs-bcols" aria-hidden="true"><i></i><span>' + esc(T("board_col_creek")) + "</span><span>" + esc(T("board_col_status")) + "</span><span>" +
      esc(T("board_col_why")) + "</span><span>" + esc(T("board_col_rain")) + '</span><span class="cs-bsince">' + esc(T("board_col_since")) + "</span></div>";
    if (!act.length) h += '<div class="cs-bnone">' + esc(T("summary_none")) + "</div>";
    else h += '<div class="cs-brows' + (late ? " cs-dimmed" : "") + '">' + act.map(function (x, n) {
      var st = x.v.st, rl = (st.rain || {}).level || 0, rn = !!(st.rain || {}).now, off = x.k === "offline";
      var r = '<div class="cs-brow cs-b-' + x.k + '"' + ' data-creek="' + esc(x.c.id) + '"'  + '><i class="cs-bbar" style="background:' + COL[x.k] + '"></i>' +
        '<span class="cs-bname">' + esc(x.c.short || x.c.name) + "</span>" +
        '<span class="cs-bword cs-v-' + x.k + '">' + icon(x.k) + esc(x.k === "offline" && (st.out_of_service || []).length ? T("gauge_out") : T("verdict_" + x.k)) + "</span>" +
        '<span class="cs-bwhy">' + review(x.c, true) + esc(brief(st, x.k)) + "</span>" +   // the tag goes with the reason: the name column is narrow
        '<span class="cs-brain">' + (rl || rn ? chip(rl, rn) : '<span class="cs-dim">' + esc(T("rain_none")) + "</span>") + "</span>" +
        '<span class="cs-bsince">' + (st.since && !off ? "since " + esc(clock(st.since)) : "") + "</span></div>";
      if (n === 0 && x.v.eoc) r += '<div class="cs-beoc"><b>EOC:</b> ' + esc(x.v.eoc) + "</div>";
      return r;
    }).join("") + "</div>";
    if (quiet.length) h += '<div class="cs-bquiet"><b>' + esc(T("verdict_none")) + ":</b> " + quiet.map(function (x) { return '<span data-creek="' + esc(x.c.id) + '">' + esc(x.c.short || x.c.name) + "</span>"; }).join(" · ") + "</div>";
    return h + "</div>";
  }

  var css = [
    ".cs-review{display:inline-block;margin-left:6px;padding:1px 8px;border:1.5px solid #5b6877;border-radius:999px;font-size:11.5px;font-weight:700;line-height:1.5;" +
    "color:#3d4957;background:rgba(138,150,163,.12);vertical-align:middle;white-space:nowrap;letter-spacing:0;text-transform:none}",
    "@media (prefers-color-scheme:dark){.cs-review{color:#c3ccd6;border-color:#9aa8b8}}:root[data-theme=dark] .cs-review{color:#c3ccd6;border-color:#9aa8b8}",
    ".cs-badge{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.03em;background:#003B5C;color:#fff;border-radius:6px;padding:3px 8px;margin:4px 0 8px}",
    ".cs-banner{background:#c62828;color:#fff;border-radius:10px;padding:12px 14px;font-size:17px;font-weight:700;line-height:1.4;margin:0 0 10px}",
    ".cs-glance{background:var(--card,var(--panel,#fff));border:1px solid var(--line,#d5dae1);border-radius:10px;padding:12px 14px;margin:0 0 12px}",
    ".cs-main{margin:0;font-size:18px;font-weight:700;line-height:1.4;color:var(--ink,#16202b)}",
    ".cs-sub{margin:8px 0 0;font-size:13px;line-height:1.45;color:var(--muted,#556274)}",
    ".cs-evac{display:inline-flex;align-items:center;margin-top:10px;min-height:44px;padding:8px 14px;border-radius:8px;background:#0A5587;color:#fff!important;text-decoration:none;font-weight:700}",
    ".cs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px;margin:0 0 12px}",
    ".cs-card{background:var(--card,var(--panel,#fff));border:1px solid var(--line,#d5dae1);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;color:var(--text,var(--ink,#16202b))}",
    ".cs-card.cs-likely{border:4px solid #c62828}.cs-card.cs-ready{border:4px solid #e07b00}.cs-card.cs-alert{border:4px solid #e6c200}",
    ".cs-card.cs-offline,.cs-card.cs-delayed{border:2px dashed #8a96a3}",
    ".cs-head{padding:12px 14px 8px}.cs-head h3{margin:0;font-size:19px;color:var(--ink,#16202b)}",
    ".cs-verdict{margin:0 14px;padding:9px 12px;border-radius:8px;display:flex;align-items:center;gap:10px;font-size:19px;font-weight:700;color:var(--ink,#16202b)}",
    ".cs-ic{width:20px;height:20px;flex:none;display:block}",
    ".cs-lvi{display:inline-block;vertical-align:-3px;margin-right:4px}.cs-lvi .cs-ic{width:16px;height:16px}.cs-lvi .cs-ic-likely .x{stroke:#fff;fill:#fff}",
    ".cs-ic-likely{color:#c62828}.cs-ic-ready{color:#b45a00}.cs-ic-alert{color:#7a6400}.cs-ic-none{color:#6b7682}",
    "span.cs-ic-nodata{width:14px;height:14px;margin:3px;border:2px dashed #6b7682;border-radius:3px;box-sizing:border-box}",
    ".cs-v-likely{background:#c62828;color:#fff}.cs-v-likely .cs-ic-likely{color:#fff}",
    ".cs-ic-likely .x{stroke:#fff;fill:#fff}.cs-v-likely .cs-ic-likely .x{stroke:#c62828;fill:#c62828}",   // the "!" shows on a red triangle and on a white one
    ".cs-v-ready{background:" + TINT.ready + "}",
    ".cs-v-alert{background:" + TINT.alert + "}",
    ".cs-v-none,.cs-v-offline,.cs-v-delayed{background:" + TINT.none + ";font-size:17px;font-weight:600}",
    "@media (prefers-color-scheme:dark){.cs-ic-ready{color:#ffa94d}.cs-ic-alert{color:#f2d544}.cs-ic-none{color:#9aa8b8}span.cs-ic-nodata{border-color:#9aa8b8}.cs-v-likely .cs-ic-likely{color:#fff}}",
    ".cs-why{margin:8px 14px 0;font-size:14.5px;line-height:1.45;color:var(--text,var(--ink))}",
    ".cs-body{padding:8px 14px 10px}.cs-body p{margin:0 0 4px;font-size:15px;line-height:1.45}",
    ".cs-danger{font-weight:700;color:#c62828}@media (prefers-color-scheme:dark){.cs-danger{color:#f47c79}}",
    ".cs-details{margin:0 14px;border-top:1px solid var(--line,#eceff3)}.cs-rainrow{margin-bottom:6px}.cs-stages .cs-band:last-child,.cs-stages .cs-row:last-child{border-bottom:0}",
    // Cards side by side line up section by section: status, What to do, creek level, rain, numbers, footer
    "@supports (grid-template-rows:subgrid){.cs-grid>.cs-card{display:grid;grid-row:span 7;grid-template-rows:subgrid;row-gap:0}.cs-grid>.cs-card>.cs-stages{align-self:start}" +
      ".cs-grid>.cs-card.cs-brief{grid-row:span 4}.cs-grid>.cs-brief>.cs-factw{align-self:start}}",   // brief cards: name, status, facts, link
    ".cs-row{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line,#eceff3);font-size:14px}",
    ".cs-nolvl{margin:8px 0 2px;padding:8px 10px;border:1px dashed var(--muted,#8a96a3);border-radius:8px;font-size:13.5px;line-height:1.4;color:var(--text,#22303f);" +
    "background:repeating-linear-gradient(135deg,transparent 0 6px,rgba(138,150,163,.10) 6px 12px)}.cs-nolvl b{display:block;color:var(--ink,#003B5C)}",
    ".cs-row:last-child{border-bottom:0}.cs-lbl{color:var(--muted,#556274)}.cs-val{font-weight:600;text-align:right}",
    ".cs-dim{color:var(--muted,#556274);font-weight:400}.cs-sm{display:block;font-size:12px;color:var(--muted,#556274)}",
    ".cs-band{padding:8px 0 9px;border-bottom:1px solid var(--line,#eceff3)}",
    ".cs-bt{display:flex;justify-content:space-between;gap:8px;font-size:14px;margin-bottom:7px;flex-wrap:wrap}.cs-now{font-weight:600}",
    ".cs-track{position:relative;display:flex;gap:2px;height:12px}.cs-s{height:100%;background:rgba(138,150,163,.25)}",
    ".cs-s:first-child{border-radius:6px 0 0 6px}.cs-s:last-of-type{border-radius:0 6px 6px 0}",
    ".cs-mark{position:absolute;top:-5px;width:4px;height:22px;margin-left:-2px;background:var(--ink,#16202b);border-radius:2px;box-shadow:0 0 0 2px var(--card,var(--panel,#fff))}",
    ".cs-ticks{display:flex;font-size:12px;color:var(--muted,#556274);margin-top:5px}.cs-ticks span{text-align:center}.cs-ticks .on{color:var(--ink,#16202b);font-weight:700}",
    ".cs-chip{display:inline-flex;align-items:center;gap:7px;border-radius:6px;padding:2px 9px;font-weight:700;color:var(--ink,#16202b)}",
    ".cs-chip.heavy{background:" + TINT.alert + "}.cs-chip.vheavy{background:" + TINT.ready + "}.cs-chip.severe{background:rgba(198,40,40,.16)}",
    ".cs-meter{display:inline-flex;gap:2px;align-items:flex-end}.cs-meter i{display:block;width:5px;border-radius:2px;background:rgba(127,127,127,.3)}",
    ".cs-meter i:nth-child(1){height:7px}.cs-meter i:nth-child(2){height:11px}.cs-meter i:nth-child(3){height:15px}",
    ".cs-chip.heavy .on{background:#a07c00}.cs-chip.vheavy .on{background:#e07b00}.cs-chip.severe .on{background:#c62828}",
    ".cs-norain{font-weight:500}.cs-chip.raining{background:rgba(10,85,135,.12)}",
    ".cs-row.cs-fc{display:block}.cs-fc .cs-val{display:block;text-align:left;margin-top:3px}.cs-fc .cs-sm{font-weight:400;margin-top:3px}",
    ".cs-fcbox{margin:10px 0 4px;padding:2px 12px;border:1px solid var(--line,#d5dae1);border-radius:10px;background:var(--card,var(--panel,#fff))}",
    ".cs-bcols{display:grid;grid-template-columns:8px 130px 150px 1fr 110px 84px;gap:0 10px;padding:3px 10px 3px 0;font-size:11.5px;font-weight:700;letter-spacing:.05em;" +
    "text-transform:uppercase;color:var(--muted,#556274);border-bottom:1px solid var(--line,#e3e8ee)}.cs-bcols .cs-bsince{font-size:inherit;color:inherit}",
    ".cs-foot{margin-top:auto;padding:8px 14px;border-top:1px solid var(--line,#e3e7ec);font-size:12.5px;color:var(--muted,#556274);display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}",
    ".cs-foot a{font-weight:600}",
    ".cs-quiet,.cs-staff{margin:4px 0 14px}.cs-quiet>summary,.cs-staff>summary{cursor:pointer;font-weight:600;min-height:40px;display:flex;align-items:center;color:var(--ink,#16202b)}",
    ".cs-tw{overflow-x:auto;background:var(--card,var(--panel,#fff));border:1px solid var(--line,#d5dae1);border-radius:10px}",
    ".cs-tbl{border-collapse:collapse;min-width:980px;width:100%;font-size:13px}.cs-tbl th{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted,#556274);padding:8px 10px;border-bottom:1px solid var(--line,#d5dae1)}",
    ".cs-tbl td{padding:8px 10px;border-bottom:1px solid var(--line,#eceff3);vertical-align:top}",
    ".cs-tag{display:inline-flex;align-items:center;gap:6px;font-weight:700;white-space:nowrap}.cs-tag i{width:11px;height:11px;border-radius:3px;display:inline-block}",
    ".cs-tile{background:var(--card,var(--panel,#fff));border-radius:8px;border:3px solid #8a96a3;padding:6px 10px;display:flex;flex-direction:column;gap:4px;overflow:hidden}",
    ".cs-tile.cs-likely{border-color:#c62828}.cs-tile.cs-ready{border-color:#e07b00}.cs-tile.cs-alert{border-color:#e6c200}.cs-tile.cs-none{border-color:rgba(138,150,163,.5)}",
    ".cs-tile.cs-offline,.cs-tile.cs-delayed{border-style:dashed}",
    ".cs-tn{font-size:17px;font-weight:700;color:var(--ink,#16202b)}.cs-tile .cs-verdict{margin:0;font-size:20px;padding:4px 10px}.cs-tile .cs-chip{padding:0 7px}",
    ".cs-tr{font-size:14.5px;line-height:1.3;color:var(--ink,#16202b)}.cs-tm{font-size:13px;margin-top:auto}",
    ".cs-ts{font-size:12.5px;color:var(--muted,#556274)}",
    ".cs-since{margin:6px 14px 0;font-size:13px;color:var(--muted,#556274)}",
    ".cs-glance .cs-main+.cs-main{margin-top:4px}.cs-late{color:var(--muted,#556274)!important;font-size:15px!important}",
    ".cs-num{margin:0 14px 10px}.cs-num>summary,.cs-how>summary{cursor:pointer;font-weight:600;font-size:14px;min-height:36px;display:flex;align-items:center;color:var(--ink,#16202b)}",
    ".cs-how{background:var(--card,var(--panel,#fff));border:1px solid var(--line,#d5dae1);border-radius:10px;padding:2px 14px;margin:0 0 12px}",
    ".cs-howb ul{list-style:none;margin:4px 0 8px;padding:0}.cs-howb li{display:flex;gap:8px;align-items:flex-start;margin:0 0 6px;font-size:14.5px}",
    ".cs-howb li .cs-ic{margin-top:1px}",
    ".cs-howb p{font-size:14px;line-height:1.45;margin:0 0 8px;color:var(--text,var(--ink))}",
    // home page (staff preview): status boxes with the color all the way around, creeks first, what to do at the bottom
    ".cs-home{display:flex;flex-direction:column;gap:12px;margin:0 0 6px}",
    ".cs-hg{background:var(--card,var(--panel,#fff));border-radius:12px;overflow:hidden;padding:12px 0 0;color:var(--text,var(--ink,#16202b))}",
    ".cs-hg-likely{border:4px solid #c62828}.cs-hg-ready{border:4px solid #e07b00}.cs-hg-alert{border:4px solid #e6c200}.cs-hg-none{border:2px solid #2e7d32;padding-bottom:12px}",
    ".cs-hg-likely{background:color-mix(in srgb,#c62828 4%,var(--card,#fff))}.cs-hg-ready{background:color-mix(in srgb,#e07b00 4%,var(--card,#fff))}.cs-hg-alert{background:color-mix(in srgb,#e6c200 6%,var(--card,#fff))}",
    ".cs-hg-none .cs-verdict{background:rgba(46,125,50,.1)}.cs-hg-none .cs-ic-none{color:#2e7d32}",
    ".cs-glance .cs-calm{margin:6px 0 0;font-size:15.5px;line-height:1.45;color:var(--ink,#16202b)}.cs-glance .cs-caveat{font-size:14.5px;color:var(--text,#22303f)}",
    ".cs-glance .cs-asof{font-weight:600}.cs-new{margin:10px 0 0;font-size:15px}.cs-new a{font-weight:700;color:var(--link,#0A5587);text-underline-offset:3px}",
    ".cs-qh{font-size:17px;margin:16px 2px 8px;color:var(--ink,#16202b)}",
    ".cs-quiet>summary::before,.cs-how>summary::before{content:'\\25B8';display:inline-block;width:1.1em;transition:transform .15s}.cs-quiet[open]>summary::before,.cs-how[open]>summary::before{transform:rotate(90deg)}",
    ".cs-how>summary{font-size:15px}.cs-quiet>summary,.cs-how>summary,.cs-num>summary{list-style:none}.cs-quiet>summary::-webkit-details-marker,.cs-how>summary::-webkit-details-marker{display:none}",
    ".cs-how>summary:focus-visible,.cs-quiet>summary:focus-visible,.cs-new a:focus-visible,.cs-more a:focus-visible{outline:3px solid #1e6fd9;outline-offset:2px}",
    ".cs-facts{margin:0;padding:6px 14px 10px;display:grid;gap:6px}.cs-facts>div{display:flex;justify-content:space-between;gap:12px;align-items:baseline;border-top:1px solid var(--line,#e3e7ec);padding-top:6px}",
    ".cs-facts .nw{white-space:nowrap}.cs-facts dt{font-size:14px;color:var(--muted,#556274)}.cs-facts dd{margin:0;font-size:15px;font-weight:600;text-align:right;color:var(--ink,#16202b)}",
    ".cs-more{justify-content:flex-start;margin-top:auto}.cs-more a,.cs-foot a{font-size:15px;font-weight:700;min-height:44px;display:inline-flex;align-items:center;gap:6px;color:var(--link,#0A5587)}",
    ".cs-howb .cs-ic-none{color:#2e7d32}",
    ".cs-howb h4{margin:12px 0 4px;font-size:15px;color:var(--ink,#16202b)}.cs-howlv{padding-left:18px}.cs-howlv li{list-style:disc}",
    ".cs-card .cs-v-none{background:rgba(46,125,50,.1)}.cs-card .cs-ic-none{color:#2e7d32}",   // creek cards: No alerts in green with a check, like the home page
    "@media (prefers-color-scheme:dark){.cs-card .cs-ic-none,.cs-hg-none .cs-ic-none{color:#66bb6a}}",
    ".cs-hrows{list-style:none;margin:0;padding:4px 14px 0}.cs-hrows li+li{border-top:1px solid var(--line,#e3e8ee)}",
    ".cs-hrow{display:flex;align-items:center;gap:10px;padding:9px 0;min-height:44px;text-decoration:none;color:inherit}",
    ".cs-hdown{margin:0;padding:9px 14px 0;font-size:15px;font-weight:700;color:var(--ink,#16202b)}.cs-hg-none .cs-hdown{border-top:1px solid var(--line,#e3e8ee);margin-top:9px}.cs-hscope{margin:0;padding:7px 14px 0;font-size:14px;line-height:1.4;color:var(--muted,#556274)}",
    ".cs-hx{flex:1;display:flex;flex-direction:column;gap:1px}.cs-hx .cs-review{align-self:flex-start;margin:2px 0}.cs-bwhy .cs-review{margin:0 6px 0 0;font-size:11px}.cs-hn{font-weight:700;font-size:16px;color:var(--ink,#16202b)}",
    ".cs-hy{font-size:14px;line-height:1.35;color:var(--text,var(--ink,#16202b))}.cs-hc{color:var(--muted,#556274);font-size:20px;flex:none}",
    "a.cs-hrow:focus-visible{outline:3px solid #1e6fd9;outline-offset:2px;border-radius:4px}",
    ".cs-hdo{margin:0;padding:9px 14px 11px;font-size:14px;line-height:1.4;border-top:1px solid var(--line,#e3e8ee)}",
    ".cs-hdo-l{display:block;font-size:11.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--muted,#556274);margin-bottom:1px}",
    ".cs-evacb{justify-content:center;margin-top:0}",
    ".cs-hlate{padding:8px 12px;background:#fff3cd;color:#5c4a00;font-weight:700;font-size:14px;border-radius:8px}",
    ".cs-hmore{background:var(--card,var(--panel,#fff));border:1px solid var(--line,#d5dae1);border-radius:12px;padding:4px 14px}",
    ".cs-hmore p{margin:8px 0;font-size:14px;line-height:1.45}.cs-hmore a{font-weight:600}.cs-hsm{font-size:12.5px!important;color:var(--muted,#556274)}",
    // EOC kiosk board (staff preview)
    ".cs-board{flex:1;min-height:0;display:flex;flex-direction:column;background:var(--panel,var(--card,#fff));border-radius:8px;overflow:hidden;border:1px solid var(--line,#d5dae1)}",
    ".cs-bhead{display:flex;justify-content:space-between;align-items:baseline;padding:6px 12px;background:#003B5C;color:#fff;font-size:13px}.cs-bhead b{font-size:17px}",
    ".cs-brows{flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden}.cs-dimmed .cs-brow{opacity:.75}",
    ".cs-brow{display:grid;grid-template-columns:8px 130px 150px 1fr 110px 84px;align-items:center;gap:0 10px;min-height:36px;flex:none;padding:0 10px 0 0;border-bottom:1px solid var(--line,#e3e8ee);font-size:14px;cursor:default}",
    ".cs-brow[data-creek]{cursor:pointer}.cs-bbar{align-self:stretch}",
    ".cs-bname{font-weight:700;color:var(--ink,#16202b);font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    ".cs-bword{display:inline-flex;align-items:center;font-weight:700;margin:0;padding:3px 8px;border-radius:6px;font-size:14px;gap:6px;justify-self:start;white-space:nowrap}.cs-bword .cs-ic{width:16px;height:16px}",
    ".cs-bwhy{font-size:14px;line-height:1.25;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;padding:3px 0;color:var(--ink,#16202b)}",
    ".cs-brain{font-size:13px;white-space:nowrap}.cs-brain .cs-chip{padding:0 7px;font-size:13px}",
    ".cs-bsince{font-size:12px;color:var(--muted,#556274);white-space:nowrap;text-align:right}",
    ".cs-b-likely{background:rgba(198,40,40,.06)}",
    ".cs-beoc{padding:5px 12px 5px 28px;font-size:13px;background:rgba(198,40,40,.06);border-bottom:1px solid var(--line,#e3e8ee)}",
    ".cs-blate{padding:6px 12px;background:#fff3cd;color:#5c4a00;font-weight:700;font-size:14px}",
    ".cs-bquiet{margin-top:auto;padding:7px 12px;font-size:13.5px;color:var(--ink,#16202b);border-top:1px solid var(--line,#e3e8ee)}",
    ".cs-bnone{flex:1;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;color:var(--ink,#16202b)}",
    ".cs-changed{font-size:13.5px;margin:6px 0 8px}",
    // the kiosk board on the home page: rows are links; on a phone each row folds to name + status, then why, then rain
    ".cs-wboard{flex:none;margin:0 0 10px}.cs-wrows{list-style:none;margin:0;padding:0}",
    ".cs-wcols,.cs-wrow{grid-template-columns:8px 130px 160px 1fr 110px 84px 14px}",
    "a.cs-wrow{color:inherit;text-decoration:none;min-height:44px;cursor:pointer}a.cs-wrow:hover{background:rgba(10,85,135,.05)}",
    "a.cs-wrow:focus-visible{outline:3px solid #1e6fd9;outline-offset:-3px}.cs-wgo{font-size:20px;color:var(--muted,#556274);text-align:right}",
    ".cs-wrow .cs-bwhy{-webkit-line-clamp:3}",
    ".cs-wnone{display:flex;align-items:center;gap:10px;padding:16px 14px 6px;font-size:18px;font-weight:700;color:var(--ink,#16202b)}",
    ".cs-wscope{margin:0;padding:0 14px 14px;font-size:14px;line-height:1.45;color:var(--muted,#556274)}",
    ".cs-wboard .cs-bquiet a{font-weight:600}.cs-wdo{margin:0 0 10px;font-size:14.5px;line-height:1.45}",
    "@media (max-width:640px){.cs-wcols{display:none}.cs-bhead{flex-wrap:wrap;gap:2px 10px}" +
    ".cs-wrow{grid-template-columns:8px 1fr auto 14px;grid-template-areas:'b n w g' 'b y y g' 'b r s g';row-gap:3px;padding:7px 10px 7px 0}" +
    ".cs-wrow .cs-bbar{grid-area:b}.cs-wrow .cs-bname{grid-area:n;white-space:normal}.cs-wrow .cs-bword{grid-area:w}" +
    ".cs-wrow .cs-bwhy{grid-area:y;padding:0}.cs-wrow .cs-brain{grid-area:r}.cs-wrow .cs-bsince{grid-area:s}.cs-wrow .cs-wgo{grid-area:g;align-self:center}}"
  ].join("\n");
  var styleEl = document.createElement("style"); styleEl.textContent = css; document.head.appendChild(styleEl);

  /* Kiosk: the dashboard creeks always, plus any preview creek that isn't quiet (worst first), up to `max` tiles */
  function kiosk(data, max) {
    var dash = (data.creeks || []).map(function (c) { return { c: c, v: view(data, c) }; });
    var extra = (data.creeks_preview || []).map(function (c) { return { c: c, v: view(data, c) }; })
      .filter(function (x) { return x.v.key !== "none"; }).sort(function (a, b) { return b.v.rank - a.v.rank; });
    var show = dash.concat(extra).slice(0, max), hidden = dash.concat(extra).length - show.length;
    var quiet = (data.creeks_preview || []).filter(function (c) { return view(data, c).key === "none"; });
    return { tiles: show.map(function (x) { return tile(data, x.c); }),
      note: [hidden ? "+" + hidden + " more with a status (see the Creeks page)" : "",
        quiet.length ? T("verdict_none") + ": " + list(quiet.map(function (c) { return c.short || c.name; })) : ""].filter(Boolean).join(" · ") };
  }

  window.CREEK_STATUS = { staff: STAFF, review: review, kiosk: kiosk, view: view, card: card, summary: summary, page: page, staffTable: staffTable, tile: tile, badge: badge, icon: icon, home: home, board: board, plain: plain, brief: brief, forecast: forecastRow };
  Object.defineProperty(window.CREEK_STATUS, "preview", { get: shown });   // true when the status layer shows on this page
})();
