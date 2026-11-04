# Gift Box Lantern v2: one colour at a time, snapped together

2026-11-04. Scott asked for it from the lantern's MakerWorld page: "Is it
possible to break this up into pieces so the different colors print
separately and get assembled. Make easy snap pieces for connections so it
doesn't have to be glued."

v2 is the same lantern as v1 (`../GIFT_BOX_LANTERN_PRINTING.md`): the four
glass sides with their Christmas scenes, the green posts and rail, the lid
with its red ribbon and bow. It's split into nine prints, in three colours,
that snap together with no glue. v1 is unchanged and is still the file for
a printer with an AMS.

**Size:** 79 × 79 × 104 mm assembled, the ribbon and bow included.

## The prints

Three files, one per colour, each a full plate:

| file | colour | prints |
|---|---|---|
| `gift_box_lantern_v2_green.3mf` | green `#2F6B45` | frame, top, lid |
| `gift_box_lantern_v2_glass.3mf` | white `#F4F1EA`, scenes green | the four glass panels |
| `gift_box_lantern_v2_red.3mf` | red `#C62F3A` | ribbon, bow |

- **The frame:** the floor, the base band and the four corner posts, with
  grooves down the posts that hold the glass, and a snap pin on top of each
  post. The OBC mark is engraved underneath.
- **The top:** the rail round the top, and the band the lid keys onto. It
  presses down onto the four pins and locks the glass in.
- **The lid:** v1's lid, with a snap pin on top for the bow.
- **The glass panels** print flat, each with its scene standing on it.
  - The glass is exactly 1.2 mm, six layers, so the scene starts on a fresh
    layer.
  - With an AMS the scenes print green.
  - Without one, pause at 1.2 mm and swap to green, or print the panels all
    white. Lit from inside, the scenes still read dark on the glow, as on v1.
- **The ribbon** lies upside down, the cross on the plate and its four ends
  standing up.
- **The bow** stands on its own foot.

PLA, 0.2 mm layers, **no supports**, everything as it lies in the file.

## Putting it together

1. Drop the four panels into the posts' grooves, scenes facing out.
2. Press the top straight down until all four pins click.
3. Set the lid on, lay the ribbon over it, and press the bow onto the lid's
   pin through the hole in the ribbon's middle. The bow holds the ribbon
   down.

The lid lifts off for the tealight's switch, as on v1. The top is meant to
stay on.

## The snap joints

Every joint is a split pin: two prongs with a barb, pushed into a socket with
a narrow throat and a wider chamber behind it.

- **The pin** is 3.4 mm across, split by a 1.0 mm slot that runs 3 mm down
  into whatever it stands on. Each prong is 1.2 mm thick, three beads, and
  flexes over about 5 mm.
- **The barb** stands 0.4 mm proud and squeezes 0.25 mm through the throat.
  That's about 1.7% strain in PLA: a firm click, well short of cracking.
- **Every pin prints standing up**, so the barb's catch is a 37° slope, not a
  ledge, and nothing needs support.

## Time and filament

PrusaSlicer with the P1S settings, each print sliced alone:

| print | time | filament |
|---|---|---|
| frame | 1 h 16 min | 27 g |
| top | 15 min | 8 g |
| lid | 39 min | 32 g |
| ribbon | 11 min | 4 g |
| bow | 14 min | 4 g |
| 4 glass panels | 1 h 7 min | 21 g white, 8 g green |

The whole set is about 3 h 42 min and 105 g: 76 g green, 21 g white, 8 g red.
The panels' time includes one colour swap each. Bambu Studio gives the real
time and purge for the AMS.

## Checked before it was pushed

The results are in `checks/`.

**Fit (`check_v2.py`, on the exported parts in place): all pass.**

- **Glass:** the panels stand in the grooves touching nothing. Pushed 0.5 mm
  in or out, they hit the groove.
- **Top:** it sits on the posts and holds each panel down. Pulled 0.5 mm up,
  the barbs catch.
- **Lid, ribbon and bow:** the lid sits on the top and the ribbon on the lid.
  The bow sits on the ribbon round the pin, and pulled 0.5 mm up, it catches.
  Lifted 0.5 mm, the ribbon is held by the bow.

**Product gate: all nine prints pass.** 0 supports, 0 overhang perimeters,
every wall at least 1.2 mm at the 1st percentile.

**Print fidelity: 0 flags on all nine.** The frame loses 4.4 mm³ in slivers
under the flag size. Nothing else is dropped or filled.

**Fragility:** nothing high and nothing on watch. The pins' prongs are listed
as slender runs, 2.5 on the frame and 3.7 on the lid, under the watch level
of 4.

The first full run failed on four counts. What changed:

- **The pins** were 3.0 mm across with 1.0 mm prongs: under the 1.2 mm wall
  floor. The slicer also dropped the sharp edge where the slot met the round.
  - The pins are 3.4 mm now.
  - The slot runs deeper, so the thicker prongs flex as easily.
  - Its ends flare into a 0.4 mm chamfer on each prong.
- **The glass groove** peaked 0.1 mm under the foot of the pin's slot. It now
  stops 1.2 mm under it.
- **The corner posts** went from 3.4 to 3.6 mm radius, for 1.2 mm of wall
  round the sockets in the top.
- **The base band's bevel** went from 1.5 to 1.2 mm. At 1.5 it left 1.15 mm
  outside the glass's channel.
- **The scenes' points** (star tips, the eaves, the moon's horns, the spire)
  are rounded to 0.6 mm. They stood 1.6 mm proud at a fraction of a bead
  wide.

**Not tested on the printer yet.** What I'd check first:

- the click of the four top pins, and that the top comes off again;
- that the panels slide into the grooves without forcing.

If a joint is too stiff or too loose, tell me. The barb (`SP_B`) and the
throat clearance (`SK_T`) are one number each.

## Renders

In `images/`:

- `gift_box_v2_{front,three_quarter,top}.png`: assembled.
- `gift_box_v2_exploded.png`: pulled apart in the order it goes together.
- `gift_box_v2_prints.png`: the nine prints as they lie on the plate.
- `gift_box_v2_frame_as_printed.png`: the frame rendered from its sliced
  toolpath, so it shows what the printer lays down, snap pins included.

These are design-review renders from the real exported parts, not photos.

Rebuild everything with `./ship.sh`, then `python3 render_v2.py`.
