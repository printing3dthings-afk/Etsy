#!/usr/bin/env python3
"""The full check set for a Christmas ornament set (2026-10-21):

    python3 check_ornament.py snowflakes [step ...]

Each design in a set is its own print (one object on the plate), checked one
by one; the renders lay them out side by side. Run the set's build.sh first.
Steps and results as tools/model_checks.py, plus three for the whole set on
its plate: pfidelity, pas_printed and pviewer (see plate_steps).
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
from model_checks import run_checks  # noqa: E402

ICE, RED, WHITE, SLATE = "#D8E6F0", "#C62F3A", "#F4F1EA", "#2E3440"
SETS = {
    "snowflakes": dict(
        name="crystal_snowflake", designs=6, colour=ICE, spacing=(84, 92),
        label="Crystal Snowflake Ornaments",
        note="Six faceted snowflake ornaments: thick arms and branches cut like crystal, "
             "a six-sided gem at the hub and a hanging loop at the top."),
    # six prints, each in colour parts
    "mini_lanterns": dict(
        name="mini_lantern", designs=6, spacing=(48, 0),
        dparts=[("frame", SLATE), ("glass", WHITE), ("art", SLATE), ("snow", WHITE), ("bow", RED)],
        label="Village Mini-Lantern Ornaments",
        note="Six hex-lantern ornaments, each with a building from the Christmas village raised on its "
             "front and back glass (church, cottage, clock tower, town tree, toy shop, well), a snowflake "
             "and stars between, snow on the roof, a red bow and a ring to hang it by."),
    # one print in colour parts (the name is the buyer's: the file's default is a sample)
    "name_ornament": dict(
        name="name_ornament", parts=[("body", RED), ("inlay", WHITE)],
        label="Personalised Name Ornament",
        note="A domed ornament, flat behind, with a name and the year inlaid flush in a second colour "
             "under a star. The sample name is Olivia."),
}

def plate_steps(key, steps):
    """One slice of the whole set as its 3MF lays it out, for the viewer:
    pfidelity (tools/print_fidelity.py --keep), pas_printed and pviewer (the
    viewer job and its still). The parts are moved by the 3MF's own item
    transforms, so the plate on screen is the one in the file (2026-10-21)."""
    import re
    import subprocess
    import zipfile
    import trimesh
    S = SETS[key]
    d = HERE / key
    tools = HERE.parent.parent / "tools"
    name = S["name"] + "s"
    work = Path("/tmp/model_checks") / f"{name}_plate"
    work.mkdir(parents=True, exist_ok=True)
    xml = zipfile.ZipFile(d / f"{S['name']}.3mf").read("3D/3dmodel.model").decode()
    moves = [(float(m.group(1)), float(m.group(2)))
             for m in re.finditer(r'<item objectid="\d+" transform="1 0 0 0 1 0 0 0 1 (\S+) (\S+) 0"', xml)]
    cols = {}
    for i in range(1, S["designs"] + 1):
        parts = [(f"{i}_{p}", c) for p, c in S["dparts"]] if "dparts" in S else [(f"{i}", S["colour"])]
        for p, c in parts:
            m = trimesh.load(d / f"{S['name']}_{p}.stl")
            m.apply_translation([moves[i - 1][0], moves[i - 1][1], 0])
            cols.setdefault(c, []).append(m)
    args = []
    for c, ms in cols.items():
        f = work / f"{name}_{c.lstrip('#')}.stl"
        trimesh.util.concatenate(ms).export(f)
        args += ["--part", f"{f}:{c}"]
    fid = work / "fid"
    if "pfidelity" in steps:
        r = subprocess.run([sys.executable, tools / "print_fidelity.py", *args, "--keep", fid],
                           capture_output=True, text=True, cwd=d)
        (d / "logs" / "fidelity_plate.txt").write_text(r.stdout + r.stderr)
    if "pas_printed" in steps:
        subprocess.run([sys.executable, tools / "as_printed.py", fid / "fidelity.gcode",
                        *sum([["--colour", c] for c in cols], []),
                        "-o", d / "images" / f"{name}_plate_as_printed.png", "--views", "--exterior",
                        "--timeout", "1800"], capture_output=True, text=True)
    if "pviewer" in steps:
        g = work / f"{name}.gcode"
        g.write_bytes((fid / "fidelity.gcode").read_bytes())
        subprocess.run([sys.executable, tools / "gcode_viewer_data.py", g, "-d", tools / "viewer" / "jobs",
                        "--append", "--label", f"{name}={S['label']}", "--note", f"{name}={S['note']}",
                        "--source", f"{name}=christmas_ornaments/{key}/{S['name']}.3mf",
                        "--colours", f"{name}={','.join(cols)}"], capture_output=True, text=True)
        from PIL import Image
        im = Image.open(d / "images" / f"{name}_plate_as_printed_three_quarter.png").convert("RGB")
        w, h = im.size
        sq = min(w, h)
        im = im.crop(((w - sq) // 2, (h - sq) // 2, (w + sq) // 2, (h + sq) // 2)).resize((900, 900), Image.LANCZOS)
        im.save(HERE.parent.parent / "data" / "plate_stills" / f"{name}.jpg", quality=80)


if __name__ == "__main__":
    key = sys.argv[1]
    S = SETS[key]
    d = HERE / key
    if "parts" in S:
        run_checks(d, S["name"], dict(label=S["label"], note=S["note"], objects=[S["parts"]],
                                      unions=[f"{S['name']}_union.stl"],
                                      source=f"christmas_ornaments/{key}/{S['name']}.3mf"), sys.argv[2:] or None)
        sys.exit()
    PLATE = ("pfidelity", "pas_printed", "pviewer")
    if any(st in PLATE for st in sys.argv[2:]):
        plate_steps(key, sys.argv[2:])
        rest = [st for st in sys.argv[2:] if st not in PLATE]
        if not rest:
            sys.exit()
        sys.argv = sys.argv[:2] + rest
    n = S["designs"]
    objects, unions, tags, shown = [], [], [], {}
    sx, sy = S["spacing"]
    for i in range(1, n + 1):
        if "dparts" in S:
            objects.append([(f"{i}_{p}", c) for p, c in S["dparts"]])
            unions.append(f"{S['name']}_{i}_union.stl")
            shown[i - 1] = [(i - 3.5) * sx, 0, 0]
        else:
            objects.append([(f"{i}", S["colour"])])
            unions.append(f"{S['name']}_{i}.stl")
            shown[i - 1] = [((i - 1) % 3 - 1) * sx, -((i - 1) // 3 - 0.5) * sy, 0]
        tags.append(f"_{i}")
    run_checks(d, S["name"], dict(label=S["label"], note=S["note"], objects=objects, unions=unions,
                                  tags=tags, shown=shown, source=f"christmas_ornaments/{key}/{S['name']}.3mf"),
               sys.argv[2:] or None)
