# Rapidly rising: basis, method and results

This file explains the "rising fast" alert on the FEWS pages: what it is for, the rule, how each gauge's setting
was chosen from its record, the choices behind the method, and its limits. The numbers live in
`creek_gauges.csv` (`rise_ft`) and `settings.csv` (`RISE_*`). The code is `rise_check` in
`scripts/creek_signals.py` (data job) and `riseCheck` in `index.html` (home page). The two must give the same
answer; `scripts/test_rise_parity.py` checks that they do. Reviewed values are signed off at the end of this file
and in [THRESHOLDS_BASIS.md](THRESHOLDS_BASIS.md).

**Status:** version 2.1, Oct 15, 2026. Based on USGS 2007–2026 and OneRain Oct 2019–2026. Independently reviewed twice;
corrections applied, and the known open issues are listed in §8. **Not yet signed off by staff.**

---

## 1. What it is for

Most FEWS creeks don't have flood levels yet, so on those creeks "rising fast" is the main creek-based warning the
public gets. It feeds the creek status (THRESHOLDS_BASIS.md §10):

- "Be ready" on a creek without flood levels (policy switch `BE_READY_FROM_RAIN`)
- "Stay alert" on a creek still at Normal
- "…and rising fast" added to a Watch or Monitoring message

The home page also shows a "Rapidly rising" card.

To do that job, it has to:

1. **Warn early.** Fire before the creek gets high, with as much lead time as possible.
2. **Rarely cry wolf.** A false alert on a dry day costs public trust.
3. **Stay steady.** It shouldn't flicker on and off.
4. **Ignore the tide** at Bayside gauges.

## 2. The rule

All times are worked out in UTC. Every reading carries its UTC time, so the repeated 1 AM hour when daylight saving
ends (Nov 1, 2026) can't double a rise. A gauge's reading **meets the rule** when all of these hold:

| # | Condition | Setting |
|---|---|---|
| 1 | The level is at least the gauge's threshold above the reading in force 60 minutes earlier | `rise_ft` per gauge, else `RISE_FT` (0.5 ft); `RISE_MINUTES` (60) |
| 2 | That earlier reading isn't too old. On a gauge that reports on a schedule, it may be no more than 15 minutes late, so a gap never looks like a fast rise. On a gauge that reports only on change (it holds its value between reports), it may be no more than 12 hours old, the same limit at which the pages call the gauge offline; longer means the gauge was down. | `RISE_REF_LATE_MIN` (15), `GAUGE_QUIET_HOURS` (12) |
| 3 | **Confirmation.** If the gauge's previous reading is within 20 minutes, it must have been rising too: at least half the threshold over its own 60 minutes. If it can't be checked, the reading doesn't count. A single bad reading jumps from a level that wasn't rising, so it fails this. | `RISE_CONFIRM_MIN` (20; 0 = off), `RISE_CONFIRM_FRACTION` (0.5) |
| 4 | **Quiet spell.** On a gauge that reports on change, if it had been quiet for over 60 minutes (its level wasn't changing) and then jumps, its next report must confirm the jump. A real rise is reported step by step. | `RISE_MINUTES` |

The gauge is **rising fast** while all of these hold:

- its newest reading is less than 90 minutes old (`RISE_FRESH_MIN`)
- the reading that met the rule was within the last 30 minutes (`RISE_HOLD_MIN`); for a scheduled gauge, its
  newest reading also counts until the next one arrives
- the level hasn't dropped more than 0.05 ft below that reading (`HOLD_TOLERANCE_FT` in the code, about one
  reading step)
- tidal gauges only: there has been at least 0.10 in of rain on the creek's rain gauges in the last 3 hours
  (`RISE_TIDAL_RAIN_IN`, `RISE_TIDAL_RAIN_HOURS`)

`rise_ft = off` turns it off for a gauge.

While the alert is only being held (the newest reading didn't meet the rule itself, or the reading that met it is
more than 30 minutes old), the home page says "Rose … up to [time]". It gives no "at this rate it reaches …"
estimate, because the rise may have stopped.

## 3. Settings by gauge

| Gauge | `rise_ft` | Basis (§6) | Status |
|---|---|---|---|
| Belmont Creek at Old County Rd (`bel_stage`) | 0.5 | 7 winters: warned before all 44 real Flood Monitoring crossings, about 40 min ahead; 24 alerts/yr. At 0.75 ft the lead drops to about 15 min. | Calibrated (7 yr) |
| Atherton Channel upstream of Caltrain (`ath_caltrain`) | 0.5 | 24 of 25 Monitoring crossings warned, about 2 h ahead; 28 alerts/yr | Calibrated (6 yr) |
| San Bruno Creek at First Avenue (`sb_stage_41102`) | 0.5 | 25 of 28 Monitoring crossings warned, about 1¾ h ahead (0.25 ft: 27 of 28, but 57 alerts/yr). Tidal gauge: the live site also requires rain (§2), which this test doesn't apply, so live alerts will be fewer. One of the 28 is probably a sensor fault (Jun 3, 2026, the gauge's last day). The gauge has been offline since June 3, 2026. | Calibrated (6 yr) |
| San Francisquito Creek at Stanford (`sfq_stage_11164500`) | 0.5 | 20 of 20 big storms warned, about 3 h ahead; 9.5 alerts/yr. At 0.75 ft: 17 of 20. | Calibrated (19 yr) |
| Pilarcitos Creek at Half Moon Bay (`pil_stage_11162630`) | 0.5 | 21 of 21 warned, about 3½ h ahead; 10 alerts/yr | Calibrated (19 yr) |
| Pescadero Creek near Pescadero (`pes_stage_11162500`) | 1.0 | 18 of 18 warned, about 2½ h ahead, with half the alerts of 0.5 ft (2.7/yr vs 5.3/yr) | Calibrated (19 yr) |
| Pescadero Creek at Stage Rd (`pes_stage_41151`) | 1.0 | Same creek as the USGS gauge. 3 of 3 warned at any setting, about 5 h ahead; 1.0 ft gives 3 alerts/yr. | **Provisional** (3 yr) |
| San Gregorio Creek at San Gregorio (`sg_stage_11162570`) | 1.0 | 18 of 18 warned, about 3¾ h ahead; 3.8 alerts/yr vs 8.5 at 0.5 ft | Calibrated (19 yr) |
| Pilarcitos Creek above Stone Dam (`pil_stage_11162619`) | 0.25 | Small creek, weak at any setting: 0.25 ft warned of 6 of 13 (about 1¼ h ahead); 0.5 ft of 4 of 13 | **Provisional** (4.6 yr) |
| Pilarcitos Creek below Stone Dam (`pil_stage_11162620`) | off | The creek barely moves below the dam: its fastest wet-season (Nov–Apr) rise in 19 years was 0.67 ft/hr. At 0.25 ft it would warn of 14 of 39 big storms, about 1¾ h ahead, with 3 alerts/yr. Off because Pilarcitos is covered by the Half Moon Bay gauge. | Calibrated (19 yr): **staff choice** |
| Pilarcitos Creek below Pilarcitos Lake spillway (`pil_stage_111626182`) | 0.5 | Rises come when the lake spills. All 8 alerts were followed by big-storm level, but none came first: a "happening now" signal, not an early warning. | Calibrated (4.6 yr) |
| San Mateo Creek below Crystal Springs Reservoir (`smc_stage_11162753`) | 0.5 | Rises follow reservoir releases, so it is mostly "happening now": 11 of 60 big storms warned, about 45 min ahead. Kept because it is San Mateo Creek's only creek-level signal until flood levels or a reservoir indicator exist (§8). | Calibrated (18 yr): **revisit** |
| Colma Creek at Orange Memorial Park (`col_stage`) | blank (0.5) | Record not usable yet: the gauge sent one reading every 12 hours until 2025 (hourly since), with outages Jun–Oct 2020, Nov 24 – Dec 15, 2021 and May 29 – Oct 16, 2025. 3 of 7 Monitoring crossings warned, but 2 of the 7 are sensor faults (Jul 15 and Aug 18, 2022), and the rule misses the rise when Colma switches from hourly to faster readings (§8). | **Default** |
| Atherton Channel at Alameda de las Pulgas (`ath_alameda`) | blank (0.5) | Record starts Jan 2026; no Monitoring crossing yet | **Default** |
| Green Hills Creek (`gh_stage_41201`) | blank (0.5) | Record starts Dec 2024. One big storm so far (Nov 17, 2025: 0.2 → 5.7 ft in about an hour), warned 64 min ahead at 0.5 ft. Too little to calibrate. | **Default** |

## 4. Data

| Data | Source and retrieval | Period | Notes |
|---|---|---|---|
| USGS gage height (parameter 00065), 8 gauges | USGS Water Data API, with WaterServices `iv` as fallback; GitHub workflow **USGS history pull** (`scripts/fetch_usgs.py`), Oct 15, 2026 | Oct 2007 – Oct 15, 2026. Exceptions: Pilarcitos above Stone Dam from Feb 28, 2022 and below the spillway from Mar 1, 2022; San Mateo from Sep 2008. | 15-minute values, as published. Approved through spring 2026; provisional only since Apr–Jul 2026, after the storm season. |
| OneRain stage, 7 gauges | OneRain public sensor pages, custom date range; archive repo workflow **OneRain history (all creeks)** (`scripts/pull_onerain_history.py`, `combine_onerain_history.py`), Oct 15, 2026 | Oct 1, 2019 (the start of the pull) or the gauge's first reading if later (Colma Jun 2020, San Bruno Sep 2020, Atherton Caltrain Oct 2020, Pescadero 41151 Oct 2023, Green Hills Dec 2024, Atherton Alameda Jan 2026) to Oct 15, 2026. The probe found Belmont readings in 2019; anything before Oct 1, 2019 wasn't pulled. | Values and times exactly as shown, to the second. The pages return at most 200 readings per request; the script detects that and re-reads in smaller pieces. The report showed no incomplete pieces. |
| Flood levels | `thresholds.csv` | | Belmont Monitoring 2.25 ft; Atherton Caltrain 2.80; San Bruno 2.40; Colma 3.40; Atherton Alameda 3.18 |

No values were edited, removed or filled in. USGS qualifiers (estimated, equipment malfunction) were kept; they
cover a small fraction of readings.

## 5. Method

Script: `scripts/evaluate_rising_fast.py --usgs <USGS download> --onerain <OneRain download>`. It writes
`out/rising_fast_eval.md` and `.csv`.

1. **Same rule as the site.** The rule is evaluated at every reading, in UTC, as if the data job ran just after
   it. Each run checks 300 random moments per gauge against a direct call to `rise_check`.
2. **Thresholds tested:** 0.25, 0.5, 0.75, 1.0 and 1.5 ft in 60 minutes.
3. **Alerts:** a stretch of "rising fast" with readings less than 3 hours apart counts as one alert, because that
   is how a person sees it on the page.
4. **Big-storm level:** the gauge's lowest flood level, if it has one. Otherwise, the median of its water-year
   peak stages, roughly a 2-year storm (about a 50% chance in any year). Only years with enough data count: 80% of
   15-minute readings, or readings in at least 10 months for gauges that report on change.
   The median yearly peak is a statistical stand-in, **not** a flood level: on gauges without flood levels, "big
   storms warned first" means warned before a typical yearly high, not before flooding. Where a gauge has flood
   levels, the lowest is Flood Monitoring (50% of channel capacity on Colma, Belmont and Atherton), which is
   still below flooding. See [THRESHOLDS_BASIS.md, Terms](THRESHOLDS_BASIS.md#terms).
5. **Big-storm crossings:** each time the creek rose through that level, at least 24 hours after the previous
   time. A crossing made by a single reading that jumps at least 1 ft from a steady level (the two readings before
   it within 0.1 ft) and falls straight back by 80% or more is a sensor spike, not a storm. It is set aside and
   counted separately. A real peak is already climbing before it, so it isn't caught by this test.
6. **Warned first:** whether an alert started in the 6 hours before a crossing, and how long before. The median
   is reported. "Followed by" counts alerts after which the creek reached its big-storm level within 6 hours.
7. **Choosing a value:**
   - Creeks that take hours to peak: the highest threshold that still warns of all, or all but one, of the
     crossings, with a median lead of 2 hours or more.
   - Flashy creeks (Belmont): protect lead time over cutting alerts.
   - Gauges below dams: case by case (§3).
   - Gauges without a usable record: the default.

## 6. Results

◀ = the gauge's chosen value. Lead is the median minutes between the first alert and the creek reaching its
big-storm level.

**USGS gauges (15-minute data, 2007–2026).** Each cell: alerts per year · big storms warned first · median lead (min).

| Gauge (big-storm level; years) | 0.25 | 0.5 | 0.75 | 1.0 | 1.5 |
|---|---|---|---|---|---|
| San Francisquito at Stanford (6.00 ft; 19 yr) | 19.9 · 20/20 · 278 | **9.5 · 20/20 · 180 ◀** | 4.9 · 17/20 · 120 | 3.0 · 12/20 · 60 | 0.9 · 5/20 · 30 |
| Pilarcitos at Half Moon Bay (9.17 ft; 19 yr) | 21.6 · 21/21 · 285 | **10.4 · 21/21 · 210 ◀** | 6.0 · 18/21 · 150 | 4.0 · 18/21 · 105 | 1.6 · 11/21 · 90 |
| Pescadero near Pescadero (USGS) (10.41 ft; 19 yr) | 7.8 · 18/18 · 285 | 5.3 · 18/18 · 195 | 4.0 · 18/18 · 165 | **2.7 · 18/18 · 150 ◀** | 1.7 · 16/18 · 82 |
| San Gregorio at San Gregorio (13.53 ft; 19 yr) | 13.3 · 18/18 · 352 | 8.5 · 18/18 · 278 | 6.1 · 18/18 · 248 | **3.8 · 18/18 · 225 ◀** | 2.4 · 14/18 · 158 |
| Pilarcitos above Stone Dam (3.40 ft; 4.6 yr) | **8.2 · 6/13 · 75 ◀** | 4.3 · 4/13 · 82 | 1.1 · 2/13 · 38 | 0.2 · 0/13 | 0 |
| Pilarcitos below Stone Dam (6.67 ft; 19 yr) | 3.0 · 14/39 · 100 | 0.2 · 0/39 | 0 | 0 | 0 |
| Pilarcitos below spillway (3.54 ft; 4.6 yr) | 5.0 · 3/16 · 15 | **1.7 · 0/16 ◀** | 1.3 · 0/16 | 1.1 · 0/16 | 0 |
| San Mateo below Crystal Springs (5.88 ft; 18 yr) | 17.6 · 21/60 · 90 | **7.2 · 11/60 · 45 ◀** | 3.1 · 3/60 · 75 | 1.3 · 0/60 | 0.5 · 0/60 |

**OneRain gauges (Oct 2019–2026, as available).** Each cell: alerts per year · big storms warned first · median lead (min).

| Gauge (big-storm level; years) | 0.25 | 0.5 | 0.75 | 1.0 | 1.5 |
|---|---|---|---|---|---|
| Belmont at Old County Rd (2.25 ft; 7.0 yr; 12 spikes set aside) | 27.6 · 44/45 · 59 | **23.6 · 44/45 · 42 ◀** | 19.0 · 44/45 · 16 | 14.9 · 42/45 · 10 | 10.5 · 33/45 · 6 |
| Atherton upstream of Caltrain (2.80 ft; 6.0 yr) | 33.2 · 24/25 · 175 | **28.1 · 24/25 · 128 ◀** | 20.3 · 23/25 · 86 | 16.4 · 22/25 · 58 | 8.6 · 15/25 · 38 |
| San Bruno at First Avenue (2.40 ft; 5.7 yr) | 57.2 · 27/28 · 204 | **31.3 · 25/28 · 110 ◀** | 17.9 · 15/28 · 42 | 8.2 · 7/28 · 22 | 2.8 · 2/28 · 14 |
| Pescadero at Stage Rd (OneRain) (11.52 ft; 3.0 yr) | 10.0 · 3/3 · 307 | 5.3 · 3/3 · 307 | 4.0 · 3/3 · 307 | **3.0 · 3/3 · 296 ◀** | 1.0 · 3/3 · 246 |
| Colma at Orange Memorial Park (3.40 ft; 6.3 yr) | 9.2 · 3/7 · 80 | **5.9 · 3/7 · 80 ◀** | 3.3 · 2/7 · 195 | 2.5 · 2/7 · 195 | 1.1 · 1/7 · 80 |
| Green Hills at Green Hills CC (4.50 ft; 1.8 yr) | 42.6 · 1/1 · 69 | **29.3 · 1/1 · 64 ◀** | 21.6 · 1/1 · 50 | 16.6 · 1/1 · 31 | 9.4 · 1/1 · 19 |

Belmont's one unwarned crossing (Oct 22, 2019) is a second sensor spike the same day, 11 hours after the first (0.08 → 5.46 → 0.09 → 5.52 → 0.08 ft). The spike test can't separate it, because the reading two before it is the first spike. All 44 real crossings were warned.

**What the results say:**

- **Natural creeks give hours of warning.** These are San Francisquito, Pescadero, San Gregorio, Pilarcitos at Half
  Moon Bay, and Atherton Caltrain. Pescadero and San Gregorio rise far enough in big storms that 1.0 ft still
  catches them all, with half the alerts.
- **Belmont is flashy.** It rose 2 ft or more within an hour on 47 different days, and up to 6.4 ft (Nov 17, 2025). At 0.5 ft it warned of every real Monitoring crossing in
  7 winters, about 40 minutes ahead; at 0.75 ft that drops to about 15 minutes. It had about 24 alerts a year,
  starting with the creek at a median 0.7 ft. Staff report that Belmont floods streets often; whether the alerts that
  didn't reach Monitoring coincided with street flooding hasn't been checked.
- **Below dams, a fast rise is a release or spill.** It says the creek is rising now, not that it will.
- **Sensor spikes happen on some OneRain gauges.** Belmont's gauge logged 27 single-reading spikes of 1 ft or more
  from Oct 2019 to 2022 (for example, 0.09 → 7.97 → 0.08 ft on Oct 17, 2019), and none since 2023. The
  rule rejects them (§7). The flood-level status does not (§8).

## 7. Methodological choices

| Choice | Alternatives considered | Why |
|---|---|---|
| Rise over 60 minutes, compared with the reading in force 60 minutes earlier | A 30-minute fitted slope (the earlier plan) | Matches the public message ("up 0.7 ft in the last hour"), is easy to check by hand, and runs the same in the browser and the data job. Single bad readings are handled by confirmation instead. |
| Confirmation: the previous reading (within 20 min) must have risen at least half the threshold | Off; the previous reading must meet the full rule (v2) | Half the threshold matched "off" at most gauges and still rejects lone spikes. The exceptions are San Mateo (11 vs 13 of 60), Pilarcitos above Stone Dam (6 vs 7 of 13), Pilarcitos below the spillway (0 vs 1 of 16) and Colma (lead 80 vs 90 min). The full-rule version cost a reading's worth of warning on the flashy OneRain gauges: Belmont 22 vs 42 min, Atherton Caltrain 95 vs 128 min, San Bruno 20 vs 25 of 28. **Cost against v2:** a few more short alerts, up to about 4 a year per gauge (under 1 at most USGS gauges), mostly brief bumps in the middle of a storm (e.g. Belmont 0.43 → 0.65 → 0.53 ft). See the table below. |
| On-change gauges quiet for over 60 minutes need a second report to confirm a jump | Never; always | In dry weather these gauges report every ~12 hours, so a glitch would have nothing nearby to confirm it. Requiring it after any gap cut Belmont's lead; after 60 minutes of quiet it cost nothing, because Belmont reports every few minutes in storms. |
| Comparison reading can't be too old (15 min late on scheduled gauges; 12 h on on-change gauges) | No limit (the earlier rule) | The earlier rule compared a gauge back from an outage with its last reading from hours or days before. |
| Times in UTC | Pacific clock time (the earlier rule) | On the night daylight saving ends, Pacific clock times 60 minutes apart can be 120 minutes apart, which doubled rises. |
| Holds 30 minutes after the reading that met the rule, unless the level drops | Hysteresis on the rate (earlier plan) | Simple, works from the readings alone on both the page and the job, and stops flicker when a rise pauses. |
| Choose thresholds by warning performance against big storms | The gauge's 99th-percentile wet-season rise (earlier plan) | Most wet-season readings are calm, so the 99th percentile is only 0.04–0.26 ft at the USGS gauges. It would fire constantly and says nothing about warning value. The script still reports it. |
| Big-storm level = lowest flood level, else the median annual peak | NWS flood stages (none for these gauges); peaks from the discharge record | Objective and defined the same way everywhere. It marks a serious storm, **not flooding** (§8). |
| Sensor spikes set aside when counting big storms | Counting them; a looser test (any reading that comes straight back) | A reading that jumps at least 1 ft from a steady level and comes straight back is a sensor fault; counting it would score the rule on warnings it should never give. A looser first version also set aside real one-reading peaks (Belmont Oct 24, 2021; Green Hills Nov 17, 2025), so the test was tightened. Only Belmont has spikes set aside (12). The test is strict, so a few faults elsewhere still count as storms, which makes those gauges look worse, not better: Colma Jul 15 and Aug 18, 2022; San Bruno Jun 3, 2026. |
| No minimum stage | A floor below which rises don't count (earlier plan) | Belmont's alerts began at a median 0.7 ft, well below Monitoring (2.25 ft). That early part of the rise is the warning. |
| Tidal gauges: keep the rain condition; no tide subtraction | Subtracting the tide's rate (earlier plan) | In a dry-weather check (Oct 12–14, 2026), the Colma, Atherton, Belmont, Green Hills, San Francisquito and San Mateo gauges moved ≤ 0.04 ft with the tide. Storm-time backwater hasn't been measured; revisit after a storm with high tides. |
| One threshold per gauge | One countywide value | Creeks differ several-fold in how fast they rise in big storms. |
| Data used as published, including provisional | Approved data only | USGS storm-season data is all approved; OneRain data is provisional, which is all there is. |

**Confirmation options** at each gauge's chosen value (alerts · big storms warned first · median lead in min):

| Gauge | Off | Full rule (v2) | Half the threshold (v2.1) |
|---|---|---|---|
| Belmont (0.5 ft) | 194 · 44/45 · 42 | 155 · 44/45 · 22 | 166 · 44/45 · 42 |
| Atherton Caltrain (0.5 ft) | 169 · 24/25 · 128 | 149 · 24/25 · 95 | 169 · 24/25 · 128 |
| San Bruno (0.5 ft) | 182 · 25/28 · 110 | 158 · 20/28 · 108 | 180 · 25/28 · 110 |
| San Francisquito (0.5 ft) | 181 · 20/20 · 180 | 170 · 19/20 · 165 | 181 · 20/20 · 180 |
| Pilarcitos HMB (0.5 ft) | 203 · 21/21 · 210 | 163 · 20/21 · 195 | 198 · 21/21 · 210 |
| San Gregorio (1.0 ft) | 73 · 18/18 · 225 | 66 · 17/18 · 210 | 73 · 18/18 · 225 |
| Pescadero (USGS) (1.0 ft) | 52 · 18/18 · 150 | 51 · 18/18 · 135 | 52 · 18/18 · 150 |
| Pilarcitos above Stone Dam (0.25 ft) | 38 · 7/13 · 60 | 36 · 5/13 · 75 | 38 · 6/13 · 75 |
| San Mateo (0.5 ft) | 143 · 13/60 · 45 | 102 · 7/60 · 45 | 130 · 11/60 · 45 |

## 8. Limits

- **Big-storm level is not a flood level** for the USGS gauges and Pescadero 41151. "Warned first" there means
  warned before a serious storm, not before flooding. When flood levels or flood observations exist, rerun the
  script against them.
- **Sensor spikes also affect the flood-level status.** The live status uses the newest reading as-is, so a spike
  like Belmont's 2019–2022 ones would show a Flood Warning for one reading. Belmont hasn't spiked since 2023, but
  a spike check on flood levels belongs in the QC work (Phase 2).
- **Hourly readings can't be confirmed.** Colma (`col_stage`) and Atherton at Alameda (`ath_alameda`) report every
  60 minutes in quiet weather and add extra readings in storms. When the reading before is an hour old, there's
  nothing within 20 minutes to confirm against, so one bad reading can show "rapidly rising" until the next reading.
  Both use the default.
- **Open issue: a gauge that switches from hourly to faster readings in a storm can miss its rise.** On Nov 17,
  2025, Colma rose from 0.2 to 4.3 ft between 11 PM and 12:05 AM. Its first fast reading had no valid comparison
  reading: the one from an hour earlier was 55 minutes late, past the 15-minute limit. The next reading therefore
  couldn't be confirmed, and the first alert came at 12:10 AM, with the creek already falling. This affects Colma and
  Atherton Alameda, and the live rule today behaves the same way. **Proposed fix (to test next):** for gauges that
  report on a schedule, compare with the last reading before the hour even if it's late, and scale the rise to the
  actual time between them. A gap then averages out instead of looking like a fast rise.
- **Open issue: "Up X ft in the last hour" can show while the creek is falling.** After a sharp peak, each falling
  reading can still be more than the threshold above the reading from an hour earlier. Belmont on Nov 17, 2025
  showed "Up 3.57 ft" at 4.34 ft, falling from 6.54 ft. The live rule today does the same. **Proposed fix (to test
  next):** a reading only meets the rule if it isn't lower than the reading before it, allowing for gauge noise.
- **Two bad readings in a row** (for example, a gauge dropping out to zero for two readings an hour ago) can still
  look like a rise. So can one bad reading in the middle of a real, moderate rise (the reading before already up
  half the threshold).
- **A long silence before a storm delays the first alert.** If an on-change gauge sends nothing for more than 12
  hours and a storm then starts, the first ~70 minutes of the rise can't alert: the last report is too old to
  compare with.
- **The "latest" reading has no UTC time of its own.** It borrows the offset of the reading before it, which is an
  hour off if the clocks changed in between. This is rare. The data job should store UTC for it.
- **No validation against observed flooding yet.** Records of when and where streets flooded (public works logs,
  service calls, dated photos) would show which stage means water in the street, and whether the alert came first.
- **Lead time is measured at the gauge.** It doesn't include the delay before the public sees it: the gauge's
  reporting interval, OneRain posting, the 5-minute data job, and page refresh. Measure that once in a storm. It
  matters most at Belmont.
- **Lead counts the first alert in the 6 hours before a crossing**, which in a storm with several bursts can be
  an earlier burst.
- **Evaluated at reading times.** On the live site an alert also ends between readings when the 30-minute hold
  runs out. The counts above treat it as ending at the next reading.
- **The tidal rain condition isn't simulated** (San Bruno), so San Bruno's live alerts will be fewer than shown.
- **Channel beds change.** San Gregorio's typical water level rose about 2 ft in 2016–17 and stayed higher for
  years, and Pescadero's has crept up. This shifts fixed stage levels much more than a rate of rise.
- **Reservoir-controlled creeks** (San Mateo below Crystal Springs, Pilarcitos below the dams): a better early
  warning is the reservoir approaching its spill level. Crystal Springs' level is USGS 11162750, in the history
  pull, and the gauge note gives spill at 294.6 ft. Not yet analyzed.

## 9. Updating

- **After each winter:** rerun the USGS history pull and the OneRain history pull, then the script. Change
  `rise_ft` only if the results move, and record it below.
- **When a creek gets flood levels, or a gauge builds a usable record** (Colma hourly, Atherton Alameda, Green
  Hills): rerun. The script uses flood levels automatically.
- **Changes to the rule itself** go in both `rise_check` and `riseCheck`. Then run
  `python scripts/test_creek_signals.py` and `python scripts/test_rise_parity.py` (needs Node.js).

## Sign-off

| Date | Who | What was checked / changed |
|---|---|---|
| 2026-10-15 | Analysis (Claude, for OneShoreline staff review), with independent reviews | v2: rule revised; per-gauge values from USGS 2007–2026 |
| 2026-10-15 | Analysis (Claude), with an independent review | v2.1: half-threshold confirmation; OneRain Oct 2019–2026 added; sensor spikes set aside |
| | | |
