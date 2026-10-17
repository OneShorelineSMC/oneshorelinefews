# San Bruno Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** what do these levels mean for people downstream? The 2026 Update has no recorded meaning; OneRain describes them as Flood Monitoring = "Potential flooding"; Flood Watch = "Flooding likely"; Flood Warning = "Projected flooding in downstream reaches". Who set them, and from what?

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
| Cities and communities | San Bruno; South San Francisco *(draft)* |
| Drains to | San Francisco Bay near SFO |
| Description | Short urban creek; the gauge at First Avenue is tidal (rises and falls with the Bay tide). |
| Flood levels set? | Yes, but what they mean isn't recorded |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the 2026 Update page | 15 min, 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Bruno Creek at First Avenue

| | |
|---|---|
| Source and ID | OneRain 41102 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=11&site=fe06588c-e5e6-4016-8a8f-2ba1f040636e&device_id=3&device=e481d107-65bb-4107-89ab-48484eb0e188)) |
| Location | 37.62273, -122.40671 |
| Reports | On change (typically every 1-5 hours in dry weather, minutes in storms) |
| Record starts | Sep 2020 (public OneRain pages) |
| Affected by the tide? | Yes. Rises and falls with the Bay tide |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (6 yr)** |
| Why this rising-fast setting | 25 of 28 rises to Flood Monitoring warned, about 1¾ h ahead (0.25 ft: 27 of 28, but shown 57 times a year). Tidal gauge: the live site also requires rain, which this test doesn't apply, so it will show less often on the live site. One of the 28 is probably a sensor fault (Jun 3, 2026, the gauge's last day). The gauge has been offline since June 3, 2026. |
| History and known issues | Offline since Jun 3, 2026; the last reading (Jun 3, 2026) is probably a sensor fault. Gauge zero in NAVD88 unknown. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.40 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 3.60 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 4.80 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: **not recorded**.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 5.8 years of readings, against the lowest flood level (Flood Monitoring, 2.4 ft): "warned" means the indicator came on before the creek reached it.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 57.2 | 27 of 28 | 3.4 h |
| 0.5 (current setting) | 31.3 | 25 of 28 | 1.8 h |
| 0.75 | 17.9 | 15 of 28 | 42 min |
| 1.0 | 8.2 | 7 of 28 | 22 min |
| 1.5 | 2.8 | 2 of 28 | 14 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| San Bruno Mountain | 41200 | 37.69222, -122.44833 | upper watershed | Shown on the 2026 Update page and counts toward the rain indicator |
| First Avenue | 41102 | 37.62273, -122.40671 | lower watershed | Shown on the 2026 Update page and counts toward the rain indicator |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: they are the 1-, 2- and 5-year storm at each gauge from NOAA Atlas 14, a standard way to say how rare rain is at that exact spot. Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

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

## Thresholds: the 2026 Update compared with OneRain today

The 2026 Update shows this creek's status on its public pages. The **2026 Update** columns are what the new site uses. The **OneRain** columns are what is set in OneRain today (read Oct 16–17, 2026): *thresholds* set on each sensor, and *dashboard colors*. Neither sends a message by itself; OneRain sends text alerts only through separate alarm rules. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |
|---|---|---|---|---|
| San Bruno Creek at First Avenue | Flood Monitoring | 2.40 ft | 2.40 ft ("Potential flooding") | Same |
| San Bruno Creek at First Avenue | Flood Watch | 3.60 ft | 3.60 ft ("Flooding likely") | Same |
| San Bruno Creek at First Avenue | Flood Warning | 4.80 ft | 4.80 ft ("Projected flooding in downstream reaches") | Same |
| San Bruno Creek at First Avenue | Rising fast | 0.5 ft within an hour | none | 2026 Update only |

No OneRain rain thresholds or dashboard colors on: San Bruno Creek at First Avenue; San Bruno Mountain.

**Tide**

| | 2026 Update uses | OneRain dashboard color |
|---|---|---|
| Tide | NOAA 9414750 Alameda: tide graph and high-tide lines (MHHW 6.37 ft NAVD88) | none recorded |

Notes:

- OneRain shows this gauge's creek-level sensor as Out of Service.

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
