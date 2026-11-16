# Gear heart: the mechanism, engineered first

Scott, 2026-11-11, picked 9A of five: "the heart's outline is made of meshing gears, all
of them turning together from a knob in the middle." It moves, so it follows the
mechanism process (`data/knowledge_base/mechanism_engineering_handbook.md`, section
7): the parts are calculated and test-printed **before** the heart is built.

**Status:**
- **Test done (2026-11-13):** Scott printed `gear_heart_test.3mf` and picked bar 1,
  "+0.20" on the centre distance ("Number 1"). The heart uses it.
- **The heart is built:** `gear_heart_plate.3mf` and `gear_heart_gears.3mf`, with
  `Gear_Heart_Guide.pdf`. Not printed yet. Section 7.

## 1. Requirement
- **One knob turns them all:** every gear turns together, smoothly, from the knob in
  the middle.
- **Assembly:** the gears press on by hand, no glue or hardware, and stay on when turned
  or brushed: at least 10 N to pull one off.
- **Size:** fits the P1S, and reads as a heart.

## 2. Concept
- **The plate:** a flat heart-shaped backplate carries the gears on posts. The gears ring
  the outline, each meshing with its neighbours.
- **Why an even loop:** a closed loop of gears must be even, or it locks solid.
- **The knob:** the centre gear carries it and meshes with the gear in the heart's top
  dip. The knob is a handle raised on its gear, so it can be any size.
- **Why not print-in-place:** a gear would have to print on top of the plate, and it
  would fuse to it.
- **Instead:** the gears print flat on their own and press onto split snap posts with a
  barb.

## 3. Numbers (`gear_budget.py` → `checks/budget.txt`, `layout.json`)
**Layout.** The heart curve is scaled until the loop of meshing distances closes
exactly (to 0.0000 mm).
- **Gears:** 14 round the heart, alternating 16 and 12 teeth, with a 20-tooth gear in
  the top dip and a 16-tooth gear at the point, plus the 16-tooth centre gear. All
  module 1.5.
- **Size:** about 126 × 116 mm.
- **Clearance:** gears that don't mesh stay at least 2.27 mm apart.
- **How it was found:** a sweep of 288 layouts. The first, with four gears a side, made
  a 95 mm heart with no room in the middle.

**Mesh.** Every centre distance gets +0.30 mm, which gives 0.22 mm of backlash.
- **Error stack:** the errors that could close it are 0.20 RSS and 0.40 worst case, so
  it's free at RSS.
- **Hub play** only opens the mesh: driving pushes the gears apart.

**Snap.** The fit check measured the coupon's real mesh: 0.19 mm of backlash at +0.20,
and 0.27 at +0.40.

| | value | rule |
|---|---|---|
| prongs | 1.6 × 4.0, flat-faced, 13.5 long (the post rises from a pocket 6.5 deep in an 8 mm plate) | |
| strain going on | 1.19 % | ≤ 1.4 % once (over the 0.8 % repeated limit: put on once) |
| slot | 2.54, closes 1.8, 0.74 to spare | ≥ 0.6 spare |
| barb engagement | 0.9 | ≥ 3 × RSS (0.86) and > worst (0.55) |
| push on | about 11 N | |
| pull off | about 14 N (37° underside: holds by friction) | ≥ 10 N |
| hub running gap | 0.35, 0.10 left at worst case | open |

**Six changes before anything printed, each found by a number:**
- **Too few gears.** With four a side, the centre gear overlapped three outline gears;
  six a side gives the 126 mm heart.
- **Barb underside.** At 45° the gate's slicer propped it (10,330 support moves); now
  37°.
- **Post shape.** A round 6 mm post split by a slot left half-round prongs that tapered
  to an edge (min wall 0.58). Now flat-faced rectangular prongs.
- **The taper that wasn't there.** The budget first assumed tapered prongs the model
  didn't draw; drawn straight, they strained 1.7%. The prong length is now set from a
  1.2% target.
- **The barb clipped off.** The prongs' flat faces cut the barb away, so nothing held a
  gear (the fit check caught it). Now the barb has its own footprint.
- **The barb's ledge.** The barb started from the post's circle, not the prong's face,
  which left a 0.6 mm ledge in mid-air (6,389 support moves). Now the slope starts at
  the face.

## 4. Failure modes
| failure | how likely | what prevents it | what the test print shows |
|---|---|---|---|
| teeth bind or catch | low | +0.30 centre distance; meshing checked through two full teeth on the exported parts | does each bar turn smoothly? |
| too much backlash, sloppy | low-medium at +0.40 | two settings on the test | which bar meshes better |
| gear won't press on | low | 11 N; the slot has 0.74 mm to spare | press it on |
| prong cracks going on | low | 1.19 % strain, under the 1.4 % once-only limit | press on, pull off once |
| gear pulls off too easily | low | 14 N | pull it off |
| gear rubs its post | low | 0.35 gap, 0.10 left at worst | spin it |
| supports or droop under the barb | low | 37° underside; 0 support moves in the gate's slice | look under the barb |

## 5. Checks run on the test print (`checks/`)
- **Fit (`check_gears.py`, exported parts in their assembled pose):**
  - nothing overlaps;
  - turned together through two full teeth at their ratio, they never collide;
  - the teeth do touch when one is turned against the other, so they really mesh;
  - backlash 0.19 / 0.27 mm;
  - a gear lifts 0.40 mm before the barb catches;
  - each spins a full circle clear of its bar.
- **Product gate:** pass, 4 bodies, min wall 1.23 mm, 0 support moves.
- **Print fidelity:** 0 flags. The prongs' slots print open.
- **Fragility:** 0 high. The 8 "watch" items are the prongs, which are meant to flex.
- **Bambu Studio:** 36 min 51 s, 9.1 g, no supports.
  - **Over the handbook's 30-minute target:** the posts stand 20 mm tall at their real
    size.

## 6. Next
1. **Scott prints `gear_heart_test.3mf`** and tells me which bar meshes better, and how
   pressing on and pulling off felt (`Gear_Heart_Test_Guide.pdf`).
2. **Then the heart:**
   - the layout in `layout.json` (`images/heart_layout_plan.png`);
   - the chosen backlash;
   - gears with decorative cut-outs, and a heart-shaped knob;
   - the backplate hollowed underneath, so the 8 mm needed for the posts doesn't
     cost a solid slab.
   - **Check:** turning all 15 gears at once, across the whole loop.

## 7. The heart (2026-11-13)

**Centre distance +0.20 (Scott's pick).** The budget's stack (0.20 RSS, 0.40 worst)
calls +0.20 "may bind"; the test print, the real mesh on his P1S, outranks it, and the
budget now says so (`TESTED_OK` in `gear_budget.py`). Each mesh hangs on its own two
posts in one plate, so errors don't add up round the loop. Backlash 0.15 mm.

**The ring's teeth had to close, not just its distances.** Going round a closed ring
of gears, each mesh fixes the next gear's angle. With the bottom gear at the heart
curve's point, the top gear came back 2.10 mm out of phase (pitch 4.71, backlash 0.15):
the last gear couldn't go on, or the ring would lock. The first design check closed
the distances only. Now `gear_budget.py` solves the bottom gear's place on the axis
(1.59 mm up) so the phase error is 0.0000 mm, keeps every non-meshing pair clear, and
writes each gear's phase into `layout.json`.
- The first version of the phase propagation had a sign backwards (the tooth's offset
  from the line of centres). Its own closure check agreed with it, because it copied
  the formula; the geometric check on the real gear shapes found every side mesh
  overlapping by 2 to 6.6 mm2. Fixed; the error at the curve's point is 2.10 with the
  right sign (2.02 with the wrong one).

**Layout.** 14 gears round the heart plus the knob gear, 126.7 x 114.8 mm, scale 3.122.

**Knob.** A round ribbed grip, 18 mm across, with a raised heart on top, on the centre
gear. It stays inside the 9.5 mm the top gear's tips leave (a 24 mm heart knob swept
over them, level with its underside). The post's head needs a 10.7 mm hole: in a heart
knob it broke through the narrow half (min wall 0.83), so the grip is round and the
hole ends in a 37 deg pointed roof. Grip grooves run out through the top (stopped short,
their flat tops drew 6,124 support moves).

**Checks (`checks/`).**
- Fit (`check_heart.py`, on the exported gears and plate, `fit_heart.txt`): the ring
  closes; the knob turned two teeth in 1 deg steps with all 15 gears at their ratios,
  no overlap at any step, smallest tooth gap 0.132 mm; each of the 15 meshes collides
  when turned 1.5 deg against itself (really meshing); non-meshing gears 2.55 mm apart
  at the closest; the knob clears the top gear in 3D; nothing touches the plate.
- Product gate: plate pass (1 body, min wall 1.40); gears pass (15 bodies, min wall 1.30,
  0 support moves).
- Print fidelity: 0 flags on both.
- Fragility: gears 0. Plate 0 high, 20 watch: the posts' prongs, meant to flex (the
  test print's were the same).
- Bambu Studio (PEI plate, 55 C): plate 2 h 15 m, 40.5 g; gears 1 h 49 m, 26.6 g.
  No supports.

**Not checked by printing yet:** the whole heart. The parts that move are the tested
ones (posts, washers, +0.20 meshes); what's new is the layout, the knob and the
heart cut-outs, all checked above on the exported parts.

## 8. Clips v2: the axle pin (2026-11-14, Brief E)

**What failed.** Scott printed the whole heart (2026-11-13): it meshes and turns, but "the
clips the gears go on need to be much stronger", and one post snapped. The posts stood up
out of the plate, so pushing a gear over the barb bent each prong at its root ACROSS the
layers. By `clip_budget.py` (`checks/clip_budget.txt`): 1.19 % strain against about 0.77 %
that PLA holds that way (1.4 % x 0.55): 154 % of it. The fracture was predictable from the
numbers; the test print's posts were the same and survived only because they went on once.

**The change.** A separate pin, printed lying on its side, so its prongs bend in the print
plane, along the layers (`pin_lib.scad`):
- shank a double-D (the 3.5 round with flats 4.8 apart, the faces it prints on), 0.35 a
  side in the gear's unchanged 7.7 bore;
- two prongs either side of a slot that widens 2.4 -> 3.2 from a rounded root, so they
  taper 2.3 -> 1.9 thick, 13.15 long;
- a barb with a square catch (it prints flat, so it hangs over nothing) and a 30 deg
  lead-in. The square catch self-locks: the gear can't be pulled off; pinch the barbs to
  take the pin out;
- a head bar, 10.5 x 4.8 x 2.4, in a pocket in the plate's bed face. It can't turn, so the
  gear turns on the pin, and it can't pull up through the hole. The pocket's roof is
  pitched at 55 deg: flat it drew 1,165 support moves in the gate's slicer, and 45 and 50
  still drew some; 55, 60 and 70 drew none. 55 keeps the ridge 1.6 under the boss top.

| barb | strain (once 1.4 %, repeated 0.8 %) | push-on | engagement (needs 3 x RSS) |
|---|---|---|---|
| 0.45 | 0.78 % ok | 18 N | 2.5 x (under) |
| **0.55** (design) | 0.95 % ok once | 22 N | 3.1 x ok |
| 0.65 | 1.12 % ok once | 26 N | 3.6 x ok |

"Once" is right for this product: a gear goes on once, and a pin comes out only for a
repair. The bosses go to r 7.0 to hold the head's pocket. The gears, washers and +0.20
meshes don't change.

**The test print** (`clip_coupon.scad`, `gear_heart_clip_test.3mf`): one bar with three of
the heart's bosses (8 tall, a washer, the pin's hole and pocket), three pins (barb 0.45,
0.55, 0.65; 1, 2, 3 dimples on the head; 1, 2, 3 grooves on the bar's front edge under the
boss each goes in) and three of the heart's 12-tooth gears. Guide:
`Gear_Heart_Clip_Test_Guide.pdf`.

**Checks (`checks/`).**
- Fit (`check_clip.py`, `fit_clip.txt`, on the exported parts), all three: the pin seats
  touching nothing; the gear on its washer touches nothing; the gear lifted 1.0 hits the
  barbs (2.8 / 3.5 / 4.2 mm3); the pin's head meets the pocket's roof at 0.46 lift (the
  gear's end play 0.81 with AX_PLAY); the gear turned 360 deg about its pin touches nothing.
- Product gate: base pass (min wall 1.23, 0 support moves); gears pass; pins pass with a
  declared band (`--wall-skip-part parts/clip/gate_skip.stl`: the bed and top faces,
  0.3 deep, 5,178 of 28,439 spans). Undeclared, the pins read 1.04 at the 1st percentile:
  the gate's rays skimming the face where the D's round meets its flat, which is the first
  and last layer of a 2.3-thick prong, not a wall. The slice prints it in full.
- Print fidelity (`fidelity_clip.txt`): 0 flags on all three; the pins drop 0.08 mm3, all
  at the 0.17-wide dimples. The barbs' crests print.
- Fragility (`fragility_clip.txt`): 0 high, 0 watch.
- Bambu Studio: 37 min 22 s, 45 layers, 8.75 g, no supports. Over the handbook's 30 min
  because the bosses, pins and gears are the heart's own size.

**Next.** Scott prints it and reports which barb went on and held best and whether any
prong whitened. Then the heart plate gets r 7.0 bosses with `pin_hole()` in place of its
posts, and the pins go on the gears plate.

**Scott's result (2026-11-16).** He printed the clip test (P1S, textured PEI, 36 min, 10 g,
"Success") and reported: "Number 3 seems to feel the best." Clip 3 is the 0.65 barb: 1.12 %
strain, inside the 1.4 % one-time limit and over the 0.8 % repeated one, so a pin goes in
once and comes out only for a repair, as the table above assumes. Whether any prong
whitened isn't reported yet. The heart v2 uses 0.65 (section 9).

## 9. The heart v2: clip-v2 pins (2026-11-16)

**What changed.** The fifteen snap posts are gone. Each gear turns on a clip-v2 axle pin with
the 0.65 barb, Scott's pick from the clip test. In `heart.scad`:
- the bosses are r 7.0 (as on the clip test), each with `pin_hole()` (the 7.7 hole and the
  head's pocket, its roof at 55°) and `pin_washer()`;
- the knob's hole is sized to the pin: r 5.1, round the 0.65 barbs, with the same 37° pointed
  roof above the pin's top;
- the fifteen pins print on the gears plate, lying on their sides in two columns beside the
  gears. Below the gears, the plate was 192 mm deep and Bambu Studio's layout couldn't place it.

The gears, washers, +0.20 meshes, layout and phases are unchanged. The v1 files
(`gear_heart_plate.3mf`, `gear_heart_gears.3mf`) are kept as they were; they carry the
posts that snapped.

**Checks (`checks/`, on the exported parts).**
- Fit (`check_heart.py`, `fit_heart.txt`): PASS.
  - Everything from section 7 still holds: the ring closes, all fifteen gears turn two knob
    teeth with no overlap (smallest gap 0.132), every mesh engages, non-meshing gears stay
    2.55 apart, and the knob clears the top gear.
  - New, the pins: all fifteen seat in the plate touching nothing. No gear touches its pin,
    at rest or turned. Each gear lifted 1.0 hits its pin's barbs (at least 4.17 mm³: held).
- Product gate:
  - plate PASS (0 support moves);
  - gears and pins PASS (30 bodies), with the pins' bed and top faces declared, 0.3 deep
    (`parts/heart_gate_skip.stl`, as on the clip test).
- Print fidelity: plate 0 flags (`fidelity_heart_plate_v2.txt`); gears and pins in
  `fidelity_heart_gears_v2.txt`.
- Fragility: `fragility_heart_v2.txt`.
- Bambu Studio (P1S 0.4, PLA Basic, 0.20 Standard, shop retail settings, textured PEI):
  - plate 1 h 54 m 51 s, 34.78 g (v1 2 h 15 m, 40.5 g: the posts are gone);
  - gears and pins 2 h 19 m 48 s, 33.18 g (v1 1 h 49 m, 26.6 g).

**Not checked by printing yet:** the v2 heart as a whole. Its pin, boss, washer and gear
are the clip test's, which Scott printed. His pick was 0.65, by feel.
