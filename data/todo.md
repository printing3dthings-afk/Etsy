# OnBrandCraftz — Master TODO List
*Last updated: 2026-06-03*

---

## 🔴 YOUR ACTIONS (only you can do these)

### Urgent (blocks automation)

| # | Task | Time | Why It's Blocked |
|---|---|---|---|
| 1 | **Top up OpenAI billing** — platform.openai.com → Billing → Add $100, raise hard limit, enable auto-recharge | 5 min | Blocks all SVG generation, photo generation, new planner creation |
| 2 | **Add Pinterest Client ID to .env** — Pinterest Developer Console → your app → App ID → `PINTEREST_CLIENT_ID=<id>` in `.env` | 5 min | Pinterest auto-posting currently broken (token can't refresh without it) |
| 3 | **Run Pinterest OAuth** (after #2) — `python tools/pinterest_oauth.py` | 2 min | Unlocks Pinterest auto-posting |
| 4 | **Run TikTok OAuth** — `python tools/tiktok_oauth.py` | 5 min | Unlocks TikTok auto-posting |

### New platform accounts (free — each unlocks a new revenue stream)

| # | Task | Time | Revenue Potential |
|---|---|---|---|
| 5 | **Create Amazon KDP account** — kdp.amazon.com → Sign in with Amazon → complete seller setup → run `python tools/kdp_publisher.py --all` to prep submissions | 15 min | $500–2,000/mo once ranked — Amazon planner market is 20× Etsy's |
| ~~6~~ | ~~Create Printify account~~ | ~~Done~~ | ✅ **COMPLETE** — 52 products live, 156 variants, orders auto-route |
| 7 | ~~**Create Mailchimp account**~~ | Deferred | Not free — revisit when monthly revenue justifies the cost |
| 8 | **Create Instagram app** — developers.facebook.com → New App → Business type → add Instagram Graph API → add to `.env`: `INSTAGRAM_APP_ID=`, `INSTAGRAM_APP_SECRET=`, `INSTAGRAM_USER_ID=`, `INSTAGRAM_ACCESS_TOKEN=` | 20 min | Visual platform — kawaii planners/stickers perform very well on Instagram Reels |

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

## CURRENT SHOP HEALTH (2026-06-02)

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
