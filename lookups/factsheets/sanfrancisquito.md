# San Francisquito Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `sanfrancisquito` |
| On the site | Staff preview only (`preview_only = yes`) |
| Cities and communities | Woodside; Portola Valley; Menlo Park; East Palo Alto; Palo Alto; Stanford (unincorporated Santa Clara County) *(draft - confirm cities and outlet)* |
| Drains to | San Francisco Bay |
| Description | Large creek on the San Mateo / Santa Clara county line; the USGS gauge is at Stanford. |
| Linked to flooding | **No**: alert levels only (rain and rising fast). No creek height here is tied to flooding yet |
| Tide station | NOAA 9414523 Redwood City (MHHW 7.02 ft NAVD88) |
| Rain totals shown | 30 min, 1 hr, 3 hr, 24 hr |

**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).

## Creek level gauges

### San Francisquito Creek at Stanford

| | |
|---|---|
| Gauge key | `sfq_stage_11164500` |
| Source and ID | USGS 11164500 ([page](https://waterdata.usgs.gov/monitoring-location/USGS-11164500/)) |
| Location | 37.42327, -122.18941 |
| Reports | Every 15 minutes (USGS) |
| Record | Oct 2007 (pulled from Oct 1, 2007; USGS record is longer) |
| Tidal | To confirm (dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide) |
| Rising fast | 0.5 ft in 60 min |
| History and known issues | USGS data approved through spring 2026, provisional since Apr 2026. |
| Note shown on the site | No flood levels set yet · To check: USGS 11164500; OneRain site SFC shows the same gauge, so read it from USGS. Confirm whether this gauge reads the tide |

**Flood levels:** none. No creek height at this gauge is tied to flooding yet, so the creek's status comes from alert levels only: rain and rising fast ([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).

**Rising fast (alert level), tested on 19.0 years of history.** Tested against 6.0 ft, the creek's typical yearly high (the median yearly peak, about a 2-year event). **This is not a flood level:** "warned" means an alert came before a typical yearly high, not before flooding.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 19.9 | 20 of 20 | 4.6 h |
| 0.5 ◀ current | 9.5 | 20 of 20 | 3.0 h |
| 0.75 | 4.9 | 17 of 20 | 2.0 h |
| 1.0 | 3.0 | 12 of 20 | 60 min |
| 1.5 | 0.9 | 5 of 20 | 30 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| Wunderlich County Park (`sfq_rain_a08363e2`) | A08363E2 | 37.40243, -122.27486 | upper watershed | Primary (shown on the pages) |
| Windy Hill Open Space Preserve (`sfq_rain_a0839db4`) | A0839DB4 | 37.35799, -122.23990 | upper watershed | Supporting (counts toward the rain level only) |
| Trappers Trail (Valley Water) (`sfq_rain_a08204fe`) | A08204FE | 37.34611, -122.18083 | upper watershed | Supporting (counts toward the rain level only) |

**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, not whether the creek floods.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Wunderlich County Park | Heavy (1-yr) | 0.369 | 0.734 | 1.37 | 3.28 |
| Wunderlich County Park | Very heavy (2-yr) | 0.464 | 0.921 | 1.71 | 4.22 |
| Wunderlich County Park | Intense (5-yr) | 0.587 | 1.17 | 2.16 | 5.46 |
| Windy Hill Open Space Preserve | Heavy (1-yr) | 0.349 | 0.692 | 1.29 | 3.1 |
| Windy Hill Open Space Preserve | Very heavy (2-yr) | 0.439 | 0.869 | 1.62 | 3.96 |
| Windy Hill Open Space Preserve | Intense (5-yr) | 0.556 | 1.1 | 2.04 | 5.08 |
| Trappers Trail (Valley Water) | Heavy (1-yr) | 0.306 | 0.603 | 1.11 | 2.65 |
| Trappers Trail (Valley Water) | Very heavy (2-yr) | 0.384 | 0.756 | 1.4 | 3.34 |
| Trappers Trail (Valley Water) | Intense (5-yr) | 0.485 | 0.956 | 1.77 | 4.25 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Current OneRain dashboard thresholds

None recorded yet (`onerain_dashboard_thresholds.csv`).

## Open items

- `sfq_stage_11164500`: USGS 11164500; OneRain site SFC shows the same gauge, so read it from USGS. Confirm whether this gauge reads the tide
- `sfq_rain_a08363e2`: check they open the Rain Increment sensor; pick one for the card
- `sfq_rain_a0839db4`: check they open the Rain Increment sensor; pick one for the card
- `sfq_rain_a08204fe`: check they open the Rain Increment sensor; pick one for the card
- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
- Link to flooding: find the creek height at each gauge where the creek leaves its banks or floods a road (survey, hydraulic study, or a past flood with gauge readings), then add it to thresholds.csv (THRESHOLDS_BASIS.md, Terms)
