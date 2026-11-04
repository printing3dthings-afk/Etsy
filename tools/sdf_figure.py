"""Chubby figurines as signed-distance fields, meshed for the P1S (2026-11-04).

OpenSCAD's union() always leaves a crease where two round solids meet, and
nothing in it fillets a concave join. A figurine built from spheres and
capsules there looks assembled, not sculpted. Here every part is a distance
field and parts are joined with a polynomial smooth-min, whose k is the
fillet width in mm, so a head flows into its body like clay
(reports/Better 3D character design.md, "smooth-min SDFs for figurines").

What this adds beyond the research recipe:

- self_support(): every layer is made to sit within r = dz * tan(angle) of
  the layer under it, by growing material down from each overhang as a cone
  of the given angle. On a round form the cone is tangent to the surface at
  that angle, so the underside of a cheek or a heart's tip becomes a smooth
  37 deg point instead of a ledge the slicer props (DETAIL_STANDARD rule 7).
  It works per layer on true 2-D distances (an EDT): a 3-D SDF just above an
  underside reads tiny because the underside is right below it, and used as
  the in-plane distance it filled nothing.
- regions(): colour parts are the figure's own mesh cut by region volumes
  with manifold3d, so the colours tile the body exactly, with no gaps or
  overlaps between filaments.

Needs scikit-image (marching cubes): python3 -m pip install scikit-image.
Not in the Railway image, and the server never imports this.
"""
from __future__ import annotations

import numpy as np

# ---------- field operations ----------


def smin(a, b, k):
    """Polynomial smooth-min; k is the fillet width in mm (k <= 0: hard min)."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def rot(axis, deg):
    """Rotation matrix about 'x', 'y' or 'z'."""
    c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
    if axis == "x":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Grid:
    """A box of sample points. Every primitive takes a Grid and returns a field."""

    def __init__(self, lo, hi, step):
        self.step = float(step)
        # half a step off the integer lattice, so no sample lands exactly on a
        # flat face at a whole-mm height (zero samples made degenerate
        # triangles in the research test)
        self.axes = [np.arange(l - step / 2, h + step, step, dtype=np.float32) for l, h in zip(lo, hi)]
        self.X, self.Y, self.Z = np.meshgrid(*self.axes, indexing="ij")
        self.origin = np.array([a[0] for a in self.axes])

    def local(self, centre, R=None):
        """Coordinates relative to centre, rotated into a part's own frame."""
        x, y, z = self.X - centre[0], self.Y - centre[1], self.Z - centre[2]
        if R is None:
            return x, y, z
        R = np.asarray(R, dtype=np.float32)
        # p_local = R^T p
        return (R[0, 0] * x + R[1, 0] * y + R[2, 0] * z,
                R[0, 1] * x + R[1, 1] * y + R[2, 1] * z,
                R[0, 2] * x + R[1, 2] * y + R[2, 2] * z)


def ellipsoid(g, c, r, R=None):
    """Bound-corrected ellipsoid distance (exact on spheres, close elsewhere)."""
    x, y, z = g.local(c, R)
    k0 = np.sqrt((x / r[0]) ** 2 + (y / r[1]) ** 2 + (z / r[2]) ** 2)
    k1 = np.sqrt((x / r[0] ** 2) ** 2 + (y / r[1] ** 2) ** 2 + (z / r[2] ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def stick(g, a, b, ra, rb):
    """A capsule from a to b whose radius runs ra -> rb (a limb)."""
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    ba = b - a
    px, py, pz = g.X - a[0], g.Y - a[1], g.Z - a[2]
    h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / float(ba @ ba), 0.0, 1.0)
    dx, dy, dz = px - ba[0] * h, py - ba[1] * h, pz - ba[2] * h
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * h)


def heart2d(u, v, width, side_deg=37.0, overlap=0.9, notch_k=0.0):
    """A heart in the (u, v) plane, tip at v = 0, pointing down.

    Two round lobes of radius rc centred (+-cx, cy), and a V whose sides lean
    side_deg from upright and touch the lobes. At 37 the heart's lower edges
    print without support standing on its tip; its height is then about its
    width. overlap = cx / rc sets the notch between the lobes; notch_k rounds
    it (a sharp notch runs down a puffy heart's face as a crease). Drawn from
    scratch (two circles and two half-planes), not from anyone's code.
    Returns (field, height).
    """
    a = np.radians(side_deg)
    rc = width / 2.0 / (1.0 + overlap)
    cx = overlap * rc
    cy = (cx * np.cos(a) + rc) / np.sin(a)     # V side tangent to the lobe
    left = np.sqrt((u + cx) ** 2 + (v - cy) ** 2) - rc
    right = np.sqrt((u - cx) ** 2 + (v - cy) ** 2) - rc
    uu = np.abs(u)
    # capped where the side meets the lobe, below the lobe's centre
    vee = np.maximum(uu * np.cos(a) - v * np.sin(a), v - (cy - rc * np.sin(a)))
    return np.minimum(smin(left, right, notch_k), vee), cy + rc


def fine_axes(us, vs, refine=4):
    """us, vs subdivided `refine` times, ending on the same samples."""
    return (np.linspace(us[0], us[-1], (len(us) - 1) * refine + 1),
            np.linspace(vs[0], vs[-1], (len(vs) - 1) * refine + 1))


def exact2d(shape_fn, us, vs, refine=4, inside=None):
    """The true signed distance of a 2-D shape, on the grid us x vs.

    shape_fn(u, v) need only be negative inside (or pass `inside`, a mask on
    fine_axes(us, vs, refine)). A union of shape fields is not a distance
    inside: where two parts meet, one field reads near zero deep inside the
    union, and a puffy() extrusion dips along that line (the heart's first
    face had a fold across it, 2026-11-04). This rasterises the shape
    `refine` times finer and measures with an EDT instead.
    """
    from scipy.ndimage import distance_transform_edt as edt

    du, dv = float(us[1] - us[0]), float(vs[1] - vs[0])
    if inside is None:
        U, V = np.meshgrid(*fine_axes(us, vs, refine), indexing="ij")
        inside = shape_fn(U, V) < 0
    h = (du / refine, dv / refine)
    d = np.where(inside, -(edt(inside, sampling=h) - h[0] / 2), edt(~inside, sampling=h) - h[0] / 2)
    return d[::refine, ::refine]


def support_rows(inside, step_u, step_v, angle=37.0):
    """Make a 2-D shape self-supporting in its own plane: rows are heights (v,
    axis 1, bottom first), columns run across (u, axis 0).

    For a thin upright leaf (an ear) the 3-D cones of self_support() erode
    through its thickness from both faces and vanish in a couple of mm, so its
    outline has to be made printable in the leaf's own plane. Each row's
    extent is carried down from the rows above, shrinking by
    (height above) * tan(angle) at each end; continuous, so no pixel snapping.
    Works row by row on the solid's span, so it is meant for convex-ish leaves.
    """
    nu, nv = inside.shape
    u = np.arange(nu) * step_u
    t = step_v * np.tan(np.radians(angle))
    lo = np.full(nv, np.inf); hi = np.full(nv, -np.inf)
    for k in range(nv):
        cols = np.flatnonzero(inside[:, k])
        if len(cols):
            lo[k], hi[k] = u[cols[0]] - step_u / 2, u[cols[-1]] + step_u / 2
    flo, fhi = lo.copy(), hi.copy()
    for k in range(nv - 2, -1, -1):
        flo[k] = min(lo[k], flo[k + 1] + t)
        fhi[k] = max(hi[k], fhi[k + 1] - t)
    out = inside.copy()
    for k in range(nv):
        if flo[k] < fhi[k]:
            out[:, k] |= (u > flo[k]) & (u < fhi[k])
    return out


def puffy(d2, depth_coord, half, round_r):
    """Extrude a 2-D field to +-half and round its edges by round_r."""
    qx = d2 + round_r
    qy = np.abs(depth_coord) - half + round_r
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2)
    return out + np.minimum(np.maximum(qx, qy), 0) - round_r


def cut_base(g, d):
    """Flat base on z = 0."""
    return np.maximum(d, -g.Z)


# ---------- printability ----------


def base_prism(g, d, height=0.8, outset=0.0):
    """Stand the bottom `height` mm straight up: each layer under it is at least
    the layer at `height`.

    Where a form leans out just above the plate (a heart standing on its tip,
    a round belly), the slicer's elephant-foot compensation shrinks the first
    layer a further 0.15 mm, so the next layers overhang it and get propped:
    107 support moves under the cow's heart, all below 0.8 mm (2026-11-04).
    `outset` widens that foot a little: standing straight, the slicer still
    propped 77 moves under the heart's tip, with no layer of the mesh more
    than 0.11 mm past the one below it.
    """
    k = int(np.searchsorted(g.axes[2], height))
    ref = d[:, :, k]
    for j in range(k):
        z = g.axes[2][j]
        if z > 0:
            # capped by the base cut's own value: copied as is, the layer at
            # `height` read -0.8 just above the plate, and marching cubes put
            # the bottom face at z = -0.13, so the slicer lifted the whole
            # figure and the maker's mark slid off its layers
            d[:, :, j] = np.minimum(d[:, :, j], np.maximum(ref - outset, -z))
    return d


def _layer_sd2(layer, step, refine):
    """Signed 2-D distance of a layer's solid (field < 0), refine x finer."""
    from scipy.ndimage import distance_transform_edt as edt, zoom

    fine = zoom(layer, refine, order=1)          # bilinear: the boundary moves sub-pixel
    inside = fine < 0
    h = step / refine
    if not inside.any():
        return None
    d = np.where(inside, -(edt(inside) * h - h / 2), edt(~inside) * h - h / 2)
    # back to the coarse grid: average each refine x refine block
    n0, n1 = layer.shape
    d = d[: n0 * refine, : n1 * refine].reshape(n0, refine, n1, refine).mean(axis=(1, 3))
    return d.astype(np.float32)


def self_support(g, d, angle=37.0, refine=4):
    """Grow material down from every overhang as a cone of `angle` from upright.

    Returns (field, added mm3). Each layer becomes its own solid unioned with
    every layer above it eroded by (height above) * tan(angle), in true 2-D
    distance: M_k = min(sd2(D_k+1), M_k+1) + r is carried as a continuous
    field, so the cone keeps its angle. The first version re-thresholded each
    layer to whole pixels before eroding it, so the cone could only shrink a
    whole 0.25 mm pixel per 0.25 mm layer: 45 deg, not 37, and the slicer
    propped every one (12,222 support moves on the cow, 2026-11-04).
    """
    step = g.step
    r = step * np.tan(np.radians(angle))
    out = d.copy()
    nz = d.shape[2]
    M = None
    before = int((d < 0).sum())
    for k in range(nz - 2, -1, -1):
        s2 = _layer_sd2(d[:, :, k + 1], step, refine)
        if s2 is None and M is None:
            continue
        src = s2 if M is None else (M if s2 is None else np.minimum(s2, M))
        M = src + r
        out[:, :, k] = np.minimum(d[:, :, k], M)
    return out, (int((out < 0).sum()) - before) * step ** 3


def mesh(g, d):
    """Marching cubes at level 0 into a trimesh (inside negative)."""
    import trimesh
    from skimage.measure import marching_cubes

    d = np.where(np.abs(d) < 1e-6, 1e-5, d).astype(np.float32)
    # a layer of empty space all round, so a region that runs to the edge of
    # the grid (a colour skin is open on its outside) still closes
    d = np.pad(d, 1, constant_values=1.0)
    v, f, _, _ = marching_cubes(d, 0.0, spacing=(g.step,) * 3)
    v = v + g.origin - g.step
    m = trimesh.Trimesh(v, f[:, ::-1], process=True)
    if m.volume < 0:
        m.invert()
    return m


def to_manifold(m):
    import manifold3d as mf
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def from_manifold(M):
    import trimesh
    me = M.to_mesh()
    return trimesh.Trimesh(np.asarray(me.vert_properties)[:, :3], np.asarray(me.tri_verts), process=True)


def overhang_report(m, angle=40.0, floor=0.3):
    """Area (mm2) of faces overhanging more than `angle` from upright, off the bed."""
    n = m.face_normals
    c = m.triangles_center
    bad = (n[:, 2] < -np.sin(np.radians(angle))) & (c[:, 2] > floor)
    return float(m.area_faces[bad].sum()), c[bad]
