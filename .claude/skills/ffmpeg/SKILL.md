---
name: ffmpeg
description: "CLI reference for video/audio encoding, transcoding, and inspection with ffmpeg/ffprobe. Use whenever a task involves producing, resizing, compressing, or inspecting a video or audio file for this shop — social video (Instagram/Facebook/TikTok/Pinterest), HyperFrames renders, Ken Burns slideshow output, or extracting audio/thumbnails from an existing file."
---

# ffmpeg — Video/Audio CLI Reference

Developer reference for `ffmpeg`/`ffprobe`. This is a cheat sheet to work
from, not a wrapper to call blindly — always check the *why* against the
actual task (a social Reel has different constraints than a HyperFrames
render).

## Where ffmpeg already runs in this codebase

- `tools/video_generator.py`'s `_render_with_ffmpeg()` pipes raw RGB24
  frames over stdin (`-f rawvideo -pix_fmt rgb24 -r <fps> -i pipe:0`) and
  encodes with `-vcodec libx264 -pix_fmt yuv420p -preset fast -an` — this
  is the Ken Burns pan-zoom slideshow path (`generate_video`).
- `tools/hyperframes_render.py` requires a real `ffmpeg` on `PATH`
  (`shutil.which("ffmpeg")` — `check_hyperframes_available()` reports it
  by name if missing) to mux the HyperFrames headless-Chrome capture into
  a final MP4.
- **Known trap, already solved once — don't re-break it:** `video_
  generator.py` resolves the binary via `imageio_ffmpeg.get_ffmpeg_exe()`
  rather than a bare `"ffmpeg"` string, specifically so Railway's `ENV
  IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg` can redirect to the system binary
  instead of the bundled (and sometimes architecture-mismatched) one. If
  you add a new ffmpeg call site in this repo, follow that same pattern —
  don't hardcode `"ffmpeg"` and assume it resolves the same way in every
  environment.

## Installation check (always do this first for a new call site)

```bash
ffmpeg -version   # binary present?
ffprobe -version  # inspection tool, ships alongside ffmpeg
```
apt package is `ffmpeg` (installs both binaries). Not in `requirements.
txt` as a Python package — it's a system binary; `imageio-ffmpeg` (which
*is* a Python dependency here) only bundles a fallback copy.

## Inspecting a file (ffprobe)

```bash
# Duration, codec, resolution, fps in one shot
ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,codec_name,duration \
  -of default=noprint_wrappers=1 input.mp4

# Just duration (float seconds) — useful for a size/length gate
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 input.mp4
```

## Common transforms

**Resize/crop to vertical 9:16** (Reels/TikTok/Shorts — 1080×1920 is the
standard target; crop-to-fill beats letterboxing for these platforms):
```bash
ffmpeg -i input.mp4 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
  -c:v libx264 -preset fast -crf 20 -c:a aac -b:a 128k output_9x16.mp4
```

**Square 1:1** (matches this shop's 2400×2400 listing-photo convention if
turning a still into a short clip):
```bash
ffmpeg -i input.mp4 -vf "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080" \
  -c:v libx264 -crf 20 -c:a aac output_1x1.mp4
```

**Extract audio only** (mp3):
```bash
ffmpeg -i input.mp4 -vn -c:a libmp3lame -q:a 2 output.mp3
```

**Extract a single frame as a thumbnail** (e.g. video-post preview image):
```bash
ffmpeg -i input.mp4 -ss 00:00:01.5 -vframes 1 -q:v 2 thumbnail.jpg
```

**Compress to fit under a target file size** (two-pass is the accurate
way — single-pass CRF is a good first try but not size-guaranteed):
```bash
# Quick first try: CRF-based (visually-driven, not size-guaranteed)
ffmpeg -i input.mp4 -c:v libx264 -crf 23 -preset slow -c:a aac -b:a 128k output_small.mp4

# Size-guaranteed two-pass, target_kbps = (target_MB * 8192 / duration_s) - audio_kbps
ffmpeg -y -i input.mp4 -c:v libx264 -b:v <target_kbps>k -pass 1 -an -f mp4 /dev/null
ffmpeg -y -i input.mp4 -c:v libx264 -b:v <target_kbps>k -pass 2 -c:a aac -b:a 128k output.mp4
```

**Concatenate clips** (same codec/resolution — use the concat demuxer, not
the filter, when no re-encoding is needed):
```bash
# files.txt: lines of `file '/abs/path/clip1.mp4'`
ffmpeg -f concat -safe 0 -i files.txt -c copy output.mp4
```

**Burn in captions/subtitles** (hardcoded into the video, needed for
platforms that don't reliably show soft subtitles — e.g. Reels):
```bash
ffmpeg -i input.mp4 -vf "subtitles=captions.srt:force_style='FontSize=24,PrimaryColour=&Hffffff&'" \
  -c:a copy output_captioned.mp4
```

## General social-video targets (industry-standard, not repo-sourced —
confirm current per-platform limits before a real post if it matters)

| Platform | Aspect | Resolution | Codec | Notes |
|---|---|---|---|---|
| Instagram Reels | 9:16 | 1080×1920 | H.264 + AAC | ≤90s ideal engagement, hard cap much higher |
| TikTok | 9:16 | 1080×1920 | H.264 + AAC | MP4/MOV, keep under ~100MB for fast processing |
| Facebook | 9:16 or 1:1 | 1080×1920 / 1080×1080 | H.264 + AAC | Same container as Reels generally works |
| Pinterest (Idea Pins) | 9:16 | 1080×1920 | H.264 + AAC | Static pins are just JPG — this only applies to video pins |

## Failure-handling pattern to copy

`video_generator.py`'s `_render_with_ffmpeg()` is the reference
implementation in this repo for driving ffmpeg as a subprocess safely:
stream frames on a writer thread while draining stderr concurrently
(prevents a full-pipe deadlock), a bounded `join(timeout=...)` rather than
an unbounded wait, and a post-encode sanity check (`sz < 10_000` → treat
as a failed render, not a tiny-but-valid file). Copy that shape for any
new ffmpeg subprocess call site rather than a bare `subprocess.run()`.
