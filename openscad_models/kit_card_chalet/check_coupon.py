#!/usr/bin/env python3
"""The check set (tools/model_checks.py) on the chalet's snap test print (2026-11-25).

    python3 check_coupon.py [step ...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from model_checks import run_checks  # noqa: E402

C = "#EDE8DC"
run_checks(HERE / "coupon", "coupon", dict(
    label="Kit-card chalet: snap test",
    note="The A-frame chalet's panel snap: a base strip with three slots and three panel stubs whose "
         "arrow tabs reach 0.35, 0.45 and 0.55. A test print, not the chalet.",
    objects=[[("base", C)], [("stub_0", C)], [("stub_1", C)], [("stub_2", C)]],
    unions=["coupon_base.stl", "coupon_stub_0.stl", "coupon_stub_1.stl", "coupon_stub_2.stl"],
    tags=["_base", "_stub_0", "_stub_1", "_stub_2"],
    source="kit_card_chalet/coupon/coupon.3mf"),
    sys.argv[1:] or ["parts", "gate", "3mf", "fidelity", "fragility"])
