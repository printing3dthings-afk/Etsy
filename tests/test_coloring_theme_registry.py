"""
Tests for the coloring-pages theme registry (2026-07-24): Scott, on the
Create screen's dynamic new-theme path: "It will be a set of 20 individual
coloring pages. Never to repeat a creation." Covers:

  - _normalize_subject() -- the exact-match dedup key.
  - The registry sidecar itself: read/write round-trip, tolerant of a
    missing/corrupt file (same volume-or-local pattern as
    _PRODUCT_CATALOG_OVERRIDES_PATH -- see .claude/rules/api-conventions.md).
  - _record_used_coloring_subjects() appends one entry per subject.
  - _generate_coloring_subjects() -- the raw Anthropic-call wrapper (mocked,
    no real API key/network involved).
  - _resolve_coloring_subjects() -- the full flow: caps at NEW_THEME_SET_SIZE,
    code-verifies the LLM's own output against the full registry and drops/
    retries anything that slips through, and surfaces a clear error when it
    can't reach the target count after a retry.

Run: python tests/test_coloring_theme_registry.py
"""
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_coloringregistry_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "coloringregistry-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _tmp_registry_path() -> Path:
    return Path(tempfile.mkdtemp(prefix="frank_coloring_registry_")) / "coloring_theme_registry.json"


def test_normalize_subject_collapses_whitespace_and_case():
    check(server._normalize_subject("  A Sleepy   Fox ") == "a sleepy fox",
          f"got {server._normalize_subject('  A Sleepy   Fox ')!r}")
    check(server._normalize_subject("a sleepy fox") == server._normalize_subject("A SLEEPY FOX"),
          "case must not affect the normalized key")


def test_registry_read_missing_file_returns_empty_list():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        check(server._coloring_theme_registry() == [], "a never-written registry must read as []")


def test_registry_read_corrupt_file_returns_empty_list():
    path = _tmp_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        check(server._coloring_theme_registry() == [], "a corrupt registry file must read as [], not raise")


def test_registry_write_read_round_trip():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._write_coloring_theme_registry([{"subject": "a fox", "normalized": "a fox"}])
        got = server._coloring_theme_registry()
    check(got == [{"subject": "a fox", "normalized": "a fox"}], f"got {got}")
    check(path.exists(), "the registry file must actually be written to disk")


def test_record_used_coloring_subjects_appends_one_entry_per_subject():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._record_used_coloring_subjects("COLOR_TEST", "woodland animals", ["a fox", "a deer"])
        registry = server._coloring_theme_registry()
    check(len(registry) == 2, f"expected 2 entries, got {len(registry)}")
    check({e["subject"] for e in registry} == {"a fox", "a deer"}, f"got {registry}")
    check(all(e["product_id"] == "COLOR_TEST" for e in registry), f"got {registry}")
    check(all(e["theme"] == "woodland animals" for e in registry), f"got {registry}")
    check(all("created_at" in e and e["created_at"] for e in registry), f"got {registry}")


def test_record_used_coloring_subjects_preserves_existing_entries():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._record_used_coloring_subjects("COLOR_A", "theme a", ["subject 1"])
        server._record_used_coloring_subjects("COLOR_B", "theme b", ["subject 2"])
        registry = server._coloring_theme_registry()
    check(len(registry) == 2, f"a second call must append, not overwrite, got {len(registry)}")


def _anthropic_response(subjects):
    msg = MagicMock()
    msg.content = [MagicMock(text=json.dumps({"subjects": subjects}))]
    return msg


def test_generate_coloring_subjects_returns_empty_without_api_key():
    with patch.object(server, "ANTHROPIC_KEY", ""):
        out = server._generate_coloring_subjects("ocean animals", exclude=[], count=20)
    check(out == [], f"no API key must yield [], got {out}")


def test_generate_coloring_subjects_returns_empty_for_blank_theme():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"):
        out = server._generate_coloring_subjects("   ", exclude=[], count=20)
    check(out == [], f"a blank theme must yield [], got {out}")


def test_generate_coloring_subjects_happy_path_parses_llm_json():
    fake_subjects = [f"ocean subject {i}" for i in range(20)]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_anthropic_create", return_value=_anthropic_response(fake_subjects)):
        out = server._generate_coloring_subjects("ocean animals", exclude=["already used one"], count=20)
    check(out == fake_subjects, f"got {out}")


def test_generate_coloring_subjects_returns_empty_on_call_failure():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_anthropic_create", side_effect=RuntimeError("simulated API failure")):
        out = server._generate_coloring_subjects("ocean animals", exclude=[], count=20)
    check(out == [], f"a raised exception from the API call must yield [], not propagate, got {out}")


def test_generate_coloring_subjects_returns_empty_on_unparseable_response():
    msg = MagicMock()
    msg.content = [MagicMock(text="not json at all")]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_anthropic_create", return_value=msg):
        out = server._generate_coloring_subjects("ocean animals", exclude=[], count=20)
    check(out == [], f"an unparseable LLM response must yield [], got {out}")


def test_resolve_coloring_subjects_errors_without_api_key():
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path), \
         patch.object(server, "ANTHROPIC_KEY", ""):
        subjects, err = server._resolve_coloring_subjects("ocean animals")
    check(subjects == [], f"got {subjects}")
    check(err is not None and "ANTHROPIC_API_KEY" in err, f"got {err!r}")


def test_resolve_coloring_subjects_happy_path_returns_new_theme_set_size():
    import generate_coloring_pages as gcp
    path = _tmp_registry_path()
    fake_subjects = [f"forest subject {i}" for i in range(gcp.NEW_THEME_SET_SIZE)]
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path), \
         patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_generate_coloring_subjects", return_value=fake_subjects):
        subjects, err = server._resolve_coloring_subjects("forest animals")
    check(err is None, f"got {err!r}")
    check(subjects == fake_subjects, f"got {subjects}")


def test_resolve_coloring_subjects_drops_llm_repeats_of_registry_and_retries():
    """The LLM slipping and repeating something already in the registry must
    be caught and dropped by code (not trusted), then made up on the retry
    pass -- belt-and-suspenders per CLAUDE.md, not reliance on the prompt alone."""
    import generate_coloring_pages as gcp
    path = _tmp_registry_path()
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path):
        server._record_used_coloring_subjects("COLOR_OLD", "forest animals", ["a sleepy fox"])

    n = gcp.NEW_THEME_SET_SIZE
    # First call: the LLM repeats the already-used "a sleepy fox" plus (n-1) new ones -- one short.
    first_batch = ["a sleepy fox"] + [f"forest subject {i}" for i in range(n - 1)]
    # Retry call: makes up the shortfall with a genuinely new subject.
    retry_batch = ["a brand new forest subject"]
    calls = {"n": 0}

    def _fake_generate(theme, exclude, count, already_accepted=None):
        calls["n"] += 1
        return first_batch if calls["n"] == 1 else retry_batch

    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path), \
         patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_generate_coloring_subjects", side_effect=_fake_generate):
        subjects, err = server._resolve_coloring_subjects("forest animals")
    check(err is None, f"got {err!r}")
    check(len(subjects) == n, f"expected {n} subjects after the retry made up the shortfall, got {len(subjects)}")
    check("a sleepy fox" not in subjects, f"a subject already in the registry must never be returned, got {subjects}")
    check(calls["n"] == 2, f"expected exactly 1 retry (2 total calls), got {calls['n']}")


def test_resolve_coloring_subjects_errors_when_still_short_after_retry():
    import generate_coloring_pages as gcp
    path = _tmp_registry_path()
    n = gcp.NEW_THEME_SET_SIZE
    # Every call returns the same 3 subjects, never enough, and always identical
    # (so accepted_normalized dedup also kicks in on the second call).
    with patch.object(server, "_COLORING_THEME_REGISTRY_PATH", path), \
         patch.object(server, "ANTHROPIC_KEY", "fake-key-for-test"), \
         patch.object(server, "_generate_coloring_subjects", return_value=["one", "two", "three"]):
        subjects, err = server._resolve_coloring_subjects("a very narrow theme")
    check(subjects == [], f"a failed resolution must return [], got {subjects}")
    check(err is not None and str(n) in err, f"the error should mention the target count ({n}), got {err!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("COLORING THEME REGISTRY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COLORING THEME REGISTRY TESTS OK — the permanent cross-listing dedup registry "
          "reads/writes correctly, subject generation is mocked end-to-end, and "
          "_resolve_coloring_subjects() code-verifies LLM output against the registry, "
          "retrying shortfalls and erroring clearly when it can't reach NEW_THEME_SET_SIZE.")


if __name__ == "__main__":
    run()
