# Snowfall Plinko (hourglass): engineering (mechanism handbook section 7), 2026-11-16

Scott picked form 4: an hourglass Galton board. Flip it, and the balls fall back through a
second set of pegs, so there's no reset. The pitch is one print with the balls inside and
nothing to assemble. That makes the risky part the balls themselves: they have to print
loose inside a closed board.

## 1. Requirement
- **Balls come free** with a shake, or a poke through the front, and roll smoothly.
- **They stay in:** no opening in the front lets a 5 mm ball out.
- **No ball wedges** anywhere on the way through, either way up.
- **One print, no supports, no hardware.**

## 2. Concept: teardrop balls over a few layers of air, under a bridged lattice front
- **The ball.** Each ball is a teardrop: a 5 mm ball with a 45° point underneath.
  - The point is the only downward face, so it hangs over nothing past 45°.
  - In use the board stands up with the points facing its back. Each ball then turns about
    its own point axis and rolls through the pegs as a true 5 mm circle.
- **Three ways for a ball to meet the floor** (the variants on the test print):
  1. the point hangs 0.2 above the floor;
  2. it hangs 0.4 above the floor;
  3. it is printed onto the floor through a 0.6 neck, to snap with a toothpick.
- **The front** is a grid, 1.2 thick, 0.6 above the balls:
  - bars 1.4 wide with 3.0 openings;
  - upright ribs, so no bar spans more than about 6.5.
  - It has to bridge over the ball chamber; there is nothing else to build it on.

## 3. Numbers (`plinko_budget.py` -> `checks/plinko_budget.txt`)
- **Ball:** 5.0 across, 6.04 tall as printed, about 0.09 g.
- **Variant 3's neck:** a sideways poke at the ball's centre, about 0.3 N, snaps it. A
  toothpick through the lattice is enough.
- **Retention:** openings 3.0 against a 5.0 ball.
- **The gap rule:** every gap a ball meets is a pass (≥ 6.5) or a stop (≤ 3.5), so nothing
  lies in between, where a ball could wedge. Gaps are measured square to the surfaces: a
  peg near a sloped wall is closer than it looks across.
- **Air under the balls, from Bambu Studio's slice** (`check_plinko.py`). The slicer only
  starts a ball where it is wider than a bead, so:
  - variant 1 leaves 0.4 of air (2 layers);
  - variant 2 leaves 0.6 (3 layers);
  - variant 3 prints straight onto the floor.
- **Thicknesses for the gate:** the back is 1.4, the front grid 1.2 thick with 1.4 bars,
  and the variant notches 2.4 apart.
  - At exactly 1.2 (back), 1.0 (grid) and 1.2 (bars), and with notches 2.0 apart, the gate
    read them just under its 1.2 floor.

## 4. Fit, on the exported parts (`check_plinko.py` -> `checks/fit_plinko.txt`): PASS
- **The floating balls** touch nothing. Variant 3's balls are joined only at their necks.
- **The lattice** is 0.6 over the tallest ball. Its widest opening is 3.00 across.
- **No wedging gap** anywhere in the hourglass. The check finds the space a ball's centre
  can reach, and looks for places a 6.5 ball can't follow.
  - Here the largest left-over sliver is 0.12 mm², a corner.
  - Proof the check works: on the first layout, with the first-row peg 6.0 square to the
    sloped wall, it reported four 3.35 mm² wedging strips.
- **The path:** a ball can get from end to end, and so could a 6.5 one.

## 5. Gates
- **Product gate: one named exception (Scott's decision, 2026-11-16).**
  - `no_unsupported_overhang` fails. The gate's slicer puts supports under the lattice
    front, which bridges up to 26 mm over the ball chamber on this test print.
  - Tested on small samples: that slicer flags a plain solid ceiling over the same
    chamber (overhang perimeters) and draws supports under a plate with slots. So no front
    that closes the board in one print, at this thickness, passes it.
  - Scott chose "Bridge it, one print" over a snap-on front or a twice-as-thick vaulted
    board.
  - Bambu Studio's own slice, supports off, draws no support. The front's first two
    layers are 698 mm of bridge lines and 643 mm of overhang perimeter round the bars.
  - The test print decides whether the bridges are good enough.
  - The floating balls' points hang over air by design too.
- **Every other gate check passes** (`checks/gate_coupon.txt`): min_wall is 1.21 at the 1st
  percentile. Variant 3's necks are declared (`parts/gate_skip.stl`).
- **print_fidelity** (`checks/fidelity_coupon.txt`): 8 flags, each the first layer of a
  floating ball's point (0.03 mm³, narrower than a bead).
  - The slicer starts each ball one layer higher than the model's tip, which is why the
    slice shows 0.4 and 0.6 of air, not 0.2 and 0.4.
  - Nothing else is lost or added.
- **Fragility** (`checks/fragility_coupon.txt`): 0 high. The 28 "watch" are the grid's bar
  segments, about 6 mm between ribs.
  - Before the ribs, two bars spanning the full 26 read slenderness 20: past the 15 at
    which the chapel's window bar snapped.
- **Slice:** Bambu Studio, PLA Matte, 0.20, its own speeds: 24 min 41 s, 11.0 g, no
  supports (`checks/release_coupon.gcode.3mf`).

## 6. Failure modes
| mode | how likely | what prevents it, or what the test print tells us |
|---|---|---|
| floating balls weld to the floor | medium for variant 1 | 2-3 layers of air in the slice; a shake or poke frees them |
| neck won't snap, or snaps leaving a nub | low / medium | 0.3 N poke; the nub faces the back, off the rolling circle |
| lattice bars sag onto the balls | medium (bridges up to 26 mm here) | 0.6 gap; ribs every 6.5; the full board's bridges will be peg to peg |
| a ball wedges | low | the gap rule, checked on the model |
| a ball escapes | low | 3.2 openings against a 5 mm ball |
| balls roll badly (lumpy points) | medium | the point faces the back; the test print shows how they roll |

## 7. What only Scott's test print can answer
- Which balls came free, and how: a shake, a tap, or a poke.
- Whether they roll smoothly and fall through the pegs.
- How the bridged lattice looks.

## 8. Scott's result (2026-11-25)
Scott: "I did the plunk test. Did not work. The cage itself was great. The balls didn't come out
at all."

- **The cage works.** The bridged lattice front printed well, so bridging a closed front over
  a chamber is proven on this printer. Keep it.
- **Print-in-place balls failed:** none came out right, in any variant.
- **Why (Scott, 2026-11-25):** "The balls didn't make it because they broke loose during print. I
  think everything is too small for that." The 5 mm teardrops broke free of their footing while
  printing, so the nozzle knocked them about and they never formed. My first guess (welded to the
  floor) was wrong.
- **What changes:** balls can't print loose inside a closed board on this printer. Scott picked **6 mm airsoft BBs** (2026-11-25):
  round, cheap, and they roll best. So the board needs a way to load them (section 9).

## 9. v2: 6 mm airsoft BBs, a loading port and a snap-in plug (2026-11-25, `v2/`)
- **Requirement:**
  - BBs load by hand and the board closes with no tools;
  - the plug holds with the board upside down, and comes out with a firm pull;
  - every gap a 6 mm BB meets is a pass (≥ 7.8) or a stop (≤ 4.2), the v1 rule scaled.
- **Concept:**
  - **The port:** 7.0 wide, through a 3.0 top wall.
  - **The plug:** the chalet's arrow tab (two in-plane prongs, 1.3 × 12, bending along the
    layers), 6.4 thick.
  - **The cage:** the one Scott called great, unchanged: bars 1.4, openings 3.0, ribs every 6.5.
  - **Inside depth:** 6.8, for 0.4 either side of a BB.
- **Numbers (`v2/bb_budget.py` → `checks/bb_budget.txt`):**
  - prong strain 0.47–0.74 % against the 0.8 % repeated limit;
  - per plug, 5–8 N in and 13–21 N out;
  - engagement 2.5×, 3.2× and 3.9× RSS: 0.45 and 0.55 pass the 3× rule;
  - 30 BBs weigh about 0.035 N on the plug, against 17 N to pull it.
- **Fit (`v2/check_bb.py` → `checks/fit_bb.txt`, manifold3d):**
  - each plug seated touches nothing, and nothing 0.05 out;
  - half-way in, the prongs overlap the port (3.8, 5.4 and 6.8 mm³), so they must bend;
  - a 6 mm sphere fits mid-depth at four places in the chamber.
- **Gates (`v2/logs/`):**
  - **Plugs:** pass. Their tab tips were widened to 1.2: at 0.4 the gate read them as sub-floor walls.
  - **Board:** passes everything except `no_unsupported_overhang`. That's the cage bridging over
    the chamber: the same exception Scott approved for v1 ("Bridge it, one print"), and v1's cage
    printed great.
  - **Print fidelity:** 0 flagged on all four parts.
  - **Fragility:** 0 high. The board's 18 "watch" are the cage bars, as on v1.
- **Slice:** `v2/plinko_bb_test.gcode.3mf`, 22 m 2 s, 9.9 g, matte PLA, no supports.
  - Bambu's own speeds, 3 walls, 15%, as v1's test was.
  - On the shop's retail settings, the slower outer wall and ironing made it 41 min, over the
    30-minute coupon limit. This is a function test, not a finish test.
- **Guide:** `v2/guide/Plinko_BB_Test_Guide.pdf`.
- **Scott answers:**
  - do BBs fall through the pegs both ways without sticking;
  - does any catch between the cage and the back;
  - which plug holds upside down and still pulls out.

## 10. Bigger print-in-place balls, tested alongside (2026-11-25, `v2/big_ball_coupon.scad`)
Scott: "The whole thing might need to be bigger so the balls have a chance to print correct."
He picked testing both: the BB test (section 9), and this one.
- **The test:** three pockets under the v1 cage, two 10 mm teardrop balls in each. Each ball
  stands on a neck to the floor: 1.6, 2.0 or 2.4 mm (one, two or three notches).
- **Numbers (`v2/big_ball_budget.py` → `checks/big_ball_budget.txt`):**
  - **While printing,** a neck holds 0.73, 1.43 or 2.47 N at the ball's top, against a
    nozzle's sideways drag of roughly 0.5 N. That drag is a rough figure, not measured.
  - **After printing,** a toothpick at the ball's centre snaps it at 1.3, 2.4 or 4.2 N.
  - **v1's 0.6 neck on a 5 mm ball** held about 0.08 N, and its floating balls held nothing.
    That fits Scott's result.
- **Fit (`checks/fit_big_ball.txt`):** a 0.3 shell round every ball clears the board. The
  tallest ball top sits 0.8 under the cage.
- **Checks (`v2/logs/*_big.txt`):**
  - **Gate:** everything passes except `no_unsupported_overhang`, the cage bridging (the v1
    exception).
  - **The cage here is 1.4 thick, one layer more than v1's.** At 1.2 the gate read its 1st
    percentile just under its 1.2 floor.
  - **Print fidelity:** 0 flagged. **Fragility:** 0 high, 0 watch.
- **Slice:** `v2/plinko_big_ball_test.gcode.3mf`, 21 m 49 s, 11.9 g. Matte PLA, Bambu's own
  speeds, 3 walls, 15%, no supports.
- **Guide:** `v2/guide/Plinko_Big_Ball_Test_Guide.pdf`.
- **Scott answers:**
  - which neck printed the balls whole and still snapped free;
  - whether they roll.
- **What decides the board:** if a neck works, the board can be printed in one piece, about
  twice v1's size. If not, it uses BBs (section 9).
