# Code style — OnBrandCraftz / Frank

Distilled from this codebase's actual conventions (not a generic style
guide) — grep the referenced files for live examples before deviating.

## Comments: WHY, never WHAT

Default to no comments. A well-named function/variable already says what
the code does. Only write a comment when it captures something the code
itself can't: a hidden constraint, a non-obvious invariant, a workaround
for a specific bug, or a decision that would look wrong without context.

This codebase leans hard on **dated root-cause comments** at the exact
place a bug was fixed — not a changelog, a landmine warning for the next
person who touches that line. Real examples: `main.py`'s `_catalog_file_
exists()` docstring explains the three incompatible path conventions in
`product_catalog.json` and *why* a basename index was the only reliable
fix; `_scan()` in `list_files()` explains *why* `.log` files are skipped
(Scott's explicit call, not an assumption). Follow this pattern: when you
fix something non-obvious, leave one comment at the fix site dated and
explaining the failure mode, not a paragraph of narration.

Never comment WHAT ("loop through files", "check if empty") — the code
already says that. Never reference the current task/ticket/PR in a
comment — it belongs in the commit message, not the file (comments rot;
git history doesn't).

## Naming

- Private/internal functions and constants: leading underscore
  (`_catalog_file_exists`, `_FILE_ROOTS`, `_BUILD_ID`).
- Module-level config dicts/maps: `_SCREAMING_SNAKE` or `_CamelCase`
  matching what they hold (`_CATEGORY_LABELS`, `_UNMATCHED_PREFIX_
  CATEGORY`).
- A `_sync()` suffix marks a function that does blocking I/O and is meant
  to be run via `asyncio.to_thread()` from an async route handler — see
  `_listings_sync()`, `_scan()` inside `list_files()`.
- JS mirrors this: `_camelCase` for internal helpers, `_SCREAMING_SNAKE`
  for constant maps (`_CATEGORY_LABELS`, `_REFIMG_CATEGORY_LABELS` in
  `frank_hud_mockup.py`).

## No premature abstraction

Three similar lines beat a speculative helper function. Don't build a
generic system for a need that has exactly one caller today. When a
second near-identical case actually shows up, extract the shared helper
then — see `_product_status_row()`, pulled out of `_build_products_
status()`'s loop body specifically because a second caller (`is_new_
product` overlay rows) needed the exact same per-entry logic, not
speculatively.

## Reuse before you write

Before adding new resolution/lookup logic, check whether it already
exists under a different name. Concrete example from this codebase: the
Files-tab attachment fix (`_build_file_owner_index()`) doesn't re-derive
"is this product real/attached" — it calls `_build_products_status()`,
the exact function `/api/products` already uses, so the Files and
Products screens can never disagree. When you're about to write a second
implementation of something, that's the signal to go find the first one.

## No backwards-compatibility scaffolding

No `_deprecated` aliases, no `# TODO: remove after migration` shims, no
re-exporting a renamed thing "just in case." If something is unused,
delete it — this repo has a real recycle bin for that
(`tools/trash.py` → `data/trash/`, see the CLAUDE.md automation-stack
entry), so nothing deleted is actually unrecoverable. Don't invent your
own compatibility layer when the trash vault already solves "what if we
need it back."

## Errors: never a bare 500, never a silent swallow

Every external call (Etsy, Anthropic, filesystem) that can fail gets
wrapped and turned into either a clear `HTTPException` with an actionable
`detail` message, or an honest `{"error": ...}` return the caller can
branch on — see `_fetch_listing_for_autofix()`, `_autofix_tags_core()`.
Never let an exception surface as a bare stack trace to the dashboard,
and never catch-and-ignore an error that changes what gets reported as
true (see `listing_compliance_sweep.py`'s `fetch_error` field — a fetch
failure is deliberately never conflated with "checked it and it's
broken").
