/* High water banner, on every page but Tides (which has its own tide banner) and the kiosk (which says it in its strip).
 * When NOAA's projection, or else the tide table, puts the Bay at Redwood City (9414523) at or above the flood level
 * (TIDE_RED_FT_RWC in settings.csv) today or tomorrow, a red bar under the National Weather Service bar says so and links
 * to Bayside Tides. Only red: higher-than-usual tides and "possible flood level if the Bay stays high" days are left to
 * the Tides page. Needs lookups.js and tide_season.js (loaded before this file). Staff, 2026-10-23.
 */
(function () {
  "use strict";
  var T = window.TIDE_SEASON, LK = window.LOOKUPS;
  if (!T || !LK) return;
  var MATCH_MIN = 90, el = null;

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }

  function place() {
    if (el) return el;
    var css = document.createElement("style");
    css.textContent =
      "#tideBan{display:flex;align-items:center;gap:10px;padding:10px 16px;background:#c62828;color:#fff;text-decoration:none;flex:none}" +
      "#tideBan[hidden]{display:none}#tideBan .ti{font-size:20px;line-height:1}#tideBan .tx{flex:1;min-width:0;line-height:1.35}" +
      "#tideBan b{font-size:16px}#tideBan .sub{display:block;font-size:13.5px;opacity:.95}" +
      "#tideBan .go{font-size:24px;line-height:1}" +
      "#tideBan:focus-visible{outline:3px solid #fff;outline-offset:-5px}";
    document.head.appendChild(css);
    el = document.createElement("a");
    el.id = "tideBan"; el.hidden = true; el.setAttribute("role", "status");
    el.href = "Tides.html" + (/[?&]preview=1\b/.test(location.search) ? "?preview=1" : "");
    // right under the National Weather Service bar (and its list), or under the page header where there is no bar
    var after = document.getElementById("alertList") || document.getElementById("alert") || document.querySelector("header");
    if (after && after.parentNode) after.parentNode.insertBefore(el, after.nextSibling);
    else document.body.insertBefore(el, document.body.firstChild);
    return el;
  }

  /* The first high tide today or tomorrow at or above the flood level that hasn't passed: {t, v, src} or null */
  function highWater(now) {
    var ex = T.expected(now), dh = T.dayHighs();
    for (var n = 0; n < 2; n++) {
      var d = T.iso(now + n * 86400000), x = ex[d], h = dh[d];
      if (x && T.level(x.v) === 2 && x.t >= now - MATCH_MIN * 60000) return { t: x.t, v: x.v, src: "projection", day: n };
      if (!x && h && T.level(h.v) === 2 && h.t >= now - MATCH_MIN * 60000) return { t: h.t, v: h.v, src: "table", day: n };
    }
    return null;
  }

  function render() {
    if (!T.state.highs) return;
    var b = place(), now = T.now(), hw = highWater(now);
    if (!hw) { b.hidden = true; return; }
    var day = hw.day === 0 ? "Today" : "Tomorrow";
    // Short for the public: what, when, what to do. The heights are one tap away on Bayside Tides.
    b.innerHTML = '<span class="ti" aria-hidden="true">⚠</span><span class="tx"><b>' + esc(LK.text("tide_head_red")) +
      " along the Bay shoreline</b>" + '<span class="sub">' + esc(day) + " about " + esc(T.clock(hw.t)) +
      ". Stay away from the shoreline and low roads near the Bay.</span></span>" +
      '<span class="go" aria-hidden="true">›</span>';
    b.setAttribute("aria-label", LK.text("tide_head_red") + " along the Bay shoreline, " + day + " about " + T.clock(hw.t) +
      " (peak " + hw.v.toFixed(1) + " ft, flood level " + T.red().toFixed(1) + " ft). Open Bayside Tides.");
    b.hidden = false;
  }

  T.onUpdate(render);
  (LK.ready || Promise.resolve()).then(function () {
    T.loadTable();                                  // shared: a page that already loads it (Shoreline) isn't asked twice
    setTimeout(function () { if (!T.state.ofs) T.loadModel(); }, 3000);
    setInterval(T.loadModel, 30 * 60000);
    setInterval(T.loadTable, 12 * 3600000);
    setInterval(render, 5 * 60000);                 // the time passes: a tide that has gone by drops off
    render();
  });
})();
