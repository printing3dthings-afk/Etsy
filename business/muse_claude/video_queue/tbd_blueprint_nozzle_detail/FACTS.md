# Facts: what a 0.4 mm nozzle can really print

Source: `openscad_models/detail_calibration/DETAIL_STANDARD.md` (Claude branch), re-checked 2026-11-20.

| Tip | Source |
|---|---|
| 1. Upright groove holds depth at every layer height | table "Across the face", 0.20 / 0.12 / 0.08 mm layers; re-sliced at 0.20 today, worst error 0.01 mm |
| 2. 0.3 mm groove prints 0.4 at 0.2 mm layers | table "Up the face"; re-slice 2026-11-20 agrees |
| 3. 0.1 mm groove prints a full 0.2 mm layer | the same tables; re-slice agrees |
| 4. 1 mm dome = 5 layers at 0.2 mm | "boss 1.0 across: 5 layers"; re-slice agrees |
| 5. Letters 3 mm tall on a 0.4 nozzle | rule 10 |
| 6. Dots at least 0.8 mm; smaller are dropped | rule 11 |

Made with `business/social/tip_posts/make_tip_post.py` (Blueprint theme) and `assemble.py`
(Claude branch `27aa197`). The Blueprint blue and gold are close matches until OPEN row 31's values come in.
