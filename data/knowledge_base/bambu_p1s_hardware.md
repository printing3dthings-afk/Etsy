# Bambu Lab P1S — hardware reference

Every number here is from **Bambu Lab's own published P1S Technical
Specifications PDF** unless a row says otherwise. Read 2026-09-19. Where a
figure contradicts what this repo previously believed, the contradiction is
called out rather than quietly overwritten — see "Corrections" at the end.

Source: `bambu-lab-P1S-tech-specs.pdf` (Bambu Lab), mirrored at
createeducation.com. Cross-checked against Bambu's store listing and the
Bambu Lab wiki where those were reachable.

## Official specification

| Group | Item | Specification |
|---|---|---|
| | Printing technology | Fused Deposition Modeling |
| Body | Build volume (W×D×H) | **256 × 256 × 256 mm³** |
| Body | Chassis | Steel |
| Body | Shell | Plastic & glass |
| Toolhead | Hot end | All-metal |
| Toolhead | Extruder gears | Steel |
| Toolhead | Nozzle | **Stainless steel** |
| Toolhead | Max hot end temperature | **300 °C** |
| Toolhead | Nozzle diameter (included) | 0.4 mm |
| Toolhead | Nozzle diameter (optional) | 0.2, 0.6, 0.8 mm |
| Toolhead | Filament cutter | Yes |
| Toolhead | Filament diameter | 1.75 mm |
| Heatbed | Build plate (included) | **Bambu Dual-Sided Textured PEI Plate** |
| Heatbed | Build plate (optional) | Cool Plate, Engineering Plate, High Temperature Plate |
| Heatbed | Max build plate temperature | **100 °C** |
| Speed | Max speed of toolhead | **500 mm/s** |
| Speed | Max acceleration of toolhead | **20 m/s²** (= 20,000 mm/s²) |
| Speed | Max hot end flow | **32 mm³/s** — measured @ABS, 150×150 mm single wall, Bambu ABS, 280 °C |
| Cooling | Part cooling fan | Closed loop control |
| Cooling | Hot end fan | Closed loop control |
| Cooling | Control board fan | Closed loop control |
| Cooling | Chamber temperature regulator fan | Closed loop control |
| Cooling | Auxiliary part cooling fan | Closed loop control |
| Filtration | Air filter | Activated carbon filter |
| Filament | PLA, PETG, TPU, ABS, ASA, PVA, PET | **Ideal** |
| Filament | PA, PC | **Capable** |
| Filament | Carbon/glass fibre reinforced polymer | **Not recommended** |
| Sensors | Chamber monitoring camera | **Low rate, 1280 × 720 @ 0.5 fps**, timelapse supported |
| Sensors | Filament run-out sensor | Yes |
| Sensors | Filament odometry | Optional, with AMS |
| Sensors | Power loss recovery | Yes |
| Physical | Dimensions (W×D×H) | **389 × 389 × 458 mm** |
| Physical | Net weight | **12.95 kg** |
| Electrical | Input voltage | 100–240 VAC, 50/60 Hz |
| Electrical | Max power | **1000 W @220 V, 350 W @110 V** |
| Electrical | USB output power | 5 V / 1.5 A |
| Electronics | Display | **2.7-inch, 192 × 64** |
| Electronics | Connectivity | Wi-Fi, Bluetooth, Bambu-Bus |
| Electronics | Storage | microSD card |
| Electronics | Control interface | Button, app, PC application |
| Electronics | Motion controller | Dual-core Cortex-M4 |
| Software | Slicer | Bambu Studio; third-party slicers exporting standard G-code (SuperSlicer, PrusaSlicer, Cura) are supported, with some advanced features unavailable |
| Software | Slicer OS | macOS, Windows |

## Build plates — measured, not described

**Textured PEI plate surface colour: `#cfb074`.** Measured directly off a
1024 px product photograph, averaging the plate interior away from markings
and the white background. The viewer's `PLATES.textured.hex` was already
`#cca96b`, which is within a few levels of that — it was right.

**Surface grain is fine and uniform, with no large-scale structure.** On the
same photograph (1010 px spanning the 256 mm plate, so 3.95 px/mm) the
speckle measures **sd 5.09 on a mean of 177.7 — about 2.9% luminance
modulation**. The individual grain is below what a 4 px/mm photograph
resolves, which is itself the useful finding: at any normal viewing distance
a real textured plate reads as a fine sheen, never as visible blobs.

Bambu's own "print surface sample" photograph — the underside of a part
pulled off a textured plate, i.e. the negative impression of the plate — shows
the same thing: a dense, even stipple with no repeating pattern.

Plate markings, for anyone rebuilding the texture: product name set
vertically up the left edge, Bambu logo outline centred, a filament-
compatibility bar along the bottom (`PLA/ABS/PETG` on the textured plate), a
heated-surface warning triangle at the bottom right, and locating notches at
top centre and bottom.

## How this bears on the viewer

- **Camera at 0.5 fps** is a hardware limit, not a relay shortcoming. The
  camera relay in `tools/relay/bambu_p1s_bridge.py` cannot do better than
  two seconds per frame no matter how it is written, and the viewer should
  not imply live video.
- **32 mm³/s max flow** is the real ceiling on how fast a bead can be laid,
  and is the honest basis for any future "is this plate's speed achievable"
  check. At a 0.42 mm wide, 0.2 mm tall bead that is about 380 mm/s of
  linear travel before the hot end, not the motion system, becomes the limit.
- **20 m/s² acceleration and 500 mm/s top speed** are toolhead maxima, not
  print speeds. Bambu's own production profiles run outer walls far slower.
- **Included plate is the dual-sided textured PEI**, so the viewer's default
  plate choice matches what a P1S actually ships with.

## Corrections to this repo's own CLAUDE.md

CLAUDE.md's "3D Printer — Bambu Lab P1S" section predates this check and has
four errors, all of them the kind that sound plausible:

1. **"Stock brass 0.4mm nozzle."** The P1S ships a **stainless steel**
   nozzle. This matters for the filament advice built on it.
2. **"2.8" monochrome LCD touchscreen."** It is a **2.7-inch 192 × 64**
   display, and the P1S is driven by a button and the app — it is not a
   touchscreen. (The X1 series has the touchscreen; the P1S does not.)
3. **"PETG-CF / PLA-CF / PA-CF — requires hardened steel nozzle."** Bambu
   lists carbon- and glass-fibre reinforced polymers as **not recommended**
   for the P1S at all. A hardened nozzle is necessary but not sufficient;
   the machine is not specified for them.
4. **"Built-in camera — remote monitoring."** True, but the useful number is
   missing: it is **1280 × 720 at 0.5 fps**, explicitly a low-rate camera.

Two things CLAUDE.md had right and are confirmed here: the 256 mm cube build
volume, and 20,000 mm/s² acceleration (Bambu states it as 20 m/s²).

---

# How the P1S lays a layer

Added 2026-09-19. Everything here is a **profile default from Bambu Studio for
a 0.4 mm nozzle**, not a per-move value read back from G-code. That
distinction matters: the G-code carries the truth, the profile carries the
intent, and anything built on the numbers below should say which it is using.

## Line width is not one number

| Where | Width |
|---|---|
| Default line width | **0.42 mm** |
| Initial (first) layer | **0.50–0.60 mm** |
| Outer wall | 0.40 mm |
| Inner wall | 0.45 mm |

A 0.4 mm nozzle lays a **0.42 mm** bead by default, not 0.40 — the extrusion
spreads as it is pressed into the layer below. The first layer is laid wider
still and squashed harder, which is what makes it grip the plate; it is also
the layer anyone looking at the bed is looking at, so drawing it at the same
width as everything else is visibly wrong.

## Layer height

0.2 mm is the standard production layer for a 0.4 nozzle and the sensible
default for a first print in almost any material. 0.08–0.12 mm is the fine
range for visible detail; 0.28 mm is the practical ceiling for that nozzle.
First layer height is 0.2 mm by default.

## Speed, and why the headline numbers are not print speeds

**500 mm/s toolhead speed and 20 m/s² acceleration are machine maxima**, not
what a part prints at. Real defaults are far slower where surface quality is
decided:

- Outer wall around **60 mm/s** in Bambu Studio's own conservative default;
  the aggressive X1C 0.20 Standard preset asks for 200 mm/s outer / 300 mm/s
  inner before filament limits clamp it.
- First layer **15–45 mm/s** depending on plate adhesion, and staying near
  50 mm/s regardless of the rest of the profile is the usual advice —
  adhesion matters more than time on layer one.

The hard ceiling underneath all of it is the hot end: **32 mm³/s**. For a
0.42 × 0.2 mm bead that is roughly 380 mm/s of linear travel before melt
rate, not the motion system, becomes the limit.

## What this changed in the viewer

`buildJob` drew every extrusion on every plate at one width. It now scales
that width by feature — inner wall 0.45/0.42, and the whole first layer
0.50/0.42 — from the table above. The flat-top fraction of the bead is
derived from the layer's own widest bead rather than the global constant, so
a wider first layer gets the flatter top a squashed bead actually has.

This is an approximation from profile defaults and is labelled as such in the
code. The real fix is per-move widths in the payload, which means re-exporting
all 72 plates through `gcode_viewer_data.py` — worth doing, not worth
bundling into a change that also touched geometry.

# The machine, checked against photographs

Measured off Bambu's own P1S product photography, 1024 px, 2026-09-19.

**The body is neutral.** Sampled across the shell: right side panel
`(27,27,27)`, lower panel `(13,13,13)`, top bezel `(83,83,83)`, base plinth
`(31,31,31)`, front face mean `(38,38,38)`. Every one is **exactly R=G=B**.
The viewer's machine palette was uniformly blue-shifted — `0x1b1e24` is
(27,30,36), `0x191d25` is (25,29,37) — and rendered at (21,24,35) against the
real (38,38,38). Fifteen body colours were remapped to their own luminance
grey, keeping one level of cool so the machine does not read as flat charcoal
in a dark UI.

**The control panel is at the top, on the left.** It sits in the bezel *above*
the glass door, with the "Bambu Lab / P1S" wordmark to its right. The viewer
had it at `zBot + 28` — the middle of the bezel *below* the door, near the
feet, and on the right. The round control beside the screen is a **D-pad**,
not a knob; the P1S has no touchscreen.

Other details visible in the reference and worth having: a pill-shaped "Bambu
Lab" door handle on the right edge of the glass, the Bambu logo and wordmark
on the right side panel, a white label strip along the bed's front edge
reading `WARNING HOT SURFACE | BUILD VOLUME 256 × 256 × 256mm`, and an LED
light bar high on the inside left wall.

**Not yet done, and named so it is not lost:** the door handle, the side-panel
branding and the front wordmark are all still missing from the model.
