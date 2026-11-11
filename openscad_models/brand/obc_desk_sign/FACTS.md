# FACTS: OBC desk sign, v1

The fact sheet Muse asked for (business/muse_claude, 2026-11-11). Every number is
from this folder's checks; the source is on each line.

## Version
- **v1**, 2026-11-11. The first version; nothing replaced.
- **Not printed yet.** Every image is a render or a toolpath simulation.

## What it is
Scott's gold OBC logo, traced from the logo image itself (not set in a font),
raised on a black plaque that slides into a black base and leans back about 10°.

## Numbers
| what | value | source |
|---|---|---|
| Plaque | 182 × 88 × 5 mm | `checks/fit.txt` |
| Letters | 150 mm wide, 2.4 mm proud | `checks/fit.txt`, `obc_desk_sign.scad` |
| Base | 196 × 46 × 14 mm | `checks/fit.txt` |
| Lean | 9.4–10.9° (depends how tight the slot prints) | `checks/fit.txt` |
| Plaque print, AMS | 2 h 23 m, 43.9 g black + 10.6 g gold | `checks/slices.txt` |
| Plaque print, one spool + pause at 5.0 mm | 2 h 19 m plus the swap, 53.2 g | `checks/slices.txt` |
| Base print | 1 h 36 m, 46.6 g | `checks/slices.txt` |
| Settings | 0.2 mm layers, supports off, P1S 0.4 nozzle, Bambu PLA Basic profile | `checks/slices.txt` |

All times are Bambu Studio's estimates (Standard 0.20 mm). There is no
"Optimized" profile slice.

## Free or paid, per platform
**None decided.** Scott asked for this to print his own sign. Whether it goes on
MakerWorld or anywhere else is his call. Don't queue it until he says so.

## Safe to say, word for word
- "My logo, as a 3D print design."
- "Gold on black. The plaque slides into its base, no glue."
- "Traced from the logo itself."
- "Two prints: the plaque (one colour change) and the base."

## Don't say
- That it's printed, tested, or "real" (not yet).
- That it's free or for sale (not decided).

## Media
| file (this folder) | shows | version |
|---|---|---|
| `images/obc_desk_sign_front.png` | front, grey studio | v1 |
| `images/obc_desk_sign_three_quarter.png` | three-quarter, grey studio | v1 |
| `images/obc_desk_sign_top.png` | top | v1 |
| `images/obc_desk_sign_as_printed.png` | the plaque rendered from its toolpath | v1 |
| `images/guide_parts.png` | the two prints as they come off the plate | v1 |
| `images/guide_insert.png` | the plaque going into the slot | v1 |
| `social/obc_sign_tiktok_claude.mp4` | the TikTok entry (also in image_choices on main) | v1 |

- **Missing:** a scale shot (in a hand, or next to a known object), which only a
  real print can give honestly. There's no lit shot, because it isn't a lantern.
- **Git LFS:** the images and the video are stored in LFS. Use
  `git lfs pull -I "<path>"` after fetching the branch.
