# Facts: Gingerbread Tin (colour), digital then real

| Claim | Source (Claude branch, `openscad_models/clickers/gingerbread_tin/`) |
|---|---|
| Real = P1S chamber camera timelapse of the tin and its lid, red with gold snowflakes | `real/canister_colour_timelapse.mp4` (Benson's media pack, item 16; 120 frames) |
| Printed from the Canister Multicolor profile on MakerWorld model 3560658 | Scott, 2026-11-21: "Multicolor for the final one"; model number from Benson's Nov 19 check |
| Digital = toolpath simulation of a slice of the tin and lid | Claude's Bambu Studio slice (2026-11-21) of `parts/canister.stl` + `canister_snow.stl` and `lid_closed.stl` + `lid_closed_holly.stl` + `lid_closed_snow.stl`. Colours: red #C8312B, gold #E8B830, green #2E7D32. 0.20 mm Standard; about 6 h 40 m and 123 g with the prime tower. Rendered by `tools/viewer/make_listing_video.py` |
| Photos = real photos of the finished tin | `real/photos/05`, `06`, `07` (Benson's media pack). Shown by `digital_vs_real.py --photo`, cropped to 3:4 with an 8% push-in, each labelled "Photo of the finished print" |
| Matched by stage | sim 0–6 s and real frames 0–54 run until the lid is done; sim 6–10 s and real 54–119 are the tin finishing (`--sim-split 6.0 --real-split 0.45`) |

**Not claimed:**
- That the simulation is the MakerWorld profile's own file. It's Claude's slice of the same
  parts, and its colours are an approximation.
- That the plate prints the cookie. The cookie is a separate print.
- That it clicks.
- That it's free.
