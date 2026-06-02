# OnBrandCraftz — Cost & Profit/Loss Analysis
*Built: 2026-06-02 | Updated automatically with each weekly report*

---

## IMAGE GENERATION PRICING (OpenAI gpt-image-1)

All tools use `quality="high"`, `size="1024x1024"` unless noted.

| Model / Settings | Cost per Image |
|---|---|
| gpt-image-1 · 1024×1024 · quality=high | **$0.167** |
| gpt-image-1 · 1536×1024 · quality=high (landscape) | **$0.250** |
| DALL-E 3 · 1024×1024 · standard (art_creation_tools) | **$0.040** |

---

## PRODUCT CREATION COSTS (one-time per product)

### Digital Planner (DP1026 – DP1029 style)

| Step | Tool | API Calls | Cost |
|---|---|---|---|
| Cover image | gpt-image-1 high | 1 | $0.17 |
| 11 sticker sheets | gen_sticker_sheet.py | 11 | $1.84 |
| 2 lifestyle listing photos | gen_listing_images.py (image.edit) | 2 | $0.33 |
| 8 additional listing photos | PDF rendering via PIL | 0 | $0.00 |
| Listing title/description/tags | Claude API (text only) | ~1K tokens | $0.02 |
| Etsy listing fee | Etsy | — | $0.20 |
| **TOTAL creation cost** | | **14 API calls** | **$2.56** |

*Sticker sheets and cover are reused infinitely — zero cost per sale after creation.*

---

### SVG Bundle (20 designs)

| Step | Tool | API Calls | Cost |
|---|---|---|---|
| 20 design base images | generate_svg_designs.py | 20 | $3.34 |
| 40 product mockups (2 per design: t-shirt + tote) | generate_svg_designs.py | 40 | $6.68 |
| 2 lifestyle listing photos | gen_listing_images.py | 2 | $0.33 |
| Listing content | Claude API | ~1K tokens | $0.02 |
| Etsy listing fee | Etsy | — | $0.20 |
| **TOTAL creation cost** | | **62 API calls** | **$10.57** |

*Note: The SVG trace itself (vtracer) is free/local — only the source PNG costs money.*

---

### Wall Art Printable (single listing)

| Step | Tool | API Calls | Cost |
|---|---|---|---|
| Art file generation | gpt-image-1 or DALL-E 3 | 1 | $0.04–$0.17 |
| Upscaling to 3000px+ | upscale_art.py (local Lanczos) | 0 | $0.00 |
| Multi-size ZIP creation | generate_print_sizes.py (local) | 0 | $0.00 |
| 2 lifestyle room shots | gen_listing_images.py (image.edit) | 2 | $0.33 |
| 8 PIL composite photos | lifestyle_composite.py (local) | 0 | $0.00 |
| Listing content | Claude API | ~1K tokens | $0.02 |
| Etsy listing fee | Etsy | — | $0.20 |
| **TOTAL creation cost** | | **3 API calls** | **$0.59–$0.72** |

---

### Sublimation Design (per niche/theme)

| Step | Tool | API Calls | Cost |
|---|---|---|---|
| Wrap design (1536×1024 landscape) | generate_sublimation_wraps.py | 1 | $0.25 |
| Tumbler mockup photos | generate_tumbler_mockups.py | 0 (PIL composite) | $0.00 |
| Listing content | Claude API | ~1K tokens | $0.02 |
| Etsy listing fee | Etsy | — | $0.20 |
| **TOTAL creation cost** | | **1 API call** | **$0.47** |

---

### Standalone Sticker Pack (per theme)

| Step | Tool | API Calls | Cost |
|---|---|---|---|
| 5 sticker sheets | gen_sticker_sheet.py | 5 | $0.84 |
| 2 lifestyle listing photos | gen_listing_images.py | 2 | $0.33 |
| Listing content | Claude API | ~1K tokens | $0.02 |
| Etsy listing fee | Etsy | — | $0.20 |
| **TOTAL creation cost** | | **7 API calls** | **$1.39** |

*If generated as part of a planner order, sticker sheets are already paid — incremental cost is only $0.55 (photos + listing fee).*

---

### 3D Printed Physical Product (per unit sold — ongoing COGS)

Unlike digital products, every physical sale has real material costs.

| Cost Item | Low | Typical | High | Notes |
|---|---|---|---|---|
| Filament (PLA/Silk PLA) | $0.45 | $1.25 | $2.50 | ~$0.15–0.25/hr print time |
| Electricity | $0.08 | $0.15 | $0.25 | $0.02/hr × 4–12 hr print |
| Printer wear/maintenance | $0.15 | $0.25 | $0.50 | Amortized over expected print life |
| Packaging (bag, tissue, label) | $0.20 | $0.35 | $0.50 | |
| USPS shipping (if free shipping offered) | $3.50 | $5.50 | $9.00 | First class vs Priority depending on weight |
| Listing creation (AI photos + content) | — | $0.72 | — | One-time, not per-sale |
| **Total COGS per unit** | **$4.38** | **$7.50** | **$12.75** | |

---

## ETSY FEE STRUCTURE (per sale)

| Fee | Rate | Example: $14.99 | Example: $9.99 | Example: $4.99 |
|---|---|---|---|---|
| Listing fee | $0.20 flat (every 4 months or per sale) | $0.20 | $0.20 | $0.20 |
| Transaction fee | 6.5% of sale price | $0.97 | $0.65 | $0.32 |
| Payment processing | 3% + $0.25 | $0.70 | $0.55 | $0.40 |
| **Total Etsy fees** | | **$1.87** | **$1.40** | **$0.92** |
| **Net to seller** | | **$13.12** | **$8.59** | **$4.07** |

---

## PER-PRODUCT PROFIT ANALYSIS

### Digital Products (zero COGS per additional sale)

| Product | Price | Etsy Fees | Net/Sale | Creation Cost | Break-Even Sales | Margin at 10 Sales |
|---|---|---|---|---|---|---|
| Digital Planner (DP1026) | $14.99 | $1.87 | $13.12 | $2.56 | **1** | $128.64 |
| Digital Planner (DP1027) | $9.99 | $1.40 | $8.59 | $2.56 | **1** | $83.34 |
| Digital Planner (DP1028) | $12.99 | $1.59 | $11.40 | $2.56 | **1** | $111.44 |
| Digital Planner (DP1029) | $12.99 | $1.59 | $11.40 | $2.56 | **1** | $111.44 |
| All 4 Planners Bundle | $39.99 | $3.95 | $36.04 | $0.20 | **1** | $360.20 |
| SVG Bundle | $9.99 | $1.40 | $8.59 | $10.57 | **2** | $74.33 |
| Wall Art (avg $7.99) | $7.99 | $1.12 | $6.87 | $0.72 | **1** | $67.98 |
| Wall Art (low $4.99) | $4.99 | $0.92 | $4.07 | $0.72 | **1** | $39.98 |
| Sublimation Bundle | $9.99 | $1.40 | $8.59 | $0.47 | **1** | $86.43 |
| Sticker Pack (single) | $4.99 | $0.92 | $4.07 | $1.39 | **1** | $39.31 |
| Sticker Pack (bundled) | $7.99 | $1.12 | $6.87 | $0.55 | **1** | $68.15 |
| FREE Sticker Sampler | $0.00 | $0.20 | -$0.20 | $1.39 | ∞ | Lead gen only |

### 3D Physical Products

| Product | Price | Etsy Fees | Gross/Sale | COGS/Unit | Net Profit | Margin % |
|---|---|---|---|---|---|---|
| Can Koozie ($16.99) | $16.99 | $1.95 | $15.04 | $7.50 | **$7.54** | 44% |
| Boho Centerpiece ($39.99) | $39.99 | $3.95 | $36.04 | $12.75 | **$23.29** | 58% |
| Desk Organizer ($12.99) | $12.99 | $1.59 | $11.40 | $7.50 | **$3.90** | 30% |
| Small Decor ($8.99) | $8.99 | $1.12 | $7.87 | $6.00 | **$1.87** | 21% |
| Lamp ($34.99) | $34.99 | $3.42 | $31.57 | $10.00 | **$21.57** | 62% |

---

## MONTHLY PLATFORM / SUBSCRIPTION COSTS

| Service | Cost | Status | Notes |
|---|---|---|---|
| OpenAI API | Pay-per-use | Active (needs billing top-up) | ~$20 for all 5 SVG bundles; ~$2.50/planner |
| Anthropic Claude API | Pay-per-use | Active | ~$0.01–0.05/week for automation (text only) |
| Etsy listing fees | $0.20/listing | Active | 93 listings × $0.20 / 4 months = $4.65/mo amortized |
| Canva Pro | $0 | Not subscribed | Listings reference it for buyers, not used in our workflow |
| EtsyHunt Pro | $0 | Not subscribed | Recommended at $3.99/mo when revenue justifies |
| Sale Samurai | $0 | Not subscribed | Recommended at $9.99/mo once ads are running |
| Domain / hosting | $0 | None | Running locally, no server costs |
| Buffer (TikTok scheduling) | $0 | Not set up | Free tier handles what's needed |
| **Current monthly fixed cost** | **~$5/mo** | | Basically just amortized listing fees |

**Current variable cost estimate (at current 2 sales/week pace):**
- OpenAI API: ~$0 (no new content being generated right now)
- Anthropic API: ~$0.05/week (automation scripts)
- Etsy fees on sales: $1.40–$1.87 per sale × 8 sales/mo = ~$13/mo
- **Total monthly operating cost: ~$18/mo**

---

## PROFIT & LOSS SUMMARY — CURRENT STATE (June 2026)

| | This Week | Monthly Pace | Annual Pace |
|---|---|---|---|
| Gross Revenue | $27.26 | $307 | $3,684 |
| Etsy Fees (~12.5%) | $3.41 | $38 | $461 |
| API / Platform Costs | ~$0 | ~$5 | ~$60 |
| 3D Print COGS (est.) | ~$10 | ~$112 | ~$1,344 |
| **Net Profit** | **~$13.85** | **~$152** | **~$1,819** |
| Net Margin | 51% | 49% | 49% |

*Revenue is heavily physical (3D printed) right now — high margin % but low volume.*
*Digital products are near-zero-COGS once created — each digital sale is 87–90% margin.*

---

## BREAKEVEN ANALYSIS — INVESTMENT TO SCALE

To go from $307/mo → $5,000/mo net, the fastest path is completing the digital + SVG pipeline.

| Investment | Cost | Expected Monthly Revenue Added | Payback Period |
|---|---|---|---|
| Top up OpenAI ($100) | $100 | Unlocks ~$20 of generation + $200–800/mo in new listings | 1–2 months |
| Complete 5 SVG bundles ($52.85) | $52.85 | ~$50–200/mo at 6–23 sales/bundle/mo | 1 month |
| Generate 20 more wall art listings ($14.40) | $14.40 | ~$40–80/mo at 1 sale/listing/mo avg | 1 month |
| Generate DP1030 ADHD Planner ($2.56) | $2.56 | ~$50–300/mo (fastest-growing niche) | <1 month |
| Generate DP1033 Teacher Planner ($2.56) | $2.56 | ~$50–200/mo (back-to-school peak Aug–Sep) | <1 month |
| Etsy Ads ($5/day after 5 reviews) | $150/mo | ~$400–600/mo revenue at 4x ROAS | Immediate |
| **Total investment needed** | **~$175** | **~$740–$1,380/mo added** | **1–2 months** |

---

## COST PER LISTING CREATED (summary reference card)

| Product Type | Cost to Create | Sells for | Net First Sale | Margin at 100 Sales |
|---|---|---|---|---|
| Digital Planner | $2.56 | $9.99–$14.99 | $6.03–$10.56 | $855–$1,315 |
| SVG Bundle | $10.57 | $9.99 | -$1.98 first | $848 |
| Wall Art | $0.59–$0.72 | $4.99–$7.99 | $3.35–$6.28 | $335–$628 |
| Sublimation | $0.47 | $4.99–$9.99 | $3.60–$8.12 | $360–$812 |
| Sticker Pack | $1.39 | $4.99 | $2.68 | $267 |
| 3D Physical | $7.50/unit | $8.99–$39.99 | varies | varies |

*Digital products are effectively infinite-margin after break-even — once you've made one sale, every subsequent sale costs $0 to fulfill.*

---

## HIGHEST ROI ACTIONS (by cost-to-revenue ratio)

1. **DP1030 ADHD Planner** — $2.56 to create, fastest-growing niche, $50–300/mo potential. ROI: 2,000–12,000%
2. **Wall art mockup upgrades** — $0.33/listing for 2 AI lifestyle shots, converts 1-photo listings from ~0% to ~2%+. ROI: very high
3. **SVG Bundles** — $10.57 each, but $9.99/sale with near-zero ongoing costs. ROI positive by sale #2
4. **Etsy Ads** — $5/day ($150/mo) should generate $600+/mo at 4x ROAS once reviews are established
5. **DP1033 Teacher Planner** — $2.56 to create, back-to-school peaks August/September, 90-day window closing

---

*This document is a living reference. Update the "Current State" section after each weekly report.*
*Full weekly report: `data/reports/2026-06-02_weekly_report.md`*
