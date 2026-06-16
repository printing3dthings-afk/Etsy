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
