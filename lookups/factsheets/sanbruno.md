# San Bruno Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `sanbruno` |
| On the site | Public |
| Cities and communities | San Bruno; South San Francisco *(draft - confirm cities and outlet)* |
| Drains to | San Francisco Bay near SFO |
| Description | Short urban creek; the gauge at First Avenue is tidal (rises and falls with the Bay tide). |
| Bay tide station | NOAA 9414750 Alameda (MHHW 6.37 ft NAVD88) |
| Rain totals shown | 15 min, 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Bruno Creek at First Avenue

| | |
|---|---|
| Gauge key | `sb_stage_41102` |
| Source and ID | OneRain 41102 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=11&site=fe06588c-e5e6-4016-8a8f-2ba1f040636e&device_id=3&device=e481d107-65bb-4107-89ab-48484eb0e188)) |
| Location | 37.62273, -122.40671 |
| Reports | On change (typically every 1-5 hours in dry weather, minutes in storms) |
| Record | Sep 2020 (public OneRain pages) |
| Tidal | Yes (rises and falls with the Bay tide) |
| Rising fast | 0.5 ft in 60 min |
| History and known issues | Offline since Jun 3, 2026; the last reading (Jun 3, 2026) is probably a sensor fault. Gauge key renamed from 'stage' to sb_stage_41102 on Oct 15, 2026. Gauge zero in NAVD88 unknown. |

**Flood levels** (gauge height, ft; gauge's own zero, not NAVD88)

| Level | Name | Stage (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.40 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 3.60 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 4.80 | OneRain sensor thresholds (Oct 2026) |  |

Meaning: **to document**.
Basis and sign-off status: [THRESHOLDS_BASIS.md §1](../THRESHOLDS_BASIS.md).

**Rising fast, tested on history** (5.8 years; big-storm level 2.4 ft)

| Threshold (ft in 60 min) | Alerts / yr | Big storms warned first | Median lead |
|---|---|---|---|
| 0.25 | 57.2 | 27 of 28 | 3.4 h |
| 0.5 ◀ current | 31.3 | 25 of 28 | 1.8 h |
| 0.75 | 17.9 | 15 of 28 | 42 min |
| 1.0 | 8.2 | 7 of 28 | 22 min |
| 1.5 | 2.8 | 2 of 28 | 14 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| San Bruno Mountain (`rain_mountain`) | 41200 | 37.69222, -122.44833 | upper watershed | Primary (shown on the pages) |
| First Avenue (`rain_first_ave`) | 41102 | 37.62273, -122.40671 | lower watershed | Primary (shown on the pages) |

**Rain levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| San Bruno Mountain | Heavy (1-yr) | 0.251 | 0.489 | 0.894 | 2.11 |
| San Bruno Mountain | Very heavy (2-yr) | 0.302 | 0.589 | 1.07 | 2.68 |
| San Bruno Mountain | Intense (5-yr) | 0.372 | 0.725 | 1.3 | 3.44 |
| First Avenue | Heavy (1-yr) | 0.227 | 0.442 | 0.799 | 1.89 |
| First Avenue | Very heavy (2-yr) | 0.277 | 0.538 | 0.97 | 2.36 |
| First Avenue | Intense (5-yr) | 0.344 | 0.669 | 1.2 | 3.0 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Open items

- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
- Document what the flood levels mean (THRESHOLDS_BASIS.md §1)
