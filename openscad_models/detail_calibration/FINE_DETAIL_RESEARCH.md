# Designing finer detail: research and measurements (2026-10-30)

Scott: "research how to design to a higher ability for smaller details. We
really need to master that ability for our prints. What other recommendations
do you have to significantly improve our 3D design abilities."

`DETAIL_STANDARD.md` already covers relief: how deep, how high, which way it
runs, and the layer grid, all measured on our own coupon. This file covers what
that standard doesn't: the smallest **shapes** (lettering, dots, pupils), the
hardware and slicer features that move those limits, and the modelling tools
that would make our organic work look sculpted rather than assembled.

## 1. Measured today: the smallest shapes, 0.4 vs 0.2 mm nozzle

`text_test/text_coupon.scad` has raised lettering ("OBC 8 Sg", 0.4 mm proud)
in six sizes, and dots 0.4–1.6 mm across. Each is printed two ways: on a top
face (lying flat) and on an upright wall. `text_test/measure_text.py` slices it
four ways with the gate's slicer (PrusaSlicer, Arachne walls), rebuilds every
layer from the beads at their real widths, and compares with the model.
"Match" is overlap ÷ union: 1.00 is perfect. Letters blobbing together or
strokes going missing both pull it down. Toolpath numbers, not plastic, as for
the detail coupon.

Letter height is the capital's height. OpenSCAD's `text(size=s)` makes
capitals about 1.05 × s tall in DejaVu Sans Bold.

| feature | 0.4 nozzle, 0.20 layers | 0.4 nozzle, 0.08 layers | 0.2 nozzle, 0.10 layers |
|---|---|---|---|
| letters 1 mm, top face | 0.60 (blobbed) | 0.64 | **0.86** |
| letters 1.5 mm, top face | 0.84 | 0.86 | **0.92** |
| letters 2 mm, top face | 0.92 | 0.92 | 0.95 |
| letters 3 mm, top face | 0.96 | 0.96 | 0.97 |
| letters 1.5 mm, upright face | 0.90 | 0.88 | **0.96** |
| letters 2–2.5 mm, upright face | 0.86–0.87 | 0.84–0.87 | **0.96–0.97** |
| letters 3 mm, upright face | 0.95 | 0.95 | 0.98 |
| dot 0.4 mm, top face | **0.00 (gone)** | 0.00 | 0.83 |
| dot 0.6 mm, top face | **0.00 (gone)** | 0.19 | 0.84 |
| dot 0.8 mm, top face | 0.93 | 0.93 | 0.93 |
| dot 0.6 mm, upright face | 0.83 | 0.67 | 0.96 |

Full table: `text_test/measured_text.json` (`python3 text_test/measure_text.py` regenerates it).

**What it says:**
- **The nozzle sets the smallest shape; the layer height sets the smallest
  step.** On the 0.4 nozzle, dropping from 0.20 to 0.08 mm layers changed
  almost nothing for letters or dots. Fine layers are for curves that climb
  (DETAIL_STANDARD rule 4), not for small shapes.
- **On the 0.4 nozzle:**
  - Raised lettering reads cleanly (≥ 0.95) from **3 mm** tall on either face.
    2 mm is usable on a face printed upward (0.92); on an upright face 2–2.5 mm
    comes out rough (0.86).
  - **Dots under 0.8 mm across vanish on a top face.** The slicer drops
    them rather than print them smaller. Arachne filters features that are
    small for the nozzle: Bambu's wiki says thin features are widened to
    about 85% of the nozzle, and OrcaSlicer's says those under the minimum
    feature size are skipped
    ([Bambu wiki](https://wiki.bambulab.com/en/software/bambu-studio/wall-generator),
    [OrcaSlicer wiki](https://github.com/orcaslicer/orcaslicer/wiki/quality_settings_wall_generator)).
    The exact cut-off in Bambu Studio may differ from our slicer's.
- **On a 0.2 nozzle:** lettering is clean from **1.5 mm**, and dots down to
  0.4 mm survive. Roughly **half the size for the same quality.**

## 2. Rules to add to the standard

10. **Lettering:**
    - On the 0.4 nozzle, raised or sunk letters are **3 mm tall, 2 mm only on
      a face printed upward**.
    - Below that, design for the 0.2 nozzle, or don't use lettering.
11. **Islands:** any separate small shape is **at least 0.8 mm across** on the
    0.4 nozzle. That covers a dot, a pupil, a berry, a rivet or a colour
    island. Smaller ones are dropped, not shrunk. A pupil is a colour island
    too: its own filament prints it as its own feature.
12. **Smallest shape → nozzle; smallest step → layer height.** Pick the
    nozzle by the smallest thing seen from the front, and the layer height by
    the roundest thing that climbs. Variable layer height (below) puts fine
    layers only where the round things are.

## 3. Recommendations, most impact first

### A. Get a 0.2 mm hotend for detail products (hardware, Scott's call)
- **What to buy:** Bambu sells a P1-series hotend with a 0.2 mm stainless
  nozzle, a quick swap on the P1S
  ([3DJake listing](https://www.3djake.ch/en-CH/bambu-lab/hotend-p1-series)).
- **What it buys,** measured above: lettering and small shapes at about half
  the size for the same quality.
- **What it costs:**
  - Time: slower prints at fine layers; community guidance is 0.05–0.12 mm
    layers ([Cal Poly](https://grandavehousing.calpoly.edu/news/bambu-lab-p1s-all-about),
    [Bambu forum](https://forum.bambulab.com/t/minimum-layer-height-limbo-how-low-can-we-go/154852)).
  - Reliability: more clogs, so retraction needs tuning
    ([Bambu forum](https://forum.bambulab.com/t/just-cannot-print-with-a-0-2mm-nozzle/29260)).
  - Strength: it's for figurines, miniatures and small signage, not
    load-bearing parts.
- **For files we sell:** the shop should state which nozzle a model was
  designed for. A file designed to rule 10 at 3 mm works on everyone's
  printer.

### B. Use Bambu Studio's "Precise Z height"
- **What it does:** it adjusts the last five layers so a part's top lands at
  its true height, not the nearest whole layer. It has been in Bambu Studio
  since 1.9; a forum user puts it under Quality → Precision
  ([Bambu wiki](https://wiki.bambulab.com/en/software/bambu-studio/layer-height)).
- **What it doesn't do:** it fixes the top surface only. A detail halfway up
  still needs DETAIL_STANDARD rule 2 (heights on the 0.2 mm grid).
- **Where to use it:** turn it on in every 3MF we ship.

### C. Variable layer height on round tops
- **What it is:** Bambu Studio's adaptive and smooth variable layer height.
  It lets 0.08 mm layers fall only where a form curves over (heads, domes,
  shoulders) and keeps 0.2 mm elsewhere. That gets rule 4's curve quality
  without printing the whole model at 0.08.
- **Range:** 0.08–0.28 mm on a 0.4 nozzle
  ([Bambu wiki](https://wiki.bambulab.com/en/software/bambu-studio/adaptive-layer-height)).
- **How people use it:** forum users run adaptive at about 0.75–0.85, then
  smooth
  ([Bambu forum](https://forum.bambulab.com/t/adaptive-layer-height-and-smoothing-issues/165945)).
- **Not with:** organic (tree) supports, which we don't use.
- **In our 3MFs:** we can set it per object for the figurines and creatures.

### D. Design each detailed face to print facing the best way: split into parts
- **What the measurements say:** the same letters scored 0.92 printed facing
  up and 0.86 printed upright on the 0.4 nozzle. Relief across an upright face
  holds to the hundredth (DETAIL_STANDARD).
- **What terrain designers do:** they print brick walls upright rather than
  flat for surface detail
  ([RMweb](https://www.rmweb.co.uk/topic/166557-more-3d-printed-architecture/),
  [Dakka](https://www.dakkadakka.com/dakkaforum/posts/list/815484.page)).
- **The design move:** split a model so every detailed face prints in its
  best direction, and join the parts with the fit-test-plate joints. That's a
  sign plate lying flat, a wall panel standing, a face looking up.

### E. Exaggerate at small scale ("heroic" proportions)
- **What miniature designers do:** FDM-focused designers scale up and
  exaggerate on purpose.
  - One designs minis at 40 mm "for clean results on a 0.4 mm nozzle".
  - Another makes FDM-specific minis "slightly larger than classic 28/32 mm"
    so faces and textures survive
    ([MakerWorld](https://makerworld.com/en/models/3043736),
    [MyMiniFactory](https://www.myminifactory.com/object/3d-print-support-free-supportless-fdm-null-brutes-gunners-squad-sci-fi-orc-proxy-no-supports-793555)).
- **For us:** on small pieces, enlarge eyes, buttons, letters and gaps to
  rule 10–11 sizes rather than shrinking them to true scale.

### F. Colour carries detail that relief can't, within limits
- **Where AMS colour works:** it's clean where a colour boundary lies across
  a face that prints upward.
- **The limits:**
  - One guide advises against colour detail under about 5 mm.
  - Tiny colour segments under-extrude
    ([Geeky Inc AMS guide](https://www.geekyinc.com/multi-color-3d-printing-anime-figures-the-ams-guide-for-p1s-x1c-2026/),
    [Bambu forum](https://forum.bambulab.com/t/problems-with-colored-miniatures/160232)).
- **Our numbers say the same thing in millimetres:** a colour island under
  0.8 mm on the 0.4 nozzle is dropped (rule 11). Design pupils, berries and
  buttons as ≥ 0.8 mm islands, ideally ≥ 1.5 mm. Or make them separate
  press-in parts, as the axolotl's eyes are.

### G. Matte filament for detailed display pieces
- **What the sources say:** vendors and hobby guides agree matte PLA hides
  layer lines and lets relief read, while silk's sheen amplifies the lines
  ([Siddament](https://siddament.com.au/blogs/filament-guide-au/matte-vs-silk-pla),
  [Snapmaker](https://www.snapmaker.com/blog/pla-matte-vs-basic/)).
  These are vendor sources, not controlled tests.
- **For us:** print and photograph detail products in matte, and keep silk
  for smooth forms.

### H. Real textures from a displacement map
- **The tool:** CNC Kitchen's BumpMesh applies a greyscale displacement map
  to an STL or 3MF in the browser. It masks downward faces so the bed stays
  flat, and it's open source (`stlTexturizer`)
  ([CNC Kitchen](https://cnckitchen.com/blog/stop-using-fuzzy-skin-i-made-something-better),
  [All3DP](https://all3dp.com/4/cnc-kitchens-free-browser-tool-lets-you-texture-3d-models-no-blender-needed/)).
- **Depth:** guides suggest 0.3–0.8 mm.
- **What it does that fuzzy skin can't:** wood grain, stone, knurl and
  basket weave, placed where you choose. Fuzzy skin is random noise.
- **In our pipeline:** do the same thing with Blender's displace modifier,
  which is already installed. Keep the map's features at least two beads
  apart (≥ 0.8 mm) so the nozzle can follow them.

### I. Better modelling tools for the forms OpenSCAD is bad at
- **The problem:** OpenSCAD builds by adding and subtracting primitives. Our
  organic pieces show it: the axolotl's first version "read as marshmallows on
  sticks".
- **The tools,** in order of value:
  1. **Signed-distance modelling** (`fogleman/sdf`, Python, writes STL).
     Shapes blend with a smooth union, so a head flows into a neck the way a
     sculpt does, and it's still code
     ([project page](https://www.michaelfogleman.com/projects/sdf/)). Best fit
     for creatures, figurines and soft forms. Check its licence before
     relying on it.
  2. **build123d** (Python, OpenCascade). True fillets and chamfers on any
     edge, and STEP export
     ([docs](https://build123d.readthedocs.io/en/stable/OpenSCAD.html)). Best
     for mechanical parts, enclosures and anything with crisp, rounded edges.
  3. **The OpenSCAD manifold build**, already in use for iteration (46 s
     against hours on CGAL). Keep it.
  4. **AI image-to-3D for a base form only.** TRELLIS.2 is MIT-licensed;
     Hunyuan3D's licence excludes some regions
     ([comparison](https://www.3daistudio.com/blog/trellis-2-vs-hunyuan-3d-differences-explained)).
     - Its output would need remeshing, our gates, and our own detail on top.
     - It needs Etsy's AI disclosure.
     - Never use it to copy someone else's design.
     - There's no evidence on how printable its meshes are, so test before
       trusting it.

### J. Close the loop with real prints
- **Print the coupons:** print `detail_coupon.stl` and `text_test/text_coupon.stl`
  once on the P1S. Then photograph them raking-lit. Every number above is
  toolpath; the plastic will be a little softer, and only a print says by how
  much.
- **If the 0.2 hotend arrives:** print them again with it.
- **A gate for small shapes:** add the shape measurement to the gate. Any design with lettering
  or small islands gets checked against rules 10–11 automatically, as
  `print_fidelity` already checks relief.
