# Kit-card A-frame chalet: the panel snap (2026-11-25)

Scott picked the A-frame chalet (2026-11-17) for the kit-card pilot: a free MakerWorld model
on one plate inside 180 × 180 (an A1 mini), snapped together with no glue, an LED tea light
inside (floor ≥ 46 mm), colour by at most one manual swap, no supports
(`threads/2026-11-12_kit-card-pilot.md` on main). This follows
`data/knowledge_base/mechanism_engineering_handbook.md` section 7: the joint is proven
before the chalet is built round it.

## 1. Requirement
- **Fit:** every panel goes in by hand, about 5 N, with no tools.
- **Hold:** it holds when the chalet is picked up by its roof.
- **Take apart:** it comes apart for storage with a firm pull, and survives being built and
  taken apart again and again.
- **Child handling:** no slivers or knife-edge tabs (Benson's brief).
- **One joint for all:** the same joint at every panel edge, through a 3.0 mm grip (the base
  floor, and the roof).

## 2. Concept: an arrow tab with two in-plane prongs, through a slot
- **The tab:** sits on the panel's edge. It is two prongs, each 1.3 thick and 12 long:
  - they're cut free inside the panel and joined to it only at the top (their root);
  - a nub on each prong passes through the slot and springs out under the far face.
- **Why the prongs bend the strong way:** the panels print flat, so the prongs lie in the
  print plane and bend along the layers. This is the Pocket Top's beam, which Scott tested
  (all three reaches held; he picked 0.45, 2026-11-15). The Gear Heart's posts bent across
  the layers and snapped.
- **The flanks:**
  - lead-in 30° from the push direction;
  - catch flank 50°. At 60° it would sit 5° from self-locking (65.8° at μ 0.45), where
    friction decides whether it ever comes out.
- **The base prints show face down,** floor on the bed. A floor printed face up would bridge
  the skirt's whole cavity. The slot's mouth gets a 0.4 chamfer for the bed face's elephant's
  foot.

## 3. Hand calculations (`snap_budget.py` → `checks/snap_budget.txt`)
```
reach 0.35: strain 0.47 %; per tab 1.9 N in, 4.9 N out; engagement 1.9x RSS, under the worst case
reach 0.45: strain 0.61 %; per tab 2.5 N in, 6.3 N out; engagement 2.5x RSS, under the worst case
reach 0.55: strain 0.74 %; per tab 3.0 N in, 7.7 N out; engagement 3.1x RSS, over the worst case
repeated-flex limit (printed PLA, XY) 0.8 %: all three are under it
grip stack (floor thickness in Z, shoulder to catch in XY): worst 0.20, RSS 0.14; the catch
  sits 0.15 below the floor
centre gap 1.6: at 0.55 the prongs still leave 0.5 between them at full bend
```
**By the rule (3× RSS and over the worst case), only 0.55 passes.** 0.45 is the Pocket Top's
pick at 2.5×. The coupon tries all three, and Scott's hand decides.

## 4. Fit check (`check_fit.py` → `checks/fit.txt`, manifold3d on the exported parts)
- **Seated:** no overlap, and none 0.05 above either. The shoulder rests on the floor, and
  the nubs are clear under it.
- **Half-way in:** the nubs overlap the slot walls (1.3, 1.7 and 2.1 mm³), so the prongs must
  bend in.

## 5. Failure modes
| how it could fail | likely? | what prevents it, or what the coupon answers |
|---|---|---|
| a prong cracks at its root | low | strain 0.47–0.74 % vs 0.8 %; bends along the layers; round root (r 0.4 and 0.8) |
| too stiff to push in | low | 2–3 N a tab; the 30° lead-in |
| falls out when picked up | medium at 0.35 | 0.35 is under the worst case; the coupon shows it |
| won't come apart | low | 50° catch, 5–8 N a tab |
| panel rattles | medium | the slot has 0.15 a side and the grip up to 0.35 of lift; the coupon shows if it's noticeable |
| prong tip snaps off in a child's hand | low | tips 1.2 wide; fragility check: no high, two watch per stub (the prongs) |
| elephant's foot closes the slot mouth | low | 0.4 mouth chamfer |

## 6. Coupon (`snap_coupon.scad`, `chalet_snap_coupon.gcode.3mf`)
- **On the plate:**
  - one base strip, 66 × 18 mm, a 3.0 floor on a 5 mm skirt, with three identical slots;
  - three panel stubs, 18 × 15 × 2.4.
- **Marked:** notches on each stub's top edge, and on the skirt beside the slot it was tested
  in: one = 0.35, two = 0.45, three = 0.55.
- **Print:** 25 m 11 s, 7.5 g, matte PLA, Standard, no supports.
- **Checks:** product gate PASS on all four parts, print fidelity 0 flagged, fragility 0 high.
  The 2 watch on each stub are its two prongs, slender by design (`coupon/logs/`).
- **Scott answers:**
  1. Which stub pushes in by hand and clicks?
  2. Which stays put when the base is held upside down and shaken?
  3. Which pulls out with a firm tug and not a struggle?
  4. After 10 in-and-outs, is any prong root whitened or cracked?
  5. Does any stub rattle?

## 7. What waits for the result
The chalet itself (G0 brief, plate layout, swap layer and the full model) is built on the
reach Scott picks. Nothing else is modelled until then.
