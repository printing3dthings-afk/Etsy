# The Gauntlet — calibration tile

One plate. Its whole job is to turn numbers this shop measured off other
people's models into facts about **your** P1S and **your** filament.

**3h 50m · 30g · about $0.60 of PLA · 120 × 79 × 15mm · no supports.**

Print `gauntlet_tile.3mf` exactly as it comes: flat, 0.2mm layers, 3 walls,
15% infill, smooth or textured PEI, whatever PLA you'd normally use for a
product. Don't scale it — every clearance on here is the thing being tested.

## What comes off the plate

One tile plus **five loose pieces**: the joint chain, the hinge strip, and
three snap clips. They're loose on purpose. A moving part fused to the tile
can't move, and a gap underneath one can't print without supports.

## The six tests

**1 — Joint chain** (the important one). Six links, five joints, one
clearance each, engraved on the link that owns the socket: 0.125 / 0.15 /
0.175 / 0.20 / 0.25mm.

Flex each joint. Some will need one firm first flex to break free — that's
normal and by design, and it's how the good commercial flexis behave. What
we want to know is **the lowest number that frees cleanly and still feels
tight, not floppy.** That single number sets every articulated product we
make from here.

The socket is the measured commercial standard, not something invented: a
rounded-rectangle slot 1.6× the ball diameter long, with a mouth narrower
than the ball. The ball physically cannot escape — it isn't a snap.

**2 — Lattice hinge strip.** 1.8mm ribs, 0.5mm slots, 2.3mm pitch,
staggered bridges. Fold it flat and back, 30–50 times. Does it survive, and
does it feel like a hinge or like a thing about to snap?

**3 — Snap clips.** Three rings, three posts. Ring 0.25 goes on post 0.25,
and so on. Push each on and off a few times. Which clicks nicely, which is
loose, which cracks the ring. Our snap box uses 0.35 — this says whether
that's right.

**4 — Wall ladder.** Uprights at 0.4 / 0.8 / 1.2 / 1.6 / 2.0mm. The
thinnest one that actually comes out solid and doesn't snap when you flick
it is our real minimum wall.

**5 — Text block.** "OBC" engraved and embossed at 3 / 4 / 5 / 6mm. The
smallest one you can read comfortably at arm's length is our floor for
lettering on a product.

**6 — Dome pair.** The same 18mm dome twice: left at OpenSCAD's default
tessellation, right at the setting I now think everything organic should
use. Look at them under a lamp and run a thumb over both. **If you can't
tell them apart, one of my main conclusions is wrong** and I'd rather know.

## What to send back

Photos are enough, plus a sentence per test. The joint chain and the dome
pair are the two that change what I do next.

## Why this exists

Every number on this tile came from measuring downloaded models and
slicing, never from a printed part. The flexi seahorse passed every check I
had and would still have printed as a solid stick — the toolpath check that
caught it is now run on everything, including this tile, and all five
joints slice free. But a slicer preview isn't a print. This is the first
time anything here gets checked against reality.
