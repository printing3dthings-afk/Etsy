#!/usr/bin/env python3
"""Trophy Rack v3: the check set (tools/model_checks.py). 2026-11-25.

    python3 check_v3.py [step ...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from model_checks import run_checks  # noqa: E402

run_checks(HERE, "trophy_rack_v3", dict(
    label="Trophy Rack v3", note="Scott's Trophy Rack medallion, v3: short rounded tips that don't snap, "
    "and a full-height keychain tab with a 3.2 mm ring.",
    objects=[[("black", "#1A1A1A"), ("yellow", "#E8C21A"), ("skin", "#E7A976"), ("white", "#F2EDE2")]],
    unions=["trophy_rack_v3_union.stl"], source="trophy_rack/v3/trophy_rack_v3.3mf",
    gate_args=["--wall-skip-part", str(HERE / "trophy_rack_v3_letters.stl")]),
    sys.argv[1:] or ["parts", "gate", "3mf", "fidelity", "fragility"])
