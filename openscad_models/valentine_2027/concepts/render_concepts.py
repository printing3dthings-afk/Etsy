#!/usr/bin/env python3
"""Render the Valentine's 2027 concept forms and lay them out for Scott
(2026-10-26). Concepts only: massing to pick a form from, not print files.

    python3 render_concepts.py lanterns [1 3 ...]
    python3 render_concepts.py shops [1 3 ...]

Each form gets a colour render (three-quarter, front to -y) and a lit night
render (all white plastic, a warm point light where the tealight's flame
would be). Every image is a render of a model, never a photo of a print.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from geo import save  # noqa: E402

MESH, IMG = HERE / "meshes", HERE / "images"
NIGHT = ROOT / "openscad_models/christmas_lanterns/concepts/night_render.py"
PALETTES = {
    "lanterns": {"frame": "#9B2335", "glass": "#F4F1EA", "art": "#4A1F2A", "accent": "#D4A64A"},
    "shops": {"body": "#7A4A33", "roof": "#3B2A2E", "trim": "#F4F1EA", "accent": "#C8314A", "glass": "#F4F1EA"},
}


def rgb(h):
    h = h.lstrip("#")
    return ",".join(f"{int(h[i:i + 2], 16) / 255:.3f}" for i in (0, 2, 4))


def forms_of(kind):
    if kind == "lanterns":
        from lantern_forms import FORMS
    else:
        from shop_forms import FORMS
    return FORMS


def build(kind, k):
    name, fn, light_z = forms_of(kind)[k]
    stem = f"{kind[:-1]}{k}"
    paths = save(fn(), MESH, stem)
    pal = dict(PALETTES[kind])
    if kind == "shops":
        from shop_forms import PAL
        pal.update(PAL.get(k, {}))
    parts = sum([["--part", f"{p}:{rgb(pal.get(n, '#F4F1EA'))}"] for n, p in paths.items()], [])
    colour = IMG / f"{stem}_colour.png"
    night = IMG / f"{stem}_night.png"
    subprocess.run([sys.executable, str(ROOT / "tools/blender_render.py"), *parts, "-o", str(colour),
                    "--azimuth", "-35", "--elevation", "20", "--samples", "48", "--resolution", "900",
                    "--timeout", "900"], check=True, capture_output=True)
    subprocess.run([sys.executable, str(NIGHT), str(night), *map(str, paths.values()), "--light-z", str(light_z),
                    "--az", "-30", "--el", "12", "--samples", "96", "--res", "900"], check=True, capture_output=True)
    return k


def sheet(kind):
    forms = forms_of(kind)
    stem = kind[:-1]
    T, top = 560, 54
    ks = [k for k in sorted(forms) if (IMG / f"{stem}{k}_colour.png").exists()]
    S = Image.new("RGB", (T * len(ks), 2 * T + top + 30), "#1A1416")
    d = ImageDraw.Draw(S)
    try:
        font = ImageFont.truetype(str(ROOT / "fonts/PlayfairDisplay-Bold.ttf"), 26)
        small = ImageFont.truetype(str(ROOT / "fonts/PlayfairDisplay-Bold.ttf"), 17)
    except OSError:
        font = small = ImageFont.load_default()
    for i, k in enumerate(ks):
        for j, tag in enumerate(("colour", "night")):
            im = Image.open(IMG / f"{stem}{k}_{tag}.png").convert("RGB")
            w, h = im.size
            c = int(min(w, h) * 0.08)
            S.paste(im.crop((c, c, w - c, h - c)).resize((T, T), Image.LANCZOS), (T * i, top + j * T))
        d.text((T * i + 16, 12), f"{k}  {forms[k][0]}", fill="#F4E9E1", font=font)
    d.text((16, top + 2 * T + 6), "Concept renders of models, not photos of prints. Top: colour. Bottom: printed white, lit by a tealight.",
           fill="#BFAFB3", font=small)
    out = HERE / f"{stem}_forms.jpg"
    S.save(out, quality=88)
    return out


if __name__ == "__main__":
    kind = sys.argv[1]
    ks = [int(a) for a in sys.argv[2:]] or sorted(forms_of(kind))
    IMG.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(2) as ex:
        for k in ex.map(lambda k: build(kind, k), ks):
            print("rendered", kind, k, flush=True)
    print(sheet(kind))
