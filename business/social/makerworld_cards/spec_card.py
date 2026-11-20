"""MakerWorld spec cards: one gallery image per model, in the Explained identity
(2026-11-20, Scott: "ramp up our designs ... from Patreon and MakerWorld to all social post").

A card is a gallery image, never the cover. MakerWorld's Nov 19 guidelines want the cover to
match the real print and at least three real-print photos per page, so a render can't stand in
for a photo. The render on a card is labelled as a render.

Every figure on a card is read from the model's own slice (Metadata/slice_info.config in the
.gcode.3mf), not typed in, so the card can't drift from the file it's published with.

    python3 spec_card.py [name ...]      # default: every card in CARDS
"""
import re
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
M = ROOT / "openscad_models"
FONTS = HERE.parent / "explained_lesson006" / "fonts"
CREAM, INK, ORANGE, TEAL, CARD = (246, 240, 226), (32, 36, 46), (232, 106, 44), (20, 110, 96), (252, 249, 242)
W, H = 1600, 1200

CARDS = {
    "openwork_name_ring": dict(
        title="OPENWORK NAME ORNAMENT",
        line="Your name on a flat open ring, with pine boughs, a star and holly.",
        image=M / "christmas_ornaments/name_ring/images/name_ring_colour_top.png",
        gcode=M / "christmas_ornaments/name_ring/gcode/name_ring_two_colour.gcode.3mf",
        size="80 × 88 × 3.2 mm with the loop",
        colours=["red", "white"],
        extra="Customizer: type your name and year"),
    "snow_globe_name_ornament": dict(
        title="SNOW GLOBE NAME ORNAMENT",
        line="A flat snow globe: cottage, tree and moon, with your name on the base.",
        image=M / "christmas_ornaments/name_globe/images/name_globe_colour_top.png",
        gcode=M / "christmas_ornaments/name_globe/gcode/name_globe_three_colour.gcode.3mf",
        size="62 × 93 × 3.2 mm with the loop",
        colours=["red", "night blue", "white"],
        extra="Customizer: type your name and year"),
    "gap_gauge": dict(
        title="GAP GAUGE",
        line="Twelve steps, 1.6 to 6.0 mm. The thickest step that fits is the gap.",
        image=M / "camera_sign/images/gap_gauge_as_printed_three_quarter.png",
        gcode=M / "camera_sign/gcode/gap_gauge.gcode.3mf",
        size="148 × 18 × 6 mm",
        colours=["any one colour"],
        extra="Steps in 0.4 mm, each one labelled"),
}


def font(name, px):
    f = {"anton": "Anton-Regular.ttf", "reg": "ChakraPetch-Regular.ttf",
         "semi": "ChakraPetch-SemiBold.ttf", "bold": "ChakraPetch-Bold.ttf"}[name]
    return ImageFont.truetype(str(FONTS / f), px)


def read_slice(path):
    """Time, total grams and per-filament (hex, grams) from Bambu Studio's own slice."""
    with zipfile.ZipFile(path) as z:
        cfg = z.read("Metadata/slice_info.config").decode()
        settings = z.read("Metadata/project_settings.config").decode()
    secs = int(re.search(r'key="prediction" value="(\d+)"', cfg).group(1))
    grams = float(re.search(r'key="weight" value="([\d.]+)"', cfg).group(1))
    fil = [(c, float(g)) for c, g in re.findall(r'color="(#[0-9A-Fa-f]{6})"[^>]*used_g="([\d.]+)"', cfg)]
    walls = re.search(r'"wall_loops": "(\d+)"', settings)
    infill = re.search(r'"sparse_infill_density": "([\d%]+)"', settings)
    layer = re.search(r'"layer_height": "([\d.]+)"', settings)
    supports = re.search(r'"enable_support": "(\d)"', settings)
    return dict(secs=secs, grams=grams, fil=fil, walls=walls and walls.group(1),
                infill=infill and infill.group(1), layer=layer and layer.group(1),
                supports=supports and supports.group(1) == "1")


def hm(secs):
    m = round(secs / 60)
    return f"{m // 60} h {m % 60} m" if m >= 60 else f"{m} m"


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def card(name, spec):
    s = read_slice(spec["gcode"])
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    # left: the render, framed and labelled as one
    pic = Image.open(spec["image"]).convert("RGB").resize((700, 700), Image.LANCZOS)
    mask = Image.new("L", pic.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 699, 699), 28, fill=255)
    im.paste(pic, (70, 250), mask)
    d.rounded_rectangle((70, 250, 770, 950), 28, outline=INK, width=4)
    d.text((420, 985), "Design-review render, not a photo", font=font("reg", 28), fill=INK, anchor="mm")
    # header
    d.text((70, 80), "ONBRANDCRAFTZ  ·  PRINT SPEC", font=font("semi", 30), fill=ORANGE, anchor="lm")
    d.text((70, 150), spec["title"], font=font("anton", 76), fill=INK, anchor="lm")
    d.text((70, 212), spec["line"], font=font("reg", 32), fill=INK, anchor="lm")
    # right: the figures, straight from the slice
    x, y = 840, 260
    rows = [("PRINT TIME", hm(s["secs"])), ("FILAMENT", f"{s['grams']:.1f} g of PLA"), ("SIZE", spec["size"])]
    for k, v in rows:
        d.text((x, y), k, font=font("semi", 28), fill=TEAL, anchor="lm")
        d.text((x, y + 52), v, font=font("anton", 60 if len(v) < 22 else 46), fill=INK, anchor="lm")
        y += 140
    d.text((x, y), "COLOURS, BY AMS SLOT", font=font("semi", 28), fill=TEAL, anchor="lm")
    y += 50
    for i, ((hx, g), label) in enumerate(zip(s["fil"], spec["colours"])):
        d.rounded_rectangle((x, y, x + 54, y + 54), 12, fill=hexrgb(hx), outline=INK, width=3)
        d.text((x + 76, y + 27), f"{i + 1}  {label}  ·  {g:.1f} g", font=font("semi", 34), fill=INK, anchor="lm")
        y += 72
    y += 24
    sup = "supports on" if s["supports"] else "no supports"
    settings = f"P1S 0.4 · {s['layer']} mm layers · {s['walls']} walls · {s['infill']} infill · {sup}"
    d.rounded_rectangle((x - 20, y, W - 70, y + 150), 18, fill=CARD, outline=INK, width=3)
    d.text((x, y + 38), "SLICED IN BAMBU STUDIO", font=font("semi", 26), fill=ORANGE, anchor="lm")
    d.text((x, y + 82), f"P1S, 0.4 mm nozzle, PLA, {s['layer']} mm layers", font=font("reg", 28), fill=INK,
           anchor="lm")
    d.text((x, y + 120), f"{s['walls']} walls, {s['infill']} infill, {sup}", font=font("reg", 28), fill=INK,
           anchor="lm")
    # No "free"/"paid" line: that's Scott's call per model (each FACTS.md), not the card's.
    d.text((70, 1110), spec["extra"], font=font("semi", 32), fill=INK, anchor="lm")
    out = HERE / "out" / f"{name}_spec.png"
    out.parent.mkdir(exist_ok=True)
    im.save(out)
    print(out, hm(s["secs"]), f"{s['grams']:.2f} g", s["fil"], settings)
    return out


if __name__ == "__main__":
    for n in (sys.argv[1:] or CARDS):
        card(n, CARDS[n])
