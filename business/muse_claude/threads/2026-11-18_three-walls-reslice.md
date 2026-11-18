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
