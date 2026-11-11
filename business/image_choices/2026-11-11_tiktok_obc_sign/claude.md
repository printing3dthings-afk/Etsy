# Claude's TikTok

`claude.mp4`: 1080 × 1920, 15 s, H.264 High, 30 fps, no audio (Muse or Scott adds
sound and the voiceover, if any).

| time | what |
|---|---|
| 0–12 s | The plaque's real slice played back by the print viewer: the black plaque builds up, then the gold OBC rises out of it. The camera turns and ends square on to the letters. |
| 12–15 s | End card: the 3D render of the finished sign standing in its base. |

**Text on screen:**
- **0–12 s:** "Turning my logo into a 3D print", and under it, on every frame, "Toolpath
  simulation of the sliced file, not print footage".
- **End card:** "OBC desk sign", "Gold on black, plaque 182 mm wide", "The plaque
  slides into its base", "3D render of the design, not a photo".
- **Placement:** all text sits clear of the top 220 px and the bottom quarter.

**What it doesn't claim:** that the sign has been printed. It hasn't yet, and every
frame is labelled as a simulation or a render.

**One honest edit to the slice:** the wipe tower (the purge block a two-colour
print makes) is left out, as a single-spool print with a pause at 5.0 mm has
none. Everything else is the print-fidelity slice of the real parts, as sliced.

## Sources (branch `claude/new-session-o245bl`)

- **The slice:** `openscad_models/brand/obc_desk_sign/`, print-fidelity slice of
  `parts/plaque.stl` + `parts/letters.stl`.
- **The clip:** `tools/viewer/make_listing_video.py obc_desk_sign --format reel
  --size 1080 --seconds 12 --hold 2 --detail high --facing -157.5`.
- **The text and end card:** `openscad_models/brand/obc_desk_sign/social/make_tiktok.py`;
  the end-card image is `images/obc_desk_sign_three_quarter.png`.
- **The 182 mm width:** `OBC_DESK_SIGN_PRINTING.md`.
