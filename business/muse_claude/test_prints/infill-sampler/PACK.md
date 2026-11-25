# TEST — Infill Sampler — pack

Status: BUILT Nov 22, 2026 (Batch 2 of the 20-test-print program). NOT uploaded — staged for Scott's word.

## Design intent
What does infill percentage actually buy you — in weight, time, stiffness and
crush strength? Seven identical blocks on one plate, each with a different
infill, tops open so the pattern itself is visible. This is also the coupon
that answers the shop's open infill question (Standard is 15%, Optimized 12%).

## Geometry (src/infill_sampler.py, src/InfillSampler_src.3mf, src/InfillSampler.stl)
- Seven solid blocks 40 x 40 x 12 mm, one plate, watertight.
- Each block embossed on its front face with its setting: GYROID 5 / 10 / 15 /
  20 / 40%, GRID 15%, LIGHTNING 15%.
- The STL in src/ is a merged reference copy; the build source is the
  multi-object scene 3MF (objects must stay separate for per-object settings).

## The variable — per-object slicer settings (NOT geometry)
Per-object overrides injected into model_settings.config (ironing-coupon
mechanism), everything else identical for all seven blocks: 0.20 mm Standard,
3 walls, matte white PLA, supports off, ironing off.
- sparse_infill_density / sparse_infill_pattern per block as labelled.
- top_shell_layers = 0 on every block — the top is open so the infill pattern
  is the surface you judge. (Ironing off for the same reason: it would hide
  the measured surface.)

## Verification (this is a sampler — variants MUST differ, and they do)
- Readback of the finished file: every block carries its exact density,
  pattern and top_shell_layers=0 through pass 1, the per-object re-slice AND
  the finish step (see build_results.json: final_readback).
- Gcode evidence, extrusion length per block in the z 5–7 mm band of the
  finished file: G5 7,054 mm < G10 8,422 < G15 10,460 < G20 11,950 < G40
  18,077; GRID 15% 11,417 (distinct from gyroid at the same density);
  LIGHTNING 15% 6,714 (sparsest, as expected — it only grows toward load).
- Round-trip re-slice with checks ON passed; stock identities; thumbnails in.

## Profile (profiles/, finish-stepped)
- InfillSampler_Standard_P1S.3mf — one profile only, by design: the
  comparison lives on the plate, so a Standard/Optimized pair would just
  print the same comparison twice. Verified slice: 1 hr 16 min - 51.56 g.

## Gallery
images/ are the Studio plate render of the profile + crops — renders,
labelled as such in the listing copy until Scott prints it.
