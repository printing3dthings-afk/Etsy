# Urban Kid v3: Benson's Hunyuan3D mesh, made printable and edited

Scott, 2026-11-26: "Benson did this. Can you make changes to this?"

He picked all four changes:
1. base and flat soles;
2. a sharper face;
3. an OBC chain tag;
4. a split for colours.

The one-piece (1-3) is done. The colour split comes next, after Scott has seen the one-piece.

**Status: not printed.** All images are design-review renders, not photos.

## Source
`source/hunyuan-white-mesh.glb`:
- **Who and how:** made by Benson with Tencent's Hunyuan3D, from his own concept art
  (`concept-front.webp`, md5 `baa2d620...`; see `../v2/research/NOTES.md`).
- **The mesh:** one closed body, 195k triangles, Y-up.
- **Benson's mesh as he sent it:** `images/benson_mesh_as_sent_*.png`.

## Licence: read before selling or posting
Tencent Hunyuan3D 2.0 and 2.1 Community Licence (read 2026-11-26 from the model pages on
Hugging Face).
- **What it allows:** Tencent claims no rights in the outputs (section 5d). Commercial use is
  allowed under 1 million monthly users.
- **Where it doesn't apply:** the EU, the United Kingdom and South Korea. Section 5(c): "You must
  not use, reproduce, modify, distribute, or display ... Output or results ... outside the
  Territory."
- **What that means here:** selling prints of this figure to EU or UK buyers, or showing it
  publicly there, falls outside what the licence covers.
- **Which version:** not known; Benson to say which one he used, and whether it was Tencent's own
  hosted site, which has its own terms.

This is a reading of the licence text, not legal advice. Scott decides before any listing or
public post.

## What build.py does
Run `python3 build.py base face tag`.
- **base:**
  - stands the mesh up and sizes it, so the whole piece is 190 mm tall, base included, as v1;
  - sinks the feet 3 mm into a 90 mm disc base, 10 mm thick, with a chamfered top edge. That
    makes the soles flat. Before this the figure stood on two points and tipped over.
- **face:** deepens the relief the mesh already has, rather than drawing new lines:
  - splits the mesh to 0.35 mm edges (the face's were 0.75 mm);
  - softens the old facets;
  - pushes each point's offset from a smoothed copy (about 2.5 mm radius) out 2.2 times, across
    the face only, fading out over 3 mm at the edges.

  The V brows, heavy lids, the grin and its dimples all deepen together. See
  `images/face_before_after.png` (left: as sent; right: deepened).
- **tag:** two OBC plates from `tag.scad`, and the chain.
  - **Why the letters are 5 mm** (Scott, 2026-11-26: "I want the chain to say OBC and the hat
    logo to say it also"): at v1's 3 mm the shop mark's B lost both its holes to
    `obc_clean()` and read as a box ("O[]C"), here and on v1's gold tag. Counted on the 2D mark,
    the B first keeps both holes at 4.5 mm, so both plates use 5 mm. See
    `images/obc_plate_face_on.png`.
  - **Nameplate:** 20.5 x 8.6 mm, OBC raised 0.6 mm inside a 1.2 mm rim, set 0.8 mm into the
    hoodie over the blank tag the mesh had.
  - **Cap badge:** 20 x 9.5 mm, the same OBC, on the back of his head. Scott, 2026-11-26: "The
    hat is currently backwards so the logo should be on the back side of his head." The cap's
    front panel, above the brim that hangs over his neck, faces backwards, so the badge sits
    there and reads from behind. The opening on his forehead is the strap's, left as Benson
    modelled it. See `images/v3_obc_cap_back.png`.
  - **Both:** a hidden 2.5 mm block behind each plate, so the curved surface never leaves a gap.
  - **Chain:** 18 links (1.8 x 2.0 x 1.6 mm, every 1.4 mm, v1's curb chain) follow the two
    strands from the collar to the plate.

## Checks (one piece)
- **product_gate** (`checks/gate_onepiece.txt`): passes everything but
  `no_unsupported_overhang`. That one fails by design: it prints on tree supports.
  - **Contact:** 63.6 cm2 of base on the plate.
  - **Balance:** the centre of mass sits over the base.
  - **min_wall:** 1st percentile 2.48 mm. The raised letters are declared detail, which
    print_fidelity checks instead.
- **print_fidelity (0.12)** (`checks/fidelity_report.txt`, run with the cap badge on the front;
  the re-run with it on the back is in progress): 0 flagged.
  - **Dropped:** 0.03 mm3 in all, every piece under 0.2 mm wide: specks, not detail.
  - **Filled:** none, so the letters, chain links and face lines all print open.

## Slice
`urban_kid_v3_one_piece_fine.gcode.3mf`:
- **Settings:** P1S 0.4, PLA Matte, textured PEI, 0.12 Fine, organic tree supports.
- **Result:** 8 h 14 m 17 s, 157.0 g, of which 85.9 g is support (Bambu Studio 2.9.2, the
  OBC badge on the back of the cap).

## Not in git
The meshes (`out/`, `*.stl`). The refined mesh runs to 65 MB, so `build.py` rebuilds it from
`source/` in about 20 seconds.
