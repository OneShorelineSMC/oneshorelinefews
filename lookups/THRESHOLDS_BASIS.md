# FEWS thresholds: basis, data sources and sign-off

What each number on the FEWS pages is, where it came from, and whether it has been checked. The numbers
themselves live in the CSV files in this folder (see [README.md](README.md)); this file explains them.

**Status key:** **Confirmed** = checked against its source and signed off · **From source, not yet signed off** ·
**Provisional** = a working value, expected to change · **To document** = the basis isn't written down yet.

Fill in "Checked by / on" here (and in the CSV row's `checked_by` / `checked_on`) when a value is reviewed.

---

## Terms

**Names.** **OneRain** is the County's existing gauge system and its dashboards, which many staff call "FEWS".
**FEWS 2026 Update** ("2026 Update" for short) is the new public creek and tide status site in this repository, built
on OneRain's gauge data. In this document "FEWS" means the 2026 Update; the fact sheets say "2026 Update" throughout
and compare it with OneRain.

**Shared vocabulary** (fact sheets, review workbook and meetings):
- **Threshold:** any set value that changes a color or a status, in either system.
- **Flood level** and **indicator:** the two kinds of 2026 Update threshold. An indicator is shown on the page (the
  rain indicator Heavy / Very heavy / Intense, and rising fast); below and in RISING_FAST_BASIS.md it is sometimes still
  called an "alert" or "alert level". It is never a text message.
- **Status:** the 2026 Update's one overall message per creek (Flooding likely, Be ready, Stay alert, No alerts).
- **OneRain threshold:** a named level on a OneRain sensor (e.g. Flood Watch, 3.25 ft); it colors that gauge's readings
  and graph and has a OneRain severity (Informational, Warning, Alert, Critical). It sends nothing by itself.
- **OneRain dashboard color:** a green/orange/red range on a OneRain dashboard reading, set separately from thresholds.
- **Text alert:** a text message sent to people. Only OneRain sends these (to Public Works and emergency responders),
  through *alarm* rules (Administration > Alarms), which may use thresholds. The 2026 Update sends no text alerts.

FEWS uses "threshold" for three different kinds of value. Only the first says anything about flooding.

**Threshold:** a set value of something FEWS measures (creek height, a rain total, or how fast the creek rises) at
which the pages change what they show or who is alerted.

| Kind | What it says | Tied to flooding? | Where it's set | Creeks |
|---|---|---|---|---|
| **Flood level** | The creek (or rain) has reached a point linked to an effect downstream, such as how full the channel is or water on a road | **Yes**, if its meaning is recorded | `thresholds.csv` (§1 creek heights, §2 rain triggers) | Colma, San Bruno, Belmont, Atherton |
| **Rain alert level** | How rare the rain is at a gauge: Heavy = 1-year, Very heavy = 2-year, Intense = 5-year storm | No: rainfall frequency isn't flood frequency | `rain_frequency.csv` (§8) | All |
| **Rising fast** (an alert level) | How quickly the creek is rising, e.g. 0.5 ft in an hour | No: a rate, not a height | `creek_gauges.csv` `rise_ft`, `settings.csv` (§11) | All with a creek gauge |

Notes:
- **Not every flood level means flooding.** On Colma, Belmont and Atherton, Flood Monitoring and Flood Watch are 50%
  and 75% of the channel's capacity downstream, so the water is still in the channel. Only Flood Warning (100%,
  "flooding likely") and Atherton's Roadway Flooded mean water outside the channel. Nobody has recorded what San
  Bruno's levels mean, and nobody has recorded who set any of the OneRain levels, or from what study (§1).
- **Belmont's rain triggers** are flood levels for rain: they set the creek to "Flooding likely". The rain + tide
  value came from an analysis of 2022–2025 events (§2).
- **OneRain's own levels** (checked Oct 17, 2026 from OneRain's public sensor pages): the Colma, San Bruno, Belmont and
  Atherton gauges carry the same levels as FEWS. OneRain also set flood levels on four USGS gauges that FEWS had no
  levels for (San Francisquito at Stanford, Pilarcitos at Half Moon Bay, San Gregorio, Pescadero); FEWS adopted them
  on Oct 17, 2026 (§1). Butano Creek near Cloverdale Road's OneRain levels (on its backup sensor) are used for Butano Creek since Oct 20, 2026. Who set them, and from what, isn't recorded; some upper levels were never reached in 2008–2026 (for
  example Pilarcitos Flood Warning 17.0 ft against a highest reading of 14.64 ft, Dec 31, 2022). Values and how often the
  USGS record reached each one are in `onerain_dashboard_thresholds.csv` and on the fact sheets.
- **Big-storm level** is used only to test rising fast ([RISING_FAST_BASIS.md](RISING_FAST_BASIS.md) §5). It is the
  gauge's lowest flood level (Flood Monitoring) where there is one. Otherwise it is the median yearly peak, a typical
  yearly high (about a 2-year event). That is a statistical stand-in, **not** a flood level. On those creeks, "big
  storms warned first" means warned before a typical yearly high, not before flooding.

**Linked to flooding** (shown on each [fact sheet](factsheets/README.md)):

| | Meaning | Creeks |
|---|---|---|
| **Yes** | Flood levels at the creek gauge, with their meaning recorded | Colma, Belmont, Atherton |
| **Partly** | Flood levels are set, but their meaning isn't recorded | San Bruno |
| **Yes (OneRain's levels, Oct 17)** | Flood levels copied from OneRain, with OneRain's own descriptions; basis not recorded | San Francisquito, Pilarcitos, San Gregorio, Pescadero, San Mateo (converted from flow) |
| **No** | Indicators only: status comes from rain and rising fast | Green Hills |

**To link a creek to flooding:** find the creek height at each gauge where the creek leaves its banks or floods a
road. Sources: a survey of the bank and road elevations tied to the gauge's zero, a hydraulic study, or a past flood
with gauge readings at the time (for example, Green Hills on Nov 17, 2025). Where the National Weather Service
publishes a flood stage for a USGS gauge, record it as a starting point. Then add the levels to `thresholds.csv`
with their meaning and source, and the creek's status will use them ahead of the alert levels (§10).

---

## 1. Creek flood levels (stage, ft) — `thresholds.csv`

All stage values are **gauge height in feet at each OneRain sensor** (the gauge's own zero), not a tidal datum.
Source for all rows: the OneRain sensor threshold settings, copied October 2026. The four USGS-gauge rows were added
on Oct 17, 2026 so the 2026 Update matches OneRain where it had no levels of its own (staff decision); they apply to
those creeks' status, which is staff preview only for now. Green Hills and Pescadero at Stage Road have no OneRain levels;
San Mateo's are on flow and are converted (row below). For USGS gauges, gauge height is the USGS gauge height, the same number OneRain shows.

| Creek · gauge | Monitoring | Watch | Warning | Above Warning | Meaning of the levels | Status | Checked by / on |
|---|---|---|---|---|---|---|---|
| Colma · Orange Memorial Park (41101) | 3.40 | 5.00 | 6.75 | — | 50% / 75% / 100% channel capacity exceedance downstream (100% = flooding likely) | From source, not yet signed off | |
| San Bruno · First Avenue (41102) | 2.40 | 3.60 | 4.80 | — | **To document** (no meaning recorded; gauge is tidal) | To document | |
| Belmont · Old County Rd (41104) | 2.25 | 3.25 | 4.00 | — | 50% / 75% / 100% channel capacity exceedance downstream | From source, not yet signed off | |
| Atherton · Alameda de las Pulgas (41107) | 3.18 | 4.60 | 5.65 | 10.40 "Roadway Flooded" (water detected on road) | 50% / 75% / 100% channel capacity downstream of Caltrain | From source, not yet signed off | |
| Atherton · upstream of Caltrain (41106) | 2.80 | 4.10 | 5.50 | — | same as above; probe is 0.37 ft above channel bottom | From source, not yet signed off | |
| San Francisquito · Stanford (USGS 11164500) | 11.00 | 12.00 | 12.80 | — | OneRain's descriptions: potential flooding / flooding likely / projected flooding in downstream reaches | From OneRain, added Oct 17, 2026; not yet signed off | |
| Pilarcitos · Half Moon Bay (USGS 11162630) | 7.50 | 9.10 | 17.00 | 24.00 "Major Flood Stage" (damaging flooding) | OneRain's descriptions: potential flooding / flooding probable with continued rain / flooding likely in downstream reaches. Flood Warning and Major were never reached in WY2008–2026 (highest 14.64 ft, Dec 31, 2022) | From OneRain, added Oct 17, 2026; **check the upper levels** | |
| San Gregorio · San Gregorio (USGS 11162570) | 15.00 | 17.70 | 21.00 | 25.00 "Major Flood Stage" (damaging flooding) | OneRain's descriptions, as for Pilarcitos. Flood Warning and Major never reached in WY2008–2026 (highest 18.74 ft) | From OneRain, added Oct 17, 2026; **check the upper levels** | |
| Pescadero · near Pescadero (USGS 11162500) | — | 11.20 | 13.25 | — | OneRain's descriptions: Watch = flooding likely; Warning = projected flooding in downstream reaches. OneRain has no Monitoring level here | From OneRain, added Oct 17, 2026; not yet signed off | |
| San Mateo · below Crystal Springs Reservoir (USGS 11162753) | — | 6.70 | 7.00 | — | OneRain sets these on **flow**: Watch = 200 cfs ("flooding probable with continued rain"), Warning = 250 cfs ("active flooding likely to occur downstream"). Converted to gauge height from paired USGS readings, 2023–2026 (200 cfs ≈ 6.70 ft, 250 cfs ≈ 6.98 ft). The rating can shift; recheck after big storms. Flow reached 200 cfs in 3 and 250 cfs in 2 of 19 water years (highest 326 cfs, WY2017) | From OneRain, converted; added Oct 17, 2026; not yet signed off | |

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

**Datum decision (Oct 16):** the pages switched to ft MLLW on Oct 16 (NOAA's native datum) and went back to NAVD88 the same day. The flood level (8.5), the King Tide / 1-year tide (8.3), the SF Bay Tidal Datums and Extreme Tides Study and staff and partners all use NAVD88. The pages ask NOAA for `datum=NAVD`, so NOAA applies its own published offset (NAVD88 = MLLW − 1.18 ft at Redwood City); there is no conversion of ours to go wrong. Older reports can use a slightly different offset (the 2016 study's NOAA table gives −1.10 at Redwood City, about 0.08 ft off today's).

| Station | MHHW (ft NAVD88) | Basis | Status | Checked by / on |
|---|---|---|---|---|
| Redwood City 9414523 | 7.02 | NOAA datums: MHHW 8.20 ft MLLW; NAVD88 is 1.18 ft above MLLW | From source, not yet signed off | |
| Alameda 9414750 | 6.37 | NOAA datums for 9414750 | **Verify against the NOAA datums page** | |
| Monterey 9413450 (Coastside Tides) | 5.48 | NOAA datums API, epoch 1983–2001 (checked Oct 16): MHHW 8.72 and NAVD88 3.24 ft above station datum; MHHW 5.34 ft MLLW; MLLW is 0.14 ft above NAVD88; HAT 7.21 ft NAVD88. NOAA West Coast OFS (WCOFS) station, so the NOAA projection is available | From source, not yet signed off | |

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


`mllw_to_navd88_ft` (−1.18 for Redwood City) also converts OneRain's Redwood City tide readings (MLLW) to NAVD88 on
the sensor map. Alameda's is blank because its OneRain tide site isn't public.

**FYI: NOAA's derived high tide flood thresholds (reference only; not used by the pages).** NOAA's Coastal
Inundation Dashboard shows "minor / moderate / major flooding" lines at each tide station (Alameda: minor flooding
at 8.5 ft MLLW). Where the National Weather Service has not set official coastal flood levels, these come from
*Patterns and Projections of High Tide Flooding Along the U.S. Coastline Using a Common Impact Threshold* (Sweet et
al., NOAA Technical Report NOS CO-OPS 086, 2018), which fitted official NOAA thresholds at tide gauges against each
gauge's tide range (GT = MHHW − MLLW):

- **Minor:** 1.04 × GT + 0.50 m above MLLW, i.e. about 0.5 m (1.6 ft) plus 4% of the tide range above MHHW
  (§2.0, Figure 3, p. 8; fitted at 66 gauges, ±0.19 m). This is the threshold NOAA uses to count high tide flood days.
- **Moderate / major:** the report gives 0.80 m (±0.25) and 1.17 m (±0.39) plus a "3–4%" tide-range factor; the
  exact factors weren't in the text we read, so the values below use 1.03 and 1.04 and are **approximate**.
- The report says derived thresholds are "not to supplant knowledge about local flood risk"; NWS levels, where set,
  are for emergency response and can differ.

| Station | GT | Minor | Moderate (approx.) | Major (approx.) |
|---|---|---|---|---|
| Redwood City 9414523 | 8.20 ft (MHHW, from this table) | 10.2 ft MLLW = **9.0 ft NAVD88** (2.0 ft above MHHW) | 11.1 ft MLLW = 9.9 ft NAVD88 | 12.4 ft MLLW = 11.2 ft NAVD88 |
| Alameda 9414750 | about 6.6 ft (backed out of NOAA's 8.5; to verify on the NOAA datums page) | 8.5 ft MLLW (NOAA dashboard) = about 8.3 ft NAVD88 | about 9.4 ft MLLW | about 10.7 ft MLLW |

Our provisional Redwood City flood level (`TIDE_RED_FT_RWC`, 8.5 ft NAVD88, §5) is about 0.5 ft below NOAA's derived
minor threshold there. That can be right (it is a staff working level for low spots near the Bay), but it is worth
weighing when the level is confirmed against known flooding. The official values can be read from NOAA's metadata API
(`https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/<id>/floodlevels.json`: `nos_minor`,
`nos_moderate`, `nos_major`, `nws_minor` …; datum not stated in the docs, to confirm); not yet read here.

### 4b. After the NOAA projection: the tide table plus the recent offset (Oct 21, 2026; provisional)

NOAA's projection (its Bay and West Coast models, `ofs_water_level`) runs about 48 hours ahead. After that the pages
used only the tide table, which leaves out a Bay that has been running high for weeks (for example in an El Niño
winter). Since Oct 21, 2026 the Tides page and the kiosk add the **recent offset** to the tide table after the
projection ends:

- **Offset** (`scripts/tide_offset.py`, data branch `tide_offset.json`, once a day): for each of the last
  `BAY_OFFSET_DAYS` (30) whole days, the day's average of NOAA's measured water level minus NOAA's tide table at the
  station (6-minute data; a day counts if at least 80% of its readings are there); the offset is the average of those
  daily averages, if at least two thirds of the days count. Redwood City, Alameda and Monterey.
- **Why daily averages over a month:** a storm surge lasts hours to a day or two, so it moves a 30-day average of daily
  means very little (a 2 ft surge for 6 hours moves it about 0.02 ft); slow rises that last weeks to months, such as
  El Niño, stay in. This is persistence of the mean sea level anomaly, which NOAA's high tide flooding research found
  adds skill at 1–3 month leads, especially on the West Coast (Dusek et al. 2022, *Frontiers in Marine Science*,
  doi:10.3389/fmars.2022.1073792).
- **Shown** only when the water has run at least `BAY_OFFSET_MIN_FT` (0.1 ft) **higher** than the tide table, the offset
  is less than `BAY_OFFSET_MAX_AGE_HOURS` (48) old, and `BAY_OFFSET_SHOW` = 1: a thin gray dotted line on the Tides page
  graph after the projection; "≈ x ft if the Bay stays high" in the day list; a gray dotted ring on calendar days the
  offset would take to the flood level (`TIDE_RED_FT_RWC`), no more than `BAY_OFFSET_AHEAD_DAYS` (30) ahead; the kiosk's Later line and look-ahead screen.
- **Never** changes a color, the headline, the King Tide stars or any creek status. Wording says it is an assumption
  ("if the Bay stays this high"), not a forecast; storms can add more.
- Not used: NOAA's Annual and Monthly High Tide Flooding Outlooks, which use El Niño (the Oceanic Niño Index), list no
  San Francisco Bay station (nearby: Point Reyes, Monterey).
- **To review:** the 30-day window, the 30 days ahead on the calendar, the 0.1 ft minimum, whether to show a Bay running lower too, and whether the kiosk's
  "running higher" note (last few high tides, `OFFSET_RECENT_HIGHS`, includes surge) should change.

## 5. Page logic settings — `settings.csv`

| Setting | Value | Basis | Status | Checked by / on |
|---|---|---|---|---|
| Rapidly rising: rise | 0.5 ft in 60 min by default; per gauge in `creek_gauges.csv` `rise_ft` (0.25–1.0 ft, or off); on UTC times; confirmed by the previous reading rising at least half as much (on-change gauges after a quiet spell: by the next report; hourly readings can't be confirmed); comparison reading no more than 15 min late (12 h for on-change gauges); holds 30 min; newest reading < 90 min old | Tested against USGS 2007–2026 and OneRain Oct 2019–2026: [RISING_FAST_BASIS.md](RISING_FAST_BASIS.md) | **Calibrated, not yet signed off** (Pilarcitos above Stone Dam, Pescadero 41151: provisional; Colma, Atherton Alameda, Green Hills: default, not enough record yet) | |
| Rapidly rising: tidal gauges | only after ≥ 0.10 in rain in 3 hr (San Bruno at First Avenue and Colma at Orange Memorial Park, `tidal = yes`) | Stops every high tide from counting as a rapid rise; storm backwater not yet measured (RISING_FAST_BASIS.md §7) | **Provisional** | |
| Rapidly rising: time to next level | shown if within 3 hr; not shown while the alert is only being held (the rise may have stopped) | Working choice | Provisional | |
| Gauge offline | 12 hr silent (gauges that report on change), 3 hr (scheduled gauges) | On-change gauges can be silent for hours when the level is steady; set to avoid false "offline" | Working choice, review | |
| Creek data delayed | 30 min | Data job runs every 5 min; 30 min = several missed runs | Working choice | |
| Map site not reporting / old reading / data late | 24 hr / 3 hr / 45 min | Map data refreshes every 15 min | Working choice | |
| High tide flood level (red), Redwood City | 8.5 ft NAVD88 (`TIDE_RED_FT_RWC`) | Staff working level ("about 8.5 and we're in the red", Oct 2026). Just under the highest astronomical tide (8.53), so the tide table alone almost never reaches it: red mostly means storms or ocean conditions (such as El Niño) are pushing a high tide up. Above MHHW (7.02) and below this = blue, "higher than usual" (information, not a hazard color: MHHW is a tidal reference, not a flood level; Oct 15) | **Provisional** — confirm against known flooding (low points, past events); NOAA's derived minor flood threshold here is 9.0 ft NAVD88 (FYI in §4) | |
| King Tide (label only, ★) | A day whose tide-table high tide at Redwood City reaches **8.3 ft NAVD88** (`KING_TIDE_FT_RWC`), the **1-year tide** | Staff were told to use the 1-year tidal condition for "King Tide" (Oct 16). 8.3 ft NAVD88 = the 1-year (100% annual chance) extreme tide at the Redwood City shoreline points in the 760s of the *San Francisco Bay Tidal Datums and Extreme Tides Study* (AECOM for BCDC, 2016, Appendix B); same datum as the pages, so no conversion. Tide table only, so stars are known months ahead. 2026-27 season (NOAA tide table, ft NAVD88): Nov 25 (8.36), Dec 23 (8.40), Dec 24 (8.43); Nov 24 (8.28) and Jan 22 (8.29) just miss. Replaces "highest tide of the month in Nov, Dec and Jan" (Oct 15–16). Gives no color or alert by itself (8.3 is above MHHW, so these days are blue; red only at 8.5) | Working choice — confirm which 760s point (or average) represents the gauge | |
| King Tide, Coastside (label only, ★) | A day whose tide-table high tide at Monterey 9413450 reaches **6.87 ft NAVD88** (`KING_TIDE_FT_MRY`), the 1-year tide (99% annual chance) | Given by OneShoreline staff (Oct 16) for the Coastside Tides page. Monterey is the nearest NOAA gauge with live readings on the open coast south of San Francisco; tides along the San Mateo coast are close to it, but waves (not included) add to the water level at the shore. No coastside flood level (red) yet | **Provisional** — record the source and confirm the gauge choice (Monterey vs San Francisco 9414290 or Half Moon Bay predictions 9414131) | |
| NOAA projection | next 48 hr (`TIDE_EXPECTED_HOURS`); "NOAA projects about X ft higher/lower than the tide table" on a King Tide day when ≥ 0.25 ft from the tide table (`TIDE_WEATHER_NOTE_FT`) | NOAA model reaches about 2 days | Working choice | |
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
| Creek status layer wording (plain-language pass, Oct 14) | Rain levels now Heavy / Very heavy / **Intense** (was Severe, an NWS word); "Light or none" when not raining hard; feet and ft/hr moved under "See the numbers"; "How to read this page" panel. **Open: the level names Flood Monitoring / Watch / Warning match NWS alert names; decide with DEM whether to rename them on public pages** | |
| Contact details and links | | |

## 7. Gauge mapping — `creek_gauges.csv`

Each gauge's OneRain ids were copied from its OneRain sensor page in October 2026. Check that each row points to
the intended sensor (open the link from the creek page's "thresholds & notes" or the sensor map) and that
`reports` (on change / interval) matches how the gauge logs. Checked by / on: ______

`tidal` (yes / no / blank = to confirm): whether the creek at the gauge rises and falls with the Bay tide. Yes: San Bruno at
First Avenue; Colma at Orange Memorial Park (Summer, OneShoreline, Oct 16, 2026). A tidal gauge counts as rapidly rising only
after rain (§5), and its creek card adds the rising-tide line when the next high tide is near and the status is Stay alert or
higher; a tidal creek at Heavy rain with a rising tide is Stay alert (§10).

## 8. Rain frequency (creek status layer, in development) — `rain_frequency.csv`

Answers the open item in §2: rain levels for every creek, not just Belmont's triggers.

- **Source:** NOAA Atlas 14, Volume 6, Version 2, point precipitation frequency estimates, depth in inches,
  **partial-duration series**, at each rain gauge's coordinates. Pulled 2026-10-13 with `scripts/fetch_atlas14.py`.
- **Why at the gauge:** Atlas 14 values are point estimates, so a gauge's rain compares like-for-like with the
  estimate at that same point.
- **Durations:** 15, 30, 60 min; 2, 3, 6, 12, 24, 48 hr. Rolling totals are checked at every duration; the most
  extreme sets the level.
- **Levels:** Heavy ≥ 1-year storm (≈63% chance in any year) · Very heavy ≥ 2-year (≈39%) · Severe ≥ 5-year (≈18%).
  Chance in any year = annual exceedance probability, 1 − e^(−1/ARI).
- **Confirmation:** Severe needs a second linked gauge at Very heavy or above (`RAIN_SEVERE_CONFIRM_GAUGES`). A creek
  with only one working rain gauge can reach Severe on that gauge alone; the staff view says so (decided Oct 14).
- **Which readings count:** rain gauges report every 1–12 hours in dry weather and on each tip when it rains, so a
  gauge counts as working if it has reported within `GAUGE_QUIET_HOURS` (12 h, as for creek gauges). A gauge that is
  silent while others on the same creek record rain will be flagged separately (`RAIN_SILENT_MIN`, proposed).
- **Hillside gauges:** `role = supporting` in `creek_gauges.csv` counts a rain gauge toward the creek's rain level
  only; it doesn't appear in the rain tables or graphs. Pairings go live after staff check them against watershed maps.
- **Status:** From source, not yet signed off. **Provisional** cutoffs until backtested against past storms.
- **Spot-checked:** Atherton 41107 1-hr 2-year 0.58 in, 24-hr 100-year 5.99 in, matching NOAA's site.
- **Limits:** rainfall frequency isn't flood frequency (wet ground, tides and blockages change the response);
  Atlas 14 doesn't reflect recent climate trends (replace with Atlas 15 when it's published for California);
  NOAA's 90% confidence bounds aren't included.

## 9. More creeks and gauge pairings (in development) — `proposed/creeks.csv`, `proposed/creek_gauges.csv`

- 10 more creeks, using the stream gauges they already have (OneRain and USGS) and nearby rain gauges.
- Rain gauges were paired from coordinates (straight-line distance and direction), favoring gauges **upslope in
  the creek's own watershed**. They haven't been checked against watershed boundaries.
- `role`: primary / supporting; `confidence`: good / fair / weak; open questions are in `open_items`.
- **Tidal creeks (per staff):** Colma, San Bruno, Green Hills (drains to Highline Canal), San Mateo,
  San Francisquito, Redwood. Whether each *gauge* reads the tide still needs confirming (`tidal = confirm`).
- **Coverage gaps:** San Bruno and Green Hills have no upslope rain gauge; lower Pilarcitos has none; Pescadero's
  hillside gauges are 5–8 miles away; Butano has none in its upper watershed.
- **San Mateo Creek:** below Crystal Springs, flow is mostly reservoir releases (SFPUC). USGS 11162753 measures flow
  below the dam (and picks up I-280 runoff); USGS 11162750 is reservoir level; the reservoir spills at 294.6 ft.
- **In preview (Oct 14):** San Francisquito, San Mateo, Green Hills, Pilarcitos, San Gregorio and Pescadero are in the
  live files with `preview_only = yes` (staff preview only), using the gauges that can be read now. Their OneRain ids were
  pre-filled from OneRain's public site list and their gauge notes say what to check. Redwood, Bear, Los Trancos and
  stay in `proposed/` until their stage gauges are public on OneRain. Butano went live on Oct 20, 2026 as a preview creek, reading OneRain's public backup sensors near Cloverdale Road and the USGS gauge beside them (11162540); its Pescadero Road gauge (41153) and Pescadero Town Ridge rain (PCCC1) stay in `proposed/`.
- **Rising fast on these creeks** uses per-gauge values from the USGS record ([RISING_FAST_BASIS.md](RISING_FAST_BASIS.md)).
  Below dams (Pilarcitos below Stone Dam and the spillway, San Mateo below Crystal Springs) a fast rise is a release
  or spill: "happening now", with little or no lead time. It is off below Stone Dam.

## 10. Creek status (in development) — `proposed/display_text.csv`, `proposed/settings.csv`

One plain status per card, worst first:

| Status | When |
|---|---|
| Flooding likely | Flood Warning (level 3+) or a level-3 rain trigger |
| Be ready | Flood Watch; or, on a creek without flood levels, rising fast or severe rain* |
| Stay alert | Flood Monitoring; very heavy rain; severe rain or rising fast on a creek still at Normal; heavy rain + rising tide on a tidal creek |
| Offline / Data delayed | as today (`status_offline`, `status_delayed`) |
| No alerts | otherwise |

\* **Policy decision:** this lets rain and rate of rise alone put a creek without flood levels at "Be ready",
which makes those cards advisory rather than informational. Switch: `BE_READY_FROM_RAIN` (1 = yes, 0 = Stay alert only).

Flood levels always take priority; rain and rate of rise never lower a status. Run the layer **staff-only first**
(silent mode for the first storms) before the public sees it.

How it runs (Oct 14): the data job works out each creek's status every run and writes it into `creeks.json`
with reason codes; the pages turn the codes into the words in `display_text.csv`. The job reads the NOAA tide
itself (measured if within the hour, else predicted) for the rising-tide line and for rain + tide triggers. If the
tide can't be read, a rain + tide trigger counts as not met and the staff view says so. Every status change is
appended to `status_log.csv` on the data branch for review after each storm. A quiet creek reads **No alerts**
(decided Oct 14). A rain gauge counts as "no recent data" only when it is silent for `RAIN_SILENT_MIN` while another
gauge on the creek records Heavy rain or more.

## 11. Rapidly rising: calibration

Done Oct 15, 2026; see [RISING_FAST_BASIS.md](RISING_FAST_BASIS.md) for the rule, the data, the per-gauge results
and the choices made. It also records which parts of the earlier plan (fitted slope, 99th-percentile threshold,
minimum stage, tide subtraction) were not used, and why. Rerun `scripts/evaluate_rising_fast.py` after each winter.

## Data sources

| Data | Source | How the pages get it | Refresh |
|---|---|---|---|
| Creek stage and rain | OneShoreline Early Warning System (OneRain), public sensor pages | GitHub Action (`.github/workflows/onerain.yml`) reads them and publishes `creeks.json` on the repo's `data` branch | every 5 min |
| All public monitoring sites (sensor map) | OneRain public site pages | same Action, `sites.json` | every 15 min |
| Bay tide: measured, predicted | NOAA Tides & Currents (CO-OPS) API, products `water_level` and `predictions`, `datum=NAVD`, local time | read by each page in the browser | 6 min / hourly |
| Bay tide: NOAA model forecast | NOAA CO-OPS API product `ofs_water_level` (San Francisco Bay Operational Forecast System), `datum=NAVD` | read by each page | hourly (model runs 4×/day) |
| NWS alerts | api.weather.gov active alerts, San Mateo County (SAME 006081) | read by each page | 3 min |
| NWS forecast notes on tides | api.weather.gov Area Forecast Discussion, office MTR (San Francisco Bay Area) | kiosk and Tides page | 30 min |
| King Tide days, high tide calendar | NOAA Tides & Currents tide table (high/low predictions) at Redwood City 9414523, 6 months ahead, ft NAVD88, against the 1-year tide (`KING_TIDE_FT_RWC`, from the SF Bay Tidal Datums and Extreme Tides Study, 2016); and the model's expected height (`ofs_water_level`) | `tide_season.js`, read by the kiosk and Tides page | twice a day / hourly |
| Tide datums | NOAA Tides & Currents datums pages for each station | entered in `tide_stations.csv` | when NOAA updates the epoch |
| Rain frequency | NOAA HDSC Precipitation Frequency Data Server, Atlas 14 Vol. 6 v2 (hdsc.nws.noaa.gov/pfds) | `scripts/fetch_atlas14.py` → `rain_frequency.csv` | once; again when Atlas 15 is published |
| USGS stream gauges | USGS Water Data API (`api.waterdata.usgs.gov`) and WaterServices (`waterservices.usgs.gov`, retiring late 2026/early 2027) | live: data job; history: `scripts/fetch_usgs.py` (workflow **USGS history pull**) | 15 min |
| OneRain history (calibration) | OneRain public sensor pages, custom date range | archive repo workflow **OneRain history pull** (`scripts/pull_onerain_history.py`) | on demand |
| Crystal Springs releases | SFPUC Peninsula Reservoir Wet Weather Operations (sfpuc.gov/PeninsulaReservoirWetWeather) | reference | as published |
| Evacuation orders | Genasys Protect (protect.genasys.com), per San Mateo County DEM | link only (proposed) | live |

## Sign-off checklist for the creek status layer (§8–11)

- [ ] Confirm each assumed rain gauge has a working rain sensor (`open_items`: 41101–41107, 41201, 41200, 41151–41153)
- [ ] Review pairings against watershed maps, especially whether Pulgas is in the Belmont Creek watershed
- [ ] Confirm which proposed stage gauges read the tide (`tidal = confirm`)
- [ ] Accept or plan for the coverage gaps (§9)
- [ ] Spot-check two or three gauges in `rain_frequency.csv` against NOAA's site
- [ ] Confirm the 1/2/5-year cutoffs after backtesting past storms
- [ ] Decide the policy switch `BE_READY_FROM_RAIN`
- [ ] Review the per-gauge rapidly-rising values and rule in RISING_FAST_BASIS.md (proposed Oct 15) and sign off
- [ ] Communications and DEM approve `proposed/display_text.csv`; order translations
- [ ] Get a Genasys Protect link centered on San Mateo County
- [ ] Run staff-only through the first storms before going public
- [ ] **Check the tide flood level (8.5 ft NAVD88, provisional) at this winter's King Tides** (Nov 25, Dec 23–24; tide table 8.36–8.43 ft): at high tide, photograph or note where water reaches at known low spots near Redwood City (Bay trail, marsh edges, low roads and parking lots) and note the Redwood City gauge reading at that time. If there is some Bay-edge overtopping at about 8.4 ft, 8.5 is about right and "provisional" can come off; if water stays well inside the shoreline, raise it; if low areas are already wet, lower it. The 1-year tide (8.3) is only 0.2 ft below 8.5, so the page will turn red about every winter when a storm lands on a King Tide: confirm that matches real flooding.

## Sign-off log

| Date | Who | What was checked / changed | Files |
|---|---|---|---|
| Oct 16, 2026 | Summer (OneShoreline) | Creek status layer made public on the home page, Creeks page and kiosk (`STATUS_PUBLIC` = 1; set 0 to return to staff-only). Creeks other than Colma, San Bruno, Belmont and Atherton carry a "Methodology under review" tag. The checklist items above are still open | settings.csv, display_text.csv, creek_status.js |
| Oct 16, 2026 | Summer (OneShoreline) | Colma Creek at Orange Memorial Park is tidal (`col_stage` `tidal` no → yes). Its rapidly-rising check now needs ≥ 0.10 in rain in 3 hr, Heavy rain + a rising tide at Alameda makes it Stay alert, and its card adds the rising-tide line. The dry-weather check (Oct 12–14) saw ≤ 0.04 ft of tidal movement; storm-time backwater is still to be measured. | `creek_gauges.csv`, `gauge_facts.csv` |
| | | | |
