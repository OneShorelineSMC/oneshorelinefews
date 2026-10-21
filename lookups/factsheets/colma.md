# Colma Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** are the heights and their meaning right? Who set them, and from what study, survey or past flood?
> - [ ] **OneRain text alerts switched off:** Flood Monitoring at Colma Creek at Orange Memorial Park (rule #15); Flood Warning at Colma Creek at Orange Memorial Park (rule #13); Flood Watch at Colma Creek at Orange Memorial Park (rule #14); Rainfall intensity (Colma) at San Bruno Mountain (rule #8); Rainfall warning at San Bruno Mountain (rule #6). Is that intended? These send no texts while off.

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
| Cities and communities | Daly City; Colma; South San Francisco *(draft)* |
| Drains to | San Francisco Bay at South San Francisco |
| Description | Urban creek from San Bruno Mountain and Daly City through Colma to South San Francisco; the gauge is at Orange Memorial Park and the flood levels are for the community downstream. |
| Flood levels set? | Yes |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the 2026 Update page | 15 min, 30 min, 1 hr |

## Creek level gauges

### Colma Creek at Orange Memorial Park

| | |
|---|---|
| Source and ID | OneRain 41101 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=12&site=32e8ebb1-4c9c-460a-a4cd-58903b96f347&device_id=5&device=dbbbcf6d-6a38-44a5-a90b-7077db13c5c2)) |
| Location | 37.65379, -122.42669 |
| Reports | Every 12 hours plus extra readings in some storms until May 2025; hourly plus extra storm readings since Oct 2025 |
| Record starts | Jun 2020 (public OneRain pages) |
| Affected by the tide? | Yes. Staff (Oct 16, 2026): tidally influenced at Orange Memorial Park. Checked against the Alameda tide (Oct 17, 2026): this gauge's reading does not follow the tide, in dry weather or in storms. Dry weather (Oct 2025 - Jun 2026, hourly): the reading stayed under 0.3 ft and did not rise with the tide, even at tides of 8.1-8.3 ft NAVD88 (about 2 ft above the average daily high tide). Storms (62 rises above 1 ft, Oct 2021 - Jun 2026): peaks came at high and low tide alike, and the creek drained just as fast at high tide (typically half way back down within an hour). Example: Jan 4, 2026, the creek fell from 2.63 ft to under half that within 10 minutes during an 8.2 ft high tide with 1.2 ft of storm surge. The tide may still back up the creek further downstream, but this gauge does not show it. Not yet checked against rain records; 2021-22 storms had too few readings to test |
| Rising-fast indicator | 0.5 ft within an hour (default) · **Default setting, not yet tested on this gauge** |
| Why this rising-fast setting | Tidal since Oct 16, 2026 (staff): the rain condition now applies. Record not usable yet: the gauge sent one reading every 12 hours until 2025 (hourly since), with outages Jun–Oct 2020, Nov 24 – Dec 15, 2021 and May 29 – Oct 16, 2025. 3 of 7 rises to Flood Monitoring warned, but 2 of the 7 are sensor faults (Jul 15 and Aug 18, 2022), and the rule misses the rise when Colma switches from hourly to faster readings. |
| History and known issues | Outages: Jun 23 - Oct 6, 2020; Nov 24 - Dec 15, 2021; May 29 - Oct 16, 2025. Sensor faults: Jul 15, 2022 (readings to about 16.7 ft); Aug 18, 2022 (one-reading spike to 4.56 ft). When it switches from hourly to faster readings in a storm, the rising-fast check can miss the rise (RISING_FAST_BASIS.md section 8). |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 3.40 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 5.00 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 6.75 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely).

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 6.3 years of readings, against the lowest flood level (Flood Monitoring, 3.4 ft): "warned" means the indicator came on before the creek reached it. Only 7 such rises in the record, so treat these results as rough.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 9.2 | 3 of 7 | 80 min |
| 0.5 (current setting) | 5.9 | 3 of 7 | 80 min |
| 0.75 | 3.3 | 2 of 7 | 3.2 h |
| 1.0 | 2.5 | 2 of 7 | 3.2 h |
| 1.5 | 1.1 | 1 of 7 | 80 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Orange Memorial Park | 41101 | 37.65379, -122.42669 | lower watershed | Shown on the 2026 Update page and counts toward the rain indicator |
| San Bruno Mountain | 41200 | 37.69222, -122.44833 | upper watershed | Counts toward the creek's rain indicator only (not shown on the page) |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 15 min | 30 min | 1 hr | 24 hr |
|---|---|---|---|---|---|
| Orange Memorial Park | Heavy (1-year) | 0.236 | 0.323 | 0.456 | 1.87 |
| Orange Memorial Park | Very heavy (2-year) | 0.283 | 0.387 | 0.546 | 2.39 |
| Orange Memorial Park | Intense (5-year) | 0.347 | 0.474 | 0.669 | 3.07 |
| San Bruno Mountain | Heavy (1-year) | 0.251 | 0.346 | 0.489 | 2.11 |
| San Bruno Mountain | Very heavy (2-year) | 0.302 | 0.417 | 0.589 | 2.68 |
| San Bruno Mountain | Intense (5-year) | 0.372 | 0.513 | 0.725 | 3.44 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

The 2026 Update shows this creek's status on its public pages. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor and OneRain's alarm rules, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages; rain and alarm rules from the admin pages). A OneRain threshold colors that gauge's readings; only an alarm rule that is **On** sends a text alert. OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? | OneRain text alert |
|---|---|---|---|---|---|
| Colma Creek at Orange Memorial Park | Flood Monitoring | 3.40 ft | 3.40 ft ("Potential flooding") | Same | Off (rule #15) |
| Colma Creek at Orange Memorial Park | Flood Watch | 5.00 ft | 5.00 ft ("Flooding likely") | Same | Off (rule #14) |
| Colma Creek at Orange Memorial Park | Flood Warning | 6.75 ft | 6.75 ft ("Flooding likely in downstream reaches") | Same | Off (rule #13) |
| Colma Creek at Orange Memorial Park | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only | – |

**Rain**

Each row is one length of time ("rain within"). **2026 Update** = the amounts at which its rain indicator turns Heavy, Very heavy and Intense (or a rain trigger shows). **OneRain** = the thresholds set on that gauge's rain sensors for the same length of time. Rows are listed only where OneRain or a 2026 Update trigger uses that length of time; the 2026 Update checks every length from 15 minutes to 48 hours.

| Gauge | Rain within | 2026 Update (inches) | OneRain thresholds and text alerts (inches) |
|---|---|---|---|
| Orange Memorial Park | 1 hr | Heavy from 0.456 in, Very heavy from 0.546 in, Intense from 0.669 in | Flood warning from 0.80 in *(time window from the threshold's name only; how OneRain applies it is unconfirmed)* |
| Orange Memorial Park | 6 hr | Heavy from 1.15 in, Very heavy from 1.38 in, Intense from 1.69 in | **Text alert** rule #22 (**On**): more than 2.00 in |
| San Bruno Mountain | 30 min | Heavy from 0.346 in, Very heavy from 0.417 in, Intense from 0.513 in | **Text alert** rule #6 (Off): more than 0.5 in |
| San Bruno Mountain | 6 hr | Heavy from 1.26 in, Very heavy from 1.52 in, Intense from 1.86 in | **Text alert** rule #23 (**On**): more than 2.00 in<br>**Text alert** rule #8 (Off): more than 2.00 in |

*Why the 2026 Update uses these amounts:* for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

No OneRain rain thresholds on: San Bruno Mountain.

**OneRain text alerts** (alarm rules: when its condition is met, a rule that is On sends a text to the contacts set up for it, such as Public Works and emergency responders; from OneRain's rule list, Oct 17, 2026)

| Rule | Gauge | Sends a text when | OneRain severity | On or off |
|---|---|---|---|---|
| #22 Rainfall intensity (Colma) | Colma Creek at Orange Memorial Park | more than 2.00 in of rain within 6 hr | Warning | **On** |
| #23 Rainfall intensity (Colma) | San Bruno Mountain | more than 2.00 in of rain within 6 hr | Warning | **On** |
| #6 Rainfall warning | San Bruno Mountain | more than 0.5 in of rain within 30 min | Warning | Off |
| #8 Rainfall intensity (Colma) | San Bruno Mountain | more than 2.00 in of rain within 6 hr | Warning | Off |
| #13 Flood Warning | Colma Creek at Orange Memorial Park | stage goes above its 'Flood Warning' threshold (6.75 ft) | Critical | Off |
| #14 Flood Watch | Colma Creek at Orange Memorial Park | stage goes above its 'Flood Watch' threshold (5.00 ft) | Warning | Off |
| #15 Flood Monitoring | Colma Creek at Orange Memorial Park | stage goes above its 'Flood Monitoring' threshold (3.40 ft) | Notice | Off |

**Tide:** the 2026 Update uses NOAA 9414750 Alameda for this creek's tide graph and high-tide lines (average daily high tide, MHHW, 6.37 ft NAVD88). OneRain's tide settings aren't included.

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
