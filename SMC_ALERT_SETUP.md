# SMC Alert into FEWS (staff, 2026-11-25)

SMC Alert (the County's alerts, sent by the Sheriff's Office through Rave / Smart911) has no public feed, and each
subscriber gets only the alerts for the addresses they registered. Road closures are an optional subscription. So FEWS
gets them through a mailbox of its own:

SMC Alert email → FEWS mailbox → Apps Script copies road and weather alerts into a Google Sheet → the Sheet, published
as CSV → the data job (`scripts/road_closures.py`) → Storm Tracker and the monthly summary, with a tide / rain cause.

No password or token goes in this repository. The only thing added here is the published CSV address, and that CSV
holds only alert text that SMC Alert already sends to the public.

## 1. The mailbox and the subscription (staff, by hand)

1. Use a shared OneShoreline Google mailbox (not a personal one).
2. Register it with SMC Alert (smcgov.org/emergency-management/smc-alert, "Register Now", on smart911.com). Set the
   password yourself.
3. Add an address in each shoreline and creek community. Alerts are sent by location, so one address per place:
   South San Francisco (east of 101), San Bruno, Millbrae, Burlingame, San Mateo, Foster City, Belmont, San Carlos
   (Harbor Industrial / Industrial Road), Redwood City, Menlo Park (Belle Haven), East Palo Alto, Pacifica, Half Moon Bay,
   Pescadero. Public addresses (a city hall, a fire station) are fine.
4. Turn on the optional **major road closures** alerts, and email delivery.

## 2. The Sheet and the script (staff, about 10 minutes)

1. In the mailbox's Google Drive, make a new Google Sheet named "SMC Alert for FEWS". Copy its id from the address bar
   (the long part between `/d/` and `/edit`).
2. In the Sheet: Extensions → Apps Script. Replace the code with `scripts/smc_alert_to_sheet.gs` from this repository.
   Paste the Sheet id into `SHEET_ID`. Save.
3. Choose `installTrigger` and press Run. Approve the access it asks for (read Gmail, edit this Sheet). It copies the
   last week's alerts and then runs every 10 minutes.
4. In the Sheet: File → Share → Publish to web → the first tab, **Comma-separated values (.csv)** → Publish. Copy the
   address it gives (it ends in `output=csv`).

## 3. Tell the data job (one line)

In `lookups/city_feeds.csv`, the last row starts with `#SMC Alert` (switched off). Replace the placeholder address with
the CSV address from step 2.4 and remove the `#`. The next road-closure run (about 10 minutes) reads it; the Storm
Tracker's road closure card says "SMC Alert: ok" when it worked.

## How the alerts are read

- A "Road Closure" alert opens a closure at the time it was sent; a later "Reopening" alert for the same road ends it.
  With no reopening alert, it shows as open for 24 hours, then is logged as ended (reopening time unknown).
- The place is the city after the subject's last comma ("Industrial Road, San Carlos"), with its side and supervisorial
  district from `lookups/places.csv`.
- Only alerts that name a closure and a storm cause count (the same rule as city posts); the script already leaves out
  crime and other alerts.
- The cause (high tide, rain, both) is set by the same rule as Caltrans closures.

## If it stops

The Storm Tracker shows "SMC Alert: NOT READ" when the CSV can't be read. Check the Sheet is still published, the
script's trigger is still there (Apps Script → Triggers), and the mailbox still gets SMC Alert email.
