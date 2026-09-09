# OnBrandCraftz — Master TODO List
*Last updated: 2026-09-08*

---

## 🔴 YOUR ACTIONS (only you can do these)

### Urgent (blocks automation)

| # | Task | Time | Why It's Blocked |
|---|---|---|---|
| 1 | **Top up OpenAI billing** — platform.openai.com → Billing → Add $100, raise hard limit, enable auto-recharge | 5 min | Blocks all SVG generation, photo generation, new planner creation |
| 2 | **Pinterest — resubmit with demo** — demo video auto-generated (`data/social/videos/pinterest_demo_resubmission.webm`, ~91 sec, via `tools/record_pinterest_demo.py`) and privacy policy is now hosted publicly at `<your Railway app URL>/static/privacy.html` (file copied to `tools/api_server/static/privacy.html`, deploys with the next push). **Remaining manual steps only:** (a) upload the `.webm` to YouTube as unlisted and copy the link, (b) go to developers.pinterest.com and resubmit the app with the video link + the static privacy URL above. When approved: copy App Secret from developers.pinterest.com into `.env` then run `python tools/pinterest_oauth.py` | 10 min | Trial denied twice — needs mockup video per Pinterest community guidance |
| 3 | **Photograph filament tags** — send photos of filament spools tonight so I can log them into `tools/filament_tracker.py`. Include the spool used for OBC-3DRK-002 (Skinny Can Koozie) | Tonight | Needed to track COGS per product |
| 4 | **Run TikTok OAuth** — `python tools/tiktok_oauth.py` | 5 min | Unlocks TikTok auto-posting |
| 19 | **Set up Gmail relay for digital delivery emails** — Microsoft killed basic-auth/app-password SMTP for personal Outlook.com mailboxes (Sept 2024), so `SMTP_PASSWORD` can't be an Outlook app password. Create or use an existing Gmail account → Google Account → Security → 2-Step Verification → App passwords → generate one → send the Gmail address + app password to Claude to add to `.env` as `SMTP_USER`/`SMTP_PASSWORD` (host becomes `smtp.gmail.com`). Customers still see OnBrandCraftz / Printing3dthings@outlook.com as the reply-to. | 10 min | Unlocks `tools/digital_delivery_tools.py` — direct email delivery of corrected/replacement files to customers (e.g. Christina Curry's wrong-file order) |

### New platform accounts (free — each unlocks a new revenue stream)

| # | Task | Time | Revenue Potential |
|---|---|---|---|
| 5 | **Create Amazon KDP account** — kdp.amazon.com → Sign in with Amazon → complete seller setup → run `python tools/kdp_publisher.py --all` to prep submissions | 15 min | $500–2,000/mo once ranked — Amazon planner market is 20× Etsy's |
| ~~6~~ | ~~Create Printify account~~ | ~~Done~~ | ✅ **COMPLETE** — 52 products live, 156 variants, orders auto-route |
| 7 | ~~**Create Mailchimp account**~~ | Deferred | Not free — revisit when monthly revenue justifies the cost |
| 8 | **Create Instagram app** — developers.facebook.com → New App → Business type → add Instagram Graph API → add to `.env`: `INSTAGRAM_APP_ID=`, `INSTAGRAM_APP_SECRET=`, `INSTAGRAM_USER_ID=`, `INSTAGRAM_ACCESS_TOKEN=` | 20 min | Visual platform — kawaii planners/stickers perform very well on Instagram Reels |
| 20 | **Create Facebook Page + app credentials** — `tools/facebook_api.py` is built and wired into the new Studio tab's "Post to Facebook" button, but has zero credentials yet (no Facebook Page exists for OnBrandCraftz at all). Can reuse the same Meta App created for Instagram above (#8) — just add the "Facebook Pages" product, connect/create the OnBrandCraftz Page, and add to `.env`: `FACEBOOK_APP_ID=`, `FACEBOOK_APP_SECRET=`, `FACEBOOK_PAGE_ID=`, `FACEBOOK_PAGE_ACCESS_TOKEN=`. See `tools/facebook_api.py` header for full step-by-step setup. | 20 min | Unlocks video posting to Facebook directly from the Studio tab |

### Review and publish new draft listings (I created these today)

| # | Task | Time | Notes |
|---|---|---|---|
| ~~9~~ | ~~Publish 11 commercial license listings~~ | ~~Done~~ | ✅ **COMPLETE** — 11 listings live ($24.99 SVG + $12.99 stickers) |
| 10 | **Review coloring pages** — `data/digital_products/coloring_pages/` — 54 PNG files + 11 ZIP sets ready. Check quality then run `python tools/upload_coloring_pages.py` (once built) | 5 min | 54 new listings at $3.99 each from existing art. Zero new design cost |
| 11 | **Review digital paper packs** — `data/digital_products/digital_paper/` — 60 pattern files + 12 theme ZIPs. Check quality then stage for listing | 5 min | 12 new listings at $4.99 each from brand color palettes. Zero cost |

### When you have 5+ reviews on any planner listing

| # | Task | Time | Notes |
|---|---|---|---|
| 12 | **Bump Etsy Ads to $5/day** — Shop Manager → Marketing → Etsy Ads → increase budget | 2 min | Stay at $1.30/day until first 5 reviews |

### Low urgency (set-and-forget, one-time)

| # | Task | Time | Notes |
|---|---|---|---|
| 13 | **Install dashboard desktop icon** — run `setup_desktop_shortcut.bat` once on your Windows machine | 1 min | Already built — drops a purple shopping bag icon on Desktop that auto-refreshes from Etsy |
| 14 | **Add shop video** — Etsy Shop Manager → any active planner listing → Add Video → 5–15 sec screen recording of planner in use | 10 min | Listing video = algorithm ranking boost |
| 15 | **Connect Buffer.com for TikTok** (after #4) — Buffer.com free account → connect TikTok → schedule from `data/tiktok_content_calendar.json` | 10 min | 30 days of content already written |
| 16 | **Test SMTP from your machine** — run `python tools/ads_monitor.py` and confirm email arrives at Printing3dthings@outlook.com | 5 min | SMTP port 587 is blocked in this environment, works fine from Windows |
| 17 | **Etsy re-auth** — due ~September 1, 2026 — run `python tools/etsy_oauth.py` | 2 min | OAuth refresh token expires 90 days after last auth |
| 20 | **Measure your Stanley cup** — three numbers with calipers, for the Stanley snack tray design: (1) lid **outer diameter** at its widest, where a tray would rest, (2) **straw outer diameter**, (3) **straw offset from centre** — centre of lid to centre of straw. Send all three. | 2 min | Stanley publishes the bounding box and base diameter but **not** the lid OD or straw diameter, and no retailer lists them. "Fits a Stanley" is a compatibility claim — CLAUDE.md's top rule makes an untested one a hard stop, so this cannot be guessed |
| 18 | **Back-to-school keywords** — by July 4, 2026 — run `python tools/seasonal_keywords.py --push` | 5 min | Updates all planner keywords for back-to-school peak season |

---

## 🔎 FINAL REVIEW BEFORE PUBLISHING (listings I generate, you approve)

Every listing I generate goes into `draft` state. You review it, then run:
```bash
python tools/approve_listing.py --list-drafts          # see what's waiting
python tools/approve_listing.py --listing-id <ID>      # review one listing
python tools/approve_listing.py --listing-id <ID> --yes  # approve and publish
```

**Drafts waiting for your review right now:**
- None — all current drafts have been published ✅

Once OpenAI billing is topped up, I will generate and stage these for your review:
- 5 SVG bundles (floral_wreath, dark_floral, western completion, retro_groovy, mama_scripts)
- DP1030 ADHD Planner (Matcha Serenity)
- DP1033 Teacher Planner 2026-2027 (Sunflower Studio)
- Wall art mockup photos for 20 listings with fewer than 5 photos
- Coloring page listing images (54 pages → need lifestyle mockups)
- Digital paper pack listing images (12 packs → need flat lay mockups)

---

## 📋 INCOMING REVIEWS (respond personally — never use a template for 4 stars and below)

Check for new reviews daily:
```bash
python tools/review_monitor.py
```
Draft responses auto-saved to `data/message_drafts/review_responses_YYYY-MM-DD.json`.
**4-star and below reviews need a personal response from you.** 5-star responses are pre-drafted.

---

## 🤖 MY QUEUE (blocked on OpenAI billing — runs automatically once topped up)

### Priority 1 — SVG Bundles (5 bundles x 20 designs)
**Est. cost: ~$20 total | Est. revenue once published: $50-200/mo**
```bash
python tools/generate_svg_designs.py western        # resume from design 13/20
python tools/generate_svg_designs.py floral_wreath  # 0/20
python tools/generate_svg_designs.py mama_scripts   # 0/20
python tools/generate_svg_designs.py retro_groovy   # 0/20
python tools/generate_svg_designs.py dark_floral    # 0/20
python tools/publish_svg_bundle.py --all            # stages for your review
```

### Priority 2 — Fix Listings with Too Few Photos (20 listings flagged)
**Report: `data/reports/listing_health_2026-06-02.txt`**
```bash
python tools/generate_wall_art_mockups.py  # generates all 10 photos per listing
```

### Priority 3 — New Digital Planners
```bash
python tools/generate_planner.py DP1030  # ADHD Planner (Matcha Serenity)
python tools/generate_planner.py DP1033  # Teacher Planner (Sunflower Studio)
```

### Priority 4 — Sublimation (Teacher Life + Nurse Life already have mockups)
```bash
python tools/publish_sublimation_pack.py --bundle teacher_life
python tools/publish_sublimation_pack.py --bundle nurse_life
```

### Priority 5 — Listing Photos for New Products (zero-cost products ready to list)
```bash
python tools/generate_coloring_page_mockups.py  # 54 coloring pages need mockup photos
python tools/generate_digital_paper_mockups.py  # 12 paper packs need flat lay photos
```

### Priority 6 — Sticker Pack Listings
```bash
python tools/upload_sticker_listings.py
```

---

## 📋 BACKLOG (future work, no deadline)

### 3D print designs
*Added 2026-09-08. There was no 3D-print queue in this file before; design work
was tracked only in `openscad_models/*_PRINTING.md` per product, which records
what was built and not what is still wanted.*

| Design | Status | Blocked on |
|---|---|---|
| **Stanley-style tumbler snack tray** — sits on the lid of a Quencher-type cup, straw hole through the middle, self-centring conical seat underneath so it fits a *range* of tumbler diameters rather than one model, 3–4 shallow snack compartments. Same six-petal flower language as the sauce trays. | Concept approved by Scott 2026-09-08, geometry **not started** | The three measurements in YOUR ACTIONS #20. Also needs a concept pitch before any `.scad` is written, per the standing rule |
| **Tighter sauce-cup fit** — the 2oz cavity has a constant 3.33mm radial gap (6.7mm across); the cup is held by being 18mm down a well, not by contact. A real nesting fit needs a 55.2mm mouth instead of 61.1mm, which visibly shrinks every well and wants `ring_r` re-solved with it. | Measured and documented 2026-09-08, **not changed** | Scott's call — it is a look change to an approved design, not a bug fix |
| **Personalized desk name plate + phone dock** — ~150 × 45 × 55mm wedge, the name across the face as a flush two-colour inlay, a ramped slot behind it holding a phone at reading angle, pen groove along the top. Prints face-down on smooth PEI so the name side comes off mirror-flat (the `snap_box` trick). ~2.5h, ~55g, two colours, no supports. New-job / graduation / teacher / coworker gifts. | Pitched 2026-09-09, **not chosen, nothing written** | Scott picking it. Lowest risk of the three — every technique in it is already proven on a real print |
| **Rotating desk carousel organizer** — ~95mm dia × 85mm, three tiers of angled pockets on a print-in-place thrust bearing, comes off the plate already turning. ~3h, ~60g, one plate. Nothing in the catalogue moves, and a spinning object films in three seconds — external traffic is a confirmed Etsy ranking signal. | Pitched 2026-09-09, **not chosen, nothing written** | Scott picking it. Highest-value technique risk: same mechanism class that fused the keychain twice, so a 20-minute bearing coupon gets printed before any 3-hour run (see Technique 57 — design to the *deposited-bead* gap, not the modelled one) |
| **Self-watering planter** — ~110mm dia × 120mm, inner pot with a wick stem sitting in an outer reservoir, water-level slot so the refill point is visible. Two objects, one plate, PETG for moisture per the filament table. ~4h, ~90g. The upsell to the live Ribbed Planter Pot — same audience, higher price, and the only one of the three with proof the buyer already exists. | Pitched 2026-09-09, **not chosen, nothing written** | Scott picking it. Highest product risk: a planter that seeps is a bad review, and watertightness rides on wall count and flow calibration as much as geometry. Needs a 24h fill test on paper towel before it ever lists |
| **Phyllotaxis luminary** — ~95mm dia × 140mm. Several hundred raised lenses on the golden-angle spiral (sunflower-seed packing); each lens is a thin spot in the wall, so backlit it becomes a field of hundreds of glowing points that reorganise into new spirals as you walk past. Texture **raised outward**, not cut in — there is a cavity, so depth is wall-limited (Technique 52's option 1). Detail target **rugosity ≥1.8**. ~4.5h, no supports, every lens self-supporting by construction. | Pitched 2026-09-09, **not chosen, nothing written** | Scott picking it. Above the usual 4h ceiling — justified at lamp pricing, but say so rather than hide it |
| **Geode tea light holder** — ~85mm dia × 75mm. Fractured rock exterior from a layered noise field, split down one side opening onto an interior lined with faceted crystal facets; candlelight escapes through the crack and catches every facet. The only one of the three where the *inside* is the payoff. Detail target **rugosity ≥1.5**, which the noise field gives free. | Pitched 2026-09-09, **not chosen, nothing written** | Scott picking it. Lowest risk of the three at ~2h, and the buyer is already proven — two tea light holders are live |

**Pitched and deliberately not included (2026-09-09):** a hinged keepsake/ring
box with a personalised lid inlay. Dropped before pitching because `snap_box`
already ships a two-piece box with a flush multi-colour logo inlay in the lid —
a hinge is a real difference, but the product it sells is the same one.

**Not on this list on purpose:** adding the straw hole to the existing 6-well
sauce tray. Measured 2026-09-08 — the tray's solid centre is only 73mm across
and a Quencher rim needs to land at 98mm, so the rim falls where the wells
already are. Moving the wells out means `ring_r` 63 → 78, which scales the tray
to ~251mm (the bed is 256) and ~11.8 hours. A separate, smaller product is the
right answer.

### 3D print tooling — getting a file to the P1S
*Written up 2026-09-08 so this can be decided later without re-deriving it.
Today the answer is **no, Frank cannot send a print**, and that is by design,
not an oversight — see "Why it cannot today" below.*

**Option A — drop the file where Bambu Studio can see it.** *Small, low risk.*
The relay already has `local_write_binary_file`, which writes into an Allowed
Folder on Scott's machine. Point it at a folder, and a finished `.3mf` lands
there ready to open — no downloading files out of chat. Scott still slices and
still presses Print. This uses an existing, already-scoped capability rather
than opening any new path to the printer. Roughly an afternoon.

**Option B — real job submission.** *Bigger, and it has a blocker that is not
about permissions.* Two steps on a P1S in LAN mode:

1. **Upload** the file to the printer over FTPS (implicit TLS, port 990, user
   `bblp`, password = the printer's Access Code).
2. **Publish** an MQTT command referencing it.

Step 2 is **already proven in this repo** — `tools/relay/bambu_p1s_bridge.py`
connects on MQTT/TLS 8883 as `bblp` with the Access Code and publishes to
`device/{SERIAL}/request` every second. The command channel exists and works;
only the payload differs.

Step 1 is **NOT verified here.** The FTPS details above are community-
documented, the same status the camera protocol had before the bridge checked
it against a real open-source reference (see the "Camera relay" comment block
in the bridge). Verify it against a real printer before trusting it.

**The real blocker is slicing, not access.** A P1S expects a Bambu-flavoured
3MF carrying its own metadata and AMS handling. This container has
`prusa-slicer`, which is fine for the honest time/cost estimates in the
`*_PRINTING.md` notes, but its output is not a drop-in for a P1S — sending it
would likely fail or print badly. Real submission wants Bambu Studio or Orca
doing the slice on Scott's machine, which is where Option A already puts the
file anyway.

**Why it cannot today, verified in code:**
- The bridge publishes exactly one MQTT message ever: `{"pushing": {"command":
  "pushall"}}` — a status request. No upload, no print command.
- `_LOCAL_EXEC_WHITELIST = {"dir_listing", "disk_usage"}`, with the comment
  *"Step 1 scope, Scott's locked-in decision: read-only diagnostics only."* The
  relay re-checks against its own hardcoded copy rather than trusting the
  server's, so a compromised Frank could not widen it.
- Frank is on Railway and has no route to the home LAN at all.
- Starting a print is a physical, irreversible action on a machine with hot
  parts — the class the Autonomy Boundaries section gates. Even built, it
  should stage for approval rather than fire, same as an Etsy publish.

**Recommendation:** Option A on its own merits. Option B only if unattended
queueing turns out to be worth it, and never without the slicing question
answered first.

### More planners
| ID | Product | Theme | Season |
|---|---|---|---|
| DP1031 | Undated Life Planner Evergreen | Sage Garden | Evergreen |
| DP1032 | Dark Mode Bundle | Midnight Kawaii | Evergreen |

### More SVG bundles
Faith and Inspirational, Nurse and Healthcare, Teacher Life, Sports Mom

### More sublimation niches
Faith/Christian, Sports Mom, Seasonal (Christmas, Valentine's)

### Planner upgrades (competitors have these, we don't yet)
- 5+ cover options per planner (competitors have 100+; we have 1)
- Daily pages for DP1026 + DP1027 (most requested feature)
- Multiple weekly layout options (horizontal + vertical)

### Teachers Pay Teachers (once DP1033 Teacher Planner is built)
- Create TpT seller account → tpt.com/Store/create
- Run `python tools/tpt_publisher.py` (built and ready)
- DP1027 Student Planner and DP1033 Teacher Planner both qualify

---

## COMPLETED TODAY (2026-06-02)

### Revenue-generating automations built this session
- [x] **Weekly market research** — runs Saturday 7am, searches 23 Etsy queries, Claude synthesizes trends into design intelligence
- [x] **Seasonal sales scheduler** — auto-triggers holiday coupon codes + emails Scott reminders for 8 annual sale windows
- [x] **54 coloring pages generated** — converted existing wall art to line-art B&W PNGs using PIL (zero AI cost), 11 ZIP sets ready
- [x] **60 digital paper patterns generated** — 12 brand themes × 5 pattern types, 3600×3600px at 300 DPI, 12 ZIPs ready
- [x] **11 commercial license draft listings created** — $24.99 SVG + $12.99 sticker commercial use licenses on Etsy (awaiting your review)
- [x] **KDP publisher built** — prep tool for Amazon KDP physical planner books. Account + `python tools/kdp_publisher.py --all` → submit
- [x] **Printify integration built** — 55 wall art files queued for physical POD. Account + `python tools/printify_publisher.py --submit-all` → live
- [x] **Commercial license tool** — `tools/commercial_license_tool.py` creates companion license listings for any product

### Earlier today
- [x] 14 listing titles fixed — added "Instant Download" within 70-char limit
- [x] tools/approve_listing.py built — review and approve draft listings before they go live
- [x] tools/listing_performance_monitor.py built — daily listing health audit
- [x] tools/review_monitor.py built — daily review check + auto-draft responses
- [x] tools/generate_dashboard.py + live HTML dashboard built
- [x] Desktop icon launcher (Windows) — setup_desktop_shortcut.bat
- [x] Weekly report — $307/mo pace, 6% of $5,000 target

## COMPLETED PREVIOUSLY

- [x] Full Etsy API v3 client with OAuth, token refresh, rate limiting
- [x] Sublimation full pipeline — design gen, tumbler mockups, ZIP, publisher
- [x] Wall art mockup generator
- [x] SVG bundle generator — 5 bundles configured
- [x] Business pipeline — weekly run, quality gates
- [x] Health check, weekly report, decision log
- [x] Message autoresponder — drafts replies, emails digest
- [x] 4 digital planners live (DP1026-DP1029)
- [x] All 4 Planners Bundle live ($39.99)
- [x] Mom Life Sublimation Bundle live ($9.99)
- [x] 93 wall art / bundle listings active
- [x] 6 kawaii sticker pack listings live
- [x] Abandoned cart coupon COMEBACK10 (10% off)
- [x] Thank-you coupon THANKYOU15 (15% off)
- [x] Post-purchase message live (signed Scott, no emojis)
- [x] Pinterest 95 pins queued
- [x] TikTok 30-day content calendar built
- [x] Email lead magnet system built

---

## CURRENT SHOP HEALTH (2026-06-04)

| Metric | Value | Target | Status |
|---|---|---|---|
| Active listings | 93 | 100+ | Close |
| Draft listings awaiting review | 0 | 0 | ✅ All published |
| Weekly net revenue | $20.45 | $1,154/wk | 6% of target |
| Monthly pace | $307/mo | $5,000/mo | 6% of target |
| Listings with title issues | 0 | 0 | ✅ Fixed today |
| Listings with photo issues | 20 | 0 | Queued (needs OpenAI) |
| SVG bundles complete | 0/5 | 5/5 | Queued (needs OpenAI) |

**Revenue streams now live (as of 2026-06-03):**
- ✅ Commercial licenses live → +$200–500/mo from crafters who need commercial rights
- ✅ Printify physical prints live → 52 products × 3 sizes, +$200–800/mo
- ⏳ Coloring pages (waiting on OpenAI for mockup photos) → +$100–300/mo
- ⏳ Digital paper packs (waiting on OpenAI for mockup photos) → +$100–200/mo
- ⏳ KDP (deferred until Etsy has more sales) → +$500–2,000/mo
