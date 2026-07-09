# [Your Business Name] — Etsy Automation Hub

> Template doctrine for a self-hosted Frank instance. Sections marked
> `<fill in>` need your business's specifics. Everything else is reusable
> Etsy-platform research and operational doctrine carried over from the
> reference OnBrandCraftz instance this template was built from.

## ⛔ TOP PRIORITY RULE — ZERO TOLERANCE: NEVER LIE TO THE CUSTOMER

> **This rule overrides everything else. No exception. No edge case. No shortcut.**

A customer interacts with: listing photos, listing title, listing description, what's included, file specs, compatibility claims, tag keywords, post-purchase messages, and the digital files they receive.

**Every single one of those touchpoints must be 100% truthful and verified against reality.**

### What "lying" includes — all are hard stops:
- A listing photo that shows a product the customer will NOT receive (AI stand-in, wrong color, wrong design)
- A description that claims a file includes something it does not (wrong count, wrong format, wrong spec)
- A title keyword that misrepresents the product (wrong category, wrong year, wrong compatibility)
- A compatibility claim that has not been tested (e.g. "works in [app]" must be verified)
- A file spec (resolution, DPI, dimensions, page size) that does not match the actual delivered file
- A quantity claim ("200+ stickers", "10 designs included", "50-page planner") that doesn't match what's actually in the delivered file
- A photo showing a variant (color, material, design) not present in the actual delivered file
- Any description section copy-pasted from another listing without verifying it applies to THIS product

### Quality gate rule (non-negotiable):
Before any listing is submitted to {{OWNER_NAME}} for review, an automated quality gate MUST verify:
1. Every file referenced in the description exists on disk and opens without error
2. Counts (pages, designs, items, variants) and file sizes match the description exactly
3. All listing photos were generated from the REAL product files — verified by cross-checking source files used
4. Every compatibility claim has been tested or is an established verified standard
5. Title character count ≤ 70, all 13 tags populated, price matches your pricing tiers
6. The file(s) delivered to the customer were validated by your file-validation tooling with zero errors

**If any gate fails → listing is blocked. Fix first. Publish never comes before truth.**

---

## Mission Statement
> **"Providing the best and most accurate transaction for our customers so we can grow responsibly."**

Every product, every image, every price, every line of code must serve this mission.
- **Best and most accurate transaction** = listings show the REAL product, every claim is verified, customers never have to ask what they bought
- **Grow responsibly** = quality never decreases as volume increases; no listing goes live that fails a quality gate; metrics are tracked weekly so decline is caught before damage is done
- Full operating standards: `data/knowledge_base/business_standards.md` (fill in your own — see the reference OnBrandCraftz instance for a worked example)

This mission statement is a starting template — keep the structure, rewrite the wording to match your own brand voice if you want, but the "real product / verified claims" core should not be diluted.

---

## Store
<fill in> — replace every field below with your own shop's details.

- **Name**: {{BUSINESS_NAME}}
- **Etsy Shop ID**: `<your-etsy-shop-id>`
- **Owner**: {{OWNER_NAME}}
- **Owner email**: `<your-contact-email>`
- **Niche**: `<what you sell — e.g. digital planners, printable wall art, SVG cut files, knitting patterns, etc.>`
- **Brand aesthetic**: `<describe your visual brand — color palette, illustration style, tone>`

---

## Physical Product Hardware (if applicable)
<fill in> If your shop sells 3D-printed products, laser-cut goods, or any other
physically-fabricated item, add a section here documenting your hardware's specs,
material guide, slicer/software settings, and production-quality workflow — the more
detail the better, since this becomes the grounding reference your automation agent
uses to answer questions and write listing copy accurately. See the source
OnBrandCraftz `CLAUDE.md` (the repo this template was built from) for a complete
worked example covering a Bambu Lab P1S 3D printer: build volume, AMS multi-color
system, supported filaments, nozzle types, slicer quality settings, and the
Bambu Studio multi-color SVG import workflow.

If you don't sell physical/fabricated goods, delete this section entirely.

---

## Credentials (all in `.env` — never hardcode, never commit)
- `ANTHROPIC_API_KEY` — Claude API
- `OPENAI_API_KEY` — image generation (gpt-image-1 / DALL-E)
- `ETSY_API_KEY` / `ETSY_CLIENT_ID` — `<set in .env>`
- `ETSY_CLIENT_SECRET` — `<set in .env>`
- `ETSY_ACCESS_TOKEN` / `ETSY_REFRESH_TOKEN` — empty until OAuth is run
- `SMTP_USER` / `SMTP_PASSWORD` — email account used for any manual digital-delivery follow-up

**Never put literal key/secret values in this file or any other file checked into
git.** Only var names belong here — the actual values live in `.env`, which must
stay gitignored.

## Etsy OAuth Status
<fill in — update once you've authorized> Run `python tools/etsy_oauth.py` to authorize (or re-authorize once a token expires/the 90-day refresh window lapses). It writes the access + refresh tokens back to `.env` automatically.
Redirect URI registered: `<your registered redirect URI>`
Scopes needed: shops_r, shops_w, listings_r, listings_w, transactions_r, billing_r, profile_r, email_r, feedback_r, address_r

---

## Product Catalog
<fill in> This is where you document every product you sell: product ID, files,
page/item counts, color theme, structure, target price, target audience — whatever
your quality gates need to verify a listing against. Keep one subsection per product
and update it the moment a product's files change (the truthfulness rule above
depends on this staying current). See the source OnBrandCraftz instance for a
worked example of a planner-product catalog with 4 SKUs.

---

## Color Design System & Theme Catalog
*Research-backed color system based on 2026 design trends (Pantone, WGSN, Envato), color psychology studies, and general market analysis. Useful starting research for any visual-product shop building out a brand palette system — adapt to your own niche.*

---

### Color Psychology — What Each Color Does

| Color Family | Psychological Effect | Best Used For |
|---|---|---|
| **Blue / Indigo** | Focus, calm, trust, creativity. University of Washington study: 12% productivity increase | Finance products, study/work tools |
| **Green / Sage** | Growth, success, calm, emotional stability. Triggers "achievement" feeling | Wellness, habit trackers, goal-oriented products |
| **Purple / Lavender** | Creativity, mindfulness, spirituality, luxury | Lifestyle/journaling products, artistic audiences |
| **Pink / Rose** | Warmth, nurturing, optimism, fun | Cute/kawaii aesthetics, youth-oriented, self-care, bridal |
| **Orange / Coral** | Motivation, energy, combats fatigue. Orange at low saturation increases productivity | Fitness, high-energy audiences |
| **Yellow / Gold** | Optimism, alertness, serotonin boost, focus | Happiness/positivity products, productivity tools |
| **Brown / Mocha** | Comfort, sophistication, warmth, grounded stability | Premium/professional audiences |
| **Charcoal / Black** | Power, elegance, focus, reduces visual noise | Dark-mode products, professional/premium tier |
| **Teal / Aqua** | Balance of calm (blue) + growth (green), futuristic, fresh | Wellness, calming aesthetics, modern design |
| **Cream / Off-White** | Clarity, serenity, "blank canvas" creativity. Pantone 2026 CoY | Minimalist, journaling, mature audiences |

---

### 2026 Color Trend Authorities

**Pantone Color of the Year 2026:** Cloud Dancer `#F4F0EA` — soft airy off-white between warm and cool. Radiates calm, clarity, serenity. "Blank canvas for creativity."

**WGSN 2026 Key Color:** Transformative Teal `#3B8E8A` — fusion of dependable dark blue and aquatic green. Grounded yet futuristic, represents change and connection with nature.

**Trending 2026 Macro Palettes (Envato/Adobe research):**
- **Sunwashed Soft** — peachy warm pastels, sun-faded warmth (peach, cream, warm sand)
- **Mermaidcore** — shimmering aqua, seafoam, pearl, iridescent violet
- **Clubroom Contrast** — bold black + gold luxury (underserved in many niches)
- **Warm Earth Revival** — taupe, sandy beige, deep chocolate, chestnut (brown having a major moment)
- **Spring Vivid Brights** — Alexandrite purple, Lava Falls red-orange, Fuchsia, Mint (bold and punchy)
- **Deep Botanical** — forest green, terracotta, sage, warm botanical greens

### Color Design Rules (general — apply to your own products)

1. **Maximum 4 colors per product theme** — Primary + Accent + Mid-tone + Neutral (plus a near-black for text)
2. **60-30-10 rule** — 60% neutral/background, 30% primary color, 10% accent pops
3. **Minimum contrast ratio 4.5:1** — text on background (WCAG AA accessibility standard)
4. **Never pure black (#000000)** — use a deep tinted black matching the palette
5. **Never pure white (#FFFFFF)** — use a cream/tinted neutral
6. **Dark mode backgrounds** — use the `#1A1A2E` to `#2D2D2D` range, never pure black
7. **Consistency across all listing photos** — props, backgrounds, and accent items must match the product's color theme

<fill in> Build your own per-product theme catalog and theme-to-product mapping table here once you have products defined — see the source OnBrandCraftz instance for a worked example with 12 named themes (Cherry Blossom, Sage Garden, Celestial Night, etc.) mapped to specific SKUs.

---

## Etsy Listing Format Requirements

### 2026 Conversion Optimization Standards
Research-backed rules that apply to any Etsy digital-product listing:

**Titles:**
- Etsy weights the **first 40 characters most heavily** — lead with the exact keyword buyers type
- Structure: `[Primary Keyword] | [Secondary Keyword] | [Feature Keyword] | [Occasion/Compatibility]`
- Use natural language, not keyword stuffing — Etsy's 2026 algorithm penalizes repetition
- Include the year (if relevant), key compatibility/format info, and "Instant Download"

**Tags:**
- Use all 13 tags — every empty slot is a missed ranking opportunity
- Each tag must be a **multi-word buyer-intent phrase** (e.g., "goodnotes planner" not just "planner")
- Tags must align with title keywords — exact title phrases in tags boost ranking
- Use long-tail over broad: a specific descriptive phrase beats a single generic word
- Max 20 characters per tag including spaces

**Descriptions:**
- The **first two sentences** must hook the buyer AND contain the primary keyword (mobile users see only this much before the fold)
- Include primary keyword naturally in sentence 1 for Google external search indexing
- Use emoji section headers (━━━ dividers) for scanability — most buyers skim, not read
- Answer the 4 buyer questions: What is it? What's included? What format/compatibility? How do I get it?
- FAQ section reduces pre-purchase questions and refund requests

**Photos — the #1 conversion factor:**
- **46% of Etsy purchases are on mobile app** (Q4 2025 official data) — every photo decision is mobile-first
- Lifestyle thumbnail typically outperforms flat white background for click-through (verified pattern, exact multiplier varies by niche — test your own)
- Use all 10 photo slots — each additional image increases conversion rate
- Recommended size: **2400×2400px square** (outperforms 2000px by estimated 7–12% CTR)
- Keep subject in center **70% of frame** — Etsy crops thumbnails on mobile
- Add **5% neutral-tone padding** around edges — prevents mobile thumbnail cropping
- **3 props max per scene** — more than 3 clutters; fewer than 3 looks staged and flat

<fill in> Build out your own pre-written title/tag/description/pricing templates per product once your catalog is defined — see the source OnBrandCraftz instance for fully worked examples (titles, 13-tag sets, full descriptions with all required sections, and a 10-photo prompt sequence) for a digital-planner product line.

---

## Production Pipelines for Specific Product Types

The reference OnBrandCraftz instance documents two fully detailed, niche-specific
production pipelines that are **examples, not generic doctrine** — adapt or replace
them entirely based on what you actually sell:

- **3D-printed SVG sign pack pipeline** — covers SVG/3MF file-quality thresholds,
  multi-color layer packaging, Bambu Studio workflow, and a full pre-publish quality
  gate checklist for sign-style 3D print products.
- **Printable wall art pipeline** — covers minimum art file resolution, multi-size
  print ZIP delivery, room-photo composition rules, and pricing tiers for printable
  art listings.

If your shop sells either of these product types, copy the relevant pipeline from
the source repo's `CLAUDE.md` and adapt it. If you sell something else entirely
(patterns, templates, courses, stickers, fonts, etc.), write your own equivalent
pipeline here: file-quality gates, packaging rules, and a pre-publish checklist
specific to your product type. The universal rules below (Listing Photos, Universal
Listing Rules) apply regardless of what pipeline you write.

### Universal Listing Rules (apply to ALL listing types — no exceptions)

These rules apply regardless of product category. Violations block publishing.

**No duplicate images.** All photo slots must contain unique images. No photo may appear more than once in a listing. Verify by hash before upload.

**Lifestyle photos must be generated with an image-editing model using the actual downloadable product file as input.** No AI-generated stand-in products. No placeholder art. The exact files the customer downloads are passed to the image-edit endpoint as the input image. This is the only method that guarantees the listing photo shows what the customer actually receives.

**EVERY photo in EVERY listing should be produced with a consistent, deliberate image pipeline — not ad-hoc screenshots or stock photos.** Per-slot method:
- Lifestyle / detail shots: never generate from a text prompt alone — always edit/render starting from the real product file(s) as input
- Flat lays / collection shots with multiple designs: generate the background, then paste the REAL design files on top pixel-perfect (image-edit models garble small text when given 5+ reference inputs at once)
- Infographics / spec sheets / how-to graphics: generate the background, then overlay text separately (AI image models cannot reliably render text)

**Every listing undergoes a complete pre-publish checklist before going live.** A listing cannot be submitted for review unless every gate for its product category has been run and passed. "Looks good" is not a gate. The gate is code.

---

## Business Structure & Tax — Research-Backed Rules (2026)

*This section reflects US federal tax rules as of 2026 and is general research, not
legal or tax advice. If you operate outside the US, or want certainty for your
specific situation, consult a licensed accountant/attorney in your jurisdiction.*

### Legal Structure
- **Now (under ~$50k net profit):** Sole proprietor + single-member LLC. LLC = same Schedule C filing, zero extra tax complexity, but gives liability protection if you ship physical goods.
- **S-Corp election threshold:** $50,000–$80,000+ in *consistent annual net profit* (not gross revenue). Filing: Form 2553 within 75 days of desired effective date.
- **S-Corp math at $100k net:** SE tax as sole prop ≈ $14,130 → S-Corp with $50k salary ≈ $7,650 payroll taxes → ~$6,480 gross savings → net savings after compliance ≈ $2,500–$4,500/yr.
- **Physical-goods adjustment:** COGS from materials reduces net profit, so gross revenue threshold to hit $50k net is higher than a pure-digital seller.

### 1099-K Thresholds (One Big Beautiful Bill Act, signed July 4, 2025)
- **Federal threshold permanently restored:** $20,000 AND 200+ transactions
- All Etsy income is taxable regardless — the 1099-K is informational only
- State thresholds vary; check your state separately

### Key Deductions
| Expense | Where on Schedule C |
|---|---|
| Materials/COGS for any physical product line | COGS, Part III, Line 36 |
| Equipment (printers, tools, upgrades) | Section 179 (2026 limit: $2.56M) or 100% bonus depreciation |
| Software/AI subscriptions (Canva, Adobe, Claude, OpenAI, etc.) | Line 27a |
| Etsy fees (transaction % + payment processing) | Line 10 |
| Home studio dedicated space | Form 8829 or $5/sq ft simplified |
| Quality samples photographed for listings | Line 22 (advertising) — NOT COGS |
| Vehicle mileage (post office runs, supply runs) | $0.725/mile (2026 rate) |

### Hobby vs. Business (OBBBA Made This Permanent)
Hobby sellers now pay tax on **gross revenue with zero deductions**. Protect business status: separate bank account, maintain bookkeeping, document pricing adjustments based on sales data, show profit in 3 of last 5 years.

---

## SKU Naming Convention & Version Control

All product files should follow a consistent naming pattern. Example structure (replace prefixes/IDs with your own product line conventions):
```
[ProductLine][ProductID]_[ThemeName]_v[N].[ext]

Examples:
PRD0001_ThemeName_v2.pdf          ← main product file, version 2
PRD0001U_ThemeName_v2.pdf         ← variant version (e.g. undated/alt-color/alt-size)
PRD0001_ThemeName_VariantName.pdf ← named variant (e.g. cover/color variant)
PRD0001_S01_AssetCategory.png     ← supplementary asset (e.g. sticker sheet, layer file)
SET-0001_PRD0001_v1.jpg           ← multi-design pack / bundle file
```

Rules:
- Increment `_v#` on every file re-uploaded to buyers
- Keep an `_archive/` subfolder — never overwrite old versions
- Maintain a `product_catalog.json` as source of truth (product_id, etsy_listing_id, price, file_paths, status, version, last_updated)
- Automation scripts read from the catalog — never hardcode listing IDs or file paths

---

## Automation Stack — What to Automate vs. Keep Manual

This is a reusable categorization pattern — fill in the right column with your own
tool names once you've built or adapted them; the framework (what kind of task
belongs in which bucket) applies to any shop.

### Automate
| Task | Tool |
|---|---|
| AI disclosure on new listings | `<your script>` |
| Image generation for listings | `<your image pipeline>` |
| Listing creation from templates | Etsy API scripts |
| **Upscale undersized art files** | `<your upscale script>` — run before creating any listing from AI-generated art that's below your minimum resolution gate |
| **Multi-size print ZIP creation** (if you sell printable art) | `<your packaging script>` — run after upscaling, before uploading to Etsy |
| **Tags audit + fix** | `<your tag-audit script>` — run after any batch of new listings |
| Post-purchase buyer message | Etsy native auto-messages (set in dashboard) |
| Shipping label generation (physical goods) | A shipping tool (e.g. Pirate Ship) |
| Financial tracking / COGS | A bookkeeping tool (e.g. Craftybase) |
| Social post scheduling | A scheduling tool (e.g. Buffer/Tailwind) |
| Shop health snapshots | `<your health-check script>` |
| **Backup product source files after producing a new product** | A backup script run as soon as a new product's source files are generated, since product data directories are typically gitignored and have no other durable backup. Hand the output to the owner to save in their own cloud storage. |
| **Log infrastructure/dashboard incidents for the agent** | Append a short dated entry (symptom, root cause, fix) to an `ops_runbook.md` any time the agent diagnoses or fixes a problem with the live site, API, deploy, or credentials — this lets the agent answer "why was X broken?" directly from a grounded log instead of guessing. Keep entries short — this is a log, not a report. |
| **Archive anything before deleting it (recycle bin)** | BEFORE removing any code block or file, archive it first via a trash/recycle-bin utility. Land everything in a committed vault (ledger + byte-exact copies), pruned after a retention window, so an accidental or regressive deletion can be recovered. Nothing deleted should be unrecoverable — and the vault must stay committed if your deploy target is ephemeral (uncommitted files are lost on redeploy). |

### Keep Manual (human judgment required)
- Review responses — tone matters; a scripted response reads as damage control
- Custom order pricing and feasibility
- Pricing changes (requires market analysis)
- New product launch decisions
- Negative review responses
- Final product/art quality approval before publishing

### The One Automation Most Sellers Skip
Etsy allows exactly **one** post-delivery buyer message. Set it to something like:
> "Hope you love your [product name]! If you have 30 seconds, a review means everything to a small shop."
Set this in Etsy Dashboard → Shop Manager → Messages → Auto-reply.

---

## Weekly & Monthly Operational Cadence

### Weekly (Friday, 30 min)
- Check Etsy Search Visibility Dashboard — fix any flagged listings immediately
- Review 7-day conversion rate per listing (Etsy Analytics → Listings)
- Respond to any outstanding messages or reviews
- Check production/restocking queue if you sell anything made-to-order

### Monthly (1st of month, 2 hours)
- Run your shop health-check script — full snapshot
- Compare conversion rates, views, revenue vs. prior month
- Identify listings with high views but low conversion (photo or price problem)
- Update seasonal keywords in top listings (update 6 weeks before peak season)
- Export orders for COGS/bookkeeping reconciliation

### Quarterly
- Estimated tax payment (Jan 15, Apr 15, Jun 15, Sep 15 — US)
- New product launch or existing product upgrade decision
- Review competitor pricing in your top niches
- S-Corp salary draw if applicable

### Seasonal Keyword Calendar (6 weeks before each peak)
| Peak Season | Update By | Keywords to Add |
|---|---|---|
| Back to school | Mid-July | `<your back-to-school keywords>` |
| Holiday gifting / New Year | Mid-October | `<your gifting/new-year keywords>` |
| Valentine's Day | Early January | `<your Valentine's-relevant keywords>` |
| Spring reset | Mid-January | `<your spring/fresh-start keywords>` |

---

## Etsy 2026 Algorithm — Confirmed Changes

### Change 1: Title Length Cap (CRITICAL — affects all listings)
- **Titles > 70 characters face mobile ranking penalty**
- Mobile = 70%+ of Etsy traffic in 2026
- Listings that shortened to <70 chars saw +34% mobile CTR and avg +4.2 position ranking boost
- **Formula:** Lead with product noun → include top 3 keywords → keep buyer-friendly language
- Example: `Kawaii Digital Planner 2026 | GoodNotes iPad | Sticker Pack` (61 chars) ✓ — adapt the structure to your own niche's primary keyword

### Change 2: Shipping Cost Penalty
- US listings with shipping above **$6** face reduced search visibility
- Action for digital products: shipping = free, already optimal
- Action for physical products: absorb shipping into price, offer free shipping or cap at $5.99 flat

### Change 3: Search Visibility Dashboard (new tool)
- Etsy now shows exactly which listings have reduced visibility and why
- Flags: title quality, shipping cost, missing attributes, photo quality
- Check weekly — bulk edit directly from the dashboard

### Two-Phase Algorithm System
Etsy's search operates in two distinct phases:
1. **Query Matching** — checks titles, tags, categories, attributes, and description keywords. If you don't match the query, you never enter the ranking pool.
2. **Ranking** — once matched, Etsy ranks results using engagement signals + personalization. This phase is where the real differentiation happens.

**Personalization (2025–2026 structural shift):** Etsy ranks results based on each shopper's individual behavior history — past clicks, favorites, purchases, preferred price ranges. Two shoppers searching the same keyword see different results. You cannot optimize for "the algorithm" — you optimize for the best possible signal from any shopper who lands on your listing.

### Ongoing Ranking Factors (Priority Order)
1. Click-through rate from search (most important — hero photo drives this)
2. Add-to-cart and purchase rates relative to impressions
3. **Dwell time** (2026 new factor) — how long a shopper stays on your listing after clicking; staying to read the description or watch a video boosts your score
4. Keyword relevance (title, tags, attributes, description first paragraph — NLP-based, not exact match)
5. Star Seller status — confirmed algorithmic weight; Star Sellers see more listing views and sales than comparable non-Star Sellers
6. Free shipping
7. Listing recency (new listing boost: **a few hours to a few days**, variable by search volume — NOT weeks)
8. Semantic intent matching (exact keywords less critical than intent; NLP understands synonyms)

**New listing boost — CORRECTED:** Etsy gives new listings a temporary boost so the algorithm can quickly learn how shoppers interact with them. Duration is a few hours to a few days depending on search volume in that category. This is NOT a 14-30 day window. Regularly renewing listings just for the boost is ineffective — focus on improving conversion rate instead.

**Ranking drop causes:**
- Policy violations reduce shop quality score, which drags ranking of ALL remaining listings
- Editing a listing can temporarily reduce its search visibility (expect 2–3 weeks to recover)
- Titles >70 chars (mobile penalty), shipping >$6 (US domestic penalty)
- Seasonal shifts in buyer demand (looks like a drop but is just category-level traffic change)

**Recovery timeline after fixes:** Most sellers see views recovering within 2–3 weeks after optimizing titles/tags. Compliance violations take weeks to months because the algorithm needs to see consistent positive signals before trusting the shop again.

### Digital Product Specific
- Category attributes and description completeness matter MORE than for physical (no fulfillment signal)
- Fill every attribute field completely
- For digital product thumbnails: **clean, high-contrast image on neutral background can outperform lifestyle mockup** for CTR — test both

### Star Seller Requirements (Digital Products)
| Requirement | Threshold | Digital Product Notes |
|---|---|---|
| Message response rate | 95%+ within 24 hours | **Main challenge** — Etsy's API has no buyer-messaging endpoint for third-party apps, so this can't be fully automated. The only mechanisms that earn Star Seller credit are manual Quick Replies and Etsy's built-in Temporary/Weekly Auto-Reply windows — see "Customer Service" below |
| On-time shipping | 95%+ | **Auto-pass** for digital products — instant digital delivery = 100% on time, always |
| Average rating | 4.8+ stars | Need 5+ orders in the review window |
| Minimum orders | 5 orders, $300+ total | Over the past 3 months |

Star Seller status is the path to catalog-wide ranking lift. For most digital-product shops, message response rate is the only real challenge — all other criteria are effectively free.

---

## Etsy Ads Strategy (Research-Backed, 2025–2026)

### ROAS Benchmarks
| Product Type | Typical ROAS | Breakeven ROAS | Top Performer |
|---|---|---|---|
| Digital products | 4.0–8.0x | 1.1–1.5x (near-zero COGS) | 12.0x+ |
| Physical products | 2.0–4.0x | 1.5–2.0x | 6.0x+ |
| Etsy-wide average | 2.8x | varies | — |

Digital products have enormous margin advantage — with zero COGS, even a 1.5x ROAS is profitable. Target 4x+ as the threshold to scale.

### Budget & Bidding
- **Starting budget:** $3–5/day for new shops — sufficient to generate data without burning money
- **Average CPC:** ~$0.50 per click → $5/day = ~10 clicks/day
- **Scale rule:** Once a listing hits ROAS > 4x consistently, raise budget by 20–30% per week (never double overnight — confuses the algorithm)
- **Run time before judging:** Minimum 30 days — Etsy's algorithm needs time to learn your ideal customer

### Which Listings to Advertise
1. **Only advertise listings with proof of life** — at least a few favorites, saves, or one organic sale before adding ads
2. **Best candidates:** Listings that already convert well organically (high conversion rate relative to views)
3. **Never spread ads across the entire catalog** — burns money without learning; pick 3–5 max to start
4. **Stop promoting** any listing that spends >$30 with zero orders
5. **Keep running** any listing with ROAS > 2x for 30+ days, then assess

### Kill Thresholds
- Kill immediately: listing spends $30+ with zero orders (not converting at all)
- Kill after 30 days: listing ROAS < 1.5x with no upward trend
- Pause and fix: listing gets clicks but zero purchases (photo or price problem, not ads problem)

---

## Review Generation Strategy (Research-Backed)

### Review Milestones — Impact on Conversion
| Reviews | Effect |
|---|---|
| 0 | Buyers 270% less likely to purchase (Capital One Shopping research) |
| 5+ | Significant trust signal established — the first critical milestone |
| 20+ | 47% of consumers hesitate to buy from shops with <20 reviews; this threshold removes that hesitation |
| 25+ | Reviews stop being a limiting factor on conversion |
| 50+ | Competitive with established sellers in most digital product niches |

### Legal Constraint — FTC Consumer Reviews Rule (CRITICAL)
**NEVER offer incentives for reviews.** The FTC Consumer Reviews Rule (effective Oct 2024) prohibits:
- Discounts or coupons in exchange for a review
- Free product in exchange for a review
- Any conditional reward tied to reviewing

Penalty: **up to $53,088 per violation.** The ONLY legal review strategy is:
1. Deliver an exceptional product (quality does all the heavy lifting)
2. Send the Etsy post-delivery auto-message asking for a review (set this in Shop Manager)
3. Include a clean reminder in the post-purchase message — no conditions, just a request

### Legal Review Tactics
- **Post-purchase message:** Signed by the owner, professional tone, no conditions attached
- **Etsy auto-message after delivery:** Set in Shop Manager → Messages → "Message to buyers" → check "Send after delivery" — keep it to one sentence: a thank-you + soft review ask
- **Reply to all reviews** — responding to reviews (especially negative ones) shows future buyers you care, which has secondary conversion impact
- **Quality drives reviews:** The #1 review driver is a product that works flawlessly out of the box. Every support message is a review that didn't happen.

---

## gpt-image-1 Prompt Engineering (Verified Techniques)

### Core Architecture
gpt-image-1 is an **instruction-tuned model** — NOT a diffusion model. Midjourney prompting won't transfer. It reads your prompt like a sentence and responds to photography vocabulary extremely well.

### The 5-Slot Prompt Formula
```
[Subject + Material + Color] on/in [Surface/Scene + Context],
[Light source + direction + quality],
[Camera + lens + angle],
[Finish descriptor],
[Constraint clause]
```

**Example (generic product-on-surface lifestyle shot — adapt subject/scene/props to your own product):**
```
[Your product], photographed at a natural angle on [a surface matching your brand
aesthetic — e.g. linen-textured desk, wood table, marble counter].
Soft diffused window light from the left, warm white balance, gentle shadow to the right.
50mm lens, eye-level angle, subject fills 65% of frame.
Sharp commercial photography, slight depth of field on background.
The image contains only [your product] and [1–3 props matching your brand color theme].
No hands, no text overlays, no visible studio equipment.
```

### THE CARDINAL RULE — Every Listing Photo Must Show the REAL Product (NEVER VIOLATE)
**Every single listing photo must contain the actual product — no exceptions, no substitutes.**
- AI-generated lifestyle scenes with AI-generated stand-in products are BANNED — they show the customer something they will NOT receive
- This rule enforces the mission statement: "Best and most accurate transaction — listings show the REAL product"
- A lifestyle image that looks beautiful but does not contain the actual product is worse than no lifestyle image at all
- **Multi-product photos (flat lays, collections, gallery walls): EVERY product file must be passed as input.** Feeding one design and prompting "show N variations" makes the AI invent products the customer doesn't get — this is a hard violation of the cardinal rule

### THE STANDARD LIFESTYLE METHOD — `images.edit` With the Real Product as Input (MANDATORY, ALL CATEGORIES)
The real product file is passed to gpt-image-1's **edit endpoint** as the input image, and the prompt tells the model to render it physically in the lifestyle scene. The model handles perspective, curvature, lighting, shadows, and placement natively — no manual coordinate compositing.

**Workflow (every product type, every scene):**
1. Load the REAL product file(s): the actual design file, photo, or document — never a description alone
2. Call `client.images.edit(model="gpt-image-1", image=<real file(s)>, prompt=<scene>, quality="high", input_fidelity="high")`
3. Prompt structure: "This image is the flat design of [product]. Render it as a single photorealistic product photograph, [physically placed/mounted/wrapped] in [scene]. The EXACT design from this image must appear with all colors, text, and details preserved accurately."
4. For multi-product shots, pass ALL product files as a list and reference each by number in the prompt
5. **Verify the output against the source files before keeping** — zoom in and compare colors, text, and composition; regenerate on any drift
6. Upscale to your target listing photo resolution (e.g. 2400×2400)

Build (or adapt) a single pipeline tool that automates this whole quality loop —
palette/text auto-extraction from the source file, a per-product-type "physics"
template describing how the real product surface should look when rendered, and an
automated verification + retry step that compares the render against the source
file before it's accepted. See the source OnBrandCraftz instance's
`tools/listing_photo_pipeline.py` for a complete reference implementation of this
pattern if you want a starting point.

For flat-lay / overhead collection shots with zero perspective, prefer a
pixel-perfect paste of the real files over an AI-generated background rather than
feeding multiple designs through images.edit — multi-design edit calls reliably
garble small text.

**Design-side rule (prevents unfixable shots):** tiny text and fine repeating edge geometry (e.g. small print, fine line patterns) often cannot survive image-edit rendering reliably. Designs with those features should appear in lifestyle scenes via a more robust sibling design, and be shown exactly in a pixel-perfect flat lay instead. For new designs intended for lifestyle renders, prefer bold shapes and large, simple lettering.

### Negative Prompting — gpt-image-1 Has No Negative Field
**Never** copy Midjourney negative prompts. Instead use positive constraint clauses at the end of every prompt:

```
"The image contains only [list exact elements].
No hands are visible. No text overlays. No watermarks.
No studio lighting equipment visible. No other objects appear in the frame."
```

| To exclude | Write |
|---|---|
| Hands/people | "No hands, no people, no human figures visible." |
| Text in image | "No text, labels, or typography appears anywhere in the image." |
| Fake art on walls | "All walls are completely bare and empty — no art, no prints, no decor hung on walls." |
| Clutter | "Exactly three props are visible: [list them]. No other objects appear." |
| Wrong colors | "The color palette is strictly [X] — no other dominant colors appear." |

### Style Consistency Across a Batch (No Seed Parameter)
Build a `STYLE_ANCHOR` string and paste it identically into every prompt in the batch:

```python
STYLE_ANCHOR = (
    "Photography style: bright airy editorial Etsy lifestyle photography. "
    "Warm cream and natural linen tones throughout. Soft diffused window light "
    "from the left, warm white balance, gentle shadows to the right. "
    "Camera at eye level, 50mm lens equivalent, slight depth of field on background. "
    "No hands, no people, no text overlays, no studio equipment visible."
)
```

For maximum consistency: pass the first accepted image as `@image1` in subsequent calls with:
`"Maintain identical lighting, color temperature, surface texture, and photography style as Image 1. Change only [specific element]."`

### Material Vocabulary That Works
| Material | Vocabulary |
|---|---|
| Linen | "natural linen texture, visible weave pattern, slightly rumpled, warm off-white" |
| Rattan | "natural rattan weave, warm honey-brown tones, slightly matte finish" |
| Ceramic | "matte ceramic surface, subtle micro-texture, slightly imperfect handmade quality" |
| Wood (oak) | "natural light oak, visible wood grain, matte satin finish, warm golden undertone" |
| Boucle | "boucle fabric texture, looped cream-white pile, soft sculptural surface" |
| Terracotta | "terracotta clay surface, slightly dusty matte texture, warm burnt orange tone" |

### Lighting Vocabulary
| Effect | Prompt |
|---|---|
| Morning lifestyle | "soft diffused window light from the left, warm white balance, gentle shadow to the right, morning atmosphere" |
| Cozy evening | "warm amber lamp glow from upper right, soft ceiling ambient light, intimate evening atmosphere, no harsh shadows" |
| Clean product | "bright even natural daylight, diffused overhead, cool-neutral white balance, no shadows on product" |
| Golden hour | "golden hour backlighting, warm orange-yellow light from upper right, long soft shadows forward" |

### gpt-image-1 Quirks
- **Iterate, don't overload:** Start with clean base prompt → refine with single-change follow-ups
- **No "8K ultra-detailed":** Camera/lens vocabulary beats generic quality modifiers. Use `"sharp commercial product photography"` not `"8K UHD photorealistic"`
- **Text rendering:** Put literal text in quotes or ALL CAPS. Even then, composite text in a design tool afterward — don't trust in-image text
- **Hands:** Even with "no hands visible," generation can slip. Regenerate rather than edit — editing creates worse artifacts
- **Color drift:** Re-specify hex or descriptive colors in every prompt (model doesn't remember previous calls)
- **Content filters on home/bedroom scenes:** Use "interior photography" language, not "photoshoot" language. Describe furniture, not atmosphere
- **Quality setting for production:** `quality="high"` for hero images; `quality="medium"` for background generation (composited anyway)
- **`input_fidelity="high"`:** Use when editing an existing image to preserve composition while changing one element

---

## Etsy API v3 — Technical Reference for Autonomous Operation

### Hard Limits (Cannot Be Coded Around)

| Limit | Value | Notes |
|---|---|---|
| **Digital files per listing** | 5 maximum | Hard platform limit — ZIP bundles to work around |
| **File size per digital file** | 20 MB per file | Hard limit — compress files before upload |
| **Access token lifetime** | 1 hour (3600s) | Must refresh automatically before expiry |
| **Refresh token lifetime** | 90 days | After 90 days, you must re-authorize via your OAuth script |
| **Rate limit — per second** | ~150 QPS (example) | Varies per app; check x-limit-per-second header |
| **Rate limit — per day** | ~100,000 QPD (example) | Sliding window (not fixed 24h reset); check x-limit-per-day header |
| **Rate limit exceeded** | HTTP 429 + `retry-after` header | Always implement exponential backoff; honor the retry-after value |
| **Scopes** | Immutable after authorization | Cannot elevate permissions without full re-auth |

### OAuth Token Auto-Refresh (Required for Autonomous Operation)

Tokens expire every **1 hour**. The refresh flow:
```
POST /oauth/token
  grant_type=refresh_token
  client_id=<ETSY_CLIENT_ID>
  refresh_token=<ETSY_REFRESH_TOKEN>
```
- Returns a new access token AND a new refresh token (90-day clock restarts)
- Does NOT require user action — fully automatable
- Write new tokens back to `.env` immediately after refresh
- **Must implement token refresh before any batch operation** — check token age and pre-refresh if within 10 minutes of expiry
- **Refresh token expires after 90 days** — you must manually re-run your OAuth script every 90 days or when a 401 is returned on the refresh endpoint

### Rate Limiting Response Headers (Read These on Every Request)

```
x-limit-per-second       → your total QPS allocation
x-remaining-this-second  → calls left this second
x-limit-per-day          → your total daily allocation
x-remaining-today        → calls left in rolling 24-hour window
```

**Autonomous batch strategy:** Check `x-remaining-this-second` before each call. If ≤ 2, sleep 1 second. If 429 received, read `retry-after` and wait exactly that many seconds before retrying.

### Known API Quirks and Workarounds

| Issue | Workaround |
|---|---|
| Non-deterministic 403 on `PATCH listings/{id}` ("listing is not editable") | Implement 3-attempt retry with 2s delay — it's a server-side race condition, not a real permission error |
| `GET listings/draft` returns 404 | Correct endpoint: `GET shops/{shop_id}/listings?state=draft` |
| `getListingImageDeprecated` returns 404 | Use `getListingImages` (current endpoint) |
| Duplicate image rank on rapid upload | Add 2s delay between sequential image uploads to same listing |
| Listings created via API previously couldn't be activated via API | Resolved as of Q1 2026 — `state=active` works on PUT |

### Suspension Triggers — What to Never Do

- **Identical descriptions across listings** — Etsy's spam detection flags templated text applied to many listings
- **High-velocity bulk listing creation** — ramp up gradually (max 10–20 new listings per day)
- **Testing transactions on a live production account** — use a separate test account for API transaction tests
- **API tools banned by Etsy** — several drop-shipping automation tools had API access revoked in the past; never use tools with a history of platform bans
- **Trademark terms in titles/tags** — even accidental use triggers shop quality score penalty affecting ALL listings

### Cascade Penalty — How One Violation Hurts Everything

Etsy uses a **shop quality score** that aggregates across all listings. When a single listing gets flagged:
1. The flagged listing is removed
2. Your shop quality score drops
3. Every other listing in the shop ranks lower
4. Lower rankings → lower conversion → further algorithmic downranking

**Recovery:** Not automatic. Requires consistent positive engagement signals over weeks to months. Removing the violation stops further damage but does not restore ranking immediately.

**Triggering violations:** Trademark terms in tags, undisclosed AI content, undisclosed production partners, keyword stuffing, missing return policies.

---

## AI-Generated Content — Mandatory Disclosure Protocol

### What Etsy Currently Requires (Updated June 10, 2025)

Etsy's Creativity Standards (etsy.com/legal/creativity) were updated June 10, 2025 to explicitly require:

1. **Disclosure in the listing description** — Must include a statement that AI tools were used
2. **Correct "who made it" categorization** — List as "Designed by a seller" (not "Made by a seller")
3. **API field values**: `who_made: "i_did"`, `when_made: "made_to_order"`, `is_supply: false`

**Required disclosure language (add to every listing description — bottom, before copyright):**
```
━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ABOUT THIS DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━
This product was designed using AI image generation tools, with original prompts,
curation, and finishing by the seller. All products are reviewed for quality before listing.
```

### What Gets Flagged and Removed

- Listings that **look AI-generated but have no AI disclosure** — automated detection catches these
- Over **17,000 listings removed** in early 2025 for disclosure violations
- Single violation = listing removal; repeated violations = account suspension
- Detection methods: automated image analysis + member reports + manual moderation

### What Is Allowed

- Using AI tools to generate art/designs = allowed WITH disclosure
- Using template tools (e.g. Canva templates) = allowed WITH disclosure (June 2025 update banned minimally-modified templates without disclosure)
- All digital product categories are covered by the June 2025 update
- Seller still must be the designer — using someone else's prompts without modification is not allowed

### Pre-Publish Checklist for AI-Generated Products

- [ ] AI disclosure paragraph added to listing description
- [ ] `who_made` field set to `"i_did"`
- [ ] Product categorized as "Designed by a seller" in Etsy dashboard
- [ ] Original prompts used (not copied from another seller)
- [ ] Seller has reviewed and approved the output before publishing

---

## Customer Service — Autonomous Response System

### What Etsy's Built-In System Actually Supports

| Feature | What It Does | Star Seller Credit? |
|---|---|---|
| **Quick Replies** | Saved templates, manually sent by seller | Yes — counts as a reply |
| **Temporary Auto-Reply** | Active for up to 5 days (vacation, busy period) | Yes — counts as first reply |
| **Weekly Auto-Reply** | Fires outside set business hours for first message only | Yes — counts as first reply |
| **AI Writing Assistant** | Drafts suggested responses (US sellers only) | N/A — still requires manual send |

**Critical:** Etsy has NO fully automated trigger-based replies that fire without seller action. All Star Seller credit requires either a manual send or one of the two built-in auto-reply modes being active.

**Quick Reply character limit:** 2,000 characters. Keep templates to 2–4 short paragraphs.

### Required Quick Reply Templates (Set Up in Shop Manager)

Adapt the bracketed specifics ([app names], [product type]) to your own product —
the five categories below cover the recurring support situations almost every
digital-product Etsy shop sees.

**Template 1 — File Won't Open:**
```
Hi! Thanks for reaching out about your download. For [your file format], I recommend:

1. Download the file to your device first (don't open directly from browser)
2. Open in [your recommended app(s)]
3. [App-specific import step, if any]

If using a laptop, [a free/common compatible reader] opens everything perfectly. Let me know if you're still having trouble and I'll send step-by-step screenshots for your specific app!

— {{OWNER_NAME}} @ {{BUSINESS_NAME}}
```

**Template 2 — Didn't Receive Download:**
```
Hi! Etsy delivers all digital files instantly — they should be in your Purchases page right now.

To find them: Etsy app → Account → Purchases & Reviews → find this order → tap "Download Files"

On desktop: etsy.com → Account → Purchases & Reviews → Download

If you still can't find the files, let me know and I'll look into your order directly.

— {{OWNER_NAME}} @ {{BUSINESS_NAME}}
```

**Template 3 — Wrong File Format:**
```
Hi! All {{BUSINESS_NAME}} [product type] are delivered as [your file format] — they work in [your compatible apps list].

If you were expecting a different format, [your format] is unfortunately the only format that supports [your interactive features, if any].

Is there a specific app you're trying to use? I'm happy to walk you through the best setup for it!

— {{OWNER_NAME}} @ {{BUSINESS_NAME}}
```

**Template 4 — Refund Request:**
```
Hi! I'm sorry the product didn't meet your expectations.

Because digital files are delivered instantly and can't be "returned" once downloaded, I'm not able to issue automatic refunds — but I genuinely want you to be happy with your purchase.

Can you tell me what specifically isn't working or isn't what you expected? In most cases I can either walk you through a fix or send an alternative file that works better for you.

— {{OWNER_NAME}} @ {{BUSINESS_NAME}}
```

**Template 5 — Sharing / License Question:**
```
Hi! The license included with your purchase is for personal use only — one person, unlimited use for yourself.

It doesn't cover: sharing the files with others, using in a classroom/group setting, or reselling/redistributing.

If you need a multi-user license (e.g. for a class or team), please send me a custom order request and I'll put something together for you!

— {{OWNER_NAME}} @ {{BUSINESS_NAME}}
```

### Digital Product Refund Policy — Legal Framework

- Sellers can set a **no-refund policy** for digital products — this is fully legal and supported by Etsy
- Etsy does NOT force refunds for digital downloads as a default
- **Exception:** Etsy Purchase Protection (effective May 7, 2026) may cover buyer claims up to $250 on "qualified orders" — but this applies to physical goods fulfillment disputes, not digital download disputes
- **When Etsy overrides seller policy:** If a buyer files a case claiming the listing description was materially inaccurate, Etsy may issue a refund regardless of seller policy — this is why every listing description must be 100% accurate (supports the mission statement)
- **Best practice:** Offer to troubleshoot before refusing — most "I want a refund" situations are actually tech support issues that can be resolved

### When Human ({{OWNER_NAME}}) Must Respond — Non-Automatable Situations

- Buyer received wrong product (mismatch between listing and delivery)
- Buyer alleges listing was deceptive or inaccurate
- Negative review left — must craft personalized, empathetic response
- Custom order requests (pricing, feasibility, timeline)
- Etsy has opened a case/dispute against the shop
- Any message that cannot be resolved with one of the 5 templates above after 2 attempts

---

## Social Media Automation — Verified 2026 Data

### Pinterest — Confirmed Working Setup

**Rich Pins for Etsy are ACTIVE and working in 2025-2026:**
- Automatically activate within 24 hours for Etsy-hosted listings — no code required
- Enable via: Etsy Dashboard → Marketing → Pinterest → Enable Rich Pins
- Rich Pins auto-pull price, availability, and product description — they update when you update the listing
- Connect Etsy account under Pinterest "Claimed accounts" to support Rich Pin functionality

**Pinterest API v5 Automation Capabilities:**
- ✅ Create pins (POST `/v5/pins`) — image URL, title, description, link, board assignment
- ✅ Create and list boards
- ✅ Schedule via Tailwind (recommended) or directly via API
- ❌ Cannot auto-repin others' content via API
- ❌ Cannot see others' analytics

**Anti-Spam Rules (Hard Limits):**
| Rule | Limit |
|---|---|
| Maximum pins per day | **50 pins/day** — exceeding this triggers spam filters |
| Evergreen content repost interval | **30 days minimum** between repins of the same content |
| Seasonal content repost interval | **7–14 days** |

<fill in> Build your own board structure once your product categories are defined
— one board per product category plus a broad catch-all and a couple of seasonal
boards is a reasonable starting structure.

**Automation workflow:**
- Post hero image + description + Etsy listing URL to the relevant board
- Space out posts: max 10/day for a new account, up to 25/day once established
- Use Tailwind's SmartSchedule for optimal timing if manual scheduling is preferred

### TikTok — Verified as Etsy Ranking Signal

**Confirmed:** External traffic from TikTok acts as a "vote of confidence" for Etsy listings and boosts organic search visibility. Etsy's algorithm registers external traffic sources as a brand authority signal.

**TikTok Algorithm 2026 Requirements:**
- Minimum **70% video completion rate** to enter virality pool (up from 50% in 2024)
- Watch time + completion rate = **40–50% of algorithm weight**
- Content ideas: process videos, behind-the-scenes, "how I made this" formats tend to perform well for handmade/digital creators — adapt to your niche

**TikTok Shop for digital products:** Not viable — TikTok Shop requires physical fulfillment; digital files cannot be listed as products. Use TikTok only for Etsy traffic, not as a sales channel.

**Realistic expectations:**
- Etsy conversion rate average: 1–3%
- TikTok Live shopping conversion: 7.4% (but not applicable to digital products)
- Organic TikTok → Etsy: treat as brand awareness + algorithmic signal, not direct sales driver

---

## Competitor Intelligence — Tool Comparison

| Tool | Price | Best For | Data Quality |
|---|---|---|---|
| **EtsyHunt** | Free + Pro $3.99/mo | Deep competitor data, shop analyzer, Chrome extension | Good — best value |
| **eRank** | From $5.99/mo | Keyword research, listing grades, bulk analysis | Estimated search volumes |
| **Sale Samurai** | $9.99/mo | Accurate search volume, AI keyword suggestions | Accurate search volume |
| **Marmalead** | $19/mo (or $190/yr) | 30-day keyword trend forecasting (95% accuracy) | Best for trend direction; search volume estimates less reliable |

**Recommended starting point for a new shop:** Start with **EtsyHunt Pro ($3.99/mo)** for competitor monitoring + Chrome extension, add **Sale Samurai ($9.99/mo)** once revenue justifies it for accurate keyword volume data.

**What competitor tools can show:**
- ✅ Competitor listing titles, tags, prices, photo count
- ✅ Estimated monthly sales (rough estimate — treat as directional)
- ✅ Search volume trends for keywords
- ✅ Niche saturation signals (competition level scores)
- ❌ Cannot see actual conversion rates of competitors
- ❌ Cannot see competitor ad spend or ROAS

**Niche saturation signals to watch:**
- Average monthly sales per top-20 listing dropping over 3+ months
- Rapid increase in listing count for a keyword (eRank "competition" score rising)
- New sellers flooding with identical products at lower prices

---

## Pricing Strategy — Research-Verified 2026

### Does Price Affect Etsy Algorithm Ranking?

**No direct effect.** Price is NOT an explicit Etsy ranking signal. However:
- Price affects **conversion rate**, which directly affects ranking
- Higher prices can **increase perceived quality** and actually improve conversion for some product types (buyers can associate higher price with more content/value)
- Lowering prices to compete on cost typically hurts perceived value without proportional conversion gain for many digital product categories

### When to Change Prices

- **Never change price on a ranked listing during its first 30 days** — the algorithm is learning from conversion data; a price change resets this signal
- **After 30+ days:** Test price changes in increments of $1–2, wait 3–4 weeks to see conversion rate impact before further changes
- **Edit in small batches:** Never change more than 5–10 listings' prices in the same week — bulk changes look like an automated sweep and can trigger review

### Etsy Sales and Coupons — Optimal Timing

| Strategy | Best Timing | Notes |
|---|---|---|
| Weekend flash sale | Friday 6pm → Sunday 11pm (buyer's time zone) | Weekends + evenings are peak Etsy browsing |
| 24-hour sale | Creates urgency — 24h outperforms 7-day for conversion spike | Don't overuse; trains buyers to wait |
| Seasonal sale | 2 weeks before each seasonal peak | Pair with seasonal keyword updates |
| Discount range | 10–70% allowed; 20–25% is sweet spot | Enough to trigger urgency without devaluing the product |
| Max duration | 30 days (Etsy platform limit) | |
| Repeat sales | No more than monthly | Too frequent = buyers wait for sales; undermines regular price |

**"Sale" badge CTR impact:** Listings with a sale badge display higher CTR in search — exact % not published by Etsy, but seller reports consistently show CTR lifts. The badge appears prominently on both desktop and mobile search thumbnails.

---

## Ranking Recovery Playbook

### After a Listing Edit (Non-Compliance)

- Expect a **2–3 week dip** while Etsy re-indexes the updated listing
- Updated listings optimized for 2026 algorithm typically **outperform the original within 2–3 weeks**
- **Do not edit the same listing again during this window** — compound edits extend the recovery period
- Edit no more than 10 listings per week to avoid triggering bulk-change detection

### After a Policy Violation

- Removing the violating listing **stops further damage** but does not immediately restore ranking
- Shop quality score recovery requires **weeks to months** of consistent positive engagement
- There is **no trick to accelerate** this — only organic sales, favorites, and positive reviews rebuild the score
- During recovery: focus on new listings rather than editing existing ones

### Holiday Mode Re-Index Trick

When Etsy seems to have "forgotten" your shop (sudden zero views with no edits or violations):
1. Go to Shop Manager → Settings → Vacation Mode → Enable (put shop in "Holiday Mode")
2. Wait 10 minutes
3. Disable Holiday Mode
4. Wait 30–60 minutes
5. Check search visibility — this forces Etsy to re-index the shop

**Use sparingly** — holiday mode signals to buyers that the shop is closed; don't run sales during this window.

### After 90-Day Refresh Token Expiry

When any API call returns 401 and the refresh endpoint also returns 401:
1. Run your Etsy OAuth script (e.g. `python tools/etsy_oauth.py`)
2. Follow the browser authorization flow
3. New access + refresh tokens are written to `.env` automatically
4. All automation resumes without any other changes

---

## Autonomy Boundaries — What Claude Can Do vs. What Requires {{OWNER_NAME}}

This three-tier structure is a reusable governance pattern — keep it, and tune the
specific examples in each tier to match your own shop's risk tolerance and
product mix.

### Fully Autonomous (No Approval Needed)

- Monitor ROAS daily and log snapshots
- Run health checks and detect issues
- Generate new listing content (titles, tags, descriptions) from templates
- Generate art files using gpt-image-1 and composite into lifestyle scenes
- Run seasonal keyword reports and dry-run previews
- Send Quick Reply templates for Tier 1 support (file won't open, didn't receive download)
- Refresh OAuth access tokens (within 90-day window)
- Update product manifests and catalog files
- Run weekly reports and log decisions

### Requires {{OWNER_NAME}}'s Review Before Action

- **Publishing any listing to Etsy** — owner reviews all photos, title, description, price before going live
- **Pushing keyword updates** — any seasonal-keyword push script should run only after the owner confirms
- **Responding to refund requests** — use the refund template first; escalate if buyer pushes back
- **Responding to negative reviews** — always human-crafted, empathetic, personalized
- **Price changes on existing ranked listings** — present recommendation, wait for approval
- **Any bulk edit touching more than 10 listings** — confirm scope before running
- **Custom order requests** — pricing and feasibility require the owner's judgment
- **Re-authorization (OAuth)** — requires the owner to complete browser flow every 90 days

### Hard Stops — Never Do Without Explicit Permission

- Push to production Etsy without the owner's final review of photos + listing content
- Issue a refund or close a case
- Delete any listing (active or draft)
- Change prices on more than 5 listings in a single session
- Post to social media accounts
- Contact buyers directly about anything other than the approved Quick Reply templates
