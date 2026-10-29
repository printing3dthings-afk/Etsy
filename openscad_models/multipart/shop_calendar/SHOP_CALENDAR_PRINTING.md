# Shop Calendar: printing notes

2026-10-29. Your pick: form 2 of the Perpetual Desk Calendar forms, the shop
front. A little shop whose three windows show the DAY, the DATE and the MONTH.
Each sits on a drum that clicks round on a printed spring. Roll a drum from
behind the shop and the next value comes up in its window.

It's 95 mm wide, 60 mm deep and 64 mm tall.

## The prints

| print | colour | as it sits in the file | from the slicer I check with |
|---|---|---|---|
| base: floor, side walls, the four springs | brick `#B85C47` | upright | 53 min, about 32 g |
| facade: the shop front, sign and awning | mint `#A9DCC8` | face up | 32 min, about 16 g |
| roof | grey `#5A5F66` | flat | 18 min, about 12 g |
| rod: the axle | cream `#F4F1EA` | standing on its head | 35 min, about 6 g |
| day drum (MON…SUN) | cream, lettering navy `#2B3A55` | on its flange | 25 min, about 13 g |
| tens drum (0 1 2 3 0 1 2 3) | cream, navy | on its flange | 16 min, about 9 g |
| ones drum (0…9) | cream, navy | on its flange | 17 min, about 9 g |
| month drum (JAN…DEC) | cream, navy | on its flange | 28 min, about 13 g |

That's about 3 h 45 min and 110 g in all, one colour per print. Grams are PLA
at 1.24 g/cm³.

`shop_calendar.3mf` has all eight on one plate with every colour set. The
drums' lettering is its own colour part:
- **With an AMS**, it prints navy on cream and reads from across a room.
- **On one colour**, it prints raised and reads by its shadow. A paint marker
  run over the letters makes it pop.

## Print settings

- PLA, 0.20 mm layers, 0.4 nozzle, **supports off**, the orientation in the
  file.
- Every print was sliced with supports switched on and needed none.
- **Don't scale.** The drum bores, the springs and the pegs are all in
  millimetres.

## The springs come from your test plate

Each drum's flange is a notched wheel. A spring arm stands behind it with a
bump that drops into the notches: the test plate's detent coupon, stood
upright. It uses the same 5 mm wide arm, the same 16 mm from root to bump,
and the same 0.6 mm push between notches.

**I've used the plate's middle value, 1.0 mm,** since you haven't sent your
results yet. When you do:
- If 0.8 or 1.2 clicked better, it's one number (`ARM_T` in
  `shop_calendar.scad`) and a 53-minute reprint of the base. Nothing else
  changes.
- The arms stand upright here and lie flat on the plate. The bend is the same,
  but upright layers are weaker across the arm, so tell me if an arm cracks.

## Put it together

1. Stand the four drums in a row on the base, between the walls, in this
   order from the left: day (flange on its left), tens (flange on its left),
   ones (flange on its right), month (flange on its right). Each flange sits
   in front of a spring.
2. Push the rod through the hole in the left wall, through all four drums,
   and into the blind hole in the right wall. Its head sits in the left wall's
   recess.
3. Press the facade onto the four pegs on the walls' front edges. Its bottom
   stands on the pavement.
4. Set the roof on the four pegs on the walls' tops.
5. **To set the date**, reach behind the shop and roll each drum with a
   finger until its window shows what you want. Each value clicks into place.
   The date is two drums, tens and ones. The tens drum carries 0 1 2 3 twice
   round, so it's always close.

It's perpetual: nothing knows the month's length, so after the 30th or 31st
you roll it on to 01 yourself.

## What was checked before this was pushed

- **Fits, on the exported prints** (`check_calendar.py`):
  - Every drum at every one of its positions: 0 mm³ of overlap with the base,
    the rod, the facade, the roof and its neighbours.
  - Half a step between positions, the only thing each drum meets is its own
    spring's bump: 1.91 mm³, the click, behind the axle at its height.
  - The rod in the walls, the facade on its pegs and the roof on its pegs:
    0 mm³.
- **Product gate:** passes on the facade, the roof, the rod and all four
  drums. The base fails the wall check on one thing only: the four spring
  arms, 1.0 mm thick on purpose, exactly as on the test plate.
- **Supports: none, on all eight.** The fixes the slicer forced:
  1. **The drums' lettering stands out of upright faces,** so every stroke's
     underside would hang in the air. Each letter carries a skirt underneath
     sloped at 50° (the relief library's `art_skirt`), and the slicer finds
     nothing to prop.
  2. **The holes across the walls** (the rod's bore and its head's recess)
     are teardrops peaked at 52°. At 45° the slicer propped them: 7,791
     support moves.
  3. **The facade's pegs are fins with sloped undersides.** Square ones started
     their lowest edge in the air, and diamond ones started as slivers too
     thin to extrude. Both were propped.
- **Two exports were quietly incomplete, and the checks caught both.** CGAL
  dropped the awning (its scallops touched each other) and all four facade
  pegs (I'd drawn their cutter as a self-crossing outline). It said so only
  in its log. Both are fixed. The build now fails a part on that message, and
  the fit check probes the export for every peg and for the awning.
- **The windows splay open at the top and bottom.** The first renders
  showed a square 10 mm window, 10 mm deep, hiding the top half of every word
  from a desk's eye height. The facade now sits 0.8 mm off the drums'
  flanges, and each opening widens 45° toward the front. It's printed face
  up, so the splay is an upward bevel and needs no support.
- **The sign is set in Poppins, like the drums.** Playfair's hairline serifs
  were 0.3 mm wide and one dropped out of the slice. Every serif font I
  measured had about a quarter of its strokes under the 1.2 mm floor at this
  size.
- **Print fidelity** (`tools/print_fidelity.py`, every colour part): 0 flags
  on all eight. The most the slicer leaves out of any one print is 0.24 mm³,
  on the month drum: corners of the letters' skirts.
- **Fragility:** 0 high and 0 watch on all eight, the rod included.

## Renders

`images/calendar_{front,three_quarter,top}.png` and `images/calendar_back.png`
were rendered in Blender from the real exported parts, assembled, with the
drums set to THU 29 OCT. They're design-review renders, not photos.

- **Straight on**, every window shows its whole word.
- **From well off to one side** (the three-quarter view), the window frames
  hide the ends of the words. The windows splay top and bottom, but not at
  the sides, which keeps the mullions between them solid. It reads best from
  the front, as a desk calendar usually is.

`images/day_drum_as_printed.png` is the day drum rendered from its sliced
toolpath, so it's a picture the printer can actually make: every letter there,
skirts and all. The drum is also in the print viewer as "Shop Calendar (day
drum)".

## Rebuilding

- `./build.sh` exports every part (OpenSCAD's CGAL, about 12 minutes), each
  passed once through manifold3d.
- `./ship.sh` runs the fit check, gate, fidelity and fragility, and writes
  the 3MF.
- `python3 render_calendar.py --views` renders the front views, and `--back`
  renders the back.
- The STLs aren't committed; the 3MF holds every part.
