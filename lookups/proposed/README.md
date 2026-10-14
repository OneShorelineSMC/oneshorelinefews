# lookups/proposed/ — drafts for the creek status layer (not used by any page yet)

These tables extend the live lookups to more creeks and add a plain-language status to every creek card.
**No page or data job reads this folder**, so editing here can't break anything.

| File | Same columns as | What it adds |
|---|---|---|
| `creeks.csv` | `../creeks.csv` | 10 more creeks (Redwood, Bear, San Francisquito, Los Trancos, San Mateo, Green Hills, Pilarcitos, San Gregorio, Pescadero, Butano), order 5–14 |
| `creek_gauges.csv` | `../creek_gauges.csv` + `source`, `usgs_site`, `role`, `distance_mi`, `confidence`, `open_items` | Stage and rain gauges for those creeks, plus extra hillside rain gauges for the four dashboard creeks |
| `display_text.csv` | `../display_text.csv` | Status words, "What to do", reason lines, summary and banner wording |
| `settings.csv` | `../settings.csv` | Numbers for the status logic, including one **policy switch** (`BE_READY_FROM_RAIN`) |

The rain frequency table itself is already in the live folder (`../rain_frequency.csv`) because nothing reads it yet.

## Moving a row to the live files

Only after the page and data-job code supports it. The pages flag any key they don't know: an unknown key in
`display_text.csv` or `settings.csv` shows "⚠ Settings file problem" on the kiosk, and a creek or gauge without
complete OneRain details stops the data job. So:

1. Fill in every `open_items` item for the row (OneRain `site_id` / `site` / `device_id` / `device` from the
   sensor's page, `reports`, `tidal`), and `checked_by` / `checked_on`.
2. When the code is ready, copy the row into the live file, leaving out the extra columns
   (`source` … `open_items`).
3. Delete it here.

USGS gauges (`source = usgs`) need a small addition to the data job before they can go live; the history pull
`scripts/fetch_usgs.py` shows how to read them.
