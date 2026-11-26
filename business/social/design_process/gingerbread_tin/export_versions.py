#!/usr/bin/env python3
"""Export every Gingerbread Tin version the video shows, from git, in its assembled pose.

Each version is the repo's own source at the commit where it was current (not a remodel):
  v1   e56e99f3  2026-10-29  the clicker, lid pressed on: the white prototype Scott printed
  v2   965fa247  2026-10-30  the clicker's lid screws on (2.7 pitch, 1.6 turns)
  can1 b5c6490a  2026-11-03  the canister Scott printed first (2.7 thread, a 3.4 mm gap at the seam)
  now  working tree          deeper thread, 1.86 mm seam, guide ring (2026-11-05)
The sources are copied to a scratch tree, the part switch's catch-all `else` (which draws the
whole assembly) is fenced off, and a few parts are appended that draw each colour region where it
sits when assembled. Meshes land in out/gingerbread_tin/meshes/<version>/<part>.stl.
"""
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE.parent / "out" / "gingerbread_tin" / "meshes"
DIRS = ["openscad_models/clickers", "openscad_models/christmas_village", "openscad_models/brand"]
VERSIONS = {"v1": "e56e99f3", "v2": "965fa247", "can1": "b5c6490a", "now": None}

CLICKER_PARTS = {
    "tin": "tin();", "tin_snow": "tin_snow();",
    "lid": "lid();", "lid_holly": "lid_holly();", "lid_snow": "lid_snow();",
    "cookie": "translate([0, 0, CZ]) cookie();", "cookie_icing": "translate([0, 0, CZ]) cookie_icing();",
    "cookie_red": "translate([0, 0, CZ]) cookie_red();", "cookie_green": "translate([0, 0, CZ]) cookie_green();",
    "mx": "mx_mock(S);",
}
CANISTER_PARTS = {
    "canister": "canister();", "canister_snow": "canister_snow();",
    "lid": "at_lid() lid_closed();", "lid_holly": "at_lid() lid_holly();", "lid_snow": "at_lid() lid_snow();",
    "mx": "at_lid() mx_mock(S);",
    "cookie": "at_lid() translate([0, 0, CZ]) cookie();", "cookie_icing": "at_lid() translate([0, 0, CZ]) cookie_icing();",
    "cookie_red": "at_lid() translate([0, 0, CZ]) cookie_red();", "cookie_green": "at_lid() translate([0, 0, CZ]) cookie_green();",
}


def tree(rev, dst):
    if rev is None:
        for d in DIRS:
            shutil.copytree(ROOT / d, dst / d, ignore=shutil.ignore_patterns("*.3mf", "*.stl", "*.png", "*.mp4",
                                                                            "*.jpg", "*.gcode*", "real", "checks"))
        return
    data = subprocess.run(["git", "-C", str(ROOT), "archive", rev, *DIRS], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=BytesIO(data)) as t:
        t.extractall(dst, filter="data")


def patch(path, parts):
    s = path.read_text()
    # fence the catch-all: an unknown part must draw nothing, not the whole assembly
    s = re.sub(r"\nelse\s+assembly\(0\);", '\nelse if (part == "assembly") assembly(0);', s)
    s = re.sub(r"\nelse \{\n", '\nelse if (part == "assembly") {\n', s)
    s += "\n// design_process/gingerbread_tin/export_versions.py: each colour region where it sits assembled\n"
    s += "".join(f'if (part == "A_{k}") {v}\n' for k, v in parts.items())
    path.write_text(s)


def main(only=None):
    for ver, rev in VERSIONS.items():
        if only and ver not in only:
            continue
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            tree(rev, td)
            g = td / "openscad_models/clickers/gingerbread_tin"
            src, parts = ((g / "gingerbread_tin_canister.scad", CANISTER_PARTS) if ver.startswith("can") or ver == "now"
                          else (g / "gingerbread_tin_clicker.scad", CLICKER_PARTS))
            jobs = [(ver, src, parts)]
            if ver == "now":        # today's clicker too, for the colour shots
                jobs.append(("now_clicker", g / "gingerbread_tin_clicker.scad", CLICKER_PARTS))
            for name, f, ps in jobs:
                patch(f, ps)
                d = OUT / name
                d.mkdir(parents=True, exist_ok=True)
                procs = {k: subprocess.Popen(["openscad", "-o", str(d / f"{k}.stl"), "-D", f'part="A_{k}"', str(f)],
                                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                         for k in ps}
                for k, p in procs.items():
                    log = p.communicate()[0]
                    ok = (d / f"{k}.stl").exists() and (d / f"{k}.stl").stat().st_size > 1000
                    print(f"{name}/{k}: {'ok' if ok else 'EMPTY'}", flush=True)
                    if not ok:
                        (d / f"{k}.stl").unlink(missing_ok=True)
                        (d / f"{k}.log").write_text(log)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
