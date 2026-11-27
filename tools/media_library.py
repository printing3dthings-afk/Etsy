#!/usr/bin/env python3
"""The shop's media library: every photo and video we own, catalogued per build.

Scott, 2026-11-27: "We need to start building an extensive library of photos and videos for use.
Including your images of how they are designed."

    python3 tools/media_library.py            # catalog + contact sheets (needs the LFS media pulled)
    python3 tools/media_library.py --no-sheets

Writes business/media_library/:
  library.json   one record per file: build, kind, tag, version, date added, size, path
  LIBRARY.md     per build: what there is, by kind and version, and where
  sheets/<build>.jpg  a contact sheet of the build's images and video first frames, labelled

THE TAG is what a post must say about the file (the shop's first rule):
  REAL       Scott's own photos and footage, and his printer's camera (only from real/, photos/,
             real_timelapses/)
  EDITED     Scott's photo with an AI-made background (always said so in a post)
  RENDER     a design-review render of the model, never a photo
  SIMULATION drawn from the sliced toolpath (as-printed stills, viewer thumbnails, sim videos)
  VIDEO      a finished video of ours (its own SCRIPT.md says what is real in it)
  LISTING    a digital product's listing image

Left out on purpose: other people's work kept for reference (data/design_references, any
references/ folder, any file named for a reference), fonts and vendored code.
"""
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "business" / "media_library"
IMG = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VID = {".mp4", ".mov", ".webm"}
DESIGN_VIDEOS = {"pie_caddy_v2": "pie_caddy", "gingerbread_tin": "clickers/gingerbread_tin"}
EXCLUDE = ("data/design_references/", "fonts/", "assets/", "tools/viewer/vendor/", "node_modules/",
           "business/media_library/")


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout


def added_dates():
    """First commit date of each path, in one pass over history."""
    d, cur = {}, None
    for line in git("log", "--diff-filter=A", "--name-only", "--format=@%ad", "--date=short").splitlines():
        if line.startswith("@"):
            cur = line[1:]
        elif line.strip():
            d[line.strip()] = cur          # log runs newest first: the last write is the first add
    return d


def viewer_sources():
    """Plate stills are named by viewer job id; the viewer's index says which design each came from."""
    s = (ROOT / "tools" / "viewer" / "jobs" / "index.js").read_text()
    by_name = {}
    for p in git("ls-files", "openscad_models").splitlines():
        by_name.setdefault(Path(p).name, p)
    out = {}
    dirs = sorted({p.split("/")[1] for p in by_name.values() if p.count("/") > 1}, key=len, reverse=True)
    for jid, src in re.findall(r'"id":"([^"]+)"[^}]*?"source":"([^"]*)"', s):
        if src.startswith("openscad_models/"):
            path = src
        elif "/" in src:
            path = "openscad_models/" + src
        else:
            path = by_name.get(src, "")
        if not path:        # no source on record: the build folder its id starts with, if any
            d = next((d for d in dirs if jid.startswith(d)), None)
            path = f"openscad_models/{d}/_" if d else ""
        out[jid] = path
    return out


def build_of(path, vsrc):
    parts = path.split("/")
    if parts[0] == "openscad_models" and len(parts) > 2:
        b = parts[1]
        # a folder of products (clickers/gingerbread_tin, christmas_village/<piece>) is filed per product
        if len(parts) > 3 and parts[1] in ("clickers", "christmas_village", "christmas_lanterns", "haunted_town",
                                          "valentine_2027", "christmas_ornaments", "multipart", "personal"):
            sub = parts[2]
            if not re.fullmatch(r"(images|real|photos|guide|checks|renders|out|v\d+)", sub):
                b = f"{parts[1]}/{sub}"
                # the village's groups hold one folder per building: file by building
                if (parts[1] == "christmas_village" and sub in ("victorian", "gingerbread", "accessories")
                        and len(parts) > 4 and not re.fullmatch(r"(images|real|photos|guide|checks|concepts)", parts[3])):
                    b += "/" + parts[3]
        return b
    if path.startswith("data/plate_stills/"):
        src = vsrc.get(Path(path).stem, "")
        return build_of(src, {}) if src.startswith("openscad_models/") else "viewer:" + Path(path).stem
    if path.startswith("business/social/design_process/out/"):
        # a design-process video and its stills belong with the build they show
        return DESIGN_VIDEOS.get(parts[4], "video:" + parts[4])
    if path.startswith("business/social/"):
        return "social:" + parts[2]
    if path.startswith("data/"):
        return "digital:" + parts[1]
    return parts[0]


def kind_of(path):
    p = path.lower()
    name = Path(p).name
    ext = Path(p).suffix
    if path.startswith("data/") and not path.startswith(("data/plate_stills/", "data/social/")):
        return "listing image", "LISTING"
    # checked before REAL, because these sit in real-sounding places or carry real-sounding names
    if "/real/studio/" in p:
        return "AI-edited photo", "EDITED"         # Scott's photo, background replaced (digital_vs_real --studio)
    if "digital_vs_real" in name:
        return "video", "VIDEO"                    # ours: sim and real cut together, each shot labelled
    if "listing-videos/" in p or ("/video/" in p and name.endswith("-timelapse.mp4")):
        return "simulation video", "SIMULATION"    # viewer replays of the sliced job (commits say so), not footage
    # REAL only from where Scott's own media is filed, never from a name alone
    if "/real/" in p or "/photos/" in p or "real_timelapses/" in p:
        return ("real video" if ext in VID else "real photo"), "REAL"
    if path.startswith("data/plate_stills/"):
        return "as-printed still", "SIMULATION"
    if "as_printed" in name or "digital_vs_real" in name or "toolpath" in name or "_sim" in name:
        return ("simulation video" if ext in VID else "as-printed still"), "SIMULATION"
    if ext in VID:
        return "video", "VIDEO"
    for k, words in (("concept", ("/concepts/",)), ("cutaway", ("section", "cutaway", "_cut", "cut_")),
                     ("exploded", ("exploded",)),
                     ("guide image", ("/guide/",)), ("before/after", ("before_after", "_vs_", "compare")),
                     ("fit check", ("fit", "clearance")), ("detail", ("detail", "close", "macro"))):
        if any(w in (p if w.startswith("/") else name) for w in words):
            return k, "RENDER"
    return "render", "RENDER"


def version_of(path):
    m = re.findall(r"(?:^|[/_ -])v(\d{1,2})(?=[/_. -]|$)", path.lower())
    return f"v{m[-1]}" if m else ""


def catalog():
    dates = added_dates()
    vsrc = viewer_sources()
    recs = []
    for p in git("ls-files").splitlines():
        ext = Path(p).suffix.lower()
        # someone else's work, kept only as a reference for a design: never ours to post
        if ext not in IMG | VID or p.startswith(EXCLUDE) or "/references/" in p or "reference" in Path(p).name:
            continue
        kind, tag = kind_of(p)
        f = ROOT / p
        size = f.stat().st_size if f.exists() else 0
        note = ""
        if "v3_hunyuan" in p:
            note = ("made from Benson's Hunyuan3D mesh: Tencent's licence excludes the EU, UK and South Korea; "
                    "Scott decides before any public post (urban_kid/v3_hunyuan/README.md)")
        recs.append(dict(path=p, build=build_of(p, vsrc), kind=kind, tag=tag, version=version_of(p), note=note,
                         added=dates.get(p, ""), media="video" if ext in VID else "image",
                         pulled=size > 1000, bytes=size))
    return recs


def contact_sheet(build, recs, dst):
    from PIL import Image, ImageDraw, ImageFont
    tiles = []
    for r in sorted(recs, key=lambda r: (r["added"], r["path"])):
        f = ROOT / r["path"]
        if not r["pulled"]:
            continue
        try:
            if r["media"] == "video":
                tmp = dst.parent / "_frame.jpg"
                # a third of the way in: at 0.5 s a design video shows only its opener's title card
                dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                            "csv=p=0", str(f)], capture_output=True, text=True).stdout.strip() or 1)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{dur / 3:.2f}", "-i", str(f), "-frames:v", "1",
                                "-vf", "scale=360:-1", str(tmp)], check=True, timeout=60)
                im = Image.open(tmp).convert("RGB")
            else:
                im = Image.open(f).convert("RGB")
        except Exception:                       # an unreadable file is listed in LIBRARY.md, not drawn
            continue
        im.thumbnail((240, 240))
        tiles.append((im, r))
    if not tiles:
        return False
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    W, H = 250, 300
    sheet = Image.new("RGB", (cols * W, rows * H + 50), (246, 244, 240))
    d = ImageDraw.Draw(sheet)
    try:
        f1 = ImageFont.truetype(str(ROOT / "business/social/explained_lesson006/fonts/ChakraPetch-SemiBold.ttf"), 13)
        f2 = ImageFont.truetype(str(ROOT / "business/social/explained_lesson006/fonts/ChakraPetch-Bold.ttf"), 22)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.text((12, 12), f"{build}: {len(tiles)} files", font=f2, fill=(40, 30, 30))
    colour = {"REAL": (30, 120, 60), "EDITED": (20, 130, 140), "RENDER": (60, 70, 160), "SIMULATION": (150, 90, 20),
              "VIDEO": (150, 30, 60), "LISTING": (90, 90, 90)}
    for i, (im, r) in enumerate(tiles):
        x, y = (i % cols) * W + 5, (i // cols) * H + 50
        sheet.paste(im, (x + (240 - im.width) // 2, y + (240 - im.height) // 2))
        d.rectangle((x, y + 242, x + 240, y + 260), fill=colour[r["tag"]])
        d.text((x + 4, y + 244), f"{r['tag']} {r['kind']} {r['version']}".strip(), font=f1, fill=(255, 255, 255))
        d.text((x + 4, y + 263), Path(r["path"]).name[:34], font=f1, fill=(50, 50, 50))
        d.text((x + 4, y + 279), r["added"] + ("  video" if r["media"] == "video" else "") + ("  licence: see note" if r["note"] else ""),
               font=f1, fill=(170, 40, 40) if r["note"] else (110, 110, 110))
    sheet.save(dst, quality=82)
    return True


def write_md(recs, sheets):
    by = defaultdict(list)
    for r in recs:
        by[r["build"]].append(r)
    tags = Counter(r["tag"] for r in recs)
    lines = [
        "# Media library",
        "",
        "Every photo and video the shop owns, by build. Generated by `tools/media_library.py`; "
        "`library.json` has one record per file.",
        "",
        "**The tag is what a post must say** (the shop's first rule): REAL is Scott's own photo or "
        "footage; EDITED is his photo with an AI-made background; RENDER is a design render, never a photo; SIMULATION is drawn from the sliced "
        "toolpath; VIDEO is a finished video of ours, with its own SCRIPT.md; LISTING is a digital "
        "product's listing image. Other sellers' images (`data/design_references`) are left out: "
        "research only, never ours to post.",
        "",
        f"- **Total:** {len(recs)} files: " + ", ".join(f"{tags[t]} {t}" for t in
                                                      ("REAL", "EDITED", "RENDER", "SIMULATION", "VIDEO", "LISTING")) + ".",
        f"- **Builds:** {len(by)}.",
        "",
        "## Builds with real footage, versions or both",
        "",
        "| build | real | renders | simulation | videos | versions | sheet |",
        "|---|---|---|---|---|---|---|",
    ]
    def row(b, rs):
        c = Counter(r["tag"] for r in rs)
        vers = sorted({r["version"] for r in rs if r["version"]})
        sh = f"[sheet](sheets/{sheets[b]})" if b in sheets else ""
        return f"| {b} | {c['REAL']} | {c['RENDER']} | {c['SIMULATION']} | {c['VIDEO']} | {' '.join(vers)} | {sh} |"
    rich = [b for b, rs in by.items() if any(r["tag"] == "REAL" for r in rs) or len({r["version"] for r in rs} - {""}) > 1]
    lines += [row(b, by[b]) for b in sorted(rich)]
    notes = sorted({(r["build"], r["note"]) for r in recs if r["note"]})
    if notes:
        lines += ["", "## Check before posting", ""] + [f"- **{b}:** {n}." for b, n in notes]
    lines += ["", "## Every build", "", "| build | real | renders | simulation | videos | versions | sheet |",
              "|---|---|---|---|---|---|---|"]
    lines += [row(b, by[b]) for b in sorted(by) if not b.startswith("digital:")]
    lines += ["", "## Digital products (listing images)", ""]
    lines += [f"- {b}: {len(by[b])} images" for b in sorted(by) if b.startswith("digital:")]
    lines += ["", "## Adding to it", "",
              "- **Scott's photos and clips** go in the build's own `real/` folder (`real/photos/` for stills), "
              "with a line in its `real/README.md`: what it shows and when.",
              "- **Design images** go in the build's `images/`, named for what they show "
              "(`_section`, `_exploded`, `_as_printed`, `_v2`), so they're tagged right here.",
              "- **Design-process videos** keep a still from each step in `stills/` beside the video (`storyboard.save_stills`); add the video to `DESIGN_VIDEOS` in the tool so it files under its build.",
              "- Then re-run `python3 tools/media_library.py`.", ""]
    (OUT / "LIBRARY.md").write_text("\n".join(lines))


def main():
    recs = catalog()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "library.json").write_text(json.dumps(recs, indent=0))
    sheets = {}
    if "--no-sheets" not in sys.argv:
        (OUT / "sheets").mkdir(exist_ok=True)
        by = defaultdict(list)
        for r in recs:
            by[r["build"]].append(r)
        for b, rs in sorted(by.items()):
            if b.startswith("digital:"):
                continue
            fn = re.sub(r"[^a-z0-9_]+", "_", b.lower()).strip("_") + ".jpg"
            if contact_sheet(b, rs, OUT / "sheets" / fn):
                sheets[b] = fn
        (OUT / "sheets" / "_frame.jpg").unlink(missing_ok=True)
    write_md(recs, sheets)
    missing = sum(1 for r in recs if not r["pulled"])
    print(f"{len(recs)} files, {len(sheets)} sheets" + (f"; {missing} not pulled from LFS (not drawn)" if missing else ""))


if __name__ == "__main__":
    main()
