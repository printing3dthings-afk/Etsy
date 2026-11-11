#!/usr/bin/env python3
"""Transparent-background renders of the banner's buildings, from the same STL
parts and README colours as business/store_kit/render_covers.py (the sale ZIPs).

Cutting the store renders out of their studio background left a grey halo and the
floor's shadow under every building, so these are rendered again with the floor
as a shadow catcher on a transparent film: the building plus its own soft contact
shadow, nothing else. The shared renderer's scene script is patched here, at run
time, rather than given a new option for one use.

    python3 cutouts.py      (writes cutouts/<building>.png, RGBA)
"""
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "business" / "store_kit")]
import blender_render as br  # noqa: E402
import render_covers as rc  # noqa: E402

OUT = HERE / "cutouts"
WANT = {"gingerbread_cottage", "victorian_coaching_inn", "gingerbread_candy_cane_chapel", "victorian_church",
        "gingerbread_cocoa_cafe", "victorian_toy_shop", "gingerbread_sweet_shop"}

_FLOOR = "floor.data.materials.append(fmat)\n"
_RENDER = "bpy.ops.render.render(write_still=True)"
assert br._SCENE_SCRIPT.count(_FLOOR) == 1 and br._SCENE_SCRIPT.count(_RENDER) == 1, "renderer script changed"
br._SCENE_SCRIPT = br._SCENE_SCRIPT.replace(_FLOOR, _FLOOR + "floor.is_shadow_catcher = True\n").replace(
    _RENDER, "scene.render.film_transparent = True\n"
             "scene.render.image_settings.color_mode = 'RGBA'\n" + _RENDER)


def main():
    OUT.mkdir(exist_ok=True)
    for style, z in rc.ZIPS.items():
        with tempfile.TemporaryDirectory() as td, zipfile.ZipFile(z) as zf:
            for folder, (_title, parts) in rc.buildings(z).items():
                if folder not in WANT:
                    continue
                spec = []
                for s, col in parts:
                    zf.extract(s, td)
                    spec.append((Path(td) / s, tuple(float(c) for c in rc.rgb(col).split(","))))
                print("render", folder, flush=True)
                br.render_review(spec, OUT / f"{folder}.png", azimuth=-30, elevation=18, resolution=900,
                                 samples=96, timeout=1500, use_cache=False)


if __name__ == "__main__":
    main()
