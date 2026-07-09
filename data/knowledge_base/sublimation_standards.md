# Sublimation Design Production Standards
## OnBrandCraftz — Quality Gate Reference (Updated from Deep Research, June 2026)

*Every rule below is research-validated. HARD REQUIREMENTS halt the pipeline. SOFT REQUIREMENTS
trigger a warning. No listing goes live until all HARD gates pass.*

---

## Technical Specifications (HARD REQUIREMENTS)

### Exact Dimensions by Blank Type

| Blank | Dimensions (inches) | Pixels @ 300 DPI | Print Paper |
|---|---|---|---|
| **20oz Skinny Straight** | 9.325" × 8.125" | **2,798 × 2,438 px** | 8.5×11" |
| **20oz Skinny Thick wall** | 11.2" × 7.725" | 3,360 × 2,318 px | 8.5×14" |
| **30oz Skinny** | 10.3" × 9.6" | 3,090 × 2,880 px | 11×17" |
| **30oz Thick wall** | 11.2" × 8.85" | 3,360 × 2,655 px | 11×17" |
| **40oz Tapered (top band)** | 12.9" × 5.75" | 3,870 × 1,725 px | 8.5×14" |
| **40oz Tapered (bottom band)** | 10.3" × 3.6" | 3,090 × 1,080 px | — |
| **11oz Mug** | 8.5" × 3.5" | 2,550 × 1,050 px | 8.5×11" |
| **15oz Mug** | 9.0" × 4.0" | 2,700 × 1,200 px | 8.5×11" |
| **12oz Camper Mug** | 11.35" × 4.35" | 3,405 × 1,305 px | 8.5×14" |

**Critical — 40oz tapered tumblers**: The 40oz blank is tapered (wider at top). A flat rectangular
wrap WILL NOT wrap correctly. Separate top-band and bottom-band template files are required,
OR a trapezoid-shaped single file. Never sell a 40oz wrap listing without both components.
This is the #1 cause of 1-star reviews in the sublimation category.

### File Format
| Format | Use | Quality Setting |
|---|---|---|
| **PNG** | Master files AND delivery — lossless, preserves transparency | N/A |
| **JPEG** | ZIP delivery alternative (smaller file) — acceptable for full-bleed designs | quality ≥ 90, subsampling=0 (`4:4:4`) |
| **PDF** | NOT used for sublimation — leave this to planners/wall art | — |

**Rule**: Always deliver PNG. JPEG acceptable as secondary/ZIP format only.
If JPEG: quality 90+ and subsampling=0 to prevent color fringing on edges and fine text.

### Color Profile (HARD REQUIREMENT)
- **sRGB IEC61966-2.1** — always. Never AdobeRGB, never CMYK
- Buyers open PNGs in Canva, Photoshop, or Silhouette — these all default to sRGB
- AdobeRGB files opened in sRGB-default apps appear washed out before the buyer even presses
- Monitor calibration: design on gamma 2.2, sRGB working space
- ICC profiles are the printer operator's (buyer's) responsibility, not the file seller's

### DPI (HARD REQUIREMENT)
- **300 DPI minimum, native** — not upscaled
- Upscaling a 72 DPI source to 300 DPI creates large files with no added detail — prints soft
- gpt-image-1 generates at screen resolution; always resize to 300 DPI dimensions using Lanczos
- Embed DPI metadata in PNG (PIL: `save(..., dpi=(300, 300))`)

### Heat Press Parameters (include in every ZIP README)
| Setting | Value |
|---|---|
| Temperature | 375°F–400°F (191°C–204°C) |
| Time | 60–120 seconds (add 30–60 sec for double-wall tumblers) |
| Pre-press | 3–5 seconds to remove blank surface moisture |
| Pressure | Medium to medium-firm |
| Print | **Mirror the image before printing** — sublimation prints in reverse |
| Humidity | Optimal 45–55% RH; above 60% causes blues to go dusty |

**CRITICAL**: Every README must include "MIRROR YOUR IMAGE BEFORE PRINTING" in bold.
Failure to mirror = the buyer gets a reversed design. This is the #1 beginner mistake.

---

## Design Quality Standards (HARD REQUIREMENTS)

### Color Saturation — Sublimation Color Shift Compensation
Sublimation output is approximately 10–15% less saturated than the digital file on screen.
**Compensate by over-saturating designs 10–15% beyond "correct."**

| Color | Known shift | Design fix |
|---|---|---|
| Blacks | Often print brown | Use near-black `#1A1A1A`, never pure `#000000` |
| Reds | Shift orange at high temp | Shift reds slightly toward magenta |
| Blues | Appear dusty at high humidity | Increase blue saturation +10–15% |
| Pastels | Extremely hard to reproduce | **Avoid pastels entirely in designs** |
| Whites | ARE the blank substrate (ink is transparent when pressed) | White in design = white on tumbler |

**Rule**: No pastel or light backgrounds. HSL saturation of background region must be ≥ 60%.
Pure black (#000000) is banned. Pure white (#FFFFFF) in background is banned.

### Text Safe Zone (HARD REQUIREMENT)
- The main readable text must stay within the **center 3 inches** of the wrap width
- On a 20oz wrap (9.33" wide): safe zone = ~3.17" to 6.17" from the left edge = px 1020–1980
- Text outside this zone wraps to the back or side of the tumbler and becomes unreadable
- Minimum text size for readability after sublimation transfer: **24pt equivalent** = ~100px at 300 DPI

### Seamless Edge Rule (HARD REQUIREMENT)
- Left edge column must match right edge column visually — pattern must tile
- The quality gate corner-luminance check runs automatically in `generate_sublimation_wraps.py`
- The edge seam check runs automatically (avg diff ≤ 80/255 per channel)
- Any seam visible as a hard line = auto-reject

### Background Coverage (HARD REQUIREMENT)
- 100% of background must be covered — no plain white or near-white areas
- Corner luminance check: all 4 corners must have average luminance ≤ 217/255

### Bleed
- Design must fill edge-to-edge on all 4 sides — no borders, no white margins
- Top and bottom edges: acceptable to leave a 0.25" clear zone at extreme top/bottom
  ONLY if the specific blank has a metal rim that would cover it

---

## Listing Quality Standards (HARD REQUIREMENTS)

### Photos — THE #1 Conversion Factor
**CRITICAL FINDING: Showing a flat PNG file as Photo 1 is a conversion killer.**
Every high-revenue sublimation listing uses a realistic tumbler mockup as the hero photo.

**Required photo sequence:**
1. **[HERO] Tumbler Mockup** — the design composited onto a realistic 20oz tumbler,
   shown in a lifestyle setting. This is what buyers need to visualize the finished product.
   Generate using `tools/generate_tumbler_mockups.py`
2. **[BUNDLE] All designs on tumblers** — small grid of all designs in the bundle on tumblers
3. **[DETAIL] Flat design close-up** — the flat PNG with design details clearly visible
4. **[HOW-TO] Print instructions graphic** — temperature, time, mirror print, 3-panel steps
5. **[SPECS] What's included card** — file count, DPI, dimensions, size compatibility
6. **[SINGLE 1]** Individual design showcase on tumbler (photo 6–10: one per design in bundle)

### Title Formula (Etsy 2026 Algorithm)
**Noun first** — what the item IS, then descriptors:
```
[Size + Product Type + Format] | [Niche/Theme] | [Quantity if bundle] | Instant Download
```
Max 70 characters (mobile ranking penalty above 70).
Example: `20oz Tumbler Wrap PNG | Mom Life Bundle 8 Designs | Instant Download` (67 chars)

### Tags (all 13 required, HARD)
| Slot | Tag | Intent |
|---|---|---|
| 1 | `sublimation tumbler` | product type |
| 2 | `tumbler wrap png` | format + product |
| 3 | `20oz tumbler wrap` | size + product |
| 4 | `sublimation design` | technique |
| 5 | `sublimation bundle` | bundle format |
| 6 | `instant download png` | format + delivery |
| 7 | `[niche] sublimation` | niche audience |
| 8 | `[niche] tumbler wrap` | niche + product |
| 9 | `tumbler design` | alternate search |
| 10 | `png sublimation` | format |
| 11 | `skinny tumbler` | size spec |
| 12 | `[niche] gift` | occasion/gifting |
| 13 | `[seasonal or niche]` | trend/occasion |

Zero tags may duplicate an exact phrase already in the title.

### Pricing Tiers
| Bundle Size | Price | Notes |
|---|---|---|
| 1 design | $3.99–$4.99 | Entry point / search discovery |
| 5 designs | $9.99–$11.99 | Sweet spot conversion |
| 8–10 designs | $12.99–$14.99 | **Best revenue per sale** |
| 15–20 designs | $17.99–$19.99 | For established shops with reviews |
| 25–50 designs | $22.99–$27.99 | Catalog anchor |

Always use .99 or .97 endings. Net per $14.99 bundle after Etsy fees ≈ $13.32.
Target for $5K/month net: **376 bundle sales/month = 12 per day average.**

---

## Copyright & Trademark (HARD REQUIREMENTS — violations = shop removal)

### Banned Content (zero exceptions)
- Any NFL, NBA, MLB, NHL team logos, names, or color combinations paired with team names
- Disney/Marvel/Star Wars characters, silhouettes, character names, or recognizable likenesses
- Any professional sports team identity (college teams included)
- Any TV show, movie, or video game IP elements
- Brand logos, mascots, or trade dress

### The "30% Rule" Is a Legal Myth
There is no legal standard that says modifying 30% of a design makes it original.
"Fan art" has no commercial safe harbor. Selling derivative works of copyrighted material
is infringement regardless of modification percentage.

### Etsy June 2025 Creativity Standards (CRITICAL — enforcement active)
Etsy updated its Creativity Standards effective June 10, 2025:
- Items produced using computerized tools must be based on the seller's OWN original design
- Purchasing commercial-license clipart bundles and re-selling them as sublimation wraps = VIOLATION
- PLR (Private Label Rights) content re-sold as sublimation wraps = VIOLATION
- Template-based designs where only colors/fonts were changed = may be flagged
- AI-generated designs: compliant IF you prompted and meaningfully directed the output
- Enforcement is automated — listings can be removed without warning

**OnBrandCraftz compliance**: All designs are generated via gpt-image-1 with original prompts
written by OnBrandCraftz. This meets the "seller created using digital tools" standard.
Every listing includes the standard AI disclosure statement.

### Safe Sources
- gpt-image-1 with original prompts (current workflow — compliant)
- Designs built from scratch in Photoshop/Illustrator/Canva (compliant)
- Public domain art (pre-1927 publications, Smithsonian Open Access, CC0 license) with
  meaningful original additions (compliant)

---

## Top Niche Prioritization (Research-Validated, 2026)

### Tier 1 — Build here first (highest loyalty, repeat purchase, least seasonal risk)
1. **Teacher** — top profession niche on all Etsy analytics platforms. Sub-niches:
   kindergarten, preschool, school counselor, librarian, art teacher, PE teacher.
   Peak: back-to-school (Aug–Sep). LaurieBethBoutique: $51,914 total revenue on teacher tumblers.
2. **Nurse/Healthcare** — confirmed top 2 profession niche. Sub-niches: NICU nurse, ER nurse,
   L&D nurse, CNA, medical assistant, pediatric nurse. Each sub-niche = separate listing.
3. **Sports Mom** — football, baseball, soccer, volleyball, cheer, wrestling, swim, basketball,
   hockey. Breed-specific (per sport) lowers competition dramatically vs. "sports mom generic."
4. **Dog/Cat Mom** — breed-specific designs 3–5× better than generic "dog mom."
   Best: golden retriever, labrador, bernedoodle, French bulldog, doodle.

### Tier 2 — Add after Tier 1 catalog is established (20+ listings)
5. **Faith/Christian** — "under-optimized" relative to demand. Cross, scripture, "Blessed."
   Year-round with Christmas/Easter peaks.
6. **Patriotic** — 4th of July, Memorial Day, Veterans Day spikes. Avoid specific military insignia.
7. **Grandma/Grandpa** — high gifting intent, Mother's/Father's Day peak.
8. **Fishing/Hunting** — underrepresented in the otherwise female-dominant sublimation market.
   Father's Day spike.

### Tier 3 — Trend-responsive, add when trending
9. **BookTok/Dark Romance** — growing Gen Z buyer base. Lower competition in 2025.
10. **Western/Boho** — cowhide, turquoise, cactus. TikTok-driven.
11. **Coquette** — bows, ribbons, pearls. Sharp upward trend confirmed by eRank Fall 2025.
12. **ADHD/Neurodiverse** — "My ADHD Brain Needs Coffee" style. Growing awareness.

---

## Niche Validation Rule
Before entering any new niche: search Etsy for the specific phrase.
- < 200 results with some recent sales = blue ocean — enter immediately
- 500–5,000 results = competitive but viable with strong mockups and SEO
- 10,000+ results = need hyper-specific angle (breed-specific, sub-occupation, etc.)
- Example: "nurse tumbler wrap" → saturated. "NICU nurse tumbler wrap png" → low competition.

---

## Production Pipeline (enforced — no skipping steps)

```
STEP 1: DESIGN GENERATION
  └─ Run generate_sublimation_wraps.py with full detailed prompt
  └─ QG: corner luminance ≤ 217/255 on all 4 corners
  └─ QG: edge seam diff ≤ 80/255 per channel
  └─ QG: image dimensions ≥ 2000px short edge
  └─ Auto-retry up to 2× on gate failure

STEP 2: MOCKUP GENERATION
  └─ Run generate_tumbler_mockups.py for every approved design
  └─ Generate realistic lifestyle tumbler mockup for Photo 1
  └─ Required BEFORE creating listing — no listing without tumbler mockup

STEP 3: ZIP BUILD
  └─ Convert masters to JPEG quality=90, subsampling=0 (or keep PNG if ZIP < 20MB)
  └─ Add README.txt with: specs, mirror print warning, resize guide, heat press settings, license
  └─ QG: ZIP size < 20MB (Etsy hard limit)

STEP 4: LISTING CONTENT
  └─ QG: title ≤ 70 chars, noun first, includes size + format + niche
  └─ QG: all 13 tags filled, each ≤ 20 chars
  └─ QG: zero tags duplicate exact title phrases
  └─ QG: description first sentence = primary keyword + what's included
  └─ Price uses .99/.97 ending

STEP 5: PUBLISH
  └─ Upload tumbler mockup as Photo 1
  └─ Upload all 10 photos
  └─ Upload ZIP file
  └─ Activate listing
  └─ Log to data/pipeline_state.json

STEP 6: MONITOR (weekly)
  └─ Run business_pipeline.py --mode monitor
  └─ Flag low-view listings (< 10 views after 30 days) → title/tag fix
  └─ Flag high-view/no-conversion listings → photo or price fix
```

---

## Quality Scoring Rubric (score before every publish — minimum 7/10 all four)

| Criterion | 1–3 (Reject) | 4–6 (Revise) | 7–10 (Publish) |
|---|---|---|---|
| **Background depth** | Pastel/pale/white | Medium saturation | Deep, saturated, full coverage |
| **Focal design quality** | Flat clipart | Decent, limited depth | Rich, layered, professional |
| **Typography** | Default font, poor contrast | OK font, could be bolder | Bold, intentional, high-contrast with shadow |
| **Seamless edges** | Visible seam line | Near-seamless | Perfect edge continuity |

---

## Competitive Benchmark — Top Performers (EtsyHunt Data, 2026)

| Shop | Weekly Sales | Strategy |
|---|---|---|
| WhatADesignUS | 104 | Patriotic/holiday, trend-chasing |
| TrendQuestCo | 98 | Retro patriotic bundles, rapid trend response |
| ZazzyDigitalDesigns | 61 | Sparklecore, glitter, seasonal |
| ScorpiosArtVN | 38 | **Premium pricing, highest revenue** ($3,474 total) |
| LaurieBethBoutique | 78 | Physical teacher tumblers ($51,914 total) |

Key pattern: **ScorpiosArtVN generates the most total revenue with the fewest sales** — premium
bundle pricing with excellent mockups outperforms race-to-the-bottom single-design pricing.
