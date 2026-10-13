# Gift Box Lantern — printing notes

Built 2026-10-13. Scott picked it, with the hex and drum lanterns, from five
lantern forms (`../concepts/lantern_forms.jpg`).

A present with glass sides, tied with a red ribbon and a bow:

- **four glass sides**, each with its own Christmas scene standing out of
  the glass: the Christmas tree with its baubles lit and gifts under it, a
  village with its church, Santa's sleigh and two reindeer crossing the moon,
  and a snowman in falling snow;
- **green corner posts**, a base band and a rail round the top;
- **a lid** tied with a ribbon over the top and down its sides, and a bow of
  four standing loops.

It holds a battery LED tealight: the box has a floor, and the lid lifts off
to reach the switch. A band round the box's mouth fits a groove under the
lid, 0.25 mm clear each side, so the lid sits square and cannot slide off.

Lit from inside, every scene shows dark on the glow: the glass is 1.3 mm,
the scenes stand 1.6 mm out of it, and the thicker plastic passes less
light, the way a lithophane does. It works printed all in white.

It measures 78 × 78 × 103.6 mm with the lid on (box 75.6 × 75.6 × 69, lid
78 × 78 × 39.6 with its bow).

`images/` holds renders of the model: `*_colour_*` in its three filament
colours with the lid on, `*_night*` printed in white and lit by a point light
where the tealight's flame goes, and `*_as_printed_*` from the sliced
toolpath. They are renders, not photos of a print; how dark the scenes read
on a real print depends on the filament and the light.

**Print this:** `gift_box_lantern.3mf`. Two objects on one plate, the box
and the lid, each standing as it prints. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| frame | the box's floor, base band, posts, rail and the band the lid keys onto | green `#2F6B45` |
| glass | the four glass sides | white `#F4F1EA` |
| art | the scenes on the glass | green `#2F6B45` |
| lid | the lid | green `#2F6B45` |
| ribbon | the ribbon and the bow | red `#C62F3A` |

Three filaments. In one colour, white is the one that glows.

## Settings that are not optional

- **Supports OFF.** Neither piece needs any: 0 support moves, 0 overhang
  perimeters, each sliced alone.
- **Print both standing up, as they sit in the file.** The lid prints on its
  underside, bow up.
- 0.2 mm layers.

## Cost — sliced, not estimated

Single colour, supports off, timed with the P1S motion model (the viewer's
clock):

| piece | time | filament |
|---|---|---|
| box | 2 h 30 m | 20.7 m, 62 g |
| lid | 0 h 56 m | 12.4 m, 37 g |
| **together** | **3 h 26 m** | **33.1 m, 99 g** |

In three colours on the AMS, slice in Bambu Studio for the real time and
purge.

## Verified before shipping — on the real exported meshes

- `../lantern_mesh.py check`: every part closed; no two parts of the box,
  or of the lid, overlap; and with the lid set on the box, nothing collides.
- `product_gate` **PASSED** on each piece's one-body union:
  - box: watertight, one body; 1st-percentile wall 1.30 mm against the 1.2
    mm floor; 0 supports; 57 cm² of bed contact, 99.9% of its footprint;
  - lid: watertight, one body; 1st-percentile wall 2.35 mm; 0 supports; 50
    cm² of bed contact, 82%;
  - the gate's uncalibrated risk note gives the lid a 70.5 mm "widest
    unsupported span" at 5.6 mm: that is the groove's ceiling measured round
    its length. Across, it bridges 2.8 mm, and the slicer prints it with no
    support and no overhang perimeter.
- `print_fidelity` (the colour slice compared with the model, layer by
  layer): **0 flags on either piece.** The box loses 0.4 mm³ of 54,754 mm³
  and fills 0.54 mm³, in slivers 0.27 mm wide at the scenes' edges; the lid
  loses nothing.
- `fragility`: 0 high, 0 watch, no slender runs on either piece.

## What it took to print without supports

- **The corner posts** first stood on the base band's bevel, so each
  corner hung over it; they run down to the plate now.
- **The bow's loops** rose from round feet that curled under themselves, and
  their holes peaked at exactly 45 degrees; the loops now rise from flat
  feet, and the holes peak at 60.
- **The scenes** are stepped out of the glass with their undersides climbing
  1.2 per 1 out, after a cleaning pass that drops anything too fine for the
  nozzle (see `../lantern_scenes.scad`).
