# Stacking drawer module — how to print it

Two objects, one plate. `drawer_module.3mf` has both already laid out and
oriented. 91 × 71 × 44mm assembled; the drawer holds about 136 cm³.

| Object | Orientation | Time | Filament |
|---|---|---|---|
| `shell` | **on its back, opening up** — as loaded | 4h 19m | 48.7 g |
| `drawer` | as it sits in use, open side up — as loaded | 3h 12m | 38.8 g |
| | **per module** | **7h 30m** | **88 g** |

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

A pocket cut into the face — **5 mm deep, 13 mm tall, with a dead flat
floor and a flat lip above it**. Nothing protrudes.

The floor is the shelf. Your fingertip goes in, sits on it, and pulls
against 5 mm of lip overhead. The two things that made a shallow version
feel bad were both the floor: it was a 45° ramp, so the finger slid down
and out of the pocket, and at 3 mm there was barely anything to slide
into.

Depth is limited by what sits behind it, and there is more there than the
plate alone — the drawer body's own front wall backs the whole pull, so a
6.5 mm plate gives 8.18 mm of material and a 5 mm pocket still leaves
**3.16 mm**.

The cost is the roof: a flat 5 mm cantilever, 56 mm long, facing down
inside the pocket. It has to be flat — an undercut *is* an overhang, and
ramping it to be self-supporting is exactly what removes the hook. It will
print with a slightly rough underside. Nobody sees it.

Four other pulls are built in and one word apart, if you want to compare
on a real print: set `pull` at the top of `drawer_module.scad` to `band`
(a shallow flush band), `ledge` (a 10 mm proud shelf — the strongest grip
of the lot, but it sticks out), `slot` (cut clean through), or `lip` (the
shallow ramped pocket this replaced).

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
