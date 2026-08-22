---
name: verify-etsy-mutations
description: "After any staged Etsy action executes (price, title, tags, description, state, photo), independently re-check the real live value on Etsy before reporting success — Frank's own 'executed' status is not proof the mutation actually took effect."
---

# Verify Etsy Mutations — "Executed" Is Not "Happened"

## Why this exists (2026-08-20 incident)

Scott approved a blanket price change across 82 listings (71 wall-art to
$4.99, 11 coloring-pages to $1.99), staged and executed through Frank's
normal `stage_batch_price_update` → Action Center → `approve_action` path.
All 82 actions recorded `status: "executed"` with zero errors. Scott was
told it was done.

It wasn't. Independently re-checking the real live price on Etsy (via the
public `GET /v3/application/listings/{id}` endpoint, not Frank's own
queue) found only 11 of 82 had actually changed. Etsy had accepted every
PATCH request with a 200 response and silently no-op'd the price field on
71 of them — a real, confirmed platform behavior, not a Frank bug in the
retry/error-handling layer. A full re-stage-and-re-approve retry of the
71 failed identically the second time, which is what proved this wasn't a
transient blip.

**The only reason this was caught**: a direct, independent re-check
against Etsy's own data, done specifically because "it says executed"
felt worth confirming rather than trusting outright — not because
anything in Frank's own reporting raised a flag. Nothing did. That's the
gap this skill closes.

## The rule

**A staged action's `status: "executed"` means the HTTP call to Etsy
returned success. It does not mean Etsy's stored data actually changed.**
These are different claims, and Etsy's API does not always make them
true together. Before telling Scott a mutation is done — especially
`update_price`, and especially anything staged as a multi-listing batch —
independently re-fetch the real current value and confirm it matches
what was requested. Do not infer success from the queue status alone.

## How to actually verify

For **price, title, tags, state** — the fields visible on Etsy's public,
unauthenticated listing endpoint — the most reliable check is Etsy's own
API directly, not Frank's cached view of it:

```
GET https://api.etsy.com/v3/application/listings/{listing_id}
Header: x-api-key: {ETSY_CLIENT_ID}:{ETSY_CLIENT_SECRET}
```

This needs no OAuth access token at all (a real, deliberate advantage —
see CLAUDE.md's "Direct Infrastructure Access" section on fetching
Railway env vars for a legitimate task), so there's no risk of touching
Frank's live refresh-token state just to read a listing back. Compare the
returned `price.amount / price.divisor` (or `title`, `tags`, `state`)
against what was requested. For a batch, check every listing in the
batch — not a sample, since this incident showed pass/fail can vary
listing-by-listing within the same batch for reasons that aren't visible
on any field the endpoint exposes.

For **description, photos** — same idea, but Frank's own
`GET /api/listings/{listing_id}/raw` endpoint is the equivalent
authenticated check (it fetches live from Etsy on every call, no
caching) since these fields aren't reliably comparable via the plain
public endpoint's response shape.

## Scope — which action types need this most

- `update_price` / `stage_batch_price_update` — **confirmed unreliable**,
  always verify. If a fix has been deployed for the field(s) suspected of
  causing this, test it on one listing and verify before trusting it on
  a batch again — this incident's first attempted fix (sending `quantity`
  alongside `price`) also failed identically on re-verification, so
  "I found a plausible cause and shipped a fix" is not itself proof.
- `update_title`, `update_tags`, `update_description` — no evidence of
  the same failure mode so far, but the check is cheap; do it anyway for
  anything the shop's actual revenue or discoverability depends on.
- `listing_photo` — verify by re-fetching `GET .../images` and checking
  the expected file actually landed at the expected rank, not just that
  the staged action executed.
- `toggle_listing_state` / `publish_listing` / `deactivate_listing` — the
  `state` field is on the same public endpoint; cheap to verify, do it.

## When a mismatch is found

1. **Stop.** Don't re-stage a blind retry across the whole batch again —
   that's exactly what happened here and it failed identically. Isolate
   to one listing, form a real hypothesis grounded in a genuine
   difference between listings that worked and ones that didn't, and
   test that hypothesis on one listing before scaling back up.
2. **Say so, plainly.** Tell Scott the real state — not "it's executing"
   or "should be done" — the actual verified number of successes versus
   failures, and that you're investigating, before he acts on the
   assumption it's finished.
3. **Check `/api/system/dependencies`** for the `etsy_api` circuit
   breaker state before making a large volume of further verification
   calls in a short window — enough rapid calls (including your own
   re-checks) can trip it, which then blocks *everything* until its
   cooldown elapses, compounding the delay.
