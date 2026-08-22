"""
Test for the 2026-08-15 addition of engine="gpt-image-1.5" to tools/image_gen.py.

Context: gpt-image-1 (the only engine that supported background="transparent",
used for every sticker/cut-out asset) shuts down 2026-10-23. Its documented
successor, gpt-image-2, explicitly does NOT support transparent background --
confirmed against OpenAI's own docs, and image_gen.py already raised a clear
error for that combination before this change. Research turned up a real,
already-shipped bridge: gpt-image-1.5 (OpenAI, December 2025) keeps native
transparent PNG output AND has a later shutdown date (2026-12-01) than
gpt-image-1 -- the correct migration target for the sticker/cut-out path
specifically, not gpt-image-2.

This test verifies the wiring, not live output (no OPENAI_API_KEY call is
made) -- the engine is explicitly documented as UNPROVEN in this codebase
until a real generation is checked, same discipline as Grok/veo elsewhere.

Run: python tests/test_gpt_image_1_5_engine.py
"""
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import image_gen  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_gpt_image_1_5_is_openai_compatible_and_maps_to_the_right_model_string():
    check("gpt-image-1.5" in image_gen._OPENAI_COMPATIBLE_ENGINES,
          "gpt-image-1.5 must route through the same REST call path as gpt-image-1/gpt-image-2, "
          "not fall into the gemini/ideogram/grok branch")
    check(image_gen._openai_model_for("gpt-image-1.5") == "gpt-image-1.5",
          "the model string sent to OpenAI's API must be exactly 'gpt-image-1.5'")
    check(image_gen._openai_model_for("gpt-image-2") == "gpt-image-2",
          "adding gpt-image-1.5 must not regress gpt-image-2's existing model mapping")
    check(image_gen._openai_model_for("openai") == "gpt-image-1",
          "adding gpt-image-1.5 must not regress the default 'openai' engine's model mapping")


def test_generate_image_allows_transparent_background_on_gpt_image_1_5():
    captured = {}

    def _fake_post(url, body, headers, retries, timeout):
        import json
        captured["payload"] = json.loads(body)
        return {"data": [{"b64_json": "aGVsbG8="}]}  # "hello" base64, just needs to decode

    with patch.object(image_gen, "_api_key", return_value="fake-key"), \
         patch.object(image_gen, "_post", side_effect=_fake_post), \
         patch("pathlib.Path.write_bytes"), \
         patch("pathlib.Path.mkdir"):
        # Must NOT raise -- gpt-image-2 raises for this exact combination, gpt-image-1.5 must not.
        image_gen.generate_image(
            "a kawaii sticker", "/tmp/out.png", output_format="png",
            background="transparent", engine="gpt-image-1.5",
        )

    check(captured["payload"]["model"] == "gpt-image-1.5",
          f"the actual API request must use model=gpt-image-1.5, got: {captured['payload'].get('model')}")
    check(captured["payload"]["background"] == "transparent",
          "the transparent background request must actually reach the API payload")


def test_gpt_image_2_still_rejects_transparent_background():
    # Regression guard: adding gpt-image-1.5 to _OPENAI_COMPATIBLE_ENGINES must not
    # accidentally loosen gpt-image-2's own transparent-background guard.
    try:
        image_gen.generate_image(
            "a kawaii sticker", "/tmp/out.png", output_format="png",
            background="transparent", engine="gpt-image-2",
        )
        check(False, "engine='gpt-image-2' must still raise on background='transparent'")
    except image_gen.ImageGenError as e:
        check("gpt-image-2" in str(e) and "transparent" in str(e),
              f"error should name the engine and the transparent-background limitation, got: {e}")


def test_unknown_engine_error_messages_mention_the_new_engine():
    try:
        image_gen.generate_image("x", "/tmp/out.jpg", engine="not-a-real-engine")
        check(False, "an unknown engine must raise ImageGenError")
    except image_gen.ImageGenError as e:
        check("gpt-image-1.5" in str(e), f"the unknown-engine error should list gpt-image-1.5 among valid options, got: {e}")


def test_non_openai_engine_transparent_background_error_recommends_gpt_image_1_5():
    try:
        image_gen.generate_image(
            "a kawaii sticker", "/tmp/out.png", output_format="png",
            background="transparent", engine="ideogram",
        )
        check(False, "ideogram does not support transparent background and must raise")
    except image_gen.ImageGenError as e:
        check("gpt-image-1.5" in str(e),
              f"the remediation should point at gpt-image-1.5 as the real fix, got: {e}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GPT-IMAGE-1.5 ENGINE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GPT-IMAGE-1.5 ENGINE TESTS OK — the new engine routes through the OpenAI-compatible "
          "path with the correct model string, allows background='transparent' (unlike "
          "gpt-image-2, which still correctly rejects it), and every relevant error message "
          "points at it as the real migration target for stickers/cut-outs.")


if __name__ == "__main__":
    run()
