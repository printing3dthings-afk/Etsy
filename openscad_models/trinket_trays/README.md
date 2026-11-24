# Christmas trinket trays: rippled frame + insert (2026-11-24)

Scott's picks:
- **The direction**, from his examples ("Examples of what I want to have in our catalog"): a frame
  with a rippled outer wall, and a smooth insert in a second colour that drops inside it. Each
  piece is one colour, so the set is two-tone without an AMS.
- **The second round, all four recommendations:** six more shapes, raised detail on the insert
  floor, two sizes, and a thumb scoop to lift the insert out.

## The range
Twelve shapes, all our own outlines:
- star, tree, mitten, bauble, bell, gingerbread (the Tin Clicker's, scaled up);
- snowman, stocking, gift box, snowflake, Santa hat, gingerbread house.

No shape is joined to a rectangle: that layout is another maker's MakerWorld exclusive.

Built by `tray_set.py` (shapely outlines, then trimesh and manifold3d) and rendered by
`render_trays.py`. The sheets are `images/tray_sheet_large.jpg` and `images/tray_sheet_small.jpg`.
They're design-review renders, not photos. Nothing has been printed yet.

## Sizes and features
- **Frame:** floor 1.6, wall 3.2 inside the ripples, rim 14 mm. One thumb scoop dips the rim to
  5 mm over 22 mm (18 on the small size), at the frontmost straight stretch, so a finger reaches
  the insert's side.
- **Insert:** wall 1.6, rim 0.8 below the frame's. It drops in with 0.4 clearance all round.
- **Raised detail:** the insert's floor carries lines 1.6 wide and dots, 0.8 proud, as
  DETAIL_STANDARD.md requires (1.2 minimum for handled relief, and 0.8 for a separate shape).
- **Two sizes:**
  - **Large:** as drawn, 148–196 mm on the long side.
  - **Small:** the outline scaled so the frame is 110 mm on its long side. Walls, floors, heights
    and detail lines keep their sizes.

## Checks
- **Gate:** all 48 parts pass the product gate (`checks/gate_*.txt`).
- **Fragility:** 0 on every set.
- **Detail on the smallest tray:** `print_fidelity` on the small gingerbread insert, the finest
  detail, flags one spot. 0.06 mm³, 0.22 mm wide, at the inside point of a wrist zigzag: the
  slicer rounds off a sliver under one bead there. It isn't visible, so it's left as drawn.

## Slices (`slices/`)
Standard, matte PLA, with ironing on every flat top: 0.15 spacing, 10% flow, 30 mm/s. No
supports. The large snowflake is turned 90° on the plate (196 × 175) to clear the prime tower.

**Large**

| shape | across | frame | insert | set |
|---|---|---|---|---|
| star | 154 × 148 mm | 2 h 13 m, 52 g | 1 h 24 m, 33 g | 3 h 37 m, 84 g |
| tree | 131 × 156 mm | 1 h 58 m, 47 g | 1 h 13 m, 28 g | 3 h 11 m, 74 g |
| mitten | 135 × 158 mm | 2 h 29 m, 59 g | 1 h 42 m, 39 g | 4 h 11 m, 98 g |
| bauble | 154 × 168 mm | 2 h 43 m, 64 g | 1 h 57 m, 45 g | 4 h 40 m, 109 g |
| bell | 152 × 156 mm | 2 h 16 m, 53 g | 1 h 28 m, 34 g | 3 h 44 m, 87 g |
| gingerbread | 173 × 180 mm | 2 h 59 m, 70 g | 1 h 53 m, 43 g | 4 h 52 m, 113 g |
| snowman | 102 × 182 mm | 2 h 12 m, 51 g | 1 h 23 m, 32 g | 3 h 35 m, 82 g |
| stocking | 123 × 163 mm | 2 h 11 m, 52 g | 1 h 25 m, 33 g | 3 h 36 m, 85 g |
| gift box | 130 × 148 mm | 2 h 32 m, 61 g | 1 h 48 m, 41 g | 4 h 20 m, 102 g |
| snowflake | 175 × 196 mm | 4 h 12 m, 95 g | 2 h 21 m, 53 g | 6 h 33 m, 148 g |
| santa hat | 162 × 152 mm | 2 h 22 m, 56 g | 1 h 29 m, 35 g | 3 h 51 m, 91 g |
| gingerbread house | 151 × 162 mm | 2 h 42 m, 65 g | 1 h 55 m, 44 g | 4 h 37 m, 109 g |

**Small**

| shape | across | frame | insert | set |
|---|---|---|---|---|
| star | 110 × 105 mm | 1 h 21 m, 31 g | 47 m, 18 g | 2 h 08 m, 49 g |
| tree | 93 × 110 mm | 1 h 13 m, 28 g | 41 m, 15 g | 1 h 54 m, 43 g |
| mitten | 94 × 110 mm | 1 h 26 m, 34 g | 53 m, 20 g | 2 h 19 m, 54 g |
| bauble | 101 × 110 mm | 1 h 22 m, 33 g | 53 m, 20 g | 2 h 15 m, 53 g |
| bell | 106 × 110 mm | 1 h 21 m, 31 g | 47 m, 18 g | 2 h 08 m, 49 g |
| gingerbread | 106 × 110 mm | 1 h 30 m, 34 g | 49 m, 18 g | 2 h 19 m, 52 g |
| snowman | 63 × 110 mm | 1 h 03 m, 24 g | 35 m, 13 g | 1 h 38 m, 37 g |
| stocking | 84 × 110 mm | 1 h 13 m, 29 g | 42 m, 16 g | 1 h 55 m, 45 g |
| gift box | 97 × 110 mm | 1 h 35 m, 38 g | 1 h 03 m, 24 g | 2 h 38 m, 62 g |
| snowflake | 98 × 110 mm | 2 h 05 m, 43 g | 58 m, 20 g | 3 h 03 m, 63 g |
| santa hat | 110 × 103 mm | 1 h 20 m, 32 g | 45 m, 17 g | 2 h 05 m, 49 g |
| gingerbread house | 102 × 110 mm | 1 h 31 m, 36 g | 56 m, 21 g | 2 h 27 m, 57 g |
