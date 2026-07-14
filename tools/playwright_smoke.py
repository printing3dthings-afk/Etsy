#!/usr/bin/env python3
"""
Real-browser smoke test — added 2026-07-10 as the direct fix for the confirmed
recurring root cause across this project's incident history: bugs that pass
`py_compile`, `node --check`, and the full pytest-style suite (all of which
either check syntax or drive the FastAPI app in-process with no real browser)
but break the moment an actual browser renders the page. Two concrete examples
from the same day this script was written:

  - The CSP `media-src` gap: every existing check stayed green throughout,
    because none of them ever asked a real browser to actually play a `blob:`
    URL through an `<audio>` element and observe whether it was blocked.
  - A systemic `from tools.X import Y` import bug (2026-07-03) that worked
    locally (repo root happens to be on `sys.path` in a dev shell) and broke
    only in Railway's actual container runtime.

This script is the missing layer: it boots the real app as a real HTTP server
(not FastAPI's in-process TestClient, which never exercises the actual
uvicorn/ASGI path or a real browser's CSP/audio/JS engine), drives it with a
real headless Chromium via Playwright, and asserts on things only a real
browser can prove:
  1. No browser console errors on the main authenticated screen.
  2. A `blob:` URL `<audio>` element actually reaches `oncanplay` — the exact
     proof used to diagnose and verify the CSP fix live; this is now a
     permanent regression test instead of an ad hoc one-off check.
  3. The Settings screen renders its expected sections.

Run locally:  python tools/playwright_smoke.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
from __future__ import annotations

import asyncio
import os
import signal
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(os.environ.get("PLAYWRIGHT_SMOKE_PORT", "18765"))
BASE_URL = f"http://127.0.0.1:{PORT}"
_TEST_USER = "pwsmoketest"
_TEST_PASS = "PwSmokeTest!2026Only"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _wait_for_health(timeout_s: float = 30.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(0.5)
    return False


def _start_server() -> tuple[subprocess.Popen, str]:
    tmp_db = tempfile.NamedTemporaryFile(prefix="frank_pw_smoke_", suffix=".db", delete=False)
    tmp_db.close()
    env = os.environ.copy()
    env["PORT"] = str(PORT)
    env["DB_PATH"] = tmp_db.name
    env["ENABLE_TEST_LOGIN"] = "true"
    env["TEST_LOGIN_USERNAME"] = _TEST_USER
    env["TEST_LOGIN_PASSWORD"] = _TEST_PASS
    env.setdefault("APP_SECRET_TOKEN", "pw-smoke-test-not-a-real-secret")
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "tools" / "api_server" / "main.py")],
        env=env, cwd=str(ROOT),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return proc, tmp_db.name


def _stop_server(proc: subprocess.Popen, db_path: str) -> None:
    try:
        proc.send_signal(signal.SIGTERM)
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass
    try:
        os.unlink(db_path)
    except OSError:
        pass


# Same portable-launch pattern as tools/browser_automation.py: this sandbox ships a
# working Chromium at CHROMIUM_PATH (a symlink) launched via executable_path; CI and
# Railway don't have that path, so `playwright install chromium` must have run there
# instead (ci-smoke.yml does this before invoking this script) and Playwright's own
# bundled browser is used by omitting executable_path.
CHROMIUM_PATH = os.getenv("CHROMIUM_PATH", "/opt/pw-browsers/chromium")


async def _run_browser_checks() -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        launch_kwargs = {"headless": True}
        if CHROMIUM_PATH and os.path.exists(CHROMIUM_PATH):
            launch_kwargs["executable_path"] = CHROMIUM_PATH
        browser = await p.chromium.launch(**launch_kwargs)
        try:
            ctx = await browser.new_context(viewport={"width": 1440, "height": 1000})
            page = await ctx.new_page()
            console_errors: list[str] = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(f"pageerror: {exc}"))

            await page.goto(f"{BASE_URL}/login", wait_until="load")
            await page.fill("#li-user", _TEST_USER)
            await page.fill("#li-pass", _TEST_PASS)
            await page.click("button[type=submit]")
            await page.wait_for_timeout(1000)
            await page.goto(f"{BASE_URL}/frank", wait_until="load")
            await page.wait_for_timeout(1500)
            try:
                await page.click("#welcome-overlay button:has-text('Got it')", timeout=3000)
            except Exception:
                pass
            await page.wait_for_timeout(500)

            check("Failed to load resource" not in "\n".join(console_errors)
                  or all("favicon" in e or "404" in e for e in console_errors),
                  f"unexpected console errors on /frank: {console_errors}")

            # ── the CSP regression proof: a blob: URL <audio> element must actually
            # be playable, not blocked by CSP media-src -- this is the exact check
            # that diagnosed and verified the 2026-07-10 voice-silence incident. ──
            blob_result = await page.evaluate("""
                () => new Promise((resolve) => {
                    try {
                        const bytes = Uint8Array.from(
                            atob('UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA='),
                            c => c.charCodeAt(0));
                        const blob = new Blob([bytes], {type: 'audio/wav'});
                        const url = URL.createObjectURL(blob);
                        const audio = new Audio(url);
                        audio.oncanplay = () => resolve({ok: true, readyState: audio.readyState});
                        audio.onerror = () => resolve({
                            ok: false,
                            errorCode: audio.error ? audio.error.code : null,
                        });
                        audio.play().catch(() => {});
                        setTimeout(() => resolve({ok: false, timedOut: true}), 5000);
                    } catch (e) { resolve({ok: false, threw: String(e)}); }
                })
            """)
            check(blob_result.get("ok") is True,
                  f"blob: URL <audio> playback failed -- this is the CSP media-src regression "
                  f"check (see tools/api_server/main.py's Content-Security-Policy header, the "
                  f"media-src directive must include blob: and data:): {blob_result}")

            # ── Settings screen renders its expected sections. Settings now lives
            # under the "Advanced" disclosure (hidden by default), so navigate via
            # showScreen() rather than clicking the hidden nav item. ──
            await page.evaluate("showScreen('settings')")
            await page.wait_for_timeout(1200)
            settings_html = await page.evaluate(
                "document.getElementById('screen-settings') ? "
                "document.getElementById('screen-settings').innerHTML : ''")
            check("setting-video-engine" not in settings_html and "setting-image-engine" not in settings_html,
                  "engine/model picker should be REMOVED from Settings (auto-picked by backend now)")
            check("new-user-name" not in settings_html,
                  "multi-admin 'Add Admin' form should be REMOVED (solo shop)")
            check("My Account" in settings_html, "Settings screen missing 'My Account' section")

            # ── Brand Kit redesign regression guards (2026-07-14): jump-nav, all 16 theme
            # cards + 3 listing-standard cards render and expand, hex-copy calls the
            # clipboard API, and the brand-mark preview canvas ids never collide. ──
            await page.evaluate("showScreen('brandkit')")
            await page.wait_for_timeout(800)
            bk = await page.evaluate("""() => {
                const chooser = document.querySelectorAll('#brandkit-chooser .create-choice');
                const content = document.getElementById('brandkit-content');
                return {
                    chooserCount: chooser.length,
                    anchorsPresent: ['bk-identity','bk-themes','bk-color-rules','bk-stickers',
                        'bk-listing-standards','bk-pricing','bk-typography','bk-brandmark','bk-photography']
                        .every(id => !!document.getElementById(id)),
                    themeCardCount: content.querySelectorAll('[id^="bk-theme-detail-"]').length,
                    listingCardCount: content.querySelectorAll('[id^="bk-listing-detail-"]').length,
                    markCanvasIds: [...document.querySelectorAll('.brand-mark-canvas')].map(c => c.id).sort(),
                };
            }""")
            check(bk.get("chooserCount") == 9, f"Brand Kit jump-nav should have 9 targets: {bk}")
            check(bk.get("anchorsPresent"), f"Brand Kit missing one or more of the 9 section anchors: {bk}")
            check(bk.get("themeCardCount") == 16, f"Brand Kit should render 16 theme cards (4 live + 12 planned): {bk}")
            check(bk.get("listingCardCount") == 3, f"Brand Kit should render 3 listing-standard cards: {bk}")
            check(bk.get("markCanvasIds") == ["brand-mark-preview", "brandkit-mark-preview"],
                  f"brand-mark canvas ids must be distinct, no collision: {bk}")

            # Click the first theme card's header -> its detail panel should go from
            # display:none to visible (toggleZip reuse).
            expand = await page.evaluate("""() => {
                const detail = document.querySelector('#brandkit-content [id^="bk-theme-detail-"]');
                if (!detail) return {ok: false};
                const before = getComputedStyle(detail).display;
                detail.parentElement.click();
                const after = getComputedStyle(detail).display;
                return {ok: before === 'none' && after !== 'none'};
            }""")
            check(expand.get("ok"), f"clicking a theme card should expand its detail panel: {expand}")

            # Click a hex swatch -> copyHex() fires; stub navigator.clipboard.writeText to
            # capture the value (real clipboard access is unreliable/permission-gated in
            # headless CI).
            copy_result = await page.evaluate("""() => new Promise(resolve => {
                let captured = null;
                navigator.clipboard.writeText = (text) => { captured = text; return Promise.resolve(); };
                const chip = document.querySelector('.bk-hexcopy');
                if (!chip) { resolve({ok: false, reason: 'no .bk-hexcopy element found'}); return; }
                chip.click();
                setTimeout(() => resolve({ok: !!captured && /^#[0-9A-Fa-f]{6}$/.test(captured), captured}), 150);
            })""")
            check(copy_result.get("ok"), f"clicking a hex chip should call clipboard.writeText with a hex value: {copy_result}")

            listing_text = await page.evaluate(
                "document.getElementById('bk-listing-standards').innerText")
            check(all(s in listing_text for s in ["Digital Planners", "Wall Art", "SVG"]),
                  "Brand Kit must render all 3 product-type listing-standards blocks")

            pricing_text = await page.evaluate("document.getElementById('bk-pricing').innerText")
            check(all(s in pricing_text for s in ["$14.99", "$4.99", "$9.99", "$17.99"]),
                  f"Brand Kit pricing section should render all 4 pricing tables: {pricing_text[:200]}")

            # ── First-time-user simplification (2026-07-11) regression guards ──
            simp = await page.evaluate("""() => {
                const hidden = el => !el || el.offsetParent === null;
                return {
                    createNav: !!document.querySelector('.nav-item[data-screen="create"]'),
                    createScreen: !!document.getElementById('screen-create'),
                    knowledgeScreen: !!document.getElementById('screen-knowledge'),
                    feedHidden: hidden(document.querySelector('.col-feed')),
                    aicoreHidden: hidden(document.querySelector('.col-aicore')),
                    relayHidden: hidden(document.getElementById('bb-relay')),
                    advancedItemsHiddenByDefault: hidden(document.querySelector('.nav-item[data-tier="advanced"]')),
                    homeLabeled: !![...document.querySelectorAll('.nav-item')].find(n => n.dataset.screen === 'cmd' && n.textContent.includes('Home')),
                    imageEngineSelect: (()=>{ const s=document.getElementById('setting-image-engine'); return !!s && [...s.options].some(o=>o.value==='gemini'); })(),
                    videoEngineSelect: (()=>{ const s=document.getElementById('setting-video-engine'); return !!s && [...s.options].some(o=>o.value==='veo'); })(),
                };
            }""")
            check(simp.get("createNav") and simp.get("createScreen"),
                  f"Create must be reachable (nav + screen): {simp}")
            check(simp.get("knowledgeScreen"), f"merged Knowledge screen missing: {simp}")
            check(simp.get("feedHidden") and simp.get("aicoreHidden") and simp.get("relayHidden"),
                  f"engineering plumbing must be hidden in the everyday view: {simp}")
            check(simp.get("advancedItemsHiddenByDefault"),
                  f"Advanced nav items must be collapsed by default: {simp}")
            check(simp.get("homeLabeled"), f"'Home' nav label expected (was Command Center): {simp}")
            check(simp.get("imageEngineSelect"), f"Create screen must have an image-engine dropdown incl. Gemini: {simp}")
            check(simp.get("videoEngineSelect"), f"Create screen must have a video-engine dropdown incl. Veo: {simp}")

        finally:
            await browser.close()


def main() -> int:
    proc, db_path = _start_server()
    try:
        if not _wait_for_health():
            check(False, "server did not become healthy within timeout — see stderr if run "
                          "with output captured, or check tools/api_server/main.py starts cleanly")
        else:
            try:
                asyncio.run(_run_browser_checks())
            except Exception:
                _failures.append("browser checks raised an unexpected error:\n" + traceback.format_exc())
    finally:
        _stop_server(proc, db_path)

    if _failures:
        print("PLAYWRIGHT SMOKE TEST FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s).", file=sys.stderr)
        return 1
    print("PLAYWRIGHT SMOKE TEST OK — real browser: no console errors, blob: audio "
          "playback works (CSP media-src regression check), Settings screen renders.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
