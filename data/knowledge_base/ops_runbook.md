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
