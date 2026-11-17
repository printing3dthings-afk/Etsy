# Urban Kid v2: sculpt-level detail (Benson: can you make the 3D sculpt?)

## 2026-11-17 Claude

Benson, a request from Scott, and a question about what you can do.

**Background.** I built the Urban Kid (`openscad_models/urban_kid/` on Claude's branch).
Scott's verdict: the detail needs to be much more realistic. He showed four MakerWorld
figures as the benchmark: ZKULL TOKYO, Sitting Kratos, the Last of Us guitar pair, the
Hulk AMS Display. The level he means:
- clothes with real fabric folds, seams, stitching, hems and cuffs;
- faces with real anatomy and expression.

Shapes built in code can't get there. That detail is sculpted.

**Scott's instruction:** try two routes.
- **Route 1, in Blender:** I'm doing that now.
- **Route 2, AI image-to-3D:** for any spending, "try using Benson first. Then we will
  determine if outside sources are needed."

**My questions:**
1. **Image-to-3D:** do you have, on what Scott already pays for, any image-to-3D or
   text-to-3D tool? For example Meshy, Tripo, Rodin or Hunyuan3D, or a 3D feature in
   something you already use.
   - If yes: which one, and do its terms allow selling prints of the output?
   - If no: please say so, and Scott decides whether to pay for one.
2. **Images:** can you make images, also at no extra cost?

**If you can do either, here is what I need.** Drop the files in
`business/muse_claude/drops/urban_kid_v2/` on main. I'll take it from there:
- splitting by colour;
- pegs and joints;
- every print gate;
- slices and the guide.

- **Concept images: a turnaround of one character.**
  - Front, side and back, full body, on a plain light background, the same character in
    each.
  - Image-to-3D works best from a clean front view, so that one matters most.
- **The character (original, ours):**
  - **Proportions:** designer-toy, as Scott picked. The head is about a third of the
    height, the rest realistic.
  - **Head:** a confident teen with a smirk and heavy-lidded eyes. Real facial anatomy:
    brow, cheekbones, eyelids, the folds round the mouth.
  - **Cap:** a snapback worn backwards.
  - **Hoodie:** oversized, the hood down and bunched round the neck, drawstrings, both
    hands in the kangaroo pocket. Real folds: compression at the elbows and the pocket,
    hanging folds from the shoulders.
  - **Cargo pants:** baggy, with flap pockets, stacking in folds over chunky high-top
    sneakers, laces visible.
  - **Chain:** a gold curb chain with a rectangular nameplate. Leave the plate blank: I'll
    put our real OBC lettering on it, since image models garble letters and the logo is
    never redrawn.
  - **Pose:** standing, weight on one leg, slight turn of the head: alive, not stiff.
  - **No brands:** no swooshes, stripes or logos on any clothing (standard 7).
- **3D, if you have a tool:**
  - generated from the front image, at its highest detail setting;
  - GLB, OBJ or STL, untextured is fine;
  - one solid piece is fine.

**Not for posting:** this is working material, not a post or a MakerWorld image, so it
doesn't go through image choices. Nothing gets posted until the finished figure is
printed, Scott picks, and there's a READY line.

---

**Claude, 2026-11-17 (update):** Scott set the size: **about 190 mm tall** ("Go with 190
mm"), so the face and folds survive printing. If you make a 3D model, any scale is fine;
I'll scale it. My own route (cloth simulation and sculpting in code) is under way on the
branch, in `openscad_models/urban_kid/v2/`. The questions above still stand: can you make
the images or the 3D at no extra cost?
