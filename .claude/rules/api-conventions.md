# API conventions — `tools/api_server/main.py`

## Route handlers stay thin; blocking work goes off the event loop

A route handler is a short `async def` wrapper. Actual filesystem/subprocess/
heavy-compute work lives in a plain (non-async) function, usually suffixed
`_sync()` or nested as a closure named `_scan()`/`_fetch()`, and is invoked
via `await asyncio.to_thread(...)`. See `list_files()` → its inner `_scan()`,
`get_metrics()` → `_fetch()`. Never do a real `rglob()`/subprocess call
directly inside an `async def` route body — it blocks the whole
single-process server for every other request while it runs.

## Auth dependency picks the right strictness

- `_auth_session_or_bearer` — read-only/browse endpoints (session cookie
  or bearer token either way).
- `_rate_limited_auth` — anything that mutates state or costs money/API
  quota (writes, staged actions, AI generation calls).
Match the existing pattern on a neighboring endpoint of the same shape
rather than picking one from habit.

## Caching

Module-level `_cache` dict + `_cache_lock`, accessed via `_cache_get(key,
ttl)` / `_cache_set(key, value)`. TTLs are chosen per endpoint's real
staleness tolerance (30s for `/api/listings`, up to 3600s for `/api/shop-
sections`) — don't default to a single global TTL constant. When a cached
value can go stale-but-still-useful on a real failure (e.g. Etsy API
outage), serve the last-known-good value rather than blanking the UI —
see `_shop_sections_sync()`'s comment on why re-caching a transient
failure for the full TTL was a real bug.

## Durable state never touches a git-tracked file at runtime

`data/product_catalog.json`, `data/listing_manifest.json`, etc. are
git-tracked and this server **never writes them** — a raw write would
vanish on the next Railway redeploy (fresh git checkout) and drift from
git history. Anything that needs to persist a runtime change (a new
`etsy_listing_id`, a freshly-registered product, uploaded reference
images) goes through the volume-or-local sidecar pattern: check
`"volume" in _FILE_ROOTS` and write to `_FILE_ROOTS["volume"] / "<name>.
json"` when mounted, else `ROOT / "data" / "<name>.json"` for local dev.
See `_PRODUCT_CATALOG_OVERRIDES_PATH`, `_REFERENCE_IMAGES_META_PATH` for
the exact pattern to copy — every new durable sidecar should look like
these, not invent a new convention.

## Nothing irreversible auto-executes

Any action that touches a real Etsy listing, spends money, or can't be
trivially undone gets staged via `db.enqueue_action(type, summary,
payload)` into the Action Center for Scott's one-tap approve/reject —
never executed directly from a chat tool or background loop. This
includes republishing, deactivating, price changes, and title/tag
rewrites. A background script (`listing_compliance_sweep.py`, health
loops) may stage actions and add todos on its own; it must never call the
actual mutating Etsy API method itself.

## File resolution: reuse the catalog helpers, don't re-derive

`product_catalog.json`'s `"files"` entries use three different path
conventions (see `_catalog_file_abs_path()`'s docstring for the full
history). Always resolve a catalog file path through `_catalog_file_
exists()` / `_catalog_file_abs_path()` / `_catalog_file_url()` — never
re-implement a "does this file exist" check by hand, it will silently
regress one of the three conventions.

## Error responses

Wrap every external call (`EtsyAPIClient`, Anthropic, subprocess) in
try/except and raise `HTTPException(status_code=..., detail=<specific,
actionable text>)` — never a bare exception that becomes a generic 500.
For a genuinely transient failure worth a smart retry hint, use
`_classify_known_failure()`'s pattern of mapping a known error signature
to a specific remediation string (which env var, which console) instead
of a generic "check your connection."
