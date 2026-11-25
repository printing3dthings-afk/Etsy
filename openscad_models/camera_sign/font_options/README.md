# Camera sign: three neon font options (2026-11-25)

Scott printed the neon sign in Lobster and sent a photo: "Hard to read. Try 3 different fonts
in the style not the plaque". Lobster's letters join, and at 8 mm tall the joins run
"nbr", "cr" and "ftz" together.

These keep the neon style (the words on their own raised outline, FOLLOW in Montserrat above,
at the size that printed and read well) and change only the handle's face. Same 130 mm handle
width as before, so each fits the same spot beside the lead screw's slot.

| option | face | why | print (2.4 mm, two colours) |
|---|---|---|---|
| 1 | Nunito Black | rounded heavy sans, open counters: the most legible | 27 m 3 s, 6.8 g |
| 2 | Righteous (its "@" from Nunito) | retro display, the look of a neon sign; letters stand apart | 26 m 5 s, 6.7 g |
| 3 | Courgette, thickened 0.25 mm | a script, but the letters don't join | 29 m 32 s, 7.3 g |
| all three on one plate | | to compare them side by side in the printer | 1 h 15 m, 18.3 g |

- **Righteous's own "@"** has counters too narrow for a nozzle; the cleanup that every face
  goes through closed them into a solid blob. It borrows Nunito's "@".
- **Courgette's strokes** are thinner than the others, so they're thickened 0.25 mm on each
  side to keep the raised letters printable.
- **Wider faces mean smaller letters** at the same 130 mm: Nunito's are a little shorter
  than Lobster's, but open counters read better small than tall joined letters.
- **Contrast matters as much as the face.** The print in the photo is blue on grey. The file's
  colours, orange on near-black, read further.

## Files
- `camera_sign.scad` (one folder up) builds them: `-D 'style="neon"' -D 'hfont="nunito"'`
  (or `righteous`, `courgette`; `lobster` is the original and still the default).
- `<font>/`: base, letters and union STLs, the 3MF, `flat_view.png` and `logs/`.
- `gcode/camera_sign_neon_<font>.gcode.3mf` and `gcode/camera_sign_neon_all_three.gcode.3mf`:
  Bambu Studio, P1S 0.4, PLA Basic, 0.20 mm Standard, supports off.
- `font_options_sheet.jpg`: the three beside Lobster, close up and about camera size.
  Flat views of the model files, not photos.

## Checks
All three: product gate PASS, print fidelity 0 flagged, fragility 0 (`<font>/logs/`).

Nothing here is printed yet. Once Scott picks one, it goes in the viewer and FACTS.md.
