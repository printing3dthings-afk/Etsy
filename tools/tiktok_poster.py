"""
TikTok Content Poster — OnBrandCraftz (@onbrandcraftz)

Posts videos to TikTok using the Content Posting API.
Reads captions and hashtags from data/tiktok_content_calendar.json.

Usage:
  python tools/tiktok_poster.py --status          # check API connection + token
  python tools/tiktok_poster.py --today           # post today's scheduled video
  python tools/tiktok_poster.py --day 3           # post day 3 from the calendar
  python tools/tiktok_poster.py --file video.mp4  # post a specific video file
  python tools/tiktok_poster.py --refresh         # refresh the access token

Requirements:
  - Run python tools/tiktok_oauth.py first to get an access token
  - TIKTOK_ACCESS_TOKEN must be set in .env
  - Video file must be mp4, under 50MB, under 60 seconds for feed posts
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path

ENV_PATH      = Path(__file__).parent.parent / ".env"
CALENDAR_PATH = Path(__file__).parent.parent / "data" / "tiktok_content_calendar.json"

CLIENT_KEY    = os.getenv("TIKTOK_CLIENT_KEY",    "awwqfpmeze4ksjm4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "Fgq1xaYUbAUEElf2pfokELTbqnk3ylIB")
ACCESS_TOKEN  = os.getenv("TIKTOK_ACCESS_TOKEN",  "")
REFRESH_TOKEN = os.getenv("TIKTOK_REFRESH_TOKEN", "")
OPEN_ID       = os.getenv("TIKTOK_OPEN_ID",       "")

API_BASE      = "https://open.tiktokapis.com/v2"
TOKEN_URL     = f"{API_BASE}/oauth/token/"
UPLOAD_URL    = f"{API_BASE}/post/publish/video/init/"
STATUS_URL    = f"{API_BASE}/post/publish/status/fetch/"
USER_INFO_URL = f"{API_BASE}/user/info/"


def _load_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _save_env_value(key: str, value: str) -> None:
    text = ENV_PATH.read_text()
    lines = text.splitlines()
    updated = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            updated.append(f"{key}={value}")
            found = True
        else:
            updated.append(line)
    if not found:
        updated.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(updated) + "\n")


def _api_call(url: str, payload: dict, token: str) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json; charset=UTF-8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def refresh_token(refresh_tok: str) -> dict:
    payload = urllib.parse.urlencode({
        "client_key":     CLIENT_KEY,
        "client_secret":  CLIENT_SECRET,
        "grant_type":     "refresh_token",
        "refresh_token":  refresh_tok,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def check_status(token: str) -> None:
    print("Checking TikTok API connection...")
    try:
        result = _api_call(
            USER_INFO_URL + "?fields=open_id,display_name,avatar_url",
            {},
            token,
        )
        if result.get("data"):
            u = result["data"].get("user", {})
            print(f"  Connected as: {u.get('display_name', 'unknown')}")
            print(f"  Open ID: {u.get('open_id', 'unknown')}")
            print(f"  Token: valid")
        else:
            print(f"  Response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"  Error: {e}")
        print("  Run: python tools/tiktok_oauth.py  to get a fresh token")


def get_today_post() -> dict | None:
    if not CALENDAR_PATH.exists():
        print("Calendar not found at data/tiktok_content_calendar.json")
        return None
    cal = json.loads(CALENDAR_PATH.read_text())
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    # Find by date or by weekday position
    for entry in cal.get("calendar", []):
        if entry.get("date") == today_str:
            return entry
    print(f"No post scheduled for today ({today_str}).")
    print("Use --day N to post a specific day from the calendar.")
    return None


def get_day_post(day_num: int) -> dict | None:
    if not CALENDAR_PATH.exists():
        return None
    cal = json.loads(CALENDAR_PATH.read_text())
    entries = cal.get("calendar", [])
    if 1 <= day_num <= len(entries):
        return entries[day_num - 1]
    print(f"Day {day_num} not found. Calendar has {len(entries)} entries.")
    return None


def build_caption(entry: dict) -> str:
    hook     = entry.get("hook", "")
    hashtags = " ".join(entry.get("hashtags", []))
    cta      = entry.get("cta", "")
    parts = []
    if hook:
        parts.append(hook)
    if cta:
        parts.append(cta)
    if hashtags:
        parts.append(hashtags)
    caption = "\n\n".join(parts)
    # TikTok caption limit: 2200 chars
    return caption[:2200]


def post_video(video_path: str, caption: str, token: str) -> dict:
    vpath = Path(video_path)
    if not vpath.exists():
        return {"error": f"File not found: {video_path}"}

    file_size = vpath.stat().st_size
    if file_size > 50 * 1024 * 1024:
        return {"error": f"File too large ({file_size//1024//1024}MB). Max 50MB."}

    print(f"  Initiating upload for: {vpath.name} ({file_size//1024}KB)...")

    # Step 1: Initialize the upload
    init_payload = {
        "post_info": {
            "title":         caption,
            "privacy_level": "SELF_ONLY",  # safe default — change to PUBLIC_TO_EVERYONE when ready
            "disable_duet":  False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source":          "FILE_UPLOAD",
            "video_size":      file_size,
            "chunk_size":      file_size,
            "total_chunk_count": 1,
        },
    }

    try:
        init_result = _api_call(UPLOAD_URL, init_payload, token)
    except Exception as e:
        return {"error": f"Init failed: {e}"}

    if init_result.get("error", {}).get("code") != "ok":
        return {"error": f"Init error: {json.dumps(init_result)}"}

    publish_id  = init_result["data"]["publish_id"]
    upload_url  = init_result["data"]["upload_url"]
    print(f"  Publish ID: {publish_id}")

    # Step 2: Upload the video bytes
    print(f"  Uploading video...")
    video_bytes = vpath.read_bytes()
    upload_req = urllib.request.Request(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type":  "video/mp4",
            "Content-Range": f"bytes 0-{file_size-1}/{file_size}",
            "Content-Length": str(file_size),
        },
        method="PUT",
    )
    try:
        with urllib.request.urlopen(upload_req, timeout=120) as r:
            upload_status = r.status
    except Exception as e:
        return {"error": f"Upload failed: {e}"}

    if upload_status not in (200, 201, 204):
        return {"error": f"Upload HTTP {upload_status}"}

    print(f"  Upload complete. Waiting for processing...")

    # Step 3: Poll for status
    for attempt in range(12):
        time.sleep(5)
        try:
            status_result = _api_call(
                STATUS_URL,
                {"publish_id": publish_id},
                token,
            )
            status = status_result.get("data", {}).get("status", "unknown")
            print(f"  Status: {status}")
            if status == "PUBLISH_COMPLETE":
                return {"success": True, "publish_id": publish_id, "status": status}
            if status in ("FAILED", "ERROR"):
                return {"error": f"Publish failed with status: {status}", "data": status_result}
        except Exception as e:
            print(f"  Status check error: {e}")

    return {"success": True, "publish_id": publish_id, "status": "processing", "note": "Video uploaded — check TikTok app to confirm it posted"}


def print_post_preview(entry: dict) -> None:
    print("\n" + "=" * 50)
    print(f"Day {entry.get('day')} — {entry.get('date', '')} {entry.get('time', '')}")
    print(f"Pillar: {entry.get('pillar', '')}")
    print(f"Hook: {entry.get('hook', '')}")
    print(f"Content: {entry.get('content', '')}")
    print(f"Audio: {entry.get('audio', '')}")
    print(f"CTA: {entry.get('cta', '')}")
    print(f"Hashtags: {' '.join(entry.get('hashtags', []))}")
    print("=" * 50)


def main() -> None:
    env = _load_env()
    token = env.get("TIKTOK_ACCESS_TOKEN", "") or ACCESS_TOKEN

    args = sys.argv[1:]

    if "--refresh" in args or not token:
        refresh_tok = env.get("TIKTOK_REFRESH_TOKEN", "") or REFRESH_TOKEN
        if not refresh_tok:
            print("No refresh token found. Run: python tools/tiktok_oauth.py")
            return
        print("Refreshing access token...")
        try:
            result = refresh_token(refresh_tok)
            new_token = result.get("access_token", "")
            new_refresh = result.get("refresh_token", refresh_tok)
            if new_token:
                _save_env_value("TIKTOK_ACCESS_TOKEN", new_token)
                _save_env_value("TIKTOK_REFRESH_TOKEN", new_refresh)
                token = new_token
                print("Token refreshed successfully.")
            else:
                print(f"Refresh failed: {json.dumps(result, indent=2)}")
                return
        except Exception as e:
            print(f"Refresh error: {e}")
            return

    if "--status" in args:
        check_status(token)
        return

    if "--today" in args:
        entry = get_today_post()
        if not entry:
            return
        print_post_preview(entry)
        caption = build_caption(entry)
        video_file = input("\nEnter path to your video file (mp4): ").strip()
        if not video_file:
            print("No file provided.")
            return
        print(f"\nPosting to TikTok (privacy: SELF_ONLY for safety)...")
        result = post_video(video_file, caption, token)
        print(json.dumps(result, indent=2))
        return

    if "--day" in args:
        idx = args.index("--day")
        day_num = int(args[idx + 1]) if idx + 1 < len(args) else 1
        entry = get_day_post(day_num)
        if not entry:
            return
        print_post_preview(entry)
        caption = build_caption(entry)
        video_file = input("\nEnter path to your video file (mp4): ").strip()
        if not video_file:
            print("No file provided.")
            return
        print(f"\nPosting to TikTok (privacy: SELF_ONLY for safety)...")
        result = post_video(video_file, caption, token)
        print(json.dumps(result, indent=2))
        return

    if "--file" in args:
        idx = args.index("--file")
        video_file = args[idx + 1] if idx + 1 < len(args) else ""
        caption = input("Caption (leave blank to use Day 1 from calendar): ").strip()
        if not caption:
            entry = get_day_post(1)
            caption = build_caption(entry) if entry else "Check out OnBrandCraftz! #kawaii #digitalplanner"
        print(f"\nPosting {video_file} to TikTok...")
        result = post_video(video_file, caption, token)
        print(json.dumps(result, indent=2))
        return

    # Default: show status + calendar summary
    print("TikTok Poster — OnBrandCraftz")
    print()
    if token:
        check_status(token)
    else:
        print("No access token. Run: python tools/tiktok_oauth.py")

    if CALENDAR_PATH.exists():
        cal = json.loads(CALENDAR_PATH.read_text())
        entries = cal.get("calendar", [])
        print(f"\nCalendar: {len(entries)} posts loaded")
        today = date.today()
        for e in entries[:5]:
            print(f"  Day {e.get('day'):2d} | {e.get('date','')} | {e.get('pillar','')[:30]}")

    print("\nCommands:")
    print("  python tools/tiktok_poster.py --status")
    print("  python tools/tiktok_poster.py --today")
    print("  python tools/tiktok_poster.py --day 1")
    print("  python tools/tiktok_poster.py --file myvideo.mp4")
    print("  python tools/tiktok_poster.py --refresh")


if __name__ == "__main__":
    main()
