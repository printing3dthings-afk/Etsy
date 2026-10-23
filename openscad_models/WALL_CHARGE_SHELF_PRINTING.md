# Wall Charging Shelf — printing notes

One part, one print, no supports, no brim.

| | |
|---|---|
| on the wall | 120 wide × 90 tall × 65 deep mm |
| on the plate | 120 × 90 footprint, 65 mm tall (prints back-flat) |
| time | **3h 25m** |
| filament | **59.0 g** |
| supports | **none** — 0.00 cm² past 55°, worst face 49.1° |
| brim | none — the first layer is a 120 × 90 plate |

Sliced with `tools/p1s_slice_profile.ini` as it stands on 2026-09-10. That
profile changed during this build; see "The slicer profile was lying" below.

## Print it back-flat

The back plate goes on the bed and the shelf grows upward, so the build
direction is the shelf's own DEPTH. That single choice is what makes the whole
thing support-free:

- the deck, both side panels and the back plate are all walls standing on the
  bed — none of them overhangs anything
- the bracket's concave free edge rises monotonically in both axes, so its
  surface is up-facing along its entire length. A convex bulge in the same
  place would not be
- the two features that *can* overhang are shaped for it: the front lip's
  underside is a 39° ramp (a conventional thin lip would be a 73° overhang),
  and the deck's plug slot ends in a 45° peak rather than a flat 24 mm bridge

Every visible surface — deck top, side rails, front lip, the outside of both
brackets — prints as a side wall, which is the best finish this printer gives.
The only bed-textured face is the back, against the wall.

## Mounting: screws. Not adhesive.

Two keyholes at the top for **#6 or #8 screws** into studs or drywall anchors,
and one plain countersunk hole at the bottom centre for an anti-lift screw.
Hang on the two top screws, then drive the bottom one.

- head recess Ø9 × 3.2 mm deep, opening on the wall side, so the plate still
  sits flat against the wall with the screw heads captured behind it
- shank slot Ø4.6, 9 mm of drop
- the step between them is a 45° cone, not a flat ledge, so it needs no bridge
- 2.8 mm of solid skin in front of the head recess is what actually carries the
  load

**Adhesive strips are not supported and the design does not pretend to be.**
The original pitch said "screw or command strip"; that half is withdrawn. A
65 mm cantilever holding a phone loads a strip in peel at its top edge, which
is the direction those strips are worst at and which 3M's own guidance
excludes shelves for. A mount that fails slowly and drops a phone is not
something to sell to strangers.

**It does not hang on the outlet's cover screw either.** Outlet plates vary,
and that screw holds a live electrical fixture.

## The bracket is a hex lattice, and every cell is a whole one

Technique 46's rule is that a bracket gusset is never a solid flat triangle —
either taper the web to the load path, or through-cut the interior as a hex
lattice inside a solid perimeter frame. This is the lattice version, because
the load is spread along the deck and the bracket is meant to be seen.

The cells are placed only where a whole cell fits. The obvious construction —
intersect an infinite hex field with the region — renders, gates and slices
perfectly well and looks wrong: a cell clipped by the boundary leaves a
tapering needle of material beside its neighbour. Measured on the first build,
those needles were 1.26–1.68 mm wide, so nothing flagged them; they are
entirely printable, they just read as a mistake. Testing each cell's six real
vertices against the outline removes them, and the solid frame is then whatever
is left over rather than a separate inset shape. Where the bracket narrows
toward its root, no cell fits and it goes solid on its own — which is also
where the material belongs.

**The two lattices are different cells on purpose.** The back plate's cells are
cut along the build axis, so they are plain vertical holes and can be regular
hexagons. The side panels' cells are cut *across* it, so each cell's roof is a
real overhang, and a regular pointy-up hexagon puts its top edges at 60° —
past what the P1S holds. Stretching the cell 1.5× along the build axis brings
them to a measured 49.1°. Sized to the real 55° limit with margin rather than
to 45°, which is what keeps the cell at 1.7:1 instead of a squashed 2.2:1.

Each opening in the back plate gets a 0.6 mm 45° lead-in on the room-facing
side. Every current phone is wide enough (>54 mm) to rest on the two mounting
bosses and never touch the lattice, but anything narrower would lean on fifty
raw cut edges.

## Cable

One slot through the deck, 24 mm wide, starting 8 mm out from the wall and
running 24 mm with a peaked end. The cord comes down from the outlet, through
the slot, and up into the phone's bottom port. It deliberately does not open to
the back edge: the deck's root at the wall is where the bending moment is
highest and it stays solid.

## Wall thicknesses

All whole numbers of 0.42 mm extrusions, per the label bin's finding that
1.6 mm sliced 48 minutes slower than 1.68 mm on less material.

| | |
|---|---|
| back plate | 2.52 (6) |
| deck | 2.94 (7) |
| side panels and rails | 3.36 (8) |
| lattice rib | 1.68 (4) |

The slice contains **zero gap fill**, which is the check that says no region
ended up thinner than the slicer could lay down cleanly.

## Maker's mark

Engraved into the front face of the lip — the top surface as printed, so it is
the crispest engraving this part can carry, and the face you look at on a wall.
Measured 1.94 mm on the thinnest stroke, 4.61 extrusions, against the ≥2 floor.

Sized to that face's own 10.94 mm height rather than to 40% of the 120 mm run:
the short dimension binds first here, and 40% of 120 would need an 11 mm cap
height that does not fit.

## The slicer profile was lying

`tools/p1s_slice_profile.ini` never set `solid_infill_speed`,
`top_solid_infill_speed` or `small_perimeter_speed`, so PrusaSlicer's own stock
defaults ran them: **20, 15 and 15 mm/s**. Measured in this shelf's own g-code:
27,840 solid-infill moves at 20 mm/s, and over 39,000 perimeter moves that fell
to 15 because every hex lattice cell is a "small" loop. Solid infill alone was
37% of the print.

Set to 200 / 80 / 50. This shelf went **5h 20m → 3h 22m on identical filament**,
and the label bin family dropped 35–40% across all four sizes. Nothing a
customer sees got faster: `small_perimeter_speed` is pinned to the same 50 mm/s
the outer wall already uses, so CLAUDE.md's "outer wall 50 mm/s or lower"
production rule still holds on every visible surface.

Identical filament weight before and after is the check that says a speed
change and nothing else happened.
