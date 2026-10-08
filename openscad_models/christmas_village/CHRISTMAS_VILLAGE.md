# Christmas Village — a collectible lantern series

**For sale (Scott, 2026-10-07):** the Christmas villages will be sold on Etsy;
the Haunted Town is for Scott's own use this year. More test prints the weekend
of 2026-10-10.

**How they sell (Scott, 2026-10-08):**
- **Two kinds of listing:** printed buildings shipped, and the files as a
  digital download.
- **Shipped prints are one colour only.**
- **Photos will include buildings painted by Jessee.** Since a buyer gets an
  unpainted one-colour print, every listing that shows a painted building
  must say so plainly, next to the photo and in the description: shown
  painted, ships unpainted in one colour.
- **Painted or colour versions are by request only:** a buyer messages Scott,
  who may sell one painted. No listing offers them as an option.
- **Shipped prints are white,** so buyers can paint them.
- **Files sell both ways:** each building as its own download listing, and a
  bundle of each style's whole village.
- **Lit by a standard battery LED tealight, and one ships with every printed
  building** (Scott, 2026-10-08). The listing says so; the download listings
  say a tealight is not included and give the size that fits (up to about
  38 mm across and 45 mm tall).

**Signs have raised letters** (2026-10-07): INN, SANTA'S WORKSHOP, TOYS,
SWEETS and COCOA. Flush inlays were colour alone and vanish on a one-colour
or painted print, as the haunted post office's first print showed. Each sign
is a climb in 0.2 mm steps (Technique 81 in
`.claude/skills/3d-print-design/SKILL.md`); all five buildings were re-checked
with 0 supports and no fidelity flags in a sign.

Started 2026-09-27 (Scott: "I want to start the setup of a Christmas village.
Start putting together 5 ideas of styles we should go with … same building
with the 5 different styles").

## What's in this folder

| folder | what it is |
|---|---|
| `victorian/cottage/` | **Victorian cottage, printable.** `victorian_cottage.3mf`, the `.scad`, part `.stl`s, `build.sh` (exports the parts; `./build.sh chk` renders the six overlap checks), printing notes, `images/` |
| `gingerbread/cottage/` | **Gingerbread cottage, printable.** Same layout as the Victorian |
| `victorian/shop_house/` | **Victorian shop-house, printable (round).** The "more shape" Victorian (below), redrawn on a stadium plan: round brick shop floor with a bow window, jettied timber upper storey, round slate roof with a dormer, tall chimney. The square version passed every check and is archived in `data/trash/` and at commit 16df111 |
| `gingerbread/turret_house/` | **Gingerbread turret house, printable (round).** The "more shape" Gingerbread (below), on a stadium plan: roofs that swoop out into icing at three heights, a leaning round turret with a bell cone and candy-cane spire, a porch on peppermint-stick columns |
| `victorian/toy_shop/` | **Victorian toy shop, printable (square and round).** Building #2: a square two-storey brick shop under a slate gable, a TOYS bay shop window, and a round brick corner tower with a flared slate cone. Meets the tealight rule (58 mm of headroom) |
| `gingerbread/candy_cane_chapel/` | **Gingerbread candy cane chapel, printable (square and round).** Building #2: a square gingerbread nave under a chocolate gable, and a round tower striped red in a spiral like a candy cane, its spire ending in a crook. Meets the tealight rule (50.6 mm of headroom) |
| `victorian/church/` | **Victorian church, printable (square and round).** Building #3: a long brick nave with a rose window, a square bell tower with a louvred belfry and a tall octagonal broach spire, a half-round apse. The tallest in the village (164 mm). Meets the tealight rule (51.6 mm) |
| `gingerbread/sweet_shop/` | **Gingerbread sweet shop, printable (round and square).** Building #3: a three-tier layer cake with frosted, dripping ledges, berries and a cherry, SWEETS on its front, and a square gingerbread shop with a lollipop sign. Meets the tealight rule (51.2 mm) |
| `victorian/coaching_inn/` | **Victorian coaching inn, printable (square).** Building #4: a long brick ground floor with a pointed carriage archway through its right end, a white plaster upper floor jettied out on a dark beam with flush dark timbers, an INN sign, a wall lantern, two chimneys. The widest in the village (97 mm). Meets the tealight rule (58.5 mm) |
| `gingerbread/cocoa_cafe/` | **Gingerbread cocoa café, printable (round and square).** Building #4: a white mug with red stripes, COCOA and a handle, full of cocoa under a swirl of whipped cream with marshmallows and a candy-cane stirrer, and a square gingerbread café out of its front under a striped awning. Meets the tealight rule (50.3 mm) |
| `victorian/townhouse/` | **Victorian townhouse, printable (square and round).** Building #5: a tall, narrow three-storey brick house with a round bow window up its whole front under a bell-flared slate cone, a door with a fanlight up two steps, and a mansard roof with three dormers and a tall chimney. The village's first three-storey house (121.5 mm). Meets the tealight rule (70.7 mm) |
| `gingerbread/santas_workshop/` | **Gingerbread Santa's workshop, printable (round and square).** Building #5: a round gingerbread drum under a steep chocolate cone with gumdrops round its foot, a square loading wing with chocolate-bar doors and a peppermint porthole, and a tall white chimney striped red like a peppermint stick. Meets the tealight rule (50.6 mm) |
| `victorian/santas_workshop/` | **Victorian Santa's workshop, printable (square).** Building #6, built before the clock tower: a long one-storey brick workshop with one big round-arched window, its glass set deep in the wall with toys drawn on it in dark lines (rocking horse, teddy, sailboat, toy soldier, jack-in-the-box, a fanlight), arched loading doors with wreaths under a SANTA'S WORKSHOP sign, three skylights, white scalloped bargeboards and a chimney. `concepts/` holds the look studies Scott picked the mix from. Meets the tealight rule (65.7 mm) |
| `victorian/clock_tower/` | **Victorian clock tower, printable (round and square).** Building #7: a square brick tower with a glazed white clock face on each side, a white cornice and a steep slate pyramid, rising out of a round one-storey brick drum under a slate cone with arched windows and a door. The clocks glow when lit. 160 mm tall. Meets the tealight rule (51.2 mm) |
| `gingerbread/cookie_clock_tower/` | **Gingerbread cookie clock tower, printable (round).** Building #6: a round gingerbread tower stacked from three thick cookie discs with icing dripping between them, a big scalloped cookie clock on its front piped round with icing dots, its frosting-white face glazed so it glows when lit, arched windows framed in icing, a chocolate shingle cone with gumdrops round its foot and a candy cane out of the top. 140.6 mm tall. Meets the tealight rule (81.1 mm) |
| `references/` | Scott's reference photos for "more shape", and what they teach |
| `concepts/` | the style study: `christmas_cottage_styles.scad` (one cottage, five styles), `render_styles.py` (exports every piece and renders each style in its colours), `meshes/` (the exported pieces), `images/` (front, three-quarter and top render per style, plus `styles_lineup.png`) |

**Chosen 2026-09-28 (Scott): "I want a village in both the first two styles.
One village each."** Two villages, **Dickens Victorian** and **Gingerbread**,
each its own folder here (`victorian/`, `gingerbread/`) with one subfolder per
building, the same layout as `haunted_town/`. The building lineup for each is
proposed to Scott before any `.scad` is written.

## More shape (Scott, 2026-09-30)

After the first two cottages: *"Try these but as more shape to them. Like
more engineering like the reference photos"* (`references/`). The cottages
were single boxes; the references are several masses with roofs at several
heights. Scott picked, from four shapes each:

- **Victorian: a two-storey shop-house.** The upper storey juts out over the
  lower one on brackets, a bay shop window on the front, a tall stepped
  chimney stack.
- **Gingerbread: a whimsical turret house.** A crooked turret under a curling
  candy-cane spire, swooping icing-edged roofs at three heights, a porch on
  peppermint-stick columns.

The first cottages stay in `victorian/cottage/` and `gingerbread/cottage/`
as built and checked; the new ones get their own folders.

**Then: "Make them not do squared if possible"** (Scott, 2026-09-30). Asked
what should stop being square, he picked all three: the buildings' boxy
shape, the sharp edges, and the base. Both buildings were redrawn with no
square corners: stadium (two half-circles joined by straights) and round
plans, roofs swept round the whole plan instead of gabled boxes, and soft
blob bases with rounded top edges in place of rectangular slabs. Windows,
doors and timbers follow the curved walls in short tangent strips, so a
raised frame hugs the curve instead of standing off it.

**Round is the series look (Scott, 2026-09-30): "Christmas village keeps a
rounder shape. I still want them all similar but different in building
layout."** Every Christmas building from here on is round: stadium, round
or combined round plans, swept roofs, soft blob bases, no square corners. What
makes each building its own is its layout: the plan, the masses and where the
roofs step, per the lineup below. The two cottages were built square before
this, and are being redrawn round (Scott: "Yes redo the cottages round too").
Picked from four layouts each: the Victorian cottage becomes **a round brick
drum under a cone of slate, with a small curved gable over the door** carrying
the bargeboard and finial; the Gingerbread cottage becomes **a cupcake: a
round gingerbread drum under a chocolate dome**, icing piped round its rim,
gumdrops round the eave and one on top. The Haunted Town stays
square for now (see `../haunted_town/HAUNTED_TOWN.md`).

**Round and square together (Scott, 2026-09-30, after seeing the round
cottages: "I like those. I want to incorporate round and square together on
some buildings. I want the Christmas village to look stunning. Do all
different shapes and stories of the buildings. Keep what you have now then
let's keep moving").** The round cottages, shop-house and turret house stay
as built. From building #2 on, a building may join round and square masses: a
square block with a round tower, a round drum with a square wing. The
buildings also differ in height: one, two and three storeys, towers and
steeples. Every building still gets the soft snow base and rounded edges, and
no two in a village share a plan or a storey count where it can be avoided.

Picked the same day, from four forms each: the **toy shop** is a two-storey
square shop with a big bay toy window, and a three-storey round tower on its
front corner under a tall slate cone, with the door in the tower. The **candy
cane chapel** is a one-storey square gingerbread nave under a steep
icing-edged gable, with a round tower at its front striped red and white in a
spiral up the tower and its spire, the spire's tip curled like a cane.

**Next pair, picked 2026-10-01** from four forms each, after Scott saw the
finished toy shop and chapel. The **Victorian church** is a long brick nave
with a round rose window in its front gable, a square bell tower on one front
corner rising to a tall slate spire (the tallest building in the village), and
a half-round apse at the back. The **Gingerbread sweet shop** is a layer-cake
tower: three round frosted tiers stacked smaller and smaller, with drips and
windows in each and a cherry on top, beside a small square shop front with a
lollipop sign. Three storeys.

**Fourth pair, picked 2026-10-01** from four forms each, after Scott saw the
finished church and sweet shop. The **Victorian coaching inn** is a long
two-storey brick inn with a timber-framed jettied upper floor, a big pointed
carriage archway through one end, a hanging lantern and inn sign, and two
chimneys: the widest building in the village. The **Gingerbread cocoa café**
is a round tower shaped like a hot-cocoa mug, a handle on its side, whipped
cream and marshmallows on top and a candy-cane stirrer, joined to a small
square café front with a striped awning.

**Fifth pair, picked 2026-10-01** from four forms each, after Scott saw the
finished inn and cocoa café. The **Victorian townhouse** is a tall, narrow
three-storey brick house, square, with a round bow window running up its whole
front, a mansard slate roof with two dormers, and steps up to a door with a
fanlight: the village's first three-storey house. The **Gingerbread Santa's
workshop** is a roundhouse: a round gingerbread drum under a cone roof with
gumdrops round its eave, a square loading wing with big double doors, and a
tall round chimney striped like a peppermint.

**A Santa's workshop for the Victorian village (Scott, 2026-10-02):** "Make it
have big windows with toys outlined on the windows sunk in so it looks like
they are inside … I want it to look like his workshop would in that style."
Built next, before the clock tower. From two look studies (`victorian/
santas_workshop/concepts/`) he picked a mix: the long brick workshop with one
big window, the loading doors with wreaths, skylights and white scalloped
bargeboards. The toys are dark lines running through the window's white glass,
so lit from inside they show as silhouettes.

**Last pair, picked 2026-10-02** from four forms each, after Scott saw the
finished Santa's workshops. The **Victorian clock tower** is a tall square
brick tower on a round one-storey brick drum with arched windows, a big white
clock face on each side near the top and a slate pyramid spire with a finial.
The **Gingerbread cookie clock tower** is a round tower stacked from thick
cookie discs, a big frosted round-cookie clock face on its front with candy
hands, under a chocolate cone with gumdrops and a candy-cane spire.

**Tealight headroom on the round cottages, decided 2026-10-01:** the Victorian
cottage, cupcake cottage and turret house stay as built, 46 mm tealight short
of 50 mm of headroom (41.6–47.2 mm). Their notes recommend a 38 mm tealight,
which fits with 48.9–54 mm of room. The toy shop (58.2 mm) and the chapel
(50.6 mm) meet the rule.

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
| 6 | **Santa's workshop**: one big window, toys on its glass (added 2026-10-02) | **Cookie clock tower**: a frosted-cookie clock face |
| 7 | **Clock tower**: a big white clock face | |

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
