# Snap-close box — how to print it

Four files, all sharing one origin. 106 × 72 × 36mm closed.

| File | Filament | Notes |
|---|---|---|
| `snap_box_base` | body colour | prints upright, open side up |
| `snap_box_lid_body` | body colour | **prints upside down**, logo face on the plate |
| `snap_box_lid_script` | charcoal | the brush wordmark |
| `snap_box_lid_swash` | gold | the underline |

## The lid

Load `lid_body`, then right-click it → **Add part → Load** and pick
`lid_script` and `lid_swash`. They land registered — do not move them. Assign
each its own filament.

Then **flip the lid 180° so the logo face is on the plate**, and use the
**smooth PEI** plate. That face is the whole point of the design: the logo is
a flush inlay, not an engraving or an emboss, so the top comes off the plate
dead flat with the logo as a pure colour change in the first four layers.

Slice it right side up and you get the same colours with a textured top and
visible layer lines across the script. Print it on textured PEI and you get
the plate's texture instead of a gloss face.

No supports on either part. Nothing on the lid exceeds 45° from vertical
except the snap groove's own 0.75mm radius, and nothing on the base exceeds it
except the snap bead's 0.55mm radius — both far too small to need help.

## The base

Prints as modelled, open side up, flat bottom on the plate. The maker's mark
is engraved 0.7mm into the underside, so it comes out of the first layer.

## The snap

The bead around the base's rim stands 0.55mm proud and the lid skirt clears it
by 0.20mm, leaving **0.35mm of interference per side**. That is mid-range for
an annular snap at a 0.4mm nozzle, and it is the one number worth tuning after
a first print:

* Lid too tight or the skirt creaks → drop `bead_r` toward 0.45.
* Lid falls off → raise it toward 0.65.
* Lid rocks but does not click → raise `clear` slightly; the skirt is binding
  on the plug before the bead ever engages.

Change one at a time and re-run the checks in the header of `snap_box.scad`.

## Sizing the logo

`logo_w` is 86mm and should not go far below ~70mm. The script's thin
connector strokes are about 8px wide against the 1232px source, so under about
70mm they fall below a single 0.4mm extrusion and the slicer simply drops
them — the wordmark breaks up into disconnected blobs. If this box is ever
scaled down, the logo needs a simpler mark, not a smaller version of this one.
