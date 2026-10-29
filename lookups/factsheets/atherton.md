# Atherton Channel

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
| On the 2026 Update site | Public pages |
| Cities and communities | Woodside (upper watershed); Atherton; unincorporated North Fair Oaks; Redwood City *(draft)* |
| Drains to | Bayfront Canal, then San Francisco Bay |
| Description | Channelized creek; flood levels are for the area downstream of the Caltrain crossing. |
| Flood levels set? | Yes |
| Tide station | NOAA 9414523 Redwood City (average daily high tide, MHHW, 7.02 ft NAVD88) |
| Rain totals on the 2026 Update page | 15 min, 30 min, 1 hr |

## Creek level gauges

### Atherton Channel at Alameda de las Pulgas

| | |
|---|---|
| Source and ID | OneRain 41107 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=48&site=222db05c-ef0a-4720-b2c1-aaba882205f8&device_id=5&device=24188afc-3ba7-498b-b865-c186ddd1f7f5)) |
| Location | 37.43736, -122.21336 |
| Reports | Hourly, with extra readings in storms |
| Record starts | Jan 27, 2026 (public OneRain pages) |
| Affected by the tide? | No |
| Rising-fast indicator | 0.5 ft within an hour (default) · **Default setting, not yet tested on this gauge** |
| Why this rising-fast setting | Record starts Jan 2026; no Monitoring crossing yet |
| History and known issues | Short record: no Flood Monitoring crossing yet. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 3.18 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 4.60 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 5.65 | OneRain sensor thresholds (Oct 2026) |  |
| 4 | Roadway Flooded | 10.40 | OneRain sensor thresholds (Oct 2026) | Spill elevation, in the same datum as the gauge (OneShoreline, Oct 29, 2026): water spills onto the road |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely). Roadway Flooded = 10.40 ft at Alameda de las Pulgas, the spill elevation: water spills onto the road. Roadway Flooded = water detected on the road.

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 0.7 years of readings, against the lowest flood level (Flood Monitoring, 3.18 ft): "warned" means the indicator came on before the creek reached it. Only 0 such rises in the record, so treat these results as rough.

| Setting (ft within an hour) | Times shown (total) | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 9 | 0 of 0 | – |
| 0.5 (current setting) | 4 | 0 of 0 | – |
| 0.75 | 3 | 0 of 0 | – |
| 1.0 | 2 | 0 of 0 | – |
| 1.5 | 0 | 0 of 0 | – |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

### Atherton Channel upstream of CalTrain

| | |
|---|---|
| Source and ID | OneRain 41106 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=14&site=a63a9e54-703b-43b1-8286-6cabbaae7fa1&device_id=4&device=b1b9cc5f-9ad6-498b-96cb-fc299b4eab79)) |
| Location | 37.46192, -122.19387 |
| Reports | On change |
| Record starts | Oct 2020 (public OneRain pages) |
| Affected by the tide? | No. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (6 yr)** |
| Why this rising-fast setting | 24 of 25 rises to Flood Monitoring warned, about 2 h ahead; shown 28 times a year |
| History and known issues | Probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow. |
| Note shown on the 2026 Update page | The probe is 0.37 ft above the channel bottom; readings below about 0.4 ft mean very low or no flow. |

**Flood levels** (gauge height, ft)

| Level | Name | Height (ft) | Source | Notes |
|---|---|---|---|---|
| 1 | Flood Monitoring | 2.80 | OneRain sensor thresholds (Oct 2026) |  |
| 2 | Flood Watch | 4.10 | OneRain sensor thresholds (Oct 2026) |  |
| 3 | Flood Warning | 5.50 | OneRain sensor thresholds (Oct 2026) |  |

What they mean: Flood Monitoring = potential for 50% channel capacity exceedance downstream; Flood Watch = 75%; Flood Warning = 100% (flooding likely). Roadway Flooded = 10.40 ft at Alameda de las Pulgas, the spill elevation: water spills onto the road.

By this definition, Monitoring and Watch mean the water is still in the channel; only Flood Warning means flooding is likely.

Why these heights: they are OneRain's thresholds for this gauge, copied in October 2026. Who set the heights, and from what study, survey or past flood, isn't recorded. Status: **From OneRain, basis unknown; not yet signed off.**

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 6.0 years of readings, against the lowest flood level (Flood Monitoring, 2.8 ft): "warned" means the indicator came on before the creek reached it.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 33.2 | 24 of 25 | 2.9 h |
| 0.5 (current setting) | 28.1 | 24 of 25 | 2.1 h |
| 0.75 | 20.3 | 23 of 25 | 86 min |
| 1.0 | 16.4 | 22 of 25 | 58 min |
| 1.5 | 8.6 | 15 of 25 | 38 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Caltrain | 41106 | 37.46192, -122.19387 | upstream of Caltrain | Shown on the 2026 Update page and counts toward the rain indicator |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 15 min | 30 min | 1 hr | 24 hr |
|---|---|---|---|---|---|
| Caltrain | Heavy (1-year) | 0.197 | 0.272 | 0.383 | 1.6 |
| Caltrain | Very heavy (2-year) | 0.248 | 0.343 | 0.483 | 2.04 |
| Caltrain | Intense (5-year) | 0.318 | 0.439 | 0.618 | 2.63 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

The 2026 Update shows this creek's status on its public pages. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor and OneRain's alarm rules, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages; rain and alarm rules from the admin pages). A OneRain threshold colors that gauge's readings; only an alarm rule that is **On** sends a text alert. OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? | OneRain text alert |
|---|---|---|---|---|---|
| Atherton Channel at Alameda de las Pulgas | Flood Monitoring | 3.18 ft | 3.18 ft ("Potential flooding") | Same | none |
| Atherton Channel at Alameda de las Pulgas | Flood Watch | 4.60 ft | 4.60 ft ("Flooding probable with continued rain") | Same | none |
| Atherton Channel at Alameda de las Pulgas | Flood Warning | 5.65 ft | 5.65 ft ("Active flooding likely to occur downstream") | Same | none |
| Atherton Channel at Alameda de las Pulgas | Roadway Flooded | 10.40 ft | 10.40 ft ("Water detected on road") | Same | none |
| Atherton Channel at Alameda de las Pulgas | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only | – |
| Atherton Channel upstream of CalTrain | Flood Monitoring | 2.80 ft | 2.80 ft ("Potential flooding") | Same | **On** (rule #11) |
| Atherton Channel upstream of CalTrain | Flood Watch | 4.10 ft | 4.10 ft ("Flooding probable with continued rain") | Same | **On** (rule #9) |
| Atherton Channel upstream of CalTrain | Flood Warning | 5.50 ft | 5.50 ft ("Active flooding likely to occur downstream") | Same | **On** (rule #10) |
| Atherton Channel upstream of CalTrain | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only | – |

**Rain**

Each row is one length of time ("rain within"). **2026 Update** = the amounts at which its rain indicator turns Heavy, Very heavy and Intense (or a rain trigger shows). **OneRain** = the thresholds set on that gauge's rain sensors for the same length of time. Rows are listed only where OneRain or a 2026 Update trigger uses that length of time; the 2026 Update checks every length from 15 minutes to 48 hours.

| Gauge | Rain within | 2026 Update (inches) | OneRain thresholds and text alerts (inches) |
|---|---|---|---|
| Caltrain | 1 hr | Heavy from 0.383 in, Very heavy from 0.483 in, Intense from 0.618 in | Flood watch from 0.40 in, Flood warning from 0.45 in *(time window from the threshold's name only; how OneRain applies it is unconfirmed)*<br>**Text alert** rule #25 (**On**): more than 0.45 in |

*Why the 2026 Update uses these amounts:* for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

**OneRain text alerts** (alarm rules: when its condition is met, a rule that is On sends a text to the contacts set up for it, such as Public Works and emergency responders; from OneRain's rule list, Oct 17, 2026)

| Rule | Gauge | Sends a text when | OneRain severity | On or off |
|---|---|---|---|---|
| #9 Flood Watch | Atherton Channel upstream of CalTrain | stage goes above its 'Flood Watch' threshold (4.10 ft) | Warning | **On** |
| #10 Flood Warning | Atherton Channel upstream of CalTrain | stage goes above its 'Flood Warning' threshold (5.50 ft) | Critical | **On** |
| #11 Flood Monitoring | Atherton Channel upstream of CalTrain | stage goes above its 'Flood Monitoring' threshold (2.80 ft) | Notice | **On** |
| #25 Rainfall intensity (Atherton) | Atherton Channel upstream of CalTrain | more than 0.45 in of rain within 1 hr | Warning | **On** |

**Tide:** the 2026 Update uses NOAA 9414523 Redwood City for this creek's tide graph and high-tide lines (average daily high tide, MHHW, 7.02 ft NAVD88). OneRain's tide settings aren't included.

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
