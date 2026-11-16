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
