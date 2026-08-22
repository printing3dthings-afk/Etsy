"""
Functional audit ROUND 2 -- _create_digital_planner (tools/art_creation_tools.py).

Round 1 (tests/test_functional_audit_digital_planner.py) found and fixed a
page-count-credit bug in the tier-3 sticker-picker call site. This round
looks at a DIFFERENT surface: the `weekly_layout` parameter.

CLAUDE.md's "Digital Planner Excellence Standards" section explicitly
requires:

    "Multiple Weekly Layout Options: Include 2 weekly layout variations
    (buyers hate having only one choice) -- Option A: Horizontal
    time-blocked ... Option B: Vertical column layout ... Let buyers choose
    by hyperlink from a 'Choose Your Layout' page."

`_create_digital_planner`'s own AGENT_TOOLS schema (art_creation_tools.py,
~line 793-814) advertises exactly this as a real, selectable parameter:

    "weekly_layout": {
        "type": "string",
        "enum": ["horizontal", "vertical", "lined", "hourly"],
        "description": "... horizontal=days stacked ..., vertical=7 day
        columns across the page, lined=simple lined layout by day,
        hourly=time-slot schedule per day. Default: horizontal.",
    }

So any caller (Claude via chat tool call, or a script) can reasonably
believe passing weekly_layout="vertical" (or "lined"/"hourly") produces a
genuinely different weekly page. It does not.

CONFIRMED BUG: inside the function body, `weekly_layout` is read into a
local variable (art_creation_tools.py line 2324:
`weekly_layout = data.get("weekly_layout", "horizontal")`) and then NEVER
referenced again anywhere else in the ~2900-line function. `draw_weekly_page()`
(line 3549) has exactly one hardcoded rendering path -- it branches only on
`_design` (the planner tier, 1 vs 2/3, for sidebar-or-not) and on `undated`,
never on `weekly_layout`. Passing "vertical", "lined", or "hourly" silently
produces the exact same output as "horizontal" -- no error, no warning, and
critically no difference in the generated PDF at all. This test proves that
by generating two planners identical in every field except `weekly_layout`
and showing the rendered weekly pages are byte-for-byte visually identical
(pixmap hash) and textually identical.

This matters under this repo's own mission statement ("best and most
accurate transaction") and the CLAUDE.md roadmap item it silently fails to
implement: a listing or agent that advertises "Choose Your Layout" / 2
weekly layout options on the strength of this tool's own schema would be
making a claim the code cannot back up.

Safety:
  - DataStore is never touched -- a minimal in-memory FakeStore duck-types
    the three methods (`get`/`set`/`save`) the function actually calls.
  - `art_creation_tools.PRODUCT_FILES_DIR` is monkeypatched to a
    tempfile.TemporaryDirectory() for the duration of every test and
    restored in `finally`.
  - No network, no Etsy/Anthropic/OpenAI calls are reachable from this code
    path (pure local reportlab/PyMuPDF rendering) -- nothing else to mock.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_r2_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402  (imported per harness convention; not used directly below)
import tools.art_creation_tools as act  # noqa: E402

import fitz  # PyMuPDF -- local rendering verification only, no network  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


class FakeStore:
    """Duck-types the exact 3 DataStore methods _create_digital_planner uses,
    entirely in memory. Never touches config.SHOP_DATA_FILE / the real
    DataStore singleton."""

    def __init__(self, products=None):
        self._data = {"digital_products": products or []}

    def get(self, *keys, default=None):
        d = self._data
        for k in keys:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                return default
        return d

    def set(self, value, *keys):
        assert keys == ("digital_products",)
        self._data["digital_products"] = value

    def save(self):
        pass  # no-op -- never write to disk


def _make_product(pid):
    return {"id": pid, "status": "concept"}


def _run_planner(data, pid):
    """Runs _create_digital_planner with PRODUCT_FILES_DIR redirected to a
    fresh tempdir. Returns (result_dict, tmpdir_obj)."""
    store = FakeStore([_make_product(pid)])
    tmpdir = tempfile.TemporaryDirectory(prefix="frank_planner_audit_r2_")
    try:
        with patch.object(act, "PRODUCT_FILES_DIR", tmpdir.name):
            data = dict(data, product_id=pid)
            raw = act._create_digital_planner(data, store)
        import json
        result = json.loads(raw)
        return result, tmpdir
    except Exception:
        tmpdir.cleanup()
        raise


def _weekly_page_index(doc):
    """Find the first page whose text contains 'WEEK 01' (the first weekly
    page, right after the 5 intro pages + 1 yearly-overview page)."""
    for i, page in enumerate(doc):
        if "WEEK 01" in page.get_text():
            return i
    return None


def _page_pixmap_hash(doc, page_idx):
    pix = doc[page_idx].get_pixmap(dpi=72)
    return hashlib.sha256(pix.tobytes("ppm")).hexdigest()


# ── Test: schema-advertised weekly_layout values ("vertical", "lined",
#          "hourly") are all confirmed silently no-ops -- output is IDENTICAL
#          to "horizontal" for every one of them ──────────────────────────
def test_weekly_layout_parameter_has_zero_effect_on_output():
    base = {
        "planner_title": "Audit Weekly Layout Planner",
        "planner_tier": 1,
        "interactive": False,
        "color_scheme": "sage_cream",
        "year": 0,  # undated -- avoids any date-based text drift between runs
        "include_sections": ["weekly"],
        "calendar_integration": "none",
    }

    # Baseline: explicit "horizontal" (also the documented default)
    data_horizontal = dict(base, weekly_layout="horizontal")
    result_h, tmp_h = _run_planner(data_horizontal, pid="DPTESTWLH")
    try:
        check(result_h.get("success") is True, f"expected success, got {result_h}")
        doc_h = fitz.open(result_h["file_path"])
        idx_h = _weekly_page_index(doc_h)
        check(idx_h is not None, "could not locate 'WEEK 01' page in horizontal-layout planner")
        text_h = doc_h[idx_h].get_text()
        hash_h = _page_pixmap_hash(doc_h, idx_h)
        full_text_h = "\n".join(pg.get_text() for pg in doc_h)
        pages_h = doc_h.page_count
        doc_h.close()

        for variant in ("vertical", "lined", "hourly"):
            data_variant = dict(base, weekly_layout=variant)
            result_v, tmp_v = _run_planner(data_variant, pid=f"DPTESTWL_{variant.upper()}")
            try:
                check(result_v.get("success") is True,
                      f"expected success for weekly_layout={variant!r}, got {result_v}")
                doc_v = fitz.open(result_v["file_path"])
                idx_v = _weekly_page_index(doc_v)
                check(idx_v is not None,
                      f"could not locate 'WEEK 01' page in weekly_layout={variant!r} planner")

                check(doc_v.page_count == pages_h,
                      f"weekly_layout={variant!r} produced a DIFFERENT page count "
                      f"({doc_v.page_count}) than horizontal ({pages_h}) -- if this "
                      f"ever starts failing it means the layout switch was actually "
                      f"implemented and this test's premise is stale")

                text_v = doc_v[idx_v].get_text()
                hash_v = _page_pixmap_hash(doc_v, idx_v)
                full_text_v = "\n".join(pg.get_text() for pg in doc_v)
                doc_v.close()

                # CONFIRMED BUG: the schema promises 4 distinct layouts
                # (horizontal/vertical/lined/hourly) but the weekly-page
                # renderer never reads `weekly_layout` at all -- every
                # variant renders pixel-identical, text-identical output.
                check(text_v == text_h,
                      f"weekly_layout={variant!r}: expected the extracted text of the "
                      f"first weekly page to be IDENTICAL to horizontal (proving the "
                      f"parameter is a no-op) but it differs -- if this fails, "
                      f"weekly_layout may have been wired up; re-derive this test's "
                      f"premise before treating it as a regression")
                check(hash_v == hash_h,
                      f"weekly_layout={variant!r}: expected the rendered pixmap of the "
                      f"first weekly page to be byte-identical to horizontal (proving "
                      f"the parameter is a no-op) but it differs")
                check(full_text_v == full_text_h,
                      f"weekly_layout={variant!r}: expected the ENTIRE document's "
                      f"extracted text to be identical to horizontal but it differs")
            finally:
                tmp_v.cleanup()
    finally:
        tmp_h.cleanup()


def run():
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
    print("FUNCTIONAL AUDIT R2 TESTS OK -- confirms weekly_layout is a schema-advertised "
          "no-op: 'vertical', 'lined', and 'hourly' all render byte-identical output to "
          "'horizontal', so the 2-weekly-layout-options feature CLAUDE.md documents does "
          "not actually exist in _create_digital_planner.")


if __name__ == "__main__":
    run()
