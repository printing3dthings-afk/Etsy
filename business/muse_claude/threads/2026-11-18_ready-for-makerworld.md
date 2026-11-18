# Ready to print or test print: for MakerWorld (2026-11-18)

**Status: OPEN.** Claude to Benson.

**Scott:** "I need everything you have ready to print or test print pushed so benson can
upload it to makers world."

Everything is on branch `claude/new-session-o245bl` at commit `480e5b59`, pushed. Paths are from the repository root.
Fetch with `git fetch origin claude/new-session-o245bl`.

**Rules for all of these:**
- **Private until Scott's test print is checked** (your G5). None of the new ones is
  printed yet.
- **Your own profile's numbers win.** Build your profiles from the 3MF, and quote the time
  and grams your profile slices to. My slices are at Claude's settings (P1S 0.4, PLA Basic,
  0.20 mm, 3 walls, 15%), for reference.

## New designs: READY lines (STANDARDS 12)

READY: Openwork Name Ornament v1. Fact sheet:
`openscad_models/christmas_ornaments/name_ring/FACTS.md`. Media kit:
`openscad_models/christmas_ornaments/name_ring/images/`.
- **Model:** `name_ring.3mf`, 2 colours.
- **Slice:** `gcode/name_ring_two_colour.gcode.3mf`, 47 m, 11.7 g.
- **Customizer:** `pmm/name_ring_pmm.scad`. Auto Arrangement must be **on** in the
  profile (`tools/pmm_build.py`, rule 3).
- **Replaces the domed Name Ornament.** Scott's dome test print came out lumpy; don't upload
  the dome again.

READY: Snow Globe Name Ornament v1. Fact sheet:
`openscad_models/christmas_ornaments/name_globe/FACTS.md`. Media kit:
`openscad_models/christmas_ornaments/name_globe/images/`.
- **Model:** `name_globe.3mf`, 3 colours.
- **Slice:** `gcode/name_globe_three_colour.gcode.3mf`, 1 h 4 m, 17.1 g.
- **Customizer:** `pmm/name_globe_pmm.scad`, Auto Arrangement **on**.

READY: Urban Kid v2 head test (a test print, not a product). Fact sheet:
`openscad_models/urban_kid/v2/head_test/HEAD_TEST.md`. Images: the same folder.
- **Slice:** `urban_kid_v2_head_test.gcode.3mf`, 37 m, 11.7 g, 0.12 mm.
- **Re-sliced today at 3 walls.** It was 33 m and 10.2 g.

READY: Gap Gauge v1 (a workshop tool). Fact sheet:
`openscad_models/camera_sign/GAUGE_FACTS.md`. Guide: `openscad_models/camera_sign/guide/Gap_Gauge_Guide.pdf`.
- **Slice:** `openscad_models/camera_sign/gcode/gap_gauge.gcode.3mf`, 27 m, 8.3 g.
- **Whether it goes on MakerWorld at all is Scott's call.** It was made to measure his P1S.

## Re-sliced today at 3 walls, all Handy-safe: for profiles of models already up
Numbers and sources are in each folder's notes or FACTS.md.
- **Tin Clicker:** `openscad_models/clickers/gingerbread_tin/checks/`
  - `tin_clicker_one_colour`: 1 h 33 m, 35.3 g;
  - `tin_ams`, `lid_ams`, `cookie_ams`;
  - `clickers/MAKERWORLD.md`'s Tin Clicker line is corrected.
- **Dumpling Clicker:** `openscad_models/dumpling_clicker_slices/`
  - one colour: **34 m**, 12.1 g;
  - AMS: 4 h 30 m.
  - See `threads/2026-11-18_three-walls-reslice.md`; it corrects OPEN row 1.
- **Ladder Mouse:** `openscad_models/bookmark_mouse/checks/ladder_mouse.gcode.3mf`,
  1 h 22 m, 16.25 g.
- **Jar Tower:** `openscad_models/jar_tower/checks/tower_{jar,cap,foot}.gcode.3mf`. Its
  FACTS.md is new.
- **Trophy Rack:** `openscad_models/trophy_rack/checks/trophy_rack.gcode.3mf`, 2 h 58 m,
  50.1 g. Its FACTS.md is new; it stays **private**, Scott's own.
- **Village, one colour:**
  - Gingerbread ×7: `openscad_models/christmas_village/gingerbread/<building>/gingerbread_<building>_one_colour.gcode.3mf`;
  - Victorian ×8: `openscad_models/christmas_village/victorian/<building>/victorian_<building>_one_colour.gcode.3mf`;
  - Santa's Workshop v2, matte white:
    `.../victorian/santas_workshop/v2/gcode/victorian_santas_workshop_v2_matte_white.gcode.3mf`,
    19 h 8 m.
  - Times: `for_scott/2026-11-17_village-listing-times.md`.

## Sliced 2026-11-17: Handy-safe, but at 2 walls
These are the test prints from yesterday. They're printable, but they're 2-wall slices, so
their quoted times run short of Scott's 3-wall setting. Build your profile from the model
and use its time.

| design | files |
|---|---|
| Birch Log trio | `openscad_models/birch_logs/` |
| Pie Drum Caddy | `openscad_models/pie_caddy/` (base, drum, 6 mm balls) |
| Snowfall Plinko release test | `openscad_models/plinko/plinko_release_test.gcode.3mf` |
| Pocket Top UFO | `openscad_models/pocket_top/ufo_top.gcode.3mf` |
| Chapel drop coupon | `openscad_models/press_chapel/drop_coupon*.gcode.3mf` |
| Technique samplers | `openscad_models/technique_samplers/` (texture, plain and ribbed vase) |
| Urban Kid v1, 6 plates | `openscad_models/urban_kid/gcode/` |
| Wishing Well windlass test | `openscad_models/wishing_well/windlass_test.gcode.3mf` |
| Zero-gap joint coupon | `openscad_models/zero_gap_joint/zero_gap_coupon.gcode.3mf` |
| v2 matte-white swaps | Gingerbread Cocoa Café v2, Victorian Clock Tower v2, Victorian Cottage, and Santa's Workshop v2 four-colour (`.../v2/gcode/` in each) |

## Not ready: don't upload
- **Camera sign** (`openscad_models/camera_sign/`):
  - its thickness is a placeholder until Scott measures the gaps with the gauge;
  - it's for his own printer.
- **Ocarina:** waits on one more voicing whistle (`openscad_models/ocarina/BRIEF.md`).
- **Urban Kid v2 full figure:** waits on your files (`threads/2026-11-17_urban-kid-detail.md`).
- **Leland's Toy Story pieces** (`openscad_models/personal/`): personal, never public.
