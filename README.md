# CAD Platform

Country Assessment Dashboard + AI verification agent.
Single repo, fully cloud-hosted, no local install required.

## Architecture

```
This repo
├── docs/                              ← GitHub Pages serves this
│   ├── index.html                     (the dashboard, public read-only view)
│   ├── logo.png
│   └── somaliland-flag.svg
│
├── agents_pipeline.py                 ← agent code (Python)
├── dashboard_export.py                  runs on Fly.io
├── ppt_factcheck.py                     in a 24/7 container
├── verify_workflow.py
├── telegram_bot.py
│
├── Dockerfile                         ← Fly.io build instructions
├── fly.toml
├── requirements.txt
├── entrypoint.sh
├── pipeline-state.json                ← live pipeline data (versioned!)
│
└── .github/workflows/deploy.yml       ← auto-deploys to Fly on every push

   ↓ deployed to:
- {github-username}.github.io/{repo-name}    ← public dashboard (Pages)
- cad-agent.fly.dev                          ← agent container (Fly.io)
```

## Daily use

| Want to… | Do this |
|---|---|
| Generate a country PPT | Send `/country Ethiopia` to your Telegram bot |
| Trigger via email | Send `RUN: Ethiopia / verify` to `developmentihpc@gmail.com` |
| Update pipeline data | Edit `pipeline-state.json` in GitHub web UI → commit → done |
| Update dashboard | Edit `docs/index.html` in GitHub web UI → commit → Pages auto-deploys |
| Update agent logic | Edit `*.py` in GitHub web UI → commit → GitHub Actions auto-deploys to Fly |
| Check agent logs | `fly logs` from any terminal, or open Fly.io web dashboard |

## Initial deploy

See `SETUP-FLY-DEPLOY.md` for the one-time setup. After that, no local steps
are required — every change deploys via GitHub.

## Required secrets

In Fly.io (`fly secrets set …`):
- `ANTHROPIC_API_KEY`
- `GMAIL_SENDER`, `GMAIL_APP_PASSWORD`, `DIGEST_RECIPIENT`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHATS`
- `DASHBOARD_URL` (your Pages URL, with trailing slash)

In GitHub (Settings → Secrets → Actions):
- `FLY_API_TOKEN` (generate at fly.io → Tokens)

## Stack

- **Dashboard**: vanilla HTML/JS, Leaflet, pptxgenjs (browser-side)
- **Agent runtime**: Python 3, Playwright (headless Chromium), python-pptx, anthropic SDK
- **Hosting**: GitHub Pages (dashboard) + Fly.io (agent container)
- **CI/CD**: GitHub Actions
