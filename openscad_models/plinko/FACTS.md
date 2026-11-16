# Snowfall Plinko (hourglass), FACTS (2026-11-16)

Scott picked form 4: an hourglass Galton board. Flip it and the balls fall back through a
second set of pegs, so there's no reset. It's one print, with the balls inside.

## Status
- **The test print is ready; the board isn't designed yet.** The risky part is balls that
  print loose inside a closed board, so it's tested first (mechanism handbook section 7).
- **Nothing here has been printed.**

## The test print (`plinko_release_test.gcode.3mf`)
- **Settings:** Bambu Studio, PLA Matte, 0.20 mm layers, supports off, Bambu's own speeds.
- **Time and filament:** 24 min 41 s, 11.0 g.
- **What's on it:** one small working hourglass and two pockets, each with 4 teardrop balls
  5 mm across.
- **How each ball meets the floor, marked by notches:**
  - 1 notch (top pocket): its point hangs 0.2 above the floor;
  - 2 notches (the hourglass): it hangs 0.4 above the floor;
  - 3 notches (bottom pocket): its point is printed onto the floor through a 0.6 neck, to
    snap with a toothpick.
- **The front** is a bridged grid with 3.0 openings, too small for a ball.
- **Guide:** `Plinko_Release_Test_Guide.pdf`.
- **Rebuild:** `release_coupon.scad`, then `check_plinko.py` and `make_images.py`.

## What's calculated and checked (details in ENGINEERING.md)
- **Fit PASS:**
  - the floating balls touch nothing;
  - no opening lets a ball out;
  - every gap in the hourglass is either wide enough to pass or too narrow to enter, never
    between, where a ball could wedge;
  - a ball can get from end to end.
- **Air under the balls in the slice:** 0.4 and 0.6 mm. The printer starts each ball a layer
  above its modelled tip.
- **Product gate: one named exception, by Scott's decision (2026-11-16, "Bridge it, one
  print").** The front grid bridges over the balls, and the gate's slicer flags any such
  ceiling. Bambu Studio's slice draws it with bridges and no support. Everything else
  passes.
- **print_fidelity:** 8 flags, each the first layer of a floating ball's point. They are
  narrower than a bead, so the slicer starts a layer higher.
- **Fragility:** 0 high.

## Not known until Scott prints it
- Which balls come free, and how: a shake, a tap or a poke.
- Whether they roll smoothly through the pegs and the neck.
- How the bridged front looks, and whether it sags onto the balls.

## Images (`images/`)
Design-review renders, not photos:
- `release_plate.png`: the print.
- `release_inside.png`: the front taken off, to show the balls and pegs.
- `release_as_printed.png`: rendered from the toolpath.

Not for children under 3: small parts.
