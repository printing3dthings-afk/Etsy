# Fold Stand v4: three pieces that stay together and fold flat

2026-11-10. v1, v2 and v3 are untouched; this sits beside them.

**Print the hinge test first.** It's both new joints at their real size, on a short
plate. The guide, `guide/Fold_Stand_v4_Guide.pdf`, covers the hinge test and then the
full stand: putting it together, using it, folding it, and what to tell me.

## Why v4

You printed v3's test piece: "It's good, but it needs to be 3 pieces that connect and
stay together. I want people to be able to fold it down and store it when not in use.
The way it works is good." You chose the prop folding flush into the plate.

## How it works

v3's easel is kept: the same six notches, **80, 75, 70, 65, 60 and 55°**. What's new
is that the three pieces are joined.

- **The prop is hinged to the plate.** It prints inside a slot in the plate, already
  on its hinge: two small cones, one each side. It swings out behind the plate to
  stand in a notch, and folds back flush into the plate. It can't come off.
- **The plate is pinned to the base.** Two side pins sit in two lugs on the base.
  - The pins have flats, and only fit the lugs' slots with the plate tipped forward to
    about 145°, well past upright.
  - Between folded and the steepest notch the pins are 35° or more off that angle, so
    the plate can't come off in use or while folded.
- **Folded,** the prop lies flush in the plate and the plate lies flat on the base:
  34 mm tall, 148 × 87 mm.

The engineering, with the numbers, is in `ENGINEERING_v4.md`.

## Using it

1. With the prop folded in, tip the plate forward to about 145° and lower its pins
   into the lugs' slots. Tilt it back: it's locked on.
2. Swing the prop out and set its foot in a notch.
3. Stand your phone on the shelf.

**To fold it:** lift the prop's foot out, fold the prop into the plate, and lay the
plate down on the base.

## Printing

PLA, 0.2 mm layers, **no supports**. Everything prints as it lies in the files.
Bambu Studio, P1S 0.4, 0.20 mm Standard, PLA Basic:

| print | file | colour | time | filament |
|---|---|---|---|---|
| hinge test (print this first) | `fold_stand_v4_hinge_test.3mf` | one colour | 30 min | 9.8 g |
| base | `fold_stand_v4_base.3mf` | white `#F4F1EA` | 1 h 43 min | 38.1 g |
| plate and prop | `fold_stand_v4_plate.3mf` | lilac `#B79CE0` | 1 h 40 min | 41.6 g |

**How each part prints:**
- **The plate** prints on its back, with the prop inside its slot. The hinge cones'
  undersides are 40° off vertical, so nothing prints over air, and they stand
  0.45 mm clear of the prop.
- **The pins** print on the plate's side edges, on the bed. A 35° flank replaces the
  part of the pin that would have overhung.
- **The lugs' bores** have 35° teardrop flanks up to their slots, so they print too.

## Testing the hinge test

1. **The prop:** push it out from the back. It should swing freely and not come off,
   even wiggled sideways.
2. **Putting it on:** fold the prop in, tip the plate to about 145°, lower its pins
   into the slots.
3. **The pivot:** tilt the plate from flat to upright. It should turn freely and not
   lift out at any angle. Tipped to 145° again, it should lift straight off.

Tell me what you find before you print the full stand.

## What's calculated, checked and not tested

**Calculated (`stand_v4_calc.py`):**
- every force at all six angles, with a 250 g phone in a thick case;
- tipping: a firm 2 N press at the very top of the phone has a margin of 1.4 to 1.6
  (v3 was 1.1);
- how far each joint engages against what printing can be off by: the pivot 4.6
  times, the prop hinge 5.2, the notches 15, where the rule is at least 3.

**Checked on the exported parts (`check_stand_v4.py`, `check_hinge_test.py`):**
- the prop prints 0.40 mm clear of the plate, and swings out untouched from folded to
  4° past the steepest notch;
- at all six angles nothing overlaps, every gap is at least 0.40, and the foot sits
  centred on its notch;
- folded, nothing overlaps;
- the plate turns 0–90° in the lugs, is held from 0 to 85°, and lifts out only at
  145°;
- pushed 1 mm sideways, a cone stops the prop.

**Not tested on the printer yet:** both new joints. That's what the hinge test is for.

## Gates (`checks/`)

- **Product gate:** the base, the plate (two bodies: plate and prop), and both
  hinge-test parts pass, with 0 support moves.
- **Print fidelity:** 0 flags on the base and the plate.
- **Fragility:** nothing slender on either.

## Renders

In `images/`, and the guide's own in `guide/images/`. These are design-review renders
of the real parts, not photos.

Check with `python3 check_stand_v4.py` and `python3 check_hinge_test.py`. Render with
`python3 render_stand_v4.py`, then build the guide with `python3 guide/make_guide.py`.
