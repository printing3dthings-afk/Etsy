#!/usr/bin/env python3
"""
generate_sign_info_graphics.py — SS1001 listing photos 7, 9, 10

Deterministic PIL info graphics built from the REAL design files — text and
designs are exact by construction (no AI rendering, nothing to verify):

  photo_07 — Bambu Studio 3-step how-to (import → split by color → assign AMS)
  photo_09 — What's included / ZIP contents specs card
  photo_10 — All 5 design previews side by side
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
OUT_DIR     = Path("data/3d_print_signs/america_250/listing_photos/final")
FONTS       = Path("assets/fonts")
C           = 2400  # canvas

NAVY   = (27, 37, 80)
RED    = (178, 52, 49)
GOLD   = (200, 148, 62)
CREAM  = (247, 242, 232)
INK    = (35, 30, 26)

DESIGNS = [
    ("Main Eagle",      DESIGNS_DIR / "america250_ai_color_raw.jpg"),
    ("Medallion",       DESIGNS_DIR / "america250_design2_medallion.jpg"),
    ("Art Deco",        DESIGNS_DIR / "america250_design3_artdeco.jpg"),
    ("Vintage Stamp",   DESIGNS_DIR / "america250_design4_stamp.jpg"),
    ("Heraldic Shield", DESIGNS_DIR / "america250_design5_shield.jpg"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def rounded_thumb(path: Path, size: int, radius: int = 24) -> Image.Image:
    img = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius, fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0))
    out.putalpha(mask)
    return out


def drop_shadow(canvas: Image.Image, box: tuple, radius: int = 24, blur: int = 18):
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 8, y0 + 10, x1 + 8, y1 + 10],
                                         radius, fill=(0, 0, 0, 70))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def center_text(d: ImageDraw.ImageDraw, cx: int, y: int, text: str,
                f: ImageFont.FreeTypeFont, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def split_by_color(path: Path, n: int = 4, size: int = 360) -> list[Image.Image]:
    """Quantize the design to n colors and return one layer image per color —
    visually demonstrates Bambu Studio's Split-by-Color on the REAL design."""
    img = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    q = img.quantize(colors=n, method=Image.MEDIANCUT)
    pal = q.getpalette()[:n * 3]
    colors = [tuple(pal[i * 3:i * 3 + 3]) for i in range(n)]
    layers = []
    qdata = list(q.getdata())
    for ci, color in enumerate(colors):
        layer = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        ldata = [(color + (255,)) if v == ci else (0, 0, 0, 0) for v in qdata]
        layer.putdata(ldata)
        layers.append((color, layer))
    return layers


# ── Photo 07 — Bambu Studio 3-step how-to ─────────────────────────────────────
def photo_07():
    canvas = Image.new("RGBA", (C, C), CREAM + (255,))
    d = ImageDraw.Draw(canvas)

    h1 = font("Poppins-Bold.ttf", 110)
    h2 = font("Poppins-SemiBold.ttf", 62)
    body = font("Poppins-Regular.ttf", 48)
    step_f = font("Poppins-Bold.ttf", 72)

    center_text(d, C // 2, 90, "HOW TO PRINT", h1, NAVY)
    center_text(d, C // 2, 230, "in Bambu Studio — 3 easy steps", h2, GOLD)

    panel_w, panel_h = 660, 1330
    gap = (C - 3 * panel_w) // 4
    top = 430
    design_path = DESIGNS[0][1]

    steps = [
        ("1", "IMPORT THE SVG", "Drag & drop SVG · set height 6mm"),
        ("2", "PAINT THE COLORS", "Press N → Fill tool → click each region"),
        ("3", "ASSIGN AMS SLOTS", "Colors auto-map · check · Slice!"),
    ]

    for i, (num, title, sub) in enumerate(steps):
        x0 = gap + i * (panel_w + gap)
        box = (x0, top, x0 + panel_w, top + panel_h)
        drop_shadow(canvas, box)
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle(box, 36, fill=(255, 255, 255, 255),
                            outline=NAVY, width=4)

        # numbered circle
        cx = x0 + panel_w // 2
        d.ellipse([cx - 70, top + 50, cx + 70, top + 190], fill=RED)
        center_text(d, cx, top + 80, num, step_f, (255, 255, 255))

        center_text(d, cx, top + 240, title, font("Poppins-Bold.ttf", 56), NAVY)
        center_text(d, cx, top + 320, sub, font("Poppins-Regular.ttf", 42), INK)

        iy = top + 430
        if i == 0:
            thumb = rounded_thumb(design_path, 520)
            canvas.alpha_composite(thumb, (cx - 260, iy))
            d = ImageDraw.Draw(canvas)
            center_text(d, cx, iy + 590, "SS1001_america250_main.svg",
                        font("Poppins-Regular.ttf", 36), INK)
        elif i == 1:
            layers = split_by_color(design_path, 4, 250)
            cell = 270
            gx0 = cx - cell - 12
            gy0 = iy + 20
            for j, (color, layer) in enumerate(layers):
                gx = gx0 + (j % 2) * (cell + 24)
                gy = gy0 + (j // 2) * (cell + 24)
                d.rounded_rectangle([gx, gy, gx + cell, gy + cell], 18,
                                    fill=(250, 248, 243, 255), outline=INK, width=3)
                canvas.alpha_composite(layer, (gx + 10, gy + 10))
                d = ImageDraw.Draw(canvas)
            center_text(d, cx, gy0 + 2 * cell + 70, "4 color regions — fill each",
                        font("Poppins-Regular.ttf", 36), INK)
        else:
            sw = 110
            labels = ["Navy", "Red", "Gold", "Cream"]
            cols = [NAVY, RED, GOLD, (235, 225, 205)]
            for j, (col, lab) in enumerate(zip(cols, labels)):
                sy = iy + j * 170
                d.rounded_rectangle([cx - 250, sy, cx - 250 + sw, sy + sw],
                                    20, fill=col, outline=INK, width=3)
                d.text((cx - 110, sy + 26), f"AMS Slot {j+1} — {lab}",
                       font=font("Poppins-SemiBold.ttf", 42), fill=INK)

    d = ImageDraw.Draw(canvas)
    center_text(d, C // 2, C - 240,
                "Works on any Bambu printer with AMS  |  235×235mm, scale to any size",
                font("Poppins-SemiBold.ttf", 46), NAVY)
    center_text(d, C // 2, C - 150,
                "Full written guide included in your download (README.txt)",
                font("Poppins-Regular.ttf", 42), INK)

    out = OUT_DIR / "photo_07_bambu_howto.jpg"
    canvas.convert("RGB").save(out, "JPEG", quality=95, dpi=(300, 300))
    print(f"✓ {out}")


# ── Photo 09 — What's included / specs ────────────────────────────────────────
def photo_09():
    canvas = Image.new("RGBA", (C, C), NAVY + (255,))
    d = ImageDraw.Draw(canvas)

    center_text(d, C // 2, 100, "WHAT'S INCLUDED", font("Poppins-Bold.ttf", 120), CREAM)
    center_text(d, C // 2, 260, "America 250 Sign SVG Pack — Digital Download",
                font("Poppins-SemiBold.ttf", 58), GOLD)

    # 5 design thumbnails fanned across the top
    tsize = 400
    total_w = 5 * tsize + 4 * 40
    x = (C - total_w) // 2
    for name, path in DESIGNS:
        thumb = rounded_thumb(path, tsize)
        drop_shadow(canvas, (x, 420, x + tsize, 420 + tsize), blur=14)
        canvas.alpha_composite(thumb, (x, 420))
        d = ImageDraw.Draw(canvas)
        center_text(d, x + tsize // 2, 840, name,
                    font("Poppins-Regular.ttf", 38), CREAM)
        x += tsize + 40

    # Specs card
    box = (300, 1000, C - 300, 2080)
    drop_shadow(canvas, box)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(box, 40, fill=CREAM + (255,))

    items = [
        "5 unique SVG sign designs — one file each",
        "Pre-sized 235×235mm — Bambu plate-ready",
        "Max 4 colors per design — AMS 4-slot ready",
        "Scales to ANY size — clean vector files",
        "README with step-by-step print guide",
        "Instant download — ZIP file, no shipping",
    ]
    iy = 1080
    for text in items:
        # hand-drawn checkmark (Poppins has no U+2713 glyph)
        d.line([(430, iy + 42), (462, iy + 74), (518, iy + 6)], fill=RED, width=14, joint="curve")
        d.text((570, iy), text, font=font("Poppins-SemiBold.ttf", 60), fill=INK)
        iy += 160

    d.rounded_rectangle([300, 2160, C - 300, 2310], 30, fill=RED)
    center_text(d, C // 2, 2192, "DIGITAL FILES ONLY — NO PHYSICAL SIGN SHIPPED",
                font("Poppins-Bold.ttf", 58), (255, 255, 255))

    out = OUT_DIR / "photo_09_whats_included.jpg"
    canvas.convert("RGB").save(out, "JPEG", quality=95, dpi=(300, 300))
    print(f"✓ {out}")


# ── Photo 10 — all 5 previews side by side ────────────────────────────────────
def photo_10():
    canvas = Image.new("RGBA", (C, C), CREAM + (255,))
    d = ImageDraw.Draw(canvas)

    center_text(d, C // 2, 90, "5 DESIGNS IN THIS PACK", font("Poppins-Bold.ttf", 110), NAVY)
    center_text(d, C // 2, 240, "America 250th Anniversary · 1776–2026",
                font("Poppins-SemiBold.ttf", 60), RED)

    # Top row: 3 designs | bottom row: 2 designs centered
    size = 680
    rows = [DESIGNS[:3], DESIGNS[3:]]
    y = 420
    for row in rows:
        total_w = len(row) * size + (len(row) - 1) * 80
        x = (C - total_w) // 2
        for name, path in row:
            drop_shadow(canvas, (x, y, x + size, y + size))
            thumb = rounded_thumb(path, size)
            canvas.alpha_composite(thumb, (x, y))
            d = ImageDraw.Draw(canvas)
            center_text(d, x + size // 2, y + size + 24, name,
                        font("Poppins-SemiBold.ttf", 52), INK)
            x += size + 80
        y += size + 140

    center_text(d, C // 2, C - 130, "All five included · SVG vector · Instant Download",
                font("Poppins-SemiBold.ttf", 52), NAVY)

    out = OUT_DIR / "photo_10_design_lineup.jpg"
    canvas.convert("RGB").save(out, "JPEG", quality=95, dpi=(300, 300))
    print(f"✓ {out}")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    photo_07()
    photo_09()
    photo_10()
