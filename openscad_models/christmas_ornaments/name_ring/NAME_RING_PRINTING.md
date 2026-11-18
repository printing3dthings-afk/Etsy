# Openwork Name Ornament: printing notes

Built 2026-11-18. Scott picked this form (1 of 5) to replace the domed name
ornament after its test print. That one's inlaid name came out lumpy: 0.6 mm
deep on a curve, it printed as slivers ("Jessee 2026", which read "7026").

**What it is:** a flat open ring, 80 mm across (88 mm with the loop), 3.2 mm thick.
- **The name and year:** raised 0.8 mm on their own outline, across the middle.
  The outline joins every letter and dot into one piece. A bar runs from it out to
  the ring on both sides.
- **Above:** a star with two pine boughs reaching down to the ends of the name.
  The boughs follow the name's width, so a short name gets steeper boughs.
- **Below:** holly, three leaves and three berries, its bottom leaf running into
  the ring.
- **Small stars:** four, caught on the ring.
- **The rest is open,** so the tree's lights show through.
- **The maker's mark:** OBC, engraved in the back of the name's outline. It reads
  when you turn the ornament over on its loop.

The pictures in `images/` are design-review renders, not photos. The sample name is
Olivia.

## Colours, by height

| part | what | height | colour in the file |
|---|---|---|---|
| frame | the ring, the loop, the name's outline and bar; the star, boughs and holly underneath | 0–2.4 mm (motifs 0–1.6) | red `#C62F3A` |
| accent | the tops of the star, boughs, holly and berries; the name and year | 1.6–2.4 mm; 2.4–3.2 mm | white `#F4F1EA` |

The AMS changes colour only on the four layers from 1.6 to 2.4 mm. The holly's
veins are cut through the white, so the red shows.

## Print it
- **`name_ring.3mf`:** one object, two parts already aligned.
- **`gcode/name_ring_two_colour.gcode.3mf`:** sliced, opens in Bambu Handy.
  - Bambu Studio, P1S 0.4, PLA Basic, 0.20 mm Standard;
  - 3 walls, 15% infill (Scott, 2026-11-12); supports off.
- **Flat, back on the plate, as it sits in the file.** Nothing overhangs.

**Cost, from Bambu Studio's own slice:** 47 m, 11.7 g (8.6 g red, 3.1 g white), supports 0.

These are at Claude's slicer settings. Benson's profiles (OPEN row 20) aren't on
main yet; re-slice with them when they land.

## Making one for a buyer

    ./build.sh "Christopher" 2026      # or ./build.sh "Mia" ""  for no year

This writes `name_ring_frame.stl`, `name_ring_accent.stl` and the union. The name
is as large as fits 60 mm across, at most 15 mm.

**MakerWorld customizer:** `pmm/name_ring_pmm.scad`, built by
`../build_name_pmm.py name_ring`.
- It uses only fonts PMM has (Lobster, Montserrat).
- It's centred on (0, 0): the profile needs Auto Arrangement on
  (`tools/pmm_build.py`, rule 3).
- **Checked here (2026-11-18):** Olivia, Jessee, Mia, Christopher, MARY-JO and Zoë
  all build and fit inside the ring. Mia, Zoë and Christopher pass the product gate.
- **Not checked:** how fast PMM generates it. That needs a Manifold build of
  OpenSCAD, and fetching one was blocked in this session.

## Checks (`logs/`)
- **Parts:** closed, no two overlap.
- **Product gate: PASS.**
  - One body, nothing thinner than 1.2 mm.
  - The raised name and tops are declared as colour detail; print fidelity
    checks them.
- **Print fidelity:** 0 flagged.
- **Fragility:** 0 high, 0 watch.
- **Silhouette (`silhouette_frame.txt`, on the frame):**
  - No near-touches, nothing thin, one clean piece.
  - It flags two things that don't apply here:
    - **Twinning:** an ornament is symmetric on purpose; the rule is for posed
      characters.
    - **Clutter:** the "engraved marks" are the recesses the white tops sit in,
      not lines cut into the face.

**What changed while checking, and why:**
- Sharp tips are rounded at 0.6 mm. A star's point or a holly spike otherwise
  runs down to nothing.
- The needles are 1.4 mm, six pairs a bough. At eight pairs they stood 0.47 mm
  apart and would print webbed.
- The needles on the inside of each bough's curve are shorter, so the air between
  them stays printable.
- The bar is 3.4 mm wide. At 2.8 the fragility check put it on watch.
