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
| product | storyboard | status |
|---|---|---|
| Pie Drum Caddy v2 | `pie_caddy_v2.py` | approved 2026-11-26, for Benson to post |
| Gingerbread Tin | `gingerbread_tin/gingerbread_tin.py` (versions from git: `export_versions.py`) | waiting on Scott |

## Not in git
`out/*/shots/` (rendered frames), `out/*/meshes/`, `out/*/kit/`. Each storyboard rebuilds them.
The finished video, its timeline and SCRIPT.md are committed.
