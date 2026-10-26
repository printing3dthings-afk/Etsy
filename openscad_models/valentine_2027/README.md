# Valentine's Day 2027 drop

Started 2026-10-26 from Scott's brief: two main pieces, one stretch, sketches first.

| piece | status |
|---|---|
| Love Lantern (main #1) | concepts: `concepts/lantern_forms.jpg`, waiting for Scott's pick |
| Chocolate Shop (main #2, village building) | concepts: `concepts/shop_forms.jpg`, waiting for Scott's pick |
| Everlasting Rose Dome (stretch) | not started: only after 1 and 2 are test-printed |

## Concepts (`concepts/`)

Massing studies to choose a form from, built in Python (manifold3d) and
rendered in Blender. Per the brief, no OpenSCAD is written until Scott has
picked; the picked forms are then modelled properly in OpenSCAD and run
through every gate. These are not print files, and every image is a render
of a model, never a photo of a print.

- `geo.py` shapes, hearts, text and relief on faces; `scenes.py` the glowing
  panel scenes (couple under a lamppost, swans' necks making a heart, a heart
  in a cottage window, a dancing couple, a pond at night).
- `lantern_forms.py` five lanterns; `shop_forms.py` five chocolate shops.
- `render_concepts.py lanterns|shops [n ...]` renders each form in colour and
  lit (printed white, a warm light where the tealight's flame would be) and
  lays out the comparison sheet.

## Timeline

Concepts in November, test prints and real photos by mid-December, listings
live by January 3. Christmas order cutoff is about December 12, so iteration
counts stay low.
