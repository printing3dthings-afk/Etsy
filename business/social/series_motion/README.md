# Series motion: the Printed kit

Scott picked **A, Printed** on 2026-11-20 (`directions.py` holds the three he chose from). Every
title is printed onto the screen layer by layer, by a nozzle sweeping back and forth, in each
series' own locked look.

## What's in `kit_out/` (1080 × 1920, 30 fps)
| piece | length | file | use |
|---|---|---|---|
| opener | 3.2 s | `<series>_opener.mp4` (+ `.png` still) | the first seconds of an episode |
| end card | 4.0 s | `<series>_endcard.mp4` (+ `.png`) | the last seconds: "FOLLOW ONBRANDCRAFTZ" and the series' CTA bar |
| lower-third | 3.0 s | `<series>_lowerthird.mov` | a name or caption strip, **transparent** (ProRes 4444): lay it over footage |
| transition | 0.9 s | `<series>_transition.mov` | **transparent**: bands print over the screen and clear; cut under it at 0.45 s |
| sizzle | 15.6 s | `all_series_openers.mp4` | every series' opener back to back |

Series: `explained`, `versus`, `blueprint`, `news`, `friday`, `product`.

## Make an episode's own pieces
    python3 kit.py OUT --series versus --chip "DAY 19"
    python3 kit.py OUT --series product --title "COOKIE CLOCK TOWER" --only opener
    python3 kit.py OUT --series explained --chip "LESSON 008" --cta "SEND THIS TO A MAKER"
The lower-third's text is set in `lowerthird()`; ask Claude for a `--text` option if you need it.

## Colours: which are exact
- **Exact:** Explained (the Lesson 006 identity) and the green line (#40F264, from the Series
  identity rule). News & Hype's yellow #FFD21F is from the rule too.
- **Close matches, to correct:** Maker's Blueprint blue and gold, Friday Makers' charcoal and
  gold, the Product posts gradient. Their hex values aren't written down anywhere in the repo.
  Benson, put the real ones in `SERIES` in `kit.py` and re-run; everything rebuilds.

## Not in the kit yet
Print Cam, Hot Plate, the Compilation and the partner series (SUNLU In the Shop, The Matte
Standard, BIQU Panda on the Bench): their looks aren't in the repo. Each is one entry in `SERIES`
once Benson gives its colours, fonts and title.
