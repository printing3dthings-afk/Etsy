# Benson's profile settings (for Claude's slicer)

Source: extracted 2026-11-18 from Benson's verified Trophy Rack profile 3MFs
(`~/workspace/your_files/trophy-rack-upload/`, built 2026-11-14 in Bambu Studio
02.08.02.61, genuine Studio exports). Each file is the `Metadata/project_settings.config`
from inside the named .3mf, copied verbatim. Load them exactly as they are.

## The four files

| File | Profile | Layer height | Process | Walls | Infill |
|---|---|---|---|---|---|
| `standard_project_settings.config` | Standard | 0.20 mm | `0.20mm Standard @BBL X1C` | 3 | 15% grid |
| `optimized_project_settings.config` | Optimized | 0.16 mm | `0.16mm Optimal @BBL X1C` | 3 | 12% gyroid |
| `multicolour_standard_project_settings.config` | Multicolour – Standard | 0.20 mm | `0.20mm Standard @BBL X1C` | 3 | 15% grid |
| `multicolour_optimized_project_settings.config` | Multicolour – Optimized | 0.16 mm | `0.16mm Optimal @BBL X1C` | 3 | 12% gyroid |

Identities on every file (stock system identities only — MakerWorld rejects custom
ones): printer `Bambu Lab P1S 0.4 nozzle`, filament `Bambu PLA Matte @BBL P1S 0.4 nozzle`
on every slot. Single-colour profiles collapse all parts to one extruder; multicolour
profiles carry the same filament identity on all four slots (tinted copies in the
Studio project).

## What changes from Bambu's stock settings — and why

Almost nothing, deliberately. Both processes are the stock system processes used
as-is — verified key-by-key against the flattened stock presets in
`~/workspace/.scratch-bambu/presets_stock/`:

- **Standard = stock `0.20mm Standard @BBL X1C` verbatim.** 3 walls and 15% grid
  infill are the stock values, not Benson tuning. Outer wall 200 mm/s, overhangs
  50/30/10 mm/s, seam aligned — all stock.
- **Optimized = stock `0.16mm Optimal @BBL X1C` verbatim.** 3 walls and **12%
  gyroid** infill are the stock values for that process. Its slower outer wall
  (55 mm/s) and slower overhangs (25/20/15/10 mm/s) are the stock Optimal values
  relative to Standard — that is what makes it "Optimized", not extra tuning.
  The scarf seam / slower walls mentioned in the Trophy Rack build notes describe
  this stock preset, not additional changes.
- **Multicolour only:** `flush_multiplier` 0.6 (60% purge-flush — the multicolour
  standard; the Cookie Jar Clicker is the one exception at 1.0, and its copy says
  so) and prime tower OFF (`enable_prime_tower` 0). Single-colour files carry
  `flush_multiplier` 1 and prime tower on, which is moot with one filament.
- **Supports: OFF everywhere** (`enable_support` 0). Every shipped design prints
  support-free by design; that is a design rule, not a slicer tweak.

## The 15% question, settled

Scott's Nov 12 setting is "3 walls and 15% infill" — with his own carve-out,
recorded in `threads/2026-11-11_animation-quality.md` (2026-11-12 11:53):
"use 15% from now on, unless a specific profile really is set to 12%."
The Optimized profiles really are set to 12% (stock 0.16mm Optimal), so they
are inside that carve-out, not in breach of it. **Rule: Standard profiles 15%,
Optimized profiles 12% gyroid, both 3 walls.** Do not "fix" Optimized to 15% —
that would change the profile's identity and its verified slice times.

Caution: the stock `0.12mm Fine @BBL X1C` process is **2 walls** / 15%. If you
use it (e.g. the 6 mm balls rebuild), set `wall_loops` to 3 yourself — Benson's
Fine builds are not covered by these four files.

## Figure support settings — none on file

Benson has **no figure support settings**: nothing Benson has shipped uses
supports at all. The support values in these configs are Bambu's stock
defaults carried along unused (`support_type` tree(auto), `support_top_z_distance`
0.2 Standard / 0.16 Optimized, `support_threshold_angle` 30 / 25) — they have
never been tuned or tested on a real figure. For the Urban Kid one-piece, the
support choice is a new decision, not something to copy from here. Do not
present these defaults as a tested figure-support recipe.

## How to use

`tools/bambu_slice.py` should load the matching config file exactly as it is.
Standard for listings and quote times; Optimized for the finer-surface profile.
Every slice Benson quotes comes from Bambu Studio with these settings — never
from the in-house checking slicer, which runs 15–34% short on time.
