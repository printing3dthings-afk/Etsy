# Fold Stand

2026-11-04. Your pick, form A of four: a phone stand of two plates on a
clicking hinge. It sets at five angles and folds flat for a bag.

The second of the three practice designs. It practises detent hinges: a hinge
that clicks to set angles and holds there.

## What it is

- **Two plates standing as an A.** The front plate carries the phone on a lip
  at its foot, with a slot through the lip for a charging cable. The back
  plate is the leg.
- **A hinge barrel along the top.** It clicks at five openings, which lean the
  phone at about **81°, 75°, 69°, 63° and 57°** to the table. It also clicks
  when folded, so it stays shut in a bag.
- **Size:**
  - folded, 80 × 113 × 20 mm;
  - standing, 80 mm wide and about 110 mm tall.

## Printing

PLA, 0.2 mm layers, **no supports**, everything as it lies in the file.
Times and weights are from PrusaSlicer with the P1S settings, each print
sliced alone:

| print | file | colour | time | filament |
|---|---|---|---|---|
| front plate | `fold_stand_front.3mf` | lilac `#B79CE0` | 43 min | 28 g |
| back plate and 2 pins | `fold_stand_back_pins.3mf` | white `#F4F1EA`, pins pink `#F6A6C1` | 1 h 14 min | 33 g |

The set is about 1 h 56 min and 61 g. The pins can be the plate's colour; pink
just shows them in the renders.

- **The plates** print flat, the hinge barrels lying along the plate. Every
  bore is a teardrop in section, so nothing hangs.
- **The pins** print standing on their heads.
- **The OBC mark** is engraved on the back plate's inner face.

## Putting it together

1. Fold the back plate onto the front plate's inner face, so its barrel sits
   between the front's two.
2. Push a pin into each end of the hinge. A pin's end is teardrop-shaped, so
   it only goes in one way up, the point toward the phone side. Press it home.

The pins hold by a press fit in the front plate. If one works loose, tell me:
that's one number (`CLR_KEY`).

## How the clicks work

- **The pins:** each is keyed to the front plate by its teardrop end. The
  round part, inside the back plate's barrel, has a notch for each stop.
- **The blades:** inside the back plate's barrel two upright blades stand
  beside the pins. Each presses a small ridge onto its pin.
- **The click:** turning the hinge, the ridge rides up out of one notch, which
  bends the blade about 0.2 mm, and drops into the next.

The blades bend sideways, so every cut that makes them prints as a wall, with
no roof to sag.

**The phone's angle:** the phone's foot sits in the lip's corner, and its back
rests on the hinge barrel, which stands 12 mm proud of the plate. So the phone
stands about 7° steeper than the plate.

**What holds it up:** standing on a table, an A is mostly held by friction
under its feet, not by its hinge. `check_stand.py` works out, for each angle
with a 200 g phone, the least grip the feet need with the hinge free:

| opening | phone leans | feet apart | grip needed (μ) |
|---|---|---|---|
| 24° | 81° | 44 mm | 0.13 |
| 36° | 75° | 65 mm | 0.23 |
| 48° | 69° | 86 mm | 0.33 |
| 60° | 63° | 105 mm | 0.45 |
| 72° | 57° | 124 mm | 0.57 |

I haven't measured how well PLA grips a desk. Figures quoted for plastic on
wood are typically around 0.3 to 0.5, but surfaces vary. So the steep angles
should stand on friction alone, while the flattest one or two also rely on the
clicks and might slide open on a slick, glossy surface. That's worth trying on
the first print.

## Checked before it was pushed

The results are in `checks/`.

**Hinge (`check_stand.py`, on the exported parts): all pass.**

- **At every stop**, folded and the five openings, nothing touches: each ridge
  sits in its notch.
- **Halfway between stops**, the ridges ride up on the pins: the click.
- **The plates never meet** anywhere from folded to fully open, checked in 1°
  steps.
- **Keyed:** a pin turned 4° in the front plate hits it.

**Product gate: all three prints pass.** 0 supports, 0 overhang perimeters,
every wall at least 1.2 mm.

**Print fidelity: 0 flags on all three.**

**Fragility:** nothing high and nothing on watch.

**What it took:**

- **Equal legs:** the back plate started 10 mm shorter than the front. Nearly
  closed, the A then leaned hard toward the short leg, and the phone stood no
  steeper than 62°. Equal legs give a lean that falls 1° for every 2° it
  opens.
- **The phone's angle:** the first stops were set as if the phone lay flat on
  the plate. The first render showed it can't: it rests on the barrel, 7°
  steeper. The check now models that, and the stops were moved to match.
- **Uncapped teardrops:** the bores' teardrop points were capped flat to keep
  the barrels small, but the 2.5 mm caps counted as overhangs. The barrels are
  bigger (8.2 mm radius) and the teardrops run to a point.
- **The tongues:** they first lay under the bore over a 1 mm gap, and the
  slicer propped the gap's roof. They're upright blades now.
  - A narrow slot between blade and bore left knife-edged wedges. Each blade
    stands in an open window over the bore's outer half instead.
  - A strip of barrel outside each blade tapered to 0.02 mm, so it's gone.
- **The pin's head:** it was smaller than the pin's own teardrop, which then
  overhung it.
- **The mark:** engraved into the face on the plate, its letters' roofs were
  bridges. It's on the inner face now, which prints facing up.

**Not tested on the printer yet.** What I'd check first:

- **the click:** firm but not stiff. The ridge height (`NOTCH`, 0.35 mm) and
  the blade's thickness (`BLADE_T`, 2.0 mm) tune it;
- **the pins' press fit;**
- **whether the flattest angle slides on your desk.**

## Renders

In `images/`:

- `fold_stand_{front,three_quarter,top}.png`: standing at the second angle,
  with a plain dark slab for a phone, resting on the lip and the barrel.
- `fold_stand_side.png`: the A from the side, without the phone.
- `fold_stand_folded.png`: folded flat.
- `fold_stand_prints.png`: the plates and pins as they lie on the plate.
- `fold_stand_front_as_printed.png`: the front plate rendered from its sliced
  toolpath, so it shows what the printer lays down. The faint diagonal line
  on its top face is where the slicer's top layer changes direction.

These are design-review renders from the real exported parts, not photos.

Rebuild everything with `./ship.sh`, then `python3 render_stand.py`.

## How-to guide

`guide/Fold_Stand_Guide.pdf` (2026-11-05), four pages:
1. the stand and what's in the bag;
2. putting it together: fold the plates, then push in the pins;
3. the five angles side by side, putting a phone on and the charging slot;
4. folding it away, and what to do if something's not right.

Its pictures are renders of the real parts (`guide/render_guide.py`), not
photos. Rebuild with `python3 guide/render_guide.py && python3 guide/build_guide.py`.
