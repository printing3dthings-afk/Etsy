#!/usr/bin/env python3
"""
Build SS1001 Vol 2 customer download ZIP:
  5 additional America 250th Anniversary 3D sign designs

Output: data/3d_print_signs/america_250/SS1001_america250_3dprint_pack_vol2.zip

Run:  python tools/build_ss1001_vol2_zip.py
"""

from __future__ import annotations
import io
import re
import zipfile
from pathlib import Path

import cairosvg
import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_ZIP = DESIGNS_DIR / "SS1001_america250_3dprint_pack_vol2.zip"

DESIGNS = [
    ("07_america250_banner_4c",  "America 250 Banner"),
    ("08_america250_burst_4c",   "America 250 Burst"),
    ("09_america250_seal_4c",    "America 250 Seal"),
    ("10_america250_shield_4c",  "America 250 Shield"),
    ("11_america250_stamp_4c",   "America 250 Stamp"),
]

Z_BASE  = (0.0, 4.0)
Z_RAISE = (4.0, 6.0)
PPM_BASE   = 0.5
PPM_DESIGN = 1.5


def svg_to_mesh(svg_path: Path, z_bottom: float, z_top: float,
                px_per_mm: float = 1.0) -> trimesh.Trimesh | None:
    content = svg_path.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="0 0 (\S+) (\S+)"', content)
    if not vb:
        print(f"  WARNING: no viewBox in {svg_path.name}")
        return None
    W_mm, H_mm = float(vb.group(1)), float(vb.group(2))
    W_px = max(1, int(W_mm * px_per_mm))
    H_px = max(1, int(H_mm * px_per_mm))

    png_bytes = cairosvg.svg2png(bytestring=content.encode(),
                                  output_width=W_px, output_height=H_px)
    arr = np.array(Image.open(io.BytesIO(png_bytes)).convert("RGBA"))
    mask = arr[:, :, 3] > 128

    if not np.any(mask):
        return None

    mm_per_px = 1.0 / px_per_mm
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    v_idx: dict[tuple, int] = {}

    def v(ix: int, iy: int, z: float) -> int:
        k = (ix, iy, z)
        if k not in v_idx:
            v_idx[k] = len(vertices)
            vertices.append([ix * mm_per_px, iy * mm_per_px, z])
        return v_idx[k]

    def quad(a: int, b: int, c: int, d: int) -> None:
        faces.append([a, b, c])
        faces.append([a, c, d])

    ys, xs = np.where(mask)
    filled: set[tuple[int, int]] = set(zip(xs.tolist(), ys.tolist()))

    for ix, iy in filled:
        a = v(ix,   iy,   z_top);    b = v(ix+1, iy,   z_top)
        c = v(ix+1, iy+1, z_top);    d = v(ix,   iy+1, z_top)
        e = v(ix,   iy,   z_bottom); f = v(ix+1, iy,   z_bottom)
        g = v(ix+1, iy+1, z_bottom); h = v(ix,   iy+1, z_bottom)

        quad(a, b, c, d)
        quad(h, g, f, e)
        if (ix-1, iy) not in filled: quad(a, d, h, e)
        if (ix+1, iy) not in filled: quad(b, f, g, c)
        if (ix,   iy-1) not in filled: quad(e, f, b, a)
        if (ix,   iy+1) not in filled: quad(d, c, g, h)

    return trimesh.Trimesh(
        vertices=np.array(vertices, dtype=np.float32),
        faces=np.array(faces, dtype=np.int32),
        process=True,
    )


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    '</Types>'
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    '</Relationships>'
)


def _build_3mf_xml(named_meshes: list[tuple[str, trimesh.Trimesh]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'unit="millimeter" xml:lang="en-US">',
        "  <resources>",
    ]
    build_items: list[str] = []
    for obj_id, (name, mesh) in enumerate(named_meshes, 1):
        lines += [
            f'    <object id="{obj_id}" name="{name}" type="model">',
            "      <mesh>",
            "        <vertices>",
        ]
        for x, y, z in mesh.vertices:
            lines.append(f'          <vertex x="{x:.2f}" y="{y:.2f}" z="{z:.2f}"/>')
        lines += ["        </vertices>", "        <triangles>"]
        for v0, v1, v2 in mesh.faces:
            lines.append(f'          <triangle v1="{v0}" v2="{v1}" v3="{v2}"/>')
        lines += ["        </triangles>", "      </mesh>", "    </object>"]
        build_items.append(f'    <item objectid="{obj_id}"/>')

    lines += ["  </resources>", "  <build>"] + build_items + ["  </build>", "</model>"]
    return "\n".join(lines)


def build_3mf_bytes(named_meshes: list[tuple[str, trimesh.Trimesh]]) -> bytes:
    xml = _build_3mf_xml(named_meshes)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("3D/3dmodel.model", xml)
    return buf.getvalue()


README_VOL2 = """\
SS1001 Vol 2 — America 250th Anniversary 3D Print Sign Pack (Designs 6–10)
OnBrandCraftz — Personal use + gifts only. Not for commercial printing/resale.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESIGNS IN THIS VOLUME  (4-color: Cream + Navy + Red + Gold)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 6. America 250 Banner  — Rectangular banner, NAVY base, GOLD border/"AMERICA",
                          RED accent bands, CREAM "250" / dates
 7. America 250 Burst   — Sunburst / Art Deco disc, CREAM base, alternating
                          NAVY & RED sunburst rays, GOLD "AMERICA" / "250"
 8. America 250 Seal    — Circular medallion/seal, CREAM disc, NAVY ring + stars,
                          RED "AMERICA" rule lines, GOLD "250" / dates
 9. America 250 Shield  — Pentagon shield, NAVY base, GOLD "AMERICA" + eagle,
                          RED star band + "250"
10. America 250 Stamp   — Postage stamp silhouette, CREAM base, NAVY frame +
                          Liberty silhouette, RED "AMERICA" / "250", GOLD "FOREVER"

For designs 1–5 see the companion file: SS1001_america250_3dprint_pack_vol1.zip

━━━━━━━━━━━━━━━━━━
WHAT'S IN THIS ZIP
━━━━━━━━━━━━━━━━━━
5 design folders, each containing:
  • [design].3mf         — EASIEST: all 4 color layers pre-assembled, Z-heights set.
                           Open in Bambu Studio, assign AMS slots, slice, print.
  • layer01_base_[COLOR].svg  — Base plate (0–4 mm)
  • layer02_[COLOR].svg       — Raised design layer 1 (4–6 mm)
  • layer03_[COLOR].svg       — Raised design layer 2 (4–6 mm)
  • layer04_[COLOR].svg       — Raised design layer 3 (4–6 mm)

⚠️ These are 4-COLOR designs. You need a Bambu AMS (or manual filament swaps at 4 mm)
   to print all 4 colors. You can also simplify by loading only 2–3 layers.

━━━━━━━━━━━━━━━━━━
OPTION 1 — EASIEST: USE THE .3MF FILE
━━━━━━━━━━━━━━━━━━
1. Open Bambu Studio
2. File → Open → select [design].3mf
3. Four parts appear pre-positioned in the Objects panel
4. In the Filament list (left panel), click "+" to add each color needed:
     Cream / Off-White PLA  (base)
     Navy Blue PLA
     Deep Red PLA
     Gold / Antique Gold PLA
5. Click each part → assign to its filament in the Objects panel
6. Slice and print!

The layer filenames include the color name (CREAM / NAVY / RED / GOLD)
so it's easy to see which filament goes where.

━━━━━━━━━━━━━━━━━━
OPTION 2 — SVG LAYERS (for custom sizing or other slicers)
━━━━━━━━━━━━━━━━━━
1. In Bambu Studio, drag & drop layer01_base_[COLOR].svg → set height 4 mm
2. Right-click the model → Add Part → drag layer02 SVG → height 2 mm → Z-offset 4 mm
3. Repeat for layer03: height 2 mm, Z-offset 4 mm
4. Repeat for layer04: height 2 mm, Z-offset 4 mm
5. Add 4 colors in Filament list, assign one color per part
6. Use the Color Painting tool (press N) → Fill tool if any region needs correction
7. Slice and print!

Scale tip: select all parts (Ctrl+A) before scaling to keep them aligned.

━━━━━━━━━━━━━━━━━━
PRINTING TIPS
━━━━━━━━━━━━━━━━━━
• FLIP THE MODEL so the design face is DOWN on a textured PEI plate.
  In Bambu Studio: right-click → Place on Face → select the top face.
  This gives a perfectly smooth, layer-line-free front face.

• Recommended filaments:
    Cream / Off-White PLA for the base plate
    Navy Blue PLA for navy elements
    Deep Red PLA for red elements
    Gold Silk PLA for gold elements (Silk PLA gives a beautiful metallic sheen!)

• Layer height: 0.2 mm recommended.  Outer wall speed: 50 mm/s for best quality.

• No AMS? Print 1–2 colors only by omitting some layers, or use manual filament
  swaps at the 4 mm height change (the slicer will prompt you).

━━━━━━━━━━━━━━━━━━
SUPPORT
━━━━━━━━━━━━━━━━━━
Questions? Message us on Etsy: OnBrandCraftz
Printing3dthings@outlook.com

© OnBrandCraftz. Personal use + gifts only.
Not for resale, commercial printing, or redistribution.
"""


def main() -> None:
    print("SS1001 Vol 2 ZIP Builder")
    print("=" * 60)

    zip_contents: list[tuple[str, bytes]] = []
    ok = 0
    errors: list[str] = []

    for slug, display_name in DESIGNS:
        design_dir = DESIGNS_DIR / slug
        if not design_dir.exists():
            errors.append(f"Missing design dir: {design_dir}")
            continue

        layers = sorted(design_dir.glob("layer*.svg"))
        if not layers:
            errors.append(f"No layer SVGs in {slug}")
            continue

        print(f"\n  Building {display_name} ({slug}) — {len(layers)} layers")

        named_meshes: list[tuple[str, trimesh.Trimesh]] = []
        for i, lf in enumerate(layers):
            is_base = (i == 0)
            ppm = PPM_BASE if is_base else PPM_DESIGN
            zb, zt = Z_BASE if is_base else Z_RAISE

            m = svg_to_mesh(lf, zb, zt, px_per_mm=ppm)
            if m is None:
                errors.append(f"  Empty mesh: {lf}")
                continue
            named_meshes.append((lf.stem, m))
            print(f"    {lf.name}: {len(m.vertices)} verts, {len(m.faces)} faces")

        if not named_meshes:
            errors.append(f"No meshes built for {slug}")
            continue

        # ZIP folder name — use design number 6-10 for vol2
        vol2_nums = {
            "07_america250_banner_4c":  6,
            "08_america250_burst_4c":   7,
            "09_america250_seal_4c":    8,
            "10_america250_shield_4c":  9,
            "11_america250_stamp_4c":   10,
        }
        num = vol2_nums.get(slug, 0)
        short_name = slug.split("america250_", 1)[-1].replace("_4c", "")
        folder = f"SS1001_{num}_{short_name}"

        threemf_name = f"SS1001_{short_name}.3mf"
        threemf_bytes = build_3mf_bytes(named_meshes)
        zip_contents.append((f"{folder}/{threemf_name}", threemf_bytes))
        print(f"    3MF: {len(threemf_bytes)//1024} KB")

        for lf in layers:
            svg_data = lf.read_bytes()
            zip_contents.append((f"{folder}/{lf.name}", svg_data))

        ok += 1

    zip_contents.append(("README_vol2.txt", README_VOL2.encode("utf-8")))

    print(f"\n  Writing ZIP: {OUT_ZIP}")
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arcname, data in zip_contents:
            zf.writestr(arcname, data)

    zip_size_mb = OUT_ZIP.stat().st_size / 1024 / 1024
    print(f"  ZIP size: {zip_size_mb:.1f} MB")

    if zip_size_mb > 20:
        print(f"  ✗ ERROR: ZIP exceeds Etsy 20MB limit! ({zip_size_mb:.1f} MB)")
    else:
        print(f"  ✓ ZIP under 20MB limit")

    print(f"\n  ✓ {ok}/{len(DESIGNS)} designs built")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")

    print("=" * 60)


if __name__ == "__main__":
    main()
