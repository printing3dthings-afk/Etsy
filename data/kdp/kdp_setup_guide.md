# Amazon KDP Setup Guide — OnBrandCraftz
*Generated 2026-06-02 by kdp_publisher.py*

Amazon KDP (Kindle Direct Publishing) lets you sell physical print-on-demand books.
Customers order on Amazon, Amazon prints and ships, you collect royalties.
Zero inventory. Zero fulfillment. Passive revenue from planners already built.

---

## Step 1 — Create Your KDP Account

1. Go to **https://kdp.amazon.com**
2. Sign in with your Amazon account (create one if needed — use Printing3dthings@outlook.com)
3. Click **Get Started** and complete the publisher profile
4. Required info:
   - Legal name (Scott's full legal name)
   - Address (US address for tax purposes)
   - Phone number
   - Bank account for royalty deposits (routing + account number)

---

## Step 2 — Complete the Tax Interview

**Do this before publishing anything — required for royalty payment.**

1. In KDP Dashboard → top-right menu → **Account** → **Tax Information**
2. Click **Start Interview**
3. For US persons: choose **Individual** → enter SSN or EIN
4. Sign the W-9 form digitally
5. KDP withholds 30% if tax interview is not completed

**Pro tip:** If you have a single-member LLC, use the LLC's EIN instead of SSN — protects your personal SSN.

---

## Step 3 — Understand KDP Royalties (Color Interiors)

Our planners are COLOR interiors (they have color on every page).
KDP royalty formula for color paperbacks:

```
Net Royalty = (List Price × 60%) − Printing Cost
Printing Cost = $0.85 + (pages × $0.012)
```

| Book | Pages | Print Cost | @$17.99 Royalty | @$16.99 Royalty |
|------|-------|------------|-----------------|-----------------|
| DP1026 Life Planner | 104 | $2.098 | $8.69 | $8.09 |
| DP1027 Student Planner | 90 | $1.930 | $8.86 | $8.26 |
| DP1028 Budget Planner | 112 | $2.194 | $8.59 | $7.99 |
| DP1029 Fitness Planner | 102 | $2.074 | $8.72 | $8.12 |

**Recommended pricing: $16.99–$17.99 per planner** — strong margin, competitive on Amazon.

---

## Step 4 — Create a New Paperback Title

For each planner:

1. KDP Dashboard → **Create** → **Paperback**

### Book Details tab:
- **Title**: See `data/kdp/DP####_kdp_submission.json` → `kdp_metadata.title`
- **Subtitle**: See json file → `kdp_metadata.subtitle`
- **Author**: OnBrandCraftz
- **Description**: Copy from json file → `kdp_metadata.description`
- **Keywords**: Enter the 7 keywords from json file (one per field)
- **Categories**: Select 2 from BISAC list (see json file → `kdp_metadata.categories`)
- **Language**: English
- **AI content**: Check **Yes** — our planners use AI-generated cover art

### Book Content tab:
- **ISBN**: Leave blank (KDP assigns a free ISBN)
- **Print options**:
  - Interior & paper type: **Color, White paper**
  - Trim size: **8.5 × 11 inches**
  - Bleed settings: **No bleed**
  - Paperback cover finish: **Matte** (recommended — feels premium, matches kawaii aesthetic)
- **Manuscript**: Upload interior PDF (see json file → `interior.pdf_file`)
- **Cover**: Either upload the cover PDF or use KDP Cover Creator

---

## Step 5 — Create the Cover

**Option A (Recommended): KDP Cover Creator (free)**
1. In the Book Content tab, select **Launch Cover Creator**
2. Choose a template or start blank
3. Upload the kawaii cover image as the front cover artwork
4. KDP auto-calculates and places the spine — verify the spine width matches the calculation
5. Add your title to the spine (small text)
6. Leave back cover simple: shop name + short description + barcode area

**Option B: Custom cover in Canva/Photoshop**
- Required dimensions per book (see json → `cover.cover_dimensions_note`)
- Must be a single full-bleed PDF: back cover + spine + front cover in one file
- Spine widths:
  - DP1026 (104 pages): see `DP1026_kdp_submission.json` → `cover.spine_width_inches`
  - DP1027 (90 pages): see `DP1027_kdp_submission.json` → `cover.spine_width_inches`
  - DP1028 (112 pages): see `DP1028_kdp_submission.json` → `cover.spine_width_inches`
  - DP1029 (102 pages): see `DP1029_kdp_submission.json` → `cover.spine_width_inches`

---

## Step 6 — Set Pricing and Distribution

1. **Territories**: All territories worldwide
2. **Primary marketplace**: amazon.com (US)
3. **List price**: Set per the recommendations in each json file
4. **KDP Select**: **Do NOT enroll** — this requires exclusivity and would conflict with Etsy digital sales
5. **Expanded Distribution**: **Enable** — reaches bookstores, libraries, and educational institutions
   - Note: Expanded distribution uses a 40% royalty rate (vs 60% for Amazon direct)

---

## Step 7 — Review and Publish

1. Click **Launch Previewer** to verify interior and cover
2. Check every page — look for text cut off near margins, color accuracy
3. Order a **proof copy** ($4–8 + shipping) before approving for sale — worth it
4. Once you approve the proof: click **Publish**
5. KDP review: 24–72 hours
6. Book live on Amazon within 72 hours of approval

---

## Step 8 — Cross-Promote on Etsy

Once each book is live on Amazon:

1. Grab the Amazon product URL
2. Add to the bottom of the Etsy listing description:
   > "Prefer a physical printed copy? Order the paperback edition on Amazon → [Amazon link]"
3. This adds buyer confidence (Amazon = trusted) without cannibalizing digital sales
   (Most buyers who want digital WILL NOT buy the $17.99 physical copy — different buyer intent)

---

## Checklist Files

Each planner has a detailed submission JSON with a step-by-step checklist:
- `data/kdp/DP1026_kdp_submission.json`
- `data/kdp/DP1027_kdp_submission.json`
- `data/kdp/DP1028_kdp_submission.json`
- `data/kdp/DP1029_kdp_submission.json`

Run anytime to refresh:
```
python tools/kdp_publisher.py --all
python tools/kdp_publisher.py --royalties
python tools/kdp_publisher.py --check
```

---

## Revenue Projection

At $17.99 list price, $8.69 average royalty per copy:

| Monthly Amazon Sales | Monthly Royalty | Annual |
|---------------------|-----------------|--------|
| 10 copies (all books) | ~$87 | ~$1,044 |
| 50 copies | ~$435 | ~$5,220 |
| 100 copies | ~$869 | ~$10,428 |

This is **passive revenue** — once the books are published, Amazon handles everything.
Each new planner product adds to the revenue stack with zero additional fulfillment work.

---

*OnBrandCraftz — Built with tools/kdp_publisher.py*
