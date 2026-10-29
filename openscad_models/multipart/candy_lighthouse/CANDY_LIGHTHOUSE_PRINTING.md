# Candy Lighthouse: printing notes

2026-10-29. Your pick: form 5 of the candy dispensers, the spiral-slide
tower, built as a lighthouse helter-skelter for M&Ms or Skittles.

Fill the clear lantern room with candy. Each click of the red roof drops one
candy through the gallery floor, down a chute inside the tower, and out of an
arched door onto the slide. The slide winds once round the tower to the tray
at the foot.

It's 100 mm across the tray and about 255 mm tall to the tip of the finial.

## The prints

| print | colour | as it sits in the file | one colour, from the slicer I check with |
|---|---|---|---|
| tower: tray, striped tower, slide, gallery | white `#F4F1EA`, red bands and parapet `#C8312B`, blue tray `#3A6EA5` | upright | 2 h 55 min, about 114 g |
| wheel: the dispensing disc and its shaft | white | disc down | 34 min, about 13 g |
| lantern: the candy hopper | clear or translucent | **upside down**, roof end on the bed | 41 min, about 24 g |
| roof: the knob you turn | red | upright | 31 min, about 14 g |

Grams are PLA at 1.24 g/cm³. The tower is the only multi-colour print. In
its three colours, with colour-change purges, the slicer I check with gives
about 9 h 50 min and 189 g. Bambu Studio's own purge settings will differ.

`candy_lighthouse.3mf` has all four on one plate, with every colour part
assigned. `candy_lighthouse_head_test.3mf` is the head-test puck below.

## Print settings

- PLA, 0.20 mm layers, 0.4 nozzle, **supports off**, the orientation in the
  file.
- Every print was sliced with supports switched on and needed none.
- **Don't scale.** The candy sizes, the click and the shaft fit are all in
  millimetres.

## Put it together

1. Drop the wheel onto the gallery floor, shaft up. Turn it until it drops
   into its click: four nubs on the floor sit in four dimples under the disc.
2. Set the lantern into the groove round the gallery, with its little key in
   the notch. The key puts the baffle inside it over the outlet.
3. Fill the lantern with candy.
4. Put the roof on. Its D-shaped socket goes over the wheel's D-shaped shaft,
   and its rim seats on the lantern.
5. Turn the roof. Every quarter turn clicks, and one candy goes.

## Test before you print the tall part

**I haven't been able to check two things with candy:**

- **The candy size is a guess.** Nothing published gave the size of an M&M or
  a Skittle. I designed for 14 mm across and 8 mm thick, which should hold
  either. Measure a few of yours. Peanut M&Ms won't fit.
- **The slide is steep but untested.** It's 38° at its middle and 31° along
  the rail, where a candy actually runs. Whether candy slides on PLA at 31° is
  a physical question. Tilt a flat PLA print to about 30° and put a candy on
  it. If it sticks, tell me and I'll make the slide steeper.

**The head test** (`candy_lighthouse_head_test.3mf`, 25 min, about 15 g) is
the gallery top on its own, as a 14 mm puck:

- Print it plus the wheel, the lantern and the roof, and stand it on a mug.
- Fill it and turn the roof. Each candy should drop straight through into
  the mug.
- That tests the pocket size, the click and the baffle with your actual candy
  before you spend 3 hours on the tower.

## How the chute works, and why it changed

The chute drops straight down from the outlet, steps inward at 50° so it stays
inside the tower, falls down an upright shaft, and runs out down a 50° ramp
through the arched door.

The first version ran the chute out through the slope under the gallery. Any
opening cut into a sloping underside leaves corners the slicer has to prop,
and it propped them with a column of support from the tray all the way up:
18,965 support moves. Reshaping that opening never got it to zero. Inside the
tower it's zero.

The door's sill is 0.4 mm above the slide's head. The candy drops about 12 mm
from the sill to the slide below the door's middle. The rail is 9 mm tall.

## What was checked before this was pushed

- **Fits, on the exported prints** (`check_lighthouse.py`). Every one is
  0 mm³ of overlap:
  - The wheel against the tower, seated in its detent and lifted 1.0 mm onto
    the nubs at 15° steps through a quarter turn.
  - The wheel against the lantern's baffle in the same positions.
  - The shaft in the roof's socket, turning with the roof.
  - The lantern in its groove and the roof on the lantern.
  - The chute: a 15 mm disc, lying flat, fits at every height of the outlet,
    the step and the shaft. A flat 14 × 8 mm candy clears the door, 0.5 mm
    above the sill.
- **Product gate:** all five prints pass (tower, wheel, lantern, roof, head
  puck).
- **Supports: none, on all five.** Fixes the slicer forced, each found by
  slicing:
  1. The chute, above.
  2. **The parapet's slot tops are pointed.** Flat, each 1.4 mm top was a
     bridge the slicer propped all the way from the tray. A 0.9 mm point was
     clean on the head puck but still propped on the tower, whose gallery
     falls at a different place in the 0.2 mm layers. A 1.4 mm point is clean
     on both.
  3. **The wheel's detent dimples are cones**, not hemispheres.
  4. **The roof's lantern seat and shaft socket have peaked tops**, since both
     are cut from below a part that prints upright.
  5. **The lantern's glazing bars and key have sloped ends**, since the
     lantern prints upside down and those ends become undersides.
- **Print fidelity** (`tools/print_fidelity.py`, every colour part): no
  flags on the wheel, the lantern, the roof or the head puck. The tower has
  2 flags, 0.09 and 0.06 mm³, at the door's sill. That's the thin lip where
  the 50° ramp meets the wall, and it prints about 0.3 mm short, which you
  won't see.
- **Fragility** (`tools/fragility.py`): 0 high and 0 watch on all five. The
  only slender run is the roof's finial, at slenderness 3.5, under the watch
  line.

## Renders

`images/lighthouse_{front,three_quarter,top}.png` were rendered in Blender
from the real exported parts, assembled. They're design-review renders, not
photos. The lantern is shown as pale blue, standing in for clear filament.

`images/tower_as_printed.png` is the tower rendered from its sliced toolpath,
so it's a picture the printer can actually make. The tower is also in the
print viewer as "Candy Lighthouse (tower)".

## Rebuilding

- `./build.sh` exports every part (OpenSCAD's CGAL, about 2 minutes).
- `./ship.sh` runs the fit check, gate, fidelity and fragility, and writes
  the 3MFs.
- `python3 render_lighthouse.py --views` renders the three views.
- The STLs aren't committed; the 3MFs hold every part.
