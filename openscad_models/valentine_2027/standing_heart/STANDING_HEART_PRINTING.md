# Standing Heart Love Lantern — printing notes

Built 2026-10-26 from Scott's Valentine's 2027 brief. Form 1 of five
(`../concepts/lantern_forms.jpg`), picked with the Swan Crown.

A heart standing in a pedestal, over a battery LED tealight:

- **the heart**: its front and back are 0.9 mm panes, so they glow. Built into
  the back of the front pane is a couple under a lamppost in falling snow,
  with a heart over them. Built into the back of the back pane are two swans
  whose necks draw a heart. Unlit, both faces look plain. Lit, the scenes show
  dark on the glow, the way a lithophane does. A raised outline runs round
  both faces, so the heart's shape reads in daylight.
- **the pedestal**: the two names and the date stand out of its front.

It is one piece with an open base: it lifts off and goes back down over the
light. Inside the pedestal is 53 × 55 mm, room for any tealight. It measures
104 × 61 × 120 mm.

The maker's mark, OBC, is engraved 0.8 mm into the underside of a small shelf
inside the pedestal's front. It reads O-B-C when the lantern is tipped back
to look at its base. This was checked on the exported geometry, not assumed.

## Print

| setting | value |
|---|---|
| file | `standing_heart_lantern.3mf` (one object, five parts, aligned) |
| filament | **matte white PLA**, one colour: assign it to every part |
| layer | 0.2 mm, Bambu's 0.20 Standard on the P1S, 0.4 nozzle |
| supports | **off**. The slicer finds none to add (gate, below) |
| plate | textured PEI |
| time | about 3 h 0 m, 105 g (P1S motion model) |

The parts are colour only so the renders can show them apart:

| part | what it is |
|---|---|
| frame | pedestal, the heart's rim, the ledge with the mark |
| glass | the two glowing panes, and the solid core under the heart's top |
| art | the two scenes, inside the panes |
| lip | the raised outline on both faces |
| text | the names and date |

## Personalise

Edit the two lines at the top of `standing_heart_lantern.scad`, or pass them in:

    NAMES="Ava & Noah" DATE="06.21.2025" ./build.sh cgal
    NAMES="Ava & Noah" DATE="06.21.2025" ./build.sh union

The names are sized to the flat of the pedestal's front, measured on Playfair
Display grown 0.25 mm, so its hairlines print. A pair too long for 3.6 mm
letters breaks onto two lines after the "&", so "Alexandria & Maximilian" fits
at about 4.0 mm.

The names are spaced 1.08 and the date 1.25, and cleaned only of gaps and
strokes under 0.4 mm (2026-10-27). Until then a heavier clean filled every
letter's counter and ran the date into one shape: the first renders showed
the names as solid blobs. Measured on the glyphs, the date now prints as its
ten characters.

## How the inside prints (why it looks the way it does)

The heart is hollow, and its ceiling is one tent peaked at the notch, sides at
58°, so every part of it leans down to a wall. A tent per lobe looked better
on paper. The two tents met in a valley under the notch that ran pane to pane
in mid-air, and the slicer could only prop it up or bridge it.

Above the tent, slots up to 12 mm deep run behind each pane, so the panes stay
thin all the way up to the lobes' curve and the whole heart glows. The first
version stopped the hollow at the chords, and the lobe tops showed dark.

## Checks (2026-10-27, after the names fix)

- parts closed, no two overlapping (`logs/parts.txt`)
- **product gate passed** (`logs/gate.txt`): watertight, one body, 0 support
  moves, 0 overhang perimeters, full height, flat base, stable. Its wall floor
  is set to 0.8 mm for this piece, in `../check_valentine.py`, because the
  0.9 mm panes are the point (Scott's glow rule). Every structural wall is
  1.2 mm or more.
- print fidelity: 0 flagged (`logs/fidelity.txt`)
- fragility: 0 high, 0 watch (`logs/fragility.txt`)

## Images

`images/` holds renders of the model, not photos of a print:

- `*_colour_*` in the part colours, from three sides
- `*_as_printed_*` from the sliced toolpath, in white
- `*_night*` printed in white and lit by a point light where the flame goes

How dark the scenes read on a real print depends on the filament and the
light. The first test print is the real check.
