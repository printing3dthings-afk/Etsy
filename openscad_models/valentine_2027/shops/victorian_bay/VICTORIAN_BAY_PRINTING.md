# Victorian Bay Chocolate Shop — printing notes

Built 2026-10-26/27 from Scott's Valentine's 2027 brief. Form 1 of five
(`../../concepts/shop_forms.jpg`), picked with the Chocolate Box. A village
building, made to stand with the Christmas Victorians.

A brick chocolate shop on the village's snow base:

- **daylight:**
  - a canted bay display window under a striped, scalloped awning
  - CHOCOLATES in raised letters over the awning
  - a panelled door with a heart, beside the bay
  - arched upstairs windows with glazing bars and stone quoins up the corners
  - a slate mansard with a heart dormer and a chimney
- **lit:** shelves of chocolates show in the bay, and a Cupid's arrow shows in
  each side heart window. They are built into the backs of the 0.9 mm panes,
  so unlit the windows look plain. The back heart window and the upstairs
  windows glow plain.

It is one piece, hollow and open underneath. It stands over a battery LED
tealight; the opening is 48.4 × 46.4 mm. It measures 65 × 74 × 104 mm.

The maker's mark, OBC, is engraved 0.8 mm into the underside of the base's
front, between the opening and the edge. It reads O-B-C with the shop tipped
back onto its back. This was checked on the exported geometry, not assumed.

## Print

| setting | value |
|---|---|
| file | `victorian_bay_chocolate_shop.3mf` (one object, six parts, aligned) |
| filament | **matte white PLA**, one colour: assign it to every part |
| layer | 0.2 mm, Bambu's 0.20 Standard on the P1S, 0.4 nozzle |
| supports | **off**. The slicer finds none to add (gate, below) |
| plate | textured PEI |
| time | about 2 h 4 m, 62 g (P1S motion model) |

The parts are colour only, so the renders can show them apart:

| part | what it is |
|---|---|
| body | the brick walls and the bay |
| roof | the mansard, dormer and chimney |
| trim | the base, window frames and bars, sign board, quoins, door frame, awning scallops, dormer heart |
| accent | the awning, letters, door and the door's heart |
| glass | the glowing panes |
| art | the chocolates and the arrows inside the panes |

## How it prints (why it looks the way it does)

- **The bay's inside opens into the shop.** Its ceiling rises 50° from just
  under the bay's top back through the wall, so it prints off the bay's front
  wall.
- **The bay's side windows** sit square in their canted walls. In the first
  build they were turned 8.8° off: the side panes poked into the bay, and the
  slicer propped the pockets at their ends (1898 support moves). That's fixed,
  and the slicer now finds none.
- **The awning** is the bay's roof. Its underside rises 1.6 per 1 out from the
  bay's top edge.
- **The shop's ceiling** is a hip at 50° from 6 mm under the walls' top, since
  the mansard is too low over a 48 mm room for one from the walls' top itself.
- **The window reveals** climb 1.6 per 1 out from the pane, and the frames
  ring the opening where it meets the wall face, so no window head needs
  support.
- **The letters** are Montserrat Black at 3.22 mm, spaced 1.25, with strokes
  0.08 bolder. Measured on the glyphs, that leaves at least 0.45 mm between
  every pair, so each letter prints as its own letter.

## Checks (2026-10-28)

- parts closed, no two overlapping (`logs/parts.txt`)
- **product gate passed** (`logs/gate.txt`): watertight, one body, 0 support
  moves, 0 overhang perimeters, full height, flat base, stable. The wall
  floor is 0.8 mm for this piece (`../../check_valentine.py`), because the
  0.9 mm panes are the point. Every structural wall is 2.4 mm.
- print fidelity: 0 flagged (`logs/fidelity.txt`). The first run's slice came
  back corrupt, with moves 70 million mm off the bed. The slicer failed while
  three checks ran at once, so fidelity was re-run alone, and that slice was
  clean.
- fragility: 0 high, 0 watch (`logs/fragility.txt`)

## Images

`images/` holds renders of the model, not photos of a print:

- `*_colour_*`: the parts in their render colours
- `*_night*`: lit from inside, in the dark
- `*_as_printed_*`: rendered from the sliced toolpath, so they show what the
  printer actually lays down

## Rebuild

`./build.sh cgal` writes the shipping parts. `./build.sh union` welds the
one-body copy the gate checks. Then run
`python3 ../../check_valentine.py shops/victorian_bay` for every check above.
