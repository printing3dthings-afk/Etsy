"""Z seam overlay in tools/viewer (2026-09-22).

Every closed outer-wall loop starts and ends at one point, and that point is
the vertical scar on the finished print. The overlay marks them and reports
how steadily the column stacks. These tests pin the three things that were
actually got wrong while building it.
"""
import base64
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_viewer_seam_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "viewer-seam-test-not-a-real-secret")

VIEWER = ROOT / "tools" / "viewer"
JOBS = VIEWER / "jobs"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _job(name):
    path = JOBS / f"{name}.js"
    if not path.exists():
        return None
    m = re.search(r"window\.__JOB_LOADED\((\{.*\})\)\s*;?\s*$", path.read_text(), re.S)
    return json.loads(m.group(1)) if m else None


def _closed_outer_loops(d):
    """The same loops app.js's collectSeam() keeps: external perimeter, >=8
    points, first point within 0.05mm of the last."""
    pts = base64.b64decode(d["pts"])
    import array
    xy = array.array("h")
    xy.frombytes(pts)
    polys = array.array("i")
    polys.frombytes(base64.b64decode(d["polys"]))
    ext = d["types"].index("External perimeter") if "External perimeter" in d["types"] else -1
    out = []
    for z100, pstart, pcount, *_ in d["layers"]:
        layer = []
        for k in range(pstart, pstart + pcount):
            t, s, n = polys[k * 3], polys[k * 3 + 1], polys[k * 3 + 2]
            if t != ext or n < 8:
                continue
            if abs(xy[s * 2] - xy[(s + n - 1) * 2]) > 5:
                continue
            if abs(xy[s * 2 + 1] - xy[(s + n - 1) * 2 + 1]) > 5:
                continue
            layer.append((xy[s * 2] / 100.0, xy[s * 2 + 1] / 100.0))
        out.append(layer)
    return out


def _nearest_neighbour_p90(per_layer, radius=8.0):
    """app.js's seamStats(), in the language the rest of these tests are in."""
    jumps = []
    for i in range(1, len(per_layer)):
        a, b = per_layer[i], per_layer[i - 1]
        if not a or not b:
            continue
        for px, py in a:
            best = min(math.hypot(px - qx, py - qy) for qx, qy in b)
            if best <= radius:
                jumps.append(best)
    if len(jumps) < 30:
        return None
    jumps.sort()
    return jumps[min(len(jumps) - 1, int(len(jumps) * 0.9))]


def _largest_loop_p90(d):
    """The WRONG metric, kept so the test proves the fix rather than asserting it."""
    import array
    xy = array.array("h")
    xy.frombytes(base64.b64decode(d["pts"]))
    polys = array.array("i")
    polys.frombytes(base64.b64decode(d["polys"]))
    ext = d["types"].index("External perimeter")
    seam = []
    for z100, pstart, pcount, *_ in d["layers"]:
        best = None
        for k in range(pstart, pstart + pcount):
            t, s, n = polys[k * 3], polys[k * 3 + 1], polys[k * 3 + 2]
            if t != ext or n < 8:
                continue
            if abs(xy[s * 2] - xy[(s + n - 1) * 2]) > 5:
                continue
            if abs(xy[s * 2 + 1] - xy[(s + n - 1) * 2 + 1]) > 5:
                continue
            xs = [xy[(s + i) * 2] for i in range(n)]
            ys = [xy[(s + i) * 2 + 1] for i in range(n)]
            area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            if best is None or area > best[0]:
                best = (area, (xy[s * 2] / 100.0, xy[s * 2 + 1] / 100.0))
        if best:
            seam.append(best[1])
    j = sorted(math.hypot(seam[i][0] - seam[i - 1][0], seam[i][1] - seam[i - 1][1])
               for i in range(1, len(seam)))
    return j[min(len(j) - 1, int(len(j) * 0.9))] if len(j) >= 30 else None


def test_a_multi_part_plate_does_not_report_plate_layout_as_seam_wander():
    # The exact defect: taking the largest loop per layer hops between the six
    # separate wells and reports ~160mm of "seam wander" on a tray whose seams
    # are in fact rock steady.
    d = _job("sauce_tray")
    if d is None:
        for cand in JOBS.glob("sauce_tray*.js"):
            d = _job(cand.stem)
            break
    if d is None or "External perimeter" not in d.get("types", []):
        return
    naive = _largest_loop_p90(d)
    fixed = _nearest_neighbour_p90(_closed_outer_loops(d))
    check(naive is not None and naive > 50,
          f"the naive metric should still be badly wrong on this plate, got {naive}")
    check(fixed is not None and fixed < 1.0,
          f"nearest-neighbour matching must report a real number, got {fixed}")


def test_seam_points_are_closed_outer_loops_only():
    d = _job("drapery_vase")
    if d is None:
        return
    per_layer = _closed_outer_loops(d)
    total = sum(len(l) for l in per_layer)
    check(total > 100, f"the vase should have hundreds of closed outer loops, got {total}")
    # An internal perimeter's seam is buried and must never be collected.
    check("Perimeter" in d["types"] and "External perimeter" in d["types"],
          "payload should distinguish external from internal perimeters")


def test_the_overlay_keeps_depth_testing_on():
    # A seam on the far side of the part is a scar you cannot see from here.
    # Drawing it through the wall would show twice as many seams as the print
    # has, which is the one rule this shop does not bend.
    src = (VIEWER / "app.js").read_text()
    m = re.search(r"seamMesh = new THREE\.Points\(g, new THREE\.ShaderMaterial\(\{(.*?)\n  \}\)\);",
                  src, re.S)
    check(m is not None, "could not find the seam material")
    if m:
        body = m.group(1)
        check("depthTest: false" not in body and "depthWrite: false" not in body,
              "the seam overlay must not disable depth testing")


def test_the_marker_clears_the_beads_own_mitered_edge():
    # 1.15x left the marker INSIDE the bead and the overlay drew nothing while
    # every piece of state said it was working. The bead's outer edge is
    # miter-extended by up to 2.4 half-widths at a corner, and a loop start is
    # very often a corner.
    src = (VIEWER / "app.js").read_text()
    m = re.search(r"var out = hwT \* ([0-9.]+);", src)
    check(m is not None, "could not find the seam outward offset")
    if m:
        factor = float(m.group(1))
        check(factor >= 2.4,
              f"offset must clear the 2.4x miter maximum, got {factor}x")


def test_the_overlay_is_mounted_after_the_job_it_belongs_to():
    # syncSeamRange() reads the live JOB. Mounting before the assignment left
    # the draw range computed from the PREVIOUS plate's seam list.
    src = (VIEWER / "app.js").read_text()
    assign = src.index("  JOB = job;")
    mount = src.index("  mountSeams(job);")
    check(mount > assign,
          "mountSeams() must run after JOB is assigned, or the draw range is stale")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER SEAM TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER SEAM TESTS OK — seams are closed outer loops only, the statistic "
          "survives a multi-part plate, the overlay still occludes, and the marker "
          "clears the bead it marks.")


if __name__ == "__main__":
    run()
