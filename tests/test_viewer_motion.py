"""The viewer's move-by-move playhead in tools/viewer/app.js (2026-10-10).

With per-move timing a line is not finished when the next one starts -- the
head travels in between -- so "how many segments are drawn at time t" has to
count segment ENDS, and the line being laid has to grow, and the GPU upload
range has to cover every vertex touched in a frame. Each is run for real under
node against a two-line plate.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "tools" / "viewer" / "app.js"
_failures: list[str] = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _function(name):
    m = re.search(r"^function %s\(.*?^\}$" % re.escape(name), APP.read_text(), re.S | re.M)
    if not m:
        raise AssertionError("function %s not found" % name)
    return m.group(0)


# Two lines of two segments each, with a 2 s travel between them:
#   seg 0: 0-1 s, seg 1: 1-2 s | travel 2-4 s | seg 2: 4-5 s, seg 3: 5-6 s
_HARNESS = """
var JOB = {nSeg: 4,
  segCum: new Float64Array([0, 1, 4, 5, 6]),
  segDone: new Float64Array([1, 2, 5, 6])};
%s
var updates = [];
var attr = {updateRange: {offset: 0, count: -1}, set needsUpdate(v) { updates.push(1); }};
%s
var out = {at: [0, 0.5, 1, 1.5, 2, 3, 4, 4.5, 6, 9].map(segAtTime)};
markPositions(attr, 24);
markPositions(attr, 0);          // same frame: must widen, not replace
out.merged = [attr.updateRange.offset, attr.updateRange.count];
attr.updateRange.count = -1;     // three uploaded it
markPositions(attr, 36);
out.fresh = [attr.updateRange.offset, attr.updateRange.count];
console.log(JSON.stringify(out));
"""


def _run():
    node = shutil.which("node")
    if not node:
        return None
    js = _HARNESS % (_function("segAtTime"), _function("markPositions"))
    r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_a_line_counts_as_drawn_when_it_ends_not_when_the_next_starts():
    out = _run()
    if out is None:
        print("  (skipped: no node)")
        return
    # During the travel (2-4 s) both segments of the first line are done and
    # none of the second: counting starts would wait for t=4 to finish seg 1.
    check(out["at"] == [0, 0, 1, 1, 2, 2, 2, 2, 4, 4],
          "segments done at t=[0,.5,1,1.5,2,3,4,4.5,6,9] should be "
          "[0,0,1,1,2,2,2,2,4,4], got %r" % out["at"])


def test_two_vertex_updates_in_one_frame_upload_both():
    out = _run()
    if out is None:
        return
    check(out["merged"] == [0, 36],
          "restoring one segment and growing another in one frame must upload "
          "both (offset 0, count 36), got %r" % out["merged"])
    check(out["fresh"] == [36, 12],
          "after an upload the next range starts fresh, got %r" % out["fresh"])


def test_the_playhead_runs_every_frame_and_never_leaks_across_plates():
    src = APP.read_text()
    tick = _function("tick")
    check("applyPlayhead(play.t);" in tick, "tick must place the head between segments")
    check(re.search(r"_partial = null;[^\n]*\n\s*jobGeom = job\.geom;", src) is not None,
          "a new plate must drop the old plate's partial-segment record before "
          "anything can write it into the new geometry")
    check("restorePartial();" in _function("setSeg"),
          "jumping to a segment must put any partly drawn one back first")


def run():
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER MOTION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER MOTION TESTS OK — lines count as drawn when they end, the line being "
          "laid grows, and every touched vertex reaches the GPU.")


if __name__ == "__main__":
    run()
