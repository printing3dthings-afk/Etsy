#!/usr/bin/env python3
"""The full check set for the nativity (2026-10-21):

    python3 check_nativity.py [step ...]

Eleven prints, checked one by one (tools/model_checks.py: parts, gate, cost,
fragility, colour). The colour renders stand them together as a scene, the
figures inside the stable and the kings and shepherd before it. Eleven do
not fit one plate in a row, the only layout tools/assemble_3mf.py makes, so
they ship as three plates, and the plate steps here make each one's 3MF,
fidelity slice, as-printed renders and viewer entry:

  plates      the three 3MFs
  pfidelity   tools/print_fidelity.py on each plate's colour parts
  pas_printed tools/as_printed.py from that slice
  pviewer     the slice into the shared viewer, and its still

Run ./build.sh and ./build.sh union first.
"""
import sys
from pathlib import Path

import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
from model_checks import run, run_checks  # noqa: E402

WOOD, GOLD = "#7A5C3F", "#C9A84C"
PIECES = ["mary", "joseph", "baby", "king1", "king2", "king3", "shepherd", "ox", "donkey", "sheep", "stable"]
GILT = {"king1", "king2", "king3", "stable"}
# the scene: the figures inside stand 0.05 over the stable's floor (3 mm up), so the
# overlap check does not read the touching faces as overlap
SCENE = {"stable": [0, 0, 0], "mary": [54, 34, 3.05], "joseph": [100, 34, 3.05], "baby": [80, 11, 3.05],
         "ox": [26, 56, 3.05], "donkey": [118, 56, 3.05], "sheep": [-22, 14, 0], "shepherd": [-20, 40, 0],
         "king1": [170, 48, 0], "king2": [170, 14, 0], "king3": [202, 31, 0]}
PLATES = {
    "nativity_holy_family": (["mary", "joseph", "baby", "ox", "donkey", "sheep"],
                             "Faceted Nativity: Holy Family and Animals",
                             "Mary, Joseph, the baby in the manger, an ox, a donkey and a sheep from the faceted "
                             "nativity, on one plate. Every figure is cut from flat faces; printed upright with no support."),
    "nativity_kings_shepherd": (["king1", "king2", "king3", "shepherd"],
                                "Faceted Nativity: Three Kings and Shepherd",
                                "The three kings, with gold crowns and gifts, and the shepherd with his staff, from the "
                                "faceted nativity. Two colours, printed upright with no support."),
    "nativity_stable": (["stable"], "Faceted Nativity: Stable",
                        "The stable for the faceted nativity: a shell open at the front, its roof climbing 46 deg to "
                        "the ridge, the Star of Bethlehem in gold over it. No support."),
}


def parts_of(pc):
    return [(f"{pc}_body", WOOD)] + ([(f"{pc}_gold", GOLD)] if pc in GILT else [])


def stl(p):
    return HERE / f"nativity_{p}.stl"


def plate_offsets(pieces, gap=6.0):
    """x offsets laying the pieces in a row, as tools/assemble_3mf.py --plate does."""
    lo = [trimesh.load(stl(f"{pc}_union")).bounds for pc in pieces]
    x, out = 0.0, {}
    for pc, b in zip(pieces, lo):
        out[pc] = [x - b[0][0], -(b[0][1] + b[1][1]) / 2, 0]
        x += b[1][0] - b[0][0] + gap
    return out


def plate_steps(steps):
    work = Path("/tmp/model_checks/nativity_plates")
    work.mkdir(parents=True, exist_ok=True)
    logs, imgs = HERE / "logs", HERE / "images"
    for name, (pieces, label, note) in PLATES.items():
        if "plates" in steps:
            args = []
            for i, pc in enumerate(pieces):
                args += (["+"] if i else []) + [f"{stl(p)}:{c}" for p, c in parts_of(pc)]
            run([sys.executable, TOOLS / "assemble_3mf.py", *(["--plate"] if len(pieces) > 1 else []),
                 HERE / f"{name}.3mf", *args], logs / f"3mf_{name}.txt")
        # the plate as one slice: each colour's parts moved into the row and merged
        off = plate_offsets(pieces)
        cols = {}
        for pc in pieces:
            for p, c in parts_of(pc):
                m = trimesh.load(stl(p))
                m.apply_translation(off[pc])
                cols.setdefault(c, []).append(m)
        partargs = []
        for c, ms in cols.items():
            f = work / f"{name}_{c.lstrip('#')}.stl"
            trimesh.util.concatenate(ms).export(f)
            partargs += ["--part", f"{f}:{c}"]
        fid = work / f"fid_{name}"
        if "pfidelity" in steps:
            r = run([sys.executable, TOOLS / "print_fidelity.py", *partargs, "--keep", fid], cwd=HERE)
            (logs / f"fidelity_{name}.txt").write_text(r.stdout)
        if "pas_printed" in steps:
            run([sys.executable, TOOLS / "as_printed.py", fid / "fidelity.gcode", *sum([["--colour", c] for c in cols], []),
                 "-o", imgs / f"{name}_as_printed.png", "--views", "--exterior", "--timeout", "1800"],
                logs / f"as_printed_{name}.txt")
        if "pviewer" in steps:
            g = work / f"{name}.gcode"
            g.write_bytes((fid / "fidelity.gcode").read_bytes())
            run([sys.executable, TOOLS / "gcode_viewer_data.py", g, "-d", TOOLS / "viewer" / "jobs", "--append",
                 "--label", f"{name}={label}", "--note", f"{name}={note}",
                 "--source", f"{name}=nativity/{name}.3mf", "--colours", f"{name}={','.join(cols)}"],
                logs / f"viewer_{name}.txt")
            from PIL import Image
            im = Image.open(imgs / f"{name}_as_printed_three_quarter.png").convert("RGB")
            w, h = im.size
            s = min(w, h)
            im = im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).resize((900, 900), Image.LANCZOS)
            im.save(ROOT / "data" / "plate_stills" / f"{name}.jpg", quality=80)


if __name__ == "__main__":
    steps = sys.argv[1:] or ["parts", "gate", "cost", "fragility", "colour", "plates", "pfidelity", "pas_printed", "pviewer"]
    std = [s for s in steps if s in ("parts", "gate", "cost", "fragility", "colour")]
    if std:
        run_checks(HERE, "nativity", dict(
            label="Faceted Nativity", note="", source="nativity/nativity_holy_family.3mf",
            objects=[parts_of(pc) for pc in PIECES], unions=[f"nativity_{pc}_union.stl" for pc in PIECES],
            tags=[f"_{pc}" for pc in PIECES], shown={i: SCENE[pc] for i, pc in enumerate(PIECES)}), std)
    plate_steps(steps)
