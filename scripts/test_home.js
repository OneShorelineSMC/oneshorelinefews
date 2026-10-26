// Tests for severity.js (the home page's severity scale, section order and colors). Run: node scripts/test_home.js
"use strict";
var S = require("../severity.js");
var n = 0;
function check(cond, msg) { if (!cond) { console.error("FAIL: " + msg); process.exit(1); } n++; }

// Section order: active sections first, more severe first, ties keep tides first; then the rest in the default order
var D = function (t, c) { return [{ id: "tides", level: t }, { id: "creeks", level: c }]; };
check(S.order(D("advisory", "normal")).join() === "tides,creeks", "tides only active: tides first");
check(S.order(D("normal", "watch")).join() === "creeks,tides", "creeks only active: creeks first");
check(S.order(D("watch", "warning")).join() === "creeks,tides", "both active: the more severe first");
check(S.order(D("advisory", "advisory")).join() === "tides,creeks", "both active, same level: tides first");
check(S.order(D("normal", "normal")).join() === "tides,creeks", "neither active: the default order");
check(S.order(D("normal", "offline")).join() === "tides,creeks", "an offline gauge is not an active condition");
check(S.order(D("info", "normal")).join() === "tides,creeks", "information is never an active condition");

// NWS products: level and hazard
check(S.nwsLevel("Coastal Flood Advisory") === "advisory" && S.hazardOf("Coastal Flood Advisory") === "tide", "Coastal Flood Advisory");
check(S.nwsLevel("Flood Warning") === "warning" && S.hazardOf("Flash Flood Warning") === "creek", "Flood Warning, Flash Flood");
check(S.nwsLevel("Coastal Flood Statement") === "watch" && S.nwsLevel("Special Weather Statement") === "info", "statements");
check(S.hazardOf("Wind Advisory") === "other", "wind is another hazard");
var list = [{ event: "Wind Advisory" }, { event: "Coastal Flood Advisory" }];
check(S.nwsFor(list, "tide") === "advisory" && S.nwsFor(list, "creek") === null, "the NWS level for one hazard");

// Local severity never above the NWS product for the same hazard, unless flooding is observed
check(S.cap("advisory", "advisory", false) === "advisory", "local = NWS: unchanged");
check(S.cap("warning", "advisory", false) === "advisory", "local above NWS: capped to the NWS level");
check(S.cap("warning", "advisory", true) === "warning", "observed flooding: not capped");
check(S.cap("advisory", "watch", false) === "watch", "advisory under an NWS Watch: watch");
check(S.cap("advisory", null, false) === "advisory", "no NWS product for that hazard: local stands");
check(S.cap("watch", "warning", false) === "watch", "never raised by the NWS level");
check(S.creekLevel("likely") === "warning" && S.creekLevel("none") === "normal" && S.creekLevel("offline") === "offline", "creek levels");
check(S.top(["normal", "advisory", "watch", "offline"]) === "advisory", "the highest level");

// Time windows
var H = 3600000, clock = function (t) { var h = Math.floor(t / H) % 24, m = Math.round(t % H / 60000);
  return ((h % 12) || 12) + (m ? ":" + String(m).padStart(2, "0") : "") + " " + (h < 12 ? "AM" : "PM"); };
check(S.windowText(10.5 * H, 15 * H, 9 * H, clock) === "10:30 AM–3 PM", "window, different halves of the day: " + S.windowText(10.5 * H, 15 * H, 9 * H, clock));
check(S.windowText(13 * H, 15 * H, 9 * H, clock) === "1–3 PM", "window, same half of the day");
check(S.windowText(10.5 * H, 15 * H, 11 * H, clock) === "now until 3 PM", "window under way");

// Colors: every pair passes WCAG 2.1 AA (4.5:1 text, 3:1 UI parts), light and dark
["light", "dark"].forEach(function (mode) {
  var card = S.CARD[mode];
  S.LEVELS.forEach(function (l) {
    var t = S.TOKENS[mode][l];
    check(S.contrast(t.ink, card) >= 4.5, mode + " " + l + " text on the card: " + S.contrast(t.ink, card).toFixed(2));
    check(S.contrast(t.ink, t.tint) >= 4.5, mode + " " + l + " badge text on its tint: " + S.contrast(t.ink, t.tint).toFixed(2));
    check(S.contrast(t.stripe, card) >= 3, mode + " " + l + " stripe on the card: " + S.contrast(t.stripe, card).toFixed(2));
    check(S.contrast(t.on, t.fill) >= 4.5, mode + " " + l + " hero text on its fill: " + S.contrast(t.on, t.fill).toFixed(2));
  });
});
check(S.contrast(S.TOKENS.light.advisory.on, S.TOKENS.light.advisory.fill) >= 4.5, "hero text on the amber fill");
var css = S.css();
check((css.match(/\.sv-hero\.sv-(warning|advisory|watch)\{background/g) || []).length === 3 && !/\.sv-card[^{]*\{background/.test(css),
  "only the hero gets a filled background; cards get a stripe");

console.log("home page: " + n + " checks passed");
