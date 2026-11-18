# Claude's entry: Lesson 006 diagram scenes

- **`claude.mp4`:** the three scenes back to back, 35.8 s, silent, for comparing.
- **`claude_clips/`:** the clips Benson cuts in.

  | clip | VO section | length |
  |---|---|---|
  | `scene1_beam.mp4` | BEND 7.6–19.8 s | 12.2 s |
  | `scene2_hookpull.mp4` | TEST 20.4–33.9 s | 13.5 s |
  | `scene3_hollow.mp4` | OURS 34.5–44.6 s | 10.1 s |

  - Each is exactly its section's length.
  - Each has a `_clean` twin without the caption band, for Benson's own captions.

## How it was made
- **Drawn frame by frame in code:** `business/social/explained_lesson006/animate.py` on the
  Claude branch, at 2x then downsampled, 30 fps.
- **Keyframed and eased.** Every beat is keyed to the VO line's own time: the beam sags as
  the first line starts, the dashed centre line draws on "the middle carries almost zero
  stress", the counter runs up and snaps on its line.
- **Fonts:** Anton and Chakra Petch, both SIL Open Font License, included with the source.

## What each scene shows
1. **BEND.**
   - A layered beam sags under a load.
   - The top skin tints orange (squeezed) and the bottom teal (stretched), fading to nothing
     in the middle.
   - A dashed line draws along the centre: "CENTRE: ~0% STRESS".
   - A bone's cross-section fills in: hard shell, light sponge.
2. **TEST.**
   - Two cards, the same hook. Each card's cross-section builds its walls and infill as its
     line is spoken: 2 rings and solid, then 5 rings and a sparse grid.
   - The counter runs up with the bar.
   - 2 walls snaps at 64 kg: the hook's bend falls away, SNAPPED in orange, "82 g of
     plastic".
   - 5 walls holds at 108 kg: HELD in teal, "54 g of plastic".
   - The CNC Kitchen credit sits under the cards from the start.
3. **OURS.**
   - The house's outline draws itself, and the tealight lights.
   - The three perimeters go on, then the 15% infill, labelled "3 WALLS" and "15% INFILL".
   - "AIR" fills the room.
   - On "strong where it works", the walls pick out in orange; on "air where it doesn't",
     the teal line.

## Choices to know about
- **No red.** The snap is burnt orange, to stay inside the four locked colours. Benson's
  cut used red there.
- **Scene 3's infill is inside the wall, not across the room.** That's how our houses are
  printed: three perimeters and sparse infill make the wall, and the room is air for the
  tealight. A grid across the whole room would say the room is printed solid with infill,
  which isn't true.

## Sources
- 64 kg / 82 g and 108 kg / 54 g: CNC Kitchen's pull tests via @3dmartos, as Benson shipped
  them, credited on screen.
- 3 walls, 15% infill: Scott, 2026-11-12, recorded in `threads/2026-11-11_animation-quality.md`.
- Timings: Benson's 2026-11-12 entry in the same thread.
