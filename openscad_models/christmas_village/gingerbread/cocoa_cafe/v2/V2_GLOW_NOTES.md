# Gingerbread cocoa café v2: windows and COCOA that show (2026-10-25)

Scott's first matte-white print showed neither the mug's windows nor COCOA.
His direction: "Make it thinner on the glow parts but thicker for the details."

## Why they did not show

The mug was 1.68 mm all round, so its windows glowed no more than the rest of
it, and their outlines and bars stood 0.4 mm proud, one bead. COCOA stood
0.84 mm proud. On matte white neither cast enough shadow to read.

## What v2 changes

| | before | v2 |
|---|---|---|
| window panes (glow) | 1.68 mm, same as the mug | **0.84 mm**, two lines; a pocket cut from inside, its ceiling sloping so it needs no support |
| window outlines and bars (dark) | 0.4 proud | **1.0 proud** on a skirt, the full wall behind |
| COCOA | 0.84 proud | **1.2 proud** on a skirt, strokes 0.2 mm fatter |

The panes are the one place under the 1.2 mm wall floor, on purpose: each is
about 7 mm wide, held all round by its outline and crossed by its bars, like
a lithophane panel. Nothing grows into the mug: the tealight has 0.8 mm to
spare there.

## Checked

- Bambu Studio slice in matte white: no supports, 44.4 g, 2 h 11 m (was 43.3 g, 1 h 59 m).
  Through a window the pane prints as two lines (was three) and the bars stand
  out; COCOA stands further out (`images/window_and_cocoa_slice_before_v2.png`).
- Lit render, before and v2 (`images/night_before_v2.png`). A render, not a photo.

## Files

- `gingerbread_cocoa_cafe_v2.scad`, `build.sh` (fast engine, for checking;
  `./build.sh cgal` for the shipping meshes).
- `gcode/gingerbread_cocoa_cafe_v2_matte_white.gcode.3mf`: ready to print.
- The original (`../gingerbread_cocoa_cafe.scad` and its 3MF) is unchanged and
  stays what the listing ships until Scott chooses to swap.
