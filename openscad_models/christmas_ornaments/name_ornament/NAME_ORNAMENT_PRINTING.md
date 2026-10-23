# Personalised Name Ornament — printing notes

Built 2026-10-21. Scott picked the domed half-bauble (1E) from five ornament
ideas: a smooth dome, flat behind, with the buyer's name and the year inlaid
flush into its face in a second colour.

- **the dome**: 80 mm across, a 3 mm upright band round its edge, rising
  10 mm more to its crown; a loop at the top with a 4.4 mm hole for a hook
  or ribbon;
- **the inlay**: the name in a script face (Dancing Script Bold), the year
  under it, a star above. All three are cut 0.6 mm into the dome, three
  layers, and filled flush, so the face stays one smooth curve.

The maker's mark, OBC, is inlaid in the middle of the flat back, in the
same white as the name, so it costs no extra colour change. It is 5 mm tall
and 17.1 mm wide, mirrored so it reads from behind, with the logo's stripe
as a groove one layer deep across its face.

It measures 80.0 × 88.0 × 13.0 mm with the loop.

`images/` holds renders of the sample ("Olivia", 2026), not photos of a
print:
- `*_colour_*` shows it in its two filament colours.
- `*_as_printed_*` comes from the sliced toolpath.

**Print this:** `name_ornament.3mf`. One object, two parts already aligned.
Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the dome, the band, the loop | red `#C62F3A` |
| inlay | the name, the year, the star, the OBC mark on the back | white `#F4F1EA` |

## Making one for a buyer

The name and year are parameters:

    ./build.sh "Christopher" 2026

This writes `name_ornament_body.stl`, `name_ornament_inlay.stl` and the
union. The name's size follows its length: as large as fits 60 mm across,
at most 13 mm. Names were checked at both ends:

- **"Christopher"** (11 letters) passes `part_mesh` and `product_gate`, with
  the same 2.65 mm 1st-percentile wall as the sample.
- **"Mia"** (3 letters, set at the 13 mm cap) passes both too, with the
  same 2.65 mm wall.

Longer than about 11 letters, the script face gets thin enough to check
again before selling.

## Settings that are not optional

- **Supports OFF.** None is needed: 0 support moves, 0 overhang perimeters.
- **Print it flat, back on the plate, dome up, as it sits in the file.**
  Every face is a top surface or an upright edge, so nothing overhangs.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 28 m** | **6.3 m, 18.7 g** |
| two colour | more: see below | 18.7 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In two colours, every layer that holds white costs a change. The
inlay follows the dome, so the name crosses many layers. Slice in Bambu
Studio for the real purge, or print several on one plate so the changes are
shared.

## Verified before shipping — on the real exported meshes (the sample)

- `tools/part_mesh.py check`: both parts closed, no overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 2.65 mm, median 10.62 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 13.0 mm of 12.99 modelled;
  - 50.7 cm² of bed contact, 72% of the footprint.
- `print_fidelity`: 0.0 mm³ dropped, 0.0 mm³ filled, 0.0 mm³ in the wrong
  colour, rounded to 0.1. The largest entries are two specks of white at
  letter edges, 0.002 mm³ each. **0 flags.**
- `fragility`: 0 high, 0 watch, 0 slender runs.

## What it took

- **The lettering is cleaned as a nozzle draws.** Gaps under 0.85 mm are
  closed and strokes under a bead are opened, the same treatment as the OBC
  mark. A script face's hairlines would otherwise be modelled finer than the
  printer can lay them.
- **The inlay is cut a fixed 0.6 mm into the dome, measured straight
  down,** so it stays three layers deep across the whole curve and sits
  flush with it.
