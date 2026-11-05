#!/usr/bin/env python3
"""Build love_letter_customizer.scad, the Giant Love Letter's MakerWorld
Parametric Model Maker file, from love_letter.scad (2026-11-05).

WHY IT IS BUILT, NOT WRITTEN. MakerWorld renders the file standalone, and its
validation gives up after about 60-75 s. love_letter.scad's body takes about
66 minutes under OpenSCAD 2021's CGAL: every raised piece is a stack of 4-20
skirted slabs (about 70 on the two faces), Cupid's pocket climbs in 20 steps of
a 3,739-point outline, and CGAL turns every boolean's operands into Nef
polyhedra, at about 0.35 ms per facet (measured: 20,480 facets 7 s, 81,920
facets 30 s). Restructured as booleans it stays slow: 20 plain slabs on a
shell already took 16 s.

So everything that does not change with the name is computed here once, exactly,
by OpenSCAD's Manifold engine from love_letter.scad itself, and written into the
customizer as one polyhedron, which needs no CGAL at all. The name is the only
thing the customizer builds: love_letter.scad's own name relief (the same
Fredoka SemiBold letters, the same size rule, the same skirted slabs), unioned
with the polyhedron in the one CGAL operation the render makes.

What changes from the shipped geometry, each measured (check_customizer.py):
  - Cupid's pocket outline is simplified to 0.01 mm and grown 0.01 mm, so it
    always contains the shipped pocket (Cupid's clearance is 0.3); his pegs are
    untouched. Its top edge climbs at 37 deg as the exact slope its 20 steps of
    0.05 approximated.
  - The relief's circles and the letters' curves use fewer segments, each
    keeping its outline within about 0.05 mm of the shipped one.
  - Manifold's simplify (0.001 mm) clears zero-width steps CGAL cannot take.

    python3 build_customizer.py       (writes love_letter_customizer.scad)
"""
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
LL = HERE.parent
OUT = HERE / "love_letter_customizer.scad"
LIBS = HERE.parents[4] / "assets" / "openscad_libs"
# an OpenSCAD with the Manifold engine (2026 snapshot), as ship.sh uses
FAST = os.environ.get("OPENSCAD_FAST", "/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun")
TOL = 0.01


def openscad(args, cwd):
    # the whole environment: without HOME, fontconfig can't find the fonts in
    # ~/.fonts (Fredoka, Montserrat) and the text silently falls back to another
    env = {**os.environ, "OPENSCADPATH": str(LIBS)}
    r = subprocess.run([FAST, "--backend=manifold", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stderr:
        sys.exit(f"openscad failed: {' '.join(args)}\n{r.stderr[-2000:]}")
    return r.stderr


def svg_rings(path):
    rings = []
    for d in re.findall(r'd="([^"]+)"', Path(path).read_text()):
        for sub in re.split(r"(?=M)", d):
            v = [float(x) for x in re.findall(r"-?[\d.]+(?:e-?\d+)?", sub)]
            if len(v) >= 6:
                rings.append(list(zip(v[0::2], v[1::2])))
    return rings


def pocket_polygon(tmp):
    """the pocket's 2D shape exactly as love_letter.scad draws it, then
    simplified and grown so it contains the original"""
    s = tmp / "pocket2d.scad"
    src = (LL / "love_letter.scad").read_text()
    mod = re.search(r"module pocket2d\(\) .*?;\n", src).group(0)
    s.write_text(f'$fn = 36; $fa = 2; $fs = 0.3;\nmodule cupid_outline() import("{LL / "cupid_white_outline.dxf"}");\n'
                 f"{mod}pocket2d();\n")
    openscad(["-o", str(tmp / "pocket2d.svg"), str(s)], tmp)
    rings = svg_rings(tmp / "pocket2d.svg")
    assert len(rings) == 1, f"the pocket is {len(rings)} rings"
    # OpenSCAD's SVG is y down
    p = Polygon([(x, -y) for x, y in rings[0]])
    q = p.simplify(TOL, preserve_topology=True).buffer(TOL, join_style=2, mitre_limit=2)
    assert q.contains(p), "the simplified pocket does not contain the shipped one"
    pts = list(q.exterior.coords)[:-1]
    print(f"pocket outline: {len(rings[0])} -> {len(pts)} points, area {p.area:.2f} -> {q.area:.2f} mm2")
    return pts


def fixed_body(tmp, pocket):
    """love_letter.scad's body_print with no name, its pocket drawn from the
    simplified outline: exported by Manifold, welded, checked closed"""
    src = (LL / "love_letter.scad").read_text()
    poly = "polygon([" + ",".join(f"[{x:.4f},{y:.4f}]" for x, y in pocket) + "]);"
    src = re.sub(r"module pocket2d\(\) .*?;\n", f"module pocket2d() {poly}\n", src)
    # The pocket's top edge climbing at POCKET_A, as the exact slope its 20 steps
    # of 0.05 approximate ("as a true 37 deg slope does"): the straight pocket, and
    # the same outline sheared up the slope to the face. Twenty copies of the
    # outline were 27,000 of the body's 60,000 triangles.
    src = re.sub(r"module cupid_pocket\(\) .*?pocket2d\(\);\n", """module cupid_pocket() on_front(-POCKET_D) translate(CUPID_AT) {
    translate([0, 0, -0.01]) linear_extrude(POCKET_D + 0.51) pocket2d();
    multmatrix([[1, 0, 0, 0], [0, 1, 1 / tan(POCKET_A), 0], [0, 0, 1, 0]]) translate([0, 0, -0.01]) linear_extrude(POCKET_D + 0.02) pocket2d();
    translate([0, POCKET_D / tan(POCKET_A), POCKET_D]) linear_extrude(0.5) pocket2d();
}
""", src, flags=re.S)
    assert "multmatrix" in src, "the pocket was not replaced"
    # The fixed relief's circles, at the fewest segments that keep each outline
    # within about 0.04 mm of the shipped one, r (1 - cos(180 / n)): far under a
    # 0.4 nozzle's reach. Each slab's wall is two triangles a segment, and the
    # seal alone is 20 slabs, so these set most of CGAL's time.
    for old, new in [("circle(SEAL_R - 1.5, $fn = 90)", "circle(SEAL_R - 1.5, $fn = 48)"),   # r 13.5: 0.029
                     ("circle(2.6, $fn = 30)", "circle(2.6, $fn = 20)"),                     # r 2.6: 0.032
                     ("circle(6, $fn = 60)", "circle(6, $fn = 32)"),                         # r <= 5.1: 0.024
                     ("circle(1.2, $fn = 20)", "circle(1.2, $fn = 12)"),                     # r 1.2: 0.041
                     ("circle(13, $fn = 90); circle(11.2, $fn = 90)", "circle(13, $fn = 48); circle(11.2, $fn = 48)"),  # 0.028
                     ("circle(0.9, $fn = 16)", "circle(0.9, $fn = 12)")]:                    # r 0.9: 0.031
        assert old in src, old
        src = src.replace(old, new)
    work = LL / "_customizer_build.scad"            # beside it, so its includes resolve
    work.write_text(src)
    try:
        # 3MF, not STL: indexed, at 1e-6 mm, so the topology comes through exactly
        # (a float32 STL welded at 1e-5 came out open)
        openscad(["-D", 'part="body_print"', "-D", 'NAME=""', "-o", str(tmp / "fixed.3mf"), str(work)], LL)
    finally:
        work.unlink()
    m = trimesh.load(tmp / "fixed.3mf", force="mesh", process=False)
    # Manifold leaves zero-width steps where one slab's outline lies on the next
    # one's: zero-area triangles and doubled vertices, which OpenSCAD merges by
    # position before CGAL, which then calls the mesh open and drops it. Manifold's
    # own simplify collapses them, keeping it a closed manifold within 0.001 mm.
    import manifold3d as mf
    mesh = mf.Mesh(vert_properties=np.asarray(m.vertices, dtype=np.float32), tri_verts=np.asarray(m.faces, dtype=np.uint32))
    mesh.merge()
    M = mf.Manifold(mesh).simplify(1e-3).to_mesh64()
    m = trimesh.Trimesh(np.asarray(M.vert_properties)[:, :3], np.asarray(M.tri_verts), process=False)
    u, cnt = np.unique(m.vertices.round(6), axis=0, return_counts=True)
    assert (cnt > 1).sum() == 0 and (m.area_faces < 1e-8).sum() == 0, "points still coincide, or triangles have no area"
    assert m.is_watertight and m.is_winding_consistent, "the fixed body is not closed"
    print(f"fixed body: {len(m.faces)} triangles, {len(m.vertices)} vertices, {m.volume:.2f} mm3, {m.extents.round(2)}")
    return m


def name_block():
    """love_letter.scad's name relief, and what it needs from name_text.scad and
    relief_lib.scad, copied out so the customizer stands alone"""
    nt = (LL.parent / "name_text.scad").read_text()
    keep = [l for l in nt.splitlines() if l.startswith(("NAME_FONT", "NAME_CHARS", "NAME_ADV", "function", "module", "    "))]
    # The letters' curves at 12 segments, not 36: OLIVIA's outline moves 0.047 mm
    # (measured against $fn 36; 0.022 at 18), far under a 0.4 nozzle's reach, and
    # the name's six skirted slabs render in about 5 s under CGAL instead of 15.
    keep = [l.replace('valign = "center");', 'valign = "center", $fn = 12);') for l in keep]
    assert any("$fn = 12" in l for l in keep), "the name's text() call was not found"
    src = (LL / "love_letter.scad").read_text()
    D = re.search(r"W = (\d+); D = (\d+);", src)
    name2d = re.search(r"module name2d\(\) .*?;\n", src).group(0)
    rl = (LL.parents[2] / "christmas_village" / "relief_lib.scad").read_text()
    art_n = re.search(r"function art_n\(.*?;\n", rl).group(0)
    skirt = re.search(r"module art_skirt\(.*?children\(\);\n", rl, re.S).group(0)
    return "\n".join(keep), D.group(2), name2d, art_n, skirt


def write(pocket, m):
    nt, D, name2d, art_n, skirt = name_block()
    v = m.vertices
    pts = ",\n".join(",".join(f"[{a:.5f},{b:.5f},{c:.5f}]" for a, b, c in v[i:i + 8]) for i in range(0, len(v), 8))
    # triangles, not polygon faces: OpenSCAD 2021 splits polygons back into
    # triangles before CGAL, so merging the flat regions (36,194 triangles to
    # about 9,400 faces) saved no time (measured 11.8 s against 10.5)
    f = m.faces
    fcs = ",\n".join(",".join(f"[{a},{b},{c}]" for a, b, c in f[i:i + 16]) for i in range(0, len(f), 16))
    OUT.write_text(f'''// Giant Love Letter Mailbox: MakerWorld customizer (2026-11-05).
// Type the child's name; it is raised on the address side in Fredoka SemiBold
// and sized to fit. One print: the envelope's body (the lid and Cupid are their
// own prints in the model's 3MF files).
//
// Built by build_customizer.py from love_letter.scad. Everything but the name is
// one polyhedron here, computed once from the design, so the render makes a
// single union: about 16 s under OpenSCAD 2021's CGAL engine (24 s for a
// ten-letter name) and under a second with Manifold. As booleans the body took
// about 66 minutes under CGAL, and MakerWorld gives up after about a minute.
// check_customizer.py measures it against the shipped design.
// Do not edit the data below by hand; rebuild it.

// The child's name, on the address side
NAME = "OLIVIA";

/* [Hidden] */
SH = 1.2;
D = {D};
$fa = 2; $fs = 0.3; $fn = 36;
{nt}

{art_n}
{skirt}
module front(h, z0 = 0) translate([0, -D / 2 - z0, 0]) rotate([90, 0, 0]) art_skirt(h, 1) children();
{name2d}
module name_relief() if (len(NAME) > 0) front(1.0) name2d();

union() {{
    body();
    name_relief();
}}

// the envelope's body: love_letter.scad's body_print with no name, {len(f)} triangles
module body() polyhedron(points = [
{pts}],
faces = [
{fcs}]);
''')
    print(f"wrote {OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        pocket = pocket_polygon(tmp)
        m = fixed_body(tmp, pocket)
        write(pocket, m)
