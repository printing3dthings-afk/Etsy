# OnBrandCraftz — Master TODO List
*Last updated: 2026-06-02*

---

## 🔴 YOUR ACTIONS (only you can do these)

| # | Task | Time | Blocks |
|---|---|---|---|
| 1 | **Top up OpenAI billing** — platform.openai.com → Billing → Add $100, raise hard limit, enable auto-recharge | 5 min | Everything below |
| 2 | **Set up cron jobs** — `crontab -e` → add the 3 lines below | 2 min | Daily automation |
| 3 | **Etsy Ads** — increase from $1.30/day to $5/day once you have 5+ reviews on any listing | 2 min | Visibility |

Cron lines for item 2 (add all 3):
```
# Daily health check (8am)
0 8 * * * cd /home/user/Etsy && python tools/health_check.py --quiet >> data/pipeline_log.txt 2>&1
# Daily message autoresponder (8am)
0 8 * * * cd /home/user/Etsy && python tools/etsy_autoresponder.py >> data/pipeline_log.txt 2>&1
# Weekly business pipeline (9am Sunday)
0 9 * * 0 cd /home/user/Etsy && python tools/agents/business_pipeline.py --mode weekly >> data/pipeline_log.txt 2>&1
```

---

## 🤖 MY QUEUE (blocked on OpenAI billing — runs automatically once topped up)

### Priority 1 — SVG Bundles (5 bundles × 20 designs)
```bash
python tools/generate_svg_designs.py western        # resume from design 13/20
python tools/generate_svg_designs.py floral_wreath  # 0/20
python tools/generate_svg_designs.py mama_scripts   # 0/20
python tools/generate_svg_designs.py retro_groovy   # 0/20
python tools/generate_svg_designs.py dark_floral    # 0/20
python tools/publish_svg_bundle.py --all            # publish after review
```
**Cost:** ~$20 total

### Priority 2 — Wall Art Mockups (upgrade all listings to 10 photos)
```bash
python tools/generate_wall_art_mockups.py
```
**Scope:** All active wall art listings — replaces 1-photo listings with proper 10-photo sets

### Priority 3 — Sublimation (Teacher Life + Nurse Life)
```bash
python tools/generate_sublimation_wraps.py teacher_life nurse_life
python tools/generate_tumbler_mockups.py teacher_life nurse_life
python tools/publish_sublimation_pack.py --bundle teacher_life
python tools/publish_sublimation_pack.py --bundle nurse_life
```

### Priority 4 — Sticker Pack Listings (create on Etsy)
Generate photos + create the 6 sticker pack listings that are sitting locally with no Etsy presence yet.

---

## 📋 BACKLOG (future work)

### New digital planners (before August for back-to-school)
| ID | Product | Theme | Priority |
|---|---|---|---|
| DP1030 | ADHD Planner | Matcha Serenity | High |
| DP1033 | Teacher Planner 2026–2027 | Sunflower Studio | High |
| DP1031 | Undated Life Planner | Sage Garden | Medium |
| DP1032 | Dark Mode Bundle | Midnight Kawaii | Medium |

### More SVG bundles
Faith & Inspirational · Nurse / Healthcare · Teacher Life · Sports Mom

### More sublimation niches
Faith/Christian · Sports Mom · Seasonal (Christmas, Valentine's)

### Planner improvements
- 5 cover options per planner (competitors have 100+)
- Daily pages for DP1026 + DP1027 (most requested feature)
- Multiple weekly layout options

---

## 🛍️ LOW URGENCY (your tasks, no deadline)

- [ ] **Shop announcement** — Etsy Shop Manager → add current promotion + social links
- [ ] **Shop video** — 5–15 sec screen recording of planner in use → upload to any active planner listing
- [ ] **TikTok** — go to Buffer.com (free), connect TikTok, schedule from `data/tiktok_content_calendar.json`
- [ ] **Email list** — create free Mailchimp account → connect to `tools/email_leadmagnet.py` (already built)

---

## ✅ COMPLETED TODAY

- [x] Etsy OAuth token refreshed and working
- [x] Post-purchase message updated (no emojis, signed Scott)
- [x] Etsy Ads turned on ($1.30/day on Mom Life Sublimation)
- [x] 13 inactive wall art listings re-activated (now 93 active listings)
- [x] Health check system built + running (`tools/health_check.py`)
- [x] Weekly business report system built (`tools/weekly_report.py`)
- [x] Message autoresponder built (`tools/etsy_autoresponder.py`) — drafts replies, emails digest
- [x] SVG bundle title lengths fixed (were 74–83 chars, now all ≤70)
- [x] etsy_oauth.py fixed to work without a local server

## ✅ COMPLETED PREVIOUSLY

### Infrastructure
- [x] Sublimation full pipeline — design gen, tumbler mockups, ZIP, publisher
- [x] Wall art mockup generator — images.edit, 27 products configured
- [x] SVG bundle generator — 5 bundles × 20 designs, vtracer tracing, publisher
- [x] Business pipeline — weekly run, quality gates
- [x] Health check, weekly report, decision log

### Live Etsy listings
- [x] 4 digital planners live (DP1026–DP1029)
- [x] All 4 Planners Bundle live ($39.99)
- [x] Mom Life Sublimation Bundle live ($9.99)
- [x] 93 wall art / bundle listings active

### Marketing
- [x] Abandoned cart coupon COMEBACK10 (10% off)
- [x] Thank-you coupon THANKYOU15 (15% off)
- [x] Post-purchase message live
- [x] Pinterest 95 pins queued
- [x] TikTok 30-day content calendar built
- [x] Email lead magnet system built
