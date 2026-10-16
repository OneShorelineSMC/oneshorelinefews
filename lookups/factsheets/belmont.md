# Belmont Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `belmont` |
| On the site | Public |
| Cities and communities | Belmont; San Carlos; unincorporated Harbor Industrial Area *(draft - confirm cities and outlet)* |
| Drains to | Belmont Slough, then San Francisco Bay |
| Description | Flashy urban creek; frequent street flooding downstream; thresholds are for the Harbor Industrial Area. |
| Linked to flooding | **Yes**: flood levels at the creek gauge (what they mean is below); rain triggers too |
| Bay tide station | NOAA 9414523 Redwood City (MHHW 7.02 ft NAVD88) |
| Rain totals shown | 30 min, 1 hr, 4 hr, 24 hr |

**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).

## Creek level gauges

### Belmont Creek at Old County Rd

| | |
|---|---|
| Gauge key | `bel_stage` |
| Source and ID | OneRain 41104 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=2&site=25fd9d56-e3ea-4ff9-a067-b3e99cc5c1fe&device_id=1&device=5c101ccb-75e1-4c68-a983-4b8c78913c03)) |
| Location | 37.51719, -122.27125 |
| Reports | On change: every 12 hours in dry weather, every few minutes in storms |
| Record | Oct 2019 or earlier (pulled from Oct 1, 2019) |
| Tidal | No (dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide) |
| Rising fast | 0.5 ft in 60 min |
| History and known issues | 27 single-reading sensor spikes of 1 ft or more from Oct 2019 to 2022 (e.g. 0.09 to 7.97 to 0.08 ft on Oct 17, 2019); none since 2023. |

**Flood levels** (gauge height, ft; gauge's own zero, not NAVD88)

| Level | Name | Stage (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.25 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 3.25 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 4.00 | OneRain sensor thresholds (Oct 2026) |  |

Meaning: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).
By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.
Basis and sign-off status: [THRESHOLDS_BASIS.md §1](../THRESHOLDS_BASIS.md).

**Rising fast (alert level), tested on 7.0 years of history.** Tested against the gauge's lowest flood level, Flood Monitoring at 2.25 ft, so "warned" means an alert came before the creek reached that level.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 27.6 | 44 of 45 | 59 min |
| 0.5 ◀ current | 23.6 | 44 of 45 | 42 min |
| 0.75 | 19.0 | 44 of 45 | 16 min |
| 1.0 | 14.9 | 42 of 45 | 10 min |
| 1.5 | 10.5 | 33 of 45 | 6 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| Old County Road (`bel_rain`) | 41104 | 37.51719, -122.27125 | lower watershed | Primary (shown on the pages) |

**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, not whether the creek floods.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Old County Road | Heavy (1-yr) | 0.22 | 0.432 | 0.796 | 1.76 |
| Old County Road | Very heavy (2-yr) | 0.264 | 0.517 | 0.947 | 2.29 |
| Old County Road | Intense (5-yr) | 0.324 | 0.637 | 1.15 | 2.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

**Rain triggers** (flood levels for rain: each one sets the creek to the status shown)

| Gauge | Window | Rain (in) | Tide | Shows | Source |
|---|---|---|---|---|---|
| `bel_rain` | 30 min | 0.20 | – | Flooding likely (rain) | Belmont Creek OneRain dashboard (Oct 2026) |
| `bel_rain` | 4 hr | 0.42 | ≥ 6.32 ft NAVD88 | Flooding likely (rain + tide) | OneRain alarm rule 'Rainfall and Tide (Belmont)' #34: 4 Hr Accumulation >= 0.42 in and OneRain Redwood City Tide Elevation >= 7.5 ft. OneRain's tide is MLLW; NOAA 9414523 MLLW is 1.18 ft below NAVD88, so 7.5 ft MLLW = 6.32 ft NAVD88. Rain threshold from analysis of 2022-2025 events |

Basis: [THRESHOLDS_BASIS.md §2](../THRESHOLDS_BASIS.md).

## Open items

- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
