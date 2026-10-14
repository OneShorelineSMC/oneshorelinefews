# OneShoreline Early Warning – web widgets and kiosk

Code for OneShoreline's San Francisco Bay and creek monitoring displays:

- **Widgets for the OneRain (Contrail) dashboard**: NWS alerts, tide forecasts, and tides above MHHW
- **A Raspberry Pi kiosk** for the office and EOC: one screen with Bay tides, creeks, a sensor map and NWS alerts
- **A creek page for phones**: stage, rainfall, tide and NWS alerts for Colma, San Bruno, Belmont and Atherton, with contact info
- **A Bay tides page for phones** (Redwood City), which also works as a single dashboard widget
- **A sensor map** of every public OneRain site (phone and desktop page, plus a Map tab on the kiosk)
- **A scheduled data job** that collects OneRain readings for the kiosk, phone page and map

Everything is plain HTML/JavaScript served by GitHub Pages from this repo
(`github.com/OneShorelineSMC/oneshorelinefews`) at:

```
https://oneshorelinesmc.github.io/oneshorelinefews/<file name>
```

`fews.oneshoreline.org` currently redirects to this address. Moving the site to that custom domain is planned for
later; when it happens, add a `CNAME` file and update the addresses in this README and `KIOSK_SETUP.md`. The home page
(`https://oneshorelinesmc.github.io/oneshorelinefews/`) is `index.html`, which links to the public pages.

The pages get live data straight from public sources (NOAA, National Weather Service, and OneRain's public
sensor pages). There are no servers to run and no accounts or API keys involved, except the one GitHub token
described under *Creek data job*.

---

## Files

### Home page

| File | Purpose |
|------|---------|
| `index.html` | Landing page at `https://oneshorelinesmc.github.io/oneshorelinefews/`, top to bottom: compact title bar; "In an emergency, call 911"; active **NWS alerts for San Mateo County shown in full** (What/Where/When/Impacts and what to do; more than 3 are listed with a tap to open); **four creek status cards** (Colma, San Bruno, Belmont, Atherton) with the same status as the creek page tiles (Normal, Monitoring/Watch/Warning, Rain trigger, Offline, Data delayed), each gauge's stage (creek level) and accumulated rain over that creek's own windows (the ones on its OneRain dashboard and in its triggers: Atherton 30 min/1 hr/24 hr, Belmont 30 min/1 hr/4 hr/24 hr, Colma 1 hr/6 hr/24 hr, San Bruno 15 min/30 min/1 hr/3 hr/24 hr because it is very flashy; a window whose rain trigger amount is reached is shown in red), the status color around the whole card, tap for that creek; **Rapidly rising** cards; a **Bay tides** card in plain but precise language (same rule as the Tides page and kiosk): when tides will be higher than an average high tide this week, in rounded times ("today about 1–3:30 PM and tomorrow about 1:15–4 PM"), how far above an average high tide at the highest, whether the Bay is running above the tide tables right now (storms, onshore wind, heavy runoff and El Niño conditions can all do that), and a small-print line defining "average high tide" as MHHW at the Redwood City gauge (7.02 ft NAVD88); tap for the Tides page; a link to the sensor map; SMC Alert sign-up with a note that this site does not send alerts and SMC Alert is not set off by these readings; **System status** (creek data, creek gauges reporting, monitoring network); OneRain link; contact, disclaimer. **Rapidly rising (provisional rule, in the CONFIG block at the top of the script):** a gauge rose at least 0.5 ft in the last hour (`RISE_FT`, `RISE_MINUTES`), its newest reading is under 90 min old and the creek data is current; tidal gauges (`RISE_TIDAL`, San Bruno at First Avenue) count only after 0.10 in of rain in the last 3 hours in that watershed. The card says when the next flood level would be reached at that rate, if within 3 hours. |
| `img/` | OneShoreline logo and icons used by the pages: `oneshoreline-logo.png` (color, for light backgrounds), `oneshoreline-logo-white.png` (white and green, for the blue title bars and dark mode), `oneshoreline-mark.png` / `oneshoreline-mark-white.png` (the round mark alone), and the browser-tab and home-screen icons (`icon-32.png`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`). Keep the folder name and file names; the pages link to them. |

**Brand colors.** Title bars and buttons use OneShoreline Blue `#0A5587`; headings use Dark Navy `#003B5C`.
OneShoreline Green `#3AAE2A` appears in the logo only (it's too light for white text). The flood-status colors
(green Normal, yellow Monitoring, orange Watch, red Warning, purple Above Warning) are kept separate from the brand
colors on purpose, so status always reads the same way.

### Dashboard widgets (used in OneRain)

Each one is added to the OneRain dashboard as an iFrame/web-page widget pointing at its GitHub Pages URL.

| File | What it shows |
|------|---------------|
| `NWSAlertsSanMateo.html` | Active NWS watches, warnings and advisories for San Mateo County, with a color-coded status banner (red = warning, amber = watch/advisory, green = none), the full alert text formatted into What / Where / When / Impacts, links to the official NWS page, and an SMC Alert sign-up link. |
| `RWC_MHHWWindows.html` | Redwood City: a plain-language summary and table of the days and times high tides are **predicted** above MHHW over the next 7 days, plus the **measured** water level now (rising/falling, and how far above or below the prediction) and the highest predicted tide of the week. |
| `Alameda_MHHWWindows.html` | Same as above for Alameda. |
| `RWC_graph.html` | Redwood City graph: the past 48 hours of measured water level over the predicted tide, then the next 7 days of predictions. Tides above MHHW are shaded red, with a "Now" line. Works on phones. |
| `Alameda_graph.html` | Same as above for Alameda. |
| `Tides.html?embed=1` | *Optional all-in-one.* Redwood City in one widget (measured vs predicted, next time above MHHW, 48-hour + 7-day graph, table of times above MHHW), without the phone page's header and bottom bar. Can replace the four MHHW/graph widgets above with one. |

### Raspberry Pi kiosk

| File | Purpose |
|------|---------|
| `ShorelineKiosk.html` | The kiosk page, laid out at 800×480 for a 7" touchscreen and scaled sharply to fit any screen (e.g. 1024×600). Tabs: **Bay Tides** (Redwood City only: the next 7 days of high tides as day cards over a matching graph, using NOAA's model forecast (wind, pressure and river flow included) for about the first 2 days and the astronomical prediction after that, how measured high tides compared with predictions over the past 7 days, NWS coastal flood alerts or forecast-discussion notes about tides, and a **King Tides** line around the County's King Tide windows), **Creeks** (an All creeks summary card for each creek, then per creek: each gauge's stage with flood thresholds, rainfall, and the Bay tide, all on one timeline), **Map** (every public OneRain site, colored by status; tap one for its readings), **About** (contact info and QR codes), and **Disclaimer**. An NWS alert bar stays on top of every tab, and a creek alert strip appears when any creek reaches Flood Monitoring / Watch / Warning level. To protect the screen from burn-in, the whole picture moves by 2 pixels every 10 minutes (too small to notice); KIOSK_SETUP.md also explains how to switch the screen off after hours. |
| `KIOSK_SETUP.md` | Step-by-step Raspberry Pi setup, kiosk options, and all settings. |

### Phone page

| File | Purpose |
|------|---------|
| `Creeks.html` | Creek page designed for phones, at `https://oneshorelinesmc.github.io/oneshorelinefews/Creeks.html`. Opens on **All creeks**: a card per creek with its status, each gauge's level, rain and tide (tap a card for that creek). Four tiles at the top, one per creek, each showing that creek's current status (Normal, Monitoring, Watch, Warning, Rain trigger, Offline); tap one to switch (`#colma`, `#sanbruno`, `#belmont`, `#atherton` at the end of the URL opens one). **Creeks** tab: NWS alert banner (tap for full text), each stage gauge with its level and thresholds (or "Gauge may be offline" with the last report), rainfall, Belmont's rain triggers, the Bay tide measured vs predicted, and rain / stage / tide graphs on one timeline (the tide graph also shows NOAA's model forecast, `ofs_water_level`, for about the next 12 hours when it is available). The bottom bar (Home · Creeks · Tides · Map · About) is on this page, the tides page and the sensor map; tapping Creeks while viewing a creek returns to All creeks. **About** tab: what the page shows, "In an emergency, call 911", SMC Alert sign-up, contact buttons, and the disclaimer. Follows the phone's dark mode, refreshes automatically, and can be saved to the home screen. |
| `Tides.html` | Bay tides page for phones, at `https://oneshorelinesmc.github.io/oneshorelinefews/Tides.html`, laid out like the kiosk Bay Tides tab: one sentence first, the week next, details behind taps. Redwood City only (NOAA 9414523, ft NAVD88; Alameda dropped Oct 13). **Headline** (status color around the box): "Tides above MHHW: Today 12:55–3:25 PM (7.64 ft) · Tomorrow …" or "No tides above MHHW in the next 7 days", then "Now 6.69 ft rising · +0.45 ft vs predicted". **Next 7 days**: each day's highest tide (a list on phones, 7 columns over the graph on wide screens), labeled measured / fcst / predicted. Heights come from one series: measured for what has happened, then NOAA's model forecast (`ofs_water_level`, about 2 days), then the astronomical prediction, so the headline and list agree. **Graph**: today through 7 days, measured, NOAA forecast and predicted, heights on the left, a "Now" tag, MHHW in the legend. **NWS forecasters on tides**: tide sentences from the NWS Bay Area forecast discussion (tap for all and the issue time); the NWS alert banner is at the top. **Behind taps**: times above MHHW with each peak's source; now and the past 7 days (running higher/lower than predicted, model accuracy, high-tide table). Then the **King Tides** card (only around King Tide windows) and the **King Tide season calendar**. Without the model, it falls back to predictions. Add `?embed=1` for a dashboard widget version (no title bar, alert banner, bottom bar or calendar). |
| `SiteMap.html` | Map of every public OneRain site, for phones and computers, at `https://oneshorelinesmc.github.io/oneshorelinefews/SiteMap.html`. Markers are colored by status (reporting, Flood Monitoring / Watch / Warning level, not reporting); square markers are rain-only gauges. Tap a site for its latest readings, how long ago they came in, a 24-hour graph, and a link to the full data on OneRain. **List** shows all sites grouped by status; **Rain 24 h** labels each site with its 24-hour rain total. `#site=41102` at the end of the URL opens that site (use the site number OneRain shows in parentheses). |

### Creek data job

| File | Purpose |
|------|---------|
| `data/tide_days_lookup_2026-27.json` | **Tide days of concern, Oct 2026 – Apr 2027**, from San Mateo County Emergency Management's sheet (San Francisco gauge, NOAA 9414290): one row per day with its category (King Tide · Elevated · none) and King Tide window, plus the three windows (Nov 21–28, Dec 20–27, Jan 17–24). The kiosk's Bay Tides tab and `Tides.html` read it for the King Tides line (shown only from 7 days before each King Tide window to its end) and the calendar, showing **dates and labels only**: the County's heights are ft MLLW at San Francisco, while the pages use ft NAVD88 at Redwood City and Alameda. Today is the Pacific-time date; both pages hide the line after the season's end date (Apr 30, 2027). For next season, add a new file in the same format and change `TIDE_DAYS_URL` in both pages. |
| `lookups/` | **Everything staff check and update, as plain tables** (see `lookups/README.md`): `creeks.csv` (creek names, intro/note text, tide station, rain totals shown), `creek_gauges.csv` (each creek's stage and rain gauges mapped to their OneRain sensors, how each reports, which are tidal), `thresholds.csv` (all flood thresholds and rain triggers), `tide_stations.csv` (MHHW and MLLW-to-NAVD88 per NOAA station), `settings.csv` (rapidly-rising rule, offline/delayed timing, NOAA forecast rules, "higher than predicted" call-outs) and `display_text.csv` (disclaimer, 911 and SMC Alert wording, tide explanations, creek status words, contact details and links). `lookups/THRESHOLDS_BASIS.md` records where each value came from and who signed off. Each row has `checked_by` / `checked_on` columns. If a file has a mistake, nothing goes blank: the data job keeps the last good settings and marks its run failed in the Actions tab with the row, and the pages keep built-in values and flag it (home page System status; kiosk bottom bar). |
| `lookups.js` | Shared by every page: reads `settings.csv`, `tide_stations.csv` and `display_text.csv` (re-read every 30 min), checks each value, and fills in the marked text on the page. Holds the built-in fallback values. |
| `scripts/creek_config.py` | Reads and checks `lookups/creeks.csv`, `creek_gauges.csv`, `thresholds.csv` and `tide_stations.csv` for the data job. Nothing to edit here for normal changes. |
| `scripts/fetch_onerain.py` | Reads the last 48 hours of every creek gauge in `lookups/creek_gauges.csv` from OneRain's **public** sensor pages (OneRain's data export requires a login; the public pages don't). |
| `scripts/fetch_sites.py` | Reads every **public** site from OneRain's Sites list: its location, each sensor's latest reading, and the last 24 hours for the small graphs and rain totals. Battery/voltage/signal sensors are left out, and sites with no other sensors (e.g. radio repeaters) don't appear. Alert levels for the map come from `lookups/thresholds.csv`; OneRain's Redwood City tide is shown in NAVD88 using `lookups/tide_stations.csv`. |
| `.github/workflows/onerain.yml` | GitHub Action that runs both scripts and publishes the results to the **`data`** branch as `creeks.json` (every run, about every 5 minutes; also copied to `sanbruno.json`, its old name) and `sites.json` (about every 15 minutes), replacing them each time (so it doesn't add commits to `main`). |
| `scripts/fetch_atlas14.py`, `.github/workflows/atlas14.yml` | **Atlas 14 pull** (run by hand from the Actions tab): NOAA Atlas 14 rain frequency tables for every FEWS site, the source of `lookups/rain_frequency.csv`. The result is a download; nothing is committed. |
| `scripts/fetch_usgs.py`, `.github/workflows/usgs_history.yml` | **USGS history pull** (run by hand): 15-minute stage/flow since 2007 for the nine USGS gauges in the proposed creeks, one parallel job per site, for calibrating the rapidly-rising rule. The result is a download (`out/` is not committed). |

The kiosk, the phone page and the home page read `https://raw.githubusercontent.com/OneShorelineSMC/oneshorelinefews/data/creeks.json`;
the map and the kiosk's Map tab read `.../data/sites.json`.

---

## Stations, sensors and thresholds

(Current values; `lookups/thresholds.csv` is the source.)

| What | Source | ID | Notes |
|------|--------|----|-------|
| Redwood City tide gauge | NOAA | 9414523 | MHHW = 7.02 ft NAVD88 |
| Alameda tide gauge | NOAA | 9414750 | MHHW = 6.37 ft NAVD88 |
| Colma Creek at Orange Memorial Park – stage / rain | OneRain | 41101 | Monitoring 3.40 · Watch 5.00 · Warning 6.75 ft · tide: Alameda |
| San Bruno Creek at First Avenue – stage / rain | OneRain | 41102 | Monitoring 2.40 · Watch 3.60 · Warning 4.80 ft · tide: Alameda |
| San Bruno Mountain – rain | OneRain | 41200 | Upper San Bruno Creek watershed |
| Belmont Creek at Old County Rd – stage / rain | OneRain | 41104 | Monitoring 2.25 · Watch 3.25 · Warning 4.00 ft · flooding likely if 30-min rain > 0.20 in, or 4-hr rain > 0.42 in with high tide · tide: Redwood City |
| Atherton Channel at Alameda de las Pulgas – stage | OneRain | 41107 | Monitoring 3.18 · Watch 4.60 · Warning 5.65 · Roadway Flooded 10.40 ft · tide: Redwood City |
| Atherton Channel upstream of CalTrain – stage / rain | OneRain | 41106 | Monitoring 2.80 · Watch 4.10 · Warning 5.50 ft (probe 0.37 ft above channel bottom) |
| NWS alerts | api.weather.gov | San Mateo County (FIPS 006081) | |
| All other OneRain sites (map) | OneRain | every site on the public Sites list | Alert colors for the creek gauges above (from `lookups/thresholds.csv`) |

All water levels are in feet, NAVD88. Tide predictions come from NOAA and do **not** include storm surge,
wind or runoff; the measured water level shows those effects.

---

## Keeping it running

### Creek data job (every 5 minutes)

GitHub's built-in scheduler doesn't reliably start this job, so it is triggered every 5 minutes by
**cron-job.org** (job name: *OneShoreline – Fetch OneRain data*), which calls GitHub's "run workflow" API:

```
POST https://api.github.com/repos/OneShorelineSMC/oneshorelinefews/actions/workflows/onerain.yml/dispatches
Body: {"ref":"main"}
Headers: Authorization: Bearer <token> · Accept: application/vnd.github+json · Content-Type: application/json
```

- The cron-job.org job uses a **GitHub fine-grained personal access token** with **Resource owner:
  OneShorelineSMC**, access to **only this repository**, and **Actions: Read and write** only. **The token
  is set to no expiration date.** If it expires, the kiosk's Creeks tab and the phone page
  show *"Creek data delayed"* and the map shows *"data delayed"*. To fix it: create a new token
  (https://github.com/settings/personal-access-tokens/new, same settings) and paste it into the cron-job.org
  job's `Authorization` header as `Bearer <token>`. If OneShorelineSMC requires approval for tokens, an
  organization owner approves it under the organization's **Settings → Personal access tokens → Pending
  requests**.
- The map data (`sites.json`) is refreshed by the same job, every third run (about every 15 minutes).
- Runs appear in the **Actions** tab. A red ✗ means OneRain couldn't be read; the log shows how many readings
  were found for each sensor. If OneRain redesigns its sensor pages, `scripts/fetch_onerain.py` may need updating.
- GitHub Actions is free for this public repository. If the repo were made private, every-5-minute runs would
  exceed the free monthly allowance.
- You can always run it by hand: **Actions → Fetch OneRain data → Run workflow**.

### Updating a widget

1. Edit the file on GitHub (pencil icon) and commit.
2. GitHub Pages updates within a minute or two.
3. In OneRain, add or bump a version number at the end of the widget URL (`?v=2`, `?v=3`, …) so browsers
   don't show a cached copy.

The Pi kiosk picks up changes at its daily 3 AM reload, or immediately if the Pi is rebooted. The phone page
picks up changes the next time someone opens it (a pull-down refresh may be needed if it was already open).

---

## Times

Every time on every page is Pacific time as on local clocks: PDT in summer, PST in winter (America/Los_Angeles),
whatever time zone the viewer's device is set to. NOAA data is requested in local time (`time_zone=lst_ldt`),
OneRain readings are converted to America/Los_Angeles by the data job, and NWS times are converted before display.
The kiosk clock and the "Updated" lines show the current zone (e.g. "12:45 PM PDT").

## Data sources

- **NOAA CO-OPS Tides & Currents API**: tide predictions, measured water levels, and the San Francisco Bay Operational Forecast System's water-level forecast at Redwood City (`ofs_water_level`), all in ft NAVD88
  (`api.tidesandcurrents.noaa.gov`)
- **National Weather Service API**: active alerts and the San Francisco Bay Area forecast discussion (kiosk
  Tides tab) (`api.weather.gov`); official alert pages on
  `forecast.weather.gov`
- **OneShoreline Early Warning System (OneRain Contrail)**: creek stage, rainfall and all map sites
  (`oneshorelineearlywarning.onerain.com`)
- **San Mateo County Emergency Management**: "Tide days of concern, Oct 2026 to Apr 2027" (King Tides line and calendar)
- **OpenStreetMap**: map background (`tile.openstreetmap.org`, © OpenStreetMap contributors)
- **Libraries** (loaded from CDNs, each locked with a Subresource Integrity hash so a changed file is refused):
  Chart.js 4.5.1 (cdnjs), Leaflet 1.9.4 (jsDelivr), qrcodejs 1.0.0 (cdnjs, kiosk About tab). To upgrade one,
  update both the URL and its `integrity` hash in every page that loads it.

## Contact

OneShoreline (San Mateo County Flood and Sea Level Rise Resiliency District) ·
1700 S. El Camino Real, Suite 502, San Mateo, CA 94402 · (650) 844-8310 · info@oneshoreline.org ·
[oneshoreline.org](https://www.oneshoreline.org)

## License

GPL-3.0 – see `LICENSE`.
