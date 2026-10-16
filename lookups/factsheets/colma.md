# Colma Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `colma` |
| On the site | Public |
| Cities and communities | Daly City; Colma; South San Francisco *(draft - confirm cities and outlet)* |
| Drains to | San Francisco Bay at South San Francisco |
| Description | Urban creek from San Bruno Mountain and Daly City through Colma to South San Francisco; the gauge is at Orange Memorial Park and the thresholds are for the community downstream. |
| Linked to flooding | **Yes**: flood levels at the creek gauge (what they mean is below) |
| Bay tide station | NOAA 9414750 Alameda (MHHW ? ft MLLW) |
| Rain totals shown | 1 hr, 6 hr, 24 hr |

**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).

## Creek level gauges

### Colma Creek at Orange Memorial Park

| | |
|---|---|
| Gauge key | `col_stage` |
| Source and ID | OneRain 41101 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=12&site=32e8ebb1-4c9c-460a-a4cd-58903b96f347&device_id=5&device=dbbbcf6d-6a38-44a5-a90b-7077db13c5c2)) |
| Location | 37.65379, -122.42669 |
| Reports | Every 12 hours plus extra readings in some storms until May 2025; hourly plus extra storm readings since Oct 2025 |
| Record | Jun 2020 (public OneRain pages) |
| Tidal | No (dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide) |
| Rising fast | 0.5 ft in 60 min (default; not calibrated) |
| History and known issues | Outages: Jun 23 - Oct 6, 2020; Nov 24 - Dec 15, 2021; May 29 - Oct 16, 2025. Sensor faults: Jul 15, 2022 (readings to about 16.7 ft); Aug 18, 2022 (one-reading spike to 4.56 ft). When it switches from hourly to faster readings in a storm, the rising-fast check can miss the rise (RISING_FAST_BASIS.md section 8). |

**Flood levels** (gauge height, ft; gauge's own zero, not a tidal datum)

| Level | Name | Stage (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 3.40 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 5.00 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 6.75 | OneRain sensor thresholds (Oct 2026) |  |

Meaning: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).
By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.
Basis and sign-off status: [THRESHOLDS_BASIS.md §1](../THRESHOLDS_BASIS.md).

**Rising fast (alert level), tested on 6.3 years of history.** Tested against the gauge's lowest flood level, Flood Monitoring at 3.4 ft, so "warned" means an alert came before the creek reached that level.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 9.2 | 3 of 7 | 80 min |
| 0.5 ◀ current | 5.9 | 3 of 7 | 80 min |
| 0.75 | 3.3 | 2 of 7 | 3.2 h |
| 1.0 | 2.5 | 2 of 7 | 3.2 h |
| 1.5 | 1.1 | 1 of 7 | 80 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| Orange Memorial Park (`col_rain`) | 41101 | 37.65379, -122.42669 | lower watershed | Primary (shown on the pages) |
| San Bruno Mountain (`col_rain_41200`) | 41200 | 37.69222, -122.44833 | upper watershed | Supporting (counts toward the rain level only) |

**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, not whether the creek floods.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Orange Memorial Park | Heavy (1-yr) | 0.236 | 0.456 | 0.827 | 1.87 |
| Orange Memorial Park | Very heavy (2-yr) | 0.283 | 0.546 | 0.984 | 2.39 |
| Orange Memorial Park | Intense (5-yr) | 0.347 | 0.669 | 1.2 | 3.07 |
| San Bruno Mountain | Heavy (1-yr) | 0.251 | 0.489 | 0.894 | 2.11 |
| San Bruno Mountain | Very heavy (2-yr) | 0.302 | 0.589 | 1.07 | 2.68 |
| San Bruno Mountain | Intense (5-yr) | 0.372 | 0.725 | 1.3 | 3.44 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Open items

- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
