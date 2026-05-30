# OnBrandCraftz — Master To-Do List (2026)
*Updated: May 2026 | Prioritized by revenue impact*

Check off items as you complete them. Everything below requires manual action — automated items are already done.

---

## ALREADY DONE ✓
- [x] Rewrote all 50 wall art titles (include "printable" + "instant download", comma format, 55–65 chars)
- [x] Added instant download preamble to 49 listing descriptions
- [x] Created "Pick Any 3 Prints" bundle listing ($14.97)
- [x] Created "Complete Wall Art Bundle 50 Prints" listing ($24.99)
- [x] Fixed Paris Skyline listing photos — art now shows as wide landscape frame
- [x] Fixed Autumn Fox listing photo — frame hangs above shelf with proper clearance
- [x] Saved competitor research report (`data/knowledge_base/competitor_research_2026.md`)

---

## PRIORITY 1 — Do This Week (Blocking Everything Else)

### File Quality
- [ ] **Install Real-ESRGAN** (free) or Topaz Gigapixel ($99/yr) for AI upscaling
  - Real-ESRGAN: https://github.com/xinntao/Real-ESRGAN (free, open source)
  - Topaz Gigapixel: better quality, easier UI, paid
- [ ] **Upscale all 50 art files** to minimum 4,800×6,000px (supports 16×20" at 300 DPI)
  - Run upscaler on each file in `data/digital_products/product_files/`
  - Save upscaled versions in a new subfolder: `product_files/upscaled/`
  - Do the top 20 listings by views first (check Etsy Analytics → Listings → sort by Views)
- [ ] **Create multi-size ZIP for each listing** after upscaling
  - Each ZIP needs: 2:3 folder, 4:5 folder, A-series folder, square folder, README.pdf
  - File naming: `fox-watercolor_8x10_300dpi.jpg` (not IMG_4456.jpg)
  - Keep ZIP under 20MB (TinyPNG to compress if needed)
  - Re-upload ZIP to each Etsy listing as the digital file delivery

### Listing Tags Audit
- [ ] **Audit all 50 listing tags** — open each listing in Etsy and check:
  - Are all 13 tag slots used? (empty = lost ranking)
  - Does any tag repeat a phrase already in the title word-for-word? (wasted slot — replace it)
  - Replace duplicates with: room type (bedroom wall art), occasion (housewarming gift), recipient (gift for her), aesthetic (boho decor), use case (gallery wall)
  - Every tag must be 2–3 words, max 20 characters

---

## PRIORITY 2 — Do This Month

### New Listings Using Existing Art (No New Art Needed)

- [ ] **Create 8–10 Nursery Listings** using existing animal art files (fox, owl, bear, deer, rabbit)
  - Title formula: `[Animal] Nursery Wall Art, Printable Instant Download, Woodland` (≤70 chars)
  - Tags to use: `nursery wall art`, `woodland nursery`, `baby room decor`, `printable nursery`, `animal nursery art`, `kids room decor`, `gender neutral`, `baby shower gift`, `woodland animals`, `nursery prints`, `printable art`, `instant download`, `infant room art`
  - Price: $8.99–$12.99
  - Note in description: "Perfect for a woodland nursery, gender-neutral baby room, or toddler's bedroom."

- [ ] **Create 5–8 Black & White Listings** (convert existing color art to grayscale)
  - In Photoshop or Preview: Image → Mode → Grayscale (or use PIL script)
  - Best candidates: architectural art, line drawings, botanical illustrations
  - Title formula: `Minimalist Black White Print, Printable Wall Art, Instant Download` (65 chars)
  - Tags: `black white print`, `minimalist wall art`, `black white art`, `modern wall decor`, `monochrome print`, `printable poster`, `instant download`, `line art print`, `gallery wall`, `bedroom wall art`, `office wall decor`, `abstract print`, `minimalist print`
  - Price: $4.99–$7.99 (impulse tier)

- [ ] **Create 3 Gallery Wall Sets of 5** (bundle cohesive art into one listing)
  - Identify 3 groups from existing catalog:
    - Coastal/ocean set (blues, water, horizon art)
    - Botanical/nature set (plants, flowers, garden art)
    - Woodland/animal set (fox, deer, owl, rabbit, bear)
  - One listing per set — all 5 files in the ZIP
  - Title formula: `Gallery Wall Set of 5, Printable [Theme] Prints, Instant Download` (≤70 chars)
  - Price: $19.99–$29.99 (20–30% discount vs. sum of individual prices)
  - Tags: `gallery wall set`, `set of 5 prints`, `printable set`, `wall art bundle`, `gallery wall art`, `printable art set`, `instant download`, `living room art`, `bedroom gallery`, `art set download`, `boho wall art`, `[theme] prints`, `wall art prints`

### Listing Photo Improvements

- [ ] **Add second room type photo to top 10 listings** (buyers shop by room first)
  - Check Etsy Analytics → which 10 listings have highest views
  - Each listing should show art in 2 different rooms — currently most show only 1
  - Generate second room using the existing `tools/lifestyle_composite.py` script
  - Second room options: bedroom if current is living room, office if current is bedroom

- [ ] **Add a gallery wall grouping photo to any listing without one**
  - Arrange 3 coordinated prints on one wall in a composite image
  - Buyers who see grouped art are 40% more likely to buy multiple

---

## PRIORITY 3 — Do This Quarter

### Pinterest (Highest-ROI Social Channel for Wall Art)

- [ ] **Create Pinterest Business account** (free — pinterest.com/business)
- [ ] **Claim your Etsy shop on Pinterest**
  - Pinterest → Settings → Claimed Accounts → enter your Etsy shop URL
  - This enables Rich Pins (auto-shows price and availability from Etsy on every pin)
- [ ] **Create 5–8 boards by room type or aesthetic** (NOT by product category)
  - ✓ "Living Room Gallery Wall Ideas"
  - ✓ "Woodland Nursery Decor"
  - ✓ "Boho Bedroom Wall Art"
  - ✓ "Home Office Art Inspiration"
  - ✓ "Minimalist Print Ideas"
  - ✗ Do NOT name boards "My Products" or "My Shop"
- [ ] **Pin 5–7 times per week** (consistency beats volume — set a weekly reminder)
  - Pin format: vertical 2:3 ratio, 1,000×1,500px minimum
  - Board title keywords must match your Etsy listing title phrasing exactly
  - Consider Tailwind (~$15/month) to schedule pins in advance
- [ ] **Note:** Results build over 2–4 months — start now, be patient

### Star Seller Status (Ranking Lift Across Entire Catalog)

- [ ] **Enable Etsy app push notifications** on your phone for messages
- [ ] **Reply to every message within 24 hours** — 95%+ reply rate required
- [ ] **Check your Star Seller dashboard** in Etsy Shop Manager → Star Seller tab
  - See current score for: message reply rate, reviews, on-time shipping
  - Fix any metric below threshold
- [ ] **Set up post-purchase auto-message** in Etsy Dashboard → Shop Manager → Messages:
  > "Hope you love your print! If you have 30 seconds, a review means everything to a small shop 🙏"

### New Trending Niche Art (Generate + List)

- [ ] **Châteaucore / French Country** — 3–5 new art files
  - Subjects: French countryside, lavender fields, arched windows, vintage florals, Parisian rooftops
  - Low competition, top Etsy trend search term 2025–2026
- [ ] **Poetcore / Literary** — 3–5 new art files
  - Subjects: typewriters, stacked books, moody library, quill pen, handwriting motifs
  - Loyal niche community, very low competition
- [ ] **Cozy Japandi Minimalist** — 3–5 new art files
  - Subjects: zen stones, single branch, matcha bowl, minimalist landscape, rice paper texture
- [ ] **Dark Academia Botanical** — 3–5 new art files
  - Subjects: Victorian herbarium illustrations, pressed flowers, aged paper botanical, mushroom specimens
- [ ] **Celestial Nursery** — 3–5 new art files
  - Subjects: moon phases, sleeping crescent moon, stars, soft celestial for nursery
  - Combines two high-intent searches: celestial + nursery

For each niche above, after generating art:
- Create listing with niche-specific title and tags
- Generate lifestyle photos using existing composite tool

---

## PRIORITY 4 — Ongoing / Quarterly

### Etsy Ads (Do NOT start until 10+ organic sales)
- [ ] Wait until you have at least 10 organic sales with reviews
- [ ] Start ads at $1–3/day total budget
- [ ] Let run for 2 weeks untouched (Etsy needs data to optimize)
- [ ] After 2 weeks: pause listings with >50 clicks and 0 sales
- [ ] Increase budget only on listings with >3% conversion rate

### Seasonal Keyword Updates (Calendar — do 6 weeks before each peak)
- [ ] **Mid-July:** Update top 10 listings with back-to-school tags
  - Add: `student room decor`, `dorm room art`, `study space wall art`
- [ ] **Mid-October:** Update with holiday/New Year tags
  - Add: `new year wall art`, `holiday gift`, `gift for her printable`
- [ ] **Early January:** Update with Valentine's Day tags
  - Add: `valentines art`, `love print`, `couples gift printable`
- [ ] **Mid-January:** Update with spring reset tags
  - Add: `spring wall art`, `floral print`, `fresh start decor`
- [ ] **Late March:** Update with Mother's Day tags
  - Add: `mothers day gift`, `gift for mom`, `floral art print`

### Monthly Health Check
- [ ] Run `python tools/shop_health_check.py` on the 1st of each month
- [ ] Identify listings with high views but low conversion → fix photo or price
- [ ] Compare conversion rates and revenue vs. prior month

---

## REVENUE PROJECTION

| Milestone | Expected Monthly Revenue | Key Unlock |
|---|---|---|
| After tags + titles (done) | $50–$200 | Listings now indexed correctly |
| After upscaling + ZIPs | $100–$400 | No more pixelated print complaints |
| After nursery + B&W + sets | $300–$800 | 3x listing count, bundle revenue |
| After Pinterest (month 3–4) | $600–$1,500 | Passive organic traffic |
| After Star Seller status | $800–$2,000 | Catalog-wide ranking lift |
| At 60–100 listings | $1,000–$3,000 | Volume + niche focus compound |

---

*Full competitive research: `data/knowledge_base/competitor_research_2026.md`*
*Business operating standards: `data/knowledge_base/business_standards.md`*
