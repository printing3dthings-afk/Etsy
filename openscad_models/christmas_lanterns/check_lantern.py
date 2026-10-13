#!/usr/bin/env python3
"""Run the full check set on a built lantern (2026-10-13).

    python3 check_lantern.py hex_lantern|drum_lantern|gift_box_lantern [step ...]

steps (default all, in order): parts gate 3mf fidelity fragility colour night
as_printed viewer. Every result lands in <lantern>/logs and <lantern>/images,
the same layout the village buildings use. Run <lantern>/build.sh and
build.sh union first.

The gift box prints as two objects (box, lid). The lid is built standing on
the plate, so the colour and night renders take a copy lifted onto the box.
"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
SCRATCH = Path("/tmp/lantern_checks")

SLATE, WHITE, RED, GREEN = "#2E3440", "#F4F1EA", "#C62F3A", "#2F6B45"
LANTERNS = {
    "hex_lantern": dict(
        label="Hex Carriage Lantern",
        note="A six-sided carriage lantern with a Christmas scene standing out of each glass panel, "
             "a snowy pointed roof, a red bow and a hanging ring. Lit by a tealight underneath, the "
             "scenes show dark on the glow even printed all in white.",
        objects=[[("frame", SLATE), ("glass", WHITE), ("art", SLATE), ("snow", WHITE), ("bow", RED)]],
        unions=["hex_lantern_union.stl"], light_z=30),
    "drum_lantern": dict(
        label="Panorama Drum Lantern",
        note="One unbroken Christmas Eve wraps all the way round a glass drum: a village and its church, "
             "the village tree, reindeer in a forest, a snowman, and Santa crossing the moon. Lit by a "
             "tealight underneath, it shows dark on the glow even printed all in white.",
        objects=[[("frame", SLATE), ("glass", WHITE), ("art", SLATE), ("bead", WHITE), ("drape", WHITE)]],
        unions=["drum_lantern_union.stl"], light_z=30),
    "gift_box_lantern": dict(
        label="Gift Box Lantern",
        note="A present with glass sides and a Christmas scene on each, tied with a red ribbon and bow. "
             "The lid lifts off to put a tealight inside; the box and lid print side by side.",
        objects=[[("frame", GREEN), ("glass", WHITE), ("art", GREEN)], [("lid", GREEN), ("ribbon", RED)]],
        unions=["gift_box_lantern_box_union.stl", "gift_box_lantern_lid_union.stl"], light_z=32,
        lid_lift=64.0),   # zr in gift_box_lantern.scad
}


def run(cmd, log=None, **kw):
    print("$", " ".join(str(c) for c in cmd)[:240], flush=True)
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    out = r.stdout + (r.stderr if r.returncode else "")
    if log:
        Path(log).write_text(out)
    if r.returncode:
        print(out[-3000:])
    return r


def rgb(h):
    h = h.lstrip("#"); return ",".join(f"{int(h[i:i+2], 16) / 255:.3f}" for i in (0, 2, 4))


def main():
    name = sys.argv[1]
    steps = sys.argv[2:] or ["parts", "gate", "3mf", "fidelity", "fragility", "colour", "night", "as_printed", "viewer"]
    L = LANTERNS[name]
    d = HERE / name
    logs, imgs = d / "logs", d / "images"
    logs.mkdir(exist_ok=True); imgs.mkdir(exist_ok=True)
    work = SCRATCH / name
    work.mkdir(parents=True, exist_ok=True)
    stl = lambda p: d / f"{name}_{p}.stl"
    allparts = [p for obj in L["objects"] for p in obj]

    # the scene as it stands, lid on: for the renders
    shown = {p: stl(p) for p, _ in allparts}
    if "lid_lift" in L:
        import trimesh
        for p, _ in L["objects"][1]:
            m = trimesh.load(stl(p)); m.apply_translation([0, 0, L["lid_lift"]])
            shown[p] = work / f"shown_{p}.stl"; m.export(shown[p])

    if "parts" in steps:
        run([sys.executable, HERE / "lantern_mesh.py", "check", *[stl(p) for p, _ in allparts]], logs / "parts.txt")
    if "gate" in steps:
        txt = ""
        for u in L["unions"]:
            r = run([sys.executable, TOOLS / "product_gate.py", d / u])
            txt += r.stdout
        (logs / "gate.txt").write_text(txt)
        print(txt)
    if "3mf" in steps:
        args = []
        for i, obj in enumerate(L["objects"]):
            if i:
                args.append("+")
            args += [f"{stl(p)}:{c}" for p, c in obj]
        run([sys.executable, TOOLS / "assemble_3mf.py", *(["--plate"] if len(L["objects"]) > 1 else []),
             d / f"{name}.3mf", *args], logs / "3mf.txt")
    if "fidelity" in steps:
        txt = ""
        for i, obj in enumerate(L["objects"]):
            k = work / f"fid{i}"
            r = run([sys.executable, TOOLS / "print_fidelity.py", *sum([["--part", f"{stl(p)}:{c}"] for p, c in obj], []),
                     "--keep", k], cwd=d)
            txt += r.stdout
        (logs / "fidelity.txt").write_text(txt)
    if "fragility" in steps:
        run([sys.executable, TOOLS / "fragility.py", *[stl(p) for p, _ in allparts]], logs / "fragility.txt")
    if "colour" in steps:
        run([sys.executable, TOOLS / "blender_render.py", *sum([["--part", f"{shown[p]}:{rgb(c)}"] for p, c in allparts], []),
             "-o", imgs / f"{name}_colour.png", "--views", "--front=-y", "--samples", "96", "--timeout", "1200"], logs / "render.txt")
    if "night" in steps:
        for az, tag in ((35, "night"), (-20, "night_front")):
            run([sys.executable, HERE / "concepts" / "night_render.py", imgs / f"{name}_{tag}.png", *[shown[p] for p, _ in allparts],
                 "--light-z", L["light_z"], "--az", az, "--samples", "160", "--res", "1100"], logs / f"{tag}.txt")
    if "as_printed" in steps:
        for i, obj in enumerate(L["objects"]):
            tag = "" if len(L["objects"]) == 1 else ("_box", "_lid")[i]
            run([sys.executable, TOOLS / "as_printed.py", work / f"fid{i}" / "fidelity.gcode",
                 *sum([["--colour", c] for c in dict.fromkeys(c for _, c in obj)], []),
                 "-o", imgs / f"{name}{tag}_as_printed.png", "--views", "--exterior", "--timeout", "1800"], logs / f"as_printed{tag}.txt")
    if "viewer" in steps:
        jobs = ROOT / "tools" / "viewer" / "jobs"
        for i, obj in enumerate(L["objects"]):
            tag = "" if len(L["objects"]) == 1 else ("_box", "_lid")[i]
            stem = f"{name}{tag}"
            g = work / f"{stem}.gcode"
            g.write_bytes((work / f"fid{i}" / "fidelity.gcode").read_bytes())
            label = L["label"] + {"": "", "_box": " (box)", "_lid": " (lid)"}[tag]
            cols = ",".join(dict.fromkeys(c for _, c in obj))
            run([sys.executable, TOOLS / "gcode_viewer_data.py", g, "-d", jobs, "--append",
                 "--label", f"{stem}={label}", "--note", f"{stem}={L['note']}",
                 "--source", f"{stem}=christmas_lanterns/{name}/{name}.3mf", "--colours", f"{stem}={cols}"], logs / f"viewer{tag}.txt")


if __name__ == "__main__":
    main()
