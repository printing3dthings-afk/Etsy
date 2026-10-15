#!/usr/bin/env python3
"""The full check set for a multi-part model, step by step (2026-10-13; pulled
out of christmas_lanterns/check_lantern.py when the village accessories
became its second user).

A product's own script describes it (its parts and their colours, the
one-body unions its build writes) and calls run_checks(). Steps, in order:

  parts       every part closed and no two overlap, per printed object
              (tools/part_mesh.py check); with shown offsets, also the
              objects as they stand together (a lid on its box)
  gate        tools/product_gate.py on each one-body union
  cost        each union sliced in one colour, supports off, and timed with
              the P1S motion model -- the clock the viewer uses
  3mf         tools/assemble_3mf.py, one object or several on one plate
  fidelity    tools/print_fidelity.py on each object's colour parts
  fragility   tools/fragility.py on each object's parts
  colour      tools/blender_render.py, three views, the parts as they stand
  night       a white print lit from inside (cfg["night"] = script, light_z)
  as_printed  tools/as_printed.py from the fidelity slice, outside only
  viewer      tools/gcode_viewer_data.py into the shared viewer

Results land in <dir>/logs and <dir>/images, the layout the village uses.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
STEPS = ["parts", "gate", "cost", "3mf", "fidelity", "fragility", "colour", "night", "as_printed", "viewer"]


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
    h = h.lstrip("#")
    return ",".join(f"{int(h[i:i+2], 16) / 255:.3f}" for i in (0, 2, 4))


def run_checks(d, name, cfg, steps=None):
    """d: the product's folder; name: its file stem (<name>_<part>.stl).
    cfg: label, note, source (the 3MF's path under openscad_models),
    objects (a list of objects, each a list of (part, #colour)), unions (one
    STL per object), and optionally tags (a suffix per object for the
    viewer and as-printed images), shown ({object index: [x, y, z]} to lift
    an object into place for renders and the fit check) and night
    ((script, light_z))."""
    steps = steps or [s for s in STEPS if s != "night" or "night" in cfg]
    d = Path(d)
    logs, imgs = d / "logs", d / "images"
    logs.mkdir(exist_ok=True)
    imgs.mkdir(exist_ok=True)
    work = Path("/tmp/model_checks") / name
    work.mkdir(parents=True, exist_ok=True)
    stl = lambda p: d / f"{name}_{p}.stl"
    objs = cfg["objects"]
    allparts = [p for obj in objs for p in obj]
    tags = cfg.get("tags") or ([""] if len(objs) == 1 else [f"_{i}" for i in range(len(objs))])

    shown = {p: stl(p) for p, _ in allparts}
    for i, off in cfg.get("shown", {}).items():
        import trimesh
        for p, _ in objs[i]:
            m = trimesh.load(stl(p))
            m.apply_translation(off)
            shown[p] = work / f"shown_{p}.stl"
            m.export(shown[p])

    if "parts" in steps:
        txt = ""
        for obj in objs:
            txt += run([sys.executable, TOOLS / "part_mesh.py", "check", *[stl(p) for p, _ in obj]]).stdout
        if cfg.get("shown"):
            txt += "as they stand together:\n" + run([sys.executable, TOOLS / "part_mesh.py", "check",
                                                      *[shown[p] for p, _ in allparts]]).stdout
        (logs / "parts.txt").write_text(txt)
        print(txt)
    if "gate" in steps:
        txt = "".join(run([sys.executable, TOOLS / "product_gate.py", d / u]).stdout for u in cfg["unions"])
        (logs / "gate.txt").write_text(txt)
        print(txt)
    if "cost" in steps:
        sys.path.insert(0, str(TOOLS))
        from virtual_printer import report
        from gcode_viewer_data import build_job
        txt = ""
        for u in cfg["unions"]:
            g = work / f"cost_{Path(u).stem}.gcode"
            r = report(str(d / u), str(g), supports=False)
            j = build_job(g, u)
            s_ = j["totalSeconds"]
            txt += (f"{u}: {int(s_ // 3600)} h {int(s_ % 3600 // 60)} m, {r['filament_mm'] / 1000:.1f} m of filament, "
                    f"{j['filamentG']} g, {r['layers']} layers, single colour, supports off\n")
        (logs / "cost.txt").write_text(txt)
        print(txt)
    if "3mf" in steps:
        args = []
        for i, obj in enumerate(objs):
            args += (["+"] if i else []) + [f"{stl(p)}:{c}" for p, c in obj]
        run([sys.executable, TOOLS / "assemble_3mf.py", *(["--plate"] if len(objs) > 1 else []),
             d / f"{name}.3mf", *args], logs / "3mf.txt")
    if "fidelity" in steps:
        txt = ""
        for i, obj in enumerate(objs):
            txt += run([sys.executable, TOOLS / "print_fidelity.py", *sum([["--part", f"{stl(p)}:{c}"] for p, c in obj], []),
                        "--keep", work / f"fid{i}"], cwd=d).stdout
        (logs / "fidelity.txt").write_text(txt)
    if "fragility" in steps:
        txt = "".join(run([sys.executable, TOOLS / "fragility.py", *[stl(p) for p, _ in obj]]).stdout for obj in objs)
        (logs / "fragility.txt").write_text(txt)
    if "colour" in steps:
        run([sys.executable, TOOLS / "blender_render.py", *sum([["--part", f"{shown[p]}:{rgb(c)}"] for p, c in allparts], []),
             "-o", imgs / f"{name}_colour.png", "--views", "--front=-y", "--samples", "96", "--timeout", "1200"], logs / "render.txt")
    if "night" in steps:
        script, light_z = cfg["night"]
        for az, tag in ((35, "night"), (-20, "night_front")):
            run([sys.executable, script, imgs / f"{name}_{tag}.png", *[shown[p] for p, _ in allparts],
                 "--light-z", light_z, "--az", az, "--samples", "160", "--res", "1100"], logs / f"{tag}.txt")
    if "as_printed" in steps:
        for i, obj in enumerate(objs):
            run([sys.executable, TOOLS / "as_printed.py", work / f"fid{i}" / "fidelity.gcode",
                 *sum([["--colour", c] for c in dict.fromkeys(c for _, c in obj)], []),
                 "-o", imgs / f"{name}{tags[i]}_as_printed.png", "--views", "--exterior", "--timeout", "1800"],
                logs / f"as_printed{tags[i]}.txt")
    if "viewer" in steps:
        for i, obj in enumerate(objs):
            stem = f"{name}{tags[i]}"
            g = work / f"{stem}.gcode"
            g.write_bytes((work / f"fid{i}" / "fidelity.gcode").read_bytes())
            label = cfg["label"] + (cfg.get("tag_labels") or {}).get(tags[i], "")
            cols = ",".join(dict.fromkeys(c for _, c in obj))
            run([sys.executable, TOOLS / "gcode_viewer_data.py", g, "-d", TOOLS / "viewer" / "jobs", "--append",
                 "--label", f"{stem}={label}", "--note", f"{stem}={cfg['note']}",
                 "--source", f"{stem}={cfg['source']}", "--colours", f"{stem}={cols}"], logs / f"viewer{tags[i]}.txt")
