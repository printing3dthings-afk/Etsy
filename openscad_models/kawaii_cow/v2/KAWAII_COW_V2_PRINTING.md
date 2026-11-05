# Kawaii Cow v2: the Santa-style rework

2026-11-05. You asked me to try the Santa print's approach on our cow and see
if it looks better. This is that try. v1 (`../cow.py`, `../kawaii_cow.3mf`)
is untouched; this sits beside it.

The images are design-review renders made from the real exported parts, not
photos. Nothing here has been printed yet.

## The idea, taken from the Santa

The Santa looks better because it is split. Each part prints the way that
suits it, and each joint hides under something (his neck in the beard).
v1 is one piece in four colours, every part blended into the next, so she
reads as one soft blob. Her ears point up because hanging ears had nothing to
print on. Her heart is a coloured skin.

v2 keeps her pose and makes five prints:

| print | colours | prints | size (mm) |
|---|---|---|---|
| body | white, black spots and hooves, red collar | upright | 44 × 57 × 39 |
| head | white, pink muzzle and cheeks, black spot and eyes | upright, on its own flat neck | 40 × 37 × 44 |
| right ear | white, pink inside | flat, pink face up | 20 × 9 × 2.6 |
| left ear | black, pink inside | flat, pink face up | 20 × 9 × 2.6 |
| heart | red | flat on its back | 29 × 28 × 12 |

Assembled she is **66 × 58 × 72 mm**, a little taller than v1 (66 mm).

What the split buys:
- **A real head on a real body.** The head sits in a red collar, which hides
  the seam (DETAIL_STANDARD rule 8: a band where two forms meet).
- **Ears that hang out sideways** like a cow's, which no single-piece print
  allowed. Each has a tab that goes into a slot in the head.
- **A crisp heart.** It is one colour, printed flat, with a stitched seam
  round its face.
- **Shaped detail instead of only colour:** a forelock of three curls,
  longer horns, deeper nostrils, and a tail tuft in locks.

## File

All five prints on one plate, in two files of the same parts:
- **`kawaii_cow_v2_bambu.3mf`, for Bambu Studio.** It is written the way
  `tools/bambu_slice.py` writes its slices. Bambu Studio 2.8 reads only the
  first part of each object in the shop's usual 3MF layout.
- **`kawaii_cow_v2.3mf`, for PrusaSlicer and the shop's checks.**

The AMS slots, the same in both:

| slot | colour | hex |
|---|---|---|
| 1 | white | `#F4F1EA` |
| 2 | black | `#2B2433` |
| 3 | red | `#D7263D` |
| 4 | pink | `#F6A6C1` |

PLA, **no supports on any print**. Print 0.12 mm layers for a sale print, as
v1 notes: her face has small round forms.

## Assembly

1. Push the head onto the peg on her neck. The peg has a flat side, so it
   only goes on one way. It is a 0.15 mm glue fit: a drop of glue holds it.
2. Push each ear's tab into its slot in the side of the head, pink face
   forward. The black ear goes on her left (your right as you face her).
   Glue.
3. Stand the heart on its tip in her lap, its flat back against her chest.
   Her arms hold its sides. A drop of glue on its back.

## Time, filament, colour changes

All from the same PrusaSlicer P1S slice and the viewer's motion model, at
0.2 mm, so the two versions compare like for like. Slice in Bambu Studio for
real numbers before pricing.

| | v1 (one piece) | v2 (five prints) |
|---|---|---|
| filament changes | 595 | 347 |
| filament incl. purge | 147.5 g | 100.6 g |
| time | 16.9 h | 10.8 h |

The saving comes from the split. The heart is one colour, so it needs no
changes at all. The ears need 7 each. v1's four colours ran her whole height.

## Checks (all in `checks/`)

- **Product gate:** all five prints pass, with 0 support moves each.
- **Fit (`check_fit_v2.py`):**
  - Each print is one closed body.
  - No two parts overlap.
  - The neck peg sits wholly inside the head, with a 0.15 mm gap all round
    (median and 5th percentile).
  - Each ear's tab is inside the head.
  - 70% of the heart's back is within 0.35 mm of her.
- **Print fidelity:** head, heart and ears have no flags.
  - The body has one: a single 0.2 mm layer of white, 2 mm wide, at z 27 in
    the crease between the collar and the neck top.
  - The head's bulge overhangs it by 5 mm, so it shows only from very low
    angles. I left it.
- **Fragility:** 0 slender runs.

## What was tried and dropped

All were cut or removed after the slicer propped them:

- **A smile** under the nostrils. It sat on the muzzle's lower face, which
  looks down, so its groove's ceiling hung: 301 support moves.
- **Rings round the horns.** On a leaning horn a groove's ceiling hangs.
- **A peg from her chest into the heart.** Its underside is a cantilever
  over air: 382 moves. A peg out of the heart's back can't print, because
  that face lies on the plate. The heart is glued instead.
- **Slots cut into the field.** Marching cubes rounds a sharp roof's peak
  into a flat strip a voxel wide, and the slicer props that strip. The ear
  slots and the neck socket are now exact solids, cut after meshing.

## Fixed in the shared tools on the way

- **`tools/virtual_printer.py`**: its junk check now catches `inf` and `nan`
  coordinates.
  - The body's first three-colour slice had 339 wipe-tower moves to `Yinf`.
    The check only looked for numbers, so it kept that slice as good.
  - Regression test: `tests/test_virtual_printer_junk.py`.
- **`tools/assemble_3mf.py --plate`**: it now puts each object's place on the
  plate into its vertices.
  - It used to put the place on the object's `<item>` as a transform.
    PrusaSlicer 2.7 applies that transform only to an object's FIRST colour
    part.
  - On this plate the head's pink and black, and each ear's pink, sliced 50
    to 140 mm away from their white.
  - Single-colour objects never showed it. Any multi-colour object made with
    `--plate` before today may have the same fault in PrusaSlicer.
  - Regression test: `tests/test_assemble_3mf.py`.

## Honest read

Better than v1:
- The head reads as a head.
- The ears hang like a cow's.
- The horns are longer, and there is a forelock.
- The heart is crisper and stitched.
- She needs about 40% fewer colour changes.

Not better, and worth your eye:
- **The collar from the front.** The heart sits under the chin, so the
  collar can't run round the front. Its two rounded ends sit either side of
  the chin and can read as little red paws.
- **The side view is squarer than v1** where her chest meets the back of
  the heart.
- **She now needs gluing.** That's five parts to assemble, where v1 came
  off the plate finished.

## Rebuild

`python3 cow_v2.py` rebuilds `parts/` in about 6 minutes. Then:
- `python3 check_fit_v2.py`
- `python3 render_cow_v2.py`, or `--plate` for the parts as they print

It needs scikit-image and manifold3d, like v1.
