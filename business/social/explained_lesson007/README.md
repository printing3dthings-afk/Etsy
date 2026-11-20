# Explained, Lesson 007: "The 0.2 mm rule"

A complete animated lesson in the Lesson 006 identity (Scott picked that style 2026-11-19).
Unlike Lesson 006, it doesn't depend on a voice-over: the caption band carries the narration,
so it works silent. `SCRIPT.md` has the same lines with times for Benson's voice-over.

## Files (`out/`)
| file | what |
|---|---|
| `lesson007.mp4` | 1080 × 1920, 30 fps, 50 s, silent, captions burned in |
| `lesson007_clean.mp4` | the same with no caption band, for Benson's own captions |
| `carousel/slide1-5.png` | 1080 × 1350 slides, cut from the video's own stills |
| `lesson007_<t>s.png` | full-frame stills (covers, Pinterest, Patreon post images) |

## Scenes
| time | scene | shows |
|---|---|---|
| 0–6.6 | HOOK | draw 0.3, get 0.4 |
| 6.6–17.6 | LAYERS | a 1 mm dome becomes five layers |
| 17.6–30 | SNAP | level grooves round to whole layers: 0.3 → 0.4, 0.1 → 0.2 |
| 30–41 | UP | upright grooves, seen from above, all within 0.01 mm |
| 41–50 | RULE | run fine detail up the face; heights on the 0.2 mm grid |

Every claim is in `FACTS.md`, with its source.

## Rebuild
    python3 animate.py out --stills 5.8,16.6,29.4,40.4,49.5   # about 4 minutes
    python3 animate.py out --clean
    python3 carousel.py
    python3 animate.py out --frame 23.0                      # one frame, for checking
