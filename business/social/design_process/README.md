# Design process: from the design file to the finished print

Scott, 2026-11-26, with the Pie Drum Caddy v2 cutaway attached: "I want you to use images like
this from your design process's to use in videos. From all of the prints you do this with. Can
you incorporate pictures like this into animations to transform from step to step until the
final product?"

**The standing rule:** every print whose design work produces images like these gets one of these
videos. That means cutaways, exploded views, fit checks, renders, as-printed stills, and coupons
next to real test prints. Scott approves each video before it posts (STANDARDS 8), and Benson
posts it with voice-over and music.

## How a video is made
1. **The real parts, moving** (`blender_anim.py`, run by a storyboard script). Blender loads the
   real exported STLs and keyframes them, so every step becomes motion rather than a slideshow:
   - parts fly in, screw home, lift off;
   - the camera travels between the design views;
   - a cut plane sweeps through the model and lands on the cutaway (the clipped surfaces hand
     over to the solid cut faces).

   - parts can turn about their own hinge axes and ride on other parts (`pivot`, `parent`), so a
     mechanism moves the way the design says it does (Fold Stand v4's prop in its folding plate).

   Same studio as `tools/blender_render.py`: floor, matte filament colours, light grey world.
   Rendered in EEVEE, about 12 s a frame at 1080. Cycles takes about 2 minutes a frame, too slow
   for animation; it's kept for stills.
2. **The frame** (`compose.py`):
   - the shots sit in the Product posts kit's frame, 1080 × 1920;
   - each step has a heading and a caption;
   - every shot is tagged **RENDER** or **REAL** (Scott's own footage), as `digital_vs_real.py`
     does;
   - steps dissolve into each other;
   - the kit's opener and end card go on either end.
3. **The storyboard** (one script per product, e.g. `pie_caddy_v2.py`): the shots, the captions,
   and where every figure in a caption comes from. Each video ships with its `SCRIPT.md`: timed
   lines for Benson's voice-over, and the source of each claim.

## Template v2: the checklist for every video (2026-11-27)
Scott, via Greg, after the Fold Stand and Gear Heart first cuts. Every new video uses
`compose_v2.py` and a storyboard that passes this list. `compose.py` (v1) stays only so the first
cuts can be rebuilt as they were. Never overwrite a cut: a new version goes beside it as
`<name>_design_v2.mp4` with its own `SCRIPT_v2.md` and `timeline_v2.json`.

**Opening**
- [ ] No title card. The first second is the payoff: the finished product working.
- [ ] Then the line "N versions to get here" (count them from the files: versions and test
      prints), then a `rewind` segment back to version 1.

**Frame**
- [ ] Renders fill the frame, 9:16: shots set `res=[1080, 1920]`. No small box in the middle.
- [ ] Every caption, heading, tag and the watermark sits on a dark backing box, at least 20% up
      from the bottom. `compose_v2.py` refuses to write a frame with text below that line.

**Ending**
- [ ] No separate end card. The follow line fades in over the last shot, 1.5 s at most.

**Pace and motion**
- [ ] 2-3 s per version, and one short caption per version (it has to be read in that time).
- [ ] Every part move eases in and out (Blender's Bezier keys), and the moves themselves take
      long enough to see.
- [ ] Nothing pops in. Parts enter from outside the frame. A `show` switch is only allowed while
      the part is off-screen.
- [ ] No parts hanging in the air. A part that isn't moving sits in its real place: check the
      posed gaps against the fit (Fold Stand v3: 0.3-0.4 mm, the real clearance).

**Look**
- [ ] `look="soft"`: matte PLA (roughness 0.8), a high, wide key light, so there are no long or
      stray shadows.
- [ ] `horizon_rgb` set so the background matches the floor (1.22 with the soft look). Check
      a frame for a band at the top.
- [ ] No flicker: no two parts share a face exactly. For the video only, draw one of them a
      hair smaller (`fold_stand_v2.py`'s `fixed()`); never change the real part.
- [ ] Show the product in use where it has one: a phone on a stand, a hand-sized prop. Anything
      drawn for the video is labelled RENDER and is listed in SCRIPT_v2.md.

**Truth**
- [ ] RENDER or REAL on every shot, PLACEHOLDER on a slate. Every number still traces to the
      product's FACTS/ENGINEERING notes, with its source listed in SCRIPT_v2.md.
- [ ] Real footage wherever it exists, cropped to fill 9:16.
- [ ] If there's no real shot of the finished product yet, leave a `placeholder` slate saying
      exactly which clip goes there. A video with a placeholder isn't postable: SCRIPT_v2.md and
      STATUS.md say so.
- [ ] No names on screen: "us", "our", "here at OBC".
- [ ] Look at frames from every shot before the full render (a 360 × 640 preview of each), and
      watch the cut before calling it done.

## Versions come from git, not from memory
To show how a design changed, export each version from the commit where it was current (see
`gingerbread_tin/export_versions.py`): the repo's own source at that commit, not a remodel. Name the
commit for every version in SCRIPT.md.

## Colours
Give Blender the design's own hex colours converted to linear (`gingerbread_tin.py`'s `lin()`).
Passed as screen values, the red tin rendered pink.

## Truth rules (the shop's first rule applies to video too)
- A render is labelled a render. Real footage is labelled REAL and is Scott's own.
- Every number on screen comes from the product's FACTS.md, ENGINEERING notes or checks, and
  SCRIPT.md says which.
- A shot shows what its caption says. The pilot's first draft said "Version 1" over v2's parts
  shown without the keeper; it now says "without a keeper", which is what's on screen.

## Videos
Every video's state is also in `STATUS.md`.

| product | storyboard | status |
|---|---|---|
| Pie Drum Caddy v2 | `pie_caddy_v2.py` | approved 2026-11-26, for Benson to post |
| Gingerbread Tin | `gingerbread_tin/gingerbread_tin.py` (versions from git: `export_versions.py`) | waiting on Scott |
| Fold Stand | `fold_stand/fold_stand.py` (four versions: `export_parts.py`) | waiting on Scott |
| Gear Heart | `gear_heart/gear_heart.py` (gear test, v1, pin test, v2, Scott's real v2 prints) | waiting on Scott; the whole v2 heart isn't printed yet |
| Fold Stand (v2 cut) | `fold_stand/fold_stand_v2.py`, template v2 | waiting on Scott; placeholder for the real stand clip |
| Gear Heart (v2 cut) | `gear_heart/gear_heart_v2.py`, template v2 | waiting on Scott; placeholder for the hand-turn clip |

## Not in git
`out/*/shots/` (rendered frames), `out/*/meshes/`, `out/*/kit/`. Each storyboard rebuilds them.
The finished video, its timeline and SCRIPT.md are committed.
