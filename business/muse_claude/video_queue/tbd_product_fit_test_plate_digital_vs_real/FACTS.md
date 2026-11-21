# Facts: fit test plate, digital then real

| Claim | Source (Claude branch, `openscad_models/multipart/test_plate/`) |
|---|---|
| Thread, ball/socket, gears, detent, bayonet; 0.2 / 0.3 / 0.4 mm each | `TEST_PLATE_PRINTING.md` (the fit table); `fit_test_plate.scad` |
| Digital = toolpath simulation of a slice of this plate | Claude's Bambu Studio slice (2026-11-21) of `logs/plate_all.stl`, the packed plate as in `fit_test_plate.3mf`. Moved back 30 mm, clear of the purge corner; 0.20 mm Standard; about 5 h 7 m and 94 g. Rendered by `tools/viewer/make_listing_video.py`. Each shot carries the label |
| Real = P1S chamber camera timelapse | `openscad_models/real_timelapses/fit_test_plate_2026-11-21.mp4`, Scott, 2026-11-21 (72 frames) |
| Matched by stage | sim 0–5 s and real frames 0–21: the flat parts; sim 5–10 s and real 21–71: the rings, pins and gears rising (`digital_vs_real.py --sim-split 5.0 --real-split 0.3`) |
| Retimed, scaled, cropped; not altered | the same script |

**Not claimed:**
- That Scott printed from this exact slice. His own may differ in arrangement or settings.
- Any test result.
- Where it's available.

**The simulation's camera is high and wide; the chamber camera is low and close.** The two
frame the plate differently.
