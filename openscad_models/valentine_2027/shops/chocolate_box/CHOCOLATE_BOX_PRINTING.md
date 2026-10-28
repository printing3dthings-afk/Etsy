# Chocolate Box Shop — printing notes

Built 2026-10-26/27 from Scott's Valentine's 2027 brief. Form 2 of five
(`../../concepts/shop_forms.jpg`), picked with the Victorian Bay. A village
building, made to stand with the Christmas Gingerbreads.

A gingerbread shop that is a box of chocolates:

- **daylight:** piped icing on every edge, with drips under the lid. Heart
  windows sit in icing frames. CHOCOLATES stands in raised letters over an
  arched door with a heart on it.
- **the lid:** it overhangs on a cove, tied with a ribbon that runs down
  three walls, and a puffed bow sits on top.
- **lit:** the front hearts show truffles and a heart box on shelves. The
  sides show Cupid's arrows, and the back shows a heart in each heart. The
  scenes are built into the backs of the 0.9 mm panes, so unlit the windows
  look plain.

It is one piece, hollow and open underneath. It stands over a battery LED
tealight; the opening is 49.2 × 49.2 mm. It measures 67 × 67 × 70 mm.

The bow lies on the lid, not standing up as in the concept. Standing, its
loops' undersides and the tops of their holes would hang in the air.

The maker's mark, OBC, is engraved 0.8 mm into the underside of the base's
front, between the opening and the edge. It reads O-B-C with the shop tipped
back onto its back. This was checked on the exported geometry, not assumed.

## Print

| setting | value |
|---|---|
| file | `chocolate_box_shop.3mf` (one object, six parts, aligned) |
| filament | **matte white PLA**, one colour: assign it to every part |
| layer | 0.2 mm, Bambu's 0.20 Standard on the P1S, 0.4 nozzle |
| supports | **off**. The slicer finds none to add (gate, below) |
| plate | textured PEI |
| time | about 2 h 0 m, 56 g (P1S motion model) |

The parts are colour only, so the renders can show them apart:

| part | what it is |
|---|---|
| body | the gingerbread walls |
| roof | the lid and the door |
| trim | the base, icing, drips, window frames, sign board, door frame |
| accent | the ribbon, bow, letters and the door's heart |
| glass | the glowing panes |
| art | the scenes inside the panes |

## How it prints (why it looks the way it does)

- **The ceiling inside** is a pyramid at 50° from just under the windows up to
  under the lid's top. Over a 49 mm room it needs 29 mm of rise, more than the
  lid has, so it starts down in the walls.
- **The window reveals** climb 1.6 per 1 out from the pane, so their heads
  print without support. The frames ring the opening where it meets the wall
  face, not the pane's outline: drawn round the pane, the frame heads hung
  over the reveal and the slicer propped every one.
- **The letters** are Montserrat Black at 3.22 mm, spaced 1.25, with strokes
  0.08 bolder. Measured on the glyphs, that leaves at least 0.45 mm between
  every pair, so each letter prints as its own letter. The first versions
  printed C into H and E into S. At 3.2 the S exported with a pinch, and at
  3.22 without the bolder strokes the slicer dropped one layer of C and O.

## Checks (2026-10-28)

- parts closed, no two overlapping (`logs/parts.txt`)
- **product gate passed** (`logs/gate.txt`): watertight, one body, 0 support
  moves, 0 overhang perimeters, full height, flat base, stable. The wall
  floor is 0.8 mm for this piece (`../../check_valentine.py`), because the
  0.9 mm panes are the point. Every structural wall is 2.4 mm.
- print fidelity: 0 flagged (`logs/fidelity.txt`)
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
`python3 ../../check_valentine.py shops/chocolate_box` for every check above.
