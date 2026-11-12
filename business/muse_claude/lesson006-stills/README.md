# Lesson 006 stills — read me first

The three JPGs in this folder are **base64-encoded text**, not raw image
bytes. The GitHub connector Benson pushes through accepts text only, so
the stills travel encoded. Decode any of them with:

    base64 -d scene1_beam.jpg > scene1_beam_decoded.jpg

Files (all 810×1440, JPEG quality 50, frames from the shipped video
`lesson006_animated_v1.mp4`):

- `scene1_beam.jpg` — BEND scene, frame at ~13.0s
- `scene2_hookpull.jpg` — TEST scene (hook pull), frame at ~27.0s
- `scene3_walls.jpg` — OURS scene (hollow shell), frame at ~39.0s
