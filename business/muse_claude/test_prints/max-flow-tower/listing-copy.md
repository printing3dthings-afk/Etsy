# TEST - Max Flow Tower

**Title (MakerWorld, <= 50 chars):** TEST - Max Flow Tower

**What it tests:** the filament's max volumetric speed - the melt-rate
cap (mm3/s) that decides how fast the hot end may actually extrude on
long walls, whatever the speed settings ask for. The tower is four
stacked slabs with 76 mm long walls (long enough for the toolhead to
reach full speed and sit on the cap) stepping 36 -> 27 mm deep; each
slab's front-bottom edge is chamfered at 45 degrees, and that sloped
underside is where an over-asked cap shows first: matte, rough,
under-extruded plastic where the melt could not keep up.

**The three profiles (the profiles ARE the test):** identical tower,
identical settings - only the filament preset's max volumetric speed
differs, verified in each file's config:

- F12: max volumetric speed 12 mm3/s - verified slice 1 h 1 min - 40.35 g.
- F18: max volumetric speed 18 mm3/s - verified slice 51 min 41 sec - 40.35 g.
- F24: max volumetric speed 24 mm3/s - verified slice 49 min 1 sec - 40.35 g.

Note the verified times fall as the cap rises - the cap is really
binding on these long walls, which is the point of the geometry.

**How to judge:** print all three, then read band by band (bottom slab
= longest sustained demand): surface gloss and roughness on the walls,
and the 45-degree undersides for under-extrusion. The highest cap
whose bands still match the 12 mm3/s reference is your filament's
honest ceiling on this printer; above it you are trading quality for
minutes.

**Record your results:**

| Cap | Wall gloss | 45-deg undersides | Time | Verdict |
|---|---|---|---|---|
| 12 mm3/s |  |  | 1 h 1 min |  |
| 18 mm3/s |  |  | 51 min 41 sec |  |
| 24 mm3/s |  |  | 49 min 1 sec |  |

**Filament:** matte white PLA, single colour (the stock preset's own
cap is 22 mm3/s, for reference). **Ironing: OFF** - the wall surface is
the measurement. Supports off.

**Per-profile copy (paste into each profile's description box):**

Prints the Max Flow Tower (cap 12 mm3/s): four stacked slabs with 76 mm walls on an engraved base, each slab's front-bottom edge chamfered at 45 degrees. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports off, no ironing. Filament max volumetric speed 12 mm3/s, verified in the file's config. Verified slice: 1 h 1 min - 40.35 g. Compare the bands against the other two caps.

Prints the Max Flow Tower (cap 18 mm3/s): four stacked slabs with 76 mm walls on an engraved base, each slab's front-bottom edge chamfered at 45 degrees. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports off, no ironing. Filament max volumetric speed 18 mm3/s, verified in the file's config. Verified slice: 51 min 41 sec - 40.35 g. Compare the bands against the other two caps.

Prints the Max Flow Tower (cap 24 mm3/s): four stacked slabs with 76 mm walls on an engraved base, each slab's front-bottom edge chamfered at 45 degrees. Matte white PLA, 0.20 mm Standard, 3 walls, 15% infill, supports off, no ironing. Filament max volumetric speed 24 mm3/s, verified in the file's config. Verified slice: 49 min 1 sec - 40.35 g. Compare the bands against the other two caps.
