# Sublimation Design Production Standards
## OnBrandCraftz — Quality Gate Reference

*These standards are enforced programmatically before any sublimation product goes live.
Violating any HARD REQUIREMENT = design is rejected from the pipeline.*

---

## Technical Specifications (HARD REQUIREMENTS)

### File Format
| Spec | Requirement | Why |
|---|---|---|
| **Format** | PNG for master files; JPEG (quality ≥ 85) for ZIP delivery | PNG = lossless master; JPEG compresses well for delivery |
| **Color profile** | **sRGB IEC61966-2.1** — never AdobeRGB, never CMYK | Sublimation printers and Sawgrass/Epson drivers expect sRGB. AdobeRGB = muddy, washed-out print |
| **DPI** | 300 DPI minimum (embedded in file metadata) | Below 300 = pixelated print, guaranteed refund requests |
| **Bit depth** | 8-bit per channel (24-bit RGB) | 16-bit is ignored by most sublimation RIP software |
| **Background** | NO transparent/alpha channel in delivery files | Sublimation prints on white blanks — transparency = white = no color transfer |

### 20oz Skinny Tumbler (primary product)
| Dimension | Value |
|---|---|
| Width | 9.33 inches = **2799 pixels** at 300 DPI |
| Height | 8.33 inches = **2499 pixels** at 300 DPI |
| Aspect ratio | ~1.12:1 (slightly wider than tall) |
| Bleed | Design must fill edge-to-edge — no white borders |
| Seam | Left edge must match right edge (seamless wrap) |

### Other Blank Sizes (include in README, resize to order)
| Blank | Dimensions | Pixels @ 300 DPI |
|---|---|---|
| 30oz Tumbler | 9.5" × 9.1" | 2850 × 2730 |
| 40oz Tumbler | 9.5" × 12.0" | 2850 × 3600 |
| 11oz Mug | 8.5" × 3.8" | 2550 × 1140 |
| 15oz Mug | 9.5" × 4.2" | 2850 × 1260 |
| 20oz Straight Tumbler | 8.5" × 9.3" | 2550 × 2790 |
| 12oz Can Cooler | 9.3" × 5.75" | 2790 × 1725 |

### ZIP Delivery Requirements
- **Max ZIP size: 20MB** (Etsy hard limit per file)
- Always include README.txt with: file list, specifications, how-to-print steps, resize guide, license
- File naming: `[theme]_[size].jpg` — no spaces, no special characters
- JPEG quality 85–90 (≥85 preserves print quality; >90 bloats file size unnecessarily)
- Use subsampling=0 (`4:4:4`) — prevents color fringing on fine text and edges

---

## Design Quality Standards (HARD REQUIREMENTS)

### Color Saturation
- **All backgrounds must be DARK and SATURATED** — light/pastel backgrounds look washed out after sublimation
- Target minimum background saturation: HSL saturation ≥ 60%
- Sublimation shifts colors ~15–20% toward lighter/more muted — design for this by over-saturating
- AVOID: pastels, pale tones, white backgrounds, light grey backgrounds
- PREFER: deep navy, forest green, burgundy, terracotta, plum, charcoal, black

### Text Legibility on Curved Surface
- **Minimum effective font size for 20oz wrap: 140pt at print resolution** (equivalent to ~190px at 300 DPI)
- Text must have HIGH CONTRAST against background — minimum 4.5:1 contrast ratio
- Avoid placing critical text within 0.5" of left or right edges (wrap seam area)
- Avoid placing text at extreme top or bottom edges (rolled under base/lid on press)
- Curved tumblers compress side edges slightly — keep focal design in CENTER 60% of width

### Seamless Edge Rule
- Left edge pixel column must visually match right edge pixel column (±10% tolerance)
- Background pattern must tile seamlessly — buyers notice seam lines on finished tumbler
- Always verify seam by loading design in image editor and duplicating side-by-side

### Bleed and Safe Zone
```
┌─────────────────────────────────┐
│ 0.25" BLEED (no critical design │
│ ─────────────────────────────── │
│                                 │
│   SAFE ZONE (focal + text)     │
│   center 8.83" × 7.83"         │
│                                 │
│ ─────────────────────────────── │
│ 0.25" BLEED (no critical design │
└─────────────────────────────────┘
```

### Background Coverage
- Background must be 100% covered — no white or near-white areas (anything > L*90 in LAB space)
- Solid dark color OR dense pattern — either is acceptable
- Gradient backgrounds: must go from dark to dark (never dark to near-white)

---

## Design Style Quality Standards

### What Converts on Etsy (research-validated)
1. **Boho floral wraps** — #1 selling style. Florals with dark background consistently outsell minimal designs 3:1
2. **Retro/vintage typography** — bold, slightly distressed fonts with drop shadows
3. **Sports mom + occupation themes** — highest search volume; lowest buyer decision friction
4. **Kawaii/cute character wraps** — strong differentiation; low competition in sublimation
5. **Faith/Christian themes** — extremely loyal buyer community, high repeat purchase rate

### Illustration Quality Requirements
- Focal element must have DEPTH: shadows, highlights, texture — flat clipart ≠ premium
- Minimum 3 distinct design layers: background pattern + mid elements + focal design + typography
- Typography must feel INTENTIONAL — not default system fonts
- All botanical/floral elements: painterly, loose, natural — never rigid clipart
- Character illustrations: kawaii proportions (large head, expressive eyes, rosy cheeks)

### Prompting Quality Gates (gpt-image-1)
Every sublimation wrap prompt MUST specify:
1. `"full bleed horizontal composition, seamless left-to-right edges"`
2. `"vibrant saturated colors, deep [COLOR] background"` — never pastels
3. `"no white or pale areas in background"` — prevents blank areas on tumbler
4. The specific color palette with hex values
5. `"print-ready quality, no watermarks, no studio equipment"`
6. Art style as the FIRST sentence (sets generation direction before visual details)

---

## Listing Quality Gates (HARD REQUIREMENTS)

### Title
- **Maximum 70 characters** (Etsy 2026 mobile ranking penalty above 70)
- Must include: "sublimation" + "tumbler wrap" + "PNG" + "instant download" (or close variants)
- Lead with the most-searched term first
- Validated formula: `[Theme] Sublimation Tumbler Wrap Bundle PNG [Size] Instant Download`

### Tags (all 13 required)
Top performing tags for sublimation (validated Q4 2025):
```
sublimation tumbler   (19 chars)
tumbler wrap png      (16 chars)
sublimation design    (18 chars)
20oz tumbler wrap     (17 chars)
sublimation bundle    (18 chars)
mom life sublimation  (20 chars)
instant download png  (20 chars)
tumbler design        (14 chars)
sublimation wrap      (16 chars)
png sublimation       (15 chars)
tumbler sublimation   (19 chars)
[theme tag, e.g. "dog mom sublimation"]
[niche tag, e.g. "nurse sublimation"]
```
No tag may duplicate a phrase in the title.

### Price Tiers
| Bundle Size | Price | Notes |
|---|---|---|
| 1–2 designs | $3.99–$4.99 | Loss leader / impulse buy |
| 4–6 designs | $6.99–$8.99 | Sweet spot for new shops |
| 8–12 designs | $9.99–$12.99 | **Best revenue per conversion** |
| 15–20 designs | $14.99–$19.99 | Premium tier after review base established |
| Mega bundle 30+ | $24.99–$34.99 | Catalog anchor price |

### Photos (10 slots, all required)
1. Hero collage — ALL designs visible at thumbnail size, dark background, bundle name
2–9. Individual design showcases — one per design, centered, labeled with spec line
10. Specs card — what's included, file specs, compatibility icons

---

## Production Pipeline (enforced workflow — no skipping steps)

```
STEP 1: GENERATE
  └─ Run generate_sublimation_wraps.py with detailed per-theme prompt
  └─ Quality gate: verify no white/pale background areas (auto-check LAB lightness)
  └─ Quality gate: verify dimensions are 2799×2499 at 300 DPI

STEP 2: REVIEW
  └─ HUMAN or AGENT reviews all designs for: seamless edges, text legibility,
     composition quality, color depth
  └─ Reject threshold: any design scoring below 7/10 on all 4 criteria
  └─ Regen rejected designs with improved prompt

STEP 3: BUILD
  └─ Convert masters to JPEG quality=88, subsampling=0
  └─ Build ZIP with README.txt
  └─ Verify ZIP < 20MB
  └─ Generate 10 listing photos (collage + individual showcases + specs card)

STEP 4: PUBLISH
  └─ Validate title ≤ 70 chars
  └─ Validate all 13 tags ≤ 20 chars each
  └─ Validate no tag duplicates title phrase
  └─ Create listing (draft state)
  └─ Upload all 10 photos
  └─ Upload ZIP file
  └─ Activate listing

STEP 5: MONITOR (weekly)
  └─ Check views, favorites, conversions per listing
  └─ Flag listings with views > 100 but conversion < 1% for photo/price fix
  └─ Flag listings with 0 views after 30 days for tag/title revision
```

---

## Commercial Use License — Required Language

Every sublimation listing MUST include this license language verbatim:

```
✅ You MAY sell finished physical products (tumblers, mugs, shirts, can coolers)
   made with these designs — unlimited production runs
✅ You MAY use for small business and craft fair production
❌ You may NOT resell, redistribute, or share the digital PNG/JPEG files
❌ You may NOT use to create other digital products for resale
❌ You may NOT claim these designs as your own original artwork
```

Commercial use license is a key conversion factor — buyers want to know they can sell finished tumblers before they purchase.

---

## Quality Scoring Rubric (use before every publish decision)

Score each design 1–10 on each criterion. Minimum 7/10 required on ALL four to publish.

| Criterion | 1–3 (Reject) | 4–6 (Revise) | 7–10 (Accept) |
|---|---|---|---|
| **Background depth** | White/pale/pastel | Medium saturation, not dark enough | Deep, saturated, full coverage |
| **Focal design quality** | Clipart-level flat | Decent illustration, limited depth | Rich, layered, professional illustration |
| **Typography** | Default system font, poor contrast | Decent font, could be bolder | Bold, intentional, high contrast, drop shadow |
| **Seamless edges** | Obvious seam line | Near-seamless, slight mismatch | Perfect edge-to-edge continuity |
