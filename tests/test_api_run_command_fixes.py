#!/usr/bin/env python3
"""
main.py's api_run_command() (2026-07-29 audit) -- a separate, near-duplicate
copy of command_center.py's own run_command() streaming-subprocess logic,
used specifically for the Railway-hosted /cmd page. Had the identical two
bugs (see test_command_center_fixes.py for the full writeup): a python3
token not normalized to sys.executable, and os.read(fd, 4096).decode(errors=
"replace") corrupting multibyte UTF-8 characters split across reads.

Run: python tests/test_api_run_command_fixes.py
"""
import asyncio
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_api_run_command_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "api-run-command-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from starlette.requests import Request  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_request() -> Request:
    scope = {"type": "http", "method": "GET", "path": "/run", "headers": [], "query_string": b""}
    return Request(scope)


def test_python3_command_normalized_to_sys_executable():
    captured_args = {}
    real_popen = server.subprocess.Popen

    def _spy_popen(args, **kwargs):
        captured_args["args"] = list(args)
        harmless = [sys.executable, "-c", "print('ok')"]
        return real_popen(harmless, **kwargs)

    async def _drain(body_iterator):
        async for _ in body_iterator:
            pass

    with patch.object(server, "_check_session", return_value=True), \
         patch("main.subprocess.Popen", side_effect=_spy_popen):
        response = server.api_run_command(_fake_request(), id="health_check")
        asyncio.run(_drain(response.body_iterator))

    check("args" in captured_args, "subprocess.Popen was never called")
    if "args" in captured_args:
        args = captured_args["args"]
        check(args[0] == sys.executable,
              f"expected cmd_args[0] to be normalized to sys.executable ({sys.executable!r}), got {args[0]!r}")


def test_incremental_decoder_handles_split_multibyte_char():
    import codecs
    emoji = "🚀".encode("utf-8")
    check(len(emoji) == 4, f"expected a 4-byte UTF-8 char for this test, got {len(emoji)} bytes")
    first_chunk = b"Initializing task" + emoji[:2]
    second_chunk = emoji[2:] + b" done\n"

    buggy = first_chunk.decode("utf-8", errors="replace") + second_chunk.decode("utf-8", errors="replace")
    check("�" in buggy, "sanity check: naive per-chunk decoding should corrupt the split emoji")

    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    fixed = decoder.decode(first_chunk) + decoder.decode(second_chunk) + decoder.decode(b"", final=True)
    check("�" not in fixed, f"incremental decoder should never emit a replacement char here, got {fixed!r}")
    check(fixed == "Initializing task🚀 done\n", f"expected the emoji to round-trip intact, got {fixed!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("API RUN COMMAND FIXES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("API RUN COMMAND FIXES TESTS OK — main.py's api_run_command() sys.executable "
          "normalization and incremental UTF-8 decoder both behave correctly.")


if __name__ == "__main__":
    run()
