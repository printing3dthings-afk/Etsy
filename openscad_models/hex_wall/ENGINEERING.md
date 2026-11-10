# Hex Wall Tiles: the engineering, before the model

2026-11-10. This is Scott's pick 6B: hexagonal wall tiles in any pattern, with
modules that hang on them. It follows the handbook's section 7.

## 1. The requirement, in numbers

- Each module (hook, shelf, mail slot, cup) holds 2 kg, with a safety factor
  of 3.
- Modules lift off by hand, with no tools and nothing to unclip.
- A module can't be knocked off by pulling it straight out from the wall.
- Each tile mounts with one or two screws. It also takes strong double-sided
  tape, for a light load.
- No supports.

## 2. The concept: a dovetail rail on the tile, a slot in the module's back

- **How it hangs:** the slot is open at the bottom and closed at the top. The
  module slides down onto the rail and hangs on the rail's top end.
- **What holds it:** its weight keeps it down, and the dovetail keeps it to the
  wall.
- **Why the rail is on the tile and the slot is in the module, not the other
  way round:**
  - **The rail:** it stands up from the tile as the tile prints on its back,
    leaning out at 30°. That's a printable overhang.
  - **The slot:** it prints as the module lies on its back. It narrows toward
    the bed, so it has no overhang.
  - **It's a window right through the module,** so you see the tile's rail
    through it. It has no ceiling, so nothing prints over air.
  - With a ceiling (a slot cut only into the back), the bridge always had a
    free edge at the slot's open end. The slicer printed that as overhang
    perimeters, however the end was shaped. I tried a straight end and an
    entry funnel.
  - **The mouth rises straight for 1.2 mm before the flank leans out.** Run
    from the back face, the flank left a 60° wedge of lip that the gate read
    at 0.2–0.4.
  - The hook sits above the window, on a taller (58 mm) module.
  - **The other way round:** a tab on the module would need the module printed
    face-down. That's impossible with a hook on its front, and a slot in the
    tile would need its lips printed over air.
- **Rank 1 in handbook section 5:** a geometric lock. Nothing flexes, so
  nothing wears.
- **The hook's root sinks 2.4 into the module.** At 0.5 the tilted bar's end
  stood 1.75 proud on its low side, and the slicer propped that 50° ledge with
  157 support moves.

## 3. Hand calculations

```
clearance 0.2: each lip overlaps 1.36, RSS 0.32, worst 0.60, ratio 4.3 -> ok
clearance 0.3: each lip overlaps 1.26, RSS 0.32, worst 0.60, ratio 4.0 -> ok
a 2 kg bag on a hook 40 out, x3: 2354 N mm; the top of a 30 tall tab pulls out with 78 N on 2 lips x 30 long; stress 0.77 MPa vs Z strength ~28
```

- **Engagement:** 4.0 to 4.3 times the RSS, and deeper than the worst case.
  The stack counts the droop of both overhanging flanks.
- **The rail is 3.5 tall.** Its flanks stop 0.8 short of the top and stand
  straight for it.
  - Run to the top, the flanks met it at a 60° edge, which the product gate
    read as 0.13 thick.
  - Blunting it at a 3 mm height would have cut the margin to 3.0 times, right
    at the rule's limit. At 3.5 mm it's back to 4.
- **Strength:** with a 2 kg bag, × 3, the rail's lips see under 1 MPa. Their
  layers hold about 28.
- **The weak point is the wall plug, not the print.** Each tile should go on a
  screw into a stud or a proper anchor for anything heavy.

## 4. Failure modes

| how it could fail | likely? | what prevents it |
|---|---|---|
| module won't slide on | medium at 0.2 | the test print settles 0.2 or 0.3 |
| module rattles | low at 0.2, medium at 0.3 | same; its weight holds it down on the rail |
| knocked off the wall | very low | it must lift 34 mm before it can come forward |
| rail's lips snap | very low | under 1 MPa against 28 |
| tile pulls off the wall | depends on the wall | screws into studs or anchors; tape for light loads only |
| the window shows the rail | certain | by design; on the finished modules it can be a feature, or covered |

## 5. The test print (`hang_coupon.scad`, `hex_wall_hang_test.3mf`)

- A strip of tile with the real rail and one countersunk screw hole.
- Two hook modules, with slots 0.2 and 0.3 clear: 1 and 2 notches.
- About 33 min and 10 g, with no supports. All three parts pass the product
  gate.

**What to check:**
1. Each module slides down onto the rail and sits flat.
2. Which one slides on easily with the least rattle?
3. Pull it straight out from the wall: it shouldn't come off.
4. Lift it up: it comes off.
5. Screw the tile up and hang a bag on the hook.

**Checked on the exported parts (`check_hang_coupon.py`), both modules:**
- hung, nothing overlaps;
- pulled 1 mm off the wall, the rail's lips hold it;
- lifted 6 mm, it still holds;
- lifted clear of the rail, it comes off.

## 6. Next

The tiles themselves, once you've told me which slot clearance you liked:
- 80 mm hexagons that sit edge to edge in any pattern;
- a set of modules: hooks, a small shelf, a mail slot, a cup.
