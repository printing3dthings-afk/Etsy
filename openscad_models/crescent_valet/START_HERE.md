# Crescent Valet — OnBrandCraftz

Original product prototype, September 15, 2026. This is an engineered, digitally checked design, not a physically validated retail release.

## Branding revision — September 15, 2026

Both the base and removable tray now have the approved OBC maker's mark engraved into their hidden undersides, 0.7 mm deep. The base mark is 28 mm wide; the tray mark is 24 mm wide. Keep the included `OBC.svg` beside the SCAD when editing. This is the print-ready Montserrat Black mark from the repository, not a substituted font or raised label. Nominal minimum strokes at those sizes exceed the repository's 0.84 mm requirement. Inspect the underside in the actual viewer and on the first print for legibility and orientation.

`Brand_Validation.json` contains fresh checks on these branded meshes. The two main parts were re-sliced: zero support moves and zero overhang perimeters at 0.20 mm. Mesh and Blender hard checks pass for both. Engraving adds thin-face advisory reports (64 base, 102 tray); these are reported, not hidden. The revised through-material first-percentile spans are 4.80 mm base and 2.17 mm tray. The detailed pre-branding measurements below describe the earlier prototype only; use the branding report for the current mesh checks.

## Open the model

- `Crescent_Valet_View.usdz`: assembled model for iPhone/iPad Quick Look. Save to Files and tap; display support depends on the app opening it.
- `Crescent_Assembly.3mf`: assembled geometry for review. The tray is positioned in its recess. Do not print this arrangement as one fused object.
- `Crescent_Base.3mf` and `Crescent_Tray.3mf`: individual print parts, each resting on z=0. These contain geometry, not a Bambu printer or filament preset.
- Binary STLs are provided as an alternative.
- `Crescent_Valet.scad`: editable parametric source; no external libraries. Select `base`, `tray`, `assembly`, or `fit_test`.

## Design decisions

The crescent tray wraps around the phone cradle, preserving the selected concept's silhouette. A 2.4 mm locating recess holds the removable tray without magnets or snaps. Its 0.45 mm clearance per side allows a lift-out fit. The two parts can be printed in different colors with no AMS changes or purge tower.

The phone support leans back 15 degrees. The raised cradle provides connector space; its center opening is 14 mm wide. An 8 mm-wide underside cord groove has a steep roof so it can be sliced without support material. Connect the cable manually, then rest the phone on the cradle. This is a cord organizer, not an electronic charger or a fixed charging-plug dock.

The design targets ordinary phones in cases up to about 14 mm thick, without bulky grips on the back. A nominal 85 × 14 × 165 mm phone envelope was checked for solid interference, but actual cases, connector housings, and camera bumps need a physical fit check. The cord route is intended for a flexible cord around 4 mm diameter or less, not a large plug passing through a closed tunnel.

## Dimensions

| Feature | Nominal size |
|---|---:|
| Overall assembled footprint | 210 × 154 mm |
| Overall height | 100 mm |
| Removable tray | 121 × 133 × 18 mm |
| Tray wall / floor | 2.8 / 3.0 mm |
| Phone support width | 74 mm |
| Phone seat height | 28 mm |
| Tray clearance per side | 0.45 mm |

## First print

1. Print `Crescent_Fit_Test.stl` first. It contains a small receptacle and separate insert using the tray clearance. The insert should drop in and lift out without force. This coupon checks fit tolerance only, not the phone or cord.
2. Import `Crescent_Base.3mf` into Bambu Studio and select your P1S, 0.4 mm nozzle, textured PEI plate, and a filament profile you have already calibrated. Keep the broad flat underside on the plate.
3. Start with 0.20 mm layers, 3 walls, 5 top and 5 bottom layers, and 15% gyroid infill. Supports off. Use the same tested settings for the tray, on a separate plate.
4. Print the base in slate and the tray in tan. Matte PLA is the intended indoor prototype material. Use your filament's established temperatures and cooling settings. Keep the seam toward the rear where practical.
5. Let the parts cool fully before removing them. Drop the tray into the recess, route the cord underneath, connect the phone, and check that the stand remains flat and stable. Optional adhesive silicone feet can improve desk grip.

The physical surface will have normal FDM layer lines. The preview is a smooth CAD render, not a photograph or layer-by-layer print simulation. Large shallow top curves may show visible stepping; evaluate the actual sample before selecting a finer production layer height or ironing.

## Checks performed

- Both main meshes are watertight, consistently oriented, positive-volume single bodies with no degenerate triangles according to the mesh gate.
- Blender's 3D Print Toolbox found zero non-manifold edges, bad contiguous edges, and intersecting faces for both parts.
- The tray has no thin-face or zero-face advisory warnings. The base has 11 thin-face and 2 near-zero-face advisory reports around small transitions; the independent through-material thickness check reports a 5.74 mm first-percentile span and no material below a 0.42 mm bead. These advisory reports are not concealed or treated as physical print measurements.
- Both parts passed the repository product gate: bed fit, wall sampling, body count, footprint, and center of mass over the base.
- PrusaSlicer 2.7.2, 256 mm build envelope, 0.4 mm nozzle, 0.20 mm layers: **zero support moves and zero overhang perimeters** for both parts. Both survive slicing to full height (100 mm base, 18 mm tray).
- Solid intersections between the assembled tray and base, and between a nominal phone envelope and base, show contact only, not an overlapping solid volume.

PrusaSlicer is not Bambu Studio. These checks assess geometry, not thermal behavior, surface finish, bed adhesion, stringing, or physical load performance. No machine G-code is included. Slice the files yourself with your chosen P1S profiles.

The branded revision's diagnostic slicer extrusion-volume totals are 135.67 cm³ for the base and 43.39 cm³ for the tray. At an assumed PLA density of 1.24 g/cm³, that is about 222 g combined, before real-world waste. This is a planning estimate, not a measured finished weight. No P1S print-time claim is made.

## Before selling

Print a full sample with the filament and profile you intend to use for production. Check tray removal, case and cable compatibility, scratches at contact points, desk grip, stability with the phone installed, and repeatability on a second print. Inspect the rim, front lip, cable opening, and rear seam closely. Use the measured filament, actual machine time, packaging, fees, and labor to set your cost and price. Market acceptance and sales are not established by a CAD check.

## How the design was improved

The first base triggered support material beneath the cradle and where the tray recess overlapped the stand. Narrowing and relocating the retaining lip, reshaping the tray's rear tip, and moving the phone cradle clear of it removed those features. Steepening the underside cord-groove roof removed the remaining supports. The final form was re-exported, rechecked, and re-sliced after those changes.
