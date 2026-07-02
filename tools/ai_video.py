"""AI video generation via OpenAI Sora image-to-video (Sora-2 job API).

The Sora video API is an ASYNCHRONOUS JOB api, not a synchronous call like
images.generate. The flow is:

    video = client.videos.create(model="sora-2", prompt=..., input_reference=<img>,
                                 seconds="4", size="720x1280")   # status: queued
    # poll client.videos.retrieve(video.id) until status == "completed"
    content = client.videos.download_content(video.id, variant="video")
    content.write_to_file(out_path)

Hard constraints enforced by the API (verified against openai SDK 2.41.1):
  - model:   only "sora-2" or "sora-2-pro"
  - seconds: only "4", "8", or "12" (strings)
  - size:    only 720x1280, 1280x720, 1024x1792, 1792x1024 (no 1:1)
  - input_reference: ONE image, and it must match the output size exactly, so
    the product photo is center-cropped (cover) and resized to the target size
    before upload.
"""
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
) -> Path:
    """Generate a video with OpenAI Sora-2 image-to-video.

    Args:
        image_paths: list of product photo Paths — the FIRST is used as the
            Sora reference image (Sora accepts a single reference).
        scene_prompt: text description of the desired motion/scene.
        api_key: OpenAI API key (org must be enabled for the Sora video API).
        duration: requested seconds; clamped to 4/8/12.
        aspect_ratio: "9:16", "16:9", "9:16_hd", "16:9_hd" (1:1 → portrait).
        listing_id: used to name the output file.
        max_wait: max seconds to poll the job before giving up.
        poll_interval: seconds between status polls.

    Returns:
        Path to the saved MP4 file.
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
