"""Guards tools/plate_audit.py -- the check that every plate can actually print.

The interesting failure here is not "the audit crashed". It is the audit
quietly measuring the wrong thing and reporting a clean bill of health, or
burying a real problem under two dozen false alarms. Both happened while it
was being written, and both are reproduced below with the exact plates that
produced them.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import plate_audit  # noqa: E402

JOBS = ROOT / "tools" / "viewer" / "jobs"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_the_numbers_are_bambus_not_ours():
    check(plate_audit.BED == 256.0,
          "printable area is no longer 256 mm -- that is Bambu's own "
          "printable_area for the P1 series")
    check(plate_audit.EXCLUDE == (0.0, 0.0, 18.0, 28.0),
          "reserved corner drifted from the P1S profile's bed_exclude_area")


def test_a_plate_with_no_wipe_tower_is_not_audited_against_its_own_skirt():
    """The empty-set bug, exactly as it fired.

    _bbox() selected `polys` wholesale when its keep-set was falsy, and an
    empty set is falsy. So every single-colour plate -- 70 of the 72 -- had
    its ENTIRE toolpath reported as a wipe tower, and mushroom and sundial
    failed the audit because their skirts, now labelled "the wipe tower",
    run past the plate edge. A real failure invented out of nothing.
    """
    r = plate_audit.audit(JOBS / "sundial.js")
    check(r["wipe"] is None,
          "sundial has no wipe tower but the audit found one: %r" % (r["wipe"],))
    check(not any("wipe tower" in e for e in r["errors"]),
          "sundial is being failed for a wipe tower it does not have: %s"
          % r["errors"])
    # and the plate that really does have one still reports it
    mc = plate_audit.audit(JOBS / "keychain_mc.js")
    check(mc["wipe"] is not None,
          "keychain_mc is a multi-colour plate -- its wipe tower went missing")


def test_centring_is_judged_on_the_part_outline_not_the_supports():
    """Supports grow on one side only.

    Measuring centring against every extrusion on the plate put 24 correctly
    arranged plates 1-3 mm 'off centre' -- flexi_seahorse, the label bins, the
    mochi fox -- because their support material only exists under the
    overhanging side. Twenty-four false alarms is the same as no audit.
    """
    for name in ("flexi_seahorse", "label_bin_L", "mochi_fox_v3", "haunted_manor"):
        r = plate_audit.audit(JOBS / (name + ".js"))
        check(not any("off the middle" in w for w in r["warnings"]),
              "%s is correctly arranged but flagged off-centre: %s"
              % (name, r["warnings"]))


def test_a_wide_part_is_flagged_for_its_skirt_and_not_for_itself():
    """sundial is 247.6 mm wide on a 256 mm plate.

    The part fits. Its skirt does not, and that is a real thing to know before
    pressing print -- but it is a warning about the skirt, not a claim that
    the part is unprintable.
    """
    r = plate_audit.audit(JOBS / "sundial.js")
    check(not r["errors"], "sundial's part fits; it should not be an error: %s"
          % r["errors"])
    check(any("skirt" in w for w in r["warnings"]),
          "sundial's skirt runs off the plate and nothing said so")
    check(r["part"][0] >= 0 and r["part"][2] <= plate_audit.BED,
          "sundial's part is outside the plate: %r" % (r["part"],))


def test_geometry_in_the_reserved_corner_fails():
    """Synthetic, because no real plate here does this -- which is the point.

    The reserved-corner rule has never fired on this catalogue, so without a
    constructed case it is untested code that would report success forever.
    This writes a real payload in the real format and runs the real audit over
    it: a 40 mm square parked in the front-left corner, where the toolhead
    parks and wipes.
    """
    import base64
    import json
    import tempfile

    pts = np.array([[200, 200], [4200, 200], [4200, 4200], [200, 4200],
                    [200, 200]], dtype=np.int16)          # 2..42 mm, hundredths
    polys = np.array([[0, 0, 5]], dtype=np.int32)
    payload = {
        "name": "Corner Squatter",
        "types": ["External perimeter"],
        "pts": base64.b64encode(pts.tobytes()).decode(),
        "polys": base64.b64encode(polys.tobytes()).decode(),
    }
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "corner.js"
        f.write_text("window.__JOB_LOADED(%s);" % json.dumps(payload))
        r = plate_audit.audit(f)
    check(any("reserved front-left corner" in e for e in r["errors"]),
          "a part sitting in the reserved corner was not flagged: %s" % r["errors"])


def test_every_plate_on_the_page_can_print_as_arranged():
    """The headline claim, checked rather than asserted."""
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = plate_audit.main([])
    check(code == 0, "plate_audit reports at least one plate that cannot "
                     "print:\n" + buf.getvalue())


def test_the_report_survives_a_plate_with_no_supports_and_no_skirt():
    """_bbox returns None for an absent feature; nothing downstream may assume
    a box is present."""
    for name in ("vase", "keychain", "cable_clip"):
        r = plate_audit.audit(JOBS / (name + ".js"))
        check(isinstance(r["errors"], list) and isinstance(r["warnings"], list),
              "%s produced a malformed report" % name)
        check(r["part"] is not None, "%s has no part geometry at all" % name)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append("%s raised:\n%s" % (fn.__name__, traceback.format_exc()))
    if _failures:
        print("PLATE AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PLATE AUDIT TESTS OK -- all 72 plates fit the P1S printable area, "
          "and the audit measures the part rather than its skirt or its "
          "supports.")


if __name__ == "__main__":
    run()
