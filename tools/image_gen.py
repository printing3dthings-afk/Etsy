#!/usr/bin/env python3
"""
image_gen.py — the single shared gpt-image-1 helper for OnBrandCraftz.

Every tool that generates imagery should call generate_image() / edit_image() here
instead of hand-rolling its own urllib call. Centralizing this guarantees:
  • Consistent quality (default quality="high" for production assets)
  • Consistent resolution (named SIZE constants — no stray 1024x1024 typos)
  • One retry/backoff implementation that honors transient OpenAI errors
  • Both b64_json and url response shapes handled in one place
  • API key loaded from .env the same way everywhere

gpt-image-1 supported sizes (the ONLY valid values):
    1024x1024  (square)    1024x1536  (portrait)    1536x1024  (landscape)
Anything larger (e.g. the 2400px listing-photo spec) is reached by upscaling AFTER
generation — gpt-image-1 cannot emit it directly.

Usage:
    from tools.image_gen import generate_image, edit_image, PORTRAIT, SQUARE, LANDSCAPE

    generate_image(prompt, "out.jpg", size=PORTRAIT)            # text -> image
    edit_image(prompt, ["empty_room.jpg"], "scene.jpg")         # image+prompt -> image
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path

# Canonical sizes — use these constants, never raw strings, so a typo can't ship a
# wrongly-shaped image.
SQUARE = "1024x1024"
PORTRAIT = "1024x1536"
LANDSCAPE = "1536x1024"
_VALID_SIZES = {SQUARE, PORTRAIT, LANDSCAPE}

_GEN_URL = "https://api.openai.com/v1/images/generations"
_EDIT_URL = "https://api.openai.com/v1/images/edits"
_MODEL = "gpt-image-1"

_BASE_DIR = Path(__file__).parent.parent
_ENV_PATH = _BASE_DIR / ".env"


class ImageGenError(Exception):
    """Raised when image generation fails after all retries."""


def _api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "")
    if not key and _ENV_PATH.exists():
        # Lazy-load from .env without overwriting anything already set
        with open(_ENV_PATH) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("OPENAI_API_KEY=") and "=" in line:
                    key = line.split("=", 1)[1].strip()
                    os.environ.setdefault("OPENAI_API_KEY", key)
                    break
    if not key:
        raise ImageGenError("OPENAI_API_KEY not set (env or .env)")
    return key


def _extract_bytes(result: dict) -> bytes:
    data = result["data"][0]
    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])
    if data.get("url"):
        with urllib.request.urlopen(data["url"], timeout=60) as r:
            return r.read()
    raise ImageGenError("response contained neither b64_json nor url")


def _post(url: str, body: bytes, headers: dict, retries: int, timeout: int) -> dict:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode()[:200]
            except Exception:
                pass
            last_err = ImageGenError(f"HTTP {e.code}: {detail}")
            # 4xx other than 429 won't fix themselves — fail fast
            if e.code != 429 and 400 <= e.code < 500:
                raise last_err
        except Exception as e:  # noqa: BLE001 — network/timeouts are all retryable
            last_err = e
        if attempt < retries - 1:
            wait = 2 ** (attempt + 1)  # 2s, 4s, 8s, ...
            print(f"    image_gen retry {attempt + 1}/{retries - 1} in {wait}s: {last_err}")
            time.sleep(wait)
    raise ImageGenError(f"image generation failed after {retries} attempts: {last_err}")


# ── Engine selection (migration off gpt-image-1, deprecated 2026-10-23) ─────────
# Providers sit behind an engine flag, same pattern as tools/ai_video.py. OpenAI
# (gpt-image-1) stays the DEFAULT until a replacement is proven; flip per deploy
# with IMAGE_ENGINE, or per call with engine=. Engines:
#   "openai"     — gpt-image-1 (default, unchanged, proven). Shuts down 2026-10-23
#                  per OpenAI's deprecations page — migrate call sites to
#                  "gpt-image-2" before then, EXCEPT anywhere background="transparent"
#                  is used (stickers/cut-outs) — see the note below.
#   "gpt-image-2" — OpenAI's gpt-image-1 successor (shipped 2026-04-21). Same REST
#                  endpoints/response shape as gpt-image-1 (this module reuses the
#                  same call path, just swaps the model string), native reasoning,
#                  sharper text-in-image, flexible sizes beyond the 3 canonical
#                  constants below if ever needed. LIMITATION: does NOT support
#                  background="transparent" (verified against OpenAI's docs,
#                  2026-07) — generate_image()/edit_image() raise a clear
#                  ImageGenError if you try, same as the gemini/ideogram guard
#                  below. Sticker/cut-out generation must keep using engine="openai"
#                  (or a future transparency-capable engine) until/unless that
#                  changes. Also omits input_fidelity on edits — gpt-image-2
#                  processes every input at high fidelity automatically, the API
#                  doesn't accept overriding it.
#   "gemini"     — Google "Nano Banana" (gemini-2.5-flash-image); best at keeping the
#                  same product consistent across scenes → ideal for listing mockups
#   "ideogram"   — Ideogram 3.0; best text-in-image (covers/badges); GENERATE-ONLY
_DEFAULT_ENGINE = "openai"
_GEMINI_IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-2.5-flash-image")
_OPENAI_COMPATIBLE_ENGINES = {"openai", "gpt-image-2"}


def _openai_model_for(eng: str) -> str:
    return "gpt-image-2" if eng == "gpt-image-2" else _MODEL


def _engine(engine: str | None) -> str:
    return (engine or os.getenv("IMAGE_ENGINE", _DEFAULT_ENGINE)).lower().strip()


def _gemini_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not key and _ENV_PATH.exists():
        with open(_ENV_PATH) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY=") and "=" in line:
                    key = line.split("=", 1)[1].strip()
                    os.environ.setdefault("GEMINI_API_KEY", key)
                    break
    if not key:
        raise ImageGenError("GEMINI_API_KEY not set (needed for engine='gemini')")
    return key


def _gemini_bytes_from_resp(resp) -> bytes:
    """Pull the first inline image out of a google-genai generate_content response.
    Shape verified live against google-genai 2.10: candidates[0].content.parts[].inline_data.data"""
    cands = getattr(resp, "candidates", None) or []
    for cand in cands:
        content = getattr(cand, "content", None)
        for part in (getattr(content, "parts", None) or []):
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                return inline.data
    raise ImageGenError("Gemini response contained no image data")


def _gemini_generate_bytes(prompt: str, model: str | None = None) -> bytes:
    from google import genai
    client = genai.Client(api_key=_gemini_key())
    resp = client.models.generate_content(
        model=model or _GEMINI_IMAGE_MODEL, contents=[prompt])
    return _gemini_bytes_from_resp(resp)


def _gemini_edit_bytes(prompt: str, image_paths: list, model: str | None = None) -> bytes:
    """Nano Banana image edit: prompt + one or more reference images → new image.
    This is the call that drives the listing-photo pipeline when IMAGE_ENGINE=gemini."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=_gemini_key())
    contents: list = [prompt]
    for p in image_paths:
        p = Path(p)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    resp = client.models.generate_content(
        model=model or _GEMINI_IMAGE_MODEL, contents=contents)
    return _gemini_bytes_from_resp(resp)


def _ideogram_key() -> str:
    key = os.getenv("IDEOGRAM_API_KEY", "")
    if not key and _ENV_PATH.exists():
        with open(_ENV_PATH) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("IDEOGRAM_API_KEY=") and "=" in line:
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        raise ImageGenError("IDEOGRAM_API_KEY not set (needed for engine='ideogram')")
    return key


_IDEOGRAM_ASPECT = {SQUARE: "1x1", PORTRAIT: "2x3", LANDSCAPE: "3x2"}


def _ideogram_generate_bytes(prompt: str, size: str) -> bytes:
    """Ideogram 3.0 text→image. UNPROVEN (no IDEOGRAM_API_KEY in this env yet) —
    written to the documented v3 REST API; confirm endpoint/fields on first real
    key, same discipline as the Veo path was before its proof."""
    key = _ideogram_key()
    boundary = "----ideo" + os.urandom(8).hex()
    parts: list[bytes] = []

    def _field(name: str, value: str):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
                     f'\r\n\r\n{value}'.encode())

    _field("prompt", prompt)
    _field("aspect_ratio", _IDEOGRAM_ASPECT.get(size, "2x3"))
    _field("rendering_speed", "DEFAULT")
    parts.append(f"--{boundary}--".encode())
    body = b"\r\n".join(parts)
    req = urllib.request.Request(
        "https://api.ideogram.ai/v1/ideogram-v3/generate", data=body, method="POST",
        headers={"Api-Key": key,
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    url = (result.get("data") or [{}])[0].get("url")
    if not url:
        raise ImageGenError(f"Ideogram response had no image url: {str(result)[:200]}")
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def _fit_to_size(raw: bytes, size: str, output_format: str) -> bytes:
    """Cover-fit provider output to the exact requested WxH so gemini/ideogram honor
    the same size contract gpt-image-1 does. (Providers emit their own native size.)"""
    import io
    from PIL import Image, ImageOps
    w, h = (int(x) for x in size.split("x"))
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.size != (w, h):
        im = ImageOps.fit(im, (w, h), method=Image.LANCZOS)
    buf = io.BytesIO()
    if output_format.lower() == "png":
        im.save(buf, "PNG")
    else:
        im.save(buf, "JPEG", quality=95)
    return buf.getvalue()


def _write(out_path: str | Path, raw: bytes) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(raw)
    return out_path


def generate_image(
    prompt: str,
    out_path: str | Path,
    size: str = PORTRAIT,
    quality: str = "high",
    output_format: str = "jpeg",
    background: str | None = None,
    retries: int = 3,
    timeout: int = 180,
    engine: str | None = None,
) -> Path:
    """Text -> image. Writes to out_path and returns it. Raises ImageGenError on failure.

    Pass background="transparent" (with output_format="png" or "webp") for stickers /
    cut-out assets that must drop onto any page without a white box behind them.
    engine selects the provider (default IMAGE_ENGINE env, else "openai").
    """
    if size not in _VALID_SIZES:
        raise ImageGenError(f"invalid size {size!r}; use one of {sorted(_VALID_SIZES)}")
    eng = _engine(engine)
    if eng not in _OPENAI_COMPATIBLE_ENGINES:
        if background == "transparent":
            raise ImageGenError(
                f"engine={eng!r} does not support transparent background — use "
                "engine='openai' for cut-out/sticker assets")
        if eng == "gemini":
            raw = _gemini_generate_bytes(prompt)
        elif eng == "ideogram":
            raw = _ideogram_generate_bytes(prompt, size)
        else:
            raise ImageGenError(f"unknown IMAGE_ENGINE {eng!r} (expected openai/gpt-image-2/gemini/ideogram)")
        return _write(out_path, _fit_to_size(raw, size, output_format))
    if eng == "gpt-image-2" and background == "transparent":
        raise ImageGenError(
            "engine='gpt-image-2' does not support transparent background — use "
            "engine='openai' (gpt-image-1) for cut-out/sticker assets")
    if background == "transparent" and output_format not in ("png", "webp"):
        raise ImageGenError("transparent background requires output_format='png' or 'webp'")
    payload = {
        "model": _openai_model_for(eng),
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": output_format,
        "n": 1,
    }
    if background:
        payload["background"] = background
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_api_key()}"}
    result = _post(_GEN_URL, body, headers, retries, timeout)
    img = _extract_bytes(result)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img)
    return out_path


def edit_image(
    prompt: str,
    image_paths: list[str | Path],
    out_path: str | Path,
    size: str = PORTRAIT,
    quality: str = "high",
    input_fidelity: str | None = None,
    retries: int = 3,
    timeout: int = 180,
    engine: str | None = None,
) -> Path:
    """Image(s)+prompt -> image (the empty-room / single-element-change workflow).

    Pass input_fidelity="high" to preserve the input composition while changing one
    element (per the gpt-image-1 notes in CLAUDE.md).
    engine selects the provider (default IMAGE_ENGINE env, else "openai"). Ideogram
    is generate-only, so engine='ideogram' on an edit raises a clear error.
    """
    if size not in _VALID_SIZES:
        raise ImageGenError(f"invalid size {size!r}; use one of {sorted(_VALID_SIZES)}")
    eng = _engine(engine)
    if eng not in _OPENAI_COMPATIBLE_ENGINES:
        if eng == "gemini":
            raw = _gemini_edit_bytes(prompt, list(image_paths))
            return _write(out_path, _fit_to_size(raw, size, "jpeg"))
        if eng == "ideogram":
            raise ImageGenError(
                "engine='ideogram' is generate-only (no reference-image edit) — "
                "use 'gemini' or 'openai' for edits")
        raise ImageGenError(f"unknown IMAGE_ENGINE {eng!r} (expected openai/gpt-image-2/gemini/ideogram)")

    boundary = "----imggen" + os.urandom(8).hex()
    parts: list[bytes] = []

    def _field(name: str, value: str):
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}'.encode()
        )

    _field("model", _openai_model_for(eng))
    _field("prompt", prompt)
    _field("size", size)
    _field("quality", quality)
    # gpt-image-2 processes every input at high fidelity automatically and doesn't
    # accept input_fidelity as a parameter — omit it for that engine even if passed.
    if input_fidelity and eng != "gpt-image-2":
        _field("input_fidelity", input_fidelity)

    for p in image_paths:
        p = Path(p)
        data = p.read_bytes()
        ext = p.suffix.lower().lstrip(".") or "png"
        mime = "image/png" if ext == "png" else "image/jpeg"
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; '
            f'filename="{p.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode() + data
        )

    parts.append(f"--{boundary}--".encode())
    body = b"\r\n".join(parts)
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {_api_key()}",
    }
    result = _post(_EDIT_URL, body, headers, retries, timeout)
    img = _extract_bytes(result)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img)
    return out_path


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Generate one image with the shared helper")
    ap.add_argument("prompt")
    ap.add_argument("out")
    ap.add_argument("--size", default=PORTRAIT, choices=sorted(_VALID_SIZES))
    ap.add_argument("--quality", default="high")
    args = ap.parse_args()
    path = generate_image(args.prompt, args.out, size=args.size, quality=args.quality)
    print(f"Saved {path}")
