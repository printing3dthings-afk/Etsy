"""Thread & Nut-Trap Plate: (a) a back plate with hex nut traps - M3/M4/M5
rows, trap across-flats at nominal +0.2/+0.4/+0.6 per row, depths nut
height + 0.2; (b) two printed M16x2 bolt+nut pairs, same nominal thread,
radial clearance 0.3 and 0.4 mm per side (the nut thread is shifted out by
the clearance; bolts are identical nominal). Threads are TRUE helical
sweeps of the ISO 60-degree profile (P=2, depth 5H/8=1.0825, crest flat
P/8, root flat P/4) - not stacked rings. Bolt: hex head AF22, thread
24 mm. Nut: hex AF24, 12 mm tall, thread runs the full height.
Label tiles name each pair's clearance."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
from shapely.geometry import Polygon
import textgeom as tg

P = 2.0                      # M16 coarse pitch
R_TIP = 8.0                  # bolt major radius (D16)
DEPTH = 5 * 0.8660254 * P / 8.0   # 1.0825
R_ROOT = R_TIP - DEPTH       # 6.9175 bolt minor radius
BASE_HW = 3 * P / 8.0        # ridge base half width 0.75
CREST_HW = P / 16.0          # crest half width 0.125
EMBED = 0.35

def sweep(prof, z0, length, steps_per_turn=60):
    """Helical sweep of a closed (dz, r) profile at full depth throughout.
    Ends are fan-capped; callers bury the start cap inside solid material
    and trim the far end flush with a slab difference after union."""
    n_turns = length / P
    n = int(np.ceil(n_turns * steps_per_turn)) + 1
    rings = []
    for i in range(n):
        tt = i / steps_per_turn
        th = 2 * np.pi * tt
        zb = z0 + P * tt
        rings.append([(r * np.cos(th), r * np.sin(th), zb + dz) for dz, r in prof])
    verts = [v for ring in rings for v in ring]
    m = len(prof)
    faces = []
    for i in range(n - 1):
        for j in range(m):
            a = i * m + j; b = i * m + (j + 1) % m
            c = (i + 1) * m + (j + 1) % m; d = (i + 1) * m + j
            faces.append((a, b, c)); faces.append((a, c, d))
    # end caps: centroid fans
    for ri, flip in ((0, True), (n - 1, False)):
        ring = rings[ri]
        cen = tuple(np.mean(ring, axis=0))
        ci = len(verts); verts.append(cen)
        for j in range(m):
            a = ri * m + j; b = ri * m + (j + 1) % m
            faces.append((ci, b, a) if flip else (ci, a, b))
    mesh = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=True)
    trimesh.repair.fix_normals(mesh)
    if mesh.volume < 0:
        mesh.invert()
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, 'sweep bad'
    return mesh

def hex_prism(af, z0, height):
    R = af / np.sqrt(3.0)
    pts = [(R * np.cos(np.radians(60 * k)), R * np.sin(np.radians(60 * k))) for k in range(6)]
    m = trimesh.creation.extrude_polygon(Polygon(pts), height=height)
    m.apply_translation([0, 0, z0])
    return m

def make_bolt(cx, cy):
    head = hex_prism(22.0, 0.0, 9.0)
    washer = tg.cyl(10.5, 1.2, zbot=9.0)
    core = tg.cyl(R_ROOT, 27.2, zbot=9.0, sections=96)
    prof = [(-BASE_HW, R_ROOT - EMBED), (BASE_HW, R_ROOT - EMBED),
            (CREST_HW, R_TIP), (-CREST_HW, R_TIP)]
    # sweep starts buried in the head/washer, runs past the top, trimmed
    # flush at 34.2 - the trim plane cuts core/thread interior, never a
    # coplanar end face (coplanar boolean faces crack on STL round-trip)
    thread = sweep(prof, 8.0, 30.0)
    bolt = tg.union([head, washer, core, thread])
    bolt = tg.difference(bolt, [tg.box(60, 60, 6, cx=0, cy=0, zbot=34.2)])
    bolt.apply_translation([cx, cy, 0])
    return bolt

def make_nut(cx, cy, clearance):
    # body built 0.5 proud top and bottom so the trim planes at z=0/12 cut
    # interior material, never a coplanar face (see make_bolt note)
    body = hex_prism(24.0, -0.5, 13.0)
    r_bore = R_TIP + clearance
    r_tip = R_ROOT + clearance
    bore = tg.cyl(r_bore, 14.0, zbot=-1.0, sections=96)
    body = tg.difference(body, [bore])
    prof = [(-BASE_HW, r_bore + EMBED), (BASE_HW, r_bore + EMBED),
            (CREST_HW, r_tip), (-CREST_HW, r_tip)]
    ridge = sweep(prof, -2.0, 16.0)
    nut = tg.union([body, ridge])
    nut = tg.difference(nut, [tg.box(60, 60, 4, cx=0, cy=0, zbot=12.0),
                              tg.box(60, 60, 4, cx=0, cy=0, zbot=-4.0)])
    nut.apply_translation([cx, cy, 0])
    return nut

def weld(mesh, tol=1e-4):
    """Merge vertex clusters closer than tol (the trim booleans leave pairs
    ~2e-7 mm apart at the trim planes; any float32/text export merges them
    and cracks the shell). Cluster-mean weld in float64, degenerate faces
    dropped; volume must not move."""
    from scipy.spatial import cKDTree
    V = mesh.vertices
    pairs = cKDTree(V).query_pairs(tol)
    if not pairs:
        return mesh
    parent = list(range(len(V)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(len(V))])
    uniq, inv = np.unique(roots, return_inverse=True)
    NV = np.zeros((len(uniq), 3)); cnt = np.zeros(len(uniq))
    np.add.at(NV, inv, V); np.add.at(cnt, inv, 1)
    NV /= cnt[:, None]
    F = inv[mesh.faces]
    keep = (F[:, 0] != F[:, 1]) & (F[:, 1] != F[:, 2]) & (F[:, 0] != F[:, 2])
    out = trimesh.Trimesh(vertices=NV, faces=F[keep], process=True)
    assert out.is_watertight and abs(out.volume - mesh.volume) < 0.5, 'weld broke mesh'
    return out

# ---- nut-trap plate ----
plate = tg.box(150, 44, 6, cx=0, cy=28)
TRAPS = [('M3', 5.5, 2.6, 40.0), ('M4', 7.0, 3.4, 28.0), ('M5', 8.0, 4.2, 16.0)]
COLS = [(-48.0, 0.2), (0.0, 0.4), (48.0, 0.6)]
tools = []
for name, af_nom, depth, ry in TRAPS:
    for cx, extra in COLS:
        af = af_nom + extra
        R = af / np.sqrt(3.0)
        pts = [(R * np.cos(np.radians(60 * k)), R * np.sin(np.radians(60 * k))) for k in range(6)]
        cut = trimesh.creation.extrude_polygon(Polygon(pts), height=depth + 1.0)
        cut.apply_translation([cx, ry, 6.0 - depth])
        tools.append(cut)
plate = tg.difference(plate, tools)
for name, af_nom, depth, ry in TRAPS:
    plate = tg.engrave(plate, name, 3.5, -68.0, ry, 6.0)
for cx, extra in COLS:
    plate = tg.engrave(plate, '+%.1f' % extra, 3.0, cx, 8.8, 6.0)
plate = tg.engrave(plate, 'M16X2', 3.5, 0.0, 46.5, 6.0)

# ---- bolt/nut pairs + label tiles ----
named = [('NutTrapPlate', plate)]
for tag, pair_cx, clr in (('A', -35.0, 0.3), ('B', 35.0, 0.4)):
    named.append(('Bolt' + tag, make_bolt(pair_cx - 17.0, -25.0)))
    named.append(('Nut' + tag, make_nut(pair_cx + 17.0, -25.0, clr)))
    tile = tg.box(34, 11, 2, cx=pair_cx, cy=-4.0)
    tile = tg.engrave(tile, 'CLR %.1f' % clr, 4.0, pair_cx, -4.0, 2.0)
    named.append(('Tile' + tag, tile))

named = [(name, weld(m)) for name, m in named]
scene = trimesh.util.concatenate([m for _, m in named])
tg.check(scene, 'ThreadNutTrapPlate')
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'ThreadNutTrapPlate.stl')
scene.export(out)
print('wrote', out)
# ALSO a scene 3MF (parts as named objects). The trim booleans left
# vertex pairs ~2e-7 mm apart at the trim planes; weld() above merges
# them, after which BOTH this 3MF and the STL round-trip as exactly 7
# watertight bodies. The build feeds Studio this 3MF (batch 2 route).
sc = trimesh.Scene()
for name, m in named:
    sc.add_geometry(m, node_name=name)
out3 = os.path.join(here, 'ThreadNutTrapPlate_src.3mf')
sc.export(out3)
print('wrote', out3)
