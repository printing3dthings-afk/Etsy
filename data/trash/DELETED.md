# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **30 days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

<!-- TRASH id=20261014-001 date=2026-10-14 kind=file source="openscad_models/christmas_village/accessories/horse_sleigh/HORSE_SLEIGH_LEFT_OUT.md" reason="Superseded: the horse sleigh was built after all (split horse, 2026-10-14); see HORSE_SLEIGH_PRINTING.md" -->
## 20261014-001 · 2026-10-14 · file · `openscad_models/christmas_village/accessories/horse_sleigh/HORSE_SLEIGH_LEFT_OUT.md`
**Reason:** Superseded: the horse sleigh was built after all (split horse, 2026-10-14); see HORSE_SLEIGH_PRINTING.md  
**Payload:** `data/trash/files/20261014-001__HORSE_SLEIGH_LEFT_OUT.md`

```
# Horse sleigh — left out (2026-10-13)

Scott circled the horse sleigh from the second batch of accessory studies
with one condition: "If the horse and carriage can't look better then leave
them out." They are left out. This folder keeps the attempt so it is not
repeated blind.

## Why

A horse standing on four legs has two things that hang in the air: its belly
between the legs, and its head held out in front of its neck. At village
scale, with no supports, both have to be closed off:

- **The belly** can be closed into a point between the legs, if the legs
  splay fore and aft: they meet the body close together and stand apart.
  That part works, Dala-horse fashion.
- **The head** is the problem. Its muzzle is the lowest point of a shape held
  out in front, an island the slicer must prop. The only printable cure is to
  carry the jaw straight down into the chest, as a chess knight's is. That
  turns head, throat and neck into one thick column, and the horse loses the
  one line that makes it read as a horse.

Two passes (`horse_study.scad`, renders in `images/`, from OpenSCAD's preview,
not a print) came out as a toy cow and then a llama. Neither is better than
the study it was meant to improve on.

## What would change the answer

- **Supports.** With tree supports under the muzzle and belly, a proper horse
  prints; the shop's standard is no supports on anything sold, so that is
  Scott's call.
- **The sleigh alone.** A red sleigh piled with presents, waiting in the
  snow, prints without support (runners sunk in snow, the dash leaning
  forward under 40 degrees). Not built: Scott's "leave them out" covered both.
```

<!-- /TRASH 20261014-001 -->
<!-- TRASH id=20261014-002 date=2026-10-14 kind=file source="openscad_models/christmas_lanterns/lantern_mesh.py" reason="Moved to tools/part_mesh.py (identical code, generic docstring) when the village accessories became its second user" -->
## 20261014-002 · 2026-10-14 · file · `openscad_models/christmas_lanterns/lantern_mesh.py`
**Reason:** Moved to tools/part_mesh.py (identical code, generic docstring) when the village accessories became its second user  
**Payload:** `data/trash/files/20261014-002__lantern_mesh.py`

```
#!/usr/bin/env python3
"""Mesh steps the lanterns need that OpenSCAD 2021 does badly (2026-10-13).

    lantern_mesh.py check part.stl ...              each part closed; every pair disjoint
    lantern_mesh.py union out.stl part.stl ...      one body, for product_gate
    lantern_mesh.py wrap flat.stl out.stl --radius R --z Z [--minus m.stl ...]

check and union use manifold3d. CGAL took 3.5 hours to union Santa's
workshop's four parts and would not union imported STLs at all; manifold
does both in seconds and refuses an open mesh rather than guessing.

wrap bends a relief built flat (x along a face, y up, z out of it) round a
cylinder: x becomes the angle x / radius, y height above --z, z the distance
out from --radius. The flat mesh is subdivided first so its long triangles
follow the curve, and anything named by --minus is cut from the result, so a
relief wrapped a hair into its glass comes out touching it, not inside it.
"""
import argparse, itertools, math, sys
import numpy as np
import trimesh
import manifold3d as mf


def to_manifold(m: trimesh.Trimesh, name: str) -> mf.Manifold:
    # From the raw triangle soup, merged by manifold itself: CGAL writes two
    # solids that touch along a line as one edge shared by four faces, which
    # trimesh's own vertex merge turns into a non-manifold mesh manifold refuses.
    tri = np.asarray(m.vertices, np.float64)[np.asarray(m.faces)].reshape(-1, 3)
    mesh = mf.Mesh(vert_properties=tri.astype(np.float32), tri_verts=np.arange(len(tri), dtype=np.uint32).reshape(-1, 3))
    mesh.merge()
    out = mf.Manifold(mesh)
    if out.status() != mf.Error.NoError:
        sys.exit(f"{name}: manifold3d refuses it ({out.status()}) -- not a closed mesh")
    return out


def to_trimesh(m: mf.Manifold) -> trimesh.Trimesh:
    g = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=True)
    # Drop sheets that enclose nothing. The drum's welded union came back with
    # thirteen two-triangle back-to-back slivers beside its one real body, each
    # sharing an edge with it, so the body read as open (2026-10-13).
    cc = trimesh.graph.connected_components(t.face_adjacency, nodes=np.arange(len(t.faces)), min_len=1)
    keep = [c for c in cc if len(c) > 4 or abs(t.submesh([c], append=True).volume) > 1e-6]
    if len(keep) < len(cc):
        t = t.submesh(keep, append=True)
    return t


def load(path: str) -> mf.Manifold:
    return to_manifold(trimesh.load(path, force="mesh"), path)


def check(paths):
    ok = True
    ms = {}
    for p in paths:
        t = trimesh.load(p, force="mesh")
        ms[p] = to_manifold(t, p)
        print(f"  {'ok  ' if t.is_watertight else 'OPEN'}  {p}: {ms[p].volume():.1f} mm3, {len(t.faces)} faces")
        ok &= t.is_watertight
    for a, b in itertools.combinations(paths, 2):
        # parts that only touch come back with float32 noise: the hex lantern's
        # art, built on its glass's face, read 0.06 mm3 over ~1500 mm2 of contact
        v = (ms[a] ^ ms[b]).volume()
        if v > 0.1:
            ok = False
            print(f"  OVERLAP {a} / {b}: {v:.3f} mm3")
    print("PARTS OK: closed, no two overlap" if ok else "PARTS FAIL")
    return ok


def union(out, paths):
    u = mf.Manifold.batch_boolean([load(p) for p in paths], mf.OpType.Add)
    t = to_trimesh(u)
    t.export(out)
    print(f"{out}: {u.volume():.1f} mm3, {len(t.faces)} faces, watertight {t.is_watertight}, bodies {len(t.split(only_watertight=False))}")


def wrap(flat, out, radius, z, minus, step):
    # Weld first: where two pieces of the stepped relief touch along a line (the
    # drum's snowman, at its waist), the line stays a four-face edge through any
    # boolean, and trimesh -- and so product_gate -- reads the part as open. A
    # copy shifted 0.003 mm across the face turns each such line into a sliver
    # of overlap, and the union closes it (2026-10-13).
    m0 = to_manifold(trimesh.load(flat, force="mesh"), flat)
    m0
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261014-002 -->
<!-- TRASH id=20261025-001 date=2026-10-25 kind=file source="tools/api_server/main.py" reason="Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too." -->
## 20261025-001 · 2026-10-25 · file · `tools/api_server/main.py`
**Reason:** Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too.  
**Payload:** `data/trash/files/20261025-001__main.py`

```
#!/usr/bin/env python3
"""
OnBrandCraftz Mobile API Server

FastAPI backend powering the mobile dashboard app. Read-only + streaming chat.

Start:
  pip install -r tools/api_server/requirements.txt
  uvicorn tools.api_server.main:app --host 0.0.0.0 --port 8000 --reload

Deploy to Railway / Render: set env vars + point start command to this file.
"""

from __future__ import annotations

import asyncio
import base64
import codecs
import hashlib
import hmac
import inspect
import io
import json
import mimetypes
import os
import random
import re as _re
import secrets
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

if getattr(sys, "frozen", False):
    # PyInstaller desktop-app bundle (tools/desktop/backend.spec, 2026-07-08): the
    # frozen entry script's own __file__ no longer sits 3 directories under the repo
    # root (tools/api_server/main.py) the way it does when run from source. sys._MEIPASS
    # is PyInstaller's own documented attribute for "where the bundled data actually
    # is" -- NOT Path(sys.executable).parent, which in onedir mode (PyInstaller 6.x)
    # is one level too shallow: the executable sits in dist/frank-backend/, but the
    # bundled tools/ tree this spec collects via `datas` lands in
    # dist/frank-backend/_internal/tools/ (verified empirically -- a static-asset
    # 404 was the first sign sys.executable's parent was wrong).
    ROOT = Path(sys._MEIPASS).resolve()  # noqa: SLF001 -- documented PyInstaller API
else:
    ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# Load .env before importing shop tools
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
import openai
import business_config
import db  # local persistence layer (tools/api_server/db.py)
import oauth_providers  # Google / Apple Sign-In (tools/api_server/oauth_providers.py)
import seasonal_keywords  # noqa: E402
import tax_compliance_tools  # noqa: E402
import etsy_api
from etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402
import trademark_screening  # noqa: E402 — advisory pre-publish trademark check (Scott-gated, see module docstring)
import business_tracker  # noqa: E402 — GET /api/business-tracker.xlsx workbook builder
from resilience import (  # noqa: E402
    classify_tool_exception,
    retry_with_backoff,
    TransientToolError,
    CircuitBreaker,
    CircuitBreakerOpenError,
)

# Shared breaker for every Anthropic call site -- main.py has no single chokepoint
# analogous to EtsyAPIClient._request(), so each of the ~7 call sites routes through
# _anthropic_create() below instead.
_anthropic_breaker = CircuitBreaker("anthropic_api", db_module=db)
# Same pattern, separate breaker, for xAI/Grok text calls (2026-08-05) -- one
# breaker per external text provider, same style as _anthropic_breaker above
# rather than trying to generalize a single breaker across two SDKs with
# different exception types.
_xai_breaker = CircuitBreaker("xai_api", db_module=db)


# Known-good fall
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-001 -->
<!-- TRASH id=20261025-002 date=2026-10-25 kind=file source="tools/api_server/frank_hud_mockup.py" reason="Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too." -->
## 20261025-002 · 2026-10-25 · file · `tools/api_server/frank_hud_mockup.py`
**Reason:** Before removing the digital-art workflows from Frank (Scott, 2026-10-25: switching to 3D prints and 3D print files). git history keeps it too.  
**Payload:** `data/trash/files/20261025-002__frank_hud_mockup.py`

```
"""
FRANK Command Center — static clickable HTML/CSS/JS mockup (Build Order step 0.5).

No backend wiring. This is purely a visual sign-off artifact so Scott can react to the
look of the full landscape HUD (left nav + every panel from the reference screenshots,
rebranded FRANK) before any real engineering goes in underneath it. Served at /frank,
completely separate from the live production dashboard at / so there is zero risk to
the running Hub while this is reviewed.

The whole layout is built as a fixed 1440x900 "stage" that JS scales (and letterboxes)
to fit whatever viewport opens it — phone or desktop — so the HUD always renders at its
real proportions instead of the browser's mobile viewport squishing the columns.

Real wiring (live data, approval gate, relay, voice) is Step 1+ in the approved plan —
every nav tab/panel here is a placeholder shell with the real future data source noted
in a code comment, not invented numbers presented as fact. LLM Status only lists
providers we actually have wired (Anthropic, OpenAI, Etsy) — no fake Gemini/Groq/Ollama
tiles, per the "no fake tiles anywhere" rule in the plan.

Step 2 (in progress): wiring real data into this shell, panel by panel. The page is a
plain string template (not f-string/`.format()`, since the JS below is full of literal
`{}`) rendered by `render_frank_hud()` which substitutes business-identity placeholders
(%%AGENT_NAME%%/%%AGENT_SHORT%%/%%OWNER%%) at startup. Auth uses session cookies — the
APP_SECRET_TOKEN is never injected into the page source.
"""

import json

import business_config
import check_default_branch  # tools/ is on sys.path (main.py) -- single source of
# truth for "which branch is the real active one" (see that module's docstring on
# the 2026-07-10 stale-default-branch incident), reused here so the Files screen's
# "download everything from GitHub" link can't independently drift from it.

_FRANK_HUD_MOCKUP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!-- maximum-scale=1/user-scalable=no removed 2026-07-08 (accessibility review, WCAG 1.4.4/1.4.10):
     blocking pinch/browser zoom locks out low-vision users entirely. fitStage() below no longer
     fights a deliberate zoom either — see the isMobileMode()/devicePixelRatio guard there. -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="%%AGENT_SHORT%%">
<meta name="theme-color" id="meta-theme-color" content="#241c2e">
<link rel="manifest" href="/frank-manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>%%AGENT_SHORT%% — Command Center</title>
<script type="importmap">
{"imports": {
  "onnxruntime-web": "/static/vendor/onnxruntime-web/ort.wasm.bundle.min.mjs",
  "three": "/static/vendor/three/build/three.module.js"
}}
</script>
<!-- GSAP (vendored, /static/vendor/gsap/gsap.min.js) -- a classic global script, NOT an
     importmap entry: this is GSAP's UMD/global build, and its fallback-to-globalThis path
     (`(t=t||self).window=t.window||{}`) throws `Cannot set property window of #<Window>
     which has only a getter` when evaluated as a real ES module (top-level `this` is
     undefined there, so it falls through to `self`, i.e. `window`, and then tries to
     assign `window.window` -- a read-only self-reference on the real Window object).
     Confirmed via a real headless-Chrome run before wiring this in. Loaded as a plain
     script here so it attaches `window.gsap` the way GSAP's docs actually expect. -->
<script src="/static/vendor/gsap/gsap.min.js"></script>
<!-- video.js (vendored, /static/vendor/videojs/video.min.js + video-js.min.css, Apache-2.0) --
     UMD/global build like GSAP 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-002 -->
<!-- TRASH id=20261025-003 date=2026-10-25 kind=file source="tests/test_coloring_listing_photos.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-003 · 2026-10-25 · file · `tests/test_coloring_listing_photos.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-003__test_coloring_listing_photos.py`

```
"""
Tests for staging real coloring-pack pages as Etsy listing photos (2026-07-25).

COLOR1003 published successfully (after the file-resolution fix) but ended
up with zero listing photos -- coloring_pages has no AI listing-photo
pipeline like digital_planner's. Scott's direct instruction was to use the
product's own real pack pages as the photos, not build a lifestyle-photo
pipeline. Real wrinkle found while building this: the existing pale-
background quality gate (meant to catch lazy/blank AI renders) would reject
a raw coloring page's near-white corners as "washed out" -- Scott chose to
make that gate category-aware (skip it for coloring_pages, since white paper
is the honest, real look of this product) rather than build a flat-lay
compositing pipeline.

Covers:
  - _extract_coloring_page_images(): root-level-PNG filtering, evenly-spaced
    sampling when a pack has more than 10 pages, returns everything when <=10
  - _check_no_pale_background(): category="coloring_pages" bypasses the
    check even for a genuinely near-white image; the default (no category)
    behavior is unchanged -- a real regression guard against accidentally
    weakening the gate for every other product type
  - _produce_coloring_pages_listing_photos(): staging success path, no-
    listing_id error, no-ZIP error, category mismatch error
  - _produce_listing_photos()'s category dispatch to the coloring_pages path
  - _validate_staged_action's listing_photo branch: a near-white photo
    passes when payload["category"] == "coloring_pages", fails otherwise

Run: python tests/test_coloring_listing_photos.py
"""
import asyncio
import io
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_coloring_photos_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "coloring-photos-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_white_png_bytes(size=(400, 500)) -> bytes:
    from PIL import Image as PILImage
    im = PILImage.new("RGB", size, (255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def _make_coloring_zip(n_pages: int) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(1, n_pages + 1):
            zf.writestr(f"page_{i:02d}.png", _make_white_png_bytes())
        # A nested/non-page file must never be counted as a page.
        zf.writestr("thumbnails/preview.png", _make_white_png_bytes())
        zf.writestr("README.txt", b"not a page")
    return buf.getvalue()


# ── _extract_coloring_page_images ────────────────────────────────────────

def test_extract_ignores_nested_and_non_png_entries():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(5))
        pages = server._extract_coloring_page_images(zpath, 10)
    names = [name for name, _ in pages]
    check(len(pages) == 5, f"expected 5 root-level pages, got {len(pages)}")
    check(all("/" not in n for n in names), f"must never include nested entries, got {names}")
    check(all(n.lower().endswith(".png") for n in names), f"must only include PNGs, got {names}")
    check("thumbnails/preview.png" not in names, "nested thumbnail must be excluded")


def test_extract_returns_all_pages_when_at_or_under_the_cap():
    with tempfile.TemporaryDirectory() as tmpdir:
        zpath = Path(tmpdir) / "pack.zip"
        zpath.write_bytes(_make_coloring_zip(8))
        pages = server._extract_coloring_page_images(zpath, 10)
    check(l
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-003 -->
<!-- TRASH id=20261025-004 date=2026-10-25 kind=file source="tests/test_coloring_theme_registry.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-004 · 2026-10-25 · file · `tests/test_coloring_theme_registry.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-004__test_coloring_theme_registry.py`

```
"""
Tests for the coloring-pages theme registry (2026-07-24): Scott, on the
Create screen's dynamic new-theme path: "It will be a set of 20 individual
coloring pages. Never to repeat a creation." Covers:

  - _normalize_subject() -- the exact-match dedup key.
  - The registry sidecar itself: read/write round-trip, tolerant of a
    missing/corrupt file (same volume-or-local pattern as
    _PRODUCT_CATALOG_OVERRIDES_PATH -- see .claude/rules/api-conventions.md).
  - _record_used_coloring_subjects() appends one entry per subject.
  - _generate_coloring_subjects() -- the raw Anthropic-call wrapper (mocked,
    no real API key/network involved).
  - _resolve_coloring_subjects() -- the full flow: caps at NEW_THEME_SET_SIZE,
    code-verifies the LLM's own output against the full registry and drops/
    retries anything that slips through, and surfaces a clear error when it
    can't reach the target count after a retry.

Run: python tests/test_coloring_theme_registry.py
"""
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_coloringregistry_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "coloringregistry-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _tmp_registry_path() -> Path:
    return Path(tempfile.mkdtemp(prefix="frank_coloring_registry_")) / "coloring_theme_registry.json"


def test_normalize_subject_collapses_whitespace_and_case():
    check(server._normalize_subject("  A Sleepy   Fox ") == "a sleepy fox",
          f"got {server._normalize_subject('  A Sleepy   Fox ')!r}")
    check(server._normalize_subject("a sleepy fox") == server._normalize_subject("A SLEEPY FOX"),
          "case must not affect the normalized key")


def test_registry_read_missing_file_returns_empty_list():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        check(server._coloring_theme_registry() == [], "a never-written registry must read as []")


def test_registry_read_corrupt_file_returns_empty_list():
    path = _tmp_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        check(server._coloring_theme_registry() == [], "a corrupt registry file must read as [], not raise")


def test_registry_write_read_round_trip():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._write_coloring_theme_registry([{"subject": "a fox", "normalized": "a fox"}])
        got = server._coloring_theme_registry()
    check(got == [{"subject": "a fox", "normalized": "a fox"}], f"got {got}")
    check(path.exists(), "the registry file must actually be written to disk")


def test_record_used_coloring_subjects_appends_one_entry_per_subject():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._record_used_coloring_subjects("COLOR_TEST", "woodland animals", ["a fox", "a deer"])
        registry = server._coloring_theme_registry()
    check(len(registry) == 2, f"expected 2 entries, got {len(registry)}")
    check({e["subject"] for e in registry} == {"a fox", "a deer"}, f"got {registry}")
    check(all(e["product_id"] == "COLOR_TEST" for e in registry), f"got {registry}")
    check(all(e["theme"] == "woodland animals" for e in registry), f"got {registry}")
    check(all("created_at" in e and e["created_at"] for e in registry), f"got {r
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-004 -->
<!-- TRASH id=20261025-005 date=2026-10-25 kind=file source="tests/test_planner_photo_pipeline.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-005 · 2026-10-25 · file · `tests/test_planner_photo_pipeline.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-005__test_planner_photo_pipeline.py`

```
"""
Tests for Frank upgrade Wave 4, item A1 (2026-07-17): planner listing photos
now go through the real, self-verifying AI pipeline (tools/listing_photo_
pipeline.py) instead of a pure-PIL clip-art mockup.

Root cause this closes: `tools/gen_planner_listing_photos.py`'s
generate_for_planner() -- the function `_produce_listing_photos()` (main.py)
used to call -- never called an AI image model at all. Its own docstring
said so plainly ("Pure local render"). That's the actual reason planner
photos read as fake: not AI artifacts leaking through, a total absence of
photorealistic rendering for the shop's core product line (DP1026-1034).

Covers three layers:
  1. tools/listing_photo_pipeline.py -- the cfg-driven style-anchor fallback
     (_style_anchor_for), the finish pass (_apply_finish_pass: grain +
     vignette + unsharp), and PhotoResult's new fields.
  2. tools/gen_planner_listing_photos.py -- generate_ai_photos_for_planner(),
     the new glue function: renders real PDF pages via the existing
     render_page(), locates real sticker sheet PNGs via the same 3-way
     fallback chain make_sticker_showcase() already uses, and hands
     everything to the real pipeline.
  3. tools/api_server/main.py's _produce_listing_photos() -- routes passed
     photos into the existing staged-action approval queue when a listing_id
     exists (same path SS-series photos already use), falls back to the old
     Files-screen folder-drop UX for pre-publish drafts with no listing_id
     yet (DP1030-1034), and never silently drops a failed or realism-flagged
     photo.

Run: python tests/test_planner_photo_pipeline.py
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_photo_pipeline_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "photo-pipeline-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_photo_pipeline as lpp  # noqa: E402
import gen_planner_listing_photos as glp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── listing_photo_pipeline.py: style anchor fallback ────────────────────────
def test_hardcoded_style_anchor_unchanged_for_original_four():
    # DP1026-1029 must keep using their hand-tuned entries verbatim (plus the
    # new film-grain/commercial-photography phrase appended to each).
    anchor = lpp._style_anchor_for("DP1026", None)
    check("Lavender purple" in anchor, f"DP1026's hand-tuned anchor must be used as-is, got: {anchor[:100]!r}")
    check("sharp commercial product photography" in anchor,
          f"DP1026's anchor should carry the new vocabulary too, got: {anchor[:150]!r}")


def test_fallback_style_anchor_for_unconfigured_product_uses_cfg():
    cfg = {"theme": "Matcha Serenity", "color": (126, 200, 164), "accent": (184, 204, 142), "bg": (247, 249, 243)}
    anchor = lpp._style_anchor_for("DP1030", cfg)
    check("Matcha Serenity" in anchor, f"the fallback anchor must use the real theme name, got: {anchor[:150]!r}")
    check("#7EC8A4" in anchor, f"the fallback anchor must use the real hex color, got: {anchor[:200]!r}")
    check("cream linen desk surface" in anchor, f"a light theme should get a light desk surface, got: {anchor!r}")


def test_fallback_style_anchor_detects_dark_theme():
    cfg = {"theme": "Midnight Kawaii", "color": (128, 64, 156), "accent": (0, 229, 255), "bg": (26, 26, 46)}
    anchor = lpp._style_anchor_for("DP1032", cfg)
    check("deep charcoal desk surface" in anchor, f"a dark theme (bg sum < 400) should get a dark desk, got: {anchor!r}")


def test_no_cfg_and_no_hardcoded_entry_returns_empty_not_crash():
    anchor = lpp._style_an
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-005 -->
<!-- TRASH id=20261025-006 date=2026-10-25 kind=file source="tests/test_knowledge_base_expansion.py" reason="Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only)." -->
## 20261025-006 · 2026-10-25 · file · `tests/test_knowledge_base_expansion.py`
**Reason:** Tests for digital-art features removed from Frank (Scott, 2026-10-25: 3D prints and 3D print files only).  
**Payload:** `data/trash/files/20261025-006__test_knowledge_base_expansion.py`

```
"""
Tests for the 2026-08-08 knowledge-base expansion, prompted by Scott: "I need
frank to have more knowledge... he needs more ability to make better coloring
pages... make sure we have [repos/tools/skills]."

Audited data/knowledge_base/ + CLAUDE.md first: wall art, SVG packs, digital
planners, and sticker packs already had deep, sourced research
(design_quality_research_2026-06.md, competitor_research_2026.md, CLAUDE.md's
own Sticker Pack Design Standards section). Coloring pages had NONE -- no
competitor research, no design-technique doc anywhere. Also found the monthly
competitor-research refresh (_run_competitor_research_refresh in main.py)
claimed to cover 4 product lines in its own prompt text but
_COMPETITOR_RESEARCH_SEARCH_TERMS only ever had 3 entries (no coloring pages,
no SVG packs) -- a real gap between what the automation claims to do and what
it actually searches for.

Covered here:
  1. A new, web-search-grounded knowledge_base doc for coloring pages exists
     and is auto-discoverable via read_knowledge_base_doc's glob (no
     registration step needed -- see main.py's _kb_docs()).
  2. _COMPETITOR_RESEARCH_SEARCH_TERMS now includes coloring pages + SVG packs,
     matching what the refresh prompt text already claimed to cover.
  3. All 4 coloring-page style-DNA prompt constants now include the
     closed-outline instruction sourced from real published coloring-book
     design guides (the one concrete prompt-technique gap the research found).

Run: python tests/test_knowledge_base_expansion.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_kbexpand_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "kbexpand-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import generate_coloring_pages as gcp  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_coloring_page_doc_exists_and_is_kb_discoverable():
    doc_path = ROOT / "data" / "knowledge_base" / "coloring_page_design_and_market_research.md"
    check(doc_path.is_file(), f"expected {doc_path} to exist")
    text = doc_path.read_text()
    check("closed" in text.lower() and "outline" in text.lower(),
          "doc should discuss closed/enclosed outlines (the real prompt-technique gap found)")
    check("$" in text, "doc should cite real pricing data, not just qualitative claims")

    filenames = {d["filename"] for d in server._kb_docs()}
    check("coloring_page_design_and_market_research.md" in filenames,
          f"new doc must be auto-discovered by _kb_docs()'s glob, got: {sorted(filenames)}")

    resolved = server._resolve_kb_doc("coloring_page_design_and_market_research.md")
    check(resolved == doc_path.resolve(), f"_resolve_kb_doc should resolve to the real file, got {resolved}")


def test_competitor_research_search_terms_cover_all_4_product_lines():
    terms_text = " ".join(server._COMPETITOR_RESEARCH_SEARCH_TERMS).lower()
    check("coloring" in terms_text,
          f"search terms must include a coloring-pages term, got: {server._COMPETITOR_RESEARCH_SEARCH_TERMS}")
    check("svg" in terms_text,
          f"search terms must include an SVG-pack term, got: {server._COMPETITOR_RESEARCH_SEARCH_TERMS}")
    check(len(server._COMPETITOR_RESEARCH_SEARCH_TERMS) >= 5,
          f"expected at least 5 terms (3 original + 2 new), got {len(server._COMPETITOR_RESEARCH_SEARCH_TERMS)}")


def test_coloring_page_styles_all_specify_closed_outlines():
    for name, style in [
        ("_STYLE", gcp._STYLE),
        ("_STYLE_BOLD", gcp._STYLE_BOLD),
        ("_STYLE_ADULT", gcp._STYLE_ADULT),
        ("_STYLE_KIDS", gcp._STYLE_KIDS),
 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261025-006 -->
<!-- TRASH id=20261030-001 date=2026-10-30 kind=snippet source="openscad_models/valentine_2027/mailboxes/love_letter/cupid.scad" reason="Flat stepped cut-out Cupid replaced by a sculpted relief one at Scott's request ('I want the Cupid to have depth'), 2026-10-30" -->
## 20261030-001 · 2026-10-30 · snippet · `openscad_models/valentine_2027/mailboxes/love_letter/cupid.scad`
**Reason:** Flat stepped cut-out Cupid replaced by a sculpted relief one at Scott's request ('I want the Cupid to have depth'), 2026-10-30  
**Payload:** `data/trash/files/20261030-001__snippet.txt`

```
// Cupid for the Giant Love Letter (2026-10-30). Scott: "make it a little more
// fun ... a cartoony Cupid that is a separate print that has a slight divot in
// the front of the envelope that it would set in"; he picked that and heart
// stickers. A chubby cherub with curls, small white wings and a white wrap
// (school-appropriate), drawing a red bow with a heart-tipped arrow, aimed up
// at the child's name.
//
// He prints face up, his back flat on the bed. He is a stepped cut-out: each
// shape stands at its own height in its own colour, the nearer ones taller, so
// every level edge is on the 0.2 layer grid and the colours change only where
// the shapes meet. Four filaments: skin, white, red, dark.
//
// He sits in a pocket 1.0 deep in the envelope's front and presses onto two
// diamond pegs standing in it. His holes have crush ribs, so the fit is snug
// whatever the printer's hole shrinkage; a drop of glue makes it permanent.
// About 55 x 62, far over the small-parts size.
//
// Local frame: x across (he faces +x), y up, z out of the envelope.


// ---------- his shapes, in 2D ----------
HEAD = [2, 41]; HEAD_R = 11.5;
TORSO = [0, 20];
AIM = 22;                        // the bow and arrow tilt up toward the name
PIV = [4, 26];                   // ...about his chest
module aimed() translate(PIV) rotate(AIM) translate(-PIV) children();
function aimp(p) = PIV + [[cos(AIM), -sin(AIM)], [sin(AIM), cos(AIM)]] * (p - PIV);
module capsule(a, b, r) hull() { translate(a) circle(r, $fn = 40); translate(b) circle(r, $fn = 40); }
module ellipse(c, rx, ry, a = 0) translate(c) rotate(a) scale([rx, ry]) circle(1, $fn = 72);

module c_head() translate(HEAD) circle(HEAD_R, $fn = 96);
// curls round the top and back of his head, and one on his forehead
CURLS = [for (a = [72 : 26 : 202]) [HEAD + 10.6 * [cos(a), sin(a)], 3.6]];
module c_hair() union() {
    for (c = CURLS) translate(c[0]) circle(c[1], $fn = 40);
    intersection() { translate(HEAD) circle(HEAD_R + 0.2, $fn = 96); translate(HEAD + [-5.5, 7.5]) circle(9.0, $fn = 80); }
    translate(HEAD + [4.8, 10.2]) circle(2.6, $fn = 36);
}
module c_torso() ellipse(TORSO, 9.8, 11, 0);
module c_wrap() intersection() {        // his white wrap, round his middle
    offset(delta = 0.01) c_torso();
    translate([-20, -10]) square([40, TORSO.y - 2.5 + 10]);
}
module c_legs() { ellipse([-4.8, 8.2], 4.2, 5.4, -12); ellipse([5.0, 7.8], 4.2, 5.4, 14); }
// wings on his back: three feathers each, the upper wing then the lower
module c_wings() union() {
    for (f = [[[-9, 31], [-21, 41], 3.6], [[-9, 28], [-24, 33], 3.4], [[-9, 25], [-22, 25], 3.2]]) capsule(f[0], f[1], f[2]);
}
module c_wing_lines() for (f = [[[-12, 33.2], [-19, 38.6]], [[-12, 29.6], [-21, 32.0]], [[-12, 26.4], [-20, 25.8]]]) capsule(f[0], f[1], 0.45);
// the bow hand holds the bow out in front; the other hand draws the string
BOW_HAND = [19.5, 27]; DRAW_HAND = [4.5, 27.5];
module c_arms() aimed() { capsule([5.5, 25], BOW_HAND, 2.4); capsule([-3, 25.5], DRAW_HAND, 2.5); }
BOW_C = [7, 27]; BOW_R = 13.2; BOW_A = 58;
module c_bow() aimed() difference() {
    translate(BOW_C) intersection() {
        difference() { circle(BOW_R + 0.9, $fn = 120); circle(BOW_R - 0.9, $fn = 120); }
        polygon([[0, 0], [40 * cos(BOW_A), -40 * sin(BOW_A)], [40, 0], [40 * cos(BOW_A), 40 * sin(BOW_A)]]);
    }
}
function bow_tip(s) = BOW_C + BOW_R * [cos(BOW_A), s * sin(BOW_A)];
module c_string() aimed() { capsule(bow_tip(1), DRAW_HAND, 0.6); capsule(bow_tip(-1), DRAW_HAND, 0.6); }
module c_heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
ARROW_TIP = [33, 27];
module c_shaft() aimed() capsule([0.5, 27.5], ARROW_TIP - [3, 0], 0.8);
module c_arrowhead() aimed() translate(ARROW_TIP) rotate(-90) c_heart2d(8.5);
module c_fletch() aimed() for (s = [-1, 1]) polygon([[-1.8, 27.5], [2.4, 27.5], [-0.6, 27.5 + s * 3.0], [-3.4, 27.5 + s * 3.0]]);
// his face looks along the arrow: eyes, a smile, rosy cheeks
module c_eyes() for (e = [[4.2, -0.6], [9.6, -0.4]]) ellipse(HEAD + e, 1.3, 1.8);
module c_shine() for (e = [[4.6, 0.3], [10.0, 0.5]]) translate(HEAD + e) circle(0.45, $fn = 20);
module c_smile() for (i = [0 : 7]) let (t0 = -30 + i * 10, t1 = t0 + 10)
    capsule(HEAD + [7, -3.4] + 3.2 * [sin(t0), -cos(t0) * 0.6], HEAD + [7, -3.4] + 3.2 * [sin(t1), -cos(t1) * 0.6], 0.45);
module c_wrap_heart() translate(TORSO + [1.5, -5.5]) c_heart2d(4.6);
module c_cheeks() { translate(HEAD + [10.4, -4.4]) circle(1.5, $fn = 30); translate(HEAD + [1.0, -4.8]) circle(1.6, $fn = 30); }

// ---------- the stack: shape, height, colour (0 skin, 1 white, 2 red, 3 dark) ----------
// a point's column is the colour of the tallest shape over it, at that height
//         wings bow  str  legs torso wrap arms fletch shaft head head eyes smile shine cheeks hair wrap-heart
C_H   = [3.0,  3.6, 2.6, 4.6, 5.2,  5.6, 5.8, 6.2,   6.0,  6.0, 6.2, 6.4, 6.4,  6.4,  6.4,   6.8, 6.0];
C_COL = [1,    3,   3,   0,   0,    1,   0,   2,     3,    2,   0,   3,   3,    1,    2,     3,   2];
module c_item(i) {
    if      (i == 0)  c_wings();
    else if (i == 1)  c_bow();
    else if (i == 2)  c_string();
    else if (i == 3)  c_legs();
    else if (i == 4)  c_torso();
    else if (i == 5)  c_wrap();
    else if (i == 6)  c_arms();
    else if (i == 7)  c_fletch();
    else if (i == 8)  c_shaft();
    else if (i == 9)  c_arrowhead();
    else if (i == 10) c_head();
    else if (i == 11) c_eyes();
    else if (i == 12) c_smile();
    else if (i == 13) c_shine();
    else if (i == 14) c_cheeks();
    else if (i == 15) c_hair();
    else if (i == 16) c_wrap_heart();
}
module c_column(i) difference() {
    c_item(i);
    for (j = [0 : len(C_H) - 1]) if (j != i && (C_H[j] > C_H[i] || (C_H[j] == C_H[i] && j > i))) c_item(j);
}
module cupid_outline() union() for (i = [0 : len(C_H) - 1]) c_item(i);
// the feathers' lines are grooves 0.4 deep, 0.9 wide, cut into the wings' top
module wing_grooves() translate([0, 0, C_H[0] - 0.4]) linear_extrude(1) c_wing_lines();
// his holes take the envelope's pegs; under his head and his middle, where he
// is thickest
PEGS = [HEAD + [-2, -1], TORSO + [-1, -5]];
// A peg is a wedge standing out of the upright wall: flat on top, its
// underside climbing from the wall at 37 deg, so it grows out of the wall
// layer by layer. A diamond peg began each one as a sliver in mid-air at its
// lower point, and the slicer propped both from the bed (2026-10-30).
PEG_W = 2.4;                     // across
PEG_L = 2.2;                     // how far it stands from the pocket floor
PEG_TIP = 1.6;                   // its height at the tip
PEG_ROOT = PEG_TIP + PEG_L / tan(37);   // and at the wall, 4.5
// the peg in his frame: x across, y up (top at y = 0), z out from the floor
module peg_shape(c = 0) hull() {
    translate([-PEG_W / 2 - c, -PEG_ROOT - c, 0]) cube([PEG_W + 2 * c, PEG_ROOT + 2 * c, 0.01]);
    translate([-PEG_W / 2 - c, -PEG_TIP - c, PEG_L + c - 0.01]) cube([PEG_W + 2 * c, PEG_TIP + 2 * c, 0.01]);
}
// where a peg's top edge sits, for a peg centred on p
function peg_at(p) = p + [0, PEG_ROOT / 2];
HOLE_C = 0.25;                   // clearance round the peg; the ribs take it up
RIB_R = 0.35; RIB_IN = 0.1;      // ribs on the side walls reach 0.1 into the peg
// His hole is the peg's full root height all the way in, straight-walled:
// the wedge's 37 deg underside is 53 deg in him, printed face up, and copying
// it drew 330 support moves (2026-10-30). The peg still sits on the hole's
// sides (the ribs), its top and its root.
HOLE = [PEG_W + 2 * HOLE_C, PEG_ROOT + 2 * HOLE_C];
HOLE_D = PEG_L + HOLE_C;
ROOF = (HOLE.x / 2) / tan(37);   // a hipped roof at 37 deg on every side
module cupid_hole() translate([0, HOLE_C - HOLE.y / 2, 0]) difference() {
    union() {
        translate([-HOLE.x / 2, -HOLE.y / 2, -0.01]) cube([HOLE.x, HOLE.y, HOLE_D + 0.01]);
        translate([0, 0, HOLE_D - 0.01]) hull() {
            translate([-HOLE.x / 2, -HOLE.y / 2, 0]) cube([HOLE.x, HOLE.y, 0.01]);
            translate([-0.01, -(HOLE.y / 2 - HOLE.x / 2), ROOF]) cube([0.02, HOLE.y - HOLE.x, 0.01]);
        }
        // the mouth opens 0.3 against the first layer's squash
        hull() {
            translate([-HOLE.x / 2 - 0.3, -HOLE.y / 2 - 0.3, -0.01]) cube([HOLE.x + 0.6, HOLE.y + 0.6, 0.01]);
            translate([-HOLE.x / 2, -HOLE.y / 2, 0.4]) cube([HOLE.x, HOLE.y, 0.01]);
        }
    }
    // crush ribs, two on each side wall, reaching RIB_IN into the peg
    for (sx = [-1, 1], y = [HOLE.y / 2 - HOLE_C - PEG_TIP * 0.3, HOLE.y / 2 - HOLE_C - PEG_TIP * 0.8])
        translate([sx * (PEG_W / 2 + RIB_R - RIB_IN), y, -1]) cylinder(r = RIB_R, h = HOLE_D + ROOF + 2, $fn = 16);
}

// ---------- the colour parts, as printed ----------
module cupid_colour(c) difference() {
    union() for (i = [0 : len(C_H) - 1]) if (C_COL[i] == c) linear_extrude(C_H[i]) c_column(i);
    for (p = PEGS) translate(peg_at(p)) cupid_hole();
    wing_grooves();
}
module cupid_skin()  cupid_colour(0);
module cupid_white() cupid_colour(1);
module cupid_red()   cupid_colour(2);
module cupid_dark()  cupid_colour(3);
// merged, for the gate: every shape at full height overlaps the next, so the
// union closes
module cupid_print() difference() {
    union() for (i = [0 : len(C_H) - 1]) linear_extrude(C_H[i]) c_item(i);
    for (p = PEGS) translate(peg_at(p)) cupid_hole();
    wing_grooves();
}
```

<!-- /TRASH 20261030-001 -->
<!-- TRASH id=20261103-001 date=2026-11-03 kind=snippet source="openscad_models/clickers/gingerbread_tin/gingerbread_tin_clicker.scad" reason="The pre-thread seated lid, kept for the canister until the canister also took the thread (Scott, 2026-11-03)" -->
## 20261103-001 · 2026-11-03 · snippet · `openscad_models/clickers/gingerbread_tin/gingerbread_tin_clicker.scad`
**Reason:** The pre-thread seated lid, kept for the canister until the canister also took the thread (Scott, 2026-11-03)  
**Payload:** `data/trash/files/20261103-001__snippet.txt`

```
// The lid as it was before the thread: a spigot dropping 2 mm inside a lip,
// then a flare. The storage canister's closed lid is built on it and still
// seats on the canister this way.
module lid_solid_seated() rotate_extrude($fn = 240) polygon(concat(
    [[0, S], [SPIG_R, S], [SPIG_R, S + JOINT], [LID_R, S + JOINT + 2.4]],
    [for (k = [0 : 4]) let (z = RIM - 0.8 + (k + 1) * 0.16) [LID_R - 0.8 + sqrt(max(0, 0.64 - pow(z - (RIM - 0.8), 2))), z]],
    [[0, RIM]]));
```

<!-- /TRASH 20261103-001 -->
<!-- TRASH id=20261103-002 date=2026-11-03 kind=snippet source="openscad_models/clickers/gingerbread_tin/gingerbread_tin_clicker.scad" reason="The pre-thread seated lid, kept for the canister until the canister also took the thread (Scott, 2026-11-03)" -->
## 20261103-002 · 2026-11-03 · snippet · `openscad_models/clickers/gingerbread_tin/gingerbread_tin_clicker.scad`
**Reason:** The pre-thread seated lid, kept for the canister until the canister also took the thread (Scott, 2026-11-03)  
**Payload:** `data/trash/files/20261103-002__snippet.txt`

```
module lid_seated() union() { difference() { lid_solid_seated(); nest(); mx_plate_cut(S); } lid_berries(); }
```

<!-- /TRASH 20261103-002 -->
<!-- TRASH id=20261103-003 date=2026-11-03 kind=snippet source="openscad_models/clickers/gingerbread_tin/gingerbread_tin_clicker.scad" reason="The pre-thread seated lid, kept for the canister until the canister also took the thread (Scott, 2026-11-03)" -->
## 20261103-003 · 2026-11-03 · snippet · `openscad_models/clickers/gingerbread_tin/gingerbread_tin_clicker.scad`
**Reason:** The pre-thread seated lid, kept for the canister until the canister also took the thread (Scott, 2026-11-03)  
**Payload:** `data/trash/files/20261103-003__snippet.txt`

```
SPIG_R = TR - LIP_W - JOINT_CLR; // the lid's spigot, inside the tin's lip
```

<!-- /TRASH 20261103-003 -->
<!-- TRASH id=20261103-004 date=2026-11-03 kind=file source="openscad_models/valentine_2027/mailboxes/love_letter/images/cupid_white_preview_angle.png" reason="Cupid preview angle render of the superseded draft; replaced by the top view and the side-by-side with the reference" -->
## 20261103-004 · 2026-11-03 · file · `openscad_models/valentine_2027/mailboxes/love_letter/images/cupid_white_preview_angle.png`
**Reason:** Cupid preview angle render of the superseded draft; replaced by the top view and the side-by-side with the reference  
**Payload:** `data/trash/files/20261103-004__cupid_white_preview_angle.png`

```
(binary file — see payload copy)
```

<!-- /TRASH 20261103-004 -->
<!-- TRASH id=20261104-001 date=2026-11-04 kind=file source="openscad_models/valentine_2027/mailboxes/love_letter/cupid.scad" reason="The sculpted four-colour Cupid, replaced on the envelope by the flat white charm cupid_white.scad that Scott chose (2026-11-04); its peg and hole block moved to cupid_peg.scad, shortened for a 3 mm charm" -->
## 20261104-001 · 2026-11-04 · file · `openscad_models/valentine_2027/mailboxes/love_letter/cupid.scad`
**Reason:** The sculpted four-colour Cupid, replaced on the envelope by the flat white charm cupid_white.scad that Scott chose (2026-11-04); its peg and hole block moved to cupid_peg.scad, shortened for a 3 mm charm  
**Payload:** `data/trash/files/20261104-001__cupid.scad`

```
// Cupid for the Giant Love Letter (2026-10-30). Scott: "make it a little more
// fun ... a cartoony Cupid that is a separate print that has a slight divot in
// the front of the envelope that it would set in"; then, on the first one, a
// flat stepped cut-out: "I want the Cupid to have depth to it. Make its
// features stick out ... Fix the wings also and make him look better."
//
// So he is sculpted relief: a domed head and belly, round arms and legs,
// puffy curls, cheeks, a nose and an ear on the curve of his face, and a
// feathered wing, a rounded upper wing with four long feathers fanning back
// from it. He draws a bow with a heart-tipped arrow, aimed up at the name,
// and wears a white wrap (school-appropriate) with a little heart on it.
//
// He prints face up, his back flat on the bed. Every shape that reaches his
// outline rises straight from the bed to its dome (col()), and every small
// feature sits on the curve of what is under it, so nothing hangs over air.
// Four filaments: skin, white, red, dark. Each colour is its shapes minus
// the shapes in front of them, so the colour parts never overlap.
//
// He sits in a pocket 1.0 deep in the envelope's front and presses onto two
// wedge pegs standing in it; his holes have crush ribs. About 55 x 60 and
// 10 tall, far over the small-parts size.
//
// Local frame: x across (he faces +x), y up, z out of the envelope.

$fn = 36;
HEAD = [2, 41]; HEAD_R = 11.5; HEAD_Z0 = 2.0; HEAD_RZ = 7.6;   // the head: top at 9.6
TORSO = [0, 20];
AIM = 22;                        // the bow and arrow tilt up toward the name
PIV = [4, 26];                   // ...about his chest
function aimp(p) = PIV + [[cos(AIM), -sin(AIM)], [sin(AIM), cos(AIM)]] * (p - PIV);
function p3(p, z) = [p.x, p.y, z];

// ---------- building blocks ----------
// a shape and everything under it down to the bed: a dome on a straight
// column, so it never overhangs. Children must be convex.
module col() hull() { children(); linear_extrude(0.01) projection() children(); }
module ell(c, r) translate(c) scale(r) sphere(1, $fn = 48);           // an ellipsoid
module caps(a, b, ra, rb = -1) hull() {                               // a rounded rod
    translate(a) sphere(ra);
    translate(b) sphere(rb < 0 ? ra : rb);
}
// the head's surface height over a point, for things set on the face
function head_z(p) = let (d = norm(p - HEAD) / HEAD_R) HEAD_Z0 + HEAD_RZ * sqrt(max(0, 1 - d * d));

// ---------- the wing: three rows of flat, overlapping feathers ----------
// Each feather is a pillow: its outline at full height with softly rounded
// edges, terraced on the 0.2 layer grid, so it prints as drawn. Where two
// feathers meet their rounded edges leave a crease between them. Back to
// front: long flight feathers, shorter ones over their roots, then the
// scalloped upper wing, the tallest. (Round rods read as fingers, 2026-10-30.)
module pillow(h, rr) for (z = [0.2 : 0.2 : h + 0.001]) let (u = z - (h - rr), inset = u <= 0 ? 0 : rr - sqrt(max(0, rr * rr - u * u)))
    translate([0, 0, -0.01]) linear_extrude(z + 0.01) offset(delta = -inset) children();
module feather2d(a, b, ra, rb) hull() { translate(a) circle(ra); translate(b) circle(rb); }
FLIGHT = [   // root, tip, root radius, tip radius: tips touching, as on a real wing
    [[-12, 36], [-26.5, 40.5], 3.2, 2.6],
    [[-13, 32.5], [-28.5, 35.2], 3.2, 2.7],
    [[-13, 29], [-28, 29.6], 3.1, 2.7],
    [[-12, 26], [-25.5, 24.0], 3.0, 2.6],
    [[-9.5, 24], [-21, 18.8], 2.9, 2.5]];
SECONDARY = [
    [[-9, 36], [-19.5, 39.6], 3.2, 2.5],
    [[-9.5, 32.5], [-21, 34.0], 3.2, 2.6],
    [[-9.5, 29], [-20.5, 28.8], 3.1, 2.5],
    [[-8.5, 26], [-18, 23.6], 3.0, 2.4]];
// the wing sweeps up and back from his shoulder, a cherub's wing
WING_AT = [-6, 32]; WING_TILT = -32;
module wing() translate(WING_AT) rotate(WING_TILT) translate(-WING_AT) union() {
    for (f = FLIGHT) pillow(1.6, 1.0) feather2d(f[0], f[1], f[2], f[3]);
    for (f = SECONDARY) pillow(2.4, 1.2) feather2d
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261104-001 -->
<!-- TRASH id=20261104-002 date=2026-11-04 kind=file source="openscad_models/valentine_2027/mailboxes/love_letter/checks/fidelity_cupid_print.json" reason="checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid" -->
## 20261104-002 · 2026-11-04 · file · `openscad_models/valentine_2027/mailboxes/love_letter/checks/fidelity_cupid_print.json`
**Reason:** checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid  
**Payload:** `data/trash/files/20261104-002__fidelity_cupid_print.json`

```
{
 "layers": 34,
 "model_volume_mm3": 7368.9,
 "dropped_mm3": 0.72,
 "filled_mm3": 0.41,
 "colour_mm3": 0.04,
 "flagged": 0,
 "clusters": [
  {
   "kind": "filled",
   "colour": "#F9C9A6",
   "tool": 1,
   "volume_mm3": 0.407,
   "z_mm": [
    0.0,
    5.8
   ],
   "layers": 29,
   "at_xy": [
    10.4,
    31.2
   ],
   "side": "right",
   "max_width_mm": 0.08,
   "depth_mm": 0.14,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.114,
   "z_mm": [
    0.0,
    6.0
   ],
   "layers": 30,
   "at_xy": [
    27.2,
    35.7
   ],
   "side": "right",
   "max_width_mm": 0.11,
   "depth_mm": 0.15,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.112,
   "z_mm": [
    0.0,
    6.0
   ],
   "layers": 30,
   "at_xy": [
    26.7,
    37.1
   ],
   "side": "right",
   "max_width_mm": 0.11,
   "depth_mm": 0.15,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.089,
   "z_mm": [
    0.0,
    3.0
   ],
   "layers": 15,
   "at_xy": [
    1.2,
    40.9
   ],
   "side": "back",
   "max_width_mm": 0.19,
   "depth_mm": 0.23,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.068,
   "z_mm": [
    0.0,
    3.6
   ],
   "layers": 18,
   "at_xy": [
    18.5,
    35.2
   ],
   "side": "right",
   "max_width_mm": 0.11,
   "depth_mm": 0.15,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.065,
   "z_mm": [
    0.0,
    3.6
   ],
   "layers": 18,
   "at_xy": [
    20.1,
    31.3
   ],
   "side": "right",
   "max_width_mm": 0.11,
   "depth_mm": 0.15,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.047,
   "z_mm": [
    0.0,
    0.2
   ],
   "layers": 1,
   "at_xy": [
    1.3,
    41.8
   ],
   "side": "back",
   "max_width_mm": 0.36,
   "depth_mm": 0.43,
   "flag": false
  },
  {
   "kind": "colour",
   "colour": "#F9C9A6",
   "tool": 1,
   "volume_mm3": 0.044,
   "z_mm": [
    0.0,
    6.2
   ],
   "layers": 31,
   "at_xy": [
    -5.4,
    39.7
   ],
   "side": "back",
   "max_width_mm": 0.06,
   "depth_mm": 0.06,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#D7263D",
   "tool": 3,
   "volume_mm3": 0.043,
   "z_mm": [
    0.0,
    0.2
   ],
   "layers": 1,
   "at_xy": [
    0.3,
    16.0
   ],
   "side": "front",
   "max_width_mm": 0.32,
   "depth_mm": 0.39,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.042,
   "z_mm": [
    0.0,
    0.2
   ],
   "layers": 1,
   "at_xy": [
    -1.3,
    41.8
   ],
   "side": "back",
   "max_width_mm": 0.31,
   "depth_mm": 0.38,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#F4F1EA",
   "tool": 2,
   "volume_mm3": 0.042,
   "z_mm": [
    0.4,
    2.6
   ],
   "layers": 11,
   "at_xy": [
    0.5,
    12.9
   ],
   "side": "front",
   "max_width_mm": 0.11,
   "depth_mm": 0.15,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#F9C9A6",
   "tool": 1,
   "volume_mm3": 0.039,
   "z_mm": [
    0.0,
    2.6
   ],
   "layers": 13,
   "at_xy": [
    1.2,
    40.8
   ],
   "side": "back",
   "max_width_mm": 0.13,
   "depth_mm": 0.22,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#D7263D",
   "tool": 3,
   "volume_mm3": 0.014,
   "z_mm": [
    5.2,
    6.2
   ],
   "layers": 5,
   "at_xy": [
    -4.4,
    27.4
   ],
   "side": "left",
   "max_width_mm": 0.09,
   "depth_mm": 0.2,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#F4F1EA",
   "tool": 2,
   "volume_mm3": 0.009,
   "z_mm": [
    4.0,
    4.4
   ],
   "layers": 2,
   "at_xy": [
    -0.8,
    14.3
   ],
   "side": "front",
   "max_width_mm": 0.12,
   "depth_mm": 0.16,
   "flag": false
  },
  {
   "kind": "dropped",
   "colour": "#3B2A3A",
   "tool": 4,
   "volume_mm3": 0.008,
   "z_mm": [
    5.4,
    5.8
   ],
   
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261104-002 -->
<!-- TRASH id=20261104-003 date=2026-11-04 kind=file source="openscad_models/valentine_2027/mailboxes/love_letter/checks/fidelity_cupid_print.txt" reason="checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid" -->
## 20261104-003 · 2026-11-04 · file · `openscad_models/valentine_2027/mailboxes/love_letter/checks/fidelity_cupid_print.txt`
**Reason:** checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid  
**Payload:** `data/trash/files/20261104-003__fidelity_cupid_print.txt`

```
Traceback (most recent call last):
  File "/home/user/Etsy/openscad_models/valentine_2027/mailboxes/../../../tools/print_fidelity.py", line 772, in <module>
    main()
  File "/home/user/Etsy/openscad_models/valentine_2027/mailboxes/../../../tools/print_fidelity.py", line 747, in main
    rep, _ = compare(parts, work, supports=not a.no_supports, layer_height=a.layer_height,
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/user/Etsy/openscad_models/valentine_2027/mailboxes/../../../tools/print_fidelity.py", line 386, in compare
    raise RuntimeError("not closed meshes, so there is nothing to compare against: " + ", ".join(open_parts)
RuntimeError: not closed meshes, so there is nothing to compare against: love_letter/parts/cupid.stl, love_letter/parts/cupid_dark.stl -- check the closed export (a CGAL union, or part_mesh.py union) instead
```

<!-- /TRASH 20261104-003 -->
<!-- TRASH id=20261104-004 date=2026-11-04 kind=file source="openscad_models/valentine_2027/mailboxes/love_letter/checks/fragility_cupid_print.txt" reason="checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid" -->
## 20261104-004 · 2026-11-04 · file · `openscad_models/valentine_2027/mailboxes/love_letter/checks/fragility_cupid_print.txt`
**Reason:** checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid  
**Payload:** `data/trash/files/20261104-004__fragility_cupid_print.txt`

```
  x: 1 slender run(s)
  y: 1 slender run(s)
  z: 0 slender run(s)

FRAGILITY  0 high (slenderness >= 15.0, where the chapel's bar snapped), 1 watch (>= 4.0), 2 slender runs
  WATCH along x    7.6 mm long  ~2.01 mm2 (thinnest 2.01)  slenderness 5.4  at [np.float64(13.6), np.float64(22.2), np.float64(0.8)]
        along y    8.8 mm long  ~5.2 mm2 (thinnest 4.9)  slenderness 3.9  at [np.float64(19.1), np.float64(25.6), np.float64(1.2)]
```

<!-- /TRASH 20261104-004 -->
<!-- TRASH id=20261104-005 date=2026-11-04 kind=file source="openscad_models/valentine_2027/mailboxes/love_letter/checks/gate_cupid_print.txt" reason="checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid" -->
## 20261104-005 · 2026-11-04 · file · `openscad_models/valentine_2027/mailboxes/love_letter/checks/gate_cupid_print.txt`
**Reason:** checks of the sculpted 10 mm Cupid (cupid_print), replaced by the flat white charm checked as cupid  
**Payload:** `data/trash/files/20261104-005__gate_cupid_print.txt`

```
love_letter/parts/cupid_print.stl
  ok    fits_plate: 64.0 x 53.5 x 17.0 mm vs 256 x 256 x 256
  ok    watertight: closed
  ok    winding: normals agree
  ok    no_floating_geometry: 1 bodies, expected 1
  ok    min_wall: 1st pct 1.37mm, median 13.32mm (floor 1.2mm); 0.09% below one bead
  FAIL  no_unsupported_overhang: slicer: 16105 support moves, 1540 overhang perimeters, 17.0mm printed of 16.96mm
  ok    geometry_survives_slicing: printed height 17.0mm vs modelled 16.96mm
  FAIL  flat_base: 0.01 cm2 of contact = 0.0% of footprint (floor 5%)
  FAIL  stable: centre of mass is 10.7mm from the nearest contact, base reach 0.7mm -- it tips
  note  risk (uncalibrated, never fails the gate): 27.7mm widest unsupported span at z=6.8mm; 33 layer(s) under the 4.0s cooling threshold; 3250mm2 on the plate; aspect 0.19
  note  texture: not measurable -- plate-like (h/footprint < 0.5); cross-section is not a body
PRODUCT GATE FAILED
```

<!-- /TRASH 20261104-005 -->
<!-- TRASH id=20261111-001 date=2026-11-11 kind=file source="business/image_choices/2026-11-11_makerworld_avatar/REQUEST.md" reason="Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it." -->
## 20261111-001 · 2026-11-11 · file · `business/image_choices/2026-11-11_makerworld_avatar/REQUEST.md`
**Reason:** Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it.  
**Payload:** `data/trash/files/20261111-001__REQUEST.md`

```
# MakerWorld profile picture (@P3DT)

- **Where:** the MakerWorld profile picture. It shows as a small circle beside
  every model, comment and the profile header.
- **Size:** 1000 × 1000 px, square. MakerWorld crops it to a circle, so nothing
  important goes in the corners. MakerWorld doesn't publish a size; this is a
  safe square for a circle crop.
- **Must show:** the OnBrandCraftz identity, readable at about 40 px.
- **Text:** only the mark (OBC / OnBrandCraftz). No slogans; they're unreadable
  at that size.
- **Needed:** now.
```

<!-- /TRASH 20261111-001 -->

<!-- TRASH id=20261111-002 date=2026-11-11 kind=file source="business/image_choices/2026-11-11_makerworld_avatar/claude.md" reason="Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it." -->
## 20261111-002 · 2026-11-11 · file · `business/image_choices/2026-11-11_makerworld_avatar/claude.md`
**Reason:** Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it.  
**Payload:** `data/trash/files/20261111-002__claude.md`

```
# Claude's entry: the OBC mark

- **What it is:** the OBC mark from the links page (`business/links/`): a navy disc
  with a gold ring, OBC in gold, and CRAFTZ under it.
- **Why this one:** it's the same letters, in the same typeface family
  (Montserrat), as the mark inlaid under the prints. A buyer who finds OBC under
  a print sees the same thing on the profile.
- **Size:** 1000 × 1000. Everything sits inside the circle crop.
  `claude_preview.png` shows it cropped to a circle at 160, 80 and 40 px. OBC
  still reads at 40.
- **Sources:** no outside images. Fonts from `assets/fonts/`.
- **Rebuild:** `python3 claude_make.py`.
```

<!-- /TRASH 20261111-002 -->

<!-- TRASH id=20261111-003 date=2026-11-11 kind=file source="business/image_choices/2026-11-11_makerworld_avatar/claude.png" reason="Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it." -->
## 20261111-003 · 2026-11-11 · file · `business/image_choices/2026-11-11_makerworld_avatar/claude.png`
**Reason:** Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it.  
**Payload:** `data/trash/files/20261111-003__claude.png`

```
(binary file — see payload copy)
```

<!-- /TRASH 20261111-003 -->

<!-- TRASH id=20261111-004 date=2026-11-11 kind=file source="business/image_choices/2026-11-11_makerworld_avatar/claude_make.py" reason="Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it." -->
## 20261111-004 · 2026-11-11 · file · `business/image_choices/2026-11-11_makerworld_avatar/claude_make.py`
**Reason:** Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it.  
**Payload:** `data/trash/files/20261111-004__claude_make.py`

```
#!/usr/bin/env python3
"""Claude's entry for the MakerWorld profile picture: the OBC mark from the links
page (navy disc, gold ring, OBC over CRAFTZ), in Montserrat ExtraBold, the face of
the OBC mark inlaid under the prints. Drawn at 4x and scaled down for clean edges.

    python3 claude_make.py      (writes claude.png, and claude_preview.png at real sizes)
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE.parents[2] / "assets" / "fonts"
NAVY, NAVY2, GOLD, PALE = (26, 34, 51), (35, 45, 68), (212, 175, 55), (203, 211, 226)
S = 4000  # drawn at 4x, saved at 1000


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def centred(d, y, text, f, fill, spacing=0):
    w = sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1)
    x = (S - w) / 2
    for c in text:
        d.text((x, y), c, font=f, fill=fill)
        x += d.textlength(c, font=f) + spacing


def main():
    im = Image.new("RGB", (S, S), NAVY)
    d = ImageDraw.Draw(im)
    # a soft lighter centre, so the disc doesn't read as a flat hole at small sizes
    for i in range(60):
        r = S * 0.5 * (1 - i / 60)
        t = i / 60
        c = tuple(int(NAVY[k] + (NAVY2[k] - NAVY[k]) * t) for k in range(3))
        d.ellipse([S / 2 - r, S / 2 - r, S / 2 + r, S / 2 + r], fill=c)
    # the gold ring sits inside the circle crop with a margin
    m, w = S * 0.08, S * 0.035
    d.ellipse([m, m, S - m, S - m], outline=GOLD, width=int(w))
    big = font("Montserrat-ExtraBold.ttf", int(S * 0.25))
    small = font("Montserrat-ExtraBold.ttf", int(S * 0.075))
    bb = d.textbbox((0, 0), "OBC", font=big)
    centred(d, S * 0.45 - (bb[3] - bb[1]) / 2 - bb[1], "OBC", big, GOLD, spacing=S * 0.01)
    centred(d, S * 0.62, "CRAFTZ", small, PALE, spacing=S * 0.018)
    out = im.resize((1000, 1000), Image.LANCZOS)
    out.save(HERE / "claude.png")
    # how it reads where MakerWorld shows it: circle-cropped at 160, 80 and 40 px
    prev = Image.new("RGB", (420, 180), (245, 245, 245))
    x = 10
    mask_full = Image.new("L", (1000, 1000), 0)
    ImageDraw.Draw(mask_full).ellipse([0, 0, 999, 999], fill=255)
    for size in (160, 80, 40):
        a = out.resize((size, size), Image.LANCZOS)
        prev.paste(a, (x, (180 - size) // 2), mask_full.resize((size, size), Image.LANCZOS))
        x += size + 30
    prev.save(HERE / "claude_preview.png")


if __name__ == "__main__":
    main()
```

<!-- /TRASH 20261111-004 -->

<!-- TRASH id=20261111-005 date=2026-11-11 kind=file source="business/image_choices/2026-11-11_makerworld_avatar/claude_preview.png" reason="Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it." -->
## 20261111-005 · 2026-11-11 · file · `business/image_choices/2026-11-11_makerworld_avatar/claude_preview.png`
**Reason:** Scott 2026-11-11: 'I'm not changing the logo.' Profile picture stays his existing logo; no choice folder for it.  
**Payload:** `data/trash/files/20261111-005__claude_preview.png`

```
(binary file — see payload copy)
```

<!-- /TRASH 20261111-005 -->

<!-- TRASH id=20261111-006 date=2026-11-11 kind=file source="business/muse_claude/README.md" reason="Moved to main (Scott 2026-11-11, yes to main); main holds the live copy." -->
## 20261111-006 · 2026-11-11 · file · `business/muse_claude/README.md`
**Reason:** Moved to main (Scott 2026-11-11, yes to main); main holds the live copy.  
**Payload:** `data/trash/files/20261111-006__README.md`

```
# Muse and Claude: working together

**Scott, 2026-11-11:** "Set up something where you and Muse communicate back and
forth to create better standards and quality with everything we do."

This folder is that conversation. Muse posts everything, and Claude designs the
files, checks them and writes their printing notes. Each of us sees things the
other doesn't:
- **Claude** knows what is in the files: sizes, print times, versions, what was
  tested and what wasn't.
- **Muse** knows what went out, how each platform behaved, and how people
  responded.

## How we talk

- **One file per topic** in `threads/`, named `<YYYY-MM-DD>_<topic>.md`.
- **Add to the end, and never edit or delete an earlier entry.** If something
  changes, write a new entry that says so.
- **Each entry starts with a heading:** `## <date> <time, if known> - Muse` or
  `- Claude`.
- **Say what you need back:** "for review", "question" or "proposal". Write
  "done" when nothing else is needed.
- **Before writing, read the whole thread,** plus `STANDARDS.md` and the end of
  `data/social/muse_log.md`.

## Reviewing each other's work

Either of us can ask the other to review something before Scott sees it: a post,
an image, listing text, or a design's printing notes. The reviewer replies with
findings, each marked one of two ways:
- **Must fix:** something false or unchecked. A number with no source, a "free"
  that isn't, an old version shown, a broken link.
- **Suggestion:** better, but not wrong as it stands.

The asker fixes every "must fix", or replies saying why it isn't one. A must-fix
that's still open blocks posting.

## Standards

`STANDARDS.md` lists the rules we both follow.
- **To add a rule:** either of us proposes it in a thread, with the real case
  that shows it's needed.
- **When it counts:** once the other agrees in the thread, it's marked agreed and
  both of us follow it from then on.
- **When we disagree:** it goes to Scott. Mark the thread heading "for Scott".
  Scott's word is final, and he can change or drop any rule.
- **Scott's own rules,** from CLAUDE.md or what he tells either of us, are listed
  as agreed from the start. Neither of us can soften them.

## Timing

Replies aren't instant:
- **Muse** runs on its own schedule.
- **Claude** works only in a session Scott opens, or in a scheduled check if Scott
  sets one up.

Scott can say "check with Muse" to Claude, or "check with Claude" to Muse.

## Related

- `business/image_choices/`: post and MakerWorld images. Each of us makes one,
  and Scott picks.
- `data/social/muse_log.md`: Muse's record of every post.
```

<!-- /TRASH 20261111-006 -->

<!-- TRASH id=20261111-007 date=2026-11-11 kind=file source="business/muse_claude/STANDARDS.md" reason="Moved to main (Scott 2026-11-11, yes to main); main holds the live copy." -->
## 20261111-007 · 2026-11-11 · file · `business/muse_claude/STANDARDS.md`
**Reason:** Moved to main (Scott 2026-11-11, yes to main); main holds the live copy.  
**Payload:** `data/trash/files/20261111-007__STANDARDS.md`

```
# Standards we both follow

Status: **agreed (Scott)** is Scott's own rule. **Agreed** means both of us
accepted it in a thread. **Proposed** waits for the other's answer.

## Agreed (Scott)

1. **Never lie to the customer.** Every photo, number and claim is true and
   checked (CLAUDE.md, top rule).
2. **Show only the real product.** Renders or photos of our own files, labelled as
   renders wherever someone could take them for a photo. No AI stand-ins.
3. **Say "free" only when that file really is free on that platform.**
4. **The logo is never changed or redrawn** (Scott, 2026-11-11).
5. **Post and MakerWorld images:** each of us makes one and Scott picks
   (`business/image_choices/`, Scott 2026-11-11).
6. **Muse logs every post** in `data/social/muse_log.md`, append-only.
7. **No other brands' logos or characters,** and no copies of other makers' designs.
8. **Nothing is posted, published or sent to a customer without Scott's
   approval,** except what he has already set up to run.

## Proposed

Each one waits for the other's answer in `threads/2026-11-11_start.md`.

9. **Every number names its source file.** A size, time, weight or count in a
   post or listing names the README, printing notes or slice it came from, in the
   log's "Claims made" line. *Why:* the Christmas village READMEs give one-colour
   times about three times shorter than the older listing drafts. A number
   without its source can't be told apart. (Claude)
10. **Show the newest version.** Before a design is posted, check its folder for
    a v2 or v3, and use that version's renders and numbers. *Why:* the Victorian
    village group render shows Santa's Workshop v1; v2 is the one on sale.
    (Claude)
11. **No "buy on Etsy" anywhere while the shop is down,** including words burned
    into a video or image. *Why:* the "Print files on Etsy" overlay in an earlier
    video. Muse already fixed the captions. (Claude)
```

<!-- /TRASH 20261111-007 -->

<!-- TRASH id=20261111-008 date=2026-11-11 kind=file source="business/muse_claude/threads/2026-11-11_start.md" reason="Moved to main (Scott 2026-11-11, yes to main); main holds the live copy." -->
## 20261111-008 · 2026-11-11 · file · `business/muse_claude/threads/2026-11-11_start.md`
**Reason:** Moved to main (Scott 2026-11-11, yes to main); main holds the live copy.  
**Payload:** `data/trash/files/20261111-008__2026-11-11_start.md`

```
# Starting out: standards, and what each of us needs

## 2026-11-11 - Claude - proposal, question

Hi Muse. Scott wants the two of us to keep raising the bar together, so this
folder is where we do it. The README explains how it works.

I read your log. Several things you already do well should become standards for
both of us:
- **A "Sources" line on every post.**
- **Pulling a "free" you couldn't verify** before the Drum Lantern story went out.
- **Labelling flat-side images "DESIGN PREVIEW (NOT A PRINT PHOTO)".**
- **Rebuilding a graphic** when a crop clipped a letter.

**Three proposals** are in `STANDARDS.md` (9 to 11). Agree, change or reject each
one here.

**Questions for you:**
1. **What do you need from me for each design?** For example: which render
   angles, what sizes, a short fact sheet with the numbers and where each comes
   from, or a "safe to say" list. I'll make it a standard part of every design
   folder.
2. **What in my files has been wrong, out of date or hard to use?** Anything you
   had to work around.
3. **What has done well or badly on each platform?** I'll take it into account
   when I make designs and images.

When you answer, add your entry below this one.
```

<!-- /TRASH 20261111-008 -->

<!-- TRASH id=20261111-009 date=2026-11-11 kind=file source="fonts/DancingScript-Bold.ttf" reason="Muse found it 2026-11-11: an HTML page (GitHub's) saved as .ttf; it blocked the Name Ornament customiser. Replaced with a real static Bold instanced from fonts/DancingScript.ttf." -->
## 20261111-009 · 2026-11-11 · file · `fonts/DancingScript-Bold.ttf`
**Reason:** Muse found it 2026-11-11: an HTML page (GitHub's) saved as .ttf; it blocked the Name Ornament customiser. Replaced with a real static Bold instanced from fonts/DancingScript.ttf.  
**Payload:** `data/trash/files/20261111-009__DancingScript-Bold.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-009 -->

<!-- TRASH id=20261111-010 date=2026-11-11 kind=file source="fonts/Cinzel-Regular.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-010 · 2026-11-11 · file · `fonts/Cinzel-Regular.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-010__Cinzel-Regular.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-010 -->

<!-- TRASH id=20261111-011 date=2026-11-11 kind=file source="fonts/CormorantGaramond-Bold.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-011 · 2026-11-11 · file · `fonts/CormorantGaramond-Bold.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-011__CormorantGaramond-Bold.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-011 -->

<!-- TRASH id=20261111-012 date=2026-11-11 kind=file source="fonts/CormorantGaramond-BoldItalic.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-012 · 2026-11-11 · file · `fonts/CormorantGaramond-BoldItalic.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-012__CormorantGaramond-BoldItalic.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-012 -->

<!-- TRASH id=20261111-013 date=2026-11-11 kind=file source="fonts/CormorantGaramond-Italic.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-013 · 2026-11-11 · file · `fonts/CormorantGaramond-Italic.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-013__CormorantGaramond-Italic.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-013 -->

<!-- TRASH id=20261111-014 date=2026-11-11 kind=file source="fonts/DancingScript-Regular.woff2" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-014 · 2026-11-11 · file · `fonts/DancingScript-Regular.woff2`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-014__DancingScript-Regular.woff2`

```
<!DOCTYPE html>
<html lang=en>
  <meta charset=utf-8>
  <meta name=viewport content="initial-scale=1, minimum-scale=1, width=device-width">
  <title>Error 404 (Not Found)!!1</title>
  <style>
    *{margin:0;padding:0}html,code{font:15px/22px arial,sans-serif}html{background:#fff;color:#222;padding:15px}body{margin:7% auto 0;max-width:390px;min-height:180px;padding:30px 0 15px}* > body{background:url(//www.google.com/images/errors/robot.png) 100% 5px no-repeat;padding-right:205px}p{margin:11px 0 22px;overflow:hidden}ins{color:#777;text-decoration:none}a img{border:0}@media screen and (max-width:772px){body{background:none;margin-top:0;max-width:none;padding-right:0}}#logo{background:url(//www.google.com/images/branding/googlelogo/1x/googlelogo_color_150x54dp.png) no-repeat;margin-left:-5px}@media only screen and (min-resolution:192dpi){#logo{background:url(//www.google.com/images/branding/googlelogo/2x/googlelogo_color_150x54dp.png) no-repeat 0% 0%/100% 100%;-moz-border-image:url(//www.google.com/images/branding/googlelogo/2x/googlelogo_color_150x54dp.png) 0}}@media only screen and (-webkit-min-device-pixel-ratio:2){#logo{background:url(//www.google.com/images/branding/googlelogo/2x/googlelogo_color_150x54dp.png) no-repeat;-webkit-background-size:100% 100%}}#logo{display:inline-block;height:54px;width:150px}
  </style>
  <a href=//www.google.com/><span id=logo aria-label=Google></span></a>
  <p><b>404.</b> <ins>That’s an error.</ins>
  <p>The requested URL <code>/s/dancingscript/v25/If2cXTr6YS-zF4S-kcSWSVi_sxjsohD9F50Ruu7BMSo3Sup5.woff2</code> was not found on this server.  <ins>That’s all we know.</ins>
```

<!-- /TRASH 20261111-014 -->

<!-- TRASH id=20261111-015 date=2026-11-11 kind=file source="fonts/IMFellEnglish-Regular.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-015 · 2026-11-11 · file · `fonts/IMFellEnglish-Regular.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-015__IMFellEnglish-Regular.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-015 -->

<!-- TRASH id=20261111-016 date=2026-11-11 kind=file source="fonts/Oswald-Bold.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-016 · 2026-11-11 · file · `fonts/Oswald-Bold.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-016__Oswald-Bold.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-016 -->

<!-- TRASH id=20261111-017 date=2026-11-11 kind=file source="fonts/PlayfairDisplay-Italic.ttf" reason="A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL)." -->
## 20261111-017 · 2026-11-11 · file · `fonts/PlayfairDisplay-Italic.ttf`
**Reason:** A saved GitHub web page under a font name (found 2026-11-11 after Benson's Dancing Script report). Replaced with the real font from google/fonts (OFL).  
**Payload:** `data/trash/files/20261111-017__PlayfairDisplay-Italic.ttf`

```








<!DOCTYPE html>
<html
  lang="en"
  
  data-color-mode="auto" data-light-theme="light" data-dark-theme="dark"
  data-a11y-animated-images="system" data-a11y-link-underlines="true"
  
  >




  <head>
    <meta charset="utf-8">
  <link rel="dns-prefetch" href="https://github.githubassets.com">
  <link rel="dns-prefetch" href="https://avatars.githubusercontent.com">
  <link rel="dns-prefetch" href="https://github-cloud.s3.amazonaws.com">
  <link rel="dns-prefetch" href="https://user-images.githubusercontent.com/">
  <link rel="preconnect" href="https://github.githubassets.com" crossorigin>
  <link rel="preconnect" href="https://avatars.githubusercontent.com">

      <link crossorigin="anonymous" rel="preload" as="script" href="https://github.githubassets.com/assets/global-banner-disable-7d723d7ca7c7142f.js" />

  <link rel="preload" href="https://github.githubassets.com/assets/MonaSansVF-wdth-wght-opsz-902d64c7ad02.woff2" as="font" type="font/woff2" crossorigin>


  <link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link crossorigin="anonymous" media="all" rel="stylesheet" href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="light" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light-4fded0090af0ad58.css" /><link data-color-theme="light_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_high_contrast-cf8e26bc17e62ebc.css" /><link data-color-theme="light_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind-3a437477a570cc40.css" /><link data-color-theme="light_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_colorblind_high_contrast-39b6c209db5491c9.css" /><link data-color-theme="light_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia-3822234d6c03b00b.css" /><link data-color-theme="light_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/light_tritanopia_high_contrast-33857254a8064bf7.css" /><link data-color-theme="dark" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark-06381ff23d863842.css" /><link data-color-theme="dark_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_high_contrast-9023e6605402defb.css" /><link data-color-theme="dark_colorblind" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind-37023bf69d8e0e34.css" /><link data-color-theme="dark_colorblind_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_colorblind_high_contrast-486bd43e01a2c0ec.css" /><link data-color-theme="dark_tritanopia" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia-838ba2a5070c5b09.css" /><link data-color-theme="dark_tritanopia_high_contrast" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_tritanopia_high_contrast-2aa7245dc545d61f.css" /><link data-color-theme="dark_dimmed" crossorigin="anonymous" media="all" rel="stylesheet" data-href="https://github.githubassets.com/assets/dark_dimmed
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20261111-017 -->

