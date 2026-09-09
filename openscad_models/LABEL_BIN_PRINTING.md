# Labeled Stacking Bin — printing notes

One parametric family, four sizes, two colours. `label_bin_<SIZE>.3mf` is the
file to print — one object, two parts, colours already assigned.

## Real print cost — sliced, not estimated

| size | outside | time | filament | sellable? |
|---|---|---|---|---|
| **S** | 90 × 71.6 × 47 | **3h 44m** | 46 g | **yes** |
| M | 90 × 71.6 × 92 | 6h 04m | 80 g | no |
| L | 180 × 71.6 × 47 | 6h 32m | 77 g | no |
| XL | 180 × 71.6 × 92 | 10h 06m | 130 g | no |

**Only S comes in under the ~4h-per-unit ceiling this shop designs to.** That
is worth saying plainly rather than shipping a "family" and letting the
arithmetic surface later: XL is a ten-hour print, which caps the printer at one
unit a day and cannot carry a margin. Treat S as the product; M/L/XL are real,
correct and gated, but they are made-to-order or personal-use sizes.

**Slice with internal perimeters at ~200 mm/s.** The shop profile runs BOTH
perimeter speeds at 50 mm/s, which is right for the *outer* wall (CLAUDE.md's
production rule — it stops ringing on the visible surface) and wrong for the
inner ones. A thin-walled bin is almost entirely perimeter, so it inherits the
outer-wall speed everywhere: **3h 44m at 200 mm/s internal vs 4h 16m at 50.**
External perimeter stays 50 and nothing visible changes. This applies to every
thin-walled part this shop prints, not just the bin.

## The label

The point of the design. A printed bin normally gets a peel-off sticker; this
one carries its label as a second filament, flush in a raised plate, so it
cannot peel or fade.

Change it by re-rendering with `-D 'label="SCREWS"'`. **Check any new word
before printing it:**

```sh
python3 tools/glyph_probe.py "SCREWS" --font "Montserrat:style=Black" --size 11
```

Require **≥2 extrusions** on the thinnest stroke and a glyph width under the
plate's own (76mm on S/M, and `plate_w` is capped at 76 for L/XL too). "PARTS"
at size 11 measures 52.1 × 11.2mm with a **7.94-extrusion** stroke — a wide
margin. A longer word needs `label_size` reduced, and the check re-run.

This matters because it is exactly how this shop has failed before:
"OnBrandCraftz" in Caveat Bold measured 0.48–1.08 extrusions and printed
**blank** on three of four sauce models, and every check then in place passed
it. `inlay_probe` confirms the second colour survives slicing here: **1.16% of
layers thin, 0.08% of volume at risk**, median region width 0.789mm.

## Stacking

Four short tongues on the rim drop into four pockets in the base of the bin
above. Verified both ways, which is the only way this is worth claiming:

- solids **must not** touch → `intersection()` = **0.0000 mm³** (a single
  degenerate facet at the contact plane, which is the bins resting on each
  other, not overlapping)
- tongue **must** enter pocket → **96.0 mm³ across 4 tongues, full 2.00 mm**

Sizes share a 90mm grid, so an L bin stacks across two S bins.

## Two failures worth keeping

**A continuous lap joint severs the floor.** The obvious design — rim lip, base
recess — puts a ring-shaped recess in the base as deep as the floor is thick,
which removes the floor's outer edge for its full thickness and detaches the
floor from the wall all the way around. It renders fine. The watertight check
caught it; no render would have. It also does not fit: skirt + gap + lip is
three zones across a 1.68mm wall, ~0.5mm each.

**Wall thickness wants to be a whole number of extrusions.** 1.6mm and 1.68mm
look interchangeable. They are not: 1.6 leaves 0.34mm the slicer fills with
slow gap-fill segments, and the same bin sliced **48 minutes slower on less
material**. 1.68 = exactly 4 × 0.42.

Also re-learned the hard way: the pads and tongues live inside the cavity's
footprint, so unioning them before the cavity is cut deletes them silently —
the model still gates watertight and is simply 2mm shorter with no stacking
feature. Caught by the bounding box reading 45mm instead of 47.

## Verified before shipping

All four sizes: watertight, one body, in the envelope, zero degenerate faces,
no terracing. Overhang past 55° on S is 2.87 cm² and every bit of it is a short
bridge — the maker's mark ceiling (0.7mm) and the four stacking pocket ceilings
(1.7mm wide). Nothing needs support.

Bin ∩ label = **0.00000 mm³**. Printed as-assembled, the inlay fills the letter
pockets and terracing drops to 0.00 cm².

## Not yet true

**Nothing here has been printed.** Every number is measured off the real mesh
or read from a real slice — but a physical print outranks all of it.
