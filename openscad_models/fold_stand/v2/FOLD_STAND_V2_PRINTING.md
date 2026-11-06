# Fold Stand v2: a ratchet hinge with release buttons

2026-11-06. v1 (`../fold_stand.scad`) is untouched; this sits beside it.

## Why v2

You printed v1 and found two faults: "No click at all. Very loose pin falls
out."

- **The click.** v1's ridge stood 0.35 mm into a V-notch on a 4 mm pin.
  - That was too shallow to catch once printed.
  - A V pushes the ridge out whichever way the hinge turns. So even a good
    click would only have resisted the legs spreading a little, and the A
    depended on its feet gripping the table.
- **The pins.** They were a 0.05 mm press fit, and they printed loose.

You asked for "a gear system that clicks as you move it and it stays", with a
release tab. v2 is that.

## How the hinge works now

- **A ratchet on each pin.** Each pin has a ring of saw-tooth notches, one
  per angle. The blade's ridge has a flat top face.
  - **Opening:** the flat face meets a notch's flat face, and the hinge
    stops. The phone's weight can't spread the legs, however slick the
    table.
  - **Folding toward upright:** the ridge rides up the notch's ramp and drops
    into the next notch. That's the click.
- **The release buttons.** The pins' heads are buttons.
  - **Pinch both ends of the hinge** to release. Each pin slides in about a
    millimetre, a cone on it lifts the ridge clear of every notch, and the
    leg swings free.
  - **Let go:** the blade pushes back on the cone and the pin returns. The
    ridge drops into the next notch, which holds the hinge from opening.
- **The pins stay in.**
  - Past the notches each pin has a wall the ridge must climb before the pin
    can come out: the blade bent 1.15 mm, about 7 N of pull.
  - They're keyed in the front plate and slide there. There's no press fit
    to print loose.
- **It locks folded**, so it stays shut in a bag. Pinch to open it.

The angles are unchanged: the phone leans at about **81°, 75°, 69°, 63° and
57°**.

## Using it

1. **Open:** pinch the two buttons on the ends of the hinge, open the leg past
   the angle you want, and let go.
2. **Set the angle:** push the leg toward the front plate until it clicks.
   Each click is a steeper angle. It won't open again until you pinch.
3. **Fold it away:** push the leg flat. It clicks shut and stays shut.

## Printing

PLA, 0.2 mm layers, **no supports**, everything as it lies in the files.
Bambu Studio, P1S 0.4, 0.20 mm Standard, PLA Basic:

| print | file | colour | time | filament |
|---|---|---|---|---|
| front plate | `fold_stand_v2_front.3mf` | lilac `#B79CE0` | 1 h 7 min | 25.2 g |
| back plate and 2 pins | `fold_stand_v2_back_pins.3mf` | white `#F4F1EA` | 1 h 18 min | 27.5 g |

**The pins are in the plate's colour.** Printed pink beside the white plate,
that plate took 4 h 7 min: almost three hours of colour changes.

- **The pins** print standing on their heads. Their notches are cut upright,
  so the teeth come out crisp.
- **The blades** inside the back plate's barrel are 1.6 mm thick and 18 mm
  long, cut free by upright slots. They bend along their layers, the strong
  way.

## Putting it together

1. Fold the back plate onto the front plate's inner face, so its barrel sits
   between the front's two.
2. Push a pin into each end of the hinge, point of the teardrop toward the
   lip side.
   - It goes in stiffly over the last few millimetres: the ridge is riding
     over the pin's end.
   - Then it clicks in. That's it holding.
   - The head stands about 1 mm proud. That's the button's travel.

## Checks (`checks/`)

**Hinge (`check_stand_v2.py`, on the exported parts):** all pass. Each figure
is how far the blade has to bend.

- **Seats at every stop:** folded and all five angles, with 0.10 of preload.
- **Locks:** opening from any stop, the full 0.55 face is reached within
  0.75°. It's a radial face, so the ridge can't ride over it.
- **Clicks:** folding, the ridge rides up a ramp (0.14 after 0.75°), over the
  crest (0.55), and drops into the next notch.
- **Releases:** with the buttons pressed, the lift is 0.81–0.82 at every
  angle, above the crests. It turns free.
- **Returns:** 0.2 mm back out from pressed, the lift falls to 0.70. The
  blade pushes the pin back.
- **Retains:** pulled 1–2 mm out, the ridge must climb 1.15. The pin stays
  in.
- **Clears:** the plates never meet from 0 to 72°. The pins don't meet when
  both are pressed, and are keyed (a pin turned 4° hits).
- **Stands:** the stance is as v1.

**Product gate:** all three prints pass, with 0 support moves.

- The pin's teeth come to a point like a thread's. Their crests are left out
  of the wall measurement, as for threads.
- Print fidelity checks the teeth instead: 0.59 mm³ dropped, nothing
  flagged.

**Print fidelity:** 0 flags on all three. **Fragility:** nothing.

## On the way

- **Supports in the notches.** The first notches stopped where the pin's
  retaining wall began. That left a flat ceiling inside each notch, and the
  slicer propped it with 1,216 support moves. Each notch now climbs out at
  37° all the way to the full radius.

## Not tested on the printer yet. What I'd check first

- **The pins going in:** stiff but possible. They should click home. If they
  won't go in, tell me: `R_FREE` sets how far the ridge reaches in.
- **The click and the lock:** a firm click when folding, and a firm stop
  against opening.
- **The buttons:** pinching both should free the leg, and letting go should
  bring the buttons back out.
  - If they stay in, the return slope (`CONE`) is too shallow for your PLA.
  - If they're too stiff, it's too steep.

## Renders

In `images/`. These are design-review renders of the real parts, not photos.

Rebuild with `./ship_v2.sh`, then `python3 render_stand_v2.py`.
