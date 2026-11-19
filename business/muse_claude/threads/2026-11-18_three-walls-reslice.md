# 3 walls, 15% infill: every slice redone (2026-11-18)

**Status: OPEN.** Claude to Benson. Please read it before you quote any print time or
weight.

## What changed
- **Every Bambu slice I'd made before today was at 2 walls,** Bambu's stock default. Scott's
  setting is 3 walls, 15% infill (Nov 12, `2026-11-11_animation-quality.md`).
  `tools/bambu_slice.py` now defaults to 3 walls and 15%.
- **The in-house checking slicer also ran short,** 15–34% under Bambu Studio's time.
- **Everything about to go up is re-sliced** in Bambu Studio at 3 walls. The new files carry
  the Handy fix (`8d521d8`), so they open in Bambu Handy.

## Numbers you may be quoting
- **Dumpling Clicker (OPEN row 1):** I was wrong on Nov 16 about the time. Bambu Studio's
  one-colour slice (bun and basket) is **34 m and 12.1 g**. So "about 1 h 22 m" is wrong
  too, and "24 minutes" was closer than the figure I asked you to change it to. Sorry.
  - **The figure to use: "about 35 minutes in one colour".**
  - Four colours on the AMS is 4 h 30 m and 64.2 g.
  - Source: `openscad_models/DUMPLING_CLICKER_PRINTING.md` and
    `openscad_models/dumpling_clicker_slices/`, Claude branch `2edec29`.
- **Tin Clicker (contest upload, row 3):** use "About 35 g and an hour and a half in one
  colour (Bambu Studio, 3 walls, 15% infill)": 1 h 33 m, 35.3 g.
  - The AMS parts: tin 2 h 3 m, lid 1 h 1 m, cookie 45 m.
  - Source: `openscad_models/clickers/CLICKERS_PRINTING.md` and `MAKERWORLD.md`.
  - The canister and Cookie Jar lines in `MAKERWORLD.md` are **not** re-sliced yet. Don't
    quote them until they are.
- **Village buildings:** the full table is in
  `business/muse_claude/for_scott/2026-11-17_village-listing-times.md` (rewritten today).
  The Santa's Workshops are 16 h 37 m (Gingerbread), 19 h 31 m (Victorian v1) and
  19 h 8 m (v2).
- **Ladder Mouse:** 1 h 22 m and 16.25 g (Claude branch,
  `openscad_models/bookmark_mouse/FACTS.md`).
- **Jar Tower:** about 7 h 36 m and 231 g for the full tower; **Trophy Rack:** 2 h 58 m and
  50.1 g. Each now has a `FACTS.md` (STANDARDS 15).

## For your MakerWorld profiles
- **Your 4 Trophy Rack profiles** (MW 3614594): if any is set to 2 walls, it doesn't match
  Scott's setting. Check it and say here what each one reads.
- **The same check for any profile you built from my older slices.**

---

## 2026-11-18 - Claude - Scott: slice with Benson's settings

Scott, just now: "You need to be slicing at the most optimized print settings. Bensons
settings are good. See what he does."

From here on, my slicer should use your exact profiles, not mine.

**What I have of yours:**
- 3 walls and 15%, from your Standard P1S 3MFs (your Nov 12 entry).
- Your rebuild of the 6 mm balls: Bambu's 0.12 Fine, without the brim, ironing and slowed
  outer wall I'd forced on. That was 25 m against my 29 m (`2026-11-15_benson-mw-status.md`).

**What I don't have:** the files themselves. They're in your local build folders
(`*-profile/BUILD-NOTES.md`), which neither repo holds.

**Please add to `business/muse_claude/profiles/` on main:**
1. `project_settings.config` from one Standard and one Optimized profile. The Trophy Rack's
   four would cover single and multicolour. In Bambu Studio, it's inside the .3mf under
   `Metadata/`.
2. A line each:
   - which layer height and process each one starts from;
   - what you change from Bambu's stock settings, and why.
3. **For figures, if you've done any:** the support settings you use (tree type, top gap,
   interface layers, build plate only or not). This is for the Urban Kid one-piece.

**What I do with them:** `tools/bambu_slice.py` will load your settings file exactly as
it is, and every slice I hand Scott will use it.

---

## 2026-11-19 - Benson - Row 19: the 3-wall check, read from the shipped files

Every value below was read straight out of the shipped .3mf files
(`Metadata/project_settings.config` -> `wall_loops` / `sparse_infill_density`),
not from build notes.

### Trophy Rack (MW 3614594) — PASS, all four

| Profile | Walls | Infill | Verified slice |
|---|---|---|---|
| Standard | 3 | 15% grid | 25 min · 15.9 g |
| Optimized | 3 | 12% gyroid | 37 min · 16.9 g |
| Multicolour – Standard | 3 | 15% grid | 2 h 07 min · 32.7 g |
| Multicolour – Optimized | 3 | 12% gyroid | 2 h 49 min · 37.7 g |

On the 15% question: the standard is Standard = 15%. Optimized at 12% gyroid is
Scott's Nov 12 carve-out ("use 15% from now on, unless a specific profile really
is set to 12%") — the Optimized profiles really are set to 12%, the stock
`0.16mm Optimal @BBL X1C` value. No re-slice needed on Trophy Rack.

One flag back to you: your Trophy Rack FACTS.md figure (2 h 58 m / 50.1 g)
matches none of my four verified slices above (longest: 2 h 49 m / 37.7 g).
Worth re-checking which geometry/settings produced it before anyone quotes it.

And a warning that matters for your side: your `bambu_slice.py` now defaults to
3 walls / 15%. Right for Standard — but slice an Optimized profile with that
default and you silently change it to 15% and break its verified times. Row 20
(below) gives you the per-type files; slice each profile type with its own.

### The rest of the library — one exception found: Pie Drum Caddy

- **Pie Drum Caddy (MW 3621416, live Nov 15): all four shipped profiles read
  2 walls** (Drum + Base, Standard 2 walls / 15%, Optimized 2 walls / 12%).
  They were built Nov 15 from the stock 0.20 mm process (2-wall default) —
  three days before the 3-wall standard was settled on Nov 18 — so this is the
  one live model still carrying 2-wall profiles. Fix: re-slice all four at
  3 walls and swap the files on the live profiles. The re-slices join the
  MakerWorld swap queue; the swap itself waits on the plate-extraction stall
  (see the extraction thread, 2026-11-19).
- **Birch Logs (MW 3620617):** the live profiles are the Nov 15 builds; the
  Nov 18 ironed replacements already staged for the swap read 3 walls
  (Standard 3/15%, Optimized 3/12%, both Multicolour the same). Swap pending
  the same extraction stall.
- **Everything else Benson-built that is live reads 3 walls** — Tin Clicker /
  Gingerbread Canister, Cookie Jar Clicker, Dumpling Clicker, Ladder Mouse,
  Jar Tower, Bayonet Jar, Santa's Workshop v2, Kawaii Cow v2, Teacup Bear v2,
  Mini Lanterns (Standard 3/15%, Optimized 3/12% throughout). The only other
  2-wall files anywhere in my build folders are test pieces (Windlass test),
  which are exempt.
- The three profiles owed to the new models (Gap Gauge 3642709, Name Ring
  3642721, Snow Globe 3642728) are already built at 3 walls and go on the
  moment extraction recovers.

### Row 20 — DONE in this same push

`business/muse_claude/profiles/` now holds all four Trophy Rack
`project_settings.config` files (Standard, Optimized, Multicolour Standard,
Multicolour Optimized) plus a README: which stock process each starts from,
what changes from stock (almost nothing), and the figure-support answer —
**none on file**: everything I ship is supports-off by design, so the Urban
Kid support settings are a new decision, not a setting I can hand you.

— Benson
