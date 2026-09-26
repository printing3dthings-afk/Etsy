"""
Tests for tools/glyph_probe.py (2026-09-09).

This tool gates a 26-variant monogram product line, and its metric was wrong
THREE times before it was right. Each wrong version looked plausible and each
is pinned here, because the failure mode is that a bad metric passes silently:

  1. min of the distance-transform ridge -- picks up a one-pixel local maximum
     where strokes meet at an acute angle. Scored Poppins SemiBold's G at
     0.04mm and would have rejected a perfectly printable font.
  2. fraction of area within half a bead of an edge -- that is just the
     boundary band, structurally ~bead/stroke for ANY shape, so every font
     landed near 12% no matter how thick.
  3. frac_lost alone -- passes "OnBrandCraftz" at the size that ACTUALLY
     printed blank, because only 0.46% of its area vanishes. Area is not the
     whole story when the lost area is a hairline inside a letter.

The shipped rule needs BOTH: nothing meaningful may vanish under a one-bead
morphological opening, AND the typical stroke must clear 2 extrusions.

Ground truth, from a real printed part:
  "OnBrandCraftz" @ 5.5 in Caveat Bold  -> printed BLANK on three of four models
  "OBC"           @ 15.3 in Caveat Bold -> printed legibly, confirmed on the bowl
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _probe(text, font, size):
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "glyph_probe.py"), text,
         "--font", font, "--size", str(size)],
        capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout


def test_the_wordmark_that_printed_blank_is_rejected():
    """The whole reason this tool exists. Non-zero exit = rejected."""
    code, out = _probe("OnBrandCraftz", "Caveat:style=Bold", 5.5)
    check(code != 0, f"the mark that actually printed blank PASSED:\n{out}")


def test_the_fix_that_printed_is_accepted():
    """A check that rejects everything is as useless as one that accepts all."""
    code, out = _probe("OBC", "Caveat:style=Bold", 15.3)
    check(code == 0, f"the OBC mark that verifiably printed was rejected:\n{out}")


def test_a_hairline_face_is_rejected():
    """Cinzel Decorative's J is 0.24mm -- 0.57 of one bead. It cannot print."""
    code, out = _probe("J", "Cinzel Decorative:style=Regular", 6)
    check(code != 0, f"a 0.24mm hairline glyph passed:\n{out}")


def test_sharp_corners_do_not_cause_a_false_reject():
    """Metric 1's exact failure: Poppins SemiBold is thick and must PASS.

    Its G/K/Q/R/V scored 0.04mm under the ridge-minimum metric purely because
    of acute stroke junctions. If this fails, the min has crept back in.
    """
    code, out = _probe("G", "Poppins:style=SemiBold", 18)
    check(code == 0, f"a thick geometric font was falsely rejected:\n{out}")


def test_the_shipped_keychain_font_passes_every_letter():
    """Fredoka is the font the monogram keychain ships in -- all 26 must clear."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "glyph_probe.py"), "--alphabet",
         "--font", "Fredoka:style=Regular", "--size", "18"],
        capture_output=True, text=True, timeout=900)
    check(r.returncode == 0, f"a letter of the alphabet fails in Fredoka:\n{r.stdout}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GLYPH PROBE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GLYPH PROBE TESTS OK -- rejects the wordmark that printed blank and a "
          "0.24mm hairline, accepts the OBC fix and thick fonts with sharp corners, "
          "and clears all 26 letters in the keychain's shipping font.")


if __name__ == "__main__":
    run()
