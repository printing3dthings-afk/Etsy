# Victorian Steam Train — printing notes

Built 2026-10-14, a Victorian village accessory from the second batch of
accessory studies (`../concepts/accessories2_scene.jpg`).

A little tank engine and one carriage on a snowy track, all one print:

- **the engine**: a green boiler with two white bands and a white dome, a
  slate smokebox with **a green wreath and red bow** on its door, a slate
  chimney, a green cab with a slate roof and windows cut into it, a red
  bunker heaped with coal, all on a red frame with **six slate wheels**;
- **the carriage**: red, **four lit windows** a side (white panes behind
  pointed openings), a slate roof, on four wheels;
- **snow** along both roofs;
- **slate rails on red sleepers**, on a long blob of snow with two drifts.

The maker's mark, OBC, is inlaid in slate into the underside: the logo's
letters, 5 mm tall and 17.1 mm wide, cut 0.6 mm into the white and filled
flush, mirrored so they read from below. A groove one layer deep crosses
their face, the stripes of the logo.

It measures 64.0 × 26.0 × 25.4 mm.

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_steam_train.3mf`. One object with four parts,
already aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | the frames, the carriage, the bunker, the sleepers, the bow | brick red `#A8483A` |
| roof | wheels, smokebox, chimney, coal, roofs, rails, the OBC mark inlaid underneath | slate `#2E3440` |
| trim | the snow, the bands, the dome, the hubs, the window panes | white `#F4F1EA` |
| accent | the boiler, the cab, the wreath | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing on its base, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 21 m** | **2.9 m, 8.5 g** |
| four colour | see below | 8.5 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In colour, the colour changes cost far more than the model: the
viewer's colour slice (PrusaSlicer, with a wipe tower, 225 changes) runs
6 h 40 m and 55.8 g. Bambu Studio's purge differs; slice there for the real
number, or print several on one plate so the changes are shared.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.36 mm, median 9.60 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 25.4 mm of 25.37 modelled;
  - 15.1 cm² of bed contact, 91% of the footprint; centre of mass over it.
- `print_fidelity`: 0.44 mm³ of 12,939 mm³ not printed, 0.11 mm³ printed
  that was not modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: 0 high, 0 watch. The one slender run is the chimney,
  slenderness 2.1.

## What it took to print without supports

- **The boiler and smokebox** are horizontal cylinders. Each is sunk into
  the frame as far as the line where its curve turns 45°, so all of the
  curve that shows climbs within the limit.
- **The wheels** are discs on the frame's sides, sunk in the rails until
  their curve leaves them at 42°. The footplate steps out over them at
  1.2 per 1.
- **The footplate's edge** first stepped out to a knife edge, a sliver
  0.1 mm thick all along the boiler; it is 0.8 mm thick now.
- **The roofs** step out 0.8 mm all round at 1.2 per 1, their corners
  rounded so a corner climbs as a side does, then rise to an arched ridge.
  Their eaves were 0.4 mm and read under one bead; they are 0.9.
- **The snow** on each roof is a tent from partway up the roof to above the
  ridge, so it thickens toward the ridge and faces up everywhere.
- **The windows** are cut in with sloping heads; the carriage's white panes
  sit behind the cut. The cab is solid, so its roof spans nothing.
- **The chimney's cap** flares out at the climb; at 0.8 mm its rim was under
  one bead, and it is 1.2 now. **The boiler bands** were 0.9 mm wide, the
  same; they are 1.3.
- **Layer lines.** The frames, rails and sleepers started 0.3 mm under the
  snow's top, mid-layer: that layer split between white and the part's
  colour, and the slicer dropped the white under all fifteen places
  (print_fidelity flagged each). They start on a layer line now. The last
  sleeper at the carriage end was clipped by the base's rounded end into a
  sliver; the sleepers stay inside it.
