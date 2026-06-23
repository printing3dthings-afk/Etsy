# Ops Runbook — Infrastructure Incidents & Fixes

Append-only log of infrastructure/dashboard problems and how they were diagnosed
and fixed. This file is loaded into the CEO Agent's (Fucking Frank) system prompt
at request time, so Scott can ask Frank directly ("why was X broken?") and get a
grounded answer instead of a guess. Keep entries short — a few lines each.

---

### 2026-06-16 — OpenAI marked "Not set" in Hub > Creds despite being in local .env
**Symptom:** Creds tab showed OpenAI, SMTP, and Pinterest as "Not set" even though
OPENAI_API_KEY had a real value in the project's `.env` file.
**Root cause:** `.env` is gitignored (credentials must never be committed — see
CLAUDE.md). Railway builds the container straight from the GitHub repo, so it never
receives the local `.env` at all. Etsy/Anthropic showed "Set" because those were
added directly as Railway environment variables at some point; OpenAI never was.
**Fix:** Set `OPENAI_API_KEY` directly on the live Railway service via the Railway
GraphQL API (`variableUpsert` mutation) using an account-level API token
(`Authorization: Bearer <token>` header, endpoint `https://backboard.railway.app/graphql/v2`).
Railway auto-redeploys on variable change.
**Future fix for this class of issue:** Any time a credential is added to local
`.env`, it must ALSO be added to Railway's service Variables (dashboard or API) —
the two are not connected. SMTP_PASSWORD and Pinterest keys are still genuinely
unset (no real values exist yet anywhere) — that's expected, not a bug.

### 2026-06-16 — Duplicate/abandoned Railway project
**Symptom:** Railway account had two projects: `calm-light` (live, matches the
deployed APP_SECRET_TOKEN) and `enchanting-purpose` (created 2026-06-12, one
service named "Etsy", zero environment variables, one successful + several failed
deployments).
**Root cause:** Leftover from an earlier deployment attempt before `calm-light`
became the real production deployment.
**Fix:** Deleted `enchanting-purpose` via `projectDelete` mutation after confirming
it had no variables and wasn't the one matching the live token. `calm-light` is the
only project now.

### 2026-06-16 — Dashboard spinners ("Fucking Frank is analyzing your shop…",
Conversion Doctor) appeared stuck
**Symptom:** Both spinners on the Dash tab spun indefinitely.
**Root cause:** `/api/suggestions` was returning HTTP 500 because the Anthropic API
itself was returning `InternalServerError: Error code: 500 - Internal server error`
on `messages.create` — a transient outage on Anthropic's side, not a bug in this
codebase. Confirmed via Railway deployment logs (full traceback ends in
`anthropic.InternalServerError`).
**Fix:** None needed in code that time — `getCeoSuggestions()` already has proper
try/catch + "Try Again" handling. If this happens again: check whether
`/api/suggestions` is slow to fail (Anthropic outage, self-resolving, just wait) vs
hangs past 120s (real bug). Don't assume it's a frontend bug — verify with a direct
curl against `/api/suggestions` and check Railway logs for the actual exception first.

### 2026-06-16 — Spinner stuck again a couple hours later — this time a real bug
**Symptom:** Same "Fucking Frank is analyzing your shop…" spinner, reported stuck
again at 18:49 UTC. `curl -X POST /api/suggestions` returned bare `HTTP 500
"Internal Server Error"` after ~73s.
**Root cause:** Different from the earlier entry — this time it was a real bug, not
an Anthropic outage. `/api/suggestions` wrapped EACH individual `messages.create`
call in `asyncio.wait_for(..., timeout=60.0)`, but the frontend's own fetch timeout
is 120s (`fetchWithTimeout(..., 120000)`). The 3-tool-call diagnostic sequence's
final synthesis call (up to 3500 output tokens, large context from 3 rounds of tool
results) legitimately took >60s on a normal, non-outage Anthropic response — direct
test confirmed Anthropic responded to a trivial call in 1.1s, so the API itself was
healthy. The `asyncio.TimeoutError` this raised was never caught, so FastAPI
returned a bare unhandled-exception 500 with no `detail` field — which is why the
frontend showed a generic failure instead of a helpful message.
**Fix:** Replaced the flat per-call 60s timeout with a single 100s overall budget
shared across all loop iterations (`deadline = time.monotonic() + 100.0`, remaining
budget passed to each `wait_for` call) — leaves headroom under the frontend's 120s
limit while not starving a legitimately-slower synthesis call. Wrapped the loop in
try/except for `asyncio.TimeoutError` (-> HTTP 504 with a clear `detail` message)
and `anthropic.APIError` (-> HTTP 502 with the real error message), so any future
failure surfaces a real message in the UI instead of bare "Internal Server Error".
**Lesson:** When a transient symptom recurs, re-verify — don't assume the earlier
diagnosis still holds. The first occurrence really was an Anthropic outage; this one
was a latent timeout bug that outage exposed me to investigating but didn't itself
cause.

### 2026-06-16 — Same spinner, third layer: 200 OK but suggestions silently empty
**Symptom:** After the timeout fix above went live, `/api/suggestions` returned HTTP
200 (no more 500/504), but the dashboard showed an empty/low-value report — headline
"Analysis complete", zero suggestions — even though Claude had clearly generated a
real, detailed diagnostic (it later turned out to include a genuinely valuable finding:
~40 wall-art listings all carrying mismatched "kawaii" tags on non-kawaii designs).
**Root cause:** The JSON-extraction code only stripped a ` ```json ` fence if the
model's response text *started* with it (`if text.startswith(fence)`). Claude's actual
response began with a conversational sentence ("Compiling the full diagnostic now.")
before the fenced block, so the check failed, `json.loads()` raised, and the code fell
into its fallback path — silently discarding the real report into an unrendered `raw`
field instead of surfacing it.
**Fix:** Added a shared `_extract_json_object()` helper (`main.py`) that searches for a
fenced ```json block *anywhere* in the text (regex), then falls back to the outermost
`{...}` span, then a bare `json.loads()` — used at all three sites that parse a model
JSON response (`/api/suggestions`, `/api/diagnose/{id}` conversion doctor, and the
batch tag generator). Verified live: response now has 8 real suggestions, no `error`
field, full headline/score/top_win/top_risk populated.
**Lesson:** A 200 status code is not proof a feature is actually working — always check
the response *body* makes sense, not just the HTTP status. This bug shipped silently
inside what looked like a successful fix.

### 2026-06-16 — Spinner STILL stuck: the real cause was raw latency (~80s), not a crash
**Symptom:** Scott reported the "Fucking Frank is analyzing your shop…" spinner still
looked stuck even after the 500 and parse fixes above. Backend was returning HTTP 200
with a valid 8-suggestion report — but only after ~75–80 seconds.
**Root cause:** `/api/suggestions` ran the data gathering as an agentic tool loop — the
model was made to call get_metrics, then list_listings(active), then list_listings(draft)
one at a time = 4 sequential Claude round-trips before the report. That's ~80s. The
in-memory cache (`_cache`) is wiped on every redeploy (db is `persistent: false`), so
right after any deploy the first dashboard load hit the full cold 80s path — dangerously
close to the frontend's 120s fetch timeout, and long enough that it reads as "stuck."
**Fix (3 commits):** (1) Gather the 3 known data pulls directly in Python with
`asyncio.gather` and do ONE synthesis call instead of a tool loop. (2) This alone was
still ~60–80s for the single big call, so the durable fix is a background warm loop
(`_warm_suggestions`): prime the cache ~5s after boot, then re-prime ~2min before each
expiry; suggestions cache TTL raised 300s → 1800s. The dashboard now serves an instant
(<1s) cache hit on every load; only the one-time ~60s window right after a fresh deploy
is cold. (3) Don't cache a parse_failed/truncated result (would freeze a broken report
for 30min); warm loop retries in 60s on parse failure. NOTE: cutting max_tokens to 2400
truncated the JSON and caused a parse fail — kept at 4000.
**Lesson:** "Spinner stuck" can mean "genuinely too slow," not "crashed." When an
endpoint is correct but slow AND its cache resets on deploy, the fix is to keep the
cache warm in the background, not to chase a nonexistent exception. Verify a fix by
timing a real cold call, not just checking it returns 200.

### 2026-06-16 — Spinner, final layer: make the cold path non-blocking (202 + poll)
**Symptom:** Scott sent a screen recording of the dashboard still spinning. The warm
cache had already finished priming ~85s earlier, so a fresh load *should* have been an
instant hit — meaning the recording caught a request that was made while the cache was
cold (the ~75s window right after a deploy) and was BLOCKING for the full synthesis. A
minute-long blocking request behind a plain spinner is indistinguishable from "hung,"
and I'd been triggering fresh cold windows by repeatedly redeploying (even doc-only
commits redeploy and wipe the in-memory cache).
**Root cause:** `/api/suggestions` blocked the HTTP request for the entire ~60-75s
synthesis whenever the cache was cold. Warm-on-boot reduced how often that happened but
didn't remove the blocking path itself.
**Fix:** Cold cache no longer blocks. The endpoint returns an instant HTTP 202
`{"status":"warming"}` (ensuring a background synthesis is running, guarded by a
`_suggestions_warming` flag so it never stacks with the warm loop), and the frontend
`getCeoSuggestions` polls every 4s (up to ~100s) while it sees 202, keeping the spinner
but never hanging on one long request. Verified live: during the post-deploy window the
endpoint returned 202 in <1s repeatedly, then flipped to the full 8-suggestion 200
report the instant the warm finished (~55s); steady-state load is ~0.17s.
**Lesson:** Never put a multi-second, let alone minute-long, synchronous AI call on a
user's hot path. Return fast with a "working on it" status and let the client poll.

### 2026-06-16 — Spinner still perceived "stuck" after 202+poll fix — root cause was no client-side persistence
**Symptom:** Scott reported spinner still spinning even after the 202+poll non-blocking fix was confirmed
working. Backend was returning correct 200 with 8 suggestions after ~75s; 202+poll architecture was intact.
**Root cause:** `_lastSuggestions` (the JS variable holding the last report) was initialized to `null`
on every page load — there was no browser-side persistence. The sessionStorage write in `getCeoSuggestions`
and `_bgRefreshSuggestions` was saving the report correctly, but the missing piece was an init IIFE before
`loadDash()` that reads it back. So on every reload (and every Railway redeploy triggers a page reload to
pick up the new service worker cache), the spinner ran again from scratch even though the browser already
had a valid report from 5 minutes ago.
**Fix:** Added an IIFE immediately before `loadDash()` that reads `sessionStorage.getItem('obc_sug')`,
validates the stored report (must have `generated_at`, non-empty `suggestions`, no `error`, and be <4h old),
and populates `_lastSuggestions`. `getCeoSuggestions` already checks `_lastSuggestions` first and shows it
instantly with a silent background refresh for newer data — so the only missing link was the init IIFE.
Also added a 2-minute server-side cache to `/api/conversion-targets` to prevent the Conversion Doctor
from hitting the Etsy API on every panel open. Bump to BUILD_ID v23.
**Lesson:** Client-side JS variables reset on every page load. If state needs to survive a reload, write
it to sessionStorage (or localStorage for longer persistence) AND read it back on init. The write without
the read is a silent no-op from the user's perspective.

### 2026-06-16 — REAL root cause of the permanently-stuck spinner: a JS SyntaxError froze the entire dashboard script
**Symptom:** Scott reported the spinner "will not go past the spinning stage" even after the v23
sessionStorage fix above — and *nothing* on the dashboard ever updated, not just the CEO report.
**Root cause:** The Files/Backups browser feature built a download link with:
`onclick="window.open(\''+url.replace(/'/g,"\\'")+'\',\'_blank\')"`. This was written inside `_WEB_UI`,
a **non-raw** Python triple-quoted string (`_WEB_UI = """..."""`, not `r"""..."""`). Python processes
backslash escapes in non-raw strings even inside triple quotes, so `\'` and `\\'` in the source got
unescaped by Python *before* the text ever reached the browser — turning what was meant to be an escaped
quote inside a JS string into a bare `'` that closed the string literal early. The result was a genuine
JavaScript `SyntaxError: Unexpected string` partway through the `<script>` block. A SyntaxError anywhere
in a `<script>` tag prevents the **entire script from executing** — not just the broken line. That meant
`loadDash()`, `getCeoSuggestions()`, the 202+poll loop, the sessionStorage restore IIFE — literally none
of it ever ran. Every spinner on the page was the static HTML placeholder baked into the page source,
which nothing ever replaced. This is why none of the v21–v23 backend/JS fixes (warm cache, 202+poll,
sessionStorage persistence) made any visible difference: the browser never got far enough to execute any
of that code. Caught by pulling the live production HTML with curl, extracting the `<script>` body, and
running it through `node --check` — this is now the standard verification step for any dashboard JS change.
**Fix:** Replaced the backslash-escaped quotes with the `&apos;` HTML-entity pattern already used
successfully elsewhere in the same file (Top Listings panel), which needs zero backslash escaping and
sidesteps the double-unescaping problem entirely. `url` here is already `encodeURIComponent`-safe so no
quote-escaping was ever actually necessary. Verified clean with `node --check` against both the locally
evaluated `_WEB_UI` Python expression and the live redeployed page. Bump to BUILD_ID v24.
**Lesson:** `_WEB_UI` embeds a large inline `<script>` inside a non-raw Python string — any backslash
written in that JS (regex escapes, quote escapes, etc.) is silently reinterpreted by Python's own string
parser first. Always verify dashboard JS changes with `node --check` against the *actual rendered output*
(curl the live page or eval the `_WEB_UI` expression with `ast`), not just by reading the Python source —
the source and the runtime JS are not the same text whenever a backslash is involved. A single SyntaxError
anywhere in the script silently kills 100% of the dashboard's interactivity with no visible error to the
user — just frozen static HTML. This class of bug is invisible to Python's own syntax checks
(`py_compile` passes fine) because the bug only exists in the *string value*, not the Python syntax.

### 2026-06-17 — Listings category filter chips never filtered (only "All" worked)
**Symptom:** Scott reported only the "All" filter chip on the Listings tab did anything; clicking any
named category (e.g. "Botanical and Floral Art") left the list unchanged.
**Root cause:** `shop_section_id` arrives from `/api/listings` as a JSON number. The filter chip's
`onclick="setSectionFilter('${c.key}')"` template literal always wrapped the value in quotes, so
`_sectionFilter` became a string while `l.shop_section_id` stayed a number — `===` comparison in
`renderListings()` never matched except by coincidence for the synthetic `'none'` (uncategorized) bucket,
which is why that one looked like it might have worked.
**Fix:** Normalized both sides of every comparison with `String(...)` (grouping key, filter compare, and
the active-chip highlight check). Bump to BUILD_ID v27.
**Separately confirmed NOT a bug:** Scott also reported listing detail panels showing "Uncategorized" —
checked live Etsy data directly via curl and confirmed those specific listings (e.g. 4522868228) genuinely
have `shop_section_id: null` on Etsy itself (87 of 164 active listings, mostly newer ones, were never
assigned to a shop section). The dashboard was reporting this correctly.
**Lesson:** Any value compared with `===` after passing through an HTML template-literal attribute
(`onclick="fn('${x}')"`) silently becomes a string, even if the original value was a number. Normalize
explicitly with `String()` on both sides rather than relying on type to survive the round trip through
the DOM.

### 2026-06-17 — CEO Agent chat ("Frank") permanently 400s mid-session after firing multiple tool calls
**Symptom:** Scott asked Frank to fix mismatched kawaii tags on 30+ wall art listings. Frank staged the
fixes and started "firing them all simultaneously." The next message in the same chat session immediately
failed with Anthropic API error 400 `invalid_request_error`: "tool_use ids were found without tool_result
blocks immediately after" — listing 8 `toolu_...` ids — and every subsequent message in that session kept
failing the same way.
**Root cause:** In `_run_agent_turn()`, the assistant's turn (including its `tool_use` blocks) is appended
to `history` *before* the tools are executed. The Anthropic API requires every `tool_use` block to be
followed by a matching `tool_result` in the very next message. If anything threw while iterating the tool
calls — most likely `await websocket.send_text(...)` for a status update failing on a flaky mobile
connection while Frank was firing many `stage_action` calls back-to-back — the loop aborted before
`history.append({"role": "user", "content": tool_results})` ever ran. That left `history` (an in-memory,
per-websocket-connection list with no persistence or self-repair) permanently corrupted for the rest of
that connection: every later turn sent the same orphaned `tool_use` blocks to Claude and got the same 400.
**Fix:** Wrapped both the status-update `send_text` and the `_execute_agent_tool` call in their own
try/except inside the per-block loop in `_run_agent_turn()`, so a failure on one tool call can no longer
abort the loop before a `tool_result` is recorded for every `tool_use` block. A failed status send is now
silently ignored (best-effort only); a failed tool execution now produces an `{"error": ...}` result
instead of an unhandled exception. `history.append(...)` for `tool_results` is now unconditional once the
loop starts. Bump to BUILD_ID v28. Redeploying also force-closed the corrupted in-memory session, so Scott
just needs to reopen the chat to get a clean `history`.
**Lesson:** Any conversation-history list fed back into the Anthropic API must guarantee `tool_use` →
`tool_result` pairing is atomic — either both happen or neither does. Appending the assistant's `tool_use`
turn before the results are known creates a window where any unrelated failure (a flaky websocket send,
not just a tool bug) corrupts that history for the rest of the session, since there is no persistence or
truncation/recovery logic to drop a bad trailing turn. Catch exceptions at the smallest possible scope
around side-effecting calls (websocket sends, tool execution) rather than relying on an outer handler.

---

## 2026-06-17 — Frank chat continuity + execution hardening (and Etsy-token-on-restart landmine)
**What changed (CEO chat / Frank):**
- **Chat now survives reconnects & restarts.** Previously the conversation lived only in an in-memory
  per-WebSocket list, so any mobile socket drop (backgrounding, network switch, carrier idle-timeout)
  silently reset Frank to amnesiac while the old bubbles stayed on screen — it *looked* like the chat
  continued but Frank had forgotten everything. Added a `chat_messages` SQLite table + a stable
  `CHAT_SESSION` id (localStorage) passed as `?session=`; `chat_ws` loads prior history on connect and
  persists each completed exchange. Only plain text is persisted — never tool_use/tool_result blocks
  (persisting half a pair would 400 on replay).
- **Heartbeat + auto-reconnect.** Client pings every 25s (server replies pong) to keep the socket warm
  through proxy idle-timeouts; on unexpected close the client auto-reconnects with capped backoff and
  silently resumes the same server-side thread.
- **Dangling-message wedge fixed.** A mid-turn stream/API failure used to leave a user message with no
  assistant reply, so the next turn sent two user turns back-to-back → API 400 → chat wedged until reload.
  `chat_ws` now snapshots `history` length and rolls back this turn's additions on any exception.
- **Frank now actually executes.** Added `listing_integrity_check` to his command registry (the read-only
  check that surfaces truthfulness/quantity-claim violations) and tightened the system prompt with an
  "ACT, DON'T NARRATE" rule so he calls the tool / stages the fix instead of saying "I'll run that."
- **Approval gate hardened.** `execute_command` extra_args are now screened against a denylist
  (`--fix/--push/--publish/--apply/--activate/--delete/--write`) so neither Frank nor a prompt-injection
  can push a live listing mutation through a CLI flag — those must still go through Scott's one-tap approval.
  Per Scott's call (2026-06-17), Frank stays at "stage for approval" for all live-listing edits.

**Open landmine (diagnosed, NOT yet fixed):** On Railway the live server refreshes the Etsy token lazily on
a 401 and writes the rotated refresh token to `.env` — but Railway's filesystem is ephemeral and re-injects
the *old* `ETSY_REFRESH_TOKEN` env var on every restart/redeploy. Etsy rotates the refresh token on each
use, so after the next restart the server will present an already-consumed token → `invalid_grant` → the
whole Etsy integration goes dark until Scott re-runs `python tools/etsy_oauth.py`. Same class of bug already
solved for GitHub Actions (write rotated token back to the secret store). Recommended durable fix: persist
rotated tokens to the `/data` SQLite volume and prefer the newer of DB-vs-env on startup. Deferred because a
botched token-precedence change could itself cause an outage and can't be tested against live Railway here.

**2026-06-17 (later same day) — landmine fixed.** Added a durable `etsy_tokens` table to `db.py`
(`save_etsy_tokens()` / `get_etsy_tokens()`, singleton row on the `/data` volume) plus two small additions
to `main.py`, deliberately **without touching `tools/etsy_api.py`** so every other consumer (CI's own
already-working rotation via `ci_refresh_etsy_secrets.py`, Scott's local scripts) is completely unaffected:
- `_reconcile_etsy_tokens()` runs once at import time, before any `EtsyAPIClient()` is constructed. It
  compares the env `ETSY_REFRESH_TOKEN` against the DB row's `refresh_token` *and* `parent_refresh_token`
  (lineage, not a timestamp race) — if the DB is a forward rotation of the current env token, the DB wins
  and overwrites `os.environ`; if the env token doesn't match the DB's lineage at all (Scott manually
  re-authorized via `etsy_oauth.py` and updated the Railway dashboard since the DB was last written), env
  wins untouched. Empty DB (first boot ever) is a no-op.
- `_token_sync_loop()` (background task, started in `_startup()`, polls every 60s) watches `os.environ` for
  a token change — `refresh_access_token()` already updates it in-memory the instant it rotates — and
  persists the new pair to the DB with the previous refresh token recorded as `parent_refresh_token`, so
  the next boot's lineage check has something to match against.
- Verified with 4 standalone scenario scripts (not committed — ad hoc): DB-forward-rotation-wins,
  fresh-reauth-in-env-wins, empty-DB-is-noop, and a full rotate→persist→simulated-restart→restore cycle.
  All passed. `python -m py_compile` clean on both files.
- Risk note: this only takes effect on the *next* Railway deploy. Until then the current single
  outstanding (working) token is unaffected — nothing about the existing token's validity changed today.

### 2026-06-17 (later still) — two independent Etsy token rotation lineages (Railway vs. GitHub Actions)
**Symptom (latent, not yet observed in production — found by code audit, not an incident report):**
the fix above deliberately left `ci_refresh_etsy_secrets.py`'s rotation untouched because it was "already
working" in isolation. But "isolation" was the problem: the live Railway server refreshes the Etsy access
token **reactively** (on a 401, `etsy_api.py` line ~382) from its own `ETSY_REFRESH_TOKEN` env var, while the
`listing_integrity_daily.yml` GitHub Actions workflow refreshes **proactively, every single scheduled run**
from a completely separate copy of the same credential stored as a GH repo secret. Etsy invalidates the
previous refresh token on every use. Two independent actors rotating the same credential with no shared
state means whichever one refreshes most recently silently invalidates the other's copy — there is no
self-healing; the stale side just hard-fails with `invalid_grant` next time it tries to refresh, requiring
a manual `tools/etsy_oauth.py` re-auth. Risk went up (not down) after adding `_quality_audit_loop()` earlier
today: that loop guarantees a real Etsy API call from inside the Railway process once a day, every day,
independent of whether Scott or Frank happen to be using the dashboard — raising the floor on how often the
Railway side touches the lineage and collides with GH Actions' fixed daily 13:00 UTC run.
**Fix:** added a single source of truth both sides can sync through, reusing the existing `APP_SECRET_TOKEN`
bearer auth (no new secret needed for the server side):
- `GET /api/etsy-tokens` / `POST /api/etsy-tokens` on the live server — read/write the durable `/data` DB's
  `etsy_tokens` row (the same lineage-aware store `_reconcile_etsy_tokens()` already uses).
- `tools/ci_refresh_etsy_secrets.py` now optionally takes `RAILWAY_APP_URL` + `APP_SECRET_TOKEN`: if set, it
  fetches the live server's current refresh token before refreshing (prefers it if newer than its own GH
  secret) and pushes the rotated pair back to the server after refreshing, in addition to updating the GH
  secrets as before. Falls back to GH-secrets-only rotation if either var is unset — not a breaking change.
- `listing_integrity_daily.yml` passes both through as `${{ secrets.RAILWAY_APP_URL }}` /
  `${{ secrets.APP_SECRET_TOKEN }}`. **Action needed from Scott:** add these two as GitHub repo secrets
  (Settings → Secrets and variables → Actions) — `APP_SECRET_TOKEN` should be the exact same value already
  set on the Railway service. Until both are added, CI rotation still works exactly as before, just without
  the collision protection.
- Verified: `python -m py_compile` clean on `main.py` and `ci_refresh_etsy_secrets.py`.

### 2026-06-17 (later still) — autoresponder built but never scheduled; two scripts broken on Railway by hardcoded `/home/user/Etsy` paths
**Finding 1 — dead capability:** `tools/etsy_autoresponder.py` exists specifically to close the Star Seller
message-response-rate gap (CLAUDE.md flags this as the "main challenge" for digital products — every other
Star Seller criterion is near-automatic for instant digital delivery). Nothing was ever invoking it — no
cron, no background loop, no `_EXEC_COMMANDS` entry. It had also never been run on Railway, so its
unguarded `with open(_env_path) as _f:` (no existence check) would have crashed immediately with
`FileNotFoundError` — Railway has no `.env` file at all; env vars are injected directly by the platform.
**Fix:** guarded the `.env` open with `if os.path.exists(_env_path):` (matching the pattern `main.py`
already uses for its own `.env` load), then wired it into `main.py`'s existing background-task pattern as
`_autoresponder_loop()` (added to `_startup()`'s task list, staggered 180s after the other loops, runs once
daily). It only drafts replies and emails Scott a digest — sending to a buyer is a separate explicit
`--send`/`--send-all` CLI step Scott runs by hand — so this stays inside the "Tier 1 support drafting"
autonomy CLAUDE.md already grants; nothing here sends a buyer-facing message automatically. Note: its dedup
state (`data/message_drafts/sent_log.json`) lives on Railway's ephemeral filesystem, not the durable `/data`
volume, so a redeploy can cause a re-drafted (never re-sent) duplicate in the next digest — harmless,
not worth the complexity of moving to the DB unless it proves annoying in practice.

**Finding 2 — live capability silently broken:** while auditing other "Automate" table scripts for the same
`.env`-loading bug class, found `tools/shop_health_check.py` had it worse than the autoresponder did —
hardcoded `sys.path.insert(0, '/home/user/Etsy')`, `open('/home/user/Etsy/.env')`, and three more
`/home/user/Etsy/...` constants (`UPSCALED_DIR`, `PRODUCT_FILES_DIR`, `SNAPSHOT_FILE`, `MANIFEST_PATH`).
Unlike the autoresponder, this one is **already registered in `main.py`'s `_EXEC_COMMANDS` registry**
(`"shop_health_check"`) — meaning Frank could already invoke it via the `execute_command` tool, and it would
have failed every time on Railway. **Fix:** replaced every hardcoded path with `ROOT = Path(__file__).resolve().parent.parent`-relative
equivalents and guarded the `.env` open the same way. Also fixed the same unguarded-open bug in
`tools/pinterest_post_queue.py` (lower priority — that one's a manual local-only CLI tool, not Railway- or
Frank-invoked, but cheap to fix while in the file). Residual known limitation, same class as the
autoresponder's: `SNAPSHOT_FILE`/`MANIFEST_PATH` still write under the repo's `data/` dir, not the durable
`/data` volume, so trend-comparison and hero-art-drift detection reset on every Railway redeploy — the
health check itself still runs and reports correctly each time, only the week-over-week comparison is lost.
- Verified: `python -m py_compile` clean on `main.py`, `etsy_autoresponder.py`, `shop_health_check.py`,
  `pinterest_post_queue.py`, `ci_refresh_etsy_secrets.py`.

### 2026-06-17 (later still) — gave Frank the seasonal keyword tool CLAUDE.md already grants him
CLAUDE.md's autonomy boundaries explicitly list "Run seasonal keyword reports and dry-run previews" under
Fully Autonomous, but `tools/seasonal_keywords.py` had no `_EXEC_COMMANDS` entry — Frank had no way to
actually run it. Added two read-only entries: `seasonal_keywords_report` (default invocation, shows
upcoming/overdue seasonal swaps) and `seasonal_keywords_preview` (`--dry-run`, shows exactly which tags
would change on which listings). Neither writes to Etsy — `--push` is the only flag that does, it's in
neither command's `args`, and `_FORBIDDEN_EXEC_FLAGS` already refuses it if ever smuggled in via
`extra_args`, so the only real path to applying a seasonal swap is still Scott approving a `stage_action` in
the Action Center. While wiring it in, found and fixed the same unguarded `.env` open bug as the other two
scripts above (`tools/seasonal_keywords.py` line ~26) — would have crashed on Railway the first time Frank
tried to call it. Verified `python -m py_compile` clean and ran `python tools/seasonal_keywords.py --weeks 10`
locally to confirm the report still renders correctly after the guard fix.

### 2026-06-17 (later still) — Frank couldn't pull a listing by ID; autofix "tags: HTTP 500"; Files area
Three issues surfaced by Scott from the live phone app (screenshots):
1. **Frank said a real listing "doesn't exist."** Scott gave Frank a listing ID; Frank reported it "not in
   active or inactive inventory… not active, not draft, not inactive." The listing was actually **expired**.
   Frank's only lookup path was `list_listings`, which fetches ONE state bucket at a time and never covered
   expired/sold_out. **Fix:** added a dedicated `get_listing` agent tool that calls
   `EtsyAPIClient.get_listing(id)` directly — that endpoint returns a listing in ANY state (active, draft,
   inactive, expired, sold_out), so Frank now finds expired listings and only says "doesn't exist" on a true
   Etsy 404. Also widened `list_listings` / `_listings_sync` allowed states to include expired + sold_out.
2. **"Some fixes could not be staged: tags: HTTP 500."** `/api/autofix/tags/{id}` (and `/title/`) only
   caught `asyncio.TimeoutError` + `EtsyAPIError` around the listing fetch; every other failure (incl. the
   post-fetch local work: tag cleaning, quality-gate validation, `db.enqueue_action`) fell through as a bare
   FastAPI 500 with no detail. **Fix:** both endpoints now catch generic fetch errors (502), special-case
   404 (listing expired/deleted → 404 with a clear message), wrap the Anthropic call (502 on failure), and
   wrap all post-fetch local work so a failure returns "Could not stage tag/title fix: <reason>" instead of
   an opaque 500. The dashboard already surfaces `detail`, so Scott now sees WHY instead of "HTTP 500".
3. **Hub → Files showed "No files yet" and ZIPs couldn't be opened on a phone.** Two parts. (a) The endpoint
   only scanned the repo's `data/digital_products` + `data/backups`, which on Railway are ephemeral +
   gitignored, so nothing is ever present there — now `/api/files` also scans the durable `/data/files`
   Volume location (survives redeploys) and returns an honest `empty_reason` explaining where files must live
   if none are found. (b) Scott can't unzip on a phone, so `/api/files` now expands each ZIP's contents and a
   new `/api/files/zip-entry` endpoint streams a single file straight out of a ZIP with the correct media
   type + inline disposition — tap a sticker PNG or PDF inside a pack and it opens directly, no unzip. Plain
   files also gained an `inline=1` open mode (PDF/image preview) vs. force-download. `__MACOSX` junk filtered;
   path-traversal still blocked; bad token still 401.
- **Still true / Scott action:** the file BYTES live on Scott's machine (Etsy's API exposes file metadata
  only — no content download URL, by design, since only buyers get download links). To make product files
  appear in the phone Files area on the hosted dashboard, drop them into the `/data/files` Volume on Railway
  (or run on a machine where `data/digital_products/` is populated). The open-without-unzip behavior works
  wherever the files physically are.
- Verified: `python -m py_compile` clean; exercised `/api/files`, `/api/files/download?inline=1`, and
  `/api/files/zip-entry` end-to-end with a real temp ZIP via FastAPI TestClient (PDF→application/pdf inline,
  PNG/TXT out of ZIP with correct types, 401 on bad token, 400 on traversal, 404 on missing entry, honest
  empty_reason when no files); confirmed `get_listing` tool registered and the no-id guard returns a clean
  error.

### 2026-06-17 (later still) — one-command file sync to the durable volume
Follow-up to the Files-area work above: Scott asked for a one-command way to actually get the local product
files onto the hosted dashboard so they show up on his phone. Built it:
- **Server:** `POST /api/files/upload?path=<rel>` (bearer auth, raw body) writes into the durable `/data/files`
  volume. Path-traversal rejected, empty body rejected (400), 30MB cap (413, mirrors Etsy's 20MB per-file),
  503 if no volume is attached. Added a `HUB_FILES_DIR` env override for the volume location (also makes it
  locally testable).
- **Client:** `tools/sync_files_to_hub.py` — walks local `data/digital_products/`, GETs `/api/files` to see
  what's already in the volume, and uploads only new/changed files (size compare), so re-runs are cheap.
  Reads `RAILWAY_APP_URL` + `APP_SECRET_TOKEN` from `.env`; skips 0-byte `.gitkeep` placeholders; never
  deletes anything on the server. Usage: `python tools/sync_files_to_hub.py` (`--dry-run`, `--all` available).
  This is a LOCAL tool (runs where the files are) — deliberately NOT added to `_EXEC_COMMANDS`, since Frank
  on Railway has no files to sync.
- **Verified end-to-end live:** started the server exactly as production does (`python tools/api_server/main.py`,
  the Dockerfile CMD) against a temp volume + temp DB, ran the real urllib client against it: 102 real files
  (~201MB) uploaded, second run skipped all 102 as already-present, the synced ZIP's inner files were openable
  via `/api/files/zip-entry` — confirming the full phone flow (sync → browse → open-without-unzip). First run
  surfaced 7 "failures" that were all empty `.gitkeep` files; fixed the client to skip 0-byte files so the run
  is clean (exit 0, no server 400s).
- **Scott action to populate the phone:** add `RAILWAY_APP_URL` (the dashboard's public URL) and
  `APP_SECRET_TOKEN` (same value as on Railway) to the local `.env`, then run `python tools/sync_files_to_hub.py`.
  Re-run it any time new products are generated. Requires a Railway Volume mounted at `/data` (already used by
  the DB).

### 2026-06-17 (later still) — CRITICAL: production has NO /data volume → DB + files are ephemeral
**Symptom:** Auto-syncing product files to the phone failed for every file with
`HTTP 503 {"detail":"No persistent /data volume on this server …"}`. The v38 upload endpoint ran correctly
— it's the server that has no `/data`.
**Root cause:** The live Railway service (`calm-light`) has **no Volume mounted at `/data`**. The app's
`db._resolve_db_path()` AND the Files-area volume root both gate on `Path("/data").is_dir()`, so with no
volume BOTH fall back to ephemeral container storage. Practical impact: the SQLite DB (etsy token lineage,
staged actions, CEO learnings, weekly snapshots) is wiped on every redeploy — all the durable-DB token-sync
work from earlier 2026-06-17 has had no durable store to write to. And product files can't be synced for the
phone Files area. This had been *assumed* attached in prior entries; it never actually was.
**What I could/couldn't do:** the `RAILWAY_TOKEN` in `.env` can't reach the Railway GraphQL API — `me` →
"Not Authorized" (not an account token), `projectToken` → "Project Token not found" (not a valid project
token either); likely expired/deploy-only. (Note for next time: Railway's API is behind Cloudflare which
**blocks the default python-urllib User-Agent with HTTP 403 "error code: 1010"** — must send a browser UA.)
So the volume cannot be attached via API with the current token; it needs the dashboard or a fresh account
token.
**Fix (done in code):** `/health` now returns `build`, `persistent` (db.is_persistent()), and `files_volume`
so volume/deploy state is verifiable at a glance, no auth: `curl https://etsy-production-b2f1.up.railway.app/health`.
**Action needed from Scott (one-time, ~30s, fixes BOTH the DB durability AND the phone files):**
Railway dashboard → project `calm-light` → the Etsy service → **Settings → Volumes → New Volume**, mount
path **`/data`** → redeploy. After it redeploys, `/health` should show `"persistent": true` and
`"files_volume": true`; then run `python tools/sync_files_to_hub.py` (or it auto-runs after
`backup_digital_products.py`) and the files appear in Hub → Files on the phone.
- Note: `RAILWAY_APP_URL=https://etsy-production-b2f1.up.railway.app` was added to the local `.env` (URL
  taken from `mobile_app/src/config.js`, confirmed against the address bar in Scott's screenshots);
  `APP_SECRET_TOKEN` was already present, so the sync tool is fully configured locally now.

### 2026-06-17 (later still) — sync auto-runs after backup
`tools/backup_digital_products.py` now calls `tools/sync_files_to_hub.py` after writing the backup ZIP
(skippable with `--no-sync`), so a freshly generated product lands on the phone in one step. Best-effort:
if RAILWAY_APP_URL/APP_SECRET_TOKEN are unset or the server is unreachable, the backup still succeeds and it
just prints a note — a sync hiccup never fails the backup. Also made that script's paths ROOT-relative and
gave it a guarded `.env` loader (was `Path("data/...")` relative to CWD before).

### 2026-06-18 — dashboard now warns visibly when persistent storage is missing
Scott confirmed via `/health` screenshot that production is still running `"persistent": false,
"files_volume": false` on build c7e503a-v38 — the volume still hasn't been attached (see the entry above;
this still needs the one-time Railway dashboard action). Until that's done, the failure mode was silent —
nothing on the dashboard told Scott data wasn't durable. **Fix:** the dashboard now fetches `/health` on
load and shows a red banner ("No durable storage attached — data and synced files will be lost on next
redeploy") whenever `persistent` is false, instead of requiring a manual `/health` check to notice. Build
bumped to d2a619f-v39.

### 2026-06-18 (later) — Volumes confirmed plan-gated, not missing; to-do list seeded
Scott scrolled through every section of the Railway service's Settings (Build, Deploy, Teardown, Cron
Schedule, Healthcheck, Serverless, Restart Policy, Config-as-code, Feature-flags, Delete Service) and
confirmed there is no Volumes section at all on the current Trial plan — it's gated behind a paid upgrade
(~$5/mo Hobby plan), not a UI/navigation issue. Scott has decided to hold off on upgrading for now. Seeded
the live to-do list with this item plus the still-open GitHub repo secrets item (`RAILWAY_APP_URL` /
`APP_SECRET_TOKEN` need to be added under repo Settings → Secrets and variables → Actions so the daily
GitHub Action and Railway stop racing each other on Etsy token rotation — see the two-lineage entry above).

### 2026-06-18 (later still) — audited every command Frank/the dashboard can execute; found 3 bugs in 9
Ran every entry in `_EXEC_COMMANDS` end-to-end (same subprocess invocation `execute_command` uses) to verify
each one actually completes within its configured timeout. Confirmed working correctly as registered:
`generate_coloring_pages_preview`, `qc_sweep`, `seasonal_keywords_report`, `seasonal_keywords_preview`.
`generate_coloring_pages` / `generate_coloring_pages_quick` were not executed (real paid gpt-image-1 calls,
3–15 min runtime) — confirmed by inspection only that their `timeout: 30` is irrelevant since both are
`long_running: True` (fire-and-forget `Popen`, no wait-for-completion), so no timeout bug exists there.

Found and fixed:
- **`shop_health_check` timeout too short.** Registered at 60s; measured real runtime against the full live
  catalog is ~118s. Always timed out via the dashboard/Frank path even though the script itself runs fine
  and surfaces real findings (duplicate hero art across several Digital Paper Pack listings at pHash
  dist=0/64, unanswered reviews). Bumped to `timeout: 150`.
- **`listing_integrity_check` timeout too short.** Registered at 180s; measured real runtime is ~281.8s.
  Same failure mode — script works and returns real findings (e.g. exact-duplicate hero art, "WRONG ART in
  hero"), but always times out before Frank ever sees the result. Bumped to `timeout: 330`.
- **`rebuild_sticker_pack.py` hardcoded `/home/user/Etsy` paths + unguarded `.env` open.** Same bug class
  fixed elsewhere on 2026-06-17 (autoresponder, shop_health_check, pinterest_post_queue) but missed for this
  file — would have crashed with `FileNotFoundError` immediately on Railway. Rewritten to the same
  `ROOT = Path(__file__).resolve().parent.parent` + guarded-`.env`-open pattern. Verified clean via
  `py_compile`.
- **`rebuild_sticker_pack` removed from `_EXEC_COMMANDS` entirely (not just timeout/path-fixed).** Two
  separate problems beyond the path bug: (1) the registry entry passes zero CLI args, but the script
  requires `--pid`/`--sheets`/`--listing` with no safe defaults — it could never have completed via this
  invocation regardless. (2) More importantly, the script DELETEs the live digital file, uploads a
  replacement, and PATCHes the listing description directly against the Etsy API — there is no
  `stage_action()` approval step anywhere in it, unlike every other mutation path in this codebase. Leaving
  it registered (even after fixing the path crash) would have silently handed Frank a fully autonomous way
  to change what a customer receives and rewrite a live listing description, in direct conflict with
  CLAUDE.md's autonomy boundaries and the "NEVER LIE TO THE CUSTOMER" rule. Removed the registry entry
  (script itself is left fixed and runnable by Scott by hand) with a comment explaining why, pending a
  decision on refactoring it to use `stage_action()` before it's ever re-exposed to Frank.

Build bumped to f4b1e2a-v41. Verified `python -m py_compile` clean on `main.py`.

---

**2026-06-18 — Dashboard stuck spinning, root cause: broken JS from single- vs double-backslash escaping.**
Symptom: dashboard reported "spinning again" after the Platform Connections roadmap-steps feature shipped.
`python -m py_compile` on `main.py` passed clean (it's valid Python), which is why the earlier
push looked safe — the bug only exists in the JS text the Python string *emits*, not in the Python
syntax itself. Root cause: `_WEB_UI` is one giant non-raw `"""..."""` Python string containing the
dashboard's HTML/JS. To make the embedded JS contain a literal `\'` (escaped quote inside a JS string),
the Python source must write `\\'` (double backslash) — a single `\'` gets collapsed by Python's own
string-escape processing into a bare `'` before it ever reaches the browser. The `toggleCredSteps`
onclick handler added in commit `e0157e7` used `\''+key+'\'` (single backslash), which rendered as
`''+key+''` in the actual served JS — `Unexpected string` syntax error, confirmed with
`node --check` on the extracted `<script>` block, which aborted the entire script tag and froze every
dashboard tab on its loading spinner. Fixed by doubling the backslashes (`\\''+key+'\\'`), matching the
one other pre-existing correct example of this pattern at the "ZIP's contents" string. Verified by
re-fetching `/` from a locally running instance and running `node --check` on the extracted script —
passes clean now.
**Takeaway:** `py_compile` only proves the Python is valid — it can't catch bugs in *text the Python
generates*. Any future edit to `_WEB_UI` must extract the `<script>...</script>` block from a live
response and run `node --check` on it before pushing.

---

**2026-06-18 (later) — Chat (Frank) and Conversion Doctor both failing: Anthropic account out of credits, plus a real bug in the Diagnose endpoint.**
Symptom: Scott reported two failures at once. (1) Frank's chat returned a raw `Error code: 400` block on
every message: `'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing
to upgrade or purchase credits.'` (2) The Conversion Doctor "Diagnose again" button on a listing returned
a bare, uninformative `HTTP 500` with no message.
Root cause of (1) is account-level, not code — the Anthropic API key backing this app has run out of
credits. **This cannot be fixed by Claude Code.** Scott needs to go to console.anthropic.com → Plans &
Billing and add credits; nothing in the codebase is broken here. The chat path already had correct error
handling (`chat_ws` catches `Exception` and sends the raw message text back over the websocket), which is
why the user saw the real Anthropic error text in the chat — that's the system working as intended,
surfacing a billing problem instead of swallowing it.
Root cause of (2) was a separate, real code bug: `diagnose_listing` (`/api/diagnose/{listing_id}`) only
caught `asyncio.TimeoutError` around its `ai_client.messages.create()` call — no `except anthropic.APIError`
handler, unlike `_compute_suggestions_inner` which already had the correct pattern. So the exact same
billing error that showed cleanly in chat instead crashed this endpoint into an unhandled exception, and
FastAPI's default 500 has no `detail` field, so the frontend's `d.detail||'HTTP '+r.status` fallback
rendered the unhelpful bare "HTTP 500". Fixed by adding:
`except anthropic.APIError as exc: raise HTTPException(status_code=502, detail=f"Anthropic API error: {exc}")`
immediately after the existing timeout handler, mirroring `_compute_suggestions_inner`. Verified with
`python -m py_compile` (no JS/`_WEB_UI` text was touched, so no `node --check` was needed this time).
**Takeaway:** every endpoint that calls `ai_client.messages.create()` directly needs both a timeout
handler and an `anthropic.APIError` handler — copy the pattern from `_compute_suggestions_inner`, don't
let any new endpoint skip it. This fix makes future Anthropic errors show a real message instead of a
bare 500, but does not and cannot fix the underlying billing issue — that's purely Scott's action.

### 2026-06-19 — Railway volume still not attached (re-verified, FRANK Command Center build start)
Symptom: kicking off the FRANK Command Center rebuild, Step 0 is "fix persistence." Re-checked
`/health` — still `"persistent": false, "files_volume": false`. Re-tested `RAILWAY_TOKEN` against
`backboard.railway.app/graphql/v2` (`me` query) — still "Not Authorized," same as 2026-06-17. No change;
this token cannot attach a volume via API.
**Action still needed from Scott (unchanged, ~30s):** Railway dashboard → project `calm-light` → Etsy
service → Settings → Volumes → New Volume → mount path `/data` → redeploy. Confirms via
`curl https://etsy-production-b2f1.up.railway.app/health` showing `persistent: true`.
**What I did instead:** proceeded with the parts of the FRANK Command Center plan that don't depend on
the volume — starting with the static HTML/CSS mockup (Build Order step 0.5) — so the dashboard rebuild
isn't blocked waiting on a manual click only Scott can do.

### 2026-06-19 — FRANK Command Center static mockup live at /frank (Build Order step 0.5)
Added `tools/api_server/frank_hud_mockup.py` (self-contained HTML/CSS/canvas-JS, no external deps,
matches existing no-webfont/no-framework convention) and a new `/frank` route in `main.py` serving it,
fully separate from the live `/` dashboard so production is never at risk while this is reviewed.
Mockup covers the full reference layout: left nav (Command Center/AI Core/Agents/Tasks/Calendar/Memory/
Conversations/Knowledge Base/Tools & Skills/Workflows/Studio + Voice Status/Focus Mode widget), top bar,
AI Core Overview column, animated canvas orb (idle rotation, click-to-preview "speaking" reactive distortion
— real audio-amplitude wiring is Step 4), Active Agents tile row (5 real loops + Local Relay + Context
Compactor marked "not built"), System Monitor, Live Intelligence Feed, Mission Timeline, Quick Commands,
bottom Talk-to-Frank bar. Every placeholder panel has an inline comment naming its real future data source
— no invented numbers presented as fact. Bumped `_BUILD_ID` to f4b1e2a-v42. No backend wiring; Step 1 (real
local file tools + approval gate detail view) is next once Scott signs off on the look.

### 2026-06-19 — FRANK mockup v2: fixed mobile rendering + orb/layout structure (Scott feedback)
Scott reviewed the v1 /frank mockup and sent two corrections: (1) reference screenshot showing the orb
was missing/buried and panels felt "compressed into the middle instead of having clear layer out
sections," and (2) an actual mobile Safari screenshot showing the page rendering squished into the top
third of the screen with a large blank area below. Root cause of (2): `<meta viewport width=1440>` +
`body{height:100vh}` doesn't scale reliably on mobile browsers. Fix: rebuilt the page around a fixed
1440x900 `#stage` div with `width=device-width` viewport meta + JS `fitStage()` that computes
`scale=min(innerWidth/1440, innerHeight/900)` and applies `transform:scale()` on load/resize — renders
at correct proportions (letterboxed) on any screen. Root cause of (1): `.main` was a single 3-column CSS
grid burying a small 220px orb among other panels. Fix: restructured into 3 explicit flex rows (rowA:
AI Core Overview | large dedicated Orb Hero panel (300px canvas) with text overlay | Live Intelligence
Feed; rowB: Active Agents | Mission Timeline | Quick Commands; rowC: System Monitor | Memory Insights |
LLM Status), proportions matched to the reference image, plus corner-bracket (`.brk`) panel accents for
clearer section separation. Verified via FastAPI TestClient hit on /frank (200 OK, all new markers
present) before deploy. Bumped `_BUILD_ID` to f4b1e2a-v43.

### 2026-06-19 — FRANK mockup: added 6 missing Hub tabs (Listings/Products/Brand Kit/Files/Connections/Security)
Scott asked "It will have the roadmap section and everything from the hub in it?" — surfaced a real plan
gap: the nav-mapping table only covered tabs present in the JARVIS reference image, silently dropping six
real, currently-used Hub sections (Listings, Brand Kit, Products, Files, Credentials+Platform Connections
Roadmap, Security Posture). Researched the live Hub code to confirm each one's real source function
(loadListings() main.py:1592, loadProductIndex() main.py:2263, _renderBrandKit() main.py:2217, loadFiles()
main.py:2455, loadCredentials() main.py:2349 + Roadmap array main.py:2280-2394, _renderSecurityPosture()
main.py:2391), asked Scott how to reconcile them with the fixed reference nav, and per his answer ("Add
new dedicated tabs") added each as its own top-level tab under a new "Shop" nav-section in
frank_hud_mockup.py, following the existing placeholder-screen pattern (each names its real source +
line number, states "restyled into the HUD shell in Step 2" since these are working screens being ported,
not new builds). Verified via FastAPI TestClient hit on /frank (200 OK, all 6 new nav-item + screen markers
present) before deploy. Bumped `_BUILD_ID` to f4b1e2a-v44.

### 2026-06-19 — Autoresponder agent: Etsy API has no messaging endpoint (silent "ok", never actually working)
**Symptom:** the live-status agent registry showed `autoresponder` as `status: "ok"`, but its detail field
embedded "Etsy API 404: Resource not found" inside the supposedly-healthy status. The autoresponder loop has
likely never fetched a single buyer message despite reporting healthy every run.
**Root cause:** Etsy Open API v3 has **no buyer-seller messaging/conversations endpoint** for third-party
apps. Confirmed by probing through the already-correctly-authed `EtsyAPIClient`: `shops/{id}/listings/active`
→ 200 and `shops/{id}/receipts` → 200 (proves the token/scopes are fine), but both `shops/{id}/conversations`
and `shops/{id}/messages` → 404. Separately confirmed a real scope denial returns 403, not 404 — so a 404 on
an otherwise-authorized account means the route simply does not exist, not a permissions problem. In
`tools/etsy_autoresponder.py`, the failure is caught, printed, and the script `return`s → exit code 0 →
`_autoresponder_loop` (main.py) sets heartbeat "ok" purely from `returncode == 0` without inspecting stdout
for an embedded failure message.
**Fix (pending Scott):** re-authorizing with more scopes will not help — the endpoint doesn't exist on Etsy's
side. This matches CLAUDE.md's own note that Etsy has no API-driven buyer messaging, only Shop Manager Quick
Replies / Auto-Reply (manual or built-in auto-reply windows only). The autoresponder agent as designed can't
do its job via the API. Options for Scott: retire the agent, or convert it to an honest no-op/disabled state;
either way the heartbeat check should be fixed to inspect actual output instead of trusting exit code 0. No
code changed yet — flagged for a decision.

### 2026-06-19 — Quality Audit agent "could not parse summary line" error not reproducible
**Symptom:** the live-status registry showed `quality_audit` as `status: "error"`, detail "could not parse
summary line".
**Investigation:** ran `tools/listing_integrity_check.py` to completion against the live shop (172 listings,
~280s) — it finished clean and printed a summary line that matches main.py's summary-parsing regex exactly
("✓ PASS / ⚠ WARN / ✗ FAIL" counts). Not a deterministic bug reproduced on this run; most likely a transient
unhandled exception mid-run (e.g. one bad live Etsy API call) before the summary print on the run that
actually failed.
**Observability gap to fix later:** when the regex fails, `_quality_audit_loop` discards the real `stdout`/
`stderr` and persists only the generic "could not parse summary line", making the actual root cause
invisible from the HUD. Should persist a truncated tail of the real output on parse failure so a future
occurrence is diagnosable instead of guessed at.

### 2026-06-19 — Two "Set of 4" listings may deliver only 1 design (Cardinal Rule risk, not infra)
**Surfaced by:** `tools/listing_integrity_check.py`'s `quantity_claim_mismatch` gate, which flags when a
listing's title claims a design count (e.g. "Set of 4") that doesn't match the number of digital files
actually attached. `4512301880` (Boho Botanical Set of 4) and `4512784922` (Four Seasons Set of 4) each have
a single `DP10xx_print_sizes.zip` attached — `generate_print_sizes.py`'s naming convention produces one such
ZIP per design (multiple print *sizes* of one design, not multiple designs). Prior `fix_queue.json` work on
both was photos-only ("using DP1065/DP1070 art source", singular) — the underlying file-quantity question was
never addressed by that work.
**Cannot fully confirm ZIP internals from this cloud container** (source files are gitignored locally and
Etsy's API exposes only file metadata, not content download, for the seller's own listings), but every
available signal (title says 4, one ZIP attached, naming convention implies one design per ZIP) points to
customers paying for 4 designs and receiving 1.
**Note:** the third "Set of 4" listing checked as a possible control case, `4512784817` (Coastal Set of 4),
is NOT a clean comparison — `data/listing_audit_report.json` already separately flags it with its own
unrelated Cardinal Rule issue ("IMAGE CONTENT: MISMATCH: the image shows a single framed artwork of a turtle
instead of a set of four coastal art prints") plus missing AI disclosure and only 6/10 photos uploaded. So no
verified "this is what a correct Set-of-4 listing looks like" example was confirmed in this pass — don't cite
it as a control case in future reasoning about this issue.
**Action:** flagged to Scott for a fix-or-pull decision on `4512301880`/`4512784922` — Hard Stop, no
listing/file changes made autonomously. Logged here for the record, not as a fixed item.

### 2026-06-19 — Resolved: autoresponder retired, two mismatched listings staged for deactivation
Scott decided both items above. **Autoresponder:** `_autoresponder_loop`, its `_AGENT_LOOP_LABELS` entry, and
its `asyncio.create_task(...)` registration were removed from `main.py` (the standalone
`tools/etsy_autoresponder.py` script itself was left in place, just unscheduled). The stale `autoresponder`
row in `agent_heartbeats` was cleared via a new `db.delete_agent_heartbeat()` function so the Agents HUD
doesn't show a frozen tile for a loop that no longer runs.
**Quantity-mismatch listings:** added a `deactivate_listing` staged-action type (same pattern as
`publish_listing`, sets `state: "inactive"`) since no staged path for deactivation existed before — only a
direct human-only endpoint. Staged both `4512301880` and `4512784922` via `db.enqueue_action` referencing this
finding; both sit as `pending` in the Action Center queue. Nothing on Etsy has changed — Scott must still tap
Approve for either listing to actually go inactive.

### 2026-06-19 — Closed: both quantity-mismatch listings approved and taken off the storefront
Scott explicitly approved ("I want you to deactivate those"). Ran `approve_action`'s code path (validate →
`_execute_staged_action` → `client.update_listing(lid, {"state": "inactive"})`) for queue IDs `1` and `2`.
Both now show `status: "executed"` in `action_queue`.
**API quirk found:** Etsy's PATCH response reports `state: "edit"` for both listings, not `"inactive"` as
requested. This is a real, distinct Etsy listing state (not an error) — likely returned because the PATCH
payload only sets `state` without re-sending other listing fields Etsy wants on a full update. Confirmed by
paginating the full `shops/{shop_id}/listings/active` feed (140 results) end to end: neither `4512301880` nor
`4512784922` appears, so the practical effect (off the public storefront, not purchasable) is achieved even
though the literal state string differs from what was requested. If a future check needs to confirm "is this
listing live," do not rely on `state == "inactive"` alone — also check absence from the `listings/active` feed,
since Etsy may return `edit` for what is functionally the same outcome.
**Result:** `4512301880` (Boho Botanical Set of 4) and `4512784922` (Four Seasons Set of 4) are confirmed off
the storefront. Finding fully closed — not just staged.

### 2026-06-20 — DP1026–DP1029 sticker pack ZIPs missing locally; live listings unaffected
New pre-publish file gate (`approve_listing.py`'s `check_product_files()`, added this session) flagged
`DP1026_sticker_pack.zip` / `DP1027` / `DP1028` / `DP1029` as missing from
`data/digital_products/product_files/`. Checked `client.get_listing_files()` against all four live listing
IDs (4509179201, 4509184958, 4509184962, 4509184968) — each still has its sticker pack ZIP, PDF, and undated
PDF attached and correctly sized on Etsy's side. **No customer-facing problem; did not deactivate anything.**
Tried to restore the local copies and could not: (1) Etsy API v3 exposes no download URL on
`GET .../listings/{id}/files` — sellers cannot pull back an already-uploaded digital file via API by design;
(2) neither `data/backups/digital_products_backup_20260616_163922.zip` nor the 06-17 backup contains these
sticker ZIPs (they predate this gap or never captured them); (3) `tools/rebuild_sticker_pack.py` needs source
sheet PNGs (`sheet_01_functional_planning.png` etc.) to rebuild a pack, and those aren't present locally either
— only `DP102[6-9]_cover.png` survived. Only manual path: Scott downloads the file from Etsy Shop Manager's
listing-edit UI (it has a download icon per file even though the API doesn't), or pulls it from wherever he
saved the original backup ZIP from `backup_digital_products.py`. Left open — informational, not urgent.

### 2026-06-20 — DP1026–DP1029 listing descriptions understated real page counts (truthfulness fix)
The same file-gate work above led to comparing each PDF's actual content against the published description.
Used `pypdf.PdfReader(...).outline` on the live `data/digital_products/product_files/DP102[6-9].pdf` files and
found real page counts of 143/131/144/133 — all higher than what the live Etsy descriptions and
`qc_sweep.py`'s `PLANNER_PAGES` dict claimed (104/90/102/91). Confirmed via the outline that the extra pages
are real, intentional sections already on CLAUDE.md's roadmap (Daily Pages × 365, Brain Dump, SMART Goals,
Year in Pixels, Class Schedule, Priority Matrix, Pomodoro Focus Tracker, Debt Payoff Tracker, Savings Goal
Tracker, Bill Payment Checklist, Progress Photos Log, 30-Day Water Tracker, Sleep Quality Log, Non-Scale
Victories) — not a generation bug or duplicate pages. This was a real violation of CLAUDE.md's "never lie to
the customer" rule (wrong page count + missing sections in description). **Fix:** rewrote each live
description via regex-anchored substitution (`/tmp/desc_work/fix_descriptions.py` — anchors on the
surrounding text rather than an exact hand-typed match, to avoid the byte-mismatch bug from an earlier
attempt) and pushed via `client.update_listing()` to all four listings (4509179201, 4509184958, 4509184962,
4509184968) — confirmed live with correct page counts and the new section bullets. Also updated
`tools/qc_sweep.py`'s `PLANNER_PAGES` dict (104→143, 90→131, 102→144, 91→133) so the count-accuracy gate stops
flagging these as WARN, and synced CLAUDE.md's "Product Catalog" and "Pre-Written Listing Content" sections to
match. **Still open:** Scott should be told the underlying PDFs grew without anyone updating the listing
copy — worth a quick process check on whatever workflow regenerates these PDFs, so the description doesn't
drift again next time content is added.

### 2026-06-20 — Western SVG commercial license listing told buyers to purchase a second listing that doesn't exist (truthfulness fix)
**Symptom:** While deciding what to do about `SVG_WESTERN`'s `"incomplete"` catalog status, found it isn't
just a dormant unbuilt product — it's tied to a live, active $24.99 listing (4515437442, "Commercial
License, Western SVG Bundle 12 Designs"). Its description said "Purchase the personal use listing (linked
in the description above) to receive the files" and "You receive the same files as the personal use listing
PLUS this commercial license certificate," and its FAQ said "Yes — this listing is the license only.
Purchase the regular listing for the design files."
**Root cause:** No such "personal use listing" exists or ever existed — confirmed via `c.get_listing_files()`
that the design ZIP (`OnBrandCraftz_western_SVG_Bundle.zip`, 15.98MB, 12 designs) is already directly attached
to and deliverable by this very license listing, and via a shop-wide search of all 140 active listings that
zero other listings contain "western" in the title. The description text was carried over from a planned
two-listing (personal-use + commercial-license) model that was apparently never actually built, leaving buyers
told to go find and purchase a listing that doesn't exist in order to receive files they already paid for.
**Fix:** Edited the live description via `client.update_listing(4515437442, {"description": ...})` — removed
the "purchase the personal use listing" line, the matching "same files as the personal use listing" line, and
the FAQ Q&A, replacing all three with accurate statements that this purchase includes both the commercial
license and the full design file set, delivered instantly. Verified live: false text gone, ZIP attachment
(filename/size/file_id) unchanged. Did not touch price, photos, tags, or `product_catalog.json`'s
`SVG_WESTERN` `"incomplete"` status — that entry tracks a separate personal-use product that was never built
(build-vs-abandon decision, out of scope for this fix).

### 2026-06-20 — DP1034 (Ultimate Celestial Life Planner) sticker pack was short of the 200+ standard, and rebuilding it blew the 20MB Etsy file limit
**Symptom:** `DP1034_sticker_pack.zip` (Celestial Night theme, built by `tools/generate_celestial_assets.py`)
shipped with only 115 individual stickers across 5 sheets — short of CLAUDE.md's 5-sheet/200+ minimum. After
generating 4 more sheets (6-9: Zodiac & Affirmations, Bonus Celestial Extras, Date Dots & Labels, Mini Icons
& Motivational Tags) to bring the count to 233, the rebuilt ZIP came out at 28MB — over the 20MB Etsy hard
limit (`ZIP size: under 20 MB` per the sticker pack QC checklist).
**Root cause:** gpt-image-1 PNG output for these transparent sticker sheets is full 32-bit RGBA with no
palette reduction — 9 sheets + 233 cropped individuals at that bit depth totalled ~29MB uncompressed, and PNG
deflate gets almost no win on already-noisy AI-generated raster art.
**Fix:** Added `--append-sheets` to `generate_celestial_assets.py` so new sheets can be generated and merged
into the existing pack without regenerating sheets already on disk. Quantized every sheet and individual
sticker PNG to a 256-color adaptive palette via `Image.quantize(colors=256, method=Image.Quantize.FASTOCTREE)`
(alpha channel preserved correctly — verified anti-aliased edges still gradient, not hard-cut) before
rezipping. Final pack: 9 sheets, 233 individual stickers, 2.7MB total (was 28MB). Spot-checked sheets 6 and 8
visually post-quantization — flat kawaii cel-shaded art shows no visible quality loss at 256 colors.
**Note for future sticker packs:** quantize every PNG (sheets + individuals) to 256 colors before zipping by
default — don't wait to discover the 20MB limit after the fact.

### 2026-06-20 — Cover-art destructive-overwrite bug shipped the wrong cover on 4 LIVE listings (DP1026-1029)
**Symptom:** DP1030's freshly AI-generated matcha-themed cover was found replaced by a generic indigo/gold
"Celestial Night" design. Investigating the code path revealed the bug was systemic, not a one-off — DP1026,
DP1027, DP1028, and DP1029 (all live, currently-selling listings) had been shipping the same indigo/gold
placeholder cover instead of their documented Lavender Dreams / Cotton Candy / Midnight Blue / Coral Peach
covers. This violated the "NEVER LIE TO THE CUSTOMER" rule — customers were receiving planners whose cover
didn't match the listing's theme.
**Root cause:** `generate_planner_v2.py` wrote newly-generated AI cover art to `{pid}_cover.png`, but
`planner_hyperlinker.py`'s `finalize()` checked for a *different* filename (`{pid}_cover_ai.png`) to decide
whether real AI art existed. Since that file never existed for these products, `finalize()` always fell
through to `build_cover_png()`, which wrote directly into `{pid}_cover.png` — silently destroying the real
AI art that had just been generated there. Both cover builders also used hardcoded module-level "Celestial
Night" color constants regardless of which product was being built, so the placeholder was always indigo/gold.
**Fix:** Renamed the AI-cover output path in `generate_planner_v2.py` to `{pid}_cover_ai.png` so it matches
what `finalize()` looks for. Parameterized `build_cover_png()`/`compose_ai_cover()` in `planner_hyperlinker.py`
to accept the product's real theme/accent/bg/dark colors instead of always using the hardcoded constants
(DP1034 pinned to the legacy defaults — its exact 3-tone gradient can't be reconstructed from the 4 generic
theme colors; verified byte-for-byte identical output post-fix). Regenerated theme-correct AI covers for
DP1026-1030 via `tools.image_gen.generate_image()`, rebuilt all dated+undated PDFs through the fixed pipeline,
visually confirmed each cover matches its documented theme, and re-uploaded the corrected `{pid}.pdf`/
`{pid}U.pdf` files to the 4 live listings (4509179201/4509184958/4509184962/4509184968) via
`delete_listing_file()` + `upload_listing_file()` — all 8 files passed `validate_digital_file()` with zero
errors. DP1030 remains an unpublished pilot; its files were fixed but no new listing was published.

### 2026-06-21 — `/` and `/frank` had zero auth; the API bearer token was readable in their page source
**Symptom:** Investigating "is Frank protected," found `GET /` and `GET /frank` had no auth check at all —
anyone with the URL got the full page, no token needed. That's worse than it sounds, because the same page
embeds the literal `APP_TOKEN` value used for every `/api/*` Bearer check and both `/ws/*` query-param checks
(`const TOKEN = ...` in `_WEB_UI`, `render_frank_hud(APP_TOKEN)`). So the API's "auth" was theater — loading
the unauthenticated page handed over the key to everything else. Also found `APP_TOKEN` defaulted to the
literal string `"changeme"` if `APP_SECRET_TOKEN` was ever unset (fails open, not closed).
**Fix:** Added a passphrase login gate in `tools/api_server/main.py` (only file touched) in front of both
`/` and `/frank`: `GET /login` / `POST /login` check the submitted passphrase against the existing
`APP_SECRET_TOKEN` (no new credential), set an HttpOnly/Secure/SameSite=Lax session cookie on success
(in-memory session store, 30-day TTL), and `GET /logout` clears it. `web_ui()`/`frank_hud_mockup()` now
redirect (307) to `/login?next=...` if the session cookie is missing/expired. Added a per-IP login rate
limiter (5 failed attempts / 15 min → 429) since there was no rate limiting anywhere in the app before.
Removed the `"changeme"` default — the server now raises `RuntimeError` at startup if `APP_SECRET_TOKEN`
is unset, instead of silently accepting a guessable token. `/api/*` Bearer auth and `/ws/*` query-token auth
are unchanged. Verified end-to-end: unauthenticated `GET /`/`/frank` → 307; 6th bad passphrase from one IP →
429; correct passphrase → cookie set + redirect; cookie then grants `/` and `/frank` normally; `/api/listings`
still 403 without Bearer token, 200 with it. Deferred (not done this round): moving the WS token off the URL,
tightening CORS, adding CSP/security headers.


## 2026-06-21 — Automated quality audit — 44 listing(s) failing
Daily listing_integrity_check found 44 FAIL / 24 WARN out of 172 listings audited. Details:
[4488477854] P3D_CRYSTAL_GLOW_LAMP — Crystal Glow Lamp, 3D Printed Faceted RGB Table Lamp, U…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4488532602] P3D_RIBBED_VASE_FOR_DRIED_FLOWERS — Ribbed Vase for Dried Flowers, 3D Printed Boho Decor, M…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4488666558] P3D_COFFEE_BAR_SIGN — Coffee Bar Sign, 3D Printed Cat Kitchen Decor, Housewar…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4490472707] P3D_SCULPTURAL_MESH_LAMP — Sculptural Mesh Lamp, 3D Printed Geometric Table Lamp, …
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4492610660] P3D_TEXTURED_TEA_LIGHT_HOLDERS — Textured Tea Light Holders, 3D Printed Candle Holder Se…
  Type: 3d_print_physical | Photos: 4 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 4 photos (want ≥8)

  [4497392795] P3D_GEOMETRIC_GLOW_LAMP — Geometric Glow Lamp, 3D Printed Table Lamp, Modern Home…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4507783049] P3D_MINIMALIST_PEN_HOLDER — Minimalist Pen Holder, 3D Printed Desk Organizer, Moder…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4509600086] DP1035, DP1064 — Tropical Leaves Print, Bold Monster


## 2026-06-21 — Automated quality audit — 44 listing(s) failing
Daily listing_integrity_check found 44 FAIL / 24 WARN out of 172 listings audited. Details:
[4488477854] P3D_CRYSTAL_GLOW_LAMP — Crystal Glow Lamp, 3D Printed Faceted RGB Table Lamp, U…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4488532602] P3D_RIBBED_VASE_FOR_DRIED_FLOWERS — Ribbed Vase for Dried Flowers, 3D Printed Boho Decor, M…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4488666558] P3D_COFFEE_BAR_SIGN — Coffee Bar Sign, 3D Printed Cat Kitchen Decor, Housewar…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4490472707] P3D_SCULPTURAL_MESH_LAMP — Sculptural Mesh Lamp, 3D Printed Geometric Table Lamp, …
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4492610660] P3D_TEXTURED_TEA_LIGHT_HOLDERS — Textured Tea Light Holders, 3D Printed Candle Holder Se…
  Type: 3d_print_physical | Photos: 4 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 4 photos (want ≥8)

  [4497392795] P3D_GEOMETRIC_GLOW_LAMP — Geometric Glow Lamp, 3D Printed Table Lamp, Modern Home…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4507783049] P3D_MINIMALIST_PEN_HOLDER — Minimalist Pen Holder, 3D Printed Desk Organizer, Moder…
  Type: 3d_print_physical | Photos: 5 | Files: 0 | Tags: 13
    ✗ [photo_count] Only 5 photos (want ≥8)

  [4509600086] DP1035, DP1064 — Tropical Leaves Print, Bold Monster

## 2026-06-22 — Production crash-loop fixed (server had been stuck on stale code) + Railway token fix
**Symptom:** Three consecutive deploys after the Part A/B security-hardening commits never went live —
production kept serving an old build. Railway CLI auth also appeared broken (`railway whoami`/`railway
status` failed with "Invalid RAILWAY_TOKEN" using Scott's new personal token).

**Root cause 1 (Railway CLI auth):** Scott's token is an account-level personal token, not a project-scoped
token. Railway CLI only accepts personal tokens via the `RAILWAY_API_TOKEN` env var — `RAILWAY_TOKEN` is for
project-scoped tokens only, and silently produces a misleading "Invalid RAILWAY_TOKEN" instead of a
wrong-token-type error. Confirmed valid by querying the GraphQL API directly (`query { me { email } }`)
before touching the CLI var name. Fixed by renaming the `.env` key from `RAILWAY_TOKEN` to
`RAILWAY_API_TOKEN`.

**Root cause 2 (the actual production outage):** `tools/api_server/main.py` has imported `openai` since the
voice-feature commit (`ec034aa`), but `Dockerfile`'s hand-picked `pip install` list was never updated to
match — `requirements.txt` lists `openai` but is NOT what governs the Docker build (`railway.toml` uses
`builder = "dockerfile"`, which ignores `requirements.txt` entirely). Every deploy since `ec034aa` crashed
on `ModuleNotFoundError: No module named 'openai'` at startup, looped through all 10 restart attempts, failed
health checks, and Railway kept serving the last build that had actually gone live — silently, with no
error surfaced anywhere obvious. `PyPDF2` (used by `etsy_api.py`'s digital-file PDF validation) was also
missing from the same list — found via an AST-based audit of all of `main.py`'s real dependencies before it
could cause a second crash-loop cycle.

**Fix:** added `"openai>=1.0.0"` and `"PyPDF2>=3.0.0"` to `Dockerfile`'s pip install (quoted to avoid the
`PyPDF2>=3.0.0` → shell `2>` redirect parsing trap). Commit `4c3737d`, pushed to
`claude/etsy-automation-agents-WFAPU`. Deploy `eb0abf50` succeeded and is now `RUNNING`; verified live:
`/health` returns 200, all new security headers present (CSP, X-Frame-Options, HSTS, etc.), `/api/ws-ticket`
now exists (403 without auth, not 404) — confirming the security-hardening work from earlier the same day is
finally actually live, not just committed.

---

## 2026-06-22 — Voice in/out broken on live Frank: OpenAI account out of quota

**Symptom:** Scott reported "voice communication is not working" in the Frank PWA on his phone.

**Diagnosis:** Hit the live TTS endpoint directly —
`POST /api/voice/speak {"text":"..."}` on the production URL returned HTTP 502 with body
`speech synthesis failed: Error code: 429 - insufficient_quota` ("You exceeded your current quota,
please check your plan and billing details"). Both voice endpoints depend on OpenAI
(`/api/voice/speak` → OpenAI TTS `tts-1`; `/api/voice/transcribe` → Whisper `whisper-1`), so an
account-level quota exhaustion takes out voice in AND out simultaneously. Same `429 insufficient_quota`
was also observed when testing the new reject-with-reason photo auto-regeneration (gpt-image-1), confirming
this is account-wide, not endpoint-specific.

**Root cause:** The OpenAI account behind `OPENAI_API_KEY` has exceeded its quota / has a billing issue —
NOT a code or deploy bug. `OPENAI=True` at startup (key is present and loaded); the key is simply rejected
at spend time.

**Fix:** Billing-side only — add credits / fix payment method at platform.openai.com → Settings → Billing.
No redeploy needed; all OpenAI-backed features (voice TTS+Whisper, gpt-image-1 photo generation, the
reject-fix photo loop) resume the moment the account has quota again.

---

## 2026-06-23 — Raw Anthropic error text leaking to users + 2 mislabeled "AI Core Overview" status dots

**Symptom:** Scott sent a screenshot of the live Frank dashboard: "There are still a lot of errors in
frank." The chat bubble showed a raw `Error code: 400 - {'type': 'error', ...'Your credit balance is too
low...'}` dump when he asked Frank to talk back, the Suggestion Warmer widget showed the same raw
`Anthropic API error: <exc>` string as its heartbeat detail, and "AI Core Overview" showed "Voice: Offline
— not built yet" and "Memory: Not wired yet" even though both features are fully built and working.

**Diagnosis:**
1. The trigger was a real Anthropic billing issue (credit balance too low) — but the chat WS handler
   (`main.py` `chat_ws`) and two suggestion-generation endpoints (`_compute_suggestions_inner`,
   `diagnose_listing`) all forwarded `str(exc)` / `f"Anthropic API error: {exc}"` straight to the client,
   so any Anthropic exception (billing, rate limit, auth, overload) dumped raw Python exception text into
   the UI instead of a readable message.
2. `frank_hud_mockup.py`'s "Voice" AI-Core-Overview indicator was bound to the `local_relay` agent's
   status (a leftover copy-paste from when Voice and Relay were being built around the same time) —
   Voice has zero dependency on the relay, it's a stateless feature of this same server
   (`/api/voice/transcribe`, `/api/voice/speak`), so it always showed the relay's "not built yet"
   placeholder regardless of whether voice itself worked.
3. "Memory" was a permanent hardcoded stub (`'Not wired yet'`) that was never wired to the already-working
   `/api/memory` endpoint (used elsewhere on the dashboard's Memory tab).

**Confirmed NOT bugs (left untouched, called out to Scott separately):** "System: Ephemeral (volume not
attached)" is accurate — no Railway persistent volume is attached (see 2026-06-17 entry above) — and
"Local Relay: Offline" is accurate — `tools/relay/frank_relay.py` is fully built but has never been
started on Scott's machine. Both require action outside this repo, not a code fix.

**Fix:** Added `_friendly_error_message(exc)` in `main.py` that maps known Anthropic failure signatures
(credit balance, rate limit, auth, overload) to short human-readable strings, with a generic fallback;
wired it into the chat WS error path, both suggestion-endpoint `HTTPException` details, and the Suggestion
Warmer's stored heartbeat — raw exception text is still printed server-side for debugging, just never sent
to the client. In `frank_hud_mockup.py`, removed the relay-bound Voice block from `loadAgents()` and
instead set Voice to Online/Offline based on whether `/health` answers (inside
`loadCredentialsAndHealth()`); replaced the Memory stub with a live fetch of `/api/memory`, rendering
real session/learnings counts.
