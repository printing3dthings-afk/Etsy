# Stacking drawer module — how to print it

Two objects, one plate. `drawer_module.3mf` has both already laid out and
oriented. 91 × 71 × 44mm assembled; the drawer holds about 136 cm³.

| Object | Orientation | Time | Filament |
|---|---|---|---|
| `shell` | **on its back, opening up** — as loaded | 4h 19m | 48.7 g |
| `drawer` | as it sits in use, open side up — as loaded | 3h 13m | 39.0 g |
| | **per module** | **7h 31m** | **88 g** |

Two complete modules fit on one plate.

No supports on either part. Print both on smooth PEI in PLA.

## Do not re-orient either part

The orientation *is* the design here, and both are already correct in the
3MF.

The shell prints **on its back with the drawer opening facing up**. That
puts every wall vertical, makes the cavity a blind hole opening upward
instead of something that has to be bridged over, and — the reason it
matters most — makes both slide features run along the build direction, so
they are the same cross-section on every layer. Stood up any other way,
those features become overhangs and the cavity needs a roof.

The drawer prints flat on the bed as it sits in use. In that pose it
measures **zero area past 55°**. The only thing the checker flags is a
0.24 cm² band in the first two layers where the bottom edge rounds off —
a slightly rough bottom edge on a face that lives inside the shell.

## How the slide works

The drawer's floor plate is wider than its body and rides in a channel:
it sits on two runners, and a rib above catches it so the drawer cannot
tip out when you pull it. Measured on the real meshes:

- flange rests on the runners — **0.04 mm**, a resting contact
- free lift before the capture rib stops it — **0.24 mm**
- rib overlaps the flange by — **2.58 mm**
- side clearance — **0.32 mm**

The drawer pulls all the way out on purpose — lift it out and carry it to
your desk. There is no stop.

If it binds on your first print, open `clear_lat` from 0.30 to 0.40 and
re-slice. If it rattles side to side, close it to 0.25. That is the one
number worth touching.

## The pull

A pocket in the face, **5 mm deep and 13 mm tall**, whose roof **ramps back
at 45°**. Nothing protrudes.

That ramp is the whole thing. A flat-roofed pocket is a ceiling you press
on and hope for friction; a ramped one is a hook — the fingertip goes in
under the lip and curls *up* into the wedge. The lip keeps a **1.5 mm flat
underside** at the mouth, where a finger actually pulls, so it is never a
knife edge.

| | |
|---|---|
| pocket floor | 5 mm deep, flat |
| lip underside | flat for the first 1.5 mm, then 45° |
| top of the wedge | 3.5 mm of plate above it |
| behind the pocket | 1.5 mm of plate |

Depth is set by what sits behind, and there is more there than the plate
alone — the drawer body's own front wall backs the whole pull, so a 6.5 mm
plate gives 8.18 mm.

**The ramp also fixed the worst thing about this part.** The flat roof was
a 5.0 mm 90° cantilever — 2.71 cm², the single largest overhang on the
drawer. Ramping it drops that to a 1.5 mm ledge and **0.75 cm² total**. It
is the one change in this whole design where grip and printability pulled
the same way instead of against each other.

Five other pulls are one word apart — set `pull` to `band`, `ledge`,
`slot`, `lip`, `shelf` (this pocket with a flat roof) or `rail` (two slots
with a bar between them).

## Stacking

Two rails run front-to-back on the bottom of each module and drop into
matching grooves on the top of the one below. The tongue is **0.2 mm
shorter than the groove is deep**, deliberately — modules seat on their
flat faces, never balanced on the tongue.

## Not print-in-place, and why

This was pitched as a drawer that comes off the plate already working.
Measuring it killed that idea, and it is worth knowing why in case it
comes up again: a drawer's floor sits above the shell's floor across a
large flat gap. At the 0.2 mm clearance that works everywhere else in this
shop, that is about 5,600 mm² of lightly welded surface — nothing like the
few square millimetres a ball joint gets away with — and it would come off
the plate as a solid brick. Opening the gap instead makes the drawer's
floor start printing in mid-air. Hanging the drawer on side rails so its
floor bridges puts a 55 mm bridge across the one surface that has to stay
flat.

Two parts on one plate costs nothing real — you still just drop the drawer
in — and it removes that failure mode completely.

## The mark

`OBC`, engraved 0.7 mm into the bottom face, 31.8 mm wide — 36% of the
face it sits on, with 6.4 extrusions across the thinnest stroke. The full
wordmark cannot print at this size at any depth; its strokes measure
0.0 mm.
