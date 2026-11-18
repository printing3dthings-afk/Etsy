# Urban Kid v2 — Benson's review of Claude's face & hoodie-fold attempts
2026-11-17. Source: `openscad_models/urban_kid/v2/` on branch
`claude/new-session-o245bl` — NOTES.md, sculpt_face.py, sculpt_face_sty.py,
folds.py, hoodie_v2.py, and all 8 research renders, pulled via Git LFS and
read by eye. Figure size locked at 190 mm (Scott); head ≈ 63 mm at the
designer-toy 1/3 proportion Scott picked.

## The one number that explains most of it
Claude's face script states its own floor: grooves kept at **0.4 mm**
printed (1 printed mm ≈ 0.0068 mesh units). A 0.4 mm groove is one
perimeter from a 0.4 mm nozzle at 0.42 mm line width. It renders
beautifully and slices to nothing. Almost every "expression too faint"
note in Claude's own log is this number, not the sculpting. Print-scale
floor for facial grooves: **≥1.2 mm wide, ≥0.8 mm deep** (≈3 line widths,
4 layers at 0.20 mm). The face pass in `face_pass_benson.py` is built to
that floor.

## Face — pass by pass
- **Realistic head, pass 3 (`face_sculpt_pass3.png`):** Claude's verdict
  is right — it reads as a neutral adult. Worse, the head is cropped flat
  at the top in the render, the pupils are tiny off-centre dots, and the
  mouth is a single hairline. Nothing here survives a slice. Dead end,
  correctly abandoned.
- **Stylised pass 1 (`face_stylized_pass1.png`):** the young head shape
  is the right base (round cheeks, short nose). But the irises are grey
  discs that float on the eyeballs, the heavy lids read *sleepy/sad*
  rather than scheming, and the smirk is a nearly straight slit — at
  front view the expression is "tired", not "up to no good".
- **Devilish pass 1 (`face_devilish_pass1.png`):** the V brows land —
  they're the strongest feature in any pass. Two problems: (1) the
  single vertical crease between the brows reads as a **scar**, not a
  furrow, and it gets worse the smaller you view it; (2) the mouth is a
  thin wavy line whose corner hooks vanish in the 3/4 view, and the
  ringed irises + small pupils read *startled*, not sly.
- **Sly smile (`face_sly_smile.png`) — the best pass, keep this base:**
  the raised left corner with its deep dimple and the bunched cheek over
  it genuinely read as a grin, front and 3/4. What still doesn't:
  - the lip line's centre is a hairline — it will not print (see floor
    above);
  - the centred lower-lip bulge, pushed up by the grin on one side,
    reads as a *swollen lip* in front view;
  - both pupils sit high in ringed irises, which fights the squint —
    the eyes say "surprised" while the mouth says "sly";
  - the glabella scar, as above.
- **Thumbnail test (done here, `thumbnail-test-sly-face.png`):** the sly
  front crop downscaled to ~12% (roughly how the head appears in a
  MakerWorld thumbnail of a 190 mm figure). What survives: eye outlines,
  nose, the raised mouth corner. What vanishes: iris/pupil detail, the
  brow V, nasolabial folds, the centre lip line. Conclusion: spend depth
  on lid lines, the grin line and dimples — not on iris detail.

## Hoodie & cloth — pass by pass
- **Cloth-sim pants (`cloth_pants_and_hoodie.png`, grey): the clear
  win, Claude is right.** Vertical hanging folds and the stack over the
  shoe read as fabric with no hand-drawing. Caveat from the render: the
  seat/upper thigh block is completely smooth — no fly, no pocket
  structure — so the legs read as fabric tubes joined to a plain block.
  The cargo flap pockets will have to be added as separate structure
  (the concept images show where they sit).
- **Cloth-sim hoodie body (same render, red):** a barrel. The kangaroo
  pocket is a flat slab with sharp corners floating on the belly — no
  opening slits, no sag — and the ribbed hem's zigzag reads as noise at
  this scale. No drawstrings in this render.
- **Sim on the mannequin (`cloth_on_mannequin.png`):** the blue sleeve
  sim crumples into spiky foil at the elbows (Claude's notes say the
  same); the red torso only gathers believably at the neck and hem.
- **Fold transfer (`hoodie_fold_transfer_failed.png`):** correctly
  labelled failed. The surface is a smooth puff with two isolated
  gouge marks on its left side; the transferred "folds" read as damage.
- **Sculpted fold strokes, try 1 (`hoodie_sculpted_folds_try1.png`):**
  worse than v1, as Claude concluded — and the render shows why in a
  way the notes understate: the strokes don't just read as cuts, there
  are **actual dark holes** punched beside the pocket and through the
  forearm area, and the back view's vertical stub marks read as
  scratches. Surface strokes on a distance field can't buckle a sleeve;
  agreed with Claude's verdict and his stated next direction (bold
  deliberate folds that change the garment's shape, or cloth sim per
  panel with seams).

## Benson's contribution (in this folder)
1. **Concept images — YES, at no extra cost.** Claude asked whether
   Benson can make images on what Scott already pays for: yes, via
   Muse's built-in image generation. Two are built and eye-checked:
   - `concept-front.webp` — clean front view, head at the 1/3
     proportion, devilish grin, blank nameplate. This is the
     image-to-3D-grade front Claude asked for first.
   - `concept-turnaround.webp` — front/side/back sheet. Two known
     generator faults, flagged honestly: the chain wrongly hangs down
     the *back* in the back view (ignore the chain there entirely),
     and the back view lifts one foot. The turnaround's head is also
     smaller than 1/3 — the front image governs proportions.
2. **Image-to-3D — NO tool on Scott's existing stack.** Benson has no
   Meshy/Tripo/Rodin/Hunyuan or any GLB/STL-generating feature in the
   tools already paid for; the image tool above outputs pictures only.
   Scott's call whether to pay for one — the front concept is ready to
   feed it either way. (Licence terms would need checking on whichever
   service Scott picks before any print is sold.)
3. **A print-scale face pass** — `face_pass_benson.py` (runs, verified)
   generating `face_relief_190.scad` + `face_pass_preview.png`: every
   feature dimensioned in printed mm at 190 mm, with Claude's mesh-unit
   conversion (×0.0068) alongside. Headline moves vs the sly pass:
   lip-line groove 1.4 mm wide × 1.0 mm deep; dimples as pits (3.2 mm /
   1.3 mm deep on the grin side); iris ring cut to its top arc only and
   pupils dished at matched heights with a shared sideways offset;
   lower-lip bulge shifted toward the grin side; **delete the vertical
   glabella crease**; keep the V brows, left cocked higher.

## Dumpling evidence (OPEN.md row 1 — still listed open/overdue)
The row rests on a wrong premise. Benson read the shipped file
`DumplingClicker_Clicker_Standard_P1S.3mf`: its own slice_info
prediction is **1414 s = 23 min 34 s**. The vote posts' "24 minutes" is
correct; the ~1 h 22 m figure does not come from the shipped file.
Evidence and the full row-by-row reply are in `draft-thread-reply.md`.
