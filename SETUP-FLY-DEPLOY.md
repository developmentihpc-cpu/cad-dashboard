# Deploying the CAD Agent to Fly.io

This puts the Telegram bot + email watcher in the cloud so they keep running
when your laptop is off.

**Architecture:** GitHub holds the code, Fly.io runs the container, your
existing dashboard (on GitHub Pages or local file) provides the data.

**Total time:** ~30 min once you have GitHub and a credit card ready.

---

## What gets deployed

The container runs **two processes side by side** in one Fly.io machine:

1. `telegram_bot.py` — polls Telegram for `/country <Country>` commands
2. `agents_pipeline.py --watch` — polls Gmail IMAP for `RUN: ...` triggers

Both use the same `dashboard_export.py` + `ppt_factcheck.py` modules under the
hood and reply via the same channels they came in on.

---

## Step 1 — Create a GitHub repo for the agent code (~5 min)

This is **a different repo** from `cad-dashboard` (the dashboard one). Keeps
private agent code separate from the public Pages site.

1. Go to [github.com](https://github.com) → **+ New repository**
2. Name: `cad-agent` (or whatever)
3. **Private** is fine here — the agent code can stay private
4. **Do not** initialise with README / .gitignore / license — leave empty
5. Click **Create repository**

GitHub will show you a quick-setup page. Keep that tab open; you'll need the
URL in step 3.

---

## Step 2 — Verify your local files are ready

Open `Project Development` and confirm these files exist:

**Will be pushed to GitHub & deployed:**
- `agents_pipeline.py`
- `dashboard_export.py`
- `ppt_factcheck.py`
- `verify_workflow.py`
- `telegram_bot.py`
- `index.html`, `logo.png`, `somaliland-flag.svg` (dashboard fallback)
- `Dockerfile`, `fly.toml`, `requirements.txt`, `entrypoint.sh`
- `.dockerignore`, `.gitignore`

**Stays local (excluded by `.gitignore`):**
- `.env` (your secrets)
- `pipeline-state.json` (your data)
- `agent_outputs/` (your outputs)
- All `*.bat` files, all `SETUP-*.md`, etc.

You don't need to touch any of these — `.gitignore` handles the exclusions.

---

## Step 3 — Push the code to GitHub

The easiest way without learning git: install **GitHub Desktop** (5 min):

1. Download from [desktop.github.com](https://desktop.github.com)
2. Install, sign in with your GitHub account
3. **File → Add local repository** → browse to `C:\Users\USER\Desktop\Project Development`
4. It'll say "this isn't a git repo, want to create one?" → **Create a repository**
5. In the dialog, name it `cad-agent`, leave the description blank, click **Create repository**
6. **File → Publish repository** → make sure "Keep this code private" is checked → **Publish repository**

GitHub Desktop pushes everything that's not in `.gitignore` to your new repo.

---

## Step 4 — Sign up for Fly.io (~3 min)

1. Go to [fly.io](https://fly.io) → **Sign up**
2. Use GitHub to sign in (or email; either's fine)
3. They'll ask for a credit card — **for verification only**. Fly gives you ~$5/month free credit. This workload should fit inside that, but expect maybe $1–3/month overage if you process many requests.

---

## Step 5 — Install the Fly CLI (~2 min)

In **PowerShell** (no need to be in any specific folder):

```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

Close and reopen PowerShell so the new PATH takes effect, then check:

```powershell
fly version
```

Should print something like `fly v0.3.x`. Then sign in:

```powershell
fly auth login
```

A browser will open — click Continue.

---

## Step 6 — Create the Fly app (~2 min)

In PowerShell, navigate to the project folder:

```powershell
cd "C:\Users\USER\Desktop\Project Development"
```

Then create the app **(do not let it generate a new fly.toml — we already have one)**:

```powershell
fly apps create cad-agent
```

If `cad-agent` is taken globally, try `cad-agent-yourname` and update `app =`
in `fly.toml` to match.

---

## Step 7 — Set your secrets (~3 min)

These are the same values as your local `.env`. Fly stores them encrypted and
exposes them as env vars to the container:

```powershell
fly secrets set ANTHROPIC_API_KEY="sk-ant-api03-…" `
                GMAIL_SENDER="developmentihpc@gmail.com" `
                GMAIL_APP_PASSWORD="sfpt gcfe psot stgw" `
                DIGEST_RECIPIENT="developmentihpc@gmail.com" `
                TELEGRAM_BOT_TOKEN="7891234567:AAH-xVKlS3y0Gkd-…" `
                TELEGRAM_ALLOWED_CHATS="1234567890" `
                DASHBOARD_URL="https://yourname.github.io/cad-dashboard/"
```

(The backticks `` ` `` are PowerShell line continuations.)

Replace each value with what's in your `.env`. The `DASHBOARD_URL` should be
your GitHub Pages URL from earlier, with the trailing slash.

Verify:

```powershell
fly secrets list
```

Should show all 7 names (values are hidden).

---

## Step 8 — Deploy (~5 min for first build)

```powershell
fly deploy
```

You'll see Fly building the Docker image (downloads Playwright base, installs
Python packages — first build is slow, ~5 min, subsequent builds are <1 min).
Then it starts the container.

When deploy finishes, check that it's running:

```powershell
fly status
fly logs
```

In the logs you should see:

```
[entrypoint] Starting CAD agent — 2026-05-14 ...
[entrypoint] DASHBOARD_URL = https://yourname.github.io/cad-dashboard/
[entrypoint] telegram_bot.py running (PID 7)
[entrypoint] agents_pipeline.py --watch running (PID 8)
[telegram] [telegram] Starting bot (polling every 3s) …
[email]    Starting watch mode (poll every 300s)…
```

---

## Step 9 — Test from your phone

You can now **shut down your laptop entirely**. From your phone's Telegram:

```
/country Ethiopia
```

Should reply:
```
⏳ Working on Ethiopia (All sectors) — this takes ~1–2 minutes …
```

…then deliver the verified PPT.

If you don't see a reply in 3 minutes, check the logs from any device:
```powershell
fly logs
```

---

## Updating the agent later

When you change a `.py` file locally and want it deployed:

1. Open GitHub Desktop, write a commit message, click **Commit to main**
2. Click **Push origin**
3. In PowerShell: `fly deploy`

That's it. Fly rebuilds and rolls out in ~1 minute.

---

## Costs (transparency)

Fly.io's pricing per month:
- shared-cpu-1x with 1 GB RAM, always on: ~$2–3
- Outbound bandwidth (PPT replies, ~250 KB each): negligible
- Image storage: free

**You get ~$5/month free credit**, so for typical usage this stays free. If
you start processing 50+ countries/day, expect ~$3–5/month overage.

To check usage:  `fly billing` or visit dashboard → billing.

---

## Troubleshooting

**`fly` command not found after install**
- Close PowerShell completely and reopen. The installer adds Fly to PATH but
  existing windows don't see it.

**Build error about Chromium / Playwright version mismatch**
- The Dockerfile pins to `playwright/python:v1.46.0-jammy`. If `requirements.txt`
  installs a newer Playwright, they may mismatch. Lock the version:
  `playwright==1.46.0` in requirements.txt.

**Telegram bot doesn't respond after deploy**
- Check `fly logs` — make sure it shows `Starting bot (polling every 3s)`
- Check secrets: `fly secrets list` — `TELEGRAM_BOT_TOKEN` must be present
- If you set `TELEGRAM_ALLOWED_CHATS`, your chat ID must be in the list

**Email watcher doesn't trigger**
- `agents_pipeline.py --watch` polls every 5 min. Wait ≥5 min after sending the email
- Check `fly logs` for `[email]    [INFO] Connected to IMAP`
- Verify `GMAIL_APP_PASSWORD` is the **app password**, not your regular password

**Container keeps restarting**
- `fly logs` will show why. Most common: a missing secret. Set it with
  `fly secrets set KEY="value"` and Fly auto-redeploys.

**"Out of memory" errors when generating PPT**
- Bump memory in `fly.toml`:  `memory = "2gb"` then `fly deploy`. Costs slightly more.

---

## Stopping it / removing it

Pause (no charges):  `fly scale count 0`
Resume:  `fly scale count 1`
Delete entirely:  `fly apps destroy cad-agent`

Your local laptop setup keeps working independently — the cloud version doesn't
replace it, just adds always-on capability.
