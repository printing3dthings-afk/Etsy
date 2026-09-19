# Glow Headphone Stand V2 — OnBrandCraftz

Prototype, not physically validated for sale. The original V1 source remains untouched.

## Files

- `glow_headphone_stand_v2.scad`: editable source. Keep `OBC.svg` beside it.
- `glow_headphone_stand_v2/`: printable STL parts, assembled 3MF, preview and validation.
- `Glow_Headphone_Stand_V2_Downlight.3mf`: assembly for viewing, not a print-plate layout. Separate and orient components in your slicer; do not print the assembly fused together.
- `shell.stl`, `diffuser.stl`, `puck_retainer.stl`, `weight_cover.stl`: separate components. The diffuser STL uses its assembly coordinates and needs positioning/orientation for printing. The optional weight cover is not included in the assembly preview.

## Changes

The arm extends 30 mm farther than the first V2 draft and mounts the LED facing down toward the base. The front end is closed. The design targets the Bambu Lab LED Lamp Kit-001; actual puck, cable and retainer fit must be tested. Includes a headband saddle/lip, tray, cable management, foot pockets and an optional weight pocket.

An approved 20 mm-wide OBC vector is engraved 0.7 mm into the base underside at X107, Y-15, away from the foot pockets, weight pocket and cable channel. This replaces the earlier side-text cut. Branding is negative geometry, not a raised label. Nominal minimum stroke is 1.78 mm, above the repository's 0.84 mm minimum. Inspect orientation in the real viewer and on the first physical print.

## Validation and first print

The branded shell passes watertightness, winding, single-body and Blender self-intersection checks. Actual engraving-floor geometry is verified in `Brand_Validation.json`. This does not establish support-free printing, snap fit, strength, diffuser brightness, thermal behavior or loaded stability.

Slice with your calibrated printer/material profile and inspect supports and layer paths. Test the retainer fit and the complete assembly before installing the LED or placing headphones on it. Check cable clearance, desk grip, loaded tipping resistance and LED temperature in use. Do not sell until a physical sample passes these checks. No machine G-code or unverified printer presets are supplied.
