# Otter: the joint, engineered first

Scott, 2026-11-11, picked 7A of five for the articulated critter: "an otter: a
jointed body that curls onto its back, holding a shell on its tummy." It moves, so it
follows the mechanism process (`data/knowledge_base/mechanism_engineering_handbook.md`,
section 7): the joint is calculated and test-printed **before** the otter is built
around it.

**Status:**
- The test print is ready: `otter_joint_test.3mf`, about 28 min.
- **The otter itself waits for Scott's test results.**

## 1. Requirement
- **Print in place:** the otter comes off the plate already jointed. No hardware, no glue.
- **Swing:** about ±15° per joint, side to side. That's the otter lying on its back,
  printed flat on its back. Eight joints curl it about 120°.
- **Strength:** survives a firm tug, taken as 20 N on a segment 15 mm from its joint.
- **Stays together:** pulling or lifting can't separate a joint.

## 2. Concept, and why not the usual ball joint
- **The shop's first flexi failed in the slice.** The seahorse's ball sat in a
  spherical cup, and the slice fused it solid (Technique 44).
- **The real flexi ball joint isn't clean either.** It's a ball in a slot socket.
  The ball's underside hangs over the socket floor, so it prints "lightly fused, freed
  by the first flex" (Technique 42).
- **The otter needs only side-to-side swing.** A joint for exactly that can print clean.
- **So: a vertical "spinning-top" pin in a C-ring.**
  - The pin is narrow at its foot and head and widest in the middle; the ring's bore
    follows it with a gap all round.
  - Every slope is 37° from upright, and both parts rise from the plate: no bridge, no
    gap over air.
  - The bulge holds the pin in vertically.
  - The C's slot, a wedge narrower at the waist than the pin, holds it in sideways.
  - A fin through the slot joins the pin to its segment, and stops the swing at the
    slot's sides.

## 3. Numbers (`joint_budget.py` → `checks/budget.txt`)
| | 0.30 gap | 0.35 gap | 0.45 gap | rule |
|---|---|---|---|---|
| sideways retention | 1.17 mm | 1.11 | 1.00 | ≥ 3 × RSS (0.52) and > worst case (0.30) |
| vertical retention | 1.20 mm | 1.15 | 1.05 | ≥ 3 × RSS (0.86) and > worst (0.55) |
| running gap left at worst case | 0.05 | 0.10 | 0.20 | open |
| first layer after elephant's foot | 0.90 | 0.95 | 1.05 | ≥ 0.30 |
| fin bending, 20 N at 15 mm | 18 MPa | 18 | 18 | ≤ 45 / 2 |
| joint across | 15.6 mm | 15.7 | 15.9 | |

**Two designs changed on the numbers before anything printed:**
- **The fin.** At 2.8 mm wide it bent at 23 MPa, over the 22.5 allowed. It's 3.2 now.
- **The slot.** The first had parallel sides. They met the round bore at 39°, leaving a
  thin wedge at each lip, and the product gate's wall check caught it (0.86 mm). A
  wedge with radial sides meets the bore square-on, and the opening is narrowest at the
  waist, where it matters: sideways retention went from 0.55 to 1.1 mm and the joint
  got smaller.

## 4. Failure modes
| failure | how likely | what prevents it | what the test print shows |
|---|---|---|---|
| pin fused to ring, won't turn | low | ≥ 0.30 gap; slopes, not bridges; foot chamfers clear elephant's foot; toolpaths show them apart on all 50 layers (`check_slice.py`) | does each gap turn after a few wiggles? |
| too loose, floppy | medium at 0.45 | three gaps on one plate | which gap feels best |
| pin pulls out sideways | low | 1.0–1.2 mm retention, 6× the tolerance spread | firm tug |
| pin lifts out | low | 1.05–1.2 mm bulge | lift one block off the other |
| fin snaps at the stop | low | 18 MPa at 20 N, half of PLA's strength along the beads | flex hard against the stop |
| swing too small or too big | low | ±19.5–21.5° measured on the exported parts | count the angle |
| cone faces rough or stringy | medium | 37° slopes; the first real print will show | look at the bore |

## 5. Checks run on the test print (`checks/`)
- **Fit (`check_joint.py`, exported parts moved as rigid bodies):**
  - nothing touches at rest;
  - free swing ±19.5–21.5° before the fin meets the slot's side;
  - lifting catches the bulge after 0.50–0.75 mm, and pulling catches after 0.45–0.65 mm.
- **Toolpaths (`check_slice.py`):** pin and ring separate on all 50 layers of all three
  joints, with printed air gaps of 0.27, 0.33 and 0.43 mm.
  - **Control:** the same coupon with a 0.05 mm gap reads fused on 47 of 50 layers.
  - **Not `gcode_probe.py --scan`:** it splits a layer at every z-hop and saw one
    object at a time.
- **Product gate:** pass, six bodies as intended, min wall 1.60 mm.
- **Print fidelity:** 0 flags.
- **Fragility:** nothing slender.
- **Bambu Studio:** 28 min 13 s, 8.4 g, no supports.

## 6. Next
1. **Scott prints `otter_joint_test.3mf`** and tells me which gap feels best, and whether
   any stuck, flopped or came apart (`Otter_Joint_Test_Guide.pdf`).
2. **Then the otter:**
   - a chubby body lying on its back with a shell on its tummy;
   - eight segments built around the chosen joint;
   - forms first, per the character workflow (Technique 83).
3. **What will be calculated, tested and not:** stated in the otter's notes, as the
   handbook requires.
