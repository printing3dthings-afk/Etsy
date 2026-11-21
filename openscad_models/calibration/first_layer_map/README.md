# First-layer map (2026-11-21)

Nine 25 mm squares, two layers (0.4 mm):
- the four corners;
- the middle of each edge;
- the centre.

It's for finding the part of the P1S plate that prints badly (Scott, 2026-11-21: "prints in one
corner mess up like it's not actually level"). Two failures that day both started at the back.

`first_layer_map.gcode.3mf`: about 28 minutes and 3 g, including heating and leveling. Tick
"Bed leveling" when you send it.

**Reading it** (look at each square and feel it):
- **Even, smooth, lines just touching:** good.
- **Lines squashed thin and see-through, or rough and ridged:** that spot sits too close to the
  nozzle.
- **Lines round with gaps between them, or the square peels off easily:** that spot sits too far
  from the nozzle.

If the bad squares are all along the back, the back of the bed is out of line with the front.
The bed rides on three lead screws linked by a belt; see Bambu's wiki on the Z timing pulley.
Clean the plate and check for anything under it before touching the mechanics. A photo of all
nine squares is enough for Claude to read.
