# Belmont Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?
> - [ ] **Rain triggers:** are the amounts and what they show right?
> - [ ] **Flooding likely (rain + tide):** the tide part (6.32 ft NAVD88) is below the average daily high tide at Redwood City (MHHW 7.02 ft), so it is met on most days' higher high tide. Is that the intended tide level?
> - [ ] **Belmont 30-minute rain trigger:** The 2026 Update shows 'Flooding likely' when 30-minute rain reaches 0.20 in. OneRain's thresholds on this gauge call 0.20 in 'Potential for flooding' and 0.25 in 'Flooding likely'. Should the 2026 Update's trigger be 0.25 in?

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
| On the 2026 Update site | Public pages |
| Cities and communities | Belmont; San Carlos; unincorporated Harbor Industrial Area *(draft)* |
| Drains to | Belmont Slough, then San Francisco Bay |
| Description | Flashy urban creek; frequent street flooding downstream; flood levels are for the Harbor Industrial Area. |
| Flood levels set? | Yes; plus rain triggers |
| Tide station | NOAA 9414523 Redwood City (average daily high tide, MHHW, 7.02 ft NAVD88) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 4 hr, 24 hr |

## Creek level gauges

### Belmont Creek at Old County Rd

| | |
|---|---|
| Source and ID | OneRain 41104 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=2&site=25fd9d56-e3ea-4ff9-a067-b3e99cc5c1fe&device_id=1&device=5c101ccb-75e1-4c68-a983-4b8c78913c03)) |
| Location | 37.51719, -122.27125 |
| Reports | On change: every 12 hours in dry weather, every few minutes in storms |
| Record starts | Oct 2019 or earlier (pulled from Oct 1, 2019) |
| Affected by the tide? | No. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (7 yr)** |
| Why this rising-fast setting | 7 winters: warned before all 44 real rises to Flood Monitoring, about 40 min ahead; shown 24 times a year. At 0.75 ft the lead drops to about 15 min. |
| History and known issues | 27 single-reading sensor spikes of 1 ft or more from Oct 2019 to 2022 (e.g. 0.09 to 7.97 to 0.08 ft on Oct 17, 2019); none since 2023. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.25 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 3.25 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 4.00 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 7.0 years of readings, against the lowest flood level (Flood Monitoring, 2.25 ft): "warned" means the indicator came on before the creek reached it.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 27.6 | 44 of 45 | 59 min |
| 0.5 (current setting) | 23.6 | 44 of 45 | 42 min |
| 0.75 | 19.0 | 44 of 45 | 16 min |
| 1.0 | 14.9 | 42 of 45 | 10 min |
| 1.5 | 10.5 | 33 of 45 | 6 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Old County Road | 41104 | 37.51719, -122.27125 | lower watershed | Shown on the 2026 Update page and counts toward the rain indicator |

**Rain triggers** (flood levels for rain: each one sets the creek to the status shown)

| Gauge | Rain within | Rain (in) | And the tide is at least | Shows | Why this number | Status |
|---|---|---|---|---|---|---|
| Old County Road | 30 min | 0.20 | – | Flooding likely (rain) | Taken from OneRain's Belmont settings (Oct 2026); it matches OneRain's lower 30-minute threshold on this gauge (0.20 in, which OneRain calls 'Potential for flooding'). No study recorded | From OneRain, not yet signed off |
| Old County Road | 4 hr | 0.42 | 6.32 ft NAVD88 | Flooding likely (rain + tide) | Rain amount from an analysis of 2022-2025 events; tide level from OneRain alarm rule #34 (7.5 ft MLLW, converted to NAVD88) | From OneRain, not yet signed off |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 24 hr |
|---|---|---|---|---|
| Old County Road | Heavy (1-year) | 0.305 | 0.432 | 1.76 |
| Old County Road | Very heavy (2-year) | 0.366 | 0.517 | 2.29 |
| Old County Road | Intense (5-year) | 0.45 | 0.637 | 2.98 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

The 2026 Update shows this creek's status on its public pages. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages, rain from the admin sensor pages). A OneRain threshold colors that gauge's readings; it doesn't send a message by itself (OneRain sends text alerts only through separate alarm rules). OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |
|---|---|---|---|---|
| Belmont Creek at Old County Rd | Flood Monitoring | 2.25 ft | 2.25 ft ("Potential flooding") | Same |
| Belmont Creek at Old County Rd | Flood Watch | 3.25 ft | 3.25 ft ("Flooding probable with continued rain") | Same |
| Belmont Creek at Old County Rd | Flood Warning | 4.00 ft | 4.00 ft ("Active flooding likely to occur downstream") | Same |
| Belmont Creek at Old County Rd | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only |

**Rain**

Each row is one length of time ("rain within"). **2026 Update** = the amounts at which its rain indicator turns Heavy, Very heavy and Intense (or a rain trigger shows). **OneRain** = the thresholds set on that gauge's rain sensors for the same length of time. Rows are listed only where OneRain or a 2026 Update trigger uses that length of time; the 2026 Update checks every length from 15 minutes to 48 hours.

| Gauge | Rain within | 2026 Update (inches) | OneRain thresholds (inches) |
|---|---|---|---|
| Old County Road | 30 min | **Flooding likely (rain)** at 0.20 in; Heavy from 0.305 in, Very heavy from 0.366 in, Intense from 0.45 in | Flood watch from 0.20 in, Flood warning from 0.25 in *(time window from the threshold's name only; how OneRain applies it is unconfirmed)* |
| Old County Road | 4 hr | **Flooding likely (rain + tide)** at 0.42 in (and tide ≥ 6.32 ft NAVD88) | Rainfall warning from 0.42 in |

*Why the 2026 Update uses these amounts:* for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

**Tide:** the 2026 Update uses NOAA 9414523 Redwood City for this creek's tide graph and high-tide lines (average daily high tide, MHHW, 7.02 ft NAVD88). OneRain's tide settings aren't included.

Notes:

- Set on OneRain's rolling 4-hour total sensor. Same rain amount as the 2026 Update's rain + tide trigger (0.42 in / 4 hr); the tide part is OneRain alarm rule #34.
- The 2026 Update shows 'Flooding likely' at 0.20 in / 30 min; OneRain calls 0.20 'Potential for flooding' and 0.25 'Flooding likely'.

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
