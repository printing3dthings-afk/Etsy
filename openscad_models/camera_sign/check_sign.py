#!/usr/bin/env python3
"""The full check set for the camera signs (tools/model_checks.py), one style at a time:

    python3 check_sign.py neon|plaque [step ...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
from model_checks import run_checks  # noqa: E402

BASE, LETTERS = "#1C1C1F", "#F28C28"
NOTES = {
    "neon": "A sign for the back wall inside the P1S, for the chamber camera: FOLLOW and "
            "@onbrandcraftz2026 in a bold script on their own raised outline.",
    "plaque": "A sign for the back wall inside the P1S, for the chamber camera: a rounded plate "
              "with a raised border, FOLLOW and @onbrandcraftz2026 in bold capitals.",
}
style = sys.argv[1]
name = f"camera_sign_{style}"
run_checks(HERE, name, dict(
    label=f"Camera Sign ({style})", note=NOTES[style], objects=[[("base", BASE), ("letters", LETTERS)]],
    unions=[f"{name}_union.stl"], source=f"camera_sign/{name}.3mf",
    gate_args=["--wall-skip-part", str(HERE / f"{name}_letters.stl")]), sys.argv[2:] or None)
