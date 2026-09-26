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
  are designed to a **≥ 46 mm circle and ≥ 50 mm of headroom** (60 until
  2026-09-25; lowered for one-story buildings, where the flat roof's seat
  sits at 54–58 mm). Reference
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
| Post Office | **brick** — V-profile courses with staggered vertical joints | **gable-headed**: straight sides under a 60° triangle | **flat, lift-off lid** inside a sagging parapet; one story; no turret |
| Chapel | **stone** — irregular blocks, each with a sheared underside | **pointed lancets** (moved here from the bakery — the most church-like) | steep gable + the tipped bell tower |
| General Store | **board-and-batten** (proven on the gables) | **tall diamonds** with 58° upper edges | false front over a shed roof |
| Schoolhouse | **half-timber** — sheared beams on plain walls, braces at ≥ 50° | **paired narrow slits** with pointed heads | hip roof + bell cupola |
| Undertaker | **fish-scale shingles** — vertical butts, scalloped in the wall plane | **coffin-shaped**, pointed at the top | mansard |

Confirmed by Scott 2026-09-25.

## The lineup

| # | building | identity feature | status |
|---|---|---|---|
| 6 | **Bakery** | round pie-crust shop window cut into slices, a pie cooling on a crate by the door, crooked BAKERY sign, crooked chimney | **revised 2026-09-25, awaiting Scott's review** — windows now round with a pointed crown, per the variety plan; `haunted_bakery.3mf`, notes in `HAUNTED_BAKERY_PRINTING.md` |
| 1 | **Post Office** | ONE story, brick, sagging parapet, flat lift-off roof with a leaning chimney, crooked POST OFFICE sign, parcels, mail slot. Plain lettering only — no USPS eagle or logo (their trademark) | **built 2026-09-25, awaiting Scott's review** — `haunted_post_office.3mf`, notes in `HAUNTED_POST_OFFICE_PRINTING.md`. The two-story turret version (2026-09-24) is archived in `data/trash/` |
| 2 | **Chapel** | stone, a bell tower on the front-left corner cracked above the roofline and tipped 7° away from the nave, one tall pointed window with Y tracery over the door, coped gables, two headstones by the step | **built 2026-09-26, awaiting Scott's review** — `haunted_chapel.3mf`, notes in `HAUNTED_CHAPEL_PRINTING.md` |
| 3 | **General Store** | false-front facade taller than the building, leaning forward on two timber props, crooked "MERCANTILE" board, barrels by the door, crooked stove pipe on a tin shed roof | **built 2026-09-25, awaiting Scott's review** — `haunted_general_store.3mf`, notes in `HAUNTED_GENERAL_STORE_PRINTING.md` |
| 4 | Schoolhouse | bell cupola on the ridge, sagging porch roof, oversized stopped clock | saved |
| 5 | Undertaker | narrow and tall between gables, a coffin standing upright against the porch post | saved |

## Scenery

| piece | what it is | status |
|---|---|---|
| **Cemetery** | a graveyard hill: seven headstones in six shapes with short joke epitaphs (RIP, BOO, BRB, NEXT, OOPS), a dead tree with a crow, three jack-o'-lanterns, a skeleton hand out of a grave, an open grave with a shovel; detail pass adds carved motifs and cracks, stepped bases, a broken iron fence and gate, a twisted-bark tree, bones, a skull, stepping stones, pebbles and grass. Solid ground, not a lantern | **built 2026-09-26, detail pass the same day; awaiting Scott's review** — `haunted_cemetery.3mf`, notes in `HAUNTED_CEMETERY_PRINTING.md` |

The bakery's measured dimensions become the template for the rest once Scott
has printed it and is happy with it.
