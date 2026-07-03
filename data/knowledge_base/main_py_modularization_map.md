# main.py Modularization Map (graphify-derived, 2026-07-03)

`tools/api_server/main.py` is ~7,135 lines and the single biggest hub in the codebase.
This is the **map** for splitting it safely — NOT the refactor itself (that's a large,
regression-prone change to do deliberately, gated behind the CI smoke + quality-gate tests).

## How this was produced
`graphify` (Tree-sitter, fully offline — no LLM/API cost) over the whole `tools/` tree:
2,157 nodes · 4,232 edges · 142 communities, built from commit `aea4a2b`. Regenerate any
time with `graphify update .` (see ops_runbook for install). The interactive `graph.html`
was handed to Scott separately; it is intentionally NOT committed (≈1.8 MB generated file).

## What graphify found inside main.py
main.py does not cluster as one thing — it splits into three low-cohesion communities
(cohesion 0.03–0.08, i.e. these groups barely reference each other = good seam lines):

| graphify community | ~size | What it is | Proposed module |
|---|---|---|---|
| Community 0 "main.py" | 55 nodes | FastAPI **route handlers** — `credentials_status`, `get_account_endpoint`, `get_agents_status`, `get_allowed_folders`, `get_conversation_detail`, `_agents_status_snapshot`, … | `routes/` (split by area: account, agents, system, listings) |
| Community 1 "_execute_agent_tool" | 61 nodes | The **agent-tool layer** — `_execute_agent_tool` dispatcher + tool impls (`autofix_draft`, `autofix_tags`, `autofix_title`, `batch_stage_tags`, `_check_no_pale_background`, …) | `agent_tools/` (dispatcher + grouped tool modules) |
| Community 6 "Request" | 42 nodes | **Admin / auth / HUD** — `admin_create_user`, `admin_delete_user`, `admin_list_users`, `admin_reset_password`, `render_frank_hud`, business-identity config | `admin.py` + `hud.py` |

## Recommended split order (lowest risk first)
1. **`agent_tools/`** — the 61-node tool layer is the most self-contained (it already funnels
   through one dispatcher `_execute_agent_tool`). Extract the dispatcher + `AGENT_TOOLS` schema
   list + tool bodies into a package; main.py imports it. The CI smoke test already asserts the
   tool registry, so a regression here fails fast.
2. **`admin.py` + `hud.py`** — admin/user endpoints + HUD rendering are cleanly separable.
3. **`routes/`** — split the remaining route handlers by area last (they touch the most shared
   app/DB state, so do them once 1–2 have shrunk the file).

## Guardrails for the refactor (when it happens)
- One community per commit; run `python tests/smoke_test.py` + `python tests/test_quality_gates.py`
  after each (both already wired into CI).
- Keep the sibling-`tools/` bare-import convention (`sys.path.insert(0, ROOT/"tools")`, main.py:43).
- Archive any removed block via `tools/trash.py` before deleting (hard rule).
- Bump `_BUILD_ID` per shipped step; ops_runbook entry.

## Honest status
This is a planning artifact, not executed work. The modularization is worth doing (a 7k-line
file is hard to navigate and risky to edit), but it is deliberate surgery, not a quick win —
do it as its own focused effort, not interleaved with feature work.
