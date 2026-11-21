# Facts: gingerbread tin, digital then real

| Claim | Source (Claude branch) |
|---|---|
| Digital = toolpath simulation of the sliced file | `openscad_models/clickers/gingerbread_tin/checks/canister_one_colour.gcode.3mf`: Bambu Studio's slice of `canister_print`, `lid_closed_print` and `cookie_print` on one plate, 0.20 mm Standard, about 2 h 40 m and 65 g. Converted with `tools/bambu_gcode.py`, rendered by `tools/viewer/make_listing_video.py` (the viewer draws it white on its yellow plate) |
| Real = P1S chamber camera timelapse | `openscad_models/real_timelapses/gingerbread_tin_canister_plate_2026-11-21.mp4`, Scott, 2026-11-21 (120 frames): the same three parts, in white |
| On MakerWorld, model 3560658 | Scott, 2026-11-21: "The clicker is on makers world"; the model number and its Tin Clicker + Canister profiles are from Benson's Nov 19 check (`threads/2026-11-19_makerworld-extraction-stall-help.md`) |
| One plate, one colour | both of the above |
| Matched by stage | sim 0–6 s and real frames 0–42 run until the lid and the cookie are done; sim 6–10 s and real 42–119 are the tin finishing (`business/social/series_motion/digital_vs_real.py`, `--sim-split 6.0 --real-split 0.35`) |
| Retimed, scaled, cropped; not altered | the same script |

**Not claimed:**
- that Scott printed from this exact file (it's the same three parts on one plate, in one
  colour; his own slice may differ);
- colours (the design's colour version isn't in the video);
- that it clicks;
- that it's free or for sale (only that it's on MakerWorld).

**The two cameras face the plate from different sides,** so the parts' left-to-right order
differs between the simulation and the real shots.
