"""
Regression test for the Ask-tab redesign (2026-07-22).

While adding _renderMarkdownLite() to frank_hud_mockup.py, `.split('\n')` was
written directly in the Python source. Since the entire HUD page is a Python
triple-quoted string (_FRANK_HUD_MOCKUP), Python's own string-escape parser
turned that `\n` into a literal embedded newline INSIDE a single-quoted JS
string literal before the JS ever reached a browser -- silently breaking the
string literal and taking down the ENTIRE inline <script> block with it (every
function in that block, including totally unrelated ones like phoneTab(),
became `undefined` at runtime). No test caught this because none of the
existing tests execute or even syntax-check the HUD's embedded JavaScript --
they only regex-match strings in the Python source. Confirmed live via
Playwright (`typeof phoneTab -> 'undefined'`, `pageerror: Invalid or
unexpected token`) before the fix (using `\\n` so Python's escape parser
resolves to a literal `\n` in the JS output).

This test extracts the HUD's inline <script> blocks post-Python-string-
resolution (importing the real module, not regex-reading the raw .py file, so
Python's own escape processing is exercised the same way it is at runtime) and
runs them through `node --check` to catch this exact class of bug -- any
Python escape sequence (\n, \t, \r, \\, etc.) typed into embedded JS that
Python silently resolves before the browser ever sees it.

Run: python tests/test_frank_hud_js_syntax.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def run() -> None:
    node = shutil.which("node")
    if not node:
        print("FRANK HUD JS SYNTAX TEST SKIPPED — no `node` binary on PATH.")
        return

    import frank_hud_mockup as fh  # noqa: E402 — exercises Python's real string-escape resolution

    src = fh._FRANK_HUD_MOCKUP
    blocks = re.findall(r"<script>(.*?)</script>", src, re.S)
    check(len(blocks) >= 1, "expected at least one inline <script>...</script> block in the HUD page")

    for i, js in enumerate(blocks):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(js)
            path = f.name
        result = subprocess.run([node, "--check", path], capture_output=True, text=True)
        check(result.returncode == 0,
              f"inline <script> block #{i} failed node --check:\n{result.stderr}")

    if _failures:
        print("FRANK HUD JS SYNTAX TEST FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FRANK HUD JS SYNTAX TEST OK — every inline <script> block in frank_hud_mockup.py "
          "(after Python's own string-escape resolution) is syntactically valid JavaScript.")


if __name__ == "__main__":
    run()
