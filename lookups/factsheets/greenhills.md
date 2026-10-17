# Green Hills Creek

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `greenhills` |
| On the site | Staff preview only (`preview_only = yes`) |
| Cities and communities | Millbrae *(draft - confirm cities and outlet)* |
| Drains to | Highline Canal, then San Francisco Bay |
| Description | Small creek through Green Hills Country Club in Millbrae. |
| Linked to flooding | **No**: alert levels only (rain and rising fast). No creek height here is tied to flooding yet |
| Tide station | NOAA 9414750 Alameda (MHHW 6.37 ft NAVD88) |
| Rain totals shown | 30 min, 1 hr, 3 hr, 24 hr |

**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).

## Creek level gauges

### Green Hills Creek at Green Hills Country Club

| | |
|---|---|
| Gauge key | `gh_stage_41201` |
| Source and ID | OneRain 41201 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=47&site=1e070958-e7b5-4329-b29d-eddf7da7df2d&device_id=1&device=aaf1108b-3657-42f4-9459-515d75c3eb7c)) |
| Location | 37.60130, -122.40930 |
| Reports | On change (about hourly in dry weather) |
| Record | Dec 24, 2024 (public OneRain pages) |
| Tidal | To confirm (dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide; tidal influence still to confirm) |
| Rising fast | 0.5 ft in 60 min (default; not calibrated) |
| History and known issues | Flash flood Nov 17, 2025: 0.20 to 5.66 ft in 70 minutes. |
| Note shown on the site | No flood levels set yet · To check: check they open the Stage sensor; set reports; Confirm whether this gauge reads the tide |

**Flood levels:** none. No creek height at this gauge is tied to flooding yet, so the creek's status comes from alert levels only: rain and rising fast ([THRESHOLDS_BASIS.md §10](../THRESHOLDS_BASIS.md)).

**Rising fast (alert level), tested on 1.8 years of history.** Tested against 4.5 ft, the creek's typical yearly high (the median yearly peak, about a 2-year event). **This is not a flood level:** "warned" means an alert came before a typical yearly high, not before flooding.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 42.5 | 1 of 1 | 69 min |
| 0.5 ◀ current | 29.3 | 1 of 1 | 64 min |
| 0.75 | 21.5 | 1 of 1 | 50 min |
| 1.0 | 16.6 | 1 of 1 | 31 min |
| 1.5 | 9.4 | 1 of 1 | 19 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| Pilarcitos Dam (`gh_rain_pld`) | PLD | 37.54800, -122.42200 | nearby | Supporting (counts toward the rain level only) |

**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, not whether the creek floods.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Pilarcitos Dam | Heavy (1-yr) | 0.316 | 0.629 | 1.18 | 2.89 |
| Pilarcitos Dam | Very heavy (2-yr) | 0.383 | 0.763 | 1.41 | 3.66 |
| Pilarcitos Dam | Intense (5-yr) | 0.473 | 0.942 | 1.73 | 4.68 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Current OneRain dashboard thresholds

None recorded yet (`onerain_dashboard_thresholds.csv`).

## Open items

- `gh_stage_41201`: check they open the Stage sensor; set reports; Confirm whether this gauge reads the tide
- `gh_rain_pld`: check they open the Rain Increment sensor
- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
- Link to flooding: find the creek height at each gauge where the creek leaves its banks or floods a road (survey, hydraulic study, or a past flood with gauge readings), then add it to thresholds.csv (THRESHOLDS_BASIS.md, Terms)
