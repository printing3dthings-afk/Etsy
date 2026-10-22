#!/usr/bin/env python3
"""Etsy listing clips from the Virtual P1S Chamber (2026-10-22).

    python3 tools/viewer/build_site.py -o /tmp/site
    (cd /tmp/site && python3 -m http.server 8765 &)
    python3 tools/viewer/make_listing_video.py hex_lantern out/hex_lantern-timelapse.mp4

Drives the page's own frame-exact export headless (window.__viewer.makeVideo)
with the plate options: the print close up on its build plate, the head and
enclosure out of shot, no caption, and a hold on the finished part. The page
hands back an H.264 MP4; x264 then re-encodes it as High profile, yuv420p,
no audio track, index at the front, the form Etsy and phones take.

Scott's rule for these: the camera is on the print itself, sitting on the
plate, close enough to watch the layers build. Not the whole machine, and not
Part only's floating studio view.
"""
import argparse
import base64
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def render(url, job, seconds, hold, fmt, scale):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        kw = {"executable_path": CHROME} if Path(CHROME).exists() else {}
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                    "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"], **kw)
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto(f"{url}/index.html#{job}")
        pg.wait_for_function("window.__viewer && window.__viewer.getJob()", timeout=300000)
        name = pg.evaluate("window.__viewer.getJob().raw.name")
        print(f"{job}: loaded {name!r}", flush=True)
        t0 = time.time()
        b64 = pg.evaluate("""async ([fmt, s, sc, h]) => {
            const blob = await window.__viewer.makeVideo(fmt, s, sc, {plate: true, caption: false, hold: h});
            if (!blob) { return null; }
            const buf = new Uint8Array(await blob.arrayBuffer());
            let bin = '';
            for (let i = 0; i < buf.length; i += 32768) { bin += String.fromCharCode.apply(null, buf.subarray(i, i + 32768)); }
            return btoa(bin);
        }""", [fmt, seconds, scale, hold])
        b.close()
    if not b64:
        sys.exit(f"{job}: the page made no video")
    print(f"{job}: rendered in {time.time() - t0:.0f} s", flush=True)
    return base64.b64decode(b64)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("job", help="the plate's id in the viewer, e.g. hex_lantern")
    ap.add_argument("out", help="the MP4 to write")
    ap.add_argument("--url", default="http://127.0.0.1:8765", help="where the built site is served")
    ap.add_argument("--seconds", type=float, default=15)
    ap.add_argument("--hold", type=float, default=2, help="seconds on the finished part")
    ap.add_argument("--format", default="square", choices=["square", "portrait", "reel"])
    ap.add_argument("--scale", type=float, default=1, help="below 1 for quick framing checks only")
    a = ap.parse_args()
    raw = render(a.url, a.job, a.seconds, a.hold, a.format, a.scale)
    with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
        f.write(raw)
        f.flush()
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f.name, "-an", "-c:v", "libx264",
                        "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.0",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out], check=True)
    print(f"{a.job}: wrote {a.out}")


if __name__ == "__main__":
    main()
