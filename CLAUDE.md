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

### Titles (max 140 chars)
- Lead with the PRIMARY search keyword buyers type
- Include year (2026) or "Undated" for evergreen
- Include app compatibility (GoodNotes, Notability)
- Include "Instant Download" and "PDF"
- Example: `Kawaii Digital Planner 2026 | GoodNotes Notability iPad | Fillable PDF Planner | Instant Download | Kawaii Sticker Pack Included`

### Descriptions — Required Sections in Order
1. **Hook** (1–2 sentences): What it is and who it's for, emotion-first
2. **WHAT'S INCLUDED** (bullet list): Every file, page count, sections
3. **COMPATIBLE APPS** (list): GoodNotes 6, Notability, PDF Expert, Xodo, Acrobat Reader, print-ready
4. **HOW TO USE STICKERS** (3 steps): Import PNGs into sticker library → drag unlimited times
5. **HOW TO USE THE PLANNER** (numbered steps): Download → open in app → tap to fill
6. **SECTIONS INCLUDED** (list): Every section name with brief description
7. **TECHNICAL DETAILS**: File format, size, page count, page size
8. **FAQ**: Common questions about compatibility, printing, refunds
9. **COPYRIGHT**: Personal use only, not for resale or redistribution

### Tags (max 13, each max 20 chars, no special characters)
Core tags for all planners:
`digital planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `fillable pdf`, `instant download`, `kawaii planner`, `2026 planner`, `pdf planner`, `digital download`

Product-specific additions:
- DP1026 (life planner): `life planner`, `daily planner`, `planner bundle`
- DP1027 (student): `student planner`, `school planner`, `study planner`
- DP1028 (budget): `budget planner`, `finance planner`, `money planner`
- DP1029 (fitness): `fitness planner`, `wellness planner`, `health planner`

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
1. **Main image**: Planner cover on iPad screen, lifestyle shot — MOST IMPORTANT (determines click-through rate)
2. **What's included**: Flat lay showing PDF + sticker PNGs
3. **Monthly spread**: Screenshot of a monthly page
4. **Weekly spread**: Screenshot of a weekly page
5. **Sticker library**: Shows all 3 kawaii sticker sheets
6. **Sticker how-to**: Step-by-step showing GoodNotes import
7. **App compatibility**: GoodNotes, Notability, PDF Expert logos/icons listed
8. **Cover close-up**: Kawaii illustrated cover detail
9. **Habit tracker page**: Shows interactive checkboxes
10. **Goals/budget page**: Shows the specialized pages

### Mockup Generation Notes
- For iPad mockups: use `gpt-image-1` with prompt showing the planner on a Silver iPad Pro 12.9" screen with Apple Pencil
- Background: cozy desk scene with coffee, plants, notebook — lifestyle feel
- Image size for Etsy: minimum 2000×2000px, ideally 3000×3000px square

---

## Listing Agent Workflow (Step-by-Step)

When asked to list a planner on Etsy:
1. Call `get_approved_unlisted_products` to see what's ready
2. Products must have `status: qc_pending` or `status: approved`
3. Call `generate_listing_content` with the full pre-written template (see below)
4. Generate listing mockup photos using `generate_digital_art` with iPad lifestyle prompts
5. Once ETSY_ACCESS_TOKEN is set (run `python tools/etsy_oauth.py`), call `publish_digital_listing`
6. After publishing, upload the PDF and sticker pack ZIP as digital files on the Etsy listing

## Pre-Written Listing Content

### DP1026 — Ultimate Digital Life Planner

**Title** (138 chars):
`Kawaii Digital Planner 2026 | GoodNotes Notability iPad | Fillable PDF + Sticker Pack | Instant Download | Life Planner Bundle`

**Tags**:
`digital planner`, `goodnotes planner`, `notability planner`, `ipad planner`, `fillable pdf`, `kawaii planner`, `2026 planner`, `instant download`, `life planner`, `planner bundle`, `pdf planner`, `digital download`, `sticker planner`

**Price**: $14.99

**Description**:
```
✨ Stay organized, stay cute — your ultimate kawaii digital life planner is here!

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

### DP1027 — Student & School Planner

**Title** (135 chars):
`Kawaii Student Planner 2026 | School Planner GoodNotes Notability | Fillable PDF + Sticker Pack | Academic Planner Instant Download`

**Tags**:
`digital planner`, `student planner`, `school planner`, `goodnotes planner`, `ipad planner`, `fillable pdf`, `kawaii planner`, `2026 planner`, `instant download`, `study planner`, `academic planner`, `pdf planner`, `digital download`

**Price**: $9.99

### DP1028 — Budget & Finance Planner

**Title** (138 chars):
`Budget Planner 2026 Digital | Finance Planner GoodNotes iPad | Fillable PDF + Sticker Pack | Money Planner Instant Download Kawaii`

**Tags**:
`budget planner`, `finance planner`, `digital planner`, `goodnotes planner`, `fillable pdf`, `money planner`, `2026 planner`, `instant download`, `ipad planner`, `kawaii planner`, `pdf planner`, `digital download`, `savings planner`

**Price**: $12.99

### DP1029 — Fitness & Wellness Planner

**Title** (136 chars):
`Kawaii Fitness Planner 2026 | Wellness Planner GoodNotes iPad | Fillable PDF + Sticker Pack | Health Habit Tracker Instant Download`

**Tags**:
`fitness planner`, `wellness planner`, `digital planner`, `goodnotes planner`, `fillable pdf`, `health planner`, `2026 planner`, `instant download`, `ipad planner`, `kawaii planner`, `habit tracker`, `meal planner`, `pdf planner`

**Price**: $12.99

---

## Image Generation Notes (for DALL-E mockups)

### iPad Lifestyle Mockup Prompt Template
```
Professional product mockup photo, square format. Silver iPad Pro 12.9 inch lying flat on a cozy 
desk, screen showing [PLANNER DESCRIPTION]. Apple Pencil resting beside it. 
Surrounding props: steaming latte in a ceramic mug, small potted succulent, a few washi tape rolls, 
a pastel pink notebook, soft natural light from the left side. 
Background: light cream/white desk with subtle wood grain texture. 
Style: bright, clean, Etsy product photography aesthetic. High resolution. No text overlays.
```

### App Compatibility Graphic Prompt
```
Clean flat-lay infographic style. White background. Shows the PDF planner file icon in center. 
Around it: GoodNotes app icon, Notability app icon, PDF Expert icon, Xodo icon, Adobe Acrobat icon. 
Connected with soft pastel lines. Label text in friendly sans-serif: "Works with your favorite apps". 
Kawaii pastel color palette. Professional digital product graphic style.
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
