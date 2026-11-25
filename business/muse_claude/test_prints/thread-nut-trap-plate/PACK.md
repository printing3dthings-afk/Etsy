# TEST — Thread & Nut-Trap Plate — pack

Status: BUILT Nov 22, 2026 (Batch 3 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
Two fit questions in one print set: printed-thread clearance (feel, not
guesswork) and hex nut-trap sizing for the three nut sizes the shop stocks.

## Geometry (src/thread_plate.py; parts in src/parts/, scene src/ThreadNutTrapPlate_src.3mf)
Seven separate objects on one plate, built as an indexed scene 3MF (named
objects: TrapPlate, BoltA, Nut03, Tile03, BoltB, Nut04, Tile04):
- Threads are TRUE helical sweeps: an ISO 60° profile (external sharp-V
  with root flat; internal with crest flat) lofted along a helix, 48
  segments/turn — not stacked rings. M16 x 2.0, 20 mm engagement.
- Bolts (x2, identical): hex head AF22 x 8, shank Ø13 x 4, thread major
  Ø16.0, minor Ø13.55. Nuts (AF24 x 12): internal thread cut at +0.3 and
  +0.4 mm RADIAL clearance per side (bore minors Ø14.15 / Ø14.35; thread
  depth reduced so flanks keep the true 0.6 mm radial gap — verified:
  pitch 2.000 mm, min bolt↔nut surface distance 0.598 mm on the 0.3 nut).
  Engraved tiles "CLR 0.3" / "CLR 0.4" sit with each pair.
- Trap plate 150 x 54 x 5: hex traps for M3 (AF 5.5), M4 (AF 7.0), M5
  (AF 8.0) at +0.2 / +0.4 / +0.6 over nominal (5.7/5.9/6.1, 7.2/7.4/7.6,
  8.2/8.4/8.6), depth = nut height + 0.2 (2.6 / 3.2 / 3.8). Row labels
  M3/M4/M5 and column labels +0.2/+0.4/+0.6 engraved.
- Mesh-verified (verify_batch3.py): every trap AF measures exact in
  section; thread pitch measured 2.000 mm off the bolt mesh.
- Build note: the manifold booleans left vertex pairs ~2e-7 mm apart at
  trim planes, which cracked the STL/3MF exports into fragments. A
  cluster-weld (tolerance 1e-4) in thread_plate.py fixed it — both
  formats now round-trip as exactly 7 watertight bodies (vol 63100 mm³).
  The build feeds Studio the scene 3MF, not the STL.
- Hardware not included — Scott supplies real M3/M4/M5 nuts; copy says so.

## Profiles (profiles/, finish-stepped, plate thumbnails in both)
- ThreadNutTrapPlate_Standard_P1S.3mf — 0.20 mm Standard @BBL X1C, 3 walls, 15% grid,
  supports off, ironing off. Verified slice: 1 hr 13 min - 43.61 g.
- ThreadNutTrapPlate_Optimized_P1S.3mf — 0.16 mm Optimal @BBL X1C, 3 walls, 12% gyroid,
  supports off, ironing off. Verified slice: 1 hr 41 min - 45.72 g.
- Both: matte white PLA (Bambu PLA Matte @BBL P1S 0.4 nozzle), printer Bambu Lab
  P1S 0.4 nozzle, round-trip re-slice with checks ON passed. Thread
  clearances and trap sizes IDENTICAL in both — layer height only.

## Profile choices / compromises
- Ironing OFF: trap mouths are fit surfaces (Batch 1 precedent — no
  ironing lip on a measured opening).
- M16 chosen over M12: at 2.0 mm pitch the thread form prints cleaner and
  the clearance difference is easier to feel; the research's coarse class.
- Print time note: the finish step's thumbnail render is pathologically
  slow on this geometry (~25 min CPU per profile — brute-force raycast
  against the helical meshes). Files are unaffected; noted for Batch 4
  planning.

## Gallery
images/ are the Studio plate render of the Standard profile + centre/corner
crops — renders, labelled as such in the listing copy until Scott prints it.
