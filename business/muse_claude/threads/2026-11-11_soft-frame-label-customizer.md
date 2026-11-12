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

## 2026-11-11 22:55 ET - Claude

READY: soft_frame label customizer — file: openscad_models/soft_frame/pmm/soft_frame_label_pmm.scad (branch claude/new-session-o245bl, commit 97006a2a)

- **Engraved, not raised: a flush inlay in a second colour,** the top two layers (0.4 mm). The label stays the blank's 31.2 × 11.2 × 0.8, so it fits the 32 × 12 × 1.5 pocket exactly as before.
  - Raised text would fit the pocket's thickness (0.8 + 0.4 in 1.5).
  - But it would stand proud, and could catch the window's top edge as the label slides down. Flush can't catch on anything.
- **Customizer parameters:**
  - `LABEL_TEXT`, one line;
  - `LABEL_COLOUR` (default #F4F1EA) and `TEXT_COLOUR` (default #2E3440). PMM's colour pickers, as on the Name Ornament.
  - Nothing else.
- **Auto-fit:**
  - The text box is 26 × 7 mm, inside the 30 × 10 window with room to spare even when the label sits 0.4 to one side of its pocket.
  - Text shrinks to fit, down to a 3 mm cap height.
  - Past that it narrows instead of shrinking further: thinner strokes stop printing cleanly in two layers.
  - Widths come from Montserrat Bold's own advances, measured in OpenSCAD, so it doesn't depend on PMM having textmetrics().
- **Font:** Montserrat:style=Bold, which is on PMM's font list (tools/pmm_fonts.json). No Dancing Script anywhere.
- **Centred on (0, 0),** per pmm_build rule 3.
- **Checked (openscad_models/soft_frame/pmm/check_pmm.txt):**
  - Six strings, from "Tea" and "Pens" to "Washi tape / stickers", each render in 0.1–0.2 s, on the plate, 0 warnings.
  - "Screws" and the longest one slice as exported: 2 m 40 s, 0.44 g, no supports.
  - The longest one, at the smallest text, has 0 print-fidelity flags.
  - A single letter ("Q") draws too. The check's 20 mm² text-area floor is set for names, so it's listed as a note, not a fault.
- **Over to you:** generate a short and a long string in the PMM editor. Watch for centred, legible and inside the plate before attaching it to 3560650.
- **Suggestion:** the description should say the label is printed in two colours (an AMS or a manual swap at 0.4 mm).
