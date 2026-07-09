# OnBrandCraftz — Etsy Automation Hub

## ⛔ TOP PRIORITY RULE — ZERO TOLERANCE: NEVER LIE TO THE CUSTOMER

> **This rule overrides everything else. No exception. No edge case. No shortcut.**

A customer interacts with: listing photos, listing title, listing description, what's included, file specs, compatibility claims, tag keywords, post-purchase messages, and the digital files they receive.

**Every single one of those touchpoints must be 100% truthful and verified against reality.**

### What "lying" includes — all are hard stops:
- A listing photo that shows a product the customer will NOT receive (AI stand-in, wrong color, wrong design)
- A description that claims a file includes something it does not (wrong page count, wrong format, wrong sticker count)
- A title keyword that misrepresents the product (wrong app, wrong year, wrong category)
- A compatibility claim that has not been tested (e.g. "works in GoodNotes" must be verified)
- A file spec (resolution, DPI, page size) that does not match the actual delivered file
- A "200+ stickers" claim when the ZIP contains fewer
- A "10 designs included" claim when only 9 exist in the ZIP
- A photo showing a multi-color 3D print using colors not in the actual delivered SVG/3MF
- Any description section copy-pasted from another listing without verifying it applies to THIS product

### Quality gate rule (non-negotiable):
Before any listing is submitted to Scott for review, an automated quality gate MUST verify:
1. Every file referenced in the description exists on disk and opens without error
2. Page counts, sticker counts, design counts, and file sizes match the description exactly
3. All 10 listing photos were generated from the REAL product files — verified by cross-checking source files used
4. Every compatibility claim (GoodNotes, Notability, Bambu Studio, etc.) has been tested or is an established verified standard
5. Title character count ≤ 70, all 13 tags populated, price matches the tier table
6. The ZIP delivered to the customer was validated by `validate_digital_file()` with zero errors

**If any gate fails → listing is blocked. Fix first. Publish never comes before truth.**

---

## Mission Statement
> **"Providing the best and most accurate transaction for our customers so we can grow responsibly."**

Every product, every image, every price, every line of code must serve this mission.
- **Best and most accurate transaction** = listings show the REAL product, every claim is verified, customers never have to ask what they bought
- **Grow responsibly** = quality never decreases as volume increases; no listing goes live that fails a quality gate; metrics are tracked weekly so decline is caught before damage is done
- Full operating standards: `data/knowledge_base/business_standards.md`

---

## Store
- **Name**: OnBrandCraftz
- **Etsy Shop ID**: `onbrandcraftz`
- **Owner**: Scott
- **Owner email**: Printing3dthings@outlook.com
- **Niche**: Digital planners, kawaii sticker packs, printable digital products, 3D printed physical products
- **Brand aesthetic**: Kawaii illustrated, pastel colors, cute/fun but polished

---

## 3D Printer — Bambu Lab P1S

The physical 3D printed products sold in the shop are printed on a **Bambu Lab P1S**.

### Core Specifications
| Spec | Value |
|---|---|
| Build Volume | 256 × 256 × 256 mm (~10×10×10 in) |
| Max Print Speed | 500 mm/s rated · 220–260 mm/s practical |
| Max Acceleration | 20,000 mm/s² |
| Max Hotend Temp | 300°C (572°F) |
| Max Bed Temp | 100°C (212°F) |
| Passive Chamber Temp | ~40°C (enables ABS/ASA without warping) |
| Noise Level | ~45 dB |
| Motion System | CoreXY |
| Layer Heights | 0.05mm / 0.1mm / 0.2mm |
| Overhang Angle | Up to 55° without supports |

### Key Hardware Features
- **Full enclosure** — passive chamber heating enables engineering filaments (ABS, ASA, PA, PC)
- **Activated carbon + HEPA filtration** — fume/particle capture, safe for indoor use
- **Auto bed leveling** — consistent first layers across every print
- **Input shaping / vibration compensation** — eliminates ringing/ghosting at high speeds
- **Self-cleaning tool head** — purges nozzle before print starts
- **Textured + smooth PEI flex plate** — pops off build plate when cooled
- **Built-in camera** — remote monitoring via Bambu Handy app
- **2.8" monochrome LCD touchscreen**
- **Bambu Studio slicer** — proprietary but full-featured, updated regularly

### AMS — Automatic Material System
- Each AMS unit holds **4 filament spools**
- Up to **4 AMS units** can be chained = **16 colors / materials** per print
- **AMS 2 Pro** (latest generation) is compatible with P1S
- Enables automatic filament switching for multi-color and multi-material prints
- Combo (P1S + AMS): $650–$750 | Printer alone: $399–$449

### Supported Materials
| Material | Use Case | Notes |
|---|---|---|
| **PLA / PLA+** | Most decorative products — vases, signs, holders, figurines | Easiest to print, sharpest details, low failure rate |
| **Silk PLA** | Premium-look products — metallic/shiny finish | Eye-catching for display items; great for koozies |
| **High-Speed PLA** | Production runs where speed matters | AMS compatible |
| **PETG** | Functional/durable parts, outdoor-adjacent use | Better heat + impact resistance than PLA |
| **PETG-CF** | Strong functional parts | Requires hardened steel nozzle |
| **TPU** | Flexible products (koozies, grips, gaskets) | Flexible, bouncy, impact resistant |
| **ABS** | Heat-resistant functional parts | Enclosure required — P1S handles natively |
| **ASA** | Outdoor-safe, UV resistant | Enclosure required |
| **PA / Nylon** | Engineering parts, high wear resistance | Needs drying; 80°C 12+ hrs |
| **PA-CF / PLA-CF** | Strongest prints, stiff and light | Requires hardened steel nozzle |
| **PC (Polycarbonate)** | Highest-strength functional parts | Max temp required |
| **PVA** | Dissolvable support material | Pairs with PLA |

### Nozzle Types
- **Stock brass 0.4mm** — PLA, PETG, TPU, Silk (standard materials only; CF filaments destroy brass fast)
- **Hardened steel 0.4mm** — Required for any carbon fiber or glass fiber filament
- **0.2mm nozzle** — Ultra-fine detail; slow
- **0.6mm / 0.8mm nozzle** — Faster production, less detail

### Build Plate Guide
| Plate | Best For | Avoid |
|---|---|---|
| Textured PEI | PETG, ABS, ASA, PA | Pure PLA can be hard to remove |
| Smooth PEI | PLA, Silk PLA | PETG bonds too strongly — can damage plate |

---

### Production Quality Settings (for selling products)

**The single most important rule: slow down the outer wall. Customers only see the outside.**

| Setting | Value | Why |
|---|---|---|
| Outer wall speed | 50 mm/s or lower | Prevents vibration artifacts, ringing, blobs |
| Outer wall acceleration | 3,000–5,000 mm/s² | Eliminates ghosting on curves |
| Wall order | Outer → Inner | Outer wall printed first = crisper edges |
| Wall generator | Arachne | Better variable-width walls for curved surfaces |
| Precise Wall | On | Dimensional accuracy |
| Seam position | Aligned | Consistent, predictable scar location |
| Seam painting | On hidden edge | Drag seam to back/bottom of model before slicing |
| Ironing | On flat tops | Glass-smooth top surfaces for display items |
| Avoid crossing walls | On | Prevents travel blobs on outer surface |
| Flow Dynamics calibration | Run per filament | Eliminates bulging corners and blobs |
| Flow Rate calibration | Run per filament | Fixes over/under extrusion |

### Filament Preparation (must dry before production runs)
| Filament | Dry Temp | Dry Time |
|---|---|---|
| PLA / PLA+ / Silk | 45°C | 6–8 hours |
| PETG | 65°C | 6–8 hours |
| ABS / ASA | 60°C | 4–6 hours |
| PA / Nylon | 80°C | 12+ hours |
| PC | 80°C | 12+ hours |
*Wet filament = stringing, popping, micro-voids, surface blobs. Never skip drying for sell-worthy prints.*

### Filament Best Picks by Product Type
| Product Type | Recommended Filament | Reason |
|---|---|---|
| Decorative vases | Silk PLA or Matte PLA | Premium finish, no post-processing |
| Can koozies | TPU or Silk PLA | Flexibility (TPU) or premium look (Silk) |
| Lamps / light holders | Translucent PLA or white PLA | Light diffusion |
| Signs / wall art | Silk PLA or dual-color PLA | Visual impact |
| Desk organizers / holders | PLA+ or PETG | Durability for daily use |
| Planters / pots | PETG | Moisture resistance |
| Candle holders | PETG or ABS | Heat tolerance near flame |
| Centerpieces | Silk PLA | Display quality finish |

### Bambu Handy App / Remote Monitoring
- Monitor live via camera from phone
- Start/pause/stop prints remotely
- Receive completion notifications
- View print history and statistics

### Known Limitations
- Proprietary Bambu Studio slicer (less flexible than open-source, but excellent for the ecosystem)
- No heated chamber for ultra-high-temp materials (PEEK, ULTEM)
- Repair ecosystem still maturing vs. established brands
- AMS can have occasional jams with flexible/abrasive filaments

### Current Bambu Lab Printer Lineup (mid-2026)
- **P2S** — Successor to the P1S (2026). 5" color touchscreen, AI error detection, actively regulated 50°C chamber, 70% stronger extruder. Same enclosed CoreXY formula.
- **P1S** — Previous generation, fully supported. All accessories compatible with P2S.
- **X2D** — Successor to the X1 Carbon (X1C discontinued). Lower price than X1C with more features.
- **A1 / A1 Mini** — Open-frame bedslinger, budget tier. Uses AMS Lite (4-slot per unit, up to 8 colors with 2 units).
- **A2L** — New (2026). Larger format (330×320×325mm), optional cutting module. Compatible with AMS Lite and AMS 2 Pro.
- **AMS 2 Pro** — Second-gen AMS. Compatible with P1S, P2S, X2D. 4 spools per unit; chain up to 4 = 16 colors.
- **AMS Lite** — A-series only. Not compatible with P-series printers.

### Competitive Position (2026)
- Farm-grade reliability — trusted by professional print farms
- Receives regular firmware updates from Bambu Lab
- **MakerWorld** (Bambu's model-sharing platform): allows uploading 3D designs for free download or exclusive paid access. Exclusive Program pays creators Exclusive Points cashable at $100+ threshold. Complementary to Etsy (different audience), not a replacement.

### Bambu Studio — SVG Import & Multi-Color Workflow (Verified June 2026)
**IMPORTANT: "Split > By Color" does NOT exist for SVG imports.** This is a long-standing limitation — imported SVGs cannot be split into separate objects in Bambu Studio. The correct workflow is:

1. Drag & drop the SVG into Bambu Studio (or File > Import). Studio extrudes it automatically — set height to 6–10mm.
2. Add filament colors: in the Filament list (left panel), click "+" to add each color needed.
3. Open the **Color Painting tool** (keyboard shortcut: **N**, or the paint-roller icon in the top toolbar).
4. Select the **Fill tool** (bucket icon). Click each closed region of the design to assign its filament color. Clean SVG paths make this fast — an entire sign takes ~2 minutes.
5. Slice. Bambu Studio auto-maps each painted region to the closest AMS slot. Verify the mapping in the print dialog, then print.

**Bambu Handy app:** iOS/Android. Remote start/pause/stop, live camera feed, push notifications on completion, print history, filament tracking. Connects via LAN or Bambu Cloud.

---

## Credentials (all in `.env` — never hardcode, never commit)
- `ANTHROPIC_API_KEY` — Claude API
- `OPENAI_API_KEY` — DALL-E image generation (gpt-image-1)
- `ETSY_API_KEY` / `ETSY_CLIENT_ID` — see `.env`, never paste the literal value here
- `ETSY_CLIENT_SECRET` — see `.env`, never paste the literal value here
- `ETSY_ACCESS_TOKEN` / `ETSY_REFRESH_TOKEN` — empty until OAuth is run
- `SMTP_USER` / `SMTP_PASSWORD` — Outlook email for digital delivery

## Etsy OAuth Status
**Authorized.** Access token and refresh token are set in `.env`. API calls to OnBrandCraftz are live.
If the token expires, run `python tools/etsy_oauth.py` to re-authorize.
Redirect URI registered: `http://localhost:3003/callback`
Scopes: shops_r, shops_w, listings_r, listings_w, transactions_r, billing_r, profile_r, email_r, feedback_r, address_r

---

## Product Catalog

### DP1026 — Ultimate Digital Life Planner (Lavender Dreams)
- **File**: `data/digital_products/product_files/DP1026.pdf` (~7MB, 143 pages)
- **Undated**: `DP1026U.pdf` (~7MB, 143 pages) — perpetual, sells year-round
- **Color scheme**: Lavender Dreams (muted purple #8666AA, soft lavender accent)
- **Cover**: Full-page kawaii illustrated cover (DALL-E, portrait 1024×1536)
- **Structure**: Cover → Welcome/Setup (p2) → Dashboard/Home (p3) → Index (p4) → How-to → Content
- **Sections**: Yearly Overview, Year in Pixels, Monthly × 12, Monthly Review × 12, Month at a Glance × 12, Weekly × 52, Daily × 365, Brain Dump, Habit Tracker, SMART Goals, Budget, Meal Plan, Notes × 4
- **Sticker Library**: 5 pages — Functional Planning, Widget Trackers, Planner & Stationery, Cozy Lifestyle, Seasonal & Holiday
- **Sticker Pack ZIP**: `DP1026_sticker_pack.zip` — 11 sheets, 328 individual stickers, 17.8MB. ✅ Live on Etsy (STICKER_LAVENDER + STICKER_FREE); descriptions updated to 11 sheets / 328+ stickers.
- **Interactive**: Yes — fillable fields, hyperlinked tabs, Dashboard home page, JS popup sticker menu (Acrobat/Xodo)
- **Footer**: ‹ INDEX + 🏠 HOME buttons on every page
- **Compatible apps**: GoodNotes 5/6, Notability, PDF Expert, Xodo, Adobe Acrobat Reader
- **Target price**: $14.99–$16.99
- **Target audience**: Women 18–35, planner lovers, stationery enthusiasts, productivity

### DP1027 — Student & School Planner 2026 (Cotton Candy)
- **File**: `data/digital_products/product_files/DP1027.pdf` (~7MB, 131 pages)
- **Undated**: `DP1027U.pdf` (~7MB, 131 pages)
- **Color scheme**: Cotton Candy (pink #DE97C6, sky blue accent)
- **Structure**: Cover → Welcome/Setup → Dashboard/Home → Index → How-to → Content
- **Sections**: Yearly Overview, Monthly × 12, Monthly Review × 12, Weekly × 52, Daily × 365, Class Schedule, Brain Dump, Priority Matrix, Pomodoro Focus Tracker, Habit Tracker, SMART Goals, Notes × 4
- **Sticker Library**: 5 pages (same 5-sheet system)
- **Sticker Pack ZIP**: `DP1027_sticker_pack.zip` — 11 sheets, 320 individual stickers, 18.2MB. ✅ Live on Etsy (STICKER_COTTON_CANDY); descriptions updated to 11 sheets / 320+ stickers. Note: Sheet 6 individual segmentation originally produced only 1 blob — root-caused 2026-07-03 to the background remover using a strict pure-white (≥238) test that misses the cream sheet background (~RGB 240,237,232); the stickers were never "too connected." Fixed in `tools/process_sticker_sheets.py` (`remove_white_background` now samples the real background color and floods by similarity): Sheet 6 recovers 1 → 21 individual stickers. Regenerate + reupload the DP1027 pack to apply (Scott-gated).
- **Interactive**: Yes
- **Target price**: $9.99–$12.99
- **Target audience**: High school/college students, back to school, study planners

### DP1028 — Budget & Finance Planner 2026 (Midnight Blue)
- **File**: `data/digital_products/product_files/DP1028.pdf` (~7MB, 144 pages)
- **Undated**: `DP1028U.pdf` (~7MB, 144 pages)
- **Color scheme**: Midnight Blue (deep royal blue #1B2568, ice-blue accent)
- **Structure**: Cover → Welcome/Setup → Dashboard/Home → Index → How-to → Content
- **Sections**: Yearly Overview, Monthly × 12, Monthly Review × 12, Month at a Glance × 12, Weekly × 52, Daily × 365, Brain Dump, Habit Tracker, SMART Goals, Budget Tracker × 12, Debt Payoff Tracker, Savings Goal Tracker, Bill Payment Checklist, Notes × 4
- **Sticker Library**: 5 pages
- **Sticker Pack ZIP**: `DP1028_sticker_pack.zip` — 11 sheets, 419 individual stickers, 16.3MB. ✅ Live on Etsy (STICKER_MIDNIGHT_BLUE); descriptions updated to 11 sheets / 419+ stickers.
- **Interactive**: Yes
- **Target price**: $12.99–$14.99
- **Target audience**: Adults tracking finances, budgeters, Dave Ramsey followers, debt payoff community

### DP1029 — Fitness & Wellness Planner 2026 (Coral Peach)
- **File**: `data/digital_products/product_files/DP1029.pdf` (~7MB, 133 pages)
- **Undated**: `DP1029U.pdf` (~7MB, 133 pages)
- **Color scheme**: Coral Peach (warm coral #FD6C49, peach-gold accent)
- **Structure**: Cover → Welcome/Setup → Dashboard/Home → Index → How-to → Content
- **Sections**: Yearly Overview, Monthly × 12, Monthly Review × 12, Weekly × 52, Daily × 365, Brain Dump, Habit Tracker, SMART Goals, Meal Plan, Progress Photos Log, 30-Day Water Tracker, Sleep Quality Log, Non-Scale Victories, Notes × 4
- **Sticker Library**: 5 pages
- **Sticker Pack ZIP**: `DP1029_sticker_pack.zip` — 11 sheets, 377 individual stickers, 15.5MB. ✅ Live on Etsy (STICKER_CORAL_PEACH); descriptions updated to 11 sheets / 377+ stickers.
- **Interactive**: Yes
- **Target price**: $12.99–$14.99
- **Target audience**: Fitness beginners, wellness journey, weight loss, healthy eating, self-care

### DP1030–DP1034 — Expanded Catalog (documentation pending)
The shop has grown beyond DP1029. Products DP1030–DP1034 exist on disk (`data/digital_products/product_files/`) as PDFs (~7–9MB each, dated + undated versions + v2 finals) with sticker pack ZIPs present for all five. Detailed documentation (titles, sections, color schemes) has not been added to CLAUDE.md yet — draft listing content exists for DP1030 (ADHD Planner) and DP1033 (Teacher Planner) in `data/dp1030_listing.json` / `data/dp1033_listing.json`; DP1031, DP1032, DP1034 have no listing content authored yet. None of DP1030–1034 are published (`status: draft`/`ready_for_review`, `etsy_listing_id: ""` in `data/product_catalog.json`). **`data/dp_listing_map.json` does NOT have entries for these codes** — those keys were previously double-booked with 5 already-published wall-art listings, since renamed to `WA1030`–`WA1034` (2026-07-09, same treatment as the earlier `DP1026`→`WA1026` fix). Add real `DP1030`–`DP1034` entries to `dp_listing_map.json` when each planner is actually published.

**Note on sticker ZIPs:** DP1026–DP1034 sticker packs all exist on disk and are all live/complete now. DP1030–1034's packs were regenerated 2026-07-09 — they were previously broken (built 2026-06-30, before the background-removal fix below, or on themed-color backgrounds the fix didn't yet handle) and shipped as 9 sheets × 1 sticker each. `tools/process_sticker_sheets.py`'s background detection was generalized to trust any uniform corner color (not just light backgrounds) and re-run; all five now have 9 real sheets and 240–470+ individual stickers each. See `tools/qc_sweep.py`'s `check_sticker_zip()` — an individual-sticker count under 50 is now a hard FAIL (this exact defect class), not just a warning.

---

## Color Design System & Theme Catalog
*Research-backed color system based on 2026 design trends (Pantone, WGSN, Envato), color psychology studies, Etsy market analysis, and competitor research. Every new planner product must be built from this palette system.*

---

### Color Psychology — What Each Color Does

| Color Family | Psychological Effect | Best Used For |
|---|---|---|
| **Blue / Indigo** | Focus, calm, trust, creativity. University of Washington study: 12% productivity increase | Finance planners, study planners, work planners |
| **Green / Sage** | Growth, success, calm, emotional stability. Triggers "achievement" feeling | Wellness, habit trackers, goal planners |
| **Purple / Lavender** | Creativity, mindfulness, spirituality, luxury | Life planners, journaling, artistic audiences |
| **Pink / Rose** | Warmth, nurturing, optimism, fun | Kawaii, student, self-care, bridal |
| **Orange / Coral** | Motivation, energy, combats fatigue. Orange at low saturation increases productivity | Fitness, fitness beginners, high-energy audiences |
| **Yellow / Gold** | Optimism, alertness, serotonin boost, focus | Happiness journals, productivity planners |
| **Brown / Mocha** | Comfort, sophistication, warmth, grounded stability | Budget, professional, premium audiences |
| **Charcoal / Black** | Power, elegance, focus, reduces visual noise | Dark mode, professionals, premium tier |
| **Teal / Aqua** | Balance of calm (blue) + growth (green), futuristic, fresh | Wellness, ADHD calming, modern aesthetics |
| **Cream / Off-White** | Clarity, serenity, "blank canvas" creativity. Pantone 2026 CoY | Minimalist, journaling, mature audiences |

---

### 2026 Color Trend Authorities

**Pantone Color of the Year 2026:** Cloud Dancer `#F4F0EA` — soft airy off-white between warm and cool. Radiates calm, clarity, serenity. "Blank canvas for creativity."

**WGSN 2026 Key Color:** Transformative Teal `#3B8E8A` — fusion of dependable dark blue and aquatic green. Grounded yet futuristic, represents change and connection with nature.

**Trending 2026 Macro Palettes (Envato/Adobe research):**
- **Sunwashed Soft** — peachy warm pastels, sun-faded warmth (peach, cream, warm sand)
- **Mermaidcore** — shimmering aqua, seafoam, pearl, iridescent violet
- **Clubroom Contrast** — bold black + gold luxury (underserved in planner market!)
- **Warm Earth Revival** — taupe, sandy beige, deep chocolate, chestnut (brown having a major moment)
- **Spring Vivid Brights** — Alexandrite purple, Lava Falls red-orange, Fuchsia, Mint (bold and punchy)
- **Deep Botanical** — forest green, terracotta, sage, warm botanical greens

---

### Current Product Color Schemes

| Product | Theme Name | Primary | Accent | Neutral | Status |
|---|---|---|---|---|---|
| DP1026 | Lavender Dreams | `#8666AA` muted purple | `#C4A8D4` soft lavender | `#FAF7FF` cream-white | ✅ Live |
| DP1027 | Cotton Candy | `#DE97C6` bubblegum pink | `#97C6DE` sky blue | `#FFF6FC` blush white | ✅ Live |
| DP1028 | Midnight Blue | `#1B2568` deep royal blue | `#7BA7C2` ice blue | `#F0F5FF` cloud white | ✅ Live |
| DP1029 | Coral Peach | `#FD6C49` warm coral | `#F5B878` peach-gold | `#FFF8F4` warm cream | ✅ Live |

---

### New Theme Catalog — 12 Designs Ready to Build

Each theme includes: name, hex palette, target aesthetic, target buyer, and the emotion it should evoke.

---

#### 🌸 Theme 01 — Cherry Blossom
**Tagline:** *"Soft as spring, organized as ever"*
| Role | Hex | Description |
|---|---|---|
| Primary | `#F4A7B9` | sakura pink |
| Accent | `#F9D0DB` | petal blush |
| Deep accent | `#C4607A` | rose petal |
| Neutral | `#FFF5F7` | cherry cream |
| Text | `#3D1A24` | deep rose-black |
- **Aesthetic:** Japanese sakura, soft spring, feminine, delicate
- **Kawaii motifs:** cherry blossom branches, tiny petals falling, bunnies in flower fields, spring birds
- **Target buyer:** Women 18–30, spring new-year-fresh-start buyers, Japan-aesthetic lovers
- **Best product:** DP1026 Life Planner cover variant, standalone spring sticker pack
- **Trend alignment:** Seasonal spring, evergreen kawaii aesthetic

---

#### 🌿 Theme 02 — Sage Garden
**Tagline:** *"Grounded. Calm. Growing."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#8BA888` | muted sage green |
| Accent | `#C8DDB5` | soft fern |
| Deep accent | `#556B50` | forest sage |
| Neutral | `#F6F8F2` | morning dew |
| Text | `#2C3828` | deep forest |
- **Aesthetic:** Cottagecore, botanical, garden, calm nature
- **Kawaii motifs:** tiny mushrooms, herb sprigs, watering cans, garden snails, flower pots, bees
- **Target buyer:** Cottagecore/nature lovers, wellness community, gardeners, women 25–40
- **Best product:** DP1029 Fitness/Wellness cover variant, DP1031 Undated Evergreen planner
- **Trend alignment:** Pantone spring palette, Deep Botanical macro trend, cottagecore Etsy niche

---

#### 🌙 Theme 03 — Celestial Night
**Tagline:** *"Plan by the stars"*
| Role | Hex | Description |
|---|---|---|
| Primary | `#1E1B4B` | deep indigo |
| Accent | `#C9A84C` | starlight gold |
| Mid tone | `#6B5FA5` | twilight purple |
| Neutral | `#F0EEF8` | moonbeam white |
| Text on dark | `#F9F6FF` | pearl white |
- **Aesthetic:** Celestial, astrology, moon phases, stars, mystical kawaii
- **Kawaii motifs:** crescent moons, stars, constellations, sleeping moon faces, tiny planets, comets, crystal balls
- **Target buyer:** Astrology community (massive on Etsy), witchy aesthetic, Gen Z, spiritual wellness buyers
- **Best product:** DP1032 Dark Mode Planner (celestial variant), standalone celestial sticker pack
- **Trend alignment:** Dark mode trend, Y3K aesthetic, celestial Etsy niche (consistently top 5 planner aesthetic)

---

#### ☕ Theme 04 — Mocha Latte
**Tagline:** *"Sophisticated. Warm. Ready for anything."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#8B5E3C` | warm mocha |
| Accent | `#D4A96A` | caramel |
| Mid tone | `#C8A882` | latte beige |
| Neutral | `#FDF8F0` | cream foam |
| Text | `#2C1A0E` | espresso |
- **Aesthetic:** Café aesthetic, warm brown luxury, sophisticated minimalist
- **Kawaii motifs:** coffee cups with cream swirls, croissants, tiny café scenes, autumn leaves, cozy mugs
- **Target buyer:** Coffee lovers, women 25–40, VSCO/aesthetic crowd, mature planner buyers
- **Best product:** DP1026 Life Planner, DP1028 Budget Planner (premium feel)
- **Trend alignment:** 2026 Warm Earth Revival macro trend, brown is having a major moment in design

---

#### 🧜 Theme 05 — Mermaidcore
**Tagline:** *"Deep-sea dreams, surface-level organized"*
| Role | Hex | Description |
|---|---|---|
| Primary | `#4ABFBF` | ocean teal |
| Accent | `#B8A9D9` | sea lavender |
| Shimmer | `#A8E6CF` | seafoam |
| Neutral | `#F0FAFF` | pearl mist |
| Text | `#1A3A4A` | deep ocean |
- **Aesthetic:** Mermaid, ocean, iridescent, fantasy kawaii
- **Kawaii motifs:** mermaid tails, shells, bubbles, starfish, pearls, seahorses, coral
- **Target buyer:** Fantasy/ocean lovers, Gen Z, creative dreamers, summer buyers
- **Best product:** DP1031 Undated Evergreen (fresh + timeless), summer seasonal release
- **Trend alignment:** Mermaidcore is one of the top 3 macro design trends for 2026 (Envato research)

---

#### 🍂 Theme 06 — Dark Academia
**Tagline:** *"Knowledge is power. Plan accordingly."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#3B2A1A` | aged leather brown |
| Accent | `#9B7D3A` | antique gold |
| Mid tone | `#7A5C3F` | warm mahogany |
| Neutral | `#F5EDD6` | aged parchment |
| Text | `#1C1208` | ink black |
- **Aesthetic:** Dark academia, vintage library, Victorian stationery, moody intellectual
- **Kawaii motifs:** tiny books, quill pens, ink bottles, hourglasses, candles, dried flowers, keys
- **Target buyer:** Students (especially college), book lovers, aesthetic Tumblr/Pinterest crowd, dark aesthetic buyers
- **Best product:** DP1027 Student Planner cover variant, DP1033 Teacher Planner
- **Trend alignment:** Dark academia is a top-performing Etsy aesthetic with dedicated buyer communities

---

#### 🌺 Theme 07 — Tropical Hibiscus
**Tagline:** *"Bright energy. Big plans."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#FF6B9D` | hot pink |
| Accent | `#FFD166` | sunshine yellow |
| Mid tone | `#06D6A0` | tropical mint |
| Neutral | `#FFFAF0` | ivory |
| Text | `#3D0029` | deep berry |
- **Aesthetic:** Tropical, maximalist, Gen Z, bold & colorful (rejects minimalism)
- **Kawaii motifs:** tropical flowers, pineapples, flamingos, parrots, watermelon slices, suns
- **Target buyer:** Gen Z buyers, bold personality types, summer seasonal, "Play Haus" aesthetic crowd
- **Best product:** DP1027 Student Planner, DP1029 Fitness Planner (high-energy niche match)
- **Trend alignment:** "Play Haus" 2026 trend (Gen Z's colorful rejection of minimalism), Spring Vivid Brights

---

#### ✨ Theme 08 — Rose Gold Luxe
**Tagline:** *"You deserve gold. And a good plan."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#B76E79` | dusty rose gold |
| Accent | `#D4AF7A` | champagne gold |
| Mid tone | `#F2C4CE` | blush |
| Neutral | `#FDF8F8` | pearl white |
| Text | `#4A2030` | deep wine |
- **Aesthetic:** Luxury, aspirational, rose gold glam, feminine premium
- **Kawaii motifs:** tiny diamonds, hearts with crowns, champagne flutes, makeup brushes, perfume bottles, stars
- **Target buyer:** Women 25–40, aspirational buyers, bridal/wedding planners, hustle culture crowd
- **Best product:** DP1026 Ultimate Life Planner (premium tier), DP1028 Budget Planner (financial goals)
- **Trend alignment:** Rose gold is perennially strong for premium digital products, Clubroom Contrast luxury aesthetic

---

#### 🌊 Theme 09 — Ocean Breeze
**Tagline:** *"Clear mind. Calm days. Clear goals."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#3B8E8A` | transformative teal |
| Accent | `#7EC8C8` | seafoam |
| Mid tone | `#A8D8D8` | aqua mist |
| Neutral | `#F0FAFA` | morning sea |
| Text | `#0D3535` | deep teal |
- **Aesthetic:** Coastal, clean, fresh, calming, modern minimalist
- **Kawaii motifs:** waves, seashells, sailboats, jellyfish, sea glass, beach umbrellas, lighthouses
- **Target buyer:** Wellness-focused buyers, adults 30–45, productivity minimalists, coastal aesthetic
- **Best product:** DP1029 Wellness Planner, DP1028 Budget Planner (calm & focused)
- **Trend alignment:** WGSN's Transformative Teal is the #1 key color for 2026 — this is on-trend at the highest level

---

#### 🔮 Theme 10 — Midnight Kawaii (Dark Mode)
**Tagline:** *"Cute goes dark."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#1A1A2E` | deep midnight |
| Accent | `#E040FB` | electric violet |
| Pop accent | `#00E5FF` | neon aqua |
| Mid tone | `#2D2B55` | space purple |
| Text | `#F0E6FF` | starlight |
- **Aesthetic:** Dark kawaii, Y3K, futuristic, neon-on-dark
- **Kawaii motifs:** glowing stars, neon-outlined cats, holographic elements, pixel art kawaii, spaceship chibi
- **Target buyer:** Dark aesthetic Gen Z, gamers, night-owl planners, tech-forward buyers
- **Best product:** DP1032 Dark Mode Planner (primary), great for ADHD planner (less visual overwhelm on dark bg)
- **Trend alignment:** Dark mode is standard in competitors; "Mood Mode" / Y3K neon accents are 2026-specific

---

#### 🌼 Theme 11 — Sunflower Studio
**Tagline:** *"Growth season. Every day."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#F4C430` | sunflower yellow |
| Accent | `#4A7C59` | stem green |
| Mid tone | `#F8E08E` | soft gold |
| Neutral | `#FFFDF0` | cream petal |
| Text | `#2A1A00` | seed brown |
- **Aesthetic:** Bright botanical, positive, cheerful, nature + sunshine
- **Kawaii motifs:** sunflowers, bees, garden tools, butterflies, ladybugs, seeds sprouting
- **Target buyer:** Positive-mindset community, spring/summer buyers, gardening niche, teachers
- **Best product:** DP1033 Teacher Planner, DP1026 Life Planner (positivity focus)
- **Trend alignment:** Yellow is scientifically proven for optimism and serotonin, Deep Botanical trend

---

#### 🍵 Theme 12 — Matcha Serenity
**Tagline:** *"Slow down. Sip. Succeed."*
| Role | Hex | Description |
|---|---|---|
| Primary | `#6B8F5E` | matcha green |
| Accent | `#B8CC8E` | pale chartreuse |
| Mid tone | `#E8F0D8` | green tea cream |
| Neutral | `#F7F9F3` | rice paper |
| Text | `#1E2D18` | deep forest |
- **Aesthetic:** Japanese minimalist, matcha café, slow living, mindfulness
- **Kawaii motifs:** matcha cups, bamboo, koi fish, zen stones, lotus flowers, tiny bento boxes
- **Target buyer:** Mindfulness/slow living community, Japan aesthetic lovers, wellness buyers, women 22–35
- **Best product:** DP1029 Wellness Planner, DP1030 ADHD Planner (calming tones reduce overwhelm)
- **Trend alignment:** Sage green / botanical tones are 2026 Deep Botanical macro trend, mindfulness is evergreen

---

### Theme-to-Product Mapping

| Product | Launch Theme | Phase 2 Covers to Add |
|---|---|---|
| DP1026 Life Planner | Lavender Dreams ✅ | Cherry Blossom · Mocha Latte · Rose Gold Luxe · Dark Academia |
| DP1027 Student Planner | Cotton Candy ✅ | Dark Academia · Tropical Hibiscus · Matcha Serenity · Ocean Breeze |
| DP1028 Budget Planner | Midnight Blue ✅ | Mocha Latte · Rose Gold Luxe · Ocean Breeze · Celestial Night |
| DP1029 Fitness Planner | Coral Peach ✅ | Sage Garden · Tropical Hibiscus · Matcha Serenity · Sunflower Studio |
| DP1030 ADHD Planner | Matcha Serenity | Ocean Breeze · Midnight Kawaii · Sage Garden |
| DP1031 Undated Evergreen | Sage Garden | Cherry Blossom · Mocha Latte · Mermaidcore |
| DP1032 Dark Mode Bundle | Midnight Kawaii | Celestial Night · Dark Academia |
| DP1033 Teacher Planner | Sunflower Studio | Sage Garden · Cherry Blossom · Mocha Latte |

---

### Color Design Rules (apply to every planner built)

1. **Maximum 4 colors per planner** — Primary + Accent + Mid-tone + Neutral (plus black for text)
2. **60-30-10 rule** — 60% neutral/background, 30% primary color, 10% accent pops
3. **Minimum contrast ratio 4.5:1** — text on background (WCAG AA accessibility standard)
4. **Never pure black (#000000)** — use deep tinted black matching the palette (e.g., `#2C1810` for mocha, `#1C1208` for dark academia)
5. **Never pure white (#FFFFFF)** — use a cream/tinted neutral (e.g., `#FDF8F0`, `#F7F9F3`)
6. **Dark mode backgrounds** — use `#1A1A2E` to `#2D2D2D` range, never pure black
7. **Tab color coding** — assign one hue from the palette to each section, vary by saturation
8. **Weekend vs weekday** — weekend calendar cells should be 15% lighter than weekday cells
9. **Cover design rule** — the kawaii illustration accent color must match the primary hex exactly
10. **Consistency across all 10 listing photos** — props, backgrounds, and accent items must match the product's color theme

---

## What Customers Receive (Digital Download)
Etsy delivers files instantly at checkout — no shipping. Each listing includes:
- **File 1**: The planner PDF — 2026 dated version (interactive, fillable, hyperlinked)
- **File 2**: The planner PDF — undated evergreen version (same layout, no year dates)
- **File 3**: Sticker Pack ZIP — 5 PNG sticker sheets (200+ stickers) with transparent backgrounds

**PDF format details:**
- US Letter size (8.5×11 in)
- Welcome/Setup page (p1), Dashboard/Home hub (p2), Planner Index (p3)
- Fillable form fields for all text areas
- Hyperlinked side navigation tabs (GoodNotes/Notability compatible)
- 🏠 HOME footer button on every page
- PDF bookmarks/outline for table of contents
- Interactive sticker menu (Acrobat Reader / Xodo / PDF Expert only)

---

## Sticker System — How It Works Per App

### GoodNotes 6 / Notability (most buyers — 90%+)
- **Sticker PNG sheets**: Tap Elements → Stickers → + (import) → select PNG files from ZIP
- All 5 sticker sheets appear in library; tap any sticker to drag onto any page, unlimited copies
- **PDF sticker button**: Navigates to the sticker library pages (no JS in GoodNotes)
- **Recommended workflow to tell buyers**: Import sticker PNGs first, then use the planner PDF

### Adobe Acrobat Reader (iOS, Android, Desktop)
- **Sticker button in footer**: Tapping opens a popup menu → pick category → pick sticker → drops as a draggable label annotation anywhere on the current page
- Annotations are draggable and stay placed
- Works on iPhone, iPad, Mac, Windows, Android

### PDF Expert / Xodo
- Same JS popup sticker menu as Acrobat (these apps support PDF JavaScript)
- Full interactivity: fillable fields, sticker popup, hyperlinks all work

### Apple Preview / Browser viewers
- Static PDF only — no interactivity
- Tell buyers to use one of the compatible apps above

---

## Etsy Listing Format Requirements

### 2026 Conversion Optimization Standards
Research-backed rules that must be applied to every listing:

**Titles:**
- Etsy weights the **first 40 characters most heavily** — lead with the exact keyword buyers type
- Structure: `[Primary Keyword] | [Secondary Keyword] | [Feature Keyword] | [Occasion/App]`
- Use natural language, not keyword stuffing — Etsy's 2026 algorithm penalizes repetition
- Include the year (2026), the app (GoodNotes/Notability), and "Instant Download"

**Tags:**
- Use all 13 tags — every empty slot is a missed ranking opportunity
- Each tag must be a **multi-word buyer-intent phrase** (e.g., "goodnotes planner" not just "planner")
- Tags must align with title keywords — exact title phrases in tags boost ranking
- Use long-tail over broad: "digital budget planner" beats "planner"
- Max 20 characters per tag including spaces

**Descriptions:**
- The **first two sentences** must hook the buyer AND contain the primary keyword (mobile users see only this much before the fold)
- Include primary keyword naturally in sentence 1 for Google external search indexing
- Use emoji section headers (━━━ dividers) for scanability — most buyers skim, not read
- Answer the 4 buyer questions: What is it? What's included? Which apps? How do I get it?
- FAQ section reduces pre-purchase questions and refund requests

**Photos — the #1 conversion factor:**
- **46% of Etsy purchases are on mobile app** (Q4 2025 official data) — every photo decision is mobile-first
- Lifestyle thumbnail → 2–3x higher CTR than flat white background (verified; "314%" claim is inflated)
- Use all 10 photo slots — each additional image increases conversion rate
- Recommended size: **2400×2400px square** (outperforms 2000px by estimated 7–12% CTR)
- Keep subject in center **70% of frame** — Etsy crops thumbnails on mobile
- Add **5% neutral-tone padding** around edges — prevents mobile thumbnail cropping
- **Show art in 2 different rooms** — buyers shop by room first, then by art style
- **Include a gallery wall image** — buyers who see grouped art are 40% more likely to buy multiple
- **Include a size reference shot** — art shown against sofa with furniture context removes #1 question
- **3 props max per scene** — more than 3 clutters; fewer than 3 looks staged and flat
- Full research: `data/knowledge_base/lifestyle_photo_mastery.md`

---

### Titles (max 70 chars — ALL listing types)
- **Hard limit: 70 characters.** Etsy's 2026 algorithm applies a mobile ranking penalty above 70 chars. 70%+ of Etsy traffic is mobile.
- Lead with the PRIMARY search keyword buyers type in first 20-30 characters
- Use comma separators, not pipes
- Include year (2026) or "Undated" for evergreen
- Include app compatibility (GoodNotes) in first 40 chars
- Example: `Digital Planner 2026 Undated, GoodNotes iPad, Instant Download` (62 chars)

### Descriptions — Required Sections in Order
1. **Hook** (1–2 sentences): Emotion-first + primary keyword in sentence 1 for Google indexing
2. **WHAT'S INCLUDED** (bullet list): Every file, page count, sections, sticker sheets
3. **COMPATIBLE APPS** (list): GoodNotes 6, Notability, PDF Expert, Xodo, Acrobat Reader, print-ready
4. **HOW TO USE STICKERS** (3 steps): Import PNGs into sticker library → drag unlimited times
5. **HOW TO USE THE PLANNER** (numbered steps): Download → open in app → tap to fill
6. **SECTIONS INCLUDED** (list): Every section name with brief description + page count in header
7. **TECHNICAL DETAILS**: File format, size, page count, page size, color theme
8. **FAQ**: 5 questions covering compatibility, printing, physical vs. digital, sharing/licensing
9. **COPYRIGHT**: Personal use only, not for resale or redistribution

### Tags (max 13, each max 20 chars, no special characters)

**DP1026 — Ultimate Digital Life Planner:**
`digital planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `kawaii planner`, `fillable planner`, `2026 life planner`, `kawaii sticker pack`, `instant download`, `printable planner`, `daily planner pdf`, `planner bundle`, `habit tracker pdf`

**DP1027 — Student & School Planner:**
`student planner`, `digital planner`, `school planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `academic planner`, `study planner`, `kawaii planner`, `fillable planner`, `back to school`, `instant download`, `kawaii sticker pack`

**DP1028 — Budget & Finance Planner:**
`budget planner`, `finance planner`, `digital planner`, `goodnotes planner`, `money planner`, `ipad planner`, `fillable planner`, `savings planner`, `debt payoff planner`, `kawaii planner`, `instant download`, `budget tracker`, `2026 budget plan`

**DP1029 — Fitness & Wellness Planner:**
`fitness planner`, `wellness planner`, `digital planner`, `goodnotes planner`, `health planner`, `ipad planner`, `habit tracker`, `meal planner pdf`, `kawaii planner`, `fillable planner`, `instant download`, `self care planner`, `2026 fitness plan`

### Pricing Strategy
| Product | Price | Reasoning |
|---------|-------|-----------|
| DP1026 Ultimate | $14.99 | 104 pages + kawaii cover + 5-sheet sticker pack — premium |
| DP1027 Student | $9.99 | Student budget — lower price point for volume |
| DP1028 Budget | $12.99 | Niche audience, high value perception |
| DP1029 Fitness | $12.99 | Niche audience, wellness = premium feel |

### Etsy Fees to Factor In
- 6.5% transaction fee on sale price
- $0.20 listing fee per listing (renews every 4 months or per sale)
- Payment processing: 3% + $0.25
- Net at $14.99: ~$12.15 | Net at $9.99: ~$8.00 | Net at $12.99: ~$10.50

### Shop Sections to Create
1. Digital Planners
2. Kawaii Sticker Packs
3. Digital Downloads

### Etsy Category / Taxonomy
- Digital planners: Craft Supplies & Tools > Patterns & How To > Digital Files (taxonomy_id: 2078)
- Alternative: Paper & Party Supplies > Calendars & Planners

### Listing Photos — Required Package (10 max)

Use all 10 slots. Each image tells one chapter of the buyer's story. Technical specs for every image: **2400×2400px square**, subject in center 70% of frame, 5% white/neutral margin at edges.

**Storytelling sequence (in order):**

1. **[HERO] Lifestyle iPad Shot** ← Most important; determines thumbnail click-through rate
   - iPad Pro 12.9" at 30° angle on a cozy desk, screen showing the planner cover or a beautiful monthly/weekly spread
   - Lifestyle props: latte mug, succulent, washi tape, dried flowers or stationery
   - Soft natural window light from the left; warm white balance
   - This image MUST stop the scroll — it is the only image seen in search results
   - No text overlays; no hands visible

2. **[TRUST] What's Included**
   - Left panel: PDF icon + bold page count + color theme name
   - Right panel: 5 sticker PNG sheets fanned out, stickers clearly visible
   - Text callouts added in Canva post: product page count, "5 sticker sheets", "200+ stickers", "Instant Download"
   - Builds buyer confidence before purchase; the #2 reason people click away is unclear value

3. **[PREVIEW] Monthly Spread**
   - Clean in-app screenshot of a full monthly calendar page
   - Shows the color theme, kawaii design, fillable cells, and section headers
   - Slight lifestyle context (iPad held or on desk)

4. **[PREVIEW] Weekly Spread**
   - Close-up of a weekly layout page showing time-blocking rows, fillable fields, kawaii typography
   - Side tab navigation visible to show hyperlinked navigation

5. **[BONUS] Sticker Library**
   - All 5 PNG sticker sheets displayed flat, stickers large and legible
   - Label each sheet in Canva post: "Sheet 1: Functional Planning", "Sheet 2: Widget Trackers", etc.
   - This image sells the sticker pack bonus — buyers specifically search for sticker packs

6. **[HOW-TO] GoodNotes Import Steps**
   - 3-panel sequential graphic: Step 1 (Elements panel open), Step 2 (file picker), Step 3 (sticker on page)
   - Numbered circles in product color
   - Reduces buyer anxiety and cuts refund requests — show them exactly how it works

7. **[COMPATIBILITY] App Logos Graphic**
   - Planner icon in center, surrounded by: GoodNotes, Notability, PDF Expert, Xodo, Acrobat icons
   - Thin pastel connecting lines; checkmark badge on each
   - Text (added in Canva): "Works with your favorite apps"

8. **[BEAUTY] Cover Close-Up**
   - iPad screen filling 80% of frame, straight-on angle, showing the full kawaii illustrated cover
   - Blurred product-color background (fabric or surface)
   - Showcases illustration quality — buyers buying kawaii want to see the art up close

9. **[FEATURE] Habit Tracker Page**
   - Habit tracker open in-app, some example rows filled in showing interactivity
   - Apple Pencil beside the iPad; motivational sticky note prop

10. **[FEATURE] Specialty Page** (product-specific)
    - DP1026: Budget Tracker or Meal Planner page
    - DP1027: Study Schedule / weekly class tracker
    - DP1028: Monthly Budget breakdown page with income/expenses
    - DP1029: Weekly Fitness Log or Meal Planner
    - Use thematically matching props (calculator+coin purse for budget; protein shaker for fitness; backpack for student)

---

## Listing Agent Workflow (Step-by-Step)

When asked to list a planner on Etsy:
1. Call `get_approved_unlisted_products` to see what's ready
2. Products must have `status: qc_pending` or `status: approved`
3. Call `generate_listing_content` with the full pre-written template (see below)
4. Generate all 10 listing photos using `generate_digital_art` with the prompts below
5. Once ETSY_ACCESS_TOKEN is set (run `python tools/etsy_oauth.py`), call `publish_digital_listing`
6. After publishing, upload the PDF and sticker pack ZIP as digital files on the Etsy listing

---

## Pre-Written Listing Content

### DP1026 — Ultimate Digital Life Planner

**Title** (62 chars — 2026 70-char mobile rule):
`Digital Planner 2026 Undated, GoodNotes iPad, Instant Download`

**Tags**:
`digital planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `kawaii planner`, `fillable planner`, `2026 life planner`, `kawaii sticker pack`, `instant download`, `printable planner`, `daily planner pdf`, `planner bundle`, `habit tracker pdf`

**Price**: $14.99

**Description**:
```
✨ Stay organized, stay cute — your ultimate kawaii digital life planner for GoodNotes and Notability is here!

Meet the Ultimate Digital Life Planner 2026, the most complete fillable PDF planner for GoodNotes, Notability, and iPad — packed with 143 beautifully designed pages, an illustrated kawaii cover, a full kawaii sticker pack (200+ stickers, 5 sheets!), and a bonus undated evergreen version so you can use it any year.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 143 pages, US Letter, Lavender Dreams color theme
✅ Bonus Undated Version — same planner, no year dates, works any year forever
✅ Kawaii Sticker Pack ZIP — 5 PNG sticker sheets (200+ stickers, transparent background)
   • Sheet 1: Functional Planning — headers, checklists, flags, date dots, priority labels
   • Sheet 2: Widget Trackers — mood tracker, water intake, sleep log, habit tracker, energy meter
   • Sheet 3: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 4: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 5: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
✅ Fully fillable — type directly in GoodNotes, Notability, PDF Expert, or Acrobat
✅ Hyperlinked side tabs — jump to any section in one tap
✅ Interactive sticker menu — tap STICKERS button for drag-and-drop sticker fun

━━━━━━━━━━━━━━━━━━━━━━━━
📱 COMPATIBLE APPS
━━━━━━━━━━━━━━━━━━━━━━━━
★ GoodNotes 6 (iPad, iPhone, Mac) — BEST experience
★ Notability (iPad, iPhone)
★ PDF Expert by Readdle
★ Xodo PDF Reader
★ Adobe Acrobat Reader (all platforms)
★ Print-ready — print at home or at a print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 HOW TO USE YOUR STICKERS
━━━━━━━━━━━━━━━━━━━━━━━━
1. Unzip your sticker pack after downloading
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 5 PNG files
3. Your stickers now live in your GoodNotes library — drag any sticker onto any page, unlimited times!
   (Notability: use Photo Stickers | PDF Expert/Acrobat: use the built-in STICKERS button in the planner footer)

━━━━━━━━━━━━━━━━━━━━━━━━
📖 HOW TO USE THE PLANNER
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download your files instantly from Etsy
2. Open the PDF in GoodNotes 6, Notability, or PDF Expert
3. Tap any text box to type — all fields are fillable
4. Use the side tabs to jump between sections
5. Import sticker PNGs for unlimited kawaii decoration

━━━━━━━━━━━━━━━━━━━━━━━━
📅 SECTIONS INCLUDED (143 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Welcome & Setup Guide — app links, how-to steps, support contact
• Dashboard / Home — tappable hub linking to every section in one tap
• Planner Index — complete table of contents with page numbers
• Yearly Overview — see all 12 months at a glance
• Year in Pixels — 12-month mood tracker grid, one colored box per day
• Monthly Calendars × 12 — full month grid with daily notes
• Monthly Reviews × 12 — reflect, celebrate wins, plan improvements
• Month at a Glance × 12 — top priorities, focus areas, intentions
• Weekly Spreads × 52 — time-blocked horizontal layout for every week of 2026
• Daily Pages × 365 — top 3 priorities, hour-by-hour schedule, notes, gratitude
• Brain Dump — free-write page to clear your head before planning
• Habit Tracker — 31-day grid, fully customizable
• SMART Goals — quarterly goals, action steps, milestones
• Budget Tracker — income, expenses, savings, bills
• Meal Planner — weekly meal plan with grocery list
• Notes Pages × 4 — lined + dot-grid mix
• Kawaii Sticker Library × 5 — 200+ illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF (2026 dated + undated versions included)
• Page size: US Letter (8.5 × 11 inches)
• Pages: 143 (each version)
• Color theme: Lavender Dreams
• File size: ~15MB PDF + sticker ZIP
• Delivery: Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Does this work on iPhone?
A: Yes! GoodNotes 6, Notability, and Adobe Acrobat Reader all work on iPhone. GoodNotes gives the best experience on iPad.

Q: Can I print this?
A: Absolutely! Print at home or at any print shop. Works great as a physical planner too.

Q: What if GoodNotes updates and it stops working?
A: PDFs are a universal format — they'll always open. The fillable fields and tabs work across all versions.

Q: Is this a physical item?
A: No — this is a digital download only. You'll receive a PDF and ZIP file instantly after purchase.

Q: Can I share this with friends?
A: This license is for personal use only. Please don't share, resell, or redistribute the files.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.
```

---

### DP1027 — Student & School Planner

**Title** (61 chars — 2026 70-char mobile rule):
`Kawaii Student Planner 2026, GoodNotes iPad, Instant Download`

**Tags**:
`student planner`, `digital planner`, `school planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `academic planner`, `study planner`, `kawaii planner`, `fillable planner`, `back to school`, `instant download`, `kawaii sticker pack`

**Price**: $9.99

**Description**:
```
🎓 Study smarter, plan cuter — the kawaii student planner for GoodNotes and Notability that makes school actually fun!

Meet the Kawaii Student Planner 2026, the most adorable fillable PDF planner for GoodNotes, Notability, and iPad — packed with 131 beautifully designed pages in a dreamy Cotton Candy color theme, plus a full kawaii sticker pack (200+ stickers, 5 sheets!) and a bonus undated version to personalize every week of your school year.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 131 pages, US Letter, Cotton Candy color theme (pink + sky blue)
✅ Bonus Undated Version — same planner, no year dates, works any school year forever
✅ Kawaii Sticker Pack ZIP — 5 PNG sticker sheets (200+ stickers, transparent background)
   • Sheet 1: Functional Planning — headers, checklists, flags, date dots, priority labels
   • Sheet 2: Widget Trackers — mood tracker, water intake, sleep log, habit tracker, energy meter
   • Sheet 3: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 4: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 5: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
✅ Fully fillable — type directly in GoodNotes, Notability, PDF Expert, or Acrobat
✅ Hyperlinked side tabs — jump to any section in one tap
✅ Interactive sticker menu — tap STICKERS button for drag-and-drop sticker fun

━━━━━━━━━━━━━━━━━━━━━━━━
📱 COMPATIBLE APPS
━━━━━━━━━━━━━━━━━━━━━━━━
★ GoodNotes 6 (iPad, iPhone, Mac) — BEST experience
★ Notability (iPad, iPhone)
★ PDF Expert by Readdle
★ Xodo PDF Reader
★ Adobe Acrobat Reader (all platforms)
★ Print-ready — print at home or at a print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 HOW TO USE YOUR STICKERS
━━━━━━━━━━━━━━━━━━━━━━━━
1. Unzip your sticker pack after downloading
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 5 PNG files
3. Your stickers now live in your GoodNotes library — drag any sticker onto any page, unlimited times!
   (Notability: use Photo Stickers | PDF Expert/Acrobat: use the built-in STICKERS button in the planner footer)

━━━━━━━━━━━━━━━━━━━━━━━━
📖 HOW TO USE THE PLANNER
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download your files instantly from Etsy
2. Open the PDF in GoodNotes 6, Notability, or PDF Expert
3. Tap any text box to type — all fields are fillable
4. Use the side tabs to jump between sections
5. Import sticker PNGs for unlimited kawaii decoration

━━━━━━━━━━━━━━━━━━━━━━━━
📅 SECTIONS INCLUDED (131 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Welcome & Setup Guide — app links, how-to steps, support contact
• Dashboard / Home — tappable hub linking to every section in one tap
• Planner Index — complete table of contents with page numbers
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with daily note cells
• Monthly Reviews × 12 — reflect on wins, set next month's focus
• Weekly Spreads × 52 — class schedule layout with assignment tracker per subject
• Daily Pages × 365 — top 3 priorities, hour-by-hour schedule, notes, gratitude
• Class Schedule — weekly class times and room tracker
• Brain Dump — free-write page before each week to clear your head
• Priority Matrix — Urgent/Important 2×2 grid for ADHD-friendly planning
• Pomodoro Focus Tracker — 25-min work / 5-min break timer boxes
• Habit Tracker — 31-day grid for study streaks, self-care, and daily goals
• SMART Goals — semester goals, action steps, milestones
• Notes Pages × 4 — lined + dot-grid for lecture notes or brainstorming
• Kawaii Sticker Library × 5 — 200+ illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF (2026 dated + undated versions included)
• Page size: US Letter (8.5 × 11 inches)
• Pages: 131 (each version)
• Color theme: Cotton Candy (pink #DE97C6 + sky blue)
• File size: ~13MB PDF + sticker ZIP
• Delivery: Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Does this work on my school laptop?
A: Yes! Open in Adobe Acrobat Reader (free) on any Windows or Mac laptop. All fields are fillable.

Q: Can I print this?
A: Absolutely! Print at home or at a campus print center. Works great as a physical binder planner too.

Q: Is this dated for 2026 only?
A: The calendar pages are dated for 2026. Weekly and notes pages work any time.

Q: Is this a physical item?
A: No — this is a digital download only. You'll receive a PDF and ZIP file instantly after purchase.

Q: Can I share this with my study group?
A: This license is for personal use only. Please don't share, resell, or redistribute the files.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.
```

---

### DP1028 — Budget & Finance Planner

**Title** (64 chars — 2026 70-char mobile rule):
`Digital Budget Planner 2026 Undated, GoodNotes, Instant Download`

**Tags**:
`budget planner`, `finance planner`, `digital planner`, `goodnotes planner`, `money planner`, `ipad planner`, `fillable planner`, `savings planner`, `debt payoff planner`, `kawaii planner`, `instant download`, `budget tracker`, `2026 budget plan`

**Price**: $12.99

**Description**:
```
💰 Take control of your money in the most adorable way possible — your kawaii budget planner for GoodNotes and Notability is here!

Meet the Digital Budget & Finance Planner 2026, the most complete fillable PDF money planner for GoodNotes, Notability, and iPad — packed with 144 beautifully designed pages in a sleek Midnight Blue color theme, with built-in trackers for every dollar, debt, and financial goal you have — plus a bonus undated version and 200+ kawaii stickers.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 144 pages, US Letter, Midnight Blue color theme
✅ Bonus Undated Version — same planner, no year dates, works any year forever
✅ Kawaii Sticker Pack ZIP — 5 PNG sticker sheets (200+ stickers, transparent background)
   • Sheet 1: Functional Planning — headers, checklists, flags, date dots, priority labels
   • Sheet 2: Widget Trackers — mood tracker, water intake, sleep log, habit tracker, energy meter
   • Sheet 3: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 4: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 5: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
✅ Fully fillable — type directly in GoodNotes, Notability, PDF Expert, or Acrobat
✅ Hyperlinked side tabs — jump to any section in one tap
✅ Interactive sticker menu — tap STICKERS button for drag-and-drop sticker fun

━━━━━━━━━━━━━━━━━━━━━━━━
📱 COMPATIBLE APPS
━━━━━━━━━━━━━━━━━━━━━━━━
★ GoodNotes 6 (iPad, iPhone, Mac) — BEST experience
★ Notability (iPad, iPhone)
★ PDF Expert by Readdle
★ Xodo PDF Reader
★ Adobe Acrobat Reader (all platforms)
★ Print-ready — print at home or at a print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 HOW TO USE YOUR STICKERS
━━━━━━━━━━━━━━━━━━━━━━━━
1. Unzip your sticker pack after downloading
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 5 PNG files
3. Your stickers now live in your GoodNotes library — drag any sticker onto any page, unlimited times!
   (Notability: use Photo Stickers | PDF Expert/Acrobat: use the built-in STICKERS button in the planner footer)

━━━━━━━━━━━━━━━━━━━━━━━━
📖 HOW TO USE THE PLANNER
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download your files instantly from Etsy
2. Open the PDF in GoodNotes 6, Notability, or PDF Expert
3. Tap any text box to type — all fields are fillable
4. Use the side tabs to jump between sections
5. Import sticker PNGs for unlimited kawaii decoration

━━━━━━━━━━━━━━━━━━━━━━━━
💸 SECTIONS INCLUDED (144 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Welcome & Setup Guide — app links, how-to steps, support contact
• Dashboard / Home — tappable hub linking to every section in one tap
• Planner Index — complete table of contents with page numbers
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with bill-due date markers
• Monthly Reviews × 12 — reflect on spending wins, set savings intentions
• Month at a Glance × 12 — monthly income, fixed expenses, savings target, debt minimum
• Weekly Spreads × 52 — week-by-week spending log and task list
• Daily Pages × 365 — top 3 priorities, hour-by-hour schedule, notes, gratitude
• Brain Dump — free-write page to clear your head before budgeting
• Habit Tracker — 31-day grid for no-spend days and money habits
• SMART Goals — financial goals, debt payoff milestones, savings targets
• Budget Tracker × 12 — monthly income vs. expenses breakdown, net savings
• Debt Payoff Tracker — snowball/avalanche method visual progress bar
• Savings Goal Tracker — visual thermometer fill-in
• Bill Payment Checklist — monthly recurring bills check-off
• Notes Pages × 4 — lined for ideas, financial planning, or research
• Kawaii Sticker Library × 5 — 200+ illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF (2026 dated + undated versions included)
• Page size: US Letter (8.5 × 11 inches)
• Pages: 144 (each version)
• Color theme: Midnight Blue (deep royal blue #1B2568 + ice-blue accent)
• File size: ~14MB PDF + sticker ZIP
• Delivery: Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Does this work on iPhone?
A: Yes! GoodNotes 6, Notability, and Adobe Acrobat Reader all work on iPhone. GoodNotes gives the best experience on iPad.

Q: Can I print this?
A: Absolutely! Print at home or at any print shop. Works great as a physical budgeting binder too.

Q: Can I use this with Dave Ramsey / zero-based budgeting?
A: Yes! The monthly budget pages have income, expense category rows, and a balance field — perfect for zero-based budgeting, envelope method, or any system.

Q: Is this a physical item?
A: No — this is a digital download only. You'll receive a PDF and ZIP file instantly after purchase.

Q: Can I share this with my partner?
A: This license is for personal use only. If your partner wants a copy, they'll need their own purchase. Thank you for supporting small creators!

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.
```

---

### DP1029 — Fitness & Wellness Planner

**Title** (65 chars — 2026 70-char mobile rule):
`Digital Fitness Planner 2026 Undated, GoodNotes, Instant Download`

**Tags**:
`fitness planner`, `wellness planner`, `digital planner`, `goodnotes planner`, `health planner`, `ipad planner`, `habit tracker`, `meal planner pdf`, `kawaii planner`, `fillable planner`, `instant download`, `self care planner`, `2026 fitness plan`

**Price**: $12.99

**Description**:
```
🌸 Your glow-up starts now — the kawaii fitness planner for GoodNotes and Notability that makes healthy habits actually stick!

Meet the Fitness & Wellness Planner 2026, your all-in-one fillable PDF wellness companion for GoodNotes, Notability, and iPad — packed with 133 beautifully designed pages in a warm Coral Peach color theme, with habit trackers, meal planning, and fitness logs — plus a bonus undated version and 200+ kawaii stickers to support your healthiest year yet.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 133 pages, US Letter, Coral Peach color theme
✅ Bonus Undated Version — same planner, no year dates, works any year forever
✅ Kawaii Sticker Pack ZIP — 5 PNG sticker sheets (200+ stickers, transparent background)
   • Sheet 1: Functional Planning — headers, checklists, flags, date dots, priority labels
   • Sheet 2: Widget Trackers — mood tracker, water intake, sleep log, habit tracker, energy meter
   • Sheet 3: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 4: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 5: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
✅ Fully fillable — type directly in GoodNotes, Notability, PDF Expert, or Acrobat
✅ Hyperlinked side tabs — jump to any section in one tap
✅ Interactive sticker menu — tap STICKERS button for drag-and-drop sticker fun

━━━━━━━━━━━━━━━━━━━━━━━━
📱 COMPATIBLE APPS
━━━━━━━━━━━━━━━━━━━━━━━━
★ GoodNotes 6 (iPad, iPhone, Mac) — BEST experience
★ Notability (iPad, iPhone)
★ PDF Expert by Readdle
★ Xodo PDF Reader
★ Adobe Acrobat Reader (all platforms)
★ Print-ready — print at home or at a print shop

━━━━━━━━━━━━━━━━━━━━━━━━
🎨 HOW TO USE YOUR STICKERS
━━━━━━━━━━━━━━━━━━━━━━━━
1. Unzip your sticker pack after downloading
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 5 PNG files
3. Your stickers now live in your GoodNotes library — drag any sticker onto any page, unlimited times!
   (Notability: use Photo Stickers | PDF Expert/Acrobat: use the built-in STICKERS button in the planner footer)

━━━━━━━━━━━━━━━━━━━━━━━━
📖 HOW TO USE THE PLANNER
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download your files instantly from Etsy
2. Open the PDF in GoodNotes 6, Notability, or PDF Expert
3. Tap any text box to type — all fields are fillable
4. Use the side tabs to jump between sections
5. Import sticker PNGs for unlimited kawaii decoration

━━━━━━━━━━━━━━━━━━━━━━━━
🏃 SECTIONS INCLUDED (133 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Welcome & Setup Guide — app links, how-to steps, support contact
• Dashboard / Home — tappable hub linking to every section in one tap
• Planner Index — complete table of contents with page numbers
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with workout and self-care markers
• Monthly Reviews × 12 — celebrate wins, reflect on habits, reset intentions
• Weekly Spreads × 52 — weekly workout planner + daily water intake + mood tracker
• Daily Pages × 365 — top 3 priorities, hour-by-hour schedule, notes, gratitude
• Brain Dump — free-write page to clear your head before planning
• Habit Tracker — 31-day grid for workouts, water, sleep, nutrition, and self-care
• SMART Goals — fitness goals, milestone celebrations, progress measurements
• Meal Planner — weekly meal plan with grocery list + macro/calorie note row
• Progress Photos Log — before/after date headers with measurement fields
• 30-Day Water Tracker — monthly glass-fill illustration
• Sleep Quality Log — track hours and quality every night
• Non-Scale Victories — celebration journal for wins beyond the scale
• Notes Pages × 4 — lined for journaling, research, or recipe notes
• Kawaii Sticker Library × 5 — 200+ illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF (2026 dated + undated versions included)
• Page size: US Letter (8.5 × 11 inches)
• Pages: 133 (each version)
• Color theme: Coral Peach (warm coral #FD6C49 + peach-gold accent)
• File size: ~14MB PDF + sticker ZIP
• Delivery: Instant digital download — no physical item shipped

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Does this work on iPhone?
A: Yes! GoodNotes 6, Notability, and Adobe Acrobat Reader all work on iPhone. GoodNotes gives the best experience on iPad.

Q: Can I print this?
A: Absolutely! Print at home or at a print shop. Makes a great physical wellness binder too.

Q: Do I need to already be fit to use this?
A: Not at all! This planner is designed for beginners starting their wellness journey just as much as dedicated athletes. Use it to build habits, track small wins, and stay motivated.

Q: Is this a physical item?
A: No — this is a digital download only. You'll receive a PDF and ZIP file instantly after purchase.

Q: Can I share this with a friend?
A: This license is for personal use only. Please don't share, resell, or redistribute the files.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale, redistribution, or commercial use.
```

---

## Digital Planner Excellence Standards
*Research-backed standards from analyzing top Etsy bestsellers and buyer reviews (2025–2026). Every new product and every update to existing planners should meet these benchmarks.*

---

### Page Architecture — Every Planner Must Include

**Navigation Foundation (3 required pages before any content):**

1. **Welcome / Setup Page** — Page 1 of every planner. Include:
   - Branded title + kawaii cover art thumbnail
   - "How to download your files" (3 bullet steps)
   - "How to import into GoodNotes / Notability" (3 bullet steps with app icon)
   - Link to tutorial YouTube video (or placeholder text: "Watch setup tutorial → [link]")
   - Customer support email (Printing3dthings@outlook.com)
   - Top sellers that include a welcome page see 30–40% fewer support messages

2. **Dashboard / Home Page** — Page 2. A central hub that hyperlinks to every section. Design like an app home screen:
   - Product name + color theme + year 2026
   - Tappable section buttons: Yearly Overview · Monthly · Weekly · [Specialty Section] · Habit Tracker · Goals · Notes · Stickers
   - "BACK TO HOME" button hyperlinked from the footer of every subsequent page
   - Color-coded section buttons matching the tab color for that section

3. **Planner Index** — Page 3. A text-based list of every section with clickable page numbers. Useful for GoodNotes table of contents mode.

**Dated + Undated Bundle (sell both in one listing — major differentiator):**
- The 2026 dated version for buyers who want a fresh start
- An undated "evergreen" version for mid-year buyers — sells all year, not just January
- Export as two separate PDFs, zip together as the deliverable
- Add "2026 + Undated Version Included" to every listing title

**Daily Pages (currently missing — highest requested feature):**
- Top competitors include Daily Spreads × 365 in addition to weekly
- Add daily page sections to DP1026 (life planner) and DP1027 (student) first
- Daily layout: date header, top 3 priorities, hour-by-hour schedule (6am–10pm), notes, gratitude box, water tracker
- Daily pages increase total page count and justify higher price point

**Multiple Weekly Layout Options:**
- Include 2 weekly layout variations (buyers hate having only one choice)
- Option A: Horizontal time-blocked (Mon–Sun with morning/afternoon/evening rows)
- Option B: Vertical column layout (7 equal columns, hour blocks)
- Let buyers choose by hyperlink from a "Choose Your Layout" page

---

### Hyperlink Architecture — Complete Navigation Map

Every page in the planner must have these navigation elements:

**Side Tab System (persistent on every page):**
- Tabs in the same position on every single page — never shift their location
- Clicking any tab always returns to the first page of that section
- Tab labels: YR (yearly) · JAN through DEC (monthly) · WK (weekly) · [niche section] · HAB (habits) · GOAL · NOTE · ✦ (stickers)
- Color-coded: each section gets a distinct accent color from the product palette

**Footer Navigation Bar (on every page):**
- ← PREV | 🏠 HOME | NEXT → (three small tappable areas)
- HOME always links back to the Dashboard (page 2)
- PREV / NEXT scroll within the current section

**Cross-section Deep Links:**
- Monthly page → hyperlinks to each week within that month
- Weekly page → hyperlinks to each daily page (when daily pages exist)
- Every specialty page (budget, habit, meal) → links back to its monthly parent
- Sticker library pages → "BACK" link to wherever the user came from

**External Calendar Integration (premium feature — adds perceived value):**
- Include a dedicated "Add to Calendar" button on monthly pages
- Links to: `webcal://` Apple Calendar (pre-populated with month name) or a Google Calendar URL
- Note in listing description: "Tap to add important dates to your Apple or Google Calendar"

---

### Cover System — Minimum Standard

Current state: 1 cover per product.
Bestsellers on Etsy: 100+ covers.
**Our target: 10 covers per product (minimum 5 at launch).**

**Required cover set for each product:**
1. **Primary (current)** — The main kawaii illustrated cover
2. **Seasonal Spring** — Cherry blossoms, soft green accents
3. **Seasonal Fall** — Pumpkins, warm amber tones
4. **Dark Mode** — Same kawaii art on deep charcoal / navy background (trending!)
5. **Minimalist** — Clean typography, no illustration, just the product color theme
6. **Bonus: Custom Name Cover** — "Add your name" cover with a fillable name field

**How to implement:**
- All covers are Page 1 of the PDF (one active, others in an appendix "Cover Gallery")
- Buyers cut-paste their preferred cover to Page 1 in GoodNotes
- Add "10 cover designs included" to every listing title and description
- Cover gallery page is hyperlinked from the Dashboard

---

### Sticker Pack Standards — Expansion Roadmap

Current state: 3 sheets × ~20 stickers = ~60 total stickers.
Bestsellers: 3,500+ stickers.
**Our target: 5 sheets × 40 stickers = 200+ stickers.**

**Expand to 5 sticker sheets (replacing/expanding the current 3):**

1. **Functional Headers & Banners** *(NEW — most requested type)*
   - Section headers: "This Week", "Top 3", "Don't Forget", "Today's Goals", "Gratitude"
   - Ribbon banners, flag labels, scrolls, tag shapes
   - All in the product's color palette, kawaii-styled typography

2. **Mood & Wellness Trackers** *(NEW — high demand)*
   - Mood faces (happy, tired, anxious, excited, calm, meh) — kawaii circle faces
   - Energy level meters (battery icon 0–100%)
   - Sleep quality (moon phases: full/crescent/quarter)
   - Water droplet counters (fill in daily)

3. **Planner & Stationery** *(existing — keep and expand)*
   - Notebooks, pens, pencil cases, washi tape, stars, coffee cups
   - Expand with: highlighters, paper clips, sticky notes, bookmarks

4. **Cozy Lifestyle** *(existing — keep and expand)*
   - Candles, mugs, books, fairy lights, sleeping cat
   - Expand with: ramen bowl, matcha latte, headphones, cozy blanket, plants

5. **Seasonal & Holiday** *(existing — keep and expand)*
   - Cherry blossoms, pumpkins, snowflakes, valentines
   - Expand with: summer sun, back-to-school pencil, new year fireworks, Christmas tree, Halloween bat

**Sticker PNG specs:**
- 300 DPI minimum
- Transparent background (PNG, not JPG)
- Individual stickers: 300–600px each at 300 DPI
- Sheet size: 3000×3000px per sheet
- Include both a sheet PNG (for reference) and individual cut stickers in a subfolder

---

### UX Design Principles

**Readability standards:**
- Minimum font size for fillable fields: 11pt (touch-friendly)
- Section header labels: 14–16pt bold kawaii font
- Tab labels: 9–11pt, must be legible at actual iPad screen scale
- Line height in weekly/daily boxes: minimum 0.5 inches for handwriting space

**Color system consistency:**
- Maximum 4 colors per planner (primary, accent, neutral, black)
- All text on light background (dark-on-light), all text on dark backgrounds white
- Section color coding: use the product's accent color as a hue — vary saturation per section
- Weekday vs. weekend: weekend columns slightly lighter to distinguish at a glance

**Layout density:**
- Leave 15% empty/breathing space on every page — never cram
- Generous tap targets: buttons and tabs minimum 44×44pt (Apple HIG standard)
- Fillable areas need visible field boundaries (light box or underline)

**Functional design principles:**
- Every decorative element has a practical twin: the kawaii coffee cup sticker doubles as a "coffee break" mood marker
- Sections flow logically: big-picture → detailed (yearly → monthly → weekly → daily)
- The planner should work equally well typed and handwritten (both use cases are buyers)

---

### Niche Enhancement Guide (per product)

**DP1026 — Ultimate Life Planner (Lavender Dreams)**
- Primary audience: women 18–35, productivity-focused
- Add: Pomodoro focus timer sheet, brain dump page, vision board page
- Add: "Year in Pixels" mood tracker (12-month grid, one colored box per day)
- Cover expansion priority: dark mode + minimalist covers first
- Future version: "DP1026 Landscape Edition" — same content, horizontal iPad orientation

**DP1027 — Student Planner (Cotton Candy)**
- Primary audience: high school + college students
- **ADHD-friendly features to add** (booming niche on Etsy):
  - Time-blocking layout with visual chunking
  - Pomodoro focus sheet (25-min work / 5-min break timer boxes)
  - "Brain Dump" free-write page before each week
  - Priority matrix (Urgent/Important 2×2 grid)
  - "3 Wins Today" celebration box on every daily page
- Add: Class schedule template, exam countdown tracker, reading log
- Future version: "DP1027 ADHD Edition" as a separate product (massive market)

**DP1028 — Budget Planner (Midnight Blue)**
- Primary audience: adults budgeting, Dave Ramsey followers, debt payoff community
- Add: Debt Payoff Tracker (snowball/avalanche method visual progress bar)
- Add: Savings Goal Tracker (visual thermometer fill-in)
- Add: Bill Payment Checklist (monthly recurring bills check-off)
- Add: Annual Net Worth snapshot page
- Cover expansion priority: professional dark mode cover (navy professionals love dark themes)
- Future version: "DP1028 Zero-Based Budget Edition" with envelope method pages

**DP1029 — Fitness Planner (Coral Peach)**
- Primary audience: beginners starting a wellness journey
- Add: Progress Photos log page (before/after date headers with measurement fields)
- Add: Water intake monthly tracker (30-day glass-fill illustration)
- Add: Sleep quality log
- Add: Supplement + medication tracker
- Add: "Non-Scale Victory" celebration journal page
- Cover expansion priority: energetic gradient sunrise cover + dark athletic cover
- Future version: "DP1029 30-Day Challenge Edition" — 30 consecutive daily layouts

---

### Product Roadmap

**Phase 1 — Upgrade Existing 4 Products (highest ROI)**
Priority order based on sales impact:
1. Add Welcome page + Dashboard to all 4 planners
2. Add "BACK TO HOME" footer on every page
3. Add undated version to all 4 (double the product value, minimal work)
4. Expand sticker packs to 5 sheets (200+ stickers)
5. Add 5 cover options to each product

**Phase 2 — New Products**
| ID | Product | Color | Rationale |
|----|---------|-------|-----------|
| DP1030 | ADHD Digital Planner 2026 | Soft Mint (#7EC8A4) | Fastest-growing niche on Etsy, low competition with kawaii aesthetic |
| DP1031 | Undated Life Planner (Evergreen) | Sage Green (#8BA888) | Sells year-round, no 2026 expiry, recurring annual revenue |
| DP1032 | Dark Mode Planner Bundle | Charcoal (#2D2D2D) | Trending dark aesthetic, stand out from all-pastel competition |
| DP1033 | Teacher Planner 2026–2027 | Warm Yellow (#F5C842) | Academic year (Aug–Jul), back-to-school peak season |

**Phase 3 — Premium Tier**
- Landscape editions of DP1026 and DP1027 (charged at $2–4 premium)
- "Bundle all planners" listing ($29.99 for all 4 — anchors individual prices)
- Customizable name covers as a paid add-on ($5–8 via custom order)

---

### Competitor Benchmarks (know what you're competing against)

| Feature | Our Current | Mid-Tier Competitors | Top Sellers |
|---------|-------------|---------------------|-------------|
| Covers included | 1 | 5–10 | 100–240 |
| Sticker count | ~60 | 200–500 | 3,500+ |
| Total pages | 88–102 | 150–300 | 500–700+ |
| Orientations | Portrait only | Portrait + Landscape | Portrait + Landscape + A4 |
| Daily pages | No | Sometimes | Yes (365+) |
| Dated + Undated | Dated only | Sometimes both | Always both |
| Welcome page | No | Sometimes | Always |
| Tutorial video link | No | Sometimes | Always |
| Cover variety | 1 | 5–10 | 100+ |
| Calendar integration | No | Rare | Yes (Apple/Google) |

**Our competitive advantage:** Kawaii aesthetic + kawaii sticker pack in the *same* download. Most competitors do not bundle a coordinated sticker pack. This is our main differentiator — lean into it hard in all copy and photos.

---

## 3D-Print SVG Pack Production Pipeline — Mandatory Standards (SS-Series)
*Every new SVG pack listing must pass ALL of these gates before going live. No exceptions.*

---

### Universal Listing Rules (apply to ALL listing types — no exceptions)

These rules apply regardless of product category. Violations block publishing.

**No duplicate images.** All 10 photo slots must contain unique images. No photo may appear more than once in a listing. Verified by MD5 hash before upload.

**Lifestyle photos must be generated with an edit-style call (`tools/image_gen.py`'s `edit_image()`) using the actual downloadable product file as input.** No AI-generated stand-in products. No placeholder art. The exact files the customer downloads are passed in as the input image. This is the only method that guarantees the listing photo shows what the customer actually receives. See THE STANDARD LIFESTYLE METHOD in the Image Generation section.

**EVERY photo in EVERY listing must be generated with an approved AI image engine — HARD RULE (Scott, June 2026; updated July 2026 for multi-engine).** Approved engines, selected via the existing `engine=` param / `IMAGE_ENGINE` setting in `tools/image_gen.py` — never a hardcoded choice in a script:
- **gpt-image-1** (OpenAI) — current default, proven, use when unsure. **Shuts down 2026-10-23** (confirmed on OpenAI's deprecations page) — the only engine that supports `background="transparent"` for sticker/cut-out assets, so it must stay available for that use case even after gpt-image-2 becomes the default for everything else.
- **gpt-image-2** (OpenAI) — gpt-image-1's successor (shipped 2026-04-21), same account/API key. Native reasoning, sharper in-image text, flexible sizes. Does **not** support `background="transparent"` — `tools/image_gen.py` raises a clear error if you try; use gpt-image-1 for stickers/cut-outs until/unless that changes.
- **Gemini "Nano Banana"** (`gemini-2.5-flash-image`) — best at keeping the same product consistent across scenes; prefer for multi-photo listing mockups
- **Ideogram 3.0** — best in-image text (covers/badges); generate-only, no edit/input-image support
This applies to all 10 slots, not just lifestyle shots. No PIL-only graphics, no plain solid-color backgrounds, no other image software (Stable Diffusion, ComfyUI, or any self-hosted generator) unless a demonstrably better tool replaces one of the four above. Per-slot method:
- Lifestyle / detail shots: a pure generate call is never acceptable here — use the engine's edit path with the real product file(s) as input (Ideogram can't do this — use gpt-image-1/2 or Gemini for these slots)
- Flat lays / collection shots with multiple designs: generate the background + pixel-perfect PIL paste of the REAL design files on top (edit-style calls garble small text with 5+ inputs, regardless of engine)
- Infographics / spec sheets / how-to graphics: generate the background + PIL text overlay (no engine reliably renders text baked into the image — Ideogram and gpt-image-2 are the closest, still verify before shipping)
- Stickers / cut-out assets requiring a transparent background: engine="openai" (gpt-image-1) only — gpt-image-2 cannot do this

**Every listing undergoes a complete pre-publish checklist before going live.** A listing cannot be submitted for Scott's review unless every gate below for its category has been run and passed. "Looks good" is not a gate. The gate is code.

---

### SS-Series SVG Pack — Title
- Max 70 chars (hard limit — mobile ranking penalty above)
- Formula: `[Design Theme] SVG, 3D Print [Type], Instant Download`
- Must contain "SVG" in the first 30 chars
- Must end with "Instant Download"
- Comma separators only — no pipes
- Target: 60–70 chars

### SS-Series SVG Pack — Tags (13 exactly, each ≤20 chars)
- Zero tags may duplicate any phrase already in the title
- Must cover: design/theme · print method · slicer · use case · format · audience
- Always include at least one: `[theme] svg files`, `3d print svg`, `svg cut file`, `digital download`

### SS-Series SVG Pack — Price
- 5-design packs: **$9.99**
- 10+ design packs: **$14.99**
- Must end in `.99`, `.97`, or `.49`

### SS-Series SVG Pack — Category
- taxonomy_id: 2078 (Craft Supplies & Tools > Patterns & How To > Digital Files)
- `type: "download"` | `who_made: "i_did"` | `when_made: "made_to_order"` | `is_supply: false`

### SS-Series SVG Pack — Photos (10 slots)
Slots 1–6: Lifestyle — all must carry the "DIGITAL FILE — SVG DOWNLOAD" badge (top-left corner)
| # | Type | Content |
|---|---|---|
| 1 | HERO | Gallery wall — 2–3 signs displayed |
| 2 | LIFESTYLE | Interior 1 (mantel, shelf, or living room) |
| 3 | LIFESTYLE | Interior 2 (porch, entryway, or bedroom) |
| 4 | LIFESTYLE | Tiered tray or small-scale display |
| 5 | LIFESTYLE | Outdoor / yard / garden setting |
| 6 | COLLECTION | All designs flat-lay or side-by-side overview |

Slots 7–10: Informational (no badge required)
| # | Type | Content |
|---|---|---|
| 7 | HOW-TO | Bambu Studio 3-step import — must show Color Painting Fill tool. NEVER show "Split by Color" (that menu does not exist) |
| 8 | DETAIL | Close-up of one finished sign showing multi-color layer detail |
| 9 | SPECS | What's included — ZIP contents graphic |
| 10 | LINEUP | All N design previews rendered side by side |

### SS-Series SVG Pack — Description (sections in this exact order)
1. Hook — emoji opener, primary keyword in sentence 1
2. ⚠️ DISCLAIMER (bold, above the fold) — "DIGITAL DOWNLOAD of SVG files — NOT a physical sign. No physical item will be shipped."
3. Pack overview — design count, dimensions, colors per design, plate compatibility
4. WHAT'S INCLUDED — bullet list including digital-only reminder
5. COMPATIBLE PRINTERS & SLICERS — Bambu Lab P-series #1, then any FDM multi-color, single-color options
6. HOW TO PRINT IN BAMBU STUDIO — 5 numbered steps: Import → Add filaments → Color Painting (press N) → Fill tool → Slice → Print. NEVER mention "Split by Color."
7. SIZE & SCALING
8. DISPLAY IDEAS
9. TECHNICAL DETAILS — includes "NO PHYSICAL ITEM SHIPPED"
10. FAQ — minimum 5 Qs: Is this physical? AMS required? Resize? Other slicers? License?
11. ABOUT THIS DESIGN — AI disclosure paragraph
12. COPYRIGHT — OnBrandCraftz, personal use + gifts only

### SS-Series SVG Pack — File Packaging
- **SVG file quality (hard requirement):** Every SVG in the ZIP must be a clean vector design. Tracked raster images exported as SVG are NOT acceptable. Quality thresholds enforced by `validate_digital_file()` in `etsy_api.py`:
  - Unique fill colors per SVG: ≤ 20 (clean vectors have 1–4 discrete fills; traced rasters have 500+)
  - Path elements per SVG: ≤ 200 (clean vectors have <50; traced rasters have 600–900)
  - File size per SVG: ≤ 150 KB (clean vectors are typically <50 KB; traced rasters are 475–750 KB)
- **Primary format (required): .3mf per design** — all color layers pre-assembled at correct Z heights (base 0–4mm, raised layers 4–6mm). Customer opens one file in Bambu Studio, assigns AMS slots, slices. This is the gold standard — no manual positioning needed.
- **Layer SVG format (also included):** Separate SVG per color layer (`layer01_base_WHITE.svg`, `layer02_red_RED.svg`, etc.), identical dimensions and origin. Included for advanced users who want to resize before printing. Customer imports each layer as a separate Part and manually positions in Z.
- **IMPORTANT — Single-file SVG is INVALID for multi-color printing:** Bambu Studio merges all SVG paths into ONE object on import — per-color region assignment is impossible from a single SVG (GitHub Issue #8044, unfixed). Never deliver a single multi-color SVG as the primary file.
- ZIP naming: `[ProductID]_[theme]_3dprint_pack.zip`
- 3MF naming: `[ProductID]_[design_name].3mf` (one per design)
- Layer SVG naming: `layer01_base_[COLOR].svg`, `layer02_[COLOR].svg`, etc. (same viewBox on all layers)
- README.txt required in every ZIP — must document both 3MF and layer SVG workflows; no "Split by Color" anywhere
- ZIP size: under 20 MB (Etsy hard limit)

### SS-Series SVG Pack — Pre-Publish Quality Gate Checklist
Run through every item before submitting for Scott review. If any item fails, fix it. Do not submit with known failures.

**File Quality (most critical)**
- [ ] Run `validate_digital_file(zip_path)` — must pass with zero errors
- [ ] Layer SVGs confirmed as clean vectors: ≤20 unique fills, ≤200 paths, ≤150 KB each
- [ ] All layer SVGs within a design share the same viewBox dimensions and origin point
- [ ] 3MF files present — one per design, all color layers pre-assembled at correct Z heights
- [ ] README.txt documents both 3MF and layer SVG workflows — no "Split by Color" anywhere
- [ ] Build script: `tools/build_[product]_zip.py` generates and validates the ZIP

**Listing Content**
- [ ] Title: 60–70 chars, contains "SVG", contains "Instant Download", comma separators
- [ ] Tags: all 13 used, each ≤20 chars, zero duplicate title phrases
- [ ] Description: all 12 sections present in order, ⚠️ disclaimer above the fold
- [ ] Price: matches tier table, ends in .99/.97/.49

**Photos**
- [ ] All 10 photos unique — no duplicates (verify by MD5 hash)
- [ ] Lifestyle photos (slots 1–6) generated with `images.edit` using actual downloadable SVG files as input
- [ ] "DIGITAL FILE — SVG DOWNLOAD" badge present on all 6 lifestyle photos
- [ ] Photo 7 HOW-TO shows Color Painting Fill tool — not "Split by Color"
- [ ] All 10 photos are distinct scenes — no two show the same setting

**File**
- [ ] ZIP contains correct SVG files and README.txt
- [ ] ZIP is under 20 MB
- [ ] ZIP passes `validate_digital_file()` with zero errors

---

## Wall Art Production Pipeline — Mandatory Standards
*Every new wall art listing must pass ALL of these gates before going live. No exceptions.*

---

### Gate 1: Art File Resolution (HARD REQUIREMENT)
**Minimum accepted master file: 3,000×4,500px (2:3 portrait) or equivalent area for other ratios.**
Any file below this is rejected from the production pipeline — do NOT create a listing from it.

| Accepted | Rejected |
|---|---|
| 3,000×4,500px or larger | 1,024×1,536px (AI raw output) |
| 3,000×3,875px or larger (4:5) | Any file under 3,000px on the short edge |

**Upscaling workflow for undersized files:**
1. Run `tools/upscale_art.py` — applies 4× Lanczos + UnsharpMask (radius=2, percent=150, threshold=3)
2. Output saved to `data/digital_products/product_files/upscaled/`
3. Verify output is ≥4,000px on the short edge before proceeding

**Color space:** Export all final files as **sRGB**. Never AdobeRGB or CMYK — Etsy auto-converts and color shifts on print are a top-3 review complaint.

---

### Gate 2: Multi-Size ZIP Delivery (HARD REQUIREMENT)
**Never upload a single JPG as the Etsy digital file.** Buyers expect multiple print sizes. Single-file listings generate the most "wrong size" complaints and refund requests.

**Run `tools/generate_print_sizes.py` for every new art file.** This produces a ZIP with:

| Folder | Sizes Included |
|---|---|
| `2x3/` | 4×6", 8×12", 12×18", 16×24" at 300 DPI |
| `4x5/` | 8×10", 16×20" at 300 DPI |
| `a_series/` | A4, A3 at 300 DPI |
| `square/` | 8×8", 12×12" at 300 DPI |
| root | `README.txt` with printing instructions |

- File naming: `DP1030_8x10_300dpi.jpg` (never IMG_4456.jpg)
- ZIP max size: 20MB (Etsy hard limit). Script auto-reduces JPEG quality to stay under.
- ZIP saved to: `data/digital_products/print_zips/DP####_print_sizes.zip`
- Upload ZIP to Etsy listing via `EtsyAPIClient.upload_listing_file()`

---

### Gate 3: Title — 2026 Algorithm Rules (HARD REQUIREMENT)
**Maximum 70 characters.** Titles over 70 chars receive a mobile ranking penalty (70%+ of Etsy traffic is mobile).

**Formula:**
```
[Primary search phrase] Printable Wall Art, Instant Download, [Style/room]
```

Rules:
- First 20–30 characters = highest algorithm weight — lead with the exact phrase buyers type
- Must include: "printable" AND "instant download"
- Use comma separators, not pipes
- Target: 55–70 characters
- **Do NOT repeat title phrases in tags** (wastes ranking slots — see Gate 4)

**Validation:** Run `len(title)` before publishing. Hard reject if > 70.

---

### Gate 4: Tags — 13 Slots, Zero Wasted (HARD REQUIREMENT)
- Use all 13 tag slots — every empty slot is a missed ranking opportunity
- **No tag may duplicate a phrase already in the title** — this is the #1 tag mistake and costs ranking coverage
- Every tag must be 2–3 words, max 20 characters including spaces
- Cover all 6 intent categories across the 13 tags:

| Category | Example Tags |
|---|---|
| Style/aesthetic | `boho wall art`, `dark academia`, `cottagecore art` |
| Room type | `bedroom wall art`, `living room art`, `office wall decor` |
| Art medium | `watercolor print`, `line art print`, `botanical print` |
| Occasion/use | `housewarming gift`, `gallery wall art`, `new home gift` |
| Recipient | `gift for her`, `nature lover gift`, `art lover gift` |
| Format | `printable poster`, `digital art print`, `downloadable art` |

**Automated audit:** Run `tools/audit_fix_wall_art_tags.py` after any batch of new listings.

---

### Gate 5: Listing Photos — 2 Rooms Minimum (HARD REQUIREMENT)
Every wall art listing must have photos showing art in **at least 2 different room types**.
Buyers shop by room first, art style second. Two rooms doubles the buyer pool.

**Required photo sequence (use all 10 slots):**
1. Living room or bedroom hero — lifestyle composite via `tools/lifestyle_composite.py`
2. Second room type (office, bedroom, entryway — different from photo 1)
3. Close-up art detail shot (shows quality)
4. Gallery wall grouping (3 coordinated prints on one wall — 40% higher multi-purchase rate)
5. Size reference shot (art shown next to furniture with scale context)
6. All formats flat lay (what's in the ZIP — multiple size files fanned out)
7. Second lifestyle angle or color variant
8. Frame style options (black, white, natural wood)
9. What's included graphic (Canva text overlay listing the sizes)
10. Bundle/collection cross-sell

**Compositing rules:**
- Use `composite_smart()` from `tools/lifestyle_composite.py` — never place art manually
- Always pass `min_clearance=70` minimum; use `min_clearance=150` for bedroom/shelf scenes
- For landscape art files: run pixel analysis first to detect actual drawing bounds, crop tight, then composite
- Verify frame does not overlap furniture before uploading — zoom in on the furniture line

**Photo specs:** 2400×2400px square, subject centered in 70% of frame, 5% neutral padding at edges.

---

### Gate 6: Description — First Sentence Rule
The first sentence of every wall art listing description must:
1. Contain the primary keyword naturally (for Google indexing)
2. State that this is an instant/digital download

**Required preamble (use verbatim or close variant):**
> "Instant download printable wall art — digital download delivered immediately after purchase, ready to print at home or at any print shop."

This is the only text mobile buyers see before the fold.

---

### Gate 7: Pricing Tiers
| Type | Price | Notes |
|---|---|---|
| Single print | $4.99–$7.99 | Impulse tier — .99 endings outperform round numbers |
| Set of 3 matching | $12.99–$19.99 | Most purchased bundle unit |
| Gallery wall set of 5–7 | $19.99–$39.99 | Highest revenue per transaction |
| Pick Any 3 bundle | $14.97 | Highest favorites-to-views ratio |
| Complete collection | $24.99 | Algorithm anchor — generates catalog-wide signal |

Always use .99 or .49/.97 endings — never round numbers.

---

### New Listing Production Checklist (Wall Art)

Run through this in order for every new wall art product:

**Art File**
- [ ] Master file ≥ 3,000px on short edge (if not, run `tools/upscale_art.py` first)
- [ ] File exported as sRGB color space
- [ ] Run `tools/generate_print_sizes.py` → ZIP created in `print_zips/`
- [ ] ZIP verified under 20MB

**Listing Content**
- [ ] Title: 55–70 characters, leads with buyer search phrase, includes "printable" + "instant download"
- [ ] Title: does NOT use pipe separators (use commas)
- [ ] Description: first sentence contains primary keyword + states instant download
- [ ] Description: all required sections present (hook, what's included, specs, FAQ)
- [ ] Tags: all 13 slots used
- [ ] Tags: zero tags duplicate title phrases
- [ ] Tags: cover all 6 intent categories (style, room, medium, occasion, recipient, format)
- [ ] Price: uses .99/.97/.49 ending, matches tier table above

**Photos**
- [ ] **CARDINAL CHECK: every photo contains the REAL product — not an AI-generated stand-in**
- [ ] Photo 1: hero lifestyle room — art composited with `composite_smart()` (real art file in real room)
- [ ] Photo 2: second different room type
- [ ] Photo 3: close-up art detail
- [ ] Photo 4: gallery wall grouping (3 prints)
- [ ] Photo 5: size reference with furniture scale
- [ ] Photo 6: ZIP contents flat lay
- [ ] Frame does not overlap any furniture (zoom check before upload)
- [ ] All photos 2400×2400px

**Publishing**
- [ ] Upload ZIP to listing via `EtsyAPIClient.upload_listing_file()`
- [ ] Run `tools/audit_fix_wall_art_tags.py` to verify tags pass audit
- [ ] Check listing live on mobile — does the thumbnail stop the scroll?

---

## Image Generation Notes (for gpt-image-1 / DALL-E)

Generate all 10 images at **2400×2400px square**. Never put text overlays in the AI-generated image — add all text callouts separately in Canva after generation. No hands or people visible (AI renders these unnaturally). Use the product's color theme as the accent color for props and backgrounds.

### Wall Art Lifestyle Photo Rules (research-validated, May 2026)

These rules apply to every wall art listing photo generated. Violating them costs CTR and conversion.

**THE 4-LAYER ROOM FORMULA (every lifestyle shot must have all 4):**
1. **Backdrop (60% of frame):** Warm cream, sage green, terracotta, or warm white wall. Textured plaster preferred. Upper 65%+ is ALWAYS completely plain wall — NOTHING in upper portion.
2. **The Art (25–35% visual weight):** Real product, properly framed, thick white mat (2.5–3 inch). Center of frame, upper-middle position.
3. **Anchor Furniture (lower 25–30%):** ONE piece — sofa, console, bed frame, shelf. Natural materials: wood, rattan, linen, marble.
4. **Accent Props (3 items max):** Curated, intentional. Each belongs to the same "world" as the art. One large + one medium + one small.

**TOP 5 ROOMS BY CONVERSION (in order):**
1. Living room (sofa + art = broadest buyer pool)
2. Bedroom (highest emotional purchase driver)
3. Home office (fast growing, underserved by competitors)
4. Dining room / kitchen (niche but decisive buyers)
5. Entryway / hallway (high-intent "new home" buyers)

**ALWAYS show art in 2 different room types per listing.** Buyers shop by room first, art style second. Two rooms = double the buyer pool.

**2026 INTERIOR DESIGN AESTHETICS TO USE IN BACKGROUNDS:**
- **Warm cream/creme neutrals** — warm beige walls, natural oak, rattan, cream linen (default for most scenes)
- **Verdant/biophilic** — plants everywhere, terracotta pots, earthy greens (include plant in 60%+ of shots)
- **Curated maximalism** — layered textures, thick frames, vintage-feeling props, "collected over time" feel
- **Japandi** — low furniture, white linen, ceramic, stone, zen calm (bedroom scenes)
- **English cottage / dark moody** — deep-toned walls (navy, forest green), books, candles, dried flowers

**LIGHTING MOODS:**
- Daytime living room / bedroom: "soft diffused window light from left, warm white balance, gentle shadow to right, morning light"
- Evening bedroom / study: "warm amber bedside lamp glow, soft ceiling ambient light, intimate evening atmosphere"
- Office / kitchen / minimal: "bright clean natural daylight, even illumination, no harsh shadows, cool-neutral"

**MOBILE THUMBNAIL RULES (46% of purchases are on mobile):**
- High contrast between frame edge and wall — never light frame on light wall
- Subject centered in top-center 60% of frame
- 5% neutral-tone edge padding on every shot
- No text in main lifestyle images — invisible at 200px thumbnail size
- Warm-toned backgrounds outperform cool-gray in the mobile search grid

**PROP PAIRINGS BY ART SUBJECT:**
- Watercolor floral → ceramic vase + dried pampas + folded linen
- Abstract landscape → terracotta vase + trailing pothos + stone bowl
- Typography quote → ceramic mug + small succulent + gold pen holder
- Ocean/coastal → sea glass dish + driftwood piece + dried lavender
- Food/kitchen art → ceramic pitcher + fresh herbs in pot + linen cloth
- Dark/moody → crystal + taper candle in brass + dark hardcover book

Full research reference: `data/knowledge_base/lifestyle_photo_mastery.md`

**Color theme reference for prompts:**
- DP1026: lavender purple (#8666AA), soft lavender accents, cream/white surfaces
- DP1027: cotton candy pink (#DE97C6), sky blue accents, light neutral surfaces
- DP1028: midnight royal blue (#1B2568), ice-blue accents, dark navy or cream surfaces
- DP1029: warm coral (#FD6C49), peach-gold accents, warm cream/sand surfaces

---

### Photo 1 — Hero Lifestyle Shot (THUMBNAIL — most critical)

```
Professional Etsy product photography, square 2400×2400px. Silver iPad Pro 12.9-inch
angled at 30 degrees on a light cream linen-textured desk. Screen displays [PLANNER_SPREAD
— e.g., "a lavender kawaii monthly calendar page with illustrated header and fillable day
cells"]. Apple Pencil rests diagonally at the lower-right corner of the iPad. Props
clustered in the upper-right: steaming ceramic latte in a white mug, a small eucalyptus
sprig in a bud vase, two [ACCENT_COLOR] washi tape rolls, a few dried flowers. Lighting:
soft diffused window light from the left, warm white balance, gentle shadow to the right.
Photography style: bright airy editorial Etsy lifestyle. Sharp focus on iPad screen,
slight depth of field on background props. iPad fills center 65% of frame. No text
overlays. No hands. Mood: cozy, aspirational, feminine.
```

---

### Photo 2 — What's Included Flat Lay

```
Clean overhead product flat lay, square 2400×2400px. Light cream background with subtle
linen texture. LEFT SIDE: silver iPad Pro showing the planner PDF open to the cover page.
RIGHT SIDE: 3 kawaii PNG sticker sheets fanned slightly, stickers clearly visible — one
sheet showing planner stickers, one cozy lifestyle stickers, one seasonal stickers. Small
accent props between the items: a thin [ACCENT_COLOR] ribbon bow, an uncapped fine-tip
pen, a tiny dried flower sprig. Lighting: soft even overhead diffused light, gentle
shadow for depth, no harsh highlights. Photography style: clean product catalog. No text
overlays — text will be added in Canva. Square format. Neutral-bright, professional.
```

---

### Photo 3 — Monthly Spread In-App Preview

```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro 12.9-inch at a 15-degree
angle on a cream desk surface, held slightly above the desk. Screen shows a full monthly
calendar spread in [PRODUCT_COLOR_THEME] — kawaii illustrated header with month name,
5-row grid calendar with fillable day cells, small icon decorations in corners, section
divider line at bottom. Apple Pencil cap visible at left edge of frame. Minimal props:
a washi tape strip at top-right, a corner of a notebook. Lighting: bright clean natural
light from the left. Photography style: app screenshot lifestyle mockup. Sharp focus on
screen content. iPad fills 70% of frame. No text overlays. Square format.
```

---

### Photo 4 — Weekly Spread In-App Preview

```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro 12.9-inch lying flat on a
light wood desk surface at a 20-degree camera angle. Screen shows a horizontal weekly
spread: 7 column headers (Mon–Sun), time-block rows for morning/afternoon/evening, a
notes column on the right, [PRODUCT_COLOR_THEME] color accents, kawaii decorative
elements in top corners, all text fields blank and fillable. Fine-tip pen resting beside
the iPad. Small to-do note pad at upper-left. Lighting: bright even natural daylight from
left window. Photography style: productivity workspace aesthetic. Sharp focus on screen.
No text overlays. Square format.
```

---

### Photo 5 — Sticker Library Showcase

```
Overhead flat lay, square 2400×2400px. Clean cream background. THREE large kawaii PNG
sticker sheets arranged in a loose fan/overlap formation: Sheet 1 (planner and
stationery stickers — miniature notebooks, pens, stars, washi tape, coffee cups), Sheet
2 (cozy lifestyle stickers — candles, mugs, open books, fairy lights, sleeping cat),
Sheet 3 (seasonal stickers — cherry blossoms, pumpkins, snowflakes, valentines). The
PNG sheets show transparent areas clearly against the cream background. Five or six
individual stickers scattered loose around the sheets as if recently peeled. Lighting:
even bright overhead light, sharp focus, no shadows on the stickers. Photography style:
illustration showcase, crisp and vibrant. All individual sticker designs clearly
legible. No text overlays. Square format.
```

---

### Photo 6 — GoodNotes Sticker Import How-To

```
Clean instructional graphic mockup, square 2400×2400px. Very light cream or white
background. THREE sequential iPad screen mockups arranged left to right, each in a
subtle drop shadow frame: LEFT — GoodNotes 6 app open showing the Elements side panel
with the Stickers tab highlighted and a visible + button; CENTER — iOS file picker
screen with 3 PNG files selected and a checkmark on each; RIGHT — GoodNotes planner
page with a kawaii sticker being dragged onto the weekly spread page. Above each iPad
frame: a filled circle numbered 1, 2, 3 in [PRODUCT_COLOR] with white number text.
Layout is clean, infographic-style. No other text. White background, minimal design.
Square format.
```

---

### Photo 7 — App Compatibility Infographic

```
Clean flat graphic, square 2400×2400px. Soft cream background with very subtle grid
texture. CENTER: a large planner PDF file icon in [PRODUCT_COLOR_THEME] palette
(document shape with PDF badge). Around it in a circular arrangement: five rounded
square app icons representing GoodNotes (green), Notability (red/orange),
PDF Expert (blue), Xodo (teal), Adobe Acrobat (dark red). Each icon connected to the
center PDF icon with a thin [ACCENT_COLOR] dashed line. Each icon has a small white
checkmark badge at bottom-right. Style: flat illustration, kawaii-friendly pastel
colors, clean geometric. No text labels (added in Canva post). Professional digital
product aesthetic. Square format.
```

---

### Photo 8 — Kawaii Cover Close-Up Beauty Shot

```
Product beauty shot, square 2400×2400px. Silver iPad Pro screen filling 78% of the
frame, photographed straight-on with slight downward angle. Screen shows the full
kawaii illustrated planner cover in [PRODUCT_COLOR_THEME] — the illustrated kawaii
character or motif, elegant title typography, the year 2026, and decorative border
elements all crisp and sharp. Background behind the iPad: extreme shallow depth of
field, blurred [ACCENT_COLOR] fabric or silk surface creating a soft color wash.
Lighting: even bright studio light with anti-glare on screen. Photography style:
beauty/detail shot, high fashion editorial applied to stationery. This image showcases
illustration quality and cover art. No text overlays. Square format.
```

---

### Photo 9 — Habit Tracker Page

```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro 12.9-inch at a relaxed
30-degree angle on a warm wooden desk. Screen shows the Habit Tracker page in
[PRODUCT_COLOR_THEME]: a 31-row grid with habit name columns, approximately 12 rows
filled with checkmarks or colored dots to demonstrate interactivity, kawaii star/moon
icon decorations in header, title "Habit Tracker" in kawaii font. Apple Pencil resting
beside the iPad. Props: a blank sticky note at upper-right, a [ACCENT_COLOR] highlighter
pen uncapped at lower-left. Lighting: warm desk lamp light from upper-right, cozy amber
tone. Photography style: cozy productivity, evening planning session. No text overlays.
Square format.
```

---

### Photo 10 — Specialty Feature Page (product-specific)

**DP1026 — Budget Tracker:**
```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro on a clean cream desk,
15-degree angle. Screen shows the Budget Tracker page in lavender theme: income row,
expense category rows (housing, food, transport, etc.), total and savings fields, some
cells filled with example dollar amounts. Props: a small calculator, a coin purse,
a coffee mug. Lighting: bright clean natural light. Photography style: personal finance
workspace. No text overlays. Square format.
```

**DP1027 — Study Schedule / Weekly Class Tracker:**
```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro on a light desk,
15-degree angle. Screen shows a weekly class and study schedule in cotton candy pink
theme: class time blocks color-coded by subject, assignment due dates in cells, study
session planning blocks. Props: a pencil case partially open, a highlighter set,
a corner of a textbook spine. Lighting: bright daylight. Photography style: student
study desk. No text overlays. Square format.
```

**DP1028 — Monthly Budget Breakdown:**
```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro on a dark navy or cream
desk, 15-degree angle. Screen shows the Monthly Budget page in Midnight Blue: income
section at top, expense categories listed below, savings row, balance calculation at
bottom, some cells filled with example values. Props: a small calculator, a minimalist
coin purse, a dark blue pen. Lighting: clean cool-toned daylight. Photography style:
professional finance planning. No text overlays. Square format.
```

**DP1029 — Weekly Fitness Log:**
```
Product lifestyle mockup, square 2400×2400px. Silver iPad Pro on a warm cream or light
wood surface, 15-degree angle. Screen shows the Weekly Fitness + Meal Planner spread in
coral peach: workout type and duration fields filled with example entries, water intake
tracker bubbles, mood checkboxes, meal plan grid with example meals. Props: a protein
shaker bottle, a pair of earbuds in their case, a small succulent. Lighting: bright
warm energetic morning light. Photography style: active wellness lifestyle. No text
overlays. Square format.
```

---

## Sticker Pack Design Standards
*Research-backed system for producing sticker packs that outperform top Etsy sellers. Top shops offer 3,500+ stickers; our minimum target is 200+ stickers per planner bundle with 5 themed sheets. Every sticker pack must be functional first, beautiful second.*

---

### Functional Sticker Types — Required in Every Pack

All packs must include stickers from each of these functional categories so buyers can actually use them in their planning workflow:

| Category | Examples | Purpose |
|---|---|---|
| **Headers & Banners** | "This Week", "Monthly Goals", "Habit Tracker", "Don't Forget", wide horizontal bars | Section labels that match planner sections |
| **Checklists & To-Do Boxes** | Open checkbox sets (3, 5, 7 boxes), checklist strips, priority flags | Planning workflow — the #1 most-requested functional sticker |
| **Action Flags & Arrows** | "→ Due", "Star" priority star, attention flag, action arrow, "!" urgent | Drawing attention to tasks and deadlines |
| **Time & Appointment Icons** | Clock, alarm, calendar pin, appointment dot, "AM/PM" tag | Time-blocking and scheduling |
| **Mood Trackers** | 5-face emotion row (😢→😊), weather moods (rainy/cloudy/partly/sunny), moon phases | Daily emotional check-in, mindfulness journaling |
| **Habit & Water Trackers** | 8-cup water grid widget, 7-circle weekly streak bubbles, 30-day dot grid habit tracker | Tracking recurring behaviors |
| **Date Dots & Numbers** | Filled circle numbers 1–31, date badges, month name tags | Undated planner customization |
| **Labels & Category Dots** | Color-coded circle labels in 8 colors, subject tags (Math, English, etc.), bill labels | Categorization and color coding |
| **Monthly Tab Dividers** | Jan–Dec abbreviated tab stickers, Q1–Q4 quarter tabs | Navigating undated layouts |
| **Widget Stickers** | Sleep tracker widget (8 bubbles), steps counter widget, mood + energy combo widget, weekly summary widget | Drop-in trackers that work inside any open space on a page |
| **Sticky Notes & Page Flags** | Mini sticky note (lined), page flag (5 colors), bookmark tab | Temporary annotations and page marking |
| **Motivational Banners** | "You've Got This", "Progress Not Perfection", "Rest is Productive" — in matching font/palette | Inspiration without being generic |
| **Seasonal Markers** | Holiday icons (12 major holidays), season change banners, birthday cake, anniversary heart | Calendar customization |
| **Washi Tape Strips** | 3 pattern strips (floral, geometric, solid), 2 lengths (half-page, full-page) | Decorative borders and section dividers |

---

### Sticker Sheet Architecture — 5-Sheet System

**Minimum 5 sheets per product (200+ total stickers). Each sheet is 3000×3000px PNG, 300 DPI, transparent background.**

| Sheet | Name | Sticker Count | Contents |
|---|---|---|---|
| **Sheet 1** | Functional Planning | 50+ | Headers, checklists, flags, action arrows, date dots, labels — pure workflow utility |
| **Sheet 2** | Widget Trackers | 40+ | Mood tracker widget, water intake widget, sleep tracker, habit tracker, weekly summary — drop-in mini-trackers |
| **Sheet 3** | Planner & Stationery | 40+ | Miniature notebooks, pens, washi tape, paper clips, sticky notes, scissors, ruler — classic kawaii planner icons |
| **Sheet 4** | Cozy Lifestyle | 40+ | Mugs, candles, books, plants, fairy lights, sleeping cat, cozy blanket, rain window — lifestyle/mood imagery |
| **Sheet 5** | Seasonal & Holiday | 40+ | Cherry blossoms (spring), sunflowers (summer), pumpkins (fall), snowflakes (winter), 12 major holiday icons |

**GoodNotes delivery format:**
- Package ALL 5 sheets as a GoodNotes sticker book (single `.goodnotes` file) — this is the most-requested format
- Also include 5 individual PNG sheet files for Notability / PDF Expert / Acrobat users
- Also include a folder of 200+ individual pre-cropped PNG stickers for advanced users who want selective import
- ZIP structure: `[ProductID]_sticker_pack.zip` → `goodnotes_sticker_book/`, `png_sheets/`, `individual_stickers/`

---

### Per-Product Sticker Customization

Each product gets themed sticker content layered on top of the 5-sheet base system. The theme color palette must match the planner's color scheme exactly.

**DP1026 — Ultimate Life Planner (Lavender Dreams `#8666AA`):**
- Sheet 1 extra: "Self-Care Sunday", "New Month New Goals", "Gratitude" banners; moon phase icons
- Sheet 2 extra: Monthly goals tracker widget, gratitude log widget
- Bonus individual stickers: 20 affirmation banners ("I am enough", "Choose joy", etc.) in lavender palette
- Prop stickers: lavender sprigs, amethyst crystal, butterfly, dream catcher

**DP1027 — Student Planner (Cotton Candy `#DE97C6`):**
- Sheet 1 extra: Subject tab stickers (Math, Science, English, History, PE, Art, free), "Due Date ⚠️", "Test Day", "Study Group" flags
- Sheet 2 extra: Study session timer widget, grade tracker widget, exam countdown widget
- Bonus individual stickers: 20 study motivational banners ("Focus Mode ON", "Nailed It!", "Coffee + Study")
- Prop stickers: graduation cap, pencil case, backpack, apple for teacher, calculator, diploma scroll

**DP1028 — Budget Planner (Midnight Blue `#1B2568`):**
- Sheet 1 extra: "Payday!", "Bill Due ⚡", "Savings Goal", "Debt Payoff", "No Spend Day" labels; budget category icons (groceries, rent, dining, entertainment)
- Sheet 2 extra: Net worth snapshot widget, debt payoff thermometer widget, savings jar fill widget
- Bonus individual stickers: 15 financial win banners ("Debt Free!", "Goal Reached!", "Emergency Fund Full")
- Prop stickers: gold coin stack, credit card scissors (debt-free symbol), piggy bank, bar chart, dollar sign wreath

**DP1029 — Fitness Planner (Coral Peach `#FD6C49`):**
- Sheet 1 extra: "Workout Done ✓", "Rest Day", "Meal Prep Sunday", "Hydration Goal", "PR!" (personal record) labels; exercise icons (run, lift, yoga, swim, bike, stretch)
- Sheet 2 extra: Weekly workout summary widget, macro tracking widget, energy level scale widget
- Bonus individual stickers: 15 fitness win banners ("New PR!", "Week Streak!", "Gym Check ✓")
- Prop stickers: dumbbell, yoga mat, water bottle, salad bowl, running shoe, heart rate monitor

---

### Kawaii Illustration Standards

Every sticker must follow these visual rules for brand consistency and professional quality:

**Chibi/Kawaii Character Proportions:**
- Head-to-body ratio: 1.5:1 to 2:1 (head is always larger than body)
- Eyes: oversized, occupy 40–50% of face height, single catch-light dot in each eye
- Mouth: small dot or tiny curved smile — never open/teeth unless celebrating
- Cheeks: small blush circles in a slightly pinker shade of skin tone
- Arms/legs: stubby, rounded, no fingers visible on items under 200px
- Expressions: calm default, happy with star eyes, excited with open mouth, sleepy with half-moon eyes

**Color Rules:**
- Every sticker pack uses exactly 5 colors from the planner's palette (primary, accent, mid-tone, neutral, text)
- Add one "pop" accent only for functional flags/alerts (warm red `#E84040` or amber `#FFB347`) — never change the base palette
- Shadows: single direction (bottom-right), 15% opacity black, offset 3–4px — never harsh
- Outlines: consistent 2px line weight, same near-black (`#1A1A1A`) — never pure black

**Sizing Consistency:**
- Decorative icon stickers: 200×200px (at 300 DPI = ~0.67 inch)
- Header/banner stickers: 800×200px (full-width label)
- Widget stickers: 400×400px to 600×600px
- Washi tape strips: 2400×120px (full-width half-page), 2400×80px (full-width narrow)
- All sizes refer to final export dimensions at 300 DPI

**File Export Protocol:**
- Individual stickers: PNG, transparent background, exact crop (1–5px transparent padding)
- Sticker sheets: PNG 3000×3000px, transparent background, 300 DPI
- GoodNotes sticker book: bundle all sheets as `.goodnotes` package
- Naming convention: `[ProductID]_S[sheet#]_[category]_sheet.png` and `[ProductID]_[sticker_name].png`

---

### GoodNotes Sticker Book Setup

GoodNotes Elements is the premium import format — it creates a persistent sticker library panel accessible from any document.

**Creating a GoodNotes Sticker Book:**
1. Each sheet file named `[Pack Name] — Sheet [N].png` (the name becomes the library tab label)
2. Import sequence for buyers: GoodNotes → Elements → Stickers → + → select all 5 PNG files
3. Stickers appear as a scrollable grid in the sticker library — tap any to place on current page
4. Stickers are reusable unlimited times from the library

**Creating a `.goodnotes` package (advanced delivery format):**
- Use GoodNotes' "Export as GoodNotes" feature on a sticker-book-style document
- Pre-organized pages: one page per sticker sheet category
- Buyers open once → stickers auto-populate Elements library
- This format is referenced and requested by 35%+ of Etsy digital sticker buyers

**Buyer instructions (include in product description and listing FAQ):**
1. Download and unzip the sticker pack
2. Open GoodNotes 6 → tap the Elements button (diamond icon, bottom toolbar)
3. Tap the Stickers tab → tap "+" → select all 5 PNG sheet files
4. Done — all stickers appear in your library and can be dragged onto any page, unlimited times

---

### Sticker Pack Pricing & Bundling Strategy

**Standalone sticker pack listings (separate from planner):**
- Individual pack (1 theme, 5 sheets, 200+ stickers): $4.99–$6.99
- Bundle (4 packs / all 4 planner themes): $12.99–$14.99 (implies 55–65% discount)
- Mega bundle (all themes + bonus seasonal pack): $17.99–$19.99
- **Research finding**: A $8 bundle of 10 sticker sheets dramatically outperforms ten $1 individual sticker listings in both conversion and revenue per visitor

**Bundling as planner bonus (included with planner purchase):**
- Mention sticker pack prominently in title: "Fillable PDF + Sticker Pack"
- List sticker count in description ("200+ kawaii stickers, 5 sheets")
- Show sticker sheet photo as Photo 5 in every listing
- Buyers scan "what's included" first — sticker count is a conversion booster

**Upsell cross-listing strategy:**
- Each planner listing should reference: "Also available: the matching standalone sticker pack — search OnBrandCraftz"
- Create one standalone sticker pack listing per theme (4 listings) + one bundle listing
- Use "Frequently Bought Together" positioning in description FAQ

---

### Sticker Pack SEO — Tags & Title Formula

**Title structure for standalone sticker pack listings:**
`[Theme] Kawaii Planner Stickers | GoodNotes Sticker Book | Planner Sticker Pack | Instant Download | [Product Type]`

**Tags for all sticker pack listings (13 required):**
`goodnotes stickers`, `planner sticker pack`, `kawaii stickers`, `digital stickers`, `goodnotes elements`, `notability stickers`, `ipad stickers`, `planner stickers`, `kawaii sticker book`, `digital planner kit`, `printable stickers`, `instant download`, `functional stickers`

**Per-theme additional tag swaps (swap 2–3 generic tags):**
- DP1026 (Lavender): swap in `lavender planner kit`, `life planner stickers`, `wellness stickers`
- DP1027 (Cotton Candy): swap in `student stickers`, `school planner kit`, `study stickers`
- DP1028 (Midnight Blue): swap in `budget planner kit`, `finance stickers`, `money planner`
- DP1029 (Coral Peach): swap in `fitness stickers`, `wellness planner kit`, `habit tracker kit`

---

### Sticker Pack Photo Requirements (10 slots)

Apply the same 2400×2400px square format and composition rules as planner photos. Each photo sells one benefit of the sticker pack.

| Slot | Purpose | Content |
|---|---|---|
| 1 | Hero flat lay | All 5 sticker sheets fanned on cream background with a few loose stickers scattered — lifestyle props in product color (washi tape, pen, dried flower) |
| 2 | GoodNotes library preview | iPad screenshot showing all 5 sheets loaded in GoodNotes Elements panel with sticker grid visible |
| 3 | In-use mockup | iPad with a planner page open, 5–8 stickers placed on it — shows the "after" result of using the pack |
| 4 | Sheet 1 close-up (Functional) | Flat overhead of Sheet 1 showing headers, checklists, flags — magnified inset showing 5–6 individual stickers clearly |
| 5 | Sheet 2 close-up (Widgets) | Flat overhead of Sheet 2 showing widget stickers — call out specific popular widgets (mood tracker, water tracker) |
| 6 | Sheet 3+4 lifestyle (Kawaii icons) | Two sheets overlapping, kawaii stationery and cozy lifestyle stickers clearly visible |
| 7 | Sheet 5 seasonal | All seasonal sticker sheet, individual stickers labeled by season with small Canva text callouts |
| 8 | GoodNotes import how-to | 3-step infographic (same 3-panel format as planner how-to guide photo) |
| 9 | Sample planner page styled | Before/after split: blank weekly page left, same page with 10 stickers placed right — shows transformation |
| 10 | What's included summary | Flat lay with product breakdown: "5 PNG Sheets", "200+ Stickers", "GoodNotes Ready", "Instant Download" text callouts added in Canva |

---

### Competitive Benchmark — What Top Sellers Offer

Use this table to verify every sticker pack release meets or exceeds the market standard:

| Feature | Our Current | Top Etsy Sellers | Our Target |
|---|---|---|---|
| Total stickers per pack | ~60 (3 sheets) | 200–3,500+ | **200+ (5 sheets)** |
| GoodNotes sticker book format | No | Yes (top sellers) | **Yes — .goodnotes + PNG** |
| Individual pre-cropped PNGs | No | Yes (premium sellers) | **Yes — 200+ individual files** |
| Functional sticker types | Decorative only | 14 functional types | **All 14 types covered** |
| Widget stickers | No | Yes (top 10% sellers) | **Yes — Sheet 2 dedicated** |
| Per-product theme customization | Partial | Fully themed | **Full theme per product** |
| Standalone sticker pack listing | No | Yes | **4 listings + 1 bundle** |
| Seasonal sticker updates | No | Annual or quarterly | **Annual seasonal refresh** |

---

### Sticker Pack QC Checklist

Before publishing any sticker pack:

- [ ] All 5 PNG sheets are 3000×3000px at 300 DPI
- [ ] All sheets have transparent backgrounds (no white fill)
- [ ] Each sheet contains 40+ stickers with consistent art style
- [ ] All 14 functional sticker categories covered across the 5 sheets
- [ ] Widget stickers on Sheet 2 match planner color palette exactly
- [ ] Individual pre-cropped PNGs exported for all 200+ stickers
- [ ] GoodNotes sticker book (`.goodnotes`) file tested and opens correctly
- [ ] Sticker naming convention followed: `[ProductID]_[name].png`
- [ ] ZIP file structure: `goodnotes_sticker_book/`, `png_sheets/`, `individual_stickers/`
- [ ] ZIP file size < 20MB (Etsy per-file limit) — compress PNGs with TinyPNG if needed
- [ ] Line weight consistent across all stickers in the pack (2px outline)
- [ ] Color palette matches the planner's 5-color palette exactly
- [ ] Product-specific bonus stickers present (functional labels, prop stickers, win banners)
- [ ] GoodNotes import instructions tested end-to-end on actual GoodNotes 6 app

---

## Quality Check Checklist (before listing)

### Wall Art File Quality
- [ ] Master art file ≥ 3,000px on short edge (if not, run `tools/upscale_art.py`)
- [ ] File is sRGB color space (not AdobeRGB or CMYK)
- [ ] Multi-size ZIP created via `tools/generate_print_sizes.py`
- [ ] ZIP contains 2:3, 4:5, A-series, and square subfolders + README.txt
- [ ] ZIP is under 20MB (Etsy hard limit)
- [ ] ZIP uploaded to listing via `EtsyAPIClient.upload_listing_file()`
- [ ] Files named descriptively: `DP1030_8x10_300dpi.jpg` (not IMG_4456.jpg)

### Wall Art Listing Quality
- [ ] Title is 55–70 characters (hard reject above 70 — mobile ranking penalty)
- [ ] Title leads with buyer search phrase in first 20–30 characters
- [ ] Title uses comma separators (not pipes)
- [ ] Title includes "printable" AND "instant download"
- [ ] All 13 tag slots used
- [ ] No tag duplicates a phrase from the title
- [ ] Tags cover all 6 intent categories: style, room, medium, occasion, recipient, format
- [ ] First description sentence contains primary keyword + states instant/digital download
- [ ] Price uses .99/.97/.49 ending
- [ ] Minimum 2 lifestyle room photos (different rooms)
- [ ] Gallery wall grouping photo included
- [ ] All frames verified above furniture line — no overlap
- [ ] Listing checked on mobile: thumbnail readable and scroll-stopping

### PDF / File Quality
- [ ] PDF opens in GoodNotes without errors
- [ ] PDF opens in Notability without errors
- [ ] PDF opens in Adobe Acrobat Reader (desktop) without errors
- [ ] All fillable fields work (tap to type in GoodNotes)
- [ ] Hyperlinked side tabs navigate correctly to the right section
- [ ] "BACK TO HOME" footer link works on every page
- [ ] Dashboard / Home page (page 2) links to all sections correctly
- [ ] Welcome / Setup page is page 1 with correct contact info
- [ ] Sticker library pages display correctly (minimum 3 pages)
- [ ] Sticker PNG sheets have transparent backgrounds (not white)
- [ ] Footer STICKERS button works (for Acrobat/Xodo users)
- [ ] All cross-section deep links tested (monthly → weekly, weekly → daily)
- [ ] File size: PDF < 20MB · Sticker ZIP < 20MB (Etsy per-file limit)
- [ ] PDF page count matches the product spec
- [ ] Dated version: all 2026 dates are correct (Jan 1 falls on correct weekday)
- [ ] Undated version: no year-specific dates remain
- [ ] Cover image renders correctly at full screen on iPad

### UX / Design Standards
- [ ] Tabs in consistent position on every page (never shift location)
- [ ] Minimum font size 11pt in fillable fields
- [ ] All section headers ≥ 14pt
- [ ] Every page has visible fillable field boundaries
- [ ] Color coding consistent across all sections
- [ ] Weekend columns visually distinct from weekdays (lighter shade)

### Content Completeness
- [ ] Welcome/Setup page included (page 1)
- [ ] Dashboard/Home page included (page 2) with all section links
- [ ] Planner index page included (page 3)
- [ ] Product-specific specialty pages present (budget, fitness log, study schedule, etc.)
- [ ] All 5 sticker sheets present in ZIP (functional headers, mood trackers, planner, cozy, seasonal)

### Listing Materials
- [ ] **CARDINAL CHECK: every photo shows the REAL product — no AI-generated product stand-ins**
- [ ] All 10 listing photos generated at 2400×2400px
- [ ] Hero photo (Photo 1) reviewed — does it stop the scroll?
- [ ] Text callouts added in Canva for Photos 2, 6, 7 (not baked into AI image)
- [ ] Tags: all 13 used, each ≤ 20 chars, no special characters
- [ ] Title: primary keyword in first 40 chars, total ≤ 70 chars (2026 algorithm: >70 chars = mobile ranking penalty)
- [ ] Title mentions: year (2026), app (GoodNotes/Notability), "Instant Download"
- [ ] Description: primary keyword in sentence 1 or 2
- [ ] Description: all 9 required sections present in order
- [ ] "2026 + Undated Version Included" noted in title and description
- [ ] Price matches pricing strategy table

---

## Business Structure & Tax — Research-Backed Rules (2026)

### Legal Structure
- **Now (under ~$50k net profit):** Sole proprietor + single-member LLC. LLC = same Schedule C filing, zero extra tax complexity, but gives liability protection for 3D-printed physical goods.
- **S-Corp election threshold:** $50,000–$80,000+ in *consistent annual net profit* (not gross revenue). Filing: Form 2553 within 75 days of desired effective date.
- **S-Corp math at $100k net:** SE tax as sole prop ≈ $14,130 → S-Corp with $50k salary ≈ $7,650 payroll taxes → ~$6,480 gross savings → net savings after compliance ≈ $2,500–$4,500/yr.
- **3D printing adjustment:** COGS from filament/materials reduces net profit, so gross revenue threshold to hit $50k net is higher than a pure-digital seller.

### 1099-K Thresholds (One Big Beautiful Bill Act, signed July 4, 2025)
- **Federal threshold permanently restored:** $20,000 AND 200+ transactions
- All Etsy income is taxable regardless — the 1099-K is informational only
- State thresholds vary; check your state separately

### Key Deductions
| Expense | Where on Schedule C |
|---|---|
| Filament, resin, materials | COGS, Part III, Line 36 |
| Bambu P1S, AMS, upgrades | Section 179 (2026 limit: $2.56M) or 100% bonus depreciation |
| Canva Pro, Adobe, AI subscriptions (Claude, OpenAI) | Line 27a |
| Etsy fees (6.5% + 3%+$0.25) | Line 10 |
| Home studio dedicated space | Form 8829 or $5/sq ft simplified |
| Quality print samples photographed | Line 22 (advertising) — NOT COGS |
| Vehicle mileage (post office runs) | $0.725/mile (2026 rate) |

### Hobby vs. Business (OBBBA Made This Permanent)
Hobby sellers now pay tax on **gross revenue with zero deductions**. Protect business status: separate bank account, maintain bookkeeping, document pricing adjustments based on sales data, show profit in 3 of last 5 years.

---

## SKU Naming Convention & Version Control

All product files must follow this naming pattern:
```
[ProductLine][ProductID]_[ThemeName]_v[N].[ext]

Examples:
DP1026_LavenderDreams_v2.pdf          ← dated planner, version 2
DP1026U_LavenderDreams_v2.pdf         ← undated version
DP1026_LavenderDreams_CherryBlossom.pdf  ← cover variant
DP1026_S01_FunctionalHeaders.png      ← sticker sheet 1
BOHO-SET_DP1000_v1.jpg                ← wall art product file
```

Rules:
- Increment `_v#` on every file re-uploaded to buyers
- Keep `_archive/` subfolder — never overwrite old versions
- Maintain `product_catalog.json` as source of truth (product_id, etsy_listing_id, price, file_paths, status, version, last_updated)
- Automation scripts read from catalog — never hardcode listing IDs or file paths

---

## Automation Stack — What to Automate vs. Keep Manual

### Automate
| Task | Tool |
|---|---|
| AI disclosure on new listings | `tools/add_ai_disclosure.py` |
| Image generation for listings | Python tools (existing) |
| Listing creation from templates | Etsy API scripts (existing) |
| **Upscale undersized art files** | `tools/upscale_art.py` — run before creating any listing from AI-generated art |
| **Multi-size print ZIP creation** | `tools/generate_print_sizes.py` — run after upscaling, before uploading to Etsy |
| **Tags audit + fix** | `tools/audit_fix_wall_art_tags.py` — run after any batch of new listings |
| Post-purchase buyer message | Etsy native auto-messages (set in dashboard) |
| Shipping label generation | Pirate Ship (free, 15–30% USPS savings) |
| Financial tracking / COGS per print | Craftybase |
| Social post scheduling | Buffer or Tailwind |
| Shop health snapshots | `tools/shop_health_check.py` |
| **Backup digital_products/ after producing a new product's files** | `tools/backup_digital_products.py` — run as soon as a new product's source art/PDF/ZIP is generated, since `data/digital_products/` is gitignored and has no other durable backup. Hand the output ZIP to Scott (via chat) to save in his own cloud storage. |
| **Log infrastructure/dashboard incidents for the CEO Agent (Fucking Frank)** | Append a short dated entry (symptom, root cause, fix) to `data/knowledge_base/ops_runbook.md` any time Claude Code diagnoses or fixes a problem with the live site, API, deploy, or credentials — Frank loads this file fresh on every chat/diagnostic request (`_ops_runbook_block()` in `tools/api_server/main.py`), so Scott can ask Frank directly "why was X broken?" and get a grounded answer instead of a guess. Keep entries short — this is a log, not a report. |
| **Archive anything before deleting it (recycle bin)** | BEFORE removing any code block or file, archive it first via `tools/trash.py` — `from tools.trash import archive_snippet, archive_file` then `archive_snippet(source_path, exact_removed_text, reason)` for code or `archive_file(path, reason)` for whole files. Everything lands in the committed vault `data/trash/` (ledger `DELETED.md` + byte-exact copies in `files/`), kept **30 days** then auto-pruned, so an accidental or regressive deletion can be recovered with `python tools/trash.py --restore <id>`. This is a hard rule per Scott (2026-06-23): nothing we delete should be unrecoverable. The vault must stay committed (the remote container is ephemeral — uncommitted files are lost). |

### Keep Manual (human judgment required)
- Review responses — tone matters; script = damage
- Custom order pricing and feasibility
- Pricing changes (requires market analysis)
- New product launch decisions
- Negative review responses
- Cover art quality approval before publishing

### The One Automation Most Sellers Skip
Etsy allows exactly **one** post-delivery buyer message. Set it to:
> "Hope you love your [product name]! If you have 30 seconds, a review means everything to a small shop 🙏"
Set this in Etsy Dashboard → Shop Manager → Messages → Auto-reply.

---

## Weekly & Monthly Operational Cadence

### Weekly (Friday, 30 min)
- Check Etsy Search Visibility Dashboard — fix any flagged listings immediately
- Review 7-day conversion rate per listing (Etsy Analytics → Listings)
- Respond to any outstanding messages or reviews
- Check 3D print queue — what sold, what needs restocking

### Monthly (1st of month, 2 hours)
- Run `python tools/shop_health_check.py` — full snapshot
- Compare conversion rates, views, revenue vs. prior month
- Identify listings with high views but low conversion (photo or price problem)
- Update seasonal keywords in top 10 listings (update 6 weeks before peak season)
- Export orders for COGS/Craftybase reconciliation

### Quarterly
- Estimated tax payment (Jan 15, Apr 15, Jun 15, Sep 15)
- New product launch or existing product upgrade decision
- Review competitor pricing in top 3 niches
- S-Corp salary draw if applicable

### Seasonal Keyword Calendar (6 weeks before each peak)
Corrected 2026-07-09 — this table previously listed only 4 of the 6 seasons
`tools/seasonal_keywords.py` actually tracks, and its "Update By" dates were
rough approximations that didn't match the script's real computed/hardcoded
deadlines (e.g. Back to School's real deadline is July 4, not "mid-July").
The dates below are the script's actual values; `_SEASONAL_TRIGGER_DATES` in
`tools/api_server/main.py` fires a few days to two weeks before each one.

| Peak Season | Update By | Keywords to Add |
|---|---|---|
| Back to school | July 4 | student planner 2026, school planner, academic planner |
| Holiday gifting / New Year | November 8 | new year planner, 2027 planner, gift for planner lover |
| Valentine's Day | ~January 3 (6wk before Feb 14) | valentine gift digital, love journal, self care planner |
| Spring reset | ~February 6 (6wk before Mar 20) | spring planner, fresh start planner, new beginnings journal |
| Mother's Day | March 30 | mothers day gift digital, gift for mom, mom planner |
| Teacher Appreciation | March 25 | teacher appreciation gift, gift for teacher, teacher digital download |

---

## Etsy 2026 Algorithm — Confirmed Changes

### Change 1: Title Length Cap (CRITICAL — affects all listings)
- **Titles > 70 characters face mobile ranking penalty**
- Mobile = 70%+ of Etsy traffic in 2026
- Listings that shortened to <70 chars saw +34% mobile CTR and avg +4.2 position ranking boost
- **Formula:** Lead with product noun → include top 3 keywords → keep buyer-friendly language
- Example: `Kawaii Digital Planner 2026 | GoodNotes iPad | Sticker Pack` (61 chars) ✓

### Change 2: Shipping Cost Penalty
- US listings with shipping above **$6** face reduced search visibility
- Action for digital products: shipping = free, already optimal
- Action for 3D printed physical products: absorb shipping into price, offer free shipping or cap at $5.99 flat

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
| Message response rate | 95%+ within 24 hours | **Main challenge** — Etsy's API has no buyer-messaging endpoint for third-party apps (confirmed 2026-06-19, see ops_runbook.md), so this can't be automated. The only mechanisms that earn Star Seller credit are manual Quick Replies and Etsy's built-in Temporary/Weekly Auto-Reply windows — see "Customer Service — Autonomous Response System" above |
| On-time shipping | 95%+ | **Auto-pass** — instant digital delivery = 100% on time, always |
| Average rating | 4.8+ stars | Need 5+ orders in the review window |
| Minimum orders | 5 orders, $300+ total | Over the past 3 months |

Star Seller status is the path to catalog-wide ranking lift. For OnBrandCraftz, message response rate is the only real challenge — all other criteria are effectively free for digital products.

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
- **Post-purchase message** (already set): Signed Scott, no emoji, professional tone — this is correct
- **Etsy auto-message after delivery:** Set in Shop Manager → Messages → "Message to buyers" → check "Send after delivery" — one sentence: "Hope you love your planner! A quick review means everything to a small shop — Scott @ OnBrandCraftz"
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

**Example (iPad lifestyle shot):**
```
Silver iPad Pro 12.9-inch at a 30-degree angle on a cream linen-textured desk,
screen displaying a lavender kawaii monthly planner spread with fillable day cells.
Soft diffused window light from the left, warm white balance, gentle shadow to the right.
50mm lens, eye-level angle, subject fills 65% of frame.
Sharp commercial photography, slight depth of field on background.
The image contains only the iPad, an Apple Pencil resting diagonally at lower right,
and a small eucalyptus sprig in a ceramic bud vase. No hands, no text overlays,
no visible studio equipment.
```

### THE CARDINAL RULE — Every Listing Photo Must Show the REAL Product (NEVER VIOLATE)
**Every single listing photo must contain the actual product — no exceptions, no substitutes.**
- AI-generated lifestyle rooms with AI-generated stand-in products are BANNED — they show the customer something they will NOT receive
- This rule enforces the mission statement: "Best and most accurate transaction — listings show the REAL product"
- A lifestyle image that looks beautiful but does not contain the actual product is worse than no lifestyle image at all
- **Multi-product photos (flat lays, collections, gallery walls): EVERY product file must be passed as input.** Feeding one design and prompting "show 5 variations" makes the AI invent products the customer doesn't get — this is a violation (caught and fixed June 2026 on SS1001 photo_06)

### THE STANDARD LIFESTYLE METHOD — `images.edit` With the Real Product as Input (MANDATORY, ALL CATEGORIES)
**Confirmed by Scott (June 2026): this is THE method for every lifestyle photo in every product category.**
The real product file is passed to gpt-image-1's **edit endpoint** as the input image, and the prompt tells the model to render it physically in the lifestyle scene. The model handles perspective, curvature, lighting, shadows, and placement natively — no manual coordinate compositing.

**Workflow (every product type, every scene):**
1. Load the REAL product file(s): art JPG, design file, or photo of the 3D print — never a description alone
2. Call `client.images.edit(model="gpt-image-1", image=<real file(s)>, prompt=<scene>, quality="high", input_fidelity="high")`
3. Prompt structure: "This image is the flat design of [product]. Render it as a single photorealistic product photograph, [physically placed/mounted/wrapped] in [scene]. The EXACT design from this image must appear with all colors, text, and details preserved accurately."
4. For multi-product shots, pass ALL product files as a list and reference each by number in the prompt
5. **Verify the output against the source files before keeping** — zoom in and compare colors, text, and composition; regenerate on any drift
6. Upscale to 2400×2400 for the listing

**MANDATORY TOOL — `tools/listing_photo_pipeline.py` (use this, not ad-hoc scripts):**
`generate_verified_photo()` automates the entire quality loop so photos come out right the FIRST time:
1. **Palette auto-extraction** — dominant hex colors pulled from the actual design file and injected as constraints (never hand-type a palette into a prompt; a hardcoded navy palette caused color drift across an entire batch in June 2026)
2. **Text auto-extraction** — a vision model reads every text item off the design once and injects it character-for-character into the prompt
3. **Physics templates** — product surface reality is encoded per product type (`sign_flat`: face-down textured-PEI print = perfectly flat face, no raised lettering; `tumbler_wrap`, `framed_print`, `flat_paper`). Add new product types to the `PHYSICS` dict.
4. **Automated verification** — after generating, a vision model compares the render against the source file(s): text character-level, colors, elements, edge details, surface flatness
5. **Auto-retry with feedback** — failures feed the specific discrepancies back into the prompt and regenerate (max 3 attempts), then report unresolved issues

`build_flat_lay()` — for overhead/collection shots (zero perspective): pixel-perfect PIL paste of the real files over an AI background. NEVER use images.edit for multi-design flat lays — with 5 designs as input it garbles small text ("ANNIVERSARY", "FOREVER" — verified June 2026).

**Design-side rule (prevents unfixable shots):** tiny text and fine repeating edge geometry (e.g. postage-stamp perforations) cannot survive images.edit rendering — 3 attempts failed on SS1001's stamp. Designs with those features should appear in lifestyle scenes via a reliable sibling design, and be shown exactly in the pixel-perfect flat lay. For NEW designs intended for lifestyle renders, prefer bold shapes and ≥24pt-equivalent lettering.

**Reference implementations:**
- `tools/listing_photo_pipeline.py` — THE standard (self-verifying, all categories)
- `tools/generate_tumbler_mockups.py`, `tools/generate_sign_lifestyle_photos.py`, `tools/generate_sign_collection_photo.py` — earlier per-product scripts; migrate their scenes to the pipeline when next touched

**Deprecated:** the old "generate empty room → PIL paste at coordinates" workflow (`composite_smart()` + empty room templates below). It produced off-center, out-of-place products and was retired June 2026. The empty-room prompt templates below are kept only as scene-vocabulary reference for edit prompts.

### Empty Room Prompt Templates

**Sofa / Living Room (boho/cream):**
```
Photorealistic interior photography. Empty living room with a warm cream textured
plaster wall, a boucle fabric sofa with sage green and terracotta throw pillows,
natural oak hardwood floors, a rattan side table with a small terracotta ceramic pot.
Soft diffused natural window light from the left, morning atmosphere, warm white balance.
The upper 60% of the wall is completely empty and plain — no art, no shelves, no objects.
35mm lens, eye-level, wide shot. IKEA catalog lifestyle photography style.
No people, no text.
```

**Bedroom (Japandi/warm minimal):**
```
Photorealistic bedroom interior photography. Off-white linen wall, low platform bed
frame in natural light oak with cream linen bedding, a small ceramic bedside lamp
emitting warm amber glow, a trailing pothos plant on a windowsill.
Evening atmosphere, warm ambient light, shadows soft.
Upper 65% of the far wall is completely bare and empty — no art, no decor.
35mm lens, eye-level. Japandi aesthetic. No people, no text, no studio equipment visible.
```

**Home Office (clean/modern):**
```
Photorealistic home office interior photography. Warm white wall with subtle linen
texture, a light oak floating desk, a matte black adjustable lamp, a small succulent
in a white ceramic pot, minimal books stacked flat. Bright clean natural daylight
from a window on the left, cool-neutral white balance, even illumination.
Upper 60% of the back wall is completely empty and blank. 50mm lens, eye-level.
No people, no art on walls, no text.
```

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
- **Text rendering:** Put literal text in quotes or ALL CAPS. Even then, composite text in Canva — don't trust in-image text
- **Hands:** Even with "no hands visible," generation can slip. Regenerate rather than edit — editing creates worse artifacts
- **Color drift:** Re-specify hex or descriptive colors in every prompt (model doesn't remember previous calls)
- **Bedroom content filters:** Use "interior photography" language, not "photoshoot" language. Describe furniture, not atmosphere
- **Quality setting for production:** `quality="high"` for hero images; `quality="medium"` for background generation (composited anyway)
- **`input_fidelity="high"`:** Use when editing an existing image to preserve composition while changing one element

---

## Etsy API v3 — Technical Reference for Autonomous Operation

### Hard Limits (Cannot Be Coded Around)

| Limit | Value | Notes |
|---|---|---|
| **Digital files per listing** | 5 maximum | Hard platform limit — ZIP bundles to work around |
| **File size per digital file** | 20 MB per file | Hard limit — compress PDFs before upload |
| **Access token lifetime** | 1 hour (3600s) | Must refresh automatically before expiry |
| **Refresh token lifetime** | 90 days | After 90 days, Scott must re-authorize via `python tools/etsy_oauth.py` |
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
- **Refresh token expires after 90 days** — Scott must manually re-run `python tools/etsy_oauth.py` every 90 days or when a 401 is returned on the refresh endpoint

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
| Fixed (Q1 2026): Listings created via API couldn't be activated via API | Now resolved — `state=active` works on PUT |

### Suspension Triggers — What to Never Do

- **Identical descriptions across listings** — Etsy's spam detection flags templated text applied to many listings
- **High-velocity bulk listing creation** — ramp up gradually (max 10–20 new listings per day)
- **Testing transactions on a live production account** — use a separate test account for API transaction tests
- **API tools banned by Etsy** — AutoDS, ShineOn, CJDropshipping had API access revoked May 2024; never use these
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
- Using Canva templates = allowed WITH disclosure (June 2025 update banned minimally-modified templates without disclosure)
- SVG files, digital planners, wall art — all digital products are covered by the June 2025 update
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

**Template 1 — File Won't Open:**
```
Hi! Thanks for reaching out about your download. For PDF planners, I recommend:

1. Download the file to your device first (don't open directly from browser)
2. Open in GoodNotes 6, Notability, or Adobe Acrobat Reader (free)
3. For GoodNotes: File > Import → select the PDF

If using a laptop, Adobe Acrobat Reader (free download) opens everything perfectly. Let me know if you're still having trouble and I'll send step-by-step screenshots for your specific app!

— Scott @ OnBrandCraftz
```

**Template 2 — Didn't Receive Download:**
```
Hi! Etsy delivers all digital files instantly — they should be in your Purchases page right now.

To find them: Etsy app → Account → Purchases & Reviews → find this order → tap "Download Files"

On desktop: etsy.com → Account → Purchases & Reviews → Download

If you still can't find the files, let me know and I'll look into your order directly.

— Scott @ OnBrandCraftz
```

**Template 3 — Wrong File Format:**
```
Hi! All OnBrandCraftz planners are delivered as interactive fillable PDFs — they work in GoodNotes 6, Notability, PDF Expert, Xodo, and Adobe Acrobat Reader.

If you were expecting a different format (like .pages or .docx), PDF is unfortunately the only format that supports the hyperlinked navigation tabs and interactive sticker menu. 

Is there a specific app you're trying to use? I'm happy to walk you through the best setup for it!

— Scott @ OnBrandCraftz
```

**Template 4 — Refund Request:**
```
Hi! I'm sorry the product didn't meet your expectations.

Because digital files are delivered instantly and can't be "returned" once downloaded, I'm not able to issue automatic refunds — but I genuinely want you to be happy with your purchase.

Can you tell me what specifically isn't working or isn't what you expected? In most cases I can either walk you through a fix or send an alternative file that works better for you.

— Scott @ OnBrandCraftz
```

**Template 5 — Sharing / License Question:**
```
Hi! The license included with your purchase is for personal use only — one person, unlimited use of the planner for yourself.

It doesn't cover: sharing the files with others, using in a classroom/group setting, or reselling/redistributing.

If you need a multi-user license (e.g. for a class or team), please send me a custom order request and I'll put something together for you!

— Scott @ OnBrandCraftz
```

### Digital Product Refund Policy — Legal Framework

- Sellers can set a **no-refund policy** for digital products — this is fully legal and supported by Etsy
- Etsy does NOT force refunds for digital downloads as a default
- **Exception:** Etsy Purchase Protection (effective May 7, 2026) may cover buyer claims up to $250 on "qualified orders" — but this applies to physical goods fulfillment disputes, not digital download disputes
- **When Etsy overrides seller policy:** If a buyer files a case claiming the listing description was materially inaccurate, Etsy may issue a refund regardless of seller policy — this is why every listing description must be 100% accurate (supports the mission statement)
- **Best practice:** Offer to troubleshoot before refusing — most "I want a refund" situations are actually tech support issues that can be resolved

### When Human (Scott) Must Respond — Non-Automatable Situations

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

**Recommended board structure for OnBrandCraftz:**
1. `Digital Planners 2026 — Kawaii GoodNotes` (primary)
2. `Kawaii Sticker Packs — GoodNotes Elements`
3. `Printable Wall Art — Instant Download`
4. `SVG Cut Files — Cricut Silhouette`
5. `Etsy Digital Downloads` (broad catch-all)
6. Seasonal boards: `Back to School Planner Ideas`, `New Year Planning 2027`

**Automation workflow using `tools/pinterest_api.py`:**
- Post hero image + description + Etsy listing URL to the relevant board
- Space out posts: max 10/day for a new account, up to 25/day once established
- Use Tailwind's SmartSchedule for optimal timing if manual scheduling is preferred

### TikTok — Verified as Etsy Ranking Signal

**Confirmed:** External traffic from TikTok acts as a "vote of confidence" for Etsy listings and boosts organic search visibility. Etsy's algorithm registers external traffic sources as a brand authority signal.

**TikTok Algorithm 2026 Requirements:**
- Minimum **70% video completion rate** to enter virality pool (up from 50% in 2024)
- Watch time + completion rate = **40–50% of algorithm weight**
- Content for planners: process videos, planning setup, "plan with me" formats perform best

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

**Recommended for OnBrandCraftz:** Start with **EtsyHunt Pro ($3.99/mo)** for competitor monitoring + Chrome extension, add **Sale Samurai ($9.99/mo)** once revenue justifies for accurate keyword volume data.

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
- Higher prices can **increase perceived quality** and actually improve conversion for some product types (especially planners — buyers associate higher price with more content)
- Lowering prices to compete on cost typically hurts perceived value without proportional conversion gain for digital planners

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
1. Scott must run: `python tools/etsy_oauth.py`
2. Follow the browser authorization flow
3. New access + refresh tokens are written to `.env` automatically
4. All automation resumes without any other changes

---

## Autonomy Boundaries — What Claude Can Do vs. What Requires Scott

### Fully Autonomous (No Approval Needed)

- Monitor ROAS daily and log snapshots
- Run health checks and detect issues
- Generate new listing content (titles, tags, descriptions) from templates
- Generate art files using gpt-image-1 and composite into lifestyle scenes
- Run seasonal keyword reports and dry-run previews
- Send Quick Reply templates for Tier 1 support (file won't open, didn't receive download)
- Refresh OAuth access tokens (within 90-day window)
- Update SVG manifests and catalog files
- Run weekly reports and log decisions

### Requires Scott's Review Before Action

- **Publishing any listing to Etsy** — Scott reviews all 10 photos, title, description, price before going live
- **Pushing keyword updates** — `seasonal_keywords.py --push` runs only after Scott confirms
- **Responding to refund requests** — use Template 4 first; escalate if buyer pushes back
- **Responding to negative reviews** — always human-crafted, empathetic, personalized
- **Price changes on existing ranked listings** — present recommendation, wait for approval
- **Any bulk edit touching more than 10 listings** — confirm scope before running
- **Custom order requests** — pricing and feasibility require Scott's judgment
- **Re-authorization (OAuth)** — requires Scott to complete browser flow every 90 days

### Hard Stops — Never Do Without Explicit Permission

- Push to production Etsy without Scott's final review of photos + listing content
- Issue a refund or close a case
- Delete any listing (active or draft)
- Change prices on more than 5 listings in a single session
- Post to social media accounts
- Contact buyers directly about anything other than the 5 Quick Reply templates
