# Shoreline Kiosk – Raspberry Pi setup

Runs `ShorelineKiosk.html` full screen on a Raspberry Pi with a 7" touchscreen (1024×600 or 800×480; the page fits either).
The page lives on GitHub Pages like the dashboard widgets, so updating the kiosk is just a commit to the repo.

Kiosk URL:

```
https://oneshorelinesmc.github.io/oneshorelinefews/ShorelineKiosk.html
```

Options you can add to the end of the URL:

| Option      | Effect                                                    |
|-------------|-----------------------------------------------------------|
| `?theme=dark` | Dark background – easier on the eyes in a dim EOC        |
| `?cursor=1`   | Always show the mouse pointer. (Without it the pointer is hidden for the touchscreen, but appears whenever a mouse moves and hides after 3 seconds.) |
| `?zoom=0`     | Use the older picture scaling instead of CSS zoom (only if a screen looks wrong) |
| `?tab=creek`  | Start on the Creeks tab (add `&creek=belmont` etc. to choose the creek) |
| `?preview=1`  | Creek status layer (staff preview): the Dashboard Creeks view shows a status tile for each dashboard creek, plus any preview-only creek that has a status (up to 6 tiles; quiet ones listed underneath). Used on the EOC kiosk during the first storms; combine with other options using `&`, e.g. `?tab=creek&preview=1` |
| `?rotate=30`  | Switch between Bay Tides and Creeks every 30 seconds |
| `?tab=map`    | Start on the Map tab                                      |
| `?tab=about`  | Start on the About tab                                    |
| `?tab=disclaimer` | Start on the Disclaimer tab                           |

## Preview on a computer first

Open the kiosk URL in any browser; the mouse pointer appears when you move the mouse. The layout scales to fit the window, so it looks the
same as on the 7" screen. Click the alert bar or a part of the Bay Tides panel to see the touch screens.

## What you need

- Raspberry Pi 4 or 5 (2 GB RAM or more is plenty), power supply, microSD card (16 GB+)
- The 7" touchscreen (HDMI for video, USB for touch on most Hosyond models)
- Wi-Fi or Ethernet that can reach `api.weather.gov`, `api.tidesandcurrents.noaa.gov`,
  `raw.githubusercontent.com`, and `cdnjs.cloudflare.com` (some office networks block sites; check with IT)

## 1. Install Raspberry Pi OS

1. On a computer, use **Raspberry Pi Imager** to write **Raspberry Pi OS (64-bit, with desktop)** to the card.
2. In Imager's settings, set a username/password, Wi-Fi, and **time zone `America/Los_Angeles`**.
3. Boot the Pi with the screen attached. Let it finish its first-boot updates.

If the screen's maker gives extra setup steps (some displays need a line added to `config.txt`),
do those now and confirm touch works on the desktop.

## 2. Turn off screen blanking

`Raspberry Pi menu → Preferences → Raspberry Pi Configuration → Display → Screen Blanking: Off`
(or in a terminal: `sudo raspi-config` → Display Options → Screen Blanking → No). Reboot.

## 2b. Make the picture sharp (run the Pi at the screen's own resolution)

Every screen has a fixed number of pixels (its *native resolution*). Many 7" Hosyond screens are **1024 × 600**;
some are 800 × 480. Check the label, box or product listing. If the Pi sends the screen any other resolution,
the screen stretches or shrinks the picture and everything looks soft, no matter what the page does.

1. `Raspberry Pi menu → Preferences → Screen Configuration`. Right-click the screen → **Resolution** →
   choose the screen's native resolution (e.g. **1024x600**), then **Apply** and keep the change.
2. If it isn't offered, set it at startup: `sudo nano /boot/firmware/cmdline.txt`, and at the end of the
   **single existing line** add a space and `video=HDMI-A-1:1024x600M@60` (use your screen's numbers, and
   `DSI-1` instead of `HDMI-A-1` if the screen connects by ribbon cable). Save and reboot.
3. In the kiosk start line below, keep `--force-device-scale-factor=1` so Chromium doesn't enlarge the page on
   its own.

The kiosk is laid out at 800 × 480 and enlarged to fit the screen. On a 1024 × 600 screen it's drawn 1.25×
larger (1000 × 600, with a thin 12-pixel border on each side), and text and graphs are drawn at the full
1024 × 600 detail rather than stretched.

The kiosk page also positions itself on whole pixels and, on current Chromium (version 128 or later),
enlarges with CSS zoom rather than a picture scale, so text stays crisp on larger screens too. Add `?zoom=0`
to the address to switch back to the older scaling if a screen ever looks wrong.

## 3. Start the kiosk automatically

Open a terminal and run:

```bash
mkdir -p ~/.config/labwc
nano ~/.config/labwc/autostart
```

Add this line (all on one line), then save with Ctrl+O, Enter, Ctrl+X:

```bash
chromium --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 --force-device-scale-factor=1 --incognito "https://oneshorelinesmc.github.io/oneshorelinefews/ShorelineKiosk.html" &
```

(When the site moves to fews.oneshoreline.org, change this address to `https://fews.oneshoreline.org/ShorelineKiosk.html`.)

Reboot (`sudo reboot`). The kiosk should open full screen after the desktop loads.

> If nothing opens: some Raspberry Pi OS versions name the browser `chromium-browser` instead of
> `chromium` – try that in the line above. Older versions that don't use the "labwc" desktop
> use `~/.config/wayfire.ini` or `~/.config/lxsession/LXDE-pi/autostart` instead; the Raspberry Pi
> documentation's "kiosk" guide for your OS version has the exact file.

## 4. Getting in and out

- To exit the kiosk temporarily: plug in a keyboard and press **Alt+F4**.
- To change what it shows: edit `ShorelineKiosk.html` on GitHub. The Pi picks up the change at its
  daily 3 AM reload, or right away if you reboot it.

## How it behaves unattended

- **Refresh:** NWS alerts every 3 min, measured water levels every 6 min, creek data every 3 min,
  tide predictions every hour.
- **Network drops:** it keeps showing the last good data and retries on its own. If data is more than
  90 minutes old, the footer turns amber: *"Data out of date"*.
- **Daily reload at 3 AM** keeps the browser fresh during multi-day activations.
- **Touch:** tap the alert bar for full NWS alert text, or a station for its full list of predicted
  times above MHHW. Detail screens return to the main view after 45 seconds. The buttons at the bottom
  switch between tabs.

## Screen care: burn-in protection and turning the screen off after hours

**Pixel shift (built in).** Every 10 minutes the whole picture moves by a pixel or two, in a small loop, so the
parts that never change (title bar, alert bar, tab buttons, panel edges) don't sit on exactly the same pixels for
days. It isn't noticeable. Settings: `PIXEL_SHIFT_MIN` (10; 0 turns it off) and `PIXEL_SHIFT_PX` (2).

The 7" screen is an LCD, so permanent burn-in is unlikely; the risk is faint temporary "ghosting" after days of
an unchanging picture, which pixel shift and switching the screen off overnight both prevent. Turning the
brightness down a little (if the screen has a control) also helps.

**Office kiosk: screen off after hours.** This is set on the Pi itself (the kiosk page keeps running, so it's
current the moment the screen comes back on). Leave the **EOC kiosk on** during activations.

1. Find the screen's name: open a terminal on the Pi and run `wlr-randr`. The first word of the output is the
   name, usually `HDMI-A-1` (or `DSI-1` for a ribbon-cable screen).
2. Run `crontab -e` (choose `nano` if asked) and add these two lines at the bottom, using that name. This turns
   the screen off at 7 PM and on at 7 AM, Monday–Friday, and leaves it off all weekend:

   ```
   0 19 * * 1-5 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wlr-randr --output HDMI-A-1 --off
   0 7  * * 1-5 WAYLAND_DISPLAY=wayland-0 XDG_RUNTIME_DIR=/run/user/1000 wlr-randr --output HDMI-A-1 --on
   ```

   Save with Ctrl+O, Enter, Ctrl+X. To change the hours, edit the first two numbers on each line
   (minute, hour, 24-hour clock); `1-5` is Monday–Friday.
3. Test it now: run the `--off` command (everything after `1-5 `) in the terminal, check the screen goes dark,
   then run the `--on` one.

Good to know:
- **During an activation or a storm**, turn the screen on right away by running the `--on` command, or simply
  reboot the Pi. To stop the schedule, run `crontab -e` and put `#` at the start of both lines.
- **Touching the screen doesn't wake it** while it's off; use the `--on` command or a reboot.
- Some small HDMI screens keep their backlight lit even with no picture. If yours glows when "off", plug the
  screen (not the Pi) into an outlet timer or smart plug set to the same hours instead.
- `1000` is the first user account on the Pi. If you created the kiosk under a different account, run `id -u`
  as that user and use its number instead.

## Map tab

The **Map** button shows every public OneShoreline Early Warning (OneRain) site on a map, like OneRain's
own map:

- **Markers** are colored by status: green = reporting, yellow / orange / red = Flood Monitoring / Watch /
  Warning level, gray = no report in the past 24 hours. Square markers are rain-only gauges. Sites at an
  alert level are drawn larger and on top.
- **The side panel** shows how many sites are at each status, which sites are at an alert level, and the
  sites with the most rain in the past 24 hours.
- **Tap a site** to see its latest readings, how long ago each came in, and a small 24-hour graph (with
  threshold lines where they're set). It returns to the overview after 45 seconds, or tap
  **Back to all sites**. Pinch or use + / − to zoom.
- The data comes from `sites.json`, published every 15 minutes by the same GitHub job as the creek data
  (see below), so the map can lag OneRain by up to about 20 minutes.
- **Alert levels** on the map come from the creek gauges and thresholds in `lookups/creek_gauges.csv` and `lookups/thresholds.csv`.

## Bay Tides tab

Redwood City only (NOAA 9414523, ft NAVD88). Built for a responder walking in at shift change: one sentence first,
the week next, details behind a tap.

- **Headline band** (top, the color goes around the whole box): red with "Tides above MHHW: Today 12:55–3:25 PM
  (7.64 ft) · Tomorrow 1:17–4:03 PM (7.70 ft) +1 more this week", or green with "No tides above MHHW in the next 7
  days". Heights come from one series: measured for what has already happened, then the NOAA model forecast, then
  the astronomical prediction, so the band and the cards always agree (e.g. "Above MHHW now, until 3:24 PM · peaked
  7.62 ft measured at 2:12 PM"; the card shows the same 7.62 marked "measured"). MHHW (7.02 ft) is
  a placeholder threshold until OneShoreline sets tide levels tied to known impacts. On the right: "Now 6.69 ft
  rising · +0.45 vs predicted"; tap it for the measured-vs-predicted table for the past week, the "running higher
  than predicted" summary and the model's accuracy over the last 24 hours. Tap the rest of the band for the times.
- **Next 7 days:** one card per day with that day's highest tide (ft) and time; red with "+0.21 ft over MHHW" when above
  MHHW. Other days carry no "below MHHW" label: past the ~2-day model forecast the heights are only the astronomical
  prediction and can't rule a high tide out. Cards marked "fcst" use the NOAA model forecast; later days use the prediction. The graph under the cards lines up with them and has three
  lines: measured (blue), NOAA forecast (teal) and predicted (dark), heights in ft NAVD88 on the left, and a "Now" tag on the current time. Tap for the forecast and predicted times above
  MHHW and the "if the Bay stays high" scenario for the days after the forecast ends.
- **NOAA model forecast:** NOAA's San Francisco Bay Operational Forecast System publishes a water-level forecast for
  the Redwood City gauge that includes wind, air pressure and river flow (Tides & Currents product
  `ofs_water_level`, requested in ft NAVD88, updated 4 times a day, about 2 days ahead). It is model guidance, not an
  official forecast; NWS advisories take precedence. If it is missing, older than 12 hours or doesn't reach 6 hours
  ahead, the tab uses the predictions alone.
- **NWS row** (bottom): never repeats the alert already in the top alert bar. It shows "NWS forecasters on tides:" the lines about tides or coastal flooding from the NWS San Francisco Bay Area office's latest
  forecast discussion (api.weather.gov, office MTR; ignored if older than 24 hours; the issue time is on the tap
  screen), or says there's nothing. If the top bar is showing a different, higher-priority alert, a Coastal Flood /
  Storm Surge / Tsunami alert appears here instead ("Also: …") so it isn't hidden. Tap for full details.

- **King Tide / high water line** (under the NWS row, `tide_season.js`): from NOAA's Redwood City tide table and the
  height expected with the weather (about 2 days ahead). It shows, first, a high tide in the next 7 days that reaches the
  flood level (`TIDE_RED_FT_RWC`, 8.5 ft NAVD88, provisional): "HIGH WATER · Tomorrow 9:40 AM: expected 8.6 ft with the
  weather, high enough to flood low areas near the Bay". Otherwise the next King Tide within 7 days (the highest tide of
  the month in Nov, Dec, Jan): "KING TIDE · King Tide Sat Nov 14: highest tide of the month, 8.1 ft around 9:40 AM",
  with "weather may push it about 0.4 ft higher" when NOAA's model differs. Hidden the rest of the time. Tap for the
  next 2 days and the coming King Tides.

## Title bar

A slim OneShoreline-blue bar across the top of every tab reads **FLOOD EARLY WARNING SYSTEM | OneShoreline |
San Mateo County**, above the NWS alert bar.

## About tab

The **About** button shows what each tab means, an "in an emergency, call 911" reminder, OneShoreline's
contact details (phone, email, website, address), and two QR codes people can scan with their phones:
**Contact OneShoreline** and **Get alerts: SMC Alert**. It returns to Bay Tides on its own after 2 minutes.
`?tab=about` at the end of the kiosk URL opens it directly (handy for checking the QR codes).

## Disclaimer tab

The **Disclaimer** button shows OneShoreline's data disclaimer (informational purposes only; thresholds are
approximate; actual conditions may vary) and "In an emergency, call 911". Like About, it returns to Bay Tides
on its own after 2 minutes and isn't part of the automatic tab rotation.

## Creeks tab

The **Creeks** tab opens on **Dashboard Creeks**: one card per creek (Colma, San Bruno, Belmont, Atherton),
bordered all the way around in its status color, with each gauge's stage (an offline gauge shows "Offline · since
Jun 3", never an old number), accumulated rain over the creek's own windows (a window that has reached a trigger is
red), and the Bay tide in ft NAVD88 with how far it is below or above MHHW and whether it is rising or falling.
Rain-trigger progress (Belmont, the only creek with rain triggers in `lookups/thresholds.csv`) appears only once it rains; when a trigger is met the card just says
"Trigger met ⚠ 4 hr rain + high tide" (the amounts are on the rain and tide rows). Tap a card, or a creek
button across the top, for that creek's graphs. Each button turns yellow, orange or red when that creek is at a
flood level. A single creek goes back to All creeks after 5 minutes (`CREEK_RETURN_MIN`). The NWS alert bar
stays at the top on every tab.

For the chosen creek, all on one time axis (last 36 hours plus the next 12 hours of predicted tide):

- **Each stage gauge** (Atherton Channel has two) with its current level, colored by the highest threshold
  passed, and a graph with its Flood Monitoring / Watch / Warning lines
- **Rain per hour** at the creek's rain gauge(s), with "Accumulated rain" totals matching the creek's OneRain
  dashboard (Atherton 30 min; Belmont 30 min and 4 hr; Colma 6 hr; San Bruno, which is very flashy, 15 min, 30 min and
  3 hr; plus 1 hr and 24 hr). San Bruno's two rain gauges are shown as a small table, one row per time window. Belmont also has a
  4-hour running-total graph with its 0.42 in trigger line. **When no rain has fallen in the last 36 hours the
  rain graphs fold into one line** ("Rain: none in the last 36 hours") and give their space to stage and tide;
  they come back with the first rain.
- **The Bay tide** at the nearest NOAA station (Alameda or Redwood City), measured, NOAA forecast and predicted.
  All four creeks are tidally influenced, so every creek keeps its tide graph; it shows whether a rise is coming
  from rain, the tide, or both. The left column has the tide now ("Bay tide 6.24 ft · 0.78 below MHHW, rising",
  plus "+0.45 vs predicted" when the Bay is running 0.2 ft or more off the tide tables).
- **Graph legends:** each graph's legend is on its own title row (rain gauges; running rain total and its trigger;
  stage with its Monitoring/Watch/Warning lines and values; tide with measured, NOAA forecast, predicted and MHHW).
  The tide graph includes the NOAA model forecast (green) for the creek's tide station (Redwood City or Alameda).
  A "Now" tag on the top graph (rain, or the first stage graph when dry) marks the line that runs through all of them. MHHW is drawn in slate gray so orange
  only ever means Flood Watch; Belmont's 4-hour rain trigger line uses its own level color (Flood Warning red).
- **Belmont Creek's rain triggers**: flooding is likely if 30-minute rain exceeds 0.20 in, or 4-hour rain
  exceeds 0.42 in while the tide is high (6.32 ft NAVD88 at Redwood City). When dry the left column lists what
  sets each trigger off; once it rains it shows the running amounts ("4 hr rain 0.30 of 0.42 in + tide 6.10 of
  6.32 ft"), red when met.

Tap **ⓘ thresholds & notes** (or any stage box) for the creek's full threshold list, what the levels mean,
and gauge notes.

**Creek alert strip:** when any creek reaches a flood level (or a rain trigger is met), a colored strip
appears under the NWS bar on every tab naming the creek, and the **Creeks** tab button turns the same color.
Tapping the strip opens that creek. These are levels on OneShoreline's creek gauges, not NWS alerts, and the
strip says "level" to keep that distinction clear. When a creek first reaches Flood Warning, the screen
switches to that creek on its own; people can tap back. (Turn that off with
`CREEK_AUTO_SWITCH_AT_WARNING = false`.) The strip never shows for an offline gauge or delayed data, so an
old reading can't raise an alarm.

If a gauge hasn't reported for a while (12 hours for gauges that report when the level changes, 3 hours for
gauges that report on a schedule), it shows **"Gauge may be offline"** with the last report time instead of
presenting an old reading as current.

**Changing a threshold, creek, gauge, MHHW, a setting or wording:** edit the table in the `lookups/` folder (see
`lookups/README.md`). Creek, gauge and threshold changes reach the kiosk, phone pages, home page and map on the next
data run (about 5 minutes after you commit); MHHW, settings and wording within about 10 minutes (the kiosk re-reads
them every 30 minutes). A mistake never blanks the screens: the job keeps the last good settings and shows the
problem row in the Actions tab, and the kiosk shows "⚠ Settings file problem" in its bottom bar.

### How the creek data gets to the kiosk (one-time setup)

OneRain doesn't let web pages on other sites read its data, and its data export needs a login, so a
scheduled job in this repo reads the readings from each sensor's **public** OneRain page (the same page
anyone can see without logging in):

- `scripts/fetch_onerain.py` reads the last 48 hours for every creek gauge in `lookups/creek_gauges.csv` from their public pages, plus
  each sensor's most recent reading (so an offline gauge shows when it last reported).
- `.github/workflows/onerain.yml` runs that script about every 5 minutes and publishes the result to a
  separate branch named **`data`** (replaced each time, so it doesn't add commits to your main branch).
- The kiosk reads `https://raw.githubusercontent.com/OneShorelineSMC/oneshorelinefews/data/creeks.json`.
- The same job also runs `scripts/fetch_sites.py` every third run (about every 15 minutes), which reads every
  public site for the **Map** tab and publishes `sites.json` on the same branch. A problem with the map
  download never holds up the creek data.

To turn it on:

1. Upload the files to the repo **with their folders**: the `lookups/` folder, `scripts/creek_config.py`,
   `scripts/fetch_onerain.py`, `scripts/fetch_sites.py` and `.github/workflows/onerain.yml`. (On GitHub: Add file → Create new file, and type the full path,
   e.g. `.github/workflows/onerain.yml`, then paste the contents.)
2. Go to the repo's **Actions** tab. If GitHub asks, click to enable workflows.
3. Click **Fetch OneRain data** → **Run workflow** to run it once now.
4. After it finishes (green check, under a minute), a **`data`** branch with `creeks.json` should appear
   in the branch list. The kiosk's creek tab fills in within a few minutes.

Things to know:

- **Timing:** GitHub runs scheduled jobs *about* every 5 minutes, sometimes 10–15 minutes late when
  GitHub is busy. The creek data on the kiosk can lag OneRain by that much. If the data file is more than
  30 minutes old, the creek tab shows **"Creek data delayed"**.
- **60-day rule:** GitHub automatically pauses scheduled jobs in a public repository after 60 days with no
  activity in the repo. If the creek tab shows "Creek data delayed" for a long time, check the Actions tab;
  if the job was paused, there will be a button to re-enable it. Any commit to the repo also resets the clock.
- **If a download fails**, the job keeps the previous data, so the screen never goes blank. Failures show
  as red marks in the Actions tab.
- **If OneRain redesigns its sensor pages,** the script may stop finding readings. The Actions log shows
  how many readings it found for each sensor on every run.
- **Creeks, gauges and flood thresholds** are all in the `lookups/` folder (`creeks.csv`, `creek_gauges.csv`, `thresholds.csv`).

## Changing settings

**MHHW, the NOAA forecast rules, "higher than predicted" call-outs, gauge-offline timing, the QR code links and all
wording** are in the `lookups/` folder (`tide_stations.csv`, `settings.csv`, `display_text.csv`; see
`lookups/README.md`), shared with the phone pages. Kiosk display settings are near the top of the `<script>` section
in `ShorelineKiosk.html`:

| Setting               | Default | Meaning                                        |
|-----------------------|---------|------------------------------------------------|
| `TIDE_STATION`        | 9414523 | The station on the Bay Tides tab (Redwood City) |
| `PAST_DAYS`           | 7       | Days of measured water level compared with predictions |
| `MODEL_EVERY_MIN`     | 60      | How often the NOAA model forecast is downloaded |
| `NWS_OFFICE`          | MTR     | NWS office whose forecast discussion is checked for tide notes |
| `AFD_EVERY_MIN`       | 30      | How often the forecast discussion is checked    |
| `TIDE_DAYS_EVERY_HOURS` | 6     | How often that file is re-read                  |
| `DAYS`                | 7       | Days of predicted tides                        |
| `STALE_AFTER_MIN`     | 90      | When the "out of date" warning appears         |
| `DETAIL_TIMEOUT_SEC`  | 45      | When detail screens close on their own         |
| `RELOAD_AT_HOUR`      | 3       | Hour of the daily reload                       |
| `CREEK_DATA_URL`      | data branch file | Where the creek tab reads its data      |
| `CREEK_PAST_HOURS`    | 36      | Hours of history on the creek tab graphs        |
| `CREEK_AHEAD_HOURS`   | 12      | Hours of predicted tide after "now"             |
| `CREEK_AUTO_SWITCH_AT_WARNING` | true | Switch to the creek tab when the creek reaches Flood Warning |
| `SITES_URL`           | data branch file | Where the Map tab reads its data        |
| `CREEK_RETURN_MIN`    | 5       | A single creek returns to the All creeks summary after this long (0 = stay) |
| `PIXEL_SHIFT_MIN`     | 10      | How often the picture shifts slightly (burn-in protection; 0 = off) |
| `PIXEL_SHIFT_PX`      | 2       | How far it shifts, in pixels                    |
| `ROTATE_SECONDS`      | 0       | Switch tabs automatically (0 = off)             |
| `TAB_RETURN_MIN`      | 0       | Return to Bay Tides after this long on the creek tab (0 = off) |
| `ABOUT_RETURN_SEC`    | 120     | About tab returns to Bay Tides after this long  |
