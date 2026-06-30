Run a pre-deploy readiness check on the OnBrandCraftz Frank codebase.

Check each of the following and report pass/fail:

1. **Python syntax**: `python -m py_compile tools/api_server/main.py tools/api_server/business_config.py tools/browser_agent.py` — must pass with no output
2. **Build ID**: Print the current `_BUILD_ID` from `tools/api_server/main.py`
3. **Required env vars**: Check `.env` for presence (not values) of: ANTHROPIC_API_KEY, APP_SECRET_TOKEN, ETSY_CLIENT_ID, ETSY_CLIENT_SECRET, ETSY_ACCESS_TOKEN, ETSY_REFRESH_TOKEN, OPENAI_API_KEY
4. **Git status**: Run `git status --short` — list any untracked or modified files that would NOT be deployed
5. **Branch check**: Run `git branch --show-current` — confirm we're on the right feature branch
6. **Secrets scan**: Run `grep -r "sk-ant-api\|sk-proj-\|ETSY_CLIENT_SECRET=" .env 2>/dev/null | wc -l` to count secrets in `.env` (should be >0, meaning they're set) — this is checking presence, not printing values
7. **Browser agent import**: `python -c "from tools.browser_agent import get_page_text, search_etsy; print('ok')"` — must print "ok"
8. **Log tail**: Show last 5 lines of `data/knowledge_base/ops_runbook.md` for recent incident awareness

Output format:
✅ PASS / ❌ FAIL / ⚠️ WARN for each check, then a final verdict: READY TO DEPLOY or ISSUES FOUND.
