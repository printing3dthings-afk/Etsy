#!/usr/bin/env python3
"""
Tests for generate_wall_art_master()'s verify+retry wiring (2026-07-30).

Previously a single-shot generate-and-hope call (tools/art_creation_tools.py)
with zero automated quality check on brand-new AI-generated wall art -- unlike
the listing-photo pipeline's already-proven verify+retry pattern
(tools/listing_photo_pipeline.py / tools/goal_loop.py). This is the first
product-art generator routed through that same shared machinery
(image_gen.verify_original_art() + goal_loop.run_until_goal()), per Scott's
ask to raise the bar on how digital products get prompted/generated.

Mocks the narrowest real dependencies: image_gen.generate_image() (never
calls a real AI API), image_gen.verify_original_art() (never calls a real
vision API), and image_gen.gemini_key_available() -- exercises
generate_wall_art_master()'s own retry/fallback logic directly. Isolates
PRODUCT_FILES_DIR to a temp dir so this never touches the real data/ tree.

(2026-07-31) Every test now explicitly mocks gemini_key_available() to True
(or False, for the dedicated skip-QA test) rather than relying on the ambient
environment's real GEMINI_API_KEY -- CI has none, so before this fix these
tests passed locally (a real key happened to be configured) but failed in CI
the moment the guard was added. See ops_runbook.md's 2026-07-31 entry.

Run: python tests/test_wall_art_verify_retry.py
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

import tools.art_creation_tools as act  # noqa: E402
from tools import image_gen  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _write_stub_png(path: str, *_a, **_k) -> None:
    from PIL import Image
    Image.new("RGB", (32, 32), color=(120, 90, 60)).save(path, "PNG")


def _noop_upscale(src_path: str, dst_path: str, target_px: int = 3000) -> None:
    # Skip the real Lanczos upscale/sharpen pipeline -- not what this test
    # verifies -- but still produce a real file at dst_path so callers that
    # check for its existence don't get a false read.
    Path(dst_path).write_bytes(Path(src_path).read_bytes())


def test_passes_on_first_attempt_no_retry():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(act, "PRODUCT_FILES_DIR", tmp), \
             patch.object(image_gen, "generate_image", side_effect=lambda prompt, out_path, **kw: _write_stub_png(out_path)) as gen_mock, \
             patch.object(image_gen, "verify_original_art", return_value={"pass": True, "issues": []}) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True), \
             patch.object(act, "_upscale_for_print", side_effect=_noop_upscale):
            path = act.generate_wall_art_master("WA_TEST01", "a boho sun in terracotta")
        check(gen_mock.call_count == 1, f"a passing first attempt must not retry, got {gen_mock.call_count} generate calls")
        check(verify_mock.call_count == 1, f"expected exactly one verify call, got {verify_mock.call_count}")
        check(os.path.isfile(path), f"expected final file to exist at {path}")


def test_retries_once_with_correction_then_passes():
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(act, "PRODUCT_FILES_DIR", tmp), \
             patch.object(image_gen, "generate_image", side_effect=lambda prompt, out_path, **kw: _write_stub_png(out_path)) as gen_mock, \
             patch.object(image_gen, "verify_original_art", side_effect=[
                 {"pass": False, "issues": ["garbled text in the corner"]},
                 {"pass": True, "issues": []},
             ]) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True), \
             patch.object(act, "_upscale_for_print", side_effect=_noop_upscale):
            path = act.generate_wall_art_master("WA_TEST02", "a sunflower field")
        check(gen_mock.call_count == 2, f"a failing first attempt must retry once, got {gen_mock.call_count} generate calls")
        check(verify_mock.call_count == 2, f"expected two verify calls, got {verify_mock.call_count}")
        # The retry's prompt must carry the specific failure forward as corrective feedback.
        second_call_prompt = gen_mock.call_args_list[1].args[0]
        check("garbled text in the corner" in second_call_prompt,
              f"the retry prompt must include the previous failure as feedback, got: {second_call_prompt[-300:]!r}")
        check(os.path.isfile(path), f"expected final file to exist at {path}")


def test_exhausted_retries_still_returns_a_file_not_raise():
    # "Never fabricate success" (goal_loop's own rule) means passed=False is
    # honest here -- but generate_wall_art_master() must not raise on a QA
    # miss (only a real generation error should raise), since the caller
    # (build_wallart_product.py) has no source art to fall back to and a
    # crash would leave the product with NO art file at all.
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(act, "PRODUCT_FILES_DIR", tmp), \
             patch.object(image_gen, "generate_image", side_effect=lambda prompt, out_path, **kw: _write_stub_png(out_path)) as gen_mock, \
             patch.object(image_gen, "verify_original_art", return_value={"pass": False, "issues": ["wrong subject matter"]}) as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=True), \
             patch.object(act, "_upscale_for_print", side_effect=_noop_upscale):
            path = act.generate_wall_art_master("WA_TEST03", "a lighthouse")
        check(gen_mock.call_count == 2, f"expected the max_attempts=2 cap to be honored, got {gen_mock.call_count}")
        check(os.path.isfile(path), "an exhausted retry must still produce a usable file, not raise")


def test_missing_gemini_key_skips_qa_single_shot():
    # 2026-07-31 (Create UX audit): verify_original_art() has its own
    # GEMINI_API_KEY dependency independent of whichever engine generated the
    # image -- without this guard, a missing key would masquerade as an
    # ordinary QA failure: retried uselessly with a "fix this" correction the
    # model can't act on, then still shipped unverified anyway. This is the
    # exact CI failure this test guards against: CI has no real
    # GEMINI_API_KEY, so the other three tests above must mock
    # gemini_key_available() themselves rather than relying on the ambient
    # environment (which happened to have a real key locally, masking the gap).
    with tempfile.TemporaryDirectory() as tmp:
        with patch.object(act, "PRODUCT_FILES_DIR", tmp), \
             patch.object(image_gen, "generate_image", side_effect=lambda prompt, out_path, **kw: _write_stub_png(out_path)) as gen_mock, \
             patch.object(image_gen, "verify_original_art") as verify_mock, \
             patch.object(image_gen, "gemini_key_available", return_value=False), \
             patch.object(act, "_upscale_for_print", side_effect=_noop_upscale):
            path = act.generate_wall_art_master("WA_TEST04", "a mountain range")
        check(gen_mock.call_count == 1, f"no Gemini key should mean a single generate call, no retry loop, got {gen_mock.call_count}")
        check(verify_mock.call_count == 0, f"verify_original_art must not be called when the Gemini key is missing, got {verify_mock.call_count} calls")
        check(os.path.isfile(path), "generation should still succeed and produce a file even with QA skipped")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("WALL ART VERIFY+RETRY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("WALL ART VERIFY+RETRY TESTS OK — generate_wall_art_master() verifies against "
          "the prompt, retries once with corrective feedback on a miss, and never raises "
          "on an exhausted QA miss (only a real generation error should).")


if __name__ == "__main__":
    run()
