# Pescadero Creek

*Draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** FEWS has none, but OneRain has its own at Pescadero Creek near Pescadero, Butano Creek near Cloverdale Road (see the appendix). Do you know who set them and from what? Should FEWS use them?
> - [ ] **Monterey tide color:** is OneRain's 7 ft measured from MLLW (the average daily low tide)? The screen doesn't say.
> - [ ] **Butano rain alarm:** OneRain's 6-hour 'Rainfall warning' (1.04 in, OneRain severity 'Critical') fires below the Butano dashboard's orange (1.2 in) and red (1.44 in). Which is intended?

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
| Cities and communities | Unincorporated Pescadero; Loma Mar; La Honda area *(draft)* |
| Drains to | Pescadero Marsh, then the Pacific Ocean |
| Description | Rural coastal creek; the town of Pescadero floods from Pescadero and Butano Creeks. |
| Flood levels set? | None in FEWS (OneRain has some; see the appendix) |
| Tide station | None set for this creek in FEWS (coastal creek). OneRain's dashboard uses Monterey tide (NOAA 9413450) |
| Rain totals on the FEWS page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### Pescadero Creek at Stage Road

| | |
|---|---|
| Source and ID | OneRain 41151 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=28&site=b7ae4c33-4536-443f-bcc5-72ded98d2412&device_id=1&device=cbd2cde7-ac86-4ad2-8a9d-a2f6d7575cd8)) |
| Location | 37.25468, -122.38330 |
| Reports | On change (every 2-12 hours in dry weather) |
| Record starts | Oct 13, 2023 (public OneRain pages) |
| Affected by the tide? | No |
| Rising-fast alert | 1.0 ft within an hour |

**Flood levels:** none in FEWS, so this creek's status comes from alert levels only (rain and rising fast).

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 3.0 years of readings, against 11.52 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means an alert came before a typical yearly high, not before flooding. Only 3 such rises in the record, so treat these results as rough.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 10.0 | 3 of 3 | 5.1 h |
| 0.5 | 5.3 | 3 of 3 | 5.1 h |
| 0.75 | 4.0 | 3 of 3 | 5.1 h |
| 1.0 (current setting) | 3.0 | 3 of 3 | 4.9 h |
| 1.5 | 1.0 | 3 of 3 | 4.1 h |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Pescadero Creek near Pescadero

| | |
|---|---|
| Source and ID | USGS 11162500 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162500/)) |
| Location | 37.26096, -122.32890 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007) |
| Affected by the tide? | No |
| Rising-fast alert | 1.0 ft within an hour |
| History and known issues | Typical water level has crept up over the record (channel change). |

**Flood levels:** none in FEWS, so this creek's status comes from alert levels only (rain and rising fast). OneRain has its own levels for this gauge: see the appendix.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 10.41 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means an alert came before a typical yearly high, not before flooding.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 7.8 | 18 of 18 | 4.8 h |
| 0.5 | 5.3 | 18 of 18 | 3.2 h |
| 0.75 | 4.0 | 18 of 18 | 2.8 h |
| 1.0 (current setting) | 2.7 | 18 of 18 | 2.5 h |
| 1.5 | 1.7 | 16 of 18 | 82 min |

Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in FEWS |
|---|---|---|---|---|
| La Honda | LAH | 37.30530, -122.25390 | nearby | Counts toward the creek's rain alert only (not shown on the page) |

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 6 hr | 24 hr |
|---|---|---|---|---|---|---|
| La Honda | Heavy (1-year) | 0.476 | 0.676 | 1.26 | 1.81 | 3.06 |
| La Honda | Very heavy (2-year) | 0.597 | 0.846 | 1.57 | 2.26 | 3.89 |
| La Honda | Intense (5-year) | 0.755 | 1.07 | 1.98 | 2.85 | 4.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Appendix: OneRain settings (for comparison only)

These are set in OneRain itself, on its dashboards (colors) and on the gauges (alarms). FEWS doesn't use them unless the "Also a FEWS level?" column says Yes. Read from OneRain on Oct 16–17, 2026.

**Rain**

| Gauge | Kind | Rain within | Color | Rain (in) | OneRain name | Also a FEWS level? | How rare at this gauge |
|---|---|---|---|---|---|---|---|
| Butano Creek near Cloverdale Road [1] | Dashboard color | 6 hr | Green | 0–1.199 | – | No | – |
| Butano Creek near Cloverdale Road | Dashboard color | 6 hr | Orange | 1.2–1.439 | – | No | less than a 1-year storm (1.46 in) |
| Butano Creek near Cloverdale Road | Dashboard color | 6 hr | Red | 1.44 and up | – | No | less than a 1-year storm (1.46 in) |
| Butano Creek near Cloverdale Road [2] | Alarm | 6 hr | Red | 1.04 and up | Rainfall warning | No | less than a 1-year storm (1.46 in) |

**Creek height**

| Gauge | OneRain name | OneRain description | Height (ft) | Also a FEWS level? | Years reached, WY2008–2026 (USGS) |
|---|---|---|---|---|---|
| Pescadero Creek near Pescadero | Flood Watch | Flooding likely | 11.20 | No | 7 of 19 years (highest 16.93 ft) |
| Pescadero Creek near Pescadero | Flood Warning | Projected flooding in downstream reaches | 13.25 | No | 4 of 19 years (highest 16.93 ft) |
| Butano Creek near Cloverdale Road [3] | Flood Watch | Flooding likely | 10.10 | No | – |
| Butano Creek near Cloverdale Road [3] | Flood Warning | Flooding likely in downstream reaches | 11.80 | No | – |

**Tide**

| Station | Color | Range | Note |
|---|---|---|---|
| Monterey tide (NOAA 9413450) [4] | Green | -10 to 6.999 ft | Datum not shown in OneRain (assumed MLLW) |
| Monterey tide (NOAA 9413450) | Orange | 7 ft and up | Datum not shown in OneRain (assumed MLLW) |

No OneRain alarms are set on: La Honda; Pescadero Creek at Stage Road.

Notes:

1. Pescadero and Butano dashboard; only window. The dashboard lists the site as 'Butano'; staff confirmed it is 41152. FEWS uses La Honda for Pescadero, not Butano.
2. Set on OneRain's rolling 6-hour total sensor. Lower than the Butano dashboard colors (orange 1.2, red 1.44 in / 6 hr).
3. Butano Creek (no FEWS gauge); sensor is labeled backup.
4. Pescadero and Butano dashboard; no red level. If the 7 ft is measured from MLLW, it equals about 7.14 ft NAVD88: above the 1-year tide (6.87 ft NAVD88) FEWS uses to mark Coastside King Tides, and close to the highest tide the tide table predicts (7.21 ft NAVD88). The highest tide NOAA has measured at Monterey is 7.88 ft MLLW (Jan 27, 1983).

<details><summary>Internal to-do for the FEWS team (reviewers can skip)</summary>

- Stage Road (stage): check they open the Stage sensor; set reports
- La Honda (rain): check they open the Rain Increment sensor

</details>

---

*Generated from the FEWS lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
