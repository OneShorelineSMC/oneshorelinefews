# Pescadero Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `pescadero` |
| On the site | Staff preview only (`preview_only = yes`) |
| Cities and communities | Unincorporated Pescadero; Loma Mar; La Honda area *(draft - confirm cities and outlet)* |
| Drains to | Pescadero Marsh, then the Pacific Ocean |
| Description | Rural coastal creek; the town of Pescadero floods from Pescadero and Butano Creeks. |
| Bay tide station | None (coastal creek) |
| Rain totals shown | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### Pescadero Creek at Stage Road

| | |
|---|---|
| Gauge key | `pes_stage_41151` |
| Source and ID | OneRain 41151 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=28&site=b7ae4c33-4536-443f-bcc5-72ded98d2412&device_id=1&device=cbd2cde7-ac86-4ad2-8a9d-a2f6d7575cd8)) |
| Location | 37.25468, -122.38330 |
| Reports | On change (every 2-12 hours in dry weather) |
| Record | Oct 13, 2023 (public OneRain pages) |
| Tidal | No |
| Rising fast | 1.0 ft in 60 min |
| Note shown on the site | No flood levels set yet · To check: check they open the Stage sensor; set reports |

**Flood levels:** none set yet. Status comes from rain and rising fast ([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).

**Rising fast, tested on history** (3.0 years; big-storm level 11.52 ft, the median yearly peak)

| Threshold (ft in 60 min) | Alerts / yr | Big storms warned first | Median lead |
|---|---|---|---|
| 0.25 | 10.0 | 3 of 3 | 5.1 h |
| 0.5 | 5.3 | 3 of 3 | 5.1 h |
| 0.75 | 4.0 | 3 of 3 | 5.1 h |
| 1.0 ◀ current | 3.0 | 3 of 3 | 4.9 h |
| 1.5 | 1.0 | 3 of 3 | 4.1 h |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

### Pescadero Creek near Pescadero

| | |
|---|---|
| Gauge key | `pes_stage_11162500` |
| Source and ID | USGS 11162500 ([page](https://waterdata.usgs.gov/monitoring-location/USGS-11162500/)) |
| Location | 37.26096, -122.32890 |
| Reports | Every 15 minutes (USGS) |
| Record | Oct 2007 (pulled from Oct 1, 2007) |
| Tidal | No |
| Rising fast | 1.0 ft in 60 min |
| History and known issues | Typical water level has crept up over the record (channel change). |
| Note shown on the site | No flood levels set yet |

**Flood levels:** none set yet. Status comes from rain and rising fast ([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).

**Rising fast, tested on history** (19.0 years; big-storm level 10.41 ft, the median yearly peak)

| Threshold (ft in 60 min) | Alerts / yr | Big storms warned first | Median lead |
|---|---|---|---|
| 0.25 | 7.8 | 18 of 18 | 4.8 h |
| 0.5 | 5.3 | 18 of 18 | 3.2 h |
| 0.75 | 4.0 | 18 of 18 | 2.8 h |
| 1.0 ◀ current | 2.7 | 18 of 18 | 2.5 h |
| 1.5 | 1.7 | 16 of 18 | 82 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| La Honda (`pes_rain_lah`) | LAH | 37.30530, -122.25390 | nearby | Supporting (counts toward the rain level only) |

**Rain levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| La Honda | Heavy (1-yr) | 0.342 | 0.676 | 1.26 | 3.06 |
| La Honda | Very heavy (2-yr) | 0.428 | 0.846 | 1.57 | 3.89 |
| La Honda | Intense (5-yr) | 0.541 | 1.07 | 1.98 | 4.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Open items

- `pes_stage_41151`: check they open the Stage sensor; set reports
- `pes_rain_lah`: check they open the Rain Increment sensor
- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
