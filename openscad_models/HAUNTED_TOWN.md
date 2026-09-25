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

## Variety — no two buildings alike (Scott, 2026-09-25)

After the bakery and the first post office: *"these are going to look too
similar."* Same theme, but each building must differ from every other in
**wall texture, window shape and roof shape**. Colour stays one shared town
palette (slate roofs, cream trim); only the wall colour changes. The bakery
is revised to fit too.

Every entry below is chosen because it prints without supports:

| building | walls | windows | roof |
|---|---|---|---|
| Bakery | clapboard (reversed sawtooth — proven) | round with a pointed crown, like its shop window | sagging gable (keep) |
| Post Office | **brick** — short sawtooth courses with staggered vertical joints | **gable-headed**: straight sides under a 60° triangle | **flat, lift-off lid**; one story; no turret |
| Chapel | **stone** — irregular blocks, each with a sheared underside | **pointed lancets** (moved here from the bakery — the most church-like) | steep gable + the tipped bell tower |
| General Store | **board-and-batten** (proven on the gables) | **tall diamonds** with 58° upper edges | false front over a shed roof |
| Schoolhouse | **half-timber** — sheared beams on plain walls, braces at ≥ 50° | **paired narrow slits** with pointed heads | hip roof + bell cupola |
| Undertaker | **fish-scale shingles** — vertical butts, scalloped in the wall plane | **coffin-shaped**, pointed at the top | mansard |

Proposed 2026-09-25 — Scott to confirm or swap any cell.

## The lineup

| # | building | identity feature | status |
|---|---|---|---|
| 6 | **Bakery** | round pie-crust shop window cut into slices, a pie cooling on a crate by the door, crooked BAKERY sign, crooked chimney | built 2026-09-24 (`haunted_bakery.3mf`); **to be revised** to the variety table — its lancets become round-crowned windows |
| 1 | **Post Office** | ONE story, brick, flat lift-off roof, crooked POST OFFICE sign, parcels, mail slot. Plain lettering only — no USPS eagle or logo (their trademark) | **redesign 2026-09-25**. The turret version (`haunted_post_office.*`) was built and gated 2026-09-24 and is superseded: Scott wants one story, a flatter roof, no turret |
| 2 | Chapel | thin bell tower cracked and tipped sideways, one tall pointed window over the door | saved |
| 3 | General Store | false-front facade taller than the building, crooked "MERCANTILE" board, barrels on the porch | saved |
| 4 | Schoolhouse | bell cupola on the ridge, sagging porch roof, oversized stopped clock | saved |
| 5 | Undertaker | narrow and tall between gables, a coffin standing upright against the porch post | saved |

The bakery's measured dimensions become the template for the rest once Scott
has printed it and is happy with it.
