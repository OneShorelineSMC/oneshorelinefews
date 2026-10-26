/* One severity scale for the home page (staff, 2026-10-26): the colors (design tokens), how local conditions map onto
 * the National Weather Service scale, the "never more severe than NWS" rule, and the order of the page's sections.
 * Works in the browser (window.SEVERITY) and in node (require), so scripts/test_home.js can test it.
 *
 *   level      meaning                                                   look
 *   warning    NWS Warning; a creek at its measured Flood Warning level   red; the only level with a full saturated fill
 *   advisory   NWS Advisory; local "flooding likely in low areas"        orange / amber
 *   watch      NWS Watch, or higher than usual with no flooding expected  yellow
 *   normal     no hazard                                                 white card, check mark
 *   offline    out of service, no data                                   gray, dashed square, muted text
 *   info       information only, never an alert state                     blue
 *
 * Contrast (WCAG 2.1 AA), checked by scripts/test_home.js on every run:
 *   hero fill / its text   warning #b71c1c / #ffffff 6.57   advisory #f0a030 / #1a1a1a 8.10   watch #ffc94a / #1a1a1a 11.36
 *   text on white card     warning #b71c1c 6.57 · advisory #a84300 6.06 · watch #5c4400 9.20 · normal #2e7d32 5.13 ·
 *                          offline #56657a 5.94 · info #1565c0 5.75
 *   badge text on its tint warning 5.74 · advisory 5.40 · watch 8.46 · normal 4.56 · offline 5.24 · info 4.96
 *   left stripe on white   warning #c62828 5.62 · advisory #c05000 4.78 · watch #9c7c00 3.96 · normal #2e7d32 5.13 ·
 *                          offline #66717d 4.97 · info #1565c0 5.75 (UI parts need 3:1)
 *   dark mode (card #18202a): the same checks, all pass (see the test)
 */
(function (root) {
  "use strict";
  var RANK = { offline: 0, info: 0, normal: 1, watch: 2, advisory: 3, warning: 4 };
  var LEVELS = ["warning", "advisory", "watch", "normal", "offline", "info"];
  var CARD = { light: "#ffffff", dark: "#18202a" };
  var TOKENS = {
    light: {
      warning:  { fill: "#b71c1c", on: "#ffffff", stripe: "#c62828", ink: "#b71c1c", tint: "#fdecea" },
      advisory: { fill: "#f0a030", on: "#1a1a1a", stripe: "#c05000", ink: "#a84300", tint: "#fff0db" },
      watch:    { fill: "#ffc94a", on: "#1a1a1a", stripe: "#9c7c00", ink: "#5c4400", tint: "#fff6cc" },
      normal:   { fill: "#ffffff", on: "#22303f", stripe: "#2e7d32", ink: "#2e7d32", tint: "#e8f5e9" },
      offline:  { fill: "#ffffff", on: "#22303f", stripe: "#66717d", ink: "#56657a", tint: "#eef1f4" },
      info:     { fill: "#ffffff", on: "#22303f", stripe: "#1565c0", ink: "#1565c0", tint: "#e3f0fc" }
    },
    dark: {
      warning:  { fill: "#b71c1c", on: "#ffffff", stripe: "#ef5350", ink: "#ff8a80", tint: "#3a1f22" },
      advisory: { fill: "#f0a030", on: "#1a1a1a", stripe: "#f0a030", ink: "#f5b335", tint: "#3a2a12" },
      watch:    { fill: "#ffc94a", on: "#1a1a1a", stripe: "#e6c200", ink: "#ffd75e", tint: "#37321a" },
      normal:   { fill: "#18202a", on: "#dbe3ec", stripe: "#66bb6a", ink: "#81c784", tint: "#1d3324" },
      offline:  { fill: "#18202a", on: "#dbe3ec", stripe: "#7d8a99", ink: "#9aa8b8", tint: "#252f3b" },
      info:     { fill: "#18202a", on: "#dbe3ec", stripe: "#4ea3f0", ink: "#90caf9", tint: "#1b2d44" }
    }
  };
  // Only warning, advisory and watch are ever a saturated fill, and only on the hero
  var FILLED = { warning: true, advisory: true, watch: true };

  /* Icons, so no level relies on color alone (WCAG 1.4.1): triangle with "!" (warning), circle with "!" (advisory),
     eye (watch), check (normal), dashed square (offline), "i" (info). Decoration only: always next to words. */
  var ICON = {
    warning: '<path d="M10 2.2 19 17.8H1Z" fill="currentColor"/><path d="M10 7.5v4.6" stroke="var(--sv-glyph,#fff)" stroke-width="2.2" stroke-linecap="round"/><circle cx="10" cy="14.9" r="1.25" fill="var(--sv-glyph,#fff)"/>',
    advisory: '<circle cx="10" cy="10" r="8.6" fill="currentColor"/><path d="M10 5.4v5.5" stroke="var(--sv-glyph,#fff)" stroke-width="2.2" stroke-linecap="round"/><circle cx="10" cy="14" r="1.3" fill="var(--sv-glyph,#fff)"/>',
    watch: '<path d="M1.3 10C3.6 6 6.6 4.2 10 4.2S16.4 6 18.7 10C16.4 14 13.4 15.8 10 15.8S3.6 14 1.3 10Z" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="10" cy="10" r="3" fill="currentColor"/>',
    normal: '<path d="M4.2 10.4 8.3 14.4 15.8 6.2" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>',
    offline: '<rect x="3" y="3" width="14" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.8" stroke-dasharray="3 2.4"/>',
    info: '<circle cx="10" cy="10" r="8.6" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M10 9v5.4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="10" cy="6" r="1.3" fill="currentColor"/>'
  };
  function icon(level) {
    var k = ICON[level] ? level : "info";
    return '<svg class="sv-ic" viewBox="0 0 20 20" width="20" height="20" aria-hidden="true" focusable="false">' + ICON[k] + "</svg>";
  }

  /* CSS from the tokens: --sv-<level>-<part> custom properties (light, then dark), and the classes every part of the
     page uses: .sv-hero (the one saturated fill), .sv-card (white card with the level's left stripe), .sv-badge (icon +
     word on the level's tint), .sv-ink (the level's text color). */
  function vars(mode) {
    var t = TOKENS[mode], out = [];
    LEVELS.forEach(function (l) { Object.keys(t[l]).forEach(function (p) { out.push("--sv-" + l + "-" + p + ":" + t[l][p]); }); });
    return out.join(";");
  }
  function css() {
    var r = [":root{" + vars("light") + "}",
      "@media (prefers-color-scheme:dark){:root:not([data-theme=light]){" + vars("dark") + "}}",
      ":root[data-theme=dark]{" + vars("dark") + "}",
      ".sv-ic{flex:none;width:1.2em;height:1.2em;vertical-align:-.22em}"];
    LEVELS.forEach(function (l) {
      var v = function (p) { return "var(--sv-" + l + "-" + p + ")"; };
      if (FILLED[l]) r.push(".sv-hero.sv-" + l + "{background:" + v("fill") + ";color:" + v("on") + ";border-color:" + v("fill") + "}" +
        ".sv-hero.sv-" + l + " .sv-ic{color:" + v("on") + ";--sv-glyph:" + v("fill") + "}");
      else r.push(".sv-hero.sv-" + l + "{border-left:6px solid " + v("stripe") + "}.sv-hero.sv-" + l + " .sv-ic{color:" + v("ink") + "}");
      r.push(".sv-card.sv-" + l + "{border-left:6px solid " + v("stripe") + "}");
      r.push(".sv-badge.sv-" + l + "{background:" + v("tint") + ";color:" + v("ink") + "}.sv-badge.sv-" + l + " .sv-ic{--sv-glyph:" + v("tint") + "}");
      r.push(".sv-ink.sv-" + l + ",.sv-" + l + " .sv-ink{color:" + v("ink") + "}");
    });
    return r.join("\n");
  }
  function inject(doc) {
    doc = doc || (typeof document !== "undefined" ? document : null);
    if (!doc || doc.getElementById("sv-css")) return;
    var s = doc.createElement("style"); s.id = "sv-css"; s.textContent = css(); doc.head.appendChild(s);
  }

  /* National Weather Service products: their level and which hazard they are about */
  function nwsLevel(event) {
    var e = String(event || "");
    if (/warning|emergency/i.test(e)) return "warning";
    if (/advisory/i.test(e)) return "advisory";
    if (/watch/i.test(e)) return "watch";
    return hazardOf(e) === "other" ? "info" : "watch";   // a Coastal Flood Statement or Flood Statement: watch for its hazard
  }
  function hazardOf(event) {
    var e = String(event || "");
    if (/coastal flood|storm surge|tidal/i.test(e)) return "tide";   // the Bay and ocean shoreline
    if (/flood/i.test(e)) return "creek";                            // Flood Watch / Warning / Advisory, Flash Flood …
    return "other";
  }
  function higher(a, b) { return a == null ? b : b == null ? a : RANK[b] > RANK[a] ? b : a; }
  // The highest level among the active products for one hazard ("tide" or "creek"), or null when none is active
  function nwsFor(list, hazard) {
    var lv = null;
    (list || []).forEach(function (p) { if (hazardOf(p.event) === hazard) lv = higher(lv, nwsLevel(p.event)); });
    return lv;
  }
  /* Local severity never shows more severe than the active NWS product for the same hazard, unless measured data says
     flooding is happening (observed). With no NWS product for that hazard, the local level stands on its own. */
  function cap(local, nws, observed) {
    if (observed || nws == null || RANK[local] <= RANK[nws]) return local;
    return RANK[nws] >= RANK.watch ? nws : "watch";
  }
  // A creek's status (creeks.json, scripts/creek_signals.py) on this scale
  function creekLevel(key) {
    return { likely: "warning", ready: "advisory", alert: "watch", none: "normal", offline: "offline", delayed: "offline" }[key] || "offline";
  }

  /* The page's condition sections in order: any with an active condition (watch or higher) first, the more severe first;
     a tie keeps the default order (tides before creeks); then the rest in the default order.
     sections: [{ id, level }] in the default order. Returns the ids. */
  function order(sections) {
    var act = sections.map(function (s, i) { return { id: s.id, r: RANK[s.level] || 0, i: i }; });
    var on = act.filter(function (s) { return s.r >= RANK.watch; }).sort(function (a, b) { return b.r - a.r || a.i - b.i; });
    var off = act.filter(function (s) { return s.r < RANK.watch; });
    return on.concat(off).map(function (s) { return s.id; });
  }
  function top(levels) { return levels.reduce(function (a, l) { return higher(a, l); }, null) || "normal"; }

  /* A time window in the page's words: "10:30 AM–3 PM", "now until 3 PM" once it has started. clock(ms) gives "10:30 AM". */
  function windowText(start, end, now, clock) {
    var a = clock(start), b = clock(end);
    if (start <= now) return "now until " + b;
    return (a.slice(-2) === b.slice(-2) ? a.slice(0, -3) : a) + "–" + b;
  }

  /* WCAG 2.1 contrast ratio of two #rrggbb colors */
  function lum(h) {
    var c = [1, 3, 5].map(function (i) { var x = parseInt(h.substr(i, 2), 16) / 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function contrast(a, b) { var x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }

  var API = { RANK: RANK, LEVELS: LEVELS, TOKENS: TOKENS, CARD: CARD, FILLED: FILLED, icon: icon, css: css, inject: inject,
    nwsLevel: nwsLevel, hazardOf: hazardOf, nwsFor: nwsFor, cap: cap, creekLevel: creekLevel, order: order, top: top,
    higher: higher, windowText: windowText, contrast: contrast };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  else root.SEVERITY = API;
})(typeof window !== "undefined" ? window : this);
