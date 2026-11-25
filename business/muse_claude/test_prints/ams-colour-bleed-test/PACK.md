TEST - AMS Colour-Bleed Test - upload pack (PRIVATE until Scott prints it)

Profiles (all four verified end-to-end; flush matrix + multiplier read
back from each finished file's config; light-filament usage climbs
1.90 g per step while dark stays at 7.83 g - the purge is real):
- Flush 120: dark->light flush 120 mm3 - verified slice 50 min 43 sec - 15.98 g total (dark 7.83 g / light 8.15 g).
- Flush 240: dark->light flush 240 mm3 - verified slice 52 min 58 sec - 17.88 g total (dark 7.83 g / light 10.05 g).
- Flush 360: dark->light flush 360 mm3 - verified slice 55 min 15 sec - 19.78 g total (dark 7.83 g / light 11.95 g).
- Flush 480: dark->light flush 480 mm3 - verified slice 57 min 26 sec - 21.68 g total (dark 7.83 g / light 13.85 g).

Gallery: images/01-plate.png (plate render from the Flush 240 file) +
02-centre-crop.png + 03-corner-crop.png. Renders, not photos - swap in
Scott's real print photos after he prints them.

Copy: listing-copy.md (model description + per-profile copy).

Thumbnail quirk (preview only, print files verified correct): the
house plate renderer colours the dark island black but renders the
dark main block in a light shade - a plate_parts colour-map quirk on
the split part bodies. The shipped gcode was checked directly:
extruder 1 (dark) prints design x -60..-16 (block) and 26..38
(island); extruder 2 (light) prints -16..60. MakerWorld regenerates
its own imagery on upload regardless.

Notes: the program's only multicolour piece. Built on the house MC
route: forge seed with a genuine multicolour project_settings source
(a 2-filament-trimmed seed was probed and rejected by the slicer -
see ../probe/), four stock-identity filament slots with slots 3-4
holding unused white duplicates (the village MC pattern); only slots
1-2 print. Flush injected into project_settings post-pass1, then
presliced so the values are baked into the sliced file. Ironing OFF.
