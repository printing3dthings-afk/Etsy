#!/usr/bin/env python3
"""The camera sign's check set (tools/model_checks.py) on the three neon font options
(2026-11-25), one at a time, each in its own folder:

    python3 check_fonts.py nunito|righteous|courgette [step ...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from model_checks import run_checks  # noqa: E402

BASE, LETTERS = "#1C1C1F", "#F28C28"
FACE = {"nunito": "a rounded heavy sans", "righteous": "a retro display face",
        "courgette": "a script with separate letters"}
f = sys.argv[1]
name = f"camera_sign_neon_{f}"
run_checks(HERE / f, name, dict(
    label=f"Camera Sign (neon, {f})",
    note=f"A sign for the back wall inside the P1S, for the chamber camera: FOLLOW and "
         f"@onbrandcraftz2026 in {FACE[f]} on their own raised outline. A font option, not printed.",
    objects=[[("base", BASE), ("letters", LETTERS)]], unions=[f"{name}_union.stl"],
    source=f"camera_sign/font_options/{f}/{name}.3mf",
    gate_args=["--wall-skip-part", str(HERE / f / f"{name}_letters.stl")]),
    sys.argv[2:] or ["parts", "gate", "3mf", "fidelity", "fragility"])
