# Flood reports: setup and staff review

People report flooding on **CommunityFloodReports.html** through an ArcGIS Survey123 form. OneShoreline staff review each report in ArcGIS Online. The data job then publishes **only the reports staff approved**, cleaned up, as a "Flood reports" layer on the sensor map.

```
Public (CommunityFloodReports.html)                ArcGIS Online (staff only)                       GitHub data job → public map
Survey123 form ── add only ──▶ source layer ◀── staff review view (edit)        
                                    │                                               
                                    └── approved-only view (read) ── API key ──▶ fetch_community_flood_reports.py ──▶ community_flood_reports.json
                                                                                   (staff summary, type, depth,
                                                                                    location rounded ~150 m,
                                                                                    photo only if approved)
```

Until steps 1–7 are done, nothing changes on the website: CommunityFloodReports.html says "Flood reporting isn't open yet" and the map has no reports layer.

## Design rules (why it's built this way)

- **Nothing reaches the public site without staff approval.** The public form can only *add* records. It can't read, change or delete them.
- **Fake approvals don't work.** Someone could send `review_status = approved` straight to the form's service. The data job therefore publishes a report only if ArcGIS's own "last edited by" field (editor tracking, set by ArcGIS, not by the sender) is a staff account listed in `REPORTS_STAFF_EDITORS`.
- **The reporter's words are never published.** The map shows the staff-written `public_summary`, the type and depth from fixed lists, and the date. Notes, contact details, exact points and account names stay in ArcGIS.
- **Locations are rounded** to a grid of about 170 m × 130 m, and reports outside San Mateo County are dropped.
- **Photos are private by default.** A photo is published only when staff set `publish_photo = yes`. It is re-encoded, which removes location, camera and time data, and shrunk to 1280 px.
- **Reports never change creek status or alerts.**
- **No bot check.** Esri doesn't offer a supported CAPTCHA for public Survey123 forms. Junk can fill the staff queue but can't reach the public site. In a spam flood, close the survey (step 8).

## 1. Create the survey (Survey123 website, web designer)

Create the survey while signed in as an **organization account that will outlive any one person**, such as a shared OneShoreline GIS account, not a personal one. Set each question's field name before the first publish; field names can't be changed afterwards. The data job needs these exact field names and choice values:

| # | Question (suggested wording) | Type | Field name | Choices: label → value | Required |
|---|---|---|---|---|---|
| 1 | Where is the flooding? | Map (point) | (the survey's location) | — | yes |
| 2 | When did you see it? | Date and time, default = now | `observed_at` | — | yes |
| 3 | What did you see? | Single choice | `report_type` | Water on a street or path → `street`; Water in or against a building → `building`; Road closed by water → `road_closed`; Creek over its banks → `creek`; Bay or ocean over the shoreline → `shoreline`; Something else → `other` | yes |
| 4 | About how deep? | Single choice | `depth` | Less than ankle-deep → `shallow`; Ankle- to knee-deep → `ankle_knee`; Above the knee → `above_knee`; Not sure → `unknown` | yes |
| 5 | Photo (optional) | Image, 1 photo | (attachment) | — | no |
| 6 | Anything else staff should know? | Multiline text, max 500 characters | `note` | — | no |
| 7 | Your phone or email, only if staff may contact you about this report | Single-line text | `contact` | — | no |
| 8 | (Note) | Note | — | Text: the same 911 and public-records sentences as the Report page | — |

Keep it short; people will fill it in on a phone in the rain. Don't add name or address questions.

## 2. Share the survey (Survey123 website → Collaborate)

- **Share survey → Who can submit to this survey?** Everyone (public).
- **What can submitters do?** **Only add new records.** This is the default; don't change it.
- **Share results → Who can view results?** Only the OneShoreline staff group. Never share the survey's source layer itself.

## 3. Add the staff fields and check editor tracking (ArcGIS Online)

Open the survey's **source hosted feature layer** (in the survey's folder) → **Data** → **Fields** → **Add**:

| Field name | Type | Length | Default | Use |
|---|---|---|---|---|
| `review_status` | String | 20 | `new` | `new`, `approved` or `rejected` (add a list of values) |
| `public_summary` | String | 300 | — | What the public map says, written by staff |
| `publish_photo` | String | 3 | `no` | `yes` or `no` (list of values) |
| `staff_note` | String | 500 | — | Internal only, never published |

Then go to the layer's **Settings** and make sure **"Keep track of who created and last updated features"** (editor tracking) is on. Survey123 normally turns it on. The data job won't publish anything without it.

Survey123 ignores fields it didn't create. Don't rename or delete the fields the survey created.

## 4. Staff review view

On the source layer, **Create View Layer** → name it "Flood reports – staff review":
- **Settings:** enable editing (update; delete too, for removing spam). Keep editor tracking on.
- **Sharing:** the staff group only.
- Open it in **Map Viewer** and save a web map, "Flood reports – review". Staff use the map and its attribute table, or Field Maps on a phone.

## 5. Approved-only view (what the website reads)

On the source layer, **Create View Layer** again → "Flood reports – approved (FEWS)":
- **View definition → filter:** `review_status` is `approved`.
- **View definition → fields:** turn off `note`, `contact` and `staff_note`. Keep `observed_at`, `report_type`, `depth`, `review_status`, `public_summary`, `publish_photo`, the editor tracking fields, ObjectID and GlobalID.
- **Settings:** editing **off**.
- **Sharing:** owner only. Not public, not shared with groups.
- Copy the view's layer URL. It ends in `/FeatureServer/0`.

## 6. API key for the data job

In ArcGIS Online: **Content → New item → Developer credentials → API key credentials**.
- **Item access:** grant access to the "approved (FEWS)" view only. No other privileges are needed.
- **Expiration:** set the longest allowed, up to 1 year. **Put a calendar reminder a week before it expires**; when it expires, the map stops updating new reports (old ones stay).
- Copy the key once; ArcGIS shows it only once.
- Changing item access later invalidates the key; generate a new one and update the GitHub secret.
- Your ArcGIS user type and role must allow creating developer credentials; ask your ArcGIS administrator if the option is missing.

## 7. Connect GitHub and the website

GitHub repo → **Settings → Secrets and variables → Actions**:

| Kind | Name | Value |
|---|---|---|
| Secret | `ARCGIS_API_KEY` | the key from step 6 |
| Variable | `REPORTS_LAYER_URL` | the view URL from step 5 (`https://services….arcgis.com/…/FeatureServer/0`) |
| Variable | `REPORTS_STAFF_EDITORS` | ArcGIS usernames allowed to approve, comma-separated (e.g. `jdoe_oneshoreline,asmith_oneshoreline`) |

Then in `lookups/display_text.csv`, set **`url_report_form`** to the survey's share link, `https://survey123.arcgis.com/share/<32-character item id>`. Only that kind of link is accepted.

**Test in the staff preview:**
1. Open `CommunityFloodReports.html?preview=1`, send a test report with a photo, and check the "Open the form in a new tab" link also works on a phone.
2. In the review map, set the test report to `approved`, write a `public_summary`, and set `publish_photo = yes`.
3. Within about 15 minutes, check `SiteMap.html?preview=1`: turn on **Flood reports**.
4. Set it back to `rejected` and confirm it disappears on the next run.
5. In the Actions tab, the step "Flood reports approved by staff" should say how many reports were and weren't published.

**Go public:** set `REPORTS_PUBLIC` to `1` in `lookups/settings.csv`. That adds the Report tab to the home page and map and shows the map layer to everyone.

## 8. Staff review guide

- **Approve** only reports that are plausible. Check against nearby gauges, the tide and other reports. Reject joke, abusive and duplicate reports.
- **Write the `public_summary`** as a short, factual description of the flooding: place and what was seen. Leave out names, house numbers, license plates and anything from the reporter that identifies a person. Links, emails and phone numbers are removed automatically, but don't rely on that.
- **Photos:** set `publish_photo = yes` only if the photo shows the flooding and no faces, license plates, house numbers or the inside of a home.
- **Contact:** use the reporter's contact only to follow up on that report.
- **Spam flood during a storm:** in the Survey123 website, **Settings → Close survey** (or schedule it closed). CommunityFloodReports.html keeps showing the form, but submissions are refused. Reopen when it's over, and bulk-reject the junk in the review map.
- **Retention:** decide how long reports are kept and delete older ones in ArcGIS. The public map already drops reports older than `REPORTS_MAX_AGE_DAYS` (180).
- **Public records:** reports sent to a public agency may be public records under the California Public Records Act. The form says so.

## Settings (`lookups/settings.csv`)

| Key | Default | Meaning |
|---|---|---|
| `REPORTS_PUBLIC` | 0 | 0 = Report tab and map layer only in the staff preview (`?preview=1`); 1 = everyone |
| `REPORTS_MAX_AGE_DAYS` | 180 | approved reports older than this (by date seen) aren't published |
| `REPORTS_MAX_PHOTOS` | 40 | at most this many photos are published at a time, newest first |

Wording: the `report_*` keys in `lookups/display_text.csv`. The type and depth labels there must stay in step with the survey's choice values above.

## Files

- `CommunityFloodReports.html`: the public page (911 warning, what happens to a report, public-records notice, the embedded form in a sandboxed frame).
- `scripts/fetch_community_flood_reports.py`: the data job step. `scripts/test_community_flood_reports.py` checks it against forged and hostile records, without network access.
- `SiteMap.html`: the "Flood reports" button and layer.
- `.github/workflows/onerain.yml`: runs the step every 15 minutes. A problem there never stops the creek data.
