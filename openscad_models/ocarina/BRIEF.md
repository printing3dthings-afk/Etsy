# Ocarina: G0 brief (Scott's form A, 2026-11-12)

A 12-hole Alto C transverse ("sweet potato") ocarina, A4 to F6, matte white, OBC mark
underneath. Benson's spec: a real tuned instrument, airtight, walls >= 2.4 mm, no
supports inside the chamber, every hole diameter a variable, and one tuning round
expected after Scott's print is checked against a tuner.

**Status: the voicing test is ready to print. The ocarina itself is not modelled yet,**
by design: its chamber size and every hole size come from the test's measurements.

## How the pitch works (Helmholtz resonator)
An ocarina is a cavity whose note depends on its volume and its total open area, not on
where the holes are:

    f = c / (2 pi) * sqrt(S / V),   S = S_window + sum over open holes of A / (t + k r)

- **c** = 350 m/s (warm breath), **t** = 2.4 mm wall, **V** = chamber volume.
- **S_window**, the voicing window's own term, is set by the window, windway and labium.
- **k**, the end correction on a finger hole, is 1.5 to 1.7 in the literature.

Neither S_window nor k can be known before a real print, so the first print measures
them (below). `ocarina_budget.py` does the arithmetic either way.

## Fingering and targets (`checks/budget.txt`)
- **Order:** the holes open one at a time, from Pure Ocarinas' fingering page:
  1. the two subholes;
  2. right pinky, ring, middle, index;
  3. left ring, middle, index;
  4. the thumbs;
  5. the left pinky last.
- **The table below is targets from the priors, not measurements.**
  - Window term 4.3 mm and k 1.6 give a 68.9 cm3 chamber.
  - The holes come out 1.7 to 9.5 mm.
- **Four holes come out under 3 mm:** the two subholes, right pinky (just: 2.9) and right
  middle. They'll be drawn at 3 mm through a deeper hole (a collar inside the chamber),
  which the budget sizes. Subhole 2's collar would be 7.2 mm, the awkward one.

## Why it prints lying on its side
Found while making the voicing test pass its checks:
- **Stood on its mouthpiece,** the labium edge's first layer is an 8 mm sliver over the
  window. The slicer propped it from the plate, straight up through the windway, which
  would ruin the instrument.
- **On its side,** the labium edge stands upright and is built bead on bead. The windway
  is an upright slot whose roof is only its 1 mm width.
- **Every inside roof is pointed, 37 degrees from upright:**
  - the chamber;
  - the windway;
  - the window;
  - the finger holes, which are teardrops.

  Nothing inside needs support.
- **The window and the labium cut are one arch, peaking over the edge.** Two separate
  slopes left a dip there that the slicer propped.
- **The labium's very tip is thinner than one bead and doesn't print.** The fidelity
  check measured 0.9 mm of it lost, so the edge is drawn 0.9 mm early and lands where it
  should.

## The voicing test (step 5 of the mechanism process: the coupon first)
- **The whistles:** `voicing_whistle_1.3mf` and `voicing_whistle_2.3mf`, about 25 min and
  10 g each.
  - They have the ocarina's exact windway, window and labium, a 6.9 cm3 chamber and two
    teardrop finger holes (5 and 8 mm).
  - They differ only in the windway's height, 1.0 or 1.3 mm. That is the voicing variable
    most likely to matter.
- **What Scott does:** reads three notes per whistle on a tuner (closed, small hole open,
  both open).
- **What the numbers give:**
  - `python3 ocarina_budget.py --coupon F0 F1 F2` turns them into the window term and k,
    and checks the third note against the model's prediction.
  - Then it gives the ocarina's chamber volume and all 12 hole sizes.
- **Predicted with the priors:** about 1387, 1863 and 2521 Hz. The point is to replace
  these with measurements.
- **The cleaner-sounding whistle picks the windway height.**

## Checks on the test (`checks/`)
- **Print fidelity:** nothing filled; the windway stays open.
  - The only flags are the labium tip, as above: 0.9 mm along the air's line, 0.27 mm wide.
  - It's compensated in the model.
- **Fragility:** 0.
- **Min wall:** 1.55 (1st percentile). The labium wedge is declared to the gate as
  deliberately thin.
- **Supports:** Bambu Studio with supports switched on (threshold 45) puts none on the
  whistles; a control slab gets 36.
  - The gate's PrusaSlicer adds 813 support moves around the windway exit.
  - The gate result stands as FAIL for this test print. Details in `checks/slicers.txt`.

## Next, after the readings
1. Run the budget with the measured notes; pick the windway height.
2. Model the ocarina: the sweet-potato form lying on its edge, flat-bottomed where it meets
   the plate; the voicing copied exactly; holes sized by the budget; subhole collars; the
   OBC mark.
3. Full gates, renders, a guide.
4. Scott's tuning print. Measured cents-off per note come back, and the holes move by
   tenths of a millimetre. **v1 is a tuning draft, and its FACTS.md will say so.**
