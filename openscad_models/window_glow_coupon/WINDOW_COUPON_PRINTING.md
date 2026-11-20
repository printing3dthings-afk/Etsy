# Window Glow Coupon: printing notes (2026-11-20)

**What it's for:** the one real photo Explained Lesson 005 ("Why our windows are 0.8 mm thin")
has been held for since Nov 11. It holds three windows side by side, 0.8, 1.6 and 2.4 mm thick,
standing upright like our house walls. Put one tea light behind it and photograph the front.

**Not printed yet.** The images are design-review renders, not photos.

## Print
- **File:** `gcode/window_coupon.gcode.3mf`. Bambu Studio's own slice, opens in Bambu Handy.
- **White PLA** (the lesson is about light through white walls), slot 1.
- **1 h 5 m, 23.9 g.** P1S 0.4, PLA Basic, 0.20 mm Standard, 3 walls, 15% infill, supports off.
- Stands on its foot as modelled; no rotating.

## The photo the lesson needs
1. A dark room. The coupon on the table, front facing the camera.
2. One battery tea light behind the wall, centred, about 2 cm back.
3. Photograph straight on, with the labels on the foot in frame.
4. Then move the tea light behind each window in turn, one photo each, so each pane's glow is
   on its own.
Send the photos to Benson. They go in Lesson 005 as they come out, without edits to the glow.

## How it's made (`window_coupon.scad`)
- **Wall 104 × 3.2 mm, 53 mm tall,** on a 34 mm foot.
- **The windows are pockets from the back,** leaving the pane at the front face. The front is
  one flat face, like a house wall seen from the street.
- **Each pocket's ceiling slopes up** at about 63°, so nothing bridges.
- **Labels** 0.8, 1.6, 2.4 are raised 0.8 mm on the foot. OBC is on the foot's back.
- Panes: 0.8 mm is two 0.4 mm lines, 1.6 is four, 2.4 is six.

## Checks (`logs/`)
- **Product gate: PASS,** with the panes declared as the feature under test
  (`panes_region.stl`). They're thinner than the 1.2 mm wall floor on purpose.
- **Print fidelity:** 0 flagged (0.02 mm³ dropped in total).
- **Fragility:** 0 slender runs.
- Viewer: "Window Glow Coupon".
