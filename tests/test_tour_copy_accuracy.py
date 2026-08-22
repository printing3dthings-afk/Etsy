"""
Regression test for Frank upgrade Wave 3 (usability), item 1, 2026-07-17.

The onboarding tour's Create-screen step (both TOUR_STEPS and
MOBILE_TOUR_STEPS in frank_hud_mockup.py) used to say "then publish straight
to Etsy" -- false. Every produce pipeline (build_planner/build_sticker_pack/
build_product) is build/QC-only; "Publishing any listing to Etsy" is
explicitly listed under CLAUDE.md's Autonomy Boundaries as something that
"Requires Scott's Review Before Action," never something Create does
automatically. The Create screen's own in-page copy already said this
correctly ("Nothing is published ... publishing is your call") -- only the
tour tooltip was wrong. This test guards against the false claim silently
creeping back in.

Run: python tests/test_tour_copy_accuracy.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def run() -> None:
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text()

    false_claims = [
        "publish straight to etsy",
        "publishes straight to etsy",
        "then publishes it to etsy",
        "goes straight to etsy",
    ]
    lower = src.lower()
    for claim in false_claims:
        check(claim not in lower, f"found a false auto-publish claim in frank_hud_mockup.py: {claim!r}")

    # Both tour arrays' Create step must exist and must NOT claim an automatic publish.
    check("const TOUR_STEPS = [" in src, "TOUR_STEPS array must exist")
    check("const MOBILE_TOUR_STEPS = [" in src, "MOBILE_TOUR_STEPS array must exist")

    tour_start = src.index("const TOUR_STEPS = [")
    tour_end = src.index("];", tour_start)
    tour_block = src[tour_start:tour_end]
    check("title: 'Create'" in tour_block, "TOUR_STEPS must still have a Create step")
    create_idx = tour_block.index("title: 'Create'")
    create_body = tour_block[create_idx:create_idx + 400]
    check("straight to etsy" not in create_body.lower(),
          f"TOUR_STEPS' Create step must not claim automatic publishing, got: {create_body[:200]!r}")
    check("approval" in create_body.lower() or "before it ever reaches etsy" in create_body.lower(),
          f"TOUR_STEPS' Create step should accurately mention the approval gate, got: {create_body[:200]!r}")

    mobile_start = src.index("const MOBILE_TOUR_STEPS = [")
    mobile_end = src.index("];", mobile_start)
    mobile_block = src[mobile_start:mobile_end]
    check("title: 'Create'" in mobile_block, "MOBILE_TOUR_STEPS must still have a Create step")
    m_create_idx = mobile_block.index("title: 'Create'")
    m_create_body = mobile_block[m_create_idx:m_create_idx + 400]
    check("straight to etsy" not in m_create_body.lower(),
          f"MOBILE_TOUR_STEPS' Create step must not claim automatic publishing, got: {m_create_body[:200]!r}")

    if _failures:
        print("TOUR COPY ACCURACY TEST FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TOUR COPY ACCURACY TEST OK — no false auto-publish claims in either tour, "
          "and the Create step in both accurately reflects the real build -> QC -> "
          "approve flow.")


if __name__ == "__main__":
    run()
