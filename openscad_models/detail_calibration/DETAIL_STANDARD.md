# Fine detail on a 0.4 mm nozzle: the standard (2026-10-24)

Scott (2026-10-23): "get significantly better at 3d print design ... we are going
to start getting into detail prints." All four kinds: finer village buildings,
figurines and miniatures, tabletop terrain, small decorative items. Stock
0.4 mm nozzle only. Sold both ways: as files and as prints made here.

The pilot that used this standard is the Victorian Santa's Workshop v2
(`../christmas_village/victorian/santas_workshop/v2/`). **Scott approved it on
2026-10-30, so this is now the standard for every new design.** Existing
designs are reworked to it only after Dec 25, top sellers first (CLAUDE.md,
"Detail-print method — APPROVED").

## Where the numbers come from

Published guidance gave almost nothing usable. Searches turned up the 3DJake
guide (0.08–0.12 mm layers and outer walls at about half speed for small text,
no sizes) and Bambu's Arachne description (features under 25% of the nozzle
filtered out). Every number below was **measured here** instead.

`detail_coupon.scad` is a wall with seven rows of features, each row grading
one variable over seven sizes. It was sliced on the gate's own slicer
(PrusaSlicer 2.7, Arachne walls, the P1S 0.4 mm profile) at 0.20, 0.12 and
0.08 mm layers. `measure_coupon.py` then rebuilt each layer's printed area from
the toolpath at every bead's own width, and read the frontmost printed point
through the middle of each feature.

`print_fidelity` could not do this job. It ignores a miss that does not hold
above and below a slicing plane, so a feature thinner than a layer is a tie to
it: the coupon at 0.12 mm layers showed **0 flags**, while the table below
shows heights off by up to half a layer.

These are **toolpath numbers, not plastic**. They say what the printer is told
to lay down. Bead rounding, ooze and a slightly soft corner come on top, and
have not been measured on a real print of the coupon yet. Printing it once
(`detail_coupon.stl`, about 25 cm³, no supports) and photographing it raking-lit is
the next check.

### Measured (logs/measured_*.json)

**Across the face: held exactly at every layer height.**

| feature | sizes tried | printed |
|---|---|---|
| upright groove 0.4 wide, depth | 0.1 – 1.0 | every depth to ±0.01 |
| level ridge 1.0 tall, how far proud | 0.1 – 1.0 | every value to ±0.01 |
| upright rib 0.6 proud, width | 0.2 – 1.0 | all print; 0.2–0.3 wide stand 0.03–0.09 *further* out (one bead's round end) |
| boss (half-dome), diameter | 0.6 – 2.6 | proud 0.27 – 1.29, i.e. the full radius less ≤ 0.03 |

**Up the face: snapped to whole layers.**

| level feature, height | at 0.20 mm layers | at 0.12 | at 0.08 |
|---|---|---|---|
| groove 0.1 | **0.20** | 0.12 | 0.08 |
| groove 0.2 | 0.20 | 0.24 | 0.24 |
| groove 0.3 | **0.40** | 0.36 | 0.32 |
| groove 0.4 | 0.40 | 0.48 | 0.40 |
| groove 0.6 | 0.60 | 0.60 | 0.64 |
| groove 0.8 | 0.80 | 0.84 | 0.80 |
| square ridge 0.3 | **0.20** | 0.36 | 0.32 |
| boss 1.0 across | 5 layers | 8 | 12 |
| boss 2.0 across | 9 layers | 16 | 25 |

A ridge with a 45° chamfer under it reads taller than its face. The chamfer's
upper half stands more than halfway out, so on a 0.6-proud ridge the model's
band is 0.3 taller. Printed, the band came out 0.1–0.2 taller at 0.20 mm
layers and 0.28–0.36 at 0.08. Draw the face that much shorter if its height
matters.

## The rules

1. **Put the finest detail where the toolpath holds it: in lines that run up
   the face.** Joints between slates, planks, flutes, mullions, voussoirs,
   vertical mortar joints. The printer places a wall to the hundredth across the
   face at any layer height. A 0.4 mm upright groove keeps its depth whether it
   is 0.1 or 1.0 deep.

2. **Put every height on the layer grid.** Every level edge of a detail sits at
   a multiple of 0.2 mm (our production layer). Off the grid it prints up to
   half a layer off: at 0.20 mm layers a 0.3 groove became 0.4 and a 0.3 ridge
   became 0.2. For files sold to other printers this is still the right grid.
   Someone printing finer has finer steps, so their error can only be smaller.

3. **Nothing under a layer is lost, it is enlarged.** A 0.1 mm level groove
   prints a full layer, 0.2: twice the size drawn. Draw a hairline level
   detail at exactly one layer, on purpose, or not at all.

4. **A curve that climbs is a stair.** A 1.0 mm dome is 5 layers at 0.20:
   five stacked rings, not a dome. At 0.20 mm layers, give small round
   features facets or chamfers instead, which print as what they are. Keep
   true curves to features ≥ 2 mm tall (9+ layers). Figurines with small round
   forms (faces, hands, buttons) want 0.12 mm (8 layers for a 1 mm dome) or
   0.08.

5. **Size widths from Technique 78 and the coupon.** A rib 0.15 mm wide
   prints, as one bead that breaks like one. Anything handled or standing out
   further than its own width gets ≥ 1.2 mm (3 beads). The workshop's
   brackets and dentils are 1.8 and 1.2. An isolated pin needs ≥ 1.0 mm
   across. A groove ≥ 0.4 mm wide keeps its depth (0.5 is used on the
   workshop for margin).

6. **Make it deep enough to see, which is more than deep enough to print.**
   The toolpath keeps 0.1 mm of relief. Nobody sees 0.1 mm. The shop's
   working depths, all from built and printed models: brick courses 0.6
   proud (Scott called the chapel's brick detail great on the print), joints
   0.4–0.6, frames and sills 0.8–1.2. On a lit building, light reads before
   relief does (Technique 59).

7. **Nothing hangs past 45° from upright, and design to about 37°.** The
   gate's slicer supports at 45. Exactly 45 is not safe: v2's first cornice
   and dentils sat at 45 and the union's slice put 29,332 support moves under
   them, from the plate up. At 36° and 35° the same slice put none. A detail's
   own ceiling counts too, however small. A 0.5 mm plank groove clipped to an
   arch had a 22° top near the crown, and that propped the door with 1,290
   moves. Ending each groove in a 60° point, as the original door's meeting
   line already did, cleared it.

8. **Detail comes in three sizes, and every visible face carries the
   smallest.**
   - *Form*, over 10 mm: the turrets, the hall, the roof.
   - *Feature*, 2–10 mm: openings, cornices, corbel tables, frames.
   - *Texture*, 0.4–2 mm: brick, slate joints, planks, voussoirs.

   Where two forms meet, put a band there: a cornice, a corbel table, a string
   course. Technique 52 found this in the corpus's best-finished prints, and
   our weakest surfaces were exactly the plain flares and bare bands between
   forms.

9. **Check the detail the slicer keeps, not the detail you drew.**
   `print_fidelity` at the production layer height is the gate. A detail
   smaller than a layer needs the bead-level probe (`measure_coupon.py` shows
   the method), because the fidelity tool calls it a tie.

10. **Lettering is 3 mm tall on the 0.4 nozzle; 2 mm only on a face printed
    upward** (added 2026-10-30, measured: `text_test/`, `FINE_DETAIL_RESEARCH.md`).
    Below that the letters blob or lose strokes. A 0.2 mm nozzle reads cleanly
    from 1.5 mm.

11. **Every separate small shape is at least 0.8 mm across** on the 0.4
    nozzle: a dot, a pupil, a berry, a rivet, or a colour island. On a top face
    0.4 and 0.6 mm dots are not shrunk, they are dropped.

12. **The nozzle sets the smallest shape; the layer height sets the smallest
    step.** 0.08 mm layers on the 0.4 nozzle changed nothing for letters or
    dots. Pick the layer height for what climbs (rule 4), and use variable
    layer height to put fine layers only there.

## Working fast enough to iterate

OpenSCAD 2021.01's CGAL engine took 1–3 hours per part on the workshop. A
2026 development build of OpenSCAD with `--backend=manifold` rendered the same
roof part in **46 s**, to the same volume (79,847.7 vs 79,847.9 mm³) and the
same 40 bodies. Its STL carries zero-area slivers at T-junctions that
trimesh/`mesh_gate` read as open edges, so **iterate on manifold, ship CGAL**:
the v2 `build.sh` does manifold by default and `./build.sh cgal` for the
shipped meshes. The development build lives in the session's scratchpad.
It is downloaded from files.openscad.org/snapshots (2026.10.15), not
installed system-wide.
