# Stone Wishing Well, FACTS (2026-11-15)

Scott picked this (idea 5), then form 1: a classic round stone well with two posts, a peaked
roof, and a crank that raises a bucket.

## Status
- **The windlass test print is ready; the well isn't built yet.** The posts and roof are
  built round the windlass, so the mechanism is tested first (mechanism handbook section 7).
- **Nothing here has been printed.**

## The windlass test (`windlass_test.gcode.3mf`)
- **Settings:** Bambu Studio's own slice, PLA Matte, 0.2 mm layers, supports off, Bambu's
  own speeds.
- **Time and filament:** 46 min 27 s, 17.0 g.
- **Parts:**
  - a stand;
  - three posts (notches: 1 = 0.40, 2 = 0.55, 3 = 0.70), the crank post being the 2-notch
    one with the arm and pin;
  - the axle;
  - the crank wheel (24 teeth, 34 mm across);
  - the pawl;
  - a bucket (15 mm across, 12 tall).
- **Also needed:** about 40 cm of thin twine.
- **Guide:** `Wishing_Well_Windlass_Test_Guide.pdf`.
- **Rebuild:** `make_coupon.sh`. Then `make_images.py` and `make_guide.py`.

## What's calculated and checked (details in ENGINEERING.md)
- **Bucket:** held by a ratchet and gravity pawl, a positive lock. The pawl is
  self-locking: a loaded tooth pulls it in.
- **Clicks:** every 15°, about 1.3 mm of twine per click.
- **The axle's snap:**
  - press in about 17 N, pull out about 63 N (design value);
  - a hard crank (5 N) can't lift it out.
- **The crank wheel:** snaps onto the axle with the Pocket Top's hub joint.
- **Gates:**
  - product gate, all parts pass;
  - print_fidelity, 0 flags;
  - fragility, 0 high;
  - fit check, PASS.

## Not known until Scott prints it
- Which post catch is best.
- Whether the pawl ever slips.
- Whether anything whitens.
- Whether the wheel stays on. That's the same joint as the Pocket Top test.

## Images (`images/`)
Design-review renders, not photos:
- `windlass_plate.png`: the parts;
- `windlass_assembled.png`;
- `windlass_ratchet.png`: from outside the crank side;
- `windlass_cradle.png`: a post's snap bearing.

Not for children under 3: small parts.
