#!/usr/bin/env python3
"""Design-process videos, template v2 (2026-11-27): full-frame 9:16, payoff first, short end.

Scott, via Greg, on the Fold Stand and Gear Heart cuts. compose.py (v1) stays as it was, so the
first cuts can be rebuilt exactly; every new video uses this file. The rules it enforces, and the
checklist for storyboards, are in README.md ("Template v2").

  - No title card. The first segment is the payoff: the finished product working. Its `big` line
    ("N versions to get here") comes in after a second, then a `rewind` segment runs the story
    backwards, fast, to version 1.
  - Every shot fills the 1080 x 1920 frame. Renders are rendered portrait; real footage is
    scaled to cover and cropped.
  - Every word on screen sits on a dark box. Captions end 1500 px down (22% up from the bottom),
    the heading, tag and watermark sit at the top: nothing in the bottom 20%.
  - No separate end card: the follow line fades in over the last 1.5 s of the last shot.

A segment is a dict:
  kind "frames":  dir (PNG frames from blender_anim.py), hold_start / hold_end (s)
  kind "video":   path, start (s), dur (s), speed (default 1), crop "w:h:x:y" (before the cover fit)
  kind "image":   path, dur (s), zoom [from, to], centre [x, y] (0-1)
  kind "rewind":  dirs [shot dirs in story order], dur (s): their frames played backwards, fast
  kind "placeholder": dur (s), lines [text, ...]: a marked slate for footage still to come
  every segment: label (heading), captions [[t, text], ...], big [[t, text], ...] (a large centred
                 line), chip ("RENDER", "REAL", "PLACEHOLDER"), fade (s, the dissolve into the next)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "series_motion"))
from directions import FPS, H, SS, W, font  # noqa: E402
from kit import SERIES  # noqa: E402

CAP_BOTTOM = 1500                     # captions end here: 420 px (22%) up from the bottom
SAFE_BOTTOM = int(H * 0.8)            # nothing below this line
BOX = (16, 14, 20, 214)               # the dark backing box (RGBA)
END_DUR = 1.5


def _wrap(text, fnt, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if fnt.getlength(t) / SS > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def cover(im):
    """Scale to cover 1080 x 1920, then crop the middle."""
    im = im.convert("RGB")
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    return im.crop((x0, y0, x0 + W, y0 + H))


class Text:
    """The word layers, each on its own dark box, drawn at SS and cached."""

    def __init__(self, sp):
        self.sp = sp
        self._cache = {}

    def _box(self, d, cx, top, lines, fnt, pad_x, pad_y, lh, fill):
        tw = max(fnt.getlength(t) for t in lines) / SS
        hgt = lh * len(lines)
        d.rounded_rectangle(((cx - tw / 2 - pad_x) * SS, (top - pad_y) * SS,
                             (cx + tw / 2 + pad_x) * SS, (top + hgt + pad_y) * SS), 22 * SS, fill=BOX)
        for i, t in enumerate(lines):
            d.text((cx * SS, (top + lh * (i + 0.5)) * SS), t, font=fnt, fill=fill, anchor="mm")

    def layer(self, label, caption, chip, big, end):
        k = (label, caption, chip, big, end)
        if k in self._cache:
            return self._cache[k]
        sp = self.sp
        im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # top row: the tag at the left, the watermark at the right
        if chip:
            f = font("bold", 30)
            tw = f.getlength(chip) / SS
            d.rounded_rectangle((40 * SS, 60 * SS, (40 + tw + 44) * SS, 116 * SS), 28 * SS, fill=BOX)
            d.text(((40 + 22 + tw / 2) * SS, 88 * SS), chip, font=f, fill=sp["acc"], anchor="mm")
        f = font("semi", 26)
        tw = f.getlength("ONBRANDCRAFTZ") / SS
        d.rounded_rectangle(((W - 40 - tw - 40) * SS, 64 * SS, (W - 40) * SS, 112 * SS), 24 * SS, fill=BOX)
        d.text(((W - 40 - 20 - tw / 2) * SS, 88 * SS), "ONBRANDCRAFTZ", font=f, fill=(240, 236, 230), anchor="mm")
        if label:
            self._box(d, W / 2, 168, [label], font("anton", 66), 30, 14, 84, sp["acc"])
        if big:
            f = font("anton", 92)
            lines = _wrap(big, f, 900)
            self._box(d, W / 2, 900 - 56 * len(lines), lines, f, 36, 22, 112, (250, 246, 238))
        if caption:
            f = font("semi", 48)
            lines = _wrap(caption, f, 900)
            lh = 64
            self._box(d, W / 2, CAP_BOTTOM - 22 - lh * len(lines), lines, f, 30, 22, lh, (250, 246, 238))
        if end:
            self._box(d, W / 2, 1060, ["FOLLOW ONBRANDCRAFTZ"], font("anton", 84), 36, 22, 104, sp["acc"])
            f = font("bold", 40)
            tw = f.getlength("LINK IN BIO") / SS
            d.rounded_rectangle(((W / 2 - tw / 2 - 60) * SS, 1240 * SS, (W / 2 + tw / 2 + 60) * SS, 1330 * SS),
                                45 * SS, fill=(*sp["acc"], 255))
            d.text((W / 2 * SS, 1285 * SS), "LINK IN BIO", font=f, fill=(30, 24, 22), anchor="mm")
        out = im.resize((W, H), Image.LANCZOS)
        a = np.asarray(out.getchannel("A"))
        if a[SAFE_BOTTOM:].any():
            raise SystemExit(f"text below the 20% line: {k}")
        self._cache[k] = out
        return out

    def draw(self, im, txt, alpha=1.0):
        layer = self.layer(*txt)
        if alpha < 1.0:
            layer = layer.copy()
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
        im.paste(layer, (0, 0), layer)
        return im


def _video_frames(seg, tmp):
    out = Path(tmp) / f"v{abs(hash((seg['path'], seg['start']))) % 10**8}"
    out.mkdir(exist_ok=True)
    speed = seg.get("speed", 1.0)
    vf = f"setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if seg.get("crop"):
        vf = f"crop={seg['crop']}," + vf
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(seg["start"]), "-i", seg["path"],
                    "-t", str(seg["dur"] * speed), "-vf", vf, str(out / "f_%04d.png")], check=True)
    return sorted(out.glob("f_*.png"))


def _image_frames(seg, tmp):
    """A still as a slow push-in, cropped 9:16 round `centre` (no hard cut-ins)."""
    out = Path(tmp) / f"i{abs(hash(seg['path'])) % 10**8}"
    out.mkdir(exist_ok=True)
    im = Image.open(seg["path"]).convert("RGB")
    w, h = im.size
    cx, cy = seg.get("centre", [0.5, 0.5])
    z0, z1 = seg.get("zoom", [1.0, 1.08])
    n = int(round(seg["dur"] * FPS))
    # a 9:16 window: as tall as the image allows, unless the image is narrower than that
    base_h = min(h, w * H / W)
    fs = []
    for k in range(n):
        e = 0.5 - 0.5 * np.cos(np.pi * k / max(1, n - 1))        # eased push-in
        z = z0 + (z1 - z0) * e
        ch = base_h / z
        cw = ch * W / H
        x0 = min(max(cx * w - cw / 2, 0), w - cw)
        y0 = min(max(cy * h - ch / 2, 0), h - ch)
        f = out / f"f_{k:04d}.png"
        im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS).save(f)
        fs.append(f)
    return fs


def _rewind_frames(seg, tmp):
    """The story's shots run backwards, fast: every frame of every dir, reversed, sampled to dur."""
    allf = []
    for d in seg["dirs"]:
        allf += sorted(Path(d).glob("f_*.png"))
    allf = allf[::-1]
    n = int(round(seg["dur"] * FPS))
    out = Path(tmp) / f"r{abs(hash(tuple(seg['dirs']))) % 10**8}"
    out.mkdir(exist_ok=True)
    fs = []
    for k in range(n):
        src = allf[min(len(allf) - 1, round(k * (len(allf) - 1) / max(1, n - 1)))]
        im = cover(Image.open(src))
        # a rewind look: a little motion blur and two soft bands rolling up
        im = im.filter(ImageFilter.BoxBlur(2))
        d = ImageDraw.Draw(im, "RGBA")
        for b in (0, 1):
            y = int((H * (1 - (k / n + b / 2) % 1)))
            d.rectangle((0, y, W, y + 26), fill=(255, 255, 255, 40))
        f = out / f"f_{k:04d}.png"
        im.save(f)
        fs.append(f)
    return fs


def _placeholder_frames(seg, tmp, sp):
    """A slate that says exactly what footage goes here; never posted as it is."""
    out = Path(tmp) / f"p{abs(hash(tuple(seg['lines']))) % 10**8}"
    out.mkdir(exist_ok=True)
    im = Image.new("RGB", (W * SS, H * SS), (34, 30, 34))
    d = ImageDraw.Draw(im)
    dash = 40 * SS
    x0, y0, x1, y1 = 90 * SS, 330 * SS, (W - 90) * SS, 1430 * SS
    for x in range(x0, x1, dash * 2):
        d.line((x, y0, min(x + dash, x1), y0), fill=sp["acc"], width=6 * SS)
        d.line((x, y1, min(x + dash, x1), y1), fill=sp["acc"], width=6 * SS)
    for y in range(y0, y1, dash * 2):
        d.line((x0, y, x0, min(y + dash, y1)), fill=sp["acc"], width=6 * SS)
        d.line((x1, y, x1, min(y + dash, y1)), fill=sp["acc"], width=6 * SS)
    f = font("anton", 64)
    y = 560
    for line in seg["lines"]:
        for t in _wrap(line, f, 780):
            d.text((W / 2 * SS, y * SS), t, font=f, fill=(240, 236, 230), anchor="mm")
            y += 84
        y += 40
        f = font("semi", 42)
    im = im.resize((W, H), Image.LANCZOS)
    p = out / "f_0000.png"
    im.save(p)
    return [p] * int(round(seg["dur"] * FPS))


def _segment_frames(seg, tmp, sp):
    k = seg["kind"]
    if k == "image":
        return _image_frames(seg, tmp)
    if k == "rewind":
        return _rewind_frames(seg, tmp)
    if k == "placeholder":
        return _placeholder_frames(seg, tmp, sp)
    if k == "frames":
        fs = sorted(Path(seg["dir"]).glob("f_*.png"))
        if not fs:
            raise SystemExit(f"no frames in {seg['dir']}")
        return ([fs[0]] * int(round(seg.get("hold_start", 0) * FPS)) + fs
                + [fs[-1]] * int(round(seg.get("hold_end", 0) * FPS)))
    return _video_frames(seg, tmp)


def _at(pairs, t):
    cur = ""
    for t0, text in pairs or []:
        if t >= t0:
            cur = text
    return cur


def render(segments, out_mp4, series="product"):
    """Write the video. Returns the timeline (for SCRIPT_v2.md and timeline_v2.json)."""
    sp = SERIES[series]
    tx = Text(sp)
    timeline, t_body = [], 0.0
    with tempfile.TemporaryDirectory() as tmp:
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium",
                                "-movflags", "+faststart", str(out_mp4)], stdin=subprocess.PIPE)
        segs = [(seg, _segment_frames(seg, tmp, sp)) for seg in segments]
        end_n = int(round(END_DUR * FPS))
        carry = []
        for i, (seg, fs) in enumerate(segs):
            last = i + 1 == len(segs)
            fade = 0 if last else int(round(seg.get("fade", 0.3) * FPS))
            n = len(fs)
            start_t = t_body

            def txt(t, k):
                end = last and k >= n - end_n
                if end:                    # the follow line replaces the caption at the end
                    return (seg.get("label", ""), "", seg.get("chip", ""), "", True)
                return (seg.get("label", ""), _at(seg.get("captions"), t), seg.get("chip", ""),
                        _at(seg.get("big"), t), False)

            for k, f in enumerate(fs[: n - fade] if fade else fs):
                t = k / FPS
                im = cover(Image.open(f))
                cur = txt(t, k)
                if carry and k < len(carry):
                    # pictures dissolve; words fade out, then the new ones fade in
                    a = (k + 1) / (len(carry) + 1)
                    old_im, old_txt = carry[k]
                    im = Image.blend(old_im, im, a)
                    im = tx.draw(im, old_txt, max(0.0, 1 - 2 * a)) if a < 0.5 else tx.draw(im, cur, min(1.0, 2 * a - 1))
                elif last and k >= n - end_n:
                    j = k - (n - end_n)
                    im = Image.blend(im, Image.new("RGB", (W, H), (20, 16, 18)), min(0.45, 0.45 * (j + 1) / 9))
                    im = tx.draw(im, cur, min(1.0, (j + 1) / 9))
                else:
                    im = tx.draw(im, cur)
                enc.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
                t_body += 1 / FPS
            carry = []
            for k, f in enumerate(fs[n - fade:] if fade else []):
                kk = n - fade + k
                carry.append((cover(Image.open(f)), txt(kk / FPS, kk)))
            caps = [(start_t + c0, c) for c0, c in seg.get("captions", [])]
            caps += [(start_t + c0, c) for c0, c in seg.get("big", [])]
            timeline.append(dict(label=seg.get("label", ""), chip=seg.get("chip", ""), kind=seg["kind"],
                                 start=start_t, end=t_body + len(carry) / FPS, captions=sorted(caps)))
        enc.stdin.close()
        enc.wait()
    total = _duration(out_mp4)
    return dict(opener=0.0, end_from=total - END_DUR, total=total, steps=timeline)


def write_script(tl, path, title, status, sources):
    rows = []
    for st in tl["steps"]:
        caps = st["captions"] or [(st["start"], "")]
        for k, (t0, text) in enumerate(caps):
            t1 = caps[k + 1][0] if k + 1 < len(caps) else st["end"]
            rows.append(f"| {t0:.1f} | {t1:.1f} | {text} | {st['label']} | {st['chip']} |")
    ph = [st for st in tl["steps"] if st["kind"] == "placeholder"]
    md = [
        f"# {title}, from the design file: script (template v2)",
        "",
        "Generated by the storyboard script from the cut's own timeline. The on-screen lines are the",
        "voice-over lines: Benson, read them over the shots, and add music. The video has no audio.",
        "",
        f"- **Length:** {tl['total']:.1f} s. No title card: it opens on the finished product. The follow"
        f" line fades in over the last {END_DUR:.1f} s ({tl['end_from']:.1f} s on).",
        "- **Labels:** every render carries RENDER; Scott's footage and photos carry REAL.",
        f"- **Status:** {status}",
    ]
    if ph:
        md.append("- **Placeholder, not postable yet:** " + "; ".join(
            f"{st['start']:.1f}-{st['end']:.1f} s ({st['label']})" for st in ph)
                  + ". Swap in Scott's clip and rebuild before it posts.")
    md += ["", "| start | end | line (on screen) | step | tag |", "|---|---|---|---|---|", *rows, "",
           "## Where each claim comes from", "", *[f"- **{c}:** {s}" for c, s in sources], ""]
    Path(path).write_text("\n".join(md))


def _duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())
