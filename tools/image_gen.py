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


def generate_image(
    prompt: str,
    out_path: str | Path,
    size: str = PORTRAIT,
    quality: str = "high",
    output_format: str = "jpeg",
    retries: int = 3,
    timeout: int = 180,
) -> Path:
    """Text -> image. Writes to out_path and returns it. Raises ImageGenError on failure."""
    if size not in _VALID_SIZES:
        raise ImageGenError(f"invalid size {size!r}; use one of {sorted(_VALID_SIZES)}")
    body = json.dumps({
        "model": _MODEL,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "output_format": output_format,
        "n": 1,
    }).encode()
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
) -> Path:
    """Image(s)+prompt -> image (the empty-room / single-element-change workflow).

    Pass input_fidelity="high" to preserve the input composition while changing one
    element (per the gpt-image-1 notes in CLAUDE.md).
    """
    if size not in _VALID_SIZES:
        raise ImageGenError(f"invalid size {size!r}; use one of {sorted(_VALID_SIZES)}")

    boundary = "----imggen" + os.urandom(8).hex()
    parts: list[bytes] = []

    def _field(name: str, value: str):
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}'.encode()
        )

    _field("model", _MODEL)
    _field("prompt", prompt)
    _field("size", size)
    _field("quality", quality)
    if input_fidelity:
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
