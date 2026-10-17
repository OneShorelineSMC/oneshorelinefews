# San Mateo Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `sanmateo` |
| On the site | Staff preview only (`preview_only = yes`) |
| Cities and communities | Hillsborough; San Mateo *(draft - confirm cities and outlet)* |
| Drains to | San Francisco Bay |
| Description | Flow below Crystal Springs Reservoir is controlled by SFPUC releases and spills. |
| Linked to flooding | **No**: alert levels only (rain and rising fast). No creek height here is tied to flooding yet |
| Tide station | NOAA 9414750 Alameda (MHHW 6.37 ft NAVD88) |
| Rain totals shown | 30 min, 1 hr, 3 hr, 24 hr |

**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).

## Creek level gauges

### San Mateo Creek Below Crystal Springs Reservoir

| | |
|---|---|
| Gauge key | `smc_stage_11162753` |
| Source and ID | USGS 11162753 ([page](https://waterdata.usgs.gov/monitoring-location/USGS-11162753/)) |
| Location | 37.52944, -122.35833 |
| Reports | Every 15 minutes (USGS) |
| Record | Sep 2008 |
| Tidal | To confirm (dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide) |
| Rising fast | 0.5 ft in 60 min |
| History and known issues | Rises follow Crystal Springs Reservoir releases and spills (reservoir level: USGS 11162750; spill about 294.6 ft). USGS data approved through spring 2026. |
| Note shown on the site | No flood levels set yet · To check: Confirm whether this gauge reads the tide; Flow below Crystal Springs dam; reservoir level is USGS 11162750 (spill at 294.6 ft) |

**Flood levels:** none. No creek height at this gauge is tied to flooding yet, so the creek's status comes from alert levels only: rain and rising fast ([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).

**Rising fast (alert level), tested on 18.1 years of history.** Tested against 5.88 ft, the creek's typical yearly high (the median yearly peak, about a 2-year event). **This is not a flood level:** "warned" means an alert came before a typical yearly high, not before flooding.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 17.6 | 21 of 60 | 1.5 h |
| 0.5 ◀ current | 7.2 | 11 of 60 | 45 min |
| 0.75 | 3.1 | 3 of 60 | 75 min |
| 1.0 | 1.3 | 0 of 60 | – |
| 1.5 | 0.5 | 0 of 60 | – |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| Crystal Springs Cottage (`smc_rain_csc`) | CSC | 37.49600, -122.32900 | nearby | Supporting (counts toward the rain level only) |

**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, not whether the creek floods.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Crystal Springs Cottage | Heavy (1-yr) | 0.257 | 0.505 | 0.931 | 2.12 |
| Crystal Springs Cottage | Very heavy (2-yr) | 0.31 | 0.61 | 1.11 | 2.73 |
| Crystal Springs Cottage | Intense (5-yr) | 0.383 | 0.753 | 1.36 | 3.54 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Current OneRain dashboard thresholds

As set in OneRain on 2026-10-16; source: OneRain admin screenshot (provided by staff). **For reference only:** FEWS doesn't use these; its own levels are above. Dashboard colors are what OneRain's dashboard shows; gauge alarms are thresholds set on the gauge itself.

| Type | Gauge | Window | Color | Range | Name | Compared with NOAA Atlas 14 (in) |
|---|---|---|---|---|---|---|
| Dashboard rain color | **to confirm** | 3 hr | Green | 0 – 0.799 in |  | – |
| Dashboard rain color | **to confirm** | 3 hr | Orange | 0.800 – 0.999 in |  | CSC: below the 1-yr (0.931) |
| Dashboard rain color | **to confirm** | 3 hr | Red | ≥ 1.000 in |  | CSC: between the 1-yr (0.931) and 2-yr (1.11) |

- Only window on the San Mateo Creek dashboard. Comparison assumes Crystal Springs Cottage (CSC), the gauge FEWS uses.

## Open items

- OneRain thresholds: Which rain gauge does the San Mateo Creek dashboard color?
- `smc_rain_csc`: check they open the Rain Increment sensor
- `smc_stage_11162753`: Confirm whether this gauge reads the tide; Flow below Crystal Springs dam; reservoir level is USGS 11162750 (spill at 294.6 ft)
- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
- Link to flooding: find the creek height at each gauge where the creek leaves its banks or floods a road (survey, hydraulic study, or a past flood with gauge readings), then add it to thresholds.csv (THRESHOLDS_BASIS.md, Terms)
