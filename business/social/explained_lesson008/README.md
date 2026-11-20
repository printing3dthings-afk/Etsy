# Explained, Lesson 008: "What 100% infill costs"

Lesson 006's advice, priced on our own Gingerbread Cottage: the same house sliced at 2 walls /
100%, 5 walls / 20% and ours, 3 walls / 15%. 42 s, in the Lesson 006 identity. It works silent:
the caption band carries the narration. `SCRIPT.md` has the lines timed for a voice-over.

## Files (`out/`)
| file | what |
|---|---|
| `lesson008.mp4` | 1080 × 1920, 30 fps, 42 s, silent, captions burned in |
| `lesson008_clean.mp4` | no caption band |
| `carousel/slide1-5.png` | 1080 × 1350 |
| `lesson008_<t>s.png` | full-frame stills |

Every claim is in `FACTS.md`. The numbers on screen are read from `facts/slices.json` when it
renders, so they can't drift from the slices.

## Rebuild
    python3 animate.py out --stills 5.6,9.8,21.0,25.8,41.2
    python3 animate.py out --clean
    python3 carousel.py
