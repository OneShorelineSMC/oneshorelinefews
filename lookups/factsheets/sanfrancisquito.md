# San Francisquito Creek

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** FEWS has none. Do you know a creek height at the gauge where the creek leaves its banks or floods a road, or a past flood we could match to a gauge reading?

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
| Cities and communities | Woodside; Portola Valley; Menlo Park; East Palo Alto; Palo Alto; Stanford (unincorporated Santa Clara County) *(draft)* |
| Drains to | San Francisco Bay |
| Description | Large creek on the San Mateo / Santa Clara county line; the USGS gauge is at Stanford. |
| Flood levels set? | None |
| Tide station | NOAA 9414523 Redwood City (average daily high tide, MHHW, 7.02 ft NAVD88) |
| Rain totals on the FEWS page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Francisquito Creek at Stanford

| | |
|---|---|
| Source and ID | USGS 11164500 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11164500/)) |
| Location | 37.42327, -122.18941 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007; USGS record is longer) |
| Affected by the tide? | Not yet confirmed. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
| Rising-fast alert | 0.5 ft within an hour |
| History and known issues | USGS data approved through spring 2026, provisional since Apr 2026. |

**Flood levels:** none in FEWS, so this creek's status comes from alert levels only (rain and rising fast).

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 6.0 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means an alert came before a typical yearly high, not before flooding.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 19.9 | 20 of 20 | 4.6 h |
| 0.5 (current setting) | 9.5 | 20 of 20 | 3.0 h |
| 0.75 | 4.9 | 17 of 20 | 2.0 h |
| 1.0 | 3.0 | 12 of 20 | 60 min |
| 1.5 | 0.9 | 5 of 20 | 30 min |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| Wunderlich County Park | A08363E2 | 37.40243, -122.27486 | upper watershed | Shown on the FEWS page and counts toward the rain alert |
| Windy Hill Open Space Preserve | A0839DB4 | 37.35799, -122.23990 | upper watershed | Counts toward the creek's rain alert only (not shown on the page) |
| Trappers Trail (Valley Water) | A08204FE | 37.34611, -122.18083 | upper watershed | Counts toward the creek's rain alert only (not shown on the page) |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Wunderlich County Park | Heavy (1-year) | 0.517 | 0.734 | 1.37 | 3.28 |
| Wunderlich County Park | Very heavy (2-year) | 0.649 | 0.921 | 1.71 | 4.22 |
| Wunderlich County Park | Intense (5-year) | 0.822 | 1.17 | 2.16 | 5.46 |
| Windy Hill Open Space Preserve | Heavy (1-year) | 0.488 | 0.692 | 1.29 | 3.1 |
| Windy Hill Open Space Preserve | Very heavy (2-year) | 0.613 | 0.869 | 1.62 | 3.96 |
| Windy Hill Open Space Preserve | Intense (5-year) | 0.777 | 1.1 | 2.04 | 5.08 |
| Trappers Trail (Valley Water) | Heavy (1-year) | 0.427 | 0.603 | 1.11 | 2.65 |
| Trappers Trail (Valley Water) | Very heavy (2-year) | 0.535 | 0.756 | 1.4 | 3.34 |
| Trappers Trail (Valley Water) | Intense (5-year) | 0.677 | 0.956 | 1.77 | 4.25 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: what FEWS uses compared with OneRain

On the public FEWS pages this creek shows readings only; its status (below) shows only in the staff preview. The **FEWS** columns are what the FEWS site uses today. The **OneRain** columns are what is set in OneRain itself (read Oct 16–17, 2026): *alarms* are thresholds set on a gauge, which send OneRain notifications; *dashboard colors* are how OneRain's dashboard colors a reading. FEWS doesn't read either; they're shown so the two can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | FEWS uses | OneRain alarm | Same? |
|---|---|---|---|---|
| San Francisquito Creek at Stanford | – | none | none | – |
| San Francisquito Creek at Stanford | Rising fast | 0.5 ft within an hour | none | FEWS only |

No OneRain rain alarms or dashboard colors on: Trappers Trail; Wunderlich County Park; Windy Hill Open Space Preserve.

**Tide**

| | FEWS uses | OneRain dashboard color |
|---|---|---|
| Tide | NOAA 9414523 Redwood City: tide graph and high-tide lines (MHHW 7.02 ft NAVD88) | none recorded |

Notes:

- No rain thresholds on this gauge in OneRain.

<details><summary>Internal to-do for the FEWS team (reviewers can skip)</summary>

- Stanford (stage): USGS 11164500; OneRain site SFC shows the same gauge, so read it from USGS. Confirm whether this gauge reads the tide
- Wunderlich County Park (rain): check they open the Rain Increment sensor; pick one for the card
- Windy Hill Open Space Preserve (rain): check they open the Rain Increment sensor; pick one for the card
- Trappers Trail (Valley Water) (rain): check they open the Rain Increment sensor; pick one for the card

</details>

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
