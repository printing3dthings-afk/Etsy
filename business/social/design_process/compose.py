#!/usr/bin/env python3
"""Design-process videos: lay rendered shots and real footage into the Product posts frame.

Scott, 2026-11-26: "use images like this from your design process's ... in animations to
transform from step to step until the final product." The shots come from blender_anim.py (the
real exported parts moving, the camera travelling, a cut plane sweeping); this file puts them in
a 1080 x 1920 frame with a step heading, a caption, and a RENDER or REAL tag on every shot (the
same labelling rule as digital_vs_real.py), dissolves between steps, and adds the kit's opener
and end card. It also returns the timeline, which the storyboard script writes as SCRIPT.md.

A segment is a dict:
  kind "frames": dir (PNG frames from blender_anim.py), hold_start / hold_end (s)
  kind "video":  path, start (s), dur (s), crop "w:h:x:y" (ffmpeg), speed (default 1)
  every segment: label (the step heading), captions [[t, text], ...] (t from the segment's
                 start), chip ("RENDER" or "REAL"), fade (s, the dissolve into the next one)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "series_motion"))
from directions import FPS, H, SS, W, font, mix  # noqa: E402
from kit import SERIES, background  # noqa: E402

CARD = (40, 400, 1000)              # x, y, size of the square the shots sit in
CAP_Y = 1450


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


class Frame:
    """The static layers of one step: background, heading, caption, the card's mask and tag."""

    def __init__(self, sp):
        self.sp = sp
        self.bg = background(sp).resize((W, H), Image.LANCZOS)
        x, y, s = CARD
        m = Image.new("L", (s * SS, s * SS), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, s * SS - 1, s * SS - 1), 34 * SS, fill=255)
        self.mask = m.resize((s, s), Image.LANCZOS)
        self._cache = {}

    def text_layer(self, label, caption, chip):
        k = (label, caption, chip)
        if k in self._cache:
            return self._cache[k]
        sp = self.sp
        im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if label:
            d.text((540 * SS, 300 * SS), label, font=font("anton", 70), fill=sp["acc"], anchor="mm")
        if caption:
            f = font("semi", 46)
            for i, line in enumerate(_wrap(caption, f, 940)):
                d.text((540 * SS, (CAP_Y + 40 + i * 62) * SS), line, font=f, fill=sp["text"], anchor="mm")
        if chip:
            f = font("bold", 30)
            x, y, _ = CARD
            tw = f.getlength(chip) / SS
            box = ((x + 26) * SS, (y + 26) * SS, (x + 26 + tw + 40) * SS, (y + 26 + 54) * SS)
            d.rounded_rectangle(box, 27 * SS, fill=(*sp["bg"], 235))
            d.text(((x + 26 + 20 + tw / 2) * SS, (y + 53) * SS), chip, font=f, fill=sp["acc"], anchor="mm")
        d.text((540 * SS, 1820 * SS), "ONBRANDCRAFTZ", font=font("semi", 28),
               fill=(*mix(sp["bg"], sp["text"], 0.8), 255), anchor="mm")
        out = im.resize((W, H), Image.LANCZOS)
        self._cache[k] = out
        return out

    def card(self, shot):
        im = self.bg.copy()
        x, y, s = CARD
        im.paste(shot.convert("RGB").resize((s, s), Image.LANCZOS), (x, y), self.mask)
        return im

    def text(self, im, label, caption, chip, alpha=1.0):
        layer = self.text_layer(label, caption, chip)
        if alpha < 1.0:
            a = layer.getchannel("A").point(lambda v: int(v * alpha))
            layer = layer.copy()
            layer.putalpha(a)
        im.paste(layer, (0, 0), layer)
        return im

    def compose(self, shot, label, caption, chip):
        return self.text(self.card(shot), label, caption, chip)


def _video_frames(seg, tmp):
    out = Path(tmp) / f"v{abs(hash(seg['path'])) % 10**8}"
    out.mkdir(exist_ok=True)
    speed = seg.get("speed", 1.0)
    vf = f"setpts=PTS/{speed},fps={FPS}"
    if seg.get("crop"):
        vf = f"crop={seg['crop']}," + vf
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(seg["start"]), "-i", seg["path"],
                    "-t", str(seg["dur"] * speed), "-vf", vf, str(out / "f_%04d.png")], check=True)
    return sorted(out.glob("f_*.png"))


def _segment_frames(seg, tmp):
    """The segment's shot frames, holds included, as a list of paths."""
    if seg["kind"] == "frames":
        fs = sorted(Path(seg["dir"]).glob("f_*.png"))
        if not fs:
            raise SystemExit(f"no frames in {seg['dir']}")
        return ([fs[0]] * int(round(seg.get("hold_start", 0) * FPS)) + fs
                + [fs[-1]] * int(round(seg.get("hold_end", 0) * FPS)))
    return _video_frames(seg, tmp)


def _caption_at(seg, t):
    cap = ""
    for t0, text in seg.get("captions", []):
        if t >= t0:
            cap = text
    return cap


def render(segments, out_mp4, opener=None, endcard=None, series="product"):
    """Write the body, then join opener + body + end card. Returns the timeline for SCRIPT.md."""
    sp = SERIES[series]
    fr = Frame(sp)
    timeline, t_body = [], 0.0
    with tempfile.TemporaryDirectory() as tmp:
        body = Path(tmp) / "body.mp4"
        enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                                "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium", str(body)],
                               stdin=subprocess.PIPE)
        segs = [(seg, _segment_frames(seg, tmp)) for seg in segments]
        carry = []                      # the previous segment's last frames, to dissolve from
        for i, (seg, fs) in enumerate(segs):
            fade = int(round(seg.get("fade", 0.4) * FPS)) if i + 1 < len(segs) else 0
            n = len(fs)
            start_t = t_body
            for k, f in enumerate(fs[: n - fade] if fade else fs):
                t = k / FPS
                txt = (seg.get("label", ""), _caption_at(seg, t), seg.get("chip", ""))
                if carry and k < len(carry):
                    # the pictures cross-dissolve; the words don't (two headings at once read as
                    # one garbled line): the old text fades out, then the new one fades in
                    a = (k + 1) / (len(carry) + 1)
                    old_card, old_txt = carry[k]
                    im = Image.blend(old_card, fr.card(Image.open(f)), a)
                    im = fr.text(im, *old_txt, alpha=max(0.0, 1 - 2 * a)) if a < 0.5 else \
                        fr.text(im, *txt, alpha=min(1.0, 2 * a - 1))
                else:
                    im = fr.text(fr.card(Image.open(f)), *txt)
                enc.stdin.write(np.asarray(im, dtype=np.uint8).tobytes())
                t_body += 1 / FPS
            # the frames this segment fades out on, blended into the next segment's start
            carry = []
            for k, f in enumerate(fs[n - fade:] if fade else []):
                t = (n - fade + k) / FPS
                carry.append((fr.card(Image.open(f)),
                              (seg.get("label", ""), _caption_at(seg, t), seg.get("chip", ""))))
            timeline.append(dict(label=seg.get("label", ""), chip=seg.get("chip", ""),
                                 start=start_t, end=t_body + len(carry) / FPS,
                                 captions=[(start_t + c0, c) for c0, c in seg.get("captions", [])]))
        enc.stdin.close()
        enc.wait()
        parts = [p for p in (opener, str(body), endcard) if p]
        inputs = sum((["-i", p] for p in parts), [])
        filt = "".join(f"[{i}:v]scale={W}:{H},setsar=1,fps={FPS},format=yuv420p[v{i}];" for i in range(len(parts)))
        filt += "".join(f"[v{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[out]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", filt, "-map", "[out]",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-movflags", "+faststart",
                        str(out_mp4)], check=True)
    off = _duration(opener) if opener else 0.0
    for t in timeline:
        t["start"] += off
        t["end"] += off
        t["captions"] = [(c0 + off, c) for c0, c in t["captions"]]
    return dict(opener=off, body_end=off + t_body, total=_duration(out_mp4), steps=timeline)


def _duration(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())
