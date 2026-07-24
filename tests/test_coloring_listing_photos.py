"""
Tests for staging real coloring-pack pages as Etsy listing photos (2026-07-25).

COLOR1003 published successfully (after the file-resolution fix) but ended
up with zero listing photos -- coloring_pages has no AI listing-photo
pipeline like digital_planner's. Scott's direct instruction was to use the
product's own real pack pages as the photos, not build a lifestyle-photo
pipeline. Real wrinkle found while building this: the existing pale-
background quality gate (meant to catch lazy/blank AI renders) would reject
a raw coloring page's near-white corners as "washed out" -- Scott chose to
make that gate category-aware (skip it for coloring_pages, since white paper
is the honest, real look of this product) rather than build a flat-lay
compositing pipeline.

Covers:
  - _extract_coloring_page_images(): root-level-PNG filtering, evenly-spaced
    sampling when a pack has more than 10 pages, returns everything when <=10
  - _check_no_pale_background(): category="coloring_pages" bypasses the
    check even for a genuinely near-white image; the default (no category)
    behavior is unchanged -- a real regression guard against accidentally
    weakening the gate for every other product type
  - _produce_coloring_pages_listing_photos(): staging success path, no-
    listing_id error, no-ZIP error, category mismatch error
  - _produce_listing_photos()'s category dispatch to the coloring_pages path
  - _validate_staged_action's listing_photo branch: a near-white photo
    passes when payload["category"] == "coloring_pages", fails otherwise

Run: python tests/test_coloring_listing_photos.py
"""
import asyncio
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_coloring_photos_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "coloring-photos-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_white_png_bytes(size=(400, 500)) -> bytes:
    from PIL import Image as PILImage
    im = PILImage.new("RGB", size, (255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _make_coloring_zip(n_pages: int) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(1, n_pages + 1):
            zf.writestr(f"page_{i:02d}.png", _make_white_png_bytes())
        # A nested/non-page file must never be counted as a page.
        zf.writestr("thumbnails/preview.png", _make_white_png_bytes())
        zf.writestr("README.txt", b"not a page")
    return buf.getvalue()


# ── _extract_coloring_page_images ────────────────────────────────────────

def test_extract_ignores_nested_and_non_png_entries():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(5))
        pages = server._extract_coloring_page_images(zpath, 10)
    names = [name for name, _ in pages]
    check(len(pages) == 5, f"expected 5 root-level pages, got {len(pages)}")
    check(all("/" not in n for n in names), f"must never include nested entries, got {names}")
    check(all(n.lower().endswith(".png") for n in names), f"must only include PNGs, got {names}")
    check("thumbnails/preview.png" not in names, "nested thumbnail must be excluded")


def test_extract_returns_all_pages_when_at_or_under_the_cap():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(8))
        pages = server._extract_coloring_page_images(zpath, 10)
    check(len(pages) == 8, f"expected all 8 pages (under the cap), got {len(pages)}")


def test_extract_samples_evenly_across_a_larger_pack():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(20))
        pages = server._extract_coloring_page_images(zpath, 10)
    check(len(pages) == 10, f"expected exactly 10 sampled pages from a 20-page pack, got {len(pages)}")
    names = sorted(name for name, _ in pages)
    check(names[0] == "page_01.png", f"sample should include the first page, got {names[0]}")
    check(names[-1] != "page_01.png" and int(names[-1].split("_")[1].split(".")[0]) >= 18,
          f"an even spread across 20 pages should reach near the end, got last={names[-1]}")


# ── _check_no_pale_background category bypass ───────────────────────────

def test_pale_background_skipped_for_coloring_pages():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "white.png"
        path.write_bytes(_make_white_png_bytes())
        msg = server._check_no_pale_background(path, category="coloring_pages")
    check(msg is None, f"coloring_pages must bypass the pale-background check entirely, got: {msg}")


def test_pale_background_still_enforced_by_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "white.png"
        path.write_bytes(_make_white_png_bytes())
        msg_no_category = server._check_no_pale_background(path)
        msg_other_category = server._check_no_pale_background(path, category="wall_art")
    check(msg_no_category is not None, "a genuinely near-white photo must still fail the gate by default")
    check(msg_other_category is not None, "the bypass must be scoped to coloring_pages only, not every category")


# ── _produce_coloring_pages_listing_photos ───────────────────────────────

_ENTRY = {"category": "coloring_pages", "name": "Halloween Set",
          "files": ["data/digital_products/coloring_pages/sets/coloring_color1003_set_01.zip"]}


def test_produce_stages_up_to_ten_and_writes_files():
    with tempfile.TemporaryDirectory() as products_tmp, tempfile.TemporaryDirectory() as staged_tmp:
        products_root = Path(products_tmp)
        nested = products_root / "coloring_pages" / "sets"
        nested.mkdir(parents=True)
        (nested / "coloring_color1003_set_01.zip").write_bytes(_make_coloring_zip(20))
        old_products_root = server._FILE_ROOTS["products"]
        old_staged_root = server._FILE_ROOTS["staged_photos"]
        server._FILE_ROOTS["products"] = products_root
        server._FILE_ROOTS["staged_photos"] = Path(staged_tmp)
        staged_action_ids = []

        async def fake_stage(**kwargs):
            check(kwargs.get("category") == "coloring_pages", f"got kwargs: {kwargs}")
            staged_action_ids.append(len(staged_action_ids) + 1)
            return staged_action_ids[-1]

        try:
            with patch.object(server, "_find_catalog_product", return_value=dict(_ENTRY)), \
                 patch.object(server, "_gather_product_review", return_value={"listing_id": 999123}), \
                 patch.object(server, "_stage_photo_action", fake_stage):
                result = server._produce_coloring_pages_listing_photos("COLOR1003")
        finally:
            server._FILE_ROOTS["products"] = old_products_root
            server._FILE_ROOTS["staged_photos"] = old_staged_root

    check("error" not in result, f"should succeed, got {result}")
    check(len(result["staged"]) == 10, f"expected 10 staged photos (Etsy's cap), got {len(result['staged'])}")
    check(result["listing_id"] == 999123, f"got {result}")
    check(result["errors"] == [], f"got {result['errors']}")


def test_produce_errors_cleanly_with_no_listing_id():
    with patch.object(server, "_find_catalog_product", return_value=dict(_ENTRY)), \
         patch.object(server, "_gather_product_review", return_value={"listing_id": None}):
        result = server._produce_coloring_pages_listing_photos("COLOR1003")
    check("error" in result and "publish it first" in result["error"], f"got {result}")


def test_produce_errors_cleanly_with_no_zip_in_catalog():
    entry = {"category": "coloring_pages", "name": "X", "files": []}
    with patch.object(server, "_find_catalog_product", return_value=entry), \
         patch.object(server, "_gather_product_review", return_value={"listing_id": 111}):
        result = server._produce_coloring_pages_listing_photos("COLOR9999")
    check("error" in result and "no coloring-pages ZIP" in result["error"], f"got {result}")


def test_produce_rejects_wrong_category():
    entry = {"category": "wall_art", "name": "X", "files": []}
    with patch.object(server, "_find_catalog_product", return_value=entry):
        result = server._produce_coloring_pages_listing_photos("WA9999")
    check("error" in result and "wall_art" in result["error"], f"got {result}")


def test_produce_rejects_unknown_product():
    with patch.object(server, "_find_catalog_product", return_value=None):
        result = server._produce_coloring_pages_listing_photos("DOES_NOT_EXIST")
    check("error" in result and "unknown product_id" in result["error"], f"got {result}")


# ── _produce_listing_photos() category dispatch ──────────────────────────

def test_produce_listing_photos_dispatches_coloring_pages_to_the_new_path():
    with patch.object(server, "_find_catalog_product", return_value=dict(_ENTRY)), \
         patch.object(server, "_produce_coloring_pages_listing_photos",
                       return_value={"pid": "COLOR1003", "staged": [], "errors": [], "message": "ok"}) as mock_fn:
        result = server._produce_listing_photos({"pid": "COLOR1003"})
    check(mock_fn.called, "coloring_pages products must dispatch to _produce_coloring_pages_listing_photos()")
    check(result.get("pid") == "COLOR1003", f"got {result}")


def test_produce_listing_photos_still_handles_missing_pid():
    result = server._produce_listing_photos({})
    check("error" in result and "pid is required" in result["error"], f"got {result}")


# ── _validate_staged_action listing_photo branch: category-scoped bypass ─

def test_validate_staged_action_passes_near_white_coloring_photo():
    with tempfile.TemporaryDirectory() as staged_tmp:
        old_staged_root = server._FILE_ROOTS["staged_photos"]
        server._FILE_ROOTS["staged_photos"] = Path(staged_tmp)
        (Path(staged_tmp) / "COLOR1003").mkdir()
        (Path(staged_tmp) / "COLOR1003" / "page_01.png").write_bytes(_make_white_png_bytes())
        try:
            candidate = {"type": "listing_photo", "payload": {
                "listing_id": 999123, "rank": 1, "path": "COLOR1003/page_01.png",
                "category": "coloring_pages",
            }}
            ok, msg = server._validate_staged_action(candidate)
        finally:
            server._FILE_ROOTS["staged_photos"] = old_staged_root
    check(ok, f"a near-white coloring-page photo with category=coloring_pages must pass, got: {msg}")


def test_validate_staged_action_still_rejects_near_white_photo_without_category():
    with tempfile.TemporaryDirectory() as staged_tmp:
        old_staged_root = server._FILE_ROOTS["staged_photos"]
        server._FILE_ROOTS["staged_photos"] = Path(staged_tmp)
        (Path(staged_tmp) / "WA9999").mkdir()
        (Path(staged_tmp) / "WA9999" / "photo.png").write_bytes(_make_white_png_bytes())
        try:
            candidate = {"type": "listing_photo", "payload": {
                "listing_id": 999123, "rank": 1, "path": "WA9999/photo.png",
            }}
            ok, msg = server._validate_staged_action(candidate)
        finally:
            server._FILE_ROOTS["staged_photos"] = old_staged_root
    check(not ok and "pale" in msg, f"a near-white photo with no category must still fail the gate, got: {ok}, {msg}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLORING LISTING PHOTOS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLORING LISTING PHOTOS TESTS OK — real pack-page extraction/sampling, the "
          "category-scoped pale-background gate bypass (and that it stays scoped, not "
          "global), the staging core function's success/error paths, the category "
          "dispatch inside _produce_listing_photos(), and the end-to-end "
          "_validate_staged_action bypass all verified.")


if __name__ == "__main__":
    run()
