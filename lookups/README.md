# lookups/ — the settings staff check and update

Everything the FEWS pages show that someone at OneShoreline should check, sign off on, or update lives in this
folder as a plain table (CSV). You don't need to touch any page code to change these.

| File | What's in it | Read by | When a change shows up |
|---|---|---|---|
| `creeks.csv` | The four dashboard creeks: names, intro and note text, which NOAA tide station, which rain totals (minutes) to show, Belmont's running-rain graph | data job → `creeks.json` → kiosk, home page, Creeks page | next data run (about 5 min) |
| `creek_gauges.csv` | Each creek's stage and rain gauges, mapped to their OneRain sensors; how each stage gauge reports; whether it is tidal | data job | next data run |
| `thresholds.csv` | Flood thresholds (Monitoring / Watch / Warning, ft) for every stage gauge, and rain triggers (in, with minutes and tide level) | data job (also colors the sensor map) | next data run |
| `tide_stations.csv` | NOAA tide stations: MHHW (ft NAVD88) and the MLLW-to-NAVD88 difference | pages directly, and the data job | pages: within about 10 min |
| `settings.csv` | Numbers behind the page logic: the rapidly-rising rule, when a gauge counts as offline or data as delayed, when the NOAA forecast is used, when "higher than predicted" is called out | pages directly | within about 10 min (the kiosk re-reads every 30 min) |
| `display_text.csv` | Wording: disclaimer, 911 line, SMC Alert note, tide explanations, status words on the creek cards, contact details and links | pages directly | within about 10 min (kiosk: 30 min) |

Where each number came from, and who has signed off, is in **[THRESHOLDS_BASIS.md](THRESHOLDS_BASIS.md)**.

## Editing

1. In GitHub, open the file and click the pencil (edit), or download it, edit it in Excel and upload it back to this
   folder with "Add files via upload". If you use Excel, save as **CSV UTF-8 (Comma delimited)**.
2. Don't rename or reorder the columns, and don't change the `key`, `creek` or `gauge` codes in the first columns
   (pages look rows up by them). Add rows freely in `thresholds.csv`.
3. Fill in `checked_by` and `checked_on` (e.g. `SS`, `2026-10-14`) when you check a row. The pages ignore these
   columns; they are your sign-off record.
4. Commit. Check the result on the pages after the times above.

In `display_text.csv`, write plain text. It is always shown as text (HTML tags show up literally). `{station}`
and `{mhhw}` in `mhhw_definition_home` are filled in automatically. Links (`url_...`) must start with `https://`.

## If something is wrong in a file

Nothing goes blank:

- **creeks.csv, creek_gauges.csv, thresholds.csv, tide_stations.csv (data job):** the job keeps using the last
  good settings, keeps publishing creek readings, and the run shows as **failed** in the repo's **Actions** tab with
  the file, row and problem ("thresholds.csv row 5: level must be 1-4 and value a positive number"). GitHub can
  email about failed runs (it goes to whoever last edited the workflow's schedule, per their notification settings).
- **settings.csv, tide_stations.csv, display_text.csv (pages):** a bad value keeps its built-in value. The home
  page's System status card shows a **Settings files** line listing the problem, and the kiosk's bottom bar shows
  "⚠ Settings file problem".

The built-in values are in `lookups.js` (top of the repo). They are only a fallback; the CSV files are what to edit.

## Columns

**creeks.csv** — `creek` code (used in links, e.g. `Creeks.html#belmont`) · `order` on the creek buttons ·
`name` · `short_name` (buttons) · `tide_station` (NOAA number, must be in `tide_stations.csv`) · `rain_windows_min`
(rain totals shown, in minutes, separated by spaces: `15 30 60 180 1440`) · `running_rain_gauge` /
`running_rain_min` / `running_rain_label` (optional running-total graph; its line is that gauge's rain trigger for
the same minutes) · `intro` (sentence under the creek name) · `note` (what the level colors mean).

**creek_gauges.csv** — `creek` · `gauge` code (used in `thresholds.csv`; don't change it once data exists) ·
`type` (`stage` or `rain`) · `label` (short name on the pages) · `site_name` (stage: full OneRain site name) ·
`where` (rain: e.g. "upper watershed") · `onerain_number` · `site_id`, `site`, `device_id`, `device` (from the
sensor's OneRain page address: Sites › site › sensor) · `reports` (stage: `on change` if OneRain only stores a
reading when the level changes, `interval` if on a schedule; sets how long a silence means "offline") · `tidal`
(stage: `yes` if the level rises and falls with the tide; such gauges count as "rapidly rising" only after rain) ·
`note` (shown with the gauge's thresholds).

**thresholds.csv** — `creek` · `gauge` · `gauge_name` (for people; not used) · `type` (`stage` or `rain`) ·
`minutes` (rain only) · `level` (1 Flood Monitoring, 2 Flood Watch, 3 Flood Warning, 4 above Flood Warning; sets
the color) · `name` (shown; blank = the standard name for the level) · `value` (ft for stage, in for rain) ·
`tide_at_least_navd88` (rain + tide triggers: tide at the creek's station at or above this, ft NAVD88) · `source`
· `notes` (shown with the threshold).

**tide_stations.csv** — `station` (NOAA number) · `name` · `mhhw_navd88_ft` (the "average high tide" line on every
tide graph and the threshold for "above MHHW") · `mllw_to_navd88_ft` (add to a MLLW height to get NAVD88; used to
show OneRain's Redwood City tide in NAVD88 on the sensor map) · `used_for` · `source`.

**settings.csv** — `key` · `value` · `unit` · `used_on` · `what_it_does`. Each value has an allowed range (in
`lookups.js`); a value outside it is ignored and reported.

**display_text.csv** — `key` · `text` · `shown_on` · `notes`.

## Not in these files (still in page code)

- Sentence structure of the computed lines (e.g. "Tides higher than an average high tide: today about 1–3:30 PM"),
  page headings and button names.
- Level colors (yellow / orange / red / purple) — part of the design and the color-blind checks.
- Kiosk display settings (tab rotation, burn-in shift, refresh timing) — top of `ShorelineKiosk.html`.
- County King Tide dates — `data/tide_days_lookup_2026-27.json` (its source line is `king_tide_source` here).
