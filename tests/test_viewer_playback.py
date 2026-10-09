"""Playback, visibility and rebuild bugs in tools/viewer/app.js (2026-09-27).

Six bugs Scott reported from reading the source, each confirmed against the
code before it was fixed. The two timing ones are tested by RUNNING the real
functions out of app.js under node, against a small hand-made plate, because
an off-by-one is exactly what a source-reading test would wave through. The
other four are pinned to the lines that fixed them.
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


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _src():
    return APP.read_text(encoding="utf-8")


def _function(name):
    """The whole top-level function, from its line to the closing brace at
    column 0."""
    m = re.search(r"^function %s\(.*?^\}$" % re.escape(name), _src(), re.S | re.M)
    if not m:
        raise AssertionError("function %s not found in app.js" % name)
    return m.group(0)


# A plate of 2 layers: segments 0-1 in layer 0, 2-4 in layer 1, each 1 s long.
# segCum[k] is when segment k STARTS, and segCum[nSeg] is the end of the print.
_HARNESS = """
var JOB = {nSeg: 5, total: 5,
  segCum: new Float32Array([0, 1, 2, 3, 4, 5]),
  layerSeg: new Int32Array([0, 2, 5]),
  segLayer: new Int32Array([0, 0, 1, 1, 1]),
  layers: [[20], [40]]};
var play = {t: 0, seg: 0};
var drawn = null;
function setSeg(n) { drawn = n; play.seg = n; }
function refreshReadout() {}
function setPlaying() {}
function syncLayerJump() {}
%s
%s
%s
var out = {
  atStart: segAtTime(0),
  midFirst: segAtTime(0.5),
  firstDone: segAtTime(1),
  midThird: segAtTime(2.5),
  atEnd: segAtTime(JOB.total),
  pastEnd: segAtTime(JOB.total + 10),
  layers: []
};
for (var L = 0; L < 2; L++) {
  gotoLayer(L);
  out.layers.push({drawn: drawn, t: play.t, layer: currentLayer(),
                   resumes: segAtTime(play.t)});
}
console.log(JSON.stringify(out));
"""


def _run_node():
    node = shutil.which("node")
    if not node:
        return None
    js = _HARNESS % (_function("segAtTime"), _function("currentLayer"),
                     _function("gotoLayer"))
    r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node failed:\n" + r.stderr)
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_the_last_segment_of_a_print_is_drawn():
    out = _run_node()
    if out is None:
        print("  (skipped: no node on PATH)")
        return
    # The bug: counting started segments minus one topped out at nSeg - 1.
    check(out["atEnd"] == 5,
          "at the end of the print all 5 segments must be drawn, got %r" % out["atEnd"])
    check(out["pastEnd"] == 5, "time past the end still draws 5, got %r" % out["pastEnd"])
    check(out["atStart"] == 0, "nothing is drawn at t=0, got %r" % out["atStart"])
    check(out["midFirst"] == 0,
          "half way through the first move nothing is complete, got %r" % out["midFirst"])
    check(out["firstDone"] == 1,
          "the first move is complete at t=1, got %r" % out["firstDone"])
    check(out["midThird"] == 2,
          "half way through the third move two are complete, got %r" % out["midThird"])


def test_going_to_a_layer_draws_all_of_it_and_playback_resumes_there():
    out = _run_node()
    if out is None:
        return
    first, second = out["layers"]
    # The bug: gotoLayer passed the last segment's INDEX where setSeg wants a
    # COUNT, stopping one move short of the layer it named.
    check(first["drawn"] == 2, "layer 1 is segments 0-1, so 2 drawn; got %r" % first["drawn"])
    check(second["drawn"] == 5, "layer 2 ends the plate, so 5 drawn; got %r" % second["drawn"])
    for i, L in enumerate(out["layers"]):
        check(L["layer"] == i,
              "after going to layer %d the readout must say layer %d, got %r"
              % (i + 1, i + 1, L["layer"] + 1))
        # play.t has to agree with the drawn count, or the next tick of the
        # clock snaps the replay somewhere else.
        check(L["resumes"] == L["drawn"],
              "the clock set by gotoLayer must map back to the same count: "
              "drew %r, clock says %r" % (L["drawn"], L["resumes"]))


def test_visibility_covers_every_feature_type():
    body = _function("applyVisibility")
    check("i < N_TYPE" in body,
          "applyVisibility must loop over every type (N_TYPE); a literal count "
          "left the wipe tower permanently on")
    check(not re.search(r"i < 1\d\b", body), "a hard-coded type count is back")


def test_part_only_drops_the_purge_tower_and_prime_line_real_print_does_not():
    src = _src()
    part = set(re.findall(r"(\d+)\s*:", re.search(r"var PART_HIDDEN = \{([^}]*)\}", src).group(1)))
    check({"10", "12"} <= part,
          "Part only must hide the prime line (10) and purge tower (12), hides %s" % sorted(part))
    real = set(re.findall(r"(\d+)\s*:", re.search(r"var REAL_HIDDEN = \{([^}]*)\}", src).group(1)))
    check(real == {"3", "9"}, "real-print mode must still hide only 3 and 9, got %s" % sorted(real))


def test_a_quality_change_restores_every_appearance_uniform():
    body = _function("setQuality")
    # A hand-picked copy of three uniforms dropped the filament override, the
    # layer shading and the saturation. The rebuild must re-derive them all.
    check("applyVisibility()" in body,
          "setQuality must re-apply the appearance state after rebuilding the material")


def test_a_late_payload_for_another_plate_is_not_mounted():
    # Every path names the plate it loaded: a fetched payload by the id it was
    # fetched for, a <script> fallback by its data-job tag.
    loader = _function("loadJob")
    check("mountRaw(raw, id)" in loader,
          "loadJob must mount a fetched payload under the id it fetched")
    check("setAttribute('data-job', id)" in _function("loadJobScriptTag"),
          "the script-tag fallback must tag the script with the plate it is for")
    body = _function("mountRaw")
    check(body.count("forId !== currentId") >= 2,
          "mountRaw must drop a stale payload both on arrival and after "
          "the two frames it waits before building")


def _parse_job_text(text):
    node = shutil.which("node")
    fn = _function("parseJobText")
    js = fn + "\nconst t=require('fs').readFileSync(0,'utf8');" \
         "try{const r=parseJobText(t);console.log(JSON.stringify({ok:true,name:r.name,layers:r.layers.length}))}" \
         "catch(e){console.log(JSON.stringify({ok:false}))}"
    r = subprocess.run([node, "-e", js], input=text, capture_output=True, text=True, timeout=60)
    return json.loads(r.stdout)


def test_a_plate_file_is_read_as_data_not_run():
    """2026-10-09: fetched and dropped plates are parsed, never executed. A
    dropped file run as a script could do anything the page can; and an inline
    script can be refused by the page's host where a parse cannot."""
    if not shutil.which("node"):
        print("  (skipped: no node on PATH)")
        return
    real = (ROOT / "tools" / "viewer" / "jobs" / "label_tile.js").read_text(encoding="utf-8")
    out = _parse_job_text(real)
    check(out.get("ok") and out.get("layers", 0) > 0,
          "a real plate file must parse to its layers, got %r" % out)
    out = _parse_job_text("alert(document.cookie)")
    check(out == {"ok": False}, "a file that is not a plate must be refused, got %r" % out)
    for name in ("loadJob", "loadPreviewFile"):
        body = _function(name)
        check("parseJobText(" in body, "%s must parse the payload as data" % name)
        check("createElement('script')" not in body and ".text = " not in body,
              "%s must not turn a payload into a script" % name)


def test_load_progress_measures_against_the_plates_own_size():
    """A compressing host sends the compressed Content-Length while the reader
    counts decompressed bytes, so the bar would fill long before the end."""
    check("Content-Length" not in _function("loadJobFetch"),
          "progress must not divide by the response's Content-Length")
    check("sizeMB" in _function("loadJob"),
          "progress must use the plate index's own payload size")


def test_a_recorded_video_lasts_the_same_whatever_the_plate():
    """At the top replay speed the median plate recorded 1.3 s (2026-10-09)."""
    m = re.search(r"var TL_SECONDS = (\d+)\b", _src())
    check(m is not None and 5 <= int(m.group(1)) <= 15,
          "the video length must be fixed between 5 and 15 s")
    body = _function("startTimelapse")
    check("JOB.total / TL_SECONDS" in body,
          "recording speed must fit the whole print into TL_SECONDS")
    check("SPEEDS[SPEEDS.length - 1]" not in body,
          "recording must not run at the top replay speed")
    check("(now - tl.t0) / 1000 * play.speed" in _function("tick"),
          "a recording must follow the wall clock, not the capped frame step")
    check("simulation, not print footage" in _function("tlFrame"),
          "every recorded frame must say it is a simulation")


def test_loading_a_plate_never_scrolls_the_page():
    """On a phone the plate list is not a scroll box, so scrollIntoView moved
    the window: every load scrolled 292 px down, header gone and the top of
    the printer cut off (2026-10-09). Only the list's own box may scroll."""
    body = _function("paintJobList")
    check("scrollIntoView" not in body, "paintJobList must not scroll the page")
    check("host.scrollTop" in body, "paintJobList must still keep the current card in its own list")


def test_a_recording_is_a_close_up_and_puts_the_view_back():
    start, stop = _function("startTimelapse"), _function("tlStop")
    check("setPartOnly(true)" in start, "a recording must frame the part, not the machine")
    check("setMotion(false)" in start, "the part must grow into frame, not sink out of it")
    check("setColorMode('filament')" in start, "a recording shows the spools' colours")
    check("tl.prev" in start and "tl.prev" in stop, "the view in use must be saved and restored")
    for what in ("setPartOnly(pv.part)", "setMotion(pv.motion)", "setColorMode(pv.color)"):
        check(what in stop, "tlStop must restore with %s" % what)
    check("tlFrame()" not in start,
          "copying the WebGL canvas outside its frame records a black first frame")


def test_a_rebuilt_machine_is_put_back_where_the_print_is():
    body = _function("restoreModeAfterRebuild")
    check("buildAMSState()" in body,
          "a rebuild must re-attach the AMS slots to the new unit's spools")
    check("setSeg(play.seg)" in body,
          "a rebuild must move the new bed and head to the paused print position")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER PLAYBACK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER PLAYBACK TESTS OK — the last bead is drawn, a layer jump lands "
          "on the whole layer and resumes there, every feature type toggles, and "
          "quality changes, late payloads and machine rebuilds keep the state.")


if __name__ == "__main__":
    run()
