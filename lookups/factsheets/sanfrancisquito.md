# San Francisquito Creek

*FEWS 2026 Update: draft fact sheet for staff review (October 2026). Please answer the questions in the box below by replying to the review request. Everything else on the page is background.*

> **What we need you to check**
>
> - [ ] **Cities and outlet** (At a glance): are the cities and communities, and where the creek drains, right?
> - [ ] **Gauges:** are the locations, record dates, reporting pattern and known issues right? Anything missing?
> - [ ] **Flood levels:** the 2026 Update has none, but OneRain has its own at San Francisquito Creek at Stanford (see Thresholds on this page). Do you know who set them and from what? Should the 2026 Update use them?

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
| Cities and communities | Woodside; Portola Valley; Menlo Park; East Palo Alto; Palo Alto; Stanford (unincorporated Santa Clara County) *(draft)* |
| Drains to | San Francisco Bay |
| Description | Large creek on the San Mateo / Santa Clara county line; the USGS gauge is at Stanford. |
| Flood levels set? | None in the 2026 Update (OneRain has some; see Thresholds below) |
| Tide station | NOAA 9414523 Redwood City (average daily high tide, MHHW, 7.02 ft NAVD88) |
| Rain totals on the 2026 Update page | 30 min, 1 hr, 3 hr, 24 hr |

## Creek level gauges

### San Francisquito Creek at Stanford

| | |
|---|---|
| Source and ID | USGS 11164500 ([gauge page](https://waterdata.usgs.gov/monitoring-location/USGS-11164500/)) |
| Location | 37.42327, -122.18941 |
| Reports | Every 15 minutes (USGS) |
| Record starts | Oct 2007 (pulled from Oct 1, 2007; USGS record is longer) |
| Affected by the tide? | Not yet confirmed. Dry-weather check (Oct 12-14, 2026): moved 0.04 ft or less with the tide |
| Rising-fast indicator | 0.5 ft within an hour · **Tested on past data (19 yr)** |
| Why this rising-fast setting | 20 of 20 big storms warned, about 3 h ahead; shown 9.5 times a year. At 0.75 ft: 17 of 20. |
| History and known issues | USGS data approved through spring 2026, provisional since Apr 2026. |

**Flood levels:** none in the 2026 Update, so this creek's status comes from indicators only (rain and rising fast). OneRain has its own levels for this gauge: see Thresholds below.

<details><summary>Background: how the rising-fast indicator performed on past data (no action needed)</summary>

Tested on 19.0 years of readings, against 6.0 ft, the creek's typical yearly high (about a 2-year event). That is **not** a flood level: "warned" means the indicator came on before a typical yearly high, not before flooding.

| Setting (ft within an hour) | Times shown per year | Warned before reaching it | Typical warning time |
|---|---|---|---|
| 0.25 | 19.9 | 20 of 20 | 4.6 h |
| 0.5 (current setting) | 9.5 | 20 of 20 | 3.0 h |
| 0.75 | 4.9 | 17 of 20 | 2.0 h |
| 1.0 | 3.0 | 12 of 20 | 60 min |
| 1.5 | 0.9 | 5 of 20 | 30 min |

How settings were chosen: the highest setting that still warned before all, or all but one, of the big rises, ideally at least 2 hours ahead; on flashy creeks such as Belmont, kept low to protect warning time. Method and limits: [RISING_FAST_BASIS.md](../RISING_FAST_BASIS.md).

</details>

## Rain gauges

| Gauge | OneRain ID | Location | Where | Use in the 2026 Update |
|---|---|---|---|---|
| Wunderlich County Park | A08363E2 | 37.40243, -122.27486 | upper watershed | Shown on the 2026 Update page and counts toward the rain indicator |
| Windy Hill Open Space Preserve | A0839DB4 | 37.35799, -122.23990 | upper watershed | Counts toward the creek's rain indicator only (not shown on the page) |
| Trappers Trail (Valley Water) | A08204FE | 37.34611, -122.18083 | upper watershed | Counts toward the creek's rain indicator only (not shown on the page) |

**Rain indicator** (Heavy, Very heavy, Intense). Why these numbers: for most creeks there is no record of how much rain causes flooding, so the rain indicator says how **rare** the rain is instead. It uses NOAA Atlas 14, the federal standard for rainfall frequency, at each gauge's own location, so the same word means equally rare rain at every gauge. The three steps are the 1-, 2- and 5-year storm: Heavy is reached in most years (about a 63% chance each year), Very heavy in about 2 years in 5 (39%), Intense in about 1 year in 5 (18%). Status: **Provisional**: a starting point, not yet checked against past floods on this creek.

<details><summary>Background: rain indicator levels at each gauge (no action needed)</summary>

The rain indicator uses the heaviest rain over any window: Heavy = 1-year storm, Very heavy = 2-year, Intense = 5-year (NOAA Atlas 14 depths at the gauge, inches). These say how rare the rain is, not whether the creek floods.

| Gauge | Level | 30 min | 1 hr | 3 hr | 24 hr |
|---|---|---|---|---|---|
| Wunderlich County Park | Heavy (1-year) | 0.517 | 0.734 | 1.37 | 3.28 |
| Wunderlich County Park | Very heavy (2-year) | 0.649 | 0.921 | 1.71 | 4.22 |
| Wunderlich County Park | Intense (5-year) | 0.822 | 1.17 | 2.16 | 5.46 |
| Windy Hill Open Space Preserve | Heavy (1-year) | 0.488 | 0.692 | 1.29 | 3.1 |
| Windy Hill Open Space Preserve | Very heavy (2-year) | 0.613 | 0.869 | 1.62 | 3.96 |
| Windy Hill Open Space Preserve | Intense (5-year) | 0.777 | 1.1 | 2.04 | 5.08 |
| Trappers Trail (Valley Water) | Heavy (1-year) | 0.427 | 0.603 | 1.11 | 2.65 |
| Trappers Trail (Valley Water) | Very heavy (2-year) | 0.535 | 0.756 | 1.4 | 3.34 |
| Trappers Trail (Valley Water) | Intense (5-year) | 0.677 | 0.956 | 1.77 | 4.25 |

Source: NOAA Atlas 14 Vol. 6 v2, partial-duration series, point estimate at the gauge (pulled 2026-10-13).

</details>

## Thresholds: the 2026 Update compared with OneRain today

On the 2026 Update's public pages this creek shows readings only; its status shows only in the staff preview. The **2026 Update** columns are what the new site uses. The **OneRain** columns are the thresholds set on each OneRain sensor, read from OneRain's own pages on Oct 17, 2026 (creek height from the public sensor pages, rain from the admin sensor pages). A OneRain threshold colors that gauge's readings; it doesn't send a message by itself (OneRain sends text alerts only through separate alarm rules). OneRain's dashboard color settings aren't included. The 2026 Update doesn't read any of these; they're shown so the two systems can be compared.

**Creek height (ft, gauge height)**

| Gauge | Level | 2026 Update uses | OneRain threshold | Same? |
|---|---|---|---|---|
| San Francisquito Creek at Stanford | Flood Monitoring | – | 11.00 ft ("Potential flooding") | OneRain only (the 2026 Update doesn't use it) |
| San Francisquito Creek at Stanford | Flood Watch | – | 12.00 ft ("Flooding likely") | OneRain only (the 2026 Update doesn't use it) |
| San Francisquito Creek at Stanford | Flood Warning | – | 12.80 ft ("Projected flooding in downstream reaches") | OneRain only (the 2026 Update doesn't use it) |
| San Francisquito Creek at Stanford | Rising fast | 0.5 ft within an hour | nothing comparable | 2026 Update only |

How often the creek reached OneRain's levels (USGS record, water years 2008–2026): Flood Monitoring 11.00 ft: 2 of 19 years (highest 13.70 ft); Flood Watch 12.00 ft: 1 of 19 years (highest 13.70 ft); Flood Warning 12.80 ft: 1 of 19 years (highest 13.70 ft).

No OneRain rain thresholds on: Trappers Trail; Wunderlich County Park; Windy Hill Open Space Preserve.

**Tide:** the 2026 Update uses NOAA 9414523 Redwood City for this creek's tide graph and high-tide lines (average daily high tide, MHHW, 7.02 ft NAVD88). OneRain's tide settings aren't included.

<details><summary>Internal to-do for the project team (reviewers can skip)</summary>

- Stanford (stage): USGS 11164500; OneRain site SFC shows the same gauge, so read it from USGS. Confirm whether this gauge reads the tide
- Wunderlich County Park (rain): check they open the Rain Increment sensor; pick one for the card
- Windy Hill Open Space Preserve (rain): check they open the Rain Increment sensor; pick one for the card
- Trappers Trail (Valley Water) (rain): check they open the Rain Increment sensor; pick one for the card

</details>

---

*Generated from the 2026 Update lookup tables (`lookups/`) by `scripts/build_creek_factsheets.py`; edit the tables, not this page. Basis for every number: [THRESHOLDS_BASIS.md](../THRESHOLDS_BASIS.md).*
