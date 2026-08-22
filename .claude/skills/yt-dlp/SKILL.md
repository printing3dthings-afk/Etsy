---
name: yt-dlp
description: "CLI reference for downloading video/audio/subtitles from a URL with yt-dlp. Use when Scott provides a video URL and wants it downloaded, its audio extracted, or its transcript/subtitles pulled — competitor research, repurposing Scott's own uploaded content, or pulling reference audio/video for a build. Never use to redistribute someone else's copyrighted content as shop product material."
---

# yt-dlp — Video/Audio Download CLI Reference

Developer reference for `yt-dlp`. This repo already depends on it
indirectly — the `youtube-transcript` skill shells out to it to pull
captions, and `clipify` expects it (alongside ffmpeg + Whisper) to be
available locally for finding/cutting clips. This skill is the general
CLI reference for everything else: downloading a full video, audio-only
extraction, and playlist/format selection.

**Scope boundary — this codebase's cardinal rule applies here too:**
never lie to the customer. Downloaded third-party video/audio is for
research and reference only (competitor listing videos, a URL Scott
sends for analysis, Scott's own previously-uploaded content he wants
repurposed) — never redistribute someone else's copyrighted content as
delivered product material or listing media without Scott's explicit
confirmation he has the rights to use it.

## Installation check (always do this first)

```bash
yt-dlp --version || pip install -U yt-dlp
```
Not in `requirements.txt` — install on demand in whatever environment
needs it. `youtube-transcript`'s own instructions already auto-install
via brew/apt/pip; follow that same on-demand pattern rather than adding
it as a standing dependency nobody asked for.

## Basic download

```bash
# Best available video+audio, merged into one file
yt-dlp -f "bv*+ba/b" -o "%(title)s.%(ext)s" "<URL>"

# Cap resolution (keeps file size sane for a quick reference pull)
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" "<URL>"
```

## Audio only

```bash
# Extract as mp3 (needs ffmpeg on PATH — see the ffmpeg skill)
yt-dlp -x --audio-format mp3 --audio-quality 0 "<URL>"
```

## Subtitles / transcript (what `youtube-transcript` automates)

```bash
# List what's actually available first — don't assume
yt-dlp --list-subs "<URL>"

# Manual (human-written) captions — highest quality, prefer this
yt-dlp --write-sub --sub-lang en --skip-download "<URL>"

# Fallback: auto-generated captions
yt-dlp --write-auto-sub --sub-lang en --skip-download "<URL>"

# Convert the downloaded .vtt to plain text if needed
yt-dlp --write-auto-sub --sub-lang en --skip-download --convert-subs srt "<URL>"
```

## Format inspection (pick an exact format_id instead of guessing)

```bash
yt-dlp -F "<URL>"     # lists every available format_id + resolution/codec
yt-dlp -f 137+140 "<URL>"   # download by explicit format_id (video+audio)
```

## Output naming templates

```bash
# Default: title.ext in cwd. Useful alternates:
yt-dlp -o "%(uploader)s - %(title)s.%(ext)s" "<URL>"
yt-dlp -o "downloads/%(id)s.%(ext)s" "<URL>"   # stable filename by video id
```

## Playlists

```bash
yt-dlp --flat-playlist -J "<PLAYLIST_URL>"   # list entries only, no download (JSON)
yt-dlp --playlist-items 1-5 "<PLAYLIST_URL>"  # download a slice, not the whole thing
```

## Rate limiting / being a good citizen

```bash
yt-dlp --limit-rate 2M "<URL>"        # cap bandwidth
yt-dlp --sleep-interval 2 --max-sleep-interval 5 "<URL>"   # pace multi-video pulls
```

## Common failure modes

- **"Sign in to confirm you're not a bot" / geo-restricted content:**
  don't reach for scraping workarounds — this is a signal to ask Scott
  for the file directly or skip the pull, not to route around the
  platform's own access controls.
- **Merging requires ffmpeg:** `-f "bv*+ba"` (separate video+audio
  streams merged into one container) needs `ffmpeg` on `PATH` — see the
  `ffmpeg` skill for the installation check. Without it, yt-dlp falls
  back to a combined-but-lower-quality single format automatically
  rather than failing outright, so check `-F`'s output if the result
  looks lower-res than expected.
- **A URL that's actually a shorts/reel/TikTok link:** yt-dlp supports
  far more than raw YouTube (TikTok, Instagram, Twitter/X, Vimeo, and
  hundreds of other extractors) — no special flag needed, just pass the
  URL as-is and let it auto-detect the extractor.
