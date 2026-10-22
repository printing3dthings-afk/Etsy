"""The viewer's video export (2026-10-21).

Scott: the timelapse button was "having trouble", and these clips go out on
social media. Reproduced headless the same day: a "10-second" recording
decoded to ONE frame, 670x691, VP9 WebM with no duration in its header,
because MediaRecorder records whatever the page manages to draw in real time.

The export now renders every frame at a fixed social size and encodes it with
WebCodecs into an MP4. These pin what made it right: frame-exact timing
rather than the wall clock, the sizes and the codec order, the caption that
says it is a simulation, the view put back afterwards, and the muxer
vendored into the offline site. The end-to-end run (a real MP4 decoded by
ffprobe, every frame present) is in tools/viewer/README.md, "Video export".
"""
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "tools" / "viewer"
APP = VIEWER / "app.js"
PAGE = VIEWER / "virtual_p1s.html"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _src():
    return APP.read_text(encoding="utf-8")


def _function(name):
    m = re.search(r"^function %s\(.*?^\}$" % re.escape(name), _src(), re.S | re.M)
    if not m:
        raise AssertionError("function %s not found in app.js" % name)
    return m.group(0)


def test_every_frame_is_rendered_not_recorded():
    """The cause of the one-frame video: real-time capture. Each frame's time
    comes from its index, never from the clock."""
    run, wc = _function("vidRun"), _function("vidWebCodecsSink")
    check("sink.add(vid.canvas, i)" in run, "frames must be encoded one by one")
    check("timestamp: Math.round(i * 1e6 / VID_FPS)" in wc,
          "a frame's timestamp must come from its index")
    check("JOB.total * Math.min(1, i / Math.max(1, Nb - 1))" in run,
          "the print's time must come from the frame index, ending on the finished part")
    check("captureStream" not in run and "MediaRecorder" not in run,
          "the export must not capture in real time")
    check("sink.backlog() > 3" in run and "encodeQueueSize" in wc,
          "the loop must wait for the encoder, not run ahead of it")
    check("if (vid && vid.on) { return; }" in _function("tick"),
          "the live loop must not draw over the export's frames")
    check("if (vid && vid.on) { return; }" in _function("onResize"),
          "a resize must not change the canvas mid-export")


def test_the_sizes_are_the_social_ones():
    src = _src()
    for w, h in ((1080, 1920), (1080, 1350), (1080, 1080)):
        check(re.search(r"w: %d, h: %d" % (w, h), src) is not None, "missing the %dx%d format" % (w, h))
    run = _function("vidRun")
    check("renderer.setPixelRatio(1)" in run and "renderer.setSize(f.w, f.h, false)" in run,
          "the renderer must draw at the format's own size, not the window's")
    check("camera.aspect = f.w / f.h" in run, "the camera must take the format's shape")


def test_always_h264_never_vp9():
    """Scott's first test clip was VP9 in an MP4 and played as a black screen
    on his phone (2026-10-21); the H.264 copy of the same frames played."""
    src = _src()
    check("vp09" not in src and "'vp9'" not in src, "nothing may encode VP9: phones and Instagram cannot play it")
    codec = _function("vidCodec")
    check("avc1.640028" in codec and "wasm" in codec,
          "H.264 from the browser first, then the WebAssembly H.264 encoder")
    wc = _function("vidWebCodecsSink")
    check("codec: 'avc'" in wc and "fastStart: 'in-memory'" in wc,
          "the browser's frames must go into an H.264 MP4 with its index at the front")
    wasm = _function("vidWasmSink")
    check("HME.createH264MP4Encoder" in wasm and "addFrameRgba" in wasm,
          "without a browser H.264 encoder, frames must go to h264-mp4-encoder")
    check("type: 'video/mp4'" in _function("vidRun"), "the saved file must be video/mp4")


def test_every_frame_says_it_is_a_simulation():
    cap = _function("vidCaption")
    check("not print footage" in cap, "the caption must say the clip is not print footage")
    run = _function("vidRun")
    d, e = run.find("vidDrawCaption(cap)"), run.find("sink.add(vid.canvas, i)")
    check(0 <= d < e, "the caption must be drawn on every frame before it is encoded")
    check("f.top * f.h" in cap, "the caption must sit below the apps' own top bar")


def test_the_buttons_clip_keeps_its_caption():
    """caption: false exists for the Etsy listing clips, made from a script
    (2026-10-22). The page's own button must still caption every frame."""
    src = _src()
    check("makeVideo(fmt, secs);" in src, "the dialog must call makeVideo without options")
    check("capOn = opts.caption !== false" in _function("vidRun"),
          "only an explicit caption: false may drop the caption")


def test_the_listing_clip_is_the_part_on_its_plate():
    """Scott's rule for the Etsy listing clips (2026-10-22): the print on the
    build plate, close up -- not the whole machine, not Part only's studio."""
    run = _function("vidRun")
    check("if (partOnly) { setPartOnly(false); }" in run and "setViewMode('chamber')" in run,
          "on the plate the machine view must stay, cut away, not Part only")
    hide = run[run.find("function vidHideMachine"):]
    for g in ("nozzle", "gantry", "yRails", "doorGroup", "chamber"):
        check(g in hide[:600], "the plate clip must hide %s out of shot" % g)
    check("o.isMesh" in hide[:600], "only meshes may go: the chamber lamp must keep lighting the part")
    check("hidden.forEach(function (o) { o.visible = true; })" in run,
          "every mesh the clip hid must come back afterwards")
    check("setViewMode(prev.view)" in run, "the view mode must come back afterwards")
    check("towerCentre(JOB)" in run and "Math.PI - VID_ORBIT / 2" in run,
          "the turn must be centred on the side away from the purge tower")
    check("typ[v] !== 12" in _function("towerCentre"), "the tower is type 12, Wipe tower")


def test_the_shadow_is_not_redrawn_every_frame():
    """27 s of a 28 s frame on the hex lantern was the shadow pass (2026-10-22)."""
    run = _function("vidRun")
    check("i % VID_SHADOW_EVERY === 0 || i === Nb" in run,
          "the shadow must be redrawn on a schedule and once on the finished part")
    check(run.count("renderer.shadowMap.needsUpdate = true") == 1,
          "nothing else in the frame loop may force a shadow redraw")


def test_the_view_comes_back():
    run = _function("vidRun")
    for what in ("setPartOnly(prev.part)", "setMotion(prev.motion)", "setColorMode(prev.color)",
                 "applyPixelRatio()", "vid.on = false"):
        check(what in run, "after the export, vidRestore() must call %s" % what)
    check(run.count("vidRestore()") >= 3, "vidRestore() must run on success, failure and cancel")


def test_the_button_opens_the_export_and_old_browsers_still_record():
    src = _src()
    check("else { openVidDialog(); }" in src, "the video button must open the export")
    check("startTimelapse()" in _function("openVidDialog"),
          "without WebCodecs the live recorder must still be there")
    page = PAGE.read_text(encoding="utf-8")
    for id_ in ("viddialog", "vidprog", "vidgo", "vidsave", "vidshare", "vidcancel"):
        check('id="%s"' % id_ in page, "the page is missing #%s" % id_)


def test_the_muxer_is_vendored_and_the_site_uses_it():
    check((VIEWER / "vendor" / "mp4-muxer.min.js").stat().st_size > 20000, "vendor/mp4-muxer.min.js is missing")
    check("MIT License" in (VIEWER / "vendor" / "mp4-muxer.LICENSE").read_text(), "the muxer's licence must ship with it")
    check((VIEWER / "vendor" / "h264-mp4-encoder.web.js").stat().st_size > 1000000, "vendor/h264-mp4-encoder.web.js is missing")
    check("MIT License" in (VIEWER / "vendor" / "h264-mp4-encoder.LICENSE").read_text(),
          "the H.264 encoder's licence must ship with it")
    sys.path.insert(0, str(VIEWER))
    import build_site
    with tempfile.TemporaryDirectory() as d:
        out = Path(d)
        build_site.build(out)
        html = (out / "index.html").read_text(encoding="utf-8")
        check('<script src="mp4-muxer.min.js"></script>' in html, "the site must load its own copy of the muxer")
        check("cdn.jsdelivr.net/npm/mp4-muxer" not in html, "the site must not need the CDN")
        check('name="h264-encoder" content="h264-mp4-encoder.web.js"' in html,
              "the site must point the H.264 encoder at its own copy")
        check((out / "h264-mp4-encoder.web.js").exists() and (out / "h264-mp4-encoder.LICENSE").exists(),
              "the site must ship the H.264 encoder and its licence")
        check((out / "mp4-muxer.min.js").exists() and (out / "mp4-muxer.LICENSE").exists(),
              "the site must ship the muxer and its licence")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER VIDEO EXPORT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER VIDEO EXPORT TESTS OK — every frame rendered at a social size, always H.264 MP4, "
          "captioned as a simulation, view restored, muxer vendored.")


if __name__ == "__main__":
    run()
