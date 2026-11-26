/**
 * SMC Alert -> Google Sheet (staff, 2026-11-25). Runs in Google Apps Script inside the FEWS mailbox that is subscribed
 * to SMC Alert, every 10 minutes. It copies SMC Alert emails about roads, flooding and storms into the first tab of a
 * Google Sheet, which is published to the web as CSV and read by the data job (scripts/road_closures.py, the
 * "SMC Alert" row in lookups/city_feeds.csv). Setup: SMC_ALERT_SETUP.md.
 *
 * What it writes: id, received (Pacific, YYYY-MM-DD HH:MM), subject, body. Only the alert's own text: no recipient,
 * no sender details, no headers. Alerts that don't mention a road, flooding or a storm (crime, missing persons and so
 * on) are skipped, so the public CSV holds only road and weather alerts. Keeps the newest MAX_ROWS rows.
 *
 * Nothing secret lives here: the Sheet's id is not a password (the CSV is public anyway), and the script runs as the
 * mailbox's own account. Don't paste any password or token into this file.
 */
var SHEET_ID = 'PASTE_THE_SHEET_ID_HERE';            // the long id in the Sheet's address: docs.google.com/spreadsheets/d/<id>/edit
var SENDER = 'smcgov@email.getrave.com';             // SMC Alert's sender (Rave Mobile Safety for the Sheriff's Office)
var LOOK_BACK = '7d';                                // how far back each run looks (it skips ones already copied)
var MAX_ROWS = 500;
var KEEP_RX = /\b(road|street|st\.|ave|blvd|highway|hwy|ramp|closed|closure|reopen|detour|flood|tide|storm|rain|mud|slide|tree|water)\b/i;

function collectSmcAlerts() {
  var sh = SpreadsheetApp.openById(SHEET_ID).getSheets()[0];
  if (sh.getLastRow() === 0) sh.appendRow(['id', 'received', 'subject', 'body']);
  var have = {};
  if (sh.getLastRow() > 1) {
    sh.getRange(2, 1, sh.getLastRow() - 1, 1).getValues().forEach(function (r) { have[r[0]] = true; });
  }
  var rows = [];
  GmailApp.search('from:' + SENDER + ' newer_than:' + LOOK_BACK).forEach(function (th) {
    th.getMessages().forEach(function (m) {
      var id = m.getId();
      if (have[id]) return;
      var subject = m.getSubject() || '';
      var body = (m.getPlainBody() || '').split(/SMC Alert sent by/i)[0]   // drop the signature block
        .replace(/^\s*SMC Alert:\s*/i, '').replace(/\s+/g, ' ').trim().slice(0, 1000);
      if (!KEEP_RX.test(subject + ' ' + body)) return;
      var received = Utilities.formatDate(m.getDate(), 'America/Los_Angeles', 'yyyy-MM-dd HH:mm');
      rows.push([id, received, subject.slice(0, 200), body]);
    });
  });
  if (rows.length) {
    rows.sort(function (a, b) { return a[1] < b[1] ? -1 : 1; });
    sh.getRange(sh.getLastRow() + 1, 1, rows.length, 4).setValues(rows);
  }
  var extra = sh.getLastRow() - 1 - MAX_ROWS;
  if (extra > 0) sh.deleteRows(2, extra);
}

/** Run once by hand after pasting the Sheet id: adds the every-10-minutes trigger (and removes any old one). */
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'collectSmcAlerts') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('collectSmcAlerts').timeBased().everyMinutes(10).create();
  collectSmcAlerts();
}
