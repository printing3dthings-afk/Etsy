# Pocket Pebble

2026-11-04. Your pick, form D of four: a smooth pocket pebble for rings,
earrings or a day's pills. It clicks shut and opens with one thumb.

The third of the three practice designs. It practises a box hinge and a snap
latch.

## What it is

- **A pebble in two shells.** The base and the lid meet at a seam, each curving
  in from the seam to a flat face. Closed, the two curves meet as one.
- **A hinge at the back.**
  - Three knuckles turn on two pins: two on the base, one on the lid.
  - Each knuckle stands on a buttress, so the hinge reads as a spine down the
    pebble's back. Inside the base, the buttresses stand as two short ribs on
    the back wall.
  - Open, the lid lies back at about 165°, nearly flat.
- **A latch at the front.** A tongue hangs inside the lid, and a bump on it
  clicks under a lip inside the base. Shut, it stays shut in a pocket.
- **To open:** a thumb in the scoop under the lid's front edge flicks it up.
- **Size:** 58 × 45 × 22 mm shut. Inside it's about 54 × 36 mm at the seam
  and 18 mm deep, 10 of that in the base.

## Printing

PLA, 0.2 mm layers, **no supports**, everything as it lies in the file.
Times and weights are from PrusaSlicer with the P1S settings, each part sliced
alone:

| print | file | colour | time | filament |
|---|---|---|---|---|
| base and 2 pins | `pocket_pebble_base_pins.3mf` | white `#F4F1EA`, pins pink `#F6A6C1` | about 20 min | 8.6 g |
| lid | `pocket_pebble_lid.3mf` | lilac `#B79CE0` | 13 min | 6.9 g |

The set is about 33 min and 15.5 g. The pins can be the base's colour; pink
just shows them in the renders.

- **The base** prints the right way up and **the lid** upside down, each on its
  flat face. Their walls lean out at most 31° (base) and 36° (lid) from
  upright.
- **The pins** print standing on their keyed end.
- **The OBC mark** is engraved in the base's floor, inside.

## Putting it together

1. Set the lid on the base, its knuckle between the base's two.
2. Push a pin into each end of the hinge. A pin's key is teardrop-shaped, so it
   only goes in one way up, the point up. Press it in until it's flush. Its end
   meets the lid's knuckle there, so it can't go too far.

The pins hold by a press fit in the base and turn freely in the lid. If one
works loose, tell me: that's one number (`CLR_KEY`).

## How it works

**The hinge:**

- **The axis** runs along the seam, 0.6 mm behind the back. Opening, the
  lid's back swings up and out, clear of the base.
- **Clearance:** each shell is cut away round the other's knuckles, with 0.4
  mm to spare.
- **The bores:** every bore is a teardrop in section, its point up as that part
  prints, so nothing hangs.

**The latch:**

- **The lip:** the base's front wall is thickened inside, behind the thumb
  scoop. A lip on that pad has a 45° lead-in on top and a 37° underside.
- **The bump:** the tongue's bump has a catch face parallel to the lip's
  underside, 0.25 mm below it.
- **Shut,** nothing touches, so the tongue rests unbent.
- **Lifting the lid,** the bump rides up the lip's underside and the tongue
  bends in.

## Checked before it was pushed

The results are in `checks/`.

**Fit (`check_pebble.py`, on the exported parts): all pass.**

- **Shut,** the lid, base and pins touch nothing.
- **The lid swings clear** of the base to 165°, checked in 1° steps. At 166°
  its back meets the base's: that's where it rests open.
- **The pins** turn freely in the lid's knuckle all the way. A pin turned 4°
  in the base hits it, so it's keyed. Pushed 0.5 mm past home, it meets the
  lid's knuckle: that's the stop.
- **The click:** the tongue bends in up to 0.68 mm as the lid lifts, most of
  it around 2° open, and it's free by 4.5°.

**Product gate: all three prints pass.** 0 supports, 0 overhang perimeters,
every wall at least 1.2 mm.

**Print fidelity:** 0 flags on the base and the pins, and 2 on the lid.

- **Where:** the lid's 2 are a feather edge above each of the base's
  knuckles, on the inside, where the lid wall's cut-out meets its inner face.
- **What it means:** the slicer leaves off about 0.06 mm³ there, so that edge
  prints about 0.2 mm blunt. It isn't a contact face, so the fit isn't
  affected.

**Fragility:** nothing high and nothing on watch.

**What it took:**

- **The knuckles' gussets:** at first each knuckle sat on a teardrop, its point
  down.
  - The point hung in the air 2.4 mm out from the shell, which leans in below
    the seam, and the slicer propped it.
  - Each knuckle now stands on a buttress to its own shell's flat face, its
    outer face at 36°.
- **The pins' heads:** the heads sat outside the knuckles, where the shell
  walls curve back in, and ran into them. They're gone. Instead, the pin's
  key stops against the lid's knuckle.
- **The pins' keys:** the teardrop's sharp point was under one bead wide. It's
  capped where it narrows to 1.2 mm.

**Not tested on the printer yet.** What I'd check first:

- **the click:** firm enough to hold shut in a pocket, easy to flick open. The
  bump's height (`BUMP`, 0.8 mm) tunes it;
- **the pins' press fit;**
- **the scoop:** whether a thumbnail finds the lid's edge easily.

## Renders

In `images/`:

- `pocket_pebble_{front,three_quarter,top}.png`: shut.
- `pocket_pebble_open.png`: open at 110°, the tongue in the lid and the lip
  and mark in the base.
- `pocket_pebble_prints.png`: the base, lid and pins as they lie on the plate.
- `pocket_pebble_base_as_printed.png`: the base rendered from its sliced
  toolpath, so it shows what the printer lays down.

These are design-review renders from the real exported parts, not photos.

Rebuild everything with `./ship.sh`, then `python3 render_pebble.py`.
