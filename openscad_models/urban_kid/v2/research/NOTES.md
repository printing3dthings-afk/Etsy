# Urban Kid v2: research notes (2026-11-17)

Scott asked for much more realistic detail and showed four sculpted MakerWorld figures as
the bar: ZKULL TOKYO, Sitting Kratos, the guitar pair, and the Hulk. "Look at the clothes and
the facial details." Two routes are running, both on his say-so:
1. Blender and code here.
2. AI image-to-3D, asked of Benson first in
   `business/muse_claude/threads/2026-11-17_urban-kid-detail.md` on main. No reply yet.

All images below are design-review renders, not photos. Nothing here has been printed.

## What works

### Cloth simulation (`../cloth_garments.py`)
The pants are the clear win: `images/cloth_pants_and_hoodie.png`, the grey part.
- **What it does:**
  - Blender's cloth solver runs headless at real human size (1 mm of v1 = 15 mm).
  - Each garment is cut too long or too wide, then pushed into place over a mannequin in
    v1's pose (`../mannequin.py`).
- **The pants:** each leg is a tube, its waist ring pushed down 8 mm onto the sneakers.
  Result:
  - long hanging folds;
  - a stack at the shoe;
  - the uneven hang of real fabric.
  None of it is drawn by hand.
- **Settings that matter:**
  - **Bending stiffness:** 0.8 crumples into foil-like wrinkles, and 6 gives stiff tubes;
    3 is cotton twill.
  - **Smoothing:** a light Taubin smoothing (6 passes) removes ring-wide spikes the solver
    leaves.
- **Speed:** about 2-3 minutes a garment, in parallel.

### Sculpting in code (`tools/mesh_sculpt.py`, `sculpt_face.py`)
- **Brushes** (ZBrush-style) on an 860k-vertex CC0 head: move, draw, stroke, crease,
  smooth, dots, noise.
- **The face** (`images/face_sculpt_pass3.png`), what's in:
  - heavy lids;
  - drilled pupils;
  - nasolabial folds;
  - the lip line;
  - a smirk.
- **What doesn't work yet:**
  - it still reads as a neutral adult, not a confident teen;
  - the expression is too faint for print scale.

### Making cloth solid (`../assemble.py`)
- **The method:** each cloth surface gets thickness from a distance field, and the
  inside is filled with `binary_fill_holes`.
- **Result:** watertight single bodies.
- **The seat of the pants:** a field, the hips plus 2 mm of ease. The simulated legs'
  waist rings are hidden inside it.

## What didn't work
- **Hoodie body as a simulated tube** (`images/cloth_on_mannequin.png`): it hangs
  believably from the neck, but the joined result reads as a barrel. A real hoodie is
  sewn panels, and an elliptical tube has none of that structure.
- **Pressing the cloth's folds into v1's hoodie** (high-pass of the cloth's distance field
  added to v1's): `images/hoodie_fold_transfer_failed.png`.
  - At 1.3 mm it looked like rock.
  - At 0.8 mm with a blur it was mush.
  - v1's seams and cords were blurred with it.
- **Sleeves simulated by drawing the cuff back:** compression folds form, but spiky at
  this mesh size. The smoothing that cures them also flattens them.

## Next, for the hoodie and face
- **Hoodie:** keep v1's shape and sculpt the folds as deliberate strokes, the way the
  reference sculptors work: a few bold, readable folds, not physics noise. That means:
  - spiral folds at the elbows;
  - hanging folds from the shoulders to the pocket;
  - gathered folds above the ribbed hem.
- **Face:**
  - a younger head shape (rounder cheeks, shorter nose);
  - a much stronger smirk and lids;
  - the head scaled up as v1's was.
- **Scale:** at 117 mm the face is about 30 mm and lid-level detail is near the nozzle's
  limit. The reference figures print larger. A v2 at about 190 mm (1.6x) would let the
  detail survive printing.
