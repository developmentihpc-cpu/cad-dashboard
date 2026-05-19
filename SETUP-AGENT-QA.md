# CAD Verification Agent — Setup Guide

This is the QA layer that sits over the dashboard. A user sends a request via
**email** or **Telegram**, the agent triggers the dashboard to export a country
PPT, fact-checks it against authoritative sources, fixes minor errors in place,
and replies with the verified `.pptx`. Major changes are routed for human
approval before being applied.

---

## What you're installing

Five new Python files, all in `Project Development/`:

| File | Role |
|---|---|
| `dashboard_export.py` | Headless browser that triggers `cd_exportCountryPPT()` |
| `ppt_factcheck.py` | Reads PPT → calls Claude → applies minor fixes |
| `verify_workflow.py` | End-to-end orchestrator (export → check → reply) |
| `telegram_bot.py` | Telegram polling bot |
| `SETUP-AGENT-QA.md` | This file |

Plus one folder created automatically: `agent_outputs/dashboard_exports/`,
`agent_outputs/pending_approvals/`.

---

## Step 1 — Install dependencies (one-time, ~3 min)

Open PowerShell in the `Project Development` folder (Shift+Right-click → "Open
PowerShell window here") and run:

```powershell
pip install playwright python-pptx anthropic
playwright install chromium
```

The `playwright install chromium` step downloads ~150 MB of Chromium binaries
that the agent uses headlessly to drive the dashboard. Only needs to be done
once per machine.

---

## Step 2 — Add your secrets to `.env`

Your existing `.env` already has `ANTHROPIC_API_KEY`, `GMAIL_SENDER`, and
`GMAIL_APP_PASSWORD` (used by the digest agent and pipeline). Add these new
keys at the bottom:

```bash
# Telegram bot
TELEGRAM_BOT_TOKEN=                # filled in Step 3 below
TELEGRAM_ALLOWED_CHATS=            # optional — comma-separated chat IDs
                                   # leave blank to allow anyone who finds the bot
```

---

## Step 3 — Create your Telegram bot (~5 min)

This is the part you asked about specifically. Step by step:

### 3a. Talk to @BotFather

1. Open Telegram (mobile or desktop)
2. In the search bar, type **`@BotFather`** and tap the verified one (blue check)
3. Tap **Start**
4. Send: **`/newbot`**
5. BotFather asks for a **name** (display name) — type something like
   `CAD Verification Agent`
6. BotFather asks for a **username** (must end in `bot`) — try
   `cad_verify_bot` or `ihpc_cad_bot` (it'll tell you if taken)
7. BotFather replies with a message that includes a **token** — looks like
   `7891234567:AAH-xVKlS3...`. **Copy this token now.**

### 3b. Paste the token into `.env`

Open `Project Development/.env`, find the `TELEGRAM_BOT_TOKEN=` line, and
paste the token after the `=`:

```bash
TELEGRAM_BOT_TOKEN=7891234567:AAH-xVKlS3y0Gkd-...
```

Save the file.

### 3c. Lock the bot to yourself only (recommended)

By default anyone who guesses your bot's username could send `/country` commands
and burn your Anthropic credits. To restrict:

1. In Telegram, search for **`@userinfobot`**, tap Start
2. It will reply with **Your ID:** followed by a number (e.g. `1234567890`)
3. Add this to `.env`:

```bash
TELEGRAM_ALLOWED_CHATS=1234567890
```

To allow multiple people, comma-separate: `1234567890,9876543210`.

### 3d. Start the bot

In PowerShell, from `Project Development`:

```powershell
python telegram_bot.py
```

You should see:

```
[telegram] Starting bot (polling every 3s) …
[telegram] Restricted to chats: {'1234567890'}
```

Leave this window open. It runs the bot.

### 3e. Test it

Back in Telegram:

1. Search for the username you chose in step 3a (e.g. `@cad_verify_bot`)
2. Tap **Start**
3. Send: `/help` — bot should reply with usage
4. Send: `/country Ethiopia` — bot should reply *"⏳ Verifying Ethiopia …"* and,
   1–2 minutes later, send back the verified `.pptx`

That's Telegram working end-to-end.

---

## Step 4 — Test the email path (separate from Telegram)

The email watcher is part of the existing `agents_pipeline.py`. You don't need
to start anything new — your existing `start_watch.bat` already runs it. To
trigger a verification by email, send to `developmentihpc@gmail.com`:

```
Subject: RUN: Ethiopia / verify
```

Body can be empty, or you can specify sectors:

```
Subject: RUN: Ethiopia / Health & Nutrition / verify
```

Within 5–10 minutes the agent replies with the verified PPT attached.

> **Note**: for the email watcher to recognise the new `verify` workflow, you
> may need to add a route in `agents_pipeline.py`. Currently it routes
> `needs / proposal / external`. If `RUN: ... / verify` doesn't trigger, tell
> me and I'll patch the trigger parser.

---

## Step 5 — How the approval flow works

**Telegram path: no approval prompts.** All fact-check fixes (minor and major)
auto-apply. The bot always sends back the fully-corrected PPT. The summary
message tells you what was changed.

**Email path: approval still required for major changes.** When the fact-checker
finds a major change (a flipped sector status, a rewritten paragraph, a changed
recommendation, or anything affecting >3 slides), the agent emails the proposed
change with a unique approval ID (e.g. `20260514-1622-ETHIO`) and waits for
your reply.

To approve via email: reply with subject `APPROVE-<id>`.
To reject: reply with subject `REJECT-<id>`.

Pending approvals are stored in `agent_outputs/pending_approvals/` until you
respond.

---

## Step 6 — Daily usage

Once everything's set up, your typical day looks like:

**Telegram path (fastest):**
```
You:    /country Ethiopia
Bot:    ⏳ Working on Ethiopia (All sectors) — this takes ~1–2 minutes …
Bot:    [PPT attachment]
        ✓ Ethiopia verified
        3 fix(es) applied
```

**Email path (more formal, paper trail):**
```
You:    Subject: RUN: Ethiopia / verify
Agent:  Subject: VERIFIED · Ethiopia country profile
        [PPT attached] [HTML summary]
```

---

## Troubleshooting

**Bot doesn't respond at all**
- Make sure `python telegram_bot.py` is still running in your PowerShell window
- Check the token is correct in `.env` (no quotes, no spaces)
- If you set `TELEGRAM_ALLOWED_CHATS`, make sure your chat ID is in the list

**"Could not export Ethiopia from dashboard"**
- The country name must match exactly what's in the dashboard's `COUNTRY_LATLNG`
  registry. Check `index.html` for the exact spelling (e.g. "South Sudan", not "S Sudan")
- If the dashboard recently changed, the headless browser may not find the
  Export button — check `dashboard_export.py` console output

**Playwright errors about Chromium**
- Re-run `playwright install chromium`
- If on a corporate network, you may need a proxy: `set HTTPS_PROXY=...`

**Fact-checker keeps flagging things that aren't wrong**
- The Claude prompt is in `ppt_factcheck.py` (`FACTCHECK_SYSTEM` constant) —
  edit it to be more conservative, then test with `python ppt_factcheck.py
  <pptx-path> Ethiopia`

**Need to make telegram_bot run on startup automatically**
- Create a shortcut to `python telegram_bot.py` and put it in
  `shell:startup` (Windows + R → `shell:startup`)

---

## What this doesn't do (yet)

- Run when your laptop is off (Fly.io deploy is paused)
- Auto-export from dashboard on a schedule (currently only on-demand via agent)
- Routing to other workflows (only `verify` is wired; `program design` and
  `program assessment` are roadmap)
- Approve/reject from inside the email itself (currently requires a reply email)

---

## Files & where things go

```
Project Development/
├── dashboard_export.py              # headless browser export
├── ppt_factcheck.py                 # Claude fact-check + auto-fix
├── verify_workflow.py               # orchestrator
├── telegram_bot.py                  # Telegram polling bot
├── SETUP-AGENT-QA.md                # this file
├── .env                             # all secrets (not in git!)
├── agent_outputs/
│   ├── dashboard_exports/           # raw exports from dashboard
│   ├── pending_approvals/           # major-change approval queue
│   └── *_verified.pptx              # verified outputs (auto-fixed)
│   └── *_approved.pptx              # final outputs after major-change approval
```
