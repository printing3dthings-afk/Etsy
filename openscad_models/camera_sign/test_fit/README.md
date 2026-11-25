# Camera sign: the clearance test (2026-11-25)

Scott: "I want you to make my sign for inside my printer to show during timelapse. I'm going to
put it up to test its clearance." So the gaps get settled by fitting the sign itself, instead of
the gap gauge.

## The files
| file | thickness off the wall | time, filament | notes |
|---|---|---|---|
| `../gcode/camera_sign_neon_two_colour.gcode.3mf` | 2.4 mm | 29 m 32 s, 7.3 g | first choice |
| `../gcode/camera_sign_plaque_two_colour.gcode.3mf` | 2.4 mm | 44 m 32 s, 13.2 g | first choice |
| `camera_sign_neon_1.6mm.gcode.3mf` | 1.6 mm | 25 m 35 s, 4.6 g | fallback |
| `camera_sign_plaque_1.6mm.gcode.3mf` | 1.6 mm | 38 m 45 s, 7.8 g | fallback |

All four have black bases and orange lettering (the AMS changes on the top four layers only),
with no supports. The 2.4 mm slices were re-made today with the current slicer tool.

- **The 2.4 mm signs** pass the gate (CAMERA_SIGN.md).
- **The 1.6 mm signs fail the gate's wall rule, as expected:** their plate is 0.8 mm under the
  letters (`gate_*_1.6.txt`). That holds taped flat to a wall but is flimsy to peel off, so use
  it only if 2.4 doesn't clear.

## The test, with the printer idle
1. Tape the sign where it'll live: on the back wall, to one side of the lead screw's slot, never
   over it.
2. **The toolhead:** in Bambu Handy, Controls, jog Y to the back in small steps, watching the
   sign. Nothing may touch it, the cable chain included.
3. **The bed:** jog Z up to the top in small steps, watching the bed's back edge pass the sign.
4. **If anything comes within a millimetre,** stop and take it down. Try the 1.6 mm version, or
   move it.
5. **Readability:** run a short print with timelapse on. Can "@onbrandcraftz2026" be read on the
   recording?

Never start a print with the sign up until steps 2 and 3 have passed.
