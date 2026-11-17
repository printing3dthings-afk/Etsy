# Urban Kid: a designer-toy figure in seven one-colour prints (2026-11-17)

Scott: "a very detailed character figure. Make it a fun urban character. Wearing a
OBC chain pendant. Baggy pants and a hoodie." He picked forms 1 and 5 of the five
shown: the designer-toy kid standing with his hands in his hoodie pocket, split
into one print per colour so he's full colour without an AMS.

## The figure
- **About 117 mm tall on a 56 mm base.** Designer-toy proportions: the head is
  drawn 1.28x round the neck.
- **Cap:** worn backwards, brim at the back. Six panel seams, a button, a sweatband,
  the snapback's opening and strap over his forehead with three studs.
- **Face:** heavy-lidded eyes, thick brows, a lopsided grin with a dimple, a nose
  and ears.
- **Hoodie:**
  - the hood down as a roll round his neck, draped onto his back;
  - drawstrings, raglan seams, a ribbed hem;
  - a kangaroo pocket with his hands in it, elbow creases and cuffs;
  - a flat chest the chain lies on.
- **Cargo pants:** baggy, bunched in four rolls over the sneakers. Cargo pockets
  with flaps and snaps, back pockets, a front crease, the hips' seam.
- **Sneakers:** chunky cupsoles with a midsole line, a toe-cap seam, laces and a
  side flash.
- **Chain:** a curb chain to an OBC nameplate, the letters raised at 3 mm.
- **Base:** the OBC mark engraved underneath, reading from below.

## Files
- **Plates, one per filament colour** (`gcode/`), Bambu Studio for the P1S, PLA
  Basic, 0.12 mm layers, supports off:

  | plate | prints | time | filament |
  |---|---|---|---|
  | `urban_kid_skin_head.gcode.3mf` | head (upside down on its top) | 30 m 43 s | 11.9 g |
  | `urban_kid_red_hoodie.gcode.3mf` | hoodie | 29 m 57 s | 8.2 g |
  | `urban_kid_charcoal_pants.gcode.3mf` | pants (on the cuffs) | 28 m 21 s | 6.2 g |
  | `urban_kid_white_sneakers.gcode.3mf` | both sneakers | 13 m 38 s | 2.5 g |
  | `urban_kid_black_cap_base_pin.gcode.3mf` | cap, base, cap pin | 46 m 14 s | 14.2 g |
  | `urban_kid_gold_chain.gcode.3mf` | chain and nameplate (flat) | 2 m 52 s | 0.4 g |
  | **all six** | | **about 2 h 32 min** | **43.5 g** |

- **Parts:** `parts/*.stl` (as printed), `parts/assembled/*.stl` (where they sit on
  him).
- **Guide:** `Urban_Kid_Guide.pdf`: printing, putting him together, what to report
  from a test print.
- **Renders:** `images/kid_*.png`, design-review renders of the real parts, not photos.
- **Viewer:** `urban_kid_kit` (all seven prints sliced as one plate, shown in one colour).

## Joints
- **Pegs and sockets:**
  - every joint is a peg in a socket, cut exactly after meshing (manifold3d);
  - 0.15 mm clearance all round: a push fit, with a drop of glue to keep;
  - each socket opening on a print's plate face has a 37 deg cone roof, so it prints
    without support.
- **Where they are:**
  - **base to sneakers:** one round peg each;
  - **sneakers to pants:** one peg each;
  - **pants to hoodie:** two pegs;
  - **hoodie to head:** one round peg, so the head turns and can be posed;
  - **head and cap:** both lie on the plate at that joint, so a loose D-pin (black,
    printed on its flat) goes between them, one way round.
- **Hidden joints:** each sits under the next colour (detail standard rule 8): the
  cuffs over the sneakers, the hem over the waist, the collar round the neck, the
  cap's band round its own seam.

## Checks (`checks/`)
- **Fit (`check_fit.py`, `fit.txt`): PASS.**
  - Every print is one closed body.
  - No two parts overlap, the pin included, set in its sockets.
  - Every joint seats on its plane, and every peg is inside the part it holds.
  - The chain's back lies on his chest, over 80 % within 0.2 mm.
- **Product gate: PASS on all nine prints, 0 support moves each.**
  - The chain declares its letters, link ridges and rim lip as surface detail to the
    wall check (`chain_detail.stl`).
- **Print fidelity at 0.12 mm: 0 flagged on all eight prints** (the second sneaker is
  the first one mirrored).
- **Fragility: 0 high, 0 watch on every print**, each run on its own
  (`fragility_<part>.txt`).
- **Silhouette check on the flat chain:** passes on gaps, thin parts and specks.
  - It flags the chain as mirror-symmetric. A necklace is meant to be; the flag is
    aimed at character poses.
  - It also caught the bail meeting the nameplate at a tangent, which is fixed.

## What the gate found, and what changed (each from the slicer, not by eye)
PrusaSlicer propped far more than the 45 deg setting suggests. Measured on these
meshes, it propped layer steps of 0.17 mm (about 40 deg). It also propped specks of
0.002 mm2 and the tips of support cones that ended in mid-air. What it took:
- **Steeper, trimmed cones.**
  - The self-support cones are grown at 28 deg.
  - A last pass clips every layer to 31 deg of the one below (`trim_up`).
- **Bumps on walls must be wider than they stand proud.** Under anything narrower,
  the cone thins out before it reaches the wall. Causes, and what replaced them:
  - the drawstrings' aglets: the cords now sink into the chest;
  - the back pockets: now patches 0.8 proud;
  - the elbows: now against the body;
  - the heel tab: removed, as it's hidden by the cuff.
- **Every raised patch's underside is chamfered.** This covers the pockets, flaps,
  snaps, the kangaroo pocket, the sneakers' flash and the cap's studs.
- **No ceilings.**
  - The eye sockets and the snapback's opening are bevelled, not round.
  - The cap's sweatband steps in rather than being grooved.
  - The hem ribs fade out at their tops.
  - The flap's edge groove and the forearm's seam groove went.
- **Sneakers rebuilt as cupsoles,** with the upper inside the sole: the first one's
  upper overhung the sole all round.
- **The legs:** a web between them, its faces leaning to meet the crotch, instead of a
  notch with a V-shaped roof.
- **The chain:**
  - a nameplate, not a disc: OBC at 3 mm is 11 mm wide and hung off a 10 mm disc;
  - the rim widened to 1.2 mm;
  - the bail set into the plate (it met the plate's edge at a tangent).

## Honest read
- **Not printed.** The fits are the 0.15 mm clearance that's worked on the cow, untested
  on this figure.
- The brows read heavy. Printed upside down, a brow's top is an overhang, so each has
  a ridge running up into the forehead.
- The arms are close to the body, so the hands-in-pocket pose reads quieter than
  elbows-out would. Elbows out left support cones ending in mid-air under them.
- The chain is glued on: it can't hang from his neck as a flat print.

## Rebuild
- `python3 kid.py` builds `parts/`.
- Then run, in order:
  - `python3 check_fit.py`;
  - the product gate on each part, with the chain's `checks/chain_detail.stl` passed to
    `--wall-skip-part`;
  - `./make_slices.sh`;
  - `python3 render_kid.py` (and `--plate`, `--exploded`);
  - `python3 make_guide.py`.
