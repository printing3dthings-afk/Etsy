# Haunted Bakery — printing notes

Building #6 of the Haunted Town series (`../HAUNTED_TOWN.md`). It is a hollow
lantern with an open base, lit from inside by a battery LED tealight.
98.7 × 74.3 × 148.8 mm including the chimney, the step and the crate.

**Print this:** `haunted_bakery.3mf`. It is one object with four parts, already
aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | walls, plinth, gables and battens, eave flare, step | plum `#5B4A5E` |
| roof | roof slab, shingles, ridge cap, chimney | slate `#2B2F38` |
| trim | window and door frames, muntins, window panes, door, corner boards, sign board, crate | cream `#EFE6D2` |

**Every window is glazed** (added 2026-09-27). A 1.48 mm pane fills the back
of each opening, set into the wall all round, and the window's bars stand on
it. The tealight glows through the panes, like frosted glass. On the first
chapel print the tallest windows' free-standing bars snapped; the pane is
what carries them now. The door stays open.
| accent | the pie-crust frame round the shop window, the pie, the sign's raised letters | crust `#D4A96A` |

**The BAKERY letters stand 0.84 mm proud of the sign board** (changed
2026-10-07). They were carved 0.6 mm into it and lined with crust colour, but
on the first one-colour print of the post office the carve's stepped ceilings
caught the light and its F's read as E's. Raised, the letters read by their
shadow on a one-colour print; in colour they are crust letters on cream.
`../sign_test/` has a 20-minute test print of all four town signs.

The per-part `.stl` files are what the assembler consumes and what the gates
check. They are not the deliverable.

## No supports, and none of the settings below are optional

- **Supports OFF.** The model is designed to print without them, and it is
  verified: the gate's slicer reports **0 support moves and 0 overhang
  perimeters**. If Bambu Studio's support painting shows anything, it is
  wrong for this part.
- **Print it standing up, the way it is in the file.** Every underside is
  at least 50° from horizontal *in this orientation only*.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament | colour changes |
|---|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **11 h 28 m** | **~113 g** | 0 |
| **four colour, AMS** | not reliable here (see below) | ~120 g model **+ purge** | **1,293** |

The four-colour slice uses all four filaments (selected 545, 409, 239 and 101
times). There are 1,293 tool changes because the trim and the walls
share almost every layer from the plinth to the roof.

**The purge is the real cost of the colour version.** With PrusaSlicer's
140 mm³ flush it came to about 265 g of purge and wipe tower. At the 350 mm³ Bambu
default that `../../LABEL_BIN_PRINTING.md` uses, the flush alone is about **590 g**,
which is five times the house itself. Bambu Studio computes its own flush
volume for each colour pair, so slice it there for the real number. The
slicer's four-extruder time estimate overflowed on an earlier slice of this
house, so no four-colour time is quoted from it. Each of the 1,293 changes costs time on the P1S
as well.

**Recommendation:** treat the single-colour print as the everyday product,
and quote the AMS version from a real Bambu Studio slice before pricing it.
The series rules already allow for a painted premium. The reference houses
were painted by Jessee. A listing must say which version the buyer gets.

## The tealight

Measured on the exported mesh: the largest clear circle about the plan centre
is **52.6 mm across at every height from the table to past 90 mm**. The series
rule is ≥ 46 mm across and ≥ 60 mm of headroom. Any common LED tealight fits:
Bambu's own is 37.2 × 36.6 mm, and generic ones are 36–38 mm across and
32–45 mm tall. The base is open. The light's switch is underneath, so the
house lifts off to switch it.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union:
  - watertight, one body;
  - 1st-percentile wall 1.30 mm against the 1.2 mm floor (re-run
    2026-10-07 with the raised letters; 1.44 with the carved ones);
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (148.8 mm);
  - 12.66 cm² of bed contact (17.3% of the footprint);
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - watertight, consistent winding;
  - body and roof: **0 zero-area faces**, every edge shared by exactly two
    faces;
  - trim: **0 zero-area faces** (12 while the letters were carved);
  - accent: **18 zero-area faces**, all in the raised letters, where their
    0.2 mm steps meet. They are slivers of no area, and the slicer handles
    them: the house slices with 0 supports and 0 overhang perimeters.
- The trim part is 20 separate pieces and the accent part is 8. Each one was
  checked for real surface contact with the part it sits on, sampled by
  area. The sign board shares 489 mm² with the wall, the crate 206 mm², the
  pie 89 mm², and every frame about half its surface.
- **The parts are disjoint.** All six pairwise intersections render EMPTY.
- The union mesh (used only for the gate) carries 108 zero-area faces where
  CGAL welds the roof to the eave.
- The 3MF round-trips through the slicer with all four parts and all four
  extruders addressed.
- **OBC maker's mark:** engraved 0.8 mm deep under the step: Montserrat
  Black, size 4.6, letter spacing 1.16, 16.2 mm wide. It reads OBC when you
  turn the building over with the front toward you (fixed 2026-09-27: it read
  "ƆBO", and its letters ran together, with 0.39–0.46 mm between them).
- **The sign's letters:** raised 0.84 mm (2026-10-07). They are built in
  five slabs, each keeping only what has letter under it all the way down its
  climb (1.2 up per 1 out, in 0.2 mm steps). So only their undersides slope;
  the holes in the A, B and R and the letters' tops stay as drawn, and they
  print with no supports.
- `print_fidelity` (re-run 2026-10-07 with the raised letters): 4.4 mm³ of
  144,986 mm³ is not printed, 0.6 mm³ printed that was not modelled, nothing
  in another colour. **2 flags**, the same as before: the knife-edge tips of
  the sagging ridge cap at each gable, 0.3 mm wide. The letters lose nothing
  it flags.
- `fragility` (2026-10-07): **0 high, 0 watch.**

## What was changed to make it print without supports

The first build needed supports almost everywhere. Every change is measured,
and `.claude/skills/3d-print-design/SKILL.md` Technique 69 records the
numbers.

- **Clapboard is a reversed sawtooth.** Each board ramps out going up and
  steps back on an upward ledge, so it has no ceilings.
- **Shingles are added, not cut.**
- **The roof ends flush at the gables, with no rake overhang.** No rake
  angle printed clean.
- **The inside ridge is level; only the outside sags.** A sagging inside
  ridge drew 12,789 support moves.
- **Corners are 58° or steeper.** Two 50° faces meeting at a corner still
  need support. This is why every window is round with its crown replaced
  by two 58° lines, and the door's head is the same.
- **The pie sits on a crate standing on the ground.** A sill shelf would
  have had a ceiling.
- **Every raised frame, the crust and the sign have a sheared underside and
  a flat top.**
- **The BAKERY letters are raised, with stepped undersides** (2026-10-07).
  They were carved, with stepped 58° ceilings (Technique 76), until the post
  office's one-colour print showed a carve reads poorly in one colour.

## Revised 2026-09-25 for the town's variety plan

Scott asked that no two buildings share a wall texture, a window shape or a
roof shape. Pointed lancets now belong to the chapel. So every bakery window
is **round with a pointed crown**, the shape of its shop window, cut into six
slices by three spokes (the bakery's pies). The door has straight sides under
the same crown. Everything else is unchanged. Re-gated on the new build:
- product_gate passed;
- all four parts clean;
- all six overlaps empty;
- tealight clear circle 52.6 mm.
