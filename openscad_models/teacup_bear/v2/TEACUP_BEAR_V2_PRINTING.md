# Teacup Bear v2: the Santa-style rework

2026-11-05. You said "Try the bear" after the Kawaii Cow v2. This is the same
treatment. v1 (`../teacup_bear.py`, `../teacup_bear.3mf`) is untouched; this
sits beside it.

The images are design-review renders made from the real exported parts, not
photos. Nothing here has been printed yet.

## What changed

v1 is one piece. Her head is blended into her body, and the support grown
under her chin and muzzle shows as a soft cone where a neck should be.

v2 is three prints:

| print | colours | prints | size (mm) |
|---|---|---|---|
| cup | cream saucer, cup and handle; pink rim band, ring and heart; brown tea | upright | 60 × 58 × 38 |
| body | tan; pink collar; cream chest patch | upright, on its flat bottom | 32 × 34 × 23 |
| head | tan; cream muzzle; brown eyes and nose; pink cheeks and inner ears | upright, on its own flat neck | 33 × 29 × 29 |

Assembled she is **60 × 58 × 69 mm**, 3 mm taller than v1.

- **A real head on a real body.** The head sits in a pink collar, which hides
  the seam (DETAIL_STANDARD rule 8: a band where two forms meet). Her neck
  narrows 33° down into her chest, so her chest slopes under her chin.
- **She stands a little taller.** Her head rides 3 mm higher than v1's, on a
  taller body.
- **A cream patch on her chest**, like a plush's.
- **The tea is filled to the brim.** v1's tea was 2 mm below the rim.
  - Printed on her own, her paws on the rim had nothing under them. The
    cones that would hold them up would have to stand where the cup's wall
    is.
  - With the tea flush, the tea and the rim are one level, and that level is
    her body's plate. Her bottom and her paws' soles both stand on it.
  - So her paws stay on the rim, as in your pick.

## Files

All three prints on one plate, in two files of the same parts:
- **`teacup_bear_v2_bambu.3mf`, for Bambu Studio.** It is written the way
  `tools/bambu_slice.py` writes its slices. Bambu Studio 2.8 reads only the
  first part of each object in the shop's usual 3MF layout.
- **`teacup_bear_v2.3mf`, for PrusaSlicer and the shop's checks.**

The AMS slots, the same in both:

| slot | colour | hex |
|---|---|---|
| 1 | cream | `#F4F1EA` |
| 2 | brown | `#4A2E22` |
| 3 | pink | `#F6A6C1` |
| 4 | tan | `#C68E5E` |

PLA, **no supports on any print**. Print 0.12 mm layers for a sale print, as
v1 notes: her face has small round forms.

## Assembly

1. Stand her body on the tea, over the peg in the middle. The peg has a flat
   side, so it only goes on one way. Her paws land on the rim.
2. Push her head onto the peg on her neck, also keyed.
3. A drop of glue on each peg. They are 0.15 mm glue fits.

## Time, filament, colour changes

All from the same PrusaSlicer P1S slice and the viewer's motion model, at
0.2 mm, so the two versions compare like for like:

| | v1 (one piece) | v2 (three prints) |
|---|---|---|
| filament changes | 315 | 306 |
| filament incl. purge | 96.9 g | 88.3 g |
| time | 9.3 h | 9.4 h |

**The split doesn't save colour changes here, unlike the cow.** v1 already
kept its colours to height bands. v2's head still needs all four colours.
The gain is the look, not the print.

## Checks (all in `checks/`)

- **Product gate:** all three prints pass, with 0 support moves each.
- **Fit (`check_fit_v2.py`):**
  - Each print is one closed body.
  - No two parts overlap.
  - Both pegs sit wholly inside the part above them, with a 0.15 mm gap all
    round.
  - All of her bottom and paws sit within 0.35 mm of the tea and rim.
- **Print fidelity:** the cup and head have no flags.
  - The body has one: a single 0.2 mm layer, 1.7 mm wide, in the crease
    under the collar at her right shoulder.
  - It's a tiny notch under the collar tube. I left it.
- **Fragility:** 0 high, 0 watch.

## What was tried and dropped

- **A bow at the front of the collar.** It stood 5 mm out over her chest. The
  support cones under it ended in keels the slicer propped: 654 moves.
- **Her neck cut flat 5 mm down.** Her muzzle makes the head's footprint stand
  6 mm out past her chest, so the neck's front hung over air: 404 moves.
- **Her neck run straight down to the tea.** It printed clean, but it made her
  torso a block.
- **Her neck narrowing 33° into her chest** is what shipped.

## Honest read

Better than v1:
- The head reads as a head, on a collar, instead of melting into a cone.
- The chest patch adds a plush detail.
- The cup is unchanged and still pretty.

Not better, and worth your eye:
- **Her torso is a little square** between her arms.
- **Her arms read less** than in v1, where they draped over the rim.
- **The tea is now flush**, so the cup's inner lip is gone.
- **No print saving**, and she needs gluing (two pegs) where v1 came off the
  plate finished.

## Rebuild

`python3 teacup_bear_v2.py` rebuilds `parts/` in about 2 minutes. Then:
- `python3 check_fit_v2.py`
- `python3 render_teacup_bear_v2.py`, or `--plate`

It needs scikit-image and manifold3d, like v1.
