# Technique samplers, FACTS (2026-11-14)

Test pieces for techniques only a printer can do. They aren't products. Background,
sources and numbers are in `data/knowledge_base/fdm_only_techniques.md`. Rebuild everything
with `make_samplers.sh`.

All files are already sliced (`.gcode.3mf`) for the P1S, 0.4 nozzle, PLA Basic, 0.20 mm,
on a textured PEI plate. Open one in Bambu Studio, or send it straight to the printer.

## 1. `texture_sampler.gcode.3mf`: four 20 mm cylinders, one texture each
**Print:** 25 min 27 s, 9.1 g, no supports.

| left to right | texture (fuzzy skin noise) | outer wall spread, measured |
|---|---|---|
| 1 | none (control) | 0.10 mm (just the 96 facets) |
| 2 | classic | 0.59 |
| 3 | Perlin | 0.25 |
| 4 | Voronoi | 0.71 |

- All three textures use the same depth (0.3 mm), point spacing (0.6) and scale (3); only
  the noise differs.
- Each cylinder carries its own setting in the file (`--object-set`).
- **What to look for:**
  - Which reads as stone (I expect Voronoi) and which as wood (Perlin)?
  - Does any feel loose or flaky when you scratch it with a nail?

## 2. `vase_ribbed.gcode.3mf` and `vase_plain.gcode.3mf`: the vase-mode slit trick
- **Both:** 40 mm across, 30 tall, printed in vase mode as one continuous wall, 0.6 mm wide.
- **Ribbed:** the model has six slits 0.001 mm wide from the rim to near the centre.
  Bambu's wall runs into each slit and back out, making six double-wall spokes inside the
  same single continuous wall. Measured: 316 mm of wall per layer, against 124 for the
  plain one.
- **Print:**
  - ribbed: 19 min 41 s, 7.7 g;
  - plain: 12 min 19 s, 3.8 g.
- **What to look for:**
  - Squeeze each across its width: the ribbed one should hardly flex.
  - Can you see or feel the six fine lines on the outside where the slits open?
  - Look inside: are the spokes there and joined to the rim?
- **Slicer settings that matter**, if you re-slice it yourself:
  - Spiral vase on.
  - "Slice gap closing radius" at **0** (Bambu's default 0.049 closes the slits).
  - Outer wall line width 0.6.

## Not tested
Nothing here has been printed. The numbers come from Bambu Studio 2.8.2's own slices,
read with `tools/bambu_gcode.py`.
