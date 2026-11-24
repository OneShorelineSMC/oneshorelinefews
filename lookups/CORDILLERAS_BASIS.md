# Cordilleras Creek: rain compared with Dec 31, 2022

Basis for `CordillerasCreek.html` (staff preview, 2026-11-23). Cordilleras Creek has no creek gauge, so the page
compares rain with the New Year's Eve 2022 storm, the best-documented time it flooded. Everything here is
provisional and not reviewed by OneShoreline staff.

## The reference storm

Flooding reported along the creek in Redwood City: the alphabet streets (G Street) and the Centennial and Edgewood
Park neighborhoods ([Redwood City Pulse](https://www.rwcpulse.com/?p=10447);
[San Mateo Daily Journal, Feb 2024](https://www.smdailyjournal.com/news/local/management-of-cordilleras-creek-still-in-question-in-redwood-city/article_ee7b60bc-c4a0-11ee-bd68-ffe4d29575f0.html)).
Redwood City had about 4.5 in that day, its third-wettest day on record (Pulse).

Rain from the OneRain public sensor pages, pulled 2026-11-23 (tip times to the second):

| Wettest | Belmont 41104 (Old County Rd) | Huddart Park | Atherton 41106 (Caltrain) |
|---|---|---|---|
| 15 min | 0.28 in (5:10 AM) | 0.37 | 0.24 |
| 1 hour | 0.88 in (1:05–2:05 PM) | 1.21 | 0.80 |
| 3 hours | 1.68 in (4:35–7:30 AM) | 2.36 | 1.40 |
| 6 hours | 2.08 in (3:44–9:37 AM) | 3.18 | 1.68 |
| 12 hours | 4.12 in (3:44 AM–3:41 PM) | 6.28 | 2.88 |
| 24 hours | 4.60 in | 7.46 | 3.24 |
| 48 hours | 5.20 in (to 6:27 PM Dec 31) | 8.56 | |
| Dec 31 total | 4.56 in | 7.30 | 3.24 |
| Dec 26–30 (before) | 2.32 in | 5.26 | |

At Belmont against NOAA Atlas 14 at the gauge, that is nearly a 25-year storm over 1 hour, 25- to 100-year over 2–3
hours, 10- to 25-year over 6 hours, beyond 100-year over 12 hours, and 25- to 100-year over 24 hours.

Two bursts, about 4–8 AM and 12–3 PM. The Redwood City tide (NOAA 9414523) peaked at 7.80 ft NAVD88 at 7:12 AM, 0.8
ft above the tide table, during the first burst. The second, wetter hour came near low tide (−0.1 ft predicted at 2:05
PM). So the flooding was mainly from rain.

The page keeps Belmont's record hour by hour (clock hours) from Dec 29, 2022 00:00 Pacific. In clock hours the wettest
1 hour is 0.80 in, 3 hours 1.64, 6 hours 2.04, 12 hours 4.08, 24 hours 4.60, 48 hours 5.16.

## Which rain gauge

Nearest OneRain rain gauges to the watershed center (37.4822, −122.2667): Pulgas 1.8 mi (hills to the west; record
starts after March 2023), Redwood Creek at Johnson St 2.1 mi (not on the public site), Belmont 41104 2.4 mi (bay plain),
Huddart Park 3.2 mi (hills to the south), Atherton 41106 4.2 mi.

Pulgas against Belmont in the 10 storms with 0.5 in or more at both (Jan–Feb 2024, Feb 2025, Nov 2026): about the same
in the wettest hour (0.97×), 1.08× over 3 hours, 1.14× over 6 hours, 1.22× over 12 hours, 1.27× in storm totals.
Huddart runs about 1.5× Belmont.

**Measured rain is the average of Belmont and Pulgas** (from 2026-11-24). Pulgas is in the data job as a "logged"
gauge (`creek_gauges.csv` role `logged`, listed under Belmont): it is read and kept in the hourly record
(`storm_tracker.json`) but counts toward nothing on the Belmont Creek pages. The average of the two runs about 10% above
Belmont, matching the Atlas 14 ratio below, so it is compared with Belmont's Dec 2022 record times K, the same as the
forecast. For hours before Pulgas was logged, the page uses Belmont times 1.1.

## The forecast

RRFS (AQPI / CW3E), the average of the 2 grid points inside the Cordilleras watershed (`rrfs.json`, `watersheds`
"CORDILLERAS CREEK"). It's compared with Belmont's Dec 2022 record times K, the ratio of NOAA Atlas 14 at the watershed
center to Atlas 14 at Belmont (2-year column): 1 h 1.12, 3 h 1.11, 6 h 1.11, 12 h 1.11, 24 h 1.09, 48 h 1.10. That
matches the Pulgas/Belmont ratios above (the watershed sits between the two). "Together" joins the last 48 hours
measured (times 1.1) with the forecast.

NOAA Atlas 14 (PDS, inches) at the watershed center, from the NOAA PFDS, 2026-11-23:

| Duration | 1-yr | 2-yr | 5-yr | 10-yr | 25-yr | 50-yr | 100-yr |
|---|---|---|---|---|---|---|---|
| 1 h | 0.472 | 0.577 | 0.717 | 0.834 | 0.998 | 1.13 | 1.26 |
| 3 h | 0.868 | 1.05 | 1.30 | 1.51 | 1.80 | 2.03 | 2.26 |
| 6 h | 1.23 | 1.50 | 1.87 | 2.18 | 2.60 | 2.94 | 3.29 |
| 12 h | 1.61 | 2.00 | 2.53 | 2.98 | 3.60 | 4.09 | 4.60 |
| 24 h | 1.97 | 2.50 | 3.21 | 3.80 | 4.63 | 5.29 | 5.97 |
| 48 h | 2.49 | 3.16 | 4.06 | 4.80 | 5.84 | 6.65 | 7.50 |

## How good the forecast is here

The Storm Tracker's "Rain forecast vs measured" card checks Cordilleras too (`scripts/rrfs_review.py`, `WATCH`): storms
are found in the Belmont + Pulgas average with the Storm Tracker's own rules (6 dry hours, at least 0.1 in), and the RRFS
forecast for the watershed 6 and 24 hours ahead is rated against Atlas 14 at the watershed's center (Heavy, Very heavy
and Intense at the 1-, 2- and 5-year depths). "Heavy forecast with no storm" isn't checked for Cordilleras yet.

## The headline

The closest any window comes to Dec 2022 (measured, or measured so far plus forecast): under 50% "Well below", 50–74%
"About half of", 75–99% "Approaching", 100% or more "At or above". These bands are placeholders for staff to set.

## What it can't say

Rain only. Whether the creek floods also depends on debris and blockages (the creek is privately owned along most of
its length), culverts, how wet the ground is, and the tide at the outlet.

## Other events to consider

Dec 11, 2014: two mobile home parks on E. Bayshore Rd (1900 block) were evacuated when "a nearby creek overflowed"
(CBS SF); the creek isn't named. It's before the OneRain record, so only daily totals could be compared.
