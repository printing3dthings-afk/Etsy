#!/usr/bin/env python3
"""Helpers for writing MakerWorld Parametric Model Maker (PMM) files (2026-11-06).

Both shop customizers failed in production on 2026-11-05: the Name Ornament
showed an empty plate in the web preview and failed cloud slicing in Bambu
Handy, and the Love Letter timed out. Four rules came out of that, and every
PMM file this shop writes now follows them:

1. **One file.** PMM reads only the uploaded .scad: an `include` of our own
   library, or an `import()` of a DXF or STL beside it, finds nothing.
   `flatten()` inlines every include/use of our own files.
2. **Only PMM's fonts.** An unknown font draws NO text, with no error: neither
   Dancing Script nor Fredoka is installed on PMM. `check_fonts()` fails a
   file whose fonts aren't in PMM's runtime list (fonts-0.8.0.json, saved
   beside this as pmm_fonts.json).
3. **On the plate.** PMM keeps the model's coordinates, and a 3MF's origin is
   the plate's front-left corner: a model centred on (0, 0) hangs three
   quarters off the plate, out of the preview and unsliceable. `PLATE_CENTRE`
   is the middle of a 256 mm plate (P1S, X1, A1).
4. **Fast.** PMM's generator gives up after about 10 s (forum reports; PMM's
   backend is an OpenSCAD build with Manifold, staff-confirmed 2025-03).
   `time_render()` renders with a Manifold build of OpenSCAD.

Customizer parameters must come before the first module or function, and a
colour parameter is a hex string with `// color` after it.
"""
import json
import os
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIBS = ROOT / "assets" / "openscad_libs"
FONTS_JSON = Path(__file__).resolve().parent / "pmm_fonts.json"
FAST = os.environ.get("OPENSCAD_FAST", "openscad")
PLATE_CENTRE = (128, 128)

_INC = re.compile(r"^\s*(include|use)\s*<([^>]+)>\s*;?\s*$")
# libraries PMM bundles itself: leave these includes alone
_BUNDLED = ("BOSL2/", "ub.scad", "KeyV2/", "gridfinity-rebuilt-openscad/", "threads-scad/",
            "Getriebe.scad", "knurledFinishLib_v2.scad")


def flatten(path, _seen=None):
    """The file's text with every include/use of our own files inlined, once each."""
    path = Path(path).resolve()
    seen = set() if _seen is None else _seen
    out = []
    for line in path.read_text().splitlines():
        m = _INC.match(line)
        if not m or m.group(2).startswith(_BUNDLED):
            out.append(line)
            continue
        dep = (path.parent / m.group(2)).resolve()
        if not dep.exists():
            dep = (LIBS / m.group(2)).resolve()
        if dep in seen:
            out.append(f"// ({m.group(2)} already inlined above)")
            continue
        seen.add(dep)
        out.append(f"// ---- inlined from {dep.relative_to(ROOT)} ----")
        out.append(flatten(dep, seen))
        out.append(f"// ---- end of {dep.name} ----")
    return "\n".join(out)


def pmm_fonts():
    return set(json.loads(FONTS_JSON.read_text())["fontNames"])


def check_fonts(scad_text):
    """Every font = "..." string in the file that PMM doesn't have."""
    used = set(re.findall(r'font\s*=\s*"([^"]+)"', scad_text)) | set(re.findall(r'_FONT\s*=\s*"([^"]+)"', scad_text))
    return sorted(used - pmm_fonts())


def check_no_imports(scad_text):
    """import() and include lines left in the file that PMM can't resolve."""
    bad = [ln.strip() for ln in scad_text.splitlines()
           if re.search(r'\bimport\s*\(', ln) and not ln.strip().startswith("//")]
    bad += [ln.strip() for ln in scad_text.splitlines() if _INC.match(ln) and not _INC.match(ln).group(2).startswith(_BUNDLED)]
    return bad


def time_render(scad, out, defines=(), backend="manifold"):
    """Render with OpenSCAD (Manifold), return (seconds, log). Fonts need HOME for fontconfig."""
    cmd = [FAST, "--backend", backend, "-o", str(out)]
    for d in defines:
        cmd += ["-D", d]
    cmd.append(str(scad))
    t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ))
    return time.time() - t, r.stdout + r.stderr
