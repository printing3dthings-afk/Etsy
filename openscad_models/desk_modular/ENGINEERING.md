# Modular desk organizer: the butterfly-key joint (2026-11-24)

Scott picked butterfly keys (2026-11-24) from the five options in `OPTIONS.md`. This follows
`data/knowledge_base/mechanism_engineering_handbook.md` section 7: numbers, concept, hand
calculations, failure modes, then a coupon of the joint before any module is built.

## 1. Requirement
- Two modules side by side are held together by a key dropped in by hand, with no tools and no
  hardware. It comes out with a fingernail.
- Pushing the set across a desk by one module (say 20 N, a firm shove) doesn't separate them.
- The joint is the same on every side of every module, every 40 mm, so any module meets any
  other.
- Strength comes from walls, not infill: the modules print at ~10% infill.

## 2. Concept
- **Pockets.** Every module has a half bow-tie pocket at the middle of each 40 mm grid unit, on
  every side. Each pocket is 8 mm into the wall, 16 mm deep, open at the top, with a floor under
  it, inside a boss 3.2 mm thick.
- **The key** is a bow-tie 16 long, 12 across the wings and 4.5 at the waist, standing 1.5 above
  the rim. It's printed upright, the same profile all the way up. A sideways pull loads it in
  the plane of its layers, the strong way. The pockets' flanks are vertical walls of the module,
  loaded in-plane too.
- **The flanks** run 25° off the key's length. Play along the joint is clearance ÷ sin 25° at
  each pocket: 2.4× the clearance, or 4.7× for the joint's two pockets. The concept sketch's 17°
  gave 3.3× a pocket.

## 3. Hand calculations (`tools/mechanism_budget.py`)
```
stack: key outline 0.1, pocket outline 0.1, wall flatness 0.1, modules square 0.1
  worst 0.40, RSS 0.20
engagement: the wing stands 3.75 past the waist -> 18.8x RSS (rule: 3x, and > worst case)  ok
waist in tension: 4.5 x 16 = 72 mm2 x ~40 MPa (in-layer PLA) -> ~2.9 kN, >100x a 20 N shove
pull-apart play (manifold3d on the coupon, nominal): 0.95 mm at 0.2, 1.2 at 0.25, 1.45 at 0.3
  printed, a pocket comes out ~0.1 small and a key ~0.1 big, so 0.2 nominal is ~0.5 mm of give
```

## 4. Failure modes
| how it could fail | likely? | what prevents it |
|---|---|---|
| key won't go in | medium at 0.2 | the coupon tries 0.2, 0.25, 0.3 |
| modules wobble apart, a visible gap | medium | 25° flanks; the coupon shows how much give each clearance leaves |
| key falls out when a module is lifted | expected | open-top pockets: lift a set by its keys' neighbours, or carry modules one at a time. Stated in the guide, not hidden |
| key snaps at the waist | very low | 72 mm² in-plane, >100× the load |
| a pocket's boss splits | low | 3.2 mm boss round the pocket, loaded in-plane |
| key is hard to get out | low | stands 1.5 proud for a fingernail |

## 5. Coupon (under 30 minutes): `key_coupon.scad`, `butterfly_key_coupon.gcode.3mf`
- **Parts:** two copies of one block (a 40 mm wall section with the pocket and its boss), and three
  keys at 0.2, 0.25 and 0.3. They're marked by one, two or three notches in the key's top.
- **Depth:** the pockets are 8 deep, not the module's 16. The fit doesn't depend on depth, and at
  16 the plate sliced at 42 minutes.
- **Print:** 26 m 5 s, 8.2 g, no supports. Gate and fragility pass on every part.
- **What Scott checks:**
  1. Which key drops in with a finger push and doesn't rattle?
  2. Push the blocks apart: how much gap opens? Is it acceptable on a desk?
  3. Does the key come out with a fingernail?
