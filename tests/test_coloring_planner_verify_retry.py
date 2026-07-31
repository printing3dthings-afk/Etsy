#!/usr/bin/env python3
"""
Tests for generate_coloring_page()'s and _generate_cover_image()'s verify+retry
wiring (2026-07-31, Create screen UX audit) -- the deferred half of
generate_wall_art_master()'s 2026-07-30 fix (see test_wall_art_verify_retry.py,
whose own docstring/comments this test file's setup mirrors). Both were
single-shot generate-and-hope calls with zero automated quality check;
Coloring Pages is the higher-risk gap of the two since generate_dynamic_theme_set()
also runs unattended via tools/post_scheduled_coloring.py's recurring cron job,
with no human reviewing the raw images before they're staged as a real listing.

Also covers the GEMINI_API_KEY guard (image_gen.gemini_key_available()): when
missing, both functions must skip the QA loop entirely (single generate call,
no retry, matching original single-shot behavior) rather than let a missing
verification key masquerade as an ordinary QA miss and burn real generation
calls on a gate that can never pass.

Mocks the narrowest real dependencies (image_gen.generate_image() /
image_gen.verify_original_art() / image_gen.gemini_key_available()) -- never
calls a real AI or vision API.

Run: python tests/test_coloring_planner_verify_retry.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import tools.generate_coloring_pages as gcp  # noqa: E402
import tools.generate_planner as gp  # noqa: E402
from tools import image_gen  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_png_bytes() -> bytes:
    from io import BytesIO
    from PIL import Image
    buf = BytesIO()
    Image.new("RGB", (40, 40), color=(10, 200, 30)).save(buf, "PNG")
    return buf.getvalue()


def _write_stub_png(path: str, *_a, **_k):
    from PIL import Image
    Image.new("RGB", (40, 40), color=(200, 30, 10)).save(path, "PNG")


# ── generate_coloring_page() ────────────────────────────────────────────────

_THEME = {"id": "TESTCP01", "title": "Test Theme", "prompt": "a simple cartoon cat, thick outlines"}


def test_coloring_page_passes_on_first_attempt_no_retry():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(gcp, "_gen_image_openai", return_value=_fake_png_bytes()) as gen_mock, \
             patch.object(image_gen, "verify_original_art", return_value={"pass": True, "issues": []}) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True):
            path = gcp.generate_coloring_page(_THEME, Path(tmp))
        check(gen_mock.call_count == 1, f"a passing first attempt must not retry, got {gen_mock.call_count} generate calls")
        check(verify_mock.call_count == 1, f"expected exactly one verify call, got {verify_mock.call_count}")
        check(path is not None and path.is_file(), f"expected final file to exist at {path}")


def test_coloring_page_retries_once_then_passes():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(gcp, "_gen_image_openai", return_value=_fake_png_bytes()) as gen_mock, \
             patch.object(image_gen, "verify_original_art", side_effect=[
                 {"pass": False, "issues": ["wrong subject entirely"]},
                 {"pass": True, "issues": []},
             ]) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True):
            path = gcp.generate_coloring_page(dict(_THEME, id="TESTCP02"), Path(tmp))
        check(gen_mock.call_count == 2, f"a failing first attempt must retry once, got {gen_mock.call_count} generate calls")
        check(verify_mock.call_count == 2, f"expected two verify calls, got {verify_mock.call_count}")
        check(path is not None and path.is_file(), f"expected final file to exist at {path}")


def test_coloring_page_exhausted_retries_still_returns_file_not_raise():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(gcp, "_gen_image_openai", return_value=_fake_png_bytes()) as gen_mock, \
             patch.object(image_gen, "verify_original_art", return_value={"pass": False, "issues": ["garbled text"]}), \
             patch.object(image_gen, "gemini_key_available", return_value=True):
            path = gcp.generate_coloring_page(dict(_THEME, id="TESTCP03"), Path(tmp))
        check(gen_mock.call_count == 2, f"expected the max_attempts=2 cap to be honored, got {gen_mock.call_count}")
        check(path is not None and path.is_file(), "an exhausted retry must still produce a usable file, not raise")


def test_coloring_page_missing_gemini_key_skips_qa_single_shot():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(gcp, "_gen_image_openai", return_value=_fake_png_bytes()) as gen_mock, \
             patch.object(image_gen, "verify_original_art") as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=False):
            path = gcp.generate_coloring_page(dict(_THEME, id="TESTCP04"), Path(tmp))
        check(gen_mock.call_count == 1, f"no Gemini key should mean a single generate call, no retry loop, got {gen_mock.call_count}")
        check(verify_mock.call_count == 0, f"verify_original_art must not be called when the Gemini key is missing, got {verify_mock.call_count} calls")
        check(path is not None and path.is_file(), "generation should still succeed and produce a file even with QA skipped")


def test_coloring_page_real_generation_failure_returns_none():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(gcp, "_gen_image_openai", return_value=None), \
             patch.object(image_gen, "gemini_key_available", return_value=False):
            path = gcp.generate_coloring_page(dict(_THEME, id="TESTCP05"), Path(tmp))
        check(path is None, f"a real image-engine failure (no bytes returned) should return None, got {path}")


# ── _generate_cover_image() ─────────────────────────────────────────────────

_CFG = {"cover_prompt": "a kawaii lavender planner cover illustration"}


def test_cover_passes_on_first_attempt_no_retry():
    # generate_image/verify_original_art/gemini_key_available/ImageGenError are all
    # imported locally inside _generate_cover_image() (`from tools.image_gen import
    # ...`), not bound at generate_planner module scope -- patch the source module
    # (image_gen) so the fresh import each call picks up the mock.
    with tempfile.TemporaryDirectory() as tmp:
        out_path = str(Path(tmp) / "cover.png")
        with patch.object(image_gen, "generate_image", side_effect=lambda prompt, out, **kw: _write_stub_png(out)) as gen_mock, \
             patch.object(image_gen, "verify_original_art", return_value={"pass": True, "issues": []}) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True):
            ok = gp._generate_cover_image(_CFG, out_path)
        check(ok is True, "expected success on a passing first attempt")
        check(gen_mock.call_count == 1, f"a passing first attempt must not retry, got {gen_mock.call_count}")
        check(verify_mock.call_count == 1, f"expected exactly one verify call, got {verify_mock.call_count}")
        check(os.path.isfile(out_path), f"expected the cover file to exist at {out_path}")


def test_cover_retries_once_then_passes():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = str(Path(tmp) / "cover.png")
        with patch.object(image_gen, "generate_image", side_effect=lambda prompt, out, **kw: _write_stub_png(out)) as gen_mock, \
             patch.object(image_gen, "verify_original_art", side_effect=[
                 {"pass": False, "issues": ["broken multi-panel collage"]},
                 {"pass": True, "issues": []},
             ]) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True):
            ok = gp._generate_cover_image(_CFG, out_path)
        check(ok is True, "expected eventual success after one retry")
        check(gen_mock.call_count == 2, f"a failing first attempt must retry once, got {gen_mock.call_count}")
        second_call_prompt = gen_mock.call_args_list[1].args[0]
        check("broken multi-panel collage" in second_call_prompt,
              f"the retry prompt must include the previous failure as feedback, got: {second_call_prompt[-300:]!r}")


def test_cover_exhausted_retries_still_returns_true_not_raise():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = str(Path(tmp) / "cover.png")
        with patch.object(image_gen, "generate_image", side_effect=lambda prompt, out, **kw: _write_stub_png(out)) as gen_mock, \
             patch.object(image_gen, "verify_original_art", return_value={"pass": False, "issues": ["wrong subject"]}), \
             patch.object(image_gen, "gemini_key_available", return_value=True):
            ok = gp._generate_cover_image(_CFG, out_path)
        check(gen_mock.call_count == 2, f"expected the max_attempts=2 cap to be honored, got {gen_mock.call_count}")
        check(ok is True, "an exhausted QA miss must still return True (a usable file exists) -- generate_planner() has no fallback cover")
        check(os.path.isfile(out_path), "the last-attempt file must still be on disk")


def test_cover_missing_gemini_key_skips_qa_single_shot():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = str(Path(tmp) / "cover.png")
        with patch.object(image_gen, "generate_image", side_effect=lambda prompt, out, **kw: _write_stub_png(out)) as gen_mock, \
             patch.object(image_gen, "verify_original_art") as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=False):
            ok = gp._generate_cover_image(_CFG, out_path)
        check(ok is True, "generation should still succeed with QA skipped")
        check(gen_mock.call_count == 1, f"no Gemini key should mean a single generate call, got {gen_mock.call_count}")
        check(verify_mock.call_count == 0, "verify_original_art must not be called when the Gemini key is missing")


def test_cover_real_generation_failure_returns_false():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = str(Path(tmp) / "cover.png")
        with patch.object(image_gen, "generate_image", side_effect=image_gen.ImageGenError("OPENAI_API_KEY not set (env or .env)")), \
             patch.object(image_gen, "gemini_key_available", return_value=False):
            ok = gp._generate_cover_image(_CFG, out_path)
        check(ok is False, "a real ImageGenError from generation itself must return False, not raise")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLORING/PLANNER VERIFY+RETRY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLORING/PLANNER VERIFY+RETRY TESTS OK — generate_coloring_page() and "
          "_generate_cover_image() both verify against the prompt, retry once with "
          "corrective feedback on a miss, never raise on an exhausted QA miss, and "
          "cleanly skip the QA pass (single generate call) when GEMINI_API_KEY is missing.")


if __name__ == "__main__":
    run()
