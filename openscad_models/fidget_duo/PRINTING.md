# OnBrandCraftz — Pebble Gecko & Mushroom Pop

First physical-prototype package. These are actual modeled parts, not generated concept meshes. Recessed OBC branding is on the gecko's underside and mushroom base rim. Finish colors shown in PNG renders include optional paint fill in the recessed eyes and mushroom spots. The USDZ previews show unpainted component colors. The gray switch in the mushroom preview is a simplified purchased-hardware reference, not a printable component.

## Start with the three small test pieces

1. Print `gecko_coupon.stl` or `.3mf` flat with supports OFF. Let it cool; gently free the joint. Verify that it moves without cracking or separating. If it fuses, do not print the full gecko yet: tune extrusion/first-layer expansion or increase the source `gap` and regenerate all parts. Never scale a finished mesh to adjust clearance.
2. Print `switch_coupon` at **0.15 mm layers and 0.15 mm first layer** so its 1.5 mm plate is reproduced exactly. Check the 14.1 mm opening with the actual full-height, plate-mount MX-style clicky switch you plan to use.
3. Print `stem_coupon` and check the cross socket on that same switch. Do not force a tight socket onto the stem. The prototype uses a 4.15 × 1.35 mm cross opening and 4.9 mm blind depth; this is a starting fit, not universal switch compatibility.

## Pebble Gecko — F1

Print `gecko` as ONE multipart object in its supplied straight pose. It contains seven separate, captured moving solids and six joints. Do not separate, auto-arrange, merge/union or glue the moving components. Do not print the curved USDZ pose. Start with PLA, 0.4 mm nozzle, 0.20 mm layers, three walls, five top/bottom layers and 15% gyroid. Keep **supports OFF**, especially inside the joints. All solids have bed contact in the supplied orientation.

The 0.5 mm nominal radial joint gap and 10° sideways articulation per joint passed mesh-intersection checks. Collisions begin between 10° and 15° in the sampled geometry; do not force beyond the mechanical stops. Straight pull tests encounter the retaining shell after the designed free play; this is geometric capture, not a pull-strength test. Vertical movement and abuse resistance are not validated. The preview uses 6° per joint.

Automatic support generation was tested and would insert support into the mechanism. The delivered support-off diagnostic slice preserves the geometry but does **not** prove the internal bridges or gaps will print cleanly. A successful physical joint coupon and complete sample are required before batch printing.

## Mushroom Pop — C1

Print ONE `mushroom_base` and ONE `mushroom_cap`. The base is already inverted with its switch plate on the bed and the open cavity facing upward; **do not flip it again**. Supports OFF for the base. The cap has its annular rim and central stem boss on the bed; supports ON inside its open underside recess. Carefully remove those supports without enlarging the cross socket. Check bridges and socket surfaces in your own slicer.

Use the same starting PLA profile as above. The 3MF files are geometry containers, not Bambu printer presets or AMS assignments. Use your printer's own filament temperatures, cooling and start/end code. No diagnostic G-code is included for printing.

Hardware: one purchased full-height, plate-mount, MX-style **clicky** mechanical keyswitch. No electronics, soldering or magnets. The design uses the legacy Cherry MX drawing as its nominal envelope: https://cdn.sparkfun.com/datasheets/Components/Switches/MX%20Series.pdf . Match the exact switch to the coupons before buying production quantities. Low-profile, optical and other stem formats are not supported by this prototype.

Clip the switch into the stem base from above; its pins hang safely in the open underside cavity. Press the cap onto the switch stem only after the coupon fits. The cap's underside recess clears the printed base through a modeled 4 mm stroke. The switch stem-boss clearance, actual actuation, off-center rocking, return force and cap retention still require hands-on testing with your switch. Do not glue the cap to the stationary base. The switch clips remain accessible from beneath for removal.

## What was checked — and what was not

See Geometry_Report.json, Movement_Report.json, Slice_Report.json and Structural_Checks.txt. Slicing uses PrusaSlicer 2.7.2 with a generic 256 mm bed profile; results are not Bambu-certified time or material estimates. Mesh checks establish watertight shells and consistent winding. The full gecko also passed Blender nonmanifold and self-intersection checks. Reports include advisory thin/degenerate-face counts; a pass is not a guarantee of finish or strength.

Neither item has been physically printed or tested here. Do not list these as proven, durable or child-safe products based on the digital checks. Before selling, inspect joint retention, broken-part hazards, coating adhesion, cap retention, repeated clicking, and your intended customer age/use. Record your real print time, material consumption, assembly effort and test results before pricing. These are prototypes awaiting physical qualification.

## Editable source and reproduction

Keep `Fidget_Duo.scad` and `OBC.svg` together. OpenSCAD's `part` selector exports the main models and coupons. `build.py` exports the gecko as individual solids before concatenating them, avoiding a slow final Boolean union. Moving solids must remain distinct. It also rebuilds the clicker and coupon parts. `preview.py` creates geometry-only 3MFs and actual-model phone views. `render.py` uses Blender 4.4 Python. `checks.py` uses trimesh/manifold and the repo's virtual-printer tool, with `FIDGET_SLICER_DIR` optionally pointing to your PrusaSlicer folder. Required packages: trimesh, numpy, scipy, shapely, rtree, manifold3d and usd-core; Blender Python needs bpy.
