# Chubby Axolotl: printing notes

2026-10-30. The first Creature Kit, your pick: form 2, "a short, fat body in
five segments with a big frilly-gilled head and four stubby jointed legs. It
sits on a desk and looks back at you."

The head, the five body pieces and all four legs click together on ball
joints, so you can pose the body, the head and each leg. It stands about 170
mm long, 63 mm across the gills and 52 mm tall.

## The prints

Each part is one colour, printed flat side down, **no supports**.

| print | colour | stands on | sliced time | PLA |
|---|---|---|---|---|
| head | pink `#F4B2C5` | the back of the head | 24 min | 14 g |
| s1 (chest, front legs' sockets) | pink | its back face | 21 min | 8 g |
| s2 | pink | its back face | 15 min | 7 g |
| s3 (hips, rear legs' sockets) | pink | its back face | 19 min | 7 g |
| s4 | pink | its back face | 12 min | 4 g |
| tail | pink | the tip of the fin | 20 min | 6 g |
| legs ×4 (front left/right, rear left/right) | pink | the sole | 6–7 min each | 1 g each |
| gills | deep pink `#D9508A` | flat | 10 min | 2 g |
| eyes ×2 | near-black `#2A2630` | the flat back | 2 min each | 0.2 g each |

About 2 h 30 min and 53 g of PLA in all, if each is printed on its own.
`chubby_axolotl.3mf` has all thirteen on one plate with their colours set:
- **With an AMS**, print the plate as it is.
- **On one colour**, print the pink parts, then the gills and the eyes as
  separate jobs (delete the others from the plate each time).

PLA, 0.20 mm layers, 0.4 mm nozzle, the orientation in the file. **Don't
scale**: the joints are in millimetres. The tail stands on its fin tip (a
13% footprint); if your plate is worn, add a brim to that part.

## The joints come from your test plate

Every joint is the test plate's ball joint: an 8 mm ball snapped into a cup
split by slits. **I've used the plate's middle value, 0.6 mm**, since your
results aren't in yet. If 0.4 or 0.8 felt better, it's one number (`BI` in
`chubby_axolotl.scad`) and a reprint of the parts with sockets: the head,
s1–s4. The legs' sockets are in s1 and s3.

Two differences from the plate, both forced by printing without supports:
- The spine's sockets open on the face each part stands on, so they print
  mouth down rather than up, with a cone for a roof. Same ball, same fit.
- The legs' sockets lie on their side in the print. Their roof is a peaked
  slot open to the mouth, so they grip on three fingers instead of four.
  Pulled straight out, a leg's ball meets 2.5 mm³ of plastic to the spine's
  3.4 (the plate's middle coupon measured 2.9). Tell me if the legs pop out
  too easily.

## Put it together

1. Press each eye into its hole in the face until its dome sits in the
   countersink. Three small ribs in each hole grip it.
2. Push the gills' two pegs into the holes on the back of the head. A drop of
   glue if they're loose.
3. Snap the chain together, front to back: s1's ball into the back of the
   head, s2's ball into the back of s1, then s3, s4 and the tail. Push each
   ball straight into its socket until it clicks.
4. Snap the legs into the belly: the four-toed pair into s1, the five-toed
   pair into s3. Toes forward, the leg leaning out.
5. Pose it. It stands on its four feet with its belly low over the desk.

## What was checked before this was pushed

- **Fits, on the exported prints, assembled** (`check_axolotl.py`):
  - At rest, no two parts touch, except each eye on its crush ribs
    (0.43 mm³, intended).
  - All four feet stand on the desk; nothing else reaches it.
  - **How far each joint turns** before two parts touch, side to side / up
    and down: head 14 / 24 up and 13 down, chest to hips 10–14 / 13–18, last
    joint to the tail 22 / 17. The body curls about 70° each way.
  - Each leg swings 15° forward and 16° back about its ball.
  - **Snap:** every ball meets plastic on its way out (above); none falls out.
- **Supports: none, on all twelve prints.** The slicer found these on the
  way:
  1. **The legs' sockets lie on their side, and three parts of them were
     propped** (4,272 support moves on s1 at first). Found by slicing each
     piece of the socket alone in a test block:
     - The hollow's roof: peaked over the centre only, it met the face in an
       edge the slicer propped (868 moves). It now runs out through the face
       as one peaked ridge: none.
     - Two slits above the ball cut slivers off the cup's shoulders (1,023
       moves). Now there are two slits below, and the open roof is the third.
     - The cup hung over the segment's rear flare (249 moves). The sockets
       moved 1.5 mm up the part and the flare was reduced.
  2. **The head was propped** (144 moves) until two changes: the maker's
     mark on its back grew from 4.4 to 5 mm letters (the first trace put the
     support under the 4.4 mm letters' ceilings), and the gills' peg holes
     moved off the edge (below). After both, none.
- **Product gate** (`tools/product_gate.py`): passes on ten of the twelve.
  - **s1 and s3 read FAIL on the wall check only**: 1% of their surface is
    under one bead (0.4 mm). It is the rim where each leg socket's pocket
    meets the belly, under the body. Moving the sockets inward and deeper
    didn't change it. The slicer prints it: print fidelity drops 0.25 and
    0.32 mm³ from those two parts, with no flags.
  - Two thin spots found on the way were fixed: the gills' peg holes sat
    0.45 mm from the edge of the head, and the vein ridges on the gills were
    exactly one bead wide.
- **Print fidelity** (`tools/print_fidelity.py`, every print): 0 flags.
- **Fragility** (`tools/fragility.py`, every print): 0 high, 0 watch.
- **The maker's mark**, OBC, is engraved on the back of the head, under the
  gills.

## What changed after the first render

The first full render read as marshmallows on sticks, not a chubby axolotl.
So before the checks above:
- **The gaps between segments went from 3.5 to 2 mm**, so the necks barely
  show. The joints turn less for it.
- **The sections are rounder** and have no ridges on top. The ridges read
  as spikes.
- **The tail became a tall, thin fin** on smooth curves. It had been a cone.
- **The legs became short and chubby**, with the belly low. They had been
  thin and held the body high.
- **The eyes became larger**, seated in a countersink so no gap shows round
  them.

## Renders

`images/axolotl_{face,hero,side,top}.png` were rendered in Blender from the
real exported parts, assembled, in their colours. They're design-review
renders, not photos. `images/head_as_printed_*.png` is the head rendered from
its sliced toolpath, an image the printer can make. The head is in the print
viewer as "Chubby Axolotl (head)".

## Rebuilding

- `./build.sh` exports every part (OpenSCAD's CGAL, about a minute).
- `./ship.sh` runs the fit check, gate, fidelity and fragility, and writes
  the 3MF.
- The STLs aren't committed; the 3MF holds every part.
