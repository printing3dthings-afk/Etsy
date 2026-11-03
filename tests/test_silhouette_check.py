"""tools/silhouette_check.py: the drawing-quality checks, on the exact defects
Scott caught in the Valentine Cupid drafts (2026-11-03/04).

- a far knee folded the wrong way ("legs backwards", draft 8db56c41)
- the bow running into the face ("the bow is part of the face", 8db56c41 and
  9737a502, overlapping it; the accepted drafts cleared it by 1.87 mm)
- detail scratched into the face as engraved lines ("too cluttered")
plus the print-side failures the same checks guard: a slot that prints closed,
a member under three beads, a speck of a hole, a twinned pose.
"""
import sys
from pathlib import Path

from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import silhouette_check as sc  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _levels(results):
    return [r[0] for r in results]


def _y_up(p):
    return (p[0], -p[1])


def test_backwards_knee_from_draft_8db56c41_fails():
    # the far leg exactly as drawn in 8db56c41 (its grid, y down): hip, knee, ankle
    hip, knee, ankle = (_y_up(p) for p in ((270, 1110), (165, 1165), (105, 1215)))
    bend = sc.joint_bend("knee", hip, knee, ankle, 1)
    check(bend < -5, f"8db56c41's far knee should read as backwards, got {bend:.1f} deg")
    res = sc.check_joints([("far leg", "knee", hip, knee, ankle, 1)])
    check(_levels(res) == ["FAIL"], f"backwards knee should FAIL, got {res}")


def test_fixed_knees_pass():
    # the current Cupid's legs (27567838, reference px y down) and 9737a502's (mm, y up)
    legs = [
        ("near", [_y_up(p) for p in ((392, 664), (418, 764), (296, 866))]),
        ("far", [_y_up(p) for p in ((262, 688), (162, 760), (72, 796))]),
        ("9737 far", [(21.6, 15.6), (13.6, 11.2), (7.4, 11.4)]),
    ]
    for name, (h, k, a) in legs:
        b = sc.joint_bend("knee", h, k, a, 1)
        check(b > 5, f"{name} knee should bend forward, got {b:.1f} deg")


def test_knee_and_elbow_mirror_with_facing():
    hip, knee, ankle = (0, 0), (0.5, -5), (-2, -9)     # standing, shin folded back
    check(sc.joint_bend("knee", hip, knee, ankle, 1) > 0, "knee facing +x")
    flip = [(-x, y) for x, y in (hip, knee, ankle)]
    check(sc.joint_bend("knee", *flip, -1) > 0, "the same knee facing -x")
    sh, el, wr = (0, 0), (-0.5, -5), (3, -8)            # forearm folded forward
    check(sc.joint_bend("elbow", sh, el, wr, 1) > 0, "elbow folds forward")
    check(sc.joint_bend("knee", sh, el, wr, 1) < 0, "the elbow's bend is backwards for a knee")


def test_parse_joints_echo():
    text = 'ECHO: "JOINT", "near leg", "knee", [26.6, 20.4], [28.4, 13.6], [18.6, 6.7], 1\n' \
           'ECHO: "other", 3\n'
    j = sc.parse_joints(text)
    check(len(j) == 1 and j[0][0] == "near leg" and j[0][1] == "knee" and j[0][5] == 1,
          f"parsed {j}")


def test_bow_into_face_fails_and_clear_bow_passes():
    head = Point(0, 0).buffer(8.6)
    # an arc of bow reaching 1.2 mm into the head, as 9737a502's did
    bow_in = affinity.translate(box(-0.6, -10, 0.6, 10), 8.6 - 1.2 + 0.6, 0)
    res = sc.check_apart(head, bow_in, "bow / head")
    check(_levels(res) == ["FAIL"], f"overlapping bow should FAIL, got {res}")
    near = affinity.translate(box(-0.6, -10, 0.6, 10), 8.6 + 1.0 + 0.6, 0)
    check(_levels(sc.check_apart(head, near, "bow / head")) == ["FAIL"], "1.0 mm apart should FAIL")
    clear = affinity.translate(box(-0.6, -10, 0.6, 10), 8.6 + 1.87 + 0.6, 0)
    check(_levels(sc.check_apart(head, clear, "bow / head")) == ["OK"], "1.87 mm apart should pass")


def test_slot_that_prints_closed_fails():
    body = box(0, 0, 20, 10)
    slot = box(5, 3, 15, 3.4)                      # 0.4 mm wide, open nowhere: a near-touch
    shape = body.difference(slot)
    check("FAIL" in _levels(sc.check_gaps(shape)), "a 0.4 mm slot should FAIL")
    ok = body.difference(box(5, 3, 15, 4.0))      # 1.0 mm: prints open
    check(sc.check_gaps(ok) == [], f"a 1.0 mm slot should pass, got {sc.check_gaps(ok)}")


def test_member_under_three_beads_fails_and_bowstring_passes():
    a, b = box(0, 0, 10, 10), box(30, 0, 40, 10)
    thin = unary_union([a, b, box(10, 4.6, 30, 5.4)])      # 0.8 mm bar
    check("FAIL" in _levels(sc.check_thin(thin)), "a 0.8 mm bar should FAIL")
    string = unary_union([a, b, box(10, 4.35, 30, 5.65)])  # 1.3 mm, the Cupid's string
    check(sc.check_thin(string) == [], f"a 1.3 mm string should pass, got {sc.check_thin(string)}")


def test_speck_hole_and_second_piece_fail():
    speck = box(0, 0, 20, 20).difference(box(9, 9, 9.6, 9.6))
    check("FAIL" in _levels(sc.check_specks(speck)), "a 0.6 mm hole should FAIL")
    two = unary_union([box(0, 0, 10, 10), box(20, 0, 30, 10)])
    check("FAIL" in _levels(sc.check_specks(two)), "two pieces should FAIL")
    check(sc.check_specks(box(0, 0, 10, 10)) == [], "one clean piece passes")


def test_twinned_pose_fails_profile_passes():
    check(_levels(sc.check_twinning(Point(0, 0).buffer(10))) == ["FAIL"], "a circle is its own mirror")
    profile = Polygon([(0, 0), (30, 0), (30, 6), (12, 8), (4, 22), (0, 22)])
    check(_levels(sc.check_twinning(profile)) == ["OK"], "a lopsided profile passes")


def test_engraved_lines_count_as_clutter():
    shape = box(0, 0, 40, 40)
    strokes = unary_union([box(4, 4 + 6 * i, 30, 4.8 + 6 * i) for i in range(5)])
    top = shape.buffer(-0.2).difference(strokes)
    res = sc.check_clutter(shape, top)
    check("FAIL" in _levels(res), f"five engraved strokes should FAIL, got {res}")
    check(_levels(sc.check_clutter(shape, shape.buffer(-0.2))) == ["OK"], "a plain face passes")


def test_compare_reports_growth_where_it_happened():
    before = box(0, 0, 20, 20)
    after = unary_union([before, box(-3, 5, 0, 15)])      # the back bulged 3 mm
    res = sc.compare(after, before)
    grew = [m for lvl, m in res if m.startswith("grew")]
    check(grew and "up to 3.0 mm" in grew[0], f"growth should be located and measured, got {res}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SILHOUETTE CHECK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SILHOUETTE CHECK TESTS OK — the backwards knee, the bow in the face, engraved "
          "clutter, closed slots, thin members, specks and twinning are each caught.")


if __name__ == "__main__":
    run()
