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
    OFFSET_RECENT_HIGHS: [4, 1, 14], OFFSET_NOTE_FT: [0.2, 0.01, 5], OFFSET_HIGH_FT: [0.5, 0.01, 10]
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
    tide_causes: "Storms, onshore wind, heavy runoff and El Niño conditions can all raise the Bay above the predicted tide.",
    mhhw_definition_home: "“Average high tide” is Mean Higher High Water (MHHW): the average of each day’s highest tide at the NOAA tide gauge in {station}, {mhhw} ft NAVD88. Tides above it reach farther onto low shorelines, marshes and trails. Based on NOAA tide measurements, NOAA’s model forecast and the predicted (astronomical) tide.",
    mhhw_definition: "MHHW (Mean Higher High Water) is the average height of the highest tide each day. Tides above it reach farther up shorelines, marshes and low-lying areas than usual.",
    noaa_forecast_note: "NOAA forecast is model guidance from NOAA's San Francisco Bay Operational Forecast System: the water level at this gauge including wind, air pressure and river flow, about 2 days ahead, updated 4 times a day. It is not an official forecast; NWS advisories take precedence.",
    predicted_tide_note: "Predicted tides come from NOAA and don't include storm surge, wind or runoff.",
    king_tide_source: "King Tide dates from San Mateo County Emergency Management, “Tide days of concern, Oct 2026 to Apr 2027.” They are astronomical tide predictions for NOAA’s San Francisco gauge (9414290) and don’t include weather. Redwood City tides usually run higher than San Francisco, and storms, wind and runoff can add more, so check the Redwood City predictions and NWS alerts for the actual forecast.",
    status_normal: "Normal", status_rain_trigger: "Rain trigger", status_rain_trigger_long: "Flooding likely (rain)",
    status_offline: "Offline", status_offline_long: "Gauge offline", status_delayed: "Data delayed", status_delayed_short: "Delayed",
    contact_org: "OneShoreline", contact_district: "San Mateo County Flood and Sea Level Rise Resiliency District",
    contact_phone: "(650) 844-8310", contact_email: "info@oneshoreline.org", contact_website: "oneshoreline.org",
    contact_address_1: "1700 S. El Camino Real, Suite 502", contact_address_2: "San Mateo, CA 94402",
    url_website: "https://www.oneshoreline.org", url_contact: "https://www.oneshoreline.org/contact-oneshoreline",
    url_smc_alert: "https://www.smcgov.org/dem/smc-alert"
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
      if (!r.text) { problems.push("display_text.csv row " + r._row + ": " + k + " is empty"); return; }
      if (/^url_/.test(k) && !safeURL(r.text)) { problems.push("display_text.csv row " + r._row + ": " + k + " must start with https://"); return; }
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
