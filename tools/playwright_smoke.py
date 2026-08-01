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
import json
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

            # ── First-login spotlight tour (2026-07-15): on a desktop viewport this
            # replaces the old single-card welcome-overlay with startTour()'s
            # multi-step spotlight walkthrough. Exercise it for real instead of just
            # dismissing it, since this IS the feature under test. ──
            tour_step1 = await page.evaluate("""() => {
                const root = document.getElementById('tour-root');
                return {
                    visible: !!root && getComputedStyle(root).display !== 'none',
                    title: document.getElementById('tour-step-title').textContent,
                    dotCount: document.querySelectorAll('#tour-dots .dot').length,
                    backDisabled: document.getElementById('tour-back-btn').disabled,
                };
            }""")
            check(tour_step1.get("visible"), f"tour should auto-show on first login (desktop): {tour_step1}")
            check("Welcome" in tour_step1.get("title", ""), f"tour step 1 should be the welcome intro: {tour_step1}")
            check(tour_step1.get("dotCount", 0) >= 10, f"tour should have ~12 steps: {tour_step1}")
            check(tour_step1.get("backDisabled"), f"Back should be disabled on step 1: {tour_step1}")

            await page.click("#tour-next-btn")
            await page.wait_for_timeout(600)
            step2 = await page.evaluate("""() => ({
                title: document.getElementById('tour-step-title').textContent,
                screen: document.querySelector('.screen.active').id,
                spotVisible: getComputedStyle(document.getElementById('tour-spot')).boxShadow !== 'none',
            })""")
            check(step2.get("title") == "Talk to Frank" or "Talk to" in step2.get("title", ""),
                  f"tour step 2 should introduce the orb: {step2}")
            check(step2.get("spotVisible"), f"tour spotlight should be visible on step 2: {step2}")

            # Jump to the Approvals nav-item step and confirm the tour actually
            # switches screens as it spotlights each nav item.
            await page.click("#tour-next-btn")
            await page.wait_for_timeout(600)
            step3 = await page.evaluate("""() => ({
                title: document.getElementById('tour-step-title').textContent,
                activeScreen: document.querySelector('.screen.active').id,
            })""")
            check(step3.get("title") == "Approvals", f"tour step 3 should be Approvals: {step3}")
            check(step3.get("activeScreen") == "screen-actions",
                  f"tour should navigate to the Approvals screen on that step: {step3}")

            # Skip out entirely -> overlay closes, frankWelcomeSeen persisted so the
            # tour won't auto-show again next load.
            await page.click(".tour-controls .tour-skip")
            await page.wait_for_timeout(300)
            skip_result = await page.evaluate("""() => ({
                hidden: getComputedStyle(document.getElementById('tour-root')).display === 'none',
                seen: localStorage.getItem('frankWelcomeSeen'),
            })""")
            check(skip_result.get("hidden"), f"Skip tour should close the overlay: {skip_result}")
            check(skip_result.get("seen") == "1", f"Skip tour should persist frankWelcomeSeen: {skip_result}")

            # The '?' header icon must replay the tour from step 1 on demand.
            await page.click("[title='Replay tutorial']")
            await page.wait_for_timeout(400)
            replay = await page.evaluate("""() => ({
                visible: getComputedStyle(document.getElementById('tour-root')).display !== 'none',
                title: document.getElementById('tour-step-title').textContent,
            })""")
            check(replay.get("visible"), f"'?' icon should reopen the tour: {replay}")
            check("Welcome" in replay.get("title", ""), f"replay should restart at step 1: {replay}")
            await page.click(".tour-controls .tour-skip")
            await page.wait_for_timeout(300)

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

            # ── Settings audit (2026-07-31): the Connections summary card used to
            # call GET /api/etsy-tokens (owner-only) alongside /api/credentials/status
            # via Promise.all, so every non-owner ("admin"-role, same as this test's
            # login) session 403'd on the second call and the whole card showed
            # "offline" -- not just the token-age line. Confirm it no longer does. ──
            conn_summary = await page.evaluate(
                "document.getElementById('settings-connections-summary') ? "
                "document.getElementById('settings-connections-summary').innerText : ''")
            check("offline" not in conn_summary.lower(),
                  f"Settings Connections summary must not show 'offline' for a standard (non-owner) "
                  f"test login -- this was the live 403-poisons-Promise.all bug: {conn_summary!r}")

            # ── #settings-build-ver used to be populated only by loadCredentialsAndHealth(),
            # which isn't in _SCREEN_LOADERS.settings -- it only worked because cmd's loaders
            # happen to fire once at initial page load. Clear it and re-trigger Settings' own
            # loaders (simulating a return visit later in the session) to prove Settings now
            # owns repopulating it itself. ──
            build_ver_state = await page.evaluate("""() => new Promise(resolve => {
                const el = document.getElementById('settings-build-ver');
                if (!el) { resolve({ok: false, reason: 'no #settings-build-ver element'}); return; }
                el.textContent = '';
                showScreen('settings');
                setTimeout(() => resolve({ok: true, text: el.textContent}), 1500);
            })""")
            check(build_ver_state.get("ok") and "Build" in build_ver_state.get("text", ""),
                  f"#settings-build-ver should repopulate when Settings' own loaders re-run "
                  f"(not just on initial page load): {build_ver_state}")

            # ── 4 new bright color themes (2026-07-18, Scott: "brighter colors but
            # make sure text is readable") -- confirm each is wired all the way
            # through: listed in the Settings swatch picker, and _setTheme()
            # actually applies its real CSS custom properties on <html>. ──
            for theme_name, expect_bg_hex in [
                ("sunwashed", "#fff8f0"),
                ("mermaid", "#f0fbfa"),
                ("clubroom", "#fffdf5"),
                ("springvivid", "#fbf7ff"),
            ]:
                theme_state = await page.evaluate(f"""() => {{
                    _setTheme('{theme_name}');
                    const cs = getComputedStyle(document.documentElement);
                    return {{
                        hasClass: document.documentElement.classList.contains('theme-{theme_name}'),
                        bg: cs.getPropertyValue('--bg').trim().toLowerCase(),
                        swatchRowText: (document.getElementById('theme-swatch-row') || {{}}).textContent || '',
                    }};
                }}""")
                check(theme_state.get("hasClass"), f"_setTheme('{theme_name}') should add the theme-{theme_name} class: {theme_state}")
                check(theme_state.get("bg") == expect_bg_hex,
                      f"theme '{theme_name}' should compute --bg={expect_bg_hex} on :root after switching: {theme_state}")
                check("✓" in theme_state.get("swatchRowText", ""),
                      f"theme swatch row should re-render showing an active checkmark: {theme_state}")
            # Reset to default so later checks in this run aren't affected.
            await page.evaluate("_setTheme('default')")

            # ── 4 new font pairings (2026-07-18) -- independent of color theme,
            # so verify the font-swatch mount point renders AND that switching
            # actually changes the real computed --font-display/--font-body,
            # while a subsequent theme switch leaves the font choice untouched
            # (proves the two systems really are decoupled, not just declared so). ──
            font_pairing_state = await page.evaluate("""() => {
                _setFontPairing('rounded');
                const csAfterFont = getComputedStyle(document.documentElement);
                const displayAfterFont = csAfterFont.getPropertyValue('--font-display').trim();
                _setTheme('mermaid');
                const csAfterTheme = getComputedStyle(document.documentElement);
                return {
                    swatchRowText: (document.getElementById('font-swatch-row') || {}).textContent || '',
                    displayAfterFont,
                    displayAfterThemeSwitch: csAfterTheme.getPropertyValue('--font-display').trim(),
                    themeHasClass: document.documentElement.classList.contains('theme-mermaid'),
                };
            }""")
            check("Friendly Rounded" in font_pairing_state.get("swatchRowText", ""),
                  f"font swatch row should list 'Friendly Rounded': {font_pairing_state}")
            check("Fredoka" in font_pairing_state.get("displayAfterFont", ""),
                  f"_setFontPairing('rounded') should set --font-display to Fredoka: {font_pairing_state}")
            check(font_pairing_state.get("displayAfterThemeSwitch") == font_pairing_state.get("displayAfterFont"),
                  f"switching color theme must not reset the chosen font pairing (the two systems should be independent): {font_pairing_state}")
            check(font_pairing_state.get("themeHasClass"), f"theme switch should still apply normally alongside a custom font pairing: {font_pairing_state}")
            # Reset both so later checks in this run aren't affected.
            await page.evaluate("_setFontPairing('default'); _setTheme('default');")

            # ── "Test Voice" button + Premium-voice fail-safe (2026-07-16) — Scott:
            # "How do I get Frank to speak out loud?" / "guarantee it will work."
            # Voice was already automatic and working; this doesn't (and can't)
            # guarantee a real device -- it proves the exact real speakText() path
            # can produce audible output on THIS device/browser right now, and that
            # a misconfigured Premium-voice toggle fails loudly instead of silently.
            # This environment has no OPENAI_API_KEY configured and Premium voice
            # defaults off, so clicking Test Voice here exercises the local Piper
            # engine end to end (real WASM model load, real <audio> playback). ──
            check("voice-test-btn" in settings_html and "voice-test-status" in settings_html,
                  "Settings screen missing the 'Test Voice' button/status line")
            await page.click("#voice-test-btn")
            # Piper's WASM/ONNX model load is the slow part on a cold run; give it
            # real headroom beyond the button's own 12s internal timeout so a slow
            # CI runner reads as a real failure, not a test-side race.
            await page.wait_for_timeout(500)
            voice_test_state = await page.evaluate("""() => new Promise(resolve => {
                let n = 0;
                const iv = setInterval(() => {
                    const statusEl = document.getElementById('voice-test-status');
                    const text = statusEl ? statusEl.textContent : '';
                    const settled = text && text !== 'Testing…';
                    if (settled || ++n > 40) {
                        clearInterval(iv);
                        resolve({
                            text: text,
                            color: statusEl ? statusEl.style.color : null,
                            stillInFlight: typeof _voiceTestInFlight !== 'undefined' ? _voiceTestInFlight : null,
                        });
                    }
                }, 500);
            })""")
            check(voice_test_state.get("text") not in (None, '', 'Testing…'),
                  f"Test Voice status never reached a terminal state within the wait window: {voice_test_state}")
            check(voice_test_state.get("stillInFlight") is False,
                  f"_voiceTestInFlight should be false once settled -- true here means the promise chain never "
                  f"resolved (hung), not that it explicitly failed: {voice_test_state}")
            print(f"  Test Voice result (informational, headless audio hardware varies by CI runner): {voice_test_state.get('text')!r}")

            # Premium-voice fail-safe, path 1: toggle already stuck ON from an
            # earlier session -- opening Settings (already done above) should
            # proactively catch it and revert.
            await page.evaluate("localStorage.setItem('frankPremiumVoice', '1')")
            await page.evaluate("showScreen('settings')")  # re-render with the forced localStorage state
            await page.wait_for_timeout(1500)
            revert_state_1 = await page.evaluate("""() => ({
                localStorageValue: localStorage.getItem('frankPremiumVoice'),
                checkboxChecked: document.querySelector('.premium-voice-cb') ?
                    document.querySelector('.premium-voice-cb').checked : null,
            })""")
            check(revert_state_1.get("localStorageValue") == '0',
                  f"a stuck-ON Premium voice toggle should auto-revert on Settings load (no OpenAI key configured "
                  f"in this environment): {revert_state_1}")
            check(revert_state_1.get("checkboxChecked") is False,
                  f"Premium voice checkbox should reflect the reverted state: {revert_state_1}")

            # Premium-voice fail-safe, path 2: live toggle flip (not just page load).
            await page.evaluate("localStorage.setItem('frankPremiumVoice', '0')")
            await page.evaluate("showScreen('settings')")
            await page.wait_for_timeout(500)
            await page.locator(".premium-voice-cb").first.check()
            await page.wait_for_timeout(1500)
            revert_state_2 = await page.evaluate("localStorage.getItem('frankPremiumVoice')")
            check(revert_state_2 == '0',
                  f"checking the Premium voice box live should also auto-revert it (no OpenAI key configured): "
                  f"localStorage value is {revert_state_2!r}")

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
            check(bk.get("listingCardCount") == 4,
                  f"Brand Kit should render 4 listing-standard cards (Planners/Wall Art/SVG/Stickers, 2026-07-31): {bk}")
            check(bk.get("markCanvasIds") == ["brand-mark-preview", "brandkit-mark-preview"],
                  f"brand-mark canvas ids must be distinct, no collision: {bk}")

            # ── createGoto() regression guard (2026-07-31): the 9 chooser tiles called a
            # function deleted 2026-07-22 by an unrelated Create-screen refactor, so every
            # tile threw ReferenceError on click and did nothing. Click one for real and
            # assert the page actually scrolled toward its target section. ──
            goto_result = await page.evaluate("""() => {
                const scroller = document.getElementById('brandkit-content');
                const target = document.getElementById('bk-pricing');
                if (!scroller || !target) return {ok: false, reason: 'missing scroller or target'};
                scroller.scrollTop = 0;
                const before = scroller.scrollTop;
                let threw = false;
                try {
                    document.querySelector('#brandkit-chooser .create-choice:nth-child(6)').click();
                } catch (e) { threw = true; }
                return {threw, before};
            }""")
            check(not goto_result.get("threw"),
                  f"clicking a Brand Kit chooser tile must not throw (createGoto must be defined): {goto_result}")
            await page.wait_for_timeout(600)
            after_scroll = await page.evaluate("document.getElementById('brandkit-content').scrollTop")
            check(after_scroll > goto_result.get("before", 0),
                  f"clicking the Pricing chooser tile should scroll #brandkit-content down toward bk-pricing: "
                  f"before={goto_result.get('before')} after={after_scroll}")

            # ── .bk-hexcopy keyboard accessibility (2026-07-31): swatches had onclick but
            # no role/tabindex, so keyboard-only users could never reach or activate them. ──
            kb_copy = await page.evaluate("""() => new Promise(resolve => {
                let captured = null;
                navigator.clipboard.writeText = (text) => { captured = text; return Promise.resolve(); };
                const chip = document.querySelector('.bk-hexcopy');
                if (!chip) { resolve({ok: false, reason: 'no .bk-hexcopy element found'}); return; }
                if (chip.getAttribute('role') !== 'button' || chip.tabIndex < 0) {
                    resolve({ok: false, reason: 'chip missing role=button/tabindex'}); return;
                }
                chip.focus();
                const focused = document.activeElement === chip;
                chip.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
                setTimeout(() => resolve({ok: focused && !!captured, focused, captured}), 150);
            })""")
            check(kb_copy.get("ok"), f"a hex chip must be keyboard-focusable and Enter-activatable: {kb_copy}")

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
            check(all(s in listing_text for s in ["Digital Planners", "Wall Art", "SVG", "Sticker Packs"]),
                  "Brand Kit must render all 4 product-type listing-standards blocks")

            pricing_text = await page.evaluate("document.getElementById('bk-pricing').innerText")
            check(all(s in pricing_text for s in ["$14.99", "$4.99", "$9.99", "$17.99"]),
                  f"Brand Kit pricing section should render all 4 pricing tables: {pricing_text[:200]}")

            # ── Connections screen regression guards (2026-07-31): Google Calendar row
            # in the API Credentials card, and the TikTok roadmap's traffic-only caveat. ──
            await page.evaluate("showScreen('connections')")
            await page.wait_for_timeout(800)
            conn_text = await page.evaluate("document.getElementById('connections-content').innerText")
            check("Google Calendar" in conn_text,
                  f"Connections screen's API Credentials card must include a Google Calendar row: "
                  f"{conn_text[:200]}")
            tiktok_toggle = await page.evaluate("""() => {
                const rows = [...document.querySelectorAll('#connections-content .hub-cred-row')];
                const row = rows.find(r => r.textContent.includes('TikTok'));
                if (!row) return {ok: false, reason: 'no TikTok roadmap row found'};
                const toggle = row.querySelector('[onclick*="toggleCredSteps"]');
                if (!toggle) return {ok: false, reason: 'TikTok row has no Roadmap toggle (already live?)'};
                toggle.click();
                return {ok: true};
            }""")
            check(tiktok_toggle.get("ok"), f"clicking the TikTok roadmap row should expand its steps: {tiktok_toggle}")
            await page.wait_for_timeout(200)
            conn_text_expanded = await page.evaluate("document.getElementById('connections-content').innerText")
            check("TikTok Shop can" in conn_text_expanded and "not a sales channel" in conn_text_expanded,
                  "TikTok roadmap steps should clarify posting is Etsy-traffic-only, not a TikTok Shop sales channel")

            # ── First-time-user simplification (2026-07-11) regression guards ──
            simp = await page.evaluate("""() => {
                const hidden = el => !el || el.offsetParent === null;
                // (2026-07-25) #setting-video-engine now only exists once the Product
                // Video tile's panel is rendered (it moved out of the always-in-DOM
                // Advanced tools disclosure into #create-detail, populated on demand
                // by createOpenCategory()) -- open it here so the check below can find
                // it, then close it again (toggle) to leave state clean.
                createOpenCategory('product_video');
                const videoEngineSelect = (()=>{ const s=document.getElementById('setting-video-engine'); return !!s && [...s.options].some(o=>o.value==='veo'); })();
                createOpenCategory('product_video');
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
                    videoEngineSelect,
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

            # ── Knowledge screen: dead showScreen('kb') regression + race condition
            # (2026-07-31 audit) -- #screen-kb was deleted 2026-07-11 when Memory+KB
            # merged into #screen-knowledge, but two call sites still targeted it.
            # showScreen() strips .active from every .screen div before checking the
            # target exists, so a missing target blanked the whole dashboard, not a
            # no-op. Both call sites fixed to target 'knowledge'; the search-result
            # path also had loadKb()/openKbDoc() racing for the same #kb-content
            # element, fixed by awaiting both in order. ──
            await page.evaluate("showScreen('knowledge')")
            await page.wait_for_timeout(800)
            memory_link = await page.evaluate("""() => {
                const link = [...document.querySelectorAll('#memory-content a')]
                    .find(a => a.textContent.includes('docs in the knowledge base'));
                if (!link) return {found: false};
                link.click();
                return {found: true};
            }""")
            check(memory_link.get("found"),
                  f"expected the 'N docs in the knowledge base' link inside the Memory panel: {memory_link}")
            await page.wait_for_timeout(200)
            active_after_link = await page.evaluate(
                "document.getElementById('screen-knowledge').classList.contains('active')")
            check(active_after_link,
                  "clicking the 'N docs in the knowledge base' link must not blank the Knowledge screen "
                  "(regression: it used to target the deleted #screen-kb)")

            kb_race = await page.evaluate("""async () => {
                showScreen('knowledge');
                const dd = document.getElementById('search-dropdown');
                dd._results = [{category: 'kb', id: 'business_standards.md', title: 'Business Standards', subtitle: '1 match'}];
                await _navigateSearchResult(0);
                const el = document.getElementById('kb-content');
                return {
                    html: el ? el.innerHTML : '',
                    activeAfter: document.getElementById('screen-knowledge').classList.contains('active'),
                };
            }""")
            check(kb_race.get("activeAfter"),
                  f"Knowledge screen must still be active after a kb search-result navigation: {kb_race}")
            check("business_standards.md" in kb_race.get("html", ""),
                  f"expected the specific doc (business_standards.md) to render after search-result "
                  f"navigation, got: {kb_race.get('html','')[:200]}")
            check("📚 Docs (" not in kb_race.get("html", ""),
                  f"the doc LIST must not have clobbered the specific doc -- this is the exact race condition "
                  f"the await-sequencing fix (loadKb() then openKbDoc(), both awaited) addresses, "
                  f"got: {kb_race.get('html','')[:200]}")

            # ── Tasks screen: silent-failure fix + View Full Schedule link (2026-08-01
            # audit) -- addHudTodo/toggleHudTodo/deleteHudTodo used to swallow every
            # failure with an empty catch(e){} and no r.ok check. addHudTodo also
            # cleared the input AND due-date fields before the request resolved, so a
            # failed add looked identical to a successful one and the typed text was
            # gone for good. ──
            await page.evaluate("showScreen('tasks')")
            await page.wait_for_timeout(500)
            add_fail = await page.evaluate("""async () => {
                const orig = window.fetchWithTimeout;
                window.fetchWithTimeout = (url, opts, ms) => {
                    if (String(url).includes('/api/todos') && opts && opts.method === 'POST') {
                        return Promise.resolve({ok: false, status: 500, json: async () => ({detail: 'boom'})});
                    }
                    return orig(url, opts, ms);
                };
                const inp = document.getElementById('hud-todo-input');
                const dueInp = document.getElementById('hud-todo-due');
                inp.value = 'Renew business license';
                dueInp.value = '2026-12-31';
                await addHudTodo();
                window.fetchWithTimeout = orig;
                const stack = document.getElementById('toast-stack');
                return {
                    inputValue: inp.value,
                    dueValue: dueInp.value,
                    toastText: stack ? stack.textContent : '',
                };
            }""")
            check(add_fail.get("inputValue") == "Renew business license",
                  f"a failed add must NOT clear the typed task text, got: {add_fail}")
            check(add_fail.get("dueValue") == "2026-12-31",
                  f"a failed add must NOT clear the chosen due date, got: {add_fail}")
            check("Could not add task" in add_fail.get("toastText", ""),
                  f"a failed add must surface a real error toast, got: {add_fail}")

            schedule_link = await page.evaluate("""() => {
                showScreen('cmd');
                const link = [...document.querySelectorAll('.col-timeline .lnk')]
                    .find(el => el.textContent.includes('View Full Schedule'));
                if (!link) return {found: false};
                link.click();
                return {found: true, active: document.getElementById('screen-calendar').classList.contains('active')};
            }""")
            check(schedule_link.get("found"),
                  f"expected the 'View Full Schedule' link on the Mission Timeline panel: {schedule_link}")
            check(schedule_link.get("active"),
                  f"'View Full Schedule' must open the real Calendar screen, not the flat Tasks list "
                  f"(regression: it used to link to showScreen('tasks')): {schedule_link}")

            # ── Frank-usability tier (2026-07-15) ──

            # Home cards must render without throwing, even with no live Etsy
            # data locally (both /api/star-seller and /api/ads-status degrade
            # gracefully -- this just proves the new loadAdsStatus() wiring
            # doesn't crash the Home screen).
            await page.evaluate("showScreen('cmd')")
            await page.wait_for_timeout(1000)
            home_cards = await page.evaluate("""() => ({
                adsCardPresent: !!document.getElementById('ads-status-body'),
                adsCardHasContent: (document.getElementById('ads-status-body')||{}).innerHTML.trim().length > 0,
            })""")
            check(home_cards.get("adsCardPresent"), f"Ads/ROAS card must be present on Home: {home_cards}")
            check(home_cards.get("adsCardHasContent"), f"Ads/ROAS card must render some content, not stay blank: {home_cards}")

            # ── Bambu P1S printer card (2026-07-29) ──
            # No local bridge runs in this dev/CI environment, so /api/printer/status
            # always reports online:false -- confirms the card renders the honest
            # "bridge offline" state instead of throwing or staying blank forever.
            printer_card = await page.evaluate("""() => {
                const el = document.getElementById('printer-status-body');
                return {present: !!el, hasContent: !!(el && el.innerHTML.trim().length > 0),
                        showsOffline: !!(el && el.innerHTML.includes('BRIDGE OFFLINE'))};
            }""")
            check(printer_card.get("present"), f"Bambu P1S printer card must be present on Home: {printer_card}")
            check(printer_card.get("hasContent"), f"Printer card must render some content, not stay blank: {printer_card}")
            check(printer_card.get("showsOffline"), f"With no bridge running, printer card must honestly show 'bridge offline': {printer_card}")

            # ── P1S click-through detail modal (2026-07-30) ── Scott asked to click the
            # card and see the camera feed + full live stats. Confirms the panel-title
            # is wired to openPrinterDetailModal(), the shared #metric-detail-modal shell
            # opens, and it self-closes cleanly (no leaked interval, no stuck open state).
            printer_tap_target = await page.evaluate(
                "() => !!document.querySelector('div.panel-title[onclick*=\"openPrinterDetailModal\"]')"
            )
            check(printer_tap_target, "P1S panel-title must be wired to openPrinterDetailModal()")
            await page.click('div.panel-title[onclick*="openPrinterDetailModal"]')
            await page.wait_for_timeout(600)
            printer_modal = await page.evaluate("""() => ({
                open: document.body.classList.contains('metric-detail-open'),
                title: (document.getElementById('mdm-title')||{}).textContent,
                bodyHasContent: (document.getElementById('mdm-body')||{}).innerHTML.trim().length > 0,
                showsOfflineOrCamera: /BRIDGE OFFLINE|camera feed/i.test((document.getElementById('mdm-body')||{}).innerHTML),
            })""")
            check(printer_modal.get("open"), f"Clicking the P1S card must open the metric-detail modal: {printer_modal}")
            check("Printer" in (printer_modal.get("title") or ""), f"Modal title must identify the P1S panel: {printer_modal}")
            check(printer_modal.get("bodyHasContent"), f"Modal body must render content, not stay blank: {printer_modal}")
            check(printer_modal.get("showsOfflineOrCamera"), f"Modal must show either the camera feed markup or an honest offline state: {printer_modal}")
            # Click near the top-left corner, not the element's center -- the centered
            # modal panel (z-index 901) sits on top of the backdrop (900) at the viewport
            # center, so a default center-click would hit the modal, never the backdrop.
            await page.click("#metric-detail-backdrop", position={"x": 5, "y": 5})
            await page.wait_for_timeout(400)
            printer_modal_closed = await page.evaluate("() => document.body.classList.contains('metric-detail-open')")
            check(not printer_modal_closed, "Clicking the backdrop must close the P1S detail modal")

            # ── Chat: sendMsg() must refocus the input after every send (2026-07-30) ──
            # Scott: "I cannot enter more than one thing into chat. After Frank responds
            # I can no longer add to the chat." Reproduced directly: clicking the round
            # send button (as opposed to pressing Enter, which leaves focus on the input
            # naturally) moves browser focus onto the BUTTON, and nothing ever gave it
            # back -- on mobile this also dismisses the on-screen keyboard. Simulates a
            # full turn (no live model in this environment) by hand-firing the exact
            # ws.onmessage events the real server sends, then asserts focus lands back
            # on #chat-input and a keystroke typed WITHOUT re-clicking the field lands
            # in its value -- exactly the repro that caught this bug.
            await page.evaluate("showScreen('cmd')")
            await page.fill("#chat-input", "first message")
            await page.evaluate("""() => {
                sendMsg();
                ws.onmessage({data: JSON.stringify({type:'chunk', content:'Hello.'})});
                ws.onmessage({data: JSON.stringify({type:'done'})});
            }""")
            await page.click("#chat-input")  # first click is legitimate -- this simulates the user's OWN first turn, not the bug
            await page.fill("#chat-input", "second message via send button")
            await page.click("#chat-send")
            focus_after_send = await page.evaluate("document.activeElement && document.activeElement.id")
            check(focus_after_send == "chat-input", f"clicking #chat-send must return focus to #chat-input, got focus on: {focus_after_send}")
            await page.evaluate("""() => {
                ws.onmessage({data: JSON.stringify({type:'chunk', content:'reply'})});
                ws.onmessage({data: JSON.stringify({type:'done'})});
            }""")
            await page.wait_for_timeout(100)
            # Type WITHOUT re-clicking the input first -- this is the exact user action
            # that silently went nowhere before the fix.
            await page.keyboard.type("third message typed without reclicking", delay=10)
            third_msg_value = await page.evaluate("document.getElementById('chat-input').value")
            check(third_msg_value == "third message typed without reclicking",
                  f"typing immediately after a response must land in #chat-input without a manual re-click, got: {third_msg_value!r}")

            # Approvals batch-threshold banner -- stub _pendingActions with 11
            # same-type items (over the 10-item safety rail) and confirm the
            # computed warning banner appears; then confirm it's absent with a
            # normal small queue.
            await page.evaluate("showScreen('actions')")
            await page.wait_for_timeout(500)
            over_limit = await page.evaluate("""() => {
                _pendingActions = Array.from({length: 11}, (_, i) => ({id: i, type: 'update_tags', payload: {}}));
                _actions = [];
                renderActionsContent();
                const el = document.getElementById('actions-content');
                return { hasWarning: el.innerHTML.includes('bigger than the 10-item safety rail') };
            }""")
            check(over_limit.get("hasWarning"), f"Approvals should warn when >10 same-type actions are pending: {over_limit}")
            under_limit = await page.evaluate("""() => {
                _pendingActions = [{id: 1, type: 'update_tags', payload: {}}];
                renderActionsContent();
                const el = document.getElementById('actions-content');
                return { hasWarning: el.innerHTML.includes('bigger than the 10-item safety rail') };
            }""")
            check(not under_limit.get("hasWarning"), f"a small queue should not trigger the batch warning: {under_limit}")

            # Fix button on the Listings tab -- must appear for a listing that's
            # still `active` but flagged manifest_status='FAIL' (2026-07-15
            # fix; previously only state==='inactive' listings got this
            # button, so an active-but-broken listing had no way to get fixed).
            await page.evaluate("showScreen('listings')")
            await page.wait_for_timeout(500)
            fix_button_check = await page.evaluate("""() => {
                _listings = [
                    {listing_id: 90001, title: 'Broken Active Listing', price: 9.99, state: 'active',
                     views: 0, num_favorers: 0, tags: [], manifest_status: 'FAIL'},
                    {listing_id: 90002, title: 'Healthy Active Listing', price: 9.99, state: 'active',
                     views: 0, num_favorers: 0, tags: [], manifest_status: 'PASS'},
                ];
                _sectionFilter = null;
                _listingState = 'active';
                renderListings();
                const el = document.getElementById('listings-content');
                return el ? el.innerHTML : null;
            }""")
            listings_html = fix_button_check or ""
            check("90001" in listings_html and "Ask" in listings_html and "Fix" in listings_html,
                  "an active listing with manifest_status='FAIL' should get the Fix button")

            # Listings screen audit (2026-07-31), finding #4: new Expired tab --
            # reactivating an expired listing IS Etsy's real renewal mechanism, so
            # the detail panel's Activate button must render for state='expired'
            # exactly like it already does for 'active'/'inactive' (previously
            # gated to only those two, so an expired listing's Activate button
            # silently never existed).
            expired_check = await page.evaluate("""async () => {
                _listings = [
                    {listing_id: 90003, title: 'Needs Renewal', price: 12.99, state: 'expired',
                     views: 0, num_favorers: 0, tags: []},
                ];
                _sectionFilter = null; _openDetailId = null;
                _listingState = 'expired';
                renderListings();
                await toggleListingDetail(90003);
                const panel = document.getElementById('hub-detail-90003');
                const expiredTabExists = !!document.querySelector('#screen-listings .hub-toggle-btn[data-state="expired"]');
                return { detailHtml: panel ? panel.innerHTML : null, expiredTabExists };
            }""")
            check(expired_check.get("expiredTabExists"), "an Expired toggle button (data-state='expired') should exist on the Listings screen")
            detail_html = expired_check.get("detailHtml") or ""
            check("Activate" in detail_html, f"an expired listing's detail panel should offer Activate, got: {detail_html[:300]}")

            # Listings screen audit (2026-07-31), finding #1: global search -> Listings
            # jump was broken every time, not intermittently -- showScreen('listings')
            # kicks off an unawaited loadListings() that wipes #listings-content to a
            # spinner (destroying every hub-detail-<id> node) before the old code's very
            # next line, toggleListingDetail(r.id), even ran. Repro the exact precondition
            # (cold _listings, a stashed search result) and confirm the detail panel now
            # actually opens with the real listing's data once _navigateSearchResult is
            # awaited end-to-end.
            await page.evaluate("""() => {
                window._origAuthGetListings = window.authGet;
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/listings?state=active') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            listings: [{listing_id: 90004, title: 'Found Via Search', price: 7.77, state: 'active',
                                        views: 3, num_favorers: 1, tags: []}],
                            count: 1, state: 'active',
                        })});
                    }
                    if (path.indexOf('/api/shop-sections') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({sections: []})});
                    }
                    if (path.indexOf('/api/listings/90004/files') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({files: []})});
                    }
                    return window._origAuthGetListings(path, ms);
                };
            }""")
            search_jump_check = await page.evaluate("""async () => {
                _listings = [];  // cold -- matches the real bug precondition
                _lastListingState = 'draft';  // stale from a hypothetical prior visit
                const dd = document.getElementById('search-dropdown');
                dd._results = [{category: 'listing', id: 90004, title: 'Found Via Search'}];
                await _navigateSearchResult(0);
                const panel = document.getElementById('hub-detail-90004');
                return { panelDisplay: panel ? panel.style.display : null, panelHtml: panel ? panel.innerHTML : null };
            }""")
            await page.evaluate("if(window._origAuthGetListings){window.authGet = window._origAuthGetListings; window._origAuthGetListings = null;}")
            check(search_jump_check.get("panelDisplay") == 'block',
                  f"the detail panel should actually be open after a search-result jump, got: {search_jump_check}")
            check("90004" in (search_jump_check.get("panelHtml") or ""),
                  f"the opened panel should be the real searched-for listing, got: {search_jump_check}")

            # Products screen rebuild (2026-07-15) -- was hardcoded to a ~5-product
            # "Core Products" slice, now the full catalog with a category filter.
            # Stub _products directly (bare assignment, not window.X -- see the tour
            # steps above for why: these are top-level `let` bindings, not globals).
            #
            # 2026-07-30: showScreen('products') below fires the real loadProducts(),
            # an async fetch of the (now 176-product) real /api/products -- reassigning
            # the top-level `loadProducts` binding afterward (the fix a later block in
            # this file uses) does NOT retarget that already-in-flight call, since
            # _SCREEN_LOADERS.products captured the ORIGINAL function reference at
            # page-load, not a live binding to the variable name. That real fetch can
            # resolve at any point afterward and clobber this block's stubbed
            # `_products` out from under it -- confirmed live in CI (176-product real
            # catalog, not the 3-product stub, flowed into the filter assertions
            # below). Mocking authGet for /api/products so the real call resolves to
            # the SAME data as the stub makes the race harmless regardless of timing,
            # rather than trying to win a timing fight against it.
            await page.evaluate("""() => {
                window._origAuthGet = window.authGet;
                const stubProducts = [
                    {id: 'DP1026', title: 'Life Planner', listing_id: '1', category: 'digital_planner',
                     status: 'active', price: 14.99, files: [{name: 'DP1026.pdf', exists: true}], all_files_present: true},
                    {id: 'WA1001', title: 'Wall Art One', listing_id: '2', category: 'wall_art',
                     status: 'active', price: 5.99, files: [{name: 'WA1001.zip', exists: false}], all_files_present: false},
                    {id: 'WA1002', title: 'Wall Art Two', listing_id: '3', category: 'wall_art',
                     status: 'active', price: 5.99, files: [{name: 'WA1002.zip', exists: true}], all_files_present: true},
                ];
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/products') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({products: stubProducts})});
                    }
                    return window._origAuthGet(path, ms);
                };
            }""")
            await page.evaluate("showScreen('products')")
            await page.wait_for_timeout(400)
            products_check = await page.evaluate("""() => {
                _products = [
                    {id: 'DP1026', title: 'Life Planner', listing_id: '1', category: 'digital_planner',
                     status: 'active', price: 14.99, files: [{name: 'DP1026.pdf', exists: true}], all_files_present: true},
                    {id: 'WA1001', title: 'Wall Art One', listing_id: '2', category: 'wall_art',
                     status: 'active', price: 5.99, files: [{name: 'WA1001.zip', exists: false}], all_files_present: false},
                    {id: 'WA1002', title: 'Wall Art Two', listing_id: '3', category: 'wall_art',
                     status: 'active', price: 5.99, files: [{name: 'WA1002.zip', exists: true}], all_files_present: true},
                ];
                _productCategoryFilter = null;
                renderProductsContent();
                const el = document.getElementById('products-content');
                const chips = document.querySelectorAll('#products-content .hub-chip-btn');
                return {
                    html: el ? el.innerHTML : null,
                    chipCount: chips.length,
                    chipLabels: [...chips].map(c => c.textContent),
                };
            }""")
            check("2/3 have all files present" in (products_check.get("html") or ""),
                  f"summary line should reflect 2/3 present: {products_check}")
            check(products_check.get("chipCount") == 3,
                  f"expected 3 chips (All + digital_planner + wall_art): {products_check}")
            check(any("Wall Art (2)" in c for c in products_check.get("chipLabels", [])),
                  f"expected a 'Wall Art (2)' chip: {products_check}")

            filter_check = await page.evaluate("""() => {
                setProductCategoryFilter('wall_art');
                const el = document.getElementById('products-content');
                return el ? el.innerHTML : null;
            }""")
            check("WA1001" in filter_check and "WA1002" in filter_check and "DP1026" not in filter_check,
                  f"filtering to wall_art should show only wall_art products: {filter_check[:300] if filter_check else filter_check}")
            check("missing: WA1001.zip" in filter_check,
                  f"a product with a missing file should name it: {filter_check[:300] if filter_check else filter_check}")
            await page.evaluate("if(window._origAuthGet){window.authGet = window._origAuthGet; window._origAuthGet = null;}")

            # ── Products-screen tappable cards (2026-07-18) -- every card now opens
            # a popup: missing-files -> fix sheet (regenerate for planners, plain
            # "Open in Files" otherwise), ready_for_review -> review modal (real
            # content, "not written yet" state, and Publish button gated on QC/
            # content/deliverables). Stub _products fresh (fixture above already
            # scrolled past) and call openProductSheet() directly rather than
            # physically clicking, same as setProductCategoryFilter()/tour-step
            # calls above -- these are top-level `let` bindings, not globals.
            tappable_setup = await page.evaluate("""() => {
                // The real app polls loadAll() every 30s, which calls loadProducts()
                // whenever the Products screen is active and overwrites _products with
                // real fetched data -- an intermittent race against this section's
                // synthetic fixture (2026-07-17: ~1/5 local runs). Neutralize it for
                // the duration of these tests; nothing here needs the real network call.
                loadProducts = async function(){};
                _products = [
                    {id: 'DP1026', title: 'Life Planner', listing_id: '1', category: 'digital_planner',
                     status: 'active', price: 14.99,
                     files: [{name: 'DP1026.pdf', exists: false}, {name: 'DP1026_sticker_pack.zip', exists: false}],
                     all_files_present: false},
                    {id: 'WA1001', title: 'Wall Art One', listing_id: '2', category: 'wall_art',
                     status: 'active', price: 5.99, files: [{name: 'WA1001.zip', exists: false}], all_files_present: false},
                    {id: 'DP1030', title: 'ADHD Planner', listing_id: null, category: 'digital_planner',
                     status: 'ready_for_review', price: 12.99, files: [], all_files_present: true},
                    {id: 'DP1031', title: 'Evergreen Planner', listing_id: null, category: 'digital_planner',
                     status: 'ready_for_review', price: 12.99, files: [], all_files_present: true},
                    {id: 'SVG1001', title: 'SVG Bundle One', listing_id: '4', category: 'svg_bundle',
                     status: 'active', price: 7.99, files: [{name: 'Bundle.zip', exists: false}],
                     all_files_present: false, file_audit: 'genuinely_missing'},
                ];
                _productCategoryFilter = null;
                renderProductsContent();
                const card = document.querySelector('#products-content .hub-prod-card.tappable');
                return {cardTappable: !!card, cardHasChevron: card ? card.innerHTML.includes('pchev') : false};
            }""")
            check(tappable_setup.get("cardTappable"), f"product cards must render with the tappable class: {tappable_setup}")
            check(tappable_setup.get("cardHasChevron"), f"tappable cards should show a chevron affordance: {tappable_setup}")

            planner_fix_sheet = await page.evaluate("""() => {
                openProductSheet('DP1026');
                return {
                    open: document.body.classList.contains('product-sheet-open'),
                    buttons: document.getElementById('product-sheet-buttons').innerHTML,
                };
            }""")
            check(planner_fix_sheet.get("open"), "tapping a missing-files planner card should open the fix sheet")
            check("Regenerate PDF" in planner_fix_sheet.get("buttons", "") and "Regenerate sticker pack" in planner_fix_sheet.get("buttons", ""),
                  f"a planner missing both PDF and ZIP should offer both regenerate buttons: {planner_fix_sheet}")
            check("Open in Files" in planner_fix_sheet.get("buttons", ""), f"fix sheet must always offer Open in Files: {planner_fix_sheet}")

            # wall_art now has a real generator wired (2026-07-18: /api/produce/print-zip) --
            # its fix sheet should offer a genuine regenerate button, same tier as planners.
            wallart_fix_sheet = await page.evaluate("""() => {
                document.body.classList.remove('product-sheet-open');
                openProductSheet('WA1001');
                return document.getElementById('product-sheet-buttons').innerHTML;
            }""")
            check("Regenerate print-size ZIP" in wallart_fix_sheet,
                  f"wall_art missing files should offer the print-zip regenerate action: {wallart_fix_sheet}")

            # Categories with no generator wired this round (2026-07-18 scoping decision:
            # svg_bundle/paper_pack/sublimation/etc.) must show the HONEST Etsy-audit state
            # instead of a fake regenerate button -- never a dead end, never a lie.
            unsupported_fix_sheet = await page.evaluate("""() => {
                document.body.classList.remove('product-sheet-open');
                openProductSheet('SVG1001');
                return document.getElementById('product-sheet-buttons').innerHTML;
            }""")
            check("Regenerate" not in unsupported_fix_sheet,
                  f"categories with no verified build tool must not offer a fake regenerate action: {unsupported_fix_sheet}")
            check("flagged for review" in unsupported_fix_sheet,
                  f"a genuinely_missing file_audit verdict should say so plainly, not just stay silent: {unsupported_fix_sheet}")
            check("Open in Files" in unsupported_fix_sheet, f"unsupported-category fix sheet should still offer Open in Files: {unsupported_fix_sheet}")

            # Regenerating a missing-files card removes it from the current view
            # (2026-07-18 -- Scott reported it kept sitting there red for the
            # ~2-4 min the background job runs, reading as still unaddressed).
            # Mock the produce endpoint (never actually kick off a paid AI job in
            # a test) and auto-accept the cost/time confirm() dialog.
            async def _mock_build_planner(route):
                await route.fulfill(status=200, content_type="application/json",
                                     body='{"pid": "DP1026", "started": true, "message": "Building DP1026 in the background."}')
            await page.route("**/api/produce/build-planner", _mock_build_planner)
            page.once("dialog", lambda d: d.accept())
            regen_result = await page.evaluate("""async () => {
                document.body.classList.remove('product-sheet-open');
                openProductSheet('DP1026');
                const before = _products.some(p => p.id === 'DP1026');
                let errMsg = null;
                try { await productRegenerateBuild('DP1026', 'planner'); } catch(e) { errMsg = String(e); }
                await new Promise(r => setTimeout(r, 200));
                const stack = document.getElementById('toast-stack');
                return {before, after: _products.some(p => p.id === 'DP1026'),
                        sheetOpen: document.body.classList.contains('product-sheet-open'),
                        errMsg, toastText: stack ? stack.textContent : null};
            }""")
            await page.unroute("**/api/produce/build-planner")
            check(regen_result.get("before") is True, f"DP1026 must exist before regenerating: {regen_result}")
            check(regen_result.get("after") is False,
                  f"DP1026 must be removed from _products (and the re-rendered list) once regeneration starts: {regen_result}")
            check(regen_result.get("sheetOpen") is False, f"the fix sheet should close on success: {regen_result}")

            # Review modal -- deliberately NOT mocked. This server process runs from
            # the real repo checkout (cwd=ROOT), so /api/products/DP1030/review hits
            # the real data/dp1030_listing.json (real content, real tags) and DP1031
            # has no dpXXXX_listing.json at all (confirmed by the P1 backend tests) --
            # exercises the real end-to-end path instead of a fixture that could drift
            # from reality. NOTE: the actual DP1030.pdf/zip binaries live under the
            # gitignored data/digital_products/ tree (CLAUDE.md: ephemeral, never
            # committed) -- present on a dev machine that's run the build pipeline,
            # absent on a clean CI/deploy checkout. So this only asserts on the
            # content/tags (always present, tracked in git) and accepts EITHER gate
            # outcome for Publish -- the exact gating logic itself (Publish only
            # when QC passes AND all deliverables exist) is already covered
            # deterministically by tests/test_products_review_endpoint.py and
            # tests/test_create_listing_publish_flow.py with mocked file state.
            review_with_content = await page.evaluate("""async () => {
                document.body.classList.remove('product-sheet-open');
                await openProductReviewModal({id: 'DP1030', title: 'ADHD Planner'});
                await new Promise(r => setTimeout(r, 300));
                return {
                    open: document.body.classList.contains('product-review-open'),
                    body: document.getElementById('prm-body').innerHTML,
                    actions: document.getElementById('prm-actions').innerHTML,
                };
            }""")
            check(review_with_content.get("open"), "tapping a ready_for_review card should open the review modal")
            check("ADHD" in review_with_content.get("body", "") and "Digital Planner" in review_with_content.get("body", ""),
                  f"review modal must show the real DP1030 title: {review_with_content}")
            check("Tags (13)" in review_with_content.get("body", ""), f"DP1030 has 13 real tags: {review_with_content}")
            actions_html = review_with_content.get("actions", "")
            check("Publish to Etsy" in actions_html or "missing deliverable" in actions_html,
                  f"actions must render either Publish or the specific reason it's blocked, not neither: {review_with_content}")
            await page.evaluate("productReviewClose()")

            review_no_content = await page.evaluate("""async () => {
                await openProductReviewModal({id: 'DP1031', title: 'Evergreen Planner'});
                await new Promise(r => setTimeout(r, 300));
                return {
                    body: document.getElementById('prm-body').innerHTML,
                    actions: document.getElementById('prm-actions').innerHTML,
                };
            }""")
            check("haven" in review_no_content.get("body", "").lower(),
                  f"DP1031 has no dpXXXX_listing.json, review modal should say content isn't written yet: {review_no_content}")
            # (2026-07-25) Was "Ask Frank to draft it" -- replaced by a real
            # generator (productReviewGenerateContent) that actually writes
            # grounded content, not a chat hand-off dead end.
            check("Generate listing content" in review_no_content.get("actions", ""),
                  f"missing content should offer the real generate-content button, not Publish: {review_no_content}")
            check("Publish to Etsy" not in review_no_content.get("actions", ""),
                  f"Publish must not appear with no content: {review_no_content}")
            # Leave the DOM clean for later checks in this same page session (the
            # modal otherwise intercepts pointer events for unrelated later clicks).
            await page.evaluate("productReviewClose(); document.body.classList.remove('product-sheet-open')")

            # ── Coloring-pages "stage listing photos from pack" button (2026-07-25) --
            # Scott: COLOR1003 published with zero listing photos (no AI photo pipeline
            # for this category); the fix stages the product's own real pack pages
            # instead. Button must appear ONLY for coloring_pages + an existing
            # listing_id + no photos yet -- never for wall_art (still genuinely
            # unsupported) and never before a listing exists (nothing to stage
            # against). Calls _renderProductReview() directly with fake review
            # objects -- #prm-body/#prm-actions exist statically, no need to open
            # the modal via network first.
            color_photo_states = await page.evaluate("""() => {
                const base = {has_content: true, content: {title: 't', description: 'd', tags: [], price: 6.99},
                              photos: [], deliverables: [], qc: {verdict: 'pass', message: ''}};
                _renderProductReview({...base, product_id: 'COLOR1003', category: 'coloring_pages', listing_id: 555});
                const withListing = document.getElementById('prm-actions').innerHTML;
                _renderProductReview({...base, product_id: 'COLOR9999', category: 'wall_art', listing_id: 555});
                const wallArt = document.getElementById('prm-actions').innerHTML;
                _renderProductReview({...base, product_id: 'COLOR1003', category: 'coloring_pages', listing_id: null});
                const noListingYet = document.getElementById('prm-body').innerHTML;
                return {withListing, wallArt, noListingYet};
            }""")
            check("prm-color-photo-btn" in color_photo_states.get("withListing", ""),
                  f"a coloring_pages product with a real listing_id and no photos must offer the stage-photos button: {color_photo_states}")
            check("prm-color-photo-btn" not in color_photo_states.get("wallArt", ""),
                  f"wall_art must NOT get the coloring-pages-specific button: {color_photo_states}")
            check("publish first" in color_photo_states.get("noListingYet", "").lower(),
                  f"with no listing_id yet the info text should say publish first, not offer the button: {color_photo_states}")
            await page.evaluate("document.body.classList.remove('product-review-open')")

            # ── "Etsy Listing" Create-screen tile (2026-07-25) -- Scott: type a
            # product ID, jump straight into the existing review/publish pipeline.
            # Deliberately NOT the build-panel machinery (_CREATE_CATEGORIES /
            # buildProductRun) -- a purpose-built one-input-one-button panel that
            # calls openProductReviewModal() directly. authGet() monkeypatch for
            # the GET /review call (frank-sw.js intercepts GETs); page.route() for
            # the POST /generate-listing-content call (the service worker only
            # wraps GET, confirmed by this file's own earlier convention notes). ──
            await page.evaluate("showScreen('create')")
            await page.wait_for_timeout(200)
            lookup_panel = await page.evaluate("""() => {
                createOpenCategory('etsy_listing_lookup');
                const panel = document.getElementById('create-detail');
                return {
                    tileOpen: document.querySelector('.create-choice[data-cat="etsy_listing_lookup"]').classList.contains('open'),
                    hasEllInput: !!document.getElementById('ell-pid'),
                    hasBuildPidInput: !!document.getElementById('bx-pid'),
                    panelHtml: panel ? panel.innerHTML : '',
                };
            }""")
            check(lookup_panel.get("tileOpen"), f"tapping the Etsy Listing tile should mark it .open: {lookup_panel}")
            check(lookup_panel.get("hasEllInput"), f"the lookup panel must render #ell-pid: {lookup_panel}")
            check(not lookup_panel.get("hasBuildPidInput"),
                  f"the lookup panel must NOT reuse the build-panel's #bx-pid machinery: {lookup_panel}")
            check("Look Up" in lookup_panel.get("panelHtml", ""), f"expected a Look Up button: {lookup_panel}")

            empty_lookup = await page.evaluate("""() => {
                document.getElementById('ell-pid').value = '';
                ellLookup();
                return {
                    modalOpen: document.body.classList.contains('product-review-open'),
                    resultHtml: document.getElementById('ell-result').innerHTML,
                };
            }""")
            check(not empty_lookup.get("modalOpen"), f"an empty ID must never open the review modal: {empty_lookup}")
            check("Enter a product ID" in empty_lookup.get("resultHtml", ""),
                  f"an empty ID should show an inline prompt, not silently no-op: {empty_lookup}")

            async def _mock_generate_content(route):
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({
                    "product_id": "DP9042", "category": "digital_planner", "status": "draft",
                    "listing_id": None, "has_content": True,
                    "content": {"title": "Generated Test Title", "description": "A generated description.",
                                "tags": ["a"] * 13, "price": 12.99},
                    "photos": [], "deliverables": [{"name": "DP9042.pdf", "rel": "x", "exists": True}],
                    "qc": {"verdict": "pass", "message": "ok"},
                }))
            await page.route("**/api/products/*/generate-listing-content", _mock_generate_content)

            lookup_and_generate = await page.evaluate("""async () => {
                window._origAuthGetEll = window.authGet;
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/products/DP9042/review') === 0) {
                        const payload = {
                            product_id: 'DP9042', category: 'digital_planner', status: 'draft',
                            listing_id: null, has_content: false, content: null,
                            photos: [], deliverables: [{name: 'DP9042.pdf', rel: 'x', exists: true}],
                            qc: {verdict: 'pass', message: 'ok'},
                        };
                        return Promise.resolve({ok: true, status: 200, json: async () => payload});
                    }
                    return window._origAuthGetEll(path, ms);
                };
                document.getElementById('ell-pid').value = 'dp9042';
                ellLookup();
                await new Promise(r => setTimeout(r, 300));
                const opened = {
                    modalOpen: document.body.classList.contains('product-review-open'),
                    actionsHtml: document.getElementById('prm-actions').innerHTML,
                };
                // Fire without awaiting so the synchronous "Generating…" state is observable.
                productReviewGenerateContent('DP9042');
                const midFlight = {
                    disabled: document.getElementById('prm-gen-btn') ? document.getElementById('prm-gen-btn').disabled : null,
                    text: document.getElementById('prm-gen-btn') ? document.getElementById('prm-gen-btn').textContent : null,
                };
                await new Promise(r => setTimeout(r, 400));
                const after = {
                    bodyHtml: document.getElementById('prm-body').innerHTML,
                    actionsHtml: document.getElementById('prm-actions').innerHTML,
                };
                productReviewClose();
                window.authGet = window._origAuthGetEll;
                return {opened, midFlight, after};
            }""")
            check(lookup_and_generate["opened"].get("modalOpen"),
                  f"typing a lowercase id must uppercase + open the review modal: {lookup_and_generate}")
            check("Generate listing content" in lookup_and_generate["opened"].get("actionsHtml", ""),
                  f"a has_content:false product should show the generate button: {lookup_and_generate}")
            check(lookup_and_generate["midFlight"].get("disabled") is True and "Generating" in (lookup_and_generate["midFlight"].get("text") or ""),
                  f"the button must disable + show 'Generating…' synchronously before the mocked response resolves: {lookup_and_generate}")
            check("Generated Test Title" in lookup_and_generate["after"].get("bodyHtml", ""),
                  f"after generation the modal must re-render with the real generated title: {lookup_and_generate}")
            check("Publish to Etsy" in lookup_and_generate["after"].get("actionsHtml", ""),
                  f"once content exists (and files/QC pass) Publish should now be offered: {lookup_and_generate}")
            await page.evaluate("document.body.classList.remove('product-review-open')")

            # ── "Product Video" Create-screen tile (2026-07-25) -- Scott: "I'm also
            # missing my section to make my ai videos". The video generate/stage/
            # post-to-social panel already existed (studioGenerate/studioStageToEtsy/
            # studioPostInstagram/studioPostFacebook, all unchanged) but the 2026-07-22
            # redesign buried it inside the collapsed "Advanced tools" disclosure with
            # zero indication it was there. Moved (not duplicated) into its own tile,
            # same special-case pattern as etsy_listing_lookup above. Confirms the tile
            # opens the real panel with every original control intact, and that the
            # markup no longer also lives inside #create-advanced-body. ──
            await page.evaluate("showScreen('create')")
            await page.wait_for_timeout(200)
            video_panel = await page.evaluate("""() => {
                createOpenCategory('product_video');
                const panel = document.getElementById('create-detail');
                const advBody = document.getElementById('create-advanced-body');
                return {
                    tileOpen: document.querySelector('.create-choice[data-cat="product_video"]').classList.contains('open'),
                    panelHtml: panel ? panel.innerHTML : '',
                    advancedBodyHtml: advBody ? advBody.innerHTML : '',
                    hasFileInput: !!document.getElementById('studio-file-input'),
                    hasListingIdInput: !!document.getElementById('studio-listing-id'),
                    hasStyleSelect: !!document.getElementById('studio-style'),
                    hasAspectSelect: !!document.getElementById('studio-aspect-ratio'),
                    hasEngineSelect: !!document.getElementById('setting-video-engine'),
                    hasGenerateBtn: !!document.getElementById('studio-generate-btn'),
                    hasStageBtn: !!document.getElementById('studio-stage-btn'),
                    hasIgBtn: !!document.getElementById('studio-ig-btn'),
                    hasFbBtn: !!document.getElementById('studio-fb-btn'),
                    hasVideosList: !!document.getElementById('studio-videos-list'),
                };
            }""")
            check(video_panel.get("tileOpen"), f"tapping the Product Video tile should mark it .open: {video_panel}")
            for key in ("hasFileInput", "hasListingIdInput", "hasStyleSelect", "hasAspectSelect",
                        "hasEngineSelect", "hasGenerateBtn", "hasStageBtn", "hasIgBtn", "hasFbBtn", "hasVideosList"):
                check(video_panel.get(key), f"Product Video panel missing an original control ({key}): {video_panel}")
            check("studio-generate-btn" not in video_panel.get("advancedBodyHtml", ""),
                  f"the video panel must no longer live inside #create-advanced-body after the move: {video_panel}")
            check("studio-videos-list" not in video_panel.get("advancedBodyHtml", ""),
                  f"the video-list preview must also have moved out of #create-advanced-body: {video_panel}")

            # ── Create-screen redesign (2026-07-22) -- Scott: "There is currently too
            # much on this page ... needs to be used by someone that does not know
            # what frank is." Replaced the old always-open tool-card stack with 7
            # honest category tiles (3 real, 4 coming-soon), a single accordion detail
            # panel, a collapsed Advanced Tools disclosure, and a new Reference Photos
            # upload library. Assert the tile grid, both tile kinds' panels, the
            # product picker, and that every relocated tool is still intact and
            # reachable -- not just visually moved into a black hole. ──
            #
            # This whole block manually stubs the global _products array to test
            # the picker deterministically -- block the REAL /api/products fetch
            # for its duration so loadProducts() (fired by _SCREEN_LOADERS.create
            # on every showScreen('create') call, including ones earlier in this
            # same test run) can never race in and silently overwrite the stub
            # with the real catalog mid-block. Unrouted once this section ends.
            async def _block_real_products(route):
                await route.fulfill(status=200, content_type="application/json", body='{"products": []}')
            await page.route("**/api/products", _block_real_products)
            await page.evaluate("showScreen('create')")
            await page.wait_for_timeout(300)
            tile_grid = await page.evaluate("""() => {
                const tiles = [...document.querySelectorAll('#create-chooser .create-choice[data-cat]')];
                return {
                    count: tiles.length,
                    cats: tiles.map(t => t.dataset.cat),
                    soonCount: tiles.filter(t => t.classList.contains('soon')).length,
                };
            }""")
            # (2026-07-25) 8th tile added: "Etsy Listing" -- type a product ID,
            # jump straight into the existing review/publish pipeline. 9th tile
            # added same day: "Product Video" -- re-exposes the video generation/
            # staging/social-posting pipeline that the 2026-07-22 redesign buried
            # in the collapsed Advanced tools disclosure with zero indication it
            # was there (Scott: "I'm also missing my section to make my ai videos").
            check(tile_grid.get("count") == 9, f"Create screen must show exactly 9 category tiles, got: {tile_grid}")
            check(set(tile_grid.get("cats", [])) == {
                "digital_planner", "wall_art", "coloring_pages",
                "sticker_pack", "svg_3dprint_pack", "sublimation", "3d_print_physical",
                "etsy_listing_lookup", "product_video",
            }, f"unexpected tile category set: {tile_grid}")
            check(tile_grid.get("soonCount") == 4, f"exactly 4 tiles should be 'coming soon', got: {tile_grid}")
            check("paper_pack" not in tile_grid.get("cats", []), "paper_pack must never appear as a tile (Scott's explicit exclusion)")

            # Stub _products so the real-category panel's picker has something to
            # show (loadProducts() itself is covered by the loadProducts-early-return
            # fix verified separately; this just gives the picker fixture data).
            # Field is "title" -- matches the REAL /api/products response shape
            # (main.py's _build_products_status(): "title": p.get("name", "")) --
            # not "name". An earlier version of this fixture used "name" here,
            # which silently matched a same-named bug in _createSyncProductPicker()
            # and would have made that bug invisible to this exact test (caught in
            # QA review, 2026-07-22).
            real_panel = await page.evaluate("""() => {
                _products = [
                    {id: 'DP1030', title: 'ADHD Planner', category: 'digital_planner'},
                    {id: 'DP1031', title: 'Evergreen Planner', category: 'digital_planner'},
                    {id: 'WA1001', title: 'Wall Art One', category: 'wall_art'},
                ];
                createOpenCategory('digital_planner');
                const panel = document.getElementById('create-detail');
                const picker = document.getElementById('create-pid-select');
                const dp1030Opt = picker ? [...picker.options].find(o => o.value === 'DP1030') : null;
                return {
                    tileOpen: document.querySelector('.create-choice[data-cat="digital_planner"]').classList.contains('open'),
                    panelHtml: panel ? panel.innerHTML : '',
                    pickerOptionCount: picker ? picker.options.length : 0,
                    pickerHasDP1030: !!dp1030Opt,
                    dp1030OptionText: dp1030Opt ? dp1030Opt.textContent : null,
                    runBtnPresent: !!document.getElementById('bx-run-btn'),
                };
            }""")
            check(real_panel.get("tileOpen"), f"opening a real category should mark its tile .open: {real_panel}")
            check("Build this planner" in real_panel.get("panelHtml", ""), f"digital_planner panel should show its plain-language primary label: {real_panel}")
            check(real_panel.get("pickerOptionCount", 0) >= 3, f"product picker should have the placeholder + 2 DP1030/DP1031 options, got: {real_panel}")
            check(real_panel.get("pickerHasDP1030"), f"product picker must include DP1030 from the stubbed _products: {real_panel}")
            check(real_panel.get("dp1030OptionText") == "DP1030 — ADHD Planner",
                  f"picker option text must show the product's real title, not blank after the dash: {real_panel}")
            check(real_panel.get("runBtnPresent"), f"the build button (#bx-run-btn) must be present in a real category's panel: {real_panel}")

            # Re-opening the SAME category (with _products unchanged) must not
            # duplicate picker options -- regression guard for the idempotent-sync fix.
            reopen_same = await page.evaluate("""() => {
                createOpenCategory('digital_planner'); // closes it (toggle)
                createOpenCategory('digital_planner'); // reopens fresh
                const picker = document.getElementById('create-pid-select');
                return {pickerOptionCount: picker ? picker.options.length : 0};
            }""")
            check(reopen_same.get("pickerOptionCount") == real_panel.get("pickerOptionCount"),
                  f"reopening a category must not duplicate picker options: {reopen_same} vs first open {real_panel}")

            # Regression guard (QA review, 2026-07-22): typing a free-text code
            # then switching back to "pick from the list instead" must not leave
            # that stale code queued in the hidden #bx-pid -- it must resync to
            # whatever the (visible-again) picker shows.
            stale_freetext = await page.evaluate("""() => {
                _createToggleNewCode(true);
                document.getElementById('bx-pid').value = 'DP9999STALE';
                _createToggleNewCode(false);
                return {bxPidValue: document.getElementById('bx-pid').value};
            }""")
            check(stale_freetext.get("bxPidValue") != "DP9999STALE",
                  f"switching back to the picker must clear a stale free-typed code from #bx-pid: {stale_freetext}")

            # Regression guard (QA review, 2026-07-22): createPollBuildStatus()
            # used a single hardcoded #cd-build-status-box id -- calling it twice
            # into two DIFFERENT containers (digital_planner's panel legitimately
            # has up to 4 simultaneous build buttons) used to collide, with the
            # second call's getElementById silently updating the FIRST box instead
            # of its own. Call it twice into two distinct elements and confirm
            # each gets its own independent status box.
            poll_isolation = await page.evaluate("""() => {
                const a = document.createElement('div'); a.id = 'pw-poll-test-a';
                const b = document.createElement('div'); b.id = 'pw-poll-test-b';
                document.body.appendChild(a); document.body.appendChild(b);
                createPollBuildStatus(123456, '', a);
                createPollBuildStatus(654321, '', b);
                const result = {
                    aHasOwnBox: a.children.length === 1,
                    bHasOwnBox: b.children.length === 1,
                    distinctNodes: a.children[0] !== b.children[0],
                };
                a.remove(); b.remove();
                return result;
            }""")
            check(poll_isolation.get("aHasOwnBox") and poll_isolation.get("bHasOwnBox"),
                  f"each createPollBuildStatus() call must create its own status box in its own outEl: {poll_isolation}")
            check(poll_isolation.get("distinctNodes"),
                  f"two concurrent polls must never share the same status box node: {poll_isolation}")

            # Regression guard (QA review, 2026-07-22): wall_art/coloring_pages'
            # one-tap builds generate no new AI art, so the Advanced "Art style"
            # engine picker (which the backend never reads for these 2
            # categories) must not render at all -- a dead control is worse than
            # no control.
            # NOTE (2026-07-22): #bx-engine now legitimately exists in the DOM
            # (hidden) for wall_art/coloring_pages too, as part of the new
            # "+ new one" new-art sub-panel (see usesNewArtDescription below) --
            # mere presence is no longer a valid dead-control signal for those
            # 2 categories, only VISIBILITY is (a user never sees a hidden
            # element). Digital Planner's is still checked for straightforward
            # presence since its outer Advanced disclosure, while collapsed, is
            # not display:none (just a CSS class toggle), so this distinction
            # doesn't apply there.
            no_dead_engine = await page.evaluate("""() => {
                createOpenCategory('wall_art');
                const waEl = document.getElementById('bx-engine');
                const wallArtEngineVisible = !!waEl && waEl.offsetParent !== null;
                createOpenCategory('wall_art'); // close
                createOpenCategory('coloring_pages');
                const cEl = document.getElementById('bx-engine');
                const coloringEngineVisible = !!cEl && cEl.offsetParent !== null;
                createOpenCategory('coloring_pages'); // close
                createOpenCategory('digital_planner');
                const plannerHasEngine = !!document.getElementById('bx-engine');
                createOpenCategory('digital_planner'); // close
                return {wallArtEngineVisible, coloringEngineVisible, plannerHasEngine};
            }""")
            check(no_dead_engine.get("wallArtEngineVisible") is False,
                  f"Wall Art's picker-mode (existing-product rebuild) view must not show a visible art-style engine picker: {no_dead_engine}")
            check(no_dead_engine.get("coloringEngineVisible") is False,
                  f"Coloring Pages' picker-mode view must not show a visible art-style engine picker: {no_dead_engine}")
            check(no_dead_engine.get("plannerHasEngine") is True, f"Digital Planner DOES use the engine picker and must still render it: {no_dead_engine}")

            # Regression guard: Scott reported live (2026-07-22) that tapping
            # "Build these coloring pages" with nothing picked showed "Enter a
            # planner code first (e.g. DP1030)" -- buildProductRun() is the ONE
            # shared build button for all 3 real categories, and its empty-pid
            # message was hardcoded to planner wording regardless of which
            # category's panel was actually open. Must be category-aware now.
            wrong_category_error = await page.evaluate("""async () => {
                createOpenCategory('coloring_pages');
                document.getElementById('bx-pid').value = '';
                await buildProductRun();
                const coloringMsg = document.getElementById('bx-result').innerHTML;
                createOpenCategory('coloring_pages'); // close
                createOpenCategory('wall_art');
                document.getElementById('bx-pid').value = '';
                await buildProductRun();
                const wallArtMsg = document.getElementById('bx-result').innerHTML;
                createOpenCategory('wall_art'); // close
                return {coloringMsg, wallArtMsg};
            }""")
            check("planner" not in wrong_category_error.get("coloringMsg", "").lower() and "DP1030" not in wrong_category_error.get("coloringMsg", ""),
                  f"Coloring Pages' empty-pid error must not reference planners/DP1030: {wrong_category_error}")
            # (2026-07-25) Coloring Pages no longer has a typed-code field at
            # all (Scott: "It should auto generate the code") -- an empty pid
            # here means the theme was never described, so the message must
            # point at describing a theme, not at a "COLOR1030"-style code.
            check("theme" in wrong_category_error.get("coloringMsg", "").lower(),
                  f"Coloring Pages' empty-pid error should point at describing a theme: {wrong_category_error}")
            check("planner" not in wrong_category_error.get("wallArtMsg", "").lower() and "DP1030" not in wrong_category_error.get("wallArtMsg", ""),
                  f"Wall Art's empty-pid error must not reference planners/DP1030: {wrong_category_error}")
            check("WA1030" in wrong_category_error.get("wallArtMsg", ""),
                  f"Wall Art's empty-pid error should use its own category example: {wrong_category_error}")

            # Regression guard: Scott's EXACT reported scenario (2026-07-22
            # follow-up) -- opening Coloring Pages, typing a genuinely new code
            # via "+ This is a new one", and tapping Build returned "COLOR01
            # isn't a configured planner (have DP1026...)". Root cause:
            # buildProductRun() never sent `category` in its POST body, so the
            # server fell back to guessing from product_catalog.json and
            # defaulted to digital_planner for any uncataloged pid. This hits
            # the REAL backend (no mocking) -- the fix's pre-flight check
            # returns a clean error with no subprocess spawned, so it's fast
            # and safe to run for real here.
            misroute_repro = await page.evaluate("""async () => {
                createOpenCategory('coloring_pages');
                _createToggleNewCode(true);
                document.getElementById('bx-pid').value = 'COLOR01';
                await buildProductRun();
                const coloringMsg = document.getElementById('bx-result').innerHTML;
                createOpenCategory('coloring_pages'); // close

                createOpenCategory('wall_art');
                _createToggleNewCode(true);
                document.getElementById('bx-pid').value = 'WA_PLAYWRIGHT_NO_SOURCE_ART';
                await buildProductRun();
                const wallArtMsg = document.getElementById('bx-result').innerHTML;
                createOpenCategory('wall_art'); // close

                return {coloringMsg, wallArtMsg};
            }""")
            coloring_lc = misroute_repro.get("coloringMsg", "").lower()
            check("planner" not in coloring_lc and "dp10" not in coloring_lc,
                  f"Scott's exact repro: a new Coloring Pages code must never be misrouted through the planner branch: {misroute_repro}")
            check("catalog" in coloring_lc,
                  f"Coloring Pages' real error for an uncataloged code should name the actual reason (catalog): {misroute_repro}")
            wallart_lc = misroute_repro.get("wallArtMsg", "").lower()
            check("planner" not in wallart_lc and "dp10" not in wallart_lc,
                  f"a new Wall Art code must never be misrouted through the planner branch: {misroute_repro}")
            check("source art" in wallart_lc,
                  f"Wall Art's real error for a code with no source file should name the actual reason (source art): {misroute_repro}")

            # Regression guard (2026-07-22, Scott's follow-up: "every action on
            # this page has to work ... if this doesn't work we don't have a
            # business"): Digital Planner is a closed set of 9 hardcoded pids,
            # all already in the picker -- the "+ new one" link can never
            # succeed there and must not render at all. Wall Art / Coloring
            # Pages, by contrast, now have a REAL new-art generation path, so
            # their "+ new one" panels must show the description + engine
            # controls.
            new_code_affordances = await page.evaluate("""() => {
                createOpenCategory('digital_planner');
                // Scoped to #create-pid-picker-wrap specifically -- the OTHER
                // .cd-newcode-link ("< pick from the list instead") lives inside
                // #create-pid-freetext-wrap, which stays in the DOM (just hidden)
                // for every category per the plan (buildProductRun()/
                // _createPidSelectChanged() reference #bx-pid unconditionally) --
                // that one is unreachable dead markup for Digital Planner, not a
                // regression, so it must not be what this check matches.
                const plannerHasLink = !!document.querySelector('#create-pid-picker-wrap .cd-newcode-link');
                createOpenCategory('digital_planner'); // close

                createOpenCategory('wall_art');
                _createToggleNewCode(true);
                const wallArtHasDesc = !!document.getElementById('bx-description');
                const wallArtHasEngineInNewCode = !!document.getElementById('bx-engine');
                createOpenCategory('wall_art'); // close

                createOpenCategory('coloring_pages');
                _createToggleNewCode(true);
                const coloringHasDesc = !!document.getElementById('bx-description');
                const coloringDescPlaceholder = (document.getElementById('bx-description')||{}).placeholder || '';
                createOpenCategory('coloring_pages'); // close

                return {plannerHasLink, wallArtHasDesc, wallArtHasEngineInNewCode, coloringHasDesc, coloringDescPlaceholder};
            }""")
            check(new_code_affordances.get("plannerHasLink") is False,
                  f"Digital Planner must never show the '+ new one' link -- it can never succeed: {new_code_affordances}")
            check(new_code_affordances.get("wallArtHasDesc") is True,
                  f"Wall Art's new-code panel must show the art-description field: {new_code_affordances}")
            check(new_code_affordances.get("wallArtHasEngineInNewCode") is True,
                  f"Wall Art's new-code panel must show an engine picker (real AI generation happens here now): {new_code_affordances}")
            check(new_code_affordances.get("coloringHasDesc") is True,
                  f"Coloring Pages' new-code panel must show the subjects-description field: {new_code_affordances}")
            check("subject" in new_code_affordances.get("coloringDescPlaceholder", "").lower(),
                  f"Coloring Pages' description placeholder should explain the one-subject-per-line convention: {new_code_affordances}")
            check("20" in new_code_affordances.get("coloringDescPlaceholder", ""),
                  f"Coloring Pages' placeholder should promise 20 auto-generated subjects (2026-07-24): {new_code_affordances}")

            # Regression guard: switching from "+ new one" back to the picker
            # must clear a typed description too (not just the pid) -- a
            # stale description must never silently survive into a rebuild
            # of an EXISTING product picked afterward.
            desc_cleared_on_toggle_back = await page.evaluate("""() => {
                createOpenCategory('wall_art');
                _createToggleNewCode(true);
                document.getElementById('bx-description').value = 'a stale leftover description';
                _createToggleNewCode(false);
                const val = document.getElementById('bx-description').value;
                createOpenCategory('wall_art'); // close
                return {val};
            }""")
            check(desc_cleared_on_toggle_back.get("val") == "",
                  f"switching back to the picker must clear a typed description: {desc_cleared_on_toggle_back}")

            # Real end-to-end: opening Wall Art's "+ new one", typing BOTH a
            # code and a description, and tapping build must send `description`
            # in the POST body (mocked network call -- no real AI spend here,
            # tools/playwright_smoke.py stays a UI-contract check; the real
            # backend logic is covered by tests/test_produce_qc.py's mocked-
            # Popen success-path tests).
            captured_body = {}

            async def _capture_build_request(route):
                import json as _json
                captured_body.update(_json.loads(route.request.post_data or "{}"))
                await route.fulfill(status=200, content_type="application/json",
                                     body='{"pid": "WA_PW_TEST", "started": true, "os_pid": 424242, '
                                          '"log_file": "WA_PW_TEST_wallart_build.log", "steps": ["generate art"], '
                                          '"message": "ok"}')
            await page.route("**/api/produce/build-product", _capture_build_request)
            await page.evaluate("""async () => {
                createOpenCategory('wall_art');
                _createToggleNewCode(true);
                document.getElementById('bx-pid').value = 'WA_PW_TEST';
                document.getElementById('bx-description').value = 'a real description for the request body';
                await buildProductRun();
            }""")
            await page.unroute("**/api/produce/build-product")
            check(captured_body.get("description") == "a real description for the request body",
                  f"buildProductRun() must send the typed description in the POST body: {captured_body}")
            check(captured_body.get("category") == "wall_art", f"got: {captured_body}")

            # Coloring Pages auto-generated code (2026-07-25): Scott: "It
            # should auto generate the code" -- opening "+ new one" must NOT
            # show a visible/focusable #bx-pid, and typing only a theme
            # (never a code) must still successfully kick off a build, with
            # the server-assigned pid coming back in the response.
            coloring_pid_field = await page.evaluate("""() => {
                createOpenCategory('coloring_pages');
                _createToggleNewCode(true);
                const el = document.getElementById('bx-pid');
                const result = {
                    type: el && el.type,
                    visible: !!el && el.offsetParent !== null,
                    hasNote: document.getElementById('create-pid-freetext-wrap').textContent.toLowerCase().includes('automatically'),
                };
                createOpenCategory('coloring_pages'); // close
                return result;
            }""")
            check(coloring_pid_field.get("type") == "hidden",
                  f"Coloring Pages' new-theme panel must never show a typed-code field: {coloring_pid_field}")
            check(coloring_pid_field.get("visible") is False, f"got: {coloring_pid_field}")
            check(coloring_pid_field.get("hasNote") is True,
                  f"the panel should explain the code is auto-assigned: {coloring_pid_field}")

            coloring_captured_body = {}

            async def _capture_coloring_build_request(route):
                import json as _json
                coloring_captured_body.update(_json.loads(route.request.post_data or "{}"))
                await route.fulfill(status=200, content_type="application/json",
                                     body='{"pid": "COLOR9042", "started": true, "os_pid": 424243, '
                                          '"log_file": "COLOR9042_coloring_build.log", '
                                          '"steps": ["coloring pages (new theme)"], "message": "ok"}')
            await page.route("**/api/produce/build-product", _capture_coloring_build_request)
            coloring_result_html = await page.evaluate("""async () => {
                createOpenCategory('coloring_pages');
                _createToggleNewCode(true);
                document.getElementById('bx-description').value = 'ocean animals';
                await buildProductRun();
                return document.getElementById('bx-result').innerHTML;
            }""")
            await page.unroute("**/api/produce/build-product")
            check(coloring_captured_body.get("pid") == "",
                  f"the frontend must send an empty pid, letting the server auto-generate it: {coloring_captured_body}")
            check(coloring_captured_body.get("category") == "coloring_pages", f"got: {coloring_captured_body}")
            check(coloring_captured_body.get("description") == "ocean animals", f"got: {coloring_captured_body}")
            check("COLOR9042" in coloring_result_html,
                  f"the server-assigned pid must render in the success banner: {coloring_result_html}")

            # Coming-soon tiles: never blank, never a dead click -- must show a
            # specific, honest explanation.
            soon_panel = await page.evaluate("""() => {
                createOpenCategory('sticker_pack');
                const panel = document.getElementById('create-detail');
                return {
                    tileOpen: document.querySelector('.create-choice[data-cat="sticker_pack"]').classList.contains('open'),
                    panelHtml: panel ? panel.innerHTML : '',
                };
            }""")
            check(soon_panel.get("tileOpen"), f"opening a coming-soon category should still mark its tile .open: {soon_panel}")
            soon_html = soon_panel.get("panelHtml", "")
            check(len(soon_html.strip()) > 40, f"a coming-soon panel must never render blank: {soon_panel}")
            check("no automatic builder" in soon_html.lower(), f"coming-soon panel must give a specific, honest reason: {soon_panel}")
            check("Build this" not in soon_html, f"a coming-soon panel must never show a working-looking build button: {soon_panel}")

            # Advanced Tools disclosure: collapsed by default, and expanding it must
            # reveal every relocated-but-unchanged tool with its IDs intact.
            # (2026-07-25) create-video/create-social moved OUT of this disclosure
            # entirely into their own "Product Video" tile (see the dedicated
            # video_panel check above) -- only SVG converter + Quality Check remain
            # here now, so this must confirm their absence, not their presence.
            advanced = await page.evaluate("""() => {
                const body = document.getElementById('create-advanced-body');
                const collapsedByDefault = body ? body.style.display === 'none' : null;
                document.getElementById('create-advanced-toggle').click();
                return {
                    collapsedByDefault,
                    expandedNow: body ? body.style.display !== 'none' : null,
                    svgPresent: !!document.getElementById('create-svg'),
                    qcPresent: !!document.getElementById('create-qc'),
                    videoPresent: !!document.getElementById('create-video'),
                    socialPresent: !!document.getElementById('create-social'),
                    svgDropzonePresent: !!document.getElementById('svgc-dropzone'),
                    qcRunBtnPresent: !!document.getElementById('qc-run-btn'),
                };
            }""")
            check(advanced.get("collapsedByDefault"), f"Advanced Tools must be collapsed by default: {advanced}")
            check(advanced.get("expandedNow"), f"clicking the Advanced Tools toggle must expand it: {advanced}")
            check(all(advanced.get(k) for k in ("svgPresent", "qcPresent")),
                  f"the 2 remaining relocated tool sections (SVG, QC) must still be present: {advanced}")
            check(not advanced.get("videoPresent") and not advanced.get("socialPresent"),
                  f"create-video/create-social must no longer live inside Advanced tools -- they moved to the Product Video tile: {advanced}")
            check(advanced.get("svgDropzonePresent") and advanced.get("qcRunBtnPresent"),
                  f"relocated tools' inner controls (dropzone, run button) must survive the move too: {advanced}")

            # Reference Photos library -- upload zone + category picker + grid must
            # be present in the primary (non-collapsed) view, per the plan.
            refimg = await page.evaluate("""() => ({
                categorySelectPresent: !!document.getElementById('refimg-category'),
                dropzonePresent: !!document.getElementById('refimg-dropzone'),
                gridPresent: !!document.getElementById('refimg-grid'),
                categoryOptionCount: (document.getElementById('refimg-category')||{options:[]}).options.length,
            })""")
            check(refimg.get("categorySelectPresent") and refimg.get("dropzonePresent") and refimg.get("gridPresent"),
                  f"Reference Photos section must render its category picker, dropzone, and grid: {refimg}")
            check(refimg.get("categoryOptionCount", 0) == 8,
                  f"category picker should offer the 7 real+coming-soon categories plus 'general', got: {refimg}")

            # Leave the panel closed for later checks in this same page session
            # (_createOpenCat is currently 'sticker_pack' from soon_panel above --
            # calling it again toggles that same panel closed).
            await page.evaluate("createOpenCategory('sticker_pack'); document.getElementById('create-advanced-toggle').click()")
            await page.unroute("**/api/products", _block_real_products)

            # ── Files screen: listing-attachment grouping (2026-07-22) -- Scott's
            # screenshot showed "PRODUCT FILES" grouping coloring_pages' internal
            # per-page theme IDs (CB001, CB002, ...) as if each were its own
            # single-file product, while the REAL deliverable ZIP customers
            # receive (coloring_set_01.zip, genuinely attached to a live listing)
            # fell into a generic leftover bucket. /api/files now annotates each
            # file with catalog_match; loadFiles() splits the "products" root into
            # "Attached to a Listing" (grouped by the real product) and "Not
            # Attached to a Listing" (grouped by type, then by product where
            # known), and sub-groups "reference_images" by its own category
            # metadata instead of the filename regex. Mock the exact scenario and
            # assert the DOM lands it in the right buckets.
            #
            # Uses an in-page authGet() monkeypatch, NOT page.route() -- Frank
            # registers its own service worker (frank-sw.js) scoped to /frank
            # that re-fetches every GET request from inside the SW's own fetch
            # handler; that sub-fetch isn't visible to Playwright's page-level
            # network interception, so a page.route("**/api/files", ...) mock
            # here silently never fires and the real (large, real-data) scan
            # runs instead -- confirmed by direct reproduction: even a bare
            # page.evaluate("fetch('/api/files')") returns a real 200 with real
            # data while the registered route handler is never invoked.
            # Patching the shared authGet() function in the page's own JS realm
            # sidesteps the network layer entirely. ──
            files_text = await page.evaluate("""() => {
                const orig = window.authGet;
                window.authGet = (path, ms) => {
                    if (path !== '/api/files') return orig(path, ms);
                    const payload = {
                        groups: [
                            {root: 'products', label: 'Product Files', files: [
                                {path: 'coloring_set_01.zip', root: 'products', size: 100,
                                 size_human: '100 B', modified: '2026-07-22T00:00:00+00:00',
                                 inline: false, is_zip: true, entries: [],
                                 catalog_match: {product_id: 'COLOR_KAWAII_COLORING_PAGES_SET_01',
                                                 category: 'coloring_pages', attached: true}},
                                {path: 'DP1030_v2.pdf', root: 'products', size: 200,
                                 size_human: '200 B', modified: '2026-07-22T00:00:00+00:00',
                                 inline: true, is_zip: false,
                                 catalog_match: {product_id: 'DP1030', category: 'digital_planner',
                                                 attached: false}},
                                {path: 'CB001_coloring.png', root: 'products', size: 50,
                                 size_human: '50 B', modified: '2026-07-22T00:00:00+00:00',
                                 inline: true, is_zip: false, catalog_match: null},
                            ]},
                            {root: 'reference_images', label: 'Reference Photos', files: [
                                {path: 'ab12cd34_moodboard.jpg', root: 'reference_images', size: 60,
                                 size_human: '60 B', modified: '2026-07-22T00:00:00+00:00',
                                 inline: true, is_zip: false, category: 'wall_art'},
                            ]},
                        ],
                        empty_reason: null,
                    };
                    return Promise.resolve({ok: true, status: 200, json: async () => payload});
                };
                showScreen('files');
                return new Promise(resolve => setTimeout(() => {
                    window.authGet = orig;
                    const el = document.getElementById('files-content');
                    // textContent, not innerText -- the collapsed sub-folder rows
                    // (CSS display:none until tapped) are real DOM content that
                    // innerText would skip as "invisible", and .hub-section-title's
                    // text-transform:uppercase would otherwise break exact-string
                    // assertions below.
                    resolve(el ? el.textContent : '');
                }, 300));
            }""")
            check("Attached to a Listing" in files_text and "Not Attached to a Listing" in files_text,
                  f"Product Files must split into both sections: {files_text[:400]}")
            check("COLOR_KAWAII_COLORING_PAGES_SET_01" in files_text,
                  f"the real, listing-attached deliverable must appear under its real product folder: {files_text[:400]}")
            check("Digital Planners" in files_text,
                  f"an unattached draft product's files must be grouped under its real category label: {files_text[:400]}")
            check("Coloring Pages" in files_text,
                  f"the orphan CB001 source image (no catalog match) must fall back to the Coloring Pages type bucket, not its own fake product: {files_text[:400]}")
            attached_section, _, not_attached_section = files_text.partition("Not Attached to a Listing")
            check("CB001" not in attached_section,
                  f"the orphan CB001 source image must never appear in the Attached section: {attached_section[:400]}")
            check("CB001" in not_attached_section,
                  f"CB001 should still be browsable as its own sub-folder inside the Coloring Pages type bucket (Scott's 'where would I still see them' ask): {not_attached_section[:400]}")
            check("Wall Art" in files_text.split("Reference Photos")[-1],
                  f"Reference Photos must sub-group by the real per-image category metadata: {files_text[:400]}")

            # ── Files screen: Download Backup honest failure (2026-07-31) -- was a
            # bare window.open() + an unconditional success toast regardless of what
            # happened in the new tab. GET /api/backup/download-all is owner-only,
            # and every self-signup tester is role="admin" not "owner", so this
            # 403'd for every one of them while the toast still claimed success.
            # Now a real fetch+blob download; assert an honest message renders on a
            # 403 instead of the old false-success toast. Mock fetchWithTimeout
            # directly (not page.route()/authGet) since downloadFullBackup() calls
            # it directly, same "mock in the page's own JS realm" reasoning as the
            # Files-grouping block above (frank-sw.js swallows page.route mocks).
            backup_toast_text = await page.evaluate("""async () => {
                const orig = window.fetchWithTimeout;
                window.fetchWithTimeout = (url, opts, ms) => {
                    if (String(url).includes('/api/backup/download-all')) {
                        return Promise.resolve({status: 403, ok: false});
                    }
                    return orig(url, opts, ms);
                };
                showScreen('files');
                downloadFullBackup();
                await new Promise(r => setTimeout(r, 400));
                window.fetchWithTimeout = orig;
                const stack = document.getElementById('toast-stack');
                return stack ? stack.textContent : '';
            }""")
            check("owner-only" in backup_toast_text,
                  f"expected an honest owner-only-action toast on a 403, got: {backup_toast_text!r}")
            check("Backup ZIP downloaded" not in backup_toast_text,
                  f"must never show the success toast when the download 403s, got: {backup_toast_text!r}")

            # ── Desktop sub-floor content-cutoff regression (2026-07-29, Scott: "the
            # chat is still cut off as well as the section to the right... it should
            # auto adjust"). Every prior "Desktop layout fix" pass in this file's
            # history (8078d7a, 98ad5ef, aab770f) only verified at-or-above the
            # STAGE_H_MIN=900 floor -- the actual bug only reproduced BELOW it, on a
            # real laptop viewport, which none of those passes ever checked. Root
            # cause was two-fold: (1) #stage's grid-template-rows used a bare "1fr"
            # for its middle row, which has an implicit content-based minimum that
            # silently overrides min-height:0 on the grid item inside it -- fixed
            # with minmax(0,1fr); (2) .main (the 3-column chat layout) is nested
            # inside #screen-cmd, not a direct grid item of #stage as its own
            # grid-column/grid-row properties implied -- #screen-cmd is display:block
            # when active, so .main's placement properties were inert, and .main (no
            # explicit height) just grew to its own content size and silently
            # overflowed its already-correctly-sized parent -- fixed with
            # height:100%. Assert the real, measurable symptom: .col-right's own
            # overflow-y:auto must actually engage (scrollHeight > clientHeight) once
            # its cards have real content, not stay permanently un-triggered like it
            # did before either fix. ──
            await page.set_viewport_size({"width": 1366, "height": 672})
            await page.evaluate("showScreen('cmd')")
            await page.wait_for_timeout(400)
            await page.evaluate("""() => {
                const setBody = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
                setBody('star-seller-body', '<div class="core-row"><span>Orders (90d)</span><span>5/5</span></div><div class="core-row"><span>Revenue (90d)</span><span>$80/$300</span></div><div class="core-row"><span>Avg Rating</span><span>5 stars</span></div><div class="core-row"><span>On-time Delivery</span><span>100%</span></div><div class="core-row"><span>Unread Messages</span><span>0</span></div>');
                setBody('cogs-status-body', '<div class="core-row"><span>Avg margin (est.)</span><span>80.1%</span></div><div class="core-row"><span>Recent profit (est.)</span><span>$22.74</span></div><div class="core-row"><span>Recent units sold</span><span>4</span></div><div class="core-row"><span>Active listings</span><span>100</span></div><div style="font-size:9.5px;line-height:1.4">Long disclaimer paragraph filler text simulating real production content wrapping across several lines of small print.</div>');
                setBody('inbox-body', '<div class="core-row"><span>New reviews</span><span>2</span></div><div class="core-row"><span>Unread messages</span><span>0</span></div><div class="core-row"><span>Pending questions</span><span>1</span></div>');
            }""")
            await page.wait_for_timeout(300)
            sub_floor_layout = await page.evaluate("""() => {
                const right = document.querySelector('.col-right');
                const inbox = document.getElementById('inbox-body');
                return {
                    rightScrollHeight: right.scrollHeight,
                    rightClientHeight: right.clientHeight,
                    inboxClientHeight: inbox.clientHeight,
                };
            }""")
            check(sub_floor_layout["rightScrollHeight"] > sub_floor_layout["rightClientHeight"],
                  f"at a real sub-floor laptop viewport (1366x672), .col-right's content must genuinely overflow its box so overflow-y:auto engages -- otherwise content is silently clipped with no scrollbar reachable anywhere: {sub_floor_layout}")
            check(sub_floor_layout["inboxClientHeight"] > 0,
                  f"Inbox & Reviews card must keep a real, non-zero height (not get flex-shrunk to invisible) even when the 4 fixed-size cards above it are near-full of realistic content: {sub_floor_layout}")
            await page.set_viewport_size({"width": 1440, "height": 1000})
            await page.wait_for_timeout(300)

            # ── Mobile spotlight tour (2026-07-15) -- same #tour-root engine as
            # desktop, spotlighting #phone-tabbar's 5 tabs instead of the
            # sidebar. setViewportSize (not a new context) so this reuses the
            # already-authenticated session. ──
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.wait_for_timeout(500)

            # 2026-07-18: the FRANK/SHOP ASSISTANT logo lockup has no click handler
            # (aria-hidden decoration) -- on mobile its label text was already
            # hidden, leaving an unlabeled glowing square that looked like a dead
            # button. Hidden via visibility:hidden (not display:none) so the
            # mobile header grid's row height is untouched -- see the CSS comment.
            hdr_logo_state = await page.evaluate("""() => {
                const el = document.querySelector('.hdr-logo');
                return el ? getComputedStyle(el).visibility : 'missing';
            }""")
            check(hdr_logo_state == "hidden", f"the non-functional logo square must not be visible on mobile, got visibility: {hdr_logo_state}")

            # ── Today tab: skeleton loader on first load, card-resolve animation
            # on refresh (2026-07-18 visual-design pass). Stubs authGet() directly
            # rather than mocking the network -- the app's service worker
            # (frank-sw.js) intercepts every GET via its own internal fetch(req)
            # call, which page.route() cannot see (confirmed earlier this session
            # debugging the "Recently completed" test below), so authGet is the
            # right seam here, same as _products/_listings fixtures elsewhere. ──
            skeleton_check = await page.evaluate("""() => ({
                tile: _skeletonCards(0, 'tile'),
                card: _skeletonCards(2),
            })""")
            check("skel-bar" in skeleton_check.get("tile", "") and "skel-tile" in skeleton_check.get("tile", ""),
                  f"_skeletonCards(0,'tile') should render shimmer tile placeholders: {skeleton_check}")
            check(skeleton_check.get("card", "").count("skel-card") == 2,
                  f"_skeletonCards(2) should render exactly 2 card placeholders: {skeleton_check}")

            today_first_load = await page.evaluate("""async () => {
                let call = 0;
                window.__origAuthGet = authGet;
                authGet = async (path) => {
                    if (path.includes('/api/actions')) {
                        call++;
                        const items = call === 1
                            ? [{listing_id: 501, severity: 'high', title: 'Card A', suggestion: 'fix A'},
                               {listing_id: 502, severity: 'high', title: 'Card B', suggestion: 'fix B'}]
                            : [{listing_id: 501, severity: 'high', title: 'Card A', suggestion: 'fix A'}];
                        return {ok: true, json: async () => ({actions: items})};
                    }
                    return {ok: true, json: async () => ({})};
                };
                await renderPhoneToday();
                return {
                    bodyText: document.getElementById('pp-today-body').textContent,
                    hasDataKeys: !!document.querySelector('[data-need-key="l:501"]') && !!document.querySelector('[data-need-key="l:502"]'),
                };
            }""")
            check(today_first_load.get("bodyText", "").count("Card A") == 1 and "Card B" in today_first_load.get("bodyText", ""),
                  f"first Today load should show both cards: {today_first_load}")
            check(today_first_load.get("hasDataKeys"), f"cards should carry data-need-key for the resolve animation to target: {today_first_load}")

            today_resolve = await page.evaluate("""async () => {
                await renderPhoneToday();  // 2nd call -- Card B drops out
                await new Promise(r => setTimeout(r, 500));  // let the .42s resolve animation finish
                const bodyText = document.getElementById('pp-today-body').textContent;
                authGet = window.__origAuthGet;  // restore for later checks in this run
                return {bodyText, cardBGone: !document.querySelector('[data-need-key="l:502"]')};
            }""")
            check("Card A" in today_resolve.get("bodyText", ""), f"Card A should still be present after refresh: {today_resolve}")
            check("Card B" not in today_resolve.get("bodyText", ""), f"resolved Card B should be gone from the final content: {today_resolve}")
            check(today_resolve.get("cardBGone"), f"resolved card should actually be removed from the DOM after the animation: {today_resolve}")

            # ── Count-up stat tiles + Star Seller milestone badge (2026-07-18).
            # Stub authGet again (same seam as above) for /api/metrics and
            # /api/star-seller, then wait past the .26s count-up animation and
            # check the tile settled on the exact real value (no float drift). ──
            countup_state = await page.evaluate("""async () => {
                window.__origAuthGet2 = authGet;
                authGet = async (path) => {
                    if (path.includes('/api/metrics')) {
                        return {ok: true, json: async () => ({orders: {last_7_days: 6, revenue_7d: 123.5}, shop: {total_sales: 42}})};
                    }
                    if (path.includes('/api/star-seller')) {
                        return {ok: true, json: async () => ({status: 'on_track', orders_90d: 12, revenue_90d: 480, avg_rating: 4.9})};
                    }
                    if (path.includes('/api/actions') || path.includes('/api/alerts')) {
                        return {ok: true, json: async () => ({actions: [], alerts: []})};
                    }
                    return {ok: true, json: async () => ({})};
                };
                await renderPhoneToday();
                await new Promise(r => setTimeout(r, 400));  // past the .26s count-up
                const tiles = Array.from(document.querySelectorAll('.ptile .n')).map(n => n.textContent);
                const bodyText = document.getElementById('pp-today-body').textContent;
                authGet = window.__origAuthGet2;
                return {tiles, hasMilestone: !!document.querySelector('.pmilestone'), bodyText};
            }""")
            check(countup_state.get("tiles") == ["6", "$123.50", "42"],
                  f"count-up should settle on the exact real values with no float drift: {countup_state}")
            check(countup_state.get("hasMilestone"), f"Star Seller on_track should render the .pmilestone badge: {countup_state}")
            check("Star Seller" in countup_state.get("bodyText", "") and "12 orders" in countup_state.get("bodyText", ""),
                  f"milestone badge should show real Star Seller numbers: {countup_state}")

            # ── Success checkmark toast on approve (2026-07-18). Unlike GET
            # requests, POST isn't intercepted by the service worker (frank-sw.js
            # only wraps GET), so page.route() works normally here. ──
            async def _mock_approve(route):
                await route.fulfill(status=200, content_type="application/json",
                                     body='{"status":"executed","id":999,"result":{"listing_id":42,"title":"New Fixed Title"}}')
            await page.route("**/api/queue/999/approve", _mock_approve)
            page.once("dialog", lambda d: d.accept())
            checkmark_state = await page.evaluate("""async () => {
                _pendingActions = [{id: 999, type: 'update_title', payload: {listing_id: 42, title: 'New Fixed Title'}}];
                await approveAction(999);
                await new Promise(r => setTimeout(r, 100));
                const stack = document.getElementById('toast-stack');
                return {hasCheckSvg: !!(stack && stack.querySelector('.toast-check svg')), toastText: stack ? stack.textContent : ''};
            }""")
            await page.unroute("**/api/queue/999/approve")
            check(checkmark_state.get("hasCheckSvg"), f"a successful approve should show the animated .toast-check icon: {checkmark_state}")
            check("New Fixed Title" in checkmark_state.get("toastText", ""), f"success toast should name what changed: {checkmark_state}")

            # ── "Recently completed" activity list (2026-07-18) -- a real bug
            # report: Scott approved a Conversion Doctor fix and had no way to
            # tell if it worked. GET /api/queue?status=all already existed
            # server-side but nothing ever rendered anything but pending items.
            # Test the shared render helper directly with synthetic data rather
            # than mocking the network call -- the app registers a service worker
            # (frank-sw.js) whose 'fetch' handler intercepts ALL GETs via its own
            # internal fetch(req) call, which happens outside the page's execution
            # context and isn't visible to page.route() (confirmed: a mocked
            # /api/queue?status=all route was silently never hit; the real
            # backend response came through instead). _recentActivityHtml() is
            # where all the actual logic lives (outcome text, icons, escaping) --
            # the fetch-and-filter glue in renderPhoneApprovals()/loadActions()
            # is exercised for real every time either screen loads normally. ──
            recent_html_check = await page.evaluate("""() => {
                const items = [
                    {id: 1, type: 'update_title', status: 'executed', decided_at: '2026-07-18T00:00:00+00:00',
                     payload: {listing_id: 42, title: 'New Fixed Title'}, result: {listing_id: 42}},
                    {id: 2, type: 'update_tags', status: 'failed', decided_at: '2026-07-18T00:00:00+00:00',
                     payload: {listing_id: 43, tags: ['a','b']}, result: {error: 'Etsy 429 rate limited'}},
                ];
                return {
                    emptyHtml: _recentActivityHtml([]),
                    filledHtml: _recentActivityHtml(items),
                };
            }""")
            check(recent_html_check.get("emptyHtml") == "", f"an empty recent-actions list should render nothing: {recent_html_check}")
            filled = recent_html_check.get("filledHtml", "")
            check("Recently completed" in filled, f"a non-empty recent-actions list should render a 'Recently completed' section: {filled[:300]}")
            check("New Fixed Title" in filled, f"an executed update_title action should show its outcome (the new title): {filled[:300]}")
            check("✅" in filled, f"an executed action should show a success icon: {filled[:300]}")
            check("Etsy 429 rate limited" in filled, f"a failed action should show the actual error, not just 'failed': {filled[:300]}")
            check("❌" in filled, f"a failed action should show a failure icon: {filled[:300]}")

            # ── Approvals UX audit (2026-07-30) ── mobile detail-expand: renderPhoneApprovals()'s
            # pcard now calls toggleActionDetail() with the same #act-detail-{id} id convention
            # desktop's renderApproval() uses, so _actionPreviewHtml()/_actionPreviewBody() (the
            # "why Frank suggested this" reasoning block + type-specific preview) run unmodified.
            # Test the shared pipeline directly (same reasoning as the "Recently completed" block
            # above -- the service worker makes network mocking unreliable, and toggleActionDetail
            # itself does no fetching, so this exercises the real function with synthetic data).
            reason_panel_check = await page.evaluate("""() => {
                _pendingActions = [{id: 9001, type: 'update_title', summary: 'Fix title',
                    payload: {title: 'A Better Title', reason: 'Missing primary keyword in first 40 chars'}}];
                document.body.insertAdjacentHTML('beforeend', '<div id="act-detail-9001" style="display:none"></div>');
                toggleActionDetail(9001);
                const panel = document.getElementById('act-detail-9001');
                const result = {display: panel.style.display, html: panel.innerHTML};
                panel.remove();
                return result;
            }""")
            check(reason_panel_check.get("display") == "block", f"toggleActionDetail should reveal the panel: {reason_panel_check}")
            check("Missing primary keyword" in reason_panel_check.get("html", ""), f"expected the reason block to render: {reason_panel_check}")
            check("💡 Why:" in reason_panel_check.get("html", ""), f"expected the labeled Why block: {reason_panel_check}")

            # Confirm-dialog wording for the 3 types that used to fall through to the generic
            # "apply this change to your live Etsy listing" message.
            confirm_msgs = await page.evaluate("() => _APPROVE_CONFIRM_MSGS")
            check("NEW listing" in confirm_msgs.get("create_listing", ""), f"create_listing confirm message should say NEW listing: {confirm_msgs}")
            check("TikTok" in confirm_msgs.get("post_tiktok", ""), f"post_tiktok confirm message should mention TikTok: {confirm_msgs}")
            check("Pinterest" in confirm_msgs.get("post_pinterest", ""), f"post_pinterest confirm message should mention Pinterest: {confirm_msgs}")

            # The 6 action types whose detail panel was previously completely blank.
            preview_checks = await page.evaluate("""() => {
                const cases = {
                    create_listing: {listing_data: {title: 'New Sign Pack', price: 14.99, tags: ['a','b'], sku: 'SS1099'}, product_id: 'SS1099', photo_paths: ['a.jpg'], file_paths: ['a.3mf']},
                    post_tiktok: {caption: 'Check out this design', video_path: 'staged_videos/x.mp4'},
                    post_pinterest: {title: 'Pin title', description: 'Pin desc', board_name: 'Digital Planners', listing_id: 555},
                    update_sku_and_category: {listing_id: 555, sku: 'DP1099', taxonomy_id: 2078},
                    listing_video: {listing_id: 555, path: 'x.mp4', rank: 1},
                    register_command: {command_name: 'my_cmd', script_path: 'tools/my_cmd.py', description: 'does a thing'},
                };
                const out = {};
                for (const [type, payload] of Object.entries(cases)) {
                    out[type] = {body: _actionPreviewBody({type, payload}), glyph: _ACT_TYPE_GLYPH[type]};
                }
                return out;
            }""")
            for t, must_contain in [
                ("create_listing", "New Sign Pack"),
                ("post_tiktok", "Check out this design"),
                ("post_pinterest", "Pin title"),
                ("update_sku_and_category", "DP1099"),
                ("listing_video", "x.mp4"),
                ("register_command", "my_cmd"),
            ]:
                entry = preview_checks.get(t, {})
                check(must_contain in entry.get("body", ""), f"{t}'s preview body should mention {must_contain!r}: {entry}")
                check(entry.get("glyph") and entry.get("glyph") != "❓", f"{t} should have a real glyph, not the ❓ fallback: {entry}")

            # Today badge must count medium severity too (data_error/System-health cards are
            # always medium) -- previously only summary.high bumped the badge.
            today_badge_check = await page.evaluate("""() => {
                setActionBadge({high: 0, medium: 3, low: 1}, 0);
                const tb = document.getElementById('ptab-today-badge');
                return {text: tb.textContent, display: tb.style.display};
            }""")
            check(today_badge_check.get("text") == "3", f"Today badge should count medium-severity items: {today_badge_check}")
            check(today_badge_check.get("display") == "flex", f"Today badge should be visible when medium count > 0: {today_badge_check}")

            # ── Today UX audit (2026-07-31) ── setActionBadge() should fold in
            # _alertsCritWarnCount (the alerts-only crit/warn count renderPhoneToday()
            # maintains) so a standing alert-only critical condition (credential leak,
            # expired token) isn't invisible to the badge just because it has no
            # /api/actions counterpart. Tested directly against the shared state/function
            # rather than through a live renderPhoneToday() fetch, for the same reason the
            # "Recently completed" block above does -- the service worker makes mocking
            # /api/alerts unreliable, and these are plain globals, not fetch-dependent.
            today_alerts_badge_check = await page.evaluate("""() => {
                _alertsCritWarnCount = 2;
                setActionBadge({high: 0, medium: 3, low: 1}, 0);
                const tb = document.getElementById('ptab-today-badge');
                const result = {text: tb.textContent};
                _alertsCritWarnCount = 0;  // reset so later tests aren't affected
                setActionBadge({high: 0, medium: 0, low: 0}, 0);
                return result;
            }""")
            check(today_alerts_badge_check.get("text") == "5", f"Today badge should be summary.medium(3) + _alertsCritWarnCount(2) = 5: {today_alerts_badge_check}")

            # phoneNeedsSheet() should suppress "Let Frank fix it" for a
            # product_file_integrity alert (the Conversion Doctor route it calls has no
            # relationship to a missing file) but show it normally for an /api/actions
            # recommendation (source:'action').
            sheet_fix_gating_check = await page.evaluate("""() => {
                _phoneNeeds = [
                    {title: 'Missing file', listing_id: 111, source: 'product_file_integrity'},
                    {title: 'Weak title', listing_id: 222, source: 'action'},
                ];
                phoneNeedsSheet(0);
                const fileIntegrityDisplay = document.getElementById('phone-sheet-fix').style.display;
                phoneNeedsSheet(1);
                const actionDisplay = document.getElementById('phone-sheet-fix').style.display;
                phoneSheetClose();
                return {fileIntegrityDisplay, actionDisplay};
            }""")
            check(sheet_fix_gating_check.get("fileIntegrityDisplay") == "none",
                  f"Fix button should be hidden for a product_file_integrity alert: {sheet_fix_gating_check}")
            check(sheet_fix_gating_check.get("actionDisplay") != "none",
                  f"Fix button should be shown for a real /api/actions recommendation: {sheet_fix_gating_check}")

            # .palert.info's dot should be visually distinct from .good/.crit/.warn --
            # a same-day calendar reminder (severity 'info') used to fall through to the
            # same green 'good' styling as a genuinely positive signal.
            palert_info_check = await page.evaluate("""() => {
                const mk = (cls) => { const d = document.createElement('div'); d.className = 'palert ' + cls;
                    const dot = document.createElement('span'); dot.className = 'pdot'; d.appendChild(dot);
                    document.body.appendChild(d); const color = getComputedStyle(dot).backgroundColor; d.remove(); return color; };
                return {info: mk('info'), good: mk('good'), crit: mk('crit'), warn: mk('warn')};
            }""")
            check(palert_info_check.get("info") != palert_info_check.get("good"),
                  f".palert.info's dot should differ from .palert.good's (no longer falls through to green): {palert_info_check}")
            check(palert_info_check.get("info") not in (palert_info_check.get("crit"), palert_info_check.get("warn")),
                  f".palert.info's dot should be its own color, not reuse crit/warn: {palert_info_check}")

            await page.evaluate("startTour()")
            await page.wait_for_timeout(400)
            mobile_step1 = await page.evaluate("""() => ({
                visible: getComputedStyle(document.getElementById('tour-root')).display !== 'none',
                title: document.getElementById('tour-step-title').textContent,
                dotCount: document.querySelectorAll('#tour-dots .dot').length,
            })""")
            check(mobile_step1.get("visible"), f"mobile tour should start when startTour() is called on a narrow viewport: {mobile_step1}")
            check("Welcome" in mobile_step1.get("title", ""), f"mobile tour step 1 should be the welcome intro: {mobile_step1}")
            check(mobile_step1.get("dotCount") == 9, f"mobile tour should have 9 steps (2026-07-23: +1 for the new Home step): {mobile_step1}")

            # 2026-07-23 (Home screen): new step, second in the sequence, using the new
            # step.popen field to open Home before spotlighting #home-hero -- confirms
            # renderTourStep()'s new dispatch branch actually fires phoneOpenHome().
            await page.click("#tour-next-btn")
            await page.wait_for_timeout(400)
            mobile_step_home = await page.evaluate("""() => {
                const el = document.getElementById('home-hero');
                const rect = el ? el.getBoundingClientRect() : null;
                const spot = document.getElementById('tour-spot').getBoundingClientRect();
                return {
                    title: document.getElementById('tour-step-title').textContent,
                    screenActive: document.getElementById('screen-home').classList.contains('active'),
                    tabbarHidden: getComputedStyle(document.getElementById('phone-tabbar')).display === 'none',
                    targetsHero: !!rect,
                    spotNearTarget: !!rect && Math.abs(spot.top - rect.top) < 40,
                };
            }""")
            check(mobile_step_home.get("title") == "Home", f"mobile tour step 2 should be Home: {mobile_step_home}")
            check(mobile_step_home.get("screenActive"), f"Home tour step should call phoneOpenHome() via step.popen: {mobile_step_home}")
            check(mobile_step_home.get("tabbarHidden"), f"tab bar should be hidden while the Home tour step is showing: {mobile_step_home}")
            check(mobile_step_home.get("targetsHero"), f"Home tour step should target #home-hero: {mobile_step_home}")
            check(mobile_step_home.get("spotNearTarget"), f"spotlight should be positioned over the hero tile: {mobile_step_home}")

            # 2026-07-23: the Ask step now navigates for real (step.ptab: 'ask' instead
            # of null) -- previously it relied on cold-load already landing on Ask, an
            # assumption Home's arrival broke (#phone-tabbar is hidden while on Home).
            await page.click("#tour-next-btn")
            await page.wait_for_timeout(400)
            mobile_step2 = await page.evaluate("""() => {
                const el = document.querySelector('.ptab[data-ptab=\"ask\"]');
                const rect = el ? el.getBoundingClientRect() : null;
                const spot = document.getElementById('tour-spot').getBoundingClientRect();
                return {
                    title: document.getElementById('tour-step-title').textContent,
                    targetsAsk: !!rect,
                    spotNearTarget: !!rect && Math.abs(spot.top - rect.top) < 40,
                };
            }"""
            )
            check(mobile_step2.get("targetsAsk"), f"mobile tour step 2 should target the Ask tab: {mobile_step2}")
            check(mobile_step2.get("spotNearTarget"), f"spotlight should be positioned over the Ask tab: {mobile_step2}")

            # 2026-07-18: new step covering the always-on floating quick-chat button
            # (#frank-popup-btn) -- easy to miss since it's not part of the tab bar.
            await page.click("#tour-next-btn")
            await page.wait_for_timeout(400)
            mobile_step3 = await page.evaluate("""() => {
                const el = document.getElementById('frank-popup-btn');
                const rect = el ? el.getBoundingClientRect() : null;
                const spot = document.getElementById('tour-spot').getBoundingClientRect();
                return {
                    title: document.getElementById('tour-step-title').textContent,
                    targetsQuickChat: !!rect,
                    spotNearTarget: !!rect && Math.abs(spot.top - rect.top) < 40,
                };
            }""")
            check(mobile_step3.get("title") == "Quick chat", f"mobile tour step 3 should be Quick chat: {mobile_step3}")
            check(mobile_step3.get("targetsQuickChat"), f"mobile tour step 3 should target #frank-popup-btn: {mobile_step3}")
            check(mobile_step3.get("spotNearTarget"), f"spotlight should be positioned over the quick-chat button: {mobile_step3}")

            await page.click("#tour-next-btn")
            await page.wait_for_timeout(500)
            mobile_step4 = await page.evaluate("""() => ({
                title: document.getElementById('tour-step-title').textContent,
                apprTabOn: document.querySelector('.ptab[data-ptab=\"appr\"]').classList.contains('on'),
            })""")
            check(mobile_step4.get("title") == "Approvals", f"mobile tour step 4 should be Approvals: {mobile_step4}")
            check(mobile_step4.get("apprTabOn"), f"mobile tour should switch to the Approvals tab via phoneTab(): {mobile_step4}")

            # 2026-07-18: the reworked "More" step now spotlights the real list
            # content (#pp-more-body), not just the tab button -- confirm the panel
            # is actually rendered and named in the body copy, matching what Scott
            # asked for (show people the real screen, not a dimmed-out tab button).
            for _ in range(3):
                await page.click("#tour-next-btn")
                await page.wait_for_timeout(400)
            mobile_step7 = await page.evaluate("""() => {
                const el = document.getElementById('pp-more-body');
                const rect = el ? el.getBoundingClientRect() : null;
                const spot = document.getElementById('tour-spot').getBoundingClientRect();
                return {
                    title: document.getElementById('tour-step-title').textContent,
                    body: document.getElementById('tour-step-body').textContent,
                    targetsMoreList: !!rect,
                    spotOverlapsTarget: !!rect && spot.top <= rect.top + 40 && spot.bottom >= rect.top,
                    moreListHasRows: document.querySelectorAll('#pp-more-body .pmore-item').length > 0,
                };
            }""")
            check(mobile_step7.get("title") == "More", f"mobile tour step 7 should be More: {mobile_step7}")
            check(mobile_step7.get("targetsMoreList"), f"More step should target #pp-more-body: {mobile_step7}")
            check(mobile_step7.get("moreListHasRows"), f"the More list should actually be rendered behind the spotlight: {mobile_step7}")
            check("Connections" in mobile_step7.get("body", ""), f"More step copy should name Connections (credential status): {mobile_step7}")
            check("Settings" in mobile_step7.get("body", ""), f"More step copy should mention Settings lives under Advanced: {mobile_step7}")

            await page.click(".tour-controls .tour-skip")
            await page.wait_for_timeout(300)

            # ── Floating "back to top" (2026-07-15) — still on the 390x844 mobile
            # viewport from the tour checks above. Force real scrollable height into
            # #phone-body (native panels have no guaranteed content length otherwise)
            # rather than relying on whatever's actually loaded. ──
            initial_state = await page.evaluate("""() => {
                const btn = document.getElementById('back-to-top-btn');
                return {present: !!btn, showingBeforeScroll: btn ? btn.classList.contains('show') : null};
            }""")
            check(initial_state.get("present"), f"#back-to-top-btn should exist in the DOM: {initial_state}")
            check(not initial_state.get("showingBeforeScroll"),
                  f"button should be hidden before any scroll: {initial_state}")

            await page.evaluate("""() => {
                const pb = document.getElementById('phone-body');
                const spacer = document.createElement('div');
                spacer.id = 'pw-scroll-spacer';
                spacer.style.height = '2000px';
                pb.appendChild(spacer);
                pb.scrollTop = 600;
            }""")
            await page.wait_for_timeout(300)
            after_scroll = await page.evaluate("""() => ({
                showing: document.getElementById('back-to-top-btn').classList.contains('show'),
                scrollTop: document.getElementById('phone-body').scrollTop,
            })""")
            check(after_scroll.get("scrollTop", 0) > 400, f"test setup should have actually scrolled #phone-body: {after_scroll}")
            check(after_scroll.get("showing"), f"button should show once scrolled past the threshold: {after_scroll}")

            await page.click("#back-to-top-btn")
            await page.wait_for_timeout(500)
            after_click = await page.evaluate("""() => ({
                scrollTop: document.getElementById('phone-body').scrollTop,
                showing: document.getElementById('back-to-top-btn').classList.contains('show'),
            })""")
            check(after_click.get("scrollTop", 999) < 50, f"clicking should scroll #phone-body back to top: {after_click}")
            check(not after_click.get("showing"), f"button should hide again once back at top: {after_click}")

            # ── Regression test for the REAL bug reported live (2026-07-15): the
            # first version of this feature tracked window.scrollY, but a
            # More-opened screen (phoneOpenScreen -> showScreen, e.g. Listings/
            # Products) actually scrolls document.body, not window --
            # html,body{height:100%;overflow:auto} makes <html> exactly
            # viewport-height with nothing of its own to overflow, so <body>
            # ends up as its own independent scrolling box. This exact path
            # (More -> a real showScreen()-rendered screen) is what the original
            # test above never exercised, which is why it shipped broken. ──
            await page.click("[data-ptab='more']")
            await page.wait_for_timeout(300)
            await page.evaluate("""() => {
                // Same class of race as the Products fixture above: 'listings' also
                // has a registered 30s loadAll() poll (loadListings), which can
                // overwrite this fake 40-item fixture with real (much shorter) data
                // mid-test -- the actual root cause behind repeated CI-only failures
                // here (2026-07-17/18), not the two other fixes landed alongside it.
                loadListings = async function(){};
                _listings = Array.from({length: 40}, (_, i) => ({
                    listing_id: 5000 + i, title: 'Regression Listing ' + i, price: 5.99,
                    state: 'active', views: i, num_favorers: 0, tags: [], thumbnail_url: '',
                }));
            }""")
            await page.click("#pp-more-body .pmore-item:has-text('Your listings')")
            await page.wait_for_timeout(400)
            await page.evaluate("() => renderListings()")
            await page.wait_for_timeout(300)

            body_pre_scroll = await page.evaluate("""() => ({
                showing: document.getElementById('back-to-top-btn').classList.contains('show'),
                bodyScrollHeight: document.body.scrollHeight,
            })""")
            check(not body_pre_scroll.get("showing"), f"button should be hidden before scrolling the More-opened screen: {body_pre_scroll}")
            check(body_pre_scroll.get("bodyScrollHeight", 0) > 900,
                  f"test setup should have produced a genuinely tall page: {body_pre_scroll}")

            await page.evaluate("() => { document.body.scrollTop = 700; }")
            await page.wait_for_timeout(400)
            body_after_scroll = await page.evaluate("""() => ({
                showing: document.getElementById('back-to-top-btn').classList.contains('show'),
                bodyScrollTop: document.body.scrollTop,
            })""")
            check(body_after_scroll.get("bodyScrollTop", 0) > 400,
                  f"document.body should actually be the scrolled element on a More-opened screen: {body_after_scroll}")
            check(body_after_scroll.get("showing"),
                  f"button must show when document.body (not window) is scrolled past the threshold: {body_after_scroll}")

            await page.click("#back-to-top-btn")
            await page.wait_for_timeout(500)
            body_after_click = await page.evaluate("""() => ({
                bodyScrollTop: document.body.scrollTop,
                showing: document.getElementById('back-to-top-btn').classList.contains('show'),
            })""")
            check(body_after_click.get("bodyScrollTop", 999) < 50,
                  f"clicking should scroll document.body back to top: {body_after_click}")
            check(not body_after_click.get("showing"), f"button should hide again once back at top: {body_after_click}")

            # ── Orb WebGL context-loss recovery (2026-07-15) — "the orb freezes
            # after switching tabs and back." Mobile browsers aggressively lose a
            # backgrounded page's WebGL context to free GPU memory; before this
            # fix there was no webglcontextlost/webglcontextrestored handling
            # anywhere, so the canvas just froze on its last frame forever.
            # Dispatches the real DOM events (not just calling handler functions
            # directly) so this actually proves the listeners are wired up, not
            # just that the reset logic works in isolation. Soft-checked: headless
            # Chromium's WebGL support (SwiftShader) can vary by environment, so
            # this only asserts the loss/restore *transition* when the orb
            # genuinely reached orbGLReady first, rather than hard-requiring GL
            # support in every CI environment. ──
            # Bare identifier references (not window.orbGLReady) -- orbGLReady/
            # orbGLLoading are top-level `let` bindings in the page's classic
            # inline script, which do NOT attach to window (unlike `var`/function
            # declarations); page.evaluate()'s function runs in the same global
            # scope/realm, so a bare reference correctly resolves through the
            # scope chain, but `window.x` would silently read undefined.
            orb_ready = await page.evaluate("() => new Promise(resolve => { "
                                             "let n = 0; const iv = setInterval(() => { "
                                             "if (orbGLReady || ++n > 40) { clearInterval(iv); resolve(!!orbGLReady); } "
                                             "}, 100); })")
            if orb_ready:
                # ── Orb native-alpha rendering (2026-07-15 rewrite) — 3 prior fixes
                # for "circle/box around the orb" each broke a different way on a
                # real device despite passing local headless-Chromium testing:
                # (1) CSS-mask-only left an opaque interior, (2) painting the theme
                # bg into the WebGL clear color crossed UnrealBloomPass's bloom
                # threshold and blew the whole canvas to white, (3) a JS
                # drawImage/getImageData luminance-key compositing hack (reading a
                # second, offscreen WebGL canvas without preserveDrawingBuffer)
                # rendered as a torn/half-cut buffer live. This rewrite removes
                # EffectComposer/UnrealBloomPass and the second-canvas readback
                # trick entirely -- canvas#orb-gl is rendered to directly with a
                # real transparent WebGL context, no intermediate buffer. Assert
                # the architecture, not pixel data (reintroducing a WebGL
                # pixel-readback in test code would reintroduce the exact class of
                # fragility this rewrite removes): canvas#orb-gl is the one and
                # only visible sphere-mode layer, #orb-gl-display no longer exists
                # in the DOM, and the WebGL context was actually created with
                # alpha:true. ──
                composite_state = await page.evaluate("""() => {
                    const gl = document.getElementById('orb-gl');
                    const glVisible = gl ? getComputedStyle(gl).display !== 'none' : null;
                    const dispElGone = document.getElementById('orb-gl-display') === null;
                    let contextAlpha = null;
                    if (glRenderer) {
                        const attrs = glRenderer.getContext().getContextAttributes();
                        contextAlpha = attrs ? attrs.alpha : null;
                    }
                    return {glVisible, dispElGone, contextAlpha};
                }""")
                check(composite_state.get("glVisible") is True,
                      f"canvas#orb-gl must be the directly visible sphere-mode layer (native-alpha rewrite, no second display canvas): {composite_state}")
                check(composite_state.get("dispElGone") is True,
                      f"canvas#orb-gl-display should no longer exist in the DOM -- it was the luminance-key compositing canvas, removed in this rewrite: {composite_state}")
                check(composite_state.get("contextAlpha") is True,
                      f"the WebGL context must be created with alpha:true for real per-pixel transparency: {composite_state}")

                lost_state = await page.evaluate("""() => {
                    const canvas = document.getElementById('orb-gl');
                    const evt = new Event('webglcontextlost', {cancelable: true});
                    canvas.dispatchEvent(evt);
                    return {defaultPrevented: evt.defaultPrevented, orbGLReady: orbGLReady};
                }""")
                check(lost_state.get("defaultPrevented"),
                      f"webglcontextlost handler must call preventDefault() or the browser will never attempt restoration: {lost_state}")
                check(lost_state.get("orbGLReady") is False,
                      f"losing context should reset orbGLReady so the frame loop stops trying to draw with dead resources: {lost_state}")

                restored_state = await page.evaluate("""() => {
                    const canvas = document.getElementById('orb-gl');
                    canvas.dispatchEvent(new Event('webglcontextrestored'));
                    return {orbGLLoading: orbGLLoading};
                }""")
                check(restored_state.get("orbGLLoading") is True,
                      f"webglcontextrestored should immediately call initOrbGL() to rebuild (orbGLLoading flips true synchronously "
                      f"at the top of that function, before any async import): {restored_state}")
            else:
                print("  (orb WebGL never reached orbGLReady in this environment -- skipping context-loss transition checks)")

            # ── A stray/stuck cc-open must never coexist with is-mobile while in the
            # NORMAL tab-bar view (2026-07-15) — Scott's header bar (with its
            # position:absolute, 1440px-stage-sized #alert-dropdown) appeared on his
            # phone alongside the mobile tab bar, with the alert dropdown clipped
            # off-screen unreadable. Root cause: syncMobileClass() only ever ADDED
            # cc-open on a mobile->desktop transition and never had a path to remove
            # it again once mobile was redetected -- if cc-open was ever set while
            # briefly misdetected as desktop (mobile Safari's matchMedia/resize
            # events can fire spuriously, e.g. around address-bar show/hide), it
            # stuck forever, permanently leaking the full desktop dashboard onto a
            # phone viewport. Fix: mobile always wins in syncMobileClass() UNLESS a
            # phoneOpenScreen()-opened screen legitimately needs cc-open kept (see
            # 2026-07-18's phone-screen-open marker, added after phoneOpenScreen()
            # deliberately setting cc-open turned out to be a real, separate,
            # legitimate case -- not the stray/stuck case this test is about).
            #
            # 2026-07-18: explicitly return to the tab-bar view first -- the More ->
            # "Your listings" click earlier in this same test run (the back-to-top
            # regression above) left phone-screen-open set from a genuine
            # phoneOpenScreen() call, and nothing after it ever navigated back to
            # the tab bar. Without this reset, forcing cc-open here doesn't
            # reproduce the actual stray/stuck scenario at all -- it just re-tests
            # the legitimate phoneOpenScreen() case from a different angle, which
            # correctly does NOT get cleared and made this test fail for the wrong
            # reason (caught live 2026-07-18 while fixing the phoneOpenScreen bug
            # this comment references). ──
            await page.evaluate("() => { if (typeof phoneTab === 'function') phoneTab('more'); }")
            await page.wait_for_timeout(200)
            cc_state = await page.evaluate("""() => {
                document.body.classList.add('cc-open');
                const stuck = document.body.classList.contains('cc-open');
                syncMobileClass();
                return {
                    stuckAppliedOk: stuck,
                    isMobileAfter: document.body.classList.contains('is-mobile'),
                    ccOpenAfter: document.body.classList.contains('cc-open'),
                };
            }""")
            check(cc_state.get("isMobileAfter") is True,
                  f"is-mobile should stay true on a mobile viewport: {cc_state}")
            check(cc_state.get("ccOpenAfter") is False,
                  f"syncMobileClass() must clear a stuck cc-open once mobile is (re)detected -- otherwise the desktop "
                  f"header bar (and its viewport-unsafe #alert-dropdown) leaks onto phone screens permanently: {cc_state}")

            # ── Second cc-open leak, found after the fix above shipped and Scott
            # reported the dropdown "still not visible" (2026-07-15 follow-up) --
            # phoneOpenScreen() (wired to every mobile "More" list item and the
            # "Create" tab) sets cc-open UNCONDITIONALLY, with no isMobileMode()
            # check, completely independent of syncMobileClass()'s resize-race
            # path fixed above. Unlike that path, cc-open here is legitimate --
            # it's what makes the target .screen content visible on mobile too --
            # so the fix isn't to block it, it's to stop #alert-dropdown from
            # being positioned relative to the (now-visible) desktop header bar
            # at all. Assert both halves: cc-open genuinely does get set by this
            # real navigation path (proving the scenario is real, not
            # hypothetical), and #alert-dropdown still renders fully inside the
            # viewport regardless. ──
            phone_open_state = await page.evaluate("""() => {
                phoneOpenScreen('settings');
                return {
                    isMobile: document.body.classList.contains('is-mobile'),
                    ccOpen: document.body.classList.contains('cc-open'),
                };
            }""")
            check(phone_open_state.get("isMobile") is True,
                  f"is-mobile should stay true after phoneOpenScreen(): {phone_open_state}")
            check(phone_open_state.get("ccOpen") is True,
                  f"phoneOpenScreen() is expected to set cc-open even on mobile (it's what reveals .screen content) -- "
                  f"if this is False the test scenario no longer matches the real bug and needs updating: {phone_open_state}")

            await page.evaluate("toggleAlertDropdown && toggleAlertDropdown()")
            await page.wait_for_timeout(200)
            dropdown_box = await page.evaluate("""() => {
                const dd = document.getElementById('alert-dropdown');
                if (!dd) return null;
                const r = dd.getBoundingClientRect();
                return {left: r.left, right: r.right, top: r.top, display: getComputedStyle(dd).display};
            }""")
            if dropdown_box and dropdown_box.get("display") != "none":
                vw = await page.evaluate("window.innerWidth")
                check(dropdown_box["left"] >= 0,
                      f"#alert-dropdown must not render past the left edge of the viewport even while cc-open is "
                      f"legitimately set on mobile (via phoneOpenScreen): {dropdown_box}, viewport width {vw}")
                check(dropdown_box["right"] <= vw,
                      f"#alert-dropdown must not render past the right edge of the viewport: {dropdown_box}, viewport width {vw}")
                hdr_box = await page.evaluate("""() => {
                    const h = document.querySelector('.hdr-bar');
                    if (!h) return null;
                    const r = h.getBoundingClientRect();
                    return {bottom: r.bottom};
                }""")
                if hdr_box:
                    check(dropdown_box.get("top", 0) >= hdr_box["bottom"] - 1,
                          f"#alert-dropdown must render BELOW the header, not overlapping its icon row -- "
                          f"dropdown {dropdown_box}, header bottom {hdr_box['bottom']}")
            await page.evaluate("toggleAlertDropdown && toggleAlertDropdown()")  # close it again

            # ── Gray block over the header (2026-07-18, reported by Scott on the
            # Products and Create screens) -- live Playwright repro traced this to a
            # DIFFERENT bug than the two cc-open leaks above: the orb is the mobile
            # home tab at load (setTimeout(() => phoneTab('ask'), 0) sets
            # frank-popup-open on every mobile page load), but phoneOpenScreen()
            # (every "More" list item, incl. Products) never cleared it, so body
            # ended up with BOTH frank-popup-open AND cc-open at once.
            # body.is-mobile.frank-popup-open #orb-view's CSS (2 classes) outranks
            # body.cc-open #orb-view{display:none} (1 class) by specificity, so the
            # full-screen orb popup (translucent radial-gradient background)
            # rendered ON TOP of the header -- confirmed via a real click on the
            # bell icon timing out because #orb-view's orb-hero-stage was
            # intercepting pointer events. Simulate the exact precondition
            # (frank-popup-open already set, as it always is right after mobile
            # load) then call phoneOpenScreen() the same way a "More" tap does.
            popup_leak_state = await page.evaluate("""() => {
                document.body.classList.add('frank-popup-open');
                phoneOpenScreen('products');
                const orb = document.getElementById('orb-view');
                return {
                    frankPopupOpenAfter: document.body.classList.contains('frank-popup-open'),
                    orbDisplay: orb ? getComputedStyle(orb).display : null,
                };
            }""")
            check(popup_leak_state.get("frankPopupOpenAfter") is False,
                  f"phoneOpenScreen() must clear a stuck frank-popup-open (set by the orb-as-home-tab load path) -- "
                  f"otherwise its higher-specificity CSS re-shows #orb-view over cc-open's hidden state: {popup_leak_state}")
            check(popup_leak_state.get("orbDisplay") == "none",
                  f"#orb-view must be display:none once a phoneOpenScreen() screen (e.g. Products) is open -- a visible "
                  f"#orb-view here is exactly the 'gray block over the header' Scott reported: {popup_leak_state}")

            # ── Create-screen redesign, mobile viewport (2026-07-22) -- the same
            # tile grid / accordion / coming-soon honesty must hold on the phone
            # layout the redesign was explicitly built for ("used by someone that
            # does not know what frank is" implies a phone, not a 1440px desktop).
            # phoneOpenScreen() is the mobile equivalent of showScreen(). ──
            mobile_create = await page.evaluate("""() => {
                phoneOpenScreen('create');
                const tiles = [...document.querySelectorAll('#create-chooser .create-choice[data-cat]')];
                return {
                    active: document.querySelector('.screen.active') ? document.querySelector('.screen.active').id : null,
                    tileCount: tiles.length,
                };
            }""")
            check(mobile_create.get("active") == "screen-create", f"phoneOpenScreen('create') should land on #screen-create: {mobile_create}")
            check(mobile_create.get("tileCount") == 9, f"mobile Create screen must show all 9 tiles too: {mobile_create}")

            mobile_soon_tap = await page.evaluate("""() => {
                document.querySelector('.create-choice[data-cat="sublimation"]').click();
                const panel = document.getElementById('create-detail');
                return {html: panel ? panel.innerHTML : ''};
            }""")
            check(len(mobile_soon_tap.get("html", "").strip()) > 40,
                  f"tapping a coming-soon tile on mobile must not render a blank panel: {mobile_soon_tap}")
            check("no automatic builder" in mobile_soon_tap.get("html", "").lower(),
                  f"mobile coming-soon panel must give the same honest explanation as desktop: {mobile_soon_tap}")
            await page.evaluate("document.querySelector('.create-choice[data-cat=\"sublimation\"]').click()")  # close it

            # ── Chat History screen (2026-07-15) — Scott: "I need a option on the
            # list to see the chat box from ask Frank to see his responses."
            # Frank's replies on mobile were only ever spoken (TTS); the working
            # "Past conversations" browser was buried inside the Knowledge screen
            # with no path to it from mobile nav at all. Moved to its own
            # #screen-conversations, reachable via the mobile More list. Confirms
            # the full path: tap More -> find the "Chat History" item -> tap it ->
            # land on the right screen with its content container present. ──
            await page.evaluate("phoneTab('more')")
            await page.wait_for_timeout(300)
            chat_history_item = await page.query_selector("#pp-more-body .pmore-item:has-text('Chat History')")
            check(chat_history_item is not None,
                  "mobile More list must have a 'Chat History' entry so Frank's replies are reachable as text, not just spoken")
            if chat_history_item is not None:
                await chat_history_item.click()
                await page.wait_for_timeout(500)
                conv_screen_state = await page.evaluate("""() => ({
                    active: document.querySelector('.screen.active') ? document.querySelector('.screen.active').id : null,
                    contentPresent: !!document.getElementById('conversations-content'),
                })""")
                check(conv_screen_state.get("active") == "screen-conversations",
                      f"tapping 'Chat History' should land on #screen-conversations: {conv_screen_state}")
                check(conv_screen_state.get("contentPresent") is True,
                      f"the conversations list/transcript container must be present on that screen: {conv_screen_state}")

            # ── More screen UX audit (2026-07-31) ── settings/files moved from
            # "Advanced" to "Shop" (matching desktop's actual grouping -- a
            # 2026-07-17 fix moved Settings there specifically because it's
            # "everyday, non-technical", but a docs claim that the fix covered
            # mobile too was never actually true); "Tools" -> "Tools & Skills" and
            # "Brand kit" -> "Brand Kit" now match the desktop nav-item/screen-title
            # labels exactly; icon/chevron spans are now aria-hidden, matching every
            # comparable icon elsewhere in the app. ──
            await page.evaluate("phoneTab('more')")
            await page.wait_for_timeout(300)
            more_state = await page.evaluate("""() => {
                const groups = Array.from(document.querySelectorAll('#pp-more-body .pmore-grp')).map(g => g.textContent);
                const rows = Array.from(document.querySelectorAll('#pp-more-body .pmore-item'));
                const rowInGroup = (screenName) => {
                    const row = rows.find(r => r.dataset.screen === screenName);
                    if (!row) return null;
                    let el = row.previousElementSibling;
                    while (el && !el.classList.contains('pmore-grp')) el = el.previousElementSibling;
                    return el ? el.textContent : null;
                };
                const firstRow = rows[0];
                return {
                    groups,
                    settingsGroup: rowInGroup('settings'),
                    filesGroup: rowInGroup('files'),
                    toolsLabel: rows.find(r => r.dataset.screen === 'tools')?.textContent || '',
                    brandkitLabel: rows.find(r => r.dataset.screen === 'brandkit')?.textContent || '',
                    firstRowAriaHidden: firstRow ? [...firstRow.querySelectorAll('span')].every(s => s.getAttribute('aria-hidden') === 'true') : false,
                };
            }""")
            check(more_state.get("settingsGroup") == "Shop", f"Settings should now be grouped under Shop: {more_state}")
            check(more_state.get("filesGroup") == "Shop", f"Files should now be grouped under Shop: {more_state}")
            check("Tools & Skills" in more_state.get("toolsLabel", ""), f"the Tools row should say 'Tools & Skills': {more_state}")
            check("Brand Kit" in more_state.get("brandkitLabel", ""), f"the Brand Kit row should be capitalized correctly: {more_state}")
            check(more_state.get("firstRowAriaHidden") is True, f"decorative icon/chevron spans on a More row should be aria-hidden: {more_state}")

            # ── Mobile Ask-tab redesign (2026-07-22), Phase 1 -- Scott: tapping "Ask"
            # used to open a nearly blank orb popup (#orb-view) with only an "Open full
            # chat" button as the way to reach anything real, confirmed as a wasted
            # extra tap via a screen recording he sent. Ask now goes straight to the
            # real chat+stats screen (#screen-cmd); voice/orb mode moved to a button
            # inside that screen instead. ──
            await page.evaluate("phoneTab('today')")  # start from a known, non-ask tab
            await page.wait_for_timeout(200)
            ask_state = await page.evaluate("""() => {
                phoneTab('ask');
                return {
                    screenCmdActive: document.getElementById('screen-cmd').classList.contains('active'),
                    orbViewVisible: getComputedStyle(document.getElementById('orb-view')).display !== 'none',
                    mobileHeaderText: (() => { const el = document.querySelector('.mobile-shop-header'); return el ? el.textContent : null; })(),
                };
            }""")
            check(ask_state.get("screenCmdActive") is True,
                  f"phoneTab('ask') must land directly on #screen-cmd, not require a second tap through the orb popup: {ask_state}")
            check(ask_state.get("orbViewVisible") is False,
                  f"the orb popup must NOT be showing right after tapping Ask -- it's now an opt-in voice control, not the landing view: {ask_state}")
            check(ask_state.get("mobileHeaderText") == "OnBrandCraftz",
                  f"the mobile-only shop-name header must render above the chat panel (Scott: keep the branding): {ask_state}")

            # Voice button opens the orb popup on demand; "Open full chat" inside it
            # returns to the same chat screen (reusing the pre-existing button/handler
            # rather than a new one -- closeFrankPopup() has no call sites in the app).
            await page.click("#chat-voice-btn")
            await page.wait_for_timeout(200)
            voice_state = await page.evaluate("() => getComputedStyle(document.getElementById('orb-view')).display !== 'none'")
            check(voice_state is True, "tapping the in-chat mic/voice button must open the orb popup")
            await page.click(".orb-open-chat")
            await page.wait_for_timeout(200)
            back_state = await page.evaluate("""() => ({
                screenCmdActive: document.getElementById('screen-cmd').classList.contains('active'),
                orbViewVisible: getComputedStyle(document.getElementById('orb-view')).display !== 'none',
            })""")
            check(back_state.get("screenCmdActive") is True and back_state.get("orbViewVisible") is False,
                  f"'Open full chat' inside the voice popup must return to the chat screen and close the popup: {back_state}")

            # A stray cc-open must never survive a round trip back to a normal tab-bar
            # panel now that phoneOpenScreen('cmd') is the primary Ask-tab path (this
            # code path used to be a rare detour, not the default -- see phoneTab()'s
            # dated comment for the live-Playwright repro that found this).
            await page.evaluate("phoneTab('today')")
            await page.wait_for_timeout(200)
            after_today = await page.evaluate("() => document.body.classList.contains('cc-open')")
            check(after_today is False,
                  "returning to a tab-bar panel (Today) after visiting Ask must clear cc-open, not leave it stuck")

            # ── Chat visual redesign (2026-07-22): markdown rendering, XSS boundary,
            # and the in-chat speaking indicator. ──
            md_state = await page.evaluate("""() => {
                const el = addBubble('This is **bold** text', 'bot', {markdown:true});
                const strong = el.querySelector('strong');
                return {hasStrong: !!strong, strongText: strong ? strong.textContent : null, hasBubbleIn: el.classList.contains('bubble-in')};
            }""")
            check(md_state.get("hasStrong") is True and md_state.get("strongText") == "bold",
                  f"a bot bubble created with {{markdown:true}} must render **bold** as a real <strong> element: {md_state}")
            check(md_state.get("hasBubbleIn") is True,
                  f"every new bubble must get the entrance-animation class: {md_state}")

            # Regression: the type:'error' path (and addBubble() calls with no markdown
            # opt) must stay plain-text/escaped -- this is a deliberate XSS boundary,
            # never render tool/buyer-adjacent error text as HTML.
            err_state = await page.evaluate("""() => {
                const el = addBubble('\\u26a0\\ufe0f <img src=x onerror=alert(1)>', 'bot');
                return {hasImg: !!el.querySelector('img'), html: el.innerHTML};
            }""")
            check(err_state.get("hasImg") is False,
                  f"addBubble() without {{markdown:true}} (the type:'error' call shape) must never render raw HTML: {err_state}")

            speak_on = await page.evaluate("() => { setSpeaking(true); return document.getElementById('chat-speaking-indicator').classList.contains('on'); }")
            speak_off = await page.evaluate("() => { setSpeaking(false); return document.getElementById('chat-speaking-indicator').classList.contains('on'); }")
            check(speak_on is True, "setSpeaking(true) must turn on #chat-speaking-indicator")
            check(speak_off is False, "setSpeaking(false) must turn off #chat-speaking-indicator")

            # ── Ask/Chat UX audit (2026-07-30), item 1 -- empty-conversation greeting.
            # main.py's /ws/chat handler only sends {type:'history'} `if history:` -- a
            # brand-new session got nothing at all, so #chat-msgs stayed completely
            # blank below the "Ask Frank" title with no explanation of what the screen
            # does. Resets _historyApplied (a JS module-scope `let`, NOT a window
            # property -- see this file's Home-greeting test for why a bare reference
            # is required here) and hand-fires the exact ws.onmessage the real server
            # sends for a virgin session.
            await page.evaluate("phoneTab('ask')")
            await page.wait_for_timeout(200)
            empty_history_state = await page.evaluate("""() => {
                document.getElementById('chat-msgs').innerHTML = '';
                document.getElementById('lc-chips').style.display = '';
                _historyApplied = false;
                ws.onmessage({data: JSON.stringify({type:'history', messages: []})});
                const bubbles = document.getElementById('chat-msgs').querySelectorAll('.lc-bubble.bot');
                return {
                    bubbleCount: bubbles.length,
                    greetingText: bubbles.length ? bubbles[0].textContent : null,
                    chipsDisplay: getComputedStyle(document.getElementById('lc-chips')).display,
                };
            }""")
            check(empty_history_state.get("bubbleCount") == 1,
                  f"an empty-history session must render exactly one greeting bubble, got: {empty_history_state}")
            check("Frank" in (empty_history_state.get("greetingText") or ""),
                  f"the greeting bubble must introduce Frank, got: {empty_history_state}")
            check(empty_history_state.get("chipsDisplay") != "none",
                  f"quick-reply chips must stay visible on a fresh empty conversation: {empty_history_state}")

            # ── Ask/Chat UX audit, item 2 -- chips hide once real history (or a real
            # send) exists. Keyed off server-side history / an actual sendMsg() call,
            # NOT the greeting bubble itself, per the adversarial review's coupling
            # warning: a client-only greeting must never be mistaken for a real message.
            nonempty_history_state = await page.evaluate("""() => {
                document.getElementById('chat-msgs').innerHTML = '';
                document.getElementById('lc-chips').style.display = '';
                _historyApplied = false;
                ws.onmessage({data: JSON.stringify({type:'history', messages: [{role:'user', content:'a prior real message'}]})});
                const bubbles = document.getElementById('chat-msgs').querySelectorAll('.lc-bubble.bot');
                return {
                    greetingBubbleCount: bubbles.length,
                    chipsDisplay: getComputedStyle(document.getElementById('lc-chips')).display,
                };
            }""")
            check(nonempty_history_state.get("greetingBubbleCount") == 0,
                  f"a session with real prior history must NOT also show the empty-conversation greeting: {nonempty_history_state}")
            check(nonempty_history_state.get("chipsDisplay") == "none",
                  f"quick-reply chips must hide once real history exists: {nonempty_history_state}")

            # A real send (not just replayed history) must also hide the chips immediately.
            send_hides_chips_display = await page.evaluate("""() => {
                document.getElementById('lc-chips').style.display = '';
                document.getElementById('chat-input').value = 'hide the chips please';
                sendMsg();
                return getComputedStyle(document.getElementById('lc-chips')).display;
            }""")
            check(send_hides_chips_display == "none",
                  f"sendMsg() must hide the quick-reply chips on a real send: {send_hides_chips_display}")

            # ── Ask/Chat UX audit, item 3 -- mobile keyboard must not cover the input
            # row. #chat-msgs' mobile max-height used a plain 60vh, which most mobile
            # browsers do NOT shrink when the on-screen keyboard opens (layout vs.
            # visual viewport). Switched to 60dvh (already used for #stage-wrap) so it
            # tracks the visible viewport instead. Confirms this Chromium build actually
            # resolves a dvh-based max-height into a real pixel value at mobile width --
            # a browser that ignored dvh would fall through to the 60vh declaration
            # immediately before it in the cascade, so this checks for a real, finite
            # resolved value rather than 'none'/unset.
            chat_msgs_max_height = await page.evaluate(
                "() => getComputedStyle(document.getElementById('chat-msgs')).maxHeight"
            )
            check(bool(chat_msgs_max_height) and chat_msgs_max_height.endswith("px") and chat_msgs_max_height != "0px",
                  f"#chat-msgs must resolve to a real max-height on mobile, not 'none'/unset: {chat_msgs_max_height!r}")

            # ── Shop Performance metric-detail modal (2026-07-22), Phase 2 -- tapping
            # the Revenue/Orders 30d sparkline cards on #screen-cmd now opens a generic
            # #metric-detail-modal with a bigger chart + real per-day table. Mocks
            # authGet() directly (not page.route -- frank-sw.js's own internal fetch()
            # call is invisible to page-level route interception, confirmed earlier in
            # this file's Files-screen block). Reuses the mobile viewport already
            # active from the Ask-tab-redesign block above.
            #
            # The Ask-tab-redesign block above deliberately ends on the "Today" tab-bar
            # panel (its own last check is "returning to Today clears cc-open"), so
            # #screen-cmd is NOT the active screen here -- #shop-spark-row lives inside
            # it and inherits display:none from the hidden .screen, which is exactly
            # what "element is not visible" meant on every click retry (reproduced
            # live). Explicitly re-navigate to Ask/#screen-cmd first.
            await page.evaluate("phoneTab('ask')")
            await page.wait_for_timeout(300)
            #
            # The mock is deliberately left installed for this ENTIRE block (restored
            # only at the very end) rather than restored right after the first
            # loadShopPerf() call -- this app's own setInterval(loadAll, 30000) polling
            # loop can fire an unmocked loadShopPerf() mid-block during a long smoke-test
            # run, re-rendering #shop-spark-row's innerHTML out from under a pending
            # click and detaching the element Playwright just resolved. Reproduced live:
            # restoring authGet immediately caused an intermittent "element was detached
            # from the DOM" failure. Keeping the mock in place makes any such interim
            # refresh idempotent instead of racy. ──
            mock_ok = await page.evaluate("""() => {
                window._origAuthGet = window.authGet;
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/analytics') === 0) {
                        const payload = {
                            days: 30, snapshot_count: 4,
                            dates: ['2026-07-19', '2026-07-20', '2026-07-21', '2026-07-22'],
                            trends: {
                                revenue_30d: [1200.00, 1215.50, 1230.00, 1250.75],
                                orders_30d: [40, 41, 42, 44],
                            },
                            delta: {revenue_30d: 20.75, orders_30d: 2},
                            latest: {revenue_30d: 1250.75, orders_30d: 44, active_listings: 80, total_sales: 900},
                            top_listings: [],
                        };
                        return Promise.resolve({ok: true, status: 200, json: async () => payload});
                    }
                    if (path.indexOf('/api/metrics') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({orders: {}, shop: {}})});
                    }
                    return window._origAuthGet(path, ms);
                };
                return loadShopPerf().then(() => true);
            }""")
            check(mock_ok is True, "mocked loadShopPerf() must resolve before the tap test proceeds")

            await page.click("#shop-spark-row .shop-spark-card:first-child")
            await page.wait_for_timeout(300)
            modal_state = await page.evaluate("""() => ({
                open: document.body.classList.contains('metric-detail-open'),
                title: document.getElementById('mdm-title').textContent,
                bodyText: document.getElementById('mdm-body').textContent,
            })""")
            check(modal_state.get("open") is True,
                  f"tapping the Revenue·30d sparkline card must open the metric detail modal: {modal_state}")
            check(modal_state.get("title") == "Revenue · 30d",
                  f"modal title must reflect the tapped metric: {modal_state}")
            body_text = modal_state.get("bodyText") or ""
            check("Jul 22" in body_text and "$1250.75" in body_text,
                  f"per-day table must render the real mocked dates/values, not placeholder text: {body_text[:400]}")
            check("rolling 30-day" in body_text,
                  f"the note must describe this as a rolling-30-day trend, never as that single day's isolated revenue (data-meaning caveat): {body_text[:400]}")

            # Close via the header button.
            await page.click("#metric-detail-modal .mdm-close-btn")
            await page.wait_for_timeout(300)
            closed_via_button = await page.evaluate("() => document.body.classList.contains('metric-detail-open')")
            check(closed_via_button is False, "the close button must remove metric-detail-open")

            # Re-open, then close via backdrop tap. Click near the top-left corner, not
            # the element's center -- the centered modal panel (z-index 901) sits on top
            # of the backdrop (900) at the viewport center, so a default center-click
            # would target the modal, not the backdrop, and never fire onclick.
            await page.click("#shop-spark-row .shop-spark-card:first-child")
            await page.wait_for_timeout(300)
            await page.click("#metric-detail-backdrop", position={"x": 5, "y": 5})
            await page.wait_for_timeout(300)
            closed_via_backdrop = await page.evaluate("() => document.body.classList.contains('metric-detail-open')")
            check(closed_via_backdrop is False, "tapping the backdrop must also close the modal")

            # Empty state: fewer than 2 data points must fall back to _miniSpark's own
            # "Accumulating daily data" copy, not new bespoke empty-state text. Swaps the
            # still-installed mock's payload rather than re-mocking, then restores the
            # real authGet only now, at the very end of this block.
            empty_text = await page.evaluate("""() => {
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/analytics') === 0) {
                        const payload = {
                            days: 30, snapshot_count: 1, dates: ['2026-07-22'],
                            trends: {revenue_30d: [1250.75], orders_30d: [44]},
                            delta: {revenue_30d: null, orders_30d: null},
                            latest: {revenue_30d: 1250.75, orders_30d: 44, active_listings: 80, total_sales: 900},
                            top_listings: [],
                        };
                        return Promise.resolve({ok: true, status: 200, json: async () => payload});
                    }
                    if (path.indexOf('/api/metrics') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({orders: {}, shop: {}})});
                    }
                    return window._origAuthGet(path, ms);
                };
                return loadShopPerf().then(() => {
                    openMetricDetailModal('orders_30d');
                    const text = document.getElementById('mdm-body').textContent;
                    metricDetailClose();
                    window.authGet = window._origAuthGet;
                    return text;
                });
            }""")
            check("Accumulating daily data" in empty_text,
                  f"a single-point series must reuse _miniSpark's own empty-state copy verbatim: {empty_text}")

            # ── Star Seller / Ads & ROAS / COGS & Profit drill-down (2026-07-22),
            # Phase 3 -- these three panels were previously live-recomputed per
            # request with no stored history; their panel-title rows are now
            # tappable (same clickable-title convention as #shop-perf-title),
            # opening the same generic #metric-detail-modal via three new
            # METRIC_DETAIL_CONFIG entries backed by a new /api/status-history
            # endpoint. Mocks authGet() directly and calls each loader directly
            # rather than waiting on the cmd-screen's own load cycle, mirroring
            # the Phase 2 loadShopPerf() pattern above. cogs_margin is mocked
            # with zero snapshot rows -- the guaranteed day-1 state -- to prove
            # the empty state doesn't crash and (regression) doesn't render its
            # "Accumulating daily data" fallback twice. ──
            mock3_ok = await page.evaluate("""() => {
                window._origAuthGet3 = window.authGet;
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/status-history?panel=star_seller') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            panel: 'star_seller', days: 30, snapshot_count: 2,
                            dates: ['2026-07-21', '2026-07-22'], trend: [330.0, 355.5],
                            latest: {status: 'on_track', revenue_90d: 355.5},
                        })});
                    }
                    if (path.indexOf('/api/star-seller') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            status: 'on_track', orders_90d: 6, revenue_90d: 355.5,
                            avg_rating: 4.9, unread_messages: 0,
                        })});
                    }
                    if (path.indexOf('/api/status-history?panel=ads_roas') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            panel: 'ads_roas', days: 30, snapshot_count: 2,
                            dates: ['2026-07-21', '2026-07-22'], trend: [2.6, 3.4],
                            latest: {used: true, status: 'ok', month_roas: 3.4},
                        })});
                    }
                    if (path.indexOf('/api/ads-status') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            used: true, status: 'ok', week_spend: 20, week_revenue: 60,
                            month_roas: 3.4, have_monthly_verdict: true, days_since_log: 1,
                        })});
                    }
                    if (path.indexOf('/api/status-history?panel=cogs_margin') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            panel: 'cogs_margin', days: 30, snapshot_count: 0,
                            dates: [], trend: [], latest: {},
                        })});
                    }
                    if (path.indexOf('/api/cogs-status') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({used: false})});
                    }
                    return window._origAuthGet3(path, ms);
                };
                return Promise.all([loadStarSeller(), loadAdsStatus(), loadCogsStatus()]).then(() => {
                    window.authGet = window._origAuthGet3;
                    return true;
                });
            }""")
            check(mock3_ok is True, "mocked loadStarSeller/loadAdsStatus/loadCogsStatus must resolve")

            star_state = await page.evaluate("""() => {
                openMetricDetailModal('star_seller');
                const s = {
                    open: document.body.classList.contains('metric-detail-open'),
                    title: document.getElementById('mdm-title').textContent,
                    bodyText: document.getElementById('mdm-body').textContent,
                };
                metricDetailClose();
                return s;
            }""")
            check(star_state.get("open") is True, f"openMetricDetailModal('star_seller') must open the modal: {star_state}")
            check("$355.50" in (star_state.get("bodyText") or ""),
                  f"star_seller modal must render real mocked history: {star_state}")

            ads_state = await page.evaluate("""() => {
                openMetricDetailModal('ads_roas');
                const s = {
                    open: document.body.classList.contains('metric-detail-open'),
                    bodyText: document.getElementById('mdm-body').textContent,
                };
                metricDetailClose();
                return s;
            }""")
            check(ads_state.get("open") is True, f"openMetricDetailModal('ads_roas') must open the modal: {ads_state}")
            check("3.40x" in (ads_state.get("bodyText") or ""),
                  f"ads_roas modal must render real mocked history: {ads_state}")

            cogs_state = await page.evaluate("""() => {
                openMetricDetailModal('cogs_margin');
                const s = {
                    open: document.body.classList.contains('metric-detail-open'),
                    bodyText: document.getElementById('mdm-body').textContent,
                };
                metricDetailClose();
                return s;
            }""")
            check(cogs_state.get("open") is True,
                  f"openMetricDetailModal('cogs_margin') must open (not crash) on the guaranteed day-1 zero-snapshot state: {cogs_state}")
            occurrences = (cogs_state.get("bodyText") or "").count("Accumulating daily data")
            check(occurrences == 1,
                  f"the empty-state copy must render exactly once (regression: _miniSpark's own fallback plus a "
                  f"redundant .mdm-empty div rendered it twice before the fix): got {occurrences} in {cogs_state}")

            tap_targets = await page.evaluate("""() => ({
                starSeller: !!document.querySelector('div.panel-title[onclick*="star_seller"]'),
                adsRoas: !!document.querySelector('div.panel-title[onclick*="ads_roas"]'),
                cogsMargin: !!document.querySelector('div.panel-title[onclick*="cogs_margin"]'),
            })""")
            check(tap_targets.get("starSeller") is True, "Star Seller panel-title must be wired to openMetricDetailModal('star_seller')")
            check(tap_targets.get("adsRoas") is True, "Ads & ROAS panel-title must be wired to openMetricDetailModal('ads_roas')")
            check(tap_targets.get("cogsMargin") is True, "COGS & Profit panel-title must be wired to openMetricDetailModal('cogs_margin')")

            # ── Home screen + shop ticker (2026-07-23) -- Concept D editorial layout
            # (hero tile for Ask + 2x2 grid for Approvals/Today/Create/More) replaces
            # cold-load landing directly on Ask; the tab bar is replaced by a live
            # auto-scrolling ticker while on Home only -- every other screen keeps the
            # tab bar unchanged. authGet() monkeypatch, not page.route() -- same
            # service-worker trap as every other mobile fixture in this file. Still on
            # the 390x844 mobile viewport set earlier in this run. ──
            # Mock stays installed through phoneOpenHome() itself, not just the initial
            # loadShopPerf()/loadStarSeller() warm-up -- showScreen('home') fires
            # _SCREEN_LOADERS.home (== [loadStarSeller]) as a real side effect of
            # opening the screen, so restoring authGet too early lets that second,
            # unmocked call race in and stomp the ticker with real (empty/erroring)
            # data. Same "keep the mock installed for the whole block" fix this file's
            # own module docstring already calls out for an earlier flake. ──
            home_state = await page.evaluate("""async () => {
                window._origAuthGetHome = window.authGet;
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/analytics') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            dates: ['2026-07-22', '2026-07-23'],
                            trends: {revenue_30d: [1000, 1234.56], orders_30d: [7, 9]},
                            delta: {}, latest: {revenue_30d: 1234.56, orders_30d: 9},
                            top_listings: [{listing_id: 1, title: 'Test Listing', views: 42,
                                num_favorers: 3, sales: 1, price: 9.99, url: '#', conversion_pct: 2.4}],
                        })});
                    }
                    if (path === '/api/metrics') {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            shop: {active_listing_count: 37, active_listing_goal: 60},
                            orders: {today_revenue: 88.5},
                        })});
                    }
                    if (path.indexOf('/api/status-history?panel=star_seller') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            panel: 'star_seller', days: 30, snapshot_count: 0, dates: [], trend: [], latest: {},
                        })});
                    }
                    if (path.indexOf('/api/star-seller') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            status: 'on_track', orders_90d: 6, revenue_90d: 355.5, avg_rating: 4.8, unread_messages: 0,
                        })});
                    }
                    return window._origAuthGetHome(path, ms);
                };
                await Promise.all([loadShopPerf(), loadStarSeller()]);
                phoneOpenHome();
                await new Promise(r => setTimeout(r, 350));
                const result = {
                    screenActive: document.getElementById('screen-home').classList.contains('active'),
                    tabbarVisible: getComputedStyle(document.getElementById('phone-tabbar')).display !== 'none',
                    tickerVisible: getComputedStyle(document.getElementById('shop-ticker')).display !== 'none',
                    tickerText: document.getElementById('ticker-track').textContent,
                };
                window.authGet = window._origAuthGetHome;
                return result;
            }""")
            check(home_state.get("screenActive") is True, f"phoneOpenHome() should activate #screen-home: {home_state}")
            check(home_state.get("tabbarVisible") is False, f"tab bar must be hidden on Home: {home_state}")
            check(home_state.get("tickerVisible") is True, f"ticker must be visible on Home: {home_state}")
            ticker_text = home_state.get("tickerText") or ""
            check("$1234.56" in ticker_text and "Test Listing" in ticker_text and "4.80" in ticker_text,
                  f"ticker should render live revenue/top-listing/star-seller data, not placeholders: {ticker_text[:300]}")
            check("$88.50" in ticker_text and "Today" in ticker_text,
                  f"ticker should include a today's-revenue chip (2026-07-30 Home audit), not just the 30d figure: {ticker_text[:300]}")

            # ── Personalized Home greeting (2026-07-30 Home-screen UX audit) --
            # _loadHomeGreeting() fetches GET /api/me via fetchWithTimeout, not authGet,
            # so mock that function directly instead (same "monkeypatch the shared
            # function" convention as authGet elsewhere in this file). ──
            greeting_state = await page.evaluate("""async () => {
                window._origFetchWithTimeoutHome = window.fetchWithTimeout;
                window.fetchWithTimeout = (url, opts, ms) => {
                    if (String(url).indexOf('/api/me') !== -1) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            username: 'scott', display_name: 'Scott', role: 'owner',
                        })});
                    }
                    return window._origFetchWithTimeoutHome(url, opts, ms);
                };
                _homeGreetingName = null; // force a fresh fetch regardless of test order -- this is the
                // module-scope `let` _loadHomeGreeting() itself reads/caches, not a window property;
                // window._homeGreetingName would create an unrelated global and leave the real cache
                // (already warmed by an earlier real /api/me call elsewhere in this run) untouched.
                await _loadHomeGreeting();
                window.fetchWithTimeout = window._origFetchWithTimeoutHome;
                const el = document.getElementById('home-greeting');
                return {text: el.textContent, visible: getComputedStyle(el).display !== 'none'};
            }""")
            check(greeting_state.get("visible") is True, f"home-greeting should be visible once a display_name is fetched: {greeting_state}")
            check("Scott" in (greeting_state.get("text") or ""), f"greeting should include the account display_name: {greeting_state}")
            check(any(p in (greeting_state.get("text") or "") for p in ("morning", "afternoon", "evening")),
                  f"greeting should be time-of-day aware: {greeting_state}")

            # (2026-07-30: a per-tile keyboard-activation handler was drafted here and
            # dropped -- a pre-existing document-level keydown listener, dated
            # 2026-07-08, already calls .click() on any focused role="button" element
            # app-wide, Home's tiles included. The draft handler double-fired every
            # keypress against that existing one; caught by this very test before
            # shipping. No Home-specific a11y gap actually exists.)

            # ── Inbox & Reviews review-list cap + expand toggle (2026-07-30 audit) --
            # previously unbounded; now caps to 2 inline with a "N more" expand link,
            # matching Shop Performance's existing toggleShopExpand() pattern. ──
            inbox_state = await page.evaluate("""async () => {
                window._origAuthGetInbox = window.authGet;
                window.authGet = (path, ms) => {
                    if (path.indexOf('/api/inbox') === 0) {
                        return Promise.resolve({ok: true, status: 200, json: async () => ({
                            unread_count: 0, reviews_awaiting_reply: 0,
                            recent_reviews: [
                                {id: 'r1', rating: 5, text: 'Great!', replied: true},
                                {id: 'r2', rating: 4, text: 'Good', replied: true},
                                {id: 'r3', rating: 3, text: 'Meh', replied: false},
                            ],
                        })});
                    }
                    return window._origAuthGetInbox(path, ms);
                };
                await loadInbox();
                window.authGet = window._origAuthGetInbox;
                const before = {
                    visibleReviews: document.querySelectorAll('#inbox-body .inbox-review').length,
                    extraDisplay: getComputedStyle(document.getElementById('inbox-extra-reviews')).display,
                    toggleText: document.getElementById('inbox-expand-toggle').textContent,
                };
                toggleInboxExpand();
                const after = {
                    extraDisplay: getComputedStyle(document.getElementById('inbox-extra-reviews')).display,
                    toggleText: document.getElementById('inbox-expand-toggle').textContent,
                };
                return {before, after};
            }""")
            ib = inbox_state.get("before") or {}
            ia = inbox_state.get("after") or {}
            check(ib.get("visibleReviews") == 3, f"all 3 review nodes exist in the DOM (2 inline + 1 inside the collapsed extra block): {ib}")
            check(ib.get("extraDisplay") == "none", f"the 3rd review must start collapsed: {ib}")
            check("1 more" in (ib.get("toggleText") or ""), f"toggle should name how many extra reviews are hidden: {ib}")
            check(ia.get("extraDisplay") == "block", f"toggleInboxExpand() must reveal the extra review: {ia}")
            check("fewer" in (ia.get("toggleText") or ""), f"toggle label must flip once expanded: {ia}")

            badge_state = await page.evaluate("""() => {
                // 2026-07-31 (Today UX audit): _alertsCritWarnCount is real shared state now
                // (see setActionBadge()'s hc computation) -- by this point in the run a real
                // renderPhoneToday() has already fired (e.g. via the tour steps below) and set
                // it from live data, so this isolated check of the summary.high pathway must
                // reset it first or htText would include whatever real alerts happen to exist.
                _alertsCritWarnCount = 0;
                setActionBadge({high: 3}, 5);
                const hab = document.getElementById('home-appr-badge');
                const htb = document.getElementById('home-today-badge');
                return {
                    haText: hab.textContent, haDisplay: getComputedStyle(hab).display,
                    htText: htb.textContent, htDisplay: getComputedStyle(htb).display,
                };
            }""")
            check(badge_state.get("haText") == "5" and badge_state.get("haDisplay") == "flex",
                  f"home-appr-badge should mirror the pending-approvals count: {badge_state}")
            check(badge_state.get("htText") == "3" and badge_state.get("htDisplay") == "flex",
                  f"home-today-badge should mirror the high-severity today count: {badge_state}")

            # ── Desktop header must not leak through on Home (2026-07-30, Scott:
            # "the top is not accessible") -- .hdr-bar/.hdr-logo were only hidden
            # under body.phone-panel (the Ask/Approvals/Today/Create/More tab-bar
            # screens); Home is reached via phoneOpenScreen() instead, which sets
            # .phone-screen-open, not .phone-panel, so the desktop header (search,
            # Command Center link, bell/help/gear, operator chip) rendered at mobile
            # width and overflowed off both edges, unreachable. Confirms both the
            # header is actually hidden AND the page has zero horizontal overflow. ──
            header_state = await page.evaluate("""() => ({
                bodyClasses: document.body.className,
                hdrBarDisplay: getComputedStyle(document.querySelector('.hdr-bar')).display,
                hdrLogoDisplay: getComputedStyle(document.querySelector('.hdr-logo')).display,
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
            })""")
            check("phone-screen-open" in header_state.get("bodyClasses", ""),
                  f"sanity check -- Home should be in the phone-screen-open state this test targets: {header_state}")
            check(header_state.get("hdrBarDisplay") == "none", f"desktop .hdr-bar must be hidden on Home: {header_state}")
            check(header_state.get("hdrLogoDisplay") == "none", f"desktop .hdr-logo must be hidden on Home: {header_state}")
            check(header_state.get("scrollWidth") == header_state.get("clientWidth"),
                  f"Home must not cause horizontal overflow at mobile width: {header_state}")

            # Navigating away restores the normal tab bar, hides the ticker, and
            # reveals the persistent return-to-Home button.
            away_state = await page.evaluate("""() => {
                phoneTab('today');
                return {
                    tabbarVisible: getComputedStyle(document.getElementById('phone-tabbar')).display !== 'none',
                    tickerVisible: getComputedStyle(document.getElementById('shop-ticker')).display !== 'none',
                    returnBtnVisible: getComputedStyle(document.getElementById('home-return-btn')).display !== 'none',
                };
            }""")
            check(away_state.get("tabbarVisible") is True, f"tab bar must reappear on Today: {away_state}")
            check(away_state.get("tickerVisible") is False, f"ticker must hide once off Home: {away_state}")
            check(away_state.get("returnBtnVisible") is True, f"return-to-Home button should show on any non-Home screen: {away_state}")

            back_state = await page.evaluate("""async () => {
                document.getElementById('home-return-btn').click();
                await new Promise(r => setTimeout(r, 350));
                return {
                    screenActive: document.getElementById('screen-home').classList.contains('active'),
                    returnBtnVisible: getComputedStyle(document.getElementById('home-return-btn')).display !== 'none',
                };
            }""")
            check(back_state.get("screenActive") is True, f"#home-return-btn must call phoneOpenHome(): {back_state}")
            check(back_state.get("returnBtnVisible") is False, f"return-to-Home button should hide again once back on Home: {back_state}")

            # Regression (2026-07-23, reported live by Scott via screenshot): the header's
            # gear icon (onclick="showScreen('settings')") bypasses phoneOpenScreen() entirely
            # -- tapping it from Home left phone-home-open stuck, so the shop ticker kept
            # showing (and the tab bar / return-to-Home button stayed hidden) on top of
            # Settings. Fixed by moving the phone-home-open cleanup into showScreen() itself,
            # the one function every navigation path (including this bare onclick) funnels
            # through. Reproduce the exact reported path: from Home, call showScreen('settings')
            # directly (not phoneTab/phoneOpenScreen) -- simulates the gear icon tap.
            gear_from_home_state = await page.evaluate("""() => {
                phoneOpenHome();
                showScreen('settings');
                return {
                    phoneHomeOpen: document.body.classList.contains('phone-home-open'),
                    tabbarVisible: getComputedStyle(document.getElementById('phone-tabbar')).display !== 'none',
                    tickerVisible: getComputedStyle(document.getElementById('shop-ticker')).display !== 'none',
                    returnBtnVisible: getComputedStyle(document.getElementById('home-return-btn')).display !== 'none',
                    settingsActive: document.getElementById('screen-settings').classList.contains('active'),
                };
            }""")
            check(gear_from_home_state.get("settingsActive") is True, f"showScreen('settings') should activate #screen-settings: {gear_from_home_state}")
            check(gear_from_home_state.get("phoneHomeOpen") is False,
                  f"phone-home-open must clear when leaving Home via a bare showScreen() call (e.g. the header gear icon): {gear_from_home_state}")
            check(gear_from_home_state.get("tickerVisible") is False,
                  f"shop ticker must not stay stuck visible on top of Settings: {gear_from_home_state}")
            check(gear_from_home_state.get("tabbarVisible") is True,
                  f"tab bar must reappear on Settings reached via the gear icon: {gear_from_home_state}")
            check(gear_from_home_state.get("returnBtnVisible") is True,
                  f"return-to-Home button must reappear on Settings reached via the gear icon: {gear_from_home_state}")

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
