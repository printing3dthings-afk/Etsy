TEST - Scarf Seam Test Bar - upload pack (PRIVATE until Scott prints it)

Profiles (all verified end-to-end; seam settings read back from each
finished file's config, scarf difference proven in gcode band stats):
- ScarfBar_Aligned_P1S.3mf - 25 min 39 sec - 23.44 g (band: 271 segments / 4329.0 mm of extrusion path)
- ScarfBar_Random_P1S.3mf - 28 min 4 sec - 23.44 g (band: 426 segments / 4371.5 mm of extrusion path)
- ScarfBar_Scarf_P1S.3mf - 29 min 55 sec - 23.45 g (band: 2317 segments / 6177.1 mm of extrusion path)

Gallery: images/01-plate.png (plate render from the Aligned file) +
02-centre-crop.png + 03-corner-crop.png. Renders, not photos - swap in
Scott's real print photos after he prints them.

Copy: listing-copy.md (model description + per-profile copy).

Notes: probe finding worth keeping - the scarf switch is the FILAMENT
preset's filament_scarf_seam_type; the process-side seam_slope_type
alone changed nothing in the gcode (../probe/). Ironing OFF.
