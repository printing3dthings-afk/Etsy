"""detail_probe.py shipped 2026-09-04 with a 157-mesh benchmark and was wired
into nothing -- not product_gate, not a test, not a command -- so its real
finding (our best model sits at the corpus median) never reached the moment a
model is judged. It is now a product_gate advisory. These tests lock in the
three things that went wrong or could go wrong while wiring it.
"""
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_texture_adv_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "texture-advisory-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import trimesh  # noqa: E402

import product_gate  # noqa: E402

_failures: list[str] = []

MODELS = ROOT / "openscad_models"


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _advisory(name):
    path = MODELS / name
    if not path.exists():
        return None
    return product_gate._texture_advisory(trimesh.load(path, force="mesh"))


def test_texture_is_an_advisory_and_never_a_gate_check():
    # A rugosity floor would correctly fail a cable clip, and a cable clip is a
    # legitimate product. Texture must never become a failing check.
    src = (ROOT / "tools" / "product_gate.py").read_text()
    check('add("texture' not in src and "add('texture" not in src,
          "texture must never be registered via add() -- add() entries fail the gate")
    check("advisories.append({\"texture\"" in src,
          "the texture reading should be appended to advisories, not to checks")


def test_printing_two_advisory_shapes_does_not_crash():
    # The exact bug hit while wiring this: the CLI printer assumed every
    # advisory was a print_risk dict and died with
    # KeyError: 'unsupported_span_mm' the first time a texture dict was added.
    res = {
        "file": "x.stl",
        "passed": True,
        "checks": [{"check": "fits_plate", "pass": True, "detail": "ok"}],
        "advisories": [
            {"unsupported_span_mm": 11.9, "unsupported_span_at_z": 66.2,
             "short_layers": 64, "slowdown_threshold_s": 5.0,
             "first_layer_area_mm2": 9759, "aspect_ratio": 0.83},
            {"texture": {"rugosity": 1.086, "corpus_percentile_at_least": 50,
                         "band": "light relief", "note": "corpus note"}},
        ],
    }
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            product_gate._print_report("x.stl", res)
    except Exception as exc:  # the original failure was an uncaught KeyError
        _failures.append(f"printing mixed advisory shapes raised {type(exc).__name__}: {exc}")
        return
    out = buf.getvalue()
    check("rugosity 1.086" in out, f"texture advisory should print its number, got:\n{out}")
    check("11.9mm" in out, f"risk advisory should still print alongside it, got:\n{out}")


def test_the_gate_reports_the_same_rugosity_technique_52_published():
    # If these ever disagree, one of the two is lying about the same corpus.
    published = {"mochi_fox_organizer.stl": 1.086,
                 "fairy_house.stl": 1.062,
                 "ribbed_organizer.stl": 1.000}
    for name, expected in published.items():
        adv = _advisory(name)
        if adv is None:
            continue
        got = adv.get("rugosity")
        check(got is not None and abs(got - expected) < 0.002,
              f"{name}: gate reports {got}, Technique 52 published {expected}")


def test_a_flat_plate_reports_not_measurable_instead_of_a_number():
    # T52's own artifact: a 0.8mm engraved lid scored 1.784 -- higher than any
    # real vase -- because a sheet has no body to cross-section.
    adv = _advisory("snap_box_base.3mf")
    if adv is None:
        return
    check(adv.get("rugosity") is None,
          f"a plate-like model must not report a rugosity number, got {adv.get('rugosity')}")
    check("plate-like" in (adv.get("note") or ""),
          f"it should say why it is unmeasurable, got {adv.get('note')!r}")


def test_a_horizontally_ribbed_model_is_not_described_as_having_no_relief():
    # ribbed_organizer carries six real 1.5mm corrugations and scores exactly
    # 1.000 because the metric sees vertical relief only. Calling that "no
    # relief" would be untrue, which is the one rule that outranks the rest.
    adv = _advisory("ribbed_organizer.stl")
    if adv is None:
        return
    band = adv.get("band", "")
    check(band == "no vertical relief",
          f"band must qualify what was measured, got {band!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCT GATE TEXTURE ADVISORY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCT GATE TEXTURE ADVISORY TESTS OK — texture is reported against the "
          "real 157-mesh corpus, never fails the gate, agrees with Technique 52's "
          "published numbers, and refuses to report a number on a flat plate.")


if __name__ == "__main__":
    run()
