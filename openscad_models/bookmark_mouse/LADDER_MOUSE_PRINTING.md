# Ladder Mouse bookmark

Scott, 2026-11-11, picked form D of five for the peekaboo bookmark: "a mouse
climbs a rope ladder that hangs down the page, with its hands on the top rung over
the edge."

- **The ladder** (tan, 1.6 mm thick, 24 × 140 mm) goes between the pages. Its rails
  carry a rope twist; the rungs are plain.
- **The top rung** sits on the page edge, 3.0 mm thick. It crosses in front of the
  mouse's chest and his pink hands hold it, standing 0.6 mm proud of it.
- **The mouse** (grey, 3.0 mm, chamfered edge) has pink ears, nose and cheeks and
  black eyes with a grey glint, all flush inlays in the top three layers, and an
  engraved mouth. His tail curls out to the right.
- **The OBC mark** is inlaid in tan under his head.
- **Not printed yet.**

## Printing
- `ladder_mouse_bookmark.3mf`: one object, four parts, for an AMS: tan, grey, pink
  and black.
- Flat on the plate, face up, no supports. About **1 h 20 m and 15.3 g** in Bambu
  Studio (`checks/slices.txt`). Most of the time is colour changes in the top layers.
- Smooth PEI plate for PLA.

## Checks (`checks/`)
- **Product gate:** pass. The rope's twist is declared texture
  (`--wall-skip-part parts/rope_band.stl`). The grooves cross each rail at 55°, so
  between them the top 0.4 mm ends in wedge tips that taper to nothing at the rail's
  edge. Under them the rail is a full 1.2 mm. Minimum wall 1.45 mm otherwise.
- **Print fidelity:** 0 flags. The only dropped plastic is those wedge tips (0.12 mm
  wide, 1.73 mm³ in all).
- **Fragility:** 0 high. The rail lengths between rungs are "watch" (slenderness 4.8;
  the chapel's bar that snapped was 15).
- **Silhouette:** pass (no near-touches, nothing under 1.2 mm, one piece).

## Traps hit on the way (all fixed)
- **The body over the rung hid it.** Layered front to back instead: hands, arms,
  the rung, then head, body and tail.
- **Three edges meeting at one point pinch the weld.** Where a hand's circle, an arm's
  edge and the rung's top met, the print came out with open edges, then a pinhole.
  Fixes:
  - the hands moved in, clear of the rails;
  - the arms taper inside the hands;
  - the corner by the tail's root is filled.
- **A 0.01 mm "safety" margin is a gap.** Cutting the ladder around the mouse
  0.01 mm wide left a hairline gap, and the print came apart in three. Cut on the
  exact outline.
- **The rope grooves ran 1.8 mm deep** in the thick part under the top rung. They
  now stop where the ladder goes into the book.

## Files
- `ladder_mouse.scad`: the model; `part` = tan, grey, pink, black, print (welded),
  rope_band, outline.
- `parts/`: the colour parts, the welded print, the rope band.
- `FACTS.md`: the fact sheet for posts and listings.
