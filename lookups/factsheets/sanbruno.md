# San Bruno Creek

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** what do these levels mean for people downstream? FEWS has no recorded meaning. Who set them, and from what?

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
| Cities and communities | San Bruno; South San Francisco *(draft)* |
| Drains to | San Francisco Bay near SFO |
| Description | Short urban creek; the gauge at First Avenue is tidal (rises and falls with the Bay tide). |
| Flood levels set? | Yes, but what they mean isn't recorded |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the FEWS page | 15 min, 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Bruno Creek at First Avenue

| | |
|---|---|
| Source and ID | OneRain 41102 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=11&site=fe06588c-e5e6-4016-8a8f-2ba1f040636e&device_id=3&device=e481d107-65bb-4107-89ab-48484eb0e188)) |
| Location | 37.62273, -122.40671 |
| Reports | On change (typically every 1-5 hours in dry weather, minutes in storms) |
| Record starts | Sep 2020 (public OneRain pages) |
| Affected by the tide? | Yes. Rises and falls with the Bay tide |
| Rising-fast alert | 0.5 ft within an hour |
| History and known issues | Offline since Jun 3, 2026; the last reading (Jun 3, 2026) is probably a sensor fault. Gauge zero in NAVD88 unknown. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.40 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 3.60 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 4.80 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: **not recorded**.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 5.8 years of readings, against the lowest flood level (Flood Monitoring, 2.4 ft): "warned" means an alert came before the creek reached it.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 57.2 | 27 of 28 | 3.4 h |
| 0.5 (current setting) | 31.3 | 25 of 28 | 1.8 h |
| 0.75 | 17.9 | 15 of 28 | 42 min |
| 1.0 | 8.2 | 7 of 28 | 22 min |
| 1.5 | 2.8 | 2 of 28 | 14 min |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| San Bruno Mountain | 41200 | 37.69222, -122.44833 | upper watershed | Shown on the FEWS page and counts toward the rain alert |
| First Avenue | 41102 | 37.62273, -122.40671 | lower watershed | Shown on the FEWS page and counts toward the rain alert |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 15 min | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|---|
| San Bruno Mountain | Heavy (1-year) | 0.251 | 0.346 | 0.489 | 0.894 | 2.11 |
| San Bruno Mountain | Very heavy (2-year) | 0.302 | 0.417 | 0.589 | 1.07 | 2.68 |
| San Bruno Mountain | Intense (5-year) | 0.372 | 0.513 | 0.725 | 1.3 | 3.44 |
| First Avenue | Heavy (1-year) | 0.227 | 0.311 | 0.442 | 0.799 | 1.89 |
| First Avenue | Very heavy (2-year) | 0.277 | 0.379 | 0.538 | 0.97 | 2.36 |
| First Avenue | Intense (5-year) | 0.344 | 0.471 | 0.669 | 1.2 | 3.0 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: what FEWS uses compared with OneRain

FEWS shows this creek's status on its public pages. The **FEWS** columns are what the FEWS site uses today. The **OneRain** columns are what is set in OneRain itself (read Oct 16–17, 2026): *alarms* are thresholds set on a gauge, which send OneRain notifications; *dashboard colors* are how OneRain's dashboard colors a reading. FEWS doesn't read either; they're shown so the two can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | FEWS uses | OneRain alarm | Same? |
|---|---|---|---|---|
| San Bruno Creek at First Avenue | Flood Monitoring | 2.40 ft | – | FEWS only |
| San Bruno Creek at First Avenue | Flood Watch | 3.60 ft | – | FEWS only |
| San Bruno Creek at First Avenue | Flood Warning | 4.80 ft | – | FEWS only |
| San Bruno Creek at First Avenue | Rising fast | 0.5 ft within an hour | none | FEWS only |

No OneRain rain alarms or dashboard colors on: San Bruno Creek at First Avenue; San Bruno Mountain.

**Tide**

| | FEWS uses | OneRain dashboard color |
|---|---|---|
| Tide | NOAA 9414750 Alameda: tide graph and high-tide lines (MHHW 6.37 ft NAVD88) | none recorded |

Notes:

- No rain thresholds on this gauge in OneRain.

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
