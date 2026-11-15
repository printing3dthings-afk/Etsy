# Pie Drum Caddy: the engineering, before the model

2026-11-10. This is Scott's pick 4B: a round drum split into wells of different
heights, turning on a ball bearing. It follows the handbook's section 7.

## 1. The requirement, in numbers

- A drum about 150 mm across, with wells 60–110 mm tall. It holds up to 1 kg of
  pens, scissors, tape and rulers.
- It should turn smoothly with a finger and not wobble.
- It should lift off its base for cleaning.
- No supports anywhere you can see, and no hardware beyond the balls.

## 2. The concept: a thrust bearing on 6 mm airsoft BBs

- **The balls** run in a channel in the base, 0.3 clear each side.
  - Underneath them is the channel's floor. That's a top surface, so it can
    be ironed smooth.
  - Above them is the drum's underside. It prints on the bed, so it's the
    smoothest surface the printer makes.
- **A post** in the middle keeps the drum centred.
- **Nothing holds it down,** so it just lifts off.
- **Why this over a V-groove race:**
  - A V-groove's sloped sides print as stair-steps, and the balls would rumble
    over them.
  - Flat-on-flat puts the balls on the two smoothest surfaces there are.
- **Why the balls aren't held in a cage:**
  - With 10% of the ring left empty they can't jam.
  - At a desk caddy's speed, balls rubbing each other cost almost nothing.
  - A cage is an extra part. It goes in only if the test print says so.

## 3. Hand calculations

```
1 kg over ~20 balls: 0.49 N each; contact radius 0.095 mm, peak pressure 26 MPa (PLA compressive yield ~60+)
ball 6.0 in a channel 6.6 wide: 0.3 each side; drum floats 2.0 above the base rim (gap >= 0.3)
coupon: ball circle r 30: 31 balls touching, use 27 (10% slack so they can't jam)
caddy: ball circle r 50: 52 balls touching, use 46 (10% slack so they can't jam)
centre post: 0.4 radial gap; post height into the bore 8 mm, RSS 0.18
```

- **Contact pressure:** 26 MPa, under half of PLA's yield.
  - Airsoft BBs are plastic, so both surfaces give a little and the pressure
    stays low.
  - 6 mm steel balls would also work, at a higher contact pressure. They'd be
    louder and cost more.
- **The post's bore** is drawn 0.15 larger on the radius, because vertical holes
  print small. That leaves a 0.4 gap, and 0.55 as drawn.

## 4. Failure modes

| how it could fail | likely? | what prevents it |
|---|---|---|
| rough or noisy | medium | the balls roll on an ironed floor and the bed face; the test print tells |
| balls jam | low | 10% of the ring left empty; 0.3 each side in the channel |
| drum wobbles | low | balls all round the ring; a warp of 0.2 tilts it 0.1° |
| drum rubs the base | very low | it floats 2.0 over the rim |
| tips when you grab a tall tool | low | the full drum sits low, with the ball ring 100 mm across |
| wears ruts | low | 26 MPa against PLA's ~60 |
| balls spill out when you lift the drum | certain, harmless | they stay in the channel unless the base is tipped; a pinch of 46 BBs |

## 5. The test print (`bearing_coupon.scad`, `pie_caddy_bearing_test.3mf`)

- The real channel and post, at 80 mm across.
- It needs 27 airsoft BBs, 6 mm. Any brand will do: a bag of thousands is a
  few dollars.
- About 50 min and 19 g, with no supports. Both parts pass the product gate.
  - That's over the 30-minute target: the 80 mm base is most of it.
  - Hollowing its middle didn't shorten it, so it stays a real-size channel
    rather than a smaller one that wouldn't test the same thing.

**What to check:**
1. Drop the BBs into the channel, then set the top on.
2. Put a mug on it: it should spin with a flick and coast.
3. Listen: quiet, or does it rumble?
4. Does the top wobble?

**Checked on the exported parts (`check_bearing_coupon.py`):**
- nothing touches;
- the balls clear the channel's walls by 0.29 each side;
- the top floats 2.0 over the base, and clears the post by 0.55.

## 6. Next

The pie drum itself, at 150 mm with a 120 mm bearing, once the test print spins
well. **It did (section 8): the drum is unblocked.**

## 7. Printed balls instead of airsoft BBs (2026-11-12)

Scott asked to print the 6 mm balls (`printed_bb.scad`, `printed_bbs_fine_0.12mm.gcode.3mf`,
`Printed_BB_Guide.pdf`).
- **30 balls, 6.0 mm**, each standing on a flat 0.4 mm deep, 3.0 mm across. A full
  sphere's lowest layers would step out past the one below and sag; above this flat the
  steps are 0.30, 0.28, 0.16 mm, under one 0.42 bead.
- **Sliced at 0.12 mm layers:** 29 min 7 s and 4.19 g on Bambu Studio, no supports
  (0.2 mm: 16 min 52 s without a brim, rounder at 0.12).
- **Brim, 3 mm, outside only, 0.1 mm gap** (Scott: "use a brim if needed"). It was:
  Bambu's auto brim added none, and a ball holds the plate by a 3 mm flat, about 7 mm².
  The brim makes it a 9 mm ring, about 64 mm² (`images/printed_bbs_first_layer_brim.png`).
  `tools/bambu_slice.py --brim 3 --bed textured`: bed 55 C. The first brim slice had no
  plate type set and Bambu Studio fell back to its Cool Plate at 35 C; fixed before printing. The viewer entry and the checks are the check slice,
  without the brim.
- **Checks:** product gate PASS (30 bodies, 0 support moves), print fidelity 0 misses,
  fragility 0.
- **Size:** about 6.1 mm across as sliced (outer-wall extent plus one bead), in the
  6.6 mm channel: 0.2 or more each side.
- **What they cost against airsoft BBs**, which are round to a few hundredths:
  - the flat: a ball lying on it is 5.6 tall and carries nothing until it rolls off;
  - the layer seam up one side, which is the main bump (sanding takes it down);
  - layer rings, 0.12 mm.
  So this run tests printed balls as much as the bearing. If it rumbles, try airsoft
  BBs before blaming the channel.

## 8. Scott's test result (2026-11-15): it works

Scott, 2026-11-15: "6mm bb's worked. When I print the actual I'll use real bb's though. So the
test works."
- The bearing test ran on the printed 6 mm balls (section 7), and it worked.
- **The real caddy uses real 6 mm airsoft BBs.** That's the case the channel was drawn for
  (section 5). Printed balls carry a flat and a layer seam that real BBs don't, so a bearing
  that turns on printed balls has margin on real ones.
- The channel and post at their tested sizes are what the drum is built on: 6.6 mm channel,
  0.29 each side.
- MakerWorld: the bearing test (3597810) and the printed balls (10549018) go on the removal
  list (`business/muse_claude/threads/test-print-removals.md` on main).


## 9. The full caddy (2026-11-15): `pie_caddy.scad`

Built on the tested bearing (section 8), scaled from a 60 mm ball ring to 100 mm. The
channel, the post and the clearances are the test's.

- **The drum, 150 mm across.** Six wedge wells, their heights climbing 45 → 115 mm round the
  drum (a spiral of slices), round a centre well 122 tall.
  - The outer wall is fluted like a pie dish: 48 scallops, 1.2 deep. They're vertical
    detail, so they print exactly and cost no extra time.
  - The base is fluted to match.
  - Walls are 1.6 (four beads) and the floor is 3.
  - The post goes 11 mm into the drum (the test's went 9), under a bore with a 37° roof.
  - The first render, with 10 mm steps and a plain wall, read as a cylinder; hence the
    14 mm steps and the flutes.
- **The base, 120 mm across.** 46 BBs on a 100 mm ring, in the tested 6.6 mm channel.
- **Fit** (`check_caddy.py` → `checks/fit_caddy.txt`): PASS.
  - Nothing touches. The balls clear the channel walls by 0.29 each side, as on the test.
    The drum floats 2.0 over the base. The post's play is 0.55.
  - Pushed sideways by that play, the drum still clears the base.
  - **Centre of mass:** the empty drum's sits 5.6 mm off the axis, from the stepped walls.
    That doesn't affect turning. With the requirement's 1 kg all in one well, it moves to
    37 mm out, still inside the 50 mm ball ring, so the drum can't tip off the balls.
- **Gates:**
  - product gate, both parts pass;
  - print_fidelity, 0 flags on both;
  - fragility, nothing slender.
- **Slices** (Bambu Studio, PLA Matte, retail settings, no supports; the base irons its
  channel floor):
  - drum: 8 h 42 min, 206 g;
  - base: 1 h 36 min, 36 g.
- **Not yet printed at full size.** Untested: the drum's 150 mm bed face over a 100 mm
  ring, and whether 115 mm walls stay true. `make_caddy.sh` rebuilds it.
