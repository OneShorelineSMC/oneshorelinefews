/* FEWS creek status layer: STAFF PREVIEW ONLY (pages show it with ?preview=1 in the address).
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
  var PREVIEW = /[?&]preview=1\b/.test(location.search);
  var COL = { likely: "#c62828", ready: "#e07b00", alert: "#e6c200", offline: "#8a96a3", delayed: "#8a96a3", none: "#8a96a3" };
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
  function list(a) { return a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " and " + a[a.length - 1]; }
  function rainWord(l) { return l >= 3 ? T("rain_severe") : l === 2 ? T("rain_vheavy") : l === 1 ? T("rain_heavy") : ""; }
  function winLabel(m) { return m < 60 ? m + " min" : m / 60 + " hr"; }

  /* One creek's status as shown: the data job's answer, or Data delayed when the data file is old */
  function view(data, c) {
    var st = c.status || {}, key = st.key || "none";
    var late = !data.generated || nowLocal() - parse(data.generated) > LK.num("CREEK_DATA_LATE_MIN") * 60000;
    if (late) key = "delayed";
    var word = key === "offline" ? T("status_offline") : key === "delayed" ? T("status_delayed") : T("verdict_" + key);
    var todo = key === "offline" || key === "delayed" ? T("verdict_nodata_todo") : T("verdict_" + key + "_todo");
    var reasons = (st.reasons || []).map(reason).filter(Boolean);
    if (late && st.key && st.key !== "none") reasons.unshift(T("verdict_" + st.key) + " at " + clock(data.generated) + ", the last update.");
    return { key: key, word: word, todo: todo, reasons: reasons, st: st, rank: RANK[key], color: COL[key] };
  }
  function reason(r) {
    var s = T(r.code, { rain: rainWord(r.rain).toLowerCase(), Rain: rainWord(r.rain), time: clock(r.time) });
    if (!s) return "";
    if (r.code === "why_watch" && r.rising_fast) s = s.replace(/\.$/, " and rising fast.");
    if (r.code === "why_monitoring" && (r.rising || r.rising_fast)) s = s.replace(/\.$/, r.rising_fast ? " and rising fast." : " and rising.");
    return s;
  }

  /* Pieces */
  function chip(level) {
    if (!level) return '<span class="cs-norain">' + esc(T("status_normal")) + "</span>";
    var k = level >= 3 ? "severe" : level === 2 ? "vheavy" : "heavy", b = "";
    for (var i = 1; i <= 3; i++) b += "<i" + (i <= level ? ' class="on"' : "") + "></i>";
    return '<span class="cs-chip ' + k + '"><span class="cs-meter" aria-hidden="true">' + b + "</span>" + esc(rainWord(level)) + "</span>";
  }
  function trendText(t) {
    if (!t || !t.trend) return "";
    var w = T("trend_" + t.trend), arrow = { fast: "↑↑", rising: "↑", steady: "→", falling: "↓" }[t.trend] || "";
    return '<span aria-hidden="true">' + arrow + "</span> " + esc(w) + (t.ft_per_hr != null && t.trend !== "steady" ? ' <span class="cs-dim">(' + (t.ft_per_hr > 0 ? "+" : "") + t.ft_per_hr.toFixed(1) + " ft/hr)</span>" : "");
  }
  // Normal | Monitoring | Watch | Warning, only the active segment colored, marker at the current stage
  function band(g, e) {
    var th = (g.thresholds || []).filter(function (t) { return t.level <= 3; });
    var p = e && e.points && e.points.length ? e.points[e.points.length - 1] : null;
    if (e && e.latest && e.latest[0] && (!p || e.latest[0] > p[0])) p = e.latest;
    var sig = e && e.signals || {};
    if (!p || !sig.trend) return '<div class="cs-row"><span class="cs-lbl">' + esc(g.label) + '</span><span class="cs-val cs-dim">' + esc(T("status_offline")) + (p ? " · " + esc(dated(p[0])) : "") + "</span></div>";
    var v = p[1];
    if (th.length < 3) return '<div class="cs-row"><span class="cs-lbl">' + esc(g.label) + '</span><span class="cs-val">' + v.toFixed(2) + " ft · " + trendText(sig) + "</span></div>";
    var cut = [th[0].value, th[1].value, th[2].value], top = cut[2] + Math.max(0.5, (cut[2] - cut[1]));
    var seg = [[0, cut[0], 35, "Normal"], [cut[0], cut[1], 20, th[0].name.replace("Flood ", "")], [cut[1], cut[2], 20, th[1].name.replace("Flood ", "")], [cut[2], top, 25, th[2].name.replace("Flood ", "")]];
    var act = v >= cut[2] ? 3 : v >= cut[1] ? 2 : v >= cut[0] ? 1 : 0, pos = 0, acc = 0;
    seg.forEach(function (s, i) {
      if (i === act) pos = acc + s[2] * Math.max(0, Math.min(1, (v - s[0]) / (s[1] - s[0] || 1)));
      acc += s[2];
    });
    var name = act ? th[act - 1].name : T("status_normal");
    return '<div class="cs-band"><div class="cs-bt"><span class="cs-lbl">' + esc(g.label) + '</span><span class="cs-now">' + v.toFixed(2) + " ft · " + esc(name) + " · " + trendText(sig) + "</span></div>" +
      '<div class="cs-track" role="img" aria-label="' + esc(g.label + ": " + name) + '">' + seg.map(function (s, i) {
        return '<span class="cs-s" style="flex:' + s[2] + (i === act ? ";background:" + LEVEL_COL[i] : "") + '"></span>'; }).join("") +
      '<span class="cs-mark" style="left:' + pos.toFixed(1) + '%"></span></div>' +
      '<div class="cs-ticks" aria-hidden="true">' + seg.map(function (s, i) {
        return '<span style="flex:' + s[2] + '"' + (i === act ? ' class="on"' : "") + ">" + esc(s[3]) + "</span>"; }).join("") + "</div></div>";
  }

  /* A creek card: status, reason, What to do, then details. opts.link: where "details" goes; opts.compact: no details */
  function card(data, c, opts) {
    opts = opts || {};
    var v = view(data, c), st = v.st, h = "";
    h += '<article class="cs-card cs-' + v.key + '" data-creek="' + esc(c.id) + '">';
    h += '<div class="cs-head"><h3>' + esc(c.name) + "</h3></div>";
    h += '<div class="cs-verdict cs-v-' + v.key + '"><span class="cs-ic" aria-hidden="true"></span>' + esc(v.word) + "</div>";
    v.reasons.forEach(function (r) { h += '<p class="cs-why">' + esc(r) + "</p>"; });
    h += '<div class="cs-body">' + (v.key === "likely" ? '<p class="cs-danger">' + esc(T("e911")) + "</p>" : "") +
      '<p class="cs-todo"><b>What to do:</b> ' + esc(v.todo) + "</p></div>";
    if (!opts.compact) {
      h += '<div class="cs-details">';
      (c.stages || []).forEach(function (g) { h += band(g, data.sensors[g.key]); });
      var r = st.rain || {};
      h += '<div class="cs-row"><span class="cs-lbl">Rain</span><span class="cs-val">' + chip(r.level) + "</span></div>";
      if (st.trigger) h += '<div class="cs-row"><span class="cs-lbl">Flooding trigger</span><span class="cs-val">' + esc(st.trigger.label) + ": " +
        st.trigger.amount.toFixed(2) + " of " + st.trigger.value.toFixed(2) + " in · met</span></div>";
      if (st.tidal && st.tide && st.tide.ft != null) {
        h += '<div class="cs-row"><span class="cs-lbl">Bay tide</span><span class="cs-val">' + st.tide.ft.toFixed(2) + " ft · " +
          (st.tide.rising ? "rising" : "falling") + (st.tide.next_high ? ' <span class="cs-dim">· high ' + esc(clock(st.tide.next_high)) + "</span>" : "") + "</span></div>";
      }
      h += "</div>";
    }
    h += '<div class="cs-foot"><span>As of ' + esc(dated(data.generated)) + (st.has_levels === false ? " · " + esc(T("no_flood_level")) : "") + "</span>" +
      (opts.link ? '<a href="' + esc(opts.link) + '">Details ›</a>' : "") + "</div>";
    return h + "</article>";
  }

  /* Top of page: one-line summary, red banner when flooding is likely, one evacuation button */
  function summary(data) {
    var by = { likely: [], ready: [], alert: [], nodata: [] };
    (data.creeks || []).forEach(function (c) {
      var v = view(data, c);
      if (by[v.key]) by[v.key].push(c.name);
      else if (v.key === "offline" || v.key === "delayed") by.nodata.push(c.name);
    });
    var m = [];
    if (by.likely.length) m.push(T("summary_likely", { creeks: list(by.likely) }));
    if (by.ready.length) m.push(T("summary_ready", { creeks: list(by.ready) }));
    if (by.alert.length) m.push(by.alert.length <= 3 ? T("summary_alert", { creeks: list(by.alert) }) : T("summary_alert_many", { n: by.alert.length }));
    if (!m.length) m.push(T("summary_none"));
    var h = "";
    if (by.likely.length) h += '<div class="cs-banner" role="alert">' + esc(T("banner_likely", { creeks: list(by.likely) })) + "</div>";
    h += '<div class="cs-glance"><p class="cs-main">' + esc(m.join(" ")) + "</p>";
    if (by.likely.length || by.ready.length) {
      var u = T("url_evacuation");
      if (/^https:\/\//.test(u)) h += '<a class="cs-evac" href="' + esc(u) + '" target="_blank" rel="noopener">' + esc(T("evac_button")) + " →</a>";
    }
    h += '<p class="cs-sub">' + esc(T("nws_separate")) + "</p></div>";
    return h;
  }

  /* All creeks for a page: summary, cards for creeks with a status, the rest folded away */
  function page(data, linkFor, opts) {
    opts = opts || {};
    var rows = (data.creeks || []).map(function (c) { return { c: c, v: view(data, c) }; });
    rows.sort(function (a, b) { return b.v.rank - a.v.rank; });
    var active = rows.filter(function (x) { return x.v.key !== "none"; }), quiet = rows.filter(function (x) { return x.v.key === "none"; });
    var h = badge() + summary(data) + '<div class="cs-grid">' + active.map(function (x) { return card(data, x.c, { link: linkFor && linkFor(x.c) }); }).join("") + "</div>";
    if (quiet.length) {
      h += '<details class="cs-quiet"' + (active.length ? "" : " open") + "><summary>" + quiet.length + " creek" + (quiet.length > 1 ? "s" : "") +
        " with no alerts — " + esc(list(quiet.map(function (x) { return x.c.short || x.c.name; }))) + '</summary><div class="cs-grid">' +
        quiet.map(function (x) { return card(data, x.c, { link: linkFor && linkFor(x.c) }); }).join("") + "</div></details>";
    }
    return h + (opts.staff === false ? "" : staffTable(data));
  }
  function badge() {
    return '<div class="cs-badge">STAFF PREVIEW · creek status layer in testing · not shown to the public</div>';
  }

  /* Staff table: everything behind each status */
  function staffTable(data) {
    var rows = (data.creeks || []).map(function (c) {
      var v = view(data, c), st = v.st, r = st.rain || {}, d = r.driver, t = st.tide;
      var lvl = v.key === "offline" ? esc(T("status_offline")) : st.level ? esc(st.level_name || "Level " + st.level) : st.has_levels === false ? '<span class="cs-dim">No flood levels</span>' : esc(T("status_normal"));
      var heavy = d ? esc(winLabel(d.minutes)) + ": " + d.inches.toFixed(2) + " in at " + esc(d.label) +
        (d.storm_years ? '<span class="cs-sm">about a ' + (d.storm_years >= 100 ? "100+" : d.storm_years) + "-year storm (" + Math.round(100 * (1 - Math.exp(-1 / d.storm_years))) + "% chance in any year)</span>" : "")
        : '<span class="cs-dim">—</span>';
      var notes = (st.staff_notes || []).concat((r.silent || []).map(function (s) { return s.label + " silent since " + (s.since ? dated(s.since) : "?"); }));
      if (st.trigger) notes.unshift("Trigger: " + st.trigger.label + " " + st.trigger.amount + " of " + st.trigger.value + " in");
      return "<tr><td><b>" + esc(c.name) + "</b></td><td><span class=\"cs-tag\"><i style=\"background:" + v.color + "\"></i>" + esc(v.word) + "</span></td>" +
        "<td>" + lvl + '<span class="cs-sm">' + trendText(st.trend) + "</span></td><td>" + chip(r.level) + "</td><td>" + heavy + "</td>" +
        "<td>" + (r.working || 0) + " of " + (r.of || 0) + '<span class="cs-sm">' + (r.elevated || 0) + " at very heavy+</span></td>" +
        "<td>" + (st.tidal ? (t && t.ft != null ? t.ft.toFixed(2) + " ft · " + (t.rising ? "rising" : "falling") + (t.next_high ? '<span class="cs-sm">high ' + esc(dated(t.next_high)) + " (" + t.next_high_ft + " ft)</span>" : "") : '<span class="cs-dim">no tide data</span>') : '<span class="cs-dim">not tidal</span>') + "</td>" +
        "<td>" + esc(notes.join("; ")) + "</td></tr>";
    });
    return '<details class="cs-staff"><summary>Staff table: what is behind each status</summary><div class="cs-tw"><table class="cs-tbl"><thead><tr>' +
      "<th>Creek</th><th>Status</th><th>Creek level · trend</th><th>Rain</th><th>Heaviest rain</th><th>Rain gauges</th><th>Tide</th><th>Notes</th>" +
      "</tr></thead><tbody>" + rows.join("") + "</tbody></table></div><p class=\"cs-sm\">Data as of " + esc(dated(data.generated)) +
      ". Status changes are logged in status_log.csv on the data branch.</p></details>";
  }

  /* Kiosk: large tiles, nothing to tap */
  function tile(data, c) {
    var v = view(data, c), st = v.st, r = st.rain || {};
    return '<div class="cs-tile cs-' + v.key + '"><div class="cs-tn">' + esc(c.name) + "</div>" +
      '<div class="cs-verdict cs-v-' + v.key + '"><span class="cs-ic" aria-hidden="true"></span>' + esc(v.word) + "</div>" +
      (v.reasons[0] ? '<div class="cs-tr">' + esc(v.reasons[0]) + "</div>" : "") +
      '<div class="cs-tm"><span class="cs-dim">Rain</span> ' + chip(r.level) + (st.trend ? ' &nbsp; <span class="cs-dim">Creek</span> ' + trendText(st.trend) : "") + "</div></div>";
  }

  var css = [
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
    ".cs-ic{width:14px;height:14px;border-radius:3px;flex:none}",
    ".cs-v-likely{background:#c62828;color:#fff}.cs-v-likely .cs-ic{background:#fff}",
    ".cs-v-ready{background:" + TINT.ready + "}.cs-v-ready .cs-ic{background:#e07b00}",
    ".cs-v-alert{background:" + TINT.alert + "}.cs-v-alert .cs-ic{background:#e6c200}",
    ".cs-v-none,.cs-v-offline,.cs-v-delayed{background:" + TINT.none + ";font-size:17px;font-weight:600}.cs-v-none .cs-ic{background:#8a96a3}",
    ".cs-v-offline .cs-ic,.cs-v-delayed .cs-ic{border:2px dashed #8a96a3}",
    ".cs-why{margin:8px 14px 0;font-size:14.5px;line-height:1.45;color:var(--text,var(--ink))}",
    ".cs-body{padding:8px 14px 10px}.cs-body p{margin:0 0 4px;font-size:15px;line-height:1.45}",
    ".cs-danger{font-weight:700;color:#c62828}",
    ".cs-details{margin:0 14px 10px;border-top:1px solid var(--line,#eceff3)}",
    ".cs-row{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line,#eceff3);font-size:14px}",
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
    ".cs-norain{font-weight:500}",
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
    ".cs-tr{font-size:13px;line-height:1.3;color:var(--ink,#16202b)}.cs-tm{font-size:13px;margin-top:auto}"
  ].join("\n");
  var styleEl = document.createElement("style"); styleEl.textContent = css; document.head.appendChild(styleEl);

  window.CREEK_STATUS = { preview: PREVIEW, view: view, card: card, summary: summary, page: page, staffTable: staffTable, tile: tile, badge: badge };
})();
