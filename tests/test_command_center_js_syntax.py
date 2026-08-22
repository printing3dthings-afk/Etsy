"""
Regression test for command_center.py's embedded JavaScript (2026-07-29).

Same bug class already caught once in frank_hud_mockup.py (see
test_frank_hud_js_syntax.py's docstring, 2026-07-22): a Python escape
sequence like `\\n` typed directly into a Python triple-quoted HTML/JS
template string gets silently resolved by Python's own string parser into a
literal embedded newline INSIDE a single-quoted JS string literal, before
the JS ever reaches a browser -- breaking that string literal and taking
down the entire inline <script> block with it. That earlier fix only added
coverage for frank_hud_mockup.py; command_center.py's own HTML/LOGIN_HTML/
SVG_PAGE_HTML templates had no equivalent test and had regressed the exact
same way (found live: `clearOutput()`'s "Console cleared." span and
`runCmd()`'s "Initializing task" span both had a literal `\n` in the Python
source instead of `\\n`, breaking clearOutput() itself and everything
downstream of it in the same <script> block -- the whole Command Center's
client-side JS, including totally unrelated functions like theme switching,
was non-functional in a real browser before this fix).

This test extracts each template's inline <script> blocks post-Python-
string-resolution (importing the real module, not regex-reading the raw .py
file, so Python's own escape processing is exercised the same way it is at
runtime) and runs them through `node --check`.

Run: python tests/test_command_center_js_syntax.py
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sp = str(ROOT)
if sp not in sys.path:
    sys.path.insert(0, sp)

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def run() -> None:
    node = shutil.which("node")
    if not node:
        print("COMMAND CENTER JS SYNTAX TEST SKIPPED — no `node` binary on PATH.")
        return

    import command_center as cc  # noqa: E402 — exercises Python's real string-escape resolution

    total_blocks = 0
    for template_name in ("HTML", "LOGIN_HTML", "SVG_PAGE_HTML"):
        src = getattr(cc, template_name)
        blocks = re.findall(r"<script>(.*?)</script>", src, re.S)
        for i, js in enumerate(blocks):
            total_blocks += 1
            with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(js)
                path = f.name
            result = subprocess.run([node, "--check", path], capture_output=True, text=True)
            check(result.returncode == 0,
                  f"{template_name} inline <script> block #{i} failed node --check:\n{result.stderr}")

    check(total_blocks >= 1, "expected at least one inline <script>...</script> block across command_center.py's templates")

    if _failures:
        print("COMMAND CENTER JS SYNTAX TEST FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print(f"COMMAND CENTER JS SYNTAX TEST OK — all {total_blocks} inline <script> block(s) across "
          "command_center.py's templates (after Python's own string-escape resolution) are syntactically valid JavaScript.")


if __name__ == "__main__":
    run()
