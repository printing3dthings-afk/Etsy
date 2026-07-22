"""
Tests for the Coloring Pages dynamic new-theme generator (2026-07-22): Scott
explicitly chose to build this now (over deferring it) after learning that
"type a new code, get new coloring-page art" could never work with the
existing 2-fixed-pack system (tools/generate_coloring_pages.py's PACKS only
ever rendered the same 40 hardcoded kawaii/fun_basic prompts, all 13 real
catalog products just repackagings of those same 2 packs).

Covers:
  - generate_dynamic_theme_set() wraps each typed subject in the SAME
    _STYLE/_STYLE_BOLD prompt DNA every hardcoded theme already uses (via
    _fun_theme(), reused not reinvented) -- no real API call (image_gen.
    generate_image is mocked).
  - build_coloring_product.py's --description branch bypasses
    _catalog_lookup() entirely for a genuinely new pid.
  - _catalog_lookup()'s overlay fallback resolves a previously-registered
    dynamic-theme product (so "Regenerate" keeps working after the first
    build registers it), preferring an explicit coloring_pack field over
    filename-prefix inference.

Run: python tests/test_coloring_dynamic_theme.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools",):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import generate_coloring_pages as gcp  # noqa: E402
import build_coloring_product as bcp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_generate_image(prompt, out_path, size=None, output_format=None, engine=None):
    from PIL import Image
    out_path = Path(out_path)
    Image.new("RGB", (64, 64), "white").save(out_path)
    return out_path


def test_dynamic_theme_prompts_include_style_dna_and_subject():
    with patch("tools.image_gen.generate_image", side_effect=_fake_generate_image):
        paths = gcp.generate_dynamic_theme_set(
            "COLOR_TEST_SET", ["A sleepy fox curled under an oak tree"], engine="gemini")
    try:
        check(len(paths) == 1, f"expected 1 generated page, got {paths}")
        prompt_used = gcp._fun_theme("x", "x", "A sleepy fox curled under an oak tree",
                                      gcp._DYNAMIC_BORDER)["prompt"]
        check("A sleepy fox curled under an oak tree" in prompt_used,
              f"the typed subject must appear verbatim in the prompt, got: {prompt_used}")
        check(gcp._STYLE in prompt_used,
              f"a dynamic theme must reuse the SAME style DNA as every hardcoded theme, got: {prompt_used}")
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


def test_dynamic_theme_namespaces_ids_by_product_id():
    with patch("tools.image_gen.generate_image", side_effect=_fake_generate_image):
        paths = gcp.generate_dynamic_theme_set("COLOR_ABC", ["subject one", "subject two"])
    try:
        names = sorted(p.name for p in paths)
        check(names == ["COLOR_ABC_01_coloring.png", "COLOR_ABC_02_coloring.png"],
              f"expected product-id-namespaced filenames, got {names}")
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


def test_dynamic_theme_skips_failed_pages_without_raising():
    def _flaky(prompt, out_path, **kw):
        if "fail" in prompt.lower():
            from tools.image_gen import ImageGenError
            raise ImageGenError("simulated failure")
        return _fake_generate_image(prompt, out_path)

    with patch("tools.image_gen.generate_image", side_effect=_flaky):
        paths = gcp.generate_dynamic_theme_set("COLOR_MIX", ["a good subject", "please FAIL this one"])
    try:
        check(len(paths) == 1, f"a failed page must be skipped, not raise or block the others, got {paths}")
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


def test_build_coloring_product_description_branch_bypasses_catalog_lookup():
    called = {"n": 0}

    def _fail_if_called(pid):
        called["n"] += 1
        return None

    with patch.object(bcp, "_catalog_lookup", side_effect=_fail_if_called), \
         patch.object(gcp, "generate_dynamic_theme_set", return_value=[Path("/tmp/fake1.png")]), \
         patch.object(gcp, "build_sets", return_value=[Path("/tmp/coloring_color_new_set_01.zip")]), \
         patch("sys.argv", ["build_coloring_product.py", "COLOR_NEW", "--description", "a fox\na balloon"]), \
         patch("qc_sweep.sweep", return_value=[]), \
         patch("backup_digital_products.run"):
        bcp.main()
    check(called["n"] == 0, "the --description branch must never call _catalog_lookup()")


def test_build_coloring_product_description_caps_at_pages_per_set():
    captured = {}

    def _capture(pid, subjects, engine=None):
        captured["subjects"] = subjects
        return []

    many_subjects = "\n".join(f"subject {i}" for i in range(10))
    with patch.object(gcp, "generate_dynamic_theme_set", side_effect=_capture), \
         patch("sys.argv", ["build_coloring_product.py", "COLOR_MANY", "--description", many_subjects]), \
         patch("qc_sweep.sweep", return_value=[]), \
         patch("backup_digital_products.run"):
        bcp.main()
    check(len(captured.get("subjects", [])) == gcp.PAGES_PER_SET,
          f"subjects must be capped at PAGES_PER_SET ({gcp.PAGES_PER_SET}), got {len(captured.get('subjects', []))}")


def test_catalog_lookup_overlay_fallback_prefers_explicit_pack():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["HUB_FILES_DIR"] = tmp
        try:
            overrides = {"COLOR_REGEN_TEST": {
                "is_new_product": True, "category": "coloring_pages",
                "files": ["data/digital_products/coloring_pages/sets/coloring_color_regen_test_set_01.zip"],
            }}
            (Path(tmp) / "product_catalog_overrides.json").write_text(json.dumps(overrides))
            result = bcp._catalog_lookup("COLOR_REGEN_TEST")
        finally:
            del os.environ["HUB_FILES_DIR"]
    check(result is not None, "a registered dynamic-theme product must resolve via the overlay fallback")
    pack, stems = result
    check(pack == "color_regen_test", f"expected the explicit coloring_pack (product_id.lower()), got {pack!r}")
    check(stems == ["coloring_color_regen_test_set_01"], f"got {stems}")


def test_catalog_lookup_returns_none_for_overlay_entry_missing_files():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["HUB_FILES_DIR"] = tmp
        try:
            overrides = {"COLOR_EMPTY": {"is_new_product": True, "category": "coloring_pages", "files": []}}
            (Path(tmp) / "product_catalog_overrides.json").write_text(json.dumps(overrides))
            result = bcp._catalog_lookup("COLOR_EMPTY")
        finally:
            del os.environ["HUB_FILES_DIR"]
    check(result is None, f"an overlay entry with no files must not resolve, got {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLORING DYNAMIC THEME TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLORING DYNAMIC THEME TESTS OK — new-theme prompt construction reuses the "
          "existing style DNA, --description bypasses catalog lookup and caps at "
          "PAGES_PER_SET, and the overlay fallback in _catalog_lookup() resolves a "
          "previously-registered dynamic product correctly.")


if __name__ == "__main__":
    run()
