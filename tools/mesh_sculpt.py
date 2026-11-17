"""Sculpting in code: ZBrush-style brushes on a dense triangle mesh (2026-11-17).

Scott, on the first Urban Kid: "The detail needs to be much better. Much more
realistic." His references (sculpted figures on MakerWorld) get their faces and
clothes from brush work on meshes of millions of polygons; shapes built from
primitives can't. This is that brush work, driven by stroke coordinates instead
of a tablet, so a sculpt is a script that can be read, re-run and changed.

Brushes (all lengths in the mesh's own units; every brush takes `mirror_x` to
mirror the stroke across a plane x = mirror_x, for faces):

  move(c, r, delta)            grab: drag the surface near c by delta
  draw(c, r, h)                push out (h > 0) or in (h < 0) along the normal
  stroke(path, r, h)           draw along a polyline: a ridge or a soft furrow
  crease(path, r, depth, pinch) a cut along a polyline that also pulls the
                               surface toward the line: the "DamStandard" brush,
                               for eyelid folds, lip lines, seams
  smooth(c, r, iters)          relax the surface
  dots(points, r, depth)       punched dots: stitching, pores, rivets
  noise(mask, amp, scale)      fine surface texture inside a region

Every brush works on the vertices within its radius only (a KD-tree), so a
stroke on an 800k-vertex head takes well under a second.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import trimesh
from scipy.spatial import cKDTree


def falloff(t, sharp=1.0):
    """1 at the centre, 0 at t = 1, smooth both ends: (1 - t^2)^3, sharpened by
    raising to `sharp`."""
    t = np.clip(t, 0.0, 1.0)
    return ((1.0 - t * t) ** 3) ** sharp


def _seg_dist(p, a, b):
    """Distance from points p to the segment a-b, and the parameter along it."""
    ab = b - a
    t = np.clip(((p - a) @ ab) / max(float(ab @ ab), 1e-18), 0.0, 1.0)
    q = a + t[:, None] * ab
    return np.linalg.norm(p - q, axis=1), q


class Sculpt:
    def __init__(self, mesh: trimesh.Trimesh):
        self.m = mesh
        self.V = np.asarray(mesh.vertices, dtype=np.float64).copy()
        self.F = np.asarray(mesh.faces)
        self._tree = None
        self._N = None
        self._L = None
        self.active = None          # a boolean mask: brushes touch only these vertices
        self.log = []

    # ---------- bookkeeping ----------
    def _dirty(self):
        self._tree = None
        self._N = None

    @property
    def tree(self):
        if self._tree is None:
            self._tree = cKDTree(self.V)
        return self._tree

    @property
    def N(self):
        if self._N is None:
            fn = np.cross(self.V[self.F[:, 1]] - self.V[self.F[:, 0]], self.V[self.F[:, 2]] - self.V[self.F[:, 0]])
            n = np.zeros_like(self.V)
            for k in range(3):
                np.add.at(n, self.F[:, k], fn)
            self._N = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-18)
        return self._N

    def _near(self, c, r):
        idx = np.asarray(self.tree.query_ball_point(c, r), dtype=np.int64)
        return idx if self.active is None else idx[self.active[idx]]

    def _mirror(self, fn, mirror_x, *pts_args):
        """Call fn for the stroke and, with mirror_x set, again for its mirror."""
        fn(*pts_args)
        if mirror_x is not None:
            m = [np.array(a, dtype=np.float64) for a in pts_args]
            out = []
            for a in m:
                a = a.copy()
                if a.ndim == 1 and a.shape[0] == 3:
                    a[0] = 2 * mirror_x - a[0]
                elif a.ndim == 2:
                    a[:, 0] = 2 * mirror_x - a[:, 0]
                out.append(a)
            fn(*out)

    def front(self, x, z, axis_y=-1, tol=None):
        """The surface point seen from the front (the -y side by default) at
        (x, z): the vertex nearest the viewer within tol of that line."""
        tol = tol or 0.0015 * max(np.ptp(self.V, axis=0))
        cand = self.V if self.active is None else self.V[self.active]
        sel = cand[(np.abs(cand[:, 0] - x) < tol) & (np.abs(cand[:, 2] - z) < tol)]
        if not len(sel):
            raise ValueError(f"no surface at x={x}, z={z}")
        return sel[np.argmin(sel[:, 1] * -axis_y)] if axis_y < 0 else sel[np.argmax(sel[:, 1])]

    def mesh(self):
        return trimesh.Trimesh(self.V.copy(), self.F.copy(), process=False)

    # ---------- brushes ----------
    def move(self, c, r, delta, mirror_x=None, sharp=1.0):
        """Grab: drag the surface within r of c by delta (mirrored delta keeps
        its sign in y and z and flips in x)."""
        def one(c, d):
            idx = self._near(c, r)
            if len(idx):
                w = falloff(np.linalg.norm(self.V[idx] - c, axis=1) / r, sharp)
                self.V[idx] += w[:, None] * d
        c, delta = np.asarray(c, float), np.asarray(delta, float)
        one(c, delta)
        if mirror_x is not None:
            cm, dm = c.copy(), delta.copy()
            cm[0] = 2 * mirror_x - cm[0]
            dm[0] = -dm[0]
            one(cm, dm)
        self._dirty()

    def draw(self, c, r, h, mirror_x=None, sharp=1.0):
        def one(c):
            idx = self._near(c, r)
            if len(idx):
                w = falloff(np.linalg.norm(self.V[idx] - c, axis=1) / r, sharp)
                self.V[idx] += (w * h)[:, None] * self.N[idx]
        self._mirror(one, mirror_x, np.asarray(c, float))
        self._dirty()

    def _path_field(self, path, r):
        """Vertices near a polyline, their distance to it, and the nearest point."""
        path = np.asarray(path, float)
        seglen = np.linalg.norm(np.diff(path, axis=0), axis=1)
        # candidates: balls along the path
        n = max(2, int(seglen.sum() / (r * 0.5)) + 2)
        cum = np.concatenate([[0], np.cumsum(seglen)])
        s = np.linspace(0, cum[-1], n)
        pts = np.stack([np.interp(s, cum, path[:, k]) for k in range(3)], axis=1)
        idx = np.unique(np.concatenate(self.tree.query_ball_point(pts, r)).astype(np.int64))
        if self.active is not None and len(idx):
            idx = idx[self.active[idx]]
        if not len(idx):
            return idx, None, None
        P = self.V[idx]
        best = np.full(len(idx), np.inf)
        near = np.zeros_like(P)
        for a, b in zip(path[:-1], path[1:]):
            d, q = _seg_dist(P, a, b)
            better = d < best
            best[better] = d[better]
            near[better] = q[better]
        return idx, best, near

    def stroke(self, path, r, h, mirror_x=None, sharp=1.0):
        """Draw along a polyline: h > 0 a raised cord or ridge, h < 0 a soft furrow."""
        def one(path):
            idx, d, _ = self._path_field(path, r)
            if len(idx):
                w = falloff(d / r, sharp)
                self.V[idx] += (w * h)[:, None] * self.N[idx]
        self._mirror(one, mirror_x, np.asarray(path, float))
        self._dirty()

    def crease(self, path, r, depth, pinch=0.5, mirror_x=None):
        """A cut along a polyline: pushed in along the normal with a sharp V
        profile, the surface either side pulled toward the line (pinch 0-1)."""
        def one(path):
            idx, d, near = self._path_field(path, r)
            if not len(idx):
                return
            t = d / r
            wcut = falloff(t, 3.0)                 # a narrow V
            wpin = falloff(t, 1.0) * (1 - wcut)
            n = self.N[idx]
            self.V[idx] -= (wcut * depth)[:, None] * n
            pull = near - self.V[idx]
            pull -= (pull * n).sum(1)[:, None] * n   # tangential only
            self.V[idx] += (wpin * pinch)[:, None] * pull
        self._mirror(one, mirror_x, np.asarray(path, float))
        self._dirty()

    def _laplacian(self):
        if self._L is None:
            n = len(self.V)
            e = np.concatenate([self.F[:, [0, 1]], self.F[:, [1, 2]], self.F[:, [2, 0]]])
            e = np.concatenate([e, e[:, ::-1]])
            A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)).tocsr()
            A.data[:] = 1.0
            deg = np.asarray(A.sum(1)).ravel()
            self._L = sp.diags(1.0 / np.maximum(deg, 1)) @ A
        return self._L

    def smooth(self, c, r, iters=3, strength=0.5, mirror_x=None):
        L = self._laplacian()

        def one(c):
            idx = self._near(c, r)
            if not len(idx):
                return
            w = falloff(np.linalg.norm(self.V[idx] - c, axis=1) / r) * strength
            for _ in range(iters):
                avg = L[idx] @ self.V
                self.V[idx] += w[:, None] * (avg - self.V[idx])
        self._mirror(one, mirror_x, np.asarray(c, float))
        self._dirty()

    def dots(self, points, r, depth):
        """Punched dots (stitches, pores, rivets): each a small dish pushed in."""
        for c in np.asarray(points, float):
            idx = self._near(c, r)
            if len(idx):
                w = falloff(np.linalg.norm(self.V[idx] - c, axis=1) / r, 2.0)
                self.V[idx] -= (w * depth)[:, None] * self.N[idx]
        self._dirty()

    def noise(self, mask, amp, scale, seed=0, octaves=3):
        """Fine texture: value noise from a few random sine waves, applied along
        the normal on the vertices where mask (a boolean array) is set."""
        rng = np.random.default_rng(seed)
        P = self.V[mask]
        f = np.zeros(len(P))
        for o in range(octaves):
            for _ in range(6):
                k = rng.normal(size=3)
                k = k / np.linalg.norm(k) * (2 * np.pi / scale) * (2 ** o)
                f += np.sin(P @ k + rng.uniform(0, 2 * np.pi)) / (2 ** o)
        f /= np.abs(f).max() + 1e-12
        self.V[mask] += (f * amp)[:, None] * self.N[mask]
        self._dirty()
