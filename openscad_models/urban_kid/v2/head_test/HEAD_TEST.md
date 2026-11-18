# Urban Kid v2: head test print (2026-11-17)

Scott: "Send just the head as a print. I want to see how it turns out."

**What it is:**
- The v2 face, the sly smile (`../research/sculpt_face_sty.py`), at its 190 mm figure size:
  41 x 49 x 31 mm as printed.
- A test of how the face's detail prints, not the figure's head.
- Not printed yet. The pictures are design-review renders, not photos.

## How it's printed and why
- **Face up, the back of the head cut flat on the plate.** Every part of the face is then a
  top surface, where FDM is sharpest. Printed upright, the nose, lids, brows and chin
  overhang and would need support right on the face.
- **Bald, with a short neck.** On the figure the cap covers the crown; this test is about the
  face.
- **Filled solid behind the ears, down to the plate.** That's where the cap and hair go on the
  figure. Left open, the gap between ear and skull needed support.

## File
- **`urban_kid_v2_head_test.gcode.3mf`:** Bambu Studio for the P1S, 0.4 nozzle, PLA Basic,
  0.12 mm Fine, textured PEI, supports off.
- **About 33 minutes and 10.2 g**, from Bambu's own slice.
- Any skin-tone or light filament will do. A light colour shows the detail best.

## Checks
- **Product gate** (`product_gate.txt`): passes everything except min_wall.
  - 0 support moves; watertight; one body; stable on a flat base (12.4 cm², 61% of the
    footprint).
  - **min_wall reads 0.66 mm at the 1st percentile.** Checked point by point:
    - 161 of the 181 thin readings are ray artefacts: their midpoints sit about 3 mm deep in
      solid material.
    - Most of the other 20 are rays skimming the flat bottom on the plate.
    - The rest are slivers where the fill behind the ears meets the skull.
  - The detail check below drops about 1 mm³ there in all. That's acceptable for a test
    print; it would be fixed before this goes on a product.
- **Print fidelity at 0.12 mm** (`fidelity.txt`): 0 flagged.
  - Nothing on the face is dropped or filled in.
  - 0.87 mm³ is dropped in all, as slivers at the ear fill's seam.
- **Fragility:** 0 high, 0 watch.

## What to look at when it's printed
- **Pupils:** do they read as dark spots? Each is a 1.2 mm deep dish.
- **Irises:** are the rings visible?
- **Mouth:** does the lip line read as a crease, and the smile's high corner, dimple and
  smile line as one expression?
- **Upper lids and brows:** do the lids' edges come out crisp, and the V brows with the
  crease between them?
- **Under-eye squint and ears:** are they clean?
- **Report:** a photo straight on and one from the side, and anything that came out soft or
  lumpy.

## Rebuild
```
blender -b human_base_meshes_bundle.blend --python ../research/export_head.py -- sty_dense.ply 4 stylized
python3 ../research/sculpt_face_sty.py sty_dense.ply sty_sculpt.ply
python3 ../head_test.py sty_sculpt.ply OUT_DIR
python3 tools/bambu_slice.py OUT_DIR/head_test.stl:#E8C9A8 -o urban_kid_v2_head_test.gcode.3mf --quality fine
```
