#!/usr/bin/env python3
"""
launch_dashboard.py  —  double-click this to open the OnBrandCraftz dashboard.

Works on Windows, Mac, and Linux.
Pulls fresh Etsy data, rebuilds the dashboard, then opens it in your browser.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE = Path(__file__).parent.resolve()
os.chdir(BASE)

print("OnBrandCraftz Dashboard")
print("=" * 40)
print("Refreshing data from Etsy...")

result = subprocess.run(
    [sys.executable, str(BASE / "tools" / "generate_dashboard.py")],
    cwd=BASE,
)

if result.returncode != 0:
    print("\nWarning: data refresh had errors — opening last saved dashboard.")

html_path = BASE / "data" / "dashboard.html"
if not html_path.exists():
    print(f"\nERROR: Dashboard not found at {html_path}")
    input("Press Enter to close...")
    sys.exit(1)

url = html_path.as_uri()
print(f"\nOpening: {url}")
webbrowser.open(url)

# Keep window open briefly on Windows so user can see any error messages
if sys.platform == "win32":
    import time
    time.sleep(2)
