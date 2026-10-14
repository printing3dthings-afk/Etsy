# Victorian Horse Sleigh — printing notes

Built 2026-10-14, a Victorian village accessory. Scott circled it from the
second batch of accessory studies (`../concepts/accessories2_scene.jpg`),
with the condition "if the horse and carriage can't look better then leave
them out". Two standing horses did not look better and it was left out;
asked to try again, this third horse is printed a different way.

A black draught horse in harness pulling a red sleigh of presents through the
snow:

- **the horse**, standing in a walk: a white blaze, white feathered hooves, a
  hanging tail, a green collar, a red girth and red traces along its flanks;
- **the sleigh**, a red cutter with a dash curling up in front, a white rim,
  slate runners that sweep up at the front to meet the traces, a green
  cushion, and four presents with ribbons and bows: white, green, slate, and
  a small green one stacked on the white;
- on an oval of snow with the sleigh banked into it.

The maker's mark, OBC, is engraved 0.8 mm into the underside of the snow,
mirrored so it reads from below.

Assembled it measures 70.0 × 24.8 × 30.8 mm.

## How it is made: the horse prints in halves

A horse printed standing has two things hanging in the air, its belly and its
head held out in front. With no support, the only cure is to tuck the muzzle
into the chest and close the belly into a point, and it stops looking like a
horse (`horse_study.scad`, two attempts, renders in `images/horse_study_*`).

So the horse is split down its spine and each half printed lying on its cut
face. Lying flat, each half is a relief: every surface faces up or out, and
the muzzle, the slim legs, the open belly and the free tail print with no
support. The halves are glued together on two short lengths of 1.75 mm
filament as dowels, and the horse is glued into four shallow sockets in the
snow in front of the sleigh.

The split brings one rule, and it shapes the horse in two places a buyer may
notice: along any line across the horse, the solid has to run unbroken from
the spine out, or that part floats above the plate. So each pair of legs
meets at the middle through a narrow inner edge (from the front, a V between
them), and the ears are joined at the middle all the way up.

## Print this

`victorian_horse_sleigh.3mf`, one plate, three objects:

| object | prints | parts |
|---|---|---|
| sleigh | standing, as it sits in the file | slate runners, posts, a present; green cushion and presents; white snow, rim, presents; red tub and a ribbon |
| horse, near half | lying on its cut face | slate horse; green collar; white blaze and feathers; red girth and trace |
| horse, far half | lying on its cut face | the same, mirrored |

Colours: slate `#2E3440`, green `#2F6B45`, white `#F4F1EA`, red `#A8483A`.

## Settings that are not optional

- **Supports OFF.** No piece needs any: 0 support moves, 0 overhang
  perimeters on all three.
- **Leave the halves lying on their cut faces**, as they sit in the file. Do
  not stand them up.
- 0.2 mm layers.

## Assembly

1. Cut two pieces of 1.75 mm filament 4.6 mm long.
2. Glue them into the two holes in one half's cut face (2.4 mm deep), then
   glue the halves together. Press flat; the cut faces are the alignment.
3. Glue the horse's hooves into the four sockets in the snow (0.6 mm deep).
   They seat with 0.15 mm clearance all round; the traces end just short of
   the runners' sweeps.

Measured on the exported meshes: the standing horse and the sleigh piece do
not overlap anywhere; moved 0.15 mm down the hooves meet the socket floors,
moved 0.15 mm any way sideways they touch nothing.

## Cost — sliced, not estimated

| piece | single colour | filament |
|---|---|---|
| sleigh | 0 h 17 m | 2.0 m, 5.9 g |
| horse, near half | 0 h 4 m | 0.4 m, 1.1 g |
| horse, far half | 0 h 4 m | 0.4 m, 1.1 g |
| **all three** | **0 h 25 m** | **2.8 m, 8.1 g** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). In four colours the colour changes cost far more than the model: the
viewer's colour slices (PrusaSlicer, with a wipe tower, one piece at a time)
run 4 h 28 m and 38.4 g for the sleigh, 1 h 47 m and 13.1 g for the near half
and 1 h 38 m and 12.7 g for the far one. The 3MF puts all three on one plate
so the changes are shared; Bambu Studio's purge differs, so slice it there
for the real number.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part of every piece closed, no two parts
  of one piece overlap.
- `product_gate` on each piece's one-body union:
  - **sleigh: PASSED.** Watertight, one body; 1st-percentile wall 1.30 mm,
    median 3.2 mm; 0 supports, 0 overhang perimeters; 13.1 cm² of bed
    contact, 76% of the footprint.
  - **each horse half: 0 supports, 0 overhang perimeters**, watertight, one
    body, 3.8 cm² of bed contact. Its min_wall reads under the floor (1st
    percentile 0.48 mm). That is the measurement, not the part: rays near
    the outline of a half-dome lying flat cross very little plastic, and
    print_fidelity, which slices the half and compares every layer's beads
    with the model, finds nothing missing (below).
  - **the horse, assembled** (both halves together, as it stands): 1st-
    percentile wall 1.31 mm, median 7.2 mm. Walls are judged here, on the
    object a buyer holds.
- `print_fidelity`, the colour slice compared with the model layer by layer:
  **0 flags on all three pieces.** The sleigh loses 1.5 mm³ of 6,646 mm³, the
  halves 0.26 and 0.86 mm³ of about 1,110 mm³ each; nothing is printed that
  was not modelled, and nothing in the wrong colour.
- `fragility`: **0 high, 0 watch** on every piece and on the assembled horse.
  The longest slender run is the runner sweeps (slenderness 3.7).
- The fit, above: no overlap between horse and sleigh; the hooves seat with
  0.15 mm clearance.

`images/` holds renders: `victorian_horse_sleigh_colour_*` of it assembled
in its four colours, and `hs_*_as_printed_*` of each piece from its sliced
toolpath. They are renders, not photos of a print.

## What it took

- **The horse.** Two standing horses (a boxy one, then a chess-knight one
  that read as a llama) were not good enough to sell; splitting it is what
  made a real horse possible.
- **Legs.** Each leg first touched the spine plane only along a line: it
  stood on a hairline in the print and left zero-width slivers in the other
  half. Each leg now meets the plane through a 1.2 mm edge and stays in its
  own half, and each half carries only its own legs.
- **Thin features** under one bead were thickened: ears (joined at the
  middle), tail tip, the end of the blaze, the traces, and the collar, whose
  lower edge print_fidelity flagged at 0.47 mm.
- **The girth and traces** were first scaled about the origin, and the girth
  ran out to a knife edge under the belly; both are scaled about the barrel's
  middle now, so they stand evenly proud.
- **The sleigh** first asked for 1,439 support moves: the presents and the
  cushion floated 0.1 mm over the tub's floor, the bows hung over the lids'
  edges, the runner tails ran off the snow where the oval narrows, and the
  dash leaned forward over the sides' flare. Each fixed; then the presents
  were moved onto a layer line, because starting mid-layer split one layer
  between red and green and the slicer dropped the red.
- **The runner sweeps** are free at the top; at 1.4 mm thick fragility
  marked them "watch". They are 1.7 mm thick and wider now.
