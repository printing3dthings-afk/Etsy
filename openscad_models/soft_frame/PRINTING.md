# Soft Frame — OnBrandCraftz

Original stackable craft-and-hobby drawer prototype, selected concept 1. This is a digitally checked prototype, not a physically validated retail release.

## What to open

- `Soft_Frame_Phone_View.usdz`: two-module display for iPhone/iPad Quick Look. Save to Files and tap. Viewer support depends on the app.
- `Soft_Frame_Assembly.3mf`: two assembled modules, with the lower drawer open. VIEW ONLY: not a printable plate layout.
- Six lowercase part-named `.3mf` files and matching binary `.stl` files: already oriented for printing. Print each part separately with your own calibrated printer/filament profiles. They contain geometry, not Bambu presets or G-code.
- `Soft_Frame.scad` and `OBC.svg`: editable source and approved brand vector. Keep them together. No external SCAD libraries required.
- `Validation.json`: mesh, Blender and slicer results for the exported parts.

## Sizes and components

One module is 160 mm wide, 125 mm deep and 63.4 mm tall including its 1.4 mm locating tongues. A two-module closed stack is 125.4 mm tall. Each extra module adds 62 mm. Internal storage is approximately 142.7 × 109.9 × 45.4 mm before adding dividers; the two removable 30 mm-high dividers form four compartments.

For one complete module, print one housing, one drawer, one long divider, one cross divider and one label tile. Dividers and tile are optional. Print a second set for the two-module arrangement shown in the preview. The sixth part is a small two-piece slide-fit coupon, not part of the product.

## Printing

1. Print `Soft_Frame_fit_test.3mf` first, in the supplied orientation. Once removed from the plate, the wide flange on the smaller sample slides lengthwise under the other sample's cap. The nominal vertical clearance is 0.5 mm. This tests the captured-slide gap, not full-size warping, stack fit or label fit.
2. Print the housing in slate/charcoal PLA, **on its back, opening upward**, exactly as supplied. This orientation eliminates a roof bridge over the drawer cavity. Keep the broad rear face on the bed.
3. Print the drawer flat, open side up, in tan PLA. Print dividers flat in slate and the label tile flat in a contrasting color. No AMS color swaps are required within a part.
4. Starting profile: calibrated 0.4 mm nozzle, 0.20 mm layers, 3 walls, 5 top/bottom layers, 15% gyroid, supports off. Use your established temperatures and flow settings. Inspect the Bambu Studio layer preview before printing. Keep visible outer walls around 40–50 mm/s as a finish trial, and place the seam toward the rear where possible.
5. Let everything cool before removal and fitting. Test smooth travel without forcing. Measure your actual print; tune clearance in the source if necessary and re-export both mating parts together.

The supplied orientations fit the 256 mm P1S build envelope. The housing is 125 mm tall on the plate. A brim can be tested if your material or plate needs more adhesion. The label tile is deliberately thin (0.8 mm); let it cool before lifting it.

## Assembly and use

Slide the drawer in from the front. Its floor flange rides on two runners beneath capture ribs, which reduce lifting and tipping while engaged. The front scallop is accessible with another module above it.

Slot the two divider strips together at their half-depth cuts, one opening upward and the other downward. Drop the grid into the drawer. End clearances are nominally 0.4 mm; the insert is removable and does not snap in.

The blank label tile slides down through the mouth above the front label window. It is 31.2 × 11.2 × 0.8 mm, with nominal side clearance 0.4 mm. Write on it or apply a small printed label. A thin card can also be tried. Verify retention on the physical sample.

Set an upper module's underside tongues into the lower module's top grooves. There is nominally 0.4 mm clearance on each side and 0.4 mm extra groove depth, allowing the flat housing faces to seat together. This locates the modules; it is not a latch. Support the whole stack when moving it.

There is **no pull-out stop**: the drawer can be removed completely. Keep at least 35 mm engaged during ordinary use until a physical test establishes a safe travel/load limit. Small craft supplies are the intended contents; no load rating or safe stack height has been established.

## Branding

The approved OBC vector is engraved 0.7 mm deep: 26 mm wide on the drawer underside and hidden rear of the housing, and 12 mm wide on the divider faces. The housing mark is on its print-bed face to avoid support scars. No raised product branding. The blank label and fit-test coupon are accessories, not separately branded products. The supplied vector's minimum stroke at these sizes exceeds the repository's 0.84 mm requirement. Confirm actual legibility and orientation on the first print.

## Digital checks and their limits

All six exports pass mesh integrity and Blender's non-manifold, winding and self-intersection hard checks. Fine-detail/thickness advisories remain visible in `Validation.json`; a recessed logo is not treated as a hole through the wall.

PrusaSlicer 2.7.2, 0.20 mm layers, 0.4 mm nozzle: all six parts reach full intended height with **zero support moves and zero overhang perimeters** in the test profile. Small bridge moves remain over engraved strokes and recesses. This is not a Bambu Studio quality or print-time guarantee.

Solid-intersection checks confirm no housing/drawer overlap closed, 42 mm open or 85 mm open, and no solid overlap between stacked housings. Raising the drawer 0.8 mm intersects the capture ribs, confirming that the guides actually capture its flange. The assembled divider pair also clears the drawer and each other. These are geometric checks, not friction, wear, strength or load tests.

The preview is rendered from the exported meshes. It is not a print photograph or a simulation of layer finish. Before selling, print a full sample and check slide smoothness, label retention, divider fit, loaded stability, stacking, engraving, surface finish and repeatability. Use measured material, machine time, labor and shipping to establish your price.
