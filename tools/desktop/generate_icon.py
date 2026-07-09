#!/usr/bin/env python3
"""
Generates the desktop app icon from the same cyan/blue "orb" palette already used
throughout Frank's UI (frank_hud_mockup.py's orb glow colors: rgba(58,214,255,...) /
rgba(122,232,255,...)) -- no new external brand asset needed, and nothing here reads
from data/brand/ (gitignored, machine-local, may not even exist).

Produces:
  desktop/build/icon.png  -- 1024x1024 master (electron-builder's Linux/AppImage icon,
                              and the source the macOS CI job converts to .icns via
                              `iconutil`, a Mac-only tool that can't run here)
  desktop/build/icon.ico  -- Windows multi-resolution icon, built directly with Pillow
                              (no external tool needed, works cross-platform)

Deliberately no text/monogram baked in -- at 16x16/32x32 taskbar sizes a letterform
just reads as noise; a simple radial-gradient orb with a soft glow stays legible at
every size electron-builder actually uses.

Run:  python tools/desktop/generate_icon.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO_ROOT / "desktop" / "build"

# Same palette as the orb's voice-reactive glow in frank_hud_mockup.py.
CYAN_CORE = (122, 232, 255)
CYAN_MID = (58, 214, 255)
DEEP_NAVY = (10, 22, 38)
BG_TRANSPARENT = (0, 0, 0, 0)

SIZE = 1024


def _radial_orb() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), BG_TRANSPARENT)
    cx = cy = SIZE / 2
    max_r = SIZE * 0.42

    # Soft outer glow first (drawn larger + blurred), then the crisp orb body on top --
    # mirrors the actual orb's own CSS glow (box-shadow-style halo behind a solid core).
    glow = Image.new("RGBA", (SIZE, SIZE), BG_TRANSPARENT)
    gdraw = ImageDraw.Draw(glow)
    glow_r = max_r * 1.35
    gdraw.ellipse(
        [cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r],
        fill=(*CYAN_MID, 140),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(SIZE * 0.05))
    img = Image.alpha_composite(img, glow)

    # Crisp radial-gradient sphere body: bright cyan core fading to deep navy edge, with
    # a small bright highlight offset toward the upper-left (gives it dimensionality
    # instead of reading as a flat circle at small sizes).
    body = Image.new("RGBA", (SIZE, SIZE), BG_TRANSPARENT)
    bdraw = ImageDraw.Draw(body)
    steps = 160
    for i in range(steps, 0, -1):
        t = i / steps  # 1.0 at outer edge -> 0.0 at center
        r = max_r * t
        # ease so the bright core stays small and punchy, matching the real orb's look
        blend = t ** 1.6
        color = tuple(int(DEEP_NAVY[c] * blend + CYAN_CORE[c] * (1 - blend)) for c in range(3))
        bdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, 255))

    # Highlight
    hl = Image.new("RGBA", (SIZE, SIZE), BG_TRANSPARENT)
    hdraw = ImageDraw.Draw(hl)
    hl_cx, hl_cy = cx - max_r * 0.32, cy - max_r * 0.35
    hl_r = max_r * 0.30
    hdraw.ellipse([hl_cx - hl_r, hl_cy - hl_r, hl_cx + hl_r, hl_cy + hl_r], fill=(255, 255, 255, 110))
    hl = hl.filter(ImageFilter.GaussianBlur(SIZE * 0.03))
    body = Image.alpha_composite(body, hl)

    img = Image.alpha_composite(img, body)
    return img


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = _radial_orb()
    png_path = OUT_DIR / "icon.png"
    master.save(png_path)
    print(f"Wrote {png_path} ({master.size[0]}x{master.size[1]})")

    ico_path = OUT_DIR / "icon.ico"
    # Pillow writes a real multi-resolution .ico directly -- Windows picks whichever
    # embedded size fits (taskbar, Start Menu, file explorer, etc.).
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    master.save(ico_path, format="ICO", sizes=ico_sizes)
    print(f"Wrote {ico_path} (sizes: {ico_sizes})")

    print("\n.icns (macOS) is generated during the macOS CI job via `iconutil` from "
          "icon.png -- that tool doesn't exist outside macOS, so it can't be produced here.")


if __name__ == "__main__":
    main()
