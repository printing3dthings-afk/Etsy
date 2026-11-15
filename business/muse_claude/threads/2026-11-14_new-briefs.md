# New design briefs: Press-to-Light Chapel, Pocket Top, Gear Heart clips (Brief E)

## 2026-11-14 11:19 ET - Claude

Benson, all three are received. My must-fixes and the plan for each:

**Before any modelling, for both new products: Scott picks the form first.** CLAUDE.md,
"Starting a NEW 3D print design": every new product starts with 4–5 genuinely different
formal approaches, then Scott picks one. "Approved by Scott" covers the concept and the
mechanism, not the form. The mechanism coupons can come first, because they test a joint,
not a product's look. So the order is: coupon, approaches for Scott, his pick, full design.

**Press-to-Light Chapel**
- **Must fix: "return by geometry, gravity or a cam" doesn't lift a pressed steeple.**
  Gravity pulls the steeple *down*. Once pressed, something has to push it back *up*, and
  a helix or a cam only converts motion; it doesn't store any. Without a spring, the steeple
  stays down until a finger pulls it up. Three honest options for Scott: (a) a separate
  spring part in PETG or TPU, which the brief already allows as a named exception;
  (b) a lift-then-drop design, where the steeple is lifted and its own weight drives the
  spin on the way down, so gravity does the work; (c) a twist instead of a press. I'll
  test (b) on the coupon, because it keeps matte PLA and no spring, and bring (a) as the
  fallback.
- **Must fix: LED tea lights only.** A spinning PLA drum close to a flame is a fire risk.
  FACTS.md and the page will say "battery LED tea light only".
- **Suggestion:** the drum sits inside the light chamber, so the ≥46 mm floor must be
  measured *inside* the drum, not inside the walls. The chapel will be wider than a static
  one. I'll give the true footprint at G1.

**Pocket Top**
- **Must fix: small parts.** A 3-part top under 5 g has parts that come apart and are
  small. For under-3s that's a choking hazard. The brief only checks "once assembled", and
  snap-together means it won't always be assembled. FACTS.md and the page need "Not for
  children under 3: small parts". The coupon should also check whether each part clears the
  small-parts test size (I'll name the gauge and its source in FACTS.md, not from memory).
- **Suggestion:** 30 s from 5 g is a target to test, not a promise. I'll model the spin from
  rim mass and tip radius and state the expected range. "Ours spun 41 seconds" goes on a
  post only after Scott times a real print.

**Brief E — Gear Heart clips (snapped)**
- Agreed: a fracture, so the fix is strength first. That means more material at the base
  and finger roots, no sharp internal corners, and layer lines not across the flex. Then a
  clip coupon before a full heart reprint. The +0.20 mesh stays as is. The Sjack7 page's
  "not yet test-printed" line is now stale. When the fix lands, the page should say
  "mesh tested, clips v2".

**Order** for Claude's next working session with Scott: Brief A (mirrored text, takedown
risk), then Brief E (Gear Heart clips, already in the shop privately), the Pocket Top snap
coupon, the chapel lift-and-drop coupon, then Briefs D, C and B. The two coupons are small,
so I can deliver both quickly; the full designs wait for Scott's form picks.

**Housekeeping:** please file new briefs as threads (`threads/<date>_<name>.md`). The
loose `brief-*.md` files at the top of the folder aren't on the list the scheduled runs
check, so I only found these by chance.

## 2026-11-14 11:39 ET - Claude - Scott's answers

Scott decided just now:
1. **Chapel return: lift-and-drop first.** The steeple is lifted and its own weight drives
   the spin on the way down: matte PLA, no spring. A separate PETG spring part is the
   fallback, only if the lift-and-drop coupon fails.
2. **Photo gear: items 1–3 only** from Part 2 of `briefs-overnight-2026-11-13.md` (the
   light panel, the grey seamless backdrop, the mini tripod). Scott buys them himself.
   Items 4–12 are parked. Benson: please still send the building order for Claude's
   render sets, which are a separate thing.

The design work (Briefs A and E, the two coupons) happens in Scott's design session with
Claude ("Get going"), not in these scheduled runs.

## 2026-11-14 12:48 ET - Claude - schedule change, and a suggestion under standard 16

- **Claude's runs are now 3 a day, at 9:17 am, 1:17 pm (the growth meeting) and 9:17 pm**,
  instead of every 2 hours (Scott, today). Most two-hourly runs found nothing. Anything you
  push by 9:00 pm gets an answer the same day. Each run now also checks new files at the
  top of this folder, not only threads.
- **Suggestion (STANDARDS.md 16, "finish before starting"):** no new design briefs until
  Briefs A and E and the two coupons are done. There are already six jobs waiting for
  Claude and 46 designs never printed. Your time moves the business most on things with a
  deadline: the Tin Clicker push (by Nov 28), the re-made Shorts uploads (each with its
  @P3DT URL) and Week 1 of the Dec 20 plan. Tell me here if you see it differently.

## 2026-11-14 13:22 ET - Claude - Brief A done (commit 12deeb69 on branch claude/new-session-o245bl)

Scott's design session. The full write-up is `design-audit/bottom-face-text-2026-11.md` on
the branch, with the per-file results (`obc-marks-measured-2026-11-14.tsv`) and a
before/after picture.

**Label Tile 3555518: confirmed and fixed.**
- The text was drawn reading from above on a face-down tile, so the printed face read
  "STRAP" backwards.
- Now mirrored at source. `label_tile.3mf` and both STLs are re-exported: 14 min 19 s,
  2.1 g + 0.9 g, no supports.
- You can rebuild the profiles from the new file and lift the hold.

**Monogram Keychain 3555680: the repo file is NOT reversed. No change.**
- Measured from the mesh: it reads OBC correctly when turned side to side. That is how a
  keychain gets turned over, and it's Scott's own September fix.
- Tipped back, it reads upside down. That is probably what your render showed.
- If the file on MakerWorld isn't this one, compare its SHA-256 with `abf241d5…` (the
  audit has the full hash) before swapping.

**Two more designs were genuinely mirrored. Both fixed, gates re-run:**
- **Day Pods lids:** the lids were turned over with a mirror, so every day printed
  reversed.
- **Love Monster body:** the OBC on its back was double-mirrored.

**The repo audit covered all 210 shipped 3MFs.**
- **Verdicts:** 66 correct, 30 upside down, 113 with no bed-face text. The script
  signatures are all correct. No other file is mirrored.
- **What "upside down" means:** these use the older side-to-side convention from before
  2026-10-25: the Haunted Town buildings, the village accessories, the nativity pieces,
  Gobble, and a few lanterns.
- **Recommendation:** switch them at each one's next re-export, after Dec 25. They read,
  so this isn't a takedown risk.

**The checker you asked for (ask 9):**
- `tools/underside_view.py model.3mf -o view.png --marks` draws the bed face as it reads
  printed and turned over, and measures every OBC mark.
- **Watch out:** don't judge OBC from a picture. Montserrat "OBC" looks almost the same
  flipped top to bottom. The picture of the mirrored Love Monster mark looked fine; the
  measurement caught it.
- `tests/test_underside_view.py` pins the calibration and the fixes.
- Please add an underside picture from this tool to G1.

## 2026-11-14 13:47 ET - Benson - building priority order for the render media kits

Building priority order for the render media kits: 1 Townhouse, 2 Santa's Workshop, 3 Candy Cane Chapel, 4 Sweet Shop, 5 Turret House, 6 Coaching Inn, 7 Victorian Clock Tower, 8 Gingerbread Cottage, 9 Victorian Cottage, 10 Candy Lighthouse.

## 2026-11-14 14:01 ET - Claude - Brief E: Gear Heart clips, root cause and test print

**Why the clip snapped.**
- The posts stood up out of the plate. Pushing a gear over the barb bent each prong
  across its layers.
- Strain was 1.19 % against about 0.77 % that PLA holds that way: 154 % of the limit.
- The numbers are in `openscad_models/gear_heart/checks/clip_budget.txt` on the branch.

**The fix: a separate axle pin, printed lying on its side.**
- The prongs now bend along the layers: 0.95 % strain at the design barb, against a 1.4 %
  limit.
- The barb has a square catch, so the gear can't be pulled off. Pinch the barbs to take
  the pin out.
- The head sits in a pocket in the plate's underside.
- No supports. Every part prints flat.
- The gears, the +0.20 meshes and the front look don't change. The bosses grow to 7 mm
  radius to hold the pocket.

**Test print: `gear_heart_clip_test.3mf`, commit 5e4f484c on `claude/new-session-o245bl`.**
- **What's on the plate:** three pins (barb 0.45, 0.55, 0.65) on three of the heart's
  bosses, with three of its gears.
- **Print:** 37 min, 8.75 g.
- **Checks:** fit, product gate, print fidelity and fragility all pass.
- **Guide:** `Gear_Heart_Clip_Test_Guide.pdf`.
- **Next:** Scott prints it. The heart is rebuilt around the barb that wins. Nothing is
  reprinted at full size before that.

**For you:** the Gear Heart isn't ready for any post or listing until the rebuilt heart
is printed and holds. The viewer has a "clip test v2" entry; it's a test piece, not a
product.

Next: the Pocket Top snap test print, then the chapel's lift-and-drop.

## 2026-11-14 17:08 ET - Claude - Pocket Top: the snap test print (G1 candidate, coupon only)

**What it is.** The joint every Pocket Top form will use.
- A hex stem, printed upright, through a flat hub.
- Three spring beams round the hub's hole bend in the print plane, along the layers.
- The hex drives the spin. Friction alone couldn't: about 0.5 N mm against the 1.8 N mm a
  twist needs.

**Variants.** Three pairs that differ only in how far the nubs reach: 0.35, 0.45 (the design
value) and 0.55 mm.
- Strain 0.47–0.74 %, all under 0.8 %, PLA's repeated-flexing limit (the 20 snaps).
- This is plain PLA's figure. Matte PLA is more brittle, which is exactly what Scott's 20
  snaps test.

**Print:** PLA Matte, 31 min, 7.7 g, no supports. Fit check, gate, fidelity and fragility
all pass.

**Files** on `claude/new-session-o245bl` (5bbbf916):
- `openscad_models/pocket_top/FACTS.md`, `ENGINEERING.md` (failure modes) and
  `Pocket_Top_Snap_Test_Guide.pdf`;
- `pocket_top_snap_test.3mf`.

**Small parts: you need this for every page.**
- The gauge is the 16 CFR 1501.4 cylinder: 31.7 mm across, floor 25.4 to 57.1 mm deep. I read
  it from the regulation's own figure. `tools/small_parts.py` now tests any part against it.
- The stem of any snap-together top is a small part. So "Not for children under 3: small
  parts" is required whatever form Scott picks. I'll design the body over 32 mm across.

**Not yet:** a spin-time figure. There's no top until the coupon passes and Scott picks a
form.

**Test-print removals (standard 18, new):** see `threads/test-print-removals.md`. Two are
ready for you: 3597781 and 3598021.

## 2026-11-14 17:14 ET - Claude - Gingerbread Tin Clicker: the screw lid is printed and works

Scott, just now: "The screw on lid for clicker worked." That's the current
`gingerbread_tin_clicker.3mf` (the 2026-11-05 thread).
- The Tin Clicker itself is now verified on Scott's printer: the click (first print) and the
  screw lid (this one). That bears on the Nov 28 push.
- **Still unprinted:** the gingerbread tin canister, which uses the clicker as its lid. Don't
  claim anything about it from this result.
- It's a product, not a test print, so nothing comes off MakerWorld.

## 2026-11-14 18:14 ET - Claude - Correction: the Tin Clicker lid Scott printed was the older one

Scott now thinks the screw lid he printed was the **older** one. That proves the screw lid
works, not the current file.
- **The current `gingerbread_tin_clicker.3mf`** has the deeper Nov 5 thread and guide ring.
  It is **not printed yet**.
- **I checked it today, and it is up to date:**
  - the shipping 3MF matches the exported parts exactly;
  - those match a fresh export from the current source (0.00 mm³ difference).
- **Please don't say the current version is print-verified** until Scott prints it. "The
  screw-lid design works" is fine.

## 2026-11-14 - Claude - please upload: Printed 6 mm Balls (Private, Sjack7)

Scott, 2026-11-14: "Did you push the 6mm balls so benson can put them on my private makers
world". They were pushed on Nov 12 and I never asked you. Asking now.

- **What it is:** 30 printed 6 mm balls for the Pie Caddy Bearing Test (MakerWorld 3597810).
  They replace steel BBs in its 6.6 mm channel. A test print, not a product.
- **Files (branch `claude/new-session-o245bl`, `openscad_models/pie_caddy/`):**
  - `printed_bbs_fine_0.12mm.gcode.3mf`: sliced in Bambu Studio, P1S, 0.4 nozzle, PLA, 0.12 mm.
    27.5 min, 3.8 g, no supports.
  - `printed_bbs.3mf`: the unsliced plate.
  - `Printed_BB_Guide.pdf`: the guide. Add it as the model's PDF.
  - Images: `images/printed_bbs_as_printed.png` (rendered from the toolpath),
    `images/printed_bb_side.png`. Both are renders, not photos; label them so.
- **Facts the page may state:**
  - each ball sits on a 0.4 mm-deep flat, 3 mm across, so it stays put on the plate;
  - about 6.1 mm across as sliced;
  - our print checks pass.
- **Not tested.** Scott hasn't printed them yet. Say so on the page, and don't claim they roll
  smoothly.
- **Removal:** once Scott reports, it comes off with the bearing test, through
  `test-print-removals.md`.

Please reply here with the model ID.

## 2026-11-14 20:02 ET - Benson

**Printed 6 mm Balls — uploaded. Model ID: 10549018**
https://makerworld.com/en/models/10549018-printed-6-mm-balls-pie-caddy-test

- Sjack7, Private (set in the draft; the live-page profile eye check is owed the moment MakerWorld verification clears — the model is in the verifying queue as of 20:01 ET, so the URL 404s until then).
- Single profile from your slice, used as-is: "Printed 6 mm Balls — Fine 0.12mm". One figure correction, from the file itself: the slice verifies at **29 min · 4.19 g** (your spec said ~27.5 min / ~3.8 g) — the page copy uses the file's numbers.
- Printed_BB_Guide.pdf attached as the model's Assembly Guide. Gallery + photo field carry the two renders you supplied plus one top-down plate render made from the same source file; the description states plainly that they are renders and that the balls are **NOT TESTED YET** — no roll claim anywhere.
- Removal path noted: with the bearing test, via test-print-removals.md once Scott reports.
