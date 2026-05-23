# OnBrandCraftz — Etsy Automation Hub

## Store
- **Name**: OnBrandCraftz
- **Etsy Shop ID**: `onbrandcraftz`
- **Owner email**: Printing3dthings@outlook.com
- **Niche**: Digital planners, kawaii sticker packs, printable digital products
- **Brand aesthetic**: Kawaii illustrated, pastel colors, cute/fun but polished

## Credentials (all in `.env` — never hardcode, never commit)
- `ANTHROPIC_API_KEY` — Claude API
- `OPENAI_API_KEY` — DALL-E image generation (gpt-image-1)
- `ETSY_API_KEY` / `ETSY_CLIENT_ID` — `v874xp0m0r4yoh72btmux151`
- `ETSY_CLIENT_SECRET` — `hjyq1cmrog`
- `ETSY_ACCESS_TOKEN` / `ETSY_REFRESH_TOKEN` — empty until OAuth is run
- `SMTP_USER` / `SMTP_PASSWORD` — Outlook email for digital delivery

## Etsy OAuth Status
**Not yet authorized.** Run `python tools/etsy_oauth.py` to complete OAuth 2.0 + PKCE flow.
Redirect URI registered: `http://localhost:3003/callback`
Scopes: shops_r, shops_w, listings_r, listings_w, transactions_r, billing_r, profile_r, email_r, feedback_r, address_r

---

## Product Catalog

### DP1026 — Ultimate Digital Life Planner (Lavender Dreams)
- **File**: `data/digital_products/product_files/DP1026.pdf` (~15MB, 102 pages)
- **Color scheme**: Lavender Dreams (muted purple #8666AA, soft lavender accent)
- **Cover**: Full-page kawaii illustrated cover (DALL-E, portrait 1024×1536)
- **Sections**: Monthly × 12, Monthly Review × 12, Month at a Glance × 12, Weekly × 52, Habit Tracker, Goals, Budget, Meal Plan, Notes × 4
- **Sticker Library**: 3 pages — Planner & Stationery, Cozy Lifestyle, Seasonal & Holiday
- **Sticker Pack ZIP**: `DP1026_sticker_pack.zip` (3 PNG sheets, transparent background)
- **Interactive**: Yes — fillable fields, hyperlinked tabs, JS popup sticker menu (Acrobat/Xodo)
- **Compatible apps**: GoodNotes 5/6, Notability, PDF Expert, Xodo, Adobe Acrobat Reader
- **Target price**: $14.99–$16.99
- **Target audience**: Women 18–35, planner lovers, stationery enthusiasts, productivity

### DP1027 — Student & School Planner 2026 (Cotton Candy)
- **File**: `data/digital_products/product_files/DP1027.pdf` (~13MB, 88 pages)
- **Color scheme**: Cotton Candy (pink #DE97C6, sky blue accent)
- **Sections**: Monthly × 12, Monthly Review × 12, Weekly × 52, Habit Tracker, Goals, Notes × 4
- **Sticker Library**: 3 pages (same kawaii sticker system)
- **Interactive**: Yes
- **Target price**: $9.99–$12.99
- **Target audience**: High school/college students, back to school, study planners

### DP1028 — Budget & Finance Planner 2026 (Midnight Blue)
- **File**: `data/digital_products/product_files/DP1028.pdf` (~14MB, 100 pages)
- **Color scheme**: Midnight Blue (deep royal blue #1B2568, ice-blue accent)
- **Sections**: Monthly × 12, Monthly Review × 12, Month at a Glance × 12, Weekly × 52, Budget, Goals, Notes × 4
- **Sticker Library**: 3 pages
- **Interactive**: Yes
- **Target price**: $12.99–$14.99
- **Target audience**: Adults tracking finances, budgeters, Dave Ramsey followers, debt payoff community

### DP1029 — Fitness & Wellness Planner 2026 (Coral Peach)
- **File**: `data/digital_products/product_files/DP1029.pdf` (~14MB, 89 pages)
- **Color scheme**: Coral Peach (warm coral #FD6C49, peach-gold accent)
- **Sections**: Monthly × 12, Monthly Review × 12, Weekly × 52, Habit Tracker, Meal Plan, Goals, Notes × 4
- **Sticker Library**: 3 pages
- **Interactive**: Yes
- **Target price**: $12.99–$14.99
- **Target audience**: Fitness beginners, wellness journey, weight loss, healthy eating, self-care

---

## What Customers Receive (Digital Download)
Etsy delivers files instantly at checkout — no shipping. Each listing includes:
- **File 1**: The planner PDF (interactive, fillable, hyperlinked)
- **File 2**: Sticker Pack ZIP — 3 PNG sticker sheets with transparent backgrounds

**PDF format details:**
- US Letter size (8.5×11 in)
- Fillable form fields for all text areas
- Hyperlinked side navigation tabs (GoodNotes/Notability compatible)
- PDF bookmarks/outline for table of contents
- Interactive sticker menu (Acrobat Reader / Xodo / PDF Expert only)

---

## Sticker System — How It Works Per App

### GoodNotes 6 / Notability (most buyers — 90%+)
- **Sticker PNG sheets**: Tap Elements → Stickers → + (import) → select PNG files from ZIP
- All 3 sticker sheets appear in library; tap any sticker to drag onto any page, unlimited copies
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
- Lifestyle thumbnail → 314% higher CTR than flat white background (A/B test data)
- Use all 10 photo slots — each additional image increases conversion rate
- Recommended size: **2400×2400px square** (outperforms 2000px by 7–12% CTR)
- Keep subject in center **70% of frame** — Etsy crops thumbnails on mobile
- Add 5% white padding around edges — recovered 19% CTR in seller testing

---

### Titles (max 140 chars)
- Lead with the PRIMARY search keyword buyers type
- Include year (2026) or "Undated" for evergreen
- Include app compatibility (GoodNotes, Notability)
- Include "Instant Download" and "PDF"
- Example: `Kawaii Digital Planner 2026 | GoodNotes Notability iPad | Fillable PDF Planner | Instant Download | Kawaii Sticker Pack Included`

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
| DP1026 Ultimate | $14.99 | 102 pages + kawaii cover + sticker pack — premium |
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
   - Right panel: 3 sticker PNG sheets fanned out, stickers clearly visible
   - Text callouts added in Canva post: "102 pages", "3 sticker sheets", "Instant Download"
   - Builds buyer confidence before purchase; the #2 reason people click away is unclear value

3. **[PREVIEW] Monthly Spread**
   - Clean in-app screenshot of a full monthly calendar page
   - Shows the color theme, kawaii design, fillable cells, and section headers
   - Slight lifestyle context (iPad held or on desk)

4. **[PREVIEW] Weekly Spread**
   - Close-up of a weekly layout page showing time-blocking rows, fillable fields, kawaii typography
   - Side tab navigation visible to show hyperlinked navigation

5. **[BONUS] Sticker Library**
   - All 3 PNG sticker sheets displayed flat, stickers large and legible
   - Label each sheet in Canva post: "Sheet 1: Planner & Stationery", etc.
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

**Title** (125 chars):
`Kawaii Digital Planner 2026 | GoodNotes Notability iPad | Fillable PDF + Sticker Pack | Instant Download | Life Planner Bundle`

**Tags**:
`digital planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `kawaii planner`, `fillable planner`, `2026 life planner`, `kawaii sticker pack`, `instant download`, `printable planner`, `daily planner pdf`, `planner bundle`, `habit tracker pdf`

**Price**: $14.99

**Description**:
```
✨ Stay organized, stay cute — your ultimate kawaii digital life planner for GoodNotes and Notability is here!

Meet the Ultimate Digital Life Planner 2026, the most complete fillable PDF planner for GoodNotes, Notability, and iPad — packed with 102 beautifully designed pages, an illustrated kawaii cover, and a full kawaii sticker pack so you can personalize every single page.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 102 pages, US Letter, Lavender Dreams color theme
✅ Kawaii Sticker Pack ZIP — 3 PNG sticker sheets (60+ stickers, transparent background)
   • Sheet 1: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 2: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 3: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
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
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 3 PNG files
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
📅 SECTIONS INCLUDED (102 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with daily notes
• Monthly Reviews × 12 — reflect, celebrate wins, plan improvements
• Month at a Glance × 12 — top priorities, focus areas, intentions
• Weekly Spreads × 52 — time-blocked horizontal layout for every week of 2026
• Habit Tracker — 31-day grid, fully customizable
• Goals Page — quarterly goals, action steps, milestones
• Budget Tracker — income, expenses, savings, bills
• Meal Planner — weekly meal plan with grocery list
• Notes Pages × 4 — lined + dot-grid mix
• Kawaii Sticker Library × 3 — illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF
• Page size: US Letter (8.5 × 11 inches)
• Pages: 102
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

**Title** (132 chars):
`Kawaii Student Planner 2026 | School Planner GoodNotes Notability | Fillable PDF + Sticker Pack | Academic Planner Instant Download`

**Tags**:
`student planner`, `digital planner`, `school planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `academic planner`, `study planner`, `kawaii planner`, `fillable planner`, `back to school`, `instant download`, `kawaii sticker pack`

**Price**: $9.99

**Description**:
```
🎓 Study smarter, plan cuter — the kawaii student planner for GoodNotes and Notability that makes school actually fun!

Meet the Kawaii Student Planner 2026, the most adorable fillable PDF planner for GoodNotes, Notability, and iPad — packed with 88 beautifully designed pages in a dreamy Cotton Candy color theme, plus a full kawaii sticker pack to personalize every week of your school year.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 88 pages, US Letter, Cotton Candy color theme (pink + sky blue)
✅ Kawaii Sticker Pack ZIP — 3 PNG sticker sheets (60+ stickers, transparent background)
   • Sheet 1: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 2: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 3: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
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
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 3 PNG files
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
📅 SECTIONS INCLUDED (88 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with daily note cells
• Monthly Reviews × 12 — reflect on wins, set next month's focus
• Weekly Spreads × 52 — class schedule layout with assignment tracker per subject
• Habit Tracker — 31-day grid for study streaks, self-care, and daily goals
• Goals Page — semester goals, action steps, milestones
• Notes Pages × 4 — lined + dot-grid for lecture notes or brainstorming
• Kawaii Sticker Library × 3 — illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF
• Page size: US Letter (8.5 × 11 inches)
• Pages: 88
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

**Title** (131 chars):
`Digital Budget Planner 2026 | Finance Planner GoodNotes iPad | Fillable PDF + Sticker Pack | Kawaii Money Planner Instant Download`

**Tags**:
`budget planner`, `finance planner`, `digital planner`, `goodnotes planner`, `money planner`, `ipad planner`, `fillable planner`, `savings planner`, `debt payoff planner`, `kawaii planner`, `instant download`, `budget tracker`, `2026 budget plan`

**Price**: $12.99

**Description**:
```
💰 Take control of your money in the most adorable way possible — your kawaii budget planner for GoodNotes and Notability is here!

Meet the Digital Budget & Finance Planner 2026, the most complete fillable PDF money planner for GoodNotes, Notability, and iPad — packed with 100 beautifully designed pages in a sleek Midnight Blue color theme, with built-in trackers for every dollar, debt, and financial goal you have.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 100 pages, US Letter, Midnight Blue color theme
✅ Kawaii Sticker Pack ZIP — 3 PNG sticker sheets (60+ stickers, transparent background)
   • Sheet 1: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 2: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 3: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
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
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 3 PNG files
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
💸 SECTIONS INCLUDED (100 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with bill-due date markers
• Monthly Reviews × 12 — reflect on spending wins, set savings intentions
• Month at a Glance × 12 — monthly income, fixed expenses, savings target, debt minimum
• Weekly Spreads × 52 — week-by-week spending log and task list
• Budget Tracker × 12 — monthly income vs. expenses breakdown, net savings
• Goals Page — financial goals, debt payoff milestones, savings targets
• Notes Pages × 4 — lined for ideas, financial planning, or research
• Kawaii Sticker Library × 3 — illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF
• Page size: US Letter (8.5 × 11 inches)
• Pages: 100
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

**Title** (132 chars):
`Kawaii Fitness Planner 2026 | Wellness Planner GoodNotes iPad | Fillable PDF + Sticker Pack | Health Habit Tracker Instant Download`

**Tags**:
`fitness planner`, `wellness planner`, `digital planner`, `goodnotes planner`, `health planner`, `ipad planner`, `habit tracker`, `meal planner pdf`, `kawaii planner`, `fillable planner`, `instant download`, `self care planner`, `2026 fitness plan`

**Price**: $12.99

**Description**:
```
🌸 Your glow-up starts now — the kawaii fitness planner for GoodNotes and Notability that makes healthy habits actually stick!

Meet the Fitness & Wellness Planner 2026, your all-in-one fillable PDF wellness companion for GoodNotes, Notability, and iPad — packed with 89 beautifully designed pages in a warm Coral Peach color theme, with habit trackers, meal planning, and fitness logs to support your healthiest year yet.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Interactive PDF Planner — 89 pages, US Letter, Coral Peach color theme
✅ Kawaii Sticker Pack ZIP — 3 PNG sticker sheets (60+ stickers, transparent background)
   • Sheet 1: Planner & Stationery — notebooks, pens, stars, washi tape, coffee cups
   • Sheet 2: Cozy Lifestyle — mugs, candles, books, fairy lights, sleeping cat
   • Sheet 3: Seasonal & Holiday — cherry blossoms, pumpkins, snowflakes, valentines
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
2. In GoodNotes 6: tap the Elements button → Stickers tab → tap + → import the 3 PNG files
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
🏃 SECTIONS INCLUDED (89 pages)
━━━━━━━━━━━━━━━━━━━━━━━━
• Yearly Overview — see all 12 months at a glance
• Monthly Calendars × 12 — full month grid with workout and self-care markers
• Monthly Reviews × 12 — celebrate wins, reflect on habits, reset intentions
• Weekly Spreads × 52 — weekly workout planner + daily water intake + mood tracker
• Habit Tracker — 31-day grid for workouts, water, sleep, nutrition, and self-care
• Meal Planner — weekly meal plan with grocery list + macro/calorie note row
• Goals Page — fitness goals, milestone celebrations, progress measurements
• Notes Pages × 4 — lined for journaling, research, or recipe notes
• Kawaii Sticker Library × 3 — illustrated sticker reference sheets

━━━━━━━━━━━━━━━━━━━━━━━━
📄 TECHNICAL DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━
• Format: Interactive fillable PDF
• Page size: US Letter (8.5 × 11 inches)
• Pages: 89
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

## Image Generation Notes (for gpt-image-1 / DALL-E)

Generate all 10 images at **2400×2400px square**. Never put text overlays in the AI-generated image — add all text callouts separately in Canva after generation. No hands or people visible (AI renders these unnaturally). Use the product's color theme as the accent color for props and backgrounds.

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

## Quality Check Checklist (before listing)
- [ ] PDF opens in GoodNotes without errors
- [ ] All fillable fields work
- [ ] Hyperlinked tabs navigate correctly
- [ ] Sticker library pages display correctly (3 pages)
- [ ] Sticker PNG sheets have transparent backgrounds
- [ ] File size < 20MB (Etsy limit per file)
- [ ] PDF page count matches spec
- [ ] Cover image displays correctly (full-page kawaii illustration)
- [ ] Footer shows STICKERS button on every planner page
- [ ] All 10 listing photos generated at 2400×2400px
- [ ] Hero photo (Photo 1) reviewed — does it stop the scroll?
- [ ] Text callouts added in Canva for Photos 2, 6, 7 (not baked into AI image)
- [ ] Tags verified: all 13 used, each ≤ 20 chars, no special characters
- [ ] Title verified: primary keyword in first 40 chars, total ≤ 140 chars
- [ ] Description: primary keyword appears in sentence 1 or 2
