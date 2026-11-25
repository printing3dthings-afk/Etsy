#!/usr/bin/env python3
"""The camera sign's check set (tools/model_checks.py) on the Instagram QR tile (2026-11-25).

    python3 check_qr.py [step ...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from model_checks import run_checks  # noqa: E402

run_checks(HERE, "camera_sign_qr", dict(
    label="Camera Sign QR tile",
    note="A 78 mm two-colour QR tile to instagram.com/onbrandcraftz2026, printed beside the camera "
         "signs: the dark modules are holes in an orange top layer. Not printed yet.",
    objects=[[("base", "#1C1C1F"), ("letters", "#F28C28")]], unions=["camera_sign_qr_union.stl"],
    source="camera_sign/qr_tile/camera_sign_qr.3mf",
    gate_args=["--wall-skip-part", str(HERE / "camera_sign_qr_letters.stl")]),
    sys.argv[1:] or ["parts", "gate", "3mf", "fidelity", "fragility"])
