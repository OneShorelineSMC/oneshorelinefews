# Green Hills Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** the 2026 Update has none. Do you know a creek height at the gauge where the creek leaves its banks or floods a road, or a past flood we could match to a gauge reading?

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
| Cities and communities | Millbrae *(draft)* |
| Drains to | Highline Canal, then San Francisco Bay |
| Description | Small creek through Green Hills Country Club in Millbrae. |
| Flood levels set? | None |
| Tide station | NOAA 9414750 Alameda (average daily high tide, MHHW, 6.37 ft NAVD88) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### Green Hills Creek at Green Hills Country Club

| | |
|---|---|
| Source and ID | OneRain 41201 ([gauge page](https://oneshorelineearlywarning.onerain.com/sensor/?site_id=47&site=1e070958-e7b5-4329-b29d-eddf7da7df2d&device_id=1&device=aaf1108b-3657-42f4-9459-515d75c3eb7c)) |
| Location | 37.60130, -122.40930 |
| Reports | On change (about hourly in dry weather) |
| Record starts | Dec 24, 2024 (public OneRain pages) |
| Affected by the tide? | Not yet confirmed. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide; tidal influence still to confirm |
| Rising-fast indicator | 0.5 ft within an hour (default) · **Default setting, not yet tested on this gauge** |
| Why this rising-fast setting | Record starts Dec 2024. One big storm so far (Nov 17, 2025: 0.2 → 5.7 ft in about an hour), warned 64 min ahead at 0.5 ft. Too little to calibrate. |
| History and known issues | Flash flood Nov 17, 2025: 0.20 to 5.66 ft in 70 minutes. |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast).

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 1.8 years of readings, against 4.5 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding. Only 1 such rises in the record, so treat these results as rough.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 42.5 | 1 of 1 | 69 min |
| 0.5 (current setting) | 29.3 | 1 of 1 | 64 min |
| 0.75 | 21.5 | 1 of 1 | 50 min |
| 1.0 | 16.6 | 1 of 1 | 31 min |
| 1.5 | 9.4 | 1 of 1 | 19 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Pilarcitos Dam | PLD | 37.54800, -122.42200 | nearby | Counts toward the creek's rain indicator only (not shown on the page) |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

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

On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor and OneRain's alarm rules, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages; rain and alarm rules from the admin pages). A OneRain threshold colors that gauge's readings; only an alarm rule that is **On** sends a text alert. OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? | OneRain text alert |
|---|---|---|---|---|---|
| Green Hills Creek at Green Hills Country Club | Flood levels | none set | none set | – | – |
| Green Hills Creek at Green Hills Country Club | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only | – |

No OneRain rain thresholds on: Pilarcitos Dam.

**OneRain text alerts:** none set up for this creek's gauges (OneRain's rule list, Oct 17, 2026).

**Tide:** the 2026 Update uses NOAA 9414750 Alameda for this creek's tide graph and high-tide lines (average daily high tide, MHHW, 6.37 ft NAVD88). OneRain's tide settings aren't included.

<details><summary>Internal to-do for the project team (reviewers can skip)</summary>

- Green Hills Country Club (stage): check they open the Stage sensor; set reports; Confirm whether this gauge reads the tide
- Pilarcitos Dam (rain): check they open the Rain Increment sensor

</details>

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
