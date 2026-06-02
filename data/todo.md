# OnBrandCraftz — Master TODO List
*Last updated: 2026-06-02*

---

## 🔴 YOUR ACTIONS (only you can do these)

| # | Task | Time | Blocks |
|---|---|---|---|
| 1 | **Top up OpenAI billing** — platform.openai.com → Billing → Add $100, enable auto-recharge | 5 min | Everything below |
| 2 | **Refresh Etsy token** — `python tools/etsy_oauth.py` (browser pops open, click Allow) | 2 min | Publishing |
| 3 | **Set up weekly cron job** — `crontab -e` → add line below | 2 min | Automation |
| 4 | **Post-purchase message** — Etsy Shop Manager → Settings → Message to Buyers → paste from `python tools/etsy_messages.py` | 3 min | Review rate |
| 5 | **Activate 6 sticker pack listings** — Etsy Shop Manager → Listings → flip each draft to Active | 5 min | Revenue |
| 6 | **Turn on Etsy Ads** — $5/day on Mom Life Sublimation Bundle (listing 4514777212) | 2 min | Visibility |

Cron line for item 3:
```
0 9 * * 0 cd /home/user/Etsy && python tools/agents/business_pipeline.py --mode weekly >> data/pipeline_log.txt 2>&1
```

---

## 🤖 AUTOMATED (runs after billing is topped up — no action needed from you)

### 1. SVG Bundles — finish western, then all 4 remaining
```bash
python tools/generate_svg_designs.py western        # resumes at design 13/20
python tools/generate_svg_designs.py floral_wreath
python tools/generate_svg_designs.py mama_scripts
python tools/generate_svg_designs.py retro_groovy
python tools/generate_svg_designs.py dark_floral
python tools/publish_svg_bundle.py --all
```
**Status:** western 12/20 done, SVGs traced. 8 designs + all mockups + 4 bundles pending.
**Cost:** ~$20 OpenAI credits for all 5 complete.

### 2. Wall Art Mockups — regenerate all 27 listings to new standard
```bash
python tools/generate_wall_art_mockups.py
```
**Status:** Tool built (images.edit, real art placed into existing frame in room). NOT run yet.
Will replace old PIL composite photos on all DP1000–DP1026 listings.

### 3. Sublimation — Teacher Life + Nurse Life bundles
Add design configs to `generate_sublimation_wraps.py`, then:
```bash
python tools/generate_sublimation_wraps.py teacher_life nurse_life
python tools/generate_tumbler_mockups.py teacher_life nurse_life
python tools/publish_sublimation_pack.py --bundle teacher_life
python tools/publish_sublimation_pack.py --bundle nurse_life
```
**Status:** Mom Life bundle live. Teacher + Nurse design configs not yet written.

---

## 📋 BACKLOG (future automated runs)

### More sublimation niches
- Faith/Christian — cross, scripture, floral
- Sports Mom — baseball, soccer, basketball
- Seasonal — Christmas, Valentine's (evergreen text only, no dates)

### More SVG bundles (after first 5 complete)
- Faith & Inspirational
- Nurse / Healthcare
- Teacher Life
- Sports Mom

### New digital planners
| ID | Product | Theme | Priority | Reason |
|---|---|---|---|---|
| DP1030 | ADHD Planner | Matcha Serenity | 🔴 High | Fastest growing niche, low competition |
| DP1033 | Teacher Planner 2026–2027 | Sunflower Studio | 🔴 High | Back-to-school peak — build before August |
| DP1031 | Undated Life Planner | Sage Garden | 🟡 Medium | Sells year-round |
| DP1032 | Dark Mode Bundle | Midnight Kawaii | 🟡 Medium | Trending aesthetic |

### Planner improvements
- Add 5 cover options to each planner (competitors have 100+)
- Add daily pages to DP1026 and DP1027 (most requested feature)
- Add multiple weekly layout options

---

## 🛍️ MANUAL ETSY / SOCIAL (your tasks, low urgency)

- [ ] **Shop announcement** — add current promotion + social links in Etsy Shop Manager
- [ ] **Shop video** — 5–15 sec screen recording of planner in use → upload to any active planner listing
- [ ] **Pinterest** — token expires daily: `python tools/pinterest_oauth.py` to refresh (95 pins queued)
- [ ] **TikTok** — use Buffer.com (free) to schedule posts from `data/tiktok_content_calendar.json`
- [ ] **Email list** — create free Mailchimp account, set up welcome automation (`tools/email_leadmagnet.py` is ready)

---

## ✅ COMPLETED

### Pipeline & infrastructure
- [x] Sublimation full pipeline — design gen, tumbler mockups via images.edit, ZIP, Etsy publisher
- [x] Wall art mockup generator — images.edit approach built, 27 products configured (`tools/generate_wall_art_mockups.py`)
- [x] SVG bundle generator — 5 bundles × 20 designs, vtracer SVG tracing, 3-product mockups, publisher
- [x] Business pipeline — monitor, weekly run, quality gates (`tools/agents/business_pipeline.py`)
- [x] Sublimation standards knowledge base — committed and tracked in git
- [x] Git hygiene — large binary outputs gitignored, state manifests tracked

### Live Etsy listings
- [x] 4 digital planners live (DP1026–DP1029) with 10 real-product photos each
- [x] All 4 Planners Bundle live (ID: 4512188970, $39.99)
- [x] Mom Life Sublimation Tumbler Bundle live (ID: 4514777212, $9.99, 8 designs)
- [x] 20+ wall art listings live (photos to be upgraded by wall art mockup runner)
- [x] 6 sticker pack draft listings — files uploaded, need activating

### Quality standards locked in
- [x] No dates / no "est." / no specific years in any design — universal buyer appeal
- [x] All listing photos use real art file via images.edit — no fictional AI renders
- [x] Title ≤70 chars enforced (mobile ranking rule)
- [x] 13 tags, ≤20 chars, no tag duplicates title phrases
- [x] ZIP files under Etsy 20MB limit

### Marketing
- [x] Abandoned cart coupon COMEBACK10 (10% off, 24-hour delay)
- [x] Thank-you coupon THANKYOU15 (15% off, 30-day expiry)
- [x] Post-purchase message templates written (`tools/etsy_messages.py`)
- [x] Pinterest 95 pins queued
- [x] TikTok 30-day content calendar built
- [x] Email lead magnet system built (`tools/email_leadmagnet.py`)
