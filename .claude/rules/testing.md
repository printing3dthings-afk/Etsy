# Testing — OnBrandCraftz / Frank

This repo does **not** use pytest classes/fixtures. Every test file is a
standalone runnable script with its own `check()`/`run()` harness. Follow
the existing pattern exactly — don't introduce a second testing style.

## The standard harness (copy this shape for every new test file)

```python
import os, sys, tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

# MUST happen before `import main` — main.py does real DB/token work at
# import time, so a real dev DB would get touched otherwise.
_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_<feature>_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "<feature>-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []

def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)

def test_something():
    ...
    check(actual == expected, f"expected X, got {actual!r}")

def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("<FEATURE> TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("<FEATURE> TESTS OK — <one sentence on what this proves>.")

if __name__ == "__main__":
    run()
```

Real examples to copy from directly: `tests/test_files_screen_grouping.py`,
`tests/test_listing_fix_manifest_gate.py`, `tests/test_action_reasoning_
panel.py`.

## Mocking

- Mock the narrowest real dependency, not the function under test. Patch
  `server.EtsyAPIClient`, `server.ANTHROPIC_KEY`, `server._anthropic_
  create`, `server._generate_tags_for_listings` — never fake out the
  logic you're actually trying to verify.
- To test a route handler directly (bypassing FastAPI's dependency
  injection), just call it as a plain async function:
  `asyncio.run(server.get_bundle_opportunities(_token="test"))`. `Depends(...)`
  default values are inert outside the real HTTP path.
- Swap `server._FILE_ROOTS["<root>"]` to a `tempfile.TemporaryDirectory()`
  for any test touching disk — never point tests at the real `data/`
  tree, and always restore the original value in a `finally`.

## Regression tests reproduce the exact bug, not generic coverage

A good test in this repo is grounded in the real failure that was found —
e.g. `test_scan_annotates_catalog_match_for_products_root_only` uses the
literal `coloring_set_01.zip` / `CB001_coloring.png` filenames from the
real reported bug, not synthetic placeholders. When you fix something
Scott reported, the regression test should make the *exact* symptom
impossible again, not just "cover the function" in the abstract.

## Full-suite entrypoint

`python tests/run_all.py` auto-discovers every `tests/test_*.py` and runs
each as a subprocess, reporting PASS/FAIL per file. Always run this before
shipping — a new test file needs no registration, it's picked up
automatically.

## Browser/UI tests

`tools/playwright_smoke.py` is one long script (not per-feature files),
sectioned with `# ── <feature> (date) ── ──` comment headers. Append new
UI regression blocks in that same file rather than creating a parallel
Playwright test runner.

**Known trap:** Frank registers its own service worker (`frank-sw.js`)
that re-fetches every GET request from inside the SW's own execution
context. `page.route("**/api/whatever", mock)` silently never fires for
requests that go through it — confirmed by direct reproduction (even a
bare `page.evaluate("fetch(...)")` bypasses the mock and hits the real
network). **Do not debug a "mock isn't working" mystery for more than a
few minutes on this app — assume the SW is the cause and mock at the JS
level instead:** monkeypatch the shared `authGet()` function directly
inside a `page.evaluate()` call. See `tools/playwright_smoke.py`'s Files
screen block for the exact working pattern.

Also prefer `el.textContent` over `el.innerText` when asserting on
rendered text in a Playwright check — `innerText` silently skips content
inside a `display:none` element (e.g. a collapsed accordion row) and
reflects CSS `text-transform`, both of which have broken assertions here
before.
