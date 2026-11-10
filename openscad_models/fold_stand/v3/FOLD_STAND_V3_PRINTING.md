# Fold Stand v3: an easel with notches

2026-11-10. v1 (`../fold_stand.scad`) and v2 (`../v2/`) are untouched; this sits
beside them.

**Print the coupon first.** It's the same joints at their real size, on a narrow
stand. If it holds your phone, the full stand is built on exactly those joints.

## Why v3

- v2's pins didn't click.
- The numbers say why. Its ratchet notch was 0.45 mm deep inside a tolerance
  stack of 0.75 mm worst case, so it could never have caught once printed.
- All of that is in `data/knowledge_base/mechanism_engineering_handbook.md`.

You picked option A: a prop whose foot sits in deep notches in the base, like an
easel.

## How it works

Three flat prints. No pins, no screws, and nothing that bends.

- **The plate's round bottom edge** sits in a groove across the base. It rocks
  freely there.
- **The prop's thin end** sits in a pocket on the back of the plate, near the
  middle.
- **The prop's thick end** drops into one of six notches on the base.
  - Each notch is one angle: **80, 75, 70, 65, 60 and 55°**.
  - The dots beside the notches count them: one dot is the steepest.

Your phone's weight pushes the plate back onto the prop, and the prop down into
its notch. Every part is pressed into its seat; nothing has to grip.

- Each seat is 3 to 4 mm deep. That's 10 to 15 times what printing can be off
  by, where the rule is at least 3 times.
- v2's notch was 1.2 times.

The engineering, step by step, is in `ENGINEERING_v3.md`.

## Using it

1. Drop the plate's round edge into the groove, with the shelf facing forward.
2. Put the prop's thin end in the pocket on the back of the plate. Drop its
   thick end into a notch.
3. Stand your phone on the shelf.

**To change the angle:** lift your phone off, move the prop's foot to another
notch, and put the phone back.

**To pack it away:** it's three flat pieces.

## Printing

PLA, 0.2 mm layers, **no supports**. Everything prints as it lies in the files.
Bambu Studio, P1S 0.4, 0.20 mm Standard, PLA Basic:

| print | file | colour | time | filament |
|---|---|---|---|---|
| coupon (print this first) | `fold_stand_v3_coupon.3mf` | one colour | 43 min | 15.5 g |
| base and prop | `fold_stand_v3_base_prop.3mf` | white `#F4F1EA` | 1 h 45 min | 39.6 g |
| plate | `fold_stand_v3_plate.3mf` | lilac `#B79CE0` | 1 h 18 min | 30.9 g |

**How each part prints:**
- **The plate** prints on its back, with the shelf standing up.
  - The pocket opens onto the bed.
  - Its ceiling is a short bridge, 9 mm. A little sag there only moves the
    angle by a tenth of a degree.
- **The prop** prints on its side, so both round ends come out round.

## Testing the coupon

1. **The plate:** it drops into the groove and rocks freely.
2. **The prop:** its thick end drops into each notch, and its thin end into the
   pocket.
3. **The hold:** with your phone on the shelf, try each notch.
   - Tap the screen as you normally would. It shouldn't move.
   - The coupon is only 30 mm wide, so it can rock sideways. The real stand is
     76.
4. **Changing the angle:** lift the phone, move the prop, put the phone back.
   Is it easy?

Tell me what you find before I build anything else on these joints.

## What's calculated, checked and not tested

**Calculated (`stand_v3_calc.py`):**
- every force;
- tipping and sliding with a 250 g phone in a thick case;
- how deep each seat is against what printing can be off by.

**Tipping and sliding:**
- A 1 N touch anywhere on the screen is safe, with a margin of 2.2 or more.
- A firm 2 N press at the very top of the phone doesn't tip it: 1.1.
- On a slick desk that firm press can slide it back a little.
  - It slides; it doesn't fall.
  - Four stick-on rubber feet would stop that if you want them.

**Checked on the exported parts (`check_stand_v3.py`):**
- At all six angles:
  - no part touches another except at the seats;
  - every gap is at least 0.3 mm, the smallest that reliably stays open;
  - the prop's thin end sits in the pocket's corner.
- The plate rocks freely from 54 to 90°.

**Not tested on the printer yet:** all of it. That's what the coupon is for.

## Gates (`checks/`)

**Product gate:**
- The base, the plate and the prop each pass, with 0 support moves.
- The plate first needed supports, under its round bottom edge and under the
  shelf's chin. That edge is now a teardrop underneath, 35° off vertical, and
  the chin leans out at 35°.

**Print fidelity:** 0 flags on all three. Nothing modelled is lost, and nothing
is filled in.

**Fragility:** nothing slender on any part.

## Renders

In `images/`. These are design-review renders of the real parts, not photos.

Rebuild with `./ship_v3.sh`, then `python3 render_stand_v3.py`.
