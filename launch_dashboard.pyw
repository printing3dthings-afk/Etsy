#!/usr/bin/env python3
"""
launch_dashboard.pyw

Silent Windows launcher — runs with pythonw.exe so no console window appears.
Refreshes dashboard data from Etsy, then opens it in your default browser.
Double-click this file, or use the desktop shortcut created by setup_desktop_shortcut.bat
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE = Path(__file__).parent.resolve()
os.chdir(BASE)

# Regenerate dashboard with fresh Etsy data
subprocess.run(
    [sys.executable, str(BASE / "tools" / "generate_dashboard.py")],
    cwd=BASE,
    creationflags=0x08000000,  # CREATE_NO_WINDOW on Windows
)

# Open in default browser
html_path = BASE / "data" / "dashboard.html"
if html_path.exists():
    webbrowser.open(html_path.as_uri())
