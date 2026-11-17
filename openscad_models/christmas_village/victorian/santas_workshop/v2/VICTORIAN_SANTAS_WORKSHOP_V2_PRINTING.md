# Victorian Santa's Workshop — printing notes (v2)

The version to print from 2026-10-30, when Scott chose v2 over the original.
What changed and how it was checked: `V2_PILOT_NOTES.md` (the added detail)
and `V2_INTERIOR_NOTES.md` (the open hall, the three tealights, the engraved
mark). The digital-download ZIP is built from this folder
(`../../../downloads/build_downloads.py`) and reads its numbers from here.

## The file

`victorian_santas_workshop_v2.3mf`: four colour parts, already in place.
In one colour, give all four the same filament.

| part | what it is | colour in the file |
|---|---|---|
| body | the hall's walls and the two triangles left of each inside wall, the turrets and the corbel brackets under their cones, the gatehouse and merlons, the chimney stacks, the window collars, the step, the pole's red stripe | brick red `#A8483A` |
| roof | the roofs and their slates with the joints between them, the turret cones and their slate joints, the planked doors, the sign boards, the NORTH POLE board and braces, the toys and lines drawn on the glass | slate `#2E3440` |
| trim | snow base and drifts with the three tealight rings, snow on the roofs, cones, merlons and stacks, every frame, sill, pane and bar, the cornice and dentils, the voussoirs, the door straps, the copings, the soffit and icicles, the letters, the pole's white stripe and ball, the finials, the wreaths' bows | white `#F4F1EA` |
| accent | the wreaths and the chimney garlands | evergreen `#2F6B45` |

The OBC maker's mark is engraved 0.8 mm into the underside, so it reads on a
one-colour print.

## Settings that are not optional

- **Supports OFF.** The union of the four parts slices with 0 support moves
  and 0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers, 0.4 mm nozzle.

## Cost — sliced in Bambu Studio (2026-11-17)

| version | file | time | filament |
|---|---|---|---|
| **matte white, one colour** | `gcode/victorian_santas_workshop_v2_matte_white.gcode.3mf` | **17 h 34 m** | **108.0 m, 343 g** |
| **four colour, AMS** | `gcode/victorian_santas_workshop_v2_four_colour.gcode.3mf` | **2 d 22 h 4 m** | **339 m, 1,078 g** (561 brick, 193 slate, 305 white, 19 green) |

Both: Bambu Studio 2.8, the P1S 0.4 nozzle, 0.20 Standard with the shop's production
settings, PLA Matte, textured PEI, supports off. **0 support moves in either.** 968
layers. Both files are finished for Bambu Handy's cloud slicing (`tools/handy_finish.py`).

**Four colour costs more than three times the plastic of the model.** The model is about
343 g; the other ~735 g is purge, because most of the 968 layers change colour four
times. As sliced it is not a sensible profile to offer. Fewer colour changes (trim and
roof only, say), or flushing into infill, would bring it down; neither is done here.

The figures before this (15 h 34 m, about 358 g, 2026-10-29) were the P1S motion model's
estimate on the CGAL union, not a Bambu Studio slice. The slice is the one to quote.

## Lighting

Three battery tealights, up to 38 mm across. They stand on the table and the
building comes down over them; three rings on the floor centre them, one in
each bay.

## Size

206.0 × 129.0 × 193.6 mm, snow base included. One solid piece.
