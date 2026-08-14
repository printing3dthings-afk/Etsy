"""
Round 2 of the functional audit of this repo's core Quality Gate functions
(CLAUDE.md's "Quality gate rule" -- "If any gate fails -> listing is
blocked. Fix first. Publish never comes before truth.").

ROUND 1 (tests/test_functional_audit_qc_gate_audit.py) covered listing_qc.
check_listing()'s title/tag/price/section rules and qc_sweep.py's
check_sticker_zip()/check_print_zip()/check_planner_pdf(). It also surfaced
(and deliberately left unfixed, after investigation showed it was original
intentional design) a finding about etsy_api.check_svg_quality()'s file-size
check only firing when combined with bad fill/path counts.

This file's job was to independently re-verify round 1's "already solid
coverage" claim about tests/test_qc_sweep_calendar.py and
tests/test_qc_sweep_coloring.py (read both in full -- confirmed genuinely
thorough: PASS/FAIL/WARN paths, dispatch routing, and even a volume-mount
regression are all covered; no gap found there worth duplicating) and then
look elsewhere on the Quality Gate surface for something genuinely new.

REAL FINDING (CONFIRMED_BUG, distinct from round 1's size-gating question):
etsy_api.check_svg_quality()'s unique-fill-color counter --

    fills = re.findall(r'fill="(#[0-9a-fA-F]{3,6})"', svg_text)

-- only matches the XML *attribute* form `fill="#rrggbb"`. It completely
misses the equally common CSS *style-attribute* form
`style="fill:#rrggbb;..."`, which is the default (or a one-click option) SVG
export style in Illustrator and Inkscape, and is a completely ordinary shape
for any human-authored or externally-sourced SVG entering this pipeline (the
in-house vtracer-based tools/svg_converter.py happens to emit attribute-style
fill="#RRGGBB", so THAT specific source is unaffected -- but the quality gate
is documented as a check on every SVG "in the ZIP" regardless of origin, and
CLAUDE.md's own workflow describes layer SVGs as something a human positions
and works with, not something guaranteed to come only from vtracer).

Net effect: a real traced-raster SVG with 50 (or 500) genuinely distinct
fill colors, expressed via style="fill:#...", is reported as unique_fills=0,
passes_gate=True, problems=[] by check_svg_quality() -- and
validate_digital_file() lets a ZIP containing it through with ZERO errors.
This is a real, silent hole in the exact rule CLAUDE.md documents verbatim:

  "SVG file quality (hard requirement): Every SVG in the ZIP must be a
  clean vector design. Tracked raster images exported as SVG are NOT
  acceptable... Unique fill colors per SVG: <= 20 (clean vectors have 1-4
  discrete fills; traced rasters have 500+)"

Also includes one genuine new-coverage test (not a bug -- a verified-correct
gap-fill) for the round-1-flagged open question: does validate_digital_file()
correctly aggregate errors from ALL bad SVGs in a ZIP, or could one file's
failure get silently dropped if another file in the same ZIP also fails?
Confirmed correct by direct test -- see test_multiple_bad_svgs_all_named_
in_error below.

No application code was modified by this file. Per the task's exception
clause, a strictly-additive fix to the fill-color regex was *possible*
(broadening the pattern to also match `fill\s*:\s*#...` inside a style
attribute) but was deliberately NOT applied here -- this is a read-testing
round, and the fix is left for a human/Scott decision since it changes what
currently-passing packs would gate on.

Run: python tests/test_functional_audit_qc_gate_audit_r2.py
"""
import os
import sys
import tempfile
import zipfile
from pathlib import Path

# ── mandatory safety setup (per task's hard rules) ──────────────────────────
_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_qc_gate_r2_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT, ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

from tools.etsy_api import check_svg_quality, validate_digital_file, FileContentError  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def expect_raises(exc, fn, msg: str) -> None:
    try:
        fn()
        _failures.append(f"expected {exc.__name__} but nothing was raised: {msg}")
    except exc:
        pass
    except Exception as e:  # noqa: BLE001
        _failures.append(f"expected {exc.__name__} but got {type(e).__name__}({e}): {msg}")


def _write_zip(tmp: str, name: str, members: dict[str, bytes]) -> str:
    path = os.path.join(tmp, name)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for member_name, data in members.items():
            zf.writestr(member_name, data)
    return path


def _traced_raster_svg(n_colors: int, *, style_attr: bool) -> bytes:
    """A synthetic traced-raster SVG: n_colors distinct <path> elements, each a
    different fill color, expressed either as the XML `fill="#.."` attribute
    (style_attr=False) or the CSS `style="fill:#..;"` attribute (style_attr=True).
    Same visual content either way -- only the fill-declaration syntax differs."""
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">']
    for i in range(n_colors):
        c = f"#{(i * 4111) % 0xFFFFFF:06x}"
        if style_attr:
            parts.append(f'<path style="fill:{c};stroke:none" d="M{i} {i} h1 v1 h-1 Z"/>')
        else:
            parts.append(f'<path fill="{c}" d="M{i} {i} h1 v1 h-1 Z"/>')
    parts.append("</svg>")
    return "".join(parts).encode()


# ── CONFIRMED BUG: CSS style="fill:#.." fills are invisible to the fill-color
# counter, so check_svg_quality() undercounts traced rasters that use it ──────

def test_control_attribute_style_traced_raster_is_correctly_rejected():
    """Sanity/contrast case: the SAME 50-distinct-color traced raster, using
    the XML fill="#.." attribute form, IS correctly caught today. This proves
    the gap below is specifically about the CSS style="" syntax, not about
    fill-counting being broken in general."""
    svg_text = _traced_raster_svg(50, style_attr=False).decode()
    result = check_svg_quality(svg_text)
    check(result["unique_fills"] == 50, f"expected 50 unique fills counted, got {result}")
    check(result["passes_gate"] is False,
          f"a 50-distinct-fill traced raster using fill=\"#..\" must fail the gate, got {result}")
    check(len(result["problems"]) >= 1, f"expected a problem reported, got {result}")


def test_css_style_fill_traced_raster_undercounts_unique_fills():
    """THE BUG: an identical 50-distinct-color traced raster, using the CSS
    style="fill:#..;" form instead (a completely ordinary Illustrator/Inkscape
    SVG export shape), is reported as having ZERO unique fills. CLAUDE.md's
    SS-Series hard requirement: 'Unique fill colors per SVG: <= 20 (clean
    vectors have 1-4 discrete fills; traced rasters have 500+)'. A file with
    50 real distinct fills is a traced raster by that rule's own numbers, and
    must not be silently reported as having 0."""
    svg_text = _traced_raster_svg(50, style_attr=True).decode()
    result = check_svg_quality(svg_text)
    check(result["unique_fills"] == 50,
          f"BUG: expected 50 unique fills counted (CLAUDE.md's own threshold rule), "
          f"but check_svg_quality()'s fill regex only matches fill=\"#..\" and misses "
          f"style=\"fill:#..\" entirely -- got unique_fills={result['unique_fills']}, "
          f"full result={result}")
    check(result["passes_gate"] is False,
          f"BUG: a 50-distinct-fill traced raster must fail the >20-unique-fills gate "
          f"regardless of whether the fill is declared via the fill=\"\" attribute or a "
          f"style=\"fill:...\" CSS declaration -- got passes_gate=True, problems={result['problems']}")


def test_css_style_fill_traced_raster_silently_clears_the_real_upload_gate():
    """End-to-end version of the bug above, through the actual pre-upload/
    pre-publish gate a real ZIP goes through (validate_digital_file(), called
    by qc_sweep.py's gate() and by the real Etsy upload path). A ZIP
    containing only this traced-raster SVG (50 real distinct colors, encoded
    with style="fill:#..") must be rejected by FileContentError -- instead it
    is accepted with zero errors, which is the actual customer-facing harm:
    a traced-raster masquerading as a vector design would ship to a buyer who
    cannot use the Color Painting Fill tool on it, exactly the failure mode
    check_svg_quality()'s own docstring names."""
    with tempfile.TemporaryDirectory() as tmp:
        zpath = _write_zip(tmp, "bad_pack.zip", {
            "layer01_traced.svg": _traced_raster_svg(50, style_attr=True),
            "README.txt": b"how to print",
        })
        try:
            facts = validate_digital_file(zpath)
            _failures.append(
                "BUG CONFIRMED: validate_digital_file() raised no FileContentError for a ZIP "
                f"containing a 50-distinct-fill traced-raster SVG (style=\"fill:#..\" syntax) -- "
                f"it was accepted with facts={facts}. Per CLAUDE.md's SS-Series hard requirement "
                "('Unique fill colors per SVG: <= 20'), this file should have been rejected."
            )
        except FileContentError:
            pass  # this is the CORRECT behavior -- if this branch is hit, the bug is fixed


def test_css_style_fill_with_500_colors_also_slips_through():
    """Push well past the threshold (500 colors, matching CLAUDE.md's own
    'traced rasters have 500+' description of the failure class this check
    exists to catch) to confirm the gap isn't a narrow near-threshold edge
    case -- it's a total blind spot for the entire style="" fill syntax."""
    svg_text = _traced_raster_svg(500, style_attr=True).decode()
    result = check_svg_quality(svg_text)
    check(result["unique_fills"] == 500,
          f"BUG: a textbook 500-distinct-fill traced raster (CLAUDE.md's own example of the "
          f"defect class) must be counted as such regardless of fill declaration syntax, "
          f"got unique_fills={result['unique_fills']}")
    check(result["passes_gate"] is False,
          f"BUG: 500 distinct fills must fail the gate no matter how they're declared, "
          f"got passes_gate=True, result={result}")


# ── genuine new coverage (not a bug): does validate_digital_file() correctly
# aggregate errors from ALL bad SVGs in a ZIP, or could one drop silently if
# another file also fails? ──────────────────────────────────────────────────

def test_multiple_bad_svgs_all_named_in_error():
    """A ZIP with THREE svgs -- one clean, one bad on fill-count only, one bad
    on path-count only -- must name BOTH bad files in the raised error, not
    just the first one encountered or only one failure class. This was an
    open question from round 1's audit ('could one file's failure be silently
    dropped if another file in the same ZIP also fails?') with zero direct
    test coverage before this file. Confirmed correct: _validate_svgs_in_zip()
    loops over every SVG and collects every file's problems independently."""
    clean_svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        b'<path d="M10 10 H90 V90 H10 Z" fill="#8666AA"/>'
        b'</svg>'
    )
    bad_fills_svg = _traced_raster_svg(50, style_attr=False)  # unique_fills=50 > 20
    bad_paths_parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">']
    for i in range(250):  # > 200 path threshold, single repeated fill so fills stays clean
        bad_paths_parts.append(f'<path fill="#111111" d="M{i} {i} h1 v1 h-1 Z"/>')
    bad_paths_parts.append("</svg>")
    bad_paths_svg = "".join(bad_paths_parts).encode()

    with tempfile.TemporaryDirectory() as tmp:
        zpath = _write_zip(tmp, "mixed_pack.zip", {
            "layer01_clean_WHITE.svg": clean_svg,
            "layer02_bad_fills.svg": bad_fills_svg,
            "layer03_bad_paths.svg": bad_paths_svg,
            "README.txt": b"how to print",
        })
        raised = None
        try:
            validate_digital_file(zpath)
        except FileContentError as e:
            raised = str(e)

    check(raised is not None, "a ZIP with 2 bad SVGs among 3 must raise FileContentError")
    if raised:
        check("layer02_bad_fills.svg" in raised,
              f"the fill-count failure must name layer02_bad_fills.svg specifically, got: {raised}")
        check("layer03_bad_paths.svg" in raised,
              f"the path-count failure must name layer03_bad_paths.svg specifically, got: {raised}")
        check("layer01_clean_WHITE.svg" not in raised,
              f"the clean SVG must not be listed as a problem file, got: {raised}")


def test_single_bad_svg_among_many_clean_ones_still_caught():
    """Not just 'the first SVG encountered' -- a bad SVG that sorts LAST among
    several clean ones must still be caught (guards against an early-return/
    break bug in the aggregation loop)."""
    clean_svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        b'<path d="M10 10 H90 V90 H10 Z" fill="#8666AA"/>'
        b'</svg>'
    )
    bad_svg = _traced_raster_svg(50, style_attr=False)
    with tempfile.TemporaryDirectory() as tmp:
        zpath = _write_zip(tmp, "mostly_clean_pack.zip", {
            "layer01_clean.svg": clean_svg,
            "layer02_clean.svg": clean_svg,
            "layer03_clean.svg": clean_svg,
            "layer99_bad_last.svg": bad_svg,  # sorts last alphabetically/by insertion
        })
        expect_raises(
            FileContentError, lambda: validate_digital_file(zpath),
            "a bad SVG sorted last among clean ones must still fail the gate",
        )


# ── runner ────────────────────────────────────────────────────────────────
def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT R2 TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT R2 TESTS OK.")


if __name__ == "__main__":
    run()
