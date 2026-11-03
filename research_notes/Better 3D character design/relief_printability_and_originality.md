# Turning 2D artwork into FDM relief pieces, charms, pendants, ornaments and figurines (Bambu P1S, 0.4 mm nozzle, 0.2 mm layers), and the legal side of using reference art

Scope note for the report writer: two kinds of source are mixed here, and each finding says which it is.
- **Tested (in-repo):** measured on this shop's own slicer toolpaths. `openscad_models/detail_calibration/DETAIL_STANDARD.md` (coupon sliced in PrusaSlicer 2.7 with Arachne and the P1S 0.4 mm profile, at 0.20, 0.12 and 0.08 mm layers) and `openscad_models/detail_calibration/FINE_DETAIL_RESEARCH.md` (lettering and dot tests, 0.4 mm vs 0.2 mm nozzle). These are local files, not URLs, and they are **toolpath measurements, not measurements of printed plastic**. The coupon has not yet been printed and photographed.
- **Published:** design guides, forums and law sources, cited by URL. Most published FDM numbers are rules of thumb and disagree with each other by about 2×.

---

## 1. Bas-relief / low-relief techniques: how depth is compressed, by hand and digitally

### Takeaway
Classical practice defines low relief as forms that project less than half their natural depth. Digital tools get there by compressing gradients, not raw depth: steep depth jumps are flattened and small slopes kept, so outlines and fine detail survive in a very shallow height field. This research found no official numeric rule from the US Mint or medal guilds. The only depth figures found are secondary (circulating coins about 0.3–0.5 mm of relief).

### Cited Findings
- **Definitions.** Bas-relief (basso-rilievo) is relief whose forms project only slightly from the background. Sources differ on what the "less than half" limit is measured against: less than half the circumference, or less than half the actual thickness. Alto-rilievo (high relief) projects at least half the natural proportions. Mezzo-rilievo is rounded to about half, with no detached parts. Wikipedia notes that these terms are "somewhat variable" and that many works mix them. Coins are the standard example of low relief — [Britannica](https://www.britannica.com/art/bas-relief); [Wikipedia: Relief](https://en.wikipedia.org/wiki/Relief); [Catholic Encyclopedia](https://www.newadvent.org/cathen/02341a.htm); [study.com](https://study.com/academy/lesson/relief-carving-low-bas-linenfold.html)
- **Coin relief depth (secondary figure, not official).** A collector/dealer blog puts average circulating-coin relief at about 0.3–0.5 mm, and the 1907 Saint-Gaudens high-relief double eagle at "perhaps 3 mm" — [shopglobalcoin.com](https://shopglobalcoin.com/blogs/blog/beyond-relief-pushing-the-boundaries-of-coin-design)
- **US Mint position (no number).** The Mint's 2022 Biennial Report to Congress treats relief height as one of several interdependent striking factors, alongside die shape, stamping force and face curvature. It discusses lowering relief as part of die-curvature work but gives no numeric limit — [US Mint 2022 Biennial Report (PDF)](https://www.usmint.gov/content/dam/usmint/reports/2022-USM-Biennial-Report_P5_FINAL.pdf). The Mint's "Anatomy of a Coin" page defines relief only as the raised part of the design — [US Mint](https://www.usmint.gov/learn/collecting-basics/anatomy-of-a-coin)
- **History: relief was lowered for production.** The ultra-high-relief double eagle and the 1921 Peace dollar were too hard on dies, and the Mint lowered relief from 1922 — [APMEX](https://learn.apmex.com/learning-guide/coin-collecting/what-are-high-relief-and-ultra-high-relief-coins/)
- **Digital bas-relief: Weyrich et al. 2007.** "Digital Bas-Relief from 3D Scenes" (Weyrich, Deng, Barnes, Rusinkiewicz, Finkelstein, ACM TOG 26(3), SIGGRAPH 2007) compresses depth gradients nonlinearly rather than depth values. It then rebuilds the height field by solving a Poisson equation, which keeps fine detail while the relief stays shallow — [Semantic Scholar](https://www.semanticscholar.org/paper/Digital-bas-relief-from-3D-scenes-Weyrich-Deng/67aa2cf15f88989047276c71f5c1247d4e28d303); [ResearchGate](https://www.researchgate.net/publication/220184550_Digital_bas-relief_from_3D_scenes)
- **Older depth-domain methods lose detail.** Methods that compress raw depth "easily lose details when the compression ratio is large" — [arXiv 1912.13140](https://arxiv.org/pdf/1912.13140)
- **Histogram-equalization variant.** Adaptive Histogram Equalization (AHE) relief applies gradient-weighted histogram equalization to model depth values — [ResearchGate: Bas-Relief Generation Using AHE](https://www.researchgate.net/publication/24409876_Bas-Relief_Generation_Using_Adaptive_Histogram_Equalization)
- **Silhouettes and depth gaps.** Related work detects the outer silhouette and reduces large depth gaps before compressing, so the final relief has no cliff-like discontinuities — [Cardiff ORCA: Bas-Relief Modeling from Normal Images](https://orca.cardiff.ac.uk/id/eprint/58823/1/basrelief_11_16.pdf); [Preserving detailed features in digital bas-relief making](https://www.researchgate.net/publication/220221742_Preserving_detailed_features_in_digital_bas-relief_making)
- **Relief from a single photo or 2D image is an active research area,** e.g. Photo2Relief (2023), which makes the human subject stand out from the background — [arXiv 2307.11364](https://arxiv.org/pdf/2307.11364)
- **ZBrush workflow.** Maxon's ZBrush docs describe "Project BasRelief": the whole model, including its SubTools, is projected as a relief onto a selected SubTool from the current view. A "Relief Step Tolerance" slider controls the regions between features; the page text explaining that slider was truncated when fetched. "Make BasRelief" creates a relief alpha the size of the document — [Maxon ZBrush help: Bas Relief](https://help.maxon.net/zbr/en-us/Content/html/user-guide/3d-modeling/sculpting/bas-relief/bas-relief.html)
- **ZBrush vs ReliefMaker (vendor comparison).** A comparison by the ReliefMaker vendor says native ZBrush relief flattens detail near the top, and that ReliefMaker keeps more depth at oblique viewing angles. It is a vendor source — [reliefmaker.com](https://www.reliefmaker.com/bas-reliefs-relief-maker-vs-zbrush-relief/)
- **Hobby technique.** Use a 3D model to make bas-relief alpha/height images — [The Art Squirrel](https://theartsquirrel.com/3699/making-bas-relief-alpha-images-using-3d-models/)

### Inferences
- The gradient-compression principle maps directly onto FDM: an FDM top face already quantizes height into 0.2 mm steps (section 3). Most of the readable information in a relief should therefore sit in the outline and in the slopes at edges, where the nozzle places walls accurately, not in subtle height changes across the field.
- Coin relief (about 0.3–0.5 mm) is only 1.5–2.5 layers at 0.2 mm, which is far too few steps for modelled form. A printed relief viewed at arm's length needs more depth than a coin. The shop's own working depths from printed models are 0.6 mm brick courses, 0.4–0.6 mm joints and 0.8–1.2 mm frames (DETAIL_STANDARD rule 6, in-repo). For a figurative relief, a total relief depth of a few millimetres (10–20+ layers) is needed for a domed form to read as a curve rather than a staircase.
- Layering foreground over background: medallic practice and the silhouette-first digital methods both suggest separating planes by a clear step at the outline, then compressing the interior. On FDM, that step is best made a whole number of layers (rule 2 below).
- Undercuts, which classical relief uses to throw a shadow line under an edge, are overhangs on FDM. They are limited to about 45° from vertical, and this shop designs to about 37°. A chamfered or stepped edge gives a similar shadow line without an overhang.

### Gaps
- No US Mint, Royal Mint or medallic-art-society document with numeric relief-depth or depth-ratio guidance was found. Sculptors' compression ratios (for example "compress depth to 1/10") were not found in a citable source.
- The exact compression parameters in Weyrich 2007 were not retrieved; only citing papers were read.
- Blender's tools for making a height field from a 2D image (displace modifier, depth-map add-ons) were not researched in this pass.

---

## 2. Design rules for flat charms, pendants, keychains and ornaments on FDM

### Takeaway
Published rules of thumb cluster around 3–5 mm total thickness for a carried charm, a 4–5 mm ring hole with about 3 mm of material around it, and a 0.3–0.8 mm chamfer on the bed edge. Raised or sunk detail should be at least about 0.5–1 mm wide and 0.3–0.5 mm deep. This shop's own toolpath tests are tighter and more useful for the P1S:
- Lettering at least 3 mm tall (2 mm on an up-facing face).
- Separate islands and dots at least 0.8 mm across.
- Grooves at least 0.4 mm wide.
- Every level edge on the 0.2 mm layer grid.

### Cited Findings
**Thickness, hole, edges (rules of thumb):**
- **Thickness.** About 3 mm minimum tag thickness, with 3 mm of solid material around the hole — [JLC3DP](https://jlc3dp.com/blog/3d-printed-keychains-tips). A 3–5 mm range is suggested by [3D-P.eu](https://3d-p.eu/how-to-make-a-3d-printed-keychain-step-by-step-tutorial/). Vextrude says 4–5 mm is the practical range and that below about 3 mm the part flexes noticeably — [Vextrude](https://vextrude.com/blog-3d-printed-keychain). An image-to-tag tool suggests 0.8–1.2 mm, a range that suits thin logo plates rather than pocket charms — [MakerTools3D](https://makertools3d.com/image-to-keychain)
- **Ring hole.** 4–5 mm diameter for a standard split ring — [Meshcast](https://meshcast.app/keychain); at least 4 mm — [Vextrude](https://vextrude.com/blog-3d-printed-keychain). A hole too close to the edge leaves a thin bridge that snaps (same sources).
- **Orientation.** Print flat. A charm printed on edge bends across the layer lines and snaps along a line — [Vextrude](https://vextrude.com/blog-3d-printed-keychain)
- **Bed-edge chamfer.** About 0.3 mm on every edge touching the bed, to stop first-layer "elephant foot" forming a lip (matters only without a brim) — [Hydra Research design rules](https://www.hydraresearch3d.com/design-rules). Meshra suggests 0.4–0.8 mm — [Meshra](https://meshra.ai/blog/chamfer-vs-fillet-3d-printing). Hubs: add a 45° chamfer or radius on every edge touching the plate — [Hubs FDM design guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/)
- **Material.** PETG or ABS outlast PLA for a keychain carried in a warm pocket or car — [Meshcast](https://meshcast.app/keychain)

**Raised (embossed) and sunk (engraved) detail (published rules of thumb, which disagree):**
- Forge Labs: embossed at least 1 mm wide × 0.5 mm high; debossed at least 1 mm wide × 0.3 mm deep — [Forge Labs FDM guide](https://forgelabs.com/design-guides/fdm)
- SAIC (Stratasys F370 spec): embossed and engraved detail at least 1 mm — [SAIC](https://sites.saic.edu/aoc/f370-design-specifications/)
- Layer X: engraved text at least 0.3 mm deep and 0.5 mm wide — [Layer X](https://layerx3d.in/blog/fdm-design-rules-wall-thickness-overhangs-bridging-tolerances)
- Hubs' own FDM page gives no emboss/engrave figure. Its SLS guide gives 1 mm emboss/engrave and 2 mm font height — [Hubs SLS](https://www.hubs.com/knowledge-base/how-design-parts-sls-3d-printing/); its material-jetting guide gives 0.5 mm — [Hubs MJ](https://www.hubs.com/knowledge-base/how-design-parts-material-jetting-3d-printing/)
- Hubs' general guide: every printer handles walls over 0.8 mm — [Hubs key design considerations](https://www.hubs.com/knowledge-base/key-design-considerations-3d-printing/)

**Text size (published, wide spread):**
- Mandarin3D: embossed text at least 1.0 mm stroke, 0.5 mm high, 4 mm character height — [Mandarin3D](https://mandarin3d.com/blog/text-and-engravings-best-practices-for-readable-3d-printed-text)
- NameSTL, 0.4 mm nozzle with PLA: bold fonts readable from about 5–6 mm, regular weights about 8 mm; a 0.2 mm nozzle roughly halves this — [NameSTL](https://www.namestl.com/3d-print-text)
- Prusa forum users: about 4 mm is the absolute minimum with careful settings; others say 10 mm (about 30 pt) is the comfortable limit on a 0.4 mm nozzle — [Prusa forum: printing small text](https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/printing-small-text/); [Prusa forum: best font](https://forum.prusa3d.com/forum/original-prusa-i3-mk3s-mk3-how-do-i-print-this-printing-help/best-font-to-print-small-letters/)

**This shop's tested numbers (in-repo toolpath measurements; tighter than the published ones):**
- Raised lettering scores clean (≥ 0.95) from **3 mm** tall on either face. **2 mm** is usable only on a face printed upward (0.92); on an upright face, 2–2.5 mm comes out rough (0.86). A 0.2 mm nozzle reads cleanly from **1.5 mm** — `FINE_DETAIL_RESEARCH.md` / `DETAIL_STANDARD.md` rule 10
- **Islands, dots and colour islands under 0.8 mm across are dropped** on a top face, not shrunk. 0.4 and 0.6 mm dots vanished. On a 0.2 mm nozzle, dots down to 0.4 mm survive — rule 11
- An upright groove **0.4 mm wide** keeps its full depth from 0.1 to 1.0 mm (±0.01 mm). Ribs 0.2–1.0 mm wide all print. Anything handled, or standing out further than its own width, gets **at least 1.2 mm (3 beads)**. An isolated pin needs **at least 1.0 mm** across — rule 5
- Level edges snap to whole layers: at 0.20 mm layers a 0.3 mm groove printed 0.4 mm and a 0.3 mm ridge printed 0.2 mm, so **put every height on the 0.2 mm grid** (rule 2). A 0.1 mm level groove prints a full 0.2 mm layer, which is enlarged, not lost (rule 3)

**Gaps and slots that print open:**
- The basic unit of accuracy is one extrusion width, about 0.45 mm on a 0.4 mm nozzle. G-code places the bead's centreline, so the plastic spreads about 0.225 mm to each side. Gaps finer than about 0.1 mm get lost — [Prusa forum: minimum reliable printing distances](https://forum.prusa3d.com/forum/prusa-core-one-hardware-firmware-and-software-help/what-are-the-minimum-reliable-printing-distances/)
- A narrow slot's fate depends on extrusion width × perimeter count, not nozzle size alone. An 0.8 mm slot can be filled in unless the extrusion width and perimeter count allow it — [LayerCraftLog](https://layercraftlog.com/fdm-printing/how-does-extrusion-width-relate-to-nozzle-size-and-print-resolution)
- Print-in-place separation is easy down to about 0.25 mm; about 0.1 mm is possible with tricks (same Prusa thread). Fit clearances: 0.2 mm total for a snug fit, 0.4 mm total for sliding — [Sovol](https://www.sovol3d.com/blogs/news/fdm-3d-printing-tolerances-clearances-how-to-design-parts-that-fit)

**Layered multi-colour plates and raised outlines:**
- **Colour-change-by-layer on a single nozzle.** Design a recess (or raised layer), pause or colour-change at the layer where it ends, and finish the top in a contrasting colour. The swap height depends on layer height. Purge 50–100 mm of new filament or the colours mix. Lift the nozzle quickly on pause so it does not melt the print — [MatterHackers](https://www.matterhackers.com/articles/how-to-print-in-multi-color-with-a-single-extruder); [Kingroon](https://kingroon.com/blogs/3d-printing-guides/how-to-make-3d-printed-keychains-a-step-by-step-tutorial); [Printables multicolor keychain example](https://www.printables.com/model/825456-one-piece-keychain-porte-cle-single-extruder-or-mm)
- **Prefer large colour regions over tiny islands** for beginner-friendly multi-colour work — [Meshcast](https://meshcast.app/guides/multicolor-3d-printing-without-ams); [Sovol](https://www.sovol3d.com/blogs/news/multicolor-printing-without-waste-a-beginner-s-guide-to-less-mess)
- **AMS colour detail.** One guide advises against colour detail under about 5 mm, and tiny colour segments under-extrude — [Geeky Inc AMS guide](https://www.geekyinc.com/multi-color-3d-printing-anime-figures-the-ams-guide-for-p1s-x1c-2026/); [Bambu forum](https://forum.bambulab.com/t/problems-with-colored-miniatures/160232). This is consistent with the in-repo 0.8 mm island floor, with about 1.5 mm preferred for pupils, berries and buttons.

### Inferences
- **Raised outline vs engraved line on a flat charm printed face-up.** Both are made by the nozzle's XY placement, so both widths are accurate to roughly a bead. A raised outline is a positive feature: at 1.2 mm or more (3 beads) it is robust, and it can take a top colour swap. An engraved line is a negative feature and needs at least about 0.4–0.5 mm of width to stay open. Its depth should be a whole number of layers (0.2, 0.4, 0.6 mm). Engraved lines suit single-colour pieces; raised outlines with a colour change at their base give the "enamel pin / cloisonné" look in one material change.
- **Cut-through negative space** (openwork in an ornament) is a vertical wall on every edge, so it prints at XY accuracy. Narrow ties left between cut-outs must meet the 1.2 mm handled-feature rule, or they snap (the fragility class `tools/fragility.py` checks).
- **A combined working spec for a P1S charm** (synthesis, not a single cited source): 3–4 mm thick, 4–5 mm hole with at least 3 mm of material around it, 0.4 mm chamfer at the bed, raised detail 0.6–1.0 mm proud (3–5 layers) and at least 1.2 mm wide, engraved lines at least 0.5 mm wide and 0.4–0.6 mm deep, text at least 3 mm tall, no island under 0.8 mm (prefer 1.5 mm).
- **Edge rounding.** The top edge of a flat charm can be rounded only as a stair of layer steps. A 45° chamfer of 2–3 layers (0.4–0.6 mm) prints cleaner than a fillet at 0.2 mm layers (DETAIL_STANDARD rule 4, in-repo: a 1 mm dome is 5 stacked rings at 0.20 mm).

### Gaps
- No Bambu Lab-published charm or keychain design guide was found.
- No controlled published test of "minimum open slot width on a 0.4 mm nozzle" was found. Every source recommends printing a slot-gradient coupon. The in-repo coupon measured grooves, not through-slots.
- Hubs' FDM page has no emboss/engrave or minimum-feature figures (checked directly); its older table format is no longer on the page.

---

## 3. FDM limits on detail: positive and negative features, vertical vs horizontal resolution, Arachne, ironing, 0.2 vs 0.4 mm nozzle

### Takeaway
The nozzle sets the smallest shape (XY). The layer height sets the smallest step (Z). Detail across a vertical face (lines running up the face) is placed to about ±0.01 mm. Detail up the face, and the shape of a top face, is quantized to whole layers. On a 0.4 mm nozzle, dropping from 0.2 to 0.08 mm layers does almost nothing for letters or dots. A 0.2 mm nozzle roughly halves the minimum lettering and island size, at the cost of speed and clog risk.

### Cited Findings
- **Positive features are limited by extrusion width.** About 0.45 mm on a 0.4 mm nozzle, with the bead spreading about 0.225 mm each side of its centreline — [Prusa forum](https://forum.prusa3d.com/forum/prusa-core-one-hardware-firmware-and-software-help/what-are-the-minimum-reliable-printing-distances/)
- **Arachne.** Bambu's wiki says thin features are widened to about 85% of the nozzle. OrcaSlicer's says features under the minimum feature size are skipped. (Both are cited in-repo; the exact cut-off in Bambu Studio may differ from PrusaSlicer's) — [Bambu wiki: wall generator](https://wiki.bambulab.com/en/software/bambu-studio/wall-generator); [OrcaSlicer wiki](https://github.com/orcaslicer/orcaslicer/wiki/quality_settings_wall_generator)
- **Tested, in-repo: XY vs Z.**
  - Upright grooves 0.1–1.0 deep printed every depth to ±0.01 mm at every layer height.
  - Level grooves and ridges snapped to whole layers (0.3 mm groove → 0.4 mm at 0.2 mm layers).
  - A 1.0 mm boss was 5 layers at 0.20 mm (a stack of rings), 8 layers at 0.12 mm and 12 at 0.08 mm.
  — `DETAIL_STANDARD.md` measured tables
- **Tested, in-repo: layer height vs nozzle.** On the 0.4 mm nozzle, going from 0.20 to 0.08 mm layers changed "almost nothing for letters or dots". The 0.2 mm nozzle gave lettering clean from 1.5 mm and kept 0.4 mm dots — `FINE_DETAIL_RESEARCH.md`
- **0.2 mm nozzle trade-offs.**
  - Bambu sells a P1-series hotend with a 0.2 mm nozzle — [3DJake](https://www.3djake.ch/en-CH/bambu-lab/hotend-p1-series)
  - Community guidance is 0.05–0.12 mm layers with it — [Cal Poly](https://grandavehousing.calpoly.edu/news/bambu-lab-p1s-all-about); [Bambu forum](https://forum.bambulab.com/t/minimum-layer-height-limbo-how-low-can-we-go/154852)
  - It clogs more and needs retraction tuning — [Bambu forum](https://forum.bambulab.com/t/just-cannot-print-with-a-0-2mm-nozzle/29260)
- **Variable layer height.** Bambu Studio's adaptive and smooth variable layer height ranges 0.08–0.28 mm on a 0.4 mm nozzle — [Bambu wiki: adaptive layer height](https://wiki.bambulab.com/en/software/bambu-studio/adaptive-layer-height); forum users run adaptive at about 0.75–0.85 and then smooth — [Bambu forum](https://forum.bambulab.com/t/adaptive-layer-height-and-smoothing-issues/165945)
- **Precise Z height.** In Bambu Studio since about 1.9, it adjusts the last layers so a top lands at its true height. It fixes the top surface only — [Bambu wiki: layer height](https://wiki.bambulab.com/en/software/bambu-studio/layer-height)
- **Overhangs and bridges.** About 45° without support for most materials; bridges under 5 mm print without visible sag — [Hubs FDM guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/). Tested in-repo: exactly 45° drew 29,332 support moves in the gate slicer, while 35–36° drew none, so the shop designs to about 37° (DETAIL_STANDARD rule 7)
- **Pins.** Hubs: vertical pins under 5 mm diameter can be weak or fail; add a fillet at the base — [Hubs FDM guide](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/). (In-repo tested: a 1.0 mm isolated pin prints, but is fragile.)
- **Print orientation for detail.** Terrain modellers print brick walls upright rather than flat for surface detail — [RMweb](https://www.rmweb.co.uk/topic/166557-more-3d-printed-architecture/); [Dakka](https://www.dakkadakka.com/dakkaforum/posts/list/815484.page). Matches in-repo letters: 0.92 face-up vs 0.86 upright, while relief across an upright face holds to ±0.01 mm.
- **Matte vs silk.** Vendor sources say matte PLA hides layer lines and lets relief read, while silk's sheen amplifies lines (vendor claims, not controlled tests) — [Siddament](https://siddament.com.au/blogs/filament-guide-au/matte-vs-silk-pla); [Snapmaker](https://www.snapmaker.com/blog/pla-matte-vs-basic/)

### Inferences
- **Orientation decides what each kind of detail can do on a flat charm or relief plaque:**
  - *Printed face-up:* the outline and all XY detail are sharp, and every height is a layer step. Best for raised outlines, lettering and colour layers.
  - *Printed standing upright:* the relief profile is placed accurately (rule 1), and the outline's vertical edges become layer-stepped instead. Best for relief whose modelled depth matters, such as a figurative plaque or a portrait medallion.
- **Ironing only smooths flat top surfaces.** It suits the flat field of a charm, or the top of a raised colour layer. It cannot smooth a domed relief (general slicer knowledge; Bambu's ironing wiki page returned HTTP 402, so this is not verified from Bambu's own text).
- For figurines, faces, hands and buttons under about 2 mm tall: the 0.4 mm nozzle at 0.12 mm or 0.08 mm layers, or the 0.2 mm nozzle (DETAIL_STANDARD rule 4).

### Gaps
- Bambu's ironing parameter page (wiki.bambulab.com/en/software/bambu-studio/parameter/ironing) returned HTTP 402, so default ironing flow, spacing and speed were not retrieved.
- No Formlabs FDM-specific numbers were found; Formlabs publishes for SLA. Prusa's Knowledge Base has no official minimum-text figure that this research found; only forum posts.
- CNC Kitchen test data on minimum feature size was not found in this pass (the CNC Kitchen BumpMesh texture tool is noted in `FINE_DETAIL_RESEARCH.md`, with texture depths of 0.3–0.8 mm).

---

## 4. How successful makers design printed ornaments, charms and figurines to look good at small size

### Takeaway
The evidence is thin and mostly from forums and model pages, but it all points one way: exaggerate. Make figures larger than true scale, enlarge eyes, buttons and letters, use large flat colour regions rather than fine colour detail, and print in matte.

### Cited Findings
- **Scale up for FDM.** FDM-focused miniature designers deliberately scale up. One designs at 40 mm "for clean results on a 0.4 mm nozzle". Another makes FDM-specific minis "slightly larger than classic 28/32 mm" so faces and textures survive — [MakerWorld model 3043736](https://makerworld.com/en/models/3043736); [MyMiniFactory supportless FDM orcs](https://www.myminifactory.com/object/3d-print-support-free-supportless-fdm-null-brutes-gunners-squad-sci-fi-orc-proxy-no-supports-793555)
- **Avoid tiny colour detail.** Multi-colour figure guidance warns against colour detail under about 5 mm — [Geeky Inc](https://www.geekyinc.com/multi-color-3d-printing-anime-figures-the-ams-guide-for-p1s-x1c-2026/)
- **Large colour regions read best.** Single-extruder multi-colour keychains on Printables use large flat colour regions and a colour change at a set layer — [Printables 825456](https://www.printables.com/model/825456-one-piece-keychain-porte-cle-single-extruder-or-mm); [Printables 378281](https://www.printables.com/model/378281-fnaf-purple-guy-multicolor-keychain)
  - Both examples depict licensed characters (One Piece, FNAF). They are cited for technique only, not as a legal model to copy (see section 5).

### Inferences
- **Practical design moves:**
  - Silhouette first: the outline must read at thumbnail size, matching the CLAUDE.md retail bar.
  - Make eyes and pupils separate colour islands of 1.5 mm or more, or press-in parts.
  - Give every separate shape at least 0.8 mm.
  - Put a contrasting raised outline (1.2 mm or more) around colour fields.
  - Keep the number of colour changes per layer low.

### Gaps
- No sales-data study of which design features drive charm and ornament sales on Etsy or MakerWorld was found.
- No MakerWorld design guide for ornaments or charms was found in this pass.
- A targeted look at top-selling ornament listings (layer count, thickness, colour count) is still needed. Per CLAUDE.md, bulk scraping of Etsy is off-limits; manual review or `/research` would be the route.

---

## 5. Legal side and originality: copyright in characters and jewelry, style vs expression, references vs tracing, Etsy policy, public domain

### Takeaway
- **What US copyright protects:** the specific visual expression of a character or ornament: its facial features, body shape, clothing and so on. It does not protect a style, an idea or a genre, or a common symbol.
- **References vs tracing:** studying references to learn and then drawing your own form is on the safe side. Tracing or transforming one specific artwork into a 3D relief reproduces its expression and makes a derivative work, which needs permission unless the source is public domain.
- **Etsy:** items made with computerized tools, which includes 3D printers, must come from the seller's own original design. That text dates from 10 June 2025. The claim that it took effect in August 2026 is disputed: the 11 Aug 2026 Prohibited Items change concerned animal fur.
- **Public domain sources:** Met and Smithsonian Open Access CC0 images are usable commercially. Check each object's rights statement and keep a record.

### Cited Findings
**US Copyright Office, Compendium (Third Edition), Chapter 900:**
- **§911 Characters.**
  - "The original, visual aspects of a character may be protected by copyright if they are sufficiently original. This may include the physical attributes of the character, such as facial features and specific body shape, as well as images of clothing and any other visual elements."
  - Registration "does not extend to unfixed characteristics … Nor does it cover the name or the general idea for the character."
  - Applicants should not claim "character concept, idea, or style."
  - [Compendium ch. 900 (PDF)](https://www.copyright.gov/comp3/chap900/ch900-visual-art.pdf)
- **§907.1 Derivative works.**
  - "Sculptures based on drawings" are listed as derivative visual-art works. They are registrable only for "a sufficient amount of new authorship". "Mere reproductions" and digital scans are not.
  - Directly relevant: turning someone's 2D drawing into a relief or figurine is a derivative work of that drawing.
  - [Compendium ch. 900](https://www.copyright.gov/comp3/chap900/ch900-visual-art.pdf)
- **§907.2 Third-party material.** Third-party clip art used in a work must be excluded from the claim. Letters and geometric shapes need not be — [Compendium ch. 900](https://www.copyright.gov/comp3/chap900/ch900-visual-art.pdf)
- **§908 Jewelry.**
  - Jewelry is typically protected as a sculptural work and as a work of artistic craftsmanship, covering "shape, color, orientation, or other creative aspects", but not functional parts such as "a plain hook or clasp".
  - It is not registrable when the piece is a "mere variation on a common or standardized design or familiar symbol". The Office's own example: a standard cross on a cord is refused.
  - Jewelry incorporated into useful articles gets the separability test (§924.3).
  - [Compendium ch. 900](https://www.copyright.gov/comp3/chap900/ch900-visual-art.pdf)

**Style vs expression:**
- Copyright protects expression, not ideas — [USPTO copyright basics](https://www.uspto.gov/ip-policy/copyright-policy/copyright-basics)
- In Jangle Vision v. Alexander Wang, the court treated an artistic style as an unprotectable idea — [Mondaq](https://www.mondaq.com/unitedstates/copyright/1398678/two-courts-two-ad-campaigns-and-copyrights-idea-expression-dichotomy)
- **Merger and scènes à faire:** when an idea can be expressed only a few ways, those expressions are not protected — [Digital Law Online](https://digital-law-online.info/lpdi1.0/treatise9.html); [IR Global](https://irglobal.com/article/understanding-the-idea-expression-dichotomy-in-copyright-law/)
- Courts find the line hard to draw. In LB Plastics v Swish (UK), infringement was found without direct copying of expression — [IR Global](https://irglobal.com/article/understanding-the-idea-expression-dichotomy-in-copyright-law/)

**Etsy:**
- The Creativity Standards say items made with computerized tools "must be produced based on a seller's original design and are often personalized or customized to a buyer's specification." Reselling purchased files, scans or bundles is not original even with a commercial licence. Production partners must be listed — [Listadum summary](https://www.listadum.com/blog/etsy-creativity-standards); [eRank](https://help.erank.com/blog/recent-updates-to-etsy-standards-and-policies/); primary page [etsy.com/legal/creativity](https://www.etsy.com/legal/creativity) (it returned 403 to the fetch tool and was not read directly)
- **Date conflict, to be stated explicitly.**
  - Growtsy (read 28 Aug 2026) quotes the Creativity Standards stamp "Last updated on Jun 10, 2025". It says the Prohibited Items header reads "updated on August 11, 2026 with changes to Section 2" (Animal Products, a ban on natural fur), with no mention of computerized tools, templates, AI or POD — [Growtsy](https://www.growtsy.com/etsy-changes)
  - ShieldMyShop and similar blogs claim an August 2026 "original design" rule for 3D-printer sellers — [ShieldMyShop](https://www.shieldmyshop.com/blog/2026-06-30-etsy-original-design-rule-cricut-laser-cutter-3d-printer-sellers-august-2026); [The Artisan Business Co.](https://theartisanbusinesscompany.com/etsys-august-rule-change-and-what-it-means-for-your-business-model/)
  - Growtsy's reading is the better documented. Note that CLAUDE.md's "Aug 11, 2026 Prohibited Items Policy update" line appears to repeat the disputed blog claim. **The requirement itself is real either way** (Creativity Standards, June 2025).
- **IP takedowns.**
  - Etsy's help centre says its IP Policy "requires us to remove or disable content" on receiving an infringement report. Etsy does not judge infringement and gives the seller the complainant's contact details. Do not relist until the matter is resolved. "Repeat reports of infringement may result in the loss of account privileges" — [Etsy Help](https://help.etsy.com/hc/en-us/articles/360034079714-What-to-Do-if-You-Receive-a-Notice-of-Intellectual-Property-Infringement)
  - No numeric strike threshold is published (third-party analysis) — [ShieldMyShop](https://www.shieldmyshop.com/blog/2026-06-29-how-many-ip-strikes-before-etsy-suspends-shop-repeat-infringer-policy)

**Public domain sources:**
- The Met's Open Access lets you "download, share, modify, and distribute the data for any purpose, including commercial and noncommercial use" for public-domain works, marked CC0 on each object page — [The Met: Image and data resources](https://www.metmuseum.org/policies/image-resources); [Met Open Access intro](https://www.metmuseum.org/perspectives/open-access-at-the-met); [Wikimedia Foundation](https://wikimediafoundation.org/news/2017/02/07/the-met-public-art-creative-commons/)
- Smithsonian Open Access releases images under CC0 but disclaims liability for unknown rights, so check each item's rights statement — [My Modern Met](https://mymodernmet.com/smithsonian-open-access-public-domain/); [Harvard TagTeam](https://tagteam.harvard.edu/hub_feeds/3997/feed_items/2626277/content)
- Aggregators such as rawpixel's "public domain cherub" collection, and pdimagearchive, host scans of antique book plates and museum items. Confirm the licence at the original institution — [rawpixel](https://www.rawpixel.com/search/public%20domain%20cherub?page=1&path=1522&sort=curated); [PD Image Archive](https://pdimagearchive.org/galleries/sources/the-metropolitan-museum//); [Public Domain Review](https://publicdomainreview.org/collection/a-selection-from-the-met-s-public-domain-collection-now-free-from-all-restrictions)

### Inferences (not legal advice)
- **Safe practice for this shop:**
  1. Use references to learn about the subject (how a cherub's wing joins the shoulder, Victorian ornament motifs) and gather several, then design a new form. Do not trace or height-map one specific copyrighted image.
  2. Keep a provenance file per design: references viewed, their source and licence, and the shop's own sketches or AI prompts. The CLAUDE.md "provenance manifest" gap would be closed by this.
  3. Use public-domain sources, such as classical putti and Victorian engravings from Met or Smithsonian CC0 items, as direct bases when a close adaptation is wanted. Save the object URL and rights statement.
  4. Never use named or licensed characters or brand marks (the One Piece and FNAF keychains above are exactly the takedown risk). Trademark screening of titles and tags is already advisory in `tools/trademark_screening.py`.
  5. Simple common forms (a plain heart, a standard star, a basic cross) carry little copyright either way. The value, and the protection, lies in the specific sculpted expression the shop adds.
- **The 3D version adds authorship but does not launder a copied source.** Under Compendium §907.1, turning a 2D image into a relief adds new authorship, but the result is still a derivative of the source. If the source is copyrighted and unlicensed, the relief infringes.
- **Etsy's original-design rule is stricter than copyright.** Even a lawfully licensed design, or a CC0 public-domain image used as-is, may not count as "the seller's original design" under the Creativity Standards (reported by Listadum and ShieldMyShop; not read from Etsy's primary page). Public-domain sources are safest when they inspire or are substantially reworked, not reproduced.

### Gaps
- The primary Etsy Creativity Standards and IP Policy pages could not be fetched (HTTP 403). Quotes come from secondary summaries and Etsy's help centre.
- The Etsy pages do not say whether an AI-generated design counts as "original" for the computerized-tools rule. Etsy separately requires AI disclosure; see CLAUDE.md.
- US public-domain cut-off: works published 95+ years ago (in 2026, works published in 1930 or earlier) are generally US public domain. This is general knowledge, **not verified from a source in this pass**. Victorian clip art (pre-1901) is safely old, but a modern scan, colourization or redrawing can carry its own rights.
- No case law specific to 3D-printed fan art or relief conversions was retrieved. Star Athletica v. Varsity Brands (2017), the separability test for useful articles that Compendium §924.3 references, was not read in full.
