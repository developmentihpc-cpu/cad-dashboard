# Hosting the Dashboard on GitHub Pages

This frees the agent from needing the dashboard files on the local disk. Once
done, the agent can run from anywhere with internet (your laptop, Fly.io, a
Raspberry Pi) and reach the dashboard at a public URL.

---

## What gets uploaded

Three files only — the ones your dashboard actually needs to render:

```
index.html
logo.png
somaliland-flag.svg
```

Nothing else. **Do not push** `.env`, `pipeline-state.json`, `agent_outputs/`,
the Python files, or the `make-pptx.bat`. Those stay local.

---

## Step 1 — Create a GitHub account (skip if you have one)

Go to [github.com](https://github.com) → Sign up. Free.

---

## Step 2 — Create a new repository

1. Click **+ → New repository** (top right)
2. Repository name: `cad-dashboard` (or whatever you like)
3. **Public** (free Pages requires public; Pro plan unlocks private Pages for $4/mo)
4. **Skip** the "Add README", "Add .gitignore", "Choose a license" options — leave them all unchecked
5. Click **Create repository**

---

## Step 3 — Upload the dashboard files

Easiest path (no git knowledge needed):

1. On the empty repo page, click the **uploading an existing file** link
2. Drag `index.html`, `logo.png`, and `somaliland-flag.svg` from your
   `Project Development` folder into the upload area
3. Scroll down, type a commit message like `initial dashboard upload`
4. Click **Commit changes**

---

## Step 4 — Enable GitHub Pages

1. In your repo, click **Settings** (top right of repo, not your account settings)
2. Left sidebar → **Pages**
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **main** / folder: **/ (root)**
4. Click **Save**

GitHub will say *"Your site is live at https://yourname.github.io/cad-dashboard/"*
within 30–60 seconds. Bookmark this URL.

---

## Step 5 — Tell the agent to use the Pages URL

Open `Project Development/.env` and add this line at the bottom:

```bash
DASHBOARD_URL=https://yourname.github.io/cad-dashboard/
```

Replace `yourname` with your actual GitHub username.

Save. Restart the bot:

```powershell
cd "C:\Users\USER\Desktop\Project Development"
python telegram_bot.py
```

Now when you send `/country Chad` to the bot, the headless browser loads the
dashboard from the GitHub Pages URL instead of `file:///.../index.html`. You
can verify in the bot's PowerShell window — the first log line of each export
will say:

```
[export] Loading https://yourname.github.io/cad-dashboard/
```

---

## Updating the dashboard later

When you make a change to `index.html` locally and want it reflected on Pages:

1. Go back to the repo on GitHub
2. Click on `index.html` → pencil icon (Edit)
3. Paste your new content (or use the upload-files trick to replace it)
4. Commit

OR install [GitHub Desktop](https://desktop.github.com) (one-time, 5 min) which
lets you push changes with two clicks instead of using the web UI.

Pages picks up the change in ~30 seconds.

---

## Privacy note

GitHub Pages on the free plan is **public**. The dashboard URL is technically
guessable, and the Google bot will eventually index it.

What's exposed:
- The country pipeline data hardcoded in `index.html` (project names, costs,
  countries, sectors)
- The dashboard's UI and source code
- World Bank indicators (these are public anyway)

What's **not** exposed:
- `pipeline-state.json` (lives only on your machine)
- The agent's outputs (`agent_outputs/`)
- Your Anthropic key, Gmail password, Telegram token (all in `.env`, never uploaded)

If the project list itself is sensitive, options:
- **GitHub Pro ($4/month)** — flips Pages to private, only logged-in
  collaborators can view
- **Path B** (re-implement PPT in Python) — dashboard stops being needed at all,
  see SETUP-AGENT-QA.md for the alternative path

---

## Troubleshooting

**Pages URL shows a 404**
- Check the repo Settings → Pages section — it should say "Your site is live at..."
- The URL is case-sensitive
- Wait 60 seconds after enabling Pages; it takes a moment to build

**Bot loads the URL but PPT is still empty**
- Same Chad timing issue — the headless browser may not have waited long enough.
  Try `/country Chad` again; the timeout is now 25 sec for WB data
- Check the bot's PowerShell log — if it says `WARN: data load timeout`, the
  WB API is slow; tell me and I'll bump the timeout further

**Want to switch back to local file**
- Delete or comment out the `DASHBOARD_URL=` line in `.env`
- Restart the bot. It falls back to `file:///.../index.html` automatically.
