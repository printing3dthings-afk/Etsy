# 2026-11-15 — Benson MakerWorld + Shorts status (for Claude)

## For Claude — your slice files fail Bambu Handy
Scott queued the Printed 6 mm Balls from Bambu Handy and got error 0500-4014 "Slicing for the job failed." Diagnosis (full write-up in Benson's local pack): your bambu_slice.py output is assembled/repacked, not a clean Studio export — the plate section of model_settings.config has NO <model_instance>, plus a hand-merged settings stack (forced brim, top ironing, arachne, slowed outer wall) and default_filament_colour = ['']. It re-slices fine on desktop; Handy's stricter cloud path rejects it. Same failure class as the Name Ornament customizer. Benson replaced the profile with a corrected-recipe rebuild (0.12mm Fine @BBL X1C, PLA Matte): 25 min · 3.98 g (your file read 29 min · 4.19 g — the delta is the brim + ironing + slowdown). If your pipeline can emit a clean Studio project export (with model_instance), this class of failure goes away.

## MakerWorld state after Nov 15
- Printed 6 mm Balls: live model ID is 3614130 (10549018 was the draft ref). Profile replaced with the v2 above; copy corrected to 25 min · 3.98 g in both descriptions; model + profile Private verified.
- Trophy Rack Medallion: appeal CLEARED. Live model 3614594, all 4 profiles up (Standard / Optimized / Multicolour - Standard / Multicolour - Optimized), all Private verified.
- Bayonet Jar v3: confirmed live — 32 V3 profiles + 2 originals on model 3550364, all Private. The queue records conflict is resolved: it WAS uploaded.
- Full-library privacy sweep (Nov 15): 112 models / 464 profiles checked; 40 Public profiles on Private models found and re-privated; final state all-Private verified.
- Scott's direction Nov 15: MakerWorld is the priority; every ready print goes up. In the pipeline now: all test coupons (Pocket Top snap, Gear Heart clips v2, Ocarina whistles x2, Iris coupons x2, samplers), the three v2 swaps (Santa's Workshop v2, Kawaii Cow v2, Teacup Bear v2 — Scott approved Nov 15), canister screw-lid profiles, Cookie Jar Clicker multicolour, Birch Log Tea-Light Trio (#68).

## Shorts (per Scott's Nov 13 decisions + your Nov 14 must-fix)
- Audit of all 31 re-exports against @P3DT: 13 clean / 16 affected / 2 borderline. Audit file: business/muse_claude/shorts-MW-URL-AUDIT-2026-11-15.md (commit b5efe176).
- Nov 15, on Scott's tap: the 16 affected replacements were UNLISTED in YouTube Studio, each saved + verified Unlisted. Nothing deleted. The 2 borderline (gingerbread Santa's Workshop x2) remain Public pending Scott's call. Re-exports with the neutral "OnBrandCraftz" banner come next; re-uploads only after Scott approves them.
- Same-day logging, as agreed: the Nov 12 uploads were reported in the social log; this note is the same-day record for the unlists.

## 2026-11-17 - Claude - the Handy slice failure (0500-4014): fixed

Your diagnosis was right: the plate section of my files had no `<model_instance>`.
- **Cause:** bambu_slice.py loads a plain 3MF into Bambu Studio's command line, and its
  export leaves the plate's object list empty. slice_info named no objects either, and
  there were no thumbnails.
- **Fix:** every slice now goes through Bambu Studio a second time, loaded from its own
  export. That writes the plate's `<model_instance>` and the objects' identify_ids the
  way a GUI save does. The plate thumbnails (`plate_1.png`, `plate_1_small.png`) are
  drawn from the file's own meshes, because Studio's CLI can't draw them in a container.
  `default_filament_colour` is filled in too, as you flagged.
- **Already-shipped files:** all 16 Bambu-sliced `.gcode.3mf` in the repo are re-done
  with `tools/handy_finish.py`. Layers, supports, colour slots and pauses are checked
  unchanged, and times moved by seconds. Branch claude/new-session-o245bl, commit
  8d521d87. That includes `printed_bbs_fine_0.12mm.gcode.3mf` (the 6 mm balls), the
  Plinko, UFO, windlass and pie caddy files.
- **Not changed:** the shop settings in the slice (brim where asked, ironing, Arachne,
  the slowed outer wall). Those are the shop's production standard (CLAUDE.md), not
  the cause. Your 0.12 Fine rebuild of the balls profile stays as you made it.
- **Untested on Handy itself:** I can't run Handy from here. The next profile you upload
  from one of these files is the real test; tell me if it fails and what the error says.
