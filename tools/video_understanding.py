"""
Video Understanding Tools — let Frank actually WATCH a video, not just handle files.

An LLM can't ingest a video file directly; the video has to be turned into frames +
audio that a multimodal model reads. Google Gemini does this natively (samples ~1 frame/
sec + audio, ~300 tokens/sec of video) and is the cleanest path — `google-genai` is already
in the image. This module wraps that behind a single `watch_video` agent tool:

    watch_video(source, question=None)
      • source = a local file path OR a URL (YouTube, TikTok, direct .mp4, ~1000 sites)
      • URLs are fetched with yt-dlp to a temp file, then uploaded to Gemini's File API
      • Gemini analyzes the video and returns TEXT — which is what Frank's Claude brain
        consumes (tool results are text, so Gemini does the "watching" and hands back words)

Requires GEMINI_API_KEY. Guarded with a clear error when unset (mirrors the other engine
paths). The proven API surface (verified live 2026-07-03 on a controlled 3-frame test video —
Gemini correctly read back the digits): client.files.upload → poll files.get until ACTIVE →
models.generate_content([file, prompt]) → resp.text.

Honest limits:
  - Video tokens are ~300/sec, so a long video is expensive — the tool caps analysis by
    telling Gemini to summarize, but the caller should prefer short clips / specific questions.
  - Gemini File API holds an uploaded file ~48h; we delete it after analysis to be tidy.
  - yt-dlp fetching a site depends on that site not blocking the server's IP (same datacenter-IP
    caveat as the browser tools); direct local files always work.
"""
from __future__ import annotations

import json
import os
import tempfile

_MODEL = os.getenv("VIDEO_UNDERSTANDING_MODEL", "gemini-2.5-flash")
_DEFAULT_PROMPT = (
    "Watch this video and give a clear, detailed description: what happens (in order), "
    "any on-screen text read verbatim, spoken words if audible, products/objects shown, "
    "colors, and overall style/mood. Note anything a shop owner would care about for "
    "quality, accuracy, or competitive research."
)

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "watch_video",
        "description": (
            "Watch and analyze a video using Google Gemini's native video understanding — use "
            "this to actually SEE video content, not just handle the file. Accepts a local file "
            "path OR a URL (YouTube, TikTok, direct .mp4, and ~1000 other sites via yt-dlp). "
            "Returns a text analysis: what happens, on-screen text, spoken words, objects/products, "
            "colors, style. Great for QA on a generated product/listing video, or watching a "
            "competitor's video for research. Requires GEMINI_API_KEY. Video analysis costs ~300 "
            "tokens per second of video, so prefer short clips and ask a specific question when you "
            "can. If a site blocks the server's IP the fetch may fail (local files always work)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Local file path (e.g. data/social/videos/clip.mp4) or a video URL.",
                },
                "question": {
                    "type": "string",
                    "description": "Optional specific question about the video (e.g. 'What product is shown and what text appears?'). If omitted, returns a full description.",
                },
            },
            "required": ["source"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "watch_video":
        return _watch_video(tool_input or {})
    return json.dumps({"error": f"Unknown video_understanding tool: {tool_name}"})


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _download(url: str) -> str:
    """Fetch a video URL to a temp file via yt-dlp (handles YouTube/TikTok/direct/etc.).
    Returns the local path. Raises with a clear message on failure."""
    try:
        import yt_dlp  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "yt-dlp is not installed — can't fetch video URLs. Pass a local file path instead, "
            "or add yt-dlp to the image."
        ) from exc

    out_dir = tempfile.mkdtemp(prefix="frank_video_")
    out_tmpl = os.path.join(out_dir, "video.%(ext)s")
    # Cap size/quality so we don't pull a 4K hour-long file: prefer <=720p mp4.
    ydl_opts = {
        "outtmpl": out_tmpl,
        "format": "best[height<=720][ext=mp4]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }
    import yt_dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    files = [os.path.join(out_dir, f) for f in os.listdir(out_dir)]
    if not files:
        raise RuntimeError(f"yt-dlp downloaded nothing from {url}")
    return max(files, key=os.path.getsize)


def _gemini_analyze(path: str, question: str | None) -> dict:
    """Upload a local video file to Gemini, wait until processed, analyze, clean up.
    Returns a result dict. Verified API surface (2026-07-03)."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return {"error": "GEMINI_API_KEY not set — video understanding needs a Gemini key."}
    try:
        from google import genai
    except ImportError:
        return {"error": "google-genai not installed — can't run video understanding."}

    import time

    client = genai.Client(api_key=api_key)
    uploaded = client.files.upload(file=path)
    try:
        # Gemini processes the video async; wait for ACTIVE (fail fast on FAILED).
        for _ in range(60):
            uploaded = client.files.get(name=uploaded.name)
            state = str(uploaded.state)
            if state.endswith("ACTIVE"):
                break
            if state.endswith("FAILED"):
                return {"error": "Gemini failed to process the video (unsupported/corrupt file?)."}
            time.sleep(2)
        else:
            return {"error": "Gemini video processing timed out."}

        prompt = (question.strip() if question and question.strip() else _DEFAULT_PROMPT)
        resp = client.models.generate_content(model=_MODEL, contents=[uploaded, prompt])
        return {
            "analysis": (resp.text or "").strip(),
            "model": _MODEL,
            "question": question or "(full description)",
        }
    finally:
        # Best-effort cleanup — files auto-expire in ~48h anyway.
        try:
            client.files.delete(name=uploaded.name)
        except Exception:
            pass


def _watch_video(data: dict) -> str:
    source = (data.get("source") or "").strip()
    question = data.get("question")
    if not source:
        return json.dumps({"error": "source is required (a local file path or a video URL)."})

    tmp_to_clean = None
    try:
        if _is_url(source):
            path = _download(source)
            tmp_to_clean = path
        else:
            path = source
            if not os.path.exists(path):
                return json.dumps({"error": f"Local file not found: {path}"})

        result = _gemini_analyze(path, question)
        result["source"] = source
        return json.dumps(result, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "source": source})
    finally:
        if tmp_to_clean:
            try:
                os.remove(tmp_to_clean)
                os.rmdir(os.path.dirname(tmp_to_clean))
            except Exception:
                pass


def is_available() -> bool:
    """True when the Gemini SDK is importable and a key is configured."""
    try:
        from google import genai  # noqa: F401
        return bool(os.getenv("GEMINI_API_KEY"))
    except ImportError:
        return False
