# Atherton Channel

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?
> - [ ] **Atherton rain window:** OneRain's Atherton dashboard colors rain over 30 minutes, but its alarms use the same amounts (0.40 / 0.45 in) over 1 hour. Over 30 minutes they are close to a 5-year storm; over 1 hour, between a 1- and 2-year storm. Which window is intended?

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
| Description | Channelized creek; flood levels are for the area downstream of the Caltrain crossing. |
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
| Affected by the tide? | No. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
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

## Thresholds: what FEWS uses compared with OneRain

FEWS shows this creek's status on its public pages. The **FEWS** columns are what the FEWS site uses today. The **OneRain** columns are what is set in OneRain itself (read Oct 16–17, 2026): *alarms* are thresholds set on a gauge, which send OneRain notifications; *dashboard colors* are how OneRain's dashboard colors a reading. FEWS doesn't read either; they're shown so the two can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | FEWS uses | OneRain alarm | Same? |
|---|---|---|---|---|
| Atherton Channel at Alameda de las Pulgas | Flood Monitoring | 3.18 ft | 3.18 ft ("Potential flooding") | Same |
| Atherton Channel at Alameda de las Pulgas | Flood Watch | 4.60 ft | 4.60 ft ("Flooding probable with continued rain") | Same |
| Atherton Channel at Alameda de las Pulgas | Flood Warning | 5.65 ft | 5.65 ft ("Active flooding likely to occur downstream") | Same |
| Atherton Channel at Alameda de las Pulgas | Roadway Flooded | 10.40 ft | 10.40 ft ("Water detected on road") | Same |
| Atherton Channel at Alameda de las Pulgas | Rising fast | 0.5 ft within an hour | none | FEWS only |
| Atherton Channel upstream of CalTrain | Flood Monitoring | 2.80 ft | 2.80 ft ("Potential flooding") | Same |
| Atherton Channel upstream of CalTrain | Flood Watch | 4.10 ft | 4.10 ft ("Flooding probable with continued rain") | Same |
| Atherton Channel upstream of CalTrain | Flood Warning | 5.50 ft | 5.50 ft ("Active flooding likely to occur downstream") | Same |
| Atherton Channel upstream of CalTrain | Rising fast | 0.5 ft within an hour | none | FEWS only |

**Rain (inches within the time shown)**

FEWS's rain alerts (Heavy, Very heavy, Intense) are the 1-, 2- and 5-year storm at the gauge, checked over windows from 15 minutes to 48 hours; only the windows OneRain or a FEWS trigger uses are listed here.

| Gauge | Rain within | FEWS uses | OneRain alarm | OneRain dashboard color |
|---|---|---|---|---|
| Caltrain | 30 min | alerts: Heavy 0.272, Very heavy 0.343, Intense 0.439 in | none | orange from 0.400 in; red from 0.45 in |
| Caltrain | 1 hr | alerts: Heavy 0.383, Very heavy 0.483, Intense 0.618 in | Flood watch 0.40 in; Flood warning 0.45 in | none |

**Tide**

| | FEWS uses | OneRain dashboard color |
|---|---|---|
| Tide | NOAA 9414523 Redwood City: tide graph and high-tide lines (MHHW 7.02 ft NAVD88) | none recorded |

Notes:

- 40 / 0.45 in) but over 30 min.

<details><summary>Internal to-do for the FEWS team (reviewers can skip)</summary>

- Ask OneRain how alarms on a Rain Increment sensor are checked: each report on its own, or rain summed over the window in the alarm's name? If each report on its own, these alarms may rarely fire.

</details>

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
