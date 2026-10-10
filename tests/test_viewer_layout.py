"""The viewer's layout, reorganised 2026-10-10.

Scott: "There is too much scrolling. I need it to be easier to navigate
around." Measured before the change, with the Phone Stand loaded:

- 1440x900: the left rail held 1,731px of content in 757px, the right 2,327px;
- 1280x720: the live readout, the AMS and every colour mode sat below the plate
  list, invisible until you scrolled the rail;
- 390x844 (a phone): the page was 11,755px tall, the plate list alone 8,493px;
- every size: the page scrolled 16px, from the body's default margin.

Each test below pins one part of the fix so the next feature cannot quietly
put it back. The tab logic is run for real under node against a small fake
DOM.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "tools" / "viewer"
HTML = (VIEWER / "virtual_p1s.html").read_text(encoding="utf-8")
APP = (VIEWER / "app.js").read_text(encoding="utf-8")

_failures: list[str] = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _between(src, start, end):
    i = src.index(start)
    return src[i:src.index(end, i)]


def _function(name):
    m = re.search(r"^function %s\(.*?^\}$" % re.escape(name), APP, re.S | re.M)
    if not m:
        raise AssertionError("function %s not found in app.js" % name)
    return m.group(0)


def test_the_live_readout_is_on_the_print_not_in_a_rail():
    stage = _between(HTML, '<div id="stage">', '<aside id="right">')
    left = _between(HTML, '<aside id="left">', '<div id="stage">')
    for rid in ("r-layer", "r-rem", "r-spd", "r-feat"):
        check('id="%s"' % rid in stage,
              "%s must sit on the stage, where it cannot scroll away" % rid)
        check('id="%s"' % rid not in left, "%s is back in the left rail" % rid)


def test_the_camera_controls_are_on_the_print():
    stage = _between(HTML, '<div id="stage">', '<aside id="right">')
    for v in ("iso", "front", "top"):
        check('data-view="%s"' % v in stage, "camera view %s is not on the stage" % v)
    check('id="partview"' in stage and 'id="fullscreen"' in stage,
          "Part only and Full screen belong with the camera views on the stage")
    check("viewmenu" not in HTML,
          "the footer's View options pop-up is back -- one more thing to open and close")


def test_every_tab_has_its_pane():
    for name in re.findall(r'data-rail="([a-z]+)"', HTML):
        check('id="rail-%s"' % name in HTML, "left tab %s has no pane" % name)
    for name in re.findall(r'data-pane="([a-z]+)"', HTML):
        check('id="pane-%s"' % name in HTML, "right tab %s has no pane" % name)
    m = re.findall(r'<button role="tab" data-m="([a-z]+)"', HTML)
    check(m == ["plates", "print", "display", "info"],
          "the phone tab bar should be Plates, Print, Display, Info, got %r" % m)
    for name in m:
        check(name == "info" or 'data-rail="%s"' % name in HTML,
              "phone tab %s opens nothing" % name)


def test_nothing_was_lost_in_the_move():
    # Every control that existed before the reorganisation still exists, once.
    for cid in ("platefilter", "platesort", "platefilters", "jobs", "platemore",
                "jobnote", "seamnote", "jobsource", "featnote", "amsslots", "amsnote",
                "modeswap", "realpanel", "realswatch", "speedpanel", "legend",
                "door", "viewmode", "ghost", "seams", "motion", "quality",
                "partview", "fullscreen", "play", "restart", "timelapse", "scrub",
                "prevlayer", "nextlayer", "layerjump", "speeds"):
        n = HTML.count('id="%s"' % cid)
        check(n == 1, "#%s appears %d times, expected exactly once" % (cid, n))


def test_the_page_itself_never_scrolls():
    check(re.search(r"body\{margin:0\}", HTML) is not None,
          "the body's default 8px margin made every size scroll 16px")
    narrow = HTML[HTML.rindex("@media (max-width:1180px){"):]
    check("height:100dvh" in narrow,
          "on a phone the app must be exactly one screen tall")
    check('grid-template-areas:"h" "s" "f" "t" "p"' in narrow,
          "on a phone: header, print, transport, tabs, one panel")
    check("#left,#right{grid-area:p" in narrow,
          "both rails share the one panel slot on a phone instead of stacking")
    check("position:sticky;bottom:0" not in narrow,
          "a sticky footer means the page scrolls again")


def test_a_hidden_tab_is_really_hidden():
    # #rail-plates sets its own display (flex on a desktop, block on a phone),
    # and an id selector outranks .rpane[hidden]. Found in a phone screenshot:
    # the Display tab opened with the whole plate list still drawn over it.
    check(".rpane[hidden]{display:none!important}" in HTML,
          "a pane with its own display rule ignores the hidden attribute")


def test_the_plate_list_fills_its_tab():
    check(re.search(r"#rail-plates #jobs\{flex:1;min-height:0;max-height:none\}", HTML)
          is not None, "the plate list should take the whole Plates tab, not a capped box")


_HARNESS = """
function mk(attrs) {
  return {attrs: attrs, hidden: false,
    getAttribute: function (k) { return k in this.attrs ? this.attrs[k] : null; },
    setAttribute: function (k, v) { this.attrs[k] = String(v); }};
}
var app = mk({'data-m': 'plates', 'data-sheet': 'open'});
var rails = ['plates', 'print', 'display'].map(function (n) { return mk({'data-rail': n}); });
var panes = {};
rails.forEach(function (r) { panes['rail-' + r.attrs['data-rail']] = mk({}); });
var mtabs = ['plates', 'print', 'display', 'info'].map(function (n) { return mk({'data-m': n}); });
var document = {
  getElementById: function (id) { return id === 'app' ? app : panes[id]; },
  querySelectorAll: function (q) { return q === '[data-rail]' ? rails : mtabs; }
};
function $(id) { return document.getElementById(id); }
var renderer = null, resized = 0;
function onResize() { resized++; }
%s
%s
%s
function state() {
  return {m: app.attrs['data-m'], sheet: app.attrs['data-sheet'],
    shown: rails.filter(function (r) { return !panes['rail-' + r.attrs['data-rail']].hidden; })
                .map(function (r) { return r.attrs['data-rail']; }),
    sel: mtabs.filter(function (b) { return b.attrs['aria-selected'] === 'true'; })
              .map(function (b) { return b.attrs['data-m']; })};
}
var out = [];
showPanel('display'); out.push(state());
showPanel('display'); out.push(state());      // same tab again: fold it away
showPanel('info'); out.push(state());
showRail('print'); out.push(state());         // a desktop tab click while Info is up
showPanel('plates'); out.push(state());
showPanel('plates', true); out.push(state()); // a shortcut never folds it
console.log(JSON.stringify(out));
"""


def test_one_panel_at_a_time_and_a_second_tap_folds_it():
    node = shutil.which("node")
    if not node:
        print("  (skipped: no node on PATH)")
        return
    js = _HARNESS % (_function("showRail"), _function("showPanel"), _function("paintPanelTabs"))
    r = subprocess.run([node, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    s = json.loads(r.stdout.strip().splitlines()[-1])
    check(s[0] == {"m": "display", "sheet": "open", "shown": ["display"], "sel": ["display"]},
          "opening Display should show only Display, got %r" % s[0])
    check(s[1]["sheet"] == "closed" and s[1]["sel"] == [],
          "tapping the open tab again should fold the panel, got %r" % s[1])
    check(s[2]["m"] == "info" and s[2]["sheet"] == "open" and s[2]["sel"] == ["info"],
          "Info should open the right rail's panel, got %r" % s[2])
    check(s[3]["m"] == "info" and s[3]["shown"] == ["print"],
          "a left-tab change while Info is up must not steal the phone panel, got %r" % s[3])
    check(s[4]["m"] == "plates" and s[4]["shown"] == ["plates"] and s[4]["sel"] == ["plates"],
          "got %r" % s[4])
    check(s[5]["sheet"] == "open", "the / shortcut must land on the plate list, not fold it")


def test_the_readout_fold_survives_storage_being_unavailable():
    fn = _function("hudFoldedAtStart")
    check("try {" in fn and "catch (e)" in fn,
          "reading the fold preference must not throw in a private window")
    check("matchMedia('(max-width:1180px)')" in fn,
          "with nothing remembered, a phone starts folded")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("VIEWER LAYOUT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("VIEWER LAYOUT TESTS OK — the readout and camera live on the print, each rail "
          "is tabs, and a phone is one screen with one panel at a time.")


if __name__ == "__main__":
    run()
