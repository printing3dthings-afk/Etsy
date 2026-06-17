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
