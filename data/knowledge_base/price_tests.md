# Price Test Log

Append-only log of every price change made to an existing ranked listing, per
CLAUDE.md's pricing rule (never change price on a listing in its first 30 days;
after 30+ days, test in $1-2 increments and wait 3-4 weeks before changing again).
Each entry records the baseline metrics at the time of the change so the test can
be judged on real before/after data.

---

### 2026-06-17 — Crystal Glow Lamp (listing 4488477854), $34.99 -> $32.99
**Listing:** "Crystal Glow Lamp, 3D Printed Faceted RGB Table Lamp, Unique Gift"
**Age at time of change:** 63 days (created 2026-04-14) — well past the 30-day
minimum before a price test is allowed.
**Baseline metrics (pre-change):** 117 views, 4 favorers, 0 sales.
**Change:** $2.00 decrement (the CLAUDE.md-compliant max single-step size),
applied via the Etsy inventory PUT endpoint (`listings/{id}/inventory`) since
this listing's price lives on its single offering, not the top-level listing
PATCH field.
**Next review:** 2026-07-08 to 2026-07-15 (3-4 weeks out). Compare views,
favorers, and sales against baseline. Do not touch this listing's price again
before that window closes.
