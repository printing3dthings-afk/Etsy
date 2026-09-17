#!/usr/bin/env python3
"""Build the Virtual P1S viewer as a standalone static site.

    python3 tools/viewer/build_site.py              # -> tools/viewer/site/
    python3 tools/viewer/build_site.py -o /tmp/out  # anywhere else
    cd tools/viewer/site && python3 -m http.server  # open it offline

WHY THIS EXISTS. `virtual_p1s.html` starts at <title> with no doctype, charset
or viewport, because as an Artifact it is wrapped by the host, which supplies
all three. Serve that file directly and a phone lays it out at 980px -- the
exact fiction that made every local mobile measurement wrong until a wrapper
was added for testing (see README, "Honest limits"). Anywhere that is NOT the
artifact host needs the real document, so building it is a step, not a copy.

The output is plain static files: HTML, one JS bundle, and one script per plate
loaded on demand. No server, no build tooling, no network except the Google
Fonts stylesheet and the three.js CDN the page already uses.
"""
import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Matches what the Artifact host injects, so the page renders identically
# whether it is served from claude.ai, GitHub Pages, or a folder on a laptop.
HEAD = (
    '<!doctype html>\n<html lang="en">\n<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<meta name="color-scheme" content="dark">\n'
    '<meta name="description" content="Replays real sliced G-code from the '
    'OnBrandCraftz model library, move by move, inside a Bambu Lab P1S.">\n'
)
BODY_OPEN = '</head>\n<body>\n'
TAIL = '\n</body>\n</html>\n'


def build(out: Path) -> Path:
    page = (HERE / "virtual_p1s.html").read_text(encoding="utf-8")
    # The page's own <title>/<link>/<style> belong in the head; everything from
    # the first real element onward is the body. The marker is the page's own
    # opening tag, not a guess about line numbers.
    split = page.index("<div id=")
    head_part, body_part = page[:split], page[split:]

    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(HEAD + head_part + BODY_OPEN + body_part + TAIL,
                                    encoding="utf-8")
    shutil.copy2(HERE / "app.js", out / "app.js")

    jobs_src = HERE / "jobs"
    if not (jobs_src / "index.js").exists():
        raise SystemExit(
            "no plate payloads in %s -- run tools/gcode_viewer_data.py first; "
            "without them the page loads and then has nothing to draw." % jobs_src)
    jobs_out = out / "jobs"
    if jobs_out.exists():
        shutil.rmtree(jobs_out)
    shutil.copytree(jobs_src, jobs_out)

    n = len(list(jobs_out.glob("*.js"))) - 1        # index.js is not a plate
    mb = sum(f.stat().st_size for f in out.rglob("*")) / 1024 / 1024
    print("built %s -- %d plates, %.1f MB" % (out, n, mb))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default=str(HERE / "site"))
    build(Path(ap.parse_args().out).resolve())


if __name__ == "__main__":
    main()
