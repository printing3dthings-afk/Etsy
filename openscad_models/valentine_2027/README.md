# Valentine's Day 2027 drop

Started 2026-10-26 from Scott's brief: two main pieces, one stretch, sketches first.

| piece | status |
|---|---|
| Love Lantern: **Standing Heart** (`standing_heart/`) | modelled, gate passed, ready to test-print |
| Love Lantern: **Swan Crown** (`swan_crown/`) | modelled; drum, lid and crown each slice with no supports; full checks running |
| Chocolate Shop: **Victorian Bay** (`shops/victorian_bay/`) | modelled; full checks running |
| Chocolate Shop: **Chocolate Box** (`shops/chocolate_box/`) | modelled; full checks running |
| Classroom mailbox: **Giant Love Letter** (`mailboxes/love_letter/`) | modelled, all checks pass, 0 supports; see `mailboxes/VALENTINE_MAILBOXES_PRINTING.md` |
| Classroom mailbox: **Hungry Love Monster** (`mailboxes/love_monster/`) | modelled, three prints, all checks pass, 0 supports; same notes |
| Everlasting Rose Dome (stretch) | not started: only after 1 and 2 are test-printed |

Scott picked two of each on 2026-10-26 ("Do 2 of each category that you
think"). Run any piece's checks with `python3 check_valentine.py <piece>`
after its `build.sh cgal` and `build.sh union`.

## Design rules for every piece (Scott, 2026-10-26)

- **Glow areas thin.** Every window pane and lantern panel is 0.8–0.9 mm,
  two lines, so it glows properly. Frames and walls round it stay full
  thickness (1.2 mm or more).
- **Window scenes go inside, thick.** Anything that sits in a window (the
  lantern scenes, a shop's chocolate display, as with the Christmas
  workshop's toys) is built on the back of the pane, 2.5–3 mm in all.
  Unlit, the pane looks plain; lit, the scene shows as a dark silhouette in
  the glow. Undersides slope as they leave the pane (relief_lib's art_in), so
  nothing needs support, and nothing reaches into the tealight's space.
- **Daylight details stay outside:** names and date, the sign's letters,
  frames, bars, ribbon and seal are raised on the outside, where they read
  unlit.
- Check both: a lit and an unlit render side by side for every piece.

The concept renders below put the scenes on the front of the glass; that is
the forms only. The real models move every scene inside.

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
