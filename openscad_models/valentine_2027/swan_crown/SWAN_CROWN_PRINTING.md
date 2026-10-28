# Swan Crown Love Lantern — printing notes

Built 2026-10-26/27 from Scott's Valentine's 2027 brief. Form 3 of five
(`../concepts/lantern_forms.jpg`), picked with the Standing Heart.

A glowing drum over a battery LED tealight, in three prints:

- **the drum:** its glass is a 0.9 mm wall all the way round. Built into its
  inside is a pond at night: two swans glide to meet under a heart, among
  reeds, under a crescent moon. Unlit the drum looks plain; lit, the scene
  shows dark on the glow, the way a lithophane does. The two names and the
  date stand out of the plinth's front.
- **the lid:** it sits in the collar on the drum's rim. Hearts are cut through
  it, so the light shows above.
- **the crown:** two swans whose necks draw a heart. It stands in the slot in
  the lid's boss.

The drum is open at both ends: it lifts off and goes back down over the light,
and it is 78 mm across inside, room for any tealight. The drum measures
88 × 89 × 87 mm, the lid 82 mm across, and the crown 66 × 52 mm.

The crown prints flat on its face. Stood up as it is shown, its bowed heads
and the inside of its notch would hang in the air; flat, every line is on the
plate. Its top edge has a stepped bevel.

The maker's mark, OBC, is engraved 0.8 mm into the underside of a foot inside
the plinth. It reads O-B-C with the drum tipped back to look at its base. This
was checked on the exported geometry, not assumed.

## Print

| setting | value |
|---|---|
| file | `swan_crown_lantern.3mf`: three objects on one plate, drum, lid and crown |
| filament | **matte white PLA**, one colour: assign it to every part |
| layer | 0.2 mm, Bambu's 0.20 Standard on the P1S, 0.4 nozzle |
| supports | **off**. The slicer finds none to add on any of the three (gate, below) |
| plate | textured PEI |
| time | drum about 1 h 28 m, 46 g; lid 23 m, 14 g; crown 11 m, 4 g (P1S motion model, each sliced alone) |

The parts are colour only, so the renders can show them apart:

| part | what it is |
|---|---|
| frame | the plinth, the rim and its collar, the foot with the mark |
| glass | the glowing drum wall |
| art | the pond scene, inside the glass |
| text | the names and date |
| lid | the lid |
| crown | the swans |

## Personalise

Edit the two lines at the top of `swan_crown_lantern.scad`, or pass them in,
then rebuild:

    NAMES="Ava & Noah" DATE="06.21.2025" ./build.sh cgal
    NAMES="Ava & Noah" DATE="06.21.2025" ./build.sh union

The names are sized to the plinth's band. A pair too long for 3.6 mm letters
breaks onto two lines after the "&".

## How it prints (why it looks the way it does)

- **OpenSCAD can't bend geometry,** so the pond and the names are built flat
  and wrapped round the drum by `build.sh` (`part_mesh wrap`).
- **The names** are Playfair Display grown 0.25 mm so its hairlines print. They
  are spaced 1.08 and the date 1.25, and cleaned only of gaps and strokes
  under 0.4 mm. The first renders showed them as solid blobs, from a heavier
  clean that filled every counter.
- **The crown's bevel** steps in 0.25 mm a layer for its top three layers.

## Checks

Re-running after the 2026-10-28 fixes; results go here when the run finishes.

## Images

`images/` holds renders of the model, not photos of a print:

- `*_colour_*`: the parts in their render colours, the crown shown standing
  in the lid
- `*_night*`: lit from inside, in the dark
- `*_as_printed_*`: per print, rendered from the sliced toolpath, so they show
  what the printer actually lays down

## Rebuild

`./build.sh cgal` writes the shipping parts. `./build.sh union` welds the
one-body copies the gate checks. Then run
`python3 ../check_valentine.py swan_crown` for every check above.
