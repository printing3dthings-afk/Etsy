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


def _swap_block():
    src = APP.read_text()
    m = re.search(r"^var SWAP_IN = .*?^var _swap = null, swapNow = null;$", src, re.S | re.M)
    if not m:
        raise AssertionError("swap constants not found")
    return m.group(0)


# One swap: segment 0 ends at t=10 in tool 0, segment 1 starts at t=75 in
# tool 1 -- a 65 s gap, the size the real cocoa cafe plate has.
_SWAP_HARNESS = """
var printerId = 'p1s', placed = [];
function placeHead(x, y, z) { placed.push([x, y, z]); }
var JOB = {nSeg: 3, segTool: new Uint8Array([0, 1, 1]),
  segCum: new Float64Array([0, 75, 76, 77]), segDone: new Float64Array([10, 76, 77])};
%s
%s
%s
%s
%s
var sw = swapPlan(1, 120, 100, 130, 110);
var out = {span: sw.keys[sw.keys.length - 1][0], phases: [], fan: [], loaded: [],
           swap: isSwapGap(1), same: isSwapGap(2)};
for (var t = 10; t <= 75.001; t += 0.25) {
  swapPlace(sw, t, 0.4, 0.6);
  var ph = swapNow.phase;
  if (out.phases[out.phases.length - 1] !== ph) { out.phases.push(ph); }
  out.fan.push(swapNow.fanOff ? 0 : 1);
  out.loaded.push(swapNow.loaded ? 1 : 0);
}
out.ys = sw.keys.map(function (k) { return k[2]; });
out.zs = placed.map(function (p) { return p[2]; });
out.end = placed[placed.length - 1];
out.unloadEnds = (out.loaded.indexOf(1) * 0.25);
out.dwell = [sw.dwellAt, sw.dwell];
JOB.segCum[1] = 30;   // a 20 s gap is not a swap, whatever the tools
out.short = isSwapGap(1);
printerId = 'ender3'; JOB.segCum[1] = 75;
out.other = isSwapGap(1);
console.log(JSON.stringify(out));
"""


def _run_swap():
    node = shutil.which("node")
    if not node:
        return None
    js = _SWAP_HARNESS % (_swap_block(), _function("swapMoveTime"), _function("isSwapGap"),
                          _function("swapPlan"), _function("swapPlace"))
    r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_a_swap_runs_bambus_sequence_in_exactly_the_modelled_time():
    out = _run_swap()
    if out is None:
        return
    check(abs(out["span"] - 65) < 1e-6,
          "the swap must fill the gap the motion model timed, 65 s, got %r" % out["span"])
    check(max(out["ys"]) >= 264.9 and min(out["ys"]) <= -2.9,
          "the head must reach the purge chute (Y265) and the cutter (Y-3), got %.1f..%.1f"
          % (min(out["ys"]), max(out["ys"])))
    check(max(out["zs"]) >= 3.3, "the bed must drop 3 mm clear of the print")
    check(out["end"][0] == 130 and out["end"][1] == 110 and abs(out["end"][2] - 0.6) < 1e-9,
          "the head must end on the next line at the next layer's height, got %r" % out["end"])
    want = ["lifting the nozzle clear", "to the purge chute", "wiping on the chute brush",
            "to the cutter", "cutting the filament", "unloading the old filament",
            "loading the new filament", "shaking off the purge", "back to the print"]
    seq = [p for p in out["phases"] if not p.startswith("to the chute")]
    pos = [seq.index(w) if w in seq else -1 for w in want]
    check(-1 not in pos and pos == sorted(pos),
          "the phases must run in the G-code's order, got %r" % out["phases"])


def test_the_swap_switches_fan_and_filament_when_the_gcode_does():
    out = _run_swap()
    if out is None:
        return
    fan = out["fan"]
    check(fan[0] == 1 and fan[-1] == 1 and 0 in fan,
          "the part fan goes off at the chute and back on after the load")
    at, dwell = out["dwell"]
    unload_end = out["unloadEnds"]
    check(abs(unload_end - (at + dwell * 28 / 57)) < 0.3,
          "the new filament counts as loaded after the 28 s unload share of the wait, "
          "at %.2f s, got %.2f" % (at + dwell * 28 / 57, unload_end))


def test_only_a_real_p1s_colour_change_is_choreographed():
    out = _run_swap()
    if out is None:
        return
    check(out["swap"] and not out["same"], "a swap is a change of tool")
    check(not out["short"], "a short gap is a travel, not a swap")
    check(not out["other"], "the sequence is the P1S's; other machines keep a plain travel")


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
