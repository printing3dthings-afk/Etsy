# Instagram QR tile (2026-11-25)

Scott: "I want all 3 on one plate to print. Make the prime tower an object and make it a QR
code to the instagram."

- **Code:** `https://instagram.com/onbrandcraftz2026`, QR version 3, M error correction
  (about 15% of it can be lost and it still reads), 29 × 29 modules.
- **Tile:** 78 mm square, 2.4 mm thick, 2.0 mm modules, a 4-module quiet zone and a 2 mm
  black rim, rounded corners.
- **Colours, by height, the same as the signs:** near-black base to 1.6 mm, orange top 0.8 mm.
  The orange is the code's light part; the dark modules are holes showing the black. That's
  dark on light, the polarity every phone camera reads.
- **Built by** `qr_tile.py` (segno for the code, shapely and trimesh for the parts). Each dark
  hole is 0.08 mm bigger a side, for the orange bead's bulge and so diagonal neighbours meet
  instead of pinching to a point.

## Checks
- Product gate PASS, print fidelity 0 flagged, fragility 0 (`logs/`).
- **It decodes** (OpenCV's QR reader):
  - the model's flat view, also blurred, grey and shrunk to 160 px;
  - every extrusion drawn from the plate's real G-code, at full, half and quarter size
    (`../font_options/plate_toolpath.jpg`).
- `images/*as_printed*` draws only outer walls, so its tile looks hollow; it isn't how the top
  prints and wasn't used for the decode check.
- **Not printed or scanned with a phone yet.** Orange on black has less contrast than black
  on white: scan it once it's off the plate.
