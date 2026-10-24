# Leland's Toy Story pieces: how to print them

For Leland's 2nd birthday. **Personal, not for sale**: Toy Story is
Disney/Pixar's, so these stay out of the shop, the catalogue and the public
viewer.

Both use 0.2 mm layers and need **supports off**. The checks below were all
run on the gate's slicer at those settings.

## Pizza Planet rocket night light: `rocket/pizza_planet_rocket.3mf`

Two objects on one plate:
- **the rocket**, standing up, in four parts: white body, red (nose, fins,
  bands, planet cone), blue (pedestal, porthole rings), yellow (PIZZA
  PLANET, the planet);
- **the base plate**, flat, in blue.

| | |
|---|---|
| size | 90 mm across, 194 mm tall |
| filament | about 88 g |
| slots | 1 white `#F4F1EA`, 2 red `#C8312B`, 3 blue `#2B5FA8`, 4 yellow `#F2C230` |
| supports | **off**: the slice needs none (0 support moves, 0 overhang perimeters) |

**Assembly, for a two-year-old's room:**
1. Put a battery LED tealight (standard 38–39 mm) in the ring on the base plate.
2. Set the rocket over it and screw the plate on from underneath with **two
   M3 × 10 mm self-tapping screws** (or #4 × 3/8"). The holes are pilot-sized
   for them.

The coin cell in the tealight is the reason for the screws. Leave nothing he
can open by hand. Put it on a shelf or nightstand he can see but not chew on.

## LELAND plaque: `plaque/leland_plaque.3mf`

Buzz Lightyear's open wings, from your photo of the toy:
- purple wings with red-and-white candy stripes over a green line;
- green end caps, with a red light on the left one;
- the jetpack in the middle, Woody's sheriff star above;
- LELAND across the wings in yellow with a red outline.

| | |
|---|---|
| size | about 218 × 77 mm, 9 mm thick |
| filament | about 42 g |
| supports | **off**: 0 support moves, 0 overhang perimeters |

**Five colours on four slots: one swap, mid-print.**

| slot | colour |
|---|---|
| 1 | **purple** `#6A3FB0`, swapped for **white** `#F4F1EA` |
| 2 | green `#5DBB3F` |
| 3 | red `#C8312B` |
| 4 | yellow `#F2C230` |

Purple is only ever the bottom 4.0 mm (the wings' face). White only ever
appears above it (the white stripes and the jetpack panel). In the 3MF slot 1
is one part covering both.

**How to set up the swap:**
1. In Bambu Studio, slice.
2. In the preview, drag the layer slider to the first layer **above 4.0 mm**
   (4.2 mm).
3. Right-click the **+** on the slider and choose **Add pause**.
4. When the P1S pauses there, unload slot 1, put the white spool in that slot,
   load it, and resume.

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
  slicer support the rocket: 15,600 and 5,686 moves.
- On the plaque, square stripe bands hung past rounded panel corners, the
  letter outline ran over the panel seam, and SHERIFF was too thin to print
  at three sizes, so it was left off the star.

The renders in `rocket/images` and `plaque/images` are renders of the model,
not photos.
