# Iris Box: engineering (Scott's form A, 2026-11-12)

A trinket box about 100 × 70 mm whose lid is a six-blade camera iris: twist the rim
and the blades swing in to close the top, or back to open it. Mechanism handbook
section 7, in its order.

**Status:** the blade-joint test print (the coupon) is ready. **The box itself is not
modelled yet**: it waits for Scott's coupon results, and for one open item (below).

## 1. Requirement, in numbers
- The opening is 48 mm across with the iris open, and no blade shows inside it.
- With the iris closed, the 45 mm mouth is covered, apart from at most a pinhole.
- One twist of under 60° goes from open to closed. Hard stops at each end.
- It turns smoothly by hand: no catching or tipping, and no rattle.
- Every part prints flat with no supports, and all walls are 1.2 mm or more.

## 2. Concept
- **Six blades on three levels.** Blade k sits on level k mod 3, so opposite blades
  share a level. With two levels, the neighbouring blades collided.
- **Each blade turns on a pin** in the box floor, at radius 41.
- **A drive pin on the twist ring runs in a slot in each blade**, at radius 28.5.
- **Turning the ring 48°** (from −46° to +2°) swings each blade 48.6°.
- **Blade outline:** computed in `iris_budget.py` (shapely), not drawn by hand:
  - each blade covers its sixth of the opening when closed;
  - it stays inside the wall through the whole swing;
  - it clears the opposite blade on its level by 2.5 mm at the closest.

## 3. Budget (`iris_budget.py` → `checks/budget.txt`)
| item | value | needed |
|---|---|---|
| radial clearance on the 4 mm pins, hole and slot | 0.55 (holes 5.1) | 0.30 open + 0.25 worst-case stack |
| gap between levels | 0.50 | 0.30 + 0.20 |
| stack: base, 3 blades of 1.4, ring | 6.2 mm | |
| pin bending, 5 N at 3 mm | 2.4 MPa | PLA across layers ~20 MPa |
| material round slot and pivot hole | 1.2 mm or more | yes |
| blade inside the open 48 mm opening | 0 mm² | 0 |
| drive pins' inner edge | r 25.95 | outside the opening's 24.0 |
| furthest blade point through the turn | r 45.50 | 45.5 |
| closest same-level blades | 2.53 mm | 0.3 |
| **uncovered when closed** | **10.9 mm² at the centre** | **under 1: FAIL, the open item** |

## 4. Failure modes
| failure | cause | guard |
|---|---|---|
| blade binds partway | pin too tight in its hole or slot | two clearances on the coupon, 0.40 and 0.55 |
| blade tips up and catches the next one | clearance too loose, or levels too close | 0.5 mm level gaps; Scott checks for tipping |
| drive pin pops out of its slot | the ring lifts off | the box's lid will hold the ring down; on the coupon, a finger does |
| ring overshoots and drives a blade past its end | no stop | groove ends stop the tongue (checked: 2° past either end, it hits) |
| blade shows in the open mouth | drive pins inside the opening | pins at r 28.5, outside 24 |
| centre doesn't close | opposite blades share a level and can't overlap | **open**: see below |
| a pin snaps | bending across layers | 2.4 MPa against ~20 |

## 5. Coupon (`iris_coupon.scad`, `check_coupon.py`)
- **What's in it:** one real blade, its pivot pin, and a piece of the twist ring with
  its drive pin, at full size. A tongue running in a groove stands in for the ring's
  bearing, and the groove's ends are the stops.
- **Two prints:** 0.40 mm clearance (`iris_coupon_1.3mf`, one notch on the base) and
  0.55 mm (`iris_coupon_2.3mf`, two notches).
- **Fit check, on the exported parts at 13 ring angles:**
  - 0 overlap through the swing;
  - closest approach 0.39 and 0.50 mm;
  - both stops work;
  - swing 48.6°.
- **Gates:** product gate PASS, print fidelity 0 flags, fragility OK, for both prints.
- **Bambu Studio slice:** 29 m 26 s and 29 m 28 s, 8.56 g each, no supports.
- **The guide:** `Iris_Coupon_Test_Guide.pdf` says what to print and how to put it
  together. Scott reports how each one slides.

## Open item: the centre pinhole
- **The problem:** closed, the blades leave a hole of about 4 mm at the centre (10.9 mm²).
  - Opposite blades share a level, so they can't overlap.
  - Trimming them clear of each other through the turn leaves the gap.
- **The fix:** two blade shapes, three of each.
  - In each opposite pair, one blade reaches past the centre.
  - The other stops short of it.
- **Why it waits:** this changes the blades' outline only, not the pivot, slot or ring
  joints the coupon tests. It is done after the coupon, before the box is modelled.
