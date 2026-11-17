# Press-to-Light Chapel: the drop test print, FACTS (2026-11-17)

Benson's brief, approved by Scott (2026-11-14): press the steeple and a spinner inside turns
round the tea light, so the light moves. Scott chose lift-and-drop: lift the steeple, let go,
and its weight spins the spinner. No spring.

## Status
- **The test print is ready; the chapel isn't designed yet.** The drive is the risky part, so
  it's tested first (mechanism handbook section 7).
- **Nothing here has been printed.**
- **Battery LED tea lights only** in the chapel itself: a spinning PLA drum near a flame is a
  fire risk.

## The test print
- **Main plate, `drop_coupon.gcode.3mf`:** base, arch, shaft, steeple and the 0.4 mm hub.
  - Bambu Studio, PLA Matte, 0.20 mm layers, Bambu's own speeds, supports off.
  - 57 min 53 s, 24.4 g. The steeple prints solid: it's the weight.
  - **Over the handbook's 30 minutes:** the drop can't be tested without the frame, the shaft
    and a steeple of real weight.
- **Second plate, `drop_coupon_hubs.gcode.3mf`:** the 0.3 and 0.5 mm hubs, 23 min 49 s,
  9.9 g. Printed only if the 0.4 hub binds or rattles.
- **Guide:** `Chapel_Drop_Test_Guide.pdf`.
- **Rebuild:** `drop_coupon.scad`, then `make_coupon.sh`, `run_gates.sh` and
  `make_images.py`.

## What's calculated and checked (details in ENGINEERING.md)
- **The drive, by hand** (`checks/budget.txt`):
  - the helix is 56 deg from level, against friction's 24-29;
  - the weight's torque is 4 times the pivot's drag at worst-case friction;
  - one full driven turn, then a coast.
- **Fit, on the exported parts** (`checks/fit_coupon.txt`):
  - through the whole drop, with the hub turned by the helix, nothing touches, for all three
    hubs;
  - at rest the hub spins free;
  - both stops catch.
- **Product gate:** every part passes. The shaft declares its taper and its pointed tip as
  thin on purpose.
- **Fragility:** 0.

## What isn't known until Scott prints it
- Whether the weight really drives it, and how many turns the hub makes in all.
- Whether the lift always finds the nut, and the stop always lets go.
- Wear after 50 drops.
