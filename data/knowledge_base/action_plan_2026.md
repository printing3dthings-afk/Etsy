# OnBrandCraftz — 2026 Action Plan
*Generated: May 2026 | Based on competitor research + Etsy API audit of 50 wall art listings*

---

## What Was Automated (Already Done)

| # | Action | Result |
|---|---|---|
| 1 | Rewrote all 50 wall art listing titles | Titles now include "printable" + "instant download", comma format, 55–65 chars, lead with buyer search phrase |
| 2 | Added instant download preamble to 49 listing descriptions | First sentence now contains primary keyword for Google indexing |
| 3 | Created "Pick Any 3 Prints" bundle listing | Listing id=4513637740, $14.97 — highest favorites ratio bundle type |
| 4 | Created "Complete Wall Art Bundle 50 Prints" listing | Listing id=4513637748, $24.99 — algorithm anchor listing |
| 5 | Fixed Paris Skyline listing photos (DP1033) | Frame now shows art as wide landscape, not tiny band in portrait frame |
| 6 | Fixed Autumn Fox listing photo (DP1038) | Frame now hangs above shelf with proper clearance (no overlap) |
| 7 | Saved full competitive intelligence report | `data/knowledge_base/competitor_research_2026.md` |

---

## Priority 1 — Critical (Do This Week)

These have the highest revenue impact and are blocking growth.

### 1.1 File Upscaling — BLOCKS ALL PRINT QUALITY
**Problem:** All product art files are ~1,024–1,536px. At 300 DPI that only prints cleanly at ~5" wide.
The #1 refund trigger on Etsy is pixelated prints.

**Action:**
- Download and install Real-ESRGAN (free, open source) or Topaz Gigapixel ($99/yr)
- Upscale every art file to minimum 3,000×4,500px (supports 10×15" at 300 DPI)
- Target: 4,800×6,000px (supports 16×20" at 300 DPI — the most popular large print size)
- Run on all 50 existing art files before running any ads

**Real-ESRGAN command (after install):**
```bash
python inference_realesrgan.py -n RealESRGAN_x4plus -i input_folder -o output_folder --outscale 4
```

**Priority order:** Upscale the top 20 listings by views first.

---

### 1.2 Multi-Size ZIP Packaging
**Problem:** Currently delivering single files. Competitors deliver ZIPs with 8–12 size variants.
Buyer confusion about which file to use = #3 review complaint.

**Action per listing:**
Create a ZIP containing:
- `2x3/` — 4×6", 8×12", 12×18", 16×24", 24×36" (JPG, 300 DPI)
- `4x5/` — 8×10", 16×20", 40×50cm (JPG, 300 DPI)
- `a_series/` — A4, A3, A2 (JPG, 300 DPI)
- `square/` — 8×8", 10×10", 12×12" (JPG, 300 DPI)
- `README.pdf` — printing instructions, which file for which frame

**Naming convention:** `fox-watercolor_8x10_300dpi.jpg` (not IMG_4456.jpg)
**ZIP size limit:** 20MB per file (Etsy hard limit) — use TinyPNG to compress if needed

**Tools to automate this:** Python PIL can resize and export all variants from the upscaled master.
Script location to create: `tools/generate_print_sizes.py`

---

### 1.3 Tags Audit — All 50 Listings
**Problem:** Tags may be duplicating title phrases (wastes ranking slots) and not covering enough buyer intents.

**Current tag issues found in research:**
- Many listings use single-word tags (underperform)
- Title phrases repeated in tags = wasted slots
- Not covering: occasion, recipient, aesthetic name, use case

**Action:**
- Run `tools/audit_tags.py` (to be created) to flag any tag that appears word-for-word in the title
- Replace duplicates with intent phrases from: room type, occasion (gift), recipient (mom, baby), aesthetic (boho, minimalist), use case (nursery, office)
- Each tag must be 2–3 words, max 20 chars

---

## Priority 2 — High Impact (Do This Month)

### 2.1 Nursery Art Expansion (8–10 New Listings)
**Research finding:** Nursery/baby = MEDIUM competition, high buyer intent. Currently 0 nursery-specific listings.
Existing art assets (fox, owl, bear, deer, rabbit) can be reused with nursery framing.

**Action:**
- Take existing animal watercolor art files
- Create new listings with nursery-specific titles and tags
- Example title: `Nursery Wall Art Printable, Instant Download, Woodland Animals` (62 chars)
- Example tags: `nursery wall art`, `baby room decor`, `woodland nursery`, `printable nursery`, `animal wall art`, `kids room decor`, `gender neutral`, `baby shower gift`, `nursery prints`, `infant room art`, `printable art`, `instant download`, `woodland animals`
- Price: $8.99–$12.99 (nursery buyers are high-intent, willing to pay)
- Target: 8–10 new listings using existing art files (no new art generation needed)

---

### 2.2 Black & White Minimalist Listings (5–8 New Listings)
**Research finding:** Black & white has LOW competition but consistent demand. Currently 0 B&W listings.
Fast to produce — convert any existing color art to grayscale.

**Action:**
- Convert 5–8 existing color art files to high-contrast B&W using PIL:
  ```python
  img.convert('L').save('output_bw.jpg')
  ```
- Focus on architectural subjects, line art, botanical illustrations (best in B&W)
- Title formula: `Minimalist Black White Print, Printable Wall Art, Instant Download` (65 chars)
- Tags: `black white print`, `minimalist wall art`, `black white art`, `modern wall decor`, `printable poster`, `instant download`, `monochrome print`, `line art print`, `abstract print`, `gallery wall`, `bedroom wall art`, `office wall decor`, `minimalist print`

---

### 2.3 Gallery Wall Set of 5 Listings (3–5 New Listings)
**Research finding:** Gallery wall sets of 5–7 are the highest revenue-per-transaction bundle type.
Price: $19.99–$39.99. 3–5x revenue vs. single print.

**Action:**
- Identify 3 cohesive art groupings from existing catalog:
  - Coastal/ocean set (blues, water, horizon themes)
  - Botanical/nature set (plants, flowers, garden)
  - Woodland/animal set (fox, deer, owl, rabbit, bear)
- Create one listing per set with all 5 art files in the ZIP
- Title: `Gallery Wall Set of 5, Printable Botanical Prints, Instant Download` (67 chars)
- Price: $19.99–$29.99 (apply 20–30% discount vs. sum of individual prices)
- Tags: `gallery wall set`, `set of 5 prints`, `printable set`, `wall art bundle`, `gallery wall art`, `printable art set`, `instant download`, `living room art`, `bedroom gallery`, `wall art prints`, `boho wall art`, `botanical prints`, `art set download`

---

### 2.4 Generate Gallery Wall Mockup Photos
**Problem:** Listings currently show art in 1 room type. Research shows 2 rooms = double buyer pool.
No gallery wall group shot exists (buyers who see grouped art are 40% more likely to buy multiple).

**Action:**
- For top 10 listings: generate a second lifestyle room using `composite_smart()`
- For any listing without a gallery wall mockup: create a 3-piece gallery wall arrangement
- Script: `tools/generate_gallery_wall.py` — arrange 3 coordinated prints on one wall

---

## Priority 3 — Growth (Do This Quarter)

### 3.1 Pinterest Setup
**Research finding:** Pinterest is the highest-ROI social channel for digital wall art. Pins circulate 12–24 months.
Results build over 2–4 months — start now.

**Steps:**
1. Create Pinterest business account (free)
2. Go to Pinterest → Settings → Claimed Accounts → claim Etsy shop URL
3. This enables Rich Pins (auto-pulls price and availability from Etsy)
4. Create 5–8 boards by ROOM TYPE or AESTHETIC (not product category):
   - "Living Room Gallery Wall Ideas"
   - "Woodland Nursery Decor"
   - "Boho Bedroom Art"
   - "Home Office Wall Art"
   - "Minimalist Print Inspiration"
5. Pin 5–7 times per week (schedule with Tailwind — ~$15/month, worth it)
6. Pin format: vertical 2:3 ratio, 1,000×1,500px minimum
7. Board title must match Etsy title phrasing exactly (keyword alignment)

**Expected results:** Organic Etsy traffic from Pinterest builds over 2–4 months. Patience required.

---

### 3.2 Etsy Ads — Start After 10 Organic Sales
**Do NOT start ads before 10+ organic sales.** No conversion data = Etsy's algorithm has nothing to optimize toward. Money wasted.

**When ready:**
- Start at $1–3/day total budget
- Let it run for 2 weeks untouched (Etsy needs data)
- After 2 weeks: turn off ads on listings with >50 clicks and 0 sales
- Increase budget only on listings with >3% conversion rate
- Target: listings that already have 2+ reviews get priority

---

### 3.3 Star Seller Status
**Research finding:** Star Seller status carries measurable ranking lift across entire catalog.

**Requirements:**
- Message reply rate: 95%+ within 24 hours (set up phone notifications for Etsy messages)
- 4.8+ average review rating
- 5+ orders in the past 3 months
- Ship on time (digital = always on time, auto-fulfilled)

**Action:**
- Check current message reply rate in Shop Manager → Star Seller tab
- Enable Etsy mobile app notifications so no message goes unanswered
- Set up auto-reply for after-hours: "Thanks for reaching out! I'll respond within 24 hours."

---

### 3.4 Review Generation
**Etsy's one-time buyer auto-message:**
Set in Etsy Dashboard → Shop Manager → Messages → Auto-reply after purchase:
> "Hope you love your print! If you have 30 seconds, a review means everything to a small shop 🙏"

This is the highest-leverage thing you can do for social proof at zero cost.

---

### 3.5 Trending Niche Listings (5–10 New Art + Listings)
**Low competition niches identified in research:**

| Niche | Competition | Action |
|---|---|---|
| Châteaucore / French Country | LOW | Generate 3–5 art files: French countryside, lavender fields, arched windows, vintage florals |
| Poetcore / Literary | LOW | Generate 3–5 art files: typewriters, stacked books, moody library, handwriting motifs |
| Cozy Japandi Minimalist | LOW-MEDIUM | Generate 3–5 art files: zen stones, single branch, matcha, minimalist landscape |
| Dark Academia Botanical | LOW-MEDIUM | Generate 3–5 art files: Victorian herbarium, pressed flowers, aged paper botanical |
| Celestial Nursery | LOW | Generate 3–5 art files: moon phases, stars, sleeping crescent, soft celestial |

Generate new art files using existing DALL-E/gpt-image-1 pipeline, then run through standard listing workflow.

---

## Priority 4 — Long-Term (Next 3–6 Months)

### 4.1 Seasonal Keyword Updates (Calendar)
Update top 10 listing tags 6 weeks before each peak season:

| Peak | Update By | Keywords |
|---|---|---|
| Back to school | Mid-July | student room decor, dorm room art, study space |
| Holiday gifting | Mid-October | art gift printable, holiday wall decor, gift for her |
| Valentine's Day | Early January | valentines art, love print, couples gift |
| Spring reset | Mid-January | spring wall art, floral print, fresh start |
| Mother's Day | Late March | mothers day gift, gift for mom, floral art |

---

### 4.2 Complete Product File Quality Upgrade
After upscaling (Priority 1.1), re-upload all files to Etsy listings with:
- Proper filename convention: `fox-watercolor_8x10_300dpi.jpg`
- sRGB color space (Etsy auto-converts — AdobeRGB shifts dramatically on print)
- All ratio variants in organized ZIP subfolders
- README.pdf with printing instructions

---

### 4.3 Expand to High-Revenue Bundles
Once nursery and B&W expansions are live (Priority 2):
- Room-specific bundles: "Living Room Gallery Wall Set", "Nursery Collection", "Home Office Art Bundle"
- "Pick Any 5" bundle (higher price point than Pick Any 3)
- Seasonal bundle (spring florals, autumn warmth, winter minimal)

---

## What Was NOT Automated (Requires Manual Action)

| Item | Why Manual | Notes |
|---|---|---|
| File upscaling | Requires local GPU software (Topaz Gigapixel or Real-ESRGAN) | Priority 1 — do first |
| Multi-size ZIP creation | Needs upscaled master files first | Blocked by upscaling |
| Pinterest setup | Account creation and board strategy | 30 min one-time setup |
| New art generation | Creative decisions needed | Use existing DALL-E pipeline |
| Review responses | Tone matters — never automated | Human judgment required |
| Tags audit + rewrite | Needs human review of each listing | 2–3 hours one-time |
| Gallery wall set curation | Creative decision: which art groups cohesively | 1 hour to curate |
| Nursery listing content | Writing unique titles/descriptions per listing | Can use templates from CLAUDE.md |
| Star Seller messaging habits | Behavior change — reply within 24 hrs | Enable phone notifications |

---

## Revenue Projection (Based on Competitor Research)

| Timeline | Expected Monthly Revenue | What Gets You There |
|---|---|---|
| Now (0 sales) | $0 | Baseline — listings just reoptimized |
| Month 1–2 | $50–$200 | Titles/tags now indexed, first organic sales |
| Month 3–4 | $200–$600 | Pinterest traffic building, 10+ reviews, bundle sales |
| Month 6+ | $600–$1,500 | Nursery + B&W + gallery sets live, Star Seller status |
| Month 9–12 | $1,000–$3,000 | 60–100 listings, niche focus, Pinterest established |

**Key lever:** The 80/20 rule says 10–15 listings will generate 80% of revenue. Focus optimization effort on whichever 10 get the most views/clicks in Month 1.

---

## Weekly Checklist (30 min/week)

- [ ] Check Etsy Search Visibility Dashboard — fix any flagged listings
- [ ] Review 7-day conversion rate per listing (Analytics → Listings)
- [ ] Respond to all messages within 24 hours
- [ ] Pin 5–7 times on Pinterest (after setup)
- [ ] Note which listings got views/clicks (these are your priority for improvement)

---

## Sources
Full competitive intelligence: `data/knowledge_base/competitor_research_2026.md`
Business operating standards: `data/knowledge_base/business_standards.md`
Photo generation guide: `data/knowledge_base/lifestyle_photo_mastery.md`
