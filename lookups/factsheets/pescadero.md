# Pescadero Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?

> **Words used on this page** (the same words for both systems)
>
> - **Threshold:** any set value that changes a color or a status, in either system.
> - **Flood level** (2026 Update): a threshold on creek height (or a rain amount) tied to an effect downstream, such as how full the channel is or water on a road. Only flood levels say anything about flooding.
> - **Indicator** (2026 Update): something the page shows in color or words, not a message. Two kinds: the **rain indicator** (Heavy, Very heavy, Intense: how rare the rain is) and **rising fast** (the creek rose at least a set amount within an hour). Not tied to flooding.
> - **Status** (2026 Update): the one overall message shown for a creek (currently worded Flooding likely, Be ready, Stay alert or No alerts). It comes from the flood levels and indicators.
> - **OneRain threshold:** a named level set on a OneRain sensor (for example Flood Watch, 3.25 ft). It colors that gauge's readings and graph; it doesn't send a message by itself.
> - **OneRain dashboard color:** the green, orange or red a OneRain dashboard gives a reading. Set separately from the thresholds.
> - **Text alert:** a text message sent to people. Only OneRain sends these, to Public Works and emergency responders, through its *alarm* rules. The 2026 Update sends no text alerts; it only shows colors and words on the page.
>
> **Units.** Creek heights are the gauge's own reading in feet (above the gauge's zero), not an elevation. Tide heights are in feet NAVD88, a survey datum; MHHW = the average daily high tide, MLLW = the average daily low tide. A 1-, 2- or 5-year storm is rain that heavy at that gauge, with about a 63%, 39% or 18% chance in any year (NOAA Atlas 14). Water year: October 1 to September 30, named for the year it ends.
>
> **Names.** **OneRain** is the County's existing gauge system and dashboards (what many people call "FEWS"). **FEWS 2026 Update** ("2026 Update") is the new public creek and tide status site built on OneRain's data. These fact sheets describe the 2026 Update and compare it with OneRain.

## At a glance

| | |
|---|---|
| On the 2026 Update site | Staff preview only (not yet on the public pages) |
| Cities and communities | Unincorporated Pescadero; Loma Mar; La Honda area *(draft)* |
| Drains to | Pescadero Marsh, then the Pacific Ocean |
| Description | Rural coastal creek; the town of Pescadero floods from Pescadero and Butano Creeks. |
| Flood levels set? | Yes |
| Tide station | None set for this creek in the 2026 Update (coastal creek) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### Pescadero Creek at Stage Road

| | |
|---|---|
| Source and ID | OneRain 41151 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=28&site=b7ae4c33-4536-443f-bcc5-72ded98d2412&device_id=1&device=cbd2cde7-ac86-4ad2-8a9d-a2f6d7575cd8)) |
| Location | 37.25468, -122.38330 |
| Reports | On change (every 2-12 hours in dry weather) |
| Record starts | Oct 13, 2023 (public OneRain pages) |
| Affected by the tide? | No |
| Rising-fast indicator | 1.0 ft within an hour · **Provisional (3 yr)** |
| Why this rising-fast setting | Same creek as the USGS gauge. 3 of 3 warned at any setting, about 5 h ahead; 1.0 ft is shown 3 times a year. |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast).

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 3.0 years of readings, against 11.52 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding. Only 3 such rises in the record, so treat these results as rough.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 10.0 | 3 of 3 | 5.1 h |
| 0.5 | 5.3 | 3 of 3 | 5.1 h |
| 0.75 | 4.0 | 3 of 3 | 5.1 h |
| 1.0 (current setting) | 3.0 | 3 of 3 | 4.9 h |
| 1.5 | 1.0 | 3 of 3 | 4.1 h |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Pescadero Creek near Pescadero

| | |
|---|---|
| Source and ID | USGS 11162500 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162500/)) |
| Location | 37.26096, -122.32890 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007) |
| Affected by the tide? | No |
| Rising-fast indicator | 1.0 ft within an hour · **Tested on past data (19 yr)** |
| Why this rising-fast setting | 18 of 18 warned, about 2½ h ahead, shown half as often as at 0.5 ft (2.7/yr vs 5.3/yr) |
| History and known issues | Typical water level has crept up over the record (channel change). |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 2 | Flood Watch | 11.20 | OneRain sensor thresholds (Oct 2026) | OneRain: Flooding likely |
| 3 | Flood Warning | 13.25 | OneRain sensor thresholds (Oct 2026) | OneRain: Projected flooding in downstream reaches |

What they mean: Flood levels near Pescadero (USGS gauge) are OneRain's (Oct 2026): Flood Watch = flooding likely; Flood Warning = projected flooding in downstream reaches. OneRain sets no Flood Monitoring level here, and none at Stage Road. Not yet reviewed by staff.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 10.41 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding. (The flood levels above were added later, in October 2026; the test hasn't been rerun against Flood Watch, 11.20 ft.)

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 7.8 | 18 of 18 | 4.8 h |
| 0.5 | 5.3 | 18 of 18 | 3.2 h |
| 0.75 | 4.0 | 18 of 18 | 2.8 h |
| 1.0 (current setting) | 2.7 | 18 of 18 | 2.5 h |
| 1.5 | 1.7 | 16 of 18 | 82 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| La Honda | LAH | 37.30530, -122.25390 | nearby | Counts toward the creek's rain indicator only (not shown on the page) |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 6 hr | 24 hr |
|---|---|---|---|---|---|---|
| La Honda | Heavy (1-year) | 0.476 | 0.676 | 1.26 | 1.81 | 3.06 |
| La Honda | Very heavy (2-year) | 0.597 | 0.846 | 1.57 | 2.26 | 3.89 |
| La Honda | Intense (5-year) | 0.755 | 1.07 | 1.98 | 2.85 | 4.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor and OneRain's alarm rules, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages; rain and alarm rules from the admin pages). A OneRain threshold colors that gauge's readings; only an alarm rule that is **On** sends a text alert. OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? | OneRain text alert |
|---|---|---|---|---|---|
| Pescadero Creek at Stage Road | Flood levels | none set | none set | – | – |
| Pescadero Creek at Stage Road | Rising fast | 1.0 ft within an hour | nothing comparable | 2026 Update only | – |
| Pescadero Creek near Pescadero | Flood Watch | 11.20 ft | 11.20 ft ("Flooding likely") | Same | none |
| Pescadero Creek near Pescadero | Flood Warning | 13.25 ft | 13.25 ft ("Projected flooding in downstream reaches") | Same | none |
| Pescadero Creek near Pescadero | Rising fast | 1.0 ft within an hour | nothing comparable | 2026 Update only | – |
| Butano Creek near Cloverdale Road (not a 2026 Update gauge) | Flood Watch | – | 10.10 ft ("Flooding likely") | OneRain only | none |
| Butano Creek near Cloverdale Road (not a 2026 Update gauge) | Flood Warning | – | 11.80 ft ("Flooding likely in downstream reaches") | OneRain only | none |

How often the creek reached OneRain's levels (USGS record, water years 2008–2026): Flood Watch 11.20 ft: 7 of 19 years (highest 16.93 ft); Flood Warning 13.25 ft: 4 of 19 years (highest 16.93 ft).

**Rain**

Each row is one length of time ("rain within"). **2026 Update** = the amounts at which its rain indicator turns Heavy, Very heavy and Intense (or a rain trigger shows). **OneRain** = the thresholds set on that gauge's rain sensors for the same length of time. Rows are listed only where OneRain or a 2026 Update trigger uses that length of time; the 2026 Update checks every length from 15 minutes to 48 hours.

| Gauge | Rain within | 2026 Update (inches) | OneRain thresholds and text alerts (inches) |
|---|---|---|---|
| Butano Creek near Cloverdale Road | 6 hr | – (the 2026 Update doesn't use this gauge) | Rainfall warning from 1.04 in |

*Why the 2026 Update uses these amounts:* for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

No OneRain rain thresholds on: La Honda.

**OneRain text alerts:** none set up for this creek's gauges (OneRain's rule list, Oct 17, 2026).

Notes:

- Butano Creek (not a 2026 Update gauge); sensor is labeled backup.
- Set on OneRain's rolling 6-hour total sensor.

<details><summary>Internal to-do for the project team (reviewers can skip)</summary>

- Stage Road (stage): check they open the Stage sensor; set reports
- La Honda (rain): check they open the Rain Increment sensor

</details>

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
