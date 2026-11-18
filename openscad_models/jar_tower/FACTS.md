# FACTS: Stacking Jar Tower, v1

Every number comes from this folder. The source is on each line (STANDARDS 15).

## Version
- **v1**, 2026-11-13. Scott's pick 1A: jars that screw into one another to make one column.
- **Built at the clearance Scott chose from the thread test.** The test was MakerWorld
  3597781 (private), and he picked mouth 1, the 0.2 mm one: "Number 1 again is the best."
  (`ENGINEERING.md` section 6.)
- **The full tower is not printed yet.** Every image is a design-review render, not a photo.

## What it is
- **Four jars** that screw one on top of the next, plus a cap and a foot.
- **Each joint:** the jar's bottom is a threaded spigot that screws into the mouth of the
  jar below. A 35° cone above the thread seats the seam and closes it.
- **Fewer jars works the same way.**

## Numbers
| what | value | source |
|---|---|---|
| Jar | 72 mm across, 64 mm tall, about 153 ml inside | `ENGINEERING.md` §7; `stacking_jar_tower_jar.3mf` |
| Cap | 72 mm across, 18 mm tall, 24 grip grooves | `stacking_jar_tower_cap.3mf` |
| Foot | 82 mm across (a skirt 5 mm past the jars), 15 mm tall | `stacking_jar_tower_foot.3mf` |
| Full tower, foot + 4 jars + cap | 247.7 mm tall | `ENGINEERING.md` §7 |
| Thread | 4 mm pitch, 1.2 mm deep, 0.2 mm radial clearance | `ENGINEERING.md` §2, §6 |
| Hold | lifting the full tower by its top jar is 7.7 N on one thread; the hand calculation puts stripping at about 13.2 kN | `ENGINEERING.md` §3 |
| Seal | spice-tight, not airtight: there's no gasket | `ENGINEERING.md` §1 |

## Print time and filament
Bambu Studio's own slice at Scott's settings: wall loops 3 and sparse infill 15% ("3 walls
and 15% infill is how our prints are set in the slicer", Scott, 2026-11-12). P1S 0.4,
PLA Basic, 0.20 mm Standard, textured PEI, no supports. Re-sliced 2026-11-18. The files
open in Bambu Handy.

| print | how many | time each | filament each | file |
|---|---|---|---|---|
| Jar | 4 | 1 h 31 m | 47.2 g | `checks/tower_jar.gcode.3mf` |
| Cap | 1 | 46 m | 20.2 g | `checks/tower_cap.gcode.3mf` |
| Foot | 1 | 46 m | 21.8 g | `checks/tower_foot.gcode.3mf` |
| **Full tower** | 6 prints | **about 7 h 36 m** | **about 231 g** | the sum of the above |

- **Superseded:** 7 h 54 m and 204 g. Those were sliced 2026-11-13 at 2 walls, before the
  Handy fix.

## Checks (`checks/`)
- **Fit (`fit_tower.txt`): PASS** at jar on jar, jar on foot and cap on jar.
  - Seated home.
  - Held when pulled 1 mm.
  - At least 0.15 mm open at the teeth.
  - Unscrews 90° to 720° touching nothing.
- **Product gate: PASS on all three parts.** The thread is declared as detail.
- **Print fidelity:** 0 dropped, 0 filled.
- **Fragility:** 0 slender runs.
- These checks were run on the meshes, at 2 walls. The 3-wall re-slice changes only how the
  inside is filled, not the outside or the fit.

## Free or paid, per platform
- **Not decided, not uploaded.** Only the thread test is on MakerWorld (3597781, private).
  Scott's call.

## Safe to say, word for word
- "Four jars that screw together into one tower, plus a cap and a foot."
- "Each jar is 72 mm across and holds about 150 ml."
- "About 25 cm tall with all four jars."
- "No supports. Each part prints standing up."
- "The thread was test-printed first, and this is the clearance that won."

## Don't say
- That the full tower is printed or tested. Only the thread test is.
- Airtight, food-safe or waterproof. It has no gasket, and nothing has been tested with food.
- A print time without its settings: about 7 h 36 m is at 3 walls and 15% infill.

## Media
| file | shows | version |
|---|---|---|
| `guide/images/tower_full.png` | the assembled tower, design-review render | v1 |
| `guide/images/tower_parts.png` | jar, cap and foot, render | v1 |
| `guide/images/tower_screw.png` | a jar screwing onto the next, render | v1 |
| `guide/images/tower_section.png` | a cut through the joint, render | v1 |
| `guide/Stacking_Jar_Tower_Guide.pdf` | assembly guide | v1 |

## Light fit
- Not a light piece.
