# Design Quality Research — June 2026
*Five-agent deep research synthesis: wall art design, SVG typography/design, planner function & UX, top-1% seller practices, premium visual design systems. All claims multi-source verified; confidence flagged where single-sourced.*

---

## VERDICT SUMMARY

| Product Line | Verdict | Gap Size |
|---|---|---|
| Wall art | Good pipeline, behind on style mix + AI finishing | Medium |
| SVG bundles | Unknown technical compliance, fonts below market | Medium-Large |
| **Planners** | **Way behind — Scott's instinct confirmed** | **Largest** |

---

## 1. WALL ART — What's Wrong and How to Fix It

### Gap 1: The AI "smoothness" tell (HIGHEST IMPACT)
Our `tools/upscale_art.py` uses 4× Lanczos + UnsharpMask. The market standard for AI art finishing:
- **AI-aware upscaling**: Topaz Gigapixel (High Fidelity / Art & CG modes, up to 6-8×) or Real-ESRGAN (free, local, anime-tuned models suit flat kawaii illustration)
- **Grain pass**: monochromatic Gaussian noise (~5–8%) on a 50% gray Overlay/Soft Light layer at 10–15% opacity — kills the "melted plastic" AI look
- **One-pass rule**: upscale to final size in ONE pass; chaining upscalers degrades quality
- Sources: letsenhance.io, vectosolve.com, topazlabs.com (high confidence)

**Action: add a film-grain/texture stage to `upscale_art.py`. Real-ESRGAN is free and runs locally.**

### Gap 2: Missing print ratios
We ship 2:3, 4:5, A-series, square. Market standard adds:
- **3:4 ratio** (9×12, 18×24) — missing entirely
- **24×36** in the 2:3 folder — missing
- Most popular sizes per research: 8×10, 2:3 poster sizes, 5×7, 11×14, 16×20, 18×24, 24×36

**Action: update `tools/generate_print_sizes.py` to add 3:4 folder + 24×36.**

### Gap 3: Style mix fights the 2026 interior trend
2026 interiors: warm saturated neutrals, butter/mustard yellow, teal, terracotta, coral. OUT: pure white, cool icy gray.
Top-performing Etsy styles (direct marketplace evidence, high confidence):
1. **Moody vintage oil painting** (still life, landscapes, seascapes, antique portraits) in brown/charcoal/grey/cream — heavily represented among Star Sellers, we have ZERO
2. **Quiet luxury** muted watercolor botanicals (cream/sage/warm beige)
3. **Sophisticated neutrals** line art + abstract shapes
4. Romantic pastels, retro/pop posters, contemporary folk

Oversaturated: generic inspirational typography, generic boho abstract.
Underserved: **non-English scripture art (Spanish/Portuguese/Korean)**, National Park art (+40% YoY), hyper-specific micro-niches.

**Nursery art = highest AOV category** (buyers purchase 3–6 coordinated prints per order; 140k+ monthly searches).

### Gap 4: Volume vs quality — the data
- NorthPrints: 253k sales from 1,042 listings (~8.3 sales/listing/month)
- LanternPress: 166k sales from 19,515 listings (~0.07 sales/listing/month)
- Curated shops earn **~100× more per listing**. 2026 AI-content flood means "verified human quality" is the differentiator.

---

## 2. SVG BUNDLES — Technical Gates and Font Upgrades

### Technical compliance gates (audit all 11 live bundles against these)
| Gate | Requirement |
|---|---|
| File size | < 5MB per SVG |
| Node count | < 10,000 (< 5,000 for simple designs) |
| Text | ALL converted to paths/outlines — live `<text>` breaks on import |
| Scripts | Welded into single closed compound paths (#1 "won't weld" complaint) |
| Strokes | Converted to fills — Design Space handles strokes unreliably |
| Colors | 3–6 flat solid hexes, standardized (near-dupes like #000 vs #010101 create junk layers) |
| viewBox | Required + explicit width/height with units (else 72-DPI sizing bug) |
| Forbidden | Gradients, transparency, filters, masks, clip paths, embedded rasters, CSS |

### Deliverable standard (we're likely under-delivering)
Market standard ZIP: **SVG + PNG (300 DPI transparent) + DXF + EPS**
- DXF covers Silhouette Studio free edition (can't open SVG)
- EPS covers print shops
- Organized format subfolders in one ZIP

### Named fonts by niche (what top sellers actually use)
| Niche | Fonts |
|---|---|
| **Farmhouse** | Hanley Script + Hanley Block, Magnolia Sky, Samantha Craft (cut-weighted strokes), Aquifer (free — the actual Magnolia brand font), Rosewood Std Fill. Signature: tall thin all-caps + bouncy script ("GATHER *together*") |
| **Retro/Groovy** | Cooper Black revival is THE anchor (open-source "Cooper*" at indestructibletype). Bubbly wavy baselines, stacked arched text, balloon fonts |
| **Western** | IFC Insane Rodeo (1.2M+ downloads), Rodeo 6-style family (regular/grunge/shadow/shadow-wave), Wild Canyon, spurred Tuscan serifs |
| **Mom-life** | Chunky retro serif "Mama" with leopard/checkered pattern fill, varsity block, messy bun motif |
| **Faith** | Clean serif/tall sans + script accent word; modern scripture layouts, not just crosses |

### Pro techniques that separate top sellers
1. **Knockout text** (text reversed out of offset shape via boolean Difference)
2. **Offset/shadow layers shipped as separate welded shapes** per color — buyers cut layered vinyl without doing their own offsetting
3. **Distressed variants baked into paths** (raster textures get ignored on import)
4. **Arched/wavy/stacked compositions** with warps expanded to final paths
5. Multi-weight variants of one design (regular + grunge + shadow) productized in the same bundle

Amateur tells: live text, unwelded scripts, open paths, stroke-only outlines, junk color layers.

---

## 3. PLANNERS — The Biggest Gap (Scott is right)

### Feature gap table: us vs 2026 top sellers
| Feature | OnBrandCraftz now | Top sellers 2026 |
|---|---|---|
| Covers | 1 | 32–240+ (hyperlinked cover picker) |
| Total pages | 90–104 | 800+ fully hyperlinked |
| Daily pages | None | 365 hyperlinked + up to 6 daily layouts |
| Weekly layouts | 1 | 4–22 options |
| Orientation | Portrait only | Portrait + landscape bundled |
| Dark mode | None | Dedicated SKU (MADEtoPLAN, ForLittleLion) |
| Start day | One | Sunday AND Monday versions |
| Calendar integration | None | Apple Calendar/Reminders/Google shortcut buttons in-PDF |
| Stickers | 200+ | 300–3,500+ + GoodNotes sticker book |
| Video tutorials | None | QR codes embedded in planner (Luxbook) |
| Versions per purchase | 2 (dated+undated) | 8 (2025/2026/undated × light/dark or orientations) |
| Free updates | No | "Lifetime access + annual updates" marketed |
| Android messaging | No | In top listing titles |
| Price | $9.99–14.99 | $19.99–31.99 for feature-rich |

### Price benchmarks (Paperlike roundup, high confidence)
- Basic (1 layout, no dailies): $9.99–12.99
- Mid (dated+undated, hyperlinks, stickers): $15–20 ← **our spec, but we charge bottom-tier prices**
- Flagship (calendar buttons, widgets, 365 dailies, help library): $23–32 (Cyberry $31.99)

### Top buyer complaints (engineer against these)
1. **Broken hyperlinks** — #1 negative review driver
2. **Lag/blank pages** from unoptimized images (on GoodNotes' official known-issues list — compress all raster assets)
3. Download/delivery failures with no support response
4. **Writing space too small** / must zoom to write
5. Confusing navigation (hidden tabs, unlinked templates)
6. Long setup / learning curve
7. Overwhelm from too many pages (ADHD planners exploit this gap)
8. Orientation lock-in (re-buying for landscape)
9. "Too feminine" pastel-only schemes limiting buyer pool
10. Multiple un-linked PDFs requiring manual assembly

### Named font system (we have NONE defined — adopt this)
**Free (Google Fonts), verified planner-specific:**
- **Patrick Hand** — highest readability; all-purpose headers AND body
- **Kalam** — body text/journal entries
- **Amatic SC** — tall condensed headers/titles
- **Caveat** — cursive accents only
- Premium upgrades: Honey Script (900+ glyphs), Kirstin ($7.99), Blush Font Co. GoodNotes bundle

**Pairing formula:** expressive script/serif headers + practical readable sans/handwriting body. Max 2 fonts, 3–4 colors.

### Layout/typography standards
- Fonts legible at 10–12pt at 100% zoom; GoodNotes renders REGULAR weights better than bold/light
- Handwriting fields: +10–20% line height over default
- PDF hyperlinks are aspect-ratio-dependent — size variants (A4/A5/Half Letter) need per-ratio link maps
- Standard sizes: A4 2480×3508, US Letter 2550×3300, A5 1748×2480, Half Letter 1275×1650 — we only ship US Letter

### Dark mode color rules (fixes needed for DP1032 Midnight Kawaii spec)
- Background: **#121212-range**, never pure black (halation for 30–60% with astigmatism). Our planned #1A1A2E ✓ OK
- Text on dark: softened white **#E9ECF1**, never #FFFFFF (21:1 is too harsh)
- **Desaturate accents on dark** — our planned neon #E040FB / #00E5FF at full saturation will fail WCAG 4.5:1 next to text; reserve one saturated element max
- Elevation on dark = lighter surfaces, not shadows

### What makes products look cheap (avoid list)
3+ fonts in one design · bevels/heavy shadows/outline text effects · inconsistent margins between pages · no white space · garish saturated primaries · pixelated clip-art · broken navigation · pure black text/borders · default system fonts

### 2026 trends to ride
- Dark mode as a product line, not a variant
- **Minimal/neutral layouts winning; decoration moved into optional stickers**
- OS calendar shortcut buttons in-PDF
- Pre-purchase customization builders (192 variations — The Planners Collective)
- ADHD "science-based" positioning with calming palettes and chunked days
- Freemium funnels (free sample planner → paid flagship)
- Soft grounded neutrals (nude/beige/earthy); typography-as-hero covers; grainy texture overlays

---

## PRIORITIZED ACTION PLAN

### P1 — Planner overhaul (largest gap, unlocks $19.99+ pricing)
Build "DP1026 v3 PRO" as the new flagship:
1. Daily pages × 365, hyperlinked from weeklies
2. 4 weekly layout options (choose-your-layout page)
3. 10+ hyperlinked covers (cover picker page)
4. Sunday + Monday start versions
5. Dark mode variant (#121212 bg, #E9ECF1 text, desaturated accents)
6. Apple/Google Calendar shortcut buttons on monthly pages
7. Adopt font system: Patrick Hand/Kalam body + Amatic SC or premium script headers
8. +15% line height on all handwriting fields
9. Compress all raster assets (lag prevention)
10. QR-linked video tutorial on welcome page
11. Reprice $19.99; market "free annual updates"
Then propagate the system to DP1027–1029, DP1030 ADHD, DP1033 Teacher.

### P2 — Wall art finishing + style expansion
1. Add grain/texture pass to `upscale_art.py` (Real-ESRGAN + 5–8% noise overlay)
2. Add 3:4 ratio + 24×36 to `generate_print_sizes.py`
3. Launch a **moody vintage oil painting** series (brown/charcoal/cream) — top style we don't cover
4. Launch coordinated **nursery sets** (highest AOV: 3–6 prints/order)
5. Warm palettes in new art: butter yellow, teal, terracotta (2026 interiors)

### P3 — SVG audit + upgrade
1. Technical audit of all 11 live bundles against the 8 gates (nodes, welds, paths, colors, viewBox)
2. Add DXF + EPS to every bundle ZIP
3. Adopt niche font system (Cooper-style retro, Rodeo-style western, Hanley-style farmhouse)
4. Add knockout-text and offset-shadow-layer designs to new bundles
5. Test-import every file in Design Space + Silhouette Studio before listing

---

*Full agent reports preserved in session transcript. Key sources: Paperlike 17 Best Digital Planners 2026, MADEtoPLAN, KDigitalStudio, VectoSolve Cricut SVG Requirements, LetsEnhance AI upscaling guides, Merchize Wall Art Trends 2026, Alura top-seller data, Etsy Seller Handbook.*
