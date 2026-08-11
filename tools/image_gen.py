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
import io
import json
import os
import re
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


def _get_bytes(url: str, retries: int, timeout: int) -> bytes:
    """Same retry/backoff policy as _post(), for a plain GET that needs raw
    bytes back rather than parsed JSON (e.g. downloading a provider's
    resulting image from a URL it handed back). Added 2026-07-19 alongside
    _ideogram_generate_bytes()'s hardening -- previously that function's own
    image-download step was a bare urlopen() with no retry at all."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode()[:200]
            except Exception:
                pass
            last_err = ImageGenError(f"HTTP {e.code}: {detail}")
            if e.code != 429 and 400 <= e.code < 500:
                raise last_err
        except Exception as e:  # noqa: BLE001 — network/timeouts are all retryable
            last_err = e
        if attempt < retries - 1:
            wait = 2 ** (attempt + 1)
            print(f"    image_gen download retry {attempt + 1}/{retries - 1} in {wait}s: {last_err}")
            time.sleep(wait)
    raise ImageGenError(f"image download failed after {retries} attempts: {last_err}")


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
#   "grok"       — xAI Grok Imagine (grok-imagine-image-quality), added 2026-08-05.
#                  Supports both generate and edit (up to 3 reference images per
#                  xAI's docs, though only the first is actually wired here until
#                  the multi-image request shape is confirmed against a real
#                  response). Transparent-background support is NOT confirmed
#                  against xAI's docs — do not use for stickers/cut-outs until
#                  verified; use "openai" for those. UNPROVEN end-to-end (no
#                  XAI_API_KEY in this dev sandbox; the real key lives on
#                  Railway) — same "confirm on first real key" discipline as
#                  Ideogram had before its own first live call.
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


def gemini_key_available() -> bool:
    """Non-raising check for _gemini_key() -- lets a caller decide whether to run
    a Gemini-backed verification pass (e.g. verify_original_art()) at all, rather
    than entering goal_loop.run_until_goal() and having a missing key masquerade
    as an ordinary verify failure. run_until_goal() has no distinct exception type
    for "config problem" vs "the image is actually bad" (see goal_loop.py) -- a
    missing key there gets folded into `issues` as "verification error: ...",
    which then gets fed back into the NEXT generation attempt as a "fix this"
    correction the model can't act on, burning real generation calls on a QA gate
    that can never pass, before silently shipping the unverified image anyway."""
    try:
        _gemini_key()
        return True
    except ImageGenError:
        return False


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


def _gemini_call_with_retry(fn, retries: int = 4, base_delay: int = 2):
    """Run a google-genai SDK call with retry/backoff on transient failures.

    The google-genai SDK does NOT retry internally, and its image endpoint returns
    a transient `500 INTERNAL` (and occasional 503/network drops) often enough that
    a single unretried call is unreliable — observed 2026-07-16 failing both the
    dashboard listing-photo tool and batch sticker generation on the first hit.
    Mirrors the OpenAI `_post()` policy: retry 5xx / 429 / network errors with
    exponential backoff, fail fast on other 4xx (bad key, invalid request — those
    won't self-heal)."""
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "code", None)
            if not isinstance(code, int):
                code = getattr(e, "status_code", None)
            # Client errors (except 429 rate-limit) won't fix themselves — fail fast.
            if isinstance(code, int) and 400 <= code < 500 and code != 429:
                raise
            last_err = e
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt)  # 2s, 4s, 8s
                print(f"    gemini retry {attempt + 1}/{retries - 1} in {wait}s: {e}")
                time.sleep(wait)
    raise ImageGenError(f"gemini call failed after {retries} attempts: {last_err}")


def _gemini_generate_bytes(prompt: str, model: str | None = None) -> bytes:
    from google import genai
    client = genai.Client(api_key=_gemini_key())
    resp = _gemini_call_with_retry(lambda: client.models.generate_content(
        model=model or _GEMINI_IMAGE_MODEL, contents=[prompt]))
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
    resp = _gemini_call_with_retry(lambda: client.models.generate_content(
        model=model or _GEMINI_IMAGE_MODEL, contents=contents))
    return _gemini_bytes_from_resp(resp)


# ── Gemini text/vision helpers — text extraction + render verification for
# tools/listing_photo_pipeline.py's generate_verified_photo(). Added 2026-07-14:
# that pipeline's extract_text()/verify_render() were hardcoded to OpenAI's GPT
# vision models regardless of which engine generated the image, so picking
# engine="gemini" still hard-required a funded OpenAI account for those two
# steps — an OpenAI billing/quota outage blocked Gemini-engine generation too.
# These give the pipeline a fully Gemini-only path. _GEMINI_TEXT_MODEL is a
# plain text/vision model (NOT _GEMINI_IMAGE_MODEL, which is tuned for image
# OUTPUT) — same client/key plumbing as generate_image()'s gemini path, and the
# same `resp.text` response shape already proven in tools/video_understanding.py.
_GEMINI_TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")


def gemini_extract_text(design_path) -> str:
    """Gemini equivalent of listing_photo_pipeline.extract_text() — every piece of
    text on a design, read by a vision model once. Same task, same output shape
    (a plain string), different provider."""
    from google import genai
    from google.genai import types
    p = Path(design_path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    client = genai.Client(api_key=_gemini_key())
    resp = _gemini_call_with_retry(lambda: client.models.generate_content(
        model=_GEMINI_TEXT_MODEL,
        contents=[
            "List every piece of text visible in this design, exactly as written, "
            "character for character, one item per line. Output only the text "
            "items, nothing else.",
            types.Part.from_bytes(data=p.read_bytes(), mime_type=mime),
        ],
    ))
    return (resp.text or "").strip()


def describe_reference_style(image_path) -> str:
    """One vision call that turns a Scott-uploaded inspiration/reference photo
    into plain-language style notes (palette, mood, motifs, composition) that
    can be prepended to a text-to-image prompt as guidance -- NOT a literal
    reproduction instruction. Added 2026-07-30 for the Reference Photos
    library (main.py's /api/reference-images/*), which previously stored
    uploads but never fed them into any generation call. Same client/model
    plumbing as gemini_extract_text() above."""
    from google import genai
    from google.genai import types
    p = Path(image_path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    client = genai.Client(api_key=_gemini_key())
    resp = _gemini_call_with_retry(lambda: client.models.generate_content(
        model=_GEMINI_TEXT_MODEL,
        contents=[
            "This is a style/inspiration reference photo for a product design. "
            "Describe, in 2-4 short sentences, the visual style a designer should "
            "borrow from it: dominant colors (as plain color names, not hex), "
            "overall mood/aesthetic, recurring motifs or subject matter, and "
            "composition/layout. Do not describe it as a literal scene to "
            "reproduce -- describe it as style guidance for a NEW, different "
            "design. Output only the description, nothing else.",
            types.Part.from_bytes(data=p.read_bytes(), mime_type=mime),
        ],
    ))
    return (resp.text or "").strip()


def verify_original_art(image_path, prompt: str) -> dict:
    """QA check for a brand-new AI-generated artwork (planner cover, wall art
    master, coloring page) against the TEXT PROMPT it was generated from --
    there is no source design file to compare against here, unlike
    gemini_verify_render()/verify_render() below, which check a rendered photo
    against a real product file. Added 2026-07-30 as the first step of routing
    original product-art generation through the same self-verifying pattern
    already proven for listing photos (tools/listing_photo_pipeline.py),
    instead of a single-shot generate-and-hope call.

    Catches the failure modes that slip through completely unchecked today:
      1. Garbled/gibberish text baked into the image (image models routinely
         invent nonsense glyphs even when the prompt says "no text")
      2. A broken multi-panel/collage grid instead of one cohesive artwork
      3. Wrong subject matter entirely (the model ignored the prompt)
    Returns {"pass": bool, "issues": [str, ...]}."""
    from google import genai
    from google.genai import types
    p = Path(image_path)
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    client = genai.Client(api_key=_gemini_key())
    check_prompt = (
        "You are a QA inspector for AI-generated product art (wall art prints, "
        "planner covers, coloring pages). This image was generated from the "
        f"following prompt:\n\n---\n{prompt}\n---\n\n"
        "Check ONLY for these THREE failure types -- ignore everything else "
        "(artistic interpretation, exact color shade, composition choices are "
        "all fine and expected to vary from the prompt):\n"
        "1. GARBLED TEXT: any word, letter cluster, or number baked into the "
        "image that is nonsensical, misspelled gibberish, or malformed "
        "(image models frequently invent fake text-like scribbles). If the "
        "prompt did not ask for specific text, ANY text-like marks that "
        "aren't clean readable words also count as a fail.\n"
        "2. BROKEN COMPOSITION: the image is split into multiple disconnected "
        "panels/tiles/frames like a broken collage grid, instead of one "
        "single cohesive piece of art.\n"
        "3. WRONG SUBJECT: the image's subject matter has nothing to do with "
        "what the prompt described (e.g. prompt asked for a sunflower and the "
        "image shows a car).\n\n"
        "Respond with EXACTLY this format, nothing else:\n"
        "PASS or FAIL\n"
        "If FAIL, one line per issue starting with '- '."
    )
    resp = _gemini_call_with_retry(lambda: client.models.generate_content(
        model=_GEMINI_TEXT_MODEL,
        contents=[check_prompt, types.Part.from_bytes(data=p.read_bytes(), mime_type=mime)],
    ))
    text = (resp.text or "").strip()
    passed = text.upper().startswith("PASS")
    issues = [line.lstrip("- ").strip() for line in text.splitlines()[1:] if line.strip().startswith("-")]
    if not passed and not issues:
        issues = [text[:200] or "verification returned no usable response"]
    return {"pass": passed, "issues": issues}


def gemini_verify_render(design_paths: list, render, physics_desc: str = "",
                         facts: str = "") -> dict:
    """Gemini equivalent of listing_photo_pipeline.verify_render(). Uses the exact
    same prompt text as the OpenAI version — verification strictness must not
    change just because a different provider is doing the looking — built on
    Gemini's vision model instead of GPT-4o. `render` is an in-memory PIL Image
    (not a file on disk), downsized the same way _b64() downsizes source images
    (768px thumbnail, JPEG q88) for comparable detail/cost to the OpenAI path.
    Returns the same {"pass": bool, "issues": [...]} shape."""
    from google import genai
    from google.genai import types

    prompt = (
        "You are a product-photo QA inspector. The FIRST image(s) are the "
        "real product design file(s) a customer downloads. The LAST image is a "
        "marketing lifestyle photo that must show the design faithfully.\n\n"
        f"The physical product is: {physics_desc}\n"
        "Appearance traits described there (e.g. fine matte surface grain, panel "
        "thickness, side edges, metallic lid) are INTENDED and are NOT defects.\n\n"
        "FAIL only on MATERIAL fidelity errors:\n"
        "1. TEXT: any word/number that is wrong, garbled, missing, or invented "
        "(character-level check on dates and small print)\n"
        "2. COLORS: a region changed to a different hue category (e.g. cream became "
        "navy, green became blue). Lighting tint, white balance, mild exposure or "
        "saturation shifts from scene lighting are NORMAL and pass.\n"
        "3. ELEMENTS: missing, added, or redesigned design elements (borders, stars, "
        "icons, edge details)\n"
        f"4. SHAPE — use these measured ground-truth facts, do not judge by eye:\n"
        f"{facts}\n"
        "Fail SHAPE only if the photo's product face clearly contradicts those "
        "facts (e.g. facts say square canvas but the panel is cut into a circle "
        "or the background color region is absent).\n"
        "5. SURFACE: individual letters/shapes sticking UP out of the face as 3D "
        "embossing. The panel itself having thickness, a drop shadow, or the "
        "described surface grain is NORMAL and passes.\n\n"
        "Perspective, viewing angle, scale, lighting, shadows, and scene context "
        "are NEVER issues.\n"
        "IMPORTANT: only report an issue if you can see it CLEARLY and are confident. "
        "If you are uncertain whether something is an issue, do NOT report it — "
        "uncertain observations are not defects.\n\n"
        "SEPARATELY (does NOT affect pass/fail — a fidelity-perfect render can "
        "still get realism notes, and vice versa): does this look like a "
        "genuine, professional product photograph rather than an obviously "
        "AI-generated or synthetic image? Note (do not fail on) unnaturally "
        "plastic/waxy surfaces, a complete absence of any grain or texture, "
        "shadows inconsistent with the stated light direction, or an "
        "unnaturally flat/lifeless catalog look with zero atmosphere. Only "
        "note something you are genuinely confident about.\n"
        'Respond with ONLY JSON: {"pass": true/false, "issues": ["specific issue", ...], '
        '"realism_issues": ["specific concern", ...]} (realism_issues: empty list if none).'
    )
    contents: list = [prompt]
    for dp in design_paths:
        p = Path(dp)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        contents.append(types.Part.from_bytes(data=p.read_bytes(), mime_type=mime))
    render_copy = render.copy()
    render_copy.thumbnail((768, 768))
    buf = io.BytesIO()
    render_copy.convert("RGB").save(buf, "JPEG", quality=88)
    contents.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))

    client = genai.Client(api_key=_gemini_key())
    resp = _gemini_call_with_retry(
        lambda: client.models.generate_content(model=_GEMINI_TEXT_MODEL, contents=contents))
    raw = (resp.text or "").strip()
    raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.M).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"pass": False, "issues": [f"verifier returned unparseable: {raw[:200]}"]}


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
    key, same discipline as the Veo path was before its proof.

    2026-07-19: previously two bare urlopen() calls with no try/except at all --
    every other engine in this module (OpenAI via _post(), Gemini via
    _gemini_call_with_retry()) retries transient failures with backoff; a plain
    network blip here failed the whole generation outright instead. Now goes
    through the same _post()/_get_bytes() retry policy as everything else."""
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
    result = _post(
        "https://api.ideogram.ai/v1/ideogram-v3/generate", body,
        headers={"Api-Key": key, "Content-Type": f"multipart/form-data; boundary={boundary}"},
        retries=3, timeout=120,
    )
    url = (result.get("data") or [{}])[0].get("url")
    if not url:
        raise ImageGenError(f"Ideogram response had no image url: {str(result)[:200]}")
    return _get_bytes(url, retries=3, timeout=120)


def _grok_key() -> str:
    key = os.getenv("XAI_API_KEY", "")
    if not key and _ENV_PATH.exists():
        with open(_ENV_PATH) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("XAI_API_KEY=") and "=" in line:
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        # 2026-08-05/2026-08-11: the real xAI key is set on Railway, but under
        # the variable name "Grok api" (with a space) instead of XAI_API_KEY
        # -- confirmed live (this codebase's every other reference to this
        # bug documents it as a known, still-unfixed Railway naming mismatch,
        # not a missing key). Check it as a fallback so a real, already-
        # provisioned key isn't silently unusable while the rename is
        # pending -- this reads an existing variable, never renames/writes
        # anything in Railway itself.
        key = os.getenv("Grok api", "")
    if not key:
        raise ImageGenError(
            "XAI_API_KEY not set (needed for engine='grok') -- also checked the "
            "known-misnamed 'Grok api' Railway variable, not set either")
    return key


_GROK_IMAGE_URL = "https://api.x.ai/v1/images/generations"
_GROK_EDIT_URL = "https://api.x.ai/v1/images/edits"
_GROK_IMAGE_MODEL = os.getenv("GROK_IMAGE_MODEL", "grok-imagine-image-quality")


def _grok_generate_bytes(prompt: str) -> bytes:
    """xAI Grok Imagine text->image (2026-08-05). UNPROVEN against a real key at
    write time (Scott added XAI_API_KEY to Railway's production env, not this
    sandbox) -- written to xAI's documented API (confirmed OpenAI-response-shape
    compatible: {"data": [{"b64_json": ...}]}, same as _extract_bytes() already
    handles), same discipline _ideogram_generate_bytes() used before its own
    first real key: confirm the exact response on first live use, fix here if
    it disagrees. No confirmed "size"/aspect-ratio request field in xAI's docs
    (unlike OpenAI's engines) -- like gemini/ideogram, request the model's
    native output and cover-fit to the requested size afterward via
    _fit_to_size() rather than guessing a field name that might reject the
    whole request."""
    payload = {"model": _GROK_IMAGE_MODEL, "prompt": prompt, "response_format": "b64_json"}
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_grok_key()}"}
    result = _post(_GROK_IMAGE_URL, body, headers, retries=3, timeout=120)
    return _extract_bytes(result)


def _grok_edit_bytes(prompt: str, image_paths: list) -> bytes:
    """xAI Grok Imagine image edit (2026-08-05). UNPROVEN, same caveat as
    _grok_generate_bytes() above. xAI's edit endpoint takes the reference
    image as a JSON object (confirmed from xAI's own docs example), NOT a
    multipart file upload like OpenAI's images/edits -- `{"image": {"url":
    <public-url-or-base64-data-uri>, "type": "image_url"}}`. Frank's inputs
    are always local files, never public URLs, so this always sends a
    base64 data URI. xAI's docs describe support for up to 3 source images
    per request but the multi-image request shape isn't documented in
    enough detail to be confident here -- only the first image_path is
    sent until that's confirmed against a real response; every OTHER
    engine in this module (openai/gemini) does support Frank's real
    multi-image edit calls, so engine='grok' should only be picked for
    single-reference-image edits until this is verified and extended."""
    if len(image_paths) > 1:
        print(f"    grok edit: {len(image_paths)} images given, only the first is sent "
              f"(multi-image request shape unconfirmed for this engine)")
    p = Path(image_paths[0])
    data = p.read_bytes()
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    data_uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    payload = {
        "model": _GROK_IMAGE_MODEL,
        "prompt": prompt,
        "image": {"url": data_uri, "type": "image_url"},
        "response_format": "b64_json",
    }
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_grok_key()}"}
    result = _post(_GROK_EDIT_URL, body, headers, retries=3, timeout=120)
    return _extract_bytes(result)


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
        elif eng == "grok":
            raw = _grok_generate_bytes(prompt)
        else:
            raise ImageGenError(f"unknown IMAGE_ENGINE {eng!r} (expected openai/gpt-image-2/gemini/ideogram/grok)")
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
        if eng == "grok":
            raw = _grok_edit_bytes(prompt, list(image_paths))
            return _write(out_path, _fit_to_size(raw, size, "jpeg"))
        raise ImageGenError(f"unknown IMAGE_ENGINE {eng!r} (expected openai/gpt-image-2/gemini/ideogram/grok)")

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
