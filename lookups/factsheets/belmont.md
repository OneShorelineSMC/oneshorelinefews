# Belmont Creek

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?
> - [ ] **Rain triggers:** are the amounts and what they show right?
> - [ ] **Flooding likely (rain + tide):** the tide part (6.32 ft NAVD88) is below the average daily high tide at Redwood City (MHHW 7.02 ft), so it is met on most days' higher high tide. Is that the intended tide level?
> - [ ] FEWS shows 'Flooding likely' at 0.20 in / 30 min (thresholds.csv, citing this dashboard), where the dashboard only turns orange; red starts at 0.25 in. Which should FEWS use?

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
| Cities and communities | Belmont; San Carlos; unincorporated Harbor Industrial Area *(draft)* |
| Drains to | Belmont Slough, then San Francisco Bay |
| Description | Flashy urban creek; frequent street flooding downstream; thresholds are for the Harbor Industrial Area. |
| Flood levels set? | Yes; plus rain triggers |
| Tide station | NOAA 9414523 Redwood City (average daily high tide, MHHW, 7.02 ft NAVD88) |
| Rain totals on the FEWS page | 30 min, 1 hr, 4 hr, 24 hr |

## Creek level gauges

### Belmont Creek at Old County Rd

| | |
|---|---|
| Source and ID | OneRain 41104 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=2&site=25fd9d56-e3ea-4ff9-a067-b3e99cc5c1fe&device_id=1&device=5c101ccb-75e1-4c68-a983-4b8c78913c03)) |
| Location | 37.51719, -122.27125 |
| Reports | On change: every 12 hours in dry weather, every few minutes in storms |
| Record starts | Oct 2019 or earlier (pulled from Oct 1, 2019) |
| Affected by the tide? | No. Dry-weather check Oct 12-14, 2026: moved 0.04 ft or less with the tide |
| Rising-fast alert | 0.5 ft within an hour |
| History and known issues | 27 single-reading sensor spikes of 1 ft or more from Oct 2019 to 2022 (e.g. 0.09 to 7.97 to 0.08 ft on Oct 17, 2019); none since 2023. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.25 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 3.25 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 4.00 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 7.0 years of readings, against the lowest flood level (Flood Monitoring, 2.25 ft): "warned" means an alert came before the creek reached it.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 27.6 | 44 of 45 | 59 min |
| 0.5 (current setting) | 23.6 | 44 of 45 | 42 min |
| 0.75 | 19.0 | 44 of 45 | 16 min |
| 1.0 | 14.9 | 42 of 45 | 10 min |
| 1.5 | 10.5 | 33 of 45 | 6 min |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| Old County Road | 41104 | 37.51719, -122.27125 | lower watershed | Shown on the FEWS page and counts toward the rain alert |

**Rain triggers** (flood levels for rain: each one sets the creek to the status shown)

| Gauge | Rain within | Rain (in) | And the tide is at least | Shows | Source |
|---|---|---|---|---|---|
| Old County Road | 30 min | 0.20 | – | Flooding likely (rain) | Belmont Creek OneRain dashboard (Oct 2026) |
| Old County Road | 4 hr | 0.42 | 6.32 ft NAVD88 | Flooding likely (rain + tide) | OneRain alarm rule 'Rainfall and Tide (Belmont)' #34: 4 Hr Accumulation >= 0.42 in and OneRain Redwood City Tide Elevation >= 7.5 ft. OneRain's tide is MLLW; NOAA 9414523 MLLW is 1.18 ft below NAVD88, so 7.5 ft MLLW = 6.32 ft NAVD88. Rain threshold from analysis of 2022-2025 events |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 24 hr |
|---|---|---|---|---|
| Old County Road | Heavy (1-year) | 0.305 | 0.432 | 1.76 |
| Old County Road | Very heavy (2-year) | 0.366 | 0.517 | 2.29 |
| Old County Road | Intense (5-year) | 0.45 | 0.637 | 2.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Appendix: OneRain settings (for comparison only)

These are set in OneRain itself, on its dashboards (colors) and on the gauges (alarms). FEWS doesn't use them unless the "Also a FEWS level?" column says Yes. Read from OneRain on Oct 16–17, 2026.

**Rain**

| Gauge | Kind | Rain within | Color | Rain (in) | OneRain name | Also a FEWS level? | How rare at this gauge |
|---|---|---|---|---|---|---|---|
| Belmont Creek at Old County Rd [1] | Dashboard color | 30 min | Green | 0–0.199 | – | No | – |
| Belmont Creek at Old County Rd | Dashboard color | 30 min | Orange | 0.20–0.249 | – | No | less than a 1-year storm (0.305 in) |
| Belmont Creek at Old County Rd | Dashboard color | 30 min | Red | 0.25 and up | – | No | less than a 1-year storm (0.305 in) |

Notes:

1. Only window on the Belmont dashboard.

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
