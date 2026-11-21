# Gingerbread cookie, face down: test piece (2026-11-21)

Scott: "We also need to start designing prints that are printed facedown so the image is flat
and looks great. Can you make just the gingerbread man part of the tin clicker face down. I want
it as a test piece."

**Not printed yet.** `images/` holds design-review renders, not photos.

## What changed from the clicker's cookie
- **Unchanged:** the outline, the size (45.4 × 47.1 × 6.2 mm) and the switch socket. It still
  drops into the Tin Clicker's lid.
- **The face is the first layer on the plate.** It's flat, with the plate's finish: textured
  PEI gives an even matte grain, smooth PEI gives gloss.
- **The colours are flush, not raised.**
  - The icing, eyes, smile, cheeks, bow and gumdrops are set 0.8 mm (four layers) into the face.
  - Every colour change happens in those first four layers. The rest prints in brown alone.
  - This is the trade-off: the face-up cookie's icing is piped and rounded, 0.8 mm proud; here
    it's flat colour.
- **The pupils** are smaller (0.75 mm radius) and nearer each eye's centre. A white ring round
  each one now has to print as a ring, so it's kept a bead wide.
- **The face's edge** is a small chamfer, 0.4 mm in over 0.6 mm up, instead of the rolled edge.
  - A rolled edge would start as a hanging lip on the plate.
  - At a full 45° the gate's slicer put support round the whole edge.
- **Mirroring:** it's built face up and turned over with a rotation, never mirrored, so the face
  reads the right way round off the plate.

## Numbers (Bambu Studio, P1S, 0.4 nozzle, PLA Basic, 0.20 mm Standard, AMS)
| | face down (this) | face up (`checks/cookie_ams.gcode.3mf`) |
|---|---|---|
| Time | 38 m 49 s | 45 m 53 s |
| Filament | 9.93 g (brown 5.76, white 2.29, red 0.85, green 1.03) | 12.76 g |

## Checks
- **Product gate:** passed (`gate.txt`). 0 support moves. The socket post's walls are declared
  like the shipped cookie's: they're set by the switch.
- **Print fidelity:** 0 flagged (`fidelity.txt`); nothing dropped or filled.
- **Fragility:** 0 high, 0 watch (`fragility.txt`).
- **Viewer:** `gingerbread_cookie_facedown`.

## File
`cookie_facedown.gcode.3mf`. AMS slots: 1 brown, 2 white, 3 red, 4 green. Print on whichever
plate gives the finish you want on the face.

## What to look at when it's printed
- Is the face flat and even, with no first-layer ridges or gaps?
- Are the colour edges crisp, with no brown showing through the white?
- Do the pupils read, with white all round them?
- Does it still drop into the lid and press the switch?
- Next to the face-up cookie: which looks better at arm's length?
