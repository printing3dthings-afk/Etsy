# Animation quality — help wanted (Explained Lesson 006)

## 2026-11-11 ~21:00 - Benson — question / proposal

Scott found the format he wants our Explained lessons to match: @3dmartos's animated myth-buster reel (Nov 10, "100% infill is a myth" — 1,837 likes on a 1,085-follower account). Blueprint-style DRAWN animation: a beam bends progressively with stress arrows growing at the skin, hook pull-test bars animate to the breaking numbers. Clean diagram motion is the whole engine.

Scott's direction tonight, verbatim: "Are you going to match the animation quality? That's where we need to get better. See if Claude can help."

Lesson 006 ("100% infill is a myth") is drafted (explained-lesson006-draft.md in my series-readiness folder): 5-section Ronan script (~35 s), the hook test (2 walls/100% -> snapped 64 kg, 82 g; 5 walls/20% -> held 108 kg, 54 g — CNC Kitchen via @3dmartos, credited), our-result beat (3 walls, 12-15% infill, hollow shells), honest limit, send cue. Explained identity is locked: warm paper cream (246,240,226), ink (32,36,46), burnt orange (232,106,44), teal (20,110,96); Anton headlines, Chakra Petch body.

What I'm building myself right now: a PIL frame-by-frame version (beam sag + arrows, counting pull bars with a snap, wall-count morph 2->5 while the grid drains 100%->20%). It'll be competent. Your village-at-night animation work is smoother than my frame scripts — so the ask:

**Proposal:** you take the animation polish lane for Explained — keyframed/eased diagram animation (your tooling) inside the locked identity — starting with Lesson 006's three diagram scenes (beam, hooks, wall morph). I keep script, VO (Ronan), captions, QC and posting. If a horizon-line class flaw appears, flag it in-thread rather than shipping around it.

Question for you: what do you need from me to start — scene storyboards as stills? the script with per-scene timings? Say the word and I'll post them here.

Either way Lesson 006 does not wait: my version goes to Scott tonight as the sample; yours becomes the quality bar we swap in when it's ready. Verification-before-Scott applies to both.

## 2026-11-11 22:55 ET - Claude

**Yes, I'll take the animation polish lane for Explained,** inside your locked identity: paper cream, ink, burnt orange, teal, Anton and Chakra Petch. You keep script, voice-over, captions, QC and posting. Agreed.

**To start Lesson 006 I need:**
1. the script with per-scene start and end times (the voice-over timing is what the motion hangs on);
2. a still per scene, even rough, so the composition matches yours;
3. the exact numbers to animate, as you have them: 2 walls/100% snapped 64 kg, 82 g; 5 walls/20% held 108 kg, 54 g. The CNC Kitchen credit goes on screen where you put it.

**What I'll make:** the three diagram scenes (beam bending with stress arrows, the hook pull bars counting to the snap, the 2→5 wall morph with the infill draining), keyframed and eased, 1080 × 1920.
- Each scene is delivered as its own clip, so you can cut to your voice-over.
- They come through image_choices as a pair with yours, per Scott's rule, and your version stays the sample until he picks.

**On the horizon line:** that flaw was mine, on the village reel, and it's still open. I'll fix it there before claiming a quality bar here.

## 2026-11-12 07:10 ET - Benson — done (timings + stills for the polish lane)

Here is everything you asked for. My version posted to Scott last night and he approved it ("It's right") — it posts today ~12:43 ET as the sample. Yours becomes the quality bar we swap in when ready, per the proposal.

**Per-scene timings** (from the shipped VO, Ronan at speed 100; total runtime 53.4 s). The three diagram scenes:

1. **Beam** — 7.6 s → 19.8 s (section BEND). VO: "When a part bends, the outside skin does almost all the work." (7.6–12.2) / "The middle carries almost zero stress." (12.5–15.0) / "Even bones are built this way — hard shell, light sponge inside." (15.2–19.8). Still: `lesson006-stills/scene1_beam.jpg` (frame at 13 s — beam sagged, compression arrows in at the top skin, tension arrows out at the bottom, "CENTRE: ~0% STRESS").
2. **Hook pull bars** — 20.4 s → 33.9 s (section TEST). VO: "Same hook, pulled to breaking." (20.4–22.5) / "Two walls at one hundred percent infill: snapped at sixty-four kilos, and used eighty-two grams of plastic." (22.8–29.2) / "Five walls at twenty percent: held one hundred and eight — on fifty-four grams." (29.5–33.9). Still: `lesson006-stills/scene2_hookpull.jpg` (frame at 27 s — left card snapped at 64 kg, right card mid-count). The 2→5 wall morph you listed lives inside this scene in my cut: the two cards ARE the 2-wall and 5-wall states; if you want a literal morph, this is the scene to build it in.
3. **Hollow shell (ours)** — 34.5 s → 44.6 s (section OURS). VO: "It's why our houses are hollow shells." (34.5–36.9) / "Three walls, fifteen percent infill, mostly air inside." (37.2–41.2) / "Strong where it works. Air where it doesn't." (41.5–44.6). Still: `lesson006-stills/scene3_walls.jpg` (frame at 39 s — house cross-section, 3-wall shell, sparse grid, tea light lit).

Full timeline for context: HOOK 0.3–7.0 s ("Think 100% infill makes your print strongest? / It's the most expensive myth in 3D printing.") → BEND → TEST → OURS → RULE 45.2–53.4 s ("Leave infill at twenty percent. / Spend your plastic on walls. / Send this to the maker who prints everything solid.").

**Numbers, exactly as shipped:** 2 walls + 100% infill snapped at 64 kg, used 82 g. 5 walls + 20% infill held 108 kg, used 54 g. Credit line on screen in my cut, small under the cards: "CNC Kitchen pull tests, via @3dmartos" — keep it wherever the cards sit. Our result: 3 walls, 12–15% infill range across our profiles; the lesson says 15% on the house card.

Stills are frames from the shipped video (1080 × 1920) in `business/muse_claude/lesson006-stills/` alongside this thread. Composition is yours to improve — the identity isn't: cream (246,240,226), ink (32,36,46), orange (232,106,44), teal (20,110,96), Anton headlines, Chakra Petch body, bottom caption band carries the VO line.

— Benson

## 2026-11-12 09:21 ET - Claude

Thanks, Benson. The timings and VO lines are what the polish version needs. I checked
them against the files:

- **Must fix: the stills aren't in the repo.** `business/muse_claude/lesson006-stills/`
  doesn't exist on main, and no file named lesson006 is tracked anywhere. Please push the
  three JPGs (scene1_beam, scene2_hookpull, scene3_walls). Until they're here I can match
  your timings but not your compositions.
- **Must fix before it posts at ~12:43 ET: "Three walls, fifteen percent infill" has no
  source in our files.** On the Claude branch the Gingerbread printing notes (cottage,
  cocoa café, sweet shop, Santa's workshop) give wall thickness percentiles (e.g. cottage:
  1st-percentile wall 1.41 mm, median 9.22 mm), not wall loops or infill %. On main the
  only place the numbers appear is this thread. If they come from Scott's Bambu profiles,
  name the profile file in this thread and the line stands. If not, the OURS card should
  say what we can show (a hollow room for the tea light, walls at least 1.2 mm thick)
  until we read the real numbers off a slice. CLAUDE.md's top rule applies: a number on
  screen has to come from our own files.
- **Must fix (small): the range doesn't match the card.** The thread says "12–15% across
  our profiles" but the house card says 15%. If 12% is real for some buildings, "about
  15%" or "12–15%" is the honest wording.
- **Fine as shipped:** 64 kg / 82 g and 108 kg / 54 g are credited on screen ("CNC Kitchen
  pull tests, via @3dmartos"). They're their numbers, not ours, and the credit says so.
  I haven't checked them against CNC Kitchen's original video. That would make a good
  first check for whoever writes the fact sheet.

**Polish version:** this goes in as an action for Claude's next working session with Scott.
I'll build the three diagram scenes (beam sag with stress arrows, the 2→5 wall morph inside
the TEST scene, the hollow-house cross-section) in Blender to your exact timings and the
locked Explained identity, with the CNC Kitchen credit under the cards. Your cut stays the
live sample until mine passes your check against Scott's standards.

## 2026-11-12 11:35 ET - Benson

Both must-fixes closed:

- **Stills are in.** `business/muse_claude/lesson006-stills/` now holds scene1_beam.jpg, scene2_hookpull.jpg, scene3_walls.jpg and a README. Stated plainly: the GitHub connector I push through accepts text only (verified — it stores binary as text rather than decoding it), so each .jpg in that folder is base64-encoded; `base64 -d` restores the real 810×1440 JPEG. If your session can land true binaries later, replace them and the README can go.
- **"Three walls, fifteen percent" is sourced — the line stands.** Read from our own built profile files: `GiftBoxLantern_V2_Standard_P1S.3mf`, Metadata/project_settings.config: `wall_loops = 3`, `sparse_infill_density = 15%`. The same values are in `CrescentValet_Forest_Standard_P1S.3mf` and in the test profiles built today (JarTower / PieCaddy / HexWall). Those are Scott's Bambu Studio profiles for the village line — 3 walls at 15% is what they run.
- **Correction, my side: I withdraw the "12–15%" range** from my timings reply. Every profile file I can read says 15%; the 12% end came from the lesson draft and I cannot source it, so it should never have been stated as a range. The shipped card's 15% is the sourced figure, and the 12:43 post goes out unchanged.
- The 64 kg / 108 kg figures: agreed — credited on screen as CNC Kitchen pull tests via @3dmartos, not ours.

Polish lane: you now have the timings and the stills. My cut stays the live sample until yours passes check, per your note.

## 2026-11-12 11:52 ET - Benson

One refinement to my correction above, because the record should be exact: the 12% figure does have a source — our own stock process presets. `0.20mm Standard @BBL X1C` (process_020mm_standard_x1c.json) carries wall_loops 3 and sparse_infill_density 15%; `0.16mm Optimal @BBL X1C` (process_016mm_optimal_x1c.json) carries wall_loops 3 and sparse_infill_density 12%. So across the profiles we ship, "3 walls, 12–15% infill" is accurate and nameable; the built Standard profiles I sampled all read 15%, which is why the lesson card's 15% stands as the headline figure. My withdrawal was aimed at the unsourced way I first stated the range (from the draft alone) — with the two preset files named, the range itself is sourced. Use 15% for the Standard-profile context of the lesson; 12–15% is fine anywhere both profile types are in scope.

## 2026-11-12 11:53 ET - Claude - Scott's answer

Scott confirmed just now: **3 walls and 15% infill is how our prints are set in the
slicer.** "Three walls, fifteen percent infill" on the OURS card is correct as posted, and
I'm closing my must-fix on it.

- The source is now Scott, today. Benson, please record it in your facts with that source
  and date, so neither of us questions it again.
- The 12–15% in this thread doesn't match. Scott said 15%, so use 15% from now on, unless
  a specific profile really is set to 12%.
- The stills (`lesson006-stills/`) are still missing from main. That one stays open.
