# Facts: OBC desk sign, digital then real

| Claim | Source (Claude branch `54d1f13d`, `openscad_models/brand/obc_desk_sign/`) |
|---|---|
| Digital = toolpath simulation of the sliced file | `social/obc_sign_tiktok_claude.mp4`, made by `tools/viewer/make_listing_video.py` from the print-fidelity slice (Nov 11). Its own text is cropped off; each shot carries the label |
| Real = P1S chamber camera timelapse | `real/obc_sign_p1s_timelapse_2026-11-21.mp4`, Scott, 2026-11-21 |
| Matched by stage | sim 0–7.5 s and real frames 0–24 are the plaque; sim 7.5–10.5 s and real 24–36 are the letters (`social/make_compare_clip.py`) |
| Photos = Scott's photos of the finished sign | `real/photos/` (front, three-quarter right and left), Scott, 2026-11-21; shown after the stack by `business/social/series_motion/digital_vs_real.py --photo`, cropped to 3:4 with a slow 8% push-in, each labelled "Photo of the finished print" |
| Retimed, scaled, cropped; not altered | the same script |
| "So we can see every layer before the printer moves" | the simulation is built from the sliced G-code, layer by layer |

Not claimed: that the real print matches the simulation to any measured accuracy.
