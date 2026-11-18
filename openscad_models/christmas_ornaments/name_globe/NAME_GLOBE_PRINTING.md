# Snow Globe Name Ornament: printing notes

Built 2026-11-18. Scott picked this form (5 of 5) to replace the domed name
ornament after its test print, whose inlaid name came out lumpy on its curve.

**What it is:** a flat snow globe on its base, 62 × 93 mm with the loop, 3.2 mm
thick.
- **On the glass:** a village cottage, a tree with a star, a moon, falling snow,
  and a drift across the bottom. The cottage's door and windows are cut through,
  so the glass shows.
- **On the base:** the name and year, raised 0.8 mm.
- **The maker's mark:** OBC, engraved in the back of the base. It reads when you
  turn the ornament over on its loop.

The pictures in `images/` are design-review renders, not photos. The sample name is
Olivia.

## Colours, by height

| part | what | height | colour in the file |
|---|---|---|---|
| frame | the globe's rim, the loop, the base | 0–2.4 mm | red `#C62F3A` |
| glass | the disc inside the rim | 0–1.2 mm | night blue `#2F4B7C`, or a translucent filament |
| snow | the scene; the name and year | 1.2–2.4 mm; 2.4–3.2 mm | white `#F4F1EA` |

The AMS changes colour on the twelve layers below 2.4 mm.

## Print it
- **`name_globe.3mf`:** one object, three parts already aligned.
- **`gcode/name_globe_three_colour.gcode.3mf`:** sliced, opens in Bambu Handy.
  - Bambu Studio, P1S 0.4, PLA Basic, 0.20 mm Standard;
  - 3 walls, 15% infill (Scott, 2026-11-12); supports off.
- **Flat, back on the plate, as it sits in the file.** Nothing overhangs.

**Cost, from Bambu Studio's own slice:** 1 h 4 m, 17.1 g (8.3 g red, 4.5 g blue, 4.3 g white), supports 0.

These are at Claude's slicer settings. Benson's profiles (OPEN row 20) aren't on
main yet; re-slice with them when they land.

## Making one for a buyer

    ./build.sh "Christopher" 2026      # or ./build.sh "Mia" ""  for no year

The name is as large as fits 46 mm across the base, at most 11 mm.

**MakerWorld customizer:** `pmm/name_globe_pmm.scad`, built by
`../build_name_pmm.py name_globe`.
- It uses only fonts PMM has (Lobster, Montserrat).
- It's centred on (0, 0): the profile needs Auto Arrangement on.
- **Checked here (2026-11-18):** Olivia, Jessee, Mia, Christopher, MARY-JO and Zoë
  all build and fit on the base.
- **Not checked:** how fast PMM generates it. That needs a Manifold build of
  OpenSCAD, and fetching one was blocked in this session.

## Checks (`logs/`)
- **Parts:** closed, no two overlap.
- **Product gate: PASS.**
  - One body, nothing thinner than 1.2 mm.
  - The scene and name are declared as colour detail.
- **Print fidelity:** 0 flagged.
- **Fragility:** 0 high, 0 watch.
- **Silhouette (`silhouette_frame.txt`, on the frame):**
  - No near-touches, nothing thin, one clean piece.
  - It flags twinning, which doesn't apply: a globe on a base is symmetric on
    purpose.
  - Run on all three parts together, it also counts the scene's snow as separate
    pieces, which they are on top of the glass. It also finds zero-area slivers
    where the parts meet, an artefact of joining separate meshes.

**What changed while checking, and why:**
- The glass is 1.2 mm, six layers, the gate's wall floor. At 1.0 it failed.
- The frame's inside corners are filled to 1.2 mm where the rim meets the base;
  the wedge of air there was too thin to print open.
- The rim's inner edge, the glass and the scene share one circle. A filleted copy
  left hairline gaps.
- The cottage's walls and the tree's lowest tier are sunk into the drift, and the
  tree's star sits on its tip. Each left a sliver of blue too thin to print.

## Test print (Scott, 2026-11-18: "Both")
Print `gcode/name_globe_three_colour.gcode.3mf`. Load red in AMS slot 1, blue in slot 2
and white in slot 3.

**What to look at:**
- **The name and year:** are the white letters solid and crisp on the base?
- **The scene:** are the cottage's windows and door clean openings showing the blue? Are
  the snow dots round?
- **The glass:** is the 1.2 mm disc flat and firm, and joined to the rim all the way round?
- **The back:** does OBC read correctly when you turn it over on its loop?
- **Report:** a photo of the front and one of the back.
