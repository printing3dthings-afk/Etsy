# Victorian Carolers — printing notes

Built 2026-10-13, a Victorian village accessory. Scott circled them from the
second batch of accessory studies (`../concepts/accessories2_scene.jpg`).

Four carolers on a patch of snow, facing the street:

- **a gentleman with a lantern** on a staff, in a red coat, green scarf and
  top hat; the lantern is six-sided, with white glass and iron posts;
- **a gentleman** in a slate coat, red scarf and top hat;
- **a lady** in a long green coat, red scarf and red poke bonnet;
- **a child** in a red coat, green scarf and slate cap;
- the three singers each hold **an open songbook** up in both hands, pages
  up at them, slate cover to the street.

They are figurines in the peg-doll manner: round coats and heads, no faces.
At 25 mm tall a face would be below one extrusion.

The maker's mark, OBC, is inlaid in slate into the middle of the underside:
the logo's letters, 4.4 mm tall and 15.3 mm wide, cut 0.6 mm into the white
and filled flush, mirrored so they read from below. A groove one layer deep
crosses their face, the stripes of the logo.

It measures 40.0 × 24.8 × 35.7 mm (the lantern is the top).

`images/` holds renders of the model: `*_colour_*` in its four filament
colours and `*_as_printed_*` from the sliced toolpath. They are renders, not
photos of a print.

**Print this:** `victorian_carolers.3mf`. One object with four parts, already
aligned. Assign a filament to each colour.

| part | what it is | colour in the file |
|---|---|---|
| body | two coats, scarves, the bonnet | brick red `#A8483A` |
| roof | a coat, the hats, the cap, the books, the staff and lantern, the OBC mark inlaid underneath | slate `#2E3440` |
| trim | the heads, the pages, the lantern's glass, the snow | white `#F4F1EA` |
| accent | the lady's coat, two scarves | green `#2F6B45` |

## Settings that are not optional

- **Supports OFF.** The slice needs none: 0 support moves, 0 overhang
  perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **0 h 19 m** | **1.8 m, 5.4 g** |
| four colour | see below | 5.4 g of model **+ purge** |

Single colour, supports off, timed with the P1S motion model (the viewer's
clock). **In four colours the colour changes are almost the whole print:**
nearly every layer holds all four, and the viewer's colour slice
(PrusaSlicer, with a wipe tower) runs 7 h 17 m and 58 g. Bambu Studio's
purge differs; slice there for the real number. To bring it down, print
several sets on one plate so the changes are shared, or print it in one
colour and paint it.

## Verified before shipping — on the real exported meshes

- `tools/part_mesh.py check`: every part closed, no two overlap.
- `product_gate` **PASSED** on the parts welded into one body:
  - watertight, one body;
  - 1st-percentile wall 1.20 mm, median 5.55 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height 35.6 mm of 35.68 modelled;
  - 7.7 cm² of bed contact, 78% of the footprint; centre of mass over it.
- `print_fidelity`: 0.54 mm³ of 5,062 mm³ not printed, nothing printed that
  was not modelled, nothing in the wrong colour. **0 flags.**
- `fragility`: 0 high, 0 watch. One slender run of slenderness 3.2, the
  staff above the bearer's hand; it is 2 mm thick and set into his coat all
  the way down.

## What it took to print without supports

The first slice asked for 7,676 support moves. Each was fixed in the model:

- **The scarves** flared out of the coats at 49 degrees; they flare at 40.
- **The forearms** climbed to the books at 55 degrees from upright; the
  elbows are lower now and the forearms climb at 39.
- **The books** were square boards whose foot faced the plate at 50
  degrees; the foot is cut back to a line climbing 55. They also had their
  pages on the wrong side, facing the street; the pages face the singers.
- **Each upper arm** ended in a downward point just outside the coat, an
  island in mid-air under every elbow; the elbows sit inside the coats.
- **The bonnet** cut the head out of itself, and the two shared a surface,
  which left the union with open edges. The head is no longer cut out of it.
- **The hat brims, the bonnet and the books** were under one bead thick;
  they are 1.2 mm.
- **The lantern's finial** came to a point finer than a layer; it is blunt.
