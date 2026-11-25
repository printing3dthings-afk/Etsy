# TEST — Snap-Fit Coupon

Title: TEST — Snap-Fit Coupon

## Description

Snap-fits fail when they're sized by guesswork. This coupon sizes them by
the strain formula instead — ε = 1.5 × thickness × deflection ÷ length² —
and lets you find the exact point where matte PLA stops forgiving.

Five cantilever arms print flat on one plate (168 x 62 mm), each with its
tip hook already engaged in a catch pocket with 0.3 mm clearance. The hook
sits 1.3 mm deep in the pocket, so every arm must deflect exactly 1.3 mm
sideways to release. The arms are tapered, root-filleted, and engraved with
their length and design strain: 0.8%, 1.2%, 1.6%, 2.0% and 2.5%. For PLA,
about 1.2% is the repeated-use limit and 2.0% the single-snap limit — this
plate brackets both.

### How to test

Flex each tip sideways until the hook pops out of its pocket, let it snap
back, and repeat 10 times. Note which arms stay crisp, which whiten at the
root, and which crack. The highest strain that survives 10 cycles is your
design ceiling for parts that open and close; the 2.0% arm is for
snap-once-and-done fits.

| Arm | Design strain | Survived 10 cycles? | Whitening? | Cracked at cycle |
|---|---|---|---|---|
| L22 | 0.8% |  |  |  |
| L18 | 1.2% |  |  |  |
| L15 | 1.6% |  |  |  |
| L14 | 2.0% |  |  |  |
| L13 | 2.5% |  |  |  |

### Profiles and material

Both profiles are matte white PLA, 3 walls, supports off, clearances
identical — only the layer height differs, so any fit difference between
them is the layers:

- Standard: 0.20 mm Standard - verified slice 1 hr 35 min - 40.42 g
- Optimized: 0.16 mm Optimal - verified slice 1 hr 58 min - 44.05 g (finer layers
  round the hook and pocket edges slightly differently — snap both and
  compare the feel)

MakerWorld may display its own re-sliced time and filament estimates.

The gallery images are renders of the plate until the print is photographed.

## Profile copy — Standard

Prints the Snap-Fit Coupon: a 168 x 62 mm plate with five tapered cantilever snap arms (design strains 0.8 / 1.2 / 1.6 / 2.0 / 2.5% at 1.3 mm release deflection), each hook printed engaged in its catch pocket with 0.3 mm clearance, arms labelled with length and strain. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports off, ironing on top faces. Verified slice: 1 hr 35 min - 40.42 g.

## Profile copy — Optimized

Prints the Snap-Fit Coupon: a 168 x 62 mm plate with five tapered cantilever snap arms (design strains 0.8 / 1.2 / 1.6 / 2.0 / 2.5% at 1.3 mm release deflection), each hook printed engaged in its catch pocket with 0.3 mm clearance, arms labelled with length and strain. Matte white PLA, 0.16 mm Optimal, 3 walls, 12% gyroid infill, supports off, ironing on top faces. Verified slice: 1 hr 58 min - 44.05 g. Same clearances as Standard — the finer layers are the only difference, so compare the snap feel between the two prints.
