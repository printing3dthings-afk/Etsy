# Pie Drum Caddy, FACTS (2026-11-15)

Scott's pick 4B: a round desk caddy in six rising slices that turns on a ring of BBs.

- **Bearing: proven.** Scott ran the bearing test on printed balls (2026-11-15): "the test
  works". The product uses real 6 mm airsoft BBs.
- **The caddy itself: not printed yet.**

## What it is
- **Drum:** 150 mm across. Six wedge wells, 45 to 115 mm tall, round a centre well 122 tall.
  The outer wall is fluted like a pie dish (48 scallops). It holds up to 1 kg.
- **Base:** 120 mm across. A post in the middle; a channel for 46 airsoft BBs (6 mm, about
  $3 a thousand).
- **Turning:** the drum turns on the BBs. Nothing locks it on, so it lifts straight off for
  cleaning.

## Print files
| file | time | filament | notes |
|---|---|---|---|
| `pie_caddy_drum.gcode.3mf` | 8 h 42 min | 206 g | prints on its smooth underside, the face the BBs run on |
| `pie_caddy_base.gcode.3mf` | 1 h 36 min | 36 g | irons its channel floor |

- PLA Matte, 0.2 mm layers, no supports. Bambu Studio's own slices.
- The colours in the renders and viewer (pie-crust drum, chocolate base) are only a
  suggestion.

## Checks
- **Product gate:** pass on both parts.
- **print_fidelity:** 0 flags.
- **Fragility:** nothing slender.
- **Fit check (`checks/fit_caddy.txt`):** PASS. Clearances are the tested bearing's, and the
  drum can't tip off the balls even with 1 kg in one well.
- Details: ENGINEERING.md section 9.

## Guide and images
- `Pie_Drum_Caddy_Guide.pdf`.
- `images/caddy_*.png`: design-review renders, not photos.

Not for children under 3: small parts (the BBs).

---

# v2: the keeper (2026-11-26)

Benson's brief and Scott (Nov 22): "Can it be designed to latch in somehow. So when it's moved it
stays in one piece." Notes: `ENGINEERING_v2.md`. v1 above and MakerWorld 3621416 are unchanged.

- **The keeper thread: proven.** Scott printed the keeper coupon at 0.2 clearance (2026-11-26):
  "Test piece was great for the drum caddy." Footage: `real/keeper_coupon_timelapse_2026-11-26.mp4`.
- **The full v2 caddy: not printed yet.**

## What changed from v1
- **Base:** the centre post grows up through the drum and is threaded at the top (4 mm pitch,
  1.2 mm deep, the jar tower's tested profile).
- **Drum:** the same fluted 150 mm drum, with a ledge inside the centre well.
- **Keeper cup (new):** a pen cup that fills the centre well, with a ridged collar on top. It
  screws onto the post clockwise, about three turns, and stops cone-on-cone, 0.5 mm above the
  drum's ledge. So the drum still spins, but it can't lift off: picked up by the collar or the
  drum, the caddy comes up in one piece. "Nothing locks it on" no longer applies to v2.
- **Cleaning:** unscrew the keeper, then lift the drum off.

## Print files
| file | time | filament | notes |
|---|---|---|---|
| `pie_caddy_v2_drum.gcode.3mf` | 8 h 41 min | 211 g | on its smooth underside, as v1 |
| `pie_caddy_v2_base.gcode.3mf` | 1 h 47 min | 40.2 g | irons its channel floor |
| `pie_caddy_v2_keeper.gcode.3mf` | 56 min | 23.2 g | standing up, 3 mm brim |

PLA Matte, 0.2 mm layers, no supports. Bambu Studio's own slices: design checks, not Benson's
shipping profiles.

## Checks
- **Product gate:** pass on base, drum and keeper, 0 support moves (`checks_v2/gate_*.txt`).
- **Fragility:** 0 (`checks_v2/fragility_caddy.txt`).
- **Fit (manifold3d):** the drum lifts 0.45 clear and is caught at 0.5; trapped, never clamped.
- **Load:** 40 N design load (1.36 kg x 3 g). The thread strips at about 1.4 kN.
- **print_fidelity:** 0 flags on base, drum and keeper; nothing dropped or filled (`checks_v2/fidelity_*.txt`).

## Guide and images
- `Pie_Drum_Caddy_v2_Guide.pdf`.
- `images/caddy_v2_*.png`: design-review renders, not photos.

Not for children under 3: small parts (the BBs).
