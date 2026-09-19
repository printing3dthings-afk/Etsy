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

The output is plain static files: HTML, two JS bundles, and one script per
plate loaded on demand. No server and no build tooling. three.js is copied in
from vendor/ and the <script src> is rewritten to point at it, so the folder
renders with no network at all -- only the Google Fonts stylesheet stays
remote, and type falls back cleanly without it. The Artifact copy keeps the
CDN tag, which is why the rewrite happens here and not in the page itself.
"""
import argparse
import hashlib
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_REPO = HERE.parent.parent

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

CDN_THREE = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'


def build(out: Path) -> Path:
    page = (HERE / "virtual_p1s.html").read_text(encoding="utf-8")
    # The page's own <title>/<link>/<style> belong in the head; everything from
    # the first real element onward is the body. The marker is the page's own
    # opening tag, not a guess about line numbers.
    split = page.index("<div id=")
    head_part, body_part = page[:split], page[split:]

    if CDN_THREE not in body_part:
        raise SystemExit(
            "the three.js <script src> in virtual_p1s.html is not %s any more, "
            "so the offline rewrite silently did nothing. Update CDN_THREE."
            % CDN_THREE)
    body_part = body_part.replace(CDN_THREE, "three.min.js")

    # Cache-bust app.js on its content. The published path has to stay "app.js"
    # so an update replaces the file rather than accumulating copies, but a
    # webview that cached the old bytes will keep serving them across app
    # restarts -- which is exactly what happened on 2026-09-19: a fix shipped,
    # the phone was quit and reopened, and the phone was still running the
    # previous build. A changed query string is a different cache key.
    app_src = HERE / "app.js"
    app_hash = hashlib.sha1(app_src.read_bytes()).hexdigest()[:10]
    if '<script src="app.js">' not in body_part:
        raise SystemExit(
            "the app.js <script src> in virtual_p1s.html is not "
            '<script src="app.js"> any more, so the cache-busting rewrite '
            "silently did nothing and a stale copy can outlive a fix.")
    body_part = body_part.replace('<script src="app.js">',
                                  '<script src="app.js?v=%s">' % app_hash)

    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(HEAD + head_part + BODY_OPEN + body_part + TAIL,
                                    encoding="utf-8")
    shutil.copy2(app_src, out / "app.js")

    three = HERE / "vendor" / "three.min.js"
    if not three.exists():
        raise SystemExit(
            "missing %s -- the built site would silently fall back to the CDN "
            "and stop working offline. Fetch it with:\n  curl -o %s %s"
            % (three, three, CDN_THREE))
    shutil.copy2(three, out / "three.min.js")

    jobs_src = HERE / "jobs"
    if not (jobs_src / "index.js").exists():
        raise SystemExit(
            "no plate payloads in %s -- run tools/gcode_viewer_data.py first; "
            "without them the page loads and then has nothing to draw." % jobs_src)
    jobs_out = out / "jobs"
    if jobs_out.exists():
        shutil.rmtree(jobs_out)
    shutil.copytree(jobs_src, jobs_out)

    # Path-traced stills. Already downscaled and committed as JPEG by
    # tools/webify_stills.py, so this is a copy rather than a conversion --
    # which is what lets a fresh CI checkout (no local PNGs) still build a
    # site with stills in it.
    stills_src = ROOT_REPO / "data" / "plate_stills"
    n_still = 0
    if stills_src.is_dir():
        jpgs = sorted(stills_src.glob("*.jpg"))
        if jpgs:
            stills_out = out / "stills"
            stills_out.mkdir(parents=True, exist_ok=True)
            for j in jpgs:
                shutil.copy2(j, stills_out / j.name)
            n_still = len(jpgs)

    n = len(list(jobs_out.glob("*.js"))) - 1        # index.js is not a plate
    mb = sum(f.stat().st_size for f in out.rglob("*")) / 1024 / 1024
    print("built %s -- %d plates, %d stills, %.1f MB" % (out, n, n_still, mb))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default=str(HERE / "site"))
    build(Path(ap.parse_args().out).resolve())


if __name__ == "__main__":
    main()
