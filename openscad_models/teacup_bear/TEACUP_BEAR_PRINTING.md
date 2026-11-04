# Teacup Bear

2026-11-04. Your pick, shape 1 of five: a chubby bear peeking over the rim of
a teacup on its saucer, paws on the rim. One print, no supports, no assembly,
no glue.

**Size:** 60 × 58 × 66 mm tall, the handle included.

**File:** `teacup_bear.3mf`, four colours, AMS slots in this order:

| slot | colour | hex | what |
|---|---|---|---|
| 1 | cream | `#F4F1EA` | saucer, cup, handle, her muzzle, eye shines |
| 2 | tan | `#C68E5E` | the bear |
| 3 | brown | `#4A2E22` | eyes, nose, the tea, the OBC mark |
| 4 | pink | `#F6A6C1` | cup rim, the heart on the cup, saucer ring, cheeks, inner ears |

## Printing

- PLA, standing on the saucer as the file opens, **no supports**.
- **0.12 mm layers for a sale print.** Her face is small round forms. 0.2 mm
  works for a test.
- **Time and filament, one colour, PrusaSlicer with the P1S settings:**
  - 0.2 mm layers: 46 min, 24 g
  - 0.12 mm layers: 1 h 3 min, 21 g
- **Colour changes:** PrusaSlicer counts 315 filament changes, about half the
  Kawaii Cow's 595.
  - The colours keep to height bands. The cup and saucer are cream, the bear
    above them tan, and her brown and pink sit mainly in the band of her face.
  - The cup's pink rim band and heart, and the brown tea, still share layers
    with the cream. That's why it isn't lower.
  - Bambu Studio orders colours more efficiently and shows the real time and
    purge. Check it there before pricing.

## How she's made

Same method as the cow: blended round shapes in Python (`teacup_bear.py`,
using `tools/sdf_figure.py`). Every size is a named number at the top of the
file. Run `python3 teacup_bear.py` to rebuild, about 4 minutes.

**The pose is also the support plan:**
- Her body rises out of tea that fills the cup to 2 mm under the rim, so her
  head sits on her body, not over air.
- Her paws rest on the rim.
- The cup widens at most 0.63 mm per mm, which is 32° from upright, so it
  needs no support.
- The handle and her round ears are thin upright plates, made printable in
  their own plane.
- The handle's hole is a teardrop pointing up, its roof 28° from upright.
  It's cut exactly after the shape is built. Cut any other way, the slicer
  propped it.

## Checked before it was pushed

The results are in `checks/`.

- **Product gate: passed.** 0 support moves and 0 overhang perimeters, on the
  full height. Walls 2.45 mm at the 1st percentile, and 75% of the footprint
  on the plate.
- **Print fidelity, all four colours: 0 flags.**
  - 1.4 mm³ dropped in slivers, nothing filled, 0.08 mm³ in the wrong colour.
  - The first build had 3 flags: the white shines in her eyes were 1.5 mm
    balls, and only a 0.6 mm dot of each reached the eye's surface. The slicer
    dropped part of each. They're 2 mm now and print whole.
- **Fragility:** nothing high and nothing on watch.
- **Not tested on the printer yet.** The parts I'd look at first:
  - the handle, whose thinnest part is 3.2 mm,
  - the eye shines, white dots 2 mm across.

## Renders

In `images/`: `teacup_bear_front.png`, `_three_quarter.png`, `_top.png`,
`_back.png`, `_handle.png`. These are design-review renders from the real
exported parts, not photos. `teacup_bear_as_printed.png` is rendered from the
toolpath.
