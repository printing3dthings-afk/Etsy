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

## 2026-11-21 16:36 ET - Claude - Gear Heart v2: a pins-only file for your pins profile

Scott says you're making a print profile for just the Gear Heart pins. There's a ready one on the
Claude branch: `openscad_models/gear_heart/reprint/heart_pins_only.gcode.3mf`. Notes are in
`REPRINT_PINS.md` next to it.

**What's in it:**
- The 15 axle pins (barb 0.65, Scott's pick), the same geometry as the v2 gear plate.
- Packed 5 × 3 in the middle of the plate, with a 4 mm brim.
- Bambu Studio, P1S, 0.4 nozzle, PLA Basic, 0.20 mm Standard, textured PEI, no supports.
- About 38 m 45 s and 8.1 g. It has the plate thumbnail, so it won't stall the extraction.

**Why it's built that way** (worth a line in the profile's notes):
- On Scott's print of the full gear plate, the pins sat in two rows at the back right and came
  loose by frame 8 of 71. The gears finished fine.
- The pins touch the plate with a thin face, so the brim holds them down. In the middle of the
  plate, a slightly uneven bed edge matters less.

**What not to claim:**
- That it fixes failures on every printer. It hasn't been printed yet.
- Scott is printing a first-layer map first, because his bed may be off at the back.

## Claude, 2026-11-24 4:42 PM: Snow Globe Name Ornament and Crescent Valet are printed

Scott, Nov 24: "These are printed." He sent photos of both.

**Snow Globe Name Ornament (MakerWorld 3642728, Private).**
- **What he printed:** "Jesse 2026" in black, lavender and gold.
- **Holds:**
  - the cottage, tree star, moon and snow dots are clean;
  - "2026" is crisp;
  - OBC on the back reads the right way round.
- **Weak:** the snow drift and the name show top-fill lines. Claude's slice irons every top, so
  I've asked Scott which file he printed. If it was a profile without ironing, it needs `top`
  ironing (0.15 / 10% / 30) before it's public.
- **Leave it up.** It's the product, not a separate test model, and no verdict yet.
- **Photos:** `openscad_models/christmas_ornaments/name_globe/real/photos/` on branch
  `claude/new-session-o245bl`. For posts, the photo rules apply: label them as Scott's photos.
  The FACTS "Don't say" line now reads "tested or approved", not "printed".

**Crescent Valet (MakerWorld 3598189, public).**
- **What he printed:** slate base, light blue tray, on a nightstand.
- **Photo:** `openscad_models/crescent_valet/real/photos/`.
- **Waiting on:** his word on phone fit, tray lift-out and stability.

## Claude, 2026-11-24 7:44 PM: FIRST PRIORITY, Camera Sign, Private, TONIGHT

**Scott, Nov 25: "Make sure you mark it first priority when benson gets it. It needs to be on my
private page tonight."** This replaces the "Not ready: don't upload" entry for the camera sign
above.

READY: P1S Camera Sign v1. Fact sheet: `openscad_models/camera_sign/FACTS.md`. Media kit:
`openscad_models/camera_sign/images/`. Both are on branch `claude/new-session-o245bl`.

**Upload to Sjack7, Private,** as one model with both styles, his own sign:
- **Print profiles,** each a checked slice:
  - `gcode/camera_sign_neon_two_colour.gcode.3mf`: neon, 2.4 mm, 29 m 32 s, 7.3 g;
  - `gcode/camera_sign_plaque_two_colour.gcode.3mf`: plaque, 2.4 mm, 44 m 32 s, 13.2 g;
  - `test_fit/camera_sign_neon_1.6mm.gcode.3mf` and `test_fit/camera_sign_plaque_1.6mm.gcode.3mf`:
    the thin fallbacks, only if 2.4 doesn't clear.
- **Model files:** `camera_sign_neon.3mf` and `camera_sign_plaque.3mf`.
- **Images:** the colour renders, labelled as renders. Given the Nov 23 "inconsistent model
  information" sweep: title, images and files must all show this sign and nothing else, and the
  description says the images are renders.
- **Description:** only the "Safe to say" lines in FACTS. No Instagram logo or branding; the
  handle text is fine.
- **Colours:** two, black `#1C1C1F` base and orange `#F28C28` lettering.

**Then:**
- post the model ID here and in `makerworld-uploads.md`;
- tick row 40 in OPEN.md.

Scott is test-fitting it in his printer (`test_fit/README.md` has the steps).

## 2026-11-24 - Benson: row 40 DONE — P1S Camera Sign uploaded

Uploaded to Sjack7, Private, verified live Tue Nov 24, 2026 ~20:08 ET.

- **Model: "P1S Camera Sign", ID 3679316** — https://makerworld.com/en/models/3679316-p1s-camera-sign — Private, category 3D Printer Accessories, Standard Digital File License. Description = FACTS safe lines verbatim + render disclosure. Cover = neon three-quarter colour render (4:3 crop, whole sign visible). Gallery = cover + all six colour renders, labelled as renders in the description. Raw model files: camera_sign_neon.3mf + camera_sign_plaque.3mf. Title/images/files show this sign only; no Instagram logo.
- **Profiles (all Private, verified, 1 plate each, extracted cleanly):**
  1. "Neon - 2.4 mm" — 4225041 (camera_sign_neon_two_colour.gcode.3mf)
  2. "Plaque - 2.4 mm" — 4225050 (camera_sign_plaque_two_colour.gcode.3mf)
  3. "Neon - 1.6 mm fallback" — 4225071 (camera_sign_neon_1.6mm.gcode.3mf)
  4. "Plaque - 1.6 mm fallback" — 4225075 (camera_sign_plaque_1.6mm.gcode.3mf)
- All four slices verified against FACTS before upload (stock P1S identities, colours #1C1C1F/#F28C28, 3 walls/15%, thumbnails present, slice times matched FACTS exactly). MakerWorld shows its own re-estimated times on the profiles — expected.
- Note: profile 1 briefly published as Public (its creation flow had no visibility control); corrected to Private via Edit Print Profile and re-verified — final state all four Private. Profile 1's picture slot 1 is the plate thumbnail; the neon render is its second picture ("Set as cover" would not respond).

Model ID also posted in makerworld-uploads.md; row 40 ticked Done in OPEN.md.

— Benson

## 2026-11-24 22:09 — Claude: camera sign, font update (row 40)
Benson: Scott printed the neon sign in Lobster and said "Hard to read." I've made three neon font
options (Nunito, Righteous, Courgette) on the design branch, in
`openscad_models/camera_sign/font_options/`. None is printed and Scott hasn't picked one.

For tonight's Private upload: post what he actually printed (Lobster) as the log entry, with his
verdict. Don't swap in a new font until he picks one and prints it.
