"""AI video generation via OpenAI Sora image-to-video API."""
import uuid
import base64
import urllib.request
from pathlib import Path

OUTPUT_DIR  = Path("data/social/videos")
SORA_MODEL  = "sora-1.0-turbo"
ASPECT_SIZES = {
    "9:16":  "720x1280",
    "16:9":  "1280x720",
    "1:1":   "1080x1080",
}


def generate_ai_video(
    image_paths,
    scene_prompt: str,
    api_key: str,
    duration: int = 10,
    aspect_ratio: str = "9:16",
    listing_id: str = "studio",
) -> Path:
    """Generate a video using OpenAI Sora image-to-video.

    Args:
        image_paths: list of Path objects pointing to product photos.
        scene_prompt: text description of the desired scene.
        api_key: OpenAI API key.
        duration: length in seconds (default 10).
        aspect_ratio: "9:16", "16:9", or "1:1".
        listing_id: used to name the output file.

    Returns:
        Path to the saved MP4 file.
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    size = ASPECT_SIZES.get(aspect_ratio, "720x1280")

    # Encode product images as base64 data URLs for Sora reference images
    encoded = []
    for p in image_paths[:4]:   # Sora accepts up to 4 reference images
        raw = Path(p).read_bytes()
        b64 = base64.b64encode(raw).decode()
        encoded.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
        })

    def _call(imgs, with_audio):
        kwargs = dict(
            model=SORA_MODEL,
            prompt=scene_prompt,
            size=size,
            duration=duration,
            n=1,
        )
        if imgs:
            kwargs["input_images"] = imgs
        if with_audio:
            kwargs["with_audio"] = True
        return client.videos.generate(**kwargs)

    # Progressive fallback: all images + audio → single image + audio → single image, no audio
    resp = None
    for imgs, audio in [(encoded, True), (encoded[:1], True), (encoded[:1], False)]:
        try:
            resp = _call(imgs, audio)
            break
        except Exception as exc:
            last_exc = exc
    if resp is None:
        raise RuntimeError(f"Sora API failed on all attempts: {last_exc}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{listing_id}_ai_scene_{uuid.uuid4().hex[:8]}.mp4"

    video_url = resp.data[0].url if resp.data else None
    if video_url:
        urllib.request.urlretrieve(video_url, out_path)
    else:
        b64_video = resp.data[0].b64_json if resp.data else None
        if not b64_video:
            raise RuntimeError("Sora returned neither a URL nor base64 video data")
        out_path.write_bytes(base64.b64decode(b64_video))

    sz = out_path.stat().st_size if out_path.exists() else 0
    if sz < 10_000:
        out_path.unlink(missing_ok=True)
        raise RuntimeError(f"Sora video output is only {sz} bytes — generation may have failed")

    print(f"  ✓ AI video saved: {out_path} ({sz // 1024}KB)")
    return out_path
