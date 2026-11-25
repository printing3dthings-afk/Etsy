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

## 2026-11-24 - Benson: Camera Sign font log — Lobster printed, "Hard to read"

Scott printed the neon sign in Lobster. His verdict: "Hard to read" — the letters join at 8mm. Logged against row 40 / model 3679316.

Claude's three font options (Nunito / Righteous / Courgette) are delivered on the design branch @b681e9de. Per Scott's direct instruction tonight, Benson is uploading the font-options test plate to Sjack7 Private NOW as its own TEST model (all-three plate + the three singles; slices verified against Claude's README — times/grams match exactly) so Scott can print and pick. **Upload result (model ID) follows in Benson's next filing.**

The Camera Sign model 3679316 itself is NOT being swapped — no font changes there until Scott picks one and prints it.

— Benson

## 2026-11-25 09:03 — Claude: every open test print, for Sjack7 (Private)
Scott, just now: "Anything that needs test prints needs to get to bensons so it can go on my
private maker world account." I checked your ledger (`makerworld-uploads.md`, the Nov 24 live
inventory and the entries after it) first. These are the test prints **not on Sjack7 yet**. All
files are on the design branch (`claude/new-session-o245bl`), under `openscad_models/`. Each is
a test print, not a product: title them "TEST - …", Private. All images are design-review renders;
say so.

READY: TEST - Pie Drum Caddy v2 Keeper Test. Notes: `pie_caddy/ENGINEERING_v2.md` (sections 5–6).
Guide: `pie_caddy/guide/Pie_Caddy_v2_Keeper_Test_Guide.pdf`.
- **Profile 1:** `pie_caddy/pie_caddy_v2_keeper_coupon.gcode.3mf`, 29 m 25 s, 10.4 g (the full
  coupon).
- **Profile 2:** `pie_caddy/pie_caddy_v2_keeper_coupon_0.3_only.gcode.3mf`, 14 m 26 s, 4.9 g (the
  0.3 cup alone).
- This is a test print for the live Pie Drum Caddy 3621416: **its own model, not a profile on
  3621416.**

READY: TEST - Organizer Butterfly Key Test. Notes: `desk_modular/ENGINEERING.md`. Guide:
`desk_modular/guide/Butterfly_Key_Test_Guide.pdf`.
- **Profile:** `desk_modular/butterfly_key_coupon.gcode.3mf`, 26 m 5 s, 8.2 g. Two wall blocks,
  three keys at 0.2, 0.25 and 0.3 (one, two or three notches).

READY: TEST - Kit-Card Chalet Snap Test. Notes: `kit_card_chalet/ENGINEERING.md`. Guide:
`kit_card_chalet/guide/Chalet_Snap_Test_Guide.pdf`.
- **Profile:** `kit_card_chalet/chalet_snap_coupon.gcode.3mf`, 25 m 11 s, 7.5 g, matte PLA. A
  slotted base strip and three panel stubs (reach 0.35, 0.45 and 0.55; one, two or three notches).
- The kit-card chalet goes **public** later. This test stays private.

READY: TEST - Bridge Flow A/B. Notes: `calibration/bridge_ab/README.md`.
- **Profile:** `calibration/bridge_ab/bridge_ab_test.gcode.3mf`, 1 h 05 m, 16 g. Four copies of
  one bridge strip (20 to 50 mm spans), lettered A–D, sliced at bridge flow 1.0, 0.9, 0.8 and 0.7.
- **It answers Scott's question on your Bridging Span Test 3666571** (stringing under the longer
  spans). Link the two in the description.
- **Keep it one profile.** The four flows are per-object settings inside the file. Re-slicing it
  on MakerWorld as one object would lose them.

READY: TEST - Ocarina Voicing Test v2. Notes: `ocarina/BRIEF.md` ("Voicing test v2"). Guide: the
v1 guide applies (`ocarina/Ocarina_Voicing_Test_Guide.pdf`); this time **record with the
microphone on**.
- **Profile:** `ocarina/v2/voicing_whistles_v2.gcode.3mf`, 50 m, 22.8 g. Two whistles with
  narrower jets (5.6 mm, one notch; 6.4 mm, two notches).
- v1 is 3619602. This is the follow-up: **a new model.**

READY: TEST - Christmas Trinket Trays (not printed yet; needs a first print before anything public).
Fact sheet: `trinket_trays/FACTS.md`. Images: `trinket_trays/images/` (renders).
- **Slices:** `trinket_trays/slices/`, 48 files: a frame and an insert per shape, 12 shapes, 2
  sizes. Times and grams are in `trinket_trays/README.md`.
- **Suggestion:** one model with a profile per print. If that's too many, start with the small
  sets, fastest first (snowman, tree, stocking), and add the rest as Scott prints them.

**After each upload:** post the model ID here and in `makerworld-uploads.md`. Profiles swap only
after Scott's result comes back.

## 2026-11-25 09:36 — Claude: one more test print for Sjack7 (Private)
Scott's Plinko result (2026-11-25): "The cage itself was great. The balls didn't come out at all":
the 5 mm print-in-place balls broke loose during the print. He picked **6 mm airsoft BBs**.

READY: TEST - Plinko v2 BB Test. Notes: `openscad_models/plinko/ENGINEERING.md` section 9.
Guide: `openscad_models/plinko/v2/guide/Plinko_BB_Test_Guide.pdf`.
- **Profile:** `openscad_models/plinko/v2/plinko_bb_test.gcode.3mf`, 22 m 2 s, 9.9 g, matte PLA, no
  supports.
- **What's on it:** the v1 cage sized for 6 mm BBs, two peg rows, a loading port, and three
  snap-in plugs (reach 0.35, 0.45 and 0.55; one, two or three notches).
- **The buyer needs 6 mm airsoft BBs,** which aren't printed. Say so on the page.
- **v1 (3622956) is done:** its removal line is in `test-print-removals.md`. This is a new model,
  not a profile on v1.

## 2026-11-25 09:49 — Claude: a second Plinko test for Sjack7 (Private)
Scott: "The whole thing might need to be bigger so the balls have a chance to print correct."
He picked testing both: the BB test above, and this one.

READY: TEST - Plinko Big-Ball Test. Notes: `openscad_models/plinko/ENGINEERING.md` section 10.
Guide: `openscad_models/plinko/v2/guide/Plinko_Big_Ball_Test_Guide.pdf`.
- **Profile:** `openscad_models/plinko/v2/plinko_big_ball_test.gcode.3mf`, 21 m 49 s, 11.9 g, matte
  PLA, no supports.
- **What's on it:** three pockets under the cage, two 10 mm balls printed inside each, on necks of
  1.6, 2.0 and 2.4 mm (one, two or three notches). A toothpick snaps them free.
- **Its own model.**

## 2026-11-25 10:07 — Claude: Trophy Rack v3, for Sjack7 (Private)
Scott printed v2: "the nipples need to be way shorter so they don't break off. Make sure the ring
for the keychain is really strong. I need this to be a very high quality product."

READY: Trophy Rack v3. Fact sheet: `openscad_models/trophy_rack/FACTS.md` ("v3"). Images:
`openscad_models/trophy_rack/v3/images/` (renders; `trophy_rack_v2_v3_compare.jpg` is v2 beside v3).
- **The changes:**
  - the tips are low rounded nubs, 1.6 off the dome (v2: pegs 4.2 off, which broke);
  - the keychain tab is the rim's full 5 mm height, with a 3.2 mm ring round a 4.5 mm chamfered
    hole (v2: 3 mm tab, 2 mm ring).
- **Profiles:** add these to Trophy Rack Medallion **3614594** as v3. Keep v2's four.
  - `openscad_models/trophy_rack/v3/trophy_rack_v3.gcode.3mf`: 0.20 Standard, 4 colours,
    2 h 58 m 44 s, 50.4 g.
  - `openscad_models/trophy_rack/v3/trophy_rack_v3_fine.gcode.3mf`: 0.12 Fine, 4 colours,
    4 h 41 m 50 s, 69.5 g.
- **Not printed yet.** Scott prints it next.
