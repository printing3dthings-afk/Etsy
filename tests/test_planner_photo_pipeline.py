"""
Tests for Frank upgrade Wave 4, item A1 (2026-07-17): planner listing photos
now go through the real, self-verifying AI pipeline (tools/listing_photo_
pipeline.py) instead of a pure-PIL clip-art mockup.

Root cause this closes: `tools/gen_planner_listing_photos.py`'s
generate_for_planner() -- the function `_produce_listing_photos()` (main.py)
used to call -- never called an AI image model at all. Its own docstring
said so plainly ("Pure local render"). That's the actual reason planner
photos read as fake: not AI artifacts leaking through, a total absence of
photorealistic rendering for the shop's core product line (DP1026-1034).

Covers three layers:
  1. tools/listing_photo_pipeline.py -- the cfg-driven style-anchor fallback
     (_style_anchor_for), the finish pass (_apply_finish_pass: grain +
     vignette + unsharp), and PhotoResult's new fields.
  2. tools/gen_planner_listing_photos.py -- generate_ai_photos_for_planner(),
     the new glue function: renders real PDF pages via the existing
     render_page(), locates real sticker sheet PNGs via the same 3-way
     fallback chain make_sticker_showcase() already uses, and hands
     everything to the real pipeline.
  3. tools/api_server/main.py's _produce_listing_photos() -- routes passed
     photos into the existing staged-action approval queue when a listing_id
     exists (same path SS-series photos already use), falls back to the old
     Files-screen folder-drop UX for pre-publish drafts with no listing_id
     yet (DP1030-1034), and never silently drops a failed or realism-flagged
     photo.

Run: python tests/test_planner_photo_pipeline.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_photo_pipeline_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "photo-pipeline-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_photo_pipeline as lpp  # noqa: E402
import gen_planner_listing_photos as glp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── listing_photo_pipeline.py: style anchor fallback ────────────────────────
def test_hardcoded_style_anchor_unchanged_for_original_four():
    # DP1026-1029 must keep using their hand-tuned entries verbatim (plus the
    # new film-grain/commercial-photography phrase appended to each).
    anchor = lpp._style_anchor_for("DP1026", None)
    check("Lavender purple" in anchor, f"DP1026's hand-tuned anchor must be used as-is, got: {anchor[:100]!r}")
    check("sharp commercial product photography" in anchor,
          f"DP1026's anchor should carry the new vocabulary too, got: {anchor[:150]!r}")


def test_fallback_style_anchor_for_unconfigured_product_uses_cfg():
    cfg = {"theme": "Matcha Serenity", "color": (126, 200, 164), "accent": (184, 204, 142), "bg": (247, 249, 243)}
    anchor = lpp._style_anchor_for("DP1030", cfg)
    check("Matcha Serenity" in anchor, f"the fallback anchor must use the real theme name, got: {anchor[:150]!r}")
    check("#7EC8A4" in anchor, f"the fallback anchor must use the real hex color, got: {anchor[:200]!r}")
    check("cream linen desk surface" in anchor, f"a light theme should get a light desk surface, got: {anchor!r}")


def test_fallback_style_anchor_detects_dark_theme():
    cfg = {"theme": "Midnight Kawaii", "color": (128, 64, 156), "accent": (0, 229, 255), "bg": (26, 26, 46)}
    anchor = lpp._style_anchor_for("DP1032", cfg)
    check("deep charcoal desk surface" in anchor, f"a dark theme (bg sum < 400) should get a dark desk, got: {anchor!r}")


def test_no_cfg_and_no_hardcoded_entry_returns_empty_not_crash():
    anchor = lpp._style_anchor_for("DP9999", None)
    check(anchor == "", f"with neither a hardcoded entry nor a cfg, must return empty string, got: {anchor!r}")


def test_specialty_prompts_exist_for_all_nine_configured_planners():
    for pid in glp.PLANNER_PAGES:
        check(pid in lpp.SPECIALTY_PROMPTS,
              f"{pid} is a configured planner but has no SPECIALTY_PROMPTS entry -- "
              f"slot_10_specialty would resolve to the literal unformatted string "
              f"'{{specialty_prompt}}' and send a broken prompt to the image model")


# ── listing_photo_pipeline.py: finish pass ──────────────────────────────────
def test_finish_pass_darkens_corners_relative_to_center():
    from PIL import Image
    import numpy as np
    img = Image.new("RGB", (400, 400), (200, 180, 220))
    out = lpp._apply_finish_pass(img)
    check(out.size == (400, 400), f"finish pass must not change dimensions, got: {out.size}")
    arr = np.array(out).astype(float)
    center = arr[200, 200].mean()
    corner = arr[5, 5].mean()
    check(corner < center, f"vignette should darken corners relative to center, got corner={corner} center={center}")


def test_finish_pass_adds_variation_not_flat_uniform_output():
    from PIL import Image
    import numpy as np
    img = Image.new("RGB", (300, 300), (150, 150, 150))
    out = lpp._apply_finish_pass(img)
    arr = np.array(out.convert("L")).astype(float)
    # A perfectly flat input run through grain must show real per-pixel
    # variation in the (ungraded) center region -- confirms grain actually applied.
    center_patch = arr[140:160, 140:160]
    check(center_patch.std() > 0.5, f"expected visible grain variation in center, got std={center_patch.std()}")


# ── PhotoResult new fields ──────────────────────────────────────────────────
def test_photo_result_new_fields_default_empty():
    r = lpp.PhotoResult(True, Path("/tmp/x.jpg"))
    check(r.realism_issues == [], f"realism_issues should default to [], got: {r.realism_issues}")
    check(r.physics == "", f"physics should default to '', got: {r.physics!r}")
    check(r.scene_prompt == "", f"scene_prompt should default to '', got: {r.scene_prompt!r}")
    check(r.design_paths == [], f"design_paths should default to [], got: {r.design_paths}")


# ── gen_planner_listing_photos.py: sticker sheet resolution ────────────────
def test_find_sticker_sheet_prefers_processed_png_sheets_path():
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        orig_dp_base, orig_art_dir = glp.DP_BASE, glp.ART_DIR
        glp.DP_BASE = td
        glp.ART_DIR = os.path.join(td, "product_files")
        os.makedirs(glp.ART_DIR, exist_ok=True)
        sheets_dir = os.path.join(td, "stickers", "DP1030", "png_sheets")
        os.makedirs(sheets_dir, exist_ok=True)
        target = os.path.join(sheets_dir, "DP1030_sheet_01.png")
        Path(target).write_bytes(b"fake png bytes")
        try:
            found = glp._find_sticker_sheet("DP1030", 1)
            check(found == target, f"expected the processed png_sheets path, got: {found}")
            missing = glp._find_sticker_sheet("DP1030", 99)
            check(missing is None, f"a nonexistent sheet must return None, got: {missing}")
        finally:
            glp.DP_BASE, glp.ART_DIR = orig_dp_base, orig_art_dir


# ── gen_planner_listing_photos.py: generate_ai_photos_for_planner glue ─────
def test_generate_ai_photos_rejects_unconfigured_pid():
    try:
        glp.generate_ai_photos_for_planner("DP9999")
        _failures.append("expected ValueError for an unconfigured pid")
    except ValueError as exc:
        check("DP9999" in str(exc), f"error should name the bad pid, got: {exc}")


def test_generate_ai_photos_renders_real_pages_and_calls_pipeline():
    import fitz
    import shutil as _shutil
    from PIL import Image

    tmp_base = tempfile.mkdtemp(prefix="frank_photo_glue_")
    try:
        os.makedirs(os.path.join(tmp_base, "product_files"), exist_ok=True)
        os.makedirs(os.path.join(tmp_base, "stickers", "DP1030", "png_sheets"), exist_ok=True)

        doc = fitz.open()
        for i in range(120):
            doc.new_page(width=300, height=400)
        doc.save(os.path.join(tmp_base, "product_files", "DP1030.pdf"))
        doc.close()

        for n in [1, 3, 6, 9]:
            Image.new("RGBA", (50, 50), (255, 0, 0, 255)).save(
                os.path.join(tmp_base, "stickers", "DP1030", "png_sheets", f"DP1030_sheet_{n:02d}.png")
            )

        orig_dp_base, orig_art_dir = glp.DP_BASE, glp.ART_DIR
        glp.DP_BASE = tmp_base
        glp.ART_DIR = os.path.join(tmp_base, "product_files")

        orig_generate = lpp.generate_planner_listing_photos
        captured = {}

        def fake_generate(product_id, pdf_cover_path, pdf_spread_paths, sticker_sheet_paths, output_dir, client=None, cfg=None):
            captured["product_id"] = product_id
            captured["cfg"] = cfg
            captured["sticker_sheet_paths"] = list(sticker_sheet_paths)
            for label, p in {"cover": pdf_cover_path, **pdf_spread_paths}.items():
                if not Path(p).exists():
                    raise AssertionError(f"{label} render was not written to disk: {p}")
            return {
                slot: lpp.PhotoResult(True, output_dir / f"{slot}.jpg", 1, [], [], physics="ipad_lifestyle",
                                       scene_prompt="test scene", design_paths=[str(pdf_cover_path)])
                for slot in glp._AI_PHOTO_SLOT_ORDER
            }

        lpp.generate_planner_listing_photos = fake_generate
        try:
            out_dir, photos = glp.generate_ai_photos_for_planner("DP1030", engine="gemini")
        finally:
            lpp.generate_planner_listing_photos = orig_generate
            glp.DP_BASE, glp.ART_DIR = orig_dp_base, orig_art_dir

        check(captured.get("product_id") == "DP1030", f"expected product_id DP1030, got: {captured.get('product_id')}")
        check(captured.get("cfg", {}).get("theme") == "Matcha Serenity",
              f"expected the real PLANNER_PAGES cfg passed through, got: {captured.get('cfg')}")
        check(len(captured.get("sticker_sheet_paths", [])) == 3,
              f"expected 3 sticker sheets (capped), got: {len(captured.get('sticker_sheet_paths', []))}")
        check(len(photos) == 10, f"expected 10 photo entries, got: {len(photos)}")
        check(all(p["passed"] for p in photos), f"expected all mocked photos to pass, got: {photos}")
        check(os.environ.get("IMAGE_ENGINE") is None,
              f"IMAGE_ENGINE must be restored after the call, got: {os.environ.get('IMAGE_ENGINE')!r}")
    finally:
        import shutil as _shutil2
        _shutil2.rmtree(tmp_base, ignore_errors=True)


# ── main.py: _produce_listing_photos() staging integration ─────────────────
def test_produce_listing_photos_stages_when_listing_id_present():
    tmp_out = tempfile.mkdtemp(prefix="frank_produce_photos_")
    tmp_pdf_dir = tempfile.mkdtemp(prefix="frank_produce_pdf_")
    try:
        Path(tmp_pdf_dir, "DP1026.pdf").write_bytes(b"fake pdf")
        for slot in glp._AI_PHOTO_SLOT_ORDER:
            Path(tmp_out, f"{slot}.jpg").write_bytes(b"fake jpg bytes")

        orig_art_dir = glp.ART_DIR
        glp.ART_DIR = tmp_pdf_dir

        def fake_generate_ai(pid, engine=None, out_dir=None):
            return tmp_out, [
                {"slot": slot, "filename": f"{slot}.jpg", "passed": True, "issues": [],
                 "realism_issues": [], "physics": "ipad_lifestyle", "scene_prompt": "x", "design_paths": []}
                for slot in glp._AI_PHOTO_SLOT_ORDER
            ]

        orig_generate_ai = glp.generate_ai_photos_for_planner
        glp.generate_ai_photos_for_planner = fake_generate_ai

        staged_calls = []

        async def fake_stage_photo_action(listing_id, rank, sku, rel_path, summary, physics, scene_prompt, design_paths, fixes_action_id=None):
            staged_calls.append({"listing_id": listing_id, "rank": rank, "sku": sku, "rel_path": rel_path})
            return 1000 + rank

        orig_stage = server._stage_photo_action
        server._stage_photo_action = fake_stage_photo_action

        try:
            result = server._produce_listing_photos({"pid": "DP1026"})
        finally:
            glp.ART_DIR = orig_art_dir
            glp.generate_ai_photos_for_planner = orig_generate_ai
            server._stage_photo_action = orig_stage

        check("error" not in result, f"expected success, got: {result}")
        check(result["count"] == 10, f"expected 10 passed photos, got: {result['count']}")
        check(len(result["staged"]) == 10, f"expected all 10 to be staged (DP1026 has a real listing_id), got: {result['staged']}")
        check(len(staged_calls) == 10, f"expected 10 real _stage_photo_action calls, got: {len(staged_calls)}")
        check(staged_calls[0]["listing_id"] == glp.PLANNER_PAGES["DP1026"]["listing_id"],
              f"expected the real DP1026 listing_id, got: {staged_calls[0]['listing_id']}")
        check("staged" in result["message"] and "approval" in result["message"],
              f"message should mention staging, got: {result['message']!r}")
    finally:
        import shutil as _shutil3
        _shutil3.rmtree(tmp_out, ignore_errors=True)
        _shutil3.rmtree(tmp_pdf_dir, ignore_errors=True)


def test_produce_listing_photos_falls_back_to_folder_when_no_listing_id():
    # DP1030 is a pre-publish draft with no listing_id in PLANNER_PAGES.
    check("listing_id" not in glp.PLANNER_PAGES["DP1030"],
          "sanity check: DP1030 must have no listing_id (still a draft) for this test to be meaningful")

    tmp_out = tempfile.mkdtemp(prefix="frank_produce_photos_nolisting_")
    tmp_pdf_dir = tempfile.mkdtemp(prefix="frank_produce_pdf_nolisting_")
    try:
        Path(tmp_pdf_dir, "DP1030.pdf").write_bytes(b"fake pdf")

        def fake_generate_ai(pid, engine=None, out_dir=None):
            return tmp_out, [
                {"slot": "slot_01_hero", "filename": "slot_01_hero.jpg", "passed": True, "issues": [],
                 "realism_issues": [], "physics": "ipad_lifestyle", "scene_prompt": "x", "design_paths": []},
            ]

        orig_art_dir = glp.ART_DIR
        glp.ART_DIR = tmp_pdf_dir
        orig_generate_ai = glp.generate_ai_photos_for_planner
        glp.generate_ai_photos_for_planner = fake_generate_ai

        try:
            result = server._produce_listing_photos({"pid": "DP1030"})
        finally:
            glp.ART_DIR = orig_art_dir
            glp.generate_ai_photos_for_planner = orig_generate_ai

        check("error" not in result, f"expected success, got: {result}")
        check(result["staged"] == [], f"no listing_id -> nothing should be staged, got: {result['staged']}")
        check("No Etsy listing_id yet" in result["message"], f"message should explain why nothing staged, got: {result['message']!r}")
    finally:
        import shutil as _shutil4
        _shutil4.rmtree(tmp_out, ignore_errors=True)
        _shutil4.rmtree(tmp_pdf_dir, ignore_errors=True)


def test_produce_listing_photos_surfaces_failures_and_realism_flags():
    tmp_out = tempfile.mkdtemp(prefix="frank_produce_photos_mixed_")
    tmp_pdf_dir = tempfile.mkdtemp(prefix="frank_produce_pdf_mixed_")
    try:
        Path(tmp_pdf_dir, "DP1030.pdf").write_bytes(b"fake pdf")
        Path(tmp_out, "slot_01_hero.jpg").write_bytes(b"fake jpg")

        def fake_generate_ai(pid, engine=None, out_dir=None):
            return tmp_out, [
                {"slot": "slot_01_hero", "filename": "slot_01_hero.jpg", "passed": True, "issues": [],
                 "realism_issues": ["slightly plastic surface"], "physics": "", "scene_prompt": "", "design_paths": []},
                {"slot": "slot_02_whats_included", "filename": None, "passed": False,
                 "issues": ["design mismatch"], "realism_issues": [], "physics": "", "scene_prompt": "", "design_paths": []},
            ]

        orig_art_dir = glp.ART_DIR
        glp.ART_DIR = tmp_pdf_dir
        orig_generate_ai = glp.generate_ai_photos_for_planner
        glp.generate_ai_photos_for_planner = fake_generate_ai

        try:
            result = server._produce_listing_photos({"pid": "DP1030"})
        finally:
            glp.ART_DIR = orig_art_dir
            glp.generate_ai_photos_for_planner = orig_generate_ai

        check(len(result["failed"]) == 1, f"expected 1 failed slot surfaced, got: {result['failed']}")
        check(result["failed"][0]["slot"] == "slot_02_whats_included", f"got: {result['failed']}")
        check(len(result["realism_flags"]) == 1, f"expected 1 realism-flagged photo surfaced, got: {result['realism_flags']}")
        check("failed verification" in result["message"], f"message should mention the failure, got: {result['message']!r}")
        check("realism notes" in result["message"], f"message should mention realism notes, got: {result['message']!r}")
    finally:
        import shutil as _shutil5
        _shutil5.rmtree(tmp_out, ignore_errors=True)
        _shutil5.rmtree(tmp_pdf_dir, ignore_errors=True)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PLANNER PHOTO PIPELINE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PLANNER PHOTO PIPELINE TESTS OK — style anchor fallback (light + dark themes), "
          "SPECIALTY_PROMPTS coverage for all 9 configured planners, the finish pass "
          "(vignette + grain), PhotoResult's new fields, sticker-sheet path resolution, "
          "the full generate_ai_photos_for_planner glue (real PDF page rendering + "
          "real sticker paths + cfg passthrough + engine env var save/restore), and "
          "_produce_listing_photos()'s staging integration (stages when a listing_id "
          "exists, falls back to the folder-drop UX when it doesn't, and never "
          "silently drops a failed or realism-flagged photo).")


if __name__ == "__main__":
    run()
