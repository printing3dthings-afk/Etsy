# OnBrandCraftz — Master TODO List
*Last updated: 2026-06-02*

---

## 🔴 YOUR ACTIONS (only you can do these)

### Urgent (blocks automation)

| # | Task | Time | Why It's Blocked |
|---|---|---|---|
| 1 | **Top up OpenAI billing** — platform.openai.com → Billing → Add $100, raise hard limit, enable auto-recharge | 5 min | Blocks all SVG generation, photo generation, new planner creation |
| 2 | **Add Pinterest Client ID to .env** — Pinterest Developer Console → your app → App ID → `PINTEREST_CLIENT_ID=<id>` in `.env` | 5 min | Pinterest auto-posting currently broken (token can't refresh without it) |
| 3 | **Run Pinterest OAuth** (after #2) — `python tools/pinterest_oauth.py` | 2 min | Unlocks Pinterest auto-posting |
| 4 | **Run TikTok OAuth** — `python tools/tiktok_oauth.py` | 5 min | Unlocks TikTok auto-posting |

### When you have 5+ reviews on any planner listing

| # | Task | Time | Notes |
|---|---|---|---|
| 5 | **Bump Etsy Ads to $5/day** — Shop Manager → Marketing → Etsy Ads → increase budget | 2 min | Stay at $1.30/day until first 5 reviews |

### Low urgency (set-and-forget)

| # | Task | Time | Notes |
|---|---|---|---|
| 6 | **Test SMTP from your real machine** — `python tools/ads_monitor.py` and check if email arrives at Printing3dthings@outlook.com | 5 min | SMTP fails in this environment (network issue), needs test from your machine |
| 7 | **Etsy re-auth every 90 days** — next due ~September 1, 2026 — run: `python tools/etsy_oauth.py` | 2 min | Refresh token expires 90 days after last auth |
| 8 | **Back-to-school keyword update** — by July 4, 2026 — run: `python tools/seasonal_keywords.py --push` | 5 min | Updates keywords on planners + student-adjacent listings for back-to-school season |
| 9 | **Install dashboard desktop icon** — run `setup_desktop_shortcut.bat` (one time) — creates purple shopping bag icon on Desktop that opens the dashboard with fresh Etsy data on every click | 1 min | Already built, just needs to be run once on your Windows machine |
| 10 | **Add shop video** — Etsy Shop Manager → any active planner listing → Add Video → upload a 5–15 sec screen recording of planner in use | 10 min | Video in listing = ranking boost |
| 10 | **Connect Buffer.com for TikTok** (after #4) — go to Buffer.com (free), connect TikTok, schedule posts from `data/tiktok_content_calendar.json` | 10 min | 30 days of TikTok content already pre-written |
| 11 | **Email list (future)** — create free Mailchimp account → connect to `tools/email_leadmagnet.py` | 20 min | Lead magnet system already built, just needs Mailchimp API key |

---

## 🔎 FINAL REVIEW BEFORE PUBLISHING (listings I generate, you approve)

Every listing I generate goes into `draft` state. You review it, then run:
```bash
python tools/approve_listing.py --list-drafts          # see what's waiting
python tools/approve_listing.py --listing-id <ID>      # review one listing
python tools/approve_listing.py --listing-id <ID> --yes  # approve and publish
```

**Current draft listings:** None (check with `--list-drafts`)

Once OpenAI billing is topped up, I will generate and stage these for your review:
- 5 SVG bundles (floral_wreath, dark_floral, western completion, retro_groovy, mama_scripts)
- DP1030 ADHD Planner (Matcha Serenity)
- DP1033 Teacher Planner 2026-2027 (Sunflower Studio)
- Wall art mockup photos for 20 listings with fewer than 5 photos

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
**Listings with 1-4 photos rank lower and convert worse. Full report: `data/reports/listing_health_2026-06-02.txt`**

One-photo listings that need mockups (14 listings):
- Gallery wall sets: 4513713142, 4513713106, 4513713044
- Nursery prints: 4513713984, 4513713962, 4513713936, 4513713922, 4513714191
- Black and white: 4513714013, 4513713945, 4513713712, 4513713514, 4513713805

4-photo listings that need 6 more photos (6 listings):
- 4509597559, 4509596017, 4509600086, 4509593697, 4509598784, 4509598660, 4492610660

```bash
python tools/generate_wall_art_mockups.py  # generates all 10 photos per listing
```

### Priority 3 — New Digital Planners (before back-to-school August)
```bash
python tools/generate_planner.py DP1030  # ADHD Planner (Matcha Serenity)
python tools/generate_planner.py DP1033  # Teacher Planner (Sunflower Studio)
```
After generation, stages as draft. You review and approve.

### Priority 4 — Sublimation (Teacher Life + Nurse Life already have mockups)
```bash
python tools/publish_sublimation_pack.py --bundle teacher_life
python tools/publish_sublimation_pack.py --bundle nurse_life
```

### Priority 5 — Sticker Pack Listings (6 packs have no Etsy listing yet)
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

---

## COMPLETED TODAY (2026-06-02)

- [x] 4 planner listing titles fixed — added "Instant Download" within 70-char limit
- [x] 10 sticker/wall art listing titles fixed — added "Instant Download" within 70-char limit
- [x] tools/approve_listing.py built — review and approve draft listings before they go live
- [x] tools/listing_performance_monitor.py built — daily listing health audit (29 flagged today, 10 fixed, 20 photo issues queued)
- [x] tools/review_monitor.py built — daily review check + auto-draft responses
- [x] Cron: weekly tag audit added (Sundays 10am)
- [x] Cron: daily review check added (8:30am)
- [x] etsy_api.py: added get_reviews() + get_shop_listings_all() methods
- [x] Weekly report run — $307/mo pace, 6% of $5,000 target
- [x] Health check: refresh token age tracking (warns at 21 days, critical at 14 days)
- [x] Research synthesized into CLAUDE.md — Etsy API limits, AI disclosure requirements, customer service templates, Pinterest/TikTok, competitor tools, pricing strategy, ranking recovery

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
| Weekly net revenue | $20.45 | $1,154/wk | 6% of target |
| Monthly pace | $307/mo | $5,000/mo | 6% of target |
| Listings with title issues | 0 | 0 | Fixed today |
| Listings with photo issues | 20 | 0 | Queued (needs OpenAI) |
| SVG bundles complete | 0/5 | 5/5 | Queued (needs OpenAI) |

**Biggest revenue lever right now:** Publish SVG bundles + fix photo-deficient wall art listings. Each SVG bundle = ~$50-200/mo passive. 20 wall art listings with better photos = meaningfully higher conversion rate.
