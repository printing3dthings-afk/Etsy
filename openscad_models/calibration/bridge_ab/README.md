# Bridge A/B test (2026-11-24)

Scott ran a bridge test from elsewhere on the P1S (`../../real_timelapses/bridge_test_2026-11-22.mp4`):
"Good for the smallest one. The rest have stringing slightly on the underside. Is there a better
way to achieve these". This is our own version, set up to answer that on our printer, the way
the ironing test settled ironing: one part, four copies on one plate, each sliced differently.

## The part (`bridge_coupon.scad`)
- **Bridges:** square pillars on a slab, with bridges of 20, 30, 40 and 50 mm between them.
  There's no 10 mm span; Scott's test was already good at the smallest one.
- **Deck:** 1.2 thick, 6 wide.
- **Label:** a raised letter at the end says which copy it is.

## What changes between the copies (`bridge_ab_test.gcode.3mf`, 1 h 6 m, 16 g)
Everything is our usual Standard slice, matte PLA, except bridge flow:

| copy | bridge flow | extrusion on the bridges (measured in the G-code, E per mm) |
|---|---|---|
| A | 1.0, what our slices use now | 0.0335 |
| B | 0.9 | 0.0301 |
| C | 0.8 | 0.0251 |
| D | 0.7 | 0.0215 |

**Why only flow:**
- Speed was the other candidate, but every copy bridged at 30 mm/s whatever its setting: the
  bridge layer is small, and Bambu's layer-cooling slowdown caps it.
- The fan is already 100% on bridges (`overhang_fan_speed = 100`).
- Thick bridges are already off (`thick_bridges = 0`).

Less flow lays a thinner strand that the head pulls tighter, so it sags and hangs less. Too
little and the strands break or leave gaps. The test finds where that turns over on this printer
and filament.

## What to look at
Turn each strip over and look under each span, 20 to 50 mm:
- **Strands:** hanging strands or a sagging belly?
- **Gaps:** gaps between the strands?

The copy that's cleanest at 40–50 mm without gaps sets our bridge flow.

## Checks
- **The product gate fails it, as it should for this part.** It flags 18 overhang perimeters:
  those are the bridges this part exists to test, with 0 support moves. min_wall reads 0.91: the
  slab is 1.0 thick.
- **The rest passes:** it's watertight, one body per copy, and prints full height.
- **The slice:** each copy's setting was checked in the 3MF's object settings and in the G-code.
