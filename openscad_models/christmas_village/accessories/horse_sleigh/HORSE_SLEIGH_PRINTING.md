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

PENDING

## Verified before shipping — on the real exported meshes

PENDING

## What it took

PENDING
