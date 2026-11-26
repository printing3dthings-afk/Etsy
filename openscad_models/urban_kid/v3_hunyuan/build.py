#!/usr/bin/env python3
"""Urban Kid v3: Benson's Hunyuan3D mesh, made printable and edited (Scott, 2026-11-26).

Source: source/hunyuan-white-mesh.glb, made by Benson from his own concept art.
Stages (each writes out/<stage>.stl so a later stage can be judged on its own):
  base  - stand it up (glTF is Y-up), size it, sink the feet SINK mm into a disc base so the
          soles are flat and it stands.
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

TOTAL_H = 190.0      # Scott's size, base included, as v1
BASE_D = 90.0        # v1's 56 mm base at the 190 mm scale
BASE_H = 10.0
BASE_CH = 1.5        # top-edge chamfer
BASE_CENTRE = (0.0, -2.0)   # under the figure's centre of mass
SINK = 3.0           # feet sunk this far into the base: the soles end up flat


def to_manifold(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def to_trimesh(man):
    g = man.to_mesh()
    return trimesh.Trimesh(g.vert_properties[:, :3], g.tri_verts, process=True)


def load_figure():
    m = trimesh.load(HERE / "source" / "hunyuan-white-mesh.glb").to_geometry()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    fig_h = TOTAL_H - BASE_H + SINK
    m.apply_scale(fig_h / m.extents[2])
    m.apply_translation(-np.array([m.centroid[0], m.centroid[1], m.bounds[0][2]]))
    m.apply_translation([0, 0, BASE_H - SINK])
    return m


def base_disc():
    r = BASE_D / 2
    prof = [(0, 0), (r, 0), (r, BASE_H - BASE_CH), (r - BASE_CH, BASE_H), (0, BASE_H)]
    disc = mf.Manifold.revolve(mf.CrossSection([prof]), circular_segments=180)
    return disc.translate([BASE_CENTRE[0], BASE_CENTRE[1], 0])


def stage_base():
    fig = to_manifold(load_figure())
    out = fig + base_disc()
    m = to_trimesh(out)
    OUT.mkdir(exist_ok=True)
    m.export(OUT / "base.stl")
    print(f"base: {len(m.split())} body, watertight {m.is_watertight}, "
          f"extents {m.extents.round(1)}, {m.volume / 1000:.1f} cm3")
    return m


# ---- face: deepen the relief the mesh already has (unsharp mask on the surface) ----------
REFINE = 0.35        # mm; the face's edges were ~0.75 mm, too coarse for 1.2 mm grooves
FACE_Z = (140.0, 167.0)   # chin to under the cap, in the final frame
FACE_X = 19.0             # half-width of the face region
FACE_FRONT_Y = -12.0      # only the front of the head
FALLOFF = 3.0             # mm over which the effect fades to zero at the region's edges
DETAIL_ITER = 60          # smoothing passes that define "broad form" (~2.5 mm radius at 0.35 mm edges)
GAIN = 2.2                # how many times deeper the detail ends up


def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def face_weight(v):
    z0, z1 = FACE_Z
    wz = _smoothstep(z0, z0 + FALLOFF, v[:, 2]) * (1 - _smoothstep(z1 - FALLOFF, z1, v[:, 2]))
    wx = 1 - _smoothstep(FACE_X - FALLOFF, FACE_X, np.abs(v[:, 0]))
    wy = 1 - _smoothstep(FACE_FRONT_Y - FALLOFF, FACE_FRONT_Y, v[:, 1])
    return wz * wx * wy


def sharpen_face(fig):
    man = to_manifold(fig).refine_to_length(REFINE)
    m = to_trimesh(man)
    w = face_weight(m.vertices)
    # soften the old 0.75 mm facets on the face first, or they get deepened too
    soft = m.copy()
    trimesh.smoothing.filter_taubin(soft, lamb=0.5, nu=0.53, iterations=10)
    v = m.vertices + w[:, None] * (soft.vertices - m.vertices)
    m = trimesh.Trimesh(v, m.faces, process=False)
    broad = m.copy()
    trimesh.smoothing.filter_laplacian(broad, lamb=0.5, iterations=DETAIL_ITER,
                                       volume_constraint=False)
    n = broad.vertex_normals
    d = np.einsum("ij,ij->i", m.vertices - broad.vertices, n)
    v = m.vertices + ((GAIN - 1) * w * d)[:, None] * n
    out = trimesh.Trimesh(v, m.faces, process=False)
    print(f"face: {int((w > 0).sum())} verts moved, detail depth before "
          f"{np.percentile(np.abs(d[w > 0.9]), 99):.2f} mm (p99), gain {GAIN}")
    return out


def stage_face():
    fig = sharpen_face(load_figure())
    man = to_manifold(fig)
    if man.status() != mf.Error.NoError:
        raise SystemExit(f"face: sharpened mesh is not a manifold ({man.status()})")
    m = to_trimesh(man + base_disc())
    OUT.mkdir(exist_ok=True)
    m.export(OUT / "face.stl")
    print(f"face: {len(m.split())} body, watertight {m.is_watertight}, {len(m.faces)} faces")
    return m


# ---- the OBC nameplate and a chain that reads as chain --------------------------------------
TAG_C = (0.8, 112.2)          # (x, z) of the blank tag in Benson's mesh, measured on the chest map
TAG_SINK = 0.8                # the plate's back face this far into the hoodie
CHAIN = [[(-2.8, 128.0), (-1.2, 122.0), (0.8, 116.4)],     # (x, z) along each strand, collar to bail
         [(5.6, 127.4), (3.6, 121.6), (0.8, 116.4)]]
LINK = 1.4                    # one link per 1.4 mm: v1's curb pitch
LINK_R = (0.9, 1.0, 0.8)      # half-length, half-width, half-thickness: 1.8 x 2.0 x 1.6, v1's cord
LINK_OUT = 0.3                # each link's centre this far proud of the hoodie


def surface_at(m, x, z, spread=0.6):
    """Front-surface point and averaged normal at (x, z), from rays shot along +y."""
    from trimesh.ray.ray_triangle import RayMeshIntersector
    off = np.array([(0, 0), (spread, 0), (-spread, 0), (0, spread), (0, -spread)])
    o = np.array([[x + a, -120.0, z + b] for a, b in off])
    d = np.tile([0.0, 1.0, 0.0], (len(o), 1))
    loc, ray, tri = RayMeshIntersector(m).intersects_location(o, d, multiple_hits=False)
    p = loc[ray == 0][0] if (ray == 0).any() else loc.mean(0)
    n = m.face_normals[tri].mean(0)
    return p, n / np.linalg.norm(n)


def frame(n, along):
    """Right-handed frame: z = n (out of the surface), x = `along` made perpendicular to n."""
    x = np.asarray(along, float) - n * np.dot(along, n)
    x /= np.linalg.norm(x)
    return x, np.cross(n, x), n


def place_tag(fig):
    p, n = surface_at(fig, *TAG_C, spread=2.5)
    xl, yl, zl = frame(n, [1, 0, 0])
    if yl[2] < 0:                       # keep the letters upright
        xl, yl = -xl, -yl
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2] = xl, yl, zl
    T[:3, 3] = p - zl * TAG_SINK
    tag = trimesh.load(OUT / "tag_all.stl")
    tag.apply_transform(T)
    return tag, T


def chain_links(fig):
    ell = trimesh.creation.icosphere(subdivisions=2)
    ell.apply_scale(LINK_R)
    links = []
    for strand in CHAIN:
        pts = np.array(strand, float)
        seg = np.cumsum(np.r_[0, np.linalg.norm(np.diff(pts, axis=0), axis=1)])
        for s in np.arange(0, seg[-1], LINK):
            x, z = (np.interp(s, seg, pts[:, 0]), np.interp(s, seg, pts[:, 1]))
            x2, z2 = (np.interp(s + 0.5, seg, pts[:, 0]), np.interp(s + 0.5, seg, pts[:, 1]))
            p, n = surface_at(fig, x, z)
            q, _ = surface_at(fig, x2, z2)
            xl, yl, zl = frame(n, q - p if s + 0.5 <= seg[-1] else p - surface_at(fig, *pts[-2])[0])
            T = np.eye(4)
            T[:3, 0], T[:3, 1], T[:3, 2] = xl, yl, zl
            T[:3, 3] = p + zl * LINK_OUT
            e = ell.copy()
            e.apply_transform(T)
            links.append(e)
    return links


def stage_tag():
    fig = sharpen_face(load_figure())
    tag, _ = place_tag(fig)
    links = chain_links(fig)
    man = to_manifold(fig) + to_manifold(tag)
    man = mf.Manifold.batch_boolean([man] + [to_manifold(l) for l in links], mf.OpType.Add)
    m = to_trimesh(man + base_disc())
    m.export(OUT / "tag.stl")
    # the letters alone, in place, for the product gate's wall check
    lt = trimesh.load(OUT / "tag_letters.stl")
    lt.apply_transform(place_tag(fig)[1])
    lt.export(OUT / "tag_letters_placed.stl")
    print(f"tag: {len(links)} links; {len(m.split())} body, watertight {m.is_watertight}, "
          f"{len(m.faces)} faces")
    return m


if __name__ == "__main__":
    stages = sys.argv[1:] or ["base"]
    for s in stages:
        globals()[f"stage_{s}"]()
