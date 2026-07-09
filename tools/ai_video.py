"""AI video generation — image-to-video, multi-engine.

Public entrypoint: generate_ai_video(...). It dispatches to a provider engine:
  - "sora"  → OpenAI Sora-2 (WORKS TODAY, but the Sora API shuts down 2026-09-24)
  - "veo"   → Google Veo 3.1 (recommended migration target; see MIGRATION note)

Engine is chosen by the `engine=` argument, else the AI_VIDEO_ENGINE env var, else
"sora" (the only engine proven end-to-end so far). Callers don't change: main.py's
/api/studio/generate keeps calling generate_ai_video() with the same signature.

── SORA (OpenAI) — proven ─────────────────────────────────────────────────────
Async JOB api (not a sync call like images.generate):
    video = client.videos.create(model="sora-2", prompt=..., input_reference=<img>,
                                 seconds="4", size="720x1280")   # status: queued
    # poll client.videos.retrieve(video.id) until status == "completed"
    content = client.videos.download_content(video.id, variant="video")
Constraints (verified against openai SDK 2.41.1): model sora-2/sora-2-pro; seconds
"4"/"8"/"12"; size 720x1280/1280x720/1024x1792/1792x1024 (no 1:1); ONE input_reference
image that must match the output size (so we center-crop the product photo to size).

── VEO 3.1 (Google) — MIGRATION TARGET, NOT YET PROVEN ────────────────────────
Requires: `pip install google-genai` AND a GEMINI_API_KEY (neither present in this
container yet). The code below follows the documented google-genai video API
(models.generate_videos → poll operation → download the file), but it has NOT been
run end-to-end against the live API. Before switching AI_VIDEO_ENGINE=veo in
production, verify one real generation on a real product file (decode the mp4,
confirm resolution/frames) — the same bar the Sora path was held to. Exact model id,
aspect-ratio and duration params must be confirmed against the installed SDK version
at that time (Veo model strings and config fields move fast).
"""
import os
import time
import uuid
from pathlib import Path

from PIL import Image, ImageOps

OUTPUT_DIR = Path("data/social/videos")
SORA_MODEL = "sora-2"

# aspect_ratio → exact Sora output size. Sora has NO 1:1 size; 1:1 and any
# unknown ratio fall back to portrait 720x1280 (the dominant social/Reels format).
ASPECT_SIZES = {
    "9:16": "720x1280",
    "16:9": "1280x720",
    "9:16_hd": "1024x1792",
    "16:9_hd": "1792x1024",
}
_DEFAULT_SIZE = "720x1280"
_VALID_SECONDS = ("4", "8", "12")


def _clamp_seconds(duration) -> str:
    """Map an arbitrary requested duration to the largest valid Sora length
    that does not exceed it (floor 4, cap 12). e.g. 10→8, 5→4, 20→12."""
    try:
        d = int(duration)
    except (TypeError, ValueError):
        return "4"
    allowed = [4, 8, 12]
    pick = 4
    for a in allowed:
        if a <= d:
            pick = a
    return str(pick)


def _prep_reference(image_path: Path, size: str) -> Path:
    """Center-crop (cover) + resize the product photo to EXACTLY the target
    size Sora requires, and write it to a temp JPEG. Returns the temp path."""
    w, h = (int(x) for x in size.split("x"))
    img = Image.open(image_path).convert("RGB")
    fitted = ImageOps.fit(img, (w, h), method=Image.LANCZOS)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ref_path = OUTPUT_DIR / f"_ref_{uuid.uuid4().hex[:8]}.jpg"
    fitted.save(ref_path, "JPEG", quality=92)
    return ref_path


def generate_ai_video(
    image_paths,
    scene_prompt: str,
    api_key: str,
    duration: int = 4,
    aspect_ratio: str = "9:16",
    listing_id: str = "studio",
    max_wait: float = 240.0,
    poll_interval: float = 4.0,
    engine: str = None,
) -> Path:
    """Generate an image-to-video clip via the selected provider engine.

    Args:
        image_paths: list of product photo Paths — the FIRST is the reference image.
        scene_prompt: text description of the desired motion/scene.
        api_key: OpenAI API key (used by the "sora" engine only; the "veo" engine
            reads GEMINI_API_KEY from the environment instead).
        duration: requested seconds (clamped per engine).
        aspect_ratio: "9:16" / "16:9" (+ "_hd" variants for Sora).
        listing_id: used to name the output file.
        max_wait / poll_interval: job polling controls.
        engine: "sora" | "veo". Defaults to AI_VIDEO_ENGINE env, else "sora".

    Returns:
        Path to the saved MP4 file.
    """
    engine = (engine or os.getenv("AI_VIDEO_ENGINE", "sora")).lower().strip()
    if not image_paths:
        raise RuntimeError("generate_ai_video requires at least one product image.")
    if engine == "veo":
        return _generate_veo(image_paths, scene_prompt, duration, aspect_ratio,
                             listing_id, max_wait, poll_interval)
    if engine == "sora":
        return _generate_sora(image_paths, scene_prompt, api_key, duration,
                              aspect_ratio, listing_id, max_wait, poll_interval)
    raise ValueError(f"unknown AI video engine {engine!r} (expected 'sora' or 'veo')")


def _generate_sora(
    image_paths,
    scene_prompt: str,
    api_key: str,
    duration: int = 4,
    aspect_ratio: str = "9:16",
    listing_id: str = "studio",
    max_wait: float = 240.0,
    poll_interval: float = 4.0,
) -> Path:
    """Generate a video with OpenAI Sora-2 image-to-video. PROVEN end-to-end.

    NOTE: OpenAI's Sora API shuts down 2026-09-24. Migrate to the "veo" engine
    before then. Until then this remains the default working path.
    """
    if not api_key:
        raise RuntimeError("OPENAI_KEY is not set — cannot call the Sora API.")
    if not image_paths:
        raise RuntimeError("generate_ai_video requires at least one product image.")

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    size = ASPECT_SIZES.get(aspect_ratio, _DEFAULT_SIZE)
    seconds = _clamp_seconds(duration)

    ref_path = _prep_reference(Path(image_paths[0]), size)

    try:
        with open(ref_path, "rb") as fh:
            video = client.videos.create(
                model=SORA_MODEL,
                prompt=scene_prompt,
                input_reference=("reference.jpg", fh, "image/jpeg"),
                seconds=seconds,
                size=size,
            )
        print(f"  → Sora job {video.id} created (status={video.status}, "
              f"{size}, {seconds}s)", flush=True)

        # Poll until terminal state or timeout.
        start = time.time()
        while video.status in ("queued", "in_progress"):
            if time.time() - start > max_wait:
                raise TimeoutError(
                    f"Sora job {video.id} still {video.status} after {max_wait:.0f}s"
                )
            time.sleep(poll_interval)
            video = client.videos.retrieve(video.id)
            prog = getattr(video, "progress", None)
            print(f"  … Sora job {video.id}: {video.status}"
                  + (f" ({prog}%)" if prog is not None else ""), flush=True)

        if video.status != "completed":
            err = getattr(video, "error", None)
            detail = getattr(err, "message", None) or err or video.status
            raise RuntimeError(f"Sora job {video.id} did not complete: {detail}")

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = OUTPUT_DIR / f"{listing_id}_ai_scene_{uuid.uuid4().hex[:8]}.mp4"
        content = client.videos.download_content(video.id, variant="video")
        content.write_to_file(out_path)
    finally:
        Path(ref_path).unlink(missing_ok=True)

    sz = out_path.stat().st_size if out_path.exists() else 0
    if sz < 10_000:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(f"Sora video output is only {sz} bytes — generation failed")

    print(f"  ✓ AI video saved: {out_path} ({sz // 1024}KB)", flush=True)
    return out_path


# ── Veo 3.1 engine (Google) — migration target, UNPROVEN in this container ─────
_VEO_ASPECTS = {"9:16": "9:16", "16:9": "16:9", "9:16_hd": "9:16", "16:9_hd": "16:9"}
_VEO_DEFAULT_ASPECT = "9:16"


def _clamp_veo_seconds(duration) -> int:
    """Veo accepts a small set of durations; clamp to [4, 8]. (Confirm the exact
    allowed set against the installed google-genai version before production.)"""
    try:
        d = int(duration)
    except (TypeError, ValueError):
        return 4
    return max(4, min(8, d))


def _generate_veo(image_paths, scene_prompt, duration, aspect_ratio, listing_id,
                  max_wait, poll_interval) -> Path:
    """Generate a video with Google Veo 3.1 image-to-video.

    ⚠️ UNPROVEN in this environment — needs `pip install google-genai` and a
    GEMINI_API_KEY. Written to the documented google-genai video API; before
    enabling AI_VIDEO_ENGINE=veo in production, run one real generation on a real
    product file and verify the mp4 (resolution + frames), exactly as the Sora
    path was proven. Model id / config fields may need updating to the live SDK.
    """
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "Veo engine selected but no GEMINI_API_KEY (or GOOGLE_API_KEY) is set — "
            "set it in the deploy env, or use engine='sora'."
        )
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            f"Veo engine needs the google-genai SDK: `pip install google-genai` ({exc})"
        )

    model = os.getenv("VEO_MODEL", "veo-3.1-fast-generate-preview")
    aspect = _VEO_ASPECTS.get(aspect_ratio, _VEO_DEFAULT_ASPECT)
    seconds = _clamp_veo_seconds(duration)

    ref = Path(image_paths[0])
    img_bytes = ref.read_bytes()
    mime = "image/png" if ref.suffix.lower() == ".png" else "image/jpeg"

    client = genai.Client(api_key=key)
    operation = client.models.generate_videos(
        model=model,
        prompt=scene_prompt,
        image=types.Image(image_bytes=img_bytes, mime_type=mime),
        config=types.GenerateVideosConfig(
            aspect_ratio=aspect,
            number_of_videos=1,
            duration_seconds=seconds,
        ),
    )
    print(f"  → Veo job started (model={model}, {aspect}, {seconds}s)", flush=True)

    start = time.time()
    while not operation.done:
        if time.time() - start > max_wait:
            raise TimeoutError(f"Veo job still running after {max_wait:.0f}s")
        time.sleep(poll_interval)
        operation = client.operations.get(operation)
        print("  … Veo job in progress", flush=True)

    resp = getattr(operation, "response", None)
    vids = getattr(resp, "generated_videos", None) if resp else None
    if not vids:
        err = getattr(operation, "error", None)
        raise RuntimeError(f"Veo job produced no video: {err or 'unknown error'}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{listing_id}_ai_scene_{uuid.uuid4().hex[:8]}.mp4"
    video = vids[0].video
    # google-genai 2.10: files.download() RETURNS the mp4 bytes (verified against
    # the installed SDK signature). Some versions also populate video.video_bytes —
    # handle both rather than relying on a .save() that isn't guaranteed to exist.
    data = client.files.download(file=video)
    if isinstance(data, (bytes, bytearray)) and data:
        out_path.write_bytes(data)
    elif getattr(video, "video_bytes", None):
        out_path.write_bytes(video.video_bytes)
    else:
        raise RuntimeError("Veo returned no downloadable video bytes")

    sz = out_path.stat().st_size if out_path.exists() else 0
    if sz < 10_000:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(f"Veo video output is only {sz} bytes — generation failed")
    print(f"  ✓ AI video saved: {out_path} ({sz // 1024}KB)", flush=True)
    return out_path
