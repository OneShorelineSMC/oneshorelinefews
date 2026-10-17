# Colma Creek

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?

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
| Cities and communities | Daly City; Colma; South San Francisco *(draft)* |
| Drains to | San Francisco Bay at South San Francisco |
| Description | Urban creek from San Bruno Mountain and Daly City through Colma to South San Francisco; the gauge is at Orange Memorial Park and the flood levels are for the community downstream. |
| Flood levels set? | Yes |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the FEWS page | 1 hr, 6 hr, 24 hr |

## Creek level gauges

### Colma Creek at Orange Memorial Park

| | |
|---|---|
| Source and ID | OneRain 41101 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=12&site=32e8ebb1-4c9c-460a-a4cd-58903b96f347&device_id=5&device=dbbbcf6d-6a38-44a5-a90b-7077db13c5c2)) |
| Location | 37.65379, -122.42669 |
| Reports | Every 12 hours plus extra readings in some storms until May 2025; hourly plus extra storm readings since Oct 2025 |
| Record starts | Jun 2020 (public OneRain pages) |
| Affected by the tide? | Yes. Staff (Oct 16, 2026): tidally influenced at Orange Memorial Park. A dry-weather check (Oct 12-14, 2026) saw 0.04 ft or less of movement with the tide, so the tide likely matters mainly in storms, when high tides can back water up the creek; not yet measured |
| Rising-fast alert | 0.5 ft within an hour (default; not yet tested on this gauge's history) |
| History and known issues | Outages: Jun 23 - Oct 6, 2020; Nov 24 - Dec 15, 2021; May 29 - Oct 16, 2025. Sensor faults: Jul 15, 2022 (readings to about 16.7 ft); Aug 18, 2022 (one-reading spike to 4.56 ft). When it switches from hourly to faster readings in a storm, the rising-fast check can miss the rise (RISING_FAST_BASIS.md section 8). |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 3.40 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 5.00 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 6.75 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 6.3 years of readings, against the lowest flood level (Flood Monitoring, 3.4 ft): "warned" means an alert came before the creek reached it. Only 7 such rises in the record, so treat these results as rough.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 9.2 | 3 of 7 | 80 min |
| 0.5 (current setting) | 5.9 | 3 of 7 | 80 min |
| 0.75 | 3.3 | 2 of 7 | 3.2 h |
| 1.0 | 2.5 | 2 of 7 | 3.2 h |
| 1.5 | 1.1 | 1 of 7 | 80 min |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| Orange Memorial Park | 41101 | 37.65379, -122.42669 | lower watershed | Shown on the FEWS page and counts toward the rain alert |
| San Bruno Mountain | 41200 | 37.69222, -122.44833 | upper watershed | Counts toward the creek's rain alert only (not shown on the page) |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 1 hr | 6 hr | 24 hr |
|---|---|---|---|---|
| Orange Memorial Park | Heavy (1-year) | 0.456 | 1.15 | 1.87 |
| Orange Memorial Park | Very heavy (2-year) | 0.546 | 1.38 | 2.39 |
| Orange Memorial Park | Intense (5-year) | 0.669 | 1.69 | 3.07 |
| San Bruno Mountain | Heavy (1-year) | 0.489 | 1.26 | 2.11 |
| San Bruno Mountain | Very heavy (2-year) | 0.589 | 1.52 | 2.68 |
| San Bruno Mountain | Intense (5-year) | 0.725 | 1.86 | 3.44 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: what FEWS uses compared with OneRain

FEWS shows this creek's status on its public pages. The **FEWS** columns are what the FEWS site uses today. The **OneRain** columns are what is set in OneRain itself (read Oct 16–17, 2026): *alarms* are thresholds set on a gauge, which send OneRain notifications; *dashboard colors* are how OneRain's dashboard colors a reading. FEWS doesn't read either; they're shown so the two can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | FEWS uses | OneRain alarm | Same? |
|---|---|---|---|---|
| Colma Creek at Orange Memorial Park | Flood Monitoring | 3.40 ft | – | FEWS only |
| Colma Creek at Orange Memorial Park | Flood Watch | 5.00 ft | – | FEWS only |
| Colma Creek at Orange Memorial Park | Flood Warning | 6.75 ft | – | FEWS only |
| Colma Creek at Orange Memorial Park | Rising fast | 0.5 ft within an hour | none | FEWS only |

**Rain (inches within the time shown)**

FEWS's rain alerts (Heavy, Very heavy, Intense) are the 1-, 2- and 5-year storm at the gauge, checked over windows from 15 minutes to 48 hours; only the windows OneRain or a FEWS trigger uses are listed here.

| Gauge | Rain within | FEWS uses | OneRain alarm | OneRain dashboard color |
|---|---|---|---|---|
| Orange Memorial Park | 1 hr | alerts: Heavy 0.456, Very heavy 0.546, Intense 0.669 in | none | none |
| Orange Memorial Park | 6 hr | alerts: Heavy 1.15, Very heavy 1.38, Intense 1.69 in | none | orange from 1.50 in; red from 2 in |

No OneRain rain alarms or dashboard colors on: San Bruno Mountain.

**Tide**

| | FEWS uses | OneRain dashboard color |
|---|---|---|
| Tide | NOAA 9414750 Alameda: tide graph and high-tide lines (MHHW 6.37 ft NAVD88) | none recorded |

Notes:

- Rain thresholds set on the Rain Increment sensor (rain since the gauge's last report); not published on the public site.
- No rain thresholds on this gauge in OneRain.

<details><summary>Internal to-do for the FEWS team (reviewers can skip)</summary>

- Ask OneRain how thresholds on a Rain Increment sensor are checked, and which alarm rules (notifications) use them: each report on its own, or rain summed over the window in the threshold's name? If each report on its own, these thresholds may rarely be reached.

</details>

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
