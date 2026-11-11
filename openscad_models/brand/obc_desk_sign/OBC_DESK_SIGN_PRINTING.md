# OBC desk sign

Scott, 2026-11-11: "I want a 3d print designed of my logo so I can print a real one."
He picked the gold OBC, as a desk sign on a base.

- **Plaque:** the gold OBC on a black plaque. 182 × 88 × 5 mm, with the letters
  150 mm wide and standing 2.4 mm proud.
- **Base:** a black base with a slot, 196 × 46 × 14 mm. The plaque slides in and leans
  back about 10°.
- **Not printed yet.** Every number below is from the model and its slices.

## The logo is the logo

The letters are traced from the logo itself (`../icons/obc_logo_master_1600.png`), not
set in a font. The vector OBC in `assets/brand/` is Montserrat Black, and at its best
weight and spacing it overlaps this logo by only 85%: the logo's letters sit closer
together. `trace_check.png` shows the trace drawn over the logo.

**The stripes are measured from the same image:** three groups, each one faint line
and three strong ones.
- **Strong lines** are cut through the gold, so the black shows: the logo's dark lines.
- **Faint lines** are 0.4 mm deep in the gold and read as a shadow.

**Two changes so it prints, both small:**
- **No stripe is narrower than 0.4 mm.** The faint ones measure about 0.3 mm at this size.
- **No gold is narrower than 1.2 mm** (three lines of plastic). Where a stripe crosses
  a curve near its top or bottom it left slivers down to 0.05 mm. They're removed, so
  those curves end in short steps.

## Files

| file | what |
|---|---|
| `obc_desk_sign_plaque.3mf` | the plaque, black and gold, face up |
| `obc_desk_sign_base.3mf` | the base, black |
| `OBC_Desk_Sign_Guide.pdf` | printing and putting it together |
| `parts/*.stl` | every part; `standing_*` are posed for checks and renders |

## Printing

- **Plaque:** with an AMS, put black in one slot and gold in another. It prints black
  to 5.0 mm and swaps to gold once. With one spool, add a pause at 5.0 mm in Bambu
  Studio's preview (layer slider), then load gold when it stops.
  - Time: about 2 h 23 m.
  - Filament: 43.9 g black and 10.6 g gold.
- **Base:** black, about 1 h 36 m, 46.6 g.
- **Settings for both:** 0.2 mm layers, supports off, smooth PEI.
- **Filament:** a silk gold looks closest to the logo. Ironing on the plaque gives the
  black a smooth face around the letters.

## Checks (`checks/`)

| check | result |
|---|---|
| product gate, plaque with letters (`gate_sign.txt`) | PASS, 1 body, thinnest wall 1.54 mm (1st percentile) |
| product gate, base | PASS |
| print fidelity, plaque + letters, 2 colours | 0 dropped, 0 filled, 0 flags |
| fragility | 0 slender runs |
| fit (`fit.txt`) | PASS |
| slices (`slices.txt`) | 0 support lines |

**What the fit check found:**
- **The fit:** the plaque doesn't touch the base and sits on the slot floor.
- **Slot clearance:** 0.5 mm, so it leans 10.9°. If the slot prints 0.25 mm tighter,
  as FDM slots usually do, it leans 9.4°.
- **Stability:** it tips only past 41° backwards and 44° forwards.

## Rebuild

1. `python3 trace_obc.py`: the outline, the stripes and the gold shapes, from the logo
   image.
2. Export each part:
   `openscad --backend=manifold -D 'part="<name>"' -o parts/<name>.stl obc_desk_sign.scad`
   for plaque, letters, sign, base, standing_plaque and standing_letters. BOSL2 must be
   on `OPENSCADPATH`.
3. `python3 check_fit.py`
4. The review renders: `tools/blender_render.py --views`, with the three standing parts
   (see `images/`).
5. `python3 render_guide.py`, then `python3 make_guide.py`.

Design-review renders in `images/` are renders of these files, not photos.
`obc_desk_sign_as_printed.png` is rendered from the print-fidelity toolpath.
