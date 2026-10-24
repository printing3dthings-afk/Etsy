# Leland's Toy Story pieces: how to print them

For Leland's 2nd birthday. **Personal, not for sale**: Toy Story is
Disney/Pixar's, so these stay out of the shop, the catalogue and the public
viewer.

Both use 0.2 mm layers and need **supports off**. Both designs sit on the
0.2 mm grid (the plaque's swap is at exactly 4.0 mm), which is why they are
sliced at 0.20 mm and not finer.

**Sending them to the printer from here:** once the bridge update is running on
your home machine, I can stage either file in the Action Center. You approve it
with the plate clear and the spools loaded, and the bridge starts it if the P1S
is idle.

## Pizza Planet rocket night light

Ready to print: `rocket/gcode/pizza_planet_rocket.gcode.3mf`, sliced by Bambu
Studio with its own P1S profiles. The editable project is
`rocket/pizza_planet_rocket.3mf`.

Two objects on one plate:
- **the rocket**, standing up, in four parts: white (body, fins), red (nose,
  bands, planet cone), blue (pedestal), and yellow (PIZZA PLANET, the planet);
- **the base plate**, flat, in blue.

The portholes are V-grooves cut into the white body, and they glow when it is
lit. White fins and grooved ports bring the AMS colour changes down from 611
to 85, so the print takes about 8 hours instead of 24.

| | |
|---|---|
| size | 90 mm across, 194 mm tall |
| time | 7 h 47 m (Bambu Studio's estimate, 0.20 mm layers) |
| filament | about 167 g, including the purge tower and flushing |
| slots | 1 white `#F4F1EA`, 2 red `#C8312B`, 3 blue `#2B5FA8`, 4 yellow `#F2C230` |
| supports | **off**: the slice needs none |

**Assembly, for a two-year-old's room:**
1. Put a battery LED tealight (standard 38–39 mm) in the ring on the base plate.
2. Set the rocket over it and screw the plate on from underneath with **two
   M3 × 10 mm self-tapping screws** (or #4 × 3/8"). The holes are pilot-sized
   for them.

The coin cell in the tealight is the reason for the screws. Leave nothing he
can open by hand. Put it on a shelf or nightstand he can see but not chew on.

## LELAND plaque

Ready to print: `plaque/gcode/leland_plaque.gcode.3mf`, with the pause already
in it. The editable project is `plaque/leland_plaque.3mf`.

Buzz Lightyear's open wings, from your photo of the toy:
- purple wings with red-and-white candy stripes over a green line;
- green end caps, with a red light on the left one;
- the jetpack in the middle, Woody's sheriff star above;
- LELAND across the wings in yellow with a red outline.

| | |
|---|---|
| size | about 218 × 77 mm, 9 mm thick |
| time | 4 h 28 m (Bambu Studio's estimate, 0.20 mm layers), plus the swap |
| filament | about 77 g, including the purge tower and flushing |
| supports | **off**: 0 support moves, 0 overhang perimeters |

**Five colours on four slots: one swap, mid-print.**

| slot | colour |
|---|---|
| 1 | **purple** `#6A3FB0`, swapped for **white** `#F4F1EA` |
| 2 | green `#5DBB3F` |
| 3 | red `#C8312B` |
| 4 | yellow `#F2C230` |

Purple is only ever the bottom 4.0 mm (the wings' face). White only ever
appears above it (the white stripes and the jetpack panel).

**The swap:** the sliced file pauses by itself at 4.2 mm. When the P1S stops,
yellow is in the nozzle and purple sits in the AMS. So don't press Unload:
open the AMS, take the purple spool and its filament out of slot 1, put the
white spool in slot 1 and feed its end in until the AMS grabs it, then resume. (Printing from the
editable `.3mf` instead? In Bambu Studio's preview, drag the layer slider to
4.2 mm, right-click the **+** and choose **Add pause**.)

Hang it with Command strips or mounting tape on the flat back: no screws, and
nothing on it that can come off.

## Checks, run on the meshes in this folder

**Rocket:**
- **Mesh gate:** passed on the CGAL meshes. Colour parts are separate
  pieces by design.
- **Supports:** 0 support moves, 0 overhang perimeters.
- **Print fidelity:** 0 flags (3 mm³ of tiny misses in total).
- **Fragility:** 0 slender members.

**Plaque:**
- **Supports:** 0 support moves, 0 overhang perimeters.
- **Print fidelity:** 0 flags (0.6 mm³).
- **Fragility:** 0 slender members.

**What it took**, recorded in the .scad sources at each fix:
- The porthole glow pockets and the stepped letter climb both made the
  slicer support the rocket: 15,600 and 5,686 moves. Cut straight in, the
  porthole grooves did too: their flat ceilings drew 25,806 support moves.
  As V-grooves whose ceilings climb at 34 degrees they need none.
- On the plaque, square stripe bands hung past rounded panel corners, the
  letter outline ran over the panel seam, and SHERIFF was too thin to print
  at three sizes, so it was left off the star.

The renders in `rocket/images` and `plaque/images` are renders of the model,
not photos.
