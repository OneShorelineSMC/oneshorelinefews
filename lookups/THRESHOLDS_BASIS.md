# FEWS thresholds: basis, data sources and sign-off

What each number on the FEWS pages is, where it came from, and whether it has been checked. The numbers
themselves live in the CSV files in this folder (see [README.md](README.md)); this file explains them.

**Status key:** **Confirmed** = checked against its source and signed off · **From source, not yet signed off** ·
**Provisional** = a working value, expected to change · **To document** = the basis isn't written down yet.

Fill in "Checked by / on" here (and in the CSV row's `checked_by` / `checked_on`) when a value is reviewed.

---

## 1. Creek flood thresholds (stage, ft) — `thresholds.csv`

All stage values are **gauge height in feet at each OneRain sensor** (the gauge's own zero), not a tidal datum.
Source for all rows: the OneRain sensor threshold settings, copied October 2026.

| Creek · gauge | Monitoring | Watch | Warning | Above Warning | Meaning of the levels | Status | Checked by / on |
|---|---|---|---|---|---|---|---|
| Colma · Orange Memorial Park (41101) | 3.40 | 5.00 | 6.75 | — | 50% / 75% / 100% channel capacity exceedance downstream (100% = flooding likely) | From source, not yet signed off | |
| San Bruno · First Avenue (41102) | 2.40 | 3.60 | 4.80 | — | **To document** (no meaning recorded; gauge is tidal) | To document | |
| Belmont · Old County Rd (41104) | 2.25 | 3.25 | 4.00 | — | 50% / 75% / 100% channel capacity exceedance downstream | From source, not yet signed off | |
| Atherton · Alameda de las Pulgas (41107) | 3.18 | 4.60 | 5.65 | 10.40 "Roadway Flooded" (water detected on road) | 50% / 75% / 100% channel capacity downstream of Caltrain | From source, not yet signed off | |
| Atherton · upstream of Caltrain (41106) | 2.80 | 4.10 | 5.50 | — | same as above; probe is 0.37 ft above channel bottom | From source, not yet signed off | |

Open questions:
- Who set the OneRain thresholds and from what analysis (hydraulic model, surveyed bank/road elevations,
  observed events)? Record the study or memo here.
- San Bruno at First Avenue: what the three levels mean, and whether they hold at high tide (the gauge rises
  and falls with the tide). Gauge zero in NAVD88 is unknown, so stage can't yet be compared with the tide.

## 2. Rain triggers — `thresholds.csv`

Only Belmont Creek has rain triggers. Colma, San Bruno and Atherton have none (see open items).

| Trigger | Value | Basis / source | Status | Checked by / on |
|---|---|---|---|---|
| Belmont 30-minute rain | ≥ 0.20 in at Old County Rd rain gauge | Belmont Creek OneRain dashboard (Oct 2026) | From source; **confirm against its OneRain alarm rule** | |
| Belmont 4-hour rain + high tide | ≥ 0.42 in and Redwood City tide ≥ 6.32 ft NAVD88 | OneRain alarm rule "Rainfall and Tide (Belmont)" #34: 4 Hr Accumulation ≥ 0.42 in and OneRain Redwood City Tide Elevation ≥ 7.5 ft. OneRain's tide is MLLW; 7.5 − 1.18 = 6.32 ft NAVD88. Rain value from analysis of 2022–2025 events. | From source; **rule #34 shows "Off" in OneRain — check whether its emails are sent** | |

Open: rain thresholds for color-coding rain totals on the other creeks (amounts per window and level), and
whether they should count toward creek status.

## 3. Rain totals shown — `creeks.csv` (`rain_windows_min`)

| Creek | Windows | Basis | Status | Checked by / on |
|---|---|---|---|---|
| Colma | 1 hr, 6 hr, 24 hr | Match the creek's OneRain dashboard | From source | |
| San Bruno | 15 min, 30 min, 1 hr, 3 hr, 24 hr | Very flashy creek; short windows added Oct 13, 2026 (Summer). 3 hr chosen as the middle window. | Provisional | |
| Belmont | 30 min, 1 hr, 4 hr, 24 hr | OneRain dashboard + its 30-min and 4-hr triggers | From source | |
| Atherton | 30 min, 1 hr, 24 hr | Match the creek's OneRain dashboard | From source | |

With two rain gauges (San Bruno), the creek cards show the larger of the two totals for each window.

## 4. Tide reference levels — `tide_stations.csv`

All tide heights on the pages are **ft NAVD88**. NOAA station datums (current National Tidal Datum Epoch).

| Station | MHHW (ft NAVD88) | Basis | Status | Checked by / on |
|---|---|---|---|---|
| Redwood City 9414523 | 7.02 | NOAA datums: MHHW 8.20 ft MLLW; NAVD88 is 1.18 ft above MLLW | From source, not yet signed off | |
| Alameda 9414750 | 6.37 | NOAA datums for 9414750 | **Verify against the NOAA datums page** | |

**MHHW is a placeholder threshold.** It is the "average high tide" line on every tide graph, the threshold for
"tides above MHHW" (Bay Tides tab, Tides page, home page), and the high-tide test for any rain trigger without its
own tide level. OneShoreline intends to replace it with tide levels tied to known impacts.

Redwood City datum crosswalk (NOAA datums page; NAVD88 = MLLW − 1.18 ft), for reference and the planned
datums page:

| Datum | ft MLLW | ft NAVD88 |
|---|---|---|
| Highest observed | 10.79 | 9.61 |
| Highest astronomical tide (HAT) | 9.71 | 8.53 |
| MHHW | 8.20 | 7.02 |
| Belmont rule #34 tide level | 7.50 | 6.32 |
| MHW | 7.57 | 6.39 |
| MSL | 4.40 | 3.22 |
| NAVD88 zero | 1.18 | 0.00 |
| MLLW | 0.00 | −1.18 |

San Francisco 9414290 (County King Tide dates): NAVD88 ≈ MLLW + 0.06 ft.

`mllw_to_navd88_ft` (−1.18 for Redwood City) also converts OneRain's Redwood City tide readings (MLLW) to NAVD88 on
the sensor map. Alameda's is blank because its OneRain tide site isn't public.

## 5. Page logic settings — `settings.csv`

| Setting | Value | Basis | Status | Checked by / on |
|---|---|---|---|---|
| Rapidly rising: rise | 0.5 ft in 60 min, newest reading < 90 min old | Working rule set Oct 2026 to flag fast rises on the home page | **Provisional** — logic TBD | |
| Rapidly rising: tidal gauges | only after ≥ 0.10 in rain in 3 hr (San Bruno at First Avenue, `tidal = yes`) | Stops every high tide from counting as a rapid rise | **Provisional** | |
| Rapidly rising: time to next level | shown if within 3 hr | Working choice | Provisional | |
| Gauge offline | 12 hr silent (gauges that report on change), 3 hr (scheduled gauges) | On-change gauges can be silent for hours when the level is steady; set to avoid false "offline" | Working choice, review | |
| Creek data delayed | 30 min | Data job runs every 5 min; 30 min = several missed runs | Working choice | |
| Map site not reporting / old reading / data late | 24 hr / 3 hr / 45 min | Map data refreshes every 15 min | Working choice | |
| NOAA model forecast used | download < 12 hr old and reaching ≥ 6 hr ahead | Model runs 4×/day; older or shorter runs are dropped and the pages fall back to predictions | Working choice | |
| "Higher than predicted" called out | ≥ 0.2 ft (red at ≥ 0.5 ft); average of the last 4 high tides | Working threshold so small differences aren't called out | Working choice, review | |

## 6. Wording — `display_text.csv`

| Item | Status | Checked by / on |
|---|---|---|
| Disclaimer (full and short) | Existing OneShoreline text | |
| SMC Alert note ("This site does not send alerts…") | **Confirm with San Mateo County** that nothing in OneRain or FEWS sends SMC Alert automatically | |
| 911 lines | | |
| Tide explanations (MHHW definition, NOAA forecast note, causes incl. El Niño) | | |
| Creek status words | Pages use different words today (e.g. "Rain trigger" vs "Flooding likely (rain)", "Offline" vs "Gauge offline", "Delayed" vs "Data delayed"); decide whether to make them match | |
| Contact details and links | | |

## 7. Gauge mapping — `creek_gauges.csv`

Each gauge's OneRain ids were copied from its OneRain sensor page in October 2026. Check that each row points to
the intended sensor (open the link from the creek page's "thresholds & notes" or the sensor map) and that
`reports` (on change / interval) matches how the gauge logs. Checked by / on: ______

## Data sources

| Data | Source | How the pages get it | Refresh |
|---|---|---|---|
| Creek stage and rain | OneShoreline Early Warning System (OneRain), public sensor pages | GitHub Action (`.github/workflows/onerain.yml`) reads them and publishes `creeks.json` on the repo's `data` branch | every 5 min |
| All public monitoring sites (sensor map) | OneRain public site pages | same Action, `sites.json` | every 15 min |
| Bay tide: measured, predicted | NOAA Tides & Currents (CO-OPS) API, products `water_level` and `predictions`, `datum=NAVD`, local time | read by each page in the browser | 6 min / hourly |
| Bay tide: NOAA model forecast | NOAA CO-OPS API product `ofs_water_level` (San Francisco Bay Operational Forecast System), `datum=NAVD` | read by each page | hourly (model runs 4×/day) |
| NWS alerts | api.weather.gov active alerts, San Mateo County (SAME 006081) | read by each page | 3 min |
| NWS forecast notes on tides | api.weather.gov Area Forecast Discussion, office MTR (San Francisco Bay Area) | kiosk and Tides page | 30 min |
| King Tide dates | San Mateo County Emergency Management, "Tide days of concern, Oct 2026 to Apr 2027" (San Francisco gauge, astronomical) → `data/tide_days_lookup_2026-27.json` | kiosk and Tides page | as published |
| Tide datums | NOAA Tides & Currents datums pages for each station | entered in `tide_stations.csv` | when NOAA updates the epoch |

## Sign-off log

| Date | Who | What was checked / changed | Files |
|---|---|---|---|
| | | | |
