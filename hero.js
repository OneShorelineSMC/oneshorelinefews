/* The one alert at the top of the home, Creeks and Tides pages, and its pieces for the kiosk (staff, 2026-10-26).
 * National Weather Service products, the Bay tide at the flood level and the creeks in one card. Same rules and words on
 * every page: built here once. Needs lookups.js and severity.js (and creek_status.js for the creek line); load after them.
 *
 *   HERO.loadNWS(cb)             National Weather Service alerts for San Mateo County: cb(list) or cb(null, true) on failure
 *   HERO.loadBay(cb)             NOAA Redwood City: measured, the projection and the tide table (pages without their own)
 *   HERO.tideState(o)            a tide gauge's state from its series: level, flood window ("now until 3:30 PM"), words
 *   HERO.tideCard(st, name)      a tide card's {cls, html, label} (home page cards, Tides page card)
 *   HERO.creeks(data, nws)       the creeks' line for the card (creek_status.js home)
 *   HERO.render(el, s)           draws the card: s = { nws, nwsFailed, bay, creeks, creekLink }
 *   HERO.strip(s)                the kiosk's one-line version: { level, text, sub }
 */
(function () {
  "use strict";
  var LK = window.LOOKUPS, SV = window.SEVERITY;
  var COUNTY_SAME = "006081";
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function unwrap(t) { return String(t || "").replace(/-\s*\n\s*(?=[a-z])/g, "-").replace(/\s*\n\s*/g, " ").replace(/\s{2,}/g, " ").trim(); }
  function labelCase(s) { return s.toLowerCase().replace(/\b[a-z]/g, function (c) { return c.toUpperCase(); }); }
  function parseLocal(s) { var a = String(s).split(/[- :]/).map(Number); return Date.UTC(a[0], a[1] - 1, a[2], a[3], a[4] || 0); }
  function nowLocal() {
    var p = {}; new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", hourCycle: "h23", year: "numeric",
      month: "numeric", day: "numeric", hour: "numeric", minute: "numeric" }).formatToParts(new Date())
      .forEach(function (x) { p[x.type] = +x.value; });
    return Date.UTC(p.year, p.month - 1, p.day, p.hour % 24, p.minute);
  }
  function fmt(ms, o) { return new Date(ms).toLocaleString("en-US", Object.assign({ timeZone: "UTC" }, o)); }
  function fTime(ms) { return fmt(ms, { hour: "numeric", minute: "2-digit" }); }
  function dayStart(ms) { var d = new Date(ms); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()); }
  function ymd(ms) { var d = new Date(ms); return d.getUTCFullYear() + String(d.getUTCMonth() + 1).padStart(2, "0") + String(d.getUTCDate()).padStart(2, "0"); }
  function untilText(iso) {
    return iso ? "until " + new Date(iso).toLocaleString("en-US", { timeZone: "America/Los_Angeles", weekday: "short", hour: "numeric", minute: "2-digit" }) : "until further notice";
  }
  function nwsUntil(p) { return untilText(p.ends || p.expires); }
  function getJSON(url, accept) {
    return fetch(url, { cache: "no-store", headers: accept ? { Accept: accept } : {} }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }
  function hasPreview() { return /[?&]preview=1\b/.test(location.search) ? "?preview=1" : ""; }

  /* ---------- the card's look (shared by the pages) ---------- */
  function injectCSS() {
    if (document.getElementById("hero-css")) return;
    SV.inject();
    var s = document.createElement("style"); s.id = "hero-css";
    s.textContent = [
      ".hero{border-radius:12px;padding:13px 16px 12px;margin:0 0 6px;background:var(--card,#fff);color:var(--text,#22303f);box-shadow:0 1px 4px rgba(0,0,0,.08)}",
      ".hero .hh{display:flex;gap:10px;align-items:flex-start}.hero .hh .sv-ic{width:26px;height:26px;margin-top:1px}",
      ".hero h2{margin:0;font-size:20px;line-height:1.25;color:inherit}",
      ".hero p{margin:6px 0 0;font-size:15.5px;line-height:1.4}.hero .act{font-weight:700}.hero .src,.hero .also{font-size:14px}",
      ".hero a{color:inherit;font-weight:700}",
      // compact (the Creeks page when the Bay tide leads): one narrow bar, the time window and a link to the Tides page
      ".hero.hcompact .hh{align-items:center;gap:8px}.hero.hcompact .hh .sv-ic{width:20px;height:20px;margin-top:0}",
      ".hero.hcompact h2{font-size:15.5px;font-weight:700}.hero.hcompact h2 a{white-space:nowrap;margin-left:4px}.hero.hcompact .hmore p{margin:3px 0 0;font-size:13.5px}",
      ".hero details{margin-top:8px;font-size:14px}.hero summary{cursor:pointer;font-weight:700;min-height:32px;display:flex;align-items:center;list-style:none}",
      ".hero summary::-webkit-details-marker{display:none}.hero summary::before{content:'▸';margin-right:6px}.hero details[open]>summary::before{content:'▾'}",
      ".hero summary:focus-visible{outline:3px solid currentColor;outline-offset:2px;border-radius:4px}",
      ".hero .nwsfull{background:var(--card,#fff);color:var(--text,#22303f);border-radius:8px;padding:2px 12px;margin-top:6px}.hero .nwsfull a{color:var(--link,#0A5587)}",
      ".hero .al h3{margin:0;font-size:18px;color:var(--ink,#003B5C)}.hero .al .when{font-size:13.5px;color:var(--muted,#56657a);margin:1px 0 8px}",
      ".hero .al dl{display:grid;grid-template-columns:5.6em 1fr;gap:4px 10px;margin:0;font-size:15px}.hero .al dt{font-weight:700;color:var(--ink,#003B5C)}.hero .al dd{margin:0}",
      ".hero .al p{margin:6px 0 0;font-size:15px}.hero .al{padding:10px 0;border-bottom:1px solid var(--line,#e3e8ee);font-size:14px}.hero .al:last-child{border-bottom:0}",
      ".hero .al details summary{color:var(--muted,#56657a);font-weight:400}",
      // tide cards (home and Tides pages): a white card with the level's stripe and an icon + word label
      ".tcard2{display:block;position:relative;text-decoration:none;color:inherit;background:var(--card,#fff);border:1px solid var(--line,#e3e8ee);border-radius:12px;padding:9px 28px 9px 12px;box-shadow:0 1px 4px rgba(0,0,0,.07)}",
      ".tcard2.sv-card{border-left-width:6px}a.tcard2:hover,a.tcard2:focus-visible{box-shadow:0 0 0 2px var(--brand,#0A5587),0 1px 4px rgba(0,0,0,.07)}",
      ".tcard2 .sd{display:block;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted,#56657a)}",
      ".tcard2 .th{display:block;font-size:16px;font-weight:700;line-height:1.3;color:var(--ink,#003B5C)}",
      ".tcard2 .lv{display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:700;border-radius:6px;padding:1px 8px 1px 6px;margin:3px 0 1px}.tcard2 .lv .sv-ic{width:15px;height:15px}",
      ".tcard2 .t2{display:block;font-size:13.5px;color:var(--muted,#56657a);margin-top:3px}",
      ".tcard2 .go2{position:absolute;right:10px;top:50%;transform:translateY(-50%);font-size:22px;color:var(--muted,#56657a)}"
    ].join("\n");
    document.head.appendChild(s);
  }

  /* ---------- National Weather Service ---------- */
  var ORDER = { warning: 0, watch: 1, advisory: 2, statement: 3 };
  function classify(e) { return /warning|emergency/i.test(e) ? "warning" : /watch/i.test(e) ? "watch" : /advisory/i.test(e) ? "advisory" : "statement"; }
  function loadNWS(cb) {
    getJSON("https://api.weather.gov/alerts/active?area=CA", "application/geo+json").then(function (d) {
      cb((d.features || []).map(function (f) { return f.properties; }).filter(function (p) {
        return ((p.geocode && p.geocode.SAME) || []).some(function (s) { return String(s).slice(-6) === COUNTY_SAME; }) &&
          p.status === "Actual" && p.messageType !== "Cancel";
      }).sort(function (a, b) { return ORDER[classify(a.event)] - ORDER[classify(b.event)] || new Date(b.sent) - new Date(a.sent); }), false);
    }).catch(function () { cb(null, true); });
  }
  function alertBody(p) {   // "* WHAT...", "* WHERE..." sections as a list; anything else under "More details"
    var rows = "", extra = "";
    String(p.description || "").split(/\n\s*\n/).forEach(function (b) {
      b.split(/(?=^\*\s+[A-Z][A-Z /&-]+\.\.\.)/m).forEach(function (part) {
        part = part.trim(); if (!part) return;
        var m = part.match(/^\*\s+([A-Z][A-Z /&-]+?)\.\.\.([\s\S]*)$/);
        if (m) rows += "<dt>" + esc(labelCase(m[1])) + "</dt><dd>" + esc(unwrap(m[2])) + "</dd>";
        else extra += "<p>" + esc(unwrap(part).replace(/^\.\.\.|\.\.\.$/g, "")) + "</p>";
      });
    });
    var h = rows ? "<dl>" + rows + "</dl>" : extra;
    if (p.instruction) h += "<p><b>What to do:</b> " + esc(unwrap(p.instruction)) + "</p>";
    if (rows && extra) h += "<details><summary>More details</summary>" + extra + "</details>";
    return h;
  }
  function nwsWhat(p) {   // the "* WHAT..." part of the description: NWS's own plain words for what is expected
    var m = /\*\s*WHAT\.\.\.([\s\S]*?)(?=\n\s*\n|\n\*|$)/.exec(String(p.description || ""));
    return m ? unwrap(m[1]) : "";
  }

  /* ---------- tides ---------- */
  function noaaURL(station, product, b, e) {
    return "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?station=" + station + "&product=" + product + "&begin_date=" + b + "&end_date=" + e +
      "&datum=NAVD&time_zone=lst_ldt&units=english&format=json&application=OneShorelineFEWS";
  }
  function toPts(a) { return (a || []).map(function (x) { return { t: parseLocal(x.t), v: parseFloat(x.v) }; }).filter(function (x) { return !isNaN(x.v); }); }
  // NOAA Redwood City for the pages that don't download it themselves (the Creeks page): cb({ pred, obs, ofs })
  function loadBay(cb) {
    var now = nowLocal(), y = ymd(now - 864e5), t0 = ymd(now), t6 = ymd(now + 6 * 864e5), t3 = ymd(now + 3 * 864e5), D = { pred: null, obs: null, ofs: null };
    Promise.all([
      getJSON(noaaURL("9414523", "predictions", t0, t6)).then(function (j) { D.pred = toPts(j.predictions); }).catch(function () {}),
      getJSON(noaaURL("9414523", "water_level", y, t0)).then(function (j) { D.obs = toPts(j.data); }).catch(function () {}),
      getJSON(noaaURL("9414523", "ofs_water_level", y, t3)).then(function (j) { var p = toPts(j.data || j.predictions); D.ofs = p.length ? p : null; }).catch(function () {})
    ]).then(function () { cb(D); });
  }
  function findWindows(pts, lvl) {
    var out = [], cur = null;
    pts.forEach(function (p, i) {
      var prev = pts[i - 1];
      if (p.v > lvl) { if (!cur) cur = { start: prev ? prev.t + (lvl - prev.v) / (p.v - prev.v) * (p.t - prev.t) : p.t, peak: p.v, peakT: p.t, src: p.src };
        if (p.v > cur.peak) { cur.peak = p.v; cur.peakT = p.t; cur.src = p.src; } }
      else if (cur) { cur.end = prev.t + (lvl - prev.v) / (p.v - prev.v) * (p.t - prev.t); out.push(cur); cur = null; }
    });
    if (cur) { cur.end = pts[pts.length - 1].t; out.push(cur); }
    out.forEach(function (w) { w.start = Math.round(w.start / 60000) * 60000; w.end = Math.round(w.end / 60000) * 60000; });
    return out;
  }
  function clock(t) { return fTime(Math.round(t / 9e5) * 9e5).replace(":00", ""); }   // to the quarter hour: "1:15 PM", "3 PM"
  /* A tide gauge's state, the same everywhere (home cards, the card at the top, the Tides page, the kiosk).
     o = { D: {pred, obs, ofs}, mhhw, red (ft, or Infinity: no flood level), water ("Bay"), nws (alerts), days (7) }.
     Heights from one series: measured, then the NOAA projection (when it reaches MODEL_MIN_AHEAD_HOURS ahead), then the
     tide table. Flood window = the time at or above the flood level; flooding likely in low areas = advisory, never
     above the NWS coastal flood product unless the gauge measures the flood level now (severity.js cap). */
  function tideState(o) {
    var D = o.D || {}, now = o.now || nowLocal(), m = o.mhhw, red = o.red == null ? Infinity : o.red, days = o.days || 7;
    if (!D.pred || !D.pred.length) return { level: "offline", head: "Tide data unavailable right now", word: "No data", tech: [], more: 0 };
    var ser = [], tail = -Infinity;
    (D.obs || []).forEach(function (x) { ser.push({ t: x.t, v: x.v, src: "measured" }); tail = x.t; });
    if (D.ofs && D.ofs[D.ofs.length - 1].t >= now + LK.num("MODEL_MIN_AHEAD_HOURS") * 36e5) { D.ofs.forEach(function (x) { if (x.t > tail) ser.push({ t: x.t, v: x.v, src: "forecast" }); }); tail = Math.max(tail, D.ofs[D.ofs.length - 1].t); }
    D.pred.forEach(function (x) { if (x.t > tail) ser.push({ t: x.t, v: x.v, src: "predicted" }); });
    ser = ser.filter(function (x) { return x.t >= now - 12 * 36e5 && x.t <= dayStart(now) + days * 864e5; });
    var ups = findWindows(ser, m).filter(function (w) { return w.end > now; });
    var flood = isFinite(red) ? findWindows(ser, red).filter(function (w) { return w.end > now; }) : [];
    function dayWord(t) { var d = Math.round((dayStart(t) - dayStart(now)) / 864e5); return d === 0 ? "today" : d === 1 ? "tomorrow" : fmt(t, { weekday: "long" }); }
    function when(w) { return w.start <= now ? SV.windowText(w.start, w.end, now, clock) : dayWord(w.start) + ", " + SV.windowText(w.start, w.end, now, clock); }
    var st = { level: "normal", more: 0, tech: [], ups: ups, floods: flood }, water = o.water || "Bay";
    if (flood.length) {
      var last = D.obs && D.obs.length ? D.obs[D.obs.length - 1] : null, observed = !!(last && now - last.t < 36e5 && last.v >= red), f = flood[0];
      st.level = SV.cap("advisory", SV.nwsFor(o.nws || [], "tide"), observed);
      st.flood = f; st.when = when(f); st.peakT = f.peakT; st.peakClock = clock(f.peakT); st.started = f.start <= now;
      st.head = (st.level === "advisory" ? "Flooding likely" : "Flooding possible") + " in low areas near the " + water + " " + st.when;
      st.word = st.level === "advisory" ? "Flooding likely" : "Flooding possible"; st.more = flood.length - 1;
    } else if (ups.length) {
      st.level = "watch"; st.when = when(ups[0]); st.head = "Higher than usual tide " + st.when + (isFinite(red) ? ". No flooding expected" : "");
      st.word = "Higher than usual"; st.more = ups.length - 1;
    } else { st.head = "No higher-than-usual tides in the next " + days + " days"; st.word = "Normal"; }
    if (ups.length) {   // the numbers: one comparison only (above an average high tide)
      var top = ups.reduce(function (x, w) { return !x || w.peak > x.peak ? w : x; }, null);
      st.tech.push("Peak " + top.peak.toFixed(1) + " ft, " + (top.peak - m).toFixed(1) + " ft above an average high tide");
      if (isFinite(red)) st.tech.push("flood level " + red.toFixed(1) + " ft");
    }
    if (!isFinite(red)) st.tech.push(LK.text("coast_no_level"));
    return st;
  }
  function tideCard(st, name) {
    var moreTxt = st.more > 0 ? "+" + st.more + " more " + (st.more === 1 ? "time" : "times") + " this week" : "";
    return { cls: "tcard2 sv-card sv-" + st.level,
      label: (name ? name + " tides: " : "") + st.word + ". " + st.head + "." + (moreTxt ? " " + moreTxt + "." : "") + (st.tech.length ? " " + st.tech.join(". ") + "." : ""),
      html: (name ? '<span class="sd">' + esc(name) + "</span>" : "") + '<span class="th">' + esc(st.head) + "</span>" +
        '<span class="lv sv-badge sv-' + st.level + '">' + SV.icon(st.level) + esc(st.word) + "</span>" +
        (moreTxt ? '<span class="t2">' + esc(moreTxt) + "</span>" : "") + (st.tech.length ? '<span class="t2">' + esc(st.tech.join(" · ")) + "</span>" : "") };
  }

  /* ---------- creeks ---------- */
  // The creeks' line for the card: level (capped by severity.js inside creek_status.js), the worst status, its creeks
  function creeks(data, nws) {
    var CS = window.CREEK_STATUS; if (!CS || !data) return null;
    var HM = CS.home(data, null, { nws: nws || [], noMore: true });
    var all = (data.creeks || []).concat(data.creeks_preview || []);
    var worst = ["likely", "ready", "alert"].filter(function (k) { return all.some(function (c) { return (c.status || {}).key === k; }); })[0];
    var names = worst ? all.filter(function (c) { return (c.status || {}).key === worst; }).map(function (c) { return c.name; }) : [];
    return { level: HM.level, likely: HM.likely, worst: worst, names: names, headline: worst ? LK.text("verdict_" + worst) + ": " + names.join(", ") : "",
      todo: worst ? LK.text("verdict_" + worst + "_todo") : "", source: "From OneShoreline’s creek gauges and rain gauges." };
  }

  /* ---------- the card ---------- */
  // Candidates: the Bay tide at the flood level, the creeks with an alert, and each NWS product. The most severe leads
  // (ties: tide, then creeks, then the others); every other one is named under it. The card's color is the highest level.
  function plan(s) {
    var list = s.nws || [], bay = s.bay, CR = s.creeks, cands = [];
    var tideP = list.filter(function (p) { return SV.hazardOf(p.event) === "tide"; });
    if (bay && bay.flood) cands.push({ kind: "tide", level: bay.level, order: 0 });
    else if (tideP.length) cands.push({ kind: "nws", p: tideP[0], level: SV.nwsLevel(tideP[0].event), order: 0 });
    if (CR && CR.level && SV.RANK[CR.level] >= SV.RANK.watch) cands.push({ kind: "creek", level: CR.level, order: 1 });
    // each other product, once: NWS often issues the same alert per forecast zone (the Bay shoreline, the coast), so the
    // same name and end time is one alert here (staff, 2026-10-26); the coastal flood product that names the tide's source
    // isn't repeated either
    var seen = {}, key = function (p) { return p.event + "|" + (p.ends || p.expires || ""); };
    if (tideP.length) seen[key(tideP[0])] = true;
    list.forEach(function (p) {
      if (seen[key(p)]) return;
      seen[key(p)] = true;
      cands.push({ kind: "nws", p: p, level: SV.nwsLevel(p.event), order: SV.hazardOf(p.event) === "creek" ? 1 : 2 });
    });
    cands.sort(function (a, b) { return SV.RANK[b.level] - SV.RANK[a.level] || a.order - b.order; });
    return { cands: cands, lead: cands[0], tideP: tideP, level: cands.length ? SV.top(cands.map(function (c) { return c.level; })) : "normal" };
  }
  function tideHead(bay) {
    return LK.text("hero_tide_head", { when: bay.when }) +
      (bay.peakT && !bay.started && Math.abs(bay.peakT - bay.flood.end) > 30 * 60000 ? ", " + LK.text("hero_tide_peak", { time: bay.peakClock }) : "") + ".";
  }
  function otherText(c, s) {
    if (c.kind === "creek") return "Creeks: " + s.creeks.headline;
    if (c.kind === "tide") return "Bay tide: " + LK.text("hero_tide_head", { when: s.bay.when });
    return c.p.event + " " + nwsUntil(c.p);
  }
  function render(el, s) {
    injectCSS();
    var P = plan(s), lead = P.lead, list = s.nws || [], h = "", head = "", sub = "", q = function (c) { return el.querySelector(c); };
    if (!q(".hh")) el.innerHTML = '<div class="hh"><span class="hic"></span><div><h2 class="hhd"></h2><p class="hsub src"></p></div></div><div class="hmore"></div>';
    if (!lead) {
      if (s.nws == null) { head = s.nwsFailed ? "National Weather Service alerts unavailable" : "Checking National Weather Service alerts…"; sub = s.nwsFailed ? "Retrying…" : "San Mateo County"; }
      else { head = LK.text("hero_none"); sub = s.bay && s.creeks ? LK.text("hero_none_sub") : "San Mateo County"; }
    } else if (lead.kind === "tide") {
      head = tideHead(s.bay);
      h += '<p class="act">' + esc(LK.text("tide_red_what")) + "</p>";
      h += '<p class="src">' + (P.tideP.length ? "National Weather Service " + esc(P.tideP[0].event) + " in effect " + esc(nwsUntil(P.tideP[0])) + "." : esc(LK.text("hero_tide_source"))) + "</p>";
    } else if (lead.kind === "creek") {
      head = s.creeks.likely.length ? LK.text("banner_likely", { creeks: s.creeks.likely.join(", ") }) : s.creeks.headline;
      h += '<p class="act">' + esc(s.creeks.todo) + "</p>";
      h += '<p class="src">' + esc(s.creeks.source) + (s.creekLink === false ? "" : ' <a href="Creeks.html' + hasPreview() + '">Creek details ›</a>') + "</p>";
    } else {
      head = lead.p.event + " " + nwsUntil(lead.p);
      var what = nwsWhat(lead.p);
      if (what) h += "<p>" + esc(what) + "</p>";
      if (lead.p.instruction) h += '<p class="act">' + esc(unwrap(lead.p.instruction)) + "</p>";
      h += '<p class="src">National Weather Service San Francisco Bay Area.</p>';
    }
    var others = P.cands.slice(1).map(function (c) { return otherText(c, s); });
    if (others.length) h += '<p class="also"><b>Also in effect:</b> ' + others.map(esc).join(" · ") + "</p>";
    var names = {}; list.forEach(function (p) { names[p.event] = (names[p.event] || 0) + 1; });
    if (list.length) h += '<details class="nwsfull-d"><summary>National Weather Service text (' + list.length + ')</summary><div class="nwsfull">' + list.map(function (p) {
      return '<div class="al"><h3>' + esc(p.event) + '</h3><div class="when">' + esc(nwsUntil(p)) + (names[p.event] > 1 && p.areaDesc ? " · " + esc(p.areaDesc) : "") +
        " · National Weather Service San Francisco Bay Area</div>" + alertBody(p) + "</div>";
    }).join("") + "</div></details>";
    // compact: the Creeks page, when the Bay tide or a coastal flood product leads: one narrow bar linking to the Tides page
    var compact = !!(s.compactTide && lead && (lead.kind === "tide" || (lead.kind === "nws" && SV.hazardOf(lead.p.event) === "tide")));
    if (compact) {
      head = lead.kind === "tide" ? LK.text("hero_tide_head", { when: s.bay.when }) + "." : lead.p.event + " " + nwsUntil(lead.p) + ".";
      h = others.length ? '<p class="also"><b>Also in effect:</b> ' + others.map(esc).join(" · ") + "</p>" : "";
    }
    el.classList.toggle("hcompact", compact);
    var d0 = q(".nwsfull-d"), wasOpen = d0 && d0.open;
    el.className = "hero sv-hero sv-" + P.level + (compact ? " hcompact" : "");
    el.setAttribute("role", lead && SV.RANK[P.level] >= SV.RANK.advisory ? "alert" : "status");
    q(".hic").innerHTML = SV.icon(lead ? P.level : "normal");
    q(".hhd").textContent = head;
    if (compact) q(".hhd").insertAdjacentHTML("beforeend", ' <a href="Tides.html' + hasPreview() + '">Tide details ›</a>');
    q(".hsub").textContent = sub; q(".hsub").hidden = !sub;
    if (q(".hmore").innerHTML !== h) { q(".hmore").innerHTML = h; if (wasOpen && q(".nwsfull-d")) q(".nwsfull-d").open = true; }
    return P;
  }
  // The kiosk's one-line version: the same lead, level and words, shorter
  function strip(s) {
    var P = plan(s), lead = P.lead;
    if (!lead) return { level: "normal", text: s.nws == null ? (s.nwsFailed ? "National Weather Service alerts unavailable" : "Checking National Weather Service alerts…") : LK.text("hero_none"),
      sub: "San Mateo County", others: [] };
    var text, sub;
    if (lead.kind === "tide") { text = LK.text("hero_tide_head", { when: s.bay.when }) + "."; sub = P.tideP.length ? "NWS " + P.tideP[0].event + " " + nwsUntil(P.tideP[0]) : "NOAA projection, Redwood City"; }
    else if (lead.kind === "creek") { text = s.creeks.likely.length ? LK.text("verdict_likely") + ": " + s.creeks.likely.join(", ") : s.creeks.headline; sub = s.creeks.todo; }
    else { text = lead.p.event + " " + nwsUntil(lead.p); sub = nwsWhat(lead.p) || "National Weather Service"; }
    return { level: P.level, text: text, sub: sub, others: P.cands.slice(1).map(function (c) { return otherText(c, s); }) };
  }

  window.HERO = { loadNWS: loadNWS, loadBay: loadBay, tideState: tideState, tideCard: tideCard, creeks: creeks, render: render, strip: strip,
    alertBody: alertBody, nwsWhat: nwsWhat, injectCSS: injectCSS, plan: plan };
})();
