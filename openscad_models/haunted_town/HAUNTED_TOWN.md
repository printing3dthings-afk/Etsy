# Haunted Town — a collectible lantern series

**Square stays (Scott, 2026-09-30):** the Christmas village went round, and
"The Halloween keep square for now." The Haunted Town keeps its square
plans and gables.

## What's in this folder

Everything for the series lives here, one folder per piece (Scott,
2026-09-27: "whole project folders").

| folder | print this | also in it |
|---|---|---|
| `chapel/` | `haunted_chapel.3mf` | `.scad` source, the four part `.stl`s, printing notes, `images/`, `photos/` of the first print |
| `bakery/` | `haunted_bakery.3mf` | `.scad`, part `.stl`s, printing notes, `images/` |
| `post_office/` | `haunted_post_office.3mf` (house and lift-off roof on one plate) | `.scad`, part `.stl`s including the lid, printing notes, `images/`, `photos/` of the first print (2026-10-06, white and painted) |
| `general_store/` | `haunted_general_store.3mf` | `.scad`, part `.stl`s, printing notes, `images/` |
| `schoolhouse/` | `haunted_schoolhouse.3mf` | `.scad`, `build.sh`, part `.stl`s, printing notes, `images/` |
| `undertaker/` | `haunted_undertaker.3mf` | `.scad`, `build.sh`, part `.stl`s, printing notes, `images/` |
| `cemetery/` | `haunted_cemetery.3mf` | `.scad`, part `.stl`s, printing notes, `images/` |
| `manor/` | `haunted_manor.3mf` (one piece, one colour) | `.scad`, `.stl`, printing notes, `images/` |
| `sign_test/` | `haunted_town_sign_test.3mf` (the four shop signs, about 20 min each) | one `.scad` per sign built from the building's own sign modules, their `.stl`s, `SIGN_TEST.md`, a render |

`images/` holds renders of the current model: `*_colour_*` in the four
filament colours, `*_grey_*` in one neutral colour so the relief reads, and
`*_as_printed_*` rendered from the sliced toolpath itself, so they show what
the printer makes rather than what the model says (the post office's is the
house alone: its lift-off roof is a separate object). Each comes as front,
three-quarter and top views. They are renders, not photos of a print;
`chapel/photos/` holds real photos.

The `.scad` files for the chapel, bakery, post office and manor include
`../../lattice_lib.scad`, the shared library one level up in
`openscad_models/`. The manor is the town's first building (Scott,
2026-09-27: "Manor is part of the town"); it came before the shared rules
below and is one colour, not four.

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
- **Hollow lantern, open base, true through-cut windows, glazed.** Every
  framed window has a 1.48 mm pane in the back of the opening, and its bars
  stand on the pane (2026-09-27). A bar left standing free in the opening
  snapped on the first chapel print. The tealight glows through the panes.
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
- **OBC maker's mark** engraved under the step, strokes ≥ 2 extrusions:
  Montserrat Black, size 4.6, letter spacing 1.16, flipped LEFT-TO-RIGHT
  (`mirror([1, 0, 0])`) so it reads OBC with the building turned over, front
  toward you. A top-to-bottom flip looks almost right on O, B and C and
  shipped backwards on every building until 2026-09-27.
- **Signs have raised letters**, 0.84 mm proud (Scott, 2026-10-07). The
  carved, lined letters before them read poorly on the first one-colour print
  of the post office: its F's looked like E's. The letters are built as a
  climb in 0.2 mm steps so only their undersides slope (Technique 81 in
  `.claude/skills/3d-print-design/SKILL.md`). The cemetery's epitaphs stay
  carved (Scott, 2026-10-07: "Leave cemetery the way it is").

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
| 6 | **Bakery** | round pie-crust shop window cut into slices, a pie cooling on a crate by the door, crooked BAKERY sign, crooked chimney | **revised 2026-09-25, awaiting Scott's review** — windows now round with a pointed crown, per the variety plan; `bakery/haunted_bakery.3mf`, notes in `bakery/HAUNTED_BAKERY_PRINTING.md` |
| 1 | **Post Office** | ONE story, brick, sagging parapet, flat lift-off roof with a leaning chimney, crooked POST OFFICE sign, parcels, mail slot. Plain lettering only — no USPS eagle or logo (their trademark) | **built 2026-09-25, awaiting Scott's review** — `post_office/haunted_post_office.3mf`, notes in `post_office/HAUNTED_POST_OFFICE_PRINTING.md`. The two-story turret version (2026-09-24) is archived in `data/trash/` |
| 2 | **Chapel** | stone, a bell tower on the front-left corner cracked above the roofline and tipped 7° away from the nave, one tall pointed window with Y tracery over the door, coped gables, two headstones by the step | **built 2026-09-26, awaiting Scott's review** — `chapel/haunted_chapel.3mf`, notes in `chapel/HAUNTED_CHAPEL_PRINTING.md` |
| 3 | **General Store** | false-front facade taller than the building, leaning forward on two timber props, crooked "MERCANTILE" board, barrels by the door, crooked stove pipe on a tin shed roof | **built 2026-09-25, awaiting Scott's review** — `general_store/haunted_general_store.3mf`, notes in `general_store/HAUNTED_GENERAL_STORE_PRINTING.md` |
| 4 | **Schoolhouse** | one-room school: half-timbered ochre walls, paired pointed windows, a hip roof with a bell cupola and a crooked chimney, a porch on pointed arches under a sagging roof, an oversized clock stopped at 11:47 in a gablet over the porch | **built 2026-10-02, awaiting Scott's review** — Scott picked the one-room school from four forms; `schoolhouse/haunted_schoolhouse.3mf`, notes in `schoolhouse/HAUNTED_SCHOOLHOUSE_PRINTING.md` |
| 5 | **Undertaker** | tall and narrow, squeezed between the bare, broken gable ends of two vanished neighbours (their roof, floor and flue scars still on the walls); fish-scale front and back, coffin windows with crosses, a sagging mansard with a coffin dormer and a crooked chimney, an UNDERTAKER sign, and a coffin standing against the porch post. The town's tallest (160.3 mm) | **built 2026-10-02, awaiting Scott's review** — Scott picked "tall and squeezed" from four forms; `undertaker/haunted_undertaker.3mf`, notes in `undertaker/HAUNTED_UNDERTAKER_PRINTING.md` |
| — | **Manor** | the first building: a tall Victorian house with a turret, gothic windows, a spiderweb rose window over the door, bats cut through the walls, carved jack-o'-lanterns | **built before the series rules** — `manor/haunted_manor.3mf`, notes in `manor/HAUNTED_MANOR_PRINTING.md`. One colour; its window bars are part of the wall, not separate trim |

## Scenery

| piece | what it is | status |
|---|---|---|
| **Cemetery** | a graveyard hill: seven headstones in six shapes with short joke epitaphs (RIP, BOO, BRB, NEXT, OOPS), a dead tree with a crow, three jack-o'-lanterns, a skeleton hand out of a grave, an open grave with a shovel; detail pass adds carved motifs and cracks, stepped bases, a broken iron fence and gate, a twisted-bark tree, bones, a skull, stepping stones, pebbles and grass. Solid ground, not a lantern | **built 2026-09-26, detail pass the same day; awaiting Scott's review** — `cemetery/haunted_cemetery.3mf`, notes in `cemetery/HAUNTED_CEMETERY_PRINTING.md` |

The bakery's measured dimensions become the template for the rest once Scott
has printed it and is happy with it.

## Print checks (2026-09-27)

Every building run through `tools/print_fidelity.py` (does the slice keep the
detail the model shows?) and `tools/fragility.py` (is anything slender enough
to snap in the hand?). Both were calibrated on the chapel Scott printed: it
has no fidelity flags, and the fragility check flags exactly the nine window
bars that snapped on that print, and none once they were glazed.

| building | detail lost (flags) | fragile members |
|---|---|---|
| Chapel | none | none high; the tower's inside corner post is "watch" (an L, it held) |
| Post Office | none | none |
| Bakery | 2: the knife-edge tips of the sagging ridge at each gable | none |
| General Store | 1: a 0.6 mm batten stub beside the door frame, 1.8 mm tall | none since 2026-10-02. The timber props were **2 high** (2.6 mm square, ~97 mm long, slenderness 31 against 17.5 for the bar that snapped); Scott picked the fix, 3.2 mm square and braced from the middle |
| Schoolhouse (2026-10-02) | 3: the ridge cap's knife-edge tip at two points, and one layer at the inside ridge of the ceiling | 1 watch: the finial, slenderness 5.0 |
| Undertaker (2026-10-02) | 4: the ridge cap's knife-edge tip near each gable wall, two scale tips at the back | none |
| Cemetery | 3: the top layer of two spear-point pickets and one finial | 7 watch: tapering branch, shovel and picket tips |
| Manor | none | 16 watch: window bars 13 mm long, ~2 × 2 mm, slenderness 6.4 |

Re-run 2026-10-07 on the bakery, post office, general store and undertaker
after their signs' letters were raised: the same flags as above, none of them
in a sign, and nothing fragile.

Every fidelity flag above was drawn with `--zoom` and is a point or sliver
thinner than one bead. The prints carry essentially all of the modelled
detail.

