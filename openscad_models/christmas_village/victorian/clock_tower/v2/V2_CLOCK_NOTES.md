# Victorian clock tower v2: the clock that shows when lit (2026-10-25)

Scott's first matte-white print lit up everywhere but the clocks: four blank
discs, lit or unlit. His direction: "Make it thinner on the glow parts but
thicker for the details."

## Why the clocks were blank

The hands and hour marks were in the file, and the slicer drew them (checked
layer by layer in the G-code). But they stood only 0.4 mm proud, one bead,
which disappears on matte white. The face was 1.48 mm thick, about 95 mm above
the tealight, so it glowed no brighter than the brick and the 0.8 mm the hands
thickened behind it made no visible difference.

## What v2 changes (the clocks only)

| | before | v2 |
|---|---|---|
| face (glow) | 1.48 mm | **0.84 mm**, two lines; a pocket cut from inside, its ceiling sloping so it needs no support |
| hands and marks (dark) | 0.4 proud, 2.7 mm total | **1.0 proud, 3.7 mm total**; strokes wider (hands 1.8/1.3, marks 1.6/1.2, boss r 1.6) |

The face is the one place under the 1.2 mm wall floor, on purpose: it is 21 mm
across, held all round by the ring and crossed by the hands, like a
lithophane panel.

## Checked

- Measured on the mesh: face 0.83 mm, hands and marks 3.68 mm.
- Bambu Studio slice in matte white: no supports, 56.9 g, 2 h 42 m (was 56.9 g, 2 h 32 m).
  The face prints as two outer lines and the hands as solid blocks
  (`images/clock_face_slice_before_v2.png`).
- Lit render, before and v2 (`images/night_before_v2.png`). A render, not a
  photo; the real print showed even less than the "before" render does.

## Files

- `victorian_clock_tower_v2.scad`, `build.sh` (fast engine, for checking;
  `./build.sh cgal` for the shipping meshes).
- `gcode/victorian_clock_tower_v2_matte_white.gcode.3mf`: ready to print.
- The original (`../victorian_clock_tower.scad` and its 3MF) is unchanged and
  stays what the listing ships until Scott chooses to swap.
