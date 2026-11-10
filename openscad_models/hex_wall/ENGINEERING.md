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
  - **The slot:** it prints into the module's back as the module prints on its
    back. It narrows toward the bed, so it has no overhang, and its ceiling is
    a 15 mm bridge.
  - **The other way round:** a tab on the module would need the module printed
    face-down. That's impossible with a hook on its front, and a slot in the
    tile would need its lips printed over air.
- **Rank 1 in handbook section 5:** a geometric lock. Nothing flexes, so
  nothing wears.

## 3. Hand calculations

```
clearance 0.2: each lip overlaps 1.53, RSS 0.32, worst 0.60, ratio 4.8 -> ok
clearance 0.3: each lip overlaps 1.43, RSS 0.32, worst 0.60, ratio 4.5 -> ok
a 2 kg bag on a hook 40 out, x3: 2354 N mm; the top of a 30 tall tab pulls out with 78 N on 2 lips x 30 long; stress 0.77 MPa vs Z strength ~28
```

- **Engagement:** 4.5 to 4.8 times the RSS, and deeper than the worst case.
  The stack counts the droop of both overhanging flanks.
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
| slot's bridged ceiling sags | low, harmless | 15 mm span; the rail never touches the ceiling (0.2–0.3 gap) |

## 5. The test print (`hang_coupon.scad`, `hex_wall_hang_test.3mf`)

- A strip of tile with the real rail and one countersunk screw hole.
- Two hook modules, with slots 0.2 and 0.3 clear: 1 and 2 notches.

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
