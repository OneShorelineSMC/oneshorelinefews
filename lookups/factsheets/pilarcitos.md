# Pilarcitos Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** the 2026 Update has none, but OneRain has its own at Pilarcitos Creek at Half Moon Bay (see Thresholds on this page). Do you know who set them and from what? Should the 2026 Update use them?

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
| Cities and communities | Half Moon Bay; unincorporated Pilarcitos Canyon (SFPUC lands above Stone Dam) *(draft)* |
| Drains to | Pacific Ocean at Half Moon Bay |
| Description | Coastal creek regulated by Pilarcitos Lake and Stone Dam in its upper reaches. |
| Flood levels set? | None in the 2026 Update (OneRain has some; see Thresholds below) |
| Tide station | None set for this creek in the 2026 Update (coastal creek) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### Pilarcitos Creek below Pilarcitos Lake Spillway

| | |
|---|---|
| Source and ID | USGS 111626182 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-111626182/)) |
| Location | 37.54769, -122.42089 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Mar 1, 2022 |
| Affected by the tide? | No |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (4.6 yr)** |
| Why this rising-fast setting | Rises come when the lake spills. All 8 times it came on, the creek went on to its typical yearly high, but never beforehand: a "happening now" signal, not an early warning. |
| History and known issues | Rises come when Pilarcitos Lake spills. |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast).

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 4.6 years of readings, against 3.54 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 5.0 | 3 of 16 | 15 min |
| 0.5 (current setting) | 1.7 | 0 of 16 | – |
| 0.75 | 1.3 | 0 of 16 | – |
| 1.0 | 1.1 | 0 of 16 | – |
| 1.5 | 0.0 | 0 of 16 | – |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Pilarcitos Creek above Stone Dam

| | |
|---|---|
| Source and ID | USGS 11162619 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162619/)) |
| Location | 37.52814, -122.40010 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Feb 28, 2022 |
| Affected by the tide? | No |
| Rising-fast indicator | 0.25 ft within an hour · **Provisional (4.6 yr)** |
| Why this rising-fast setting | Small creek, weak at any setting: 0.25 ft warned of 6 of 13 (about 1¼ h ahead); 0.5 ft of 4 of 13 |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast).

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 4.6 years of readings, against 3.4 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 (current setting) | 8.2 | 6 of 13 | 75 min |
| 0.5 | 4.3 | 4 of 13 | 82 min |
| 0.75 | 1.1 | 2 of 13 | 38 min |
| 1.0 | 0.2 | 0 of 13 | – |
| 1.5 | 0.0 | 0 of 13 | – |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Pilarcitos Creek below Stone Dam

| | |
|---|---|
| Source and ID | USGS 11162620 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162620/)) |
| Location | 37.52466, -122.39942 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007) |
| Affected by the tide? | No |
| Rising-fast indicator | Off at this gauge · **Tested on past data (19 yr): staff choice** |
| Why this rising-fast setting | The creek barely moves below the dam: its fastest wet-season (Nov–Apr) rise in 19 years was 0.67 ft/hr. At 0.25 ft it would warn of 14 of 39 big storms, about 1¾ h ahead, with shown 3 times a year. Off because Pilarcitos is covered by the Half Moon Bay gauge. |
| History and known issues | Below Stone Dam the level barely moves: fastest wet-season rise in 19 years 0.67 ft/hr. |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast).

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 6.67 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 3.0 | 14 of 39 | 1.7 h |
| 0.5 | 0.2 | 0 of 39 | – |
| 0.75 | 0.0 | 0 of 39 | – |
| 1.0 | 0.0 | 0 of 39 | – |
| 1.5 | 0.0 | 0 of 39 | – |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Pilarcitos Creek at Half Moon Bay

| | |
|---|---|
| Source and ID | USGS 11162630 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11162630/)) |
| Location | 37.46667, -122.43306 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007) |
| Affected by the tide? | No |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (19 yr)** |
| Why this rising-fast setting | 21 of 21 warned, about 3½ h ahead; shown 10 times a year |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast). OneRain has its own levels for this gauge: see Thresholds below.

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 9.17 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 21.6 | 21 of 21 | 4.8 h |
| 0.5 (current setting) | 10.4 | 21 of 21 | 3.5 h |
| 0.75 | 6.0 | 18 of 21 | 2.5 h |
| 1.0 | 4.0 | 18 of 21 | 1.8 h |
| 1.5 | 1.6 | 11 of 21 | 1.5 h |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Pilarcitos Dam | PLD | 37.54800, -122.42200 | upper watershed | Shown on the 2026 Update page and counts toward the rain indicator |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: they are the 1-, 2- and 5-year storm at each gauge from NOAA Atlas 14, a standard way to say how rare rain is at that exact spot. Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Pilarcitos Dam | Heavy (1-year) | 0.444 | 0.629 | 1.18 | 2.89 |
| Pilarcitos Dam | Very heavy (2-year) | 0.539 | 0.763 | 1.41 | 3.66 |
| Pilarcitos Dam | Intense (5-year) | 0.665 | 0.942 | 1.73 | 4.68 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview. The **2026 Update** columns are what the new site uses. The **OneRain** columns are what is set in OneRain today (read Oct 16–17, 2026): *thresholds* set on each sensor, and *dashboard colors*. Neither sends a message by itself; OneRain sends text alerts only through separate alarm rules. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |
|---|---|---|---|---|
| Pilarcitos Creek below Pilarcitos Lake Spillway | – | none | none | – |
| Pilarcitos Creek below Pilarcitos Lake Spillway | Rising fast | 0.5 ft within an hour | none | 2026 Update only |
| Pilarcitos Creek above Stone Dam | – | none | none | – |
| Pilarcitos Creek above Stone Dam | Rising fast | 0.25 ft within an hour | none | 2026 Update only |
| Pilarcitos Creek below Stone Dam | – | none | none | – |
| Pilarcitos Creek below Stone Dam | Rising fast | off | none | 2026 Update only |
| Pilarcitos Creek at Half Moon Bay | Flood Monitoring | – | 7.50 ft ("Potential flooding") | OneRain only (the 2026 Update doesn't use it) |
| Pilarcitos Creek at Half Moon Bay | Flood Watch | – | 9.10 ft ("Flooding probable with continued rain") | OneRain only (the 2026 Update doesn't use it) |
| Pilarcitos Creek at Half Moon Bay | Flood Warning | – | 17.00 ft ("Flooding likely in downstream reaches") | OneRain only (the 2026 Update doesn't use it) |
| Pilarcitos Creek at Half Moon Bay | Major Flood Stage | – | 24.00 ft ("Damaging flooding") | OneRain only (the 2026 Update doesn't use it) |
| Pilarcitos Creek at Half Moon Bay | Rising fast | 0.5 ft within an hour | none | 2026 Update only |

How often the creek reached OneRain's levels (USGS record, water years 2008–2026): Flood Monitoring 7.50 ft: 16 of 19 years (highest 14.64 ft); Flood Watch 9.10 ft: 10 of 19 years (highest 14.64 ft); Flood Warning 17.00 ft: 0 of 19 years (highest 14.64 ft); Major Flood Stage 24.00 ft: 0 of 19 years (highest 14.64 ft).

No OneRain rain thresholds or dashboard colors on: Pilarcitos Dam.

<details><summary>Internal to-do for the project team (reviewers can skip)</summary>

- Below Pilarcitos Lake Spillway (stage): USGS 111626182 and OneRain PLD (Pilarcitos Dam) are at the same spot
- Pilarcitos Dam (rain): check they open the Rain Increment sensor

</details>

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
