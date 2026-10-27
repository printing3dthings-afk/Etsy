# Fit test plate — print once, tell me what worked

2026-10-27. Before any multipart product is drawn for real, this one plate
finds the clearances that work on **your** P1S with **your** filament. Every
product after it uses the numbers you report back, not a guess.

**File:** `fit_test_plate.3mf` (33 parts, one plate, one colour). The
separate STLs are in `parts/` if you want to reprint one.

## Print settings

- Any PLA you'll use for the products (one colour is fine), textured or smooth
  PEI.
- Bambu Studio **0.20mm Standard**, 0.4 nozzle. **Supports OFF**: none of the
  33 parts needs any (checked by slicing each one with supports on: 0 support
  moves on every part, and 0 on the whole plate).
- Sliced estimate: **about 3 h 40 min, about 93 g**, 16 mm tall.
- Leave the default 2 walls. Don't scale anything: the clearances are absolute
  millimetres.

## What's on it

Five mechanisms, one per product. Each is a mating pair printed three times,
at three clearances. **Every part has its clearance engraved on its tab**, so
match tab to tab. The gears and detent wheels are identical across the three
sets; their clearance is on the base they sit on.

| mechanism | for | parts | engraved values |
|---|---|---|---|
| thread, 24 mm, pitch 3 | Nesting Characters | screw + nut | 0.2 / 0.3 / 0.4 (gap all round) |
| ball joint, 8 mm ball | Creature Kit | ball on a stem + split socket | 0.4 / 0.6 / 0.8 (how much narrower the socket's mouth is than the ball) |
| gear pair, module 1.5, 20 + 10 teeth | Kinetic Toy | base with two pins + two gears | +0 / +0.15 / +0.3 (extra space between the gears' centres) |
| detent, 12 clicks | Perpetual Calendar | base with a spring arm + notched wheel | 0.8 / 1.0 / 1.2 (spring arm thickness) |
| bayonet twist-lock | Candy Dispenser | ring + cap | 0.2 / 0.3 / 0.4 (gap around the lugs) |

## How to test each one

1. **Thread:** screw the nut onto the screw (either way up). Note which
   values turn by hand all the way down without forcing, and which feel
   wobbly.
2. **Ball joint:** turn the ball over and push it into the socket's mouth.
   It should snap in with a firm push and stay in any pose you leave it in.
   Note which ones: won't go in, snap in and hold a pose, or flop.
3. **Gears:** press both gears onto the pins (the big gear on the wider end).
   Spin the big one. Note which turn smoothly, which bind, and which
   skip or rattle.
4. **Detent:** press the wheel onto the pin under the arm. Turn it. It should
   click into each of the 12 notches and stay put. Note which click firmly,
   which are too stiff to turn, and which arms crack or barely click.
5. **Bayonet:** turn the cap over, line its three lugs up with the ring's
   three openings, push down, and twist about a quarter turn. Note which
   go in and twist smoothly, which jam, and which feel loose.

## What to send back

One line per mechanism is enough, e.g.:

> thread 0.3 · ball 0.6 · gears +0.15 · detent 1.0 · bayonet 0.3

If two values both work, give me both and say which feels better. If none
work (all too tight or all too loose), say which way: I'll make a second plate
around that end rather than guess. A photo of anything that cracked helps.

## What was checked before this was pushed

- **Fits, assembled:** `check_fits.py` puts each pair together as used and
  measures the overlap: thread, ball seated, gears through a whole tooth,
  wheel in a notch, cap lowered in and twisted to the stop. All 0 mm³. The
  intended interference is there too: the ball overlaps the socket mouth
  (1.4 / 2.9 / 4.6 mm³, the snap), and the detent bump overlaps the rim
  between notches (4.2 mm³, the click).
- **Supports:** every part sliced with supports on, 0 support moves.
  Getting there meant steepening every 45° slope to 39–40° off vertical
  (thread flanks, the ball's neck, the bayonet's lugs and slot roof): Bambu
  Studio puts support under exactly 45°.
- **Product gate:** passes on every part except two, both on purpose:
  - the **detent arm** is 0.8–1.2 mm thick because it is the spring being
    tested;
  - the **20-tooth gear's** tooth tips are under 1.2 mm, as every gear's are.
    Print fidelity shows nothing of the gear dropped in the slice.
- **Print fidelity:** 0 flags on every part (the first labels were too fine
  and lost a stroke, so they were enlarged).
- **Fragility:** 0 slender members on any part.

## Rebuild

`./build.sh` exports all 33 parts, runs the fit check and writes the 3MF.
`./build.sh parts` exports only. Source: `fit_test_plate.scad`, with threads
from `../thread_lib.scad`.
