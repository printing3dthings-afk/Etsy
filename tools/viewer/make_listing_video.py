#!/usr/bin/env python3
"""Etsy listing clips from the Virtual P1S Chamber (2026-10-22).

    python3 tools/viewer/build_site.py -o /tmp/site
    (cd /tmp/site && python3 -m http.server 8765 &)
    python3 tools/viewer/make_listing_video.py hex_lantern out/hex_lantern-timelapse.mp4

Drives the page's own frame-exact export headless (window.__viewer.makeVideo)
with the plate options: the print close up on its build plate, the head and
enclosure out of shot, no caption, and a hold on the finished part. The page
hands back H.264 MP4s; x264 then joins and re-encodes them as High profile,
yuv420p, no audio track, index at the front, the form Etsy and phones take.

The clip is made in chunks of --chunk frames, each saved to --work as it
finishes, and a rerun skips the chunks already there. On this container's
software renderer the hex lantern takes over two hours, and the first run of
all eight lost three hours of frames when the machine restarted (2026-10-22).

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
FPS = 30   # VID_FPS in app.js


def render(url, job, seconds, hold, fmt, scale, frm=None, to=None):
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
        b64 = pg.evaluate("""async ([fmt, s, sc, h, a, b]) => {
            const blob = await window.__viewer.makeVideo(fmt, s, sc, {plate: true, caption: false, hold: h, from: a, to: b});
            if (!blob) { return null; }
            const buf = new Uint8Array(await blob.arrayBuffer());
            let bin = '';
            for (let i = 0; i < buf.length; i += 32768) { bin += String.fromCharCode.apply(null, buf.subarray(i, i + 32768)); }
            return btoa(bin);
        }""", [fmt, seconds, scale, hold, frm, to])
        b.close()
    if not b64:
        sys.exit(f"{job}: the page made no video")
    print(f"{job}: frames {frm}-{to} rendered in {time.time() - t0:.0f} s", flush=True)
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
    ap.add_argument("--chunk", type=int, default=60, help="frames per saved piece")
    ap.add_argument("--work", default=None, help="where the pieces are kept (default: a temp dir)")
    a = ap.parse_args()
    n = round(max(2, min(60, a.seconds)) * FPS)
    work = Path(a.work or tempfile.mkdtemp(prefix=f"{a.job}_"))
    work.mkdir(parents=True, exist_ok=True)
    pieces = []
    for i0 in range(0, n, a.chunk):
        i1 = min(n, i0 + a.chunk)
        piece = work / f"{a.job}_{i0:04d}_{i1:04d}.mp4"
        if not piece.exists():
            tmp = piece.with_suffix(".part")
            tmp.write_bytes(render(a.url, a.job, a.seconds, a.hold, a.format, a.scale, i0, i1))
            tmp.rename(piece)
        pieces.append(piece)
    lst = work / f"{a.job}_pieces.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in pieces))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high",
                    "-level", "4.0", "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart",
                    a.out], check=True)
    print(f"{a.job}: wrote {a.out}")


if __name__ == "__main__":
    main()
