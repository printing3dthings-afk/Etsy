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

## 6. Scott's pick: 0.2 (2026-11-13)

He printed the test: "Number 1 again is the best". So every joint is the 0.2 mouth, the
snug one. The hand calculation above flagged its flank gap (0.16) as under the 0.3 rule;
the real print settles it, as the test was meant to.

## 7. The tower (`jar_tower.scad`, `check_tower.py`)

- **Jar:** 64 mm tall, the test's spigot at the bottom and the 0.2 mouth at the top, a
  1.6 mm floor and a 2.4 mm wall. About 153 ml inside.
  - Its inside rises from the floor up the spigot's bore, out along a 35° cone (2.4 mm
    from the seat cone outside), up the wall, and in along another cone to the mouth's
    crests. No ledge anywhere is over air, so it prints standing on its teeth with no
    supports, as the test spigot did.
- **Cap:** a spigot with a closed top and 24 grip grooves round its side. Prints upside
  down. The grooves end in a 37° slope rather than a flat roof: flat, they drew 4,407
  support moves.
- **Foot:** the 0.2 mouth on a skirt that flares 5 mm past the jars at the bed, with a lip
  2 mm tall.
- **Tower:** foot + 4 jars + cap stands 247.7 mm. Fewer jars works the same way.

**Checked on the exported parts (`check_tower.py`, `checks/fit_tower.txt`)**, at each of
jar on jar, jar on foot and cap on jar:
- seated: 0.05 mm short of home nothing touches, 0.1 past the cones overlap;
- held: pulled straight up 1 mm, the teeth hit;
- open gap at the teeth when home: 0.15 mm at the least;
- unscrews: turned back 90° to 720°, it touches nothing.

**Gates, all three parts:** product gate PASS, print fidelity 0 dropped and 0 filled,
fragility 0 slender runs. The wall check needs the thread declared (as on the test), and
on the foot also the band where the skirt meets the thread:
- that band's thin readings are all chords 5.5 to 10 mm long through solid wall, from the
  skirt cone to a thread flank. Their faces are 115° apart, so the gate re-measures each
  along the flank's normal at the groove's edge and gets ~0. Print fidelity on the same
  part drops nothing.

**Mesh fixes on the way (2026-11-13):**
- The jar came out as 7 bodies: a root cylinder 0.01 off the thread's own root, then a
  crest bore that coincided with the thread, both left zero-volume slivers. Both removed.
- The cavity's top cone ended exactly on the mouth's bore edge: coincident faces, an open
  mesh. It now ends 0.1 inside the crests, 0.3 lower.
- Rotating the cap 180° in OpenSCAD broke its mesh; it's flipped in Python instead.

**Slices** (Bambu Studio, P1S 0.4, PLA Basic, standard 0.20, Textured PEI 55 °C, no
supports): see `PRINTING.md`.
