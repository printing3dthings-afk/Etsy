# Giant Love Letter: the MakerWorld name customizer

`love_letter_customizer.scad` is the file to attach to the MakerWorld model as
its Parametric Model Maker file.
- **The setting:** NAME is the only one (default `OLIVIA`). The default render
  is the envelope's body with the name raised on the address side, in Fredoka
  SemiBold, sized to fit as in the shipped design.
- **The other prints:** the lid and Cupid are separate prints and aren't in
  this file.

## Why it's built this way (2026-11-05)

MakerWorld renders the file standalone, and its validation gives up after
about 60–75 seconds.

**The shipped body took about 66 minutes under OpenSCAD 2021's CGAL engine.**
- CGAL turns every boolean's operands into Nef polyhedra, at about 0.35 ms per
  facet: measured, 20,480 facets took 7 s and 81,920 took 30 s.
- The body has about 70 skirted relief slabs.
- Cupid's pocket climbs in 20 steps of a 3,739-point outline.
- Even 20 plain slabs on a bare shell took 16 s.

So the boolean structure alone can't get it under a minute.

**The fix:**
- **Computed once:** everything that doesn't change with the name is
  computed once, by the Manifold engine, from `love_letter.scad` itself.
- **One polyhedron:** that body is written into the customizer as a single
  `polyhedron()` of 30,494 triangles, which CGAL takes as it is.
- **The name:** the customizer builds it with the shipped design's own code
  (the same font, size rule and skirted slabs), and unions it with the body
  once.

**Render times:**

| name | CGAL (OpenSCAD 2021) | Manifold |
|---|---|---|
| OLIVIA | 16.4 s | under 1 s |
| Ana | 16.8 s | |
| MARY-JO | 20.9 s | |
| MAXIMILIAN | 24.2 s | |

## How it compares with the shipped design (`check_customizer.py`)

Measured against `love_letter.scad`'s `body_print` with the same name:
- **Bounding box:** identical, 180 × 67.8 × 122 mm.
- **Volume:** 11–12 mm³ less, 0.007%.
- **Where the geometry differs at all:** 34–63 mm³ in total, 0.02–0.04% of the
  body.
- **Cupid in his pocket:** he overlaps the new body exactly as the shipped one,
  0.11 mm³, which is his pegs in their holes.

Each difference is a deliberate change, made because each one cut render time:

| change | how much it moves | volume (OLIVIA) |
|---|---|---|
| The name's curves at 12 segments, not 36 | 0.047 mm | 33.6 mm³ |
| Cupid's pocket outline, simplified to 0.01 mm then grown 0.01 mm | stays at least as big as shipped; Cupid has 0.3 mm clearance | 5.5 mm³ |
| The pocket's top edge at the exact 37° slope its 20 steps of 0.05 mm approximated | — | (included above) |
| The fixed relief's circles at fewer segments | each outline within about 0.04 mm | 10.6 mm³ |
| Manifold's own simplify at 0.001 mm | removes zero-width steps CGAL rejects | — |

Every one of these is far finer than a 0.4 mm nozzle reproduces.

## Rebuilding

- `python3 build_customizer.py` rewrites the .scad from `love_letter.scad`.
  Run it after any change to the design.
- `python3 check_customizer.py` re-measures it.
- Both need an OpenSCAD with the Manifold engine (set `OPENSCAD_FAST`). The
  check also needs OpenSCAD 2021 on the path, for the CGAL timing.
- **Don't edit the polyhedron by hand.**

**Two traps, both found building this:**
- **Export as 3MF, never STL.** A float32 STL, welded, came out open. The
  build writes 3MF, which is indexed and exact to 1e-6 mm.
- **Pass OpenSCAD the full environment.** Without `HOME`, fontconfig can't
  find the fonts in `~/.fonts`, and the text silently falls back to another
  font. That once cost 228 mm³ of difference against the shipped body.

## Not done here

Benson's v2 (`~/workspace/your_files/love-letter-customizer/`) wasn't
reachable from this session, so this file was built from the shipped design
directly. Its default matches his figures for the shipped body: 169,579.96 mm³
measured on the shipped part against his 169,579.98, and the same bounding
box.
