# TEST — Support Interface Test — pack

Status: BUILT Nov 22, 2026 (Batch 2 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
The surface a support touches is usually the worst surface on the print.
This coupon isolates the support interface: one flat roof underside,
printed twice — once with completely stock support settings, once with a
tuned interface — so the underside finish and the removal effort can be
compared directly.

## Geometry (src/support_interface_test.py, src/SupportInterfaceTest.stl)
- Two legs 14 x 30 x 14 mm under a roof slab 64 x 30 x 4 mm; the roof
  underside is flat, 14 mm above the plate, with a 36 mm clear span
  between the legs. One watertight solid, 64 x 30 x 18 mm overall.
- The judged surface is the roof underside after support removal.

## The variable — support settings (supports ON: the exception that proves the rule)
Both profiles: 0.20 mm Standard base, 3 walls, 15% grid, matte white PLA,
ironing off (it cannot reach the judged underside anyway).
- Stock: enable_support on, everything else exactly the stock preset —
  support_type tree(auto), interface pattern auto, interface spacing
  0.5 mm, top Z distance 0.2 mm, interface top layers 2.
- Tuned: support_type normal(auto); support_interface_pattern rectilinear;
  support_interface_spacing 0.2 mm; support_top_z_distance 0.2 mm;
  support_interface_top_layers 3. (Dense rectilinear interface = a flatter,
  more continuous contact sheet under the roof; normal supports give that
  interface full coverage under a flat span, where tree supports touch at
  branch tips.)

## Verification
- Both files read back with their exact support values in project_settings;
  slice_info confirms support_used=true for both; round-trip re-slices with
  checks ON passed; stock identities; thumbnails in.
- The verify used a support-parameterised variant of the house checker
  (the stock checker hard-requires supports off).

## Profiles (profiles/, finish-stepped)
- SupportInterfaceTest_Stock_P1S.3mf — verified slice: 30 min 32 sec - 14.22 g
- SupportInterfaceTest_Tuned_P1S.3mf — verified slice: 21 min 08 sec - 15.62 g
  (tuned is faster here — normal supports under one flat span beat tree
  generation time — and slightly heavier: the dense interface is real
  material. Reported as sliced.)

## Gallery
images/ are the Studio plate render of the Tuned profile + crops —
renders, labelled as such in the listing copy until Scott prints it.
