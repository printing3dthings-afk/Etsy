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

## Test result (Scott, 2026-11-16)
- **Whistle 2 sounded better** ("The ocarina test. Number 2 sounded better"). So the
  ocarina's windway is **1.3 mm** high (`WHS[1]`), with everything else as on the whistles.
- **Still needed:** whistle 2's three tuner readings (all covered, small hole open, both
  open). They set the chamber volume and the 12 hole sizes; without them the budget runs on
  priors and the tuning print has further to move.

## Whistle 2's tuner readings (Scott's screen recording, 2026-11-18)
- **The recording has no sound.** An iPhone screen recording leaves the microphone off
  unless it's switched on. The numbers below are read off the tuner app's own display, four
  frames a second.
- **Three steady notes,** each taken as the middle of its readings while it sounded (the
  repeated value the app holds afterwards is left out):

  | order | readings (Hz) | middle | note |
  |---|---|---|---|
  | 1st (8.0–10.5 s) | 1452–1489 | **1472 Hz** | F#6, about -13 cents |
  | 2nd (13.5–15.5 s) | 1923–1999 | **1976 Hz** | B6, about -5 cents |
  | 3rd (16.5–20.0 s) | 1683–1810 | **1768 Hz** | A6, about +11 cents |

  The readings wander ±20 cents within a note, which is breath pressure.

- **Which holes, read from the physics:**
  - The 1st note is the lowest, so it's all closed.
  - The 2nd is the highest and the 3rd is between, but opening a hole can only raise the
    pitch. So the 3rd can't be "both open" after the 2nd.
  - The reading that fits is closed, then the 8 mm hole alone, then the 5 mm hole alone:
    - the 5 mm note gives the window term (4.84 mm) and k (3.17);
    - those then predict the 8 mm hole alone at **1962 Hz, 12 cents from the 1976
      measured.**
  - Read as the guide's order (closed, small, both), the third note misses the model by
    180 cents.
  - **Scott to confirm,** and if he can, one more note with both holes open. The model
    predicts about 2190 Hz.
- **What it means:**
  - **k is about 3.2, twice the literature's 1.5–1.7.** Each hole raises the pitch less
    than assumed. That could be the teardrop holes, or a finger hovering close over an
    open hole, which lowers the note.
  - **With k 3.2, the 12-hole Alto C needs a 77.6 cm3 chamber.** Its three highest holes
    come out too big for a finger:
    - left thumb 14.1 mm;
    - right thumb 17.5 mm;
    - left pinky 10.9 mm.
  - **Not modelled yet, on purpose.** First confirm the readings, then pick the fix:
    1. **Retest with fingers lifted well clear.** If k drops toward 1.6, the holes shrink
       back into range.
    2. **A narrower voicing window.** That lowers the window term, and with it every hole
       and the chamber, at some cost in volume.
    3. **Fewer holes,** a 10-hole range that drops the top notes.
- `python3 ocarina_budget.py --coupon 1472 1768 1976` gives the table above. The middle
  number is the 5 mm hole and the last is the check, so the script's "both" check line
  doesn't apply to this reading.

### Retest, with sound (Scott's second recording, 2026-11-18)
- **Measured from the audio this time,** ten readings a second, each note taken as the
  middle of its steady part:
  - closed **1478 Hz**;
  - then **2125 Hz**;
  - then **1822 Hz**.
- **The same order fits again:** closed, the 8 mm hole, then the 5 mm hole.
- **Each hole fitted on its own:**
  - the 5 mm gives k **2.53**, the 8 mm gives k **2.12**;
  - one k for both is 61 cents off on the 8 mm note;
  - the window term is **4.88 mm**, the same as the first recording (4.84).
- **k fell from 3.2 to 2.1–2.5 with the fingers lifted clear.** So the first recording's
  fingers were pulling the notes down. It's still above the literature's 1.6.
- **What it means for the ocarina:**
  - **At k 2.3 and this window, the chamber is 78 cm3,** and two holes are still too big
    for a finger: left thumb 11.1 mm, right thumb 13.5 mm.
  - **A narrower voicing window fixes it.** Hole size scales with the window term:

    | window term | chamber | largest hole | too big for a finger |
    |---|---|---|---|
    | 4.88 mm (this whistle) | 78 cm3 | 13.5 mm | both thumbs |
    | 4.0 mm | 64 cm3 | 11.4 mm | right thumb |
    | 3.5 mm | 56 cm3 | 10.1 mm | none |

  - **The window term is measured, not drawn.** A narrower window needs one more whistle to
    measure it, with the same windway (1.3 mm, whistle 2) and the window and labium about
    30% narrower. The cost is a slightly quieter instrument.
- **Proposed next print:** that whistle, about 25 min and 10 g, read the same way. Then the
  ocarina is modelled.

### Voicing test v2: a narrower window (Scott: "Yes", 2026-11-19)
- **Why:** with whistle 2's window (term 4.88 mm) the ocarina's thumb holes come out too
  big for a finger. A window term of about 3.5 mm brings every hole under 10.5 mm.
- **`voicing_coupon_v2.scad`, in `v2/`:** two whistles, the same as v1's whistle 2
  (windway 1.3 mm) except the jet's width:
  - **one notch:** 5.6 mm (v1: 8.0), about 30% narrower, aiming at a term of about 3.4;
  - **two notches:** 6.4 mm, about 20% narrower, aiming at about 3.9.
- **Print:** `v2/voicing_whistles_v2.gcode.3mf`, both on one plate, **50 m, 22.8 g**
  (Bambu Studio, 3 walls, 15%). Lying on their sides as they come, no supports.
- **Checks (`v2/checks/`):**
  - **Bambu Studio with supports switched on puts none on either whistle.** The gate's
    PrusaSlicer adds 722 support moves round the windway exit, as on v1 (813). The gate's
    FAIL stands for this test print, for the same reason (`checks/slicers.txt`).
  - **Fidelity:** only the labium tip, the same 0.9 mm as v1, and the model already allows
    for it.
  - **Min wall:** 1.55 mm.
  - **Fragility:** 0.
- **What Scott does:** the same as before. For each whistle:
  - read three notes on the tuner: all closed, the small hole open, then the big hole open;
  - keep his fingers well clear of the open holes;
  - record with the microphone on.
  - Also say which one sounds cleaner.
- **Then:** `ocarina_budget.py --coupon` on each gives its window term and k. The whistle
  that brings every hole under 10.5 mm, and sounds clean, sets the ocarina's voicing.

## Next, after the readings
1. Run the budget with the measured notes; pick the windway height.
2. Model the ocarina: the sweet-potato form lying on its edge, flat-bottomed where it meets
   the plate; the voicing copied exactly; holes sized by the budget; subhole collars; the
   OBC mark.
3. Full gates, renders, a guide.
4. Scott's tuning print. Measured cents-off per note come back, and the holes move by
   tenths of a millimetre. **v1 is a tuning draft, and its FACTS.md will say so.**
