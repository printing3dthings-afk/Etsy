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
import zipfile
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


def _fake_generate_image(prompt, out_path, size=None, output_format=None, quality=None, engine=None):
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


def test_coloring_pages_generate_at_medium_quality_not_high():
    """2026-08-10 cost audit: generate_image()'s own default is quality="high"
    ($0.167/image on gpt-image-1/2 at our SQUARE size, confirmed against
    OpenAI's pricing docs) -- wasted spend for a coloring page, which is pure
    thick black-line-on-white with no gradients or fine detail to lose.
    _gen_image_openai() must explicitly request "medium" ($0.042/image, ~4x
    cheaper) rather than silently inheriting the expensive default."""
    captured = {}

    def _capture_quality(prompt, out_path, size=None, output_format=None, quality=None, engine=None):
        captured["quality"] = quality
        return _fake_generate_image(prompt, out_path, size, output_format, quality, engine)

    with patch("tools.image_gen.generate_image", side_effect=_capture_quality):
        paths = gcp.generate_dynamic_theme_set(
            "COLOR_QUALITY_TEST", ["A curious owl on a branch"], engine="openai")
    try:
        check(len(paths) == 1, f"expected 1 generated page, got {paths}")
        check(captured.get("quality") == "medium",
              f"coloring pages must request quality='medium', got {captured.get('quality')!r}")
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


def test_new_theme_set_size_is_30():
    """Regression guard for Scott's explicit request (2026-08-08): 'I need for
    the coloring pages to be made in groups of 30.' Every downstream reader
    (_resolve_coloring_subjects()/build_coloring_product.py) derives its count
    from this ONE constant, so this is the single real assertion needed."""
    check(gcp.NEW_THEME_SET_SIZE == 30, f"expected 30, got {gcp.NEW_THEME_SET_SIZE}")


def test_dynamic_theme_difficulty_selects_correct_style_uniformly():
    """Scott (2026-08-08): 'make sure the kids coloring pages are separate
    from the adult due to the adult being more detailed.' One `difficulty`
    value must select ONE style wrapper for every subject in the batch --
    never a mix of kids-simple and adult-intricate pages in the same group."""
    captured_prompts = {}

    def _record(prompt, out_path, size=None, output_format=None, quality=None, engine=None):
        captured_prompts.setdefault("prompts", []).append(prompt)
        return _fake_generate_image(prompt, out_path)

    subjects = ["a sleepy fox", "a hot air balloon", "a birthday cake"]
    for difficulty, expected_style in (
        ("kids", gcp._STYLE_KIDS),
        ("adult", gcp._STYLE_ADULT),
        ("standard", gcp._STYLE),
    ):
        captured_prompts.clear()
        # Force the single-shot, no-QA path (see generate_coloring_page()'s own
        # docstring) so exactly one generate call happens per subject --
        # otherwise a real (if exhausted/rate-limited) GEMINI_API_KEY in the
        # environment makes the vision-QA retry loop call _generate() a second
        # time on a failed verification, which is real, correct production
        # behavior but makes "N subjects -> N prompts recorded" nondeterministic
        # and not what this test is actually checking (style-tier selection).
        with patch("tools.image_gen.generate_image", side_effect=_record), \
             patch("tools.image_gen.gemini_key_available", return_value=False):
            paths = gcp.generate_dynamic_theme_set(
                f"COLOR_DIFF_{difficulty.upper()}", subjects, difficulty=difficulty)
        try:
            check(len(paths) == len(subjects), f"[{difficulty}] expected {len(subjects)} pages, got {paths}")
            prompts = captured_prompts.get("prompts", [])
            check(len(prompts) == len(subjects), f"[{difficulty}] expected {len(subjects)} prompts recorded")
            for p in prompts:
                check(expected_style in p,
                      f"[{difficulty}] every page in the batch must use the SAME style tier, "
                      f"expected {expected_style[:40]!r} in prompt, got: {p[:200]}")
            # Cross-check: a kids/adult prompt must NOT also contain the other
            # tiers' style text -- proves this isn't accidentally reusing the
            # generic _fun_theme() wrapper under a different difficulty label.
            if difficulty != "standard":
                for p in prompts:
                    check(gcp._STYLE not in p or expected_style == gcp._STYLE,
                          f"[{difficulty}] must not fall back to the standard _fun_theme style DNA")
        finally:
            for p in paths:
                p.unlink(missing_ok=True)


def test_dynamic_theme_unrecognized_difficulty_falls_back_to_standard():
    with patch("tools.image_gen.generate_image", side_effect=_fake_generate_image):
        paths = gcp.generate_dynamic_theme_set(
            "COLOR_BADDIFF", ["a garden gnome"], difficulty="expert-level-nonsense")
    try:
        check(len(paths) == 1, f"expected 1 page even with a bogus difficulty value, got {paths}")
    finally:
        for p in paths:
            p.unlink(missing_ok=True)


def test_build_coloring_product_threads_difficulty_through():
    captured = {}

    def _capture_difficulty(pid, subjects, engine=None, difficulty=None):
        captured["difficulty"] = difficulty
        return []

    with patch.object(gcp, "generate_dynamic_theme_set", side_effect=_capture_difficulty), \
         patch("sys.argv", ["build_coloring_product.py", "COLOR_KIDS_TEST", "--description", "a puppy",
                             "--difficulty", "kids"]), \
         patch("qc_sweep.sweep", return_value=[]), \
         patch("backup_digital_products.run"):
        bcp.main()
    check(captured.get("difficulty") == "kids",
          f"--difficulty must reach generate_dynamic_theme_set() unchanged, got {captured}")


def test_build_coloring_product_difficulty_defaults_to_standard():
    captured = {}

    def _capture_difficulty(pid, subjects, engine=None, difficulty=None):
        captured["difficulty"] = difficulty
        return []

    with patch.object(gcp, "generate_dynamic_theme_set", side_effect=_capture_difficulty), \
         patch("sys.argv", ["build_coloring_product.py", "COLOR_NODIFF_TEST", "--description", "a puppy"]), \
         patch("qc_sweep.sweep", return_value=[]), \
         patch("backup_digital_products.run"):
        bcp.main()
    check(captured.get("difficulty") == "standard",
          f"omitting --difficulty must default to 'standard' (pre-existing behavior unchanged), got {captured}")


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


def test_build_coloring_product_description_caps_at_new_theme_set_size():
    captured = {}

    def _capture(pid, subjects, engine=None, difficulty=None):
        captured["subjects"] = subjects
        captured["difficulty"] = difficulty
        return []

    # Must exceed NEW_THEME_SET_SIZE regardless of its current value, or the
    # cap never actually triggers and this test silently stops testing anything
    # (confirmed real: this used a hardcoded range(25) before NEW_THEME_SET_SIZE
    # was bumped 20->30 on 2026-08-08, which would have made 25 < 30 and let an
    # uncapped list slip through as a false pass).
    many_subjects = "\n".join(f"subject {i}" for i in range(gcp.NEW_THEME_SET_SIZE + 10))
    with patch.object(gcp, "generate_dynamic_theme_set", side_effect=_capture), \
         patch("sys.argv", ["build_coloring_product.py", "COLOR_MANY", "--description", many_subjects]), \
         patch("qc_sweep.sweep", return_value=[]), \
         patch("backup_digital_products.run"):
        bcp.main()
    check(len(captured.get("subjects", [])) == gcp.NEW_THEME_SET_SIZE,
          f"subjects must be capped at NEW_THEME_SET_SIZE ({gcp.NEW_THEME_SET_SIZE}), "
          f"got {len(captured.get('subjects', []))}")


def test_build_sets_new_theme_batch_size_produces_one_zip():
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        for i in range(gcp.NEW_THEME_SET_SIZE):
            p = Path(tmp) / f"page_{i:02d}.png"
            p.write_bytes(b"fake png bytes")
            pages.append(p)
        orig_sets_dir = gcp.SETS_DIR
        gcp.SETS_DIR = Path(tmp) / "sets"
        try:
            zip_paths = gcp.build_sets(pages, pack="colornew", batch_size=gcp.NEW_THEME_SET_SIZE)
        finally:
            gcp.SETS_DIR = orig_sets_dir
    check(len(zip_paths) == 1, f"20 pages with batch_size=20 must produce exactly 1 ZIP, got {len(zip_paths)}")
    check(zip_paths[0].name == "coloring_colornew_set_01.zip", f"got {zip_paths[0].name}")


def test_build_sets_default_batch_size_unchanged_for_old_packs():
    """Regression guard: the 2 old fixed packs (kawaii/fun_basic) must keep
    batching at PAGES_PER_SET (5) when build_sets() is called with no
    batch_size arg (exactly how their own rebuild path calls it) -- proves
    this whole 20-page feature never touched their behavior."""
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        for i in range(20):
            p = Path(tmp) / f"page_{i:02d}.png"
            p.write_bytes(b"fake png bytes")
            pages.append(p)
        orig_sets_dir = gcp.SETS_DIR
        gcp.SETS_DIR = Path(tmp) / "sets"
        try:
            zip_paths = gcp.build_sets(pages, pack="kawaii")
        finally:
            gcp.SETS_DIR = orig_sets_dir
    check(len(zip_paths) == 4, f"20 pages with no batch_size arg must still produce 4 ZIPs of 5, got {len(zip_paths)}")


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


# ── Bundle merge (2026-08-10, cost-effective-scale request) ─────────────────
# Combines several EXISTING coloring-pages products' real ZIPs into one new
# bundle ZIP with zero new AI spend. Pure file work -- no image_gen mock
# needed, just real (fake-content) ZIPs on disk.

def _write_fake_source_zip(sets_dir: Path, pid: str, n_pages: int) -> None:
    sets_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(sets_dir / f"coloring_{pid.lower()}_set_01.zip", "w") as zf:
        for i in range(n_pages):
            zf.writestr(f"{pid}_{i:02d}_coloring.png", b"fake png bytes")


def test_merge_existing_sets_combines_real_pages_with_no_name_collisions():
    with tempfile.TemporaryDirectory() as tmp:
        sets_dir = Path(tmp) / "sets"
        _write_fake_source_zip(sets_dir, "COLOR1004", 30)
        _write_fake_source_zip(sets_dir, "COLOR1005", 30)
        orig_sets_dir = gcp.SETS_DIR
        gcp.SETS_DIR = sets_dir
        try:
            result = gcp.merge_existing_sets_into_bundle(["COLOR1004", "COLOR1005"], "COLOR_MEGA_TEST")
        finally:
            gcp.SETS_DIR = orig_sets_dir
        check(result["total_pages"] == 60, f"expected 60 combined pages, got {result['total_pages']}")
        check(result["missing"] == [], f"expected no missing sources, got {result['missing']}")
        check(result["zip_path"].exists(), "the combined ZIP must actually be written to disk")
        with zipfile.ZipFile(result["zip_path"], "r") as zf:
            names = zf.namelist()
            check(len(names) == 60, f"expected 60 members in the combined ZIP, got {len(names)}")
            check(len(set(names)) == 60, "member names must all be unique (no source collision)")
            check(all(n.startswith("COLOR1004_") or n.startswith("COLOR1005_") for n in names),
                  "every member must be prefixed with its real source pid")
        manifest_path = result["zip_path"].with_suffix(".manifest.json")
        check(manifest_path.exists(), "a manifest sidecar must be written so QC knows the real page count")
        manifest = json.loads(manifest_path.read_text())
        check(manifest["total_pages"] == 60, f"got {manifest}")
        check(manifest["bundle_pid"] == "COLOR_MEGA_TEST", f"got {manifest}")


def test_merge_existing_sets_all_missing_leaves_no_manifest_either():
    with tempfile.TemporaryDirectory() as tmp:
        sets_dir = Path(tmp) / "sets"
        orig_sets_dir = gcp.SETS_DIR
        gcp.SETS_DIR = sets_dir
        try:
            result = gcp.merge_existing_sets_into_bundle(["COLOR_GHOST_C", "COLOR_GHOST_D"], "COLOR_MEGA_EMPTY2")
        finally:
            gcp.SETS_DIR = orig_sets_dir
        check(not result["zip_path"].with_suffix(".manifest.json").exists(),
              "no manifest should be left behind when nothing was merged")


def test_merge_existing_sets_reports_missing_source_without_dropping_silently():
    """A source pid whose ZIP isn't reachable (e.g. an old pre-volume-fix
    product whose files were never migrated) must be reported in `missing`,
    not just silently excluded -- see merge_existing_sets_into_bundle()'s
    docstring."""
    with tempfile.TemporaryDirectory() as tmp:
        sets_dir = Path(tmp) / "sets"
        _write_fake_source_zip(sets_dir, "COLOR1004", 30)
        orig_sets_dir = gcp.SETS_DIR
        gcp.SETS_DIR = sets_dir
        try:
            result = gcp.merge_existing_sets_into_bundle(
                ["COLOR1004", "COLOR_KAWAII_COLORING_PAGES_SET_01"], "COLOR_MEGA_TEST2")
        finally:
            gcp.SETS_DIR = orig_sets_dir
    check(result["total_pages"] == 30, f"only the reachable source's pages should be counted, got {result}")
    check(result["missing"] == ["COLOR_KAWAII_COLORING_PAGES_SET_01"], f"got {result['missing']}")
    check(len(result["included"]) == 1, f"got {result['included']}")


def test_merge_existing_sets_all_sources_missing_writes_no_zip():
    with tempfile.TemporaryDirectory() as tmp:
        sets_dir = Path(tmp) / "sets"
        orig_sets_dir = gcp.SETS_DIR
        gcp.SETS_DIR = sets_dir
        try:
            result = gcp.merge_existing_sets_into_bundle(["COLOR_GHOST_A", "COLOR_GHOST_B"], "COLOR_MEGA_EMPTY")
        finally:
            gcp.SETS_DIR = orig_sets_dir
        check(result["total_pages"] == 0, f"got {result}")
        check(sorted(result["missing"]) == ["COLOR_GHOST_A", "COLOR_GHOST_B"], f"got {result['missing']}")
        check(not result["zip_path"].exists(), "no ZIP file should be left behind when nothing was merged")


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
          "NEW_THEME_SET_SIZE, build_sets() batches 20 pages into 1 ZIP for the new-theme "
          "path while old packs still batch at 5, and the overlay fallback in "
          "_catalog_lookup() resolves a previously-registered dynamic product correctly.")


if __name__ == "__main__":
    run()
