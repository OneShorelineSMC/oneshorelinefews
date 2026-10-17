# San Mateo Creek

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
| Cities and communities | Hillsborough; San Mateo *(draft)* |
| Drains to | San Francisco Bay |
| Description | Flow below Crystal Springs Reservoir is controlled by SFPUC releases and spills. |
| Flood levels set? | Yes |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Mateo Creek Below Crystal Springs Reservoir

| | |
|---|---|
| Source and ID | USGS 11162753 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162753/)) |
| Location | 37.52944, -122.35833 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Sep 2008 |
| Affected by the tide? | Not yet confirmed. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (18 yr): revisit** |
| Why this rising-fast setting | Rises follow reservoir releases, so it is mostly "happening now": 11 of 60 big storms warned, about 45 min ahead. Kept because it is San Mateo Creek's only creek-level signal until flood levels or a reservoir indicator exist. |
| History and known issues | Rises follow Crystal Springs Reservoir releases and spills (reservoir level: USGS 11162750; spill about 294.6 ft). USGS data approved through spring 2026. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 2 | Flood Watch | 6.70 | OneRain sensor thresholds (Oct 2026), converted from flow | OneRain: Flooding probable with continued rain. OneRain sets it as 200 cfs flow; 6.70 ft is the matching USGS gauge height (2023-2026 readings) |
| 3 | Flood Warning | 7.00 | OneRain sensor thresholds (Oct 2026), converted from flow | OneRain: Active flooding likely to occur downstream. OneRain sets it as 250 cfs flow; 7.00 ft is the matching USGS gauge height (2023-2026 readings) |

What they mean: Flood levels below Crystal Springs are OneRain's (Oct 2026), which OneRain sets on flow: Flood Watch = 200 cfs (about 6.70 ft), flooding probable with continued rain; Flood Warning = 250 cfs (about 7.00 ft), active flooding likely downstream. Not yet reviewed by staff. Tide station to confirm.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 18.1 years of readings, against the lowest flood level (Flood Watch, 5.88 ft): "warned" means the indicator came on before the creek reached it.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 17.6 | 21 of 60 | 1.5 h |
| 0.5 (current setting) | 7.2 | 11 of 60 | 45 min |
| 0.75 | 3.1 | 3 of 60 | 75 min |
| 1.0 | 1.3 | 0 of 60 | – |
| 1.5 | 0.5 | 0 of 60 | – |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Crystal Springs Cottage | CSC | 37.49600, -122.32900 | nearby | Counts toward the creek's rain indicator only (not shown on the page) |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Crystal Springs Cottage | Heavy (1-year) | 0.357 | 0.505 | 0.931 | 2.12 |
| Crystal Springs Cottage | Very heavy (2-year) | 0.431 | 0.61 | 1.11 | 2.73 |
| Crystal Springs Cottage | Intense (5-year) | 0.532 | 0.753 | 1.36 | 3.54 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages, rain from the admin sensor pages). A OneRain threshold colors that gauge's readings; it doesn't send a message by itself (OneRain sends text alerts only through separate alarm rules). OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |
|---|---|---|---|---|
| San Mateo Creek Below Crystal Springs Reservoir | Flood Watch | 6.70 ft | – | 2026 Update only |
| San Mateo Creek Below Crystal Springs Reservoir | Flood Warning | 7.00 ft | – | 2026 Update only |
| San Mateo Creek Below Crystal Springs Reservoir | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only |

No OneRain rain thresholds on: Crystal Springs Cottage.

**Tide:** the 2026 Update uses NOAA 9414750 Alameda for this creek's tide graph and high-tide lines (average daily high tide, MHHW, 6.37 ft NAVD88). OneRain's tide settings aren't included.

<details><summary>Internal to-do for the project team (reviewers can skip)</summary>

- Crystal Springs Cottage (rain): check they open the Rain Increment sensor
- Below Crystal Springs Reservoir (stage): Confirm whether this gauge reads the tide; Flow below Crystal Springs dam; reservoir level is USGS 11162750 (spill at 294.6 ft)

</details>

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
