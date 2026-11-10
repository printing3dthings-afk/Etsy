# Stacking Jar Tower: the engineering, before the model

2026-11-10. This is Scott's pick 1A: jars that screw into one another to make a
single column. It follows `data/knowledge_base/mechanism_engineering_handbook.md`,
section 7.

## 1. The requirement, in numbers

- Four jars, each 72 mm across, plus a cap and a foot.
  - Each jar holds about 150 g: spices, earbuds, SD cards.
- The full tower must lift by its top jar without letting go: 7.7 N on one
  thread.
- It must screw on and off thousands of times without wear that matters.
- It must not seize if it goes on a little crooked.
- The seam between jars should be the same on every print.
- Spice-tight, not airtight: there's no gasket.

## 2. The concept

Each jar's bottom is a threaded spigot, which screws into the mouth of the jar
below.
- Above the spigot, a cone at 35° seats on a matching countersink in the mouth.
  - That cone is the stop and the seal.
  - It sets the seam: the cones meet at the same height whatever the clearance.
- The thread is the gingerbread tin's: 4 mm pitch, 1.2 deep, flanks 35° off
  vertical.
  - Both halves print upright with no supports.
  - The spigot prints standing on its teeth, with a lead-in chamfer at their
    foot.
- **Why a thread and not a bayonet:** the shop's bayonet jar locks at one
  angle. A thread stacks at any angle, and the cone pulls each seam shut.

## 3. Hand calculations (`tools/mechanism_budget.py`)

```
radial clearance 0.2: overlap 1.0, RSS 0.19, worst 0.32, ratio 5.2 -> ok; open gap 0.2 vs 0.3 -> below: may bind
radial clearance 0.3: overlap 0.9, RSS 0.19, worst 0.32, ratio 4.7 -> ok; open gap 0.3 vs 0.3 -> ok
radial clearance 0.4: overlap 0.8, RSS 0.19, worst 0.32, ratio 4.1 -> ok; open gap 0.4 vs 0.3 -> ok
lifting a full 4-jar tower by the top: 7.7 N on one thread; spreading the mouth 10.9 N
tooth root area 959 mm2 x Z-shear ~14 MPa -> strips at ~13.2 kN
```

- **Engagement:** 4 to 5 times the RSS at every clearance, and deeper than the
  worst case.
- **Strength:** the teeth would strip at about 13 kN, against a 7.7 N load.
- **The flank gap** is the clearance × cos 35°: 0.16, 0.25 or 0.33.
  - Only 0.4 clears the 0.3 rule on the flanks.
  - 0.2 is the gingerbread tin's, and it's in the test print as the tight
    variant.

## 4. Failure modes

| how it could fail | likely? | what prevents it |
|---|---|---|
| binds or seizes | medium at 0.2, low at 0.3–0.4 | the test print settles which clearance |
| cross-threads | low | 4 mm pitch, 1.2 deep, a lead-in chamfer; it needs a big tilt to jump a tooth |
| strips | very low | 13 kN against 7.7 N |
| loosens over time | low | the cone seat clamps when tightened; nothing flexes |
| seam differs print to print | low | the cones set it, not the thread run-out |
| spices leak at the seam | low | the cone is a continuous land seal; not airtight |
| mouth splits | very low | 1.9 mm wall outside the thread root; hoop load ~11 N |

## 5. The test print (`jar_tower_coupon.scad`, `jar_tower_thread_test.3mf`)

- One spigot and three mouths, at the real 72 mm.
- The mouths have 0.2, 0.3 and 0.4 clearance: 1, 2 and 3 notches on their rims.
  - The notches are 0.5 deep. At 0.8 they left 1.1 mm between a notch and the
    thread's groove.
  - The flat rim outside the countersink is 1.3 wide. At 1.0 the rim was only
    1.0 thick at its top.
- About 33 min and 13.6 g, with no supports. All four rings pass the product
  gate.
- **Product gate:** the thread's teeth are declared to its wall check, as on the
  gingerbread tin.
  - That's the band from crest to root.
  - A tooth runs from 3.7 mm at its root to a 0.29 mm flat at its crest by
    design.

**What to check:**
1. The spigot screws into each mouth by hand and stops on the cone.
2. Which one feels best: snug, no wobble, no binding.
3. Tug and wiggle it screwed home: it should feel solid.
4. Screw it in starting a little crooked: it should find the thread, not jam.

**Checked on the exported parts (`check_thread_coupon.py`), every mouth:**
- the cones seat: 0.05 mm short of home nothing touches;
- pulled straight up 1 mm, the teeth hold it;
- turned back two full turns, it touches nothing on the way out.

## 6. Next

The full tower, once you've told me which clearance you liked:
- the jars, with the cone seam styled as a reveal line;
- a cap;
- a foot, so the bottom jar doesn't stand on its own teeth.
