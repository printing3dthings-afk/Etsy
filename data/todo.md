# OnBrandCraftz — Master TODO List
*Last updated: 2026-05-28*

---

## 🔴 DO RIGHT NOW (You do these — takes 10 minutes)

- [ ] **Activate bundle listing** — Etsy Shop Manager → Listings → ID 4512188970 → change to Active (photos + files are uploaded and ready)
- [ ] **Activate 6 sticker pack listings** — same process for all 6 drafts below
- [ ] **Turn on Etsy Ads** — $5/day on Puffer Koozie (7♥) and Boho Centerpiece (5♥) in Etsy app
- [ ] **Get first 5 reviews** — ask friends/family to buy the $0.20 free sticker sheet (listing 4512255508) and leave a review

---

## 🆕 DRAFT LISTINGS — READY TO ACTIVATE (just flip to active)

| Listing | ID | Price | What's needed |
|---|---|---|---|
| Free Kawaii Sticker Sheet | 4512255508 | $0.20 | Add photos → activate |
| Lavender Dreams Sticker Pack | 4512255514 | $4.99 | Add photos → activate |
| Cotton Candy Sticker Pack | 4512254015 | $4.99 | Add photos → activate |
| Midnight Blue Sticker Pack | 4512255536 | $4.99 | Add photos → activate |
| Coral Peach Sticker Pack | 4512254027 | $4.99 | Add photos → activate |
| All 4 Sticker Packs Bundle | 4512254035 | $12.99 | Add photos → activate |
| All 4 Planners Bundle | 4512188970 | $39.99 | **Photos + files uploaded ✓ — just activate** |

---

## 📸 LISTING PHOTOS NEEDED
*(Can build with real PDF renders — no OpenAI needed for planner pages)*

- [ ] Generate 10 photos for DP1026 Life Planner (listing 4509179201)
- [ ] Generate 10 photos for DP1027 Student Planner (listing 4509184958)
- [ ] Generate 10 photos for DP1028 Budget Planner (listing 4509184962)
- [ ] Generate 10 photos for DP1029 Fitness Planner (listing 4509184968)
- [ ] Generate photos for all 6 sticker pack listings
  - Note: sticker sheet images (real) already exist — just need listing photo composites

---

## 🛍️ ETSY SHOP SETUP (manual steps in Etsy)

- [ ] **Post-purchase message** — run `python tools/etsy_messages.py` to get text → paste into Shop Manager → Settings → Info & Appearance → Message to Buyers
- [ ] **Abandoned cart coupon (COMEBACK10)** — Shop Manager → Marketing → Sales & Discounts → Create Offer → Abandoned Cart → 10% off, 24-hour delay
- [ ] **Thank-you coupon (THANKYOU15)** — Shop Manager → Marketing → Sales & Discounts → Create Offer → Thank You → 15% off, 30-day expiry
- [ ] **Shop announcement** — add email list signup link + current promotion
- [ ] **Shop video** — record a 5-15 second screen recording flipping through a planner → upload to any active planner listing

---

## 📱 SOCIAL MEDIA SETUP (manual steps needed)

- [ ] **Pinterest** — token expires daily, run `python tools/pinterest_oauth.py` to refresh. 95 pins queued ready to fire.
- [ ] **TikTok** — add Login Kit + Content Posting API to developer app, configure redirect URI → run `python tools/tiktok_oauth.py` (needs browser)
- [ ] **TikTok alternative** — sign up for Buffer.com (free), connect @onbrandcraftz, schedule from `data/tiktok_content_calendar.json`
- [ ] **Instagram** — set up Meta developer app → get INSTAGRAM_ACCESS_TOKEN → `tools/instagram_api.py` is ready

---

## 📧 EMAIL LIST (Mailchimp — manual setup)

- [ ] Create free Mailchimp account → create audience "OnBrandCraftz VIP List"
- [ ] Create signup form → add URL to `.env` as `MAILCHIMP_SIGNUP_URL`
- [ ] Upload one sticker sheet to Google Drive (public) → add link to `.env` as `LEAD_MAGNET_URL`
- [ ] Set up Welcome automation email (`python tools/email_leadmagnet.py --templates`)
- [ ] Add signup link to TikTok/Pinterest/Instagram bios + Etsy shop announcement
- [ ] Create coupon VIP10 in Etsy (10% off, permanent, for email subscribers)

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

- [ ] Add 5 cover options to each planner (currently 1 each) — competitors have 100+
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

---

## ✅ COMPLETED

- [x] 4 digital planner listings live on Etsy (DP1026, DP1027, DP1028, DP1029)
- [x] All 4 planners have: Welcome page, Dashboard, Index, undated version, hyperlinked tabs, HOME footer
- [x] Tag fixes applied to all 4 planners + 4 wall art listings
- [x] Bundle listing created, photos uploaded, digital files uploaded (ID: 4512188970) — just needs activating
- [x] 6 sticker pack listings created as drafts with digital files uploaded
- [x] **Sticker packs expanded to 200+ stickers** — each planner now has 11 unique illustrated sheets
- [x] All listing descriptions accurate — no false sticker count claims
- [x] Sticker pack ZIPs rebuilt with correct per-planner sheet names
- [x] Standalone sticker pack listings updated with new 11-sheet ZIPs (200+ stickers each)
- [x] All 4 Planners Bundle description updated to 800+ stickers
- [x] Post-purchase message templates written (`tools/etsy_messages.py`)
- [x] Coupon strategy documented (COMEBACK10, THANKYOU15, BUNDLE20)
- [x] Pinterest boards + pin descriptions set up (95 pins queued)
- [x] TikTok 30-day content calendar built (`data/tiktok_content_calendar.json`)
- [x] Email lead magnet system built (`tools/email_leadmagnet.py`)
- [x] TikTok OAuth + poster scripts built (`tools/tiktok_oauth.py`, `tools/tiktok_poster.py`)
- [x] Analytics dashboard with action items (`python tools/analytics_tracker.py`)
- [x] TikTok developer app created (Client Key + Secret saved to .env)
- [x] All listing photos now use real product renders (no AI-generated fictional planner content)
