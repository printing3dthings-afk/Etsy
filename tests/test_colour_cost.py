"""tools/colour_cost.py (2026-10-03).

The chapel showed a colour costs per LAYER it occupies, not per gram: 7 g of
trim on 517 of 815 layers cost 14.9 h. This pins that shape on a small model:
a thin second-colour pin running the full height must cost far more than its
grams suggest, and dropping it must measurably save time.
"""
import sys
import tempfile
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import bambu_slicer  # noqa: E402
import colour_cost  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_a_full_height_sliver_costs_more_than_its_grams():
    if not bambu_slicer.available():
        print("  (skipped: Bambu Studio not installed)")
        return
    td = Path(tempfile.mkdtemp(prefix="colour_cost_test_"))
    block = trimesh.creation.box(extents=[20, 20, 15]); block.apply_translation([0, 0, 7.5])
    pin = trimesh.creation.box(extents=[2, 2, 15]); pin.apply_translation([11, 0, 7.5])
    block.export(str(td / "block.stl")); pin.export(str(td / "pin.stl"))
    r = colour_cost.report([(str(td / "block.stl"), "#77716B"), (str(td / "pin.stl"), "#EFE6D2")],
                           what_if=True, log=lambda *a: None)
    pin_row = r["per_colour"][1]
    check(pin_row["layers"] >= 70, f"the pin spans the whole height, got {pin_row['layers']} layers")
    check(pin_row["used_g"] > 5 * pin_row["model_g"],
          f"purge must dwarf the pin's own plastic: used {pin_row['used_g']} g for {pin_row['model_g']} g")
    check(pin_row.get("drop_saves_h", 0) > 0.2,
          f"dropping the pin's colour must save real time, saved {pin_row.get('drop_saves_h')} h")
    check(r["as_designed"]["colour_changes"] >= pin_row["layers"],
          "at least one colour change per layer the pin occupies")
    check(abs(r["one_colour"]["hours"] - (r["as_designed"]["hours"] - pin_row["drop_saves_h"])) < 0.05,
          "with two colours, dropping one is the one-colour slice")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLOUR COST TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLOUR COST TESTS OK — a thin full-height colour is priced by the layers it spans, "
          "and dropping it is a measured saving.")


if __name__ == "__main__":
    run()
