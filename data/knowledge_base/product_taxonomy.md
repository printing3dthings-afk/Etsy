# Product Taxonomy — Category Reference

Canonical, machine-feedable reference for every product category OnBrandCraftz
sells. Built 2026-08-05 as part of closing the koozie/planner listing-
mismatch bug — before this, category classification lived only as scattered
prose in CLAUDE.md and three separate, disagreeing title-keyword regex
lists (`tools/listing_qc.py`, `tools/order_notifier.py`, and a deleted
`sync_product_catalog.py`). This file is the single source of truth both
`classify_unmapped_listing()` (main.py) and any chat/human question about
"what category is X" should read from.

**How to use this table**: check `is_physical` first (from the raw Etsy
listing's `shipping_profile_id` presence, or `type == "physical"`) — that
alone separates `3d_print_physical`/`sublimation` from every digital
category with zero ambiguity. For digital listings, `taxonomy_id` (if
already set on the live listing) is the next-strongest signal. Only fall
back to title/price/description matching when both of those are
inconclusive, and never guess with low confidence — leave it
`uncategorized` and let a human confirm.

| Category | Prefix | Physical? | Etsy `type` | Typical price | Title/tag pattern | Real examples |
|---|---|---|---|---|---|---|
| `digital_planner` | `DP` | No | `download` | $9.99–$14.99 | "Digital Planner", "GoodNotes", "Instant Download" | DP1026 Ultimate Digital Life Planner, DP1027 Student & School Planner |
| `digital_planner_bundle` | `BUNDLE_PLANNERS` | No | `download` | ~$39.99 | "Bundle", "All \[N\] Planners" | BUNDLE_PLANNERS All 4 Planners Bundle |
| `wall_art` | `DP` (legacy) / `WA` | No | `download` | $1–$24.99 (mostly $4.99–$7.99) | "Printable Wall Art", "Instant Download", art style + subject | DP1008 Mediterranean Lemon Window, DP1009 Amalfi Coast Village Print |
| `wall_art_bundle` | `BUNDLE_` | No | `download` | ~$14.97 | "Set of \[N\]", "Bundle", "Series" | BUNDLE_MED Mediterranean Series — Set of 3 |
| `sticker_pack` | `STICKER_` | No | `download` | $0.99–$7.99 | "Kawaii Sticker Pack", "GoodNotes Elements" | STICKER_DP1026 Kawaii Sticker Pack — Lavender Dreams |
| `sticker_pack_license` | `LICENSE_STICKER_` | No | `download` | ~$12.99 | "Commercial License", references a sticker_pack pid | LICENSE_STICKER_DP1026 |
| `svg_bundle` | `SVG_` | No | `download` | $7.99–$9.99 | "SVG Bundle", theme name, "Cricut", "Silhouette" | SVG_FLORAL Floral Botanical SVG Bundle, SVG_GRAD Graduation 2026 SVG Bundle |
| `svg_bundle_license` | `LICENSE_SVG_` | No | `download` | ~$24.99 | "Commercial License", references an svg_bundle pid | LICENSE_SVG_FLORAL |
| `svg_3dprint_pack` (SS-series) | `SS_` | No | `download` | ~$14.99 | "SVG", "3D Print", contains "SVG" in first 30 chars, ends "Instant Download" — SEE WARNING BELOW | SS_AMERICA_250_SVG America 250 SVG, 10 Patriotic 3D Print Signs |
| `paper_pack` | `PAPER_` | No | `download` | ~$4.99 | "Digital Paper Pack", "Scrapbook", theme name | PAPER_SUNFLOWER_STUDIO_DIGITAL_PAPER_PACK |
| `coloring_pages` | `COLOR` | No | `download` | $1.99–$4.99 | "Coloring Pages", "Coloring Book", "Printable", "Instant Download" | COLOR_KAWAII_COLORING_PAGES_PRINTABLE |
| `sublimation` | `SUBLIM_` | No | `download` | ~$9.99 | "Sublimation", "Tumbler Wrap", "PNG" | SUBLIM_MOM_LIFE Mom Life Tumbler Wrap Sublimation |
| `3d_print_physical` | `P3D_` | **Yes** | `physical` | $8.99–$34.99 | describes a shippable physical object (koozie, holder, lamp, organizer) — NOT "SVG"/"download"/"instant" anywhere in the title | P3D_SLIM_CAN_KOOZIE, P3D_MINIMALIST_PEN_HOLDER, P3D_GEOMETRIC_GLOW_LAMP |
| `uncategorized` | `MISC_` | No (all confirmed digital so far) | `download` | $5.99–$19.98 | fell through classification — needs a human to assign a real category | MISC_BOTANICAL_HERBS_ART_PRINT (should likely be `wall_art`) |

## Two categories that look confusingly similar — read this before guessing

**`svg_3dprint_pack` (SS-series) vs. `3d_print_physical` (P3D-series) is
the single most common misclassification risk**, and is exactly what went
wrong in the 2026-08-05 koozie bug:

- `svg_3dprint_pack` / `SS_*` — a **digital download**: SVG/3MF cut files
  the *buyer* 3D-prints themselves. `type: "download"`, no
  `shipping_profile_id`. Title always contains "SVG" and ends "Instant
  Download" (CLAUDE.md's SS-Series Gate 3). Example: `SS_AMERICA_250_SVG`.
- `3d_print_physical` / `P3D_*` — a **physical product**: OnBrandCraftz
  prints it and ships the actual object. `type: "physical"`, has a real
  `shipping_profile_id`. Title never says "SVG" or "Instant Download."
  Example: `P3D_SLIM_CAN_KOOZIE`.

A listing titled with "Kawaii" + "Koozie" + "SVG" + "3D Print File" is
describing an `svg_3dprint_pack` (a digital cut-file design), but if its
photos show an actual printed physical object, that's the Cardinal Rule
violation to flag, not a hint to classify it as `3d_print_physical` — the
title says download, so trust `type`/`shipping_profile_id` over the
photo when they disagree, and flag the photo mismatch separately (that's
a listing-integrity problem, not a categorization problem).

## `uncategorized` is a known, real gap — not a fallback to trust blindly

13 live catalog entries (all `MISC_*`, all `source: "etsy_sync"`) are
still sitting in `uncategorized` — they fell through the deleted
`sync_product_catalog.py`'s title-regex classifier when it ran once
2026-06-17 and were never manually corrected. Most read like `wall_art`
by title (`MISC_BOTANICAL_HERBS_ART_PRINT`, `MISC_COTTAGECORE_BOTANICAL_
ART_PRINT`) but haven't been confirmed. Treat any listing this table's
classifier resolves to `uncategorized` the same way: don't guess further,
surface it for a human to assign a real category.
