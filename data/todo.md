# OnBrandCraftz — Master TODO List
*Last updated: 2026-05-27*

---

## 🔴 DO FIRST (Highest Revenue Impact)

- [ ] **Top up OpenAI billing** — unlocks listing photo generation for all planners and sticker packs (biggest single conversion boost)
- [ ] **Turn on Etsy Ads** — $5/day each on Puffer Koozie (7♥) and Boho Centerpiece (5♥) — do in Etsy app right now
- [ ] **Get first 5 reviews** — ask friends/family to purchase the $0.20 free sticker sheet listing and leave a review (listing ID: 4512255508)
- [ ] **Activate bundle listing** — listing ID 4512188970, $39.99 — add photos then change state to active in Etsy

---

## 📸 LISTING PHOTOS NEEDED
*(All blocked until OpenAI billing is topped up)*

- [ ] Generate 10 photos for DP1026 Life Planner (listing ID: 4509179201)
- [ ] Generate 10 photos for DP1027 Student Planner (listing ID: 4509184958)
- [ ] Generate 10 photos for DP1028 Budget Planner (listing ID: 4509184962)
- [ ] Generate 10 photos for DP1029 Fitness Planner (listing ID: 4509184968)
- [ ] Generate photos for all 6 sticker pack listings (IDs below)
- [ ] Generate photos for bundle listing (ID: 4512188970)

---

## 🆕 NEW LISTINGS — DRAFTS READY TO ACTIVATE

These are created and waiting. Add photos → flip to active.

| Listing | ID | Price | Status |
|---|---|---|---|
| Free Kawaii Sticker Sheet (review driver) | 4512255508 | $0.20 | Draft |
| Lavender Dreams Sticker Pack | 4512255514 | $4.99 | Draft |
| Cotton Candy Sticker Pack | 4512254015 | $4.99 | Draft |
| Midnight Blue Sticker Pack | 4512255536 | $4.99 | Draft |
| Coral Peach Sticker Pack | 4512254027 | $4.99 | Draft |
| All 4 Sticker Packs Bundle | 4512254035 | $12.99 | Draft |
| All 4 Planners Bundle | 4512188970 | $39.99 | Draft |

---

## 📱 SOCIAL MEDIA SETUP

- [ ] **TikTok** — finish developer app setup (add Login Kit + Content Posting API products, configure redirect URI) then run `python tools/tiktok_oauth.py`
- [ ] **TikTok alternative** — sign up for Buffer.com (free), connect @onbrandcraftz, start scheduling from the 30-day calendar (`data/tiktok_content_calendar.json`)
- [ ] **Instagram** — set up Meta developer app on computer (`tools/instagram_api.py` is ready, needs INSTAGRAM_ACCESS_TOKEN)
- [ ] **Pinterest** — waiting for app approval (token expires daily, run `python tools/pinterest_oauth.py` to refresh). 95 pins queued ready to fire.

---

## 📧 EMAIL LIST (Mailchimp)

- [ ] Create free Mailchimp account at mailchimp.com
- [ ] Create audience "OnBrandCraftz VIP List"
- [ ] Create signup form → copy URL → add to `.env` as `MAILCHIMP_SIGNUP_URL`
- [ ] Upload one sticker sheet PNG to Google Drive → make public → add link to `.env` as `LEAD_MAGNET_URL`
- [ ] Set up Welcome automation email (template ready: `python tools/email_leadmagnet.py --templates`)
- [ ] Add signup link to TikTok bio, Pinterest bio, Instagram bio
- [ ] Add signup link to Etsy shop announcement
- [ ] Create coupon VIP10 in Etsy (10% off, permanent, for email subscribers)

---

## 🛍️ ETSY SHOP SETUP

- [ ] **Post-purchase message** — paste short message into Etsy → Shop Manager → Settings → Info & Appearance → Message to Buyers (run `python tools/etsy_messages.py` to get text)
- [ ] **Abandoned cart coupon (COMEBACK10)** — Shop Manager → Marketing → Sales & Discounts → Create Offer → Abandoned Cart → 10% off, 24-hour delay
- [ ] **Thank-you coupon (THANKYOU15)** — Shop Manager → Marketing → Sales & Discounts → Create Offer → Thank You → 15% off, 30-day expiry
- [ ] **Shop announcement** — add email list signup link + current promotion
- [ ] **Shop video** — record a 5-15 second screen recording of flipping through a planner → upload to any active planner listing

---

## 🆕 NEW PRODUCTS TO BUILD

| Product | ID | Theme | Priority | Reason |
|---|---|---|---|---|
| ADHD Planner | DP1030 | Matcha Serenity | 🔴 High | Fastest growing niche on Etsy, low competition |
| Teacher Planner | DP1033 | Sunflower Studio | 🔴 High | August back-to-school peak — build NOW |
| Undated Life Planner | DP1031 | Sage Garden | 🟡 Medium | Sells year-round, no 2026 expiry |
| Dark Mode Bundle | DP1032 | Midnight Kawaii | 🟡 Medium | Trending dark aesthetic |

---

## 🎨 PRODUCT IMPROVEMENTS

- [ ] Add Welcome/Setup page to all 4 planners (reduces support messages 30-40%)
- [ ] Add Dashboard/Home page to all 4 planners
- [ ] Add "BACK TO HOME" footer on every page
- [ ] Add undated evergreen version to all 4 planners (doubles product value)
- [ ] Expand sticker packs to 200+ stickers (currently ~60)
- [ ] Add 5 cover options to each planner (currently 1 each)
- [ ] Add daily pages to DP1026 and DP1027 (top requested feature)

---

## 💰 ADS STRATEGY

- [ ] Turn on Etsy Ads at $5/day for Puffer Koozie (7♥)
- [ ] Turn on Etsy Ads at $5/day for Boho Centerpiece (5♥)
- [ ] Once planners reach 5+ reviews → turn on Etsy Ads for each planner at $5/day
- [ ] After 30 days of ad data → increase budget on best performers only

---

## 🔧 TECHNICAL / CLEANUP

- [ ] Delete planner backup files: `data/digital_products/product_files/*.orig_backup` (86.3 MB) — after verifying planners work in GoodNotes
- [ ] Add Content Posting API to TikTok developer app (requires demo video)
- [ ] Complete TikTok OAuth (`python tools/tiktok_oauth.py`) — needs computer with browser
- [ ] Top up OpenAI account to re-enable image generation

---

## ✅ COMPLETED

- [x] 4 digital planner listings live on Etsy (DP1026, DP1027, DP1028, DP1029)
- [x] Tag fixes applied to all 4 planners + 4 wall art listings (buyer-intent phrases)
- [x] Bundle listing created as draft (ID: 4512188970, $39.99)
- [x] 6 sticker pack listings created as drafts
- [x] Post-purchase message templates written (`tools/etsy_messages.py`)
- [x] Coupon strategy documented (COMEBACK10, THANKYOU15, BUNDLE20)
- [x] Pinterest boards + pin descriptions set up (95 pins queued)
- [x] TikTok 30-day content calendar built (`data/tiktok_content_calendar.json`)
- [x] Email lead magnet system built (`tools/email_leadmagnet.py`)
- [x] TikTok OAuth + poster scripts built (`tools/tiktok_oauth.py`, `tools/tiktok_poster.py`)
- [x] Analytics dashboard with action items (`python tools/analytics_tracker.py`)
- [x] TikTok developer app created (Client Key + Secret saved to .env)
