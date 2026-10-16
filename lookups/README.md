# lookups/ — the settings staff check and update

Everything the FEWS pages show that someone at OneShoreline should check, sign off on, or update lives in this
folder as a plain table (CSV). You don't need to touch any page code to change these.

| File | What's in it | Read by | When a change shows up |
|---|---|---|---|
| `creeks.csv` | The four dashboard creeks: names, intro and note text, which NOAA tide station, which rain totals (minutes) to show, Belmont's running-rain graph | data job → `creeks.json` → kiosk, home page, Creeks page | next data run (about 5 min) |
| `creek_gauges.csv` | Each creek's stage and rain gauges, mapped to their OneRain sensors; how each stage gauge reports; whether it is tidal | data job | next data run |
| `thresholds.csv` | Flood thresholds (Monitoring / Watch / Warning, ft) for every stage gauge, and rain triggers (in, with minutes and tide level) | data job (also colors the sensor map) | next data run |
| `tide_stations.csv` | NOAA tide stations: MHHW (ft MLLW) and, for reference, how far NAVD88 is above MLLW | pages directly, and the data job | pages: within about 10 min |
| `settings.csv` | Numbers behind the page logic: the rapidly-rising rule, when a gauge counts as offline or data as delayed, when the NOAA forecast is used, when "higher than predicted" is called out, flood reports (`REPORTS_*`) | pages directly (`REPORTS_*` also the data job) | within about 10 min (the kiosk re-reads every 30 min) |
| `display_text.csv` | Wording: disclaimer, 911 line, SMC Alert note, tide explanations, status words on the creek cards, contact details and links, the Report page and flood report labels (`report_*`, `url_report_form`: blank = reporting not open) | pages directly | within about 10 min (kiosk: 30 min) |
| `rain_frequency.csv` | Rain depths (in) for the 1-, 2- and 5-year storms at each rain gauge and duration (15 min – 48 hr), from NOAA Atlas 14, with the level they set (1 Heavy · 2 Very heavy · 3 Severe) and 10/25/100-year values for reference | data job (creek status layer, staff preview) | next data run |
| `creek_facts.csv` | Each creek's cities and communities, where it drains, and a short description, for the fact sheets | fact sheets only | next fact-sheet rebuild |
| `gauge_facts.csv` | Each creek gauge's record, reporting pattern, history and known issues, for the fact sheets | fact sheets only | next fact-sheet rebuild |
| `rising_fast_results.csv` | Rising-fast results per gauge, written by `scripts/evaluate_rising_fast.py` (don't edit by hand) | fact sheets only | when the evaluation is rerun |
| `factsheets/` | **One fact sheet per creek, generated** from the tables above by `scripts/build_creek_factsheets.py` (the **Rebuild creek fact sheets** Action reruns it whenever a table changes). Don't edit these pages; edit the tables. | — | automatic |
| `proposed/` | Drafts for the creek status layer: 10 more creeks and their gauges. See `proposed/README.md` | **not read** | — |

Where each number came from, and who has signed off, is in **[THRESHOLDS_BASIS.md](THRESHOLDS_BASIS.md)**.
The "rapidly rising" rule and each gauge's setting are explained in **[RISING_FAST_BASIS.md](RISING_FAST_BASIS.md)**.

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
the same minutes) · `intro` (sentence under the creek name) · `note` (what the level colors mean) · `preview_only`
(`yes` = staff preview only: the creek appears only on pages opened with `?preview=1`, never on the public pages;
`tide_station` may be blank for these).

**creek_gauges.csv** — `creek` · `gauge` code (used in `thresholds.csv`; don't change it once data exists) ·
`type` (`stage` or `rain`) · `label` (short name on the pages) · `site_name` (stage: full OneRain site name) ·
`where` (rain: e.g. "upper watershed") · `onerain_number` · `site_id`, `site`, `device_id`, `device` (from the
sensor's OneRain page address: Sites › site › sensor) · `reports` (stage: `on change` if OneRain only stores a
reading when the level changes, `interval` if on a schedule; sets how long a silence means "offline") · `tidal`
(stage: `yes` if the level rises and falls with the tide; such gauges count as "rapidly rising" only after rain) ·
`rise_ft` (stage: how much the level must rise in an hour to count as "rapidly rising" at this gauge, in ft from
0.05 to 10; `off` = not used here; blank = `RISE_FT` in settings.csv; basis in `RISING_FAST_BASIS.md`) ·
`note` (shown with the gauge's thresholds) · `role` (optional; rain: blank or `primary` = shown on the pages,
`supporting` = a hillside gauge that only counts toward the creek's rain level in the creek status layer; OneRain
`onerain_number` can be letters and digits, e.g. `PUL`) · `source` (blank/`onerain`, or `usgs` for a USGS stream
gauge: then fill `usgs_site` with the USGS number and leave the OneRain columns blank; its gage height is read from USGS).

**thresholds.csv** — `creek` · `gauge` · `gauge_name` (for people; not used) · `type` (`stage` or `rain`) ·
`minutes` (rain only) · `level` (1 Flood Monitoring, 2 Flood Watch, 3 Flood Warning, 4 above Flood Warning; sets
the color) · `name` (shown; blank = the standard name for the level) · `value` (ft for stage, in for rain) ·
`tide_at_least_mllw` (rain + tide triggers: tide at the creek's station at or above this, ft MLLW) · `source`
· `notes` (shown with the threshold).

**tide_stations.csv** — `station` (NOAA number) · `name` · `mhhw_mllw_ft` (the "average high tide" line on every
tide graph and the threshold for "above MHHW", ft MLLW) · `navd88_above_mllw_ft` (reference only, for comparing with NAVD88
documents; nothing is converted) · `used_for` · `source`. All tide heights are ft MLLW, NOAA's datum for the gauges.

**settings.csv** — `key` · `value` · `unit` · `used_on` · `what_it_does`. Each value has an allowed range (in
`lookups.js`); a value outside it is ignored and reported.

**display_text.csv** — `key` · `text` · `shown_on` · `notes`.

**rain_frequency.csv** — `onerain_number` (rain gauge) · `gauge` (its code in `creek_gauges.csv`, if it's already live) ·
`site_name` · `minutes` (duration) · `ari_years` (the storm: 1-, 2-, 5-, 10-, 25-, 100-year) · `aep_pct` (chance in any year)
· `level` (1 Heavy, 2 Very heavy, 3 Severe; blank = reference only; **edit this column to change the cutoffs**) · `name` ·
`value_in` · `lat` / `lon` (where NOAA's estimate is for) · `source` · `notes`. Regenerate the depths with the
**Atlas 14 pull** workflow (`scripts/fetch_atlas14.py`) rather than editing them by hand.

## Not in these files (still in page code)

- Sentence structure of the computed lines (e.g. "Tides higher than an average high tide: today about 1–3:30 PM"),
  page headings and button names.
- Level colors (yellow / orange / red / purple) — part of the design and the color-blind checks.
- Kiosk display settings (tab rotation, burn-in shift, refresh timing) — top of `ShorelineKiosk.html`.
- King Tide days and the high tide calendar are worked out from NOAA's Redwood City tide table each time (`tide_season.js`); the flood level is `TIDE_RED_FT_RWC` in `settings.csv`.
