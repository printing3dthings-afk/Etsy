# Lesson 008 facts: every claim and its source

Lesson: "What 100% infill costs". Our Gingerbread Cottage, sliced three times in Bambu Studio
on 2026-11-20 by `tools/bambu_slice.py`. Settings: P1S 0.4, PLA Basic, 0.20 mm Standard,
supports off, the four cottage parts in one colour. Only walls and infill change. Each slice's
own figures are in `facts/slices.json`, copied from its `Metadata/slice_info.config`.

| Said or shown | Source | Value |
|---|---|---|
| 2 walls, 100% infill: 113 g, 3 h 04 m | slices.json `w2_i100` | 112.98 g, 11,010 s |
| 5 walls, 20%: 64 g, 2 h 24 m | `w5_i20` | 64.37 g, 8,643 s |
| Ours, 3 walls, 15%: 51 g, 2 h 15 m | `w3_i15` | 51.32 g, 8,115 s |
| "Less than half" | 51.32 / 112.98 | 45% |
| "About 50 minutes longer" | 11,010 − 8,115 s | 48 min 15 s |
| 3 walls, 15% is ours | Scott, 2026-11-12 | |
| "Lesson 6 showed where the strength is: in the walls" | Lesson 006's credited source: CNC Kitchen pull tests, via @3dmartos | not our test |

## Said with care
- **No strength claim for these three slices.** We didn't test them. The strength line points
  back to Lesson 006 and its credited source. Keep it that way in the caption.
- **The 100% slice uses zig-zag infill,** because Bambu Studio refuses grid at 100%. The other
  two use grid, Bambu's default. That's how anyone would slice it, but say "sliced" and not
  "printed": none of the three was printed for this lesson.
- **Why 2 h 15 m, not the 2 h 13 m in the cottage's printing notes:** the notes' slice
  (Nov 18) used one merged mesh; this one slices the four parts. The lesson compares three
  slices made the same way on the same day, so use these three together, not mixed with the
  notes.
- **The cottage picture is a render,** labelled on screen "Design-review render, not a photo".
  A real photo of a printed cottage would be better. Swap it in if Scott has one.
