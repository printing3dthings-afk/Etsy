# Christmas Village — a collectible lantern series

Started 2026-09-27 (Scott: "I want to start the setup of a Christmas village.
Start putting together 5 ideas of styles we should go with … same building
with the 5 different styles").

## What's in this folder

| folder | what it is |
|---|---|
| `concepts/` | the style study: `christmas_cottage_styles.scad` (one cottage, five styles), `render_styles.py` (exports every piece and renders each style in its colours), `meshes/` (the exported pieces), `images/` (front, three-quarter and top render per style, plus `styles_lineup.png`) |

**Chosen 2026-09-28 (Scott): "I want a village in both the first two styles.
One village each."** Two villages, **Dickens Victorian** and **Gingerbread**,
each its own folder here (`victorian/`, `gingerbread/`) with one subfolder per
building, the same layout as `haunted_town/`. The building lineup for each is
proposed to Scott before any `.scad` is written.

## The two villages (agreed with Scott 2026-09-28: "I like them all")

Six buildings each, one big identity feature per building, and no two in a
village sharing walls, windows and roof shape. Built to the Haunted Town rules
the chapel proved on the printer: four colours in one 3MF, glazed windows with
the bars on the panes, room for a 38 mm LED tealight, and the same 8 mm base
height so a village lines up as a street.

| # | Dickens Victorian (brick, slate, white, evergreen) | Gingerbread (gingerbread, chocolate, icing, candy red) |
|---|---|---|
| 1 | **Brick cottage**: the style study, made printable | **Gingerbread cottage**: the style study, made printable |
| 2 | **Toy shop**: bay shop window, hanging sign | **Candy cane chapel**: red and white striped steeple |
| 3 | **Church**: tall spire, round rose window | **Sweet shop**: round lollipop window and sign |
| 4 | **Coaching inn**: two storeys, arched carriage gateway, lantern | **Cocoa cafe**: a tower shaped like a hot-cocoa mug |
| 5 | **Townhouse**: tall and narrow, front steps, dormer | **Santa's workshop**: peppermint chimney, gumdrops on the ridge |
| 6 | **Clock tower**: a big white clock face | **Cookie clock tower**: a frosted-cookie clock face |

The two cottages come first: the design already exists, and they test each
style's hardest details on the printer (the Victorian's pierced bargeboard and
icicles, the Gingerbread's icing drips and dots).

## The five styles

Same cottage in every one: a 64 × 58 mm gable-front house, 50 mm to the
eaves, one door, two front windows, an attic window, a chimney at the back
left, standing on a white snow base. The styles change the walls, roof,
window shapes, trim and decorations. Each uses four filament colours, and one
of them is always white because it is also the snow.

| style | walls | roof | windows | decorations | colours |
|---|---|---|---|---|---|
| **Dickens Victorian** | brick with white quoins | steep 56° slate, snow on the upper half, icicles | segmental arches with keystones, a pointed attic window | pierced white bargeboard with a finial, green shutters, wreath and garland, a lamp post | brick red, slate, white, evergreen |
| **Gingerbread** | smooth gingerbread with piped icing at the corners | 50° chocolate scallop tiles, icing along the ridge, icing drips on every edge | round-topped, outlined in piped icing dots | gumdrops on the ridge, candy canes by the door, a peppermint attic window, a chocolate-bar door | gingerbread, chocolate, icing white, candy red |
| **Nordic** | white board-and-batten, red corner boards | 46° charcoal standing-seam roof, deep snow, icicles | square, red frames, a heart-shaped attic window | a gold star on the gable, a gold heart on the red door, candle bridges in the windows | white, charcoal, falu red, gold |
| **Alpine chalet** | white plaster below, round logs above with their ends crossed at the corners | low 26° roof with a deep 12 mm overhang, fully snowed over | square, wood frames | a balcony with heart cut-outs, red heart shutters, window boxes with berries, carved bargeboard | wood, dark brown, white, red |
| **Kawaii pastel** | smooth pink, rounded corners | 50° mint scallop tiles, a puffy snow cap with round drips | round portholes | a lemon star on the ridge, a lemon door with a pink heart, a round chimney | pink, mint, white, lemon |

## What the concept is and is not

It is a look study for picking a direction, not a printable model. It has not
been through `tools/product_gate.py`, and it would fail: sills, balcony and
window boxes have flat undersides, window bars stand free in their openings,
the chalet's 26° roof and 12 mm eave need brackets, and the pieces overlap
instead of being disjoint colour parts.

The style Scott picks gets rebuilt to the rules the Haunted Town already
proved on the printer: disjoint colour parts in one 3MF, every underside at
least 45° from horizontal, a 1.48 mm pane behind every window with its bars
standing on the pane, room inside for a 38 mm LED tealight, an open base,
and the OBC mark underneath.
