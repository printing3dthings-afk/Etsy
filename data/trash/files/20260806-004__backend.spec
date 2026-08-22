# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Frank's backend (tools/api_server/main.py), bundled as a
standalone executable for the desktop app (desktop/ Electron shell spawns this as a
child process). No pre-installed Python required on the end-user machine.

Build (must run ON the target OS -- PyInstaller does not cross-compile):
  python -m PyInstaller tools/desktop/backend.spec --distpath dist/desktop-backend

Why onedir, not onefile: main.py resolves sys.path.insert(0, ROOT / "tools") at import
time and imports sibling modules (daily_brief, trash, etc.) as bare names -- that only
works if tools/ exists as real files on disk next to the executable, which onedir mode
gives for free (the datas entry below copies the whole tools/ tree into the bundle).
onefile mode self-extracts to a temp dir per launch, which would also work but adds
startup latency and an extra temp-cleanup failure mode for no benefit here.

main.py itself has a matching frozen-detection branch (search `getattr(sys, "frozen"`)
that computes ROOT as the directory containing the frozen executable instead of walking
up from __file__, since __file__ for a frozen entry script doesn't sit 3 directories
under the repo root the way it does when run from source.
"""
from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parent.parent  # tools/desktop -> tools -> repo root
MAIN_PY = REPO_ROOT / "tools" / "api_server" / "main.py"

a = Analysis(
    [str(MAIN_PY)],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / "tools"), str(REPO_ROOT / "tools" / "api_server")],
    binaries=[],
    datas=[
        # The whole tools/ tree (incl. tools/api_server/static/'s ~34MB vendor JS) as
        # real files on disk -- see the onedir rationale above. Harmless if this also
        # duplicates main.py's own source alongside the compiled entry script.
        (str(REPO_ROOT / "tools"), "tools"),
        # Read-mostly reference docs the CEO agent reads at runtime (business_standards.md,
        # ops_runbook.md, etc.) -- NOT the rest of data/ (staged_photos, digital_products,
        # backups, trash are large/gitignored/user-specific and don't belong in an installer).
        (str(REPO_ROOT / "data" / "knowledge_base"), "data/knowledge_base"),
        (str(REPO_ROOT / "data" / "dp_listing_map.json"), "data"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="frank-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # keep a console window for now -- makes startup errors visible
                   # during bring-up; Electron can hide it later once this is proven stable
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="frank-backend",
)
