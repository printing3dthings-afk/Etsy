"""
Regression test for the mobile Ask-tab redesign (2026-07-22, Phase 1).

Scott reported the "Ask" tab was a dead end: tapping it opened a nearly blank
orb popup (#orb-view) with only a "Open full chat" button, and only tapping
THAT revealed the real chat + stats content -- confirmed via a screen
recording he sent. Phase 1 makes Ask land directly on the real content
(#screen-cmd), demotes voice/orb mode to an in-screen button, adds a mobile
shop-name header, and redesigns the chat bubbles (cyan accent, entrance
animation, markdown rendering, in-chat speaking indicator).

Static source checks only (no server/browser needed) -- the live runtime
behavior (state-machine classes, markdown rendering, XSS boundary) was
verified via Playwright during development; this test guards the specific
source-level regressions that would silently undo the fix.

Run: python tests/test_ask_tab_redesign.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HUD_PATH = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def run() -> None:
    src = HUD_PATH.read_text()

    # ── IA fix: Ask tab must route straight to the chat/stats screen ───────
    m = re.search(r"function phoneTab\(which\)\{.*?\n\}", src, re.S)
    check(m is not None, "expected to find phoneTab(which) function body")
    body = m.group(0) if m else ""
    check("if (which === 'ask'){ phoneOpenScreen('cmd'); return; }" in body,
          "phoneTab('ask') must route directly to phoneOpenScreen('cmd'), not back to "
          "the blank orb popup (openFrankPopup()) -- that regressed the exact dead-end "
          "flow Scott reported")
    check("document.body.classList.remove('cc-open');" in body,
          "phoneTab() must clear a stale cc-open class when returning to a tab-bar "
          "panel -- confirmed live via Playwright that phoneOpenScreen('cmd') (now the "
          "primary Ask-tab path) leaves cc-open stuck otherwise")

    # ── Mobile shop-name header (Scott: keep the branding, as a header) ────
    # 2026-08-15: the header is now Scott's real hand-lettered wordmark image
    # (light/dark-mode variants swapped via CSS), not plain text.
    check('<div class="mobile-shop-header"><img class="wordmark-light" '
          'src="/static/brand/onbrandcraftz-wordmark.svg" alt="OnBrandCraftz"' in src,
          "expected a mobile-only OnBrandCraftz wordmark image inside the chat panel")
    check("body.is-mobile .mobile-shop-header{display:flex" in src,
          "the shop-name header must be shown on mobile (hidden by default for desktop)")

    # ── Voice mode demoted to an in-screen control ──────────────────────────
    check('<button id="chat-voice-btn" onclick="openFrankPopup()"' in src,
          "expected a mic/voice button inside the chat input row that opens the "
          "existing orb popup on demand")

    # ── Chat bubble redesign: cyan accent + entrance animation + shadow ────
    check(".lc-bubble.bot{" in src and "border:1px solid var(--cyan)" in src,
          "bot bubbles must carry the app's cyan accent (previously flat panel-gray "
          "with zero cyan anywhere in chat)")
    check("@keyframes bubble-in{" in src, "expected a bubble-in entrance animation")
    check(".lc-bubble.bubble-in{animation:bubble-in" in src,
          "bubble entrance animation must be wired to the .bubble-in class")
    check(".lc-bubble{animation:none}" in src,
          "bubble entrance animation must be silenced under prefers-reduced-motion")

    # ── Markdown rendering: once at 'done', never per-chunk ────────────────
    check("function _renderMarkdownLite(text) {" in src,
          "expected a _renderMarkdownLite() helper")
    done_m = re.search(r"\} else if \(d\.type === 'done'\) \{.*?\n    \}", src, re.S)
    check(done_m is not None, "expected to find the type:'done' WS handler branch")
    done_body = done_m.group(0) if done_m else ""
    check("_renderMarkdownLite(finalText)" in done_body,
          "the type:'done' handler must render markdown once on the completed reply")
    chunk_m = re.search(r"\} else if \(d\.type === 'chunk' && bot\) \{.*?\n    \}", src, re.S)
    check(chunk_m is not None and "_renderMarkdownLite" not in chunk_m.group(0),
          "the type:'chunk' handler must NOT call _renderMarkdownLite per-chunk "
          "(re-parsing partial markdown mid-stream, e.g. an unclosed '**', is wasted "
          "work and can render garbage until the message completes)")

    # ── XSS boundary: error path and user bubbles stay plain-text ──────────
    check("addBubble('⚠️ ' + d.content, 'bot');" in src,
          "the type:'error' path must call addBubble() WITHOUT a markdown opt (stays "
          "plain textContent, not innerHTML) -- this is a deliberate XSS boundary, "
          "buyer/tool-error text must never be parsed as HTML")
    check("function addBubble(text, who, opts) {" in src,
          "addBubble() must take an explicit opts param so markdown rendering is "
          "opt-in per call site, not a blanket default for every 'bot' bubble")

    # ── Speaking indicator stays in sync with the single setSpeaking() call site ──
    setspeaking_m = re.search(r"function setSpeaking\(on, viaFallback\)\{.*?\n\}", src, re.S)
    check(setspeaking_m is not None, "expected to find setSpeaking()")
    sp_body = setspeaking_m.group(0) if setspeaking_m else ""
    check("chat-speaking-indicator" in sp_body,
          "setSpeaking() must toggle #chat-speaking-indicator so the in-chat cue can "
          "never drift out of sync with the orb's own speaking state")
    check('<div id="chat-speaking-indicator"' in src,
          "expected the #chat-speaking-indicator element to exist near the chat input")

    if _failures:
        print("ASK TAB REDESIGN TEST FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ASK TAB REDESIGN TEST OK — Ask routes straight to chat/stats, voice is an "
          "in-screen control, the shop-name header is mobile-only, and the chat "
          "redesign (bubbles/animation/markdown/speaking indicator) is wired correctly "
          "with its XSS boundary intact.")


if __name__ == "__main__":
    run()
