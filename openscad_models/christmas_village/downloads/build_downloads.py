#!/usr/bin/env python3
"""Build the Christmas village digital-download ZIPs from the committed models.

One ZIP per building (its 3MF, its four part STLs, README, LICENSE) and one
bundle per style. Every number in a README is read from the files themselves:
size from the part meshes, print time and filament from the building's own
printing notes, part colours from its notes table. Nothing is typed in by hand,
so a README can never drift from the model it ships with.

    python3 build_downloads.py            # writes out/*.zip, then validates each

The ZIPs are build output (gitignored); rebuild them from here any time.
"""
import re
import sys
import textwrap
import zipfile
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
VILLAGE = HERE.parent
ROOT = VILLAGE.parent.parent
OUT = HERE / "out"
sys.path.insert(0, str(ROOT / "tools"))

STYLES = {
    "victorian": ("Victorian", ["cottage", "shop_house", "toy_shop", "church", "coaching_inn",
                                "townhouse", "santas_workshop", "clock_tower"]),
    "gingerbread": ("Gingerbread", ["cottage", "turret_house", "candy_cane_chapel", "sweet_shop",
                                    "cocoa_cafe", "santas_workshop", "cookie_clock_tower"]),
}
PARTS = ["body", "roof", "trim", "accent"]
CONTACT = "Printing3dthings@outlook.com"

LICENSE = """OnBrandCraftz -- licence for these 3D print files

Personal use only. You may print these files for yourself and to give as
gifts.

You may not:
- sell prints made from these files;
- share, resell or give away the files themselves;
- upload them to any other site or file-sharing service.

(c) OnBrandCraftz. Questions: {contact}
""".format(contact=CONTACT)


def building_facts(style: str, slug: str) -> dict:
    d = VILLAGE / style / slug
    name = f"{style}_{slug}"
    notes = next(d.glob("*_PRINTING.md")).read_text()
    title = notes.splitlines()[0].lstrip("# ").split(" — ")[0].strip()
    m = re.search(r"^\| \*\*single colour[^|]*\| \*\*([^*]+)\*\* \| \*\*([^*]+)\*\* \|", notes, re.M)
    if not m:
        raise SystemExit(f"{name}: no single-colour cost row in its notes")
    time, fil = m.group(1).strip(), m.group(2).strip()
    grams = re.search(r"about (\d+) g", fil)
    colours = {}
    for part in PARTS:
        r = re.search(rf"^\| {part} \| (.+?) \| ([^|`]+?) `(#[0-9A-Fa-f]{{6}})` \|", notes, re.M)
        if not r:
            raise SystemExit(f"{name}: no colour row for {part} in its notes")
        colours[part] = (r.group(1).strip(), r.group(2).strip(), r.group(3))
    stls = [d / f"{name}_{p}.stl" for p in PARTS]
    for f in stls + [d / f"{name}.3mf"]:
        if not f.exists():
            raise SystemExit(f"missing {f}")
    bounds = trimesh.util.concatenate([trimesh.load(f) for f in stls]).bounds
    size = bounds[1] - bounds[0]
    return dict(dir=d, name=name, title=title, time=time, grams=grams.group(1) if grams else None,
                colours=colours, size=size, stls=stls, threemf=d / f"{name}.3mf")


def readme(b: dict, style_label: str) -> str:
    w, dp, h = b["size"]
    rows = "\n".join(f"  {p}: {c[1]} {c[2]}\n" + textwrap.fill(c[0], 76, initial_indent="    ",
                                                                subsequent_indent="    ")
                     for p, c in b["colours"].items())
    grams = f", about {b['grams']} g of PLA" if b["grams"] else ""
    return f"""{b['title']} -- 3D print files
OnBrandCraftz Christmas Village, {style_label} style

WHAT'S IN THIS ZIP
- {b['name']}.3mf: the whole building, its four colour parts already in
  place. Opens in Bambu Studio and PrusaSlicer.
- stl/: the same four parts as STL files, for any other slicer. Load all four
  together and keep their positions; they line up as exported.
- README.txt (this file) and LICENSE.txt.

SIZE
{w:.0f} x {dp:.0f} x {h:.0f} mm (width x depth x height), snow base included.

PRINT SETTINGS THAT MATTER
- Supports OFF. Every overhang is shaped to print without them.
- Print it standing up, exactly as it sits in the file.
- 0.2 mm layers.
- Designed and sliced for a Bambu Lab P1S with a 0.4 mm nozzle.

TIME AND FILAMENT
In one colour: {b['time']}{grams} (sliced estimate, 0.2 mm layers). Four
colours add colour changes and purge: slice it in your own slicer for the
real figure.

COLOURS
The four parts and the colours they are set to in the 3MF:
{rows}
For a one-colour print, set all four parts to the same filament. White
prints are ready to paint.

LIGHTING
The building is hollow with an open base. Set it over a battery LED tealight
up to about 38 mm across and 45 mm tall (tealight not included), and lift
the building off to switch it on. Use only battery LED lights, never a
candle with a flame.

LICENCE
Personal use only; see LICENSE.txt.

Questions: {CONTACT}
"""


def add_building(z: zipfile.ZipFile, b: dict, style_label: str, prefix: str = "") -> None:
    z.write(b["threemf"], f"{prefix}{b['name']}.3mf")
    # Binary STL (2026-10-08): OpenSCAD writes ASCII, about five times larger,
    # which put both village bundles over Etsy's 20 MB per-file limit.
    for s in b["stls"]:
        z.writestr(f"{prefix}stl/{s.name}", trimesh.load(s, process=False).export(file_type="stl"))
    z.writestr(f"{prefix}README.txt", readme(b, style_label))


def main() -> int:
    from etsy_api import FileContentError, validate_digital_file

    OUT.mkdir(exist_ok=True)
    built = []
    for style, (label, slugs) in STYLES.items():
        facts = [building_facts(style, s) for s in slugs]
        for b in facts:
            p = OUT / f"OnBrandCraftz_{b['name']}_3D_print_files.zip"
            with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
                add_building(z, b, label)
                z.writestr("LICENSE.txt", LICENSE)
            built.append(p)
        # A bundle over Etsy's 20 MB per-file limit is split into parts, whole
        # buildings each (the gingerbread meshes come to 32 MB); a listing can
        # carry up to five files.
        groups, cur, size = [], [], 0
        for b in facts:
            est = (OUT / f"OnBrandCraftz_{b['name']}_3D_print_files.zip").stat().st_size
            if cur and size + est > 19.0 * 1048576:
                groups.append(cur); cur, size = [], 0
            cur.append(b); size += est
        groups.append(cur)
        listing = "\n".join(f"- {b['title']} ({b['name']}/)" for b in facts)
        for gi, g in enumerate(groups, 1):
            part = f"_part{gi}of{len(groups)}" if len(groups) > 1 else ""
            p = OUT / f"OnBrandCraftz_{style}_christmas_village_bundle{part}.zip"
            here = "" if len(groups) == 1 else (
                f"\nThis is download {gi} of {len(groups)}; it holds "
                + ", ".join(b["title"] for b in g) + ".\n")
            with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr("README.txt", f"OnBrandCraftz Christmas Village, {label} style: all "
                           f"{len(facts)} buildings\n\n{listing}\n{here}\nEach folder has its own README with "
                           f"its size, print settings and colours.\n\nPersonal use only; see LICENSE.txt.\n"
                           f"Questions: {CONTACT}\n")
                z.writestr("LICENSE.txt", LICENSE)
                for b in g:
                    add_building(z, b, label, f"{b['name']}/")
            built.append(p)

    bad = 0
    for p in built:
        try:
            validate_digital_file(str(p))
            err = ""
        except FileContentError as e:
            err = str(e)
        print(f"{'FAIL' if err else 'ok  '} {p.stat().st_size / 1048576:5.1f} MB  {p.name}  {err}")
        bad += bool(err)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
