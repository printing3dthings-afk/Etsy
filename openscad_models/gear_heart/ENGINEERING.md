# Gear heart: the mechanism, engineered first

Scott, 2026-11-11, picked 9A of five: "the heart's outline is made of meshing gears, all
of them turning together from a knob in the middle." It moves, so it follows the
mechanism process (`data/knowledge_base/mechanism_engineering_handbook.md`, section
7): the parts are calculated and test-printed **before** the heart is built.

**Status:**
- The test print is ready: `gear_heart_test.3mf`, about 37 min.
- **The heart itself waits for Scott's test results.**

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
