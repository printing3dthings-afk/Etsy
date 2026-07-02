#!/usr/bin/env python3
"""
Build the SS1001 customer download ZIP:
  - 5 America 250th Anniversary 3D sign designs
  - Each design folder contains:
      * 1 × .3mf file  — all 3 color layers pre-assembled at correct Z heights
                          (open in Bambu Studio, assign AMS colors, slice, print)
      * 3 × .svg files — individual color layers for custom sizing / advanced users
  - README.txt — printing workflow for both formats

Output: data/3d_print_signs/america_250/SS1001_america250_3dprint_pack.zip

Run:  python tools/build_ss1001_zip.py
"""

from __future__ import annotations
import io
import re
import sys
import zipfile
from pathlib import Path

import cairosvg
import numpy as np
import trimesh
from PIL import Image

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_ZIP = DESIGNS_DIR / "SS1001_america250_3dprint_pack.zip"

# ── 5 designs to include (slug → display name) ────────────────────────────────
DESIGNS = [
    ("01_america250_america_bold",   "America Bold"),
    ("02_america250_star_badge",     "Star Badge"),
    ("03_america250_freedom_sign",   "Freedom Sign"),
    ("04_america250_happy_4th",      "Happy 4th"),
    ("05_america250_land_free",      "Land of the Free"),
]

# Z-height plan (mm):  base layer = 0→4 mm,  raised design layers = 4→6 mm
Z_BASE  = (0.0, 4.0)
Z_RAISE = (4.0, 6.0)

# Raster resolution per layer type
PPM_BASE   = 0.5   # px/mm — base is a simple solid plate, lower res is fine
PPM_DESIGN = 1.5   # px/mm — design layers need enough res for 0.4mm nozzle details


# ── Mesh builder ──────────────────────────────────────────────────────────────

def svg_to_mesh(svg_path: Path, z_bottom: float, z_top: float,
                px_per_mm: float = 1.0) -> trimesh.Trimesh | None:
    """
    Convert a black-on-transparent SVG layer to a closed 3D mesh.
    Uses cairosvg alpha channel as the fill mask, then builds a
    watertight voxel mesh (one 1-px-thick slab per filled pixel).
    """
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
    mask = arr[:, :, 3] > 128   # alpha channel → filled region

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

        quad(a, b, c, d)    # top face
        quad(h, g, f, e)    # bottom face
        if (ix-1, iy) not in filled: quad(a, d, h, e)   # left wall
        if (ix+1, iy) not in filled: quad(b, f, g, c)   # right wall
        if (ix,   iy-1) not in filled: quad(e, f, b, a) # front wall
        if (ix,   iy+1) not in filled: quad(d, c, g, h) # back wall

    return trimesh.Trimesh(
        vertices=np.array(vertices, dtype=np.float32),
        faces=np.array(faces, dtype=np.int32),
        process=True,
    )


# ── 3MF builder ───────────────────────────────────────────────────────────────

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
    """Return the bytes of a valid .3mf file (ZIP container) for N named meshes."""
    xml = _build_3mf_xml(named_meshes)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("3D/3dmodel.model", xml)
    return buf.getvalue()


# ── README content ─────────────────────────────────────────────────────────────

README = """\
SS1001 — America 250th Anniversary 3D Print Sign Pack
OnBrandCraftz — Personal use + gifts only. Not for commercial printing/resale.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT'S IN THIS ZIP
━━━━━━━━━━━━━━━━━━
5 design folders, each containing:
  • [design].3mf  — EASIEST: all color layers pre-assembled, Z-heights set.
                    Open in Bambu Studio, assign AMS slots, slice, print.
  • layer01_base_WHITE.svg  — White base plate  (prints at 4mm tall)
  • layer02_red_RED.svg     — Red elements       (prints at 2mm, sits on top of base)
  • layer03_blue_BLUE.svg   — Blue elements      (prints at 2mm, sits on top of base)

All signs default to ~165–220mm wide (fits Bambu 256mm plate with AMS prime tower).
Scale in Bambu Studio before slicing — SVGs are resolution-independent.

━━━━━━━━━━━━━━━━━━
OPTION 1 — EASIEST: USE THE .3MF FILE
━━━━━━━━━━━━━━━━━━
1. Open Bambu Studio
2. File → Open → select [design].3mf
3. Three parts appear pre-positioned: base (0–4mm), red layer (4–6mm), blue layer (4–6mm)
4. In the Filament list (left panel), click "+" to add 3 colors
5. Click each part in the Objects panel → assign to its filament color:
     base_WHITE → White or Cream PLA
     layer_RED  → Deep Red PLA
     layer_BLUE → Navy Blue PLA
6. Slice and print!

NOTE: Red and blue layers print at the same Z height (4–6mm) in different XY positions.
Bambu Studio handles this correctly — each color body prints in its own AMS turn.

━━━━━━━━━━━━━━━━━━
OPTION 2 — SVG LAYERS (for custom sizing or other slicers)
━━━━━━━━━━━━━━━━━━
1. In Bambu Studio, drag & drop layer01_base_WHITE.svg → set height 4mm
2. Right-click the model → Add Part → drag layer02_red_RED.svg → set height 2mm
   → In Object panel, set Z-offset to 4mm (so it sits on top of the base)
3. Repeat for layer03_blue_BLUE.svg: height 2mm, Z-offset 4mm
4. Add 3 colors in Filament list, assign one color per SVG part
5. Use the Color Painting tool (press N) if you want to adjust any region → Fill tool
6. Slice and print!

Scale tip: select all 3 parts (Ctrl+A) before scaling to keep them aligned.

━━━━━━━━━━━━━━━━━━
PRINTING TIPS
━━━━━━━━━━━━━━━━━━
• FLIP THE MODEL so the design face is DOWN on a textured PEI plate.
  This gives a perfectly smooth, layer-line-free front face.
  In Bambu Studio: right-click → Place on Face → select the top face.

• Recommended filaments:
    White/Cream PLA for the base
    Deep Red PLA for the red layer
    Navy Blue PLA for the blue layer (or any dark blue)
    OPTIONAL: Gold Silk PLA for the blue layer on the Star Badge design — stunning!

• Layer height: 0.2mm recommended. Outer wall speed: 50mm/s or lower for best quality.

• No AMS? Use filament swaps at layer 4mm (switch from white to your design colors).
  The slicer will prompt you to swap when the base is done.

━━━━━━━━━━━━━━━━━━
SUPPORT
━━━━━━━━━━━━━━━━━━
Questions? Message us on Etsy: OnBrandCraftz
Printing3dthings@outlook.com

© OnBrandCraftz. Personal use + gifts only.
Not for resale, commercial printing, or redistribution.
"""


# ── Main build ────────────────────────────────────────────────────────────────

def main() -> None:
    print("SS1001 ZIP Builder")
    print("=" * 60)

    # Collect all files to pack
    zip_contents: list[tuple[str, bytes]] = []   # (arcname, data)

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

        # ── Build 3MF ──────────────────────────────────────────────────────
        named_meshes: list[tuple[str, trimesh.Trimesh]] = []
        for i, lf in enumerate(layers):
            is_base = (i == 0)
            ppm = PPM_BASE if is_base else PPM_DESIGN
            zb, zt = Z_BASE if is_base else Z_RAISE

            m = svg_to_mesh(lf, zb, zt, px_per_mm=ppm)
            if m is None:
                errors.append(f"  Empty mesh: {lf}")
                continue
            layer_name = lf.stem   # e.g. "layer01_base_WHITE"
            named_meshes.append((layer_name, m))
            print(f"    {lf.name}: {len(m.vertices)} verts, {len(m.faces)} faces")

        if not named_meshes:
            errors.append(f"No meshes built for {slug}")
            continue

        # Short folder name for ZIP
        short = slug.replace("america250_", "").replace("01_", "1_").replace("02_", "2_") \
                    .replace("03_", "3_").replace("04_", "4_").replace("05_", "5_")
        folder = f"SS1001_{short}"

        # Add 3MF to zip contents
        threemf_name = f"SS1001_{slug.split('_',2)[-1]}.3mf"
        threemf_bytes = build_3mf_bytes(named_meshes)
        zip_contents.append((f"{folder}/{threemf_name}", threemf_bytes))
        print(f"    3MF: {len(threemf_bytes)//1024} KB")

        # ── Add layer SVGs ─────────────────────────────────────────────────
        for lf in layers:
            svg_data = lf.read_bytes()
            zip_contents.append((f"{folder}/{lf.name}", svg_data))

        ok += 1

    # ── Add README ────────────────────────────────────────────────────────
    zip_contents.append(("README.txt", README.encode("utf-8")))

    # ── Write ZIP ────────────────────────────────────────────────────────
    print(f"\n  Writing ZIP: {OUT_ZIP}")
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arcname, data in zip_contents:
            zf.writestr(arcname, data)

    zip_size_mb = OUT_ZIP.stat().st_size / 1024 / 1024
    print(f"  ZIP size: {zip_size_mb:.1f} MB")

    if zip_size_mb > 20:
        errors.append(f"ZIP exceeds Etsy 20MB limit: {zip_size_mb:.1f} MB")

    print("\n" + "=" * 60)
    if errors:
        print(f"  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    ✗ {e}")
        sys.exit(1)
    else:
        print(f"  ✓ {ok}/{len(DESIGNS)} designs built successfully")
        print(f"  ZIP: {OUT_ZIP}")
        print(f"  Size: {zip_size_mb:.1f} MB (Etsy limit: 20 MB)")


if __name__ == "__main__":
    main()
