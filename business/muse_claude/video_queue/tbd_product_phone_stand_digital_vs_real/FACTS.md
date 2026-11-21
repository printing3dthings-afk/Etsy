# Facts: phone stand, digital then real

| Claim | Source (Claude branch, `openscad_models/`) |
|---|---|
| Digital = toolpath simulation of the sliced file | `video/phone_stand-timelapse.mp4`, the viewer's `phone_stand` job (`phone_stand.3mf`), made by `tools/viewer/make_listing_video.py`. Each shot carries the label |
| Real = P1S chamber camera timelapse | `real_timelapses/phone_stand_2026-11-21.mp4`, Scott, 2026-11-21 (Bambu cloud timelapse, 120 frames) |
| Matched by stage | sim 0–5 s and real frames 0–30 are the base and lips; sim 5–9 s and real 30–119 are the back (`business/social/series_motion/digital_vs_real.py`, `--sim-split 5.0 --real-split 0.25`) |
| Retimed, scaled, cropped; not altered | the same script |

**Not claimed:**
- that the real print matches the simulation to any measured accuracy;
- that the stand is for sale or free.

**Colour:** the simulation draws the part grey on the viewer's yellow plate; the real one is
Scott's yellow PLA.
