# Birch Log Tea-Light Trio, FACTS (2026-11-15)

Scott picked this from five product ideas (idea 4), then form 1 of five: three upright cut logs.
**Nothing here has been printed.** Every number below is from the model or from Bambu Studio's
own slice (2.8.2).

## What it is
Three upright birch logs, each with a well on top for a **38 mm LED tea light**.
- **LED tea lights only, never a real candle:** the logs are PLA.
- **What looks like birch, and where it comes from:**
  - **Bark texture:** made by the slicer, not the model. Bambu Studio's Perlin fuzzy skin runs
    on the outer walls only. It was measured on the texture sampler (`../technique_samplers/`,
    `data/knowledge_base/fdm_only_techniques.md` section 1).
  - **Dark marks:** short lens-shaped lenticels in rows, plus one or two dark "eyes" (the chevron
    over a branch scar). They're a second colour, 1.0 mm deep into the bark.
  - **The cut face:** a third colour, tan, 0.8 mm deep, with uneven growth rings (grooves 0.6 wide,
    0.4 deep) and two drying cracks.

| log | height | across (widest) | well |
|---|---|---|---|
| short | 60 mm | 72 mm | 40.5 mm across, 14 deep |
| middle | 90 mm | 79 mm | same |
| tall | 120 mm | 84 mm | same |

- **Inside:** hollow, open at the foot, with 2 mm walls throughout.
  - A tube up the middle carries a 10 mm hole from the foot to the well floor. Push the light
    out with a pencil, or just tip the log.
  - Every surface that faces down inside slopes at 37° from upright, so nothing is bridged and
    there are no supports.

## The print (`birch_logs_trio.gcode.3mf`)
All three logs on one P1S plate. It's Bambu Studio's own slice and a full project: open it to
re-slice, or send it straight to the printer.

- **Settings:** PLA Matte, 0.4 nozzle, 0.20 mm layers, textured PEI, supports off. Perlin fuzzy
  skin 0.3 mm deep, points 0.6 apart, scale 3.
- **Time and filament:** **13 h 41 min, 318 g** in all:
  - 293 g ivory white (bark);
  - 15.5 g charcoal (marks);
  - 9.1 g tan (cut face).
- **Colour changes: 113.** About 69 g of the total is purge into the prime tower.
- **Why the marks are in rows:** every layer with charcoal in it costs a colour change and its
  purge, however little charcoal it holds. So all the marks sit in the same height bands on all
  three logs: 6 rows of 8 layers and 2 eye bands of 25.
- **Slice history:**
  - The first try spread thin marks over 3× more bands: 139 changes and 86 g of purge.
  - A version with fewer, thinner marks used 66 layers (81 changes). Its render read as a white
    cylinder with a few hairlines, not birch, so the marks got bolder instead.
- **AMS slots:** 1 white, 2 charcoal, 3 tan. Any matte ivory, charcoal and latte/tan PLA works.
- **Rebuild:** `make.sh`, from the repo root.

## Checks (`checks/`)
- **Product gate:** PASS on each log as one solid (`gate_log0..2.txt`).
  - watertight, one body, no supports, flat base, stable;
  - thinnest wall 1.9–2.0 mm (floor 1.2).
- **Print fidelity:** short log, 0 flags. Middle and tall: `fidelity_log1/2.txt`.
- **Fragility:** `fragility_log2.txt`.

## Images (`images/`)
- `trio_model.png` is a design-review render of the model. It has no bark texture, because the
  texture only exists in the toolpath.
- The `trio_as_printed_*` views are rendered from Bambu Studio's toolpath, fuzzy skin included.
- **Both are renders, not photos.**

## Not known until it's printed
- How the Perlin bark looks and feels in matte PLA at this size.
- Whether the 0.8 mm-tall dark lenticels read cleanly through the fuzzy outer wall.
- That a given brand of LED tea light fits: the well is 40.5 mm for 38 mm lights.
