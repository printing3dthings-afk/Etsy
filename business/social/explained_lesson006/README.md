# Explained, Lesson 006: Claude's diagram scenes (polish lane)

OPEN.md row 12. Benson's proposal: `business/muse_claude/threads/2026-11-11_animation-quality.md`
on main. Benson keeps script, voice-over, captions, QC and posting. These clips are
Claude's side of an image choice (`business/image_choices/2026-11-18_lesson006-diagrams/`
on main): Scott picks, and Benson's shipped cut stays live until he does.

## The clips (`out/`), 1080 x 1920, 30 fps, silent
| clip | VO section | length | with captions | clean |
|---|---|---|---|---|
| beam bending | BEND 7.6–19.8 s | 12.2 s | `scene1_beam.mp4` | `scene1_beam_clean.mp4` |
| hook pull, 2 walls vs 5 | TEST 20.4–33.9 s | 13.5 s | `scene2_hookpull.mp4` | `scene2_hookpull_clean.mp4` |
| our hollow houses | OURS 34.5–44.6 s | 10.1 s | `scene3_hollow.mp4` | `scene3_hollow_clean.mp4` |

- Each clip is exactly its section's length, so it drops onto the VO with no retiming.
- Every beat is keyed to the VO lines' own times (in `animate.py`).
- The "clean" clips leave the caption band off, for Benson's own captions.
- `out/lesson006_diagrams_claude_preview.mp4` puts the three back to back, for viewing only.

## Identity, as locked
- **Colours:** cream (246,240,226), ink (32,36,46), burnt orange (232,106,44), teal
  (20,110,96).
- **Type:** Anton headlines, Chakra Petch body.
  - The fonts are in `fonts/`. Both are SIL Open Font License; `OFL.txt` is Anton's, and
    Chakra Petch's is the same licence.
- **Red:** none. Benson's cut used red for the snap; here it's burnt orange, to stay
  inside the four colours.

## Numbers on screen, and where they come from
- **64 kg / 82 g and 108 kg / 54 g:** CNC Kitchen's pull tests, as Benson shipped them.
  Credited on screen: "CNC Kitchen pull tests, via @3dmartos".
- **3 walls, 15% infill:** Scott, 2026-11-12.
- **Scene 3 shows the wall as our prints really are:** the three perimeters and the sparse
  infill sit inside the wall's thickness, and the room is air, where the tealight goes.
  A grid filling the whole room would say the room is printed solid with infill. It isn't.

## Rebuild
`python3 animate.py out` (add `--clean` for the clean set, `--scene N` for one). About 3
minutes for all three.
