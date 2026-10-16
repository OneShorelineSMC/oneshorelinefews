# San Gregorio Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `sangregorio` |
| On the site | Staff preview only (`preview_only = yes`) |
| Cities and communities | Unincorporated San Gregorio; La Honda (upper watershed) *(draft - confirm cities and outlet)* |
| Drains to | Pacific Ocean at San Gregorio State Beach |
| Description | Rural coastal creek. |
| Bay tide station | None (coastal creek) |
| Rain totals shown | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Gregorio Creek at San Gregorio

| | |
|---|---|
| Gauge key | `sg_stage_11162570` |
| Source and ID | USGS 11162570 ([page](https://waterdata.usgs.gov/monitoring-location/USGS-11162570/)) |
| Location | 37.32578, -122.38664 |
| Reports | Every 15 minutes (USGS) |
| Record | Oct 2007 (pulled from Oct 1, 2007) |
| Tidal | No |
| Rising fast | 1.0 ft in 60 min |
| History and known issues | Typical water level rose about 2 ft in 2016-17 and stayed higher for years (channel change). |
| Note shown on the site | No flood levels set yet |

**Flood levels:** none set yet. Status comes from rain and rising fast ([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).

**Rising fast, tested on history** (19.0 years; big-storm level 13.53 ft, the median yearly peak)

| Threshold (ft in 60 min) | Alerts / yr | Big storms warned first | Median lead |
|---|---|---|---|
| 0.25 | 13.3 | 18 of 18 | 5.9 h |
| 0.5 | 8.5 | 18 of 18 | 4.6 h |
| 0.75 | 6.1 | 18 of 18 | 4.1 h |
| 1.0 ◀ current | 3.8 | 18 of 18 | 3.8 h |
| 1.5 | 2.4 | 14 of 18 | 2.6 h |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| La Honda (`sg_rain_lah`) | LAH | 37.30530, -122.25390 | nearby | Primary (shown on the pages) |

**Rain levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| La Honda | Heavy (1-yr) | 0.342 | 0.676 | 1.26 | 3.06 |
| La Honda | Very heavy (2-yr) | 0.428 | 0.846 | 1.57 | 3.89 |
| La Honda | Intense (5-yr) | 0.541 | 1.07 | 1.98 | 4.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Open items

- `sg_rain_lah`: check they open the Rain Increment sensor
- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
