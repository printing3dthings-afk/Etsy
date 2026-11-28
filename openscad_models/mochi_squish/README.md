# Dumpling Bun squish (TPU)

Scott, 2026-11-28: five new designs for the public MakerWorld (@P3DT), "something people are
wanting ... something most haven't started 3D printing yet". He picked #5, a TPU squish ("Mochi
Squish"), then form 1 of 5: the **Dumpling Bun**. It's a sibling to our Dumpling Clicker: the same
bao silhouette, at palm size (60 mm across, 34.9 mm tall), in TPU 95A, so it squeezes flat and
springs back.

**Status:** the design passes its checks. Next is the squish coupon, below. The full bun's print
settings wait on Scott's pick.

## Step 1: the squish coupon (`dumpling_squish_coupon.gcode.3mf`)
A TPU squish's feel comes from the slicer's walls and infill, not the shape, so this sets it by
hand first. There are three small buns (36 mm, 0.6 scale), each sliced with its own settings, with
dots in the base so you can tell them apart:

| dots | walls | gyroid infill | feel I expect |
|---|---|---|---|
| 1 | 1 | 5% | softest: squeezes nearly flat |
| 2 | 2 | 10% | medium |
| 3 | 2 | 15% | firmest |

- **Print:** Bambu TPU 95A HF profile, P1S 0.4, 0.20 Standard, textured PEI, no supports.
  58 min, 14.1 g (Bambu Studio 2.9.2's estimate). The settings for each bun are stored in the file.
- **TPU on a P1S:** feed it from the spool holder on the back, **not through the AMS**. Dry it
  first (TPU picks up water: it strings and pops when wet).
- **What to tell me:** which number feels best to squeeze. If it's "softer than 1" or "firmer
  than 3", say so. The full-size bun is softer than a sample at the same settings, because it's
  bigger, and the final profile allows for that.

## The design (`dumpling_bun.scad`, `build.sh`)
- **Body:** the Dumpling Clicker's bao profile, scaled up and solid. The folds are raised (never cut
  in), start 18% up, swirl 45° and gather under a pinched knot.
- **Face:** dimples, since it's one colour. Eyes 2.1 mm deep, a smile 0.9 mm, a 0.6 mm blush.
  Every dimple is hooded: its ceiling rises toward the opening at 56°, so it prints with no support.

## Checks (`checks/`)
- **Product gate** (`gate_bun.txt`): PASS. One body, walls 1st percentile 7.8 mm, 0 support moves,
  0 overhang perimeters, full height.
  - How it got there: at first, the folds stood past the knot as thin fins (0.7 mm walls), the
    knot's underside overhung, and the eye, smile and blush dimples drew support. Each was found on
    the slicer's own toolpath and fixed in the .scad.
- **Print fidelity** (`fidelity_bun.txt`): 0.26 mm³ dropped in all. One flag: a 0.03 mm³ sliver,
  0.23 mm wide, over two layers, where the right eye's hood meets a fold. It's below anything you
  can see or feel, so the face prints as modelled.
- **Full bun slice:** 53 min 49 s, 17.3 g at 2 walls / 10% gyroid, no supports (`bun_2w10.gcode.3mf`).

## Images (`images/`, design-review renders, not photos)
- `bun_front.png`, `bun_three_quarter.png`, `bun_top.png`: the bun.
- `coupon_plate.png`: the three coupon buns.
