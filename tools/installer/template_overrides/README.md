# {{BUSINESS_NAME}} — Etsy Automation Hub

A self-hosted CEO agent ("{{AGENT_NAME}}") that runs your own Etsy shop's
automation: listing creation, order management, AI art generation, social
posting, customer-service Quick Replies, and a mobile/web dashboard you chat
with directly. This is a single-tenant template — running it stands up your
own independent instance with its own `.env`, database, and data. It is not
a hosted multi-tenant service.

This package was built from a working reference instance (OnBrandCraftz)
via `tools/installer/package_template.py`, which stripped that shop's
proprietary product catalog, brand assets, and business data, leaving the
reusable framework (agents, tools, API server, mobile/web app) plus generic
doctrine in `CLAUDE.md` and `data/knowledge_base/`. Sections marked
`<fill in>` in `CLAUDE.md` need your business's specifics before the agent
will give you grounded answers about your own catalog and standards.

## Quick Start (local)

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the setup wizard — creates `.env` from `.env.example`, prompts for
   your Anthropic API key, business identity, and any optional integrations
   (Etsy, OpenAI, email delivery, Pinterest, Canva, Instagram/Facebook):
   ```
   python tools/installer/setup_wizard.py
   ```
3. Start the server:
   ```
   uvicorn tools.api_server.main:app --reload
   ```
4. Open the printed local URL and log in with the dashboard token shown in
   `.env` under `APP_SECRET_TOKEN`.
5. Edit `CLAUDE.md` and replace the `<fill in>` sections with your own
   store name, product catalog, and operating standards — {{AGENT_NAME}}
   reads this file fresh on every chat to ground its answers.

You can re-run `python tools/installer/setup_wizard.py` at any time to add
an integration you skipped, or edit `.env` directly.

## Deploying to Railway

This repo ships with a `Dockerfile` and `railway.toml` already configured
— Railway auto-detects both, no build configuration needed.

**Manual deploy (works immediately, no published template required):**
1. Push this repo to your own GitHub account.
2. In Railway: New Project → Deploy from GitHub repo → select your repo.
3. Railway detects the `Dockerfile` + `railway.toml` and builds automatically.
4. Add your environment variables under the service's Variables tab — copy
   them from the `.env` you generated locally with the setup wizard (or run
   the wizard, then paste each `KEY=value` line in).
5. Deploy. Check `/health` once it's live.

**One-click deploy button** (optional, requires you to first publish your
own Railway Template from this repo — see
[Railway's publish-a-template docs](https://docs.railway.com/templates/publish-and-share)):
```
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new/template/<TEMPLATE_CODE>?utm_medium=integration&utm_source=button&utm_campaign=generic)
```
Replace `<TEMPLATE_CODE>` with the code Railway assigns when you publish
your template — there is no default/shared code, since this is a
single-tenant instance and not a hosted service.

## What's Included

- `tools/api_server/` — FastAPI backend + CEO agent (chat, tool-calling,
  dashboard API)
- `tools/` — Etsy/OpenAI/Pinterest/Canva/Instagram/Facebook integrations,
  OAuth helper scripts, image/print-file generation pipelines
- `agents/`, `town_app/`, `web/`, `mobile_app/` — the reusable automation
  framework and front-ends
- `CLAUDE.md` — your business doctrine (quality gates, catalog, standards)
  — `<fill in>` sections are yours to complete
- `data/knowledge_base/` — the agent's persistent operational log/learnings
  (starts empty for a new instance)

## Support

This is a self-hosted template with no managed support channel — you're
running your own instance. See each tool's docstring in `tools/` for setup
details on individual integrations (Etsy, Canva, Pinterest, Instagram,
Facebook).
