# Detail test piece: MakerWorld upload, ready to go

For Scott's own MakerWorld account, kept private. Nothing here has been
posted: MakerWorld needs his sign-in, and this cloud session has no browser
and is blocked by makerworld.com.

## Files to upload

- `detail_coupon.3mf`: the piece, one part, standing as it prints.
- Images, in this order:
  1. `detail_coupon_key.png`: what each row tests, with every size labelled.
  2. `detail_coupon_three_quarter.png`
  3. `detail_coupon_front.png`
  4. `detail_coupon_top.png`
  All four are renders, not photos. Replace them with a photo once it's printed.

## Text to paste

**Title:** Fine Detail Test Piece for a 0.4 mm Nozzle

**Description:**

A wall of 49 tiny features in seven rows, each row grading one thing from
too small to plenty. Print it, look at it under a raking light, and you can see
which sizes your printer keeps.

Rows, top to bottom (smallest on the left, in mm):
- Ribs, width: 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0
- Upright grooves, depth: 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0
- Bosses (half-domes), diameter: 0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.6
- Ridges 1.0 tall, how far out: 0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 1.0
- Level grooves, height: 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2
- Chamfered ridges, height: 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2
- Square ridges, height: 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2

**Printing:** PLA, 0.2 mm layers, 0.4 mm nozzle, supports off, standing up as
it opens. 90 × 6 × 46 mm. About 33 minutes and 14 g (Bambu Studio, P1S,
PLA Matte, standard 0.2 mm profile).

**What to look for:** upright detail holds its size at any layer height. Level
detail snaps to whole layers, so at 0.2 mm a 0.3 groove prints as 0.4 and a
0.3 ridge as 0.2. Small domes come out as stacked rings.

**AI:** designed with the help of AI tools (OpenSCAD written by Claude).
Tick MakerWorld's AI-assisted box if the form asks.

## Checks

- `tools/mesh_gate.py`: passes. Closed, one body, 24.9 cm³.
- Bambu Studio slice (`tools/bambu_slice.py`, P1S, PLA Matte, 0.2 mm
  standard): 230 layers, 0 support lines, 33 min 5 s, 14.4 g.
