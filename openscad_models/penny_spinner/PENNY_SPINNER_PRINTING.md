# Penny Spinner

2026-11-04. Your pick, form 4 of five: a low desk top weighted with US
pennies at the rim, so it carries more spin.

## What it is

- **Eight round petals** round the rim, each a pocket for two pennies.
- **A window** in each petal's top shows the penny's copper, so the top reads
  as a teal flower set with copper. The pennies are what give it the weight.
- **A hex stem** to twirl it by.
- **A round tip** underneath, on a cream base.

It holds 16 pennies (40 g). It also spins empty, or with pennies in opposite
pairs of pockets.

**Pennies are not included.** The listing and every photo must say so. The
renders show them.

**Size:** 79 mm across and 45 mm tall, the stem included. It weighs 31 g
printed, 71 g with 16 pennies.

## Printing

Three prints, one colour each, no supports, no glue. PLA, 0.2 mm layers,
everything as it lies in the file. Times and weights are from PrusaSlicer
with the P1S settings:

| print | file | colour | time | filament |
|---|---|---|---|---|
| crown | `penny_spinner_crown.3mf` | teal `#3B8E8A` | 32 min | 14 g |
| base and stem | `penny_spinner_base_stem.3mf` | cream `#F4F1EA` | 45 min | 17 g |

The whole set is about 1 h 16 min and 31 g.

- **The crown** prints the right way up. Its pockets open underneath and
  narrow at 34° into the windows, so nothing hangs.
- **The base** prints upside down, so the tip is the last thing printed. The
  OBC mark is engraved on the flat ring underneath.
- **The stem** prints standing on its grip.

## Putting it together

1. Turn the crown upside down and drop two pennies into each pocket.
2. Set the base on it, also upside down.
3. Turn the stack over and push the stem down through the crown's hole into
   the base until it clicks.

To change the pennies, hold the base and pull the stem out firmly.

Use pennies from 1982 on (2.5 g), or keep the older, heavier ones (3.11 g) in
opposite pockets. One old penny among new ones puts the weight 0.18 mm off
centre. How much that shows in a spin is one of the things a test print will
tell.

## How it holds together

- **The stem's hex** runs through a hex hole in the crown and into a hex
  socket in the base. A twirl turns all three together, and nothing
  unscrews.
- **The snap pin** on the stem's end clicks into a socket in the base and
  holds the stack together. It's the gift box's snap pin, made bigger for
  this:
  - 4.4 mm across, with 1.7 mm prongs and a 4.5 mm slot;
  - the barb stands 0.4 proud, about 1.6% strain in PLA.

The first version joined crown and base with a printed threaded stud. A
stud that small is nearly all thread, and every tooth's crest failed the
1.2 mm wall floor, so the stem became the joint.

## Checked before it was pushed

The results are in `checks/`.

**Fit and balance (`check_spinner.py`, on the exported parts): all pass.**

- **Crown and base:** they sit together touching nothing, with the stem
  clear of both.
- **The stem:** pulled 0.5 mm up, the barb catches in the base. Turned 6°,
  the hex hits both the crown and the base, so the twirl is keyed.
- **The pennies:** two in each pocket touch nothing. Lifted 1 mm or pushed
  0.5 mm out, they hit the pocket. The window is 15 mm across against a
  penny's 19 mm, so none can leave.
- **Balance:** empty, the centre of mass is 0.007 mm off the spin axis.
- **Weight:** the pennies more than double the top's spin inertia, counted
  against solid plastic. Printed with infill, the plastic weighs less, so
  their share is larger still.
- **Lean:** it can lean 19.5° before the rim touches the table. Its centre of
  mass sits 17 mm above the tip.

**Product gate: all three prints pass.** 0 supports, 0 overhang perimeters.

**Print fidelity: 0 flags on all three.** Nothing dropped or filled.

**Fragility:** nothing high and nothing on watch.

**What it took:**

- **The stud** was replaced by the stem, as above.
- **The window's edge** was a knife edge where the bevel met the top face. The
  window now runs straight up 1.2 mm above the bevel.
- **The stem's pin** went from the gift box's 3.4 mm to 4.4 mm. On a small
  part the smaller prongs were too much of what the gate measured.
  - The slot now runs through the end of the hex as well. The library's
    slot left 0.25 mm slivers bridging its ends.
  - It runs flat to flat across the hex. At 45° it cut thin wedges where it
    met the flats.
- **Two OpenSCAD and tooling traps:**
  - The socket's mouth only touched the end of the hex socket, so it came
    out as a sealed void. `clean_parts.py` filled that void back in without
    a word, leaving the pin in solid plastic. The two now overlap, and
    `clean_parts.py` warns when it fills a void.
  - The base's thread, in the stud version, came out left-handed. Mirroring
    a right-hand thread reverses it.

**Not tested on the printer yet.** What I'd check first:

- how firmly the stem clicks in, and that it pulls out again;
- how long it spins with and without pennies. That's the claim worth a
  number before it goes in a listing.

If the stem is too stiff or too loose, tell me. The barb (`SP_B`) and the
socket's clearance (`SK_T`) are one number each.

## Renders

In `images/`:

- `penny_spinner_{front,three_quarter,top}.png`: assembled with 16 pennies.
- `penny_spinner_exploded.png`: pulled apart in the order it goes together.
- `penny_spinner_prints.png`: the three prints as they lie on the plate.

These are design-review renders from the real exported parts, not photos. The
pennies are plain copper discs.

Rebuild everything with `./ship.sh`, then `python3 render_spinner.py`.
