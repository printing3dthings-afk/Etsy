# Haunted Town — a collectible lantern series

Agreed with Scott 2026-09-23. One style language across every building so they
stand together on a shelf as one street. The quality bar is two painted
haunted houses Scott showed as reference — **someone else's designs, painted
by Jessee** — so they set the standard only. No shape, proportion or detail is
taken from them.

What those references do that our first haunted manor did not:
- an uneven silhouette that reads at thumbnail size (lean, off-centre tower);
- walls, trim and roof as clearly separate colours;
- a few BIG readable features (round window, curled spire, pumpkins) rather
  than many fine ones;
- something to tell a story with — porch, steps, props.

## Shared rules, every building

- **Sagging ridge** — the ridge dips in the middle, the eaves stay straight.
- **A crooked chimney.**
- **Steep roofs that print without supports** (underside ≤ 45° from vertical
  on anything visible; eaves carried on a 45° flare, never a flat soffit).
- **Printed in AMS colour**: walls / roof / trim / accent as separate parts in
  ONE 3MF (`tools/assemble_3mf.py`). Jessee's hand-painted weathering is an
  optional premium version — a listing must say which one the buyer gets.
- **Hollow lantern, open base, true through-cut windows.**
- **Fits a battery LED tealight.** Clear space inside must take a 38 mm
  diameter × 45 mm tall light with margin: the base opening and the interior
  are designed to a **≥ 46 mm circle and ≥ 60 mm of headroom**. Reference
  sizes found 2026-09-23: Bambu's own LED tealight 37.2 × 36.6 mm; common
  generic ones 36–38 mm across, 32–45 mm tall. The switch is on the light's
  underside, so the house simply lifts off to switch it.
- **Same street**: identical plinth height (8 mm) and ground-floor door height
  on every building so a row lines up.
- **One identity feature per building**, big enough to read in a thumbnail.
- **OBC maker's mark** engraved in the plinth, strokes ≥ 2 extrusions.

## The lineup

| # | building | identity feature | status |
|---|---|---|---|
| 6 | **Bakery** | round pie-crust shop window cut into slices, a pie cooling on a crate by the door, crooked BAKERY sign, crooked chimney | **built 2026-09-24, awaiting Scott's review** — `haunted_bakery.3mf`, notes in `HAUNTED_BAKERY_PRINTING.md` |
| 1 | Post Office | tilted "POST OFFICE" hanging sign, mail slot, parcels leaning on the porch. Plain lettering only — no USPS eagle or logo (their trademark) | saved |
| 2 | Chapel | thin bell tower cracked and tipped sideways, one tall pointed window over the door | saved |
| 3 | General Store | false-front facade taller than the building, crooked "MERCANTILE" board, barrels on the porch | saved |
| 4 | Schoolhouse | bell cupola on the ridge, sagging porch roof, oversized stopped clock | saved |
| 5 | Undertaker | narrow and tall between gables, a coffin standing upright against the porch post | saved |

The bakery's measured dimensions become the template for the rest once Scott
has printed it and is happy with it.
