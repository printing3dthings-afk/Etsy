# Crystal Snowflake Ornaments — printing notes

Built 2026-10-21. Scott picked the faceted-crystal form (8E) from five
ornament ideas: thick bevelled snowflakes that catch the light like cut ice,
sturdier than a lace snowflake, which snaps.

A set of six, each its own print and each about 68 × 84 mm with its loop:

| file | design | height |
|---|---|---|
| `crystal_snowflake_1.stl` | **fern**: two pairs of branches on every arm | 6.4 mm |
| `crystal_snowflake_2.stl` | **star**: one pair of branches, a gem at every tip | 6.6 mm |
| `crystal_snowflake_3.stl` | **spear**: one pair of branches, forked tips | 6.4 mm |
| `crystal_snowflake_4.stl` | **plate**: a hexagon ring joining the arms | 6.4 mm |
| `crystal_snowflake_5.stl` | **dendrite**: three pairs of branches | 6.4 mm |
| `crystal_snowflake_6.stl` | **bold**: wide arms, swept branches, gem tips | 7.6 mm |

Every arm and branch is a gabled bar: a flat edge 1.6 mm tall, then two
faces rising at 45° to a ridge down its middle. Where bars cross, their faces
meet in valleys, so the flake reads as cut crystal. The hub is a six-sided
gem with a flat table. A loop at the top tip takes a hook or ribbon (4.4 mm
hole).

The maker's mark, OBC, is engraved 0.8 mm into the gem's flat back, 4 mm
tall and 14 mm wide, mirrored so it reads from behind. It is cut as whole
letters. Unlike the inlaid village pieces, there is no second colour to
fill it, and the logo's stripe ridges would be strips one layer thick.

`images/` holds renders of the models, not photos of a print:
- `*_colour_*` shows the six in ice blue.
- `crystal_snowflake_N_as_printed_*` and `crystal_snowflakes_plate_as_printed_*`
  come from the sliced toolpath.

**Print these:** `crystal_snowflake.3mf` has all six on one plate in one
colour, three across and two deep, 217 × 176 mm. Or print any one STL on its
own.

The first version of this file put the six in a single column 575 mm long,
two thirds of it off the plate: `tools/assemble_3mf.py` could only lay
objects in a row or a column. It wraps them onto shelves now (2026-10-21).

## Settings that are not optional

- **Supports OFF.** None is needed: 0 support moves, 0 overhang perimeters
  on every flake.
- **Print them flat, back on the plate, as they sit in the file.** Every
  face slopes up from a vertical edge, so nothing overhangs.
- 0.2 mm layers. A translucent or silk filament shows the facets best; the
  renders use ice blue `#D8E6F0`.

## Cost — sliced, not estimated

Single colour, supports off, timed with the P1S motion model (the viewer's
clock):

| flake | time | filament |
|---|---|---|
| 1 fern | 0 h 16 m | 1.9 m, 5.6 g |
| 2 star | 0 h 15 m | 2.0 m, 5.9 g |
| 3 spear | 0 h 14 m | 1.7 m, 4.9 g |
| 4 plate | 0 h 16 m | 2.0 m, 5.9 g |
| 5 dendrite | 0 h 16 m | 1.8 m, 5.4 g |
| 6 bold | 0 h 16 m | 2.2 m, 6.5 g |
| **the set** | about 1 h 33 m one at a time | **34.2 g** |

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: each flake closed.
- `product_gate` **PASSED** on all six:
  - watertight, one body;
  - 1st-percentile wall 1.63–1.73 mm against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - full printed height;
  - 15.0–18.9 cm² of bed contact (26–33% of the footprint).
- `print_fidelity`, modelled but not printed:
  - **flakes 1–5:** 0.37–6.49 mm³ of 5,047–6,444 mm³. **0 flags.**
  - **flake 6:** 8.47 mm³ of 7,493 mm³ and **11 flags, explained below.**
- `fragility`: 0 high, 0 watch on all six.

**Flake 6's eleven flags** are the tops of its ridges where the arms meet
the hub. Its arms are 12 mm wide at the foot, so their ridges stand 7.6 mm
high there, the tallest of the set. The last layer of each ridge, for about
1.4 mm along it, is narrower than a bead (0.20–0.27 mm), so the slicer
leaves it off. Each flag is 0.02–0.04 mm³: the ridge ends 0.2 mm lower over
that stretch. Flattening the ridges into tables would remove the flags but
also the crystal look. On a faceted ridge 7 mm tall, the difference does not
show.

## What it took

- **The arms were widened.** At 5.4–8 mm wide with a gentler rise, the first
  versions read as flat lace, not crystal. They are 8–12 mm at the hub now,
  and the faces rise at 45°.
- **The mark's back cut was rebuilt.** As first written, subtracting one
  outline from the other left slivers of no width, and CGAL could not close
  the mesh. It is built from two whole shapes now.
- **The stripe ridges came out.** With the logo's stripes left in, the
  letters' ridges were strips one layer thick across them, and `fragility`
  watched one on every flake. Whole letters cleared all six.
