# Labeled Stacking Bin — printing notes

One parametric family, four sizes. **Two separate prints:** the bin
(`label_bin_<SIZE>.stl`, single colour) and the label tile
(`label_tile.3mf`, two parts, colours assigned). One tile fits every size.

## Real print cost — sliced, not estimated

| part | outside | time | filament | sellable? |
|---|---|---|---|---|
| **bin S** | 90 × 71.6 × 47 | **3h 59m** | 43 g | **yes** |
| bin M | 90 × 71.6 × 92 | 6h 17m | 73 g | no |
| bin L | 180 × 71.6 × 47 | 7h 08m | 75 g | no |
| bin XL | 180 × 71.6 × 92 | 11h 01m | 121 g | no |
| **tile** | 63.6 × 18.1 × 1.2 | **14m** | 1.7 g | — |

The bins are **single colour and purge nothing**. Only the tile is two-colour,
and it makes about six tool changes.

**Only S comes in under the ~4h-per-unit ceiling this shop designs to.** That
is worth saying plainly rather than shipping a "family" and letting the
arithmetic surface later: XL is a ten-hour print, which caps the printer at one
unit a day and cannot carry a margin. Treat S as the product; M/L/XL are real,
correct and gated, but they are made-to-order or personal-use sizes.

These are sliced with `tools/p1s_slice_profile.ini` as it now stands. That
profile was **changed on 2026-09-09** as part of this build: it ran BOTH
perimeter speeds at 50 mm/s, which is right for the *outer* wall (CLAUDE.md's
production rule stops ringing on the visible surface) and wrong for the inner
ones — and a thin-walled part is almost entirely perimeter, so it inherited 50
everywhere. Internal is now 200, external still 50, nothing visible changed,
and the bin went 4h 16m → 3h 44m. **Every print-time figure quoted in this repo
before that date is pessimistic, not wrong.**

## The scoop

The front of each column is scooped open so you can see into the bin and reach
in, instead of it being a plain box. It costs about 27 minutes — a sloped cut
adds perimeters and top surfaces, and it forced the front/back tongues outboard
to ±30 (a single centred tongue sits exactly where the scoop cuts and would be
deleted by it, silently). That was paid back by taking the floor to 1.6mm and
the pads to 8mm, so S still lands under 4h *with* the scoop where the plain box
was 4h 00m.

**One scoop per column, not one wide one.** Scaling a single scoop to a 180mm
bin spans ±52 and swallows the inner tongues at ±15. Per column, every scoop
sits between its own column's two tongues by construction, at any width the
family grows to. Verified on L: 10 tongues engaging, none lost.

The scoop bottoms at z=30 and the label plate tops out at z=28, so it can never
orphan the plate off the wall — the failure mode Technique 6 documents.

## Why the label is a separate tile

It was originally moulded into the bin's front face as a flush two-colour
inlay. That construction is wrong, and the reason is **purge, not looks**:

The text spans **56 layers**, so a two-colour print makes **112 tool changes**,
each flushing into the wipe tower.

| flush volume | purge |
|---|---|
| 150 mm³ (tuned, similar colours) | 20.8 g |
| 250 mm³ | 34.7 g |
| **350 mm³ (Bambu default)** | **48.6 g** |

**The bin weighs 45 g.** At stock settings you would throw away more plastic
than the part. Worth noting the earlier "3h 53m / 45 g" figure for the moulded
version was a *single-extruder* slice — it never modelled the colour change or
the wipe tower at all, so it was never the real cost.

A tile printed **flat, text face down on smooth PEI** puts the text in three
layers: six tool changes, ~2.6 g, and a mirror-smooth face. It is also
**re-labelable** — swap a 14-minute tile instead of reprinting a four-hour bin,
which is the actual point of a labelled storage system.

**Slide-in, not snap.** A snap needs a spring-force calculation, fatigues, and
fights you every time you change it. The slot has none of that: the tile drops
in from the top under gravity and lands on a 1.5mm stop. Two lips overhang the
opening by 2.0mm each, so the 63.6mm tile cannot pass back out through the
60.0mm mouth — **retained by 1.80mm per side**. Verified: a seated tile
intersects the bin at **EMPTY**.

## The label

The point of the design. A printed bin normally gets a peel-off sticker; this
one carries its label as a second filament, flush in a raised plate, so it
cannot peel or fade.

Change it by re-rendering the tile with `-D 'label="SCREWS"' -D 'part="tile"'`
(and `part="tiletext"`). **Check any new word before printing it:**

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
- tongue **must** enter pocket → **S: 144 mm³ / 6 tongues · L: 240 mm³ / 10
  tongues**, full 2.00 mm each

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
