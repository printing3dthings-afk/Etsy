# Pie Drum Caddy v2: the keeper (2026-11-24)

Following `data/knowledge_base/mechanism_engineering_handbook.md` section 7: requirement in
numbers, concept, hand calculations, failure modes, then a coupon of the joint for Scott to
print before the full caddy. Source: `pie_caddy_v2.scad`. v1 (`pie_caddy.scad`) is live and
untouched.

## 1. Requirement (Benson's brief, 2026-11-22, and Scott)
- "Can it be designed to latch in somehow. So when it's moved it stays in one piece."
- Lifting by the drum with 1 kg in the wells must not separate it: drum 206 g, contents
  1.0 kg, base about 150 g.
- The drum still spins freely: trapped, never clamped. The brief asks for 0.3–0.5 mm of
  running clearance under the keeper.
- At least 3 full turns of thread. Finger-tightened, and it unscrews fully, so the drum lifts
  off for cleaning as in v1.
- No supports anywhere visible, no hardware beyond the BBs, and the bearing unchanged:
  ball circle r 50, 46 BBs, channel 0.3 a side.

## 2. Concept (Scott's pick, 2026-11-24: "Tall keeper cup")
The brief's knob sat on the centre well's floor, 97.5 mm down a 23.2 mm tube, where no finger
reaches. Instead:
- **The post** (Ø16) grows up through the drum. It's plain through the drum's bore, threaded
  above the bore's top (the ledge, 15 mm above the drum's underside), and tipped with a 45°
  cone.
- **The keeper cup** is a tube filling the centre well. Its foot is a nut; above the nut, a
  45° cone roof; above that, a 1.6 mm floor and a 95 mm pen cup. A knurled collar sits 1 mm
  above the hub's top.
- **The stop:** the cup screws down until its cone roof lands on the post's tip. That stop,
  not how hard it's turned, puts the cup's foot 0.5 mm above the ledge. Lifting the drum
  brings the ledge up against the foot, so the drum can't come off, and it never clamps.
  The cup stands still while the drum turns round it, and lifting by the collar carries the
  whole caddy.
- **The thread** is exactly the jar tower's tested profile: 4 mm pitch, 1.2 mm deep, 35° flanks
  (Scott's pick, 0.2 clearance, Nov 13). It runs 12.5 mm, just over 3 turns.

## 3. Hand calculations (`tools/mechanism_budget.py`)
```
thread cl 0.2 (3 mm / 1.0, first try): depth 0.8, RSS 0.23, worst 0.40, ratio 3.41  ok
thread cl 0.3 (3 mm / 1.0, first try): depth 0.7, RSS 0.23, worst 0.40, ratio 2.98  FAILS the 3x rule
  -> changed to the jar's 4 mm / 1.2: depth 1.0 at 0.2 (4.3x), 0.9 at 0.3 (3.9x)
axial gap under the keeper, 0.5 drawn: worst 0.45, RSS 0.23 -> 0.05 at worst, 0.27 typical; never clamps
post in the drum's bore, 0.55 drawn (0.15 hole compensation): worst 0.25 -> 0.30 open at worst
keeper in the centre well, 0.6 drawn: worst 0.25 -> 0.35 at worst (0.5 left 0.25, under the 0.3 rule)
load: 1.36 kg x 9.81 x 3 = 40 N
thread shear: 173 mm2 x ~8 MPa (interlayer) -> strips at ~1.4 kN, 35x the load
post core in tension (interlayer): 154 mm2 -> ~1.7 kN, 42x
```

## 4. Failure modes
| how it could fail | likely? | what prevents it |
|---|---|---|
| keeper clamps the drum (no spin) | low | the stop is cone on cone; the gap is set by geometry, not torque |
| drum rubs the keeper's side | low | 0.6 drawn, 0.35 at worst |
| thread binds | medium at 0.2, low at 0.3 | the coupon tries both on this 16 mm post |
| cross-threads | low | 4 mm pitch, a lead-in cone on the post and a countersink in the nut |
| strips or the post snaps | very low | 35x and 42x the lifting load |
| keeper unscrews as the drum turns | low | the drum touches the keeper only when lifted; resting, the gap is open, so no torque reaches it |
| over-tightening cracks the cup's foot | low | the load goes cone to cone into the post's tip, 7 mm of solid |

## 5. Coupon (print this first, under 30 minutes)
`coupon_base` (a disc with the post's plain stub and thread), `coupon_ring` (the drum's hub round
its bore) and `coupon_keeper` at clearance 0.2 and 0.3 (one and two notches). **What to
check:**
1. Does each keeper screw down by fingers to a firm stop?
2. With the keeper home, does the ring still turn freely under it, and lift only a hair
   before it stops?
3. Which clearance feels better: smooth with no wobble?
