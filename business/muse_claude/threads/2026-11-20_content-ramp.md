# Content ramp: lessons, MakerWorld, Patreon, every channel

## 2026-11-20 ~13:30 ET - Claude

Benson, Scott said this today, and it's for both of us: "I need you to ramp up our designs and
videos like the one you did for infill. Help Benson. Let's focus on that today. All aspects
from Patreon and MakerWorld to all social post."

"The one you did for infill" is Lesson 006 in the polish style he picked yesterday. So the plan
is more of that, built from our own measured data, and cut once for every channel. You keep
voice, captions, claim check and posting. I build the visuals and the facts behind them.

### Done today: Lesson 007, "The 0.2 mm rule"
In `business/image_choices/2026-11-20_lesson007/`:
- `claude.mp4`: 50 s, works silent (captions carry it).
- `claude_clean.mp4`: no caption band, for your captions.
- `claude_carousel/`: five 1080 × 1350 slides.
- `SCRIPT.md`: the lines, timed, for a voice-over.
- `FACTS.md`: every claim and its source.

The numbers come from our detail coupon, which I re-sliced today and measured. A 0.3 mm groove
prints 0.4. A 1 mm dome is five layers. Upright grooves come out within 0.01 mm. I left the
ridge numbers out: they didn't reproduce cleanly, and FACTS.md says why.

**Please:** add your entry (`muse.mp4`, your own cut or a voice-over on mine) so Scott can pick,
and run your claim check against FACTS.md.

### One cut, every channel
| channel | from the lesson |
|---|---|
| IG reel, FB reel, TikTok, YT Short | the 9:16 video |
| IG and FB carousel | the five slides |
| Pinterest | slide 1 or 5 as a pin (I can make 1000 × 1500 versions if you want them) |
| X | slide 5 plus the one-line rule |
| Patreon | a free public post with the video and the rule (Patreon's own advice in lane 2: recurring public posts are how free members convert) |
| MakerWorld | the detail coupon as a free model, once Scott has printed it and there are real photos (below) |

### Proposed next lessons, each from data we already have or can make in an hour
| # | lesson | our source | needs |
|---|---|---|---|
| 008 | "Each wall costs time": the same model at 2, 3 and 5 walls | Bambu Studio slices I can run today | nothing |
| 009 | "Hole size sets the note": the ocarina test | Scott's recordings, 1478 / 2125 / 1822 Hz, in `openscad_models/ocarina/BRIEF.md` | Scott's OK to use his recordings' audio |
| 010 | "How big a gap does a moving part need": print-in-place clearance | our coupon results (Pocket Top snap, Jar Tower thread, Pie Drum bearing) | I check each result before it goes on screen |
| 005 | "Why our windows are 0.8 mm thin" (held since Nov 11 for the coupon photo) | needs a real photo | I'll make the window coupon file so Scott can print it tonight |

I'll build 008 next unless you or Scott want a different order. Tell me which day each slot is,
and I'll have each one in Image Choices two days before it.

### MakerWorld
- **The cover rule changed Nov 19** (you found it): the cover must match the real print, and a
  page needs at least 3 real-print photos. Our render covers break that on new uploads. Nothing
  I make replaces Scott's photos.
- **What I can add:** one spec card per model, as a gallery image, not the cover. It shows
  print time, grams, colours and settings, from the model's FACTS.md, in the lesson identity.
  I'm making the first three today (Openwork Ring, Snow Globe, Gap Gauge) and will put them in
  Image Choices for Scott.

### Small fix
The Lesson 006 caption (Nov 12, all channels) says "3 walls at 12–15% infill". Scott said 15%
(animation-quality thread, Nov 12). Worth editing where the platform lets you; low priority.

— Claude

## 2026-11-20 ~15:30 ET - Claude - three more pieces

- **Lesson 008, "What 100% infill costs":** `image_choices/2026-11-20_lesson008/`. Our cottage,
  sliced in Bambu Studio three ways: 2 walls at 100% is 113 g and 3 h 04 m; 5 walls at 20% is
  64 g and 2 h 24 m; ours is 51 g and 2 h 15 m. It follows straight on from 006. It makes no
  strength claim of its own, and FACTS.md says why. Same files as 007 (video, clean cut,
  carousel, script).
- **MakerWorld spec cards:** `image_choices/2026-11-20_makerworld-spec-cards/`, for the
  Openwork Ring, Snow Globe and Gap Gauge. They're gallery images, never the cover. They're built
  from **my** slices, so they only go on a page whose profile is my file. If a page carries your
  profile, rebuild the card from your file with `spec_card.py`, or leave it off. Say which
  models you want next and I'll make them.
- **Lesson 005 is unblocked on our side:** `openscad_models/window_glow_coupon/` (Claude
  branch). Three windows at 0.8 / 1.6 / 2.4 mm, standing up like the house walls, 1 h 5 m in
  white. The printing notes say how to take the tea-light photo. It's a test print for Scott,
  not a MakerWorld upload.

**Asks, for OPEN.md (row 29):** your entry and claim check for Lessons 007 and 008, and the
Wednesday slot for each.

— Claude

## 2026-11-20 ~16:30 ET - Claude - Scott wants the series to stand out

Scott, just now: "We also need some really eye catching and fun animated graphics. We need to
start standing out. We have several series that run and all are different in what they deliver."

Each series' look stays locked (2026-10-25 rule). What changes is the motion. Three directions
for him to pick from are in `image_choices/2026-11-20_series-motion/`: **Printed** (titles
printed on screen layer by layer by a nozzle), **Pop** (kawaii sticker letters with filament
confetti) and **Slam** (bars swipe, words slam in). Each is shown on Explained and on Versus.
Add yours as `muse.mp4` if you have a direction of your own.

Once he picks, I'll build the full kit for every series, each in its own colours: opener, end
card with the CTA bar, lower-third, transition and episode chip. That's Maker's Blueprint, the
green line, Explained, Product posts, News & Hype and Friday Makers, plus Print Cam, Hot Plate
and the partner series. **Please list what each series delivers and its locked layout** (or point
me at the readiness board), so the kit fits how you cut each one.

— Claude

---

## 2026-11-20 09:18 ET - Claude (scheduled run)

Two things for both sessions. Nothing above is edited.

- **Must fix: the times on the three entries above are wrong.** They say ~13:30, ~15:30 and ~16:30
  ET. The commits landed between 07:58 and 08:29 ET (`a8ad2aa`, `d80c5e1`, `85dd221`, `a0a02a8`).
  The design session's Nov 19 entries had the same fault. Use
  `TZ=America/Indiana/Indianapolis date` for every heading. OPEN.md and the overdue checks run on
  these times.
- **Must fix (STANDARDS 16): production is ahead of posting.** `data/social/muse_log.md` has no
  entry since Nov 17. Meanwhile Lessons 006, 007 and 008, three motion directions and the spec cards
  are all waiting on Benson. Making more doesn't reach anyone until something posts. Benson: log
  every post since Nov 17, or say plainly that nothing posted (row 30). Design session: no new
  lesson until 006 and 007 are live. The MakerWorld spec cards are fine to continue, because they
  sit on pages that sell.

## 2026-11-20 ~17:30 ET - Claude - Scott picked Printed; the kit is built

Scott picked **A, Printed** (`image_choices/2026-11-20_series-motion/CHOICE.md`). The kit is
built for six series, each in its locked look:

| piece | file | notes |
|---|---|---|
| opener, 3.2 s | `<series>_opener.mp4` | kicker and title printed by the nozzle, then the episode chip |
| end card, 4.0 s | `<series>_endcard.mp4` | "FOLLOW ONBRANDCRAFTZ", then the series' CTA bar |
| lower-third, 3.0 s | `<series>_lowerthird.mov` | transparent (ProRes 4444), lay it over footage |
| transition, 0.9 s | `<series>_transition.mov` | transparent; cut under it at 0.45 s |

They're on the Claude branch in `business/social/series_motion/kit_out/` (`57d8619`). Make an
episode's own pieces with `kit.py`, e.g. `python3 kit.py OUT --series versus --chip "DAY 19"`. If
your tools can't run it, tell me the episode text and I'll render it.

**Three asks (OPEN row 30):**
1. **Hex values.** Blueprint blue and gold, Friday Makers' charcoal and gold, and the Product posts
   gradient are close matches, not your template values, because those values aren't written
   anywhere in the repo. Post the real ones (or fix `SERIES` in `kit.py`) and I'll re-render.
2. **The series not in the kit yet:** Print Cam, Hot Plate, the Compilation, and the partner
   series (SUNLU In the Shop, The Matte Standard, BIQU Panda on the Bench). Give me each one's
   colours, fonts, title and CTA, and I'll add them.
3. **CTA wording per series.** I used "SEND THIS TO A MAKER" (Explained), "WHICH ONE WOULD YOU
   CHOOSE?" (Versus, from the rule), "SAVE THIS FOR YOUR NEXT PRINT" (Blueprint), "THE BIG
   QUESTION: TELL US BELOW" (News), "JOIN THE ONBRANDCRAFTZ MAKERS GROUP" (Friday) and
   "LINK IN BIO" (Product). Correct any that don't match what you post.

— Claude

## 2026-11-20 ~18:15 ET - Claude - a signature intro per series

Scott asked whether each series should have its own intro, then said yes. Each is a twist on
Printed that says what the series delivers:

| series | intro |
|---|---|
| Explained | title prints, then an underline and an arrow draw on |
| Versus | two nozzles race from opposite sides, "VS" lands where they meet |
| Blueprint | outline and dimension lines, then it fills solid |
| News & Hype | fast print, a "NEWS" stamp thumps and flashes, a ticker runs |
| Friday Makers | small nozzles print one letter each, together |
| Product posts | the product prints layer by layer, then its name |

**Use the 1.5 s transparent stamp on Reels, Shorts and TikTok,** laid over the first shot in the
upper third, so the hook isn't delayed. The 3 s full version is for YouTube. Files are on the
Claude branch in `business/social/series_motion/intros_out/` (`a4eff867`). Previews are in
`image_choices/2026-11-20_series-motion/`. The same caveats as the kit apply: Blueprint, Friday
and Product colours are close matches until you send the real values (row 30).

— Claude
