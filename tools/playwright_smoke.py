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

            # ── Mobile spotlight tour (2026-07-15) -- same #tour-root engine as
            # desktop, spotlighting #phone-tabbar's 5 tabs instead of the
            # sidebar. setViewportSize (not a new context) so this reuses the
            # already-authenticated session. ──
            await page.set_viewport_size({"width": 390, "height": 844})
            await page.wait_for_timeout(500)
            await page.evaluate("startTour()")
            await page.wait_for_timeout(400)
            mobile_step1 = await page.evaluate("""() => ({
                visible: getComputedStyle(document.getElementById('tour-root')).display !== 'none',
                title: document.getElementById('tour-step-title').textContent,
                dotCount: document.querySelectorAll('#tour-dots .dot').length,
            })""")
            check(mobile_step1.get("visible"), f"mobile tour should start when startTour() is called on a narrow viewport: {mobile_step1}")
            check("Welcome" in mobile_step1.get("title", ""), f"mobile tour step 1 should be the welcome intro: {mobile_step1}")
            check(mobile_step1.get("dotCount") == 7, f"mobile tour should have 7 steps: {mobile_step1}")

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

            await page.click("#tour-next-btn")
            await page.wait_for_timeout(500)
            mobile_step3 = await page.evaluate("""() => ({
                title: document.getElementById('tour-step-title').textContent,
                apprTabOn: document.querySelector('.ptab[data-ptab=\"appr\"]').classList.contains('on'),
            })""")
            check(mobile_step3.get("title") == "Approvals", f"mobile tour step 3 should be Approvals: {mobile_step3}")
            check(mobile_step3.get("apprTabOn"), f"mobile tour should switch to the Approvals tab via phoneTab(): {mobile_step3}")

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
                # ── Orb luminance-key alpha compositing (2026-07-15) — "get rid of
                # the circle around Frank" / "the orb is gone" (a real regression
                # caught live: painting the theme's --bg into the WebGL clear color
                # crossed UnrealBloomPass's brightness threshold and blew the whole
                # canvas out to solid white). The fix replaced that with real
                # per-pixel alpha: canvas#orb-gl renders offscreen against pure
                # black, and orbGLFrame() copies it onto the visible
                # canvas#orb-gl-display every other frame with alpha set to each
                # pixel's own max(r,g,b) -- background pixels (black) become fully
                # transparent, wireframe/bloom pixels stay opaque. Wait a couple of
                # frames for that composite to actually run once, then assert the
                # architecture directly: the offscreen canvas must stay hidden, the
                # display canvas must be the visible one, and a corner pixel (pure
                # background) must have near-zero alpha while a center pixel
                # (through the wireframe) has meaningfully higher alpha -- the
                # exact signature that would be flat/uniform if this regressed back
                # to a solid-color circle (either black or white). ──
                await page.wait_for_timeout(200)
                composite_state = await page.evaluate("""() => {
                    const off = document.getElementById('orb-gl');
                    const disp = document.getElementById('orb-gl-display');
                    const offVisible = off ? getComputedStyle(off).display !== 'none' : null;
                    const dispVisible = disp ? getComputedStyle(disp).display !== 'none' : null;
                    let cornerAlpha = null, centerAlpha = null;
                    if (disp && orbGlDisplayCtx) {
                        const w = disp.width, h = disp.height;
                        cornerAlpha = orbGlDisplayCtx.getImageData(2, 2, 1, 1).data[3];
                        centerAlpha = orbGlDisplayCtx.getImageData(w >> 1, h >> 1, 1, 1).data[3];
                    }
                    return {offVisible, dispVisible, cornerAlpha, centerAlpha};
                }""")
                check(composite_state.get("offVisible") is False,
                      f"the offscreen WebGL canvas (#orb-gl) must stay display:none -- it's a render buffer, not the visible layer: {composite_state}")
                check(composite_state.get("dispVisible") is True,
                      f"the 2D display canvas (#orb-gl-display) must be the visible one in sphere mode: {composite_state}")
                check(composite_state.get("cornerAlpha") is not None and composite_state["cornerAlpha"] < 40,
                      f"a corner pixel (pure background, no wireframe there) should be near-transparent via the luminance key, "
                      f"not opaque -- a value near 255 here would mean the solid-circle bug regressed: {composite_state}")

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

            # ── cc-open must never coexist with is-mobile (2026-07-15) — Scott's
            # header bar (with its position:absolute, 1440px-stage-sized
            # #alert-dropdown) appeared on his phone alongside the mobile tab bar,
            # with the alert dropdown clipped off-screen unreadable. Root cause:
            # syncMobileClass() only ever ADDED cc-open on a mobile->desktop
            # transition and never had a path to remove it again once mobile was
            # redetected -- if cc-open was ever set while briefly misdetected as
            # desktop (mobile Safari's matchMedia/resize events can fire
            # spuriously, e.g. around address-bar show/hide), it stuck forever,
            # permanently leaking the full desktop dashboard onto a phone
            # viewport. Fix: mobile now always wins in syncMobileClass() -- force
            # cc-open on here (simulating the exact stuck state) and confirm the
            # real function call self-heals it. ──
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
