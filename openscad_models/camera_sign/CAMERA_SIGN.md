# Camera sign: notes

Built 2026-11-18.

**Scott:** "I want something that sends people to my instagram to be modeled and printed
that I can hang in the circle area." He circled the back wall inside his P1S, behind the
toolhead, in a photo from the chamber camera. So anyone watching the camera or a timelapse
sees where to find him.

He picked two of five forms:
- **Neon (form 1):** "FOLLOW" and "@onbrandcraftz2026" in a bold script, on their own
  raised outline. The shape is the letters, nothing else. About 138 × 29 mm.
- **Plaque (form 5):** a rounded plate with a raised border, "FOLLOW" and the handle in
  bold capitals. About 144 × 38 mm.

**No Instagram logo:** it's their trademark. "FOLLOW" says what the handle is for.

The pictures in `images/` are design-review renders, not photos.

## Before printing: Scott's two gaps (NOT YET MEASURED)
The back wall is inside the printer's moving space:
- the bed rises to just under the nozzle, close to the wall;
- the toolhead and its rail come back to it when printing near the rear;
- the back Z lead screw runs in a slot in the middle of the wall.

**The sign's thickness off the wall, `THICK`, is a 2.4 mm placeholder** until Scott
measures:
1. **Behind the toolhead:** move it all the way back (Bambu Handy, Controls, the Y axis);
   measure the gap from its back to the back wall.
2. **Behind the bed:** raise the bed to the top; measure the gap from its back edge to the
   wall, away from the lead screw's slot.

**Measure with the gap gauge** (`gap_gauge.scad`, below), or a ruler.

Then `./build.sh <thickness>`, with the thickness at most the smaller gap less 1 mm, and
re-run the checks and the slice.

**Where it goes:** to one side of the lead screw's slot, never over it, and nowhere the
bed's edge passes. Mount it with double-sided tape on the flat back. Magnets work only if
the wall is steel, which isn't checked yet.

**Readability:** the camera is 1280 × 720. The handle's letters are about 8 mm tall
(neon) and 6 mm (plaque), roughly 20 px on camera from the front of the chamber. If they
don't read in a timelapse, the sign can't simply be made wider: it has to stay on one side
of the lead screw's slot.

## Colours, by height
| part | what | height | colour in the file |
|---|---|---|---|
| base | the outline (neon) or the plate (plaque) | 0 to THICK - 0.8 | near-black `#1C1C1F` |
| letters | the words, and the plaque's border | the top 0.8 mm | orange `#F28C28` |

The AMS changes colour only on the top four layers.

## Print it
- **Files:** `camera_sign_neon.3mf` or `camera_sign_plaque.3mf`; sliced:
  `gcode/camera_sign_<style>_two_colour.gcode.3mf`.
  - Bambu Studio, P1S 0.4, PLA Basic, 0.20 mm Standard;
  - 3 walls, 15% infill; supports off.
  - **At the 2.4 mm placeholder.** Don't print until the gaps are in.
  - **Cost at the placeholder, from Bambu Studio's own slice:**
    - neon: 30 m, 7.3 g (5.9 g black, 1.4 g orange);
    - plaque: 45 m, 13.2 g (11.5 g black, 1.8 g orange).
- **Flat, face up, back on the plate.** Nothing overhangs.
- **Filament:** PLA is fine for the chamber's passive ~40 °C when printing PLA. PETG
  would be safer if Scott prints ABS or ASA with the chamber hot.

## Checks (`logs/neon`, `logs/plaque`, at the placeholder thickness)
- **Parts:** closed, no two overlap.
- **Product gate: PASS.** The raised letters are declared as colour detail.
- **Print fidelity:** 0 flagged.
- **Fragility:** 0.
- **Silhouette, neon outline:** PASS (no near-touches, nothing thin, one piece).

## Rebuild
    ./build.sh [thickness]
    python3 check_sign.py neon parts gate fidelity fragility 3mf colour as_printed viewer
    python3 check_sign.py plaque parts gate fidelity fragility 3mf colour as_printed viewer

The handle's text size comes from its measured width in each font (`W_SCRIPT`,
`W_BOLD`). Re-measure if the handle changes.

## The gap gauge (Scott asked for it, 2026-11-18)
**Why:** Bambu's wiki, manual and store give neither gap.

**What it is:**
- `gap_gauge.scad`: a 148 × 18 mm strip with twelve steps, 1.6 to 6.0 mm in 0.4 mm steps.
  Each step's thickness is engraved on it, plus a 6 mm handle with the OBC mark.
- The steps are multiples of the 0.2 mm layer, so each prints to its number, within about
  0.1 mm.
- **It starts at 1.6 mm.** A gap under that can't take a sign anyway: the thinnest that
  prints in two colours is about 1.6 mm, and it wants 1 mm to spare.
- **Sliced:** `gcode/gap_gauge.gcode.3mf`, 27 m, 8.3 g, one colour, supports off. Print it
  flat, as it lies.

**How to use it:**
1. **Behind the toolhead:**
   - In Bambu Handy, Controls, move the toolhead all the way to the back.
   - Slide the gauge in, thin end first, between the back of the toolhead and the back wall.
   - The thickest step that goes in without forcing is the gap.
2. **Behind the bed:**
   - Raise the bed to the top.
   - Do the same between its back edge and the wall, away from the lead screw's slot.
3. **Never move an axis with the gauge in.**

**Checks (`logs/gauge/`):**
- **Product gate: PASS.** The numbers' area is declared as detail
  (`part = "detail"`): the spans between engraved strokes are lettering, not walls.
- **Print fidelity:** 0 flagged.
- **Fragility:** 0.
