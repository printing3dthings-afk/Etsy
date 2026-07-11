"""
Records a screen-capture demo video of the Pinterest pin-scheduler prototype
(pinterest_app_demo/index.html) by driving it with headless Chromium via Playwright.

Output is used for the Pinterest developer app resubmission (trial denied twice;
Pinterest's guidance is to resubmit with a short demo video + privacy policy URL).
Playwright's record_video_dir produces a .webm directly from the browser session —
no ffmpeg/xvfb needed, and YouTube accepts .webm uploads as-is.

Usage: python tools/record_pinterest_demo.py
"""

import shutil
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_HTML = REPO_ROOT / "pinterest_app_demo" / "index.html"
OUTPUT_DIR = REPO_ROOT / "data" / "social" / "videos"
OUTPUT_PATH = OUTPUT_DIR / "pinterest_demo_resubmission.webm"

VIEWPORT = {"width": 1280, "height": 900}


def record() -> Path:
    if not DEMO_HTML.exists():
        raise FileNotFoundError(f"Demo HTML not found at {DEMO_HTML}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_video_dir:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport=VIEWPORT,
                record_video_dir=tmp_video_dir,
                record_video_size=VIEWPORT,
            )
            page = context.new_page()
            page.goto(DEMO_HTML.resolve().as_uri())

            # 1. Login screen
            page.wait_for_timeout(5000)

            # 2. Click "Connect Pinterest Account" -> OAuth consent screen
            page.click(".btn-pinterest")
            page.wait_for_timeout(2000)

            # 3. Let the viewer read the requested permissions
            page.wait_for_timeout(10000)

            # 4. Click "Allow Access" -> dashboard
            page.click(".btn-allow")
            page.wait_for_timeout(2000)

            # 5. Show the dashboard step bar + stats row
            page.wait_for_timeout(8000)

            # 6. Click "Post Next Pin" several times, showing the live API log
            for _ in range(6):
                page.click(".btn-small")
                page.wait_for_timeout(8500)

            # 7. Scroll down to the configured boards grid
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(8000)

            # 8. Final pause before closing
            page.wait_for_timeout(5000)

            video_handle = page.video
            context.close()
            browser.close()

            recorded_path = Path(video_handle.path())
            shutil.move(str(recorded_path), str(OUTPUT_PATH))

    return OUTPUT_PATH


if __name__ == "__main__":
    out = record()
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"Demo video written to {out} ({size_mb:.1f} MB)")
