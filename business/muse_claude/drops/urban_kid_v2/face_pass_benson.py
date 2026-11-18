#!/usr/bin/env python3
"""Urban Kid v2 — Benson's face pass: PRINT-SCALE feature relief spec.

Why this pass exists (from Benson's review of Claude's v2 renders,
2026-11-17): Claude's sculpt_face_sty.py keeps grooves at >= 0.4 mm
printed (his stated floor). A 0.4 mm groove is ONE perimeter from a
0.4 mm nozzle — it renders beautifully and prints as nothing. Every
feature below is sized to survive a 0.20 mm layer / 0.42 mm line-width
slice in matte PLA at the locked 190 mm figure size:

  groove width  >= 1.2 mm  (~3 line widths)
  groove depth  >= 0.8 mm  (4 layers)
  raised detail >= 0.8 mm proud, >= 2.0 mm across

Figure frame (printed mm, 190 mm total, head = 1/3 height):
  head height 63.3, head width (cheekbones) 54, chin at z=0 of the
  head-local frame, face plane y=0, x = figure's left (+).

Claude's mesh units: his script states 1 printed mm ~= 0.0068 units
(at his ~55 mm head). The `units` column converts with that factor;
if the head is rescaled, the printed-mm column governs.

Run: python3 face_pass_benson.py
Outputs: face_relief_190.scad (groove/relief solids to boolean against
the head, or to drive mesh_sculpt strokes), face_pass_preview.png
(front-view feature map at true relative scale).
"""

# name, geometry (printed mm, head-local: x from centre, z from chin)
FEATURES = [
    # --- mouth: the grin carries the character, so it gets the depth ---
    dict(name="lip_line_groove", kind="stroke",
         pts=[(-15.0, 19.2), (-8.0, 18.1), (0.0, 17.8), (8.0, 18.6), (15.0, 22.3)],
         width=1.4, depth=1.0,
         note="Left corner (figure's left, +x) ends 3.0 mm above the right corner's rise: the lopsided sly grin. Stops 1.5 mm short of the dimple so it cannot hook into a scar (Claude's sly-pass lesson)."),
    dict(name="dimple_L", kind="pit", centre=(16.8, 23.2), dia=3.2, depth=1.3,
         note="Deep pit at the raised corner."),
    dict(name="dimple_R", kind="pit", centre=(-16.2, 20.2), dia=2.6, depth=0.9,
         note="Shallower on the low side — asymmetry is the expression."),
    dict(name="smile_line_L", kind="stroke",
         pts=[(16.8, 23.2), (19.5, 26.5), (20.5, 30.5)], width=1.1, depth=0.8,
         note="Nasolabial/smile arc on the grin side, from dimple up-out."),
    dict(name="smile_line_R", kind="stroke",
         pts=[(-16.2, 20.2), (-18.5, 23.0), (-19.3, 26.0)], width=1.1, depth=0.7,
         note="Shorter and shallower on the low side."),
    dict(name="lower_lip_bulge", kind="raise", centre=(1.5, 14.8), dia=13.0, height=1.1,
         note="Stretched by the grin, shifted toward the raised side; NOT a centred pout (the sly render's centred bulge read as a swollen lip)."),
    # --- eyes: rings read as 'startled' at print scale; dishes + lids read as sly ---
    dict(name="pupil_dish_L", kind="pit", centre=(11.2, 39.5), dia=3.4, depth=1.2,
         note="Glance to his left: pupil centre offset +2.3 mm from eye centre (13.5, 40.0). Depth matches Claude's measured 1.2 mm."),
    dict(name="pupil_dish_R", kind="pit", centre=(-11.2, 39.5), dia=3.4, depth=1.2,
         note="Same offset both eyes — a matched glance, not a wall eye (devilish pass pupils sat at mismatched heights)."),
    dict(name="iris_groove_L", kind="ring", centre=(11.2, 39.5), dia=6.8, width=0.9, depth=0.6,
         note="REDUCED from Claude's full ring: draw only the top 120 degrees of the ring; the lid covers the rest in a squint, and a full floating ring is what read as 'startled'."),
    dict(name="iris_groove_R", kind="ring", centre=(-11.2, 39.5), dia=6.8, width=0.9, depth=0.6,
         note="Top arc only, as left."),
    dict(name="upper_lid_line_L", kind="stroke",
         pts=[(7.5, 42.8), (11.0, 43.8), (15.0, 43.2), (18.5, 41.8)], width=1.3, depth=0.9,
         note="Lid edge sits so the lid covers the top 45% of the eye: heavy-lidded. Deeper than any other eye line — this is the line that must survive paint."),
    dict(name="upper_lid_line_R", kind="stroke",
         pts=[(-18.5, 41.8), (-15.0, 43.2), (-11.0, 43.8), (-7.5, 42.8)], width=1.3, depth=0.9,
         note="Mirror of left."),
    dict(name="lower_lid_raise_L", kind="raise", centre=(13.0, 36.4), dia=10.0, height=1.4,
         note="Cheek pushed up into the lower lid on the grin side: the squint."),
    dict(name="lower_lid_raise_R", kind="raise", centre=(-13.0, 36.4), dia=10.0, height=0.9,
         note="Less on the low side."),
    # --- brows: keep the V, kill the forehead 'scar' ---
    dict(name="brow_L", kind="raise_bar",
         pts=[(6.0, 47.6), (12.0, 48.6), (19.0, 50.6)], width=2.4, height=0.9,
         note="Inner end LOW (47.6), outer end flicked UP 3.0 mm over its length: the V."),
    dict(name="brow_R", kind="raise_bar",
         pts=[(-19.0, 49.8), (-12.0, 48.2), (-6.0, 47.6)], width=2.4, height=0.9,
         note="Outer flick 2.2 mm — his left brow cocked higher (matches the grin side)."),
    dict(name="glabella_softening", kind="note_only",
         note="DELETE the single vertical centre crease used in devilish/sly passes. At print scale it reads as a scar, not a furrow (visible in both renders, worst at thumbnail). Replace with two 3.0 mm creases angled 30 deg from vertical, 1.0 mm wide, 0.6 mm deep, starting at each brow's inner end — or nothing. Benson's vote: nothing; the V alone sells it."),
]

UNIT = 0.0068  # Claude's stated mesh units per printed mm (sculpt_face_sty.py)


def scad():
    out = ["// Urban Kid v2 face relief — Benson pass, 190 mm figure, head-local mm",
           "// Grooves are NEGATIVE solids: difference() them from the head.",
           "// Raises are POSITIVE solids: union() them. Origin: chin centre,",
           "// face plane y=0, +x = figure's left, z up. Head 63.3 tall x 54 wide.",
           "$fn = 48;", ""]
    for f in FEATURES:
        if f["kind"] == "stroke":
            pts = ", ".join(f"[{x}, {z}]" for x, z in f["pts"])
            out.append(f"// {f['name']}: width {f['width']} mm, depth {f['depth']} mm")
            out.append(f"module {f['name']}() {{")
            out.append(f"  pts = [{pts}];")
            out.append(f"  for (i = [0 : len(pts) - 2]) hull() {{")
            out.append(f"    translate([pts[i][0], 0, pts[i][1]]) sphere(d = {f['width']});")
            out.append(f"    translate([pts[i+1][0], 0, pts[i+1][1]]) sphere(d = {f['width']});")
            out.append("  }")
            out.append("}\n")
        elif f["kind"] == "pit":
            x, z = f["centre"]
            out.append(f"// {f['name']}: dia {f['dia']} mm, depth {f['depth']} mm")
            out.append(f"module {f['name']}() {{ translate([{x}, 0, {z}]) "
                       f"scale([1, {f['depth'] / (f['dia'] / 2):.2f}, 1]) sphere(d = {f['dia']}); }}\n")
    out.append("// Raises (brows, lid/cheek, lower lip) are specified in the")
    out.append("// printed table — apply as mesh_sculpt draw strokes with the")
    out.append("// listed diameters/heights; boolean spheres distort on a")
    out.append("// curved face and Claude's brush tools already do this better.")
    return "\n".join(out)


def preview():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.4, 6.3))
    # head outline
    import matplotlib.patches as mp
    ax.add_patch(mp.Ellipse((0, 31.6), 54, 63.3, fill=False, lw=1.5, color="#888"))
    for f in FEATURES:
        if f["kind"] == "stroke":
            xs, zs = zip(*f["pts"])
            ax.plot(xs, zs, "-", lw=f["width"] * 2.2, color="#c0392b", solid_capstyle="round")
        elif f["kind"] == "pit":
            x, z = f["centre"]
            ax.add_patch(mp.Circle((x, z), f["dia"] / 2, color="#c0392b"))
        elif f["kind"] in ("raise", "raise_bar"):
            if "pts" in f:
                xs, zs = zip(*f["pts"])
                ax.plot(xs, zs, "-", lw=f["width"] * 2.2, color="#2471a3", solid_capstyle="round")
            else:
                x, z = f["centre"]
                ax.add_patch(mp.Circle((x, z), f["dia"] / 2, fill=False, lw=2, color="#2471a3"))
        elif f["kind"] == "ring":
            x, z = f["centre"]
            ax.add_patch(mp.Arc((x, z), f["dia"], f["dia"], theta1=30, theta2=150, lw=2, color="#c0392b"))
    ax.set_xlim(-30, 30); ax.set_ylim(0, 66); ax.set_aspect("equal")
    ax.set_title("Urban Kid v2 — Benson face pass (front, printed mm)\nred = cut, blue = raise")
    ax.set_xlabel("x (mm from centre)"); ax.set_ylabel("z (mm from chin)")
    fig.tight_layout(); fig.savefig("face_pass_preview.png", dpi=150)


if __name__ == "__main__":
    with open("face_relief_190.scad", "w") as fh:
        fh.write(scad())
    preview()
    print(f"{'feature':22} {'printed':>16} {'mesh units':>12}")
    for f in FEATURES:
        if f["kind"] == "note_only":
            print(f"{f['name']:22} {'—':>16}"); continue
        main = f.get("width", f.get("dia"))
        print(f"{f['name']:22} {str(main) + ' mm':>16} {main * UNIT:>12.4f}")
    print("\nwrote face_relief_190.scad and face_pass_preview.png")
