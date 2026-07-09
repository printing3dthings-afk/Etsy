#!/usr/bin/env python3
"""
Builds the standalone Frank backend executable for the desktop app, using
tools/desktop/backend.spec. Must run ON the target OS -- PyInstaller does not
cross-compile a Windows .exe from Linux/Mac or vice versa. In practice this means:
  - Local runs (this script) only ever produce a binary for the OS you ran it on.
  - The real Windows .exe / Mac .app come from .github/workflows/build-desktop.yml's
    matrix build on windows-latest / macos-latest GitHub-hosted runners.

Run:  python tools/desktop/build_backend.py
Output: dist/desktop-backend/frank-backend/ (a directory -- onedir mode, see the
        spec's docstring for why onedir instead of onefile).
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC = REPO_ROOT / "tools" / "desktop" / "backend.spec"
DIST = REPO_ROOT / "dist" / "desktop-backend"
BUILD = REPO_ROOT / "build" / "desktop-backend"


def main() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC),
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        "--noconfirm",
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        return result.returncode
    out_dir = DIST / "frank-backend"
    print(f"\nBuilt: {out_dir}")
    print(f"Run it directly to test: {out_dir / 'frank-backend'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
