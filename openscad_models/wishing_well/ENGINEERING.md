# Stone Wishing Well: the windlass, engineering (mechanism handbook section 7), 2026-11-15

Scott picked form 1: a round stone well, two posts, a peaked roof, and a crank that raises a
bucket. The well itself (stone ring, roof) waits on this test, because its posts are built
round the windlass.

## 1. Requirement
- **Hold the bucket where it's left:** up to 20 g on a drum of radius 5. That's 0.98 N mm,
  and 2.94 N mm with a factor of 3.
- **Stay in place:** a firm 5 N push on the handle, in any direction, mustn't lift the axle
  out of its posts.
- **Wear:** hundreds of turns. The snaps are pressed in once, or a few times on test.
- **No glue, no hardware.** Just twine for the bucket.

## 2. Concept: a ratchet and gravity pawl; bearings that snap in the print plane
- **Why not plain bearings:** they'd hold 0.30 N mm against the bucket's 0.98, so it would
  unwind.
- **Why not a preloaded snap as a friction brake:** that's section 5 class 3. It holds a
  0.2 % strain, which creeps.
- **So a ratchet with a gravity pawl:** class 4, a positive lock.
- **How each part is printed:**
  - **Posts:** printed flat. Each bearing is a snap: two fingers bend in the print plane,
    along the layers. The Gear Heart's posts bent across the layers and snapped.
  - **Axle:** printed upright, so its journals are drawn in XY and come out round.
  - **Crank wheel:** printed flat, so the teeth are drawn in XY. It goes on the axle's hex
    with the Pocket Top's hub joint (three in-plane beams, reach 0.45), which Scott is
    testing already.
  - **Pawl:** hangs on a T-headed pin. It can only go on, or come off, when it points
    straight up; it works 78° away from that.

## 3. Numbers (`windlass_budget.py` -> `checks/windlass_budget.txt`)

| bearing catch | finger strain | press in | pull out | note |
|---|---|---|---|---|
| 0.40 (1 notch) | 0.76 % | 12 N | 89 N | under the 3×RSS rule (0.52): exploratory |
| **0.55 (2 notches)** | 1.05 % | 17 N | 63 N | the design value |
| 0.70 (3 notches) | 1.34 % | 22 N | 55 N | near the one-time limit (1.4 %) |

- **Fingers:** 1.3 thick, 10.1 long and 8 wide (the post's thickness). The strain shown is
  checked against the one-time limit, because the axle is pressed in once. Every row is over
  the 0.8 % repeated limit, so the test should press each post only a few times.
- **The catch, 0.50 → 0.55:** 0.50 failed the 3×RSS rule by 0.02 (needs 0.52), so the
  design value moved to 0.55.
- **Ratchet:** 24 teeth, 1.6 tall, pitch 4.45, wheel 34 across. The pawl's tip goes 1.25
  deep.
  - The stack between pawl and tooth is 0.95 worst case and 1.15 for 3×RSS: OK.
  - **Why 24 teeth:** 32, with tips sharp enough to print, left the pawl tip and the tooth
    tips under 1.2 mm.
- **Winding:** the full bucket takes 0.10 N at the handle.

## 4. Fit, on the exported parts (`check_windlass.py` -> `checks/fit_windlass.txt`): PASS
- **Seated:** the axle clears all three posts. Lifted 2.4 mm, it meets each catch: the snap
  snaps.
- **The wheel's hub:** it clears the hex. Its nubs press the groove floor by the preload
  (0.14 mm³).
- **The ratchet:**
  - turned 2° clockwise (seen from outside the crank side), a tooth runs into the pawl:
    blocked;
  - **self-locking:** with a tooth pressed in, lifting the pawl makes the overlap worse
    (0.11 → 0.46 mm³), so the load pulls the pawl in, not out;
  - turned the other way, the ramps lift the pawl at most 7.5°, and it clicks every 15°.
- **Which way the twine goes:** the bucket has to pull the way the pawl blocks. So the twine
  leaves the drum on the pawl's side, and winding is anticlockwise seen from outside.
- **The handle:** its full turn clears the pawl, the pin and the post.

## 5. Failure modes
| mode | how likely | what prevents it, or what the test tells us |
|---|---|---|
| bearing finger cracks at its root | medium for 0.70 | in-plane bend, rounded slot ends; the test presses each a few times |
| axle pops out when cranking | low | pull-out 55–89 N against a 5 N crank force |
| won't press in | low for 0.55 | 30° lead-in; 17 N |
| pawl slips under load | low | self-locking geometry (fit check), 1.25 deep against a 0.95 worst-case stack |
| pawl misses teeth when winding fast | medium | gravity only; the test checks for missed clicks |
| wheel pulls off the hex | low | same joint as the Pocket Top: Scott's test passed all three, and he picked 0.45, the value used here (2026-11-15) |
| twine slips on the drum | low | knotted through a cross hole |
| small parts swallowed | certain for the pawl and bucket | "Not for children under 3: small parts" |

## 6. Gates (`checks/`)
- **Product gate:** all eight parts pass.
  - The crank wheel's tooth ring is left out of the wall floor, as thread teeth are. Its tips
    are 1 mm lands, and print_fidelity sees them print.
- **print_fidelity:** 0 flags on the crank post, a far post, the axle, the wheel, the pawl
  and the bucket.
- **fragility:** 0 high. The 3 "watch" notes are the crank wheel's hub beams, which are
  springs by design (slenderness 4.1–5.5).
- **Slice:** Bambu Studio, PLA Matte, Bambu's own speeds: 46 min 27 s, 17.0 g, 0 supports.
  That's over the handbook's 30-minute coupon because the plate tests four joints at once:
  the bearings, the hub, the ratchet and pawl, and the drum.

## 7. What only Scott's test can answer
- Which catch feels right going in and holds when cranked hard.
- Whether the pawl ever slips or misses a tooth.
- Whether the bucket stays up, and whether the wheel stays on.
- Whether anything whitens at the finger roots.
