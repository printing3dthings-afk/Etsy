# Monogram Fidget Keychain — printing notes

Print-in-place spinner, three colours, one letter per unit. `letter="J"` today;
the file takes any of A–Z from the same parameter.

**Print this:** `monogram_keychain_J.3mf` — one file, one object, three parts,
already aligned. Open it and assign a filament to each part.

| part | what it is | colour |
|---|---|---|
| ring | knurled frame + keyring lug | frame colour |
| rotor | the spinning disc | face colour |
| halo | the offset surround behind the letter | accent |
| letter | the raised monogram | accent |
| mark | OBC maker's mark, flush in the underside | **white** |

Each part is independently selectable — right-click one in Bambu Studio and set
its filament. The parts are named `ring` / `rotor` / `halo` / `letter` / `mark`, not by
filename, so the list is readable.

## Slicer settings that are not optional

**Ironing OFF.** This is a print-in-place part and ironing is the one setting
that can weld it shut: it drags the nozzle across every top surface at near-zero
flow, and the rotor's top face is a narrow annulus whose outer edge sits right
at the gap. It also makes that annulus look worse, not better — short passes
with a direction change at every turnaround is ironing's bad case, and it is
what the first printed J came off the plate looking like.

**No brim on the rotor.** A brim bridges the two bodies at the bed by design.

The per-part `.stl` files are the source the assembler consumes and what
`mesh_gate.py` checks — they are not the deliverable.

> **Do not export the 3MF from OpenSCAD.** Its 3MF writer merges every body
> into a single object with no materials (verified: 1 object, 1 item, 0
> basematerials, 20,065 fused triangles). That file slices fine and no filament
> can be assigned to any part of it. Build the deliverable with
> `tools/assemble_3mf.py` and confirm the parts survived.

## Why this font, and why that is not a matter of taste

A monogram product ships 26 letters and is only as good as its **widest** glyph
and its **thinnest**. `tools/glyph_probe.py` measured every letter in every
candidate face, then scaled each to fit inside the bezel (r=11.1mm after the
halo offset) and re-checked the stroke that survives:

| font | size that fits all 26 | worst stroke | |
|---|---|---|---|
| **Caveat Bold** | **14.7** | **3.87 extrusions** | **shipped** |
| Bebas Neue | 18.2 | 5.46 | modern, not elegant |
| Fredoka | 13.9 | 6.63 | prints beautifully, reads basic |
| Dancing Script Bold | 12.9 | 2.09 | passes, no margin |
| Cinzel Decorative Bold | 8.7 | **1.21** | **fails** |
| Great Vibes | 8.2 | **0.76** | **fails** |

Cinzel Decorative is the trap worth remembering. Judged on stroke width alone at
a fixed size it passes comfortably — but its **Q is 47mm wide at size 22**,
decorative swashes, so fitting the worst glyph on the face shrinks every stroke
to 1.21 extrusions. **A font can fail on proportion rather than on weight**, and
only measuring both catches it.

## The maker's mark is an inlay now, and why

The printed J's underside was unreadable. Two separate reasons, both measured:

1. **It was never printable.** `glyph_probe.py` puts "OBC" in Caveat Bold at
   this size at **1.89 extrusions** — under the 2.00 floor the standing rule
   sets, so the slicer had less than one bead to work with on the thinnest
   strokes. It now uses **Montserrat Black at 2.45 extrusions**, the face the
   rest of the catalogue's marks already use.
2. **Depth was the wrong signal.** That face is printed against the *textured*
   plate, and the plate's stipple is coarser than a mark this size can afford to
   be deep. Colour reads where depth cannot.

So the pocket is now filled by a body of its own — `mark`, white, flush with the
face, a colour swap in the first three layers. Three things fall out of it for
free: the mark cannot wear off, being through-coloured rather than surface-deep;
the pocket's unsupported ceiling stops existing because something holds it up;
and `inlay_probe.py` confirms **0 thin layers, 0% of volume at risk**, minimum
layer width 0.965mm = 2.3 extrusions, so the white prints on every layer instead
of silently merging into the orange.

**The mark also printed backwards.** `mirror([0,1,0])` flips the text in Y,
which from below reads as a 180° *rotation*, not a mirror. The underside is seen
by turning the part about its vertical axis, so world +X maps to screen-left and
**X is the axis to pre-flip**. Fixed, and verified by projecting the mesh as the
eye actually sees it rather than by reasoning about it twice.

The probe is validated against real ground truth: it **rejects** "OnBrandCraftz"
at the size that actually printed blank on three of four sauce models, and
**accepts** the "OBC" that replaced it and verifiably printed.

## The print-in-place trap, and how it caught us

The rotor is captive inside the frame on a shallow V — the rotor's rim bulges
1.5mm at mid-height and the frame's bore mirrors it. Both faces of the V sit at
22° from vertical, far inside the 55° limit, so the trap prints with no support
in either direction.

**The first J fused and would not spin.** The gap was measured on the exported
meshes afterwards and was a uniform **0.400mm at every height** — the model
built exactly what it promised, so this was never a modelling error. 0.40mm is
the number Technique 22's hinge spins on, but a hinge is a short pin and this is
a 7.4mm-tall journal facing the frame around its whole circumference: roughly
700mm² of facing surface, where **one weld anywhere stops the part**.

A print-in-place gap does not weld along its whole height. It welds in two
places, and both are now relieved rather than merely widened:

| where | why it welds there | before | after |
|---|---|---|---|
| first layer, on the plate | elephant's foot spreads the first layers of **both** bodies into the gap | 0.400 | **1.549** |
| rotor's top face | ironing drags melt off the rim and over the gap | 0.400 | **1.020** |
| V apex (load-bearing) | nothing — this is the capture and stays tight | 0.400 | **0.454** |

The relief is a 0.6mm chamfer on the rotor's two outer edges with the frame's
bore flared to match, so the gap opens exactly where the welding happens and
stays tight where the mechanism lives. The clearance itself went to 0.45mm —
worth 12% more margin for 0.12mm more axial play (0.99 → **1.110mm**), which is
set by the 22° V angle, not by the clearance.

**Worth doing before printing the replacement:** twist the fused J hard with
pliers. If it breaks free and then spins, the weld was at the bed and thin —
which says elephant's foot, and the chamfer is the fix. If it will not break,
the weld runs the V and ironing is the likelier culprit. Ten seconds, and it
tells us which mechanism to trust.

The bore is defined **once**, by the rotor's own envelope, and cut from the
frame. Defining it in both places left 40 zero-volume slivers where two
near-coincident surfaces fought.

## Detail, on purpose

Corpus finding 1 — *"a smooth panel reads as unfinished, not as minimal"* — so
the frame carries 44 knurl scallops and the rotor face a bezel groove ringing
the letter. The letter's top sits **flush with the frame**, which is both the
cleaner look and the reason the proudest feature never rubs in a pocket.

The rotor face is **flat, deliberately**. A shallow dome there would stair-step
exactly like the sauce bowl's top did (Technique 54).

## Real print cost — sliced, not estimated

| | size | time | filament | cost |
|---|---|---|---|---|
| one keychain | 57.1 × 43.8 × 9.0 mm | **51m 14s** | 8.75 g | $0.17 |

The clearance relief and the white inlay cost 74 seconds and 0.05g between them.

Small enough to plate 6–8 at once, which is corpus finding 10 — *"a 180mm
one-per-plate model is a long print and a weak set."* Against the sauce bowl's
11h53m for a single unit, this is the shape of product that actually pays.

## Verified before shipping — on the real exported mesh
- Watertight, 0 degenerate faces. The merged mesh reports **3** bodies, not 4:
  the halo is a flange that touches the letter, so they fuse there. That shared
  boundary is exactly right for multi-material — no gap, no overlap — and the
  shipped `.3mf` carries all **4** as independent, individually colourable parts.
- **Zero terracing** — no upward surface shallow enough to stair-step.
- Overhang past 55°: **1.24 cm²**, all of it accounted for — 0.35 cm² is the
  0.7mm-deep OBC mark ceiling on the rotor underside (a bridge that short prints
  fine, confirmed on the real sauce bowl), and 0.89 cm² is the letter's flat
  base, which physically rests on the rotor. The gate counts each colour body
  alone and cannot see that one sits on another; this is why its overhang line
  reports and never fails.

## What the real print settled, and what it did not

**Printed 2026-09-09 (the J, orange/purple/white).** What the photographs
proved, and what is still open:

- **The monogram works.** The J came out crisp with a clean halo — the font
  probe's whole argument, validated on plastic.
- **The clearance did not.** 0.40mm fused. Fixed above; **unproven until the
  next one spins.**
- **The mark did not.** Under-strength font *and* wrong handedness *and* the
  wrong signal (depth on a textured face). All three fixed above; the inlay is
  measured but **not yet printed**.
- **Still not measured on plastic:** whether 1.110mm of axial play reads as
  pleasant or as rattly in the hand. If it rattles, the knob is the V angle
  (`bulge` against `Th`), not the clearance — a one-number change.

**Print one more J before committing to a 26-letter set.** Three of this part's
four subsystems changed since the last one came off the plate.
