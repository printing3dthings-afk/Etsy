# Kawaii Cow

2026-11-04. Your pick from the five figurine ideas: a chubby desk-buddy cow,
built with the smooth-blend method from the character-design research.

She sits like a plush toy with her legs out in front and a red heart in her
lap. Her chin rests on the heart and her front hooves hold its sides. One
print, no supports, no assembly, no glue.

**Size:** 51 × 58 × 66 mm tall.

**File:** `kawaii_cow.3mf`, four colours, AMS slots in this order:

| slot | colour | hex | what |
|---|---|---|---|
| 1 | white | `#F4F1EA` | her body, horns |
| 2 | black | `#2B2433` | spots, left ear, eyes, horn tips, hoof pads, tail tuft, the OBC mark |
| 3 | pink | `#F6A6C1` | muzzle, cheeks, inner ears |
| 4 | red | `#D7263D` | the heart |

## Printing

- PLA, standing on her base as the file opens, **no supports**.
- **0.12 mm layers for a sale print.** Her face is small round forms (eyes,
  nostrils, cheeks), and at 0.2 mm a 1 mm dome is 5 visible steps
  (DETAIL_STANDARD rule 4). 0.2 mm works for a quick test.
- **Time and filament, one colour, PrusaSlicer with the P1S settings:**
  - 0.2 mm layers: 43 min, 26 g
  - 0.12 mm layers: 1 h 1 min, 24 g
- **Colour changes are most of the print.** Almost every layer has two
  colours: the heart runs up to 28 mm, the black from the base to the horn
  tips, and the pink from 26 to 59 mm.
  - PrusaSlicer counts 595 filament changes.
  - Bambu Studio orders each layer to start with the last layer's colour, so
    its count will be lower, but still a few hundred.
  - Each change costs time and purge filament. PrusaSlicer's four-colour
    slice uses 148 g including its purge tower, against 26 g for the cow
    herself. Its time estimate for a multi-colour slice isn't reliable, and
    Bambu purges differently, so slice the 3MF in Bambu Studio for the real
    total before pricing her.
  - If it comes out too long, the cheapest change to make is dropping the
    black spots that sit at the heart's height. Tell me and I'll make a
    lighter version.

## What she is made of

Built in Python from blended round shapes (`cow.py`, using
`tools/sdf_figure.py`), not OpenSCAD. That's what lets the head flow into the
body without a crease. Every size is a named number at the top of `cow.py`.
Run `python3 cow.py` to rebuild the parts, which takes about 4 minutes. It
needs scikit-image (`python3 -m pip install scikit-image`).

**The pose is also the support plan.** Every part that would hang has
something under it within the slicer's limit:
- Her muzzle sits on the heart, the heart stands on its tip in her lap, and
  her hooves rest on her feet.
- A soft pad behind the heart carries her chin across the gap to her belly.
- A low cushion between her feet fills a crevice the slicer kept propping.
- Her ears point up and out at 55°. Drooping, an ear's tip is its lowest
  point and prints first, in mid-air.
- Under everything else, the model grows smooth 33° slopes. Under round
  forms they are tangent, so they look like part of the shape.

**Details:**
- The cushion in her lap shows as a low white skirt in front of the heart,
  like a plush's bottom spreading on the plate. If you'd rather it didn't
  show, the alternative is a small support under the heart's tip.
- The heart is red, not pink. In pink it ran into the pink muzzle resting
  on it, and the two read as one blob.
- That left no slot for cream horns, so the horns are white with black tips.
  The tips are what make them read as horns.
- Each hoof pad has a cleft groove down the middle.
- Her head tilts 7°, so she isn't a mirror image of herself.
- The OBC mark is inlaid in black under her base.

## Checked before it was pushed

The results are in `checks/`.

- **Product gate: passed.**
  - 0 support moves and 0 overhang perimeters, on the full 65.7 mm height.
  - Walls 2.61 mm at the 1st percentile.
  - 69% of her footprint on the plate.
- **Print fidelity, all four colours: 0 flags.** The slicer drops 6.6 mm³
  in total, all slivers under 0.3 mm deep. It fills nothing, and puts
  0.02 mm³ in the wrong colour.
- **Fragility: nothing high and nothing on watch.** She is chunky all
  through.
- **Not tested on the printer yet.** The parts I'd look at first:
  - the ears' rims, the thinnest parts at 2.6 mm,
  - whether the eye shines (white dots about 2 mm across in the black eyes) come out
    clean.

## Renders

`images/cow_front.png`, `cow_three_quarter.png`, `cow_top.png`,
`cow_back.png`, `cow_side.png`: design-review renders from the real exported
parts, not photos. `cow_as_printed.png` is rendered from the toolpath itself,
so it shows what the printer will lay down.

She's in the shared viewer as "Kawaii Cow (4 colours)", replaying the
four-colour slice the checks ran on.
