# Printify Setup Guide — OnBrandCraftz
*Generated 2026-06-02 by printify_publisher.py*

Printify is a free print-on-demand platform. Buyers order on Etsy, Printify prints
and ships, you keep the margin. Zero inventory, zero fulfillment overhead.

---

## How It Works

```
Buyer places Etsy order
        ↓
Etsy auto-forwards to Printify (via integration)
        ↓
Printify routes to nearest print facility
        ↓
Print ships to buyer in 5–10 business days
        ↓
You earn: Etsy sale price − Printify cost = profit
```

---

## Step 1 — Create Printify Account

1. Go to https://printify.com
2. Sign up with Printing3dthings@outlook.com
3. No monthly fee — free to use

---

## Step 2 — Connect Your Etsy Shop

1. Printify Dashboard → My stores → Add new store
2. Select Etsy from the platform list
3. Authorize Printify to access your Etsy account
4. Printify will appear in your Etsy Connected Apps

---

## Step 3 — Get Your API Key

1. Printify Dashboard → top-right avatar → My account → Connections → API
2. Generate a new token
3. Add to .env:
   ```
   PRINTIFY_API_KEY=your_token_here
   ```

---

## Step 4 — Understand Blueprints

Printify uses "blueprints" — product templates. For wall art posters:

| Blueprint | ID   | Type                  | Notes                  |
|-----------|------|-----------------------|------------------------|
| Prodigi   | 461  | Color matte poster    | Most popular for art   |
| Matte     | 6   | Enhanced matte poster | Printify Choice        |

Verify current IDs at: https://api.printify.com/v1/catalog/blueprints.json

---

## Step 5 — File Quality

Some wall art files are still at 1024×1536px (raw AI output).
Printify needs 300 DPI minimum — for 8×10 that means 2400×3000px.

Upscale files before submitting:
```bash
python tools/upscale_art.py
python tools/printify_publisher.py --queue   # regenerate queue with upscaled dimensions
```

The submit commands automatically use upscaled versions when available.

---

## Step 6 — Submit Products

```bash
# Verify connection
python tools/printify_publisher.py --status

# Submit one product to test
python tools/printify_publisher.py --submit DP1000

# Review in Printify dashboard, then submit all
python tools/printify_publisher.py --submit-all
```

---

## Pricing Model

| Size     | Sell Price | ~Print Cost | ~Profit | ~Margin |
|----------|------------|-------------|---------|---------|
| 8×10 in  | $19.99     | ~$8.00      | ~$9.00  | ~46%    |
| 12×16 in | $27.99     | ~$12.00     | ~$12.00 | ~46%    |
| 18×24 in | $39.99     | ~$18.00     | ~$18.00 | ~47%    |

*Actual Printify costs vary by print provider and destination.*
*Always verify costs in Printify's variant pricing screen before publishing.*

---

## After Submission

1. Open Printify Dashboard → find the new product
2. Review variants and pricing
3. Click Publish to push as a draft Etsy listing
4. In Etsy: open draft → add lifestyle photos → set tags → publish

---

## Revenue Projection (52 art files × 3 sizes)

| Monthly Orders (all sizes) | Monthly Profit | Annual    |
|---------------------------|----------------|-----------|
| 20 orders                 | ~$220          | ~$2,640   |
| 50 orders                 | ~$550          | ~$6,600   |
| 100 orders                | ~$1,100        | ~$13,200  |

**This is a second revenue stream from art already built — zero additional design work.**

---

*OnBrandCraftz — tools/printify_publisher.py*
