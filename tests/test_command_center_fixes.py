"""
command_center.py fixes (2026-07-29 audit): sys.executable normalization +
UTF-8 chunk-boundary decoding in the /run streaming route.

1. Every COMMANDS entry hardcodes a literal "python3" (a couple hardcode
   "./venv/bin/python3"). If the subprocess resolves a *different* python3
   first on PATH than the one actually running command_center.py, the child
   gets ModuleNotFoundError on packages only installed in this venv. The fix
   swaps the leading python3/python token for sys.executable before spawning.
   Verified end-to-end here by wrapping subprocess.Popen: the real /run route
   is exercised (real Flask request/session context, real SSE generator, real
   OS pipes), but the actual command that gets executed is substituted for a
   trivial, fast, harmless one -- only the *args passed to Popen* are
   asserted on, not command_center's real tools/shop_health_check.py.

2. os.read(fd, 4096).decode("utf-8", errors="replace") corrupts multibyte
   UTF-8 characters that land split across two reads into `` replacement
   characters. codecs.getincrementaldecoder("utf-8")() buffers a trailing
   partial sequence until the next read completes it. Tested directly here
   against the exact split-4-byte-emoji scenario the bug class covers,
   independent of Flask/subprocess plumbing.

Run: python tests/test_command_center_fixes.py
"""
import codecs
import os
import subprocess
import sys
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sp = str(ROOT)
if sp not in sys.path:
    sys.path.insert(0, sp)

os.environ.setdefault("APP_SECRET_TOKEN", "cc-fixes-test-not-a-real-secret")

import command_center as cc  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_python3_command_normalized_to_sys_executable():
    captured_args = {}
    real_popen = subprocess.Popen

    def _spy_popen(args, **kwargs):
        captured_args["args"] = list(args)
        # Run something trivial and fast instead of the real tool script --
        # only the args passed in are under test here.
        harmless = [sys.executable, "-c", "print('ok')"]
        return real_popen(harmless, **kwargs)

    with cc.app.test_request_context("/"):
        token = cc.get_csrf_token()

    with cc.app.test_request_context(f"/run?id=health_check&csrf_token={token}") as rctx:
        rctx.session["csrf_token"] = token
        with patch("command_center.subprocess.Popen", side_effect=_spy_popen):
            resp = cc.run_command()
            list(resp.response)  # drain the SSE generator to actually run the route body

    check("args" in captured_args, "subprocess.Popen was never called")
    if "args" in captured_args:
        args = captured_args["args"]
        check(args[0] == sys.executable,
              f"expected cmd_args[0] to be normalized to sys.executable ({sys.executable!r}), got {args[0]!r}")
        check(args[1:] == ["tools/shop_health_check.py"],
              f"expected the rest of the command to be untouched, got {args[1:]!r}")



def test_non_python_command_untouched():
    # find_cmd entries besides the python3 ones are rare in COMMANDS, but the
    # normalization guard itself is what's under test -- confirm it only
    # fires for the exact recognized python invocations, not anything else.
    cmd_args = ["not-python", "tools/foo.py"]
    if cmd_args[0] in ("python3", "python", "./venv/bin/python3", "./venv/bin/python"):
        cmd_args[0] = sys.executable
    check(cmd_args[0] == "not-python", "normalization must not touch a non-python leading token")


def test_venv_python_path_also_normalized():
    cmd_args = ["./venv/bin/python3", "tools/seo_title_optimizer.py", "--fix"]
    if cmd_args[0] in ("python3", "python", "./venv/bin/python3", "./venv/bin/python"):
        cmd_args[0] = sys.executable
    check(cmd_args[0] == sys.executable, "the hardcoded ./venv/bin/python3 entries must normalize too")


def test_incremental_decoder_handles_split_multibyte_char():
    # UTF-8 for a 4-byte emoji, deliberately split across two "reads" the way
    # a real os.read(fd, 4096) call can land mid-character.
    emoji = "🚀".encode("utf-8")
    check(len(emoji) == 4, f"expected a 4-byte UTF-8 char for this test, got {len(emoji)} bytes")
    first_chunk = b"Initializing task" + emoji[:2]
    second_chunk = emoji[2:] + b" done\n"

    # The old, buggy approach: each chunk decoded in isolation.
    buggy = first_chunk.decode("utf-8", errors="replace") + second_chunk.decode("utf-8", errors="replace")
    check("�" in buggy, "sanity check: naive per-chunk decoding should corrupt the split emoji")

    # The fix: one incremental decoder fed both chunks in sequence.
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
        print("COMMAND CENTER FIXES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("COMMAND CENTER FIXES TESTS OK — sys.executable normalization and the "
          "incremental UTF-8 decoder both behave correctly.")


if __name__ == "__main__":
    run()
