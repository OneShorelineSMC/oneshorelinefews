/* FEWS shared lookups: reads the staff-maintained files in lookups/ for every page.
 *
 *   lookups/settings.csv       numbers the pages use (rapidly-rising rule, offline timing, NOAA forecast rules, ...)
 *   lookups/tide_stations.csv  NOAA tide stations and their MHHW (ft NAVD88)
 *   lookups/display_text.csv   wording shown on the pages (disclaimer, SMC Alert note, status words, contact info, ...)
 *
 * Creeks, gauges and thresholds (lookups/creeks.csv, creek_gauges.csv, thresholds.csv) reach the pages through the
 * data job's creeks.json instead.
 *
 * Load this file just before a page's own script. It works right away with the built-in values below (the
 * fallback if a file can't be read), then reads the CSV files and calls each page's LOOKUPS.onChange handler.
 * A value that is missing or doesn't make sense keeps its built-in value and is listed in LOOKUPS.problems.
 * Everything from the files is shown as plain text (never as HTML), and links must be https:// addresses.
 */
(function () {
  "use strict";
  var BASE = "lookups/";
  var RELOAD_MIN = 30;   // pick up edits without restarting the kiosk

  // Built-in values: used only until (or if) the CSV files can't be read. Edit the CSV files, not these.
  // [value, smallest allowed, largest allowed]
  var SETTINGS = {
    RISE_FT: [0.5, 0.05, 10], RISE_MINUTES: [60, 5, 720], RISE_FRESH_MIN: [90, 5, 720],
    RISE_TIDAL_RAIN_IN: [0.10, 0, 5], RISE_TIDAL_RAIN_HOURS: [3, 0.25, 48], RISE_ETA_HOURS: [3, 0.25, 48],
    GAUGE_QUIET_HOURS: [12, 0.5, 168], GAUGE_QUIET_HOURS_INTERVAL: [3, 0.25, 168], CREEK_DATA_LATE_MIN: [30, 5, 1440],
    SITE_QUIET_HOURS: [24, 1, 336], SITE_OLD_READING_HOURS: [3, 0.25, 168], SITE_DATA_LATE_MIN: [45, 5, 1440],
    MODEL_MAX_AGE_HOURS: [12, 1, 72], MODEL_MIN_AHEAD_HOURS: [6, 0, 72],
    OFFSET_RECENT_HIGHS: [4, 1, 14], OFFSET_NOTE_FT: [0.2, 0.01, 5], OFFSET_HIGH_FT: [0.5, 0.01, 10],
    // creek status layer (the data job uses the same ranges, scripts/creek_signals.py)
    RAIN_SEVERE_CONFIRM_GAUGES: [2, 1, 5], RAIN_SILENT_MIN: [60, 15, 720], TREND_WINDOW_MIN: [30, 5, 240], TREND_MAX_WINDOW_MIN: [120, 15, 360], TREND_STEADY_FT_PER_HR: [0.1, 0.01, 2], TIDE_RISING_LOOKAHEAD_HOURS: [3, 0.5, 12], BE_READY_FROM_RAIN: [1, 0, 1],
    // flood reports (scripts/fetch_community_flood_reports.py, CommunityFloodReports.html, SiteMap.html)
    SF_FORECAST_NOTE_FT: [0.25, 0.05, 3], SF_FORECAST_HOURS: [48, 6, 72],
    MORE_CREEKS_PUBLIC: [1, 0, 1],
    REPORTS_PUBLIC: [0, 0, 1], REPORTS_MAX_AGE_DAYS: [180, 1, 730], REPORTS_MAX_PHOTOS: [40, 0, 200]
  };
  var TIDES = {
    "9414523": { id: "9414523", name: "Redwood City", mhhw: 7.02 },
    "9414750": { id: "9414750", name: "Alameda", mhhw: 6.37 }
  };
  var TEXT = {
    e911: "In an emergency, call 911.",
    e911_note: "This site shows conditions; no one is watching it to send help.",
    disclaimer: "Data provided for informational purposes only; OneShoreline is not liable for data errors or mis-interpretation of data by users of this site. Thresholds shown are approximate and will be updated as more information about the hydrologic response of the watershed is gleaned from the monitoring data. Actual flood conditions may vary based on channel blockages, sensor errors, or other complications.",
    disclaimer_short: "For informational purposes only; thresholds are approximate.",
    disclaimer_short_map: "For informational purposes only; data are provisional and thresholds are approximate.",
    smc_alert_intro: "Sign up for SMC Alert to get emergency alerts for San Mateo County by text, email or phone.",
    smc_alert_note: "This site does not send alerts. SMC Alert messages are sent by San Mateo County officials and are not set off by the creek, rain or tide readings shown here, so a high reading on this site does not mean an alert has gone out.",
    tide_causes: "Storms, onshore wind, heavy runoff and El Niño conditions can all raise the Bay above the tide table.",
    mhhw_definition_home: "“Average high tide” is Mean Higher High Water (MHHW): the average of each day’s highest tide at the NOAA tide gauge in {station}, {mhhw} ft NAVD88. Tides above it reach farther onto low shorelines, marshes and trails. Based on NOAA tide measurements, the height NOAA expects with the weather (about 2 days ahead) and the tide table.",
    mhhw_definition: "MHHW (Mean Higher High Water) is the average height of the highest tide each day. Tides above it reach farther up shorelines, marshes and low-lying areas than usual.",
    noaa_forecast_note: "Expected with weather: NOAA's San Francisco Bay model (SFBOFS) works out the water level at this gauge including wind, air pressure and river flow, about 2 days ahead, 4 times a day. It is model guidance, not an official forecast; NWS advisories take precedence.",
    predicted_tide_note: "The tide table is the normal tide from the moon and sun, worked out years ahead by NOAA. It doesn't include storm surge, wind or runoff.",
    king_tide_source: "King Tide dates from San Mateo County Emergency Management, “Tide days of concern, Oct 2026 to Apr 2027.” They come from the tide table for NOAA’s San Francisco gauge (9414290) and don’t include weather. Redwood City tides usually run higher than San Francisco, and storms, wind and runoff can add more, so check the Redwood City card and NWS alerts for what to expect.",
    status_normal: "Normal", status_rain_trigger: "Rain trigger", status_rain_trigger_long: "Flooding likely (rain)",
    status_offline: "Offline", status_offline_long: "Gauge offline", status_delayed: "Data delayed", status_delayed_short: "Delayed",
    contact_org: "OneShoreline", contact_district: "San Mateo County Flood and Sea Level Rise Resiliency District",
    contact_phone: "(650) 844-8310", contact_email: "info@oneshoreline.org", contact_website: "oneshoreline.org",
    contact_address_1: "1700 S. El Camino Real, Suite 502", contact_address_2: "San Mateo, CA 94402",
    url_website: "https://www.oneshoreline.org", url_contact: "https://www.oneshoreline.org/contact-oneshoreline",
    url_smc_alert: "https://www.smcgov.org/dem/smc-alert",
    // Creek status layer (staff preview; THRESHOLDS_BASIS.md §10). {words} are filled in by the pages.
    verdict_likely: "Flooding likely",
    verdict_likely_todo: "Move away from the creek and low areas now. Follow instructions from local officials.",
    verdict_ready: "Be ready",
    verdict_ready_todo: "Stay away from the creek. Be ready to move to higher ground if local officials tell you to.",
    verdict_alert: "Stay alert",
    verdict_alert_todo: "Avoid creek banks, low spots and flooded streets. Check back often.",
    verdict_none: "No alerts",
    verdict_none_todo: "Nothing unusual right now. Conditions can change quickly during storms.",
    verdict_nodata_todo: "Check local conditions and official alerts.",
    why_warning: "The creek is at its Flood Warning level.",
    why_watch: "The creek is at its Flood Watch level.",
    why_monitoring: "The creek is higher than usual.",
    why_normal_rain: "The creek is normal now, but {rain} rain could make it rise quickly.",
    why_rising_fast: "The creek is rising fast.",
    why_rain: "{Rain} rain in this creek's area.",
    why_stale: "Our rain gauge for this creek hasn\u2019t reported since {time}.",
    why_sanmateo: "Crystal Springs Reservoir holds back much of this water.",
    tide_rising_line: "Rising tide: water near the Bay drains slowly until about {time}.",
    rain_heavy: "Heavy",
    rain_vheavy: "Very heavy",
    rain_severe: "Intense",
    trend_fast: "Rising fast",
    trend_rising: "Rising",
    trend_steady: "Steady",
    trend_falling: "Falling",
    summary_likely: "Flooding likely at {creeks}.",
    summary_ready: "Be ready near {creeks}.",
    summary_alert: "Stay alert near {creeks}.",
    summary_alert_many: "Stay alert near {n} other creeks.",
    summary_none: "No creek alerts right now.",
    summary_none_area: "No creek alerts near {area} right now.",
    banner_likely: "Flooding is likely at {creeks}. If you are in danger, call 911.",
    evac_button: "See if your area has an evacuation order",
    url_evacuation: "https://protect.genasys.com/",
    tide_words: "Tide table and expected height. The tide table is the normal tide from the moon and sun, worked out years ahead. The expected height adds today's wind, storms and runoff, from NOAA's model, about 2 days ahead.",
    lbl_tide_table: "Tide table",
    lbl_expected: "Expected with weather",
    sf_fcst_higher: "Expected {fcst} ft with the weather, {diff} ft above the tide table",
    sf_fcst_lower: "Expected {fcst} ft with the weather, {diff} ft below the tide table",
    sf_fcst_reaches: "Expected {fcst} ft at San Francisco with the weather, {diff} ft above the tide table (not a County King Tide day)",
    sf_fcst_chip: "HIGHER THAN TIDE TABLE",
    sf_fcst_source: "Expected heights: NOAA's San Francisco Bay model (SFBOFS) at the San Francisco gauge (9414290), ft MLLW like the County's dates, about 2 days ahead, including wind, storms and runoff. Model guidance, not an official forecast; NWS advisories take precedence. The County's King Tide and Elevated days don't change.",
    more_creeks_title: "More creeks · readings only",
    more_creeks_intro: "Readings from gauges on other San Mateo County creeks. Flood levels for these creeks haven't been set yet, so no status is shown. Tap a creek for its graphs.",
    more_creeks_badge: "Readings only",
    more_creeks_note: "Flood levels for this creek haven't been set yet, so these are readings only, with no status. A higher or rising level doesn't by itself mean flooding. In an emergency, call 911.",
    no_flood_level_title: "Flood levels not set yet",
    no_flood_level: "OneShoreline is still setting flood levels for this creek. Until then, its status is based on rain in the hills above and how fast the creek is rising, shown below.",
    limited_rain: "Rain gauges may miss storms here",
    nws_separate: "This page shows creek conditions measured by OneShoreline. It is separate from National Weather Service alerts \u2014 follow whichever is more serious.",
    why_trigger: "Rain has reached this creek's flooding trigger.",
    why_trigger_tide: "Rain and a high tide have reached this creek's flooding trigger.",
    why_gauge_offline: "The creek gauge isn't reporting, so this status comes from the rain.",
    rain_none: "Light or none",
    verdict_offline: "Not reporting",
    verdict_delayed: "Not updated since {time}",
    since_line: "Since {time}",
    was_line: "before that: {status}",
    numbers_title: "See the numbers",
    howto_title: "How to read this page",
    howto_likely: "Flooding likely: move away from the creek and low areas now.",
    howto_ready: "Be ready: the creek could flood. Be ready to move to higher ground.",
    howto_alert: "Stay alert: conditions are getting worse. Avoid creek banks and check back often.",
    howto_none: "No alerts: nothing unusual right now. Conditions can change quickly in a storm.",
    howto_band: "The bar shows where the creek is between its normal level and its flood level, measured at a creek gauge. The marker is the latest reading.",
    howto_rain: "Rain is compared with how often that much rain falls at the same gauge: Heavy (about once a year), Very heavy (about once every two years), Intense (about once every five years).",
    eoc_action_likely: "",
    eoc_action_ready: "",
    eoc_action_alert: "",
    changed_title: "Changed in the last hour",
    staff_legend: "Rain levels: Heavy = at least a 1-year storm for some duration at that gauge, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14). Storm size and chance in any year are for the heaviest window. Supporting = a hillside gauge that counts toward the creek's rain level but isn't in its rain tables. Trigger = a rain (and tide) rule in thresholds.csv.",
    creek_level_at: "Creek level at {place}",
    creek_level_word: "Creek level",
    rain_row: "Rain",
    // Flood reports (CommunityFloodReports.html, SiteMap.html). url_report_form blank = reporting not open yet.
    report_title: "Report flooding",
    report_911: "If anyone is in danger, or water is coming into a home, call 911. This form doesn't send help.",
    report_intro: "Tell OneShoreline where you see flooding: water over a street or path, a creek or the Bay over its banks, or a road closed by water. Staff use reports to learn where and when flooding happens.",
    report_what_happens: "OneShoreline staff read every report. They may add it to the flood reports map with a short description and an approximate location (about a block). Your name, contact details and your own words are never shown on the map. A photo is shown only if staff choose to.",
    report_timing: "Staff review reports during working hours, so a report may take a day or more to appear on the map.",
    report_records: "Reports, including photos, are kept by OneShoreline and may be public records under the California Public Records Act. Leave out anything you don't want shared, such as faces, license plates or house numbers.",
    report_safety: "Don't walk or drive into floodwater to report it or take a photo.",
    report_not_open: "Flood reporting isn't open yet. In an emergency, call 911.",
    report_open_tab: "Open the form in a new tab",
    url_report_form: "",
    report_map_note: "Reports from the public, reviewed by OneShoreline staff. Locations are approximate (about a block). Reports aren't monitored; in an emergency, call 911.",
    report_none: "No reviewed flood reports in the past {days} days.",
    report_seen: "Seen {time}",
    report_type_street: "Water on a street or path",
    report_type_building: "Water in or against a building",
    report_type_road_closed: "Road closed by water",
    report_type_creek: "Creek over its banks",
    report_type_shoreline: "Bay or ocean over the shoreline",
    report_type_other: "Other flooding",
    report_depth_shallow: "Less than ankle-deep",
    report_depth_ankle_knee: "Ankle- to knee-deep",
    report_depth_above_knee: "Above the knee",
    report_depth_unknown: "Depth not given"
  };

  var cur = { settings: {}, tides: {}, text: {} }, handlers = [], L;
  function reset() {
    cur.settings = {}; Object.keys(SETTINGS).forEach(function (k) { cur.settings[k] = SETTINGS[k][0]; });
    cur.tides = {}; Object.keys(TIDES).forEach(function (k) { cur.tides[k] = { id: k, name: TIDES[k].name, mhhw: TIDES[k].mhhw }; });
    cur.text = {}; Object.keys(TEXT).forEach(function (k) { cur.text[k] = TEXT[k]; });
  }

  // CSV with quoted fields (as Excel and Google Sheets save it) -> array of objects keyed by lower-case header
  function parseCSV(s) {
    s = String(s).replace(/^﻿/, "");
    var rows = [], row = [], f = "", q = false;
    for (var i = 0; i < s.length; i++) {
      var ch = s[i];
      if (q) { if (ch === '"') { if (s[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += ch; }
      else if (ch === '"') q = true;
      else if (ch === ",") { row.push(f); f = ""; }
      else if (ch === "\n" || ch === "\r") { if (ch === "\r" && s[i + 1] === "\n") i++; row.push(f); rows.push(row); row = []; f = ""; }
      else f += ch;
    }
    if (f !== "" || row.length) { row.push(f); rows.push(row); }
    var head = (rows.shift() || []).map(function (h) { return h.trim().toLowerCase(); }), out = [];
    rows.forEach(function (r, n) {
      if (!r.some(function (x) { return x.trim() !== ""; })) return;
      var o = { _row: n + 2 }; head.forEach(function (h, j) { o[h] = (r[j] || "").trim(); }); out.push(o);
    });
    return out;
  }
  function safeURL(u) { return /^https:\/\/[^\s"'<>]+$/i.test(u) ? u : null; }

  function apply(files) {
    var problems = [];
    reset();
    if (files.settings) files.settings.forEach(function (r) {
      var k = r.key, d = SETTINGS[k], v = parseFloat(r.value);
      if (!d) { if (k) problems.push("settings.csv row " + r._row + ": unknown key " + k); return; }
      if (!/^-?\d+(\.\d+)?$/.test(r.value) || v < d[1] || v > d[2]) { problems.push("settings.csv row " + r._row + ": " + k + " must be a number from " + d[1] + " to " + d[2]); return; }
      cur.settings[k] = v;
    });
    if (files.tides) files.tides.forEach(function (r) {
      var v = parseFloat(r.mhhw_navd88_ft);
      if (!/^\d{7}$/.test(r.station) || !/^-?\d+(\.\d+)?$/.test(r.mhhw_navd88_ft) || v < -5 || v > 20) { problems.push("tide_stations.csv row " + r._row + ": station or mhhw_navd88_ft not valid"); return; }
      cur.tides[r.station] = { id: r.station, name: r.name || r.station, mhhw: v };
    });
    if (files.text) files.text.forEach(function (r) {
      var k = r.key;
      if (!(k in TEXT)) { if (k) problems.push("display_text.csv row " + r._row + ": unknown key " + k); return; }
      if (!r.text && !/^eoc_action_|^url_report_form$/.test(k)) { problems.push("display_text.csv row " + r._row + ": " + k + " is empty"); return; }   // EOC steps and the report form link may be blank
      if (/^url_/.test(k) && r.text && !safeURL(r.text)) { problems.push("display_text.csv row " + r._row + ": " + k + " must start with https://"); return; }
      cur.text[k] = r.text;
    });
    L.problems = problems;
    if (problems.length && window.console) console.warn("FEWS lookups: " + problems.join("; "));
  }

  function fill(root) {   // elements marked in the page's HTML
    root = root || document;
    Array.prototype.forEach.call(root.querySelectorAll("[data-text]"), function (el) {
      var s = L.text(el.getAttribute("data-text")), m = el.hasAttribute("data-lead") && /^(.+?[.!?])(\s+[\s\S]*)$/.exec(s);
      if (!m) { el.textContent = s; return; }
      var b = document.createElement("b"); b.textContent = m[1];   // first sentence in bold
      el.textContent = ""; el.appendChild(b); el.appendChild(document.createTextNode(m[2]));
    });
    Array.prototype.forEach.call(root.querySelectorAll("[data-href]"), function (el) {
      var u = safeURL(L.text(el.getAttribute("data-href"))); if (u) el.setAttribute("href", u);
    });
    Array.prototype.forEach.call(root.querySelectorAll("[data-tel]"), function (el) { el.setAttribute("href", L.tel()); });
    Array.prototype.forEach.call(root.querySelectorAll("[data-mailto]"), function (el) {
      var e = L.text("contact_email"); if (/^[^\s@"'<>]+@[^\s@"'<>]+$/.test(e)) el.setAttribute("href", "mailto:" + e);
    });
  }

  function get(name) {
    var v = Math.floor(Date.now() / 600000);   // GitHub Pages caches for 10 minutes; so do we
    return fetch(BASE + name + "?v=" + v, { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(name + " " + r.status); return r.text(); })
      .then(parseCSV);
  }
  function load() {
    var files = {}, failed = [];
    function one(key, name) { return get(name).then(function (rows) { files[key] = rows; }, function () { failed.push(name); }); }
    return Promise.all([one("settings", "settings.csv"), one("tides", "tide_stations.csv"), one("text", "display_text.csv")]).then(function () {
      apply(files);
      if (failed.length) L.problems.unshift("couldn't read " + failed.join(", ") + " (using built-in values)");
      L.loaded = !failed.length;
      fill();
      handlers.forEach(function (fn) { try { fn(); } catch (e) { if (window.console) console.error(e); } });
    });
  }

  L = window.LOOKUPS = {
    problems: [], loaded: false,
    num: function (k) { return k in cur.settings ? cur.settings[k] : NaN; },
    station: function (id) { return cur.tides[id] || { id: id, name: id, mhhw: null }; },
    mhhw: function (id) { return (cur.tides[id] || {}).mhhw; },
    // Plain text with {name} filled in; callers escape it before putting it in HTML (or use textContent)
    text: function (k, vars) {
      var s = k in cur.text ? cur.text[k] : "";
      return vars ? s.replace(/\{(\w+)\}/g, function (m, n) { return n in vars ? String(vars[n]) : m; }) : s;
    },
    tel: function () { var d = L.text("contact_phone").replace(/\D/g, ""); return d.length === 10 ? "tel:+1" + d : d.length === 11 && d[0] === "1" ? "tel:+" + d : "tel:+16508448310"; },
    onChange: function (fn) { handlers.push(fn); },
    fill: fill,
    ready: null
  };
  reset();
  if (document.readyState !== "loading") fill(); else document.addEventListener("DOMContentLoaded", function () { fill(); });
  fill();
  L.ready = load();
  setInterval(load, RELOAD_MIN * 60000);
})();
