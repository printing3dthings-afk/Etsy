# Things only a printer can make: techniques, proven and not (started 2026-11-14)

Scott, 2026-11-14: "We need to get much much better at small details and out of the box
thinking. Remember 3d printing can produce things regular design can't... It needs to look
and function flawlessly."

This file is a ledger of techniques: what each one does, how sure we are, and what tests
it next. The status words mean exactly this:
- **PROVEN HERE:** measured on our own pipeline, in Bambu Studio 2.8.2, the slicer Scott
  prints from.
- **PROVEN BY SCOTT:** printed and reported.
- **RESEARCHED:** sourced, but not tested here yet.
- **IDEA:** reasoned from the above, with no test and no market check yet.

Anything a listing or a post says about a technique needs PROVEN BY SCOTT.

## Tools added for this (so every later design can use them)
- **`tools/bambu_gcode.py`:** turns Bambu Studio G-code into the tagged form our readers
  use.
  - Before it, a Bambu slice read as ONE layer, and its curves were skipped: they're G2/G3
    arcs, 3,635 of them on one coupon.
  - Now `print_fidelity`, `as_printed` and the viewer can show exactly what Bambu Studio
    will print, including fuzzy skin and vase mode, not PrusaSlicer's guess.
  - Checked: 45 of 45 layers, and filament conserved to the mm (4,200 = 4,200).
  - Test: `tests/test_bambu_gcode.py`.
- **`tools/bambu_slice.py --set key=value`:** any Bambu process setting, by its own name.
- **`tools/bambu_slice.py --object-set N:key=value`:** a setting for one object only. That
  means one texture per swatch, or one material setting per part.

## 1. Fuzzy skin noise as texture: stone, wood, stucco. PROVEN HERE
- Bambu Studio 2.8 has five noise types: `classic`, `perlin`, `billow`, `ridgedmulti` and
  `voronoi`.
  - Settings: `fuzzy_skin=external`, `fuzzy_skin_noise_type`, `fuzzy_skin_thickness`,
    `fuzzy_skin_point_distance`, `fuzzy_skin_scale`, plus octaves and persistence.
  - The GUI can also paint it onto chosen faces (2.2+).
- **Measured on a 30 mm cylinder** (thickness 0.4, point distance 0.6, scale 3), outer wall
  radius at layer 50:

  | noise | look (as-printed render from Bambu's own toolpath) | radius spread | print time |
  |---|---|---|---|
  | classic | random roughness: stucco, sand | ±0.50 mm | 13 m 47 s |
  | perlin | soft horizontal grain: wood, bark | ±0.23 | 12 m 54 s |
  | voronoi | cells with stepped edges: cobblestone, flagstone, dry-stone wall | ±1.17 | 20 m 27 s |

  Plain, the time was close to classic's.
- **Bonding:** the outer bead sits a median 0.29–0.38 mm from the wall behind it, and at
  most 0.81 mm away, the same in all three types. Voronoi is no weaker than the classic
  fuzzy skin people print every day.
  - For a wall that carries load, keep thickness ≤ 0.3.
  - Voronoi costs about 50 % more time on a wall.
- **Per object:** `--object-set` gives each object its own noise. On the sampler, plain,
  classic, Perlin and Voronoi read 0.10 / 0.36 / 0.22 / 1.04 mm spread.
- **Why it matters:**
  - Stone and wood walls on village buildings with no modelled stones. Modelled weathering
    read as cheese (Technique 63); this is real texture, from the toolpath.
  - Bark on trees.
  - A grip that is the decoration.
- **Limits:**
  - Side walls only; tops and bottoms stay smooth.
  - It changes the outline by up to the thickness, so keep it off mating faces (a modifier
    or painting does that).
- **Next:** Scott feels the sampler (`openscad_models/technique_samplers/`).

## 2. Vase mode with slits: ribs inside one continuous wall. PROVEN HERE
- **Source:** Arvid Norlander, "3D printing with unconventional vase mode", 2025-06-23,
  vorpal.se. The idea came from RC plane wings.
- **The idea:**
  - Vase mode prints only the outline. A slit 0.0001–0.001 mm wide cut into the solid is
    part of the outline.
  - So the single wall runs into the slit and back out, two beads touching: a rib.
  - "You are basically modelling the infill yourself."
- **Bambu Studio needs `slice_closing_radius=0`** (default 0.049, which closes the slit),
  plus `spiral_mode=1`.
- **Measured** on a 40 mm × 30 mm cylinder with six 0.001 mm slits from the rim to r 4,
  `outer_wall_line_width=0.6`:
  - one continuous wall of **316 mm per layer**, against 124 mm without slits (predicted
    318 / 126);
  - the layer plot shows six double-wall spokes;
  - **19 m 41 s and 7.7 g**, against 12 m 19 s and 3.8 g.
- **What it buys:**
  - The speed and seamlessness of vase mode, with internal ribs where you want them.
  - A rim-heavy wheel, or a lampshade with light-catching ribs, printed as one wall.
- **Limits:**
  - No overhang shallower than vase mode can climb; no supports.
  - One outline per layer.
  - A slit open to the outside leaves a fine line you can feel.
  - Wall thickness is the line width (up to about 2× the nozzle).
- **Next:** Scott squeezes the printed rib cylinder against the plain one.

## 3. Two materials that don't stick: zero-gap moving parts. RESEARCHED
- **The physics:** PLA and PETG bond poorly. That's why Bambu sells them as a support pair,
  and why one calibration model prints PLA straight on PETG with zero gap.
- **The idea:** a hinge or bearing whose two halves are different materials can print
  touching, with **no clearance**.
  - Every print-in-place joint we make needs 0.3–0.45 mm today (Techniques 40, 57). That
    gap is the wobble.
  - Zero gap would make it a precision joint.
- **What nobody has published:** a controlled test of moving joints this way. The forum
  advice is still "leave 0.3–0.4 so it doesn't fuse" (Bambu forum and MakerWorld
  "Multi-Material Interface Calibration & Test Tool", 464717).
- **Risks:**
  - PETG strings.
  - A two-material print purges filament at every change.
  - The bed temperature has to suit both: PEI, about 65 °C.
- **Coupon built (2026-11-14):** `openscad_models/zero_gap_joint/`.
  - Scott has **Bambu Support For PLA**, so the second material is that, not PETG. It is
    made not to bond to PLA layer on layer.
  - Three turntables: a 0.30 air gap (the control), a one-bead sleeve of support material
    with no air, and the sleeve plus 0.10 air.
  - 1 h 1 min. The fit, gate, fidelity (both materials) and fragility checks all pass.
- **The open question only a print answers:** does it stay unbonded side by side, in the
  same layer?

## 4. Interlocking beams between materials. RESEARCHED
- Bambu Studio 2.8 has `interlocking_beam` (width, depth, layer count, orientation):
  printed dovetails across a boundary between two materials.
- This is the opposite of section 3: it locks materials that don't bond. Examples:
  - a soft TPU grip locked into PLA;
  - a PETG living hinge locked into PLA leaves.
- **Limit:** the P1S's AMS can't feed TPU, so TPU means a manual swap. PETG with PLA works
  through the AMS.
- **Next:** test whether a PETG flexure locked into PLA by these beams survives 100 flexes,
  where a PLA one cracks.

## 5. Pause and embed: magnets, steel, coins, nuts, LEDs. RESEARCHED (we already use pauses)
- `tools/bambu_slice.py --pause-at Z` already inserts pauses.
- **Rules from the Bambu forum and MakerWorld guides:**
  - pause on the layer before the pocket closes;
  - add about one layer of extra depth for ceiling sag;
  - press the part fully home so the nozzle clears it;
  - the P1S's enclosure leaves little room to reach in.
- **What it opens up:**
  - mass where plastic can't put it (a steel washer in a top's rim);
  - sealed magnets, so nothing can be swallowed loose;
  - sound (sealed BBs);
  - weight in a base.
- **Next:** a pocket-depth coupon for the magnets and washers Scott has.

## 6. Snap-through (bistable) flexures. RESEARCHED
- **Sources:**
  - Curved-beam bistability (MSAM 3-4; pre-curved first-buckling-mode beams);
  - FDM-printed PLA snapping "metabeams" with a spiral geometry that allows "large
    reversible deformation even when made from a relatively stiff material such as PLA"
    (arXiv 2602.18330, 2026).
- **What it opens up:** clicks and toggles with no spring and no switch, which is the
  clicker category. A box that stays open or shut by itself.
- **The catch:** "unpredictable mechanical characteristics" of FDM polymer (the
  LIRMM papers), so it is coupon-first, in the print plane, like the Pocket Top beams.

## 7. Detail: what we already know, and where it's written
`openscad_models/detail_calibration/DETAIL_STANDARD.md` (measured floor sizes),
`FINE_DETAIL_RESEARCH.md` (0.4 vs 0.2 nozzle), skill Techniques 52–54, 76, 81–82. Fuzzy
skin (section 1) adds texture that doesn't fight the detail floor, because it lives in the
toolpath, not the mesh.

## Gaps found in our own checks while doing this
- **Sealed voids:** no gate looks for them.
  - The zero-gap rotor had a cavity that touched its axis along a zero-width line, so the
    mesh stayed one watertight shell, and every gate passed it.
  - The cut-away render caught it.
  - Until a check exists, cut any turned part through its axis and look.
- **The as-printed renderer and Bambu top surfaces:** Bambu's top lines render with dark
  gaps between them, though the toolpath is solid (lines 0.377 apart, about 0.37 wide).
  - Its ironing pass, filed as "Other" before the mapping, drew tops black.
  - For now, show Bambu-sliced pieces from a low camera angle.

## Product ideas that follow (IDEA: none of these is market-checked yet)
1. **A vase-mode spinning top or spinner:**
   - a rim and spokes in one continuous wall, so the mass sits at the rim, where spin time
     comes from;
   - minutes to print, against the Pocket Top's 10-minute budget.
   - Goes to Scott as one of the Pocket Top's form approaches.
2. **Textured village pieces for the post-Dec 25 reworks:** Voronoi stone foundations,
   Perlin timber, painted per face. That's realism the 0.4 nozzle can't model.
3. **Ribbed vase-mode lampshades:** the ribs cast lines when lit. Fast, light, seamless.
4. **Zero-wobble print-in-place:** two-material hinges and bearings (section 3), if the
   coupon works. Nobody publishes that today.
5. **Sealed-magnet pieces:** fridge or village magnets with nothing loose to swallow
   (section 5).
