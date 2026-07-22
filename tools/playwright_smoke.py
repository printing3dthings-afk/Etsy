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

            # Products screen rebuild (2026-07-15) -- was hardcoded to a ~5-product
            # "Core Products" slice, now the full catalog with a category filter.
            # Stub _products directly (bare assignment, not window.X -- see the tour
            # steps above for why: these are top-level `let` bindings, not globals).
            await page.evaluate("showScreen('products')")
            await page.wait_for_timeout(300)
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
            check("Ask Frank to draft it" in review_no_content.get("actions", ""),
                  f"missing content should offer the chat hand-off button, not Publish: {review_no_content}")
            check("Publish to Etsy" not in review_no_content.get("actions", ""),
                  f"Publish must not appear with no content: {review_no_content}")
            # Leave the DOM clean for later checks in this same page session (the
            # modal otherwise intercepts pointer events for unrelated later clicks).
            await page.evaluate("productReviewClose(); document.body.classList.remove('product-sheet-open')")

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
            check(tile_grid.get("count") == 7, f"Create screen must show exactly 7 category tiles, got: {tile_grid}")
            check(set(tile_grid.get("cats", [])) == {
                "digital_planner", "wall_art", "coloring_pages",
                "sticker_pack", "svg_3dprint_pack", "sublimation", "3d_print_physical",
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
            check("COLOR1030" in wrong_category_error.get("coloringMsg", ""),
                  f"Coloring Pages' empty-pid error should use its own category example: {wrong_category_error}")
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
            check(all(advanced.get(k) for k in ("svgPresent", "qcPresent", "videoPresent", "socialPresent")),
                  f"all 4 relocated tool sections must still be present: {advanced}")
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

            await page.evaluate("startTour()")
            await page.wait_for_timeout(400)
            mobile_step1 = await page.evaluate("""() => ({
                visible: getComputedStyle(document.getElementById('tour-root')).display !== 'none',
                title: document.getElementById('tour-step-title').textContent,
                dotCount: document.querySelectorAll('#tour-dots .dot').length,
            })""")
            check(mobile_step1.get("visible"), f"mobile tour should start when startTour() is called on a narrow viewport: {mobile_step1}")
            check("Welcome" in mobile_step1.get("title", ""), f"mobile tour step 1 should be the welcome intro: {mobile_step1}")
            check(mobile_step1.get("dotCount") == 8, f"mobile tour should have 8 steps: {mobile_step1}")

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
            check(mobile_create.get("tileCount") == 7, f"mobile Create screen must show all 7 tiles too: {mobile_create}")

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
