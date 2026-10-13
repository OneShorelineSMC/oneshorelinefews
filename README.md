# OneShoreline Early Warning – web widgets and kiosk

Code for OneShoreline's San Francisco Bay and creek monitoring displays:

- **Widgets for the OneRain (Contrail) dashboard**: NWS alerts, tide forecasts, and tides above MHHW
- **A Raspberry Pi kiosk** for the office and EOC: one screen with Bay tides, creeks, a sensor map and NWS alerts
- **A creek page for phones**: stage, rainfall, tide and NWS alerts for Colma, San Bruno, Belmont and Atherton, with contact info
- **A Bay tides page for phones** (Redwood City), which also works as a single dashboard widget
- **A sensor map** of every public OneRain site (phone and desktop page, plus a Map tab on the kiosk)
- **A scheduled data job** that collects OneRain readings for the kiosk, phone page and map

Everything is plain HTML/JavaScript served by GitHub Pages from this repo
(`github.com/OneShorelineSMC/oneshorelinefews`) at OneShoreline's own web address:

```
https://fews.oneshoreline.org/<file name>
```

The `CNAME` file tells GitHub Pages to use that address; don't delete it. The home page
(`https://fews.oneshoreline.org/`) is `index.html`, which links to the public pages.

The pages get live data straight from public sources (NOAA, National Weather Service, and OneRain's public
sensor pages). There are no servers to run and no accounts or API keys involved, except the one GitHub token
described under *Creek data job*.

---

## Files

### Home page

| File | Purpose |
|------|---------|
| `index.html` | Landing page at `https://fews.oneshoreline.org/`: shows live NWS, creek and network status, and links to the creek page, the sensor map and OneRain, plus SMC Alert sign-up, contact info and the disclaimer. |
| `CNAME` | Tells GitHub Pages the site's address (`fews.oneshoreline.org`). |
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
| `RWC_PeakOutlook.html`, `Alameda_PeakOutlook.html` | *Optional / older.* Large single number: highest predicted tide in the next 7 days. The MHHW widgets now include this, so these are only needed if still on the dashboard. |

### Raspberry Pi kiosk

| File | Purpose |
|------|---------|
| `ShorelineKiosk.html` | The kiosk page, laid out at 800×480 for a 7" touchscreen and scaled sharply to fit any screen (e.g. 1024×600). Tabs: **Bay Tides** (Redwood City only: the next 7 days of predicted high tides as day cards over a matching graph, how measured high tides compared with predictions over the past 7 days, NWS coastal flood alerts or forecast-discussion notes about tides, and a **King Tides** line around the County's King Tide windows), **Creeks** (an All creeks summary card for each creek, then per creek: each gauge's stage with flood thresholds, rainfall, and the Bay tide, all on one timeline), **Map** (every public OneRain site, colored by status; tap one for its readings), **About** (contact info and QR codes), and **Disclaimer**. An NWS alert bar stays on top of every tab, and a creek alert strip appears when any creek reaches Flood Monitoring / Watch / Warning level. To protect the screen from burn-in, the whole picture moves by 2 pixels every 10 minutes (too small to notice); KIOSK_SETUP.md also explains how to switch the screen off after hours. |
| `KIOSK_SETUP.md` | Step-by-step Raspberry Pi setup, kiosk options, and all settings. |

### Phone page

| File | Purpose |
|------|---------|
| `Creeks.html` | Creek page designed for phones, at `https://fews.oneshoreline.org/Creeks.html`. Opens on **All creeks**: a card per creek with its status, each gauge's level, rain and tide (tap a card for that creek). Four tiles at the top, one per creek, each showing that creek's current status (Normal, Monitoring, Watch, Warning, Rain trigger, Offline); tap one to switch (`#colma`, `#sanbruno`, `#belmont`, `#atherton` at the end of the URL opens one). **Creeks** tab: NWS alert banner (tap for full text), each stage gauge with its level and thresholds (or "Gauge may be offline" with the last report), rainfall, Belmont's rain triggers, the Bay tide measured vs predicted, and rain / stage / tide graphs on one timeline. The bottom bar (Home · Creeks · Tides · Map · About) is on this page, the tides page and the sensor map; tapping Creeks while viewing a creek returns to All creeks. **About** tab: what the page shows, "In an emergency, call 911", SMC Alert sign-up, contact buttons, and the disclaimer. Follows the phone's dark mode, refreshes automatically, and can be saved to the home screen. |
| `Tides.html` | Bay tides page for phones, at `https://fews.oneshoreline.org/Tides.html`. Redwood City only (Alameda was dropped Oct 13; it is still used by the Creeks graphs for San Bruno and Colma): measured water level (rising/falling, and how far above or below the prediction), the next predicted time above MHHW, a graph of the past 48 hours and next 7 days with tides above MHHW shaded red, and a table of every predicted time above MHHW this week. NWS alert banner on top; same bottom bar as the creek page (Home · Creeks · Tides · Map · About). Below the alert banner, a **King Tides** card that appears only around the County's King Tide windows (see `data/tide_days_lookup_2026-27.json`), and below the station cards a **King Tide season calendar** (Oct 2026 – Apr 2027, labeled as San Francisco astronomical predictions without weather) marking King Tide days, Elevated tide days and the three windows; tap a day for its label. Both hide after Apr 30, 2027. Add `?embed=1` for a dashboard widget version (keeps the King Tides card, hides the calendar). All levels in ft NAVD88. |
| `SanBrunoCreekMobile.html` | Old address of the phone page; forwards to `Creeks.html#sanbruno` so existing links and home-screen shortcuts keep working. |
| `SiteMap.html` | Map of every public OneRain site, for phones and computers, at `https://fews.oneshoreline.org/SiteMap.html`. Markers are colored by status (reporting, Flood Monitoring / Watch / Warning level, not reporting); square markers are rain-only gauges. Tap a site for its latest readings, how long ago they came in, a 24-hour graph, and a link to the full data on OneRain. **List** shows all sites grouped by status; **Rain 24 h** labels each site with its 24-hour rain total. `#site=41102` at the end of the URL opens that site (use the site number OneRain shows in parentheses). |

### Creek data job

| File | Purpose |
|------|---------|
| `data/tide_days_lookup_2026-27.json` | **Tide days of concern, Oct 2026 – Apr 2027**, from San Mateo County Emergency Management's sheet (San Francisco gauge, NOAA 9414290): one row per day with its category (King Tide · Elevated · none) and King Tide window, plus the three windows (Nov 21–28, Dec 20–27, Jan 17–24). The kiosk's Bay Tides tab and `Tides.html` read it for the King Tides line (shown only from 7 days before each King Tide window to its end) and the calendar, showing **dates and labels only**: the County's heights are ft MLLW at San Francisco, while the pages use ft NAVD88 at Redwood City and Alameda. Today is the Pacific-time date; both pages hide the line after the season's end date (Apr 30, 2027). For next season, add a new file in the same format and change `TIDE_DAYS_URL` in both pages. |
| `thresholds.csv` | **All flood thresholds**, one row per threshold: creek, gauge key, type (`stage` or `rain`), minutes (rain only), level (1 Monitoring · 2 Watch · 3 Warning · 4 beyond Warning), name, value (ft or in), `tide_at_least_navd88` (rain only, when the tide must also be high: the creek's NOAA tide in ft NAVD88; e.g. Belmont's 6.32 ft, which is OneRain's 7.5 ft MLLW alarm level converted to NAVD88), source and notes. Edit it on GitHub like a table (pencil icon). Changes reach every page on the next data run (within ~5 minutes). If a row has a mistake, the job keeps the last good thresholds and shows a red ✗ with the row number in the Actions tab. Rain rows count toward the creek's status, like Belmont's flooding-likely triggers. |
| `scripts/creek_config.py` | Creeks and gauges (OneRain sensor IDs), plus each creek's button name, which rain totals it shows (to match its OneRain dashboard), and Belmont's 4-hour rain graph. (Thresholds are in `thresholds.csv`.) The kiosk, phone page, home page and map all read them from the published data. |
| `scripts/fetch_onerain.py` | Reads the last 48 hours of every creek gauge in `creek_config.py` from OneRain's **public** sensor pages (OneRain's data export requires a login; the public pages don't). |
| `scripts/fetch_sites.py` | Reads every **public** site from OneRain's Sites list: its location, each sensor's latest reading, and the last 24 hours for the small graphs and rain totals. Battery/voltage/signal sensors are left out, and sites with no other sensors (e.g. radio repeaters) don't appear. Alert levels for the map are set in `THRESHOLDS` at the top. |
| `.github/workflows/onerain.yml` | GitHub Action that runs both scripts and publishes the results to the **`data`** branch as `creeks.json` (every run, about every 5 minutes; also copied to `sanbruno.json`, its old name) and `sites.json` (about every 15 minutes), replacing them each time (so it doesn't add commits to `main`). |

The kiosk, the phone page and the home page read `https://raw.githubusercontent.com/OneShorelineSMC/oneshorelinefews/data/creeks.json`;
the map and the kiosk's Map tab read `.../data/sites.json`.

---

## Stations, sensors and thresholds

(Current values; `thresholds.csv` is the source.)

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
| All other OneRain sites (map) | OneRain | every site on the public Sites list | Alert colors for the creek gauges above (from `scripts/creek_config.py`) |

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

## Data sources

- **NOAA CO-OPS Tides & Currents API**: tide predictions and measured water levels
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
