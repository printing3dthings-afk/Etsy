# OnBrandCraftz — Business Standards & Growth Framework
## Living Document | Updated May 2026

---

## MISSION STATEMENT

> **"Providing the best and most accurate transaction for our customers so we can grow responsibly."**

Every decision made in this business — every product created, every image generated, every price set, every piece of code written — must be evaluated against this statement. If an action cannot be justified by this mission, it does not happen.

### What This Mission Means Operationally

**"Best and most accurate transaction"** means:
- Every product file is exactly what the listing says it is — no exceptions
- Every image shows the REAL product the customer will download
- Every description is truthful, specific, and complete
- No customer ever receives less than what was promised
- No customer ever has to ask "what did I buy?"

**"Grow responsibly"** means:
- Quality cannot decrease as volume increases
- No listing goes live that fails any quality gate
- Sales growth never comes at the expense of a single customer's trust
- Metrics are tracked so decline is caught immediately — not after the damage is done
- Every improvement is permanent — we never undo progress

---

## PART 1: THE QUALITY GATES

Every product must pass ALL of the following gates before it goes live on Etsy. These are not suggestions. A single gate failure = the product does not list.

### Gate 1 — File Quality Gate
| Standard | Minimum | Target |
|----------|---------|--------|
| Image DPI | 300 | 300–600 |
| Shortest side (pixels) | 3000 | 4500+ |
| File size (for image art) | 2 MB | 4–20 MB |
| File size (for PDF planners) | 8 MB | 12–20 MB |
| Color mode | sRGB | sRGB |
| Format | JPG/PNG/PDF | JPG/PNG/PDF |
| Etsy per-file limit | <20 MB | <18 MB (buffer) |

**Auto-rejection triggers:**
- File size < 500 KB for any multi-page planner (physically impossible to contain real artwork)
- Resolution < 2000px on shortest side
- File does not open without errors
- Dates in a "2026" planner that are on the wrong weekday

### Gate 2 — Listing Photo Gate
| Standard | Requirement |
|----------|-------------|
| Photos show real product | MANDATORY — no AI-generated fake content |
| Photo count | Minimum 7, target 10 |
| Hero image resolution | 2400×2400px |
| Hero has 5% edge padding | Required — prevents mobile crop |
| Two different room settings | Required for wall art |
| Gallery wall image | Required for wall art |
| Size reference image | Required for wall art |
| No text baked into lifestyle photos | Required |
| Art visible at 200×200px crop | Pass/fail visual check |

**Auto-rejection triggers:**
- Lifestyle photos generated from redo_lifestyle_rooms.py without compositing real art (fake AI art)
- Single room setting only (wall art listings)
- Missing size reference
- Photos showing furniture overlapping the frame

### Gate 3 — Listing Content Gate
| Standard | Requirement |
|----------|-------------|
| Title length | ≤140 chars, primary keyword in first 40 |
| Tags | All 13 used, each ≤20 chars, no special chars |
| Description | All 9 required sections present |
| Price | Above price floor for category |
| "Instant Download" visible | In title or first description sentence |
| What's included | Every file listed with page count / format |
| FAQ section | Minimum 4 questions covering compatibility, printing, physical vs digital, sharing |

**Price floors (non-negotiable):**
- Single digital art print: $7.99 minimum (target $9.99)
- Digital planner: $9.99 minimum (target $12.99–$17.99)
- Bundle / gallery wall set: $14.99 minimum
- Physical 3D product: $12.99 minimum

### Gate 4 — Accuracy Gate (Mission Critical)
This gate exists because of the mission statement. Every claim made about the product must be verified before listing.

| Claim | Verification method |
|-------|---------------------|
| "Instant download" | Confirm file is attached to listing before publishing |
| "300 DPI print-ready" | Run check_file_specs — DPI must be confirmed, not assumed |
| "X pages" | Count pages in actual file |
| "Works with GoodNotes" | PDF must open without errors |
| "2026 dated" | Verify Jan 1, 2026 falls on Thursday |
| "Undated version included" | Confirm undated PDF exists and has no year references |
| "Sticker pack included" | Confirm ZIP file opens and contains all 5 sheets |

---

## PART 2: THE CUSTOMER TRUST STANDARDS

### What Earns Trust (and Must Never Be Broken)
1. **Product matches listing** — If the listing says "5 sticker sheets, 200+ stickers," the file contains exactly that.
2. **Download works first try** — Files must be tested on at least one compatible app before listing
3. **Description answers questions before they're asked** — A buyer should never need to message us to understand what they're buying
4. **Response time within 24 hours** — Every message gets a response within 24 hours, 12 hours target
5. **Zero tolerance for false claims** — If we cannot confirm it, we do not claim it

### What Destroys Trust (Zero Tolerance List)
- Listing images that show fake/AI-generated art instead of the real product
- Page counts, file sizes, or DPI values that are rounded up or guessed
- Features listed that don't work (e.g., hyperlinks that don't navigate correctly)
- Selling an "undated" planner that still has year-specific dates
- Sticker packs with fewer stickers than claimed

---

## PART 3: ETSY SHOP HEALTH METRICS

### Etsy Star Seller Requirements (maintain at all times)
Etsy awards Star Seller status based on a 3-month rolling window:

| Metric | Etsy Minimum | Our Target |
|--------|-------------|-----------|
| Message response rate | ≥95% within 24 hours | 100% within 12 hours |
| On-time dispatch rate | ≥95% | 100% (digital = instant) |
| 5-star reviews | ≥95% of reviews | 100% — 5 stars only |
| Average order value | No minimum | Increase 10% quarterly |
| Listings with at least 1 review | ≥10 | All listings with sales |

### Shop Health Dashboard — Check Weekly
Run `python tools/shop_health_check.py` (to be built) every Monday:
- Total sales (week / month / all-time)
- Conversion rate by listing
- Favorite-to-sale ratio (high favorites + low sales = photo or price problem)
- New reviews this week (respond within 24 hours)
- Any messages unanswered >12 hours
- Any listing with 0 views in 30 days (SEO problem)
- Any listing with >50 views but 0 sales (photo/price/description problem)

### Listing Health — Check Monthly
For every active listing:
- View count (30-day trend — rising, flat, or falling?)
- Conversion rate (views → purchases) — target >3%
- Favorite rate (views → favorites) — target >5%
- Review sentiment — any negative feedback patterns?
- Photo performance — has the hero shot been updated in last 60 days?

---

## PART 4: RESPONSIBLE GROWTH FRAMEWORK

### The Growth Ladder — Never Skip a Rung
Responsible growth means adding the next level only when the current level is solid.

```
RUNG 1 — Foundation (0–10 sales)
  ✓ Every listing passes all 4 quality gates
  ✓ All 10 photo slots used on every listing
  ✓ Two lifestyle room settings per wall art listing
  ✓ Response time <24 hours
  ✓ 100% 5-star reviews
  → THEN advance to Rung 2

RUNG 2 — Optimization (10–50 sales)
  ✓ A/B test hero image on 2+ listings
  ✓ Add gallery wall image to every wall art listing
  ✓ Add size reference image to every wall art listing
  ✓ Add video (3-second loop) to top 5 listings
  ✓ Respond to every review publicly
  → THEN advance to Rung 3

RUNG 3 — Scale (50–200 sales)
  ✓ Add 2nd room lifestyle shot to every listing
  ✓ Create gallery wall bundle listings (3–4 prints)
  ✓ Launch Pinterest/TikTok driving external traffic
  ✓ Build email list from buyers (digital delivery system)
  ✓ Weekly shop health review (formal)
  → THEN advance to Rung 4

RUNG 4 — Authority (200–1000 sales)
  ✓ Star Seller badge earned and maintained
  ✓ 100+ active listings
  ✓ New products launched monthly
  ✓ Seasonal collection launches (spring/fall/holiday)
  ✓ Revenue covers operational costs with positive margin
  → THEN advance to Rung 5

RUNG 5 — Market Leadership (1000+ sales)
  ✓ Top 5% conversion rate in category
  ✓ 500+ reviews, 4.9+ average
  ✓ Featured in Etsy editorial or external press
  ✓ Pinterest and TikTok driving measurable traffic
  ✓ New product pipeline 60+ days ahead
```

### The Anti-Regression Rules
These rules exist specifically to prevent going backwards:

1. **Never remove a feature once shipped** — if we added 2-room lifestyle shots, all future listings have them
2. **Never list a product that is worse than our current worst listing** — new always meets or exceeds the existing standard
3. **Photo quality floor raises permanently** — once we hit a quality level, that becomes the new minimum
4. **Price floors only move up** — once we set a price floor, it never moves down (dropping prices signals quality decline)
5. **Quality gate failures are permanent lessons** — every rejection gets logged and the gate it failed is documented to prevent recurrence

---

## PART 5: CODE QUALITY STANDARDS

### Every Script Written Must Follow These Rules

**Security**
- Never hardcode credentials — always parse .env manually
- Never commit .env or any file containing secrets
- Never log API keys, tokens, or customer data

**Reliability**
- Every API call must have retry logic (3 attempts, exponential backoff: 2s, 4s, 8s)
- Every file operation must check file exists before reading
- Every upload must verify success before marking complete
- Never upload a file that failed generation — skip with warning instead

**Transparency**
- Every batch operation must print a clear summary at the end (what succeeded, what failed)
- Every composite/generation must log furniture_y, frame_bottom, and clearance values
- Every Etsy API call result (listing ID, image ID, rank) must be logged to a file

**Prevention**
- composite_smart must always be used instead of fixed-position compositing
- scene_prompt must always enforce upper-70% wall constraint
- Every lifestyle photo must be QC-checked before upload
- No upload-on-fail logic — a failed composite stays local, never goes to Etsy

**Maintainability**
- Listing ID mappings are the single source of truth (never duplicated across scripts)
- Frame colors are defined once and imported everywhere
- All constants (ART_DIR, LISTING_IDS, etc.) live in one place per domain

---

## PART 6: DECISION FRAMEWORK

When any decision must be made, apply this 4-question test:

1. **Does this serve the customer first?** — Will this make the customer's experience better, or is it purely for our convenience?
2. **Is this accurate?** — Can we stand behind every claim this decision involves?
3. **Does this help us grow responsibly?** — Will this add sustainable value, or create technical/quality debt?
4. **Does this maintain our standards?** — Does this meet or raise our current quality bar?

If the answer to any of these is "no," the decision is rejected and reworked.

### When to Slow Down vs. Move Forward
**Move forward immediately** when:
- All quality gates pass
- The change improves customer experience
- The change is reversible if something unexpected occurs

**Slow down and verify first** when:
- The change affects a live listing (customers may be viewing it)
- The change involves deleting or overwriting existing files
- The change is to pricing, tags, or titles (affects search ranking)
- The change involves sending any communication to customers

**Always ask before proceeding** when:
- The action is irreversible (deleting images on Etsy, changing listing status)
- The change affects all listings simultaneously
- The action involves customer payment or refund data
- Credentials or API tokens are involved

---

## PART 7: COMPETITIVE STANDARD

### The Floor We Must Always Be Above
Based on research of top-performing Etsy wall art and digital product shops:

| Area | Competitor Average | Our Minimum Standard | Our Target |
|------|-------------------|----------------------|-----------|
| Listing photos | 5–7 images | 7 images | 10 images |
| Rooms shown per listing | 1 | 2 | 3 |
| File resolution | 2000px | 3000px | 4500px |
| File DPI | 150–300 | 300 | 300–600 |
| Sizes included | 1–2 | 3–4 | 5+ (all standard sizes) |
| Review response rate | 30% of shops | 100% | 100% |
| Response time | 24–72 hours | <24 hours | <12 hours |
| Description completeness | 40% have FAQ | All listings | All listings |
| Gallery wall option | 20% of shops | All wall art listings | All wall art listings |
| Video listing | <10% of shops | Top 5 listings | All listings (eventually) |

### The Benchmark Commitment
Once per quarter, manually review 3 top-selling competitor shops in each product category. Document:
- Their best practices we are not yet using
- Their weaknesses we already exceed
- Any new standards they have set that we must match or surpass

This review is added to the next planning cycle as concrete action items.

---

## PART 8: WEEKLY REVIEW CHECKLIST

Run every Monday. Takes ~15 minutes. Prevents drift.

### Sales & Revenue
- [ ] Total sales this week vs. last week
- [ ] Revenue this week vs. last week
- [ ] Which listings had sales? (identify what's working)
- [ ] Which listings had views but no sales? (identify conversion problems)
- [ ] Average order value vs. previous week

### Customer Experience
- [ ] Any new reviews? (respond publicly within 24 hours)
- [ ] Any messages? (reply within 12 hours)
- [ ] Any negative signals (unfavorited items, abandoned carts with messaging)?
- [ ] Any download complaints or file issues reported?

### Listing Health
- [ ] Any listing with 0 views in past 7 days? (SEO problem — check tags)
- [ ] Any listing with high views + low favorites? (photo problem — hero image)
- [ ] Any listing with high favorites + low sales? (price or description problem)
- [ ] Any listing photos that need updating (6+ months old)?

### Product Pipeline
- [ ] New products in progress — on track?
- [ ] Any quality gate failures this week — root cause documented?
- [ ] OpenAI billing — enough credit for next week's planned generation?
- [ ] Any tool errors or broken automations discovered this week?

### Growth Tracking
- [ ] Current rung on Growth Ladder? What's needed to advance?
- [ ] Competitor review due? (quarterly)
- [ ] Any new interior design trends or buyer behavior shifts to capture?

---

*This document is the operating constitution of OnBrandCraftz.*
*When code, decisions, or products conflict with anything here, this document wins.*
*Last updated: May 2026*

---

## PART 9: DEEP RESEARCH FINDINGS — May 2026

*Research conducted May 29, 2026. All findings sourced from multiple independent sources. Single-source claims are flagged.*

---

### 9.1 — Etsy Quality Signals & Customer Trust Metrics (Verified)

#### Star Seller — Exact Thresholds (as of 2026)
The Star Seller badge requires ALL FOUR of these simultaneously over a rolling 3-month window:

| Metric | Threshold | How It Is Measured |
|--------|-----------|---------------------|
| Message response rate | ≥95% | First message in each thread only; auto-replies count |
| On-time shipping + tracking | ≥95% | Digital downloads are AUTOMATICALLY counted as on-time — exempt from this metric |
| Average review rating | ≥4.8 stars | Rolling 3-month window of received reviews |
| Order volume | ≥5 orders | In the 3-month window |
| Shop age | First sale ≥90 days ago | One-time eligibility requirement |

**Critical math:** A single 1-star review among 13 reviews can drop a 4.83 average to 4.54. At low volume (under 20 reviews per quarter), every review is high-stakes.

**Action for OnBrandCraftz:** Our digital-only shop has an automatic advantage on the shipping metric — all orders count as on-time without any action needed. Focus energy on message response rate and review quality.

#### Etsy's Internal Customer & Market Experience Score
Etsy gives each shop a **Customer and Market Experience Score** that feeds directly into search placement across the entire shop (not just the offending listing). Sources confirmed this score includes:
- Case rate (disputes opened against the shop)
- Review average
- Message response rate
- Policy compliance history
- Intellectual property violation history

**Case rate threshold (single-source — verify):** A case rate above approximately 1% of orders triggers search ranking suppression. Shops repeatedly failing this standard risk temporary or permanent selling privilege revocation.

**What counts as a "case":** A buyer opening a formal dispute with Etsy (not just messaging the seller). Accurate product descriptions are the primary defense — items "accurately described but not meeting expectations" are NOT eligible for Purchase Protection claims.

#### Review Rating Calculation — New Decay Model (2025 Update)
Etsy shifted from a 12-month rolling window to a lifetime-weighted system:
- All-time reviews count, but newer reviews have higher weight
- Each review's influence **halves every 12 months** (half-life decay model)
- A review from 2 years ago carries 25% of the weight of a review from today
- A review from 3 years ago carries ~12.5% of the weight
- **Star Seller eligibility still uses only the last 3 months** — the decay model affects the public shop rating display only

**Implication for OnBrandCraftz:** We are brand new with 4 sales and 5-star ratings. These early 5-star reviews will decay over time but currently have maximum weight. Sustaining early quality is compounding — early perfect reviews set the baseline and depreciate slowly.

#### Listing Quality Score — What It Actually Is
Etsy maintains a hidden, continuously recalculated Listing Quality Score per listing. The primary factors, in order of impact:
1. **Conversion rate** — orders divided by visits (most important single factor)
2. **Click-through rate (CTR)** — clicks from search results vs. impressions
3. **Add-to-cart rate** — visits that result in cart additions
4. **Favorites rate** — visits that result in favorites
5. **Purchase volume** — absolute number of sales (recency-weighted)
6. **Shop-level factors** — Star Seller status, case history, policy compliance

**New listing boost:** New listings receive a temporary algorithmic boost to test performance. If the listing fails to generate engagement during this window, it is suppressed. This makes the first 30–60 days of a listing critical.

**Warning signals for a declining quality score:**
- High impressions + low CTR = hero image is not stopping the scroll
- Normal CTR + low conversion = description/price/trust mismatch
- High favorites + low sales = price too high or purchase friction
- Sudden 40%+ view drop with no listing changes = algorithmic suppression

#### Ranking Algorithm — 2026 Updates
- **Title length penalty:** Titles over 70 characters now face ranking penalties on mobile, where 46% of purchases happen. The first 40 characters are weighted most heavily. *(Note: this conflicts with Etsy's 140-character max guidance — it means keyword density in the first 40 chars matters most, not that the title must be short.)*
- **Engagement signals are primary:** Click-through rate, add-to-cart, and purchase rate now outweigh keyword matching for established listings.
- **Mobile-first personalization:** Etsy's app generated 46% of GMV by Q3 2025 — all photo decisions must be optimized for the 200×200px mobile thumbnail first.
- **Shop quality affects all listings:** A shop with case history or poor metrics will see suppression across its entire catalog, not just flagged listings.
- **Daily activity preference:** Shops that publish consistently (1–3 listings per week) are preferred over batch uploads of 20+ listings at once.

---

### 9.2 — Responsible Scaling: Systems for 4 → 100 → 1000 Sales

#### Conversion Rate Benchmarks (from multiple verified sources)

| Category | New Shop (0–6 mo) | Established | Top Performers |
|----------|-------------------|-------------|----------------|
| Digital Downloads | 2–5% | 5–8% | 12–20% |
| All Etsy (average) | 0.5–2% | 2–3% | 5–10% |
| Direct/repeat buyers | — | 5–15% | 15%+ |

**Interpretation for OnBrandCraftz:** Our digital planners and wall art should target 5–8% conversion as an established benchmark. Below 3% = something is wrong. Below 1% = critical failure requiring immediate intervention.

**Price-point conversion impact:**
- Under $20 products: 3–6% (impulse purchase range — all our planners qualify)
- $20–$50: 2–4%
- $50+: 0.5–2%

This validates our $9.99–$14.99 pricing as optimal for conversion.

#### The KPIs to Track — Specific Fields, Weekly

Every Monday, the health check must capture and trend these specific numbers:

**Shop-Level (from Etsy Shop Manager API):**
- `transaction_sold_count` — total all-time sales
- `review_count` + `review_average` — shop review health
- `listing_active_count` — catalog size
- `num_favorers` — shop favorites (brand awareness proxy)

**Per-Listing (from Stats API, where available):**
- `views_30d` — last 30 days views per listing
- `visits_30d` — last 30 days unique visits
- `favorites_all_time` — total favorites
- `conversion_rate` = orders ÷ visits × 100
- `favorites_rate` = favorites ÷ views × 100
- `photo_count` — number of active images

**Warning thresholds that trigger review:**
| Metric | Warning Level | Critical Level |
|--------|--------------|----------------|
| Conversion rate | <3% | <1% |
| Favorites rate | <2% | <0.5% |
| Views (30 days) | <10 | 0 |
| Review average | <4.9 | <4.8 (Star Seller risk) |
| Message response rate | <98% | <95% (Star Seller loss) |
| Photo count | <7 | <5 |
| Days since last sale | >14 | >30 |

#### Growth Stage Systems — What to Build When

**Rung 1 → 2 (4 → 10 sales): Focus is trust, not scale**
- Set up automated message-to-buyers (Etsy's built-in feature) immediately — fires on every purchase
- Template: Thank buyer, explain instant download location, list supported apps, provide support email
- Purpose: Preemptively answers the 3 most common questions before they become messages

**Rung 2 → 3 (10 → 50 sales): Focus is engagement data**
- Begin tracking per-listing conversion rates weekly
- A/B test hero images — run each version for minimum 2 weeks before switching
- Identify which listings generate favorites but not sales — these have a price/trust gap

**Rung 3 → 4 (50 → 200 sales): Focus is systems preventing regression**
- Weekly health check becomes non-negotiable (already built: `shop_health_check.py`)
- Monthly listing audit for every active listing (not just new ones)
- Begin review velocity tracking — how many reviews per week? Target: review on 15–20% of orders

**Rung 4 → 5 (200 → 1000 sales): Focus is compounding**
- Repeat buyer rate tracking (requires external spreadsheet — Etsy dashboard doesn't show this)
- Customer lifetime value calculation: average order × estimated repeat purchase frequency
- External traffic from Pinterest/TikTok starts to matter for reducing Etsy algorithm dependence

---

### 9.3 — Digital Product Quality Standards for Etsy

#### The #1 Cause of Customer Confusion for Digital Downloads
**Buyers cannot find their download.** Etsy delivers files through:
1. The purchase confirmation email (link)
2. The "Purchases and Reviews" section of the buyer's Etsy account

Buyers on mobile frequently miss both. This is not our fault, but it generates messages and potentially negative reviews if unaddressed.

**Solution (implement immediately):**
Include in every "Message to Buyers" (Etsy's automated post-purchase message):
```
Your files are available instantly! To download:
1. Check your email — Etsy sent a link in your purchase confirmation
2. Or go to: etsy.com → Your Account → Purchases and Reviews → [this order] → Download Files
Need help? Email: Printing3dthings@outlook.com — we respond within 24 hours.
```

#### File Upload Technical Requirements (Etsy Hard Limits)
- Maximum **5 files** per listing
- Maximum **20 MB per file**
- Supported formats: PDF, JPEG, PNG, SVG, ZIP, GIF, MP4
- **Workaround for files >20 MB:** Host on Google Drive / Dropbox; include access link inside a small PDF uploaded to Etsy

**Our current planners are 14–15 MB PDFs** — within the limit. However, if the sticker ZIP + PDF + undated PDF together exceed 5 files at 20 MB each, we need to restructure delivery.

#### AI Disclosure Requirements — MANDATORY (June 10, 2025 Policy)
Etsy's Creativity Standards (updated June 10, 2025) require disclosure in every listing where AI was used to create the product. This is **strictly enforced** — automated detection flags and removes non-compliant listings.

**Required production dropdown settings via API:**
```python
listing_data = {
    "who_made": "i_did",          # must be "i_did" — we designed it
    "when_made": "made_to_order", # digital = made to order
    "is_supply": False,           # finished product, not supplies
}
```

**Required disclosure text** (add to bottom of every description, below copyright section):
```
---
This product was created with AI assistance (DALL-E image generation for cover artwork).
All content has been reviewed, edited, and finalized by the seller.
```

**What qualifies as "using AI":**
- DALL-E / gpt-image-1 for cover artwork — YES, must disclose
- Claude for description writing assistance — YES, must disclose (single-source — verify)
- Using Canva templates — NO disclosure needed
- Python scripts for PDF layout — NO disclosure needed

**Consequences of non-disclosure:**
- Primary: Listing removal (automated)
- Escalation: Repeated violations → account flag
- Severe (100+ undisclosed listings): Shop ban
- Appeal: Compliant listings restored within 3–7 days

**Note:** The shop currently uses DALL-E for planner covers and AI for description assistance. All listings need this disclosure added.

#### Digital Product "Not As Described" Prevention
Items accurately described cannot be claimed as "not as described" under Etsy Purchase Protection. The defense is accuracy.

**High-risk claims that must be verified before listing:**
- "200+ stickers" — count them
- "104 pages" — open the PDF, check page count
- "Works with GoodNotes 6" — test it
- "Fillable fields" — tap a field in GoodNotes and confirm typing works
- "Hyperlinked tabs" — tap each tab and verify navigation
- "Instant download" — confirm files are attached before publishing

**Etsy Purchase Protection for digital products:** If a file is "not as described," the buyer can open a case within 100 days of purchase. Etsy can mediate a refund. Our defense is 100% accurate descriptions, so zero legitimate "not as described" cases are possible.

---

### 9.4 — Etsy Automation & API Policy (Verified)

#### Official Rate Limits (Etsy Open API v3)
| Limit Type | Current Allocation | Mechanism |
|------------|-------------------|-----------|
| Queries Per Day (QPD) | 10,000 per 24 hours | Sliding window (not midnight reset) |
| Queries Per Second (QPS) | 10 per second (standard; actual headers may show higher) | Per-second bucket |
| Response on limit exceeded | HTTP 429 with `retry-after` header | Seconds to wait |

**Rate limit headers on every successful response:**
- `x-limit-per-second` — total QPS allocation
- `x-remaining-this-second` — remaining this second
- `x-limit-per-day` — total QPD allocation
- `x-remaining-today` — remaining in the 24-hour window

**Current code gap:** `tools/etsy_api.py` uses `delays = [2, 4]` for retry (fixed 2s, 4s). This is functional but does not read the `retry-after` header or add jitter. At scale this will cause synchronized retry waves.

#### What Automation Is Allowed vs. Prohibited

**ALLOWED:**
- Creating, updating, and managing listings via the API (this is the API's core purpose)
- Automatically uploading photos to listings
- Reading shop stats and order data
- Auto-responding to messages via Etsy's built-in "Message to Buyers" feature
- Using third-party tools that use the official API (Marmalead, eRank, Sale Samurai, etc.)
- Scheduling listing renewals
- Batch updating prices or tags via the API

**PROHIBITED (immediate suspension risk):**
- Using browser automation or scraping tools (Selenium, Playwright) on Etsy pages
- Artificially inflating shop statistics (views, favorites, reviews)
- Automated systems that generate fake reviews or engagement
- Scraping competitor listings without authorization
- Building tools that "analyze" Etsy data at scale without written Etsy authorization
- Uploading identical or near-identical listings repeatedly (shadow ban trigger)
- Making bulk rapid changes (e.g., changing 50 titles in 10 minutes) — looks like manipulation

**Shadow ban triggers (verified from seller community):**
1. Uploading the same design multiple times with minimal variation
2. Changing titles, tags, or prices on many listings in a single session
3. Keyword stuffing in titles (titles that read unnaturally)
4. Rapid upload velocity (20+ listings in a day for a new shop)
5. Trademark terms in titles/tags (brand names: Disney, Stanley, Lululemon)

**Shadow ban detection signals (watch for 2+ simultaneously):**
- Sudden 40%+ drop in search views with no listing changes
- New listings generate zero initial views
- Traffic shifts to only direct-link traffic (no search)
- Flat impression metrics despite new listing additions

**Recovery from shadow ban:** Fix the underlying trigger. Recovery typically happens within a few days to weeks (varies by severity). The ranking penalty persists even after fixing — similar to credit score recovery.

#### API Security Requirements for Our Code

**Never do:**
```python
# DO NOT hardcode credentials
api_key = "v874xp0m0r4yoh72btmux151"  # NEVER
```

**Always do:**
```python
# Load from environment only
import os
api_key = os.getenv("ETSY_API_KEY")
```

**Token refresh:** Access tokens expire. Our `etsy_api.py` already handles 401 → auto-refresh. This is correct.

**Request to increase limits:** If we hit 10,000 QPD (we won't at current scale, but will at 1000+ listings), contact `developer@etsy.com` with application details and usage estimates.

---

### 9.5 — Continuous Improvement & Regression Prevention

#### The Three-Layer Quality Gate System (Research-Validated)

Quality gates in continuous delivery prevent defective products from reaching customers. Applied to OnBrandCraftz:

**Gate Layer 1 — Pre-Publish (automated):** Runs before any listing goes live
- File spec check (DPI, resolution, file size, page count)
- Listing content check (title length, tag count, required sections)
- AI disclosure presence check
- Photo count check (≥7)
- Price floor check

**Gate Layer 2 — Post-Publish (automated, 48-hour check):** Runs 48 hours after listing goes live
- Confirm listing is active (not removed by Etsy moderation)
- Confirm files are downloadable (test the download URL)
- Check that listing appears in search for its primary keyword

**Gate Layer 3 — Ongoing (weekly manual):** The weekly health check
- Conversion rate trending down vs. previous 4-week average? → Flag for review
- Views trending down? → SEO investigation
- Any new reviews with feedback patterns? → Product improvement queue

#### Early Warning Signal System — Specific Triggers

These specific conditions should generate an automated alert (printed to console, or emailed) when detected during the weekly health check:

| Condition | Warning Message | Required Action |
|-----------|----------------|-----------------|
| Conversion rate < 1% on any listing with >30 visits | CONVERSION FAIL: [listing title] | Review photo, price, description |
| View count drops >40% week-over-week | VISIBILITY DROP: [listing title] | Check tags, title, policy compliance |
| No sales in 14 days | SALES GAP: 14 days without a sale | Run full listing audit |
| Review average drops below 4.9 | REVIEW ALERT: avg now [X] | Read all recent reviews immediately |
| Message unanswered >10 hours | MESSAGE URGENT: [sender] [time] | Respond now — Star Seller risk |
| Photo count < 7 on any active listing | PHOTO GAP: [listing title] | Schedule photo addition this week |
| New listing has 0 views after 7 days | SEO FAILURE: [listing title] | Rewrite title and tags completely |
| Any listing disappears from active | LISTING REMOVED: [title] | Check for policy violation immediately |

#### Regression Prevention Metrics — Track These Weekly

Track these in a simple log file (`data/performance/weekly_snapshots.json`):

```json
{
  "week": "2026-W22",
  "snapshot_date": "2026-05-25",
  "shop": {
    "total_sales": 4,
    "review_average": 5.0,
    "review_count": 2,
    "active_listings": 12,
    "shop_favorites": 0
  },
  "listings": [
    {
      "listing_id": "...",
      "title": "...",
      "views_7d": 0,
      "favorites_all_time": 0,
      "conversion_rate": null,
      "photo_count": 10
    }
  ],
  "alerts_triggered": [],
  "actions_taken": []
}
```

By saving weekly snapshots, we can calculate trends: Is conversion rate going up or down? Are views growing? This prevents the "frog in boiling water" problem where gradual decline goes unnoticed.

#### Review Request Strategy — What Is Allowed

Etsy allows review requests but prohibits incentives. The allowed strategy:

**Channel 1 — Message to Buyers (automatic, fires on every purchase):**
Set once in Etsy Shop Manager > Shop Settings > Message to Buyers. Include:
- Thank you + download instructions (primary purpose)
- One polite sentence about reviews (secondary): "If you love your purchase, a review helps other customers find us — we'd be so grateful!"

**Channel 2 — Follow-up message (manual, sent 3–7 days after delivery):**
For digital products where delivery is instant, send at 3–5 days:
```
Hi [name]! I hope you're enjoying your [product name]. If you've had a chance to use it,
I'd love to hear what you think — a review helps other shoppers find us and means the world
to a small shop. Thank you so much for your support!
```

**What is PROHIBITED:**
- Offering discounts, gifts, or extras in exchange for a review
- Asking specifically for a "5-star" review
- Sending multiple follow-up messages

**Review velocity target:** 15–20% of buyers leave a review. At our current 4 sales, we should have at minimum 1 review. We have this (5-star). Target: 1 review request follow-up sent to every buyer 4 days after purchase.

---

### 9.6 — Code-Level Recommendations

#### Upgrade 1: Improved API Rate Limiting with Retry-After Header

**Current state in `tools/etsy_api.py`:** Fixed `delays = [2, 4]` with no jitter and no `retry-after` header reading.

**Recommended upgrade:**

```python
import random
import time

def _request(self, method: str, path: str, params=None, body=None) -> dict:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    max_attempts = 4
    base_delay = 2.0

    for attempt in range(max_attempts):
        try:
            req = self._build_request(method, url, body)
            with urllib.request.urlopen(req, timeout=15) as resp:
                # Log rate limit headers for monitoring
                remaining_day = resp.headers.get('x-remaining-today', 'unknown')
                remaining_sec = resp.headers.get('x-remaining-this-second', 'unknown')
                raw = resp.read().decode()
                return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Read retry-after header from the error response
                retry_after_raw = e.headers.get('retry-after', None)
                if retry_after_raw:
                    try:
                        wait = float(retry_after_raw)
                    except ValueError:
                        wait = base_delay * (2 ** attempt)
                else:
                    wait = base_delay * (2 ** attempt)
                # Add ±25% jitter to prevent synchronized retry waves
                jitter = wait * 0.25 * (2 * random.random() - 1)
                wait_final = max(1.0, wait + jitter)
                if attempt < max_attempts - 1:
                    time.sleep(wait_final)
                    continue
            # ... rest of error handling
```

#### Upgrade 2: AI Disclosure Auto-Injection in Listing Creation

In `tools/etsy_listing_tools.py`, any function that calls `create_listing` or `update_listing` should automatically append the AI disclosure to the description if it's not already present:

```python
AI_DISCLOSURE_TEXT = """
---
This product was created with AI assistance (DALL-E image generation for cover artwork,
Claude AI for copywriting assistance). All content has been reviewed, edited, and finalized
by the seller. © OnBrandCraftz. Personal use only.
"""

def ensure_ai_disclosure(description: str) -> str:
    """Add AI disclosure to listing description if not already present."""
    if "AI assistance" in description or "ai assistance" in description.lower():
        return description  # Already disclosed
    # Remove existing copyright block and replace with disclosure + copyright
    if "© COPYRIGHT" in description:
        parts = description.split("━━━━━━━━━━━━━━━━━━━━━━━━\n© COPYRIGHT")
        return parts[0] + AI_DISCLOSURE_TEXT
    return description + AI_DISCLOSURE_TEXT
```

#### Upgrade 3: Weekly Snapshot Logger

Add to `tools/shop_health_check.py`:

```python
import json
from pathlib import Path
from datetime import datetime, timezone

SNAPSHOT_FILE = Path("/home/user/Etsy/data/performance/weekly_snapshots.json")

def save_weekly_snapshot(shop_data: dict, listing_data: list, alerts: list):
    """Append this week's snapshot to the performance log."""
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing snapshots
    snapshots = []
    if SNAPSHOT_FILE.exists():
        with open(SNAPSHOT_FILE) as f:
            snapshots = json.load(f)

    week_str = datetime.now(timezone.utc).strftime("%Y-W%W")
    snapshot = {
        "week": week_str,
        "snapshot_date": datetime.now(timezone.utc).isoformat(),
        "shop": {
            "total_sales": shop_data.get("transaction_sold_count", 0),
            "review_average": shop_data.get("review_average", 0),
            "review_count": shop_data.get("review_count", 0),
            "active_listings": shop_data.get("listing_active_count", 0),
            "shop_favorites": shop_data.get("num_favorers", 0),
        },
        "listings": listing_data,
        "alerts_triggered": alerts,
        "actions_taken": [],  # Filled in manually after review
    }

    snapshots.append(snapshot)

    # Keep last 52 weeks only
    if len(snapshots) > 52:
        snapshots = snapshots[-52:]

    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshots, f, indent=2)

    print(f"\n  Snapshot saved → {SNAPSHOT_FILE}")
    print(f"  Trend data: {len(snapshots)} weeks on record")
```

#### Upgrade 4: Listing Pre-Publish Validation Gate (add to etsy_listing_tools.py)

```python
def pre_publish_gate(listing_data: dict, files: list[str]) -> tuple[bool, list[str]]:
    """
    Run all quality gates before publishing. Returns (passed: bool, failures: list).
    A listing MUST NOT publish if this returns False.
    """
    failures = []

    # Gate 1: Title
    title = listing_data.get("title", "")
    if len(title) > 140:
        failures.append(f"Title too long: {len(title)} chars (max 140)")
    if not title:
        failures.append("Title is empty")

    # Gate 2: Tags
    tags = listing_data.get("tags", [])
    if len(tags) < 13:
        failures.append(f"Only {len(tags)} tags (need 13)")
    for tag in tags:
        if len(tag) > 20:
            failures.append(f"Tag '{tag}' is {len(tag)} chars (max 20)")

    # Gate 3: Price floor
    price = listing_data.get("price", {}).get("amount", 0)
    if price < 799:  # $7.99 in cents
        failures.append(f"Price ${price/100:.2f} is below floor of $7.99")

    # Gate 4: AI disclosure
    description = listing_data.get("description", "")
    if "ai assistance" not in description.lower() and "dall-e" not in description.lower():
        failures.append("Missing AI disclosure in description (required since June 2025)")

    # Gate 5: Files
    if not files:
        failures.append("No files attached — cannot publish instant download without files")
    for f in files:
        size_mb = os.path.getsize(f) / (1024 * 1024)
        if size_mb > 20:
            failures.append(f"File {f} is {size_mb:.1f}MB — exceeds Etsy 20MB limit")

    # Gate 6: Description completeness
    required_sections = ["WHAT'S INCLUDED", "COMPATIBLE APPS", "TECHNICAL DETAILS", "FAQ"]
    for section in required_sections:
        if section not in description:
            failures.append(f"Description missing section: {section}")

    passed = len(failures) == 0
    return passed, failures
```

#### Upgrade 5: Message-to-Buyers Auto-Setup Check

Add a one-time check in `shop_health_check.py` to verify the "Message to Buyers" template is set. If the Etsy API returns `auto_message` as empty, warn the operator:

```python
def check_message_to_buyers(client):
    """Verify the post-purchase message is configured."""
    shop_url = f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
    shop = _get(client, shop_url)
    msg = shop.get("sale_message", "") or shop.get("digital_sale_message", "")
    if not msg or len(msg) < 50:
        print("\n  ⚠ WARNING: Message to Buyers is not set or is too short.")
        print("    Go to: Etsy Shop Manager → Settings → Info & Appearance → Message to Buyers")
        print("    This message fires automatically on every purchase.")
        print("    Include: download instructions, app links, support email, review ask.")
    else:
        print(f"\n  ✓ Message to Buyers is set ({len(msg)} chars)")
```

---

### 9.7 — Quality Gate Checklist (Consolidated Master Version)

This is the single authoritative checklist. Run it before every listing goes live.

#### Pre-Publish Checklist (automated via pre_publish_gate)
- [ ] Title: ≤140 chars, primary keyword in first 40 chars
- [ ] Title: Contains year (2026) or "Undated", app name (GoodNotes), "Instant Download"
- [ ] Tags: All 13 used, each ≤20 chars, no special characters
- [ ] Price: Above category floor ($7.99 prints / $9.99 planners)
- [ ] Description: All required sections present (WHAT'S INCLUDED, COMPATIBLE APPS, HOW TO USE, TECHNICAL DETAILS, FAQ, COPYRIGHT)
- [ ] Description: AI disclosure present (mandatory since June 10, 2025)
- [ ] Files: ≤5 files attached, each ≤20 MB
- [ ] Files: PDF opens in GoodNotes without error (manual test, pre-listing)
- [ ] Photos: ≥7 photos uploaded (target 10)
- [ ] who_made = "i_did", when_made = "made_to_order" set in listing API call
- [ ] For planners: page count in description matches actual PDF page count
- [ ] For planners: sticker count in description matches actual sticker count

#### Post-Publish 48-Hour Check (manual)
- [ ] Listing is active in Etsy search (search its primary keyword)
- [ ] Download link works (test via a test purchase or confirm via API)
- [ ] Listing appears with correct photos in correct order
- [ ] No Etsy moderation notice received in seller inbox

#### Weekly Regression Check (automated via shop_health_check.py)
- [ ] No listing has views but zero sales AND >30 days old AND >30 views (conversion failure)
- [ ] No listing has 0 views in the last 7 days (SEO/visibility failure)
- [ ] Review average remains ≥4.9
- [ ] No unanswered messages >10 hours old
- [ ] Shop health snapshot saved to weekly_snapshots.json

---

### 9.8 — Regression Prevention System

#### Metrics to Track Weekly (in weekly_snapshots.json)

| Metric | Target | Warning | Critical | Action |
|--------|--------|---------|----------|--------|
| Total sales (week) | Growing | Flat 2+ weeks | Declining | Review traffic sources |
| Conversion rate (any listing) | ≥5% | <3% | <1% | Rewrite/rephoto that listing |
| Review average | 5.0 | 4.9 | 4.8 | Read all recent reviews immediately |
| Message response rate | 100% | 98% | <95% | Star Seller risk — respond now |
| Views (any listing, 30d) | Growing | <10 | 0 | Rewrite title + tags |
| Active listings | Growing | Same 4+ weeks | Declining | Add new products |
| Days since last sale | <7 | 8–14 | >14 | Full shop audit |
| Photo count (any listing) | 10 | 7–9 | <7 | Add photos this week |

#### The Non-Negotiable Regression Rules (additions to Part 4)

6. **Never mass-edit listings in a single session** — changes to >5 listings in one hour may trigger shadow ban detection. Spread changes over multiple days.
7. **Never use browser automation on Etsy's website** — only use the official API. Selenium/Playwright on Etsy pages violates ToS.
8. **Never list duplicate or near-duplicate products** — every product must be meaningfully different. Same design with a different color alone is not sufficient differentiation.
9. **Never upload more than 3–5 new listings per day** for a shop under 100 sales — Etsy flags rapid upload velocity as suspicious for new shops.
10. **Never remove the AI disclosure once added** — if Etsy has seen a listing without it, the flag may already be processing. Adding it retroactively and leaving it is the correct path.

---

### 9.9 — Sources

All findings in Part 9 are sourced from:

- Etsy Open API v3 Documentation: https://developer.etsy.com/documentation/essentials/rate-limits/
- Etsy API Terms of Use: https://www.etsy.com/legal/api/
- Etsy Creativity Standards (June 2025): https://www.etsy.com/legal/creativity/
- Etsy Star Seller Requirements 2026 (CraftyBase): https://craftybase.com/blog/how-to-become-etsy-star-seller
- Etsy Algorithm 2026 (Marmalead): https://blog.marmalead.com/etsy-algorithm-2026/
- Etsy Algorithm 2026 (ListyBox): https://listybox.com/blog/how-etsy-algorithm-works-2026
- Etsy Review Rating Calculation Update (Value Added Resource): https://www.valueaddedresource.net/etsy-shop-review-ratings-calculation-update/
- Etsy Conversion Rate Benchmarks (Insight Agent): https://www.insightagent.app/guides/etsy-conversion-rate-benchmarks
- Etsy Listing Quality Score (Marmalead): https://blog.marmalead.com/etsy-listing-quality-score/
- Shadow Ban Guide (Dylan Jahraus): https://dylanjahraus.com/this-is-the-fastest-way-to-get-shadow-banned-on-etsy/
- AI Disclosure 2026 (Inkfluence AI): https://www.inkfluenceai.com/blog/etsy-ai-disclosure-explained-2026
- Etsy Policy Compliance & Search Ranking (isCompliant): https://iscompliant.app/Blog/etsy-algorithm-compliance-search-ranking
- Digital Download Seller Guide (Insight Agent): https://www.insightagent.app/guides/digital-downloads-on-etsy-complete-guide
- Etsy Shop Scaling (LinkMyBooks): https://linkmybooks.com/blog/how-to-scale-etsy-shop
- Python Rate Limit Backoff (MarkAICode): https://markaicode.com/python-api-rate-limit-exponential-backoff/
- Etsy Review Request Guide (Alura): https://www.alura.io/post/how-to-ask-customers-for-a-review-on-etsy
- Etsy Seller Protection 2026 (LitCommerce): https://litcommerce.com/blog/how-etsy-seller-protection-works/
- Customer Service for Digital Products (Gold City Ventures): https://goldcityventures.com/how-to-handle-customer-service-for-digital-product-sales-on-etsy/
- KPI Tracking (Sale Samurai): https://salesamurai.io/top-metrics-to-track-what-are-the-key-performance-indicators-kpis-in-a-successful-etsy-strategy/
- Customer Experience Score (Etsy Seller Handbook): https://www.etsy.com/seller-handbook/article/375461267511
- Etsy Star Seller (Outfy): https://www.outfy.com/blog/how-to-become-an-etsy-star-seller/

**Single-source claims (verify before treating as definitive):**
- Case rate threshold of ~1% triggering search suppression (cited in Etsy algorithm guides, not official Etsy documentation)
- Claude AI (description writing) requiring AI disclosure — Etsy's policy targets product creation tools; verify whether copywriting assistance requires disclosure
- The specific "34% mobile CTR increase" for titles under 70 chars (cited by ListyBox only, no independent verification found)
