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

## Known Recurring Issues
*Auto-generated by the quality-audit loop -- a failure heading that's appeared 3+ times below. Investigate the root cause rather than re-fixing the symptom each time.*

- **automated health check failure (known cause)** — seen 7 times

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

---

## 2026-06-23 — Frank's installed PWA was unusable on Scott's phone (content cut off, no mobile nav)

**Symptom:** Scott: "I need the app on my home screen to be able to show everything on Frank's main page
and not be cut off... I want to make sure I can work from my phone without losing function." The installed
home-screen PWA showed the desktop layout shrunk to ~27% size with most screens' content clipped.

**Diagnosis (confirmed via grep against the 3,000+ line inline template in `frank_hud_mockup.py`, no
guessing):**
1. The entire dashboard is a fixed 1440×900px `#stage` that JS (`fitStage()`) uniformly scaled down to fit
   any viewport via `transform:scale()` — on an iPhone (390×844) that's `scale≈0.271`. Zero `@media`
   queries existed anywhere in the CSS; the scale hack was the only "mobile" handling, and it reflowed
   nothing.
2. 8 screens (Tasks, Action Center, Calendar, Memory, Conversations, Knowledge Base, Tools & Skills,
   Workflows) plus `.hub-scroll` (Listings/Products/Brand Kit/Files/Connections/Security) and Studio's
   video list hardcoded inline `max-height:700px`/`760px`/`420px`, sized for the 900px-tall desktop stage —
   these clipped content on a phone regardless of the stage-scaling fix.
3. The 226px-fixed sidebar nav (16 screens, 4 groups) had no mobile pattern — at 390px wide it would have
   eaten 58% of the screen.

**Fix (all in `frank_hud_mockup.py` unless noted):**
- Viewport meta tag: added `viewport-fit=cover` so `env(safe-area-inset-*)` resolves on iOS standalone mode.
- `fitStage()`: now checks `window.matchMedia('(max-width:880px)')` and skips the scale transform on
  mobile (`stage.style.transform='none'`); a `syncMobileClass()` function toggles `body.is-mobile` on
  resize/orientation-change so CSS and JS agree on mode.
- New `@media (max-width:880px)` block (plus a nested `@media (max-width:380px)` for small phones):
  `#stage` goes fluid and the whole page becomes a normal scrolling document (`html,body{overflow-y:auto}`,
  `#stage{height:auto}`); the sidebar becomes a fixed off-canvas drawer
  (`translateX(-100%)` ↔ `translateX(0)` via `body.drawer-open`) with its own backdrop and a duplicate
  search input (the header search/clock are hidden on mobile to make room for the hamburger button);
  `.mrow` panel rows stack vertically full-width instead of sitting in fixed-width columns; the agents grid
  collapses 4→2→1 columns; every one of the 8 hardcoded `max-height` clamps plus `.hub-scroll` and
  `#studio-videos-list` get `max-height:none !important;overflow:visible !important`; touch targets
  (`.nav-item`, `.icon-btn`, `.qc-btn`, `#chat-send`, `.talk-pill`) were bumped to ~40-44px; safe-area-inset
  padding was added to the header/footer/drawer for the iPhone notch/home-indicator.
- Hamburger button (`#hamburger-btn`, CSS-hidden on desktop) wired to `openDrawer()`/`closeDrawer()`/
  `toggleDrawer()`; drawer auto-closes on navigation via one added line in the existing `showScreen()`
  chokepoint (`if (isMobileMode()) closeDrawer();`), which covers every nav path (sidebar clicks, "View
  All ›" links, Quick Commands) without touching each call-site individually.
- Bumped `_BUILD_ID` in `main.py` (`f4b1e2a-v45` → `v46`) so Scott's already-installed PWA's service
  worker cache-busts and fetches this new shell instead of serving the old cached one indefinitely.
- Desktop (≥881px) is untouched — every change is gated behind the `880px` media query / `body.is-mobile`,
  confirmed by re-grepping `STAGE_W`/`STAGE_H`/`innerWidth`/`innerHeight` to verify they're still only
  referenced inside the now-mobile-gated `fitStage()`, and by a CSS brace-balance + `node --check` pass on
  the extracted inline `<script>` block (118KB, no syntax errors).

---

## 2026-06-23 — Recycle-bin safety net + mic auto-stop-on-silence + dashboard dead-code cleanup

Three changes shipped together at Scott's request.

**1. Recycle bin (`tools/trash.py` + `data/trash/`).** Scott: "I want a file that keeps anything you
delete for 30 days so in case it was accidentally removed or caused an issue we can pull whatever we need
back." Built a deletion safety net: `archive_snippet(source, content, reason)` / `archive_file(path, reason)`
write to a committed, human-readable ledger `data/trash/DELETED.md` (machine-parseable per-entry header
comment + verbatim content in an adaptive backtick fence) plus a byte-exact payload copy under
`data/trash/files/` so restores never depend on re-parsing markdown. `restore(id[, dest])` recovers a
snippet (stdout/file) or a whole file (back to its original path). `prune(days=30)` drops expired entries +
their payloads and runs automatically after every archive. **The vault is committed to git on purpose** —
this remote environment's container is ephemeral, so an uncommitted vault would vanish with the session.
Time-based expiry is driven by a one-liner added to the existing daily `_snapshot_loop()` in `main.py`
(calls `trash.prune()` every 24h) — chosen over a separate cron because that loop already runs continuously
on the live Railway server, so there's nothing extra to keep alive. A hard rule was added to CLAUDE.md
("Archive anything before deleting it") so future sessions use it. Tested: snippet round-trip is byte-exact,
a synthetic 40-day-old entry is pruned with its payload, and the adaptive fence survives content containing
triple backticks.

**2. Microphone auto-stop on silence (`frank_hud_mockup.py`).** Previously the talk-pill/orb recorded until
a *second* tap — there was zero silence detection. Added `_startSilenceMonitor()`/`_stopSilenceMonitor()`:
a Web Audio `AnalyserNode` (fftSize 512) on the persistent mic stream computes RMS in a
`requestAnimationFrame` loop; once the user has spoken (RMS > 0.025) and then stayed quiet (RMS < 0.015) for
1500ms, it stops the **recorder** — which fires the existing `onstop` → transcribe path. A 30s hard cap
prevents a noisy room recording forever. Wired in after `_voiceRecorder.start()` and torn down in `onstop`
(so manual re-tap still stops immediately). **Critically preserves the beb230b fix**: it stops only the
`MediaRecorder`, never the `_voiceStream` tracks, and reuses one `AudioContext`/analyser across recordings.
If Web Audio is unavailable it silently degrades to the old manual tap-to-stop (no regression). Bumped
`_BUILD_ID` `v46`→`v47` so the installed PWA picks up the new shell.

**3. Dead-code cleanup (`frank_hud_mockup.py`).** Removed ~1.7KB of confirmed-dead remnants of the original
voice-widget UI (replaced long ago by the QUICK COMMANDS buttons + bottom talk-pill): CSS `.wave-row`,
`.mic-circle`(+`.live`), `.vw-sub`, `.vw-tap`, `.focus-btn`(+`.on`), `@keyframes micpulse`, `.col-quick`;
and dead JS `openDrawer()` (never called) + the `#focus-toggle` handler (no such element exists). Each block
was archived to the new recycle bin *before* removal (ids 20260623-001..005), so it's all recoverable.
Verified: greps for the 9 removed symbols return zero; kept symbols (`@keyframes wave`, `.vw-title`,
`.mini-wave`, `closeDrawer`, `toggleDrawer`) still present; CSS braces balanced (267/267); `node --check`
clean. **Backend "wasted code" was investigated but NOT touched** — candidate unused endpoints
(`/api/history`, `/api/snapshot`, `/api/conversion-targets`, `/api/autofix/{tags,title}`, etc.) and tool
scripts all plausibly have external/agent/manual callers a frontend grep can't see, so they're left for
Scott to confirm before any removal. Also noted: 3 of 4 "QUICK COMMANDS" sidebar buttons ("Start New Task",
"Run Health Check", "Run Workflow") have no `onclick` and currently do nothing — wiring them is a separate
small feature, not done here.

### 2026-06-23 — Full-wiring audit of Frank (frontend + backend) per Scott's request
**Ask:** Confirm every function/button/endpoint in Frank is actually wired up and running, not just
"not dead code." Two independent Explore agents audited the frontend (`frank_hud_mockup.py`, every
onclick/addEventListener/fetch/nav screen/voice+chat wiring) and the backend (`main.py`, all 67
REST/WebSocket endpoints, all 5 background loops, all local module imports).
**Result:** Backend is fully wired — no missing imports, no broken routes, no stub endpoints standing
in for real ones, all background loops have proper error handling. Frontend had exactly one gap: the
3 dead "QUICK COMMANDS" sidebar buttons flagged (but left unfixed) in the prior cleanup session above
still had no `onclick`.
**Fix:** Wired all 3 to existing, already-proven functions instead of writing new code — "Run Health
Check" → `runWorkflow('shop_health_check', this)` (same call the Workflows screen's buttons already use;
`shop_health_check` is a registered `_EXEC_COMMANDS` key); "Run Workflow" → `showScreen('workflows')`
(navigates to the screen that lists every workflow with its own working Run button); "Start New Task" →
`showScreen('tasks')` + `.focus()` on the existing always-in-DOM `#hud-todo-input` (already wired to
`addHudTodo()`). Bumped `_BUILD_ID` `v47`→`v48`. Verified: `py_compile` clean, re-extracted `<script>`
block passes `node --check`, grep confirms all 3 onclicks present and reference real functions.
**Outcome:** Frank now has zero known broken UI wiring.

### 2026-06-24 — Phase 1 polish pass (toasts, confirm/alert cleanup, welcome overlay, mobile fixes)
**Ask:** Scott's roadmap (polish → agentic capability → distribution) called for a frontend polish pass
before Phase 2's new chat tools. All 4 items below are `frank_hud_mockup.py`-only; no backend mutation
paths or the Action Center approval gate were touched.
**1. Toast/snackbar primitive.** Added `#toast-stack` (fixed-position, sibling of `#drawer-backdrop` so
desktop stage-scaling doesn't affect its coordinates) + `showToast(message, type, ms)` with
`toast-in`/`toast-out` keyframe animations. Wired into `runWorkflow()` so the sidebar "Run Health Check"
button — previously silent after its confirm — now reports staged/started/success/failure.
**2. confirm()/alert() standardization.** Inventoried all 13 sites. Kept native `confirm()` only for:
`approveAction()` (the Action Center gate itself), `toggleListingState()` (bypasses the gate, mutates the
live storefront directly), and the Instagram/Facebook post actions (irreversible external publishes) —
4 sites total, matching the plan's invariant. `runWorkflow(id, btn, requiresApproval)` now only confirms
when `!requiresApproval` (threaded from `w.requires_approval` in `renderWorkflows()`; sidebar button passes
`false` since health-check is read-only). The remaining 8 sites (including `batchStageTags()`, which only
ever stages actions for later Action Center approval and so doesn't qualify under the keep-list) now use
`showToast()`. Final `alert()` count: 0.
**3. First-run welcome overlay.** `#welcome-overlay` + `.welcome-card` summarizing the 4 nav groupings
(Frank/Knowledge/Tools/Shop) plus a one-line approval-gate reminder. Shows once via the same
`localStorage` try/catch pattern already used for `chatSession` (degrades to showing every time if
localStorage is unavailable) — dismiss button sets `frankWelcomeSeen`.
**4. Mobile fixes.** Inside the existing `@media (max-width:880px)` block: `.act-btn{font-size:11px;
padding:7px 4px}` (prevents Action Center Approve/Fix/Reject label clipping) and
`.studio-grid>div:last-child{flex:1 1 100%;min-width:0}` (Studio's fixed 300px video-list column goes
full-width on phone instead of staying cramped).
**Verified:** `py_compile` clean on both files; `<script>` block re-extracted via `ast.literal_eval()` on
the `_FRANK_HUD_MOCKUP` string (required — naive regex extraction preserves un-decoded Python escapes and
gives false-positive `node --check` failures) and passes `node --check`; grep confirms exactly one
`#toast-stack`/`showToast` definition, one `#welcome-overlay`, zero `alert(`, and `runWorkflow`'s signature
consistent at both call sites. Bumped `_BUILD_ID` `v48`→`v49`.
**Not verified:** no browser is available in this environment — the mobile CSS changes are unverified
visually; flagging rather than claiming a check that didn't happen.

### 2026-06-24 — Phase 2 agentic capability expansion (chat ↔ REST bridge, 7 new tools)
**Ask:** Scott's roadmap's second phase — close the gap between "Frank has a tool-use loop" and "Frank
can do everything the dashboard's buttons can do." Every new mutating tool stages through the existing
`db.enqueue_action()` → Action Center → approve → executor pipeline; the approval gate itself was never
touched. All changes in `tools/api_server/main.py`.
**M1 — autofix/batch-tag/listing-state bridged into chat.** `autofix_listing_tags`/`autofix_listing_title`
wrap the existing `_autofix_tags_core()`/`_autofix_title_core()` verbatim — pure exposure, no new staging
logic. `stage_batch_tag_update` is new orchestration: hard-capped at 10 listing_ids (rejects above, never
silently truncates, per CLAUDE.md's existing bulk-edit rule), stages each listing's tag update as its own
separate Action Center row so Scott approves/rejects per-listing, never all-or-nothing. `toggle_listing_state`
got a **second, chat-only path** — the dashboard's `POST /api/listings/{id}/state` stays exactly as-is
(still gated only by its own `confirm()`), but chat has no UI confirm dialog, so its tool always stages via
a new `toggle_listing_state` action type with its own `_validate_staged_action` branch and a new
`_execute_staged_action` dispatch branch.
**M2 — read-only conversion diagnostics exposed to chat.** Extracted `GET /api/conversion-targets` and
`POST /api/diagnose/{listing_id}`'s bodies into standalone `_get_conversion_targets_core()` /
`_diagnose_listing_core(listing_id)`; the REST routes became thin cache-wrapped callers, and two new
read-only `AGENT_TOOLS` (`get_conversion_targets`, `diagnose_listing_conversion`) call the same core
functions directly (bypassing the HTTP-layer cache, as expected). No staging — pure reads. Fixed a latent
bug surfaced during extraction: the diagnose core function referenced an undefined `cache_key` left over
from before the extraction; removed it from the core function and gave the route its own local `cache_key`.
**M3 — `register_command` self-extension tool.** Lets Claude wire up an *existing* script under `tools/`
as a new named command — a new capability, not a one-time mutation, so it gets the same staging mechanism
plus extra guardrails: the tool's input schema has no `requires_approval` field at all, and the executor
(`_execute_register_command_staged_action`) hardcodes `requires_approval: True` on every registration
regardless of what's proposed — Claude can never register a command that skips approval. Validation (in
`_validate_staged_action`) rejects: `script_path` outside `tools/` or containing `..`, a `script_path` that
doesn't exist on disk yet (Claude can wire up an existing script, not write-and-register in one call), a
`command_name` that collides with an existing `_EXEC_COMMANDS` entry, and a non-positive `timeout`. New
sidecar `data/registered_commands.json` (starts as `{}`, git-tracked) persists approved registrations
across restarts — `_load_registered_commands()` merges it into the in-memory `_EXEC_COMMANDS` dict at
import time, forcibly re-stamping `requires_approval: True` on every loaded entry as a second hardcoding
layer. `approve_action`'s three-way dispatch (`is_local`/`is_script`/else) became four-way with a new
`is_register_command` branch.
**Verified:** `py_compile` clean. Live-import simulation (`import main as m` from `tools/api_server/`,
calling `_execute_agent_tool` via `asyncio.to_thread`) exercised every new tool: `get_conversion_targets`
completed a real successful Etsy API call; `diagnose_listing_conversion` correctly returned a clean
`{"error": ...}` (not a crash) when `ANTHROPIC_API_KEY` is unset; `register_command` correctly rejected a
`script_path` outside `tools/`, a `script_path` containing `..`, a nonexistent `script_path`, and a
duplicate `command_name` against a real existing `_EXEC_COMMANDS` key (`shop_health_check`); a valid
registration staged successfully, and running the approved action through
`_execute_register_command_staged_action` correctly wrote `requires_approval: True` into both the live
`_EXEC_COMMANDS` dict and `data/registered_commands.json` on disk, and a fresh `_load_registered_commands()`
call reloaded it correctly. Test action and sidecar entry were cleaned up (action rejected, sidecar reset
to `{}`) after verification — no test artifacts left in the live system. Bumped `_BUILD_ID` `v49`→`v50`.
**M4 (revisiting the approval gate itself) stays explicitly deferred** — not part of this pass, per Scott's
standing instruction that approval remains mandatory for every mutating action.

### 2026-06-24 — Frank Reliability & CEO-Knowledge Upgrade (Phases 0–3, full initiative)
**Ask:** Scott's goal — Frank should hit "98% functionality without having to keep using Claude Code,"
meaning 98% of Frank's day-to-day operation shouldn't require Scott invoking Claude Code to fix something
broken. Four sub-goals: never assume (every claim traces to a real answer), agent loops converge correctly
the first time, Frank diagnoses/fixes his own problems where safe, and Frank reasons with CEO-grade
judgment. **Standing constraint preserved everywhere in this pass:** every mutating action still requires
Action Center approval — "self-healing" means better diagnosis/retry/escalation, never auto-bypassing
approval. Tier-1 auto-heal stays Etsy-free. `ceo_agent.py`'s `tool_approve_and_publish`/`tool_build_agent`
were studied for patterns only, never ported (they bypass the approval gate by design).

**Phase 0 — Foundations.** New `tools/api_server/resilience.py`: `retry_with_backoff()` (exponential
backoff + full jitter, category-aware `retryable` predicate) and `CircuitBreaker` (per-dependency
open/half-open/closed state, persisted via new `circuit_breaker_state` table in `db.py`). New structured
tool-error taxonomy (`ToolError`/`TransientToolError`/`ValidationToolError`/`NotFoundToolError`/
`TerminalToolError`) replaced the blanket `except Exception` closing `_execute_agent_tool` — tool errors
now return `{"error", "category", "retryable"}` so the model knows whether a retry is worth attempting.

**Phase 1 — Close the knowledge-loading gap.** `_summarize_and_rotate_kb_file()` rotates `ops_runbook.md`/
`ceo_learnings.md` once they exceed ~20KB (Haiku-tier summarization of everything older than a recent tail)
so the existing hard truncation in `_ops_runbook_block`/`_ceo_learnings_block` becomes a safety net instead
of silent data loss. New `read_knowledge_base_doc` agent tool (thin wrapper on the existing
`_resolve_kb_doc`/`_kb_docs`/`_kb_search`) gives Frank on-demand retrieval across all of
`data/knowledge_base/`, including `CLAUDE.md` itself (special-cased in `_resolve_kb_doc`). Deleted the
hardcoded product/price list from `_CEO_SYSTEM` — Frank now always calls `list_listings(state='active')`
for current catalog/pricing instead of reciting a string that drifts from reality. New
`ceo_operating_playbook.md` (Bezos one-way/two-way-door framework, pre-mortems, kill criteria, SKU-renewal
ROI rule, financial cadence, etc.) — on-demand retrieval only, never baked into every prompt. New "WHEN YOU
DON'T KNOW SOMETHING" protocol in `_CEO_SYSTEM`: tools → ops_runbook → ceo_learnings → knowledge base → web
search → ask Scott (pricing/legal/tax/live-listing topics) or give a clearly-caveated estimate (everything
else) — never invent a plausible-sounding answer silently.

**Phase 2 — Consistent retry/backoff everywhere.** All 5 background loops (`_snapshot_loop`,
`_warm_suggestions`, `_token_sync_loop`, `_quality_audit_loop`, `_health_check_loop`) migrated onto a
shared `_run_loop_iteration()` built on Phase 0's primitives — jittered exponential backoff replaces fixed
sleeps, each loop trips its own circuit breaker on repeated failure. The one-off Etsy 403 retry became a
`retry_with_backoff()` call. `_execute_staged_action`'s Etsy calls (`update_listing`/`upload_listing_image`/
`upload_listing_video`) now retry on 429/500/502/503 — only on an *already-approved* mutation, never a new
one. New `"executing"` action status (alongside `pending`/`executed`/`failed`/`rejected`) set before
`_execute_staged_action` runs, so a crash mid-execution can't leave an action silently re-approvable for a
duplicate publish/upload.

**Phase 3 — Self-diagnosis, safe remediation, CEO-grade reasoning.** Three-tier escalation for the health/
quality loops: Tier 1 auto-heals cache invalidation, reaping crashed processes, transient Anthropic-API
retries — never touches Etsy. Tier 2 alerts with a looked-up remediation from `_KNOWN_FAILURE_REMEDIATIONS`.
Tier 3 writes a blameless-postmortem-style report (`_write_escalation_report`) into `ops_runbook.md` for
novel failures — symptoms, what was tried, root-cause hypothesis labeled as a hypothesis. The KB-rotation
pass now also promotes a failure category appearing 3+ times into a `## Known Recurring Issues` section at
the top of `ops_runbook.md`. New "TOOL-RECEIPT DISCIPLINE" rule in `_CEO_SYSTEM`: every factual claim about
live shop state must trace to an actual tool-call result from the current conversation, never a restated
number from several turns back. `_validate_staged_action` now re-fetches a listing's live state at
*approval* time (not staging time) for Etsy-facing staged actions and refuses if it changed since staging.
Ported `QualityGate.check_image_dimensions`/`check_no_pale_background` from `business_pipeline.py` into
`_validate_staged_action`'s `listing_photo` branch using PIL directly — pale/washed-out background is a
hard block, wrong dimensions is a warning (legitimate source sizes vary before pipeline resize).
New read-only `find_business_gaps` agent tool — advisory diagnostics (active-listing count vs. goal,
quality-audit trend, under-used KB docs); never auto-builds agents or auto-publishes; `_CEO_SYSTEM` points
to it for broad "how are we doing" questions instead of Frank re-deriving the same picture from five
separate tool calls. New `context_compactor` agent (flips the `/api/agents/status` placeholder from
`not_built` to real, data-driven status): new `chat_summaries` table (`db.py`) holds one running summary
per session; `_maybe_compact_chat_history()` folds everything older than the live replay tail into a Haiku
summary once a session's tail exceeds 60 messages (keeping the most recent 30 untouched), walking the cut
point backward to land immediately after a complete assistant turn so role-alternation is never violated
on replay. `/ws/chat`'s history load now splices a session's summary in ahead of its live tail instead of
relying on `load_chat_history`'s hard cutoff, which silently dropped anything past its `limit`.
**check_zip_size from `business_pipeline.py` was explicitly NOT ported** — no staged-action type exists for
digital-file/ZIP uploads (those go through standalone scripts directly via `EtsyAPIClient.upload_listing_file()`,
never through Action Center), so the gate would be dead code; noted here so it isn't mistaken for an
oversight later.
**Verified:** `py_compile` clean across `main.py`/`db.py`/`resilience.py`/`ceo_agent.py`. Phase 0 exercised
directly in a REPL: `retry_with_backoff` showed jittered delays and succeeded after forced transient
failures; `CircuitBreaker` tripped after the configured failure count and half-opened after cooldown.
`context_compactor` exercised end-to-end against a throwaway SQLite DB with the real Anthropic client
mocked: seeded 80 messages (40 pairs) into a session, confirmed compaction folded 50 into a summary and
left 30 in the tail, and confirmed the kept tail starts on a `user` role (required for valid replay).
Earlier segments verified Phase 1 (KB-doc retrieval and `list_listings` fire correctly instead of guessing)
and Phase 2 (forced Etsy 5xx retries with the `executing` status guard holding) directly. Bumped `_BUILD_ID`
`v50`→`v51`.
**Not touched, by design:** the Action Center approval gate itself, and the prior "Frank Roadmap" plan's
Phase 3 (distribution/white-label readiness) — both remain exactly as they were before this initiative.

## 2026-06-24 — Frank Voice: fully offline by default (local WASM), OpenAI demoted to dormant opt-in

**Request:** Scott wanted Frank's voice (talk-to-Frank mic input + spoken replies) to work with zero
internet connection, without paying for OpenAI Whisper/TTS on every use, and without a hidden dependency
on any third-party CDN — "a complete package in frank."

**Root finding before building:** browser-native `SpeechRecognition` is NOT offline on any current
desktop/mobile browser — Chrome streams the recorded audio to Google's servers to transcribe it. It was
demoted from "the offline feature" to a last-resort fallback only.

**What shipped:** `Xenova/whisper-tiny.en` via Transformers.js (speech-in) and Piper-web (speech-out) now
run as quantized ONNX/WASM models entirely client-side, replacing OpenAI as the default voice engine.
Self-hosted the full WASM runtime (transformers.min.js, onnxruntime-web's wasm bundle + its `.mjs`/`.wasm`
glue, piper-tts-web's JS chunks, and the raw Piper phonemizer `.wasm`/`.data` binaries) under
`tools/api_server/static/vendor/` — ~32MB committed to the repo, explicitly approved by Scott over a
CDN-dependent alternative, served same-origin via the existing `/static` mount. Model *weights* (the
Whisper/Piper voice itself) are intentionally NOT vendored — they download once from Hugging Face via the
libraries' own fetch+cache logic (browser Cache API / OPFS) and persist client-side; no server-side
storage or Railway Volume implication.

Added a `<script type="importmap">` in `frank_hud_mockup.py`'s `<head>` mapping the bare specifier
`"onnxruntime-web"` to the self-hosted bundle, since Piper-web loads it via a bare dynamic `import()` —
without the import map this would have silently resolved to a CDN default. Both Transformers.js and
Piper-web are explicitly pointed at the same single self-hosted onnxruntime-web copy
(`env.backends.onnx.wasm.wasmPaths` / `TtsSession.create({wasmPaths})`) to avoid loading two different
onnxruntime-web versions in the same page. Added `'wasm-unsafe-eval'` to the CSP `script-src` header in
`main.py` — `WebAssembly.compile()`/`instantiate()` is blocked without it even though plain script loading
and `fetch()` already worked under `script-src 'self'`.

`speakText()`/`transcribeAndSend()` now branch on a new `frankPremiumVoice` localStorage flag (default
OFF, toggle checkbox added next to the talk pill) — OFF routes through the new local WASM engines, ON
routes through the existing `/api/voice/transcribe` and `/api/voice/speak` OpenAI endpoints exactly as
before. Both paths still fall through to the pre-existing browser `SpeechRecognition`/`speechSynthesis`
fallback on failure. The OpenAI endpoints themselves were not modified at all. Bumped `_BUILD_ID`
`v51`→`v52`.

**Verified in this environment:** `py_compile` clean on both files; the embedded classic `<script>` block
(after Python's own string-literal parsing resolves all escapes) passes `node --check`; the import map JSON
parses and resolves to the correct vendor path; all 9 vendor files referenced by the new JS exist on disk
at the exact paths used (`du -sh` confirms 32MB total) and are not gitignored; the `/static` mount already
serves arbitrary subpaths so no server code change was needed beyond the CSP/`_BUILD_ID` edits.

**Not verified — and cannot be, in this sandboxed, display-less environment:** an actual browser load of
`/frank`, the real model-weight download from Hugging Face, end-to-end transcription/speech with the
network disabled, the Premium-voice toggle's live behavior, localStorage persistence across reloads, and
iOS Safari/PWA behavior. Scott should manually run through the plan's verification checklist (in
`/root/.claude/plans/atomic-dancing-shamir.md`) once deployed before treating this as fully shipped. Expect
roughly 10–30 seconds of transcription latency for a short utterance on WASM — the honest tradeoff for
genuine offline operation, not a bug.

## 2026-06-24 — Dependency Health panel, working alert bell, real Settings screen

**Request:** Scott looked at the mobile Command Center and asked (1) whether the panels were backed by
real data, and (2) why the notification bell and gear icon did nothing. Investigation found Mission
Timeline / Memory Insights / Shop Performance were all genuinely wired but showing legitimate early-stage
empty states — no action needed. System Monitor (CPU/RAM/DISK gauges) was the one fake panel: hardcoded
`conic-gradient` percentages baked into inline CSS, zero JS, zero backend. The bell (frozen badge "3") and
gear icon were both dead decoration — no click handler, no backend, and for the gear, no target screen at
all.

**What shipped (`tools/api_server/main.py` + `tools/api_server/frank_hud_mockup.py`):**
1. **System Monitor → Dependency Health.** New `GET /api/system/dependencies` loops the 3 tracked circuit
   breakers (`etsy_api`, `anthropic_api`, `relay`) through `db.get_circuit_breaker_state()`; a dependency
   with no DB row yet (never tripped) reports `state:"closed", consecutive_failures:0` — the same default
   `CircuitBreaker._load()` uses, not an error. The fake gauge markup and its orphaned `.gauge`/`.gauge-row`/
   `.ring` CSS were archived via `tools/trash.py` (ids `20260624-007`, `20260624-008`) before deletion, then
   replaced with a 3-pill row (`loadDependencyHealth()`, green/red/amber dot per state) on the existing 30s
   `loadAll()` cadence.
2. **Alert bell → real alerts.** New `GET /api/alerts` aggregates 3 real conditions server-side into one
   list + count, so the badge and dropdown can never disagree: any circuit breaker in `open` state
   (critical), the Etsy refresh-token age vs. the 90-day window via `db.get_etsy_tokens()['updated_at']`
   (warning ≥75 days, critical ≥90), and any `db.list_agent_heartbeats()` row with `status=="error"`
   (warning). Frontend: badge hides when count is 0, dropdown opens on click and closes on outside-click
   (`loadAlerts()`, `toggleAlertDropdown()`, `_renderAlerts()`).
3. **Real Settings screen.** New sidebar nav-item (`data-screen="settings"`) and the previously-dead gear
   icon (`onclick="showScreen('settings')"`) both land on a new `#screen-settings` panel — no extra JS
   needed beyond what already existed, since `showScreen()`/the nav-item click binder are fully generic by
   id. Three sections: Voice (a second Premium-voice checkbox sharing the `.premium-voice-cb` class so it
   stays in sync with the bottombar toggle via the existing `_isPremiumVoice()`/`_setPremiumVoice()`
   helpers, plus a plain-language explanation of what the toggle actually does), Connections (a condensed
   summary card sourced from `/api/credentials/status` + `/api/etsy-tokens`, with jump links to the full
   Connections/Security screens rather than a duplicate live panel), About (the `v1.0.0 · MOCKUP` string).

Both new endpoints require the existing `_auth` dependency like every other route. Bumped `_BUILD_ID`
`v53`→`v54`.

**Verified in this environment:** `py_compile` clean on both files; `<div>` tag counts balance globally
(622/622) and within each newly-edited region individually; both new endpoints confirmed using
`Depends(_auth)`; the System Monitor removal was archived to `data/trash/DELETED.md` before deletion per
Scott's standing recycle-bin rule.

**Not verified — cannot be, in this sandboxed, display-less environment:** an actual browser load of
`/frank` confirming the 3 pills render green, a live circuit-breaker-open test turning a pill red and
surfacing in the alert dropdown, the bell's open/close-on-outside-click behavior, and the Settings↔bottombar
voice toggle sync. Scott should run the plan's verification checklist
(`/root/.claude/plans/atomic-dancing-shamir.md`) once deployed.

### 2026-06-24 — Frank follow-up audit: 3 more dead elements (search, briefing button, grid icon)
**Symptom:** Scott asked again whether anything on Frank is still not wired up after the
Dependency Health/Alert Bell/Settings fix above. A fresh 3-agent audit of
`frank_hud_mockup.py` found 3 elements with zero JS handler of any kind: the topbar global
search input, the bottom-bar "Executive Briefing" button, and a topbar grid icon (▦) with no
discoverable original intent anywhere in code or git history.
**Root cause:** All three were left unwired when originally added — no listener, no backend
route, nothing.
**Fix:** Search input now has `id="global-search"` + an Enter-key handler calling
`runGlobalSearch()`, which does a client-side substring match (listings → tasks → tools → KB
docs, first match wins) over data already loaded by existing loaders (`_listings`,
`cacheGet('tasks')`, `cacheGet('tools')`, `_kbDocs`) and navigates to the matching
screen/item, or toasts "No matches" if nothing hits. The Executive Briefing button now opens
a `#brief-panel` dropdown (same `.alert-dropdown` pattern as the bell, anchored upward via
`bottom:42px`) whose `renderExecutiveBriefing()` reads already-cached `shopPerf`,
`_actionsSummary`/`_pendingActions`, and `alerts` data — zero new fetches, zero new backend
endpoints. The grid icon was archived via `tools/trash.py` (id `20260624-009`) then deleted —
no replacement, since no intent for it was ever found. Bumped `_BUILD_ID` `v54`→`v55`.
**Verified in this environment:** `py_compile` clean on both files; `<div>` balance checked
manually around both new markup regions. **Not verified — cannot be, in this sandboxed,
display-less environment:** live search navigation per entity type, the briefing panel
actually opening/closing and showing correct data, the bell and briefing dropdowns not
fighting each other, the grid icon's visual absence, and zero console errors. Scott should
run the plan's verification checklist (`/root/.claude/plans/atomic-dancing-shamir.md`) once
deployed.

### 2026-06-25 — Frank/Hub wiring audit #2: `/api/history` was dead code, removed
**Symptom:** Scott asked for another wiring audit (screen nav + backend endpoint wiring + a
re-sweep for orphaned handlers). Direct `Grep`/`Read` cross-reference of every `@app.get/post/
put/delete` route in `main.py` against every fetch call in `frank_hud_mockup.py` found 13
routes with no caller in Frank; checking `_WEB_UI` (the Hub, root `/` route, `main.py` lines
~2495-4198) and every script under `tools/` resolved 11 of the 13 — they're called from the
Hub or from standalone automation scripts (`tools/stage_p3d_photo_approvals.py`,
`tools/ci_refresh_etsy_secrets.py`, `tools/sync_files_to_hub.py`), not from Frank's UI.
**Root cause / finding:** `GET /api/history` had zero callers anywhere — not in `_WEB_UI`, not
in `frank_hud_mockup.py`, not in any `tools/`, `mobile_app/`, `town_app/`, `agents/`, or
`commands/` file. It's superseded by `GET /api/analytics` (which `_WEB_UI` does call and which
returns a superset of the same data — trend arrays, deltas, top-10 listings, snapshot_count).
Reads as a route that was built then replaced without being deleted. Separately, `POST
/api/snapshot` also has zero callers, but its own docstring says it's a manual/on-demand
testing trigger — production snapshotting happens via the internal `_snapshot_loop()`
background task, not this route. Scott reviewed both findings and decided: delete
`/api/history`, leave `/api/snapshot` as-is.
**Fix:** Archived the exact `/api/history` route block via `tools/trash.py`'s
`archive_snippet()` (id `20260625-001`, reason: dead endpoint, superseded by `/api/analytics`)
before deleting it from `main.py`. Bumped `_BUILD_ID` `v55`→`v56`.
**Verified in this environment:** `python -m py_compile` clean on `main.py` and
`frank_hud_mockup.py` both before and after the edit. Screen navigation (19 nav items ↔ 19
screen divs ↔ 15 `showScreen()` call sites) and the previously-fixed search/briefing/grid-icon
work were re-checked and found clean — no new dead UI elements found this pass. Full citation
table in `/root/.claude/plans/atomic-dancing-shamir.md`.
**Not verified — cannot be, in this sandboxed, display-less environment:** live behavior of
anything above; this was a static-analysis audit only.


## 2026-06-25 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.


## 2026-06-25 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.


## 2026-06-25 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.


## 2026-06-25 — Automated quality audit — 164 listing(s) failing
Daily listing_integrity_check found 164 FAIL / 2 WARN out of 172 listings audited. Details:
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

  [4509184968] DP1029 — Digital Fitness Planner 2026 Undated, GoodN


## 2026-06-25 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.

## 2026-06-25 — Frank HUD: live status pill, color theme selector, My Account — shipped + live-verified

Three Settings features added to `frank_hud_mockup.py`, each live-tested with a headless
Playwright script against a running `main.py` instance (not just static review):

1. **Live status pill** (header) — replaced the hardcoded "SYSTEM STATUS ● OPTIMAL" text
   with a pill driven by the already-polled `/api/agents/status` + `/api/system/dependencies`
   responses: red ERROR if any agent/dependency reports `error`/`open`, amber DEGRADED if
   `running_count < total_count` or any dependency is `half_open`, else green OPTIMAL.
   Verified showing ERROR correctly in this sandbox because `ANTHROPIC_API_KEY` is blank
   here (see the recurring health-check entries above) — confirmed this is the pill
   reflecting a real condition, not a wiring bug.
2. **Color theme selector** (Settings > Appearance) — 4 swatches (Cyan/Gold/Emerald/Rose)
   toggle a `theme-*` class on `<html>`, persisted via `localStorage['frankTheme']`
   (per-device display preference, not synced to the backend by design). Verified all 4
   swatches produce a real visible repaint of sidebar/header/button accents via screenshot,
   not just a class-name change.
3. **My Account** (Settings) — new `user_profile` DB table + `GET`/`POST /api/account`,
   persists name/email/phone/timezone server-side. Verified end-to-end: saved via the UI,
   confirmed `POST /api/account` -> `200 OK` in the server log, reloaded the page, and the
   4 fields repopulated from the backend (not stale DOM/localStorage).

**Two real JS bugs found and fixed during build, both only caught by live
console/pageerror-instrumented browser testing — static review missed both:**
- Theme swatch `onclick` attribute was built with single-backslash escaping inside a JS
  string that itself needed the backslash escaped, producing broken HTML; fixed to use a
  properly double-escaped quote.
- The new theme array was originally named `const _THEMES`, colliding with a pre-existing,
  unrelated `const _THEMES` (Products/Brand Kit color palettes) in the same `<script>`
  block ~1700 lines away — `SyntaxError: Identifier '_THEMES' has already been declared`
  silently broke the entire script block, not just the new code. Fixed by renaming the new
  array to `_UI_THEMES`.

**Lesson:** both bugs were invisible to `py_compile`/code review and only surfaced via
`page.on("pageerror")` during live testing — reinforces always live-verifying JS changes
in this file, not just compiling the Python that emits it.


## 2026-06-25 — Automated quality audit — 163 listing(s) failing
Daily listing_integrity_check found 163 FAIL / 2 WARN out of 172 listings audited. Details:
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

  [4509193231] DP1058 — Sage Lavender Botanical Print, Dusty Rose W

## 2026-06-25 — Circuit breakers wired for real (were defined but never instantiated)

**Symptom:** `tools/api_server/resilience.py` has a complete DB-backed `CircuitBreaker` class, but
nothing in `main.py` ever instantiated or called it. `/api/system/dependencies` (the endpoint the
Dependency Health pills and status pill read) only ever read the `circuit_breaker_state` table —
nothing ever wrote a non-default row, so `etsy_api`, `anthropic_api`, and `relay` always reported
`closed`/healthy, even during a real outage. Found during a full-disclosure audit Scott requested.

**Root cause:** the breaker class existed in isolation; no caller wired it into a real call path.

**Fix:**
1. `tools/etsy_api.py` — added an optional, duck-typed `_circuit_breaker_hook` (default `None`) +
   `set_circuit_breaker_hook()`. Split `_request()` into a thin gate (checks `allow_request()`,
   records success/failure) wrapping the renamed `_request_impl()` (unchanged retry/refresh logic).
   Only network errors (`status==0`) and 403/429/500/502/503 trip the breaker — a clean 400/404
   means Etsy responded correctly and our request was wrong, not a dependency-health signal. The
   hook stays `None` for standalone scripts that import `etsy_api.py` outside the FastAPI server
   (verified: `set_circuit_breaker_hook` never called → zero behavior change for them). `main.py`'s
   `_startup()` now calls `etsy_api.set_circuit_breaker_hook(CircuitBreaker("etsy_api", db_module=db))`.
2. `anthropic_api` has no single chokepoint (7 call sites across `main.py`), so added a shared
   `_anthropic_breaker` + `_anthropic_create(client, **kwargs)` helper; trips only on
   `APIConnectionError`/`RateLimitError`/`InternalServerError` (genuine infra failure, not a bad
   request/key). Migrated all 6 synchronous `messages.create()` call sites to it. The 7th site
   (`/ws/chat`'s streaming `messages.stream()` call in `_run_agent_turn`) doesn't fit that helper's
   shape — it's a context manager iterated chunk-by-chunk in a worker thread — so it's gated inline
   on the same shared breaker instead (`allow_request()` before the `with` block, `record_failure()`/
   `record_success()` around it). This was the highest-volume real Anthropic consumer (every chat
   turn), so leaving it unwired would have defeated most of the point of the fix.
3. `relay` is a websocket connection, not a retry/backoff dependency, so no breaker was added for it
   — `circuit_breaker_state` was simply the wrong data source. Added `_relay_dependency_status()`,
   reusing the same `_relay_ws` + `db.get_relay_state()` signal `_agents_status_snapshot()` already
   read correctly, mapped into the dependency-pill vocabulary (`closed` when connected and not
   killed; `open` when the kill switch is engaged or the relay is disconnected — offline is a real
   outage, not a healthy default). Both `/api/system/dependencies` and `/api/alerts` now special-case
   `relay` through this helper instead of querying `circuit_breaker_state` for it.

**Verified:** `py_compile` clean on both files; a standalone import of `etsy_api.py` with no hook set
behaves identically to before; a simulated 5x Etsy 503 against a fake DB module confirmed the breaker
opens after 3 consecutive failures and correctly rejects further calls until cooldown; a simulated 5x
clean 404 confirmed it never trips the breaker; a simulated success after prior failures confirmed it
resets to `closed`/0. Did not yet live-test against the real Etsy/Anthropic APIs or a real relay
disconnect (out of scope for the local container — no live relay/Railway process here).

**Scope note:** two lower-severity findings from the same audit were explicitly deferred, not
forgotten: `context_compactor`'s heartbeat is still hardcoded `"ok"` regardless of real compaction
failures, and `tools/trash.py` remains a manual-only safety net (no autonomous code path deletes
files today, so this is a judgment call, not a live bug). Scott chose to scope this cycle to the
circuit breakers only.

## 2026-06-25 — Heartbeat honesty, delete safety net, silent-failure logging (7/10 → 9/10 cycle)

Follow-up to the circuit-breaker cycle above — closes the two items deferred there, plus one more
gap from the same 3-agent audit (silently-swallowed exceptions). Three pure honesty/observability
fixes, zero behavior change to anything Scott or a buyer would notice.

**Fix 1 — `context_compactor` heartbeat now reports real success/failure.**
`_maybe_compact_chat_history()` now calls `db.set_agent_heartbeat("context_compactor", ...)` on both
its success path (after the existing success `print()`) and its `except Exception` path, mirroring
the pattern the 5 real background loops already use via `_run_loop_iteration()`.
`_agents_status_snapshot()`'s `context_compactor` block now reads `heartbeats.get("context_compactor")`
instead of hardcoding `"status": "ok"` — falls back to the existing friendly cold-start message only
when no heartbeat row exists yet (so today's UI is unchanged until a real compaction run happens).

**Fix 2 — `tools/trash.py` wired into the 2 real DB-delete paths.**
`delete_allowed_folder` and `remove_todo` (both in `main.py`) now fetch the row via the existing
`list_allowed_folders()`/`list_todos()` functions and call `archive_snippet()` (JSON-serialized row)
before deleting, labeled `db:allowed_folders`/`db:todos`. Fetch-then-delete ordering means the 404
path is unaffected — if the row is already gone, the archive call is skipped and the existing 404
falls through unchanged. This was the last gap in CLAUDE.md's "nothing we delete should be
unrecoverable" rule — it was previously a manual convention with no autonomous backend enforcement.

**Fix 3 — logged the 6 silently-swallowed exceptions found in the same audit** (all confirmed
best-effort/non-critical paths — fix is visibility only, no control-flow change):
- 2 sites in `_execute_agent_tool()` (staging-time baseline fetch for `publish_listing` and
  `toggle_listing_state`) — added a one-line print instead of a bare `pass`.
- 3 sites in `_find_business_gaps_impl()` (circuit breaker state check, pending-actions backlog,
  KB docs inventory) — these broke the function's own established convention (two sibling blocks
  already append a `"diagnostic_error"` gap entry on failure instead of a bare log line); made all 3
  consistent with that existing pattern so Scott sees the failure on the Business Gaps screen.
- 1 site in `get_analytics()` (live `top_listings` enrichment, 15s-timeout Etsy call) — added a print
  on failure instead of silently returning an empty list with no trace.

**Verified:** `py_compile` clean; manually ran `archive_snippet()` end-to-end against the live trash
vault to confirm the wiring works (test entry removed afterward — not a real deletion, no need to
keep it). Did not re-run a live Playwright HUD pass this cycle (out of scope, deferred along with the
22+ standalone OAuth scripts that ignore `refresh_access_token()`'s return value — both deferred to a
future cycle per Scott's choice).

## 2026-06-25 — Local Relay dependency pill showing "disconnected"

**Symptom:** Scott reported the live dashboard's dependency status shows the Local Relay as
disconnected.

**Root cause:** Not a bug — this is the correct, honest status when `tools/relay/frank_relay.py`
isn't actively running. That script is intentionally a manual process meant to run on Scott's own
computer (not on Railway) — it opens a websocket to the Hub's `/ws/relay` endpoint so Frank can
execute `local_*` tool calls on Scott's real filesystem after Action Center approval. Server-side,
`_relay_ws` (`main.py` ~line 564) is a pure in-memory variable, set only while a websocket client is
actually connected (set in the `@app.websocket("/ws/relay")` handler ~line 7451, cleared to `None` on
disconnect ~line 7477-7478). `_relay_dependency_status()` (~line 6808) reports `open`
(unhealthy/"disconnected") whenever `_relay_ws is None` or the kill switch is engaged — its own detail
string for this exact case is literally `"no relay connected"` (~line 6879). There is no Railway-side
process that auto-starts the relay; if it has never been started on Scott's machine, "disconnected" is
expected, not an outage.

**Fix (or note):** No code change — confirmed via code read, not guessed. Gave Scott the 3-step setup:
`pip install websockets`; create a `.env` next to `frank_relay.py` with `FRANK_RELAY_URL` (wss://
+ Railway host + `/ws/relay`) and `APP_SECRET_TOKEN` (same token the dashboard uses); run
`python tools/relay/frank_relay.py` and leave it running (auto-reconnects every 5s, heartbeats every
20s — the dashboard pill should flip to connected within seconds of a successful connection). Awaiting
Scott's confirmation on whether this is first-time setup or a previously-working connection that
dropped, to know if further investigation (network/token) is warranted.

## 2026-06-25 — Local Relay deployed as a second, always-on Railway service

**Follow-up to the entry above.** Scott wants Frank's filesystem tools available "from anywhere,"
without depending on his laptop being open and running `frank_relay.py` manually. Confirmed via code
read that the relay script has no hard dependency on Scott's machine (no hardcoded paths, no
OS-specific calls, no machine-identity coupling — just a portable asyncio websocket client gated by
the Allowed Folders list it polls from the Hub every 30s). Scott chose: deploy it as a **new, second
Railway service** in the same project (not a separate VPS), with a **fresh empty cloud workspace**
folder (not a mirror of his laptop's files).

**Code changes this cycle:**
- Added `tools/relay/Dockerfile` (no `EXPOSE`/healthcheck — this is an outbound-only websocket
  client, never an HTTP server) and `tools/relay/requirements.txt` (`websockets`, `psutil` —
  dedicated, not the bloated root `requirements.txt`).
- Updated `frank_relay.py`'s module docstring — it previously asserted "Runs on Scott's own computer,
  not on Railway," which was no longer true; now documents both supported deployment modes.
- Fixed a pre-existing seeded placeholder: `db.ensure_default_sandbox_folder()` (`db.py`) seeds an
  Allowed Folder row the first time the table is empty, and was seeding the Windows-style
  `C:\Users\<you>\frank_sandbox` — almost certainly already seeded into the live production DB.
  Harmless on Linux (backslash is just a character there) but confusing clutter. Changed the seed
  default and the dashboard's input placeholder (`main.py`) to `/data/workspace`, the real path the
  new relay service will use.

**Manual steps required outside the repo (Railway dashboard, Scott):** add a second service
(e.g. `frank-relay`) in the existing project pointed at this repo, with service variable
`RAILWAY_DOCKERFILE_PATH=tools/relay/Dockerfile`; attach a new Volume mounted at `/data`; set env vars
`FRANK_RELAY_URL` (the **main** service's `wss://.../ws/relay` URL — not the new service's own) and
`APP_SECRET_TOKEN` (same value as the main service). After it connects, remove the old seeded
Windows-path Allowed Folder via the dashboard and add `/data/workspace` as the real one.

**Known gap, flagged not solved:** no existing path gets *binary* files (PDFs, ZIPs, images) into the
new workspace — `local_write_file` only handles text content, and the existing file-upload paths
(`/api/files/upload`, `tools/sync_files_to_hub.py`) write to the main service's own `/data/files`
volume, a different Railway volume on a different service. Text-file workflows are unaffected; this is
a separate follow-up if Scott needs binary files there.

**Open question for Scott:** whether the current Railway plan/tier supports a second service + a
second Volume — can't be verified from this environment.

### 2026-06-25 — Solved the binary-file gap: dashboard upload straight into the relay workspace
**Context:** the relay-deployment entry above flagged that there was no way to get binary files
(PDFs, ZIPs, images) into the relay's `/data/workspace` — `local_write_file` only ever handled text,
and `/api/files/upload`/`sync_files_to_hub.py` both write to the main service's own `/data/files`
volume, never to the relay's. Scott confirmed (when asked) that any new upload widget should always
push straight to the relay workspace — no destination picker, since Hub storage already has its own
batch path via `sync_files_to_hub.py`.
**Fix:**
- `tools/relay/frank_relay.py` — new `local_write_binary_file` handler (base64-decodes `content_b64`,
  writes bytes, same `_is_allowed()` realpath check as every other handler). Registered in
  `_TOOL_HANDLERS`. Bumped the relay's own `websockets.connect(max_size=...)` to 64MB — a base64-encoded
  30MB upload inflates to ~40MB inside the JSON `tool_request` envelope the relay receives.
- `tools/api_server/main.py` — new `POST /api/relay/upload?path=...` endpoint: takes the raw body
  (same convention as `/api/files/upload`), base64-encodes it, dispatches to the relay via
  `_dispatch_to_relay("local_write_binary_file", ..., timeout=90.0)`, returns 502 if the relay is
  offline. Reuses the existing `_MAX_UPLOAD_BYTES` (30MB) ceiling.
- Dashboard: new "Upload File to Relay Workspace" card on the Relay panel (file picker + destination
  path input, prefilled to `/data/workspace/<filename>`) and an `uploadToRelay()` JS function.
- `local_write_binary_file` is deliberately **not** added to `_LOCAL_STAGED_TOOLS` — it's only ever
  triggered by this direct human-initiated dashboard action, never by an LLM tool call, so it skips
  the Action Center approval gate by design (same reasoning as `addAllowedFolder()`).
**Verification:** `py_compile` clean on both files; manual confirmation still needed once the relay
service is live — upload a small PDF to `/data/workspace/test.pdf`, list-dir to confirm byte count,
restart the Railway service and re-check the file persisted on the Volume, and confirm an upload to a
path outside Allowed Folders (e.g. `/etc/passwd`) is rejected by `_is_allowed()`.

### 2026-06-26 — Two historical credential leaks found in git history; one fixed, rotation pending
**Symptom:** while building the self-host installer (setup wizard work), found two separate places
where real secrets had been committed in plain text instead of left in `.env`.
1. `SETUP.bat` (root) — an old commit (`0c85408`, "Add Windows one-click setup and launcher batch
   files") had `echo ANTHROPIC_API_KEY=...> .env` / `echo ETSY_API_KEY=...>> .env` baked into the
   script. The working tree had already been fixed in an earlier session (now just
   `copy .env.example .env`), but the old commit is still in history.
2. `CLAUDE.md` (root, this file's sibling doctrine doc) — the Credentials section hardcoded the real
   `ETSY_CLIENT_ID`/`ETSY_CLIENT_SECRET` values across 30 commits on this branch.
**Root cause:** both predate the `.env`-only convention being consistently enforced; `CLAUDE.md`'s
leak was introduced when the Credentials section was first written and never caught since it's a
doctrine file, not code, so it wasn't in the secrets-scan path.
**Forensics (compared live `.env` values against the leaked strings by boolean equality, never
printed actual secrets):** the leaked `ETSY_CLIENT_ID`/`ETSY_CLIENT_SECRET` in `CLAUDE.md` are still
the live, active credentials — a real, current exposure. The leaked `ANTHROPIC_API_KEY`/
`ETSY_API_KEY` in `SETUP.bat`'s history no longer match `.env` — those two were already rotated at
some prior point.
**Blast radius (`git merge-base --is-ancestor` + blob-content grep across commits, not diff text):**
the `SETUP.bat`-leak commit (`0c85408`) is an ancestor of every branch on the remote, including
`main` — scrubbing it would mean rewriting production's history. The `CLAUDE.md` leak's 30 commits
are confined entirely to `claude/etsy-automation-agents-WFAPU` — scrubbing only this branch is much
lower risk.
**Fix so far:** stripped the literal `ETSY_CLIENT_ID`/`ETSY_CLIENT_SECRET` values from `CLAUDE.md`'s
working tree, replaced with a pointer to `.env` (commit `07e4b3b`), pushed.
**Still open — Scott's action required, tracked as a todo:** rotate the Etsy Keystring + Shared
Secret via the Etsy Developer dashboard (the live leak), update `.env`, re-run
`python tools/etsy_oauth.py`. Anthropic/OpenAI keys already appear rotated — no action expected there.
Git-history scrub (either branch) was explicitly deferred by Scott until after rotation — not done.

---

### 2026-06-30 — Frank's speak-back was a stub; Studio video tab didn't exist

**Symptom 1:** Frank reported "Step 4 not done" when asked to speak — confusing error from a stale stub.
**Root cause:** `local_speak` tool handler at main.py:1958 returned `{"spoken": False, "note": "Step 1 stub…real TTS ships in Step 4."}` — a placeholder left from initial scaffolding. The real `/api/voice/speak` OpenAI TTS endpoint already existed and worked but was never connected.
**Fix:** Updated `_execute_agent_tool` to return `{"spoken": True, "text": text}`. Added WS dispatch in the tool loop to emit `{"type": "speak", "text": text}` before executing `local_speak` — frontend picks this up and plays audio. Added `speakText()` frontend function calling `/api/voice/speak`, a 🔇/🔊 toggle button in the chat input row, and auto-speak-on-done when voice is enabled (stored in localStorage as `frankSpeak`).

**Symptom 2:** "Create video section" had no UI despite the `/api/studio/generate` backend existing and working.
**Root cause:** Studio endpoints were built server-side (commit history) but no frontend tab was wired in. `video_generator.py` + all deps (numpy/Pillow/moviepy) were confirmed working via background test (generated 176KB MP4 in ~8s with dummy images).
**Fix:** Added 🎬 Studio hub section button in the Hub nav, `loadStudio()` JS function with listing-ID + style-select generate form, inline `<video>` preview on completion, download link, and previously-generated video list via `/api/studio/videos`. Build ID bumped to v63.

## 2026-06-30 — Daily Brief added (proactive 6AM email)

**What:** Added `tools/daily_brief.py` + `_daily_brief_loop()` background task in `main.py`.
Frank now emails a daily shop-status brief to printing3dthings@outlook.com at 6AM UTC automatically.
Manual trigger: `POST /api/brief/run` with `X-App-Token` header, or `python tools/daily_brief.py`.
Brief includes: unread message count (Star Seller risk), active/draft listing counts, orders last 7 days, recent KB incidents, and a Claude Haiku synthesis for TODAY'S FOCUS.
**Caveat:** `messaging_r` OAuth scope not granted — unread message count will show 0 until scope is added. 140 active listings confirmed live via Etsy API.

## 2026-06-30 — Added automated listing QC gate (Maker/Checker pattern)

**What:** Built `tools/listing_qc.py` and wired it into Frank as the `check_listing_quality` agent tool. Implements the one genuine gap found in the SAMS/Loop Engineering slide assessment: an automated Checker pass between content generation (Maker) and Scott's review.
**Checks:** title length (≤70 chars), exactly 13 tags each ≤20 chars with no special characters, no tag duplicating a title phrase, price suffix (.99/.97/.49), plus product-type-specific keyword and required-description-section checks for digital planners, SVG packs, and wall art (product type auto-detected from title/description, or passed explicitly).
**Output:** `passed`/`errors`/`warnings`/`reminders` — errors block (must fix before showing Scott), warnings are advisory, reminders are static human-only checks (real product photos, file validation, PDF interactivity, etc.) that the tool can't automate but Frank must still surface.
**Wiring:** Added to `AGENT_TOOLS`, dispatch branch in `_execute_agent_tool`, WS status message, and an instruction in `_CEO_SYSTEM`'s Quality standards section telling Frank to call this after drafting listing content and before presenting it to Scott. Build ID bumped to v66.

---

## 2026-06-30 — Audit remediation: fixed 2 background loop errors + updated CLAUDE.md

**Symptom:** Two background tasks showing "error" status in the dependency health panel on every boot:
1. `quality_audit` — "could not parse summary line"
2. `suggestion_warmer` — "Something went wrong talking to the AI provider"

**Root cause (quality audit):** `data/` is excluded from the Docker build context via `.dockerignore`. On Railway, `data/listing_manifest.json` does not exist. `listing_integrity_check.py` exits early with "ERROR: not found" — no summary line is printed. The summary regex fails to match, raising `RuntimeError("could not parse summary line")`.

**Root cause (suggestion warmer):** `_compute_suggestions_inner()` raises `HTTPException(502, detail="Could not gather shop data: <Etsy error>")` when Etsy data gathering fails at startup. This was passed to `_friendly_error_message()` which is designed for Anthropic errors — the HTTPException falls through to the generic fallback message, hiding the real cause.

**Fix (quality audit):** Added manifest existence check before running the subprocess in `_quality_audit_iteration()`. Returns `{"skipped": True, "reason": "..."}` instead of crashing. `_quality_audit_loop` lambdas updated to show `"warning"` status with the skip reason instead of treating it as an error.

**Fix (suggestion warmer):** Changed `on_error_detail` lambda to extract `exc.detail` from HTTPExceptions before falling back to `_friendly_error_message`. The actual cause (Etsy failure message) now surfaces in the heartbeat instead of the generic Anthropic error message.

**Additional:** Updated CLAUDE.md product catalog — corrected file sizes for DP1026-1029 (were ~15MB/14MB, actual ~7MB each), added ⚠️ warnings for missing sticker ZIPs on DP1026-1029, added note on expanded catalog through DP1034.

**Scott todos posted to Frank:** (1) Mount Railway Volume at /data; (2) Add SMTP env vars to Railway; (3) Generate sticker ZIPs for DP1026-1029.

**Build:** a3c9d1b-v67

---

## 2026-06-30 — Silent Anthropic credit drain from _warm_suggestions loop

**Symptom:** Scott's Anthropic API credits were draining rapidly with minimal visible usage. After topping up, received "out of credit" email shortly after.

**Root cause:** `_warm_suggestions` background loop in `main.py` fires every `_SUGGESTIONS_TTL - 120` seconds = every 1,680 seconds ≈ 28 minutes, 24/7. Each call invokes the full CEO diagnostic (claude-sonnet-4-6, ~2,000 output tokens). That's ~51 calls/day × ~2,000 tokens × $15/MTok output ≈ **$1.53/day = ~$45/month** in silent background costs. This compound with other background tasks (daily_brief at $0.02/day is negligible; ceo_agent.py uses Opus 4.8 only when Scott explicitly chats with Frank).

**Fix:** Changed `_SUGGESTIONS_TTL = 1800` → `14400` (30 minutes → 4 hours) in `main.py:559`. The `base_interval=_SUGGESTIONS_TTL - 120` and `_cache_get(..., ttl=_SUGGESTIONS_TTL)` both read from this constant, so one change cascades correctly. Reduces background calls from ~51/day to ~6/day — **~88% reduction in background API spend** (~$45/month → ~$5/month). Dashboard still sees a fresh report because the warmer fires proactively before expiry.

**Approved by Scott (2026-06-30).**

**Build:** a3c9d1b-v68

## 2026-07-01 — Token & cost reduction: prompt caching + Haiku title autofix + KB read cache

Three zero-quality-tradeoff optimisations applied to `tools/api_server/main.py` (v69):

1. **Prompt caching on main CEO chat** — `_CEO_SYSTEM` (~2 100 tok) and `AGENT_TOOLS` (~2 000 tok) are now passed as a list-form `system` with `cache_control: {type: ephemeral}` on the static block, and `_tools_with_cache()` tags the last tool entry. Static content is cached for 5 min; cache reads cost $0.30/MTok vs $3/MTok full price (~90% on those tokens for turns 2+).

2. **Title autofix: Sonnet → Haiku** — `_autofix_title_core` switched from `claude-sonnet-4-6` to `claude-haiku-4-5-20251001`. Output is capped at 100 tokens max (a corrected title); Haiku handles this mechanical task perfectly. 73% per-call saving.

3. **KB file read cache** — `_read_kb_cached()` + `_kb_cache` dict added. `_ops_runbook_block()` and `_ceo_learnings_block()` now re-read their `.md` files at most once every 60 s instead of on every chat turn. Stabilises the dynamic system-block content, improving prompt-cache hit rates. Any `log_learning` write appears within 60 s — no stale-data risk.

All three changes verified by `python -m py_compile`. Main chat model (Sonnet), history window, compaction TTL, suggestions TTL, and Opus-for-code-gen all untouched.

## 2026-07-01 — Display fix: desktop Frank blank + mobile safe-area glitches

**Symptoms reported by Scott:**
- Desktop Frank (`/frank`) showed only a dark orb — no dashboard, no sidebar, no header
- Phone app (React Native) had header overlapping status bar / keyboard overlapping input bar on some iPhones

**Root causes found (5 bugs):**

1. **Frank HUD blank on desktop** (`frank_hud_mockup.py`): CSS `body:not(.cc-open) .sidebar, .screen, .hdr-bar, ...{ display:none }` hides all panels until `body.cc-open` is set. That class is only set by the hamburger button click — but the hamburger was `position:absolute` and invisible on desktop (no `display:none` base rule, so technically visible but hard to notice at top-left). `syncMobileClass()` never added `cc-open` on init for desktop. Fix: `syncMobileClass()` now calls `document.body.classList.add('cc-open')` when `!isMobileMode()`. Hamburger also hidden via `display:none` base CSS; shown back in the `@media (max-width:880px)` block.

2. **Both PWA manifests had `"orientation": "portrait"`** (`main.py` lines 4605, 4661): Wrong for the landscape 1440×900 FRANK HUD and unnecessarily restrictive for the mobile PWA. Changed to `"any"` in both.

3. **Persist banner always hidden** (`main.py` line 2839): Banner was `position:static`, placed behind all `position:fixed` screens. Made it `position:fixed; top:0; z-index:300`. JS now also expands `--hdr` by the banner's offsetHeight so screens don't slide under it.

4. **ChatScreen header padding hardcoded** (`ChatScreen.js` line 361): `paddingTop: 60` ignored actual device safe area. Changed to dynamic `insets.top + 14` via `useSafeAreaInsets()`.

5. **KeyboardAvoidingView offset hardcoded** (`ChatScreen.js` line 265): `keyboardVerticalOffset={90}` wrong for tall iPhones. Changed to `insets.top + 44`.

**Files changed:** `frank_hud_mockup.py`, `main.py` (v70), `mobile_app/src/screens/ChatScreen.js`


## 2026-07-01 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.


## 2026-07-01 — Automated quality audit — 130 listing(s) failing
Daily listing_integrity_check found 130 FAIL / 13 WARN out of 172 listings audited. Details:
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


## 2026-07-01 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.


## 2026-07-01 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.

---
**2026-07-01 — Studio Video Generation: v76 fix (build-7)**
- **Symptom:** Studio tab Generate Video button returned HTTP 500 on Railway; UI showed "HTTP 500" with no detail. 48-byte MP4 stubs from older v72-era attempts visible in video list.
- **Root cause 1 (v75 fix partially wrong):** `video_generator.py` hardcoded `/usr/bin/ffmpeg` but that binary only exists on Railway (apt-installed). Local dev has only the imageio-ffmpeg bundled binary. Using `imageio_ffmpeg.get_ffmpeg_exe()` instead resolves both: locally uses bundled binary, Railway (with `ENV IMAGEIO_FFMPEG_EXE=/usr/bin/ffmpeg`) uses system binary.
- **Root cause 2 (v76 fix):** `subprocess.Popen` stdin pattern — calling `proc.stdin.close()` then `proc.communicate()` raises `ValueError: flush of closed file` because Python's communicate() calls `self.stdin.flush()` unconditionally. Fixed by writing frames in a daemon thread while main thread drains stderr, then calling `proc.wait()` (not `communicate()`).
- **Fix:** `tools/video_generator.py` — `imageio_ffmpeg.get_ffmpeg_exe()` + threading pattern. `tools/api_server/main.py` — added `/api/studio/diagnose` endpoint, threading fix in mini-encode test, bumped `_BUILD_ID` → `b4d0e2c-v76`.
- **Verified:** Full HTTP end-to-end test locally — upload 2 JPEG images → POST `/api/studio/generate` → 54.8 KB MP4 returned, file confirmed on disk. `/api/studio/diagnose` returns `mini_encode_ok: true`.


## 2026-07-01 — Automated health check failure (known cause)
5-minute health loop detected a problem: Etsy: ok — OnBrandCraftz | Anthropic key set: False

**Diagnosis:** ANTHROPIC_API_KEY is unset in this environment -- set it in the deploy environment's env vars (or .env locally) and redeploy/restart.

---
**2026-07-01 — Security audit fixes: v82 (APP_SECRET_TOKEN removed from HTML)**
- **Symptom:** `APP_SECRET_TOKEN` was embedded in page source as `const TOKEN = '...'` in both the mobile PWA (`_WEB_UI` in main.py, line ~3174) and the Frank HUD (via `__APP_TOKEN__` substitution in frank_hud_mockup.py). Any user viewing View Source could extract the admin token.
- **Additional issues:** Sessions weren't persisted (Railway restart = everyone logged out); password reset didn't invalidate existing sessions; WebSocket disconnect was silent (no user toast).
- **Fixes (all in v82):**
  - **Fix A (security):** Removed token injection from HTML. Both UIs now use `const TOKEN = ''` (placeholder). `fetchWithTimeout()` in both files strips `Authorization` headers and sends `credentials:'same-origin'` so the httpOnly session cookie is used automatically. File download URLs no longer include `?token=...`. New FastAPI dep `_auth_session_or_bearer` accepts cookie | Bearer header | `?token=` query param.
  - **Fix B (security):** Password reset (`/api/admin/users/{u}/reset-password`) now deletes all in-memory sessions and `hub_sessions` DB rows for that user.
  - **Fix C (reliability):** Sessions persisted to `hub_sessions` SQLite table (schema in db.py). `_get_session_user` falls back to DB on cache miss; warms in-memory cache on hit. Purge runs at startup + hourly.
  - **Fix D (reliability):** WebSocket `ws.onclose` now calls `showToast('Reconnecting… (N/5)', 'warn')` during retries and `showToast('Connection lost. Refresh the page.', 'error', 0)` at max retries. `showToast(ms=0)` now means persistent (no auto-dismiss).
  - **Fix E (relay pending):** Confirmed already handled — `_dispatch_to_relay` already had `finally: _relay_pending.pop(req_id, None)`. No change needed.
  - **Fix F (dead UI):** `batchStageTags()` and `mem-canvas` render code were already implemented. No change needed.
- **Files changed:** `tools/api_server/db.py`, `tools/api_server/main.py`, `tools/api_server/frank_hud_mockup.py`
- **Build:** `b4d0e2c-v82`

## 2026-07-01 — v83: Frank HUD Desktop Layout Overhaul

**Changes:**
- Fix 1 — Scrollbars: `.dep-pill-row`, `.shop-spark-row`, `.mem-row` now use `overflow-y:auto` + `min-height:0` + `justify-content:flex-start` so content scrolls instead of clipping
- Fix 2 — 3-column desktop grid: `.main` changed from `display:flex;flex-direction:column` (3 stacked rows) to `display:grid;grid-template-columns:290px 1fr 310px`. Chat panel (`col-center`) now fills the entire center column at full height. Left column: AI Core + Dependency Health + Mission Timeline. Right column: Shop Performance + Memory Insights + Active Agents + Live Feed. Old `.mrow` and row-specific column rules archived via tools/trash.py.
- Fix 3 — Light theme WCAG AA contrast: `--cyan` 3.39:1→5.88:1, `--cyan2` 2.46:1→8.57:1, `--gold` 3.69:1→5.74:1, `--muted` 5.15:1→7.69:1 (all against `--panel:#ffffff`)
- Fix 4 — Products screen: `renderProducts()` now calls `/api/products` endpoint (async) instead of `_PRODUCTS_STATIC` hardcoded array. New FastAPI endpoint reads `data/dp_listing_map.json` and checks actual PDF/ZIP files on disk for DP1026–DP1035.
- Mobile: `.col-center{order:-1}` makes chat appear first on mobile; `#chat-msgs` max-height 55vh→60vh; new column overflow rules replace old `.mrow` rules.
- `_BUILD_ID` bumped to `b4d0e2c-v83`

## 2026-07-02 — v87: Security + correctness fixes from codebase audit (9 issues)

**Triggered by:** Comprehensive codebase audit by senior engineer review agent.

**Fixes applied:**

1. **etsy_api.py:95 — 403 removed from _BREAKER_TRIP_STATUSES**
   - Root cause: 403 (auth failure / stale OAuth token) was tripping the circuit breaker, showing Etsy as DOWN when the actual problem was an expired access token. Misleading operational signal.
   - Fix: Removed 403 from the set. It now only trips on 429/500/502/503 (genuine service failures).

2. **main.py:393 — _auth() timing oracle fixed**
   - Root cause: `credentials.credentials != APP_TOKEN` used plain `!=` (timing-distinguishable). `_auth_session_or_bearer()` already used `secrets.compare_digest()`.
   - Fix: Both auth paths now use `secrets.compare_digest()`.

3. **main.py:827 — asyncio.get_event_loop() deprecated call**
   - Root cause: `asyncio.get_event_loop().create_future()` deprecated Python 3.10+, raises in 3.14.
   - Fix: Changed to `asyncio.get_running_loop().create_future()`.

4. **main.py:6112 — _APP_SECRET_TOKEN undefined variable**
   - Root cause: `/api/brief/run` endpoint referenced `_APP_SECRET_TOKEN` (undefined) instead of `APP_TOKEN`. Would raise NameError on every call.
   - Fix: Changed to `secrets.compare_digest(token, APP_TOKEN)` with empty-string guard.

5. **main.py:547 — _login_fails dict unbounded growth**
   - Root cause: IPs with all-expired failures left an empty list in the dict forever. Under bot traffic this grows without bound.
   - Fix: Pop key after filtering produces an empty list.

6. **db.py:186 — WAL PRAGMA on every connection open**
   - Root cause: `journal_mode=WAL` is a persistent file-level property (survives reconnect). Running it on every `_connect()` added two extra SQLite round-trips per query.
   - Fix: Moved to `init_db()` (runs once at startup). Removed from `_connect()`.

7. **frank_hud_mockup.py:1525 — Math.random() for session ID fallback**
   - Root cause: Browsers with `window.crypto` but not `randomUUID()` fell back to `Math.random()` which is not cryptographically secure.
   - Fix: Use `crypto.getRandomValues(new Uint8Array(8))` which IS available everywhere `crypto` exists.

8. **frank_hud_mockup.py:1924 — Math.random() for SVG gradient IDs**
   - Root cause: `_miniSpark()` generated a random ID on each call. Replaced `Math.random().toString(36)` with a monotonic counter `_miniSparkCounter`. Eliminates randomness, ensures uniqueness within the page session.

9. **frank_hud_mockup.py:2321/2353 — Duplicate /api/todos HTTP fetch**
   - Root cause: `loadMissionTimeline()` and `loadTasks()` each issued an independent fetch to `/api/todos`, doubling the call count on every dashboard load.
   - Fix: Added `_sharedTodosFetch()` with a shared in-flight promise. Both callers now share one round-trip per tick.

Also: business_config.py AGENT_NAME_SHORT default changed from derived `AGENT_NAME.replace("Fucking ", "")` to hardcoded `"Frank"` — more predictable for installer deployments.

Build ID: b4d0e2c-v87

## 2026-07-02 · v88 · Codebase Cleanup

**Motivation:** 88 releases of iterative feature work accumulated dead code, 2 silent bugs, and ~55 one-off scripts never cleaned up.

**Bugs fixed:**
- `frank_hud_mockup.py`: `#mem-canvas` page-load TypeError — element removed in v85 but JS still called `.getContext('2d')` on null, crashing ALL event listeners registered after that line (orb click and voice capture were silently broken).
- `main.py`: `studio_generate_video` except block used undefined `logger` → `NameError` masked real video errors with a misleading traceback.

**Dead code removed (all archived to data/trash/ first):**
- `_WEB_UI` old mobile PWA dashboard (~1874 lines) + `_SW_JS`, `_MANIFEST`, and their routes — superseded by `/frank` HUD.
- `_auth()` dead function + `HTTPBearer` security imports from main.py.
- `/api/studio/diagnose` Railway debug endpoint (v76 scaffolding).
- Revenue calculator triplicated in 3 places → one `_order_revenue()` helper.
- `datetime.utcnow()` → `datetime.now(timezone.utc)`.
- `/api/ping` was making unauthenticated Etsy calls — replaced with pure internal response.
- 8 dead EtsyAPIClient methods: `get_conversation`, `update_listing_inventory`, `delete_listing_file`, `sync_orders_from_etsy`, `create_review_response`, `get_shipping_profiles`, `create_shipping_profile`, `get_client()`.
- `drawMem()`, `updateMemoryWidget()`, `mc`/`mctx` dead JS + 12 dead CSS rules from `frank_hud_mockup.py`.
- Dead JS functions: `isControlCenterOpen`, `openControlCenter`.
- Removed unused `app_token` parameter from `render_frank_hud()`.
- Switched HUD template to sentinel tokens (`%%AGENT_NAME%%`, `%%AGENT_SHORT%%`, `%%OWNER%%`) replacing fragile literal-string substitution.
- 55 one-off scripts from `tools/` archived (IDs 20260702-033 → 20260702-087). Recoverable 30 days via `python tools/trash.py --restore <id>`.
- `tools/agents/ceo_agent.py` archived (superseded by HUD chat; ID 20260702-087).

**Build ID:** b4d0e2c-v88

## 2026-07-02 · v89 · Studio AI (Sora) generator fixed — was calling a nonexistent API

**Symptom:** Studio "✨ AI Scene (Sora)" style always failed. `tools/ai_video.py` was
written against a hallucinated API shape that mirrors images.generate.

**Root cause:** `ai_video.py` called `client.videos.generate(model="sora-1.0-turbo",
prompt=..., input_images=[<base64 data-urls>], duration=10, n=1, with_audio=True)` and
expected a synchronous `resp.data[0].url`. None of that exists:
- `client.videos` has no `.generate()` — the real API is an async JOB: `videos.create`
  → poll `videos.retrieve` → `videos.download_content(id, variant="video")`.
- Model `sora-1.0-turbo` is not real. Valid: `sora-2`, `sora-2-pro`.
- `input_images`/base64 data-urls/`with_audio`/`n` are not params. Sora takes ONE
  `input_reference` image that must match the output size.
- `duration=10` invalid — seconds are only "4"/"8"/"12".
- Size `1:1 → 1080x1080` invalid — Sora sizes are 720x1280 / 1280x720 / 1024x1792 /
  1792x1024 (no square).

**Fix:**
- Rewrote `generate_ai_video()` against the real Sora-2 job API (create → poll →
  download_content). Clamps duration to 4/8/12, maps aspect→valid size, center-crops
  the product photo to the exact output size for the reference image, polls with a
  wall-clock cap, and surfaces `video.error` on failure.
- `main.py` studio_generate_video: changed hardcoded `duration=10` → `8` (valid).
- `frank_hud_mockup.py`: removed the "1:1 Square" aspect option (Sora can't produce
  1:1; leaving it would deliver a portrait video when the user picked square — a
  truthfulness violation).

**Proof (real generation, authorized spend):** org IS Sora-2 enabled. Ran end-to-end
with a real product image → Sora job `video_6a46753f6bb081908ca0d98411eadfcd06dd273a4ed4440e`
→ saved a valid 1.7 MB MP4 (ftyp/moov/mdat, 720x1280, 126 frames ≈ 31.5fps, 4s) in 85s.
Decoded with imageio to confirm frames render. MP4 sent to Scott.

**Build ID:** b4d0e2c-v89

## 2026-07-02 · v90 · Loop engineering (goal-verification loops)

**Motivation:** Scott asked to "add loop engineering to any task that can benefit — compare
to the goal before saying complete." Generalized the one good verify-retry loop we had.

**Added `tools/goal_loop.py`:** `run_until_goal(generate, verify, max_attempts, on_reject)`
+ `LoopResult`. Generate → verify against the goal → feed specific failures back → retry →
honest pass/fail. Hard rule enforced in code: `passed=True` ONLY when a verify actually
returned pass=True; on exhaustion returns `passed=False` with the last issues (never
fabricates success). Distinct from resilience.py (which retries transient/network errors);
goal_loop retries QUALITY failures where nothing threw but the output is wrong.

**Wired in:**
- `listing_photo_pipeline.generate_verified_photo` refactored onto `run_until_goal` — parity
  proven with stubbed known-good/known-bad/recover-on-2 tests (output saved only on real
  pass, rejects archived per failed attempt, honest fail on exhaustion).
- `etsy_listing_tools._generate_listing_content` now runs `pre_publish_gate` at generation
  time and returns `success=false` + specific `gate_failures` when the draft breaks the 2026
  rules (title >70, <13 tags, missing "instant download", short desc, bad price ending).
  Closes the loop at the agent layer — Frank can't report content "done" while it fails the
  gate. (No in-code LLM regenerator added — that would duplicate Frank's brain; the agent is
  the generator across tool calls.)

**Verified:** goal_loop unit tests (5 cases) + photo-pipeline parity (3 cases) + listing gate
(bad blocked with feedback, clean passes). All green. Build b4d0e2c-v90.

## 2026-07-02 · v91 · LLM consolidation (centralized model tiers)

**Motivation:** Research verdict — keep Claude as the brain (leads on tool-use/policy
adherence), but the ~8 model strings were hardcoded and scattered, and "consolidate away the
second OpenAI brain" turned out to be a non-issue (OpenAI is only Whisper STT + TTS here, not
a reasoning brain).

**Changes:**
- Added model-tier constants to `business_config.py`: MODEL_PRIMARY (default
  claude-sonnet-4-6), MODEL_CHEAP (claude-haiku-4-5-20251001), MODEL_HARD (claude-opus-4-8).
  All env-overridable.
- Replaced the 7 hardcoded model strings in main.py with the constants (4 primary, 3 cheap).
- Documented that OpenAI = STT/TTS only (no reasoning-brain consolidation needed).

**Honest note on Sonnet 5:** could NOT verify claude-sonnet-5 access — no ANTHROPIC_API_KEY
in this container (it's injected only in the Railway deploy env). So I did NOT blind-swap the
live brain to an unverified model. Default stays on the proven claude-sonnet-4-6; promoting to
Sonnet 5 is now a one-env-var flip (`MODEL_PRIMARY=claude-sonnet-5`) once Scott confirms the
account has access. Defaults verified byte-identical to prior hardcoded models (zero behavior
change without an override).

**Build:** b4d0e2c-v91.

### ACTION FOR SCOTT
To upgrade Frank's brain to Sonnet 5: confirm the Anthropic account has claude-sonnet-5
access, then set env var `MODEL_PRIMARY=claude-sonnet-5` on Railway and redeploy. No code
change. Revert by unsetting it.

## 2026-07-02 · v92 · Veo 3.1 video engine prepped (Sora shutdown migration)

**Motivation:** OpenAI's Sora API shuts down 2026-09-24. Research picked Google Veo 3.1 as
the migration target. Prepped the code path now so the switch is low-risk and ready.

**Changes (tools/ai_video.py):**
- Split into engines behind `generate_ai_video(..., engine=)`: "sora" (proven, default) and
  "veo" (Google Veo 3.1). Engine resolves from arg → AI_VIDEO_ENGINE env → "sora".
- `_generate_sora` = the existing proven path, unchanged. main.py's /api/studio/generate
  contract is unchanged (still calls generate_ai_video with the same args).
- `_generate_veo` written to the documented google-genai video API (generate_videos → poll
  operation → download). Reads GEMINI_API_KEY from env (not the OpenAI key).
- Added `google-genai>=1.0.0` to api_server/requirements.txt (lazy-imported, doesn't affect
  startup).

**HONESTLY UNPROVEN:** google-genai SDK is not installed in this container and there's no
GEMINI_API_KEY, so the Veo path has NOT been run end-to-end. All guards fire cleanly (clear
errors on missing key / missing SDK / unknown engine — verified). Before flipping to Veo in
production, run one real generation on a real product file and verify the mp4 — same bar as
the Sora fix. Veo model id / config field names must be confirmed against the live SDK then.

**Build:** b4d0e2c-v92.

### ACTION FOR SCOTT (before Sept 24)
1. Get a Google Gemini API key (Veo 3.1 access), set `GEMINI_API_KEY` on Railway.
2. Set `AI_VIDEO_ENGINE=veo` (and optionally `VEO_MODEL`).
3. Have Claude run one real generation + verify the mp4 before relying on it.

## 2026-07-02 · v93 · Drop Canva (dormant) + split marketing email to Resend

**Canva:** confirmed FULLY DORMANT — no Python module imports the canva client at runtime
(only reportlab's unrelated `pdfgen.canvas`); no keys set. Nothing to pay for or maintain.
Did NOT delete files (setup_wizard runs canva_oauth.py as an optional subprocess; deleting
would break that optional path). Instead marked Canva DEPRECATED/SKIP in the connections
guide (api_connections_tools.py) so no deploy is steered to wire up a paid tool PIL replaces.

**Email:** `email_marketing_tools._send_newsletter` now prefers Resend for marketing/bulk
(better deliverability; Outlook/Gmail SMTP throttle + hurt reputation on bulk). Added
`_send_via_resend` (dependency-free, urllib → api.resend.com). Transport selection: Resend
when `RESEND_API_KEY` set, else SMTP fallback (unchanged). Transactional file delivery
(digital_delivery_tools.py) stays on SMTP — untouched. SES documented as the cheaper at-scale
alternative (needs boto3/SigV4) in a code comment. Verified all 3 branches (resend / smtp
fallback / clear error when neither configured).

**Build:** b4d0e2c-v93.

### ACTION FOR SCOTT (optional, only if doing email marketing)
Sign up at resend.com (free ≤3k/mo), verify a sending domain, set `RESEND_API_KEY` and
`RESEND_FROM=you@yourverifieddomain` on Railway. Newsletters then route via Resend
automatically; without it they keep using SMTP.

## 2026-07-02 · v94 · Veo proof attempt — integration correct, blocked on Google billing

**What happened:** Ran a real Veo generation with a live Gemini API key (google-genai 2.10.0
installed, key in .env, AI_VIDEO_ENGINE=veo).
- Key AUTHENTICATED (no 401).
- Model `veo-3.1-fast-generate-preview` was ACCEPTED (reached quota check → request well-formed,
  integration correct). `veo-3.1-generate-preview` also accepted. Old `veo-3.0-generate-001`
  id 404s on Gemini API v1beta (irrelevant fallback).
- Generation BLOCKED: HTTP 429 RESOURCE_EXHAUSTED — "check your plan and billing details."
  Veo is not on the Gemini free tier; the project needs billing/paid tier enabled.

**Code correction (verified against the installed SDK):** _generate_veo download now writes the
bytes returned by client.files.download() (with a video.video_bytes fallback) instead of the
doc-based video.save(). Default model confirmed correct: veo-3.1-fast-generate-preview.

**Status:** Veo path is proven correct up to the paywall. NOT yet proven end-to-end (no billing).

### ACTION FOR SCOTT
1. Enable billing / paid tier on Google Cloud project 208375896852 (the one the Gemini key
   belongs to) so Veo video calls are allowed. In Google Cloud Console → Billing → link a
   billing account to that project; confirm Veo/Generative AI quota.
2. REVOKE the Gemini key that was pasted into chat (it's exposed). After billing is on, create
   a FRESH key and set GEMINI_API_KEY in Railway Variables (not chat).
3. Then tell Claude "billing is on" → I run the real generation + verify the MP4 (same bar as
   the Sora proof) before flipping Veo on in production.

**Build:** b4d0e2c-v94.

## 2026-07-02 · v94 (proof) · Veo 3.1 PROVEN end-to-end ✅

After billing was enabled, ran a real Veo generation on a real product image:
- model veo-3.1-fast-generate-preview, aspect 9:16, job completed in 128s
- output: valid MP4 (ftyp/mdat/moov), 192 frames @ 720x1280 portrait (~24fps), WITH native
  audio track — decoded via imageio to confirm. MP4 sent to Scott.

**Sora → Veo migration is functionally complete and verified.** ai_video.py "veo" engine works.

**Production rollout (safe default preserved):** code default engine is still "sora" — Veo
activates only when AI_VIDEO_ENGINE=veo. So production keeps using Sora until Scott sets the
Railway env vars below. Flip whenever ready (and before Sora's Sept 24 shutdown).

### REMAINING SCOTT ACTIONS
1. REVOKE the Gemini key pasted in chat (exposed). Create a fresh one.
2. In Railway → Variables: set GEMINI_API_KEY=<fresh key> and AI_VIDEO_ENGINE=veo, redeploy.
   That flips the live Studio video engine to Veo. (Optional: VEO_MODEL to pick fast/quality.)
3. The container's throwaway .env key will die on recycle; only the Railway var matters for prod.

## 2026-07-02 · v95 · Image migration — Nano Banana engine (gpt-image-1 deprecation)

**Motivation:** gpt-image-1 deprecates 2026-10-23. Added a swappable image engine, mirroring
the Veo video migration, and PROVED Nano Banana for real (Gemini key + billing already live).

**Changes:**
- tools/image_gen.py: generate_image()/edit_image() now dispatch on IMAGE_ENGINE (default
  "openai", unchanged) → "gemini" (Nano Banana, gemini-2.5-flash-image) / "ideogram" (v3, text
  →image, generate-only). New engines guarded (missing key/SDK/unknown → clear error).
  IMAGE_MODEL env overrides the gemini model (3.1-flash-image / imagen-4 are a flip).
- tools/listing_photo_pipeline.py: generate_verified_photo generate step routes through the
  engine flag — IMAGE_ENGINE=gemini drives the self-verifying loop with Nano Banana; verify
  (gpt-4o) + goal_loop unchanged.

**PROVEN this session (real calls):**
- Nano Banana text→image: valid 1024x1536 image.
- Nano Banana edit (the listing-photo use): real product art → lifestyle scene, valid 1024x1024.
  Both sent to Scott.
- Full pipeline with IMAGE_ENGINE=gemini: generation ran via Nano Banana inside the real loop;
  gpt-4o verifier correctly rejected a physics-profile mismatch in the test (sign_flat vs a
  framed print) — the honest-failure guardrail working, not a model fault. Integration proven.

**Ideogram:** written, UNPROVEN (no IDEOGRAM_API_KEY). Guards verified.

**Default stays OpenAI** (zero regression — dispatch only triggers when IMAGE_ENGINE!=openai;
guards + default confirmed). Build b4d0e2c-v95.

### ACTION FOR SCOTT (before Oct 23)
- To flip listing photos + mockups to Nano Banana: set IMAGE_ENGINE=gemini and GEMINI_API_KEY
  (fresh Railway key) in Railway, redeploy. Optional IMAGE_MODEL to try gemini-3.1-flash-image.
- For text-in-image covers/badges: get an Ideogram key, set IDEOGRAM_API_KEY, use engine
  "ideogram" (I'll prove it once the key exists).

## 2026-07-02 · v96 · Upgrade Frank's brain to Sonnet 5 (with safe fallback)

**Change:** MODEL_PRIMARY default flipped claude-sonnet-4-6 → claude-sonnet-5 in
business_config.py. Takes effect on next Railway deploy of this branch.

**Safety net (so this can't hard-break Frank):** _anthropic_create() in main.py now catches
NotFoundError/PermissionDeniedError and, if the requested model is unavailable to the account,
retries ONCE on _MODEL_FALLBACK="claude-sonnet-4-6" and logs it. Verified with a mock (sonnet-5
unavailable → auto-retry on sonnet-4-6, no crash). So if the Anthropic account lacks Sonnet 5
access, Frank keeps running on 4.6 and logs the fallback instead of erroring.

**Honest caveat:** couldn't verify claude-sonnet-5 account access from this container (no
ANTHROPIC key here — only in Railway). The fallback makes that safe. Instant manual rollback:
set MODEL_PRIMARY=claude-sonnet-4-6 in Railway.

**Build:** b4d0e2c-v96.

### NOTE FOR SCOTT
After the next deploy, if Frank's logs show "[anthropic] model 'claude-sonnet-5' unavailable
… falling back to 'claude-sonnet-4-6'", your account isn't enabled for Sonnet 5 — request
access at console.anthropic.com, or leave it (it runs fine on 4.6).

## 2026-07-02 · v97 · 4 new color themes + daily-brief deadline surfacing

**Color themes:** added 4 UI themes to the Settings → Appearance picker — Sakura (rose),
Matcha (green), Ocean Teal, Midnight Kawaii (neon). Edited exactly 2 places in
frank_hud_mockup.py: the `html.theme-<name>{...14 vars...}` CSS blocks and the `_UI_THEMES`
JS registry. Now 8 themes total (default + 7). Persistence unchanged (localStorage frankTheme,
per-device).

**Daily-brief deadlines:** daily_brief.py now surfaces open to-dos with a due_date within 14
days (or overdue) as an "⏰ DEADLINES APPROACHING" block — in both the AI-synthesized brief
(preserved verbatim) and the no-AI fallback. Reads db.list_todos(); degrades to no-op if the
DB is unavailable so the brief still sends. So the two dated to-dos (Veo before Sep 24, Nano
Banana before Oct 23) auto-surface in Frank's daily brief as their deadlines near.
Verified: overdue + soon shown, far-future/undated excluded, sorted soonest-first.

**Build:** b4d0e2c-v97.

## 2026-07-02 · v98 · Settings: runtime agent-name rename + AI engine toggles

**Foundation:** new `settings(key,value)` table in db.py + get_setting/set_setting/all_settings
(cached). main.py `_apply_settings_overrides()` syncs stored overrides into the exact places
code reads them — env vars for the per-call flags (IMAGE_ENGINE, AI_VIDEO_ENGINE, IMAGE_MODEL)
and business_config attributes for live-read values (MODEL_PRIMARY, AGENT_NAME/SHORT/OWNER).
Runs at startup and after every settings change. Tool modules unchanged (zero-risk).

**AI engine toggles:** Settings → "AI Engines" card: video (sora/veo) + image
(openai/gemini/ideogram) dropdowns → POST /api/settings → live switch, no Railway edit.

**Agent rename (full dynamic):** Settings → "Branding" card renames the agent. Mechanism:
- UI/login/manifest already sentinel-templated → reflect the new name on next load (HUD cache
  busted via _refresh_identity()).
- Agent self-identity: _system_block() + _tools_with_cache() run `_localize_identity()` per
  request, swapping the baked-in name for the current one. No-op (byte-identical, prompt-cache
  still hits) when unchanged → zero behavior change by default; one-time cache miss on rename.
- Fixed the hardcoded "FRANK" PWA manifest name (now follows AGENT_NAME_SHORT).

**Verified deterministically:** settings roundtrip, apply-sync, localize (clean rename +
no-op), HUD renders with all cards/themes, no sentinel leaks, all files compile.
**NOT verified here:** a live agent turn saying the new name (no Anthropic key in this
container; code not yet deployed). Confirm post-deploy: rename in Settings → ask the agent
its name.

**Shipping note:** planned as 2 commits but the shared settings foundation entangled the name
+ engine code in the same functions; shipped as 1 to avoid broken intermediate states. The
send-path name substitution is the only core-loop touch and is clearly delimited/revertible.

**Build:** b4d0e2c-v98.

### NOTE FOR SCOTT
Rename Frank: Settings → Branding → type a name → Save → reload. Switch AI engines:
Settings → AI Engines (needs GEMINI_API_KEY for Veo/Nano Banana). All persist in the DB.

---

## 2026-07-03 — "Nothing saves when I log out" = ephemeral storage (no /data volume)

**Symptom (Scott):** Every time he logs out / comes back to Frank, his data is gone —
todos, Settings (agent name, engine toggles), even his login account (back to the
first-run "create account" setup screen).

**Root cause:** The Railway service has **no Volume mounted at `/data`**. Confirmed live:
`GET /health` → `"persistent":false`. `db._resolve_db_path()` then falls back to the
ephemeral in-container path (`hub_data/hub.db`). Because Railway auto-deploys on every push
to `claude/etsy-automation-agents-WFAPU` AND recycles the container on its own, every restart
starts on a fresh empty disk — wiping the entire SQLite DB (todos, settings, `hub_users`,
`hub_sessions`, saved files, metric history, rotated Etsy tokens). Empty `hub_users` → login
shows the first-run setup page, so it *feels* like logout erased everything. Same root cause
as the earlier "7 todos vanished" incident.

**The actual fix (Scott, Railway dashboard):** attach a Volume with mount path `/data`. The
code already prefers `/data/hub.db` automatically once it exists (no code change needed). The
new volume starts empty, so one final "create owner account" setup — then it persists forever.

**Safeguard shipped this session (so it can never be silent again):**
- `main.py` startup now prints a loud multi-line `[db] ⚠️ EPHEMERAL STORAGE` banner to logs
  when `not db.is_persistent()`.
- `_SETUP_PAGE` (login/setup screen) shows a red warning block when not persistent — exactly
  where the wipe dumps you — explaining to attach a `/data` volume. Empty on a real volume.
- HUD (`frank_hud_mockup.py`) shows a fixed red top banner "DATA IS NOT BEING SAVED …" driven
  by `checkPersistence()` → `fetch('/health')`; auto-hides once `persistent:true`.
- Zero behavior change when a volume is attached (all guards keyed off `db.is_persistent()`).

**Build:** b4d0e2c-v99.

---

## 2026-07-03 — Gave Frank a real browser (Playwright, wired into the agent)

**What:** Wired the previously-unused `tools/browser_automation.py` into Frank's agent so he
can SEE rendered pages, not just scrape HTML with requests. Four new tools: `render_page`,
`screenshot_url`, `check_browser_status`, `check_etsy_search_rank`. Primary purpose: let Frank
verify his own live listings actually render correctly (the "never lie / show the real product"
rule), screenshot them, and read JS-heavy research pages the requests-based `browse_web` can't.

**Why now:** Scott asked what GitHub tooling could make Frank more capable. A browser was the
highest-fit add, and the module already existed — this was a wiring job, not new code.

**Changes:**
- `tools/browser_automation.py` — made portable off the sandbox: `CHROMIUM_PATH` is now env-
  overridable and `_launch_context` omits `executable_path` (uses Playwright's bundled Chromium)
  when that path doesn't exist — the Railway case. `is_available()` no longer path-gates.
- `Dockerfile` — added `playwright>=1.45.0` to the pip list + `RUN playwright install
  --with-deps chromium`. This meaningfully grows the image and Chromium peaks ~300–500MB RAM
  per call (launched on-demand and closed each call, so the spike is transient). Scott chose
  Railway (autonomous) over relay/hosted knowing this.
- `tools/api_server/main.py` — bare `import browser_automation` (matches the sibling-module
  pattern; `tools/` is on sys.path via line 43), `AGENT_TOOLS.extend(...TOOL_DEFINITIONS)`,
  a dispatch branch in `_execute_agent_tool` that `json.loads` the module's string returns into
  the dict contract, and status-line labels. Tool count 31 → 35.

**Verified (sandbox, real):** portability fix launches Chromium; full navigate→title→text→
screenshot pipeline proven via a `data:` URL (no network — sandbox egress is locked for the
browser, so live-internet render can't be shown here); `import main` loads clean with the bare
import and routes `render_page` through the real dispatcher returning a dict.

**Post-deploy checks still owed (the real proof):**
1. Call `check_browser_status` on Railway → Chromium must boot in the image without OOM.
2. `render_page` on a real onbrandcraftz listing URL → **datacenter-IP question**: Etsy may 403
   Railway's IP (it 403s the sandbox IP). If 200, autonomous listing verification works; if 403,
   the browser still serves all non-Etsy pages and the tools report "blocked" honestly.

**Known follow-up (not this change):** the Dockerfile pip list also lacks `google-genai`
(needed when Scott flips `IMAGE_ENGINE=gemini`/Veo) and `beautifulsoup4`/`lxml`/`requests`
(used by the existing `browse_web`/`search_etsy`) — worth reconciling the Dockerfile against
requirements.txt in a dedicated pass.

**Build:** b4d0e2c-v100.

---

## 2026-07-03 — Dockerfile reconciled to requirements.txt (dependency drift fix)

**Problem:** The Dockerfile installed a hand-picked pip list that had drifted out of sync
with the app's real deps. Missing from the image: `requests`/`beautifulsoup4`/`lxml`
(browse_web/search_etsy), `google-genai` (Veo / Nano Banana / Gemini video understanding),
`python-multipart` (login form parsing), `PyNaCl` (relay crypto), `apscheduler`, `vtracer`,
`reportlab`, `flask`. Any feature needing those would fail at runtime on Railway despite
working locally.

**Fix:**
- `Dockerfile` now runs `pip install -r requirements.txt` instead of a hand-picked list, so
  the image can't silently drift from the manifest again. Kept the ffmpeg apt install and the
  `playwright install --with-deps chromium` step (playwright is in requirements.txt).
- `requirements.txt`: added `google-genai>=1.0.0` (was only in tools/api_server/requirements.txt);
  changed `uvicorn>=0.29.0` → `uvicorn[standard]>=0.29.0` **then pinned** `uvicorn[standard]==0.29.0`
  and `fastapi==0.111.0` to the known-good versions the working image ran on. `[standard]` is
  required for the WebSocket chat path (pulls websockets/uvloop/httptools/watchfiles).

**Verified:** `pip install --dry-run --ignore-installed -r requirements.txt` resolves 100% to
prebuilt wheels (no compiler needed on python:3.11-slim) — fastapi-0.111.0, uvicorn-0.29.0,
starlette-0.37.2, websockets-16.0, vtracer-0.6.15, lxml-6.1.1, PyNaCl-1.6.2, google-genai-2.10.0
all wheel-resolve. Only fastapi/uvicorn were pinned-vs-float deltas from the old image; every
other now-added package was simply absent before, so this is strictly additive to the working
core. Post-deploy proof = /health returns v101 (a successful build means the -r install worked
in the real Docker build).

**Enables:** google-genai in the image is the missing piece for both the image/video engine
migrations (IMAGE_ENGINE=gemini, AI_VIDEO_ENGINE=veo) AND Gemini native video understanding —
once GEMINI_API_KEY is set, Frank can analyze video (Gemini ingests video files <100MB inline,
larger via File API, or YouTube URLs; samples ~1 FPS + audio).

**Build:** b4d0e2c-v101.

---

## 2026-07-03 — Frank can now WATCH video (Gemini native, watch_video tool)

**What:** New `watch_video(source, question)` agent tool (tools/video_understanding.py).
Source = a local file path OR a URL (YouTube/TikTok/direct .mp4/~1000 sites via yt-dlp). The
video is uploaded to Google Gemini's File API and analyzed natively (Gemini samples ~1 fps +
audio), returning a TEXT description/answer — which is what Frank's Claude brain consumes
(tool results are text, so Gemini does the "watching" and hands back words). Use cases: QA on a
generated product/listing video, or watching a competitor's video for research.

**Why this design:** An LLM can't ingest a video file directly — it needs frames+audio. Two
options: (a) ffmpeg frame-extraction → vision model, or (b) Gemini native. Gemini is cleaner
and google-genai is already in the image (added in the Dockerfile reconciliation). Frame-
extraction→Claude is awkward here because tool results are text, not image blocks.

**Proven live (2026-07-03):** built a controlled 3-frame test video (digits 1/2/3) and Gemini
read them back correctly ("1, 2, 3") — both directly and through the real main.py dispatcher.
Verified API surface: client.files.upload → poll files.get until FileState.ACTIVE →
models.generate_content([file, prompt]) → resp.text. Uploaded file is deleted after analysis.

**Changes:**
- `tools/video_understanding.py` (new) — watch_video tool, Gemini analysis, yt-dlp URL fetch
  (<=720p mp4 cap), guards for missing key/SDK/file.
- `tools/api_server/main.py` — registered in AGENT_TOOLS (now 36 tools), dispatch branch
  (json.loads → dict), status line "🎬 Watching…".
- `requirements.txt` — added `yt-dlp>=2025.1.1` (pure-python wheel, verified resolves).

**Requires:** GEMINI_API_KEY set on Railway. Honest limits: video is ~300 tokens/sec (prefer
short clips / specific questions); yt-dlp fetching a site depends on that site not blocking the
server's datacenter IP (local files always work); the "paste a video into chat" UX still needs
an upload path + the /data volume (separate follow-up).

**Build:** b4d0e2c-v102.

---

## 2026-07-03 — CI smoke-test gate (first automated test for Frank)

**Problem (from the productivity review):** main.py is 7,135 lines, had ZERO automated
tests, and Railway auto-deploys every push straight to production with no gate. The most
common prod-breaker is an import-time crash (bad import / module-scope error) — e.g. the
`from tools import ...` top-level bug that nearly shipped with the browser tools.

**Fix:**
- `tests/smoke_test.py` — imports the server module (catches syntax/import crashes in main.py
  and every module it imports), then asserts the AGENT_TOOLS registry built (≥25 tools),
  the session's wired tools are present (render_page/screenshot_url/check_browser_status/
  check_etsy_search_rank/watch_video), the dispatcher is callable, and tool schemas are
  well-formed. No server start, no background loops, no network/API calls, no secrets.
- `.github/workflows/ci-smoke.yml` — on every push + PR: setup py3.11, pip install
  -r requirements.txt, `compileall tools tests`, run the smoke test.

**Verified:** smoke passes locally (36 tools, exit 0); `compileall tools tests` is clean, so
the first CI run won't red-flag legacy code.

**IMPORTANT — to make this a HARD gate (not just an alarm):** GitHub Actions runs in parallel
with Railway's deploy; a red check does NOT stop Railway by default. Enable Railway → service →
Settings → **"Wait for CI to pass"** (Check Suites) so Railway only deploys after this check is
green. Until then, CI is an early-warning signal, not a deploy blocker.

**Follow-ups from the same review (not done here):** graceful tool degradation (tools self-report
"unavailable: needs GEMINI_API_KEY / relay offline" instead of raw errors); harden the
`get_me` fail-open-to-owner path (main.py:3146) to fail closed; begin extracting main.py (7,135
lines) into modules.

---

## 2026-07-03 — Capability visibility in Dependency Health (graceful degradation, Unit A)

**From the productivity review:** optional capabilities that need a key/connection can fail
when someone tries them, with no place showing what's Ready vs Needs-setup. (Tool-level messages
were already clean — relay dispatch and watch_video return human-readable errors.)

**Unit A (backend):** `/api/system/dependencies` now also returns a `capabilities` list —
video analysis (Gemini), Gemini image engine, browser, relay — each `{key, label, available,
hint}`. `_capability_report()` reuses `video_understanding.is_available()`,
`browser_automation.is_available()`, `bool(os.getenv("GEMINI_API_KEY"))`, and relay
connected/kill state. Reports booleans + a fix hint only — never a key value.

**Verified:** with the Gemini key present → video/image/browser available:true; without it →
available:false + hint "needs GEMINI_API_KEY"; relay shows "offline — not connected" when no
relay. Key value confirmed not leaked in the payload. py_compile + smoke green.

**Next (Unit B):** render these as Ready / Needs-setup pills in the HUD Dependency Health panel.

**Build:** b4d0e2c-v103.

---

## 2026-07-03 — Capability pills in the HUD (graceful degradation, Unit B)

**Unit B (UI):** `_renderDependencyHealth()` in frank_hud_mockup.py now also renders the
`capabilities` from /api/system/dependencies as pills under a "Capabilities" subheader —
green "READY" when available, amber "NEEDS SETUP · <hint>" otherwise (e.g. "needs
GEMINI_API_KEY", "relay offline — not connected"). Reuses the existing .dep-pill / half_open
styling; escHtml on all fields.

**Verified:** JS render logic run with mock data (Node) → available→READY (green), unavailable
→NEEDS SETUP (amber) + hint, correct markup; py_compile + smoke green. So a tester now SEES
what needs setup instead of discovering it by a failed tool call.

**Build:** b4d0e2c-v104.

---

## 2026-07-03 — Harden get_me to fail closed (minor, from the review)

**Honest scope correction:** the productivity review flagged get_me as "fails open to owner."
On reading the code, the REAL enforcement (`_require_owner`, main.py:3150) already fails closed
(403s an unknown user on every admin action), so this was never an exploitable privilege
escalation — worst case a stale session (user row deleted/reset) briefly SEES owner-only UI it
can't actually use.

**Fix:** get_me (main.py:3146) now returns role "" instead of "owner" when the session's user
row is missing — aligns the UI hint with the fail-closed enforcement. No real owner is affected
(they always have a row). Verified: py_compile + smoke green.

**Build:** b4d0e2c-v105.

---

## 2026-07-03 — Quality gates now have real tests (CI-enforced)

**Symptom / gap:** The code that enforces the #1 rule ("never lie to the customer /
quality never decreases") — `EtsyAPIClient.pre_publish_gate()` and
`validate_digital_file()` in `etsy_api.py` — had ZERO tests. A careless edit could
silently disable a check (title ≤70, all 13 tags, price ending, mislabeled/corrupt/
empty ZIP, traced-raster SVG rejection, path-traversal) and a violating listing or a
broken file could ship with nothing to catch it. The existing CI smoke test only
proves the app *imports*, not that the rules *work*.

**Fix:** Added `tests/test_quality_gates.py` — 28 dependency-light, secret-free tests
covering every branch of `pre_publish_gate` (title length/floor/phrase, tag count/
width/special-chars/title-dup, desc length, price floor + .99/.97/.49 ending + cents
normalization, is_supply) and `validate_digital_file` (missing/empty/oversize,
extension + magic-byte mismatch, ZIP CRC/empty/no-product-files/path-traversal, clean
vs traced-raster SVG). Wired into `.github/workflows/ci-smoke.yml` so it runs on every
push/PR alongside the smoke test. Needs no APP_SECRET_TOKEN, no network, no API keys.

**Note:** The first run caught a real duplication bug — in the *test fixture*, not the
code: a baseline tag ("budget planner") duplicated a title phrase, which the gate
correctly rejected. Fixed the fixture; the gate behaved exactly as designed. No runtime
code changed, so `_BUILD_ID` was intentionally NOT bumped (test/CI-only change).

---

## 2026-07-03 — 🚨 LIVE INCIDENT: Frank's Anthropic account out of credits (agent down)

**Symptom:** Driving the deployed Frank over `/ws/chat` returns an error frame:
"Frank's AI provider account is out of credits — let Scott know to top up Anthropic billing."
Every agent turn (owner OR tester) fails right now — Frank's brain is offline. The rest of the
app (dashboard, endpoints, health) is up; only the Anthropic-backed agent loop is dead.

**Root cause:** The production `ANTHROPIC_API_KEY`'s account balance is depleted (Anthropic
returns an insufficient-credits error, mapped by `_friendly_error_message`). Not an auth/key
problem — the key authenticates; the balance is zero.

**Fix (Scott's action):** Top up Anthropic billing (console.anthropic.com → Billing). No code
change needed; the agent resumes the moment credits are available.

**Secondary finding (smaller follow-up, not fixed here):** `/api/system/dependencies` shows
`anthropic_api` breaker state "closed" with `updated_at: null` — the out-of-credits failure is
NOT tripping the Anthropic circuit breaker, so the Dependency Health panel reports Anthropic as
healthy while the agent is actually down. Worth wiring the credits/402 error into
`_anthropic_breaker.record_failure()` so the panel reflects reality. Logged for later.

**Verified in the same session:** sandbox→Railway WebSocket egress WORKS (ticket mint via Bearer
+ `/ws/chat` connect both succeeded), and `/api/system/dependencies` reports
`browser: available:true` on Railway — so Playwright/Chromium is installed in the image. The full
browser render proof (Chromium boots a page + Etsy-IP reachability) is blocked only by the
out-of-credits issue, since browser tools run through the agent loop. Re-run the browser probe
once credits are restored.

---

## 2026-07-03 — Fixed DP1027 Sheet 6 sticker segmentation (misdiagnosed as "too connected")

**Symptom:** DP1027 Sheet 6 produced only 1 individual sticker (the whole sheet as one
blob), vs 23–56 on every other sheet. CLAUDE.md had recorded this as "stickers too connected
in AI output."

**Root cause (actual):** NOT connected stickers — the stickers are clearly separated. The
`remove_white_background()` in `tools/process_sticker_sheets.py` removed background only where
ALL RGB channels were ≥238 (pure white). Sheet 6's background is cream paper (~RGB 240,237,232);
the blue channel (232) is below 238, so the background was never detected → never removed →
every sticker stayed fused into one opaque blob → connected-components found 1 region.

**Fix:** `remove_white_background()` now SAMPLES the background color from the four sheet corners
(median) and floods border-connected pixels within an RGB distance (`BG_COLOR_TOLERANCE=42`) of
it — a superset of the old pure-white behavior that also handles cream/tinted paper. Safety
fallback to the strict white≥238 test when corners aren't a uniform light color (so dark/
full-bleed art is never eaten). Verified on the REAL Sheet 6: **1 → 21** individual stickers,
clean transparent cutouts; other sheets unregressed (still segment normally). Pure numpy/scipy
(already deps) — no new dependency in any image.

**rembg was evaluated and REJECTED for this:** rembg/u2net segments foreground-vs-background,
not instance-vs-instance; on this busy sheet it masked ~93% as one foreground blob and still
yielded 1 sticker. The lightweight color-flood is both correct AND lighter (no 176MB model,
no onnxruntime). The plan had assumed rembg; testing on the real file proved otherwise.

**Not done (Scott-gated):** regenerating + reuploading the DP1027 pack to the live Etsy listing.
The tool is fixed and proven; applying it to the shipped pack touches a live listing = Scott's
call. No `_BUILD_ID` bump — this is a build-time script, not part of the Railway server image.

---

## 2026-07-03 — Added Scrapling competitor-intel tool (parser proven; stealth unverified here)

**What:** New `tools/competitor_intel.py` (competitor/keyword/trend research via Scrapling's
adaptive parser + stealth fetch, with a plain-requests fallback). Optional deps in
`requirements-research.txt` — deliberately NOT in `requirements.txt`/the Railway server image,
since Scrapling pulls a browser-impersonation stack (curl_cffi, browserforge) and its core
benefit is unproven.

**Honest verification status:** Scrapling's PARSER is verified (css/xpath/regex extraction on
real HTML). The stealth FETCH (curl_cffi TLS impersonation — the thing that would beat Etsy's
datacenter-IP 403) could NOT be validated in the build sandbox: that environment routes egress
through a MITM HTTPS proxy that resets curl_cffi's custom TLS ("connection reset by peer"), so
the tool falls back to plain requests and Etsy still 403s. This is a sandbox artifact, not a
Scrapling flaw — on a normal network (Scott's PC via relay, or Railway) there's no such proxy.

**Not wired into Frank yet — on purpose.** Wiring it as a live agent tool would imply the Etsy
path works, which is unproven. Gate: run `python tools/competitor_intel.py --selfcheck` on the
relay or Railway; if the stealth fetch gets a 200 from Etsy there, THEN add scrapling to the
server image and register it as an agent tool. Until then it's a ready-but-unvalidated research
helper. ToS caution documented in the module (Etsy scraping is low-volume, public-data only;
Scott opted in and owns that risk).

---

## 2026-07-03 — graphify codebase map (offline) → main.py modularization plan

**What:** Ran `graphify` (safishamsi/graphify — Tree-sitter static graph, FULLY OFFLINE, no LLM
cost) over `tools/`. 2,157 nodes / 4,232 edges / 142 communities from commit aea4a2b. Install:
`uv tool install graphifyy && graphify install`; offline rebuild: `graphify update .` (the plain
`extract` tries an LLM semantic pass on docs/images — use `update` or a code-only folder to stay
offline; our Anthropic account is out of credits so offline is required).

**Payoff:** graphify auto-flagged "Should main.py be split?" and showed main.py fragments into 3
low-cohesion communities — route handlers (55 nodes), the agent-tool layer (61 nodes), and
admin/auth/HUD (42 nodes). Turned that into a concrete split map:
`data/knowledge_base/main_py_modularization_map.md` (committed). Interactive `graph.html` (~1.8MB)
handed to Scott, NOT committed (generated-file bloat). This is a PLANNING artifact — the
modularization itself is deliberate future surgery, gated behind the CI smoke + quality-gate tests.

---

## 2026-07-03 — smoke test hardened to pin core agent tools + routing (main.py split prep)

**What:** `tests/smoke_test.py` gained two guards ahead of the planned main.py agent-tool-layer
extraction: (4b) `EXPECTED_CORE_TOOLS` (the 25 dispatcher-handled core tools) must all be in the
`AGENT_TOOLS` registry; (4c) each core tool must also have a `name == "..."` branch in
`_execute_agent_tool` (checked by source inspection, since invoking the dispatcher would hit
Etsy/db/anthropic). Two prod-inert test commits (142deb0, 3bd299f) — no `_BUILD_ID` bump.

**Why:** the old smoke test asserted only `AGENT_TOOLS` len≥25 + the 5 browser/video names, so a
core tool could be dropped/renamed OR lose its dispatch branch and CI would stay green (padded to
≥25). That's exactly the failure mode a file-split could introduce. These checks make it fail loud.

**Split status:** the actual extraction (Phase 1) is HELD. Reason: the agent-tool layer is
entangled with module globals (`_cache`, `db`, anthropic client/breaker, business_config) and Frank
is currently down (Anthropic credits) so a moved handler can't be runtime-verified. Chose the safe
source-inspection routing test over a ~360-line blind HANDLERS-dict refactor. Do the split once
Frank is live for dispatch verification and/or these guards have proven themselves in CI.

---

## 2026-07-03 — creative-production tooling reviewed (art / 3D / QC GitHub options)

**What:** Scott asked whether we're running the best GitHub options for visual design, digital-art
production, 3D physical products, and streamlining. Researched the 2026 landscape + our stack;
wrote the honest scorecard to `data/knowledge_base/creative_tooling_assessment.md`.

**Outcome:** assessment-only, no code. Genuine upgrades (AI upscaling via Real-ESRGAN/Upscayl;
image→3D via TRELLIS.2/Hunyuan3D) are GPU-heavy and Scott's GPU is weak → local off; the zero-GPU
cloud-API path (Replicate/Tripo/Meshy) is available if ever wanted, matching our buy-don't-host
doctrine. Neither is a must-build (Lanczos already clears the wall-art gate; image→3D is a
strategic new-product bet). SKIPs: sticker SAM2/RMBG (color-flood already solves our flat sheets,
2026-07-03 fix); vtracer/potrace (output traced-raster SVGs our own validate_digital_file() gate
rejects for AMS color separation). Design QC (VLM verify_render + goal_loop + gates) already
stronger than most shops. See the assessment doc for the full table.

---

## 2026-07-03 — Frank Phone Mode: dedicated 4-tab mobile shell (v106)

**What:** Scott: the HUD is too cramped on a phone — 19 desktop screens reflowed into one long
scroll. Added a phone-only bottom tab bar (Ask / Approvals / Today / More) in
`frank_hud_mockup.py`, gated entirely behind `body.is-mobile`. Desktop is untouched. Tabs delegate
to existing machinery — Ask→orb/chat, Approvals→`showScreen('actions')` (Action Center, auto-loads),
Today→`showScreen('cmd')` (home glance), More→a full-screen overlay of the existing 19-item nav (so
nothing is lost, just demoted). On phone the floating hamburger + desktop bottom bar are hidden and
the sidebar is hidden-until-More. Styled through existing theme vars (`--panel/--cyan2/--red/…`) so
the color-theme selector recolors it too. Approvals badge mirrors `setActionBadge` onto `#ptab-badge`.

**Verify:** py_compile + smoke + quality-gate green. Playwright at 390×844 confirmed all 16 checks —
tab bar shows, hamburger/sidebar hidden by default, each tab drives the right screen, More overlay
reveals+closes the nav, and the bar recolors on theme change; at 1440×900 desktop is unchanged
(no is-mobile, tab bar hidden, sidebar visible). NOT yet proven live: chat replies (need Anthropic
billing) and a real staged-action approve→Etsy round-trip (need live server) — deferred honestly.

**Note / v1 tradeoff:** "Today" reuses the existing home dashboard screen rather than a bespoke
compact glance (the mockup showed a tighter card layout). Fast-follow if Scott wants it tighter.

---

## 2026-07-03 — Frank Phone Mode v2: native panels + More scroll fix (v107)

**What:** Scott tested v1 on his phone — Ask + the tab bar were great, but Approvals/Today reused
DESKTOP screens (too big) and More reused the desktop sidebar which the mobile @media forced to
position:static + overflow:visible !important → couldn't scroll. Fixed by building 3 dedicated
phone-native panels in a new `#phone-body` (own classes, immune to the desktop overrides):
Approvals = compact `_pendingActions` cards reusing `approveAction`/`openRejectModal`; Today =
metric tiles (/api/metrics) + alerts (/api/alerts); More = a scrollable launcher → `showScreen`.
Ask still = orb. Styled through theme vars so the color selector recolors it. v1 phoneTab archived
via trash.py (20260703-001) before replacement.

**Verify:** py_compile + smoke green (v107). Playwright at 390×844 — 20 checks incl. Approvals
renders compact cards wired to phoneApprove, Today shows tiles+alerts from stubbed endpoints, and
critically **the More panel scrolls** (scrollHeight>clientHeight, scrollTop=300); panels recolor on
theme change; desktop (1440×900) unchanged. Live approve→Etsy + live metrics still need Frank on
billing. Note: More's destination screens remain desktop-style for now (occasional access) — a v3
could phone-optimize individual screens if Scott wants.

---

## 2026-07-03 — Frank Phone Mode v3: kill horizontal overflow on desktop screens (v108)

**What:** Scott's phone shots still showed content too wide (cards/rows cut off, page scrolled
sideways). Two things: (1) the shots were the OLD build — every tab opened a desktop screen;
v107's compact panels hadn't loaded yet (the /frank-sw.js SW is network-first for navigations,
so a reopen after the Railway build pulls latest — deploy lag, no SW change). (2) Real bug: the
19 desktop screens use inline `grid-template-columns:1fr 1fr` blocks that never collapse on phone.
Fix (CSS, mobile-gated, desktop untouched): `body.is-mobile .screen [style*="1fr 1fr"]{grid-
template-columns:1fr !important}` (an !important rule beats non-important inline styles), plus a
hard `overflow-x:hidden` + `max-width:100vw` guard on #stage/.main/.screen/.panel and width caps on
inputs/buttons/imgs. Also nudged the red persist-warning banner below the iOS status bar
(safe-area-inset-top) since it overlapped the clock.

**Verify:** py_compile + smoke green (v108). Playwright at 390px: 9 desktop screens (settings,
account, connections, security, listings, products, cmd, core, agents) all measured **0px
horizontal overflow**; compact Today tiles still 3-across; desktop 1440px keeps its 2-col grids.
Note: the guard both collapses grids and clips residual, so nothing scrolls sideways.

---

## 2026-07-03 — Phone Approvals badge/panel mismatch fixed (v109)

**What:** Scott: Approvals tab badge showed "7" but the panel said "All clear — nothing to
approve." Root cause: `setActionBadge(summary, pending)` set the phone badge to `summary.high +
pending`, i.e. it counted high-severity *recommendations* from `/api/actions` (_compute_actions:
publish draft, title>70, low-conversion, zero-views), while the phone Approvals panel only renders
*pending staged actions* from `/api/queue`. So 7 recommendations + 0 pending → badge 7, empty panel.
Fix: (1) phone `#ptab-badge` now counts ONLY `pending` (real approvals) so the badge matches the
panel; (2) `renderPhoneToday` now merges the high/medium recommendations (each with its `suggestion`)
into Today → "Needs attention" alongside alerts, so the recommendations aren't lost — they live
where they belong. Desktop `#badge-actions` unchanged.

**Verify:** py_compile + smoke green (v109). Playwright, Scott's exact case (7 recs, 0 pending):
Approvals badge hidden + panel "All clear" (consistent); Today shows 7 recs + 1 alert = 8 items with
their fixes under "Needs attention"; and the badge still shows the pending count (2) when real
approvals exist.

---

## 2026-07-03 — Move the needs-attention badge to the Today tab (v110)

**What:** Follow-up to v109 (Scott: "move the alert to the correct tab"). Since the high-severity
recommendations now render under Today → Needs attention, the count badge belongs on the Today tab,
not Approvals. Added `#ptab-today-badge` to the Today tab button; `setActionBadge` now sets it to
`summary.high` (the urgent recommendations). Approvals badge stays `pending`-only. Verified
(Playwright, 7 recs / 0 pending): Approvals badge hidden + "All clear"; Today tab badge shows "7";
Today panel lists the 7 recs + alert; Approvals badge still shows pending count when approvals exist.

---

## 2026-07-03 — Phone: reachable bottom controls + dismissible persist banner (v111)

**What:** Scott (Studio screen on phone): couldn't tap Generate Video — it sat under the fixed
bottom tab bar and wouldn't scroll into reach; also wanted to dismiss the red "DATA IS NOT BEING
SAVED" banner. Fixes: (1) bottom clearance on phone was `body.is-mobile .main{padding-bottom:74px}`
< the bar height (58px + safe-area ≈ 90px), so the last control couldn't clear it → changed to
`.main,.screen{padding-bottom:calc(80px + env(safe-area-inset-bottom)) !important}` (scales with the
bar). (2) Added an `×` to `#persist-warning` → `dismissPersistWarning()` sets `.show` off + a
`_persistWarnDismissed` guard so `checkPersistence()` won't re-show it this session (returns on a
fresh reload — real warning until /data volume is attached). Desktop untouched.

**Verify:** py_compile + smoke green (v111). Playwright 390×844: Studio 'Generate Video' button
bottom (716) ≤ tab-bar top (785) and on-screen (tappable); banner shows when persistent:false, hides
on ×, stays hidden after re-running checkPersistence; desktop 1440 has no tab bar.

---

## 2026-07-03 — Phone Today: tappable cards → fix-it/view-on-Etsy sheet + metrics tile fix (v112)

**What:** Scott asked for each "Needs attention" card on the phone Today tab to be tappable with a
popup: let Frank fix it, or view the listing on Etsy. Same screenshot showed the ORDERS tile
rendering "[object Object]". Implemented in frank_hud_mockup.py:
1. **Action sheet** `#phone-sheet` (+ backdrop, themed vars): "🤖 Let Frank fix it" → prefills
   `#chat-input` with a targeted prompt ("Diagnose and fix Etsy listing <id> — issue flagged:
   <title>. …stage for my approval, don't change the live listing without me") → `sendMsg()` (real
   WS chat path) → navigates to the cmd screen so the reply is visible + toast. "🏷 View listing on
   Etsy" → `window.open(card.url || etsy.com/listing/<id>)`. Cancel/backdrop closes.
2. **Tappable cards:** recommendations from `/api/actions` keep `listing_id`/`url`; listing-linked
   cards render `role=button` + chevron → `phoneNeedsSheet(i)` (data via `_phoneNeeds[]`, no attr-
   escaping). Plain alerts stay non-tappable.
3. **Tile fix:** `/api/metrics` returns `orders` as an OBJECT and has no top-level views/conversion
   → tiles now use the real shape: `orders.last_7_days`, `orders.revenue_7d` ($, 2dp),
   `shop.total_sales` ("Orders · 7d / Rev · 7d / Total sales"). No more [object Object].

**Verify:** py_compile + smoke green (v112). Playwright 390×844 (stubbed real-shape APIs): 13/13 —
tiles 6 / $71.94 / 21; 2 of 4 cards tappable (listing-linked only); sheet opens w/ title; View
opens https://www.etsy.com/listing/101 (context-stubbed); Fix-it lands the targeted prompt in chat
on the cmd screen; backdrop closes; desktop sheet hidden. Test gotcha logged: Playwright matches
routes in REVERSE registration order — register catch-alls FIRST. Caveat: with Anthropic billing
still empty, Frank replies to fix-it with the credit error until topped up (UI path verified).
