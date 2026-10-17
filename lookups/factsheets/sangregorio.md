# San Gregorio Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** the 2026 Update has none, but OneRain has its own at San Gregorio Creek at San Gregorio (see Thresholds on this page). Do you know who set them and from what? Should the 2026 Update use them?

> **Words used on this page** (the same words for both systems)
>
> - **Threshold:** any set value that changes a color or a status, in either system.
> - **Flood level** (2026 Update): a threshold on creek height (or a rain amount) tied to an effect downstream, such as how full the channel is or water on a road. Only flood levels say anything about flooding.
> - **Alert level** (2026 Update): a rain alert (Heavy, Very heavy, Intense: how rare the rain is) or **rising fast** (the creek rose at least a set amount within an hour). Not tied to flooding.
> - **Status** (2026 Update): the one overall message for a creek: Flooding likely, Be ready, Stay alert or No alerts. It comes from the flood levels and alert levels.
> - **OneRain threshold:** a named level set on a OneRain sensor (for example Flood Watch, 3.25 ft). It colors that gauge's readings and graph; it doesn't send a message by itself.
> - **OneRain dashboard color:** the green, orange or red a OneRain dashboard gives a reading. Set separately from the thresholds.
> - **Notification:** a message sent to people. OneRain sends these through separate *alarm* rules. The 2026 Update sends none; it only displays.
>
> **Units.** Creek heights are the gauge's own reading in feet (above the gauge's zero), not an elevation. Tide heights are in feet NAVD88, a survey datum; MHHW = the average daily high tide, MLLW = the average daily low tide. A 1-, 2- or 5-year storm is rain that heavy at that gauge, with about a 63%, 39% or 18% chance in any year (NOAA Atlas 14). Water year: October 1 to September 30, named for the year it ends.
>
> **Names.** **OneRain** is the County's existing gauge system and dashboards (what many people call "FEWS"). **FEWS 2026 Update** ("2026 Update") is the new public creek and tide status site built on OneRain's data. These fact sheets describe the 2026 Update and compare it with OneRain.

## At a glance

| | |
|---|---|
| On the 2026 Update site | Staff preview only (not yet on the public pages) |
| Cities and communities | Unincorporated San Gregorio; La Honda (upper watershed) *(draft)* |
| Drains to | Pacific Ocean at San Gregorio State Beach |
| Description | Rural coastal creek. |
| Flood levels set? | None in the 2026 Update (OneRain has some; see Thresholds below) |
| Tide station | None set for this creek in the 2026 Update (coastal creek) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Gregorio Creek at San Gregorio

| | |
|---|---|
| Source and ID | USGS 11162570 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162570/)) |
| Location | 37.32578, -122.38664 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007) |
| Affected by the tide? | No |
| Rising-fast alert | 1.0 ft within an hour · **Tested on past data (19 yr)** |
| Why this rising-fast setting | 18 of 18 warned, about 3¾ h ahead; 3.8 alerts/yr vs 8.5 at 0.5 ft |
| History and known issues | Typical water level rose about 2 ft in 2016-17 and stayed higher for years (channel change). |

**Flood levels:** none in the 2026 Update, so this creek's status comes from alert levels only (rain and rising fast). OneRain has its own levels for this gauge: see Thresholds below.

<details><summary>Background: how the rising-fast alert performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 13.53 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means an alert came before a typical yearly high, not before flooding.

| Alert setting (ft within an hour) | Alerts per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 13.3 | 18 of 18 | 5.9 h |
| 0.5 | 8.5 | 18 of 18 | 4.6 h |
| 0.75 | 6.1 | 18 of 18 | 4.1 h |
| 1.0 (current setting) | 3.8 | 18 of 18 | 3.8 h |
| 1.5 | 2.4 | 14 of 18 | 2.6 h |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| La Honda | LAH | 37.30530, -122.25390 | nearby | Shown on the 2026 Update page and counts toward the rain alert |

**Rain alerts** (Heavy, Very heavy, Intense). Why these numbers: they are the 1-, 2- and 5-year storm at each gauge from NOAA Atlas 14, a standard way to say how rare rain is at that exact spot. Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain alert levels at each gauge (no action needed)</summary>

The creek's rain alert uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| La Honda | Heavy (1-year) | 0.476 | 0.676 | 1.26 | 3.06 |
| La Honda | Very heavy (2-year) | 0.597 | 0.846 | 1.57 | 3.89 |
| La Honda | Intense (5-year) | 0.755 | 1.07 | 1.98 | 4.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview. The **2026 Update** columns are what the new site uses. The **OneRain** columns are what is set in OneRain today (read Oct 16–17, 2026): *thresholds* set on each sensor, and *dashboard colors*. Neither sends a message by itself; OneRain sends notifications only through separate alarm rules. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |
|---|---|---|---|---|
| San Gregorio Creek at San Gregorio | Flood Monitoring | – | 15.00 ft ("Potential flooding") | OneRain only (the 2026 Update doesn't use it) |
| San Gregorio Creek at San Gregorio | Flood Watch | – | 17.70 ft ("Flooding probable with continued rain") | OneRain only (the 2026 Update doesn't use it) |
| San Gregorio Creek at San Gregorio | Flood Warning | – | 21.00 ft ("Flooding likely in downstream reaches") | OneRain only (the 2026 Update doesn't use it) |
| San Gregorio Creek at San Gregorio | Major Flood Stage | – | 25.00 ft ("Damaging flooding") | OneRain only (the 2026 Update doesn't use it) |
| San Gregorio Creek at San Gregorio | Rising fast | 1.0 ft within an hour | none | 2026 Update only |

How often the creek reached OneRain's levels (USGS record, water years 2008–2026): Flood Monitoring 15.00 ft: 4 of 19 years (highest 18.74 ft); Flood Watch 17.70 ft: 3 of 19 years (highest 18.74 ft); Flood Warning 21.00 ft: 0 of 19 years (highest 18.74 ft); Major Flood Stage 25.00 ft: 0 of 19 years (highest 18.74 ft).

No OneRain rain thresholds or dashboard colors on: La Honda.

<details><summary>Internal to-do for the project team (reviewers can skip)</summary>

- La Honda (rain): check they open the Rain Increment sensor

</details>

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
