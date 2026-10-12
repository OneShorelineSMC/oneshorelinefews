# Shoreline Kiosk – Raspberry Pi setup

Runs `ShorelineKiosk.html` full screen on a Raspberry Pi with a 7" 800×480 touchscreen.
The page lives on GitHub Pages like the dashboard widgets, so updating the kiosk is just a commit to the repo.

Kiosk URL:

```
https://fews.oneshoreline.org/ShorelineKiosk.html
```

Options you can add to the end of the URL:

| Option      | Effect                                                    |
|-------------|-----------------------------------------------------------|
| `?theme=dark` | Dark background – easier on the eyes in a dim EOC        |
| `?cursor=1`   | Show the mouse pointer (handy when previewing on a computer) |
| `?tab=creek`  | Start on the San Bruno Creek tab                          |
| `?rotate=30`  | Switch between Bay Tides and San Bruno Creek every 30 seconds |
| `?tab=map`    | Start on the Map tab                                      |
| `?tab=about`  | Start on the About tab                                    |
| `?tab=disclaimer` | Start on the Disclaimer tab                           |

## Preview on a computer first

Open the kiosk URL with `?cursor=1` in any browser. The layout scales to fit the window, so it looks the
same as on the 7" screen. Click the alert bar or a station panel to see the touch screens.

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

## 3. Start the kiosk automatically

Open a terminal and run:

```bash
mkdir -p ~/.config/labwc
nano ~/.config/labwc/autostart
```

Add this line (all on one line), then save with Ctrl+O, Enter, Ctrl+X:

```bash
chromium --kiosk --noerrdialogs --disable-infobars --check-for-update-interval=31536000 --incognito "https://fews.oneshoreline.org/ShorelineKiosk.html" &
```

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
  switch between the Bay Tides and San Bruno Creek tabs.

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
- **Alert levels** are only shown where thresholds have been entered: currently San Bruno Creek at First
  Avenue. To add more, edit `THRESHOLDS` near the top of `scripts/fetch_sites.py`.

## About tab

The **About** button shows what each tab means, an "in an emergency, call 911" reminder, OneShoreline's
contact details (phone, email, website, address), and two QR codes people can scan with their phones:
**Contact OneShoreline** and **Get alerts: SMC Alert**. It returns to Bay Tides on its own after 2 minutes.
`?tab=about` at the end of the kiosk URL opens it directly (handy for checking the QR codes).

## Disclaimer tab

The **Disclaimer** button shows OneShoreline's data disclaimer (informational purposes only; thresholds are
approximate; actual conditions may vary) and "In an emergency, call 911". Like About, it returns to Bay Tides
on its own after 2 minutes and isn't part of the automatic tab rotation.

## San Bruno Creek tab

The buttons at the bottom of the screen switch between **Bay Tides** and **San Bruno Creek**.
The NWS alert bar stays at the top on both tabs.

The creek tab shows, all on one time axis (last 36 hours plus the next 12 hours of predicted tide):

- **Rain per hour** at First Avenue and San Bruno Mountain (bars), with 1-hour and 24-hour totals
- **San Bruno Creek stage at First Avenue**, with the Flood Monitoring (2.40 ft), Flood Watch (3.60 ft) and
  Flood Warning (4.80 ft) lines. The current stage is colored by the highest threshold it has passed.
- **Alameda tide**, measured and predicted. The creek at First Avenue rises and falls with the tide, so
  this shows whether a rise in the creek is coming from rain, the tide, or both.

**Creek alert strip:** when the creek reaches Flood Monitoring (2.40 ft), Flood Watch (3.60 ft) or Flood
Warning (4.80 ft), a yellow, orange or red strip appears under the NWS bar on every tab, and the
**San Bruno Creek** tab button turns the same color. Tapping the strip opens the creek tab. These are levels
on OneShoreline's creek gauge, not NWS alerts, and the strip says "level" to keep that distinction clear.
When the creek first reaches Flood Warning, the screen switches to the creek tab on its own; people can tap
back to Bay Tides. (Turn that off with `CREEK_AUTO_SWITCH_AT_WARNING = false`.) The strip never shows for
an offline gauge or delayed data, so an old reading can't raise an alarm.

If the creek gauge hasn't reported for 12 hours, the screen says **"Gauge may be offline"** and shows when
the last report was, instead of presenting an old reading as current.

### How the creek data gets to the kiosk (one-time setup)

OneRain doesn't let web pages on other sites read its data, and its data export needs a login, so a
scheduled job in this repo reads the readings from each sensor's **public** OneRain page (the same page
anyone can see without logging in):

- `scripts/fetch_onerain.py` reads the last 72 hours for the three sensors from their public pages, plus
  each sensor's most recent reading (so an offline gauge shows when it last reported).
- `.github/workflows/onerain.yml` runs that script about every 5 minutes and publishes the result to a
  separate branch named **`data`** (replaced each time, so it doesn't add commits to your main branch).
- The kiosk reads `https://raw.githubusercontent.com/OneShorelineSMC/oneshorelinefews/data/sanbruno.json`.
- The same job also runs `scripts/fetch_sites.py` every third run (about every 15 minutes), which reads every
  public site for the **Map** tab and publishes `sites.json` on the same branch. A problem with the map
  download never holds up the creek data.

To turn it on:

1. Upload the files to the repo **with their folders**: `scripts/fetch_onerain.py`,
   `scripts/fetch_sites.py` and `.github/workflows/onerain.yml`. (On GitHub: Add file → Create new file, and type the full path,
   e.g. `.github/workflows/onerain.yml`, then paste the contents.)
2. Go to the repo's **Actions** tab. If GitHub asks, click to enable workflows.
3. Click **Fetch OneRain data** → **Run workflow** to run it once now.
4. After it finishes (green check, under a minute), a **`data`** branch with `sanbruno.json` should appear
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
- **Sensors** are listed at the top of `scripts/fetch_onerain.py`. Flood thresholds are `STAGE_THRESHOLDS`
  in `ShorelineKiosk.html`.

## Changing settings

Near the top of the `<script>` section in `ShorelineKiosk.html`:

| Setting               | Default | Meaning                                        |
|-----------------------|---------|------------------------------------------------|
| `STATIONS`            | Redwood City, Alameda | NOAA station IDs, names, and MHHW (ft NAVD88) |
| `HISTORY_HOURS`       | 48      | Hours of measured water level on the graphs    |
| `DAYS`                | 7       | Days of predicted tides                        |
| `STALE_AFTER_MIN`     | 90      | When the "out of date" warning appears         |
| `DETAIL_TIMEOUT_SEC`  | 45      | When detail screens close on their own         |
| `RELOAD_AT_HOUR`      | 3       | Hour of the daily reload                       |
| `CREEK_DATA_URL`      | data branch file | Where the creek tab reads its data      |
| `STAGE_THRESHOLDS`    | 2.40 / 3.60 / 4.80 ft | Flood Monitoring / Watch / Warning lines |
| `CREEK_PAST_HOURS`    | 36      | Hours of history on the creek tab graphs        |
| `CREEK_AHEAD_HOURS`   | 12      | Hours of predicted tide after "now"             |
| `GAUGE_QUIET_HOURS`   | 12      | Silence after which the creek gauge "may be offline" |
| `CREEK_AUTO_SWITCH_AT_WARNING` | true | Switch to the creek tab when the creek reaches Flood Warning |
| `SITES_URL`           | data branch file | Where the Map tab reads its data        |
| `SITE_QUIET_HOURS`    | 24      | Silence after which a map site shows gray ("not reporting") |
| `ROTATE_SECONDS`      | 0       | Switch tabs automatically (0 = off)             |
| `TAB_RETURN_MIN`      | 0       | Return to Bay Tides after this long on the creek tab (0 = off) |
| `CONTACT_URL`         | OneShoreline contact page | Where the "Contact OneShoreline" QR code points |
| `ALERT_SIGNUP_URL`    | SMC Alert page | Where the "Get alerts" QR code points       |
| `ABOUT_RETURN_SEC`    | 120     | About tab returns to Bay Tides after this long  |
