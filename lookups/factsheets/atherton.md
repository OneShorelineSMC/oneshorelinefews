# Atherton Channel

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?
> - [ ] Window: dashboard uses 30 min, the gauge alarms use 1 hour for the same amounts. Which is intended?

> **How to read this page**
>
> - **Flood level:** a creek height (or rain amount) tied to an effect downstream, such as how full the channel is or water on a road. Only flood levels say anything about flooding.
> - **Alert level:** says how unusual the rain is, or how fast the creek is rising. Not tied to flooding.
> - **Rising fast:** the creek rose at least the set amount (for example 0.5 ft) within an hour.
> - **Creek heights** are the gauge's own reading in feet (height above the gauge's zero), not an elevation. **Tide heights** are in feet NAVD88, a survey datum. MHHW = the average daily high tide; MLLW = the average daily low tide.
> - **1-year, 2-year, 5-year storm:** rain that heavy at that gauge has about a 63%, 39% or 18% chance in any year (NOAA Atlas 14).
> - **Water year (WY):** October 1 to September 30, named for the year it ends.
> - **OneRain** is the system that runs the gauges and the County's dashboards; FEWS is the public flood warning site built on its data.

## At a glance

| | |
|---|---|
| On the FEWS site | Public pages |
| Cities and communities | Woodside (upper watershed); Atherton; unincorporated North Fair Oaks; Redwood City *(draft)* |
| Drains to | Bayfront Canal, then San Francisco Bay |
| Description | Channelized creek; thresholds are for the area downstream of the Caltrain crossing. |
| Flood levels set? | Yes |
| Tide station | NOAA 9414523 Redwood City (average daily high tide, MHHW, 7.02 ft NAVD88) |
| Rain totals on the FEWS page | 30 min, 1 hr, 24 hr |

## Creek level gauges

### Atherton Channel at Alameda de las Pulgas

| | |
|---|---|
| Source and ID | OneRain 41107 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=48&site=222db05c-ef0a-4720-b2c1-aaba882205f8&device_id=5&device=24188afc-3ba7-498b-b865-c186ddd1f7f5)) |
| Location | 37.43736, -122.21336 |
| Reports | Hourly, with extra readings in storms |
| Record starts | Jan 27, 2026 (public OneRain pages) |
| Affected by the tide? | No |
| Rising-fast alert | 0.5 ft within an hour (default; not yet tested on this gauge's history) |
| History and known issues | Short record: no Flood Monitoring crossing yet. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 3.18 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 4.60 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 5.65 | OneRain sensor thresholds (Oct 2026) |  |
| 4 | Roadway Flooded | 10.40 | OneRain sensor thresholds (Oct 2026) | Water detected on road |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely). Roadway Flooded = water detected on the road.

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 0.7 years of readings, against the lowest flood level (Flood Monitoring, 3.18 ft): "warned" means an alert came before the creek reached it. Only 0 such rises in the record, so treat these results as rough.

| Alert setting (ft within an hour) | Alerts (total) | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 9 | 0 of 0 | – |
| 0.5 (current setting) | 4 | 0 of 0 | – |
| 0.75 | 3 | 0 of 0 | – |
| 1.0 | 2 | 0 of 0 | – |
| 1.5 | 0 | 0 of 0 | – |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Atherton Channel upstream of CalTrain

| | |
|---|---|
| Source and ID | OneRain 41106 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=14&site=a63a9e54-703b-43b1-8286-6cabbaae7fa1&device_id=4&device=b1b9cc5f-9ad6-498b-96cb-fc299b4eab79)) |
| Location | 37.46192, -122.19387 |
| Reports | On change |
| Record starts | Oct 2020 (public OneRain pages) |
| Affected by the tide? | No. Dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide |
| Rising-fast alert | 0.5 ft within an hour |
| History and known issues | Probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow. |
| Note shown on the FEWS page | The probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.80 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 4.10 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 5.50 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 6.0 years of readings, against the lowest flood level (Flood Monitoring, 2.8 ft): "warned" means an alert came before the creek reached it.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 33.2 | 24 of 25 | 2.9 h |
| 0.5 (current setting) | 28.1 | 24 of 25 | 2.1 h |
| 0.75 | 20.3 | 23 of 25 | 86 min |
| 1.0 | 16.4 | 22 of 25 | 58 min |
| 1.5 | 8.6 | 15 of 25 | 38 min |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| Caltrain | 41106 | 37.46192, -122.19387 | upstream of Caltrain | Shown on the FEWS page and counts toward the rain alert |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 24 hr |
|---|---|---|---|---|
| Caltrain | Heavy (1-year) | 0.272 | 0.383 | 1.6 |
| Caltrain | Very heavy (2-year) | 0.343 | 0.483 | 2.04 |
| Caltrain | Intense (5-year) | 0.439 | 0.618 | 2.63 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Appendix: OneRain settings (for comparison only)

These are set in OneRain itself, on its dashboards (colors) and on the gauges (alarms). FEWS doesn't use them unless the "Also a FEWS level?" column says Yes. Read from OneRain on Oct 16–17, 2026.

**Rain**

| Gauge | Kind | Rain within | Color | Rain (in) | OneRain name | Also a FEWS level? | How rare at this gauge |
|---|---|---|---|---|---|---|---|
| Atherton Channel upstream of CalTrain [1] | Dashboard color | 30 min | Green | 0–0.399 | – | No | – |
| Atherton Channel upstream of CalTrain | Dashboard color | 30 min | Orange | 0.400–0.449 | – | No | between a 2- and 5-year storm (0.343–0.439 in) |
| Atherton Channel upstream of CalTrain | Dashboard color | 30 min | Red | 0.45 and up | – | No | between a 5- and 10-year storm (0.439–0.518 in) |
| Atherton Channel upstream of CalTrain | Alarm | 1 hr | Orange | 0.40 and up | Hourly rainfall intensity flood watch | No | between a 1- and 2-year storm (0.383–0.483 in) |
| Atherton Channel upstream of CalTrain | Alarm | 1 hr | Red | 0.45 and up | Hourly rainfall intensity flood warning | No | between a 1- and 2-year storm (0.383–0.483 in) |

Notes:

1. Only window on the Atherton dashboard. Same values as the gauge's hourly alarms (0.40 / 0.45 in) but over 30 min.

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
