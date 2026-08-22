#!/usr/bin/env python3
"""Regression test for the 2026-07-10 GitHub Actions incident: both
tools/ci_report_health_issue.py and tools/ci_report_issue.py crashed on
*every* invocation (every 5 minutes, for the health watchdog) with
`http.client.InvalidURL: URL can't contain control characters`.

Root cause: each script's MARKER_TITLE contains an em dash ("—"), and
`find_open_issue()` interpolated it raw into a GitHub search URL. The em
dash's UTF-8 bytes (0xE2 0x80 0x94) include 0x80 and 0x94, which fall in
the \\x7f-\\x9f range Python 3.11's http.client treats as a "control
character" and refuses to send -- so the request never even reached the
network, it died in the local `putrequest()` path validation. That means
this bug reproduces with zero network access, which is what this test
exploits: `urllib.request.urlopen()` validates the path before opening
any socket, so calling `gh_request()` with a real (bad or fixed) URL
either raises immediately (bug) or attempts a real socket connect,
distinguishable without needing a live GitHub token.

Run: python tests/test_ci_report_issue_url.py
"""
import http.client
import os
import socket
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tools.ci_report_health_issue as health_mod
import tools.ci_report_issue as integrity_mod

_passed = 0
_failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global _passed, _failed
    if condition:
        _passed += 1
        print(f"  PASS: {name}")
    else:
        _failed += 1
        print(f"  FAIL: {name} {detail}")


def _find_open_issue_does_not_crash_on_url_construction(mod, label: str) -> None:
    """find_open_issue() must get past URL construction and attempt a real
    network call (which fails harmlessly with no route/DNS in this sandbox)
    rather than raising http.client.InvalidURL before ever reaching the
    network. Any exception OTHER than InvalidURL proves the URL itself was
    accepted by http.client's path validator -- exactly what was broken."""
    try:
        mod.find_open_issue("printing3dthings-afk/Etsy", "fake-token-not-real")
    except http.client.InvalidURL as e:
        check(f"{label}: find_open_issue does not raise InvalidURL", False, f"-- {e}")
        return
    except (urllib.error.URLError, socket.error, socket.gaierror, ConnectionError, OSError, TimeoutError):
        # Expected: no real network route in this sandbox / bad fake token.
        # This is proof the URL passed local validation and an actual
        # connection attempt was made -- the bug is fixed.
        check(f"{label}: find_open_issue does not raise InvalidURL", True)
        return
    except Exception:
        # Any other exception (e.g. a real 401 RuntimeError if network is
        # reachable) also proves we got past URL validation.
        check(f"{label}: find_open_issue does not raise InvalidURL", True)
        return
    check(f"{label}: find_open_issue does not raise InvalidURL", True)


def test_health_issue_url_construction():
    _find_open_issue_does_not_crash_on_url_construction(health_mod, "ci_report_health_issue")


def test_integrity_issue_url_construction():
    _find_open_issue_does_not_crash_on_url_construction(integrity_mod, "ci_report_issue")


def test_marker_titles_still_contain_em_dash():
    # Sanity check that this test is actually exercising the hazardous
    # character, not a title that got quietly de-fanged.
    check(
        "ci_report_health_issue.MARKER_TITLE contains em dash",
        "—" in health_mod.MARKER_TITLE,
    )
    check(
        "ci_report_issue.MARKER_TITLE contains em dash",
        "—" in integrity_mod.MARKER_TITLE,
    )


def main() -> int:
    print("Running ci_report_issue URL-construction tests...\n")
    test_marker_titles_still_contain_em_dash()
    test_health_issue_url_construction()
    test_integrity_issue_url_construction()
    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
