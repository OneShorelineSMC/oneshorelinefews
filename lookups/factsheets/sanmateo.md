# San Mateo Creek

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** FEWS has none. Do you know a creek height at the gauge where the creek leaves its banks or floods a road, or a past flood we could match to a gauge reading?
> - [ ] **San Mateo dashboard:** which rain gauge does OneRain's San Mateo Creek dashboard color (3-hour rain)? The comparison here assumes Crystal Springs Cottage.

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
| On the FEWS site | Staff preview only (not yet on the public pages) |
| Cities and communities | Hillsborough; San Mateo *(draft)* |
| Drains to | San Francisco Bay |
| Description | Flow below Crystal Springs Reservoir is controlled by SFPUC releases and spills. |
| Flood levels set? | None |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the FEWS page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Mateo Creek Below Crystal Springs Reservoir

| | |
|---|---|
| Source and ID | USGS 11162753 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162753/)) |
| Location | 37.52944, -122.35833 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Sep 2008 |
| Affected by the tide? | Not yet confirmed. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
| Rising-fast alert | 0.5 ft within an hour |
| History and known issues | Rises follow Crystal Springs Reservoir releases and spills (reservoir level: USGS 11162750; spill about 294.6 ft). USGS data approved through spring 2026. |

**Flood levels:** none in FEWS, so this creek's status comes from alert levels only (rain and rising fast).

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 18.1 years of readings, against 5.88 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means an alert came before a typical yearly high, not before flooding.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 17.6 | 21 of 60 | 1.5 h |
| 0.5 (current setting) | 7.2 | 11 of 60 | 45 min |
| 0.75 | 3.1 | 3 of 60 | 75 min |
| 1.0 | 1.3 | 0 of 60 | – |
| 1.5 | 0.5 | 0 of 60 | – |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| Crystal Springs Cottage | CSC | 37.49600, -122.32900 | nearby | Counts toward the creek's rain alert only (not shown on the page) |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Crystal Springs Cottage | Heavy (1-year) | 0.357 | 0.505 | 0.931 | 2.12 |
| Crystal Springs Cottage | Very heavy (2-year) | 0.431 | 0.61 | 1.11 | 2.73 |
| Crystal Springs Cottage | Intense (5-year) | 0.532 | 0.753 | 1.36 | 3.54 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: what FEWS uses compared with OneRain

On the public FEWS pages this creek shows readings only; its status (below) shows only in the staff preview. The **FEWS** columns are what the FEWS site uses today. The **OneRain** columns are what is set in OneRain itself (read Oct 16–17, 2026): *alarms* are thresholds set on a gauge, which send OneRain notifications; *dashboard colors* are how OneRain's dashboard colors a reading. FEWS doesn't read either; they're shown so the two can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | FEWS uses | OneRain alarm | Same? |
|---|---|---|---|---|
| San Mateo Creek Below Crystal Springs Reservoir | – | none | none | – |
| San Mateo Creek Below Crystal Springs Reservoir | Rising fast | 0.5 ft within an hour | none | FEWS only |

**Rain (inches within the time shown)**

FEWS's rain alerts (Heavy, Very heavy, Intense) are the 1-, 2- and 5-year storm at the gauge, checked over windows from 15 minutes to 48 hours; only the windows OneRain or a FEWS trigger uses are listed here.

| Gauge | Rain within | FEWS uses | OneRain alarm | OneRain dashboard color |
|---|---|---|---|---|
| to confirm | 3 hr | – (FEWS doesn't use this gauge) | none | orange from 0.800 in; red from 1.000 in |

No OneRain rain alarms or dashboard colors on: Crystal Springs Cottage.

**Tide**

| | FEWS uses | OneRain dashboard color |
|---|---|---|
| Tide | NOAA 9414750 Alameda: tide graph and high-tide lines (MHHW 6.37 ft NAVD88) | none recorded |

Notes:

- Comparison assumes Crystal Springs Cottage (CSC), the gauge FEWS uses.
- No rain thresholds on this gauge in OneRain.

<details><summary>Internal to-do for the FEWS team (reviewers can skip)</summary>

- Crystal Springs Cottage (rain): check they open the Rain Increment sensor
- Below Crystal Springs Reservoir (stage): Confirm whether this gauge reads the tide; Flow below Crystal Springs dam; reservoir level is USGS 11162750 (spill at 294.6 ft)

</details>

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
