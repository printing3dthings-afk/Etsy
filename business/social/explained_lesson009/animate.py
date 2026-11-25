"""Explained, Lesson 009 ("Hole size sets the note"): our ocarina voicing test whistle, three
notes from Scott's own recording (2026-11-25). Same identity and engine as Lessons 006-008.

Scott OK'd using his recordings' audio for this lesson (2026-11-20, ocarina BRIEF.md). The notes
are his retest with sound (2026-11-18): all holes closed 1478 Hz, the 5 mm hole open 1822 Hz, the
8 mm hole open 2125 Hz, measured from the audio (facts/notes.json). Each note's own clip plays
under its card, so what you hear is what the number says. The whistle is drawn as a diagram and
labelled one: no render or photo is passed off as the print.

    python3 animate.py OUT_DIR [--clean] [--frame T]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "explained_lesson006"))
from animate import (CREAM, INK, ORANGE, TEAL, CARD, W, H, Frame, mix, clamp, prog,  # noqa: E402
                     ease_out, ease_in_out, ease_back, font, wrap)

RECORDING = Path("/root/.claude/uploads/d6e7a036-e991-5b99-8baf-18b52486dbea/754d114a-RPReplay_Final1794999756.mp4")
AUDIO = Path("/tmp/lesson009_whistle_retest.m4a")   # the recording's audio. Not committed: the repo is public,
                                                   # and only the three notes are cleared for use
FACTS = json.loads((HERE / "facts" / "notes.json").read_text())
N = FACTS["notes"]
DUR = 30.0
LESSON = "LESSON 009"
CREDIT = "OUR VOICING TEST WHISTLE · SCOTT'S RECORDING · PITCH MEASURED FROM THE AUDIO"
# (card start, note key, label, colour): each note plays 0.6 s after its card lands
CARDS = [(5.0, "closed", "ALL HOLES CLOSED", INK), (10.0, "hole5", "5 MM HOLE OPEN", TEAL),
         (15.0, "hole8", "8 MM HOLE OPEN", ORANGE)]
PLAY_AT = {k: a + 0.8 for a, k, _, _ in CARDS}

VO = [
    (0.3, 2.6, "Why does an ocarina have different-sized holes?"),
    (2.8, 4.8, "We printed a test whistle to find out."),
    (5.2, 7.0, "All holes closed:"),
    (9.0, 9.9, f"{N['closed']['hz']} hertz."),
    (10.2, 12.0, "Open the 5 millimetre hole:"),
    (14.0, 14.9, f"{N['hole5']['hz']}. Higher."),
    (15.2, 17.0, "Open the bigger 8 millimetre hole:"),
    (19.0, 19.9, f"{N['hole8']['hz']}. Higher still."),
    (20.3, 23.0, "The bigger the open hole, the higher the note."),
    (23.2, 26.4, "That's why every hole on an ocarina is its own size."),
    (26.8, 29.8, "Send this to the maker who wants to print an instrument."),
]
SCENES = [("HOOK", 0.0, 5.0), ("NOTES", 5.0, 20.2), ("RULE", 20.2, DUR)]


def chrome(f):
    f.text((60, 70), "3D PRINTING, EXPLAINED", font("semi", 30), INK, anchor="lm")
    f.rrect((826, 46, 1020, 96), 12, outline=ORANGE, width=3)
    f.text((923, 71), LESSON, font("semi", 30), ORANGE)
    f.text((60, 1862), "ONBRANDCRAFTZ", font("semi", 24), INK, anchor="lm")


def caption(f, t):
    for a, b, s in VO:
        al = min(prog(t, a - 0.15, a + 0.1), 1 - prog(t, b + 0.1, b + 0.3)) if t < b + 0.3 else 0
        if al <= 0:
            continue
        fnt = font("reg", 40)
        ls = wrap(s, fnt, 860)
        h = 66 + 52 * (len(ls) - 1)
        y0 = 1560
        f.rrect((50, y0, 1030, y0 + h + 24), 18, fill=mix(CREAM, INK, al))
        for i, l in enumerate(ls):
            f.text((540, y0 + 12 + 33 + 52 * i), l, fnt, CREAM, alpha=al, bg=mix(CREAM, INK, al))


def fade(t, a, b, d=0.35):
    return min(ease_out(prog(t, a, a + d)), 1 - prog(t, b - d, b))


def title(f, t, s, y, a0, col=INK, px=96):
    p = ease_out(prog(t, a0, a0 + 0.55))
    f.text((540, y + 36 * (1 - p)), s, font("anton", px), col, alpha=p)


def whistle(f, cx, cy, sc, open5, open8, al):
    """The test whistle as a diagram: a rounded body, the mouthpiece, two finger holes."""
    if al <= 0:
        return
    body = mix(CREAM, CARD, al)
    edge = mix(CREAM, INK, al)
    f.rrect((cx - 230 * sc, cy - 120 * sc, cx + 230 * sc, cy + 120 * sc), 110 * sc, fill=body, outline=edge,
            width=max(int(5 * sc), 2))
    f.rrect((cx - 340 * sc, cy - 36 * sc, cx - 222 * sc, cy + 36 * sc), 18 * sc, fill=body, outline=edge,
            width=max(int(5 * sc), 2))
    f.rrect((cx - 214 * sc, cy - 60 * sc, cx - 176 * sc, cy - 20 * sc), 6 * sc, fill=edge)     # the window
    for (hx, r, op, col) in ((cx + 10 * sc, 26 * sc, open5, TEAL), (cx + 130 * sc, 42 * sc, open8, ORANGE)):
        if op > 0:
            f.circle((hx, cy), r, fill=mix(body, INK, op * al), outline=mix(CREAM, col, al), width=max(int(5 * sc), 2))
        else:
            f.circle((hx, cy), r, fill=mix(body, (220, 214, 200), al), outline=edge, width=max(int(4 * sc), 2))
    f.text((cx + 10 * sc, cy + 78 * sc), "5 mm", font("bold", int(30 * sc)), TEAL, alpha=al)
    f.text((cx + 130 * sc, cy + 92 * sc), "8 mm", font("bold", int(30 * sc)), ORANGE, alpha=al)


def wave(f, t, cx, cy, hz, start, col, al):
    """A sine trace drawn faster for a higher note, while its clip plays."""
    k = prog(t, start, start + 0.25) * (1 - prog(t, start + 1.4, start + 1.7))
    if k <= 0 or al <= 0:
        return
    import math
    cyc = hz / 1478 * 4.0
    pts = [(cx - 420 + i * 8.4, cy + 70 * k * math.sin(2 * math.pi * (i / 100 * cyc - t * 3))) for i in range(101)]
    f.line(pts, col, 8, alpha=al * k)


def hook(f, t):
    al = fade(t, 0.0, 5.0)
    title(f, t, "HOLE SIZE", 300, 0.25, INK, 120)
    title(f, t, "SETS THE NOTE", 430, 0.45, ORANGE, 120)
    whistle(f, 590, 860, 1.25, 0, 0, ease_out(prog(t, 1.0, 1.6)) * al)
    f.text((540, 1130), "Diagram of our test whistle", font("reg", 28), INK, alpha=ease_out(prog(t, 1.4, 1.9)) * al)
    f.text((540, 1260), "PRINTED ON OUR P1S", font("anton", 64), TEAL, alpha=ease_out(prog(t, 2.8, 3.3)) * al)


def notes(f, t):
    for k, (a, key, label, col) in enumerate(CARDS):
        b = a + 5.0 if k < 2 else 20.2
        if not (a - 0.01 <= t < b + 0.4):
            continue
        al = fade(t, a, b)
        title(f, t, label, 300, a + 0.05, col, 96)
        whistle(f, 590, 640, 1.15, 1.0 if key == "hole5" else 0.0, 1.0 if key == "hole8" else 0.0, al)
        wave(f, t, 540, 960, N[key]["hz"], PLAY_AT[key], col, al)
        p = ease_out(prog(t, a + 3.8, a + 4.3)) * al
        f.text((540, 1200), f"{N[key]['hz']} Hz", font("anton", 150), col, alpha=p)
        f.text((540, 1330), "measured from the recording", font("reg", 30), INK, alpha=p)
        f.text((540, 1420), "PLAYING: SCOTT'S REAL RECORDING", font("semi", 30), mix(CREAM, INK, 0.7),
               alpha=clamp(prog(t, PLAY_AT[key], PLAY_AT[key] + 0.2) - prog(t, PLAY_AT[key] + 1.6, PLAY_AT[key] + 1.9)) * al)


def rule(f, t):
    a0 = 20.2
    al = ease_out(prog(t, a0, a0 + 0.4))
    title(f, t, "BIGGER HOLE, HIGHER NOTE", 300, a0 + 0.1, TEAL, 84)
    vmax = 2125
    for i, (key, lab, col) in enumerate([("closed", "CLOSED", INK), ("hole5", "5 MM OPEN", TEAL), ("hole8", "8 MM OPEN", ORANGE)]):
        p = ease_out(prog(t, a0 + 0.4 + 0.3 * i, a0 + 1.2 + 0.3 * i)) * al
        y = 470 + i * 200
        f.text((80, y), lab, font("bold", 36), col, anchor="lm", alpha=clamp(p * 2))
        L = 860 * N[key]["hz"] / vmax * ease_in_out(prog(t, a0 + 0.4 + 0.3 * i, a0 + 1.2 + 0.3 * i))
        if L > 4:
            f.rrect((80, y + 34, 80 + L, y + 124), 16, fill=mix(CREAM, col, al))
            f.text((80 + L - 24, y + 79), f"{N[key]['hz']} Hz", font("anton", 56), CREAM, anchor="rm",
                   alpha=clamp(p), bg=col)
    p = ease_out(prog(t, 23.2, 23.8)) * al
    f.rrect((90, 1090 + 30 * (1 - p), 990, 1250 + 30 * (1 - p)), 22, fill=mix(CREAM, CARD, p),
            outline=mix(CREAM, ORANGE, p), width=5)
    f.text((540, 1140 + 30 * (1 - p)), "SO EVERY OCARINA HOLE", font("anton", 54), INK, alpha=p)
    f.text((540, 1205 + 30 * (1 - p)), "IS ITS OWN SIZE", font("anton", 54), ORANGE, alpha=p)
    f.text((540, 1340), "SEND THIS TO A MAKER", font("anton", 64), INK, alpha=ease_out(prog(t, 26.8, 27.4)) * al)
    f.text((540, 1460), CREDIT, font("semi", 20), mix(CREAM, INK, 0.7), alpha=al)


DRAW = {"HOOK": hook, "NOTES": notes, "RULE": rule}


def frame_at(t, clean=False):
    f = Frame()
    chrome(f)
    for name, a, b in SCENES:
        if a - 0.01 <= t < b + 0.4:
            DRAW[name](f, t)
    if not clean:
        caption(f, t)
    return f.out()


def audio_track(out):
    """Each note's own clip from Scott's recording, placed under its card; silence elsewhere.
    Built sample by sample in numpy: an ffmpeg atrim/adelay/amix graph wrote a 5.8 s track with
    no notes in it (2026-11-25), and a placed clip is easy to check here."""
    import wave
    import tempfile
    import numpy as np
    if not AUDIO.exists():
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(RECORDING), "-vn", "-c:a", "aac",
                        "-b:a", "192k", str(AUDIO)], check=True)
    sr = 48000
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "src.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(AUDIO), "-ac", "1", "-ar", str(sr),
                        str(src)], check=True)
        with wave.open(str(src)) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
        y = np.zeros(int(DUR * sr), np.float32)
        ramp = int(0.04 * sr)
        for key, at in PLAY_AT.items():
            a, b = N[key]["clip"]
            seg = x[int(a * sr):int(b * sr)].copy()
            seg[:ramp] *= np.linspace(0, 1, ramp)
            seg[-ramp:] *= np.linspace(1, 0, ramp)
            i = int(at * sr)
            y[i:i + len(seg)] += seg
        dst = Path(td) / "notes.wav"
        with wave.open(str(dst), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(np.clip(y, -32768, 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(dst), "-ac", "2", "-c:a", "aac",
                        "-b:a", "192k", str(out)], check=True)


def render(out_dir, fps=30, clean=False):
    out_dir = Path(out_dir)
    silent = out_dir / f"lesson009{'_clean' if clean else ''}_silent.mp4"
    nf = int(round(DUR * fps))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)],
                          stdin=subprocess.PIPE)
    for i in range(nf):
        ff.stdin.write(frame_at(i / fps, clean).tobytes())
    ff.stdin.close()
    ff.wait()
    notes_a = out_dir / "notes.m4a"
    audio_track(notes_a)
    out = out_dir / f"lesson009{'_clean' if clean else ''}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(notes_a), "-c:v", "copy",
                    "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    silent.unlink()
    print(out, f"{DUR} s, {nf} frames")


def script_md():
    lines = ["# Lesson 009 script: the narration, timed", "",
             "Generated from `VO` in `animate.py`; the numbers are read from `facts/notes.json`.",
             "The video carries Scott's three real notes as its audio, each under its own card "
             f"(at {', '.join(f'{v:.1f} s' for v in PLAY_AT.values())}). Keep them audible under the voice-over and music.",
             "", "| start | end | line | scene |", "|---|---|---|---|"]
    for a, b, s in VO:
        sc = next(n for n, x, y in SCENES if x <= a < y)
        lines.append(f"| {a:.1f} | {b:.1f} | {s} | {sc} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--frame", type=float)
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.frame is not None:
        p = Path(a.out) / f"frame_{a.frame:.1f}.png"
        frame_at(a.frame, a.clean).save(p)
        print(p)
        return
    (HERE / "SCRIPT.md").write_text(script_md())
    render(a.out, a.fps, a.clean)


if __name__ == "__main__":
    main()
