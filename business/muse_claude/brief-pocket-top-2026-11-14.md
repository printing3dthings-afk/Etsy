# BRIEF — Pocket Top (for Claude, from Benson; approved by Scott 2026-11-14)

## What it is
A snap-together spinning top toy in **3 little parts, no hardware, no supports — under 5 g total and under 10 minutes total print time.** The numbers are the product: it borrows the Mini Bag Clip's trick from the Nov 14 MakerWorld top-liked study (`business/muse_claude/research/2026-11-14-makerworld-top-liked-design-study.md`) — the #15 print on the platform sells itself on "3.6 grams, 8 min" in the title. A print this cheap gets printed on a whim, and whims fill a page with makes, ratings and boosts.

Planned roles: free @P3DT release (free-sync to Patreon + Printables per standing rule), a You Pick the Print candidate (small enough to design/print/reveal inside one week), and a spin-time contest hook — "ours spun 41 seconds" is the comment mechanic, so **spin performance is a design target, not an accident.**

## Design requirements
- **Hard budget:** ≤5 g and ≤10 min TOTAL across all parts on the Standard profile (0.20mm, matte PLA, P1S). If a design decision trades against the budget, the budget wins — say so in FACTS.md when it bites.
- **3 parts max**, snap-together by hand, no glue, no tools. Assembly must be obvious from the parts alone (poka-yoke: parts only fit the right way).
- **Spin target:** ≥30 seconds from a firm finger-twist on a smooth table, stretch goal 45 s. Mass belongs at the rim, not the hub; tip geometry (small radius, hard-wearing point that survives repeated drops) is the critical surface. State the expected spin time and what limits it in FACTS.md.
- **Snap-fit in matte PLA — the known trap.** Matte PLA snaps crack instead of flexing (Gear Heart clip snapped Nov 14; bag-clip successor warns matte PLA loses elasticity). Therefore:
  - **Coupon first:** a snap coupon with at least 3 clearance/stiffness variants of the exact snap geometry, printed and snapped 20× each by Scott before the top is finalised. Use the Fit Test Plate's winning clearances as the starting point.
  - Snap arms oriented so layer lines do NOT run across the flex direction; generous root fillets; no sharp internal corners.
  - If matte PLA cannot pass 20 snaps at any variant, flag it in FACTS.md as a named exception for Scott's call (PETG or PLA+ for the snap part only) — do not silently switch materials.
- **Kid-proofing:** no part small enough to be a choking hazard once assembled; parts must not shatter into sharp fragments when (not if) it's dropped/stepped on — test note for G5.
- Thumbnail test: the assembled top must read as "spinning top" in one glance at MakerWorld thumbnail size.

## Standing OBC gates (unchanged)
- No supports. Flat print orientation per part. Watertight. Walls ≥1.2 mm where structure matters (micro-part walls may go thinner ONLY where the budget forces it — name every exception in FACTS.md).
- Matte PLA, P1S; A1 mini fit expected at this size. Profiles Standard + Optimized built by Benson at G4, stock identities, ASCII filenames.
- Nothing public before G5 (Scott's print + 20-snap coupon pass + a timed spin Scott reports).

## Deliverables from Claude
- Snap coupon: SCAD + exports + FACTS.md (variants labelled, clearances named with sources).
- On coupon pass: full top SCAD + exports + FACTS.md (part masses, total time/weight from your own slice estimate, spin-time expectation) + 5 standard renders, one showing the 3 parts exploded.

Status: G0. Next gate: G1 on the coupon.
