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
