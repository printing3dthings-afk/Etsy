# Christmas trinket trays: rippled frame + insert (2026-11-24)

Scott's pick from his examples ("Examples of what I want to have in our catalog"): a frame with
a rippled outer wall, and a smooth insert in a second colour that drops inside it. Each piece is
one colour, so the set is two-tone without an AMS.

Six shapes: star, tree, mitten, bauble, bell, and the Tin Clicker's gingerbread man, scaled up.
They're built by `tray_set.py` (shapely outlines, then trimesh/manifold3d) and rendered by
`render_trays.py`.

## Sizes
- **Frame:** floor 1.6, wall 3.2 inside the ripples, rim 14 mm.
- **Insert:** wall 1.6, rim 0.8 below the frame's.
- **Clearance:** 0.4 all round, a drop-in fit.

## Checks
- **Product gate:** all 12 parts pass (`checks/gate_*.txt`).
- **Fragility:** 0 on every set.

## Slices
Standard, matte PLA, with ironing on every flat top: 0.15 spacing, 10% flow, 30 mm/s, the
shop's rule since the ironing test. `slices/`, 0 supports.

| shape | frame | insert | set |
|---|---|---|---|
| star | 2 h 13 m, 52.5 g | 1 h 23 m, 31.9 g | 3 h 35 m, 84 g |
| tree | 1 h 58 m, 47.1 g | 1 h 12 m, 27.4 g | 3 h 10 m, 75 g |
| mitten | 2 h 30 m, 59.8 g | 1 h 40 m, 38.6 g | 4 h 11 m, 98 g |
| bauble | 2 h 44 m, 64.9 g | 1 h 54 m, 44.6 g | 4 h 38 m, 109 g |
| bell | 2 h 15 m, 53.8 g | 1 h 27 m, 33.4 g | 3 h 41 m, 87 g |
| gingerbread | 2 h 59 m, 71.0 g | 1 h 49 m, 42.5 g | 4 h 48 m, 113 g |

## Open questions for Scott
- **Size.** Frames are 131–180 mm across. A smaller size would cut print time and filament
  roughly in half.
- **Thumb notch.** The insert sits 0.8 below the frame's rim with 0.4 all round, so nothing gives
  a finger hold to lift it out. A scoop in the frame's rim would fix that.

These are design-review renders, not photos. Not yet printed.
