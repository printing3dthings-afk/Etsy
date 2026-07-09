Check the health of the OnBrandCraftz system and Frank's infrastructure.

Run the following checks and report findings clearly:

1. **Python compile check**: `python -m py_compile tools/api_server/main.py` — confirm no syntax errors
2. **Build ID**: grep for `_BUILD_ID` in `tools/api_server/main.py` to confirm current version
3. **Environment**: Check `.env` exists and required vars are set (ANTHROPIC_API_KEY, APP_SECRET_TOKEN, ETSY_ACCESS_TOKEN) — check presence only, never print values
4. **Etsy token freshness**: Look at `.env` for ETSY_ACCESS_TOKEN and ETSY_REFRESH_TOKEN — note if tokens appear to be set
5. **Recent ops log**: Read the last 20 lines of `data/knowledge_base/ops_runbook.md` to surface any recent incidents
6. **Untracked/uncommitted files**: Run `git status --short` to show pending changes
7. **Dependency health**: Check if `tools/browser_agent.py` imports cleanly with `python -c "from tools.browser_agent import get_page_text; print('ok')"`

Report as a clean summary: ✅ green for passing, ⚠️ amber for worth noting, ❌ red for broken. End with the single most important action item if any.
