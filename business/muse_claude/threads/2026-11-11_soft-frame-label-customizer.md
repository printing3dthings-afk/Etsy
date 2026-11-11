# Soft Frame — label customizer (Scott's call, 2026-11-11)

## 2026-11-11 17:53 EST - Benson — for review

Scott, looking at the Soft Frame's Label print profiles in Bambu Handy:
"These parts need to be customizable. Can you do that and keep them under
the print profile." I gave him the scope choice — label text only, or all
parts parametric (text + sizes). **His pick: "Just the label — add my own
text."**

So: the label becomes a MakerWorld Parametric Model Maker customizer,
attached to the EXISTING Soft Frame model (Sjack7 3560650, Private). The 10
print profiles stay exactly as they are — the customizer lives on the same
model page alongside them. Nothing else about the design changes.

**Design facts (from src Soft_Frame.scad, verified by Benson):**
- Label as shipped: `linear_extrude(0.8) rounded_rect(31.2, 11.2, 0.7)` —
  a blank 31.2 × 11.2 × 0.8 mm plate, prints flat.
- It slides into the drawer's label pocket (label_cut: 32 × 12 mm pocket,
  front window, top loading mouth, no adhesive). The customised label must
  keep the blank's exact footprint and 0.8 mm profile so it still fits the
  pocket — that points to ENGRAVED (recessed) text on the face rather than
  raised text, unless your pocket clearance numbers say raised is safe.
  Your call, with the numbers shown.

**What I need from you:** a PMM-ready SCAD for the label —
- Customizer parameters: the text string (one line), and only what earns
  its place beyond that.
- Text auto-fits the plate: scales down for long strings, stays inside the
  plate with a margin, centred.
- Geometry centred on (0,0) — the Name Ornament lesson; PMM generation
  must come out centred on the plate.
- Font: use one the PMM renderer actually has, or embed per repo practice —
  and say which you used. (Name Ornament flag: Dancing Script may not
  exist in PMM's renderer. The repo's DancingScript-Bold.ttf is a real
  font now, but renderer availability is the open question — Benson's
  acceptance test below is what settles it.)
- The rest of the Soft Frame is untouched; this is a label-only file.

**Acceptance:** post a READY line here — "READY: soft_frame label
customizer — file: <path>" — and Benson verifies in the PMM editor
(generates centred with a short string and a long one, text legible and
inside the plate) before attaching it to model 3560650. If PMM generation
fails the way the Name Ornament save did, we learn it in the editor, not
from a user.
