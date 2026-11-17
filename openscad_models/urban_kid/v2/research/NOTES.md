# Urban Kid v2: research notes (2026-11-17)

**Size, decided (Scott, 2026-11-17: "Go with 190 mm").** v2 is v1 scaled 1.625x, about
190 mm tall. Designs stay in v1's frame and units; fields are built on grids seen through
`kid.Scaled`, so every print rule (grooves, overhangs, walls) applies at the real size.

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

## Sculpted folds on v1's hoodie, first try (`../folds.py`, `../hoodie_v2.py`)
`images/hoodie_sculpted_folds_try1.png`. Folds placed as strokes on the distance field:
elbow compression, shoulder-to-pocket tension, hem gathers, back drapes.
- At 0.5 mm they didn't read at all; at 2.2x they read as cuts and stubs, not cloth.
- Strokes falling into the gap between forearm and body still punch holes.
- Verdict: worse than v1. Cloth folds need the shape of the garment to change round
  them (a fold is the whole sleeve buckling), which surface strokes can't do.

## The face moved to the stylized CC0 head (`sculpt_face_sty.py`)
`images/face_stylized_pass1.png`. 'Head - Stylized' from the same CC0 bundle is young (round
face, big eyes, short nose), which the realistic head never was however it was sculpted.
On it:
- heavy, half-closed upper lids;
- brows drawn down with a furrow between them;
- a smirk up at his left with a dimple;
- fuller lips;
- carved irises.

Lessons, each from a broken render:
- **Find the eyeballs by mesh connection, not distance.** Picked by distance, the
  lids' inner rims were frozen too, and the lids tore into a "drip".
- **Grab a lid at its edge.** Grabbed above the edge, the skin moved further than the
  edge and folded over it.
- **The slit is at z 0.640, not 0.666.** The base mesh's densest crease at 0.666 is
  under the nose: the first lip line landed there.

Still to do:
- the smirk's corner kinks;
- the irises barely read under the lids;
- hair under the cap;
- setting the head into the figure at 190 mm.

## The devilish grin (Scott: "Maybe a devilish smile or smirk. A fun up to no good look.")
`images/face_devilish_pass1.png`. What changed:
- **Mouth:** a wide closed-lip grin, both corners up (his left higher), dimples, smile lines.
- **Eyes:** cheeks lifted into a squint; eyes glancing sideways.
- **Brows:** a V, flicked up at the outer ends.

Lessons, each from a broken render:
- **The base mesh's eyes are layered** (a cornea dome over a sunken iris). Carved, they
  were a crater beside a blister. Each is now a plain ball, turned 17 deg, with the iris
  ringed and the pupil dished 0.0085 deep (about 1.2 mm printed).
- **Brow inner ends drawn toward the middle bunched into a knob:** they now only go down.
- **The renderer caches by settings, not by file contents,** so re-rendering the same path
  showed the old picture: `crop_render.py` passes `--no-cache` now. It also deletes its
  ~100 MB crop meshes; left behind, they filled the disk.

## Bigger, sly smile (Scott: "Grin bigger like a sly smile.")
`images/face_sly_smile.png`. Lopsided:
- his left corner pulled far up and back (about 2.5 mm printed) into a deep dimple and
  smile line, the cheek bunched over it, and that eye squinted more;
- his right corner only a little up.

Run on too far up, the lip line hooked at its end like a scar: it now stops short.
