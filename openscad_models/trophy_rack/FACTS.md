# FACTS: Trophy Rack medallion, v3 (and v2)

Every number comes from this folder. The source is on each line (STANDARDS 15).

## Version
- **v2**, 2026-11-14 (`bb939e6`), then the tips in skin colour, Scott's pick (`4f0063e`).
- **What v2 changed from v1:**
  - folded ribbon tails;
  - a rounded band;
  - thicker lettering, so it prints;
  - larger, sagging domes;
  - angled tips.
- **v1** was the first model, in 5 colours (`71d1b0d`). It's replaced.
- **For Scott's own use; not a shop product.** It's reproduced from Scott's photos of a
  Mardi Gras bead pendant.
- **Not printed yet,** as far as this folder knows. Every image here is a render.

## v3 (2026-11-25, `v3/`): Scott's fixes after printing v2
Scott: "the nipples need to be way shorter so they don't break off. Make sure the ring for the
keychain is really strong. I need this to be a very high quality product."

| what | v2 | v3 | source |
|---|---|---|---|
| Tips | a 3.2 mm peg standing 4.2 off the dome; they broke off | a rounded nub 1.6 off the dome, flaring into a 6.4 mm foot | `v3/trophy_rack_v3.scad` |
| Keychain tab thickness | 3.0 | 5.0 (the rim's full height) | the same |
| Ring round the hole | 2.0 wide: 6 mm² at its top, the part's thinnest section | 3.2 wide: 16 mm² | the same; `checks/fragility.txt` |
| Hole | 4.0, sharp edges | 4.5, edges chamfered | the same |
| Neck into the shield | 9 wide | 16 wide | the same |
| Overall thickness | 17.9 | 15.7 | `v3/trophy_rack_v3_union.stl` |

- **Checks (`v3/logs/`):**
  - **Product gate PASS:** min wall 2.4 at the 1st percentile, no supports. The lettering is
    declared as detail.
  - **Print fidelity:** 0 flagged.
  - **Fragility:** 0 high, 0 watch, 0 slender runs. v2 had one slender run, at the ring.
- **Slices** (Bambu Studio, P1S 0.4, PLA Basic, 3 walls, 15%, shop retail settings, no supports):
  - `v3/trophy_rack_v3.gcode.3mf`, 0.20 Standard: **2 h 58 m 44 s, 50.4 g** (black 10.3, yellow
    5.2, skin 13.1, cream 21.8).
  - `v3/trophy_rack_v3_fine.gcode.3mf`, 0.12 Fine: **4 h 41 m 50 s, 69.5 g**. Finer layers mean
    more colour swaps, so more purge.
  - Most of the grams are purge from the colour swaps, not the medallion (about 12 g): see
    "What the difference is" below.
- **Not printed yet.** `v3/images/` are renders.
  - `trophy_rack_v2_v3_compare.jpg` shows v2 and v3 from the same camera.
- **Status:** Scott called it "a very high quality product" (2026-11-25). Whether it's sold, and
  where, is his call. The sections below still describe it as his own piece.

## What it is
- **Shield:** a black rim with a hanging tab (2 mm hole for a jump ring) and a yellow field.
- **Domes:** two skin-colour domes with tips.
- **Banner:** a cream ribbon across the bottom, with "TROPHY RACK" raised in black,
  following its curve.

## Numbers
| what | value | source |
|---|---|---|
| Size | 63 mm wide (shield), 89 mm across the ribbon tips, 18 mm thick at the tips | `PRINTING.md`; `parts/all.stl` measures 89.0 x 67.6 x 17.9 mm |
| Hanging hole | 2 mm, for a jump ring | `PRINTING.md` |
| Lettering | raised 0.8 mm; strokes grown 0.22 mm a side, thinnest about 0.65 mm | `PRINTING.md` |
| Colours (one AMS) | black `#1A1A1A`, yellow `#E8C21A`, skin `#E7A976`, cream `#F2EDE2` | `PRINTING.md` |

## Print time and filament
**Quote Benson's MakerWorld profiles to buyers; they're the files a buyer prints.** Read from
the shipped .3mf files (`threads/2026-11-18_three-walls-reslice.md` on main, 2026-11-19):

| MakerWorld profile | walls, infill | time, filament |
|---|---|---|
| Standard (one colour) | 3, 15% grid | 25 min, 15.9 g |
| Optimized (one colour) | 3, 12% gyroid | 37 min, 16.9 g |
| Multicolour – Standard | 3, 15% grid | 2 h 07 min, 32.7 g |
| Multicolour – Optimized | 3, 12% gyroid | 2 h 49 min, 37.7 g |

**Our own slices, reconciled 2026-11-25 (OPEN row 23; logs in `checks/reconcile_2026-11-25/`).**
Bambu Studio, P1S 0.4, PLA Basic, 0.20 mm Standard, 3 walls, 15%, no supports:

| slice | time | filament |
|---|---|---|
| one colour, Bambu's stock settings | 25 m 5 s | 15.1 g |
| one colour, the shop's retail settings (outer wall 50 mm/s, ironing) | 37 m 42 s | 14.8 g |
| four colours, stock settings | 2 h 43 m 12 s | 50.1 g |
| four colours, retail settings (`checks/trophy_rack.gcode.3mf`) | 2 h 58 m 23 s | 50.1 g (black 10.1, yellow 5.2, skin 13.2, cream 21.8) |
| four colours, retail, no prime tower | 2 h 40 m 44 s | 43.9 g |

**What the difference is:**
- **One colour agrees with Benson** (25 m 5 s / 15.1 g on stock settings, against his
  25 min / 15.9 g). The time gap in our retail slice is our slower outer wall and ironing.
- **In four colours, the gap is purge.** Our 50.1 g is about 12 g of model, 7 g of prime
  tower and 28 g flushed over 38 colour swaps (counted from the G-code). The flush volumes are
  Bambu's own for these four colours (black to cream, the biggest, is 561 mm³ a swap).
- Benson's multicolour profile purges about 17 g less. That points at his colours, or his flush
  volumes, differing from ours, but his settings file isn't in this repo, so that part isn't
  confirmed. Asked on main (row 23).

**Superseded:** 2 h 54 m, about 47 g, sliced 2026-11-14 at 2 walls.

## Checks (`checks/`)
- **Product gate: PASS.** The raised lettering is declared as detail.
- **Print fidelity:** 0 flags.
- **Fragility:** 0 high, 0 watch.
- **Colour parts:** no two overlap.

## Free or paid, per platform
- **MakerWorld:** model 3614594, private, with Benson's 4 profiles (Standard, Optimized,
  Multicolour Standard, Multicolour Optimized). From `threads/2026-11-15_benson-mw-status.md`
  on main.
- **Etsy:** not listed. It's for Scott's own use.
- Whether it ever goes public is Scott's call.

## Safe to say, word for word
- "A trophy rack medallion: shield, two domes and a TROPHY RACK banner."
- "Four colours on one AMS, printed flat, no supports."
- "89 mm across the ribbon."

## Don't say
- That it's a shop product or for sale. It isn't.
- That it's printed. Not yet.
- Anything implying it's an official or licensed Mardi Gras item. It's Scott's own piece,
  from his photos.

## Media
| file | shows | version |
|---|---|---|
| `images/trophy_rack_front.png` | straight on, design-review render | v2, tips in skin colour |
| `images/trophy_rack_angle.png` | at an angle, render | v2 |
| `images/trophy_rack_compare.jpg` | the render beside Scott's photo | v2 |

## Light fit
- Not a light piece.
