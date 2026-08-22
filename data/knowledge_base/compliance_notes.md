# Compliance Notes — SOC 2, HIPAA, GDPR

*Written 2026-07-18 in response to Scott asking to "make sure" the business
is compliant on SOC, HIPAA, and GDPR. This is an engineering-level review and
hardening pass, not a legal opinion — see "What this is NOT" at the bottom
before treating anything here as a substitute for actual legal advice where
that matters. Readable on demand via `read_knowledge_base_doc` (same
mechanism as `business_standards.md` — call it with no arguments to see
everything available, or `filename=compliance_notes.md` to read this
directly) so Frank can answer compliance questions grounded in this document
instead of guessing.*

---

## HIPAA — does not apply

**Conclusion: OnBrandCraftz is not a HIPAA covered entity or business
associate. No engineering work is needed.**

HIPAA governs Protected Health Information (PHI) handled by healthcare
providers, health plans, and their business associates. This business sells
digital products and 3D-printed goods on Etsy — it does not provide
healthcare and does not receive health data from customers.

The one product that sounds health-adjacent, the **Fitness & Wellness
Planner** (DP1029), is a blank PDF template. The customer fills it in
themselves, on their own device (GoodNotes/Notability/iPad) — nothing filled
in ever comes back to the business. There is no upload endpoint, no "email
us your planner" feature, and no database field anywhere in this codebase
that stores a customer's health/fitness data. Verified directly by reading
the product's build pipeline (`tools/planner_page_adder.py`,
`build_planners.py`) and searching every API route in
`tools/api_server/main.py` — there is no code path that receives this kind of
data from a customer.

If this business ever adds a feature that actually collects health data from
customers (e.g., a form, an upload, anything that comes back from a filled-in
planner), HIPAA applicability should be re-evaluated at that point — this
conclusion is about the business as it exists today.

---

## GDPR — relevant, and mostly in good shape after this pass

Etsy sells globally and this shop has (or can have) EU customers, so GDPR
principles are worth taking seriously even though there's no specific legal
requirement forcing the issue today.

### What's implemented

- **Data minimization at the source.** Only two agent tools ever touch
  buyer-adjacent data: `get_orders` (returns order id, buyer name, total,
  item count, date — verified directly in its handler, `main.py`, that it
  builds a "slim" dict and never touches the raw Etsy receipt's email/
  shipping-address fields) and `get_reviews` (rating, review text, listing —
  no buyer identifier at all). No other registered agent tool exposes
  anything customer-identifying.
- **The durable chat history doesn't retain buyer names.** `_PII_TOOLS` /
  `_should_persist_chat_turn` (`main.py`) deliberately skip writing a chat
  turn to the searchable `chat_messages` table whenever `get_orders` was
  called that turn — Scott's own prior decision, documented in code comments
  dated 2026-07-15. (The in-memory conversation for that live session still
  has the name, since Frank needs it to answer naturally — only the
  *durable, searchable* copy is skipped.)
- **Retention limits on local buyer-referencing files** (added 2026-07-18):
  drafted reply text (`data/message_drafts/*.json`, which can quote or
  reference a buyer's message or review) is deleted after 90 days
  (`_prune_buyer_data_retention()` in `main.py`, runs daily). The two
  ID-only dedupe files (`data/notified_orders.json`,
  `data/message_drafts/sent_log.json`) are capped to their most recent 2,000
  entries for the same reason, since Etsy itself remains the permanent
  record of all order/message history.
- **An accurate customer-facing privacy notice** now exists at
  `/static/privacy.html` (served by `main.py`; `privacy.html` at repo root is
  kept identical). It previously claimed *"No personal data belonging to
  customers or third parties is collected or retained"* — false, given the
  above — and has been rewritten to accurately describe what's collected, why,
  how long, and how a buyer can ask about or request deletion of what this
  app-level tool holds (separate from Etsy's own platform-level data, which
  Etsy governs directly).
- **No accidental git exposure.** Checked the one file that would have been a
  real, live exposure: `data/hub_db_backups/hub_db_state.json` is committed to
  this **public** GitHub repo. All 3 historical versions of that file were
  pulled and scanned (450 combined `action_queue`/`activity_log` records in
  the largest one) for emails, buyer/receipt/customer keywords, and order
  data — zero hits, past or present. `tools/backup_hub_db.py`'s exclusion
  list (tokens, sessions, password hashes) has held in practice.

### What's NOT resolved by engineering work

- **Controller vs. processor status.** Whether OnBrandCraftz-as-seller is
  legally a GDPR "controller" for the subset of buyer data Etsy shares with
  sellers (separate from Etsy's own platform-level controller status for the
  underlying marketplace transaction) is a legal question, not a technical
  one. **If Scott ever needs certainty on this — e.g. an EU customer or
  regulator asks — get a lawyer's read on it.** This document takes the
  practical position (accurate disclosure, data minimization, retention
  limits, a deletion-request contact path) without resolving the formal
  legal categorization, because those practical protections are the right
  thing to do regardless of how that question is answered.
- **A formal Data Subject Access Request (DSAR) process.** Today it's "email
  the shop and Scott handles it manually," which is proportionate for a
  business this size, but there's no automated tooling to search all the
  local files above for a specific buyer's name and produce/delete a
  response. Worth building if request volume ever justifies it.

---

## SOC 2 — hardened, not audited

**Scott's stated goal (confirmed 2026-07-18): harden the underlying
security practices, not pursue a certified report.** A real SOC 2 Type I or
II report requires engaging a licensed CPA firm for a paid audit over weeks
to months, producing formal policies-and-procedures documentation and (for
Type II) evidence of controls operating effectively over an observation
period — none of that can be produced by engineering work alone, and isn't
attempted here. What follows is an honest inventory against SOC 2's Trust
Services Criteria, useful on its own regardless of whether a formal audit
ever happens.

### Security controls in place

| Area | Control |
|---|---|
| Authentication | Single `APP_SECRET_TOKEN` (server refuses to start if unset) via session cookie or Bearer header |
| Password storage | `pbkdf2:sha256:<salt>$<hash>` — never plaintext, never reversible |
| Session management | `hub_sessions` table with `expires_at` |
| Secrets at rest (env) | `.env` gitignored, never committed; `*.pem/*.key/*.crt` etc. also gitignored |
| **Secrets at rest (DB)** | **Etsy OAuth tokens now encrypted in SQLite** (PyNaCl SecretBox, `TOKEN_ENCRYPTION_KEY` env var — added 2026-07-18; falls back to plaintext, same as before, if the key isn't set) |
| Transport encryption | TLS terminated by Railway at the edge; `Strict-Transport-Security` + `Content-Security-Policy` headers verified by `tests/test_security_headers.py` |
| Audit trail | `activity_log` (actor/action/outcome) and `action_queue` (staged-action approval history with `decided_at`) — general-purpose, not a dedicated tamper-evident security-event log |
| Backups | `tools/backup_hub_db.py` exports non-secret state (explicitly excludes tokens/sessions/password hashes) to a committed JSON snapshot; no evidence of encrypted-at-rest *full* backups or a documented restore-test procedure |
| Incident response | Written procedure added 2026-07-18 (see `ops_runbook.md`'s "Incident Response" section) — covers credential leaks and suspected data exposure, the two incident types that have actually happened here before |

### What a real SOC 2 audit would additionally require (named, not silently missing)

- An accredited CPA firm engagement (this is not something engineering work
  can produce).
- Formal, versioned written policies (access control policy, change
  management policy, vendor management policy, etc.) — today these exist as
  code + comments + this document, not as separate governance artifacts an
  auditor would expect.
- Evidence of controls operating over an observation period (Type II) —
  logs/tickets/approvals showing the process was actually followed, not just
  that it exists.
- A named, accountable security officer role and employee security-awareness
  training records — not really applicable at solo-operator scale today, but
  an auditor would ask.
- Formal vendor risk assessments for sub-processors (Anthropic, OpenAI,
  Railway, Etsy, SMTP provider) — today these are just "used under their own
  terms of service," which is the practical norm for a business this size but
  not a formal SOC 2 vendor-management artifact.

---

## What this is NOT

This document and the accompanying code changes are an engineering-level
data-handling and security review, done by an AI coding assistant reading
and hardening the actual codebase — not a legal opinion, not a substitute
for professional legal or audit advice, and not a certification of anything.
Get a lawyer or a licensed auditor involved before relying on this document
for anything with real legal stakes (a regulator inquiry, an enterprise
customer's compliance questionnaire, an actual SOC 2 engagement).
