# lookups/proposed/ — drafts for the creek status layer (not used by any page yet)

These tables extend the live lookups to more creeks and add a plain-language status to every creek card.
**No page or data job reads this folder**, so editing here can't break anything.

| File | Same columns as | What it adds |
|---|---|---|
| `creeks.csv` | `../creeks.csv` | 10 more creeks (Redwood, Bear, San Francisquito, Los Trancos, San Mateo, Green Hills, Pilarcitos, San Gregorio, Pescadero, Butano), order 5–14 |
| `creek_gauges.csv` | `../creek_gauges.csv` + `source`, `usgs_site`, `role`, `distance_mi`, `confidence`, `open_items` | Stage and rain gauges for those creeks, plus extra hillside rain gauges for the four dashboard creeks |

The rain frequency table itself is already in the live folder (`../rain_frequency.csv`) because nothing reads it yet.

## Moving a row to the live files

Only after the page and data-job code supports it. The pages flag any key they don't know: an unknown key in
`display_text.csv` or `settings.csv` shows "⚠ Settings file problem" on the kiosk, and a creek or gauge without
complete OneRain details stops the data job. So:

1. Fill in every `open_items` item for the row (OneRain `site_id` / `site` / `device_id` / `device` from the
   sensor's page, `reports`, `tidal`), and `checked_by` / `checked_on`. For OneRain sites that are public, the ids
   were pre-filled on Oct 14 from OneRain's public site list: open the sensor link to check them. Sites marked
   NOT PUBLIC can't be read until OneRain makes them public.
2. When the code is ready, copy the row into the live file, leaving out the extra columns
   (`source`, `usgs_site`, `distance_mi`, `confidence`, `open_items`). Keep `role`: hillside rain gauges for the four
   dashboard creeks go in as `supporting` (so they count toward the rain level without changing the rain tables).
3. Delete it here.

**Moved to the live files (Oct 14):** the status wording (`verdict_*`, `why_*`, `rain_*`, `trend_*`, `summary_*`,
`banner_likely`, `evac_button`, `url_evacuation`, …) is now in `../display_text.csv` and the status numbers
(`RAIN_SEVERE_CONFIRM_GAUGES`, `RAIN_SILENT_MIN`, `TREND_*`, `TIDE_RISING_LOOKAHEAD_HOURS`, `BE_READY_FROM_RAIN`) in
`../settings.csv`; `lookups.js` and the data job know them. Colma's San Bruno Mountain gauge is live as a supporting
rain gauge.

**Ready in code (Oct 14):** letter-and-digit OneRain numbers (PUL, A0835678 …) and `role = supporting` rain gauges.
Rain levels and creek trends are computed by the data job and written into `creeks.json`; no page shows them yet.

USGS gauges (`source = usgs`) need a small addition to the data job before they can go live; the history pull
`scripts/fetch_usgs.py` shows how to read them.
