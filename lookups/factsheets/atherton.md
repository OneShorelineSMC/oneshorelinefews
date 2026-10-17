# Atherton Channel

*Fact sheet generated from the FEWS lookup tables by `scripts/build_creek_factsheets.py`. Don't edit this page; edit the tables and rerun the script.*

## At a glance

| | |
|---|---|
| Creek id | `atherton` |
| On the site | Public |
| Cities and communities | Woodside (upper watershed); Atherton; unincorporated North Fair Oaks; Redwood City *(draft - confirm cities and outlet)* |
| Drains to | Bayfront Canal, then San Francisco Bay |
| Description | Channelized creek; thresholds are for the area downstream of the Caltrain crossing. |
| Linked to flooding | **Yes**: flood levels at the creek gauge (what they mean is below) |
| Tide station | NOAA 9414523 Redwood City (MHHW 7.02 ft NAVD88) |
| Rain totals shown | 30 min, 1 hr, 24 hr |

**Flood levels** are creek heights (or rain triggers) tied to an effect downstream, such as how full the channel is or water on a road. **Alert levels** say how unusual the rain is or how fast the creek is rising; they aren't tied to flooding at this creek. Definitions: [THRESHOLDS_BASIS.md, Terms](../THRESHOLDS_BASIS.md#terms).

## Creek level gauges

### Atherton Channel at Alameda de las Pulgas

| | |
|---|---|
| Gauge key | `ath_alameda` |
| Source and ID | OneRain 41107 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=48&site=222db05c-ef0a-4720-b2c1-aaba882205f8&device_id=5&device=24188afc-3ba7-498b-b865-c186ddd1f7f5)) |
| Location | 37.43736, -122.21336 |
| Reports | Hourly, with extra readings in storms |
| Record | Jan 27, 2026 (public OneRain pages) |
| Tidal | No |
| Rising fast | 0.5 ft in 60 min (default; not calibrated) |
| History and known issues | Short record: no Flood Monitoring crossing yet. |

**Flood levels** (gauge height, ft; gauge's own zero, not NAVD88)

| Level | Name | Stage (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 3.18 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 4.60 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 5.65 | OneRain sensor thresholds (Oct 2026) |  |
| 4 | Roadway Flooded | 10.40 | OneRain sensor thresholds (Oct 2026) | Water detected on road |

Meaning: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).
By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.
Basis and sign-off status: [THRESHOLDS_BASIS.md §1](../THRESHOLDS_BASIS.md).

**Rising fast (alert level), tested on 0.7 years of history.** Tested against the gauge's lowest flood level, Flood Monitoring at 3.18 ft, so "warned" means an alert came before the creek reached that level.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 9 total | 0 of 0 | – |
| 0.5 ◀ current | 4 total | 0 of 0 | – |
| 0.75 | 3 total | 0 of 0 | – |
| 1.0 | 2 total | 0 of 0 | – |
| 1.5 | 0 total | 0 of 0 | – |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

### Atherton Channel upstream of CalTrain

| | |
|---|---|
| Gauge key | `ath_caltrain` |
| Source and ID | OneRain 41106 ([page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=14&site=a63a9e54-703b-43b1-8286-6cabbaae7fa1&device_id=4&device=b1b9cc5f-9ad6-498b-96cb-fc299b4eab79)) |
| Location | 37.46192, -122.19387 |
| Reports | On change |
| Record | Oct 2020 (public OneRain pages) |
| Tidal | No (dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide) |
| Rising fast | 0.5 ft in 60 min |
| History and known issues | Probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow. |
| Note shown on the site | The probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow. |

**Flood levels** (gauge height, ft; gauge's own zero, not NAVD88)

| Level | Name | Stage (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.80 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 4.10 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 5.50 | OneRain sensor thresholds (Oct 2026) |  |

Meaning: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).
By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.
Basis and sign-off status: [THRESHOLDS_BASIS.md §1](../THRESHOLDS_BASIS.md).

**Rising fast (alert level), tested on 6.0 years of history.** Tested against the gauge's lowest flood level, Flood Monitoring at 2.8 ft, so "warned" means an alert came before the creek reached that level.

| Threshold (ft in 60 min) | Alerts / yr | Warned before reaching it | Median lead |
|---|---|---|---|
| 0.25 | 33.2 | 24 of 25 | 2.9 h |
| 0.5 ◀ current | 28.1 | 24 of 25 | 2.1 h |
| 0.75 | 20.3 | 23 of 25 | 86 min |
| 1.0 | 16.4 | 22 of 25 | 58 min |
| 1.5 | 8.6 | 15 of 25 | 38 min |

Method, choices and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

## Rain gauges

| Gauge | OneRain ID | Location | Where | Role |
|---|---|---|---|---|
| Caltrain (`ath_rain`) | 41106 | 37.46192, -122.19387 | upstream of Caltrain | Primary (shown on the pages) |

**Rain alert levels at each gauge** (NOAA Atlas 14 depths, in): Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year, for the heaviest window of rain. They say how rare the rain is at the gauge, not whether the creek floods.

| Gauge | Level | 15 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Caltrain | Heavy (1-yr) | 0.197 | 0.383 | 0.712 | 1.6 |
| Caltrain | Very heavy (2-yr) | 0.248 | 0.483 | 0.893 | 2.04 |
| Caltrain | Intense (5-yr) | 0.318 | 0.618 | 1.13 | 2.63 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13). Basis: [THRESHOLDS_BASIS.md §8](../THRESHOLDS_BASIS.md).

## Current OneRain dashboard thresholds

None recorded yet (`onerain_dashboard_thresholds.csv`).

## Open items

- Confirm cities and outlet in creek_facts.csv (draft - confirm cities and outlet)
