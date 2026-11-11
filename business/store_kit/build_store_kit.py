#!/usr/bin/env python3
"""Store kit for selling outside Etsy (2026-11-11, while the Etsy shop is down).

Joins each Christmas village bundle's Etsy parts (split to stay under Etsy's 20 MB
per file) into one ZIP per village. Payhip and Ko-fi take files up to gigabytes,
so a buyer gets one download. Every building folder and the licence are copied byte
for byte; the top README loses only its "This is download N of M" line. The check
below confirms the merged ZIP holds exactly that.

    python3 build_store_kit.py      (writes out/, which is not committed)

The parts come from openscad_models/christmas_village/downloads/build_downloads.py.
"""
import hashlib
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "openscad_models" / "christmas_village" / "downloads" / "out"
OUT = HERE / "out"
VILLAGES = {
    "victorian": "OnBrandCraftz_Victorian_Christmas_Village_8_buildings.zip",
    "gingerbread": "OnBrandCraftz_Gingerbread_Christmas_Village_7_buildings.zip",
}


def merge(style, name):
    parts = sorted(SRC.glob(f"OnBrandCraftz_{style}_christmas_village_bundle_part*of*.zip"))
    if not parts:
        sys.exit(f"no {style} bundle parts in {SRC}: run build_downloads.py first")
    OUT.mkdir(exist_ok=True)
    dest = OUT / name
    seen, digests = set(), {}
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for p in parts:
            with zipfile.ZipFile(p) as src:
                for info in src.infolist():
                    if info.is_dir():
                        continue
                    data = src.read(info)
                    if info.filename == "README.txt":
                        # each part's top README differs only in its "This is download N of M" line;
                        # the merged ZIP is one download, so that line goes and the rest must agree
                        data = re.sub(rb"\nThis is download \d+ of \d+;[^\n]*\n", b"\n", data)
                    if info.filename in seen:
                        # README.txt / LICENSE.txt repeat in every part; keep one, but only if identical
                        if hashlib.sha256(data).hexdigest() != digests[info.filename]:
                            sys.exit(f"{info.filename} differs between parts: not merging blindly")
                        continue
                    seen.add(info.filename)
                    digests[info.filename] = hashlib.sha256(data).hexdigest()
                    z.writestr(info, data)
    # check: every file of every part is in the merged ZIP, byte for byte
    with zipfile.ZipFile(dest) as m:
        assert m.testzip() is None, f"{dest.name} is corrupt"
        got = {i.filename: hashlib.sha256(m.read(i)).hexdigest() for i in m.infolist()}
    assert got == digests, f"{dest.name}: contents differ from the parts"
    folders = sorted({n.split("/")[0] for n in got if "/" in n})
    print(f"{dest.name}: {len(parts)} parts -> 1 ZIP, {dest.stat().st_size / 1e6:.1f} MB, "
          f"{len(folders)} buildings: {', '.join(folders)}")


if __name__ == "__main__":
    for style, name in VILLAGES.items():
        merge(style, name)
