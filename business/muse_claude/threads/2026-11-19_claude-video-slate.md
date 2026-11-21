# Claude video slate — Explained finished videos, 16 topics (Scott's commission, Nov 19; production terms updated Nov 20)

**From:** Benson · **To:** Claude · **Date:** 2026-11-19 · **Updated:** 2026-11-20

**Update — 2026-11-20:** Scott decided today: *"Claude now will make all animations and videos for social media."* That decision changes the production terms in this thread: instead of diagram scenes for Benson to cut, you now deliver **finished, post-ready videos** — full animation, edit and audio. The workflow and spec below are rewritten to the new terms; the 16 topics and their misconception hooks are unchanged.

## Why this exists

Scott's verdict on Lesson 006 is in: your three diagram scenes replaced the Nov 12 animated version. The re-cut — claim-checked under STANDARDS 14, caption corrected to "34% less plastic" — replaced the live posts on Nov 19 on Scott's direct order. Your format is now the house format for these lessons — and as of Nov 20 (see the update note above) you own the whole production: animation, edit and audio, delivered finished.

So Scott is commissioning a full slate: **16 topics**. He asked for "a lot of different videos" from you — this is that list, approved by him in chat on Nov 19, with the production terms updated Nov 20.

## Division of labour (new terms, Nov 20)

1. **Claude makes the videos** — finished, post-ready files: full animation, edit and audio, built to the spec below. No scene clips for Benson to cut.
2. **Benson claim-checks** every number in each video against its notes file (STANDARDS 14), **QCs the finished file** (frames, burned-in text, audio levels), and **posts after Scott's approval**. Nothing goes live unapproved.
3. **Scott approves the first finished video as the sample** before the batch rhythm starts — one video worked to the bar, then the batches roll.

## Deliverable spec per topic — one finished video

- **One finished, post-ready video**, 1080×1920 vertical, **~45–60 s** for Explained lessons, following the lesson beats: the false belief → the proof/test → our way.
- **Misconception-first open:** the false belief is on screen in picture AND in the first spoken line at frame 1, then one proof beat, then the verdict in the series' existing treatment.
- **Labels-only burned-in text:** short labels beside the thing named, plus the claim/verdict — never full sentences duplicating the narration. The **full transcript ships as a caption/sidecar file** alongside the video.
- **Audio mastered to −14 LUFS / −1 dBTP.** Music sits at least 12 dB under any voiceover and drops out entirely under teaching beats.
- **A notes file naming the SOURCE for every number or test result shown.** The claim check needs the source chain (e.g. "CNC Kitchen pull tests, via @3dmartos"). Unattributed numbers will be sent back — if a figure can't be sourced, don't put it on screen; show the mechanism instead.

## Delivery

- In **batches of 2–3 topics**, each batch dropped in `business/image_choices/` with a `CHOICE.md`, like the Lesson 006 drop (`2026-11-18_lesson006-diagrams`): per topic, the finished video, its transcript sidecar and its notes file.
- **First batch: topics 1–3** (layer direction, overhangs, bridging). Sequence the rest as suits the work.

## The 16 topics

Each line is the topic plus the misconception it opens on.

1. **Layer direction** — "Prints are equally strong in every direction" (they split along layers, not across them)
2. **Overhangs** — "Any angle prints the same" (why ~45° stays clean, steep angles collapse, what part cooling really does)
3. **Bridging** — "You can't print over open air" (how a bridge is drawn, tension + cooling)
4. **Warping** — "Corners lift because the bed isn't sticky enough" (shrinkage vs adhesion, layer by layer)
5. **Stringing** — "Stringing means the nozzle is too hot" (what retraction actually does inside the hotend)
6. **Z-seam** — "The seam scar is a defect you can tune away completely" (why every print has one; hiding vs removing)
7. **Elephant's foot** — "The first layer is supposed to squish out" (what the flare is, the small offset fix)
8. **Supports** — "Overhangs always need supports" (designing support-free; when supports are genuinely needed)
9. **Top & bottom layers** — "Infill % is the strength dial" (the solid skins carry the load — companion to Lesson 006, distinct test)
10. **Layer height** — "Finer layers are just slower and prettier" (0.12 vs 0.28: time, looks, and the counterintuitive strength difference)
11. **Speed vs strength** — "Faster printing, same part" (what happens to extrusion and bonding at speed)
12. **Heat** — "A finished print is solid plastic, it can't melt on a dashboard" (glass transition; PLA softening ~60 °C)
13. **Wet filament** — "Filament doesn't care about humidity" (steam, popping, rough walls from moisture)
14. **Bed adhesion helpers** — "A raft fixes adhesion" (brim vs skirt vs raft — what each one actually does)
15. **Part cooling** — "More fan is always better" (why PLA wants full fan and other filaments don't)
16. **Flow rate** — "Wall thickness is set by the model" (over/under-extrusion: why walls measure fat or thin)

## Closing notes

- Lesson 006's replacement posts went live Nov 19 with your scenes; the new links are confirmed in the Lesson 006 thread.
- No reply needed on format. **Do flag any topic where the physics can't be shown honestly in an animation** — we'd rather rework a topic than ship a video that fudges the mechanism.

— Benson

---

## 2026-11-20 21:18 ET - Claude (scheduled run)

Good slate, and the misconception-first spec is right. Two places conflict with Scott's later
decision (STANDARDS 21, `1dd98eb` and `a809175`), and four topics need reframing before anyone
animates them.

### Must fix: where this thread disagrees with STANDARDS 21
1. **Audio.** Your update says Claude delivers "full animation, edit and audio", mastered to
   −14 LUFS. Scott decided afterwards, on Nov 20, that **Benson adds the voice-over and music when
   posting**. Claude delivers a clean cut plus a timed script. So the loudness spec is yours to meet
   at mix time, not Claude's.
2. **Delivery.** Your slate says batches go into `image_choices/` with a CHOICE.md. STANDARDS 21 says
   **videos go into `video_queue/`** and skip the pick-one protocol. Scott approves each video before it
   posts. Lessons 007 and 008 are already there.

### Topics to reframe (honest physics, as you asked)
- **5. Stringing.** "Stringing means the nozzle is too hot" isn't a misconception. Temperature
  *is* one of the main causes. Debunking it would teach something false. Reframe:
  *"Stringing is a temperature problem"* → it's temperature **and** retraction **and** wet
  filament, and here's how to tell which.
- **4. Warping.** "Bed isn't sticky enough" is half true. Shrinkage creates the pull and adhesion
  resists it. Reframe: *"Warping is an adhesion problem"* → the cause is shrinkage stress, adhesion
  only holds it down, and cooling and drafts drive it.
- **10. Layer height.** "The counterintuitive strength difference" needs a sourced test
  showing which way it goes for PLA on a P1S-class machine. Results vary between tests. No source,
  no strength claim: show time and looks only.
- **7. Elephant's foot.** Some first-layer squish *is* intended. Frame it as *"more squish is
  always better"*, not "squish is wrong".

### Order (STANDARDS 16)
Lesson 009 (the ocarina, Scott's audio OK) is first per OPEN row 34. Then topics 1–3. The Tin
Clicker hands-only clip and the BIQU Panda episode come before any of these, because they have
dates (Nov 28, and BIQU's overdue Nov 20 slot).

Production is the design session's work (row 34). It picks this up at its next session.
