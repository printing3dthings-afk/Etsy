# Haunted General Store — printing notes

Building #3 of the Haunted Town series (`../HAUNTED_TOWN.md`). A board-and-batten
store behind a tall false front that leans forward and to one side. The front
is propped up by two raking timbers, each braced back to the front from its
middle, and carries a crooked MERCANTILE board.
Two barrels stand on the ground beside the door. Behind the front is a steep
tin shed roof with a crooked stove pipe.
Like the others, it is a hollow lantern with an open base, lit from inside by
a battery LED tealight. It measures 88.2 × 76.2 × 124.0 mm including the props.

Built 2026-09-25 to Scott's variety plan: board-and-batten walls, tall diamond
windows, a false front over a shed roof. It shares none of these with the
bakery or the post office.

**Print this:** `haunted_general_store.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | walls, plinth, the leaning false front, battens | sage `#5E6B57` |
| roof | shed roof slab, tin ribs, stove pipe, barrel hoops | slate `#2B2F38` |
| trim | diamond window frames, bars and panes, door frame and door, back corner boards, the sign board, the cap on the front | cream `#EFE6D2` |

**Every window is glazed** (added 2026-09-27). A 1.48 mm pane fills the back
of each opening, set into the wall all round, and the window's bars stand on
it. The tealight glows through the panes, like frosted glass. On the first
chapel print the tallest windows' free-standing bars snapped; the pane is
what carries them now. The door stays open.
| accent | the barrels, the props and their feet, the raised MERCANTILE letters | kraft `#D4A96A` |

**The MERCANTILE letters stand 0.84 mm proud of the sign board** (changed
2026-10-07). They were carved 0.6 mm into it and lined with kraft, but on the
first one-colour print of the post office the carve's stepped ceilings caught
the light and its F's read as E's. Raised, the letters read by their shadow
on a one-colour print; in colour they are kraft letters on cream.
`../sign_test/` has a 20-minute test print of all four town signs.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.** Every underside is at
  least 50° from horizontal in this orientation only.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **9 h 51 m** | **~81 g** | 0 |
| **four colour, AMS** | not reliable here | ~81 g model **+ purge** | **1,317** (before the braces) |

The four-colour print makes about as many changes as the bakery (1,293).
Trim and walls share almost every layer from the plinth to the top of the
front. Purge will again cost more than the house. Slice it in Bambu Studio
for the real flush figure before pricing, as with the other two. A listing
must say which version the buyer gets.

## The tealight

Measured on the exported mesh:
- **47.8 mm clear across from the table up to 50 mm**;
- a 46 mm circle still fits up to **51.1 mm**. Above that, the steep shed
  ceiling comes down toward the back.

The series rule is ≥ 46 mm across and ≥ 50 mm of headroom. An LED tealight
is at most 45 mm tall. The base is open, so the house lifts off to switch
the light.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.38 mm, median 2.71 mm, against the 1.2 mm floor
    (re-run 2026-10-07 with the raised letters);
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (124.0 mm);
  - 11.84 cm² of bed contact (17.6% of the footprint);
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - all four are closed, watertight surfaces;
  - body and roof: **0 zero-area faces**, every edge shared by exactly two
    faces;
  - trim: **0 zero-area faces**;
  - accent: **17 zero-area faces**, all in the letters, where their 0.2 mm
    steps meet. They are slivers of no area, and the slicer handles them:
    the store slices with 0 supports.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- `print_fidelity` (re-run 2026-10-07 with the raised letters): 1 flag, the
  same 0.6 mm batten stub beside the door frame as before. The letters lose
  nothing it flags.
- `fragility` (re-run 2026-10-07): **nothing slender enough to snap. 0 high,
  0 watch.** Before the props were braced they were the town's only two "high"
  members: 2.6 mm square and ~97 mm in one run, slenderness 31, against 17.5
  for the chapel window bar that snapped on Scott's first print.
- The roof part is 5 pieces, the trim 15 and the accent 13. Each piece was
  checked for real surface contact with the part it sits on, sampled by
  area. Every prop foot stands on its own pad on the plate.
- The 3MF round-trips through the slicer with all four parts and all four
  extruders addressed.
- **OBC maker's mark:** engraved 0.8 mm deep under the step: Montserrat
  Black, size 4.6, letter spacing 1.16, 16.2 mm wide. It reads OBC when you
  turn the building over with the front toward you (fixed 2026-09-27: it read
  "ƆBO", and its letters ran together, with 0.39–0.46 mm between them).
- **MERCANTILE letters:** size 5.2, letter spacing 1.06, 51.5 mm wide on
  the 56 mm board, raised 0.84 mm. They are built in five slabs, each keeping
  only what has letter under it all the way down its climb (1.4 up per 1 out
  here, steeper than the other signs for the front's lean, in 0.2 mm steps).
  So only their undersides slope; the holes in the A and R and the letters'
  tops stay as drawn, and they print with no supports.

## Design notes

- **The lean is real geometry.** The false front is sheared 2.5° forward and
  3° sideways. Its windows, door frame and sign are placed on the leaned
  face, so they lean with it. The side walls are clipped to the front's
  inside face and leave no gap.
- **The props are there for the story and for the print.** Two raking
  timbers run from 96 mm up the front, near its outer edges, to feet on the
  ground 20 mm ahead of it. They read as "this front is about to fall". On the plate they
  are plain 50°+ columns.
- **Each prop is 3.2 mm square and braced from its middle** (2026-10-02).
  A brace runs back up to the front at 56° from horizontal, so its underside
  is 34° from vertical. The left brace lands 2.5 mm in from the front's edge,
  which the lean pulls inward. Thickened alone, a prop would have needed to
  be 5.3 mm square to stop being fragile; braced, two shorter runs of 3.2 mm
  are enough and they still read as timbers.
- **The shed roof is one 50° slab.** That is steep enough to print without
  a ceiling. The side view therefore reads as a lean-to rather than a low
  shed. That is the price of no supports and no lift-off lid.
- **The diamond frames are 3.2 mm wide.** The raised frames use the same
  sheared underside as the other buildings. On a 62° diamond arm that shear
  eats about 2.9 mm of height, so a narrower frame left the lower arms under
  one bead (1st-percentile wall 0.68 mm on the first build).
- **The battens stop above each window with a V notch.** That is the sheared
  batten bottom, which the gate needs. It shows in the renders.
