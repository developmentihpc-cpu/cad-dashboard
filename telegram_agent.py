"""
CAD Dashboard — Telegram Bot
==============================
Commands:
  /Country <name>                          read-only pipeline status (instant)
  /report <country> [sector] [workflow]    run agent pipeline + deliver PPT
                                           (~3 min, runs in background thread)

Modes:
  python telegram_agent.py           # one poll, exit (GitHub Actions)
  python telegram_agent.py --watch   # long-poll forever (local / Railway)
"""

import json, os, sys, time, threading, requests
from datetime import datetime
from pathlib import Path

BASE_DIR    = Path(__file__).parent
ENV_FILE    = BASE_DIR / ".env"
STATE_FILE  = BASE_DIR / "pipeline-state.json"
OFFSET_FILE = BASE_DIR / ".telegram_offset"

STEP_NAMES  = ["Intake", "Country Analysis", "Program Dev",
               "Stakeholder Eng.", "Leadership Review", "Approved"]

# ── Env ────────────────────────────────────────────────────────────────────────

def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_CHATS",
                "ANTHROPIC_API_KEY", "DIGEST_RECIPIENT"):
        if key not in env and key in os.environ:
            env[key] = os.environ[key]
    return env

ENV = load_env()

# ── Telegram helpers ───────────────────────────────────────────────────────────

def tg(method, **kwargs):
    token = ENV.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        return {}
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}",
                      json=kwargs, timeout=30)
    return r.json()

def send(chat_id, text):
    tg("sendMessage", chat_id=chat_id, text=text,
       parse_mode="HTML", disable_web_page_preview=True)

def is_allowed(chat_id):
    """Deny-by-default chat allowlist.

    Prior behaviour returned True when TELEGRAM_ALLOWED_CHATS was empty —
    that combined with --allow-unauthenticated meant ANY Telegram chat could
    talk to the bot. Now an empty/missing allowlist locks the bot down.
    To open access, set TELEGRAM_ALLOWED_CHATS to a comma-separated list of
    chat IDs in .env (local) and in GitHub Secrets (Cloud Run + Actions).
    """
    allowed = ENV.get("TELEGRAM_ALLOWED_CHATS", "").strip()
    if not allowed:
        print(f"[deny] TELEGRAM_ALLOWED_CHATS is empty — rejecting chat_id={chat_id}")
        return False
    return str(chat_id) in [c.strip() for c in allowed.split(",")]

def get_offset():
    try:
        return int(OFFSET_FILE.read_text().strip()) if OFFSET_FILE.exists() else None
    except Exception:
        return None

def save_offset(offset):
    OFFSET_FILE.write_text(str(offset), encoding="utf-8")

# ── State ──────────────────────────────────────────────────────────────────────

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Try fetching from GitHub if not local
    repo = ENV.get("GITHUB_REPO", "developmentihpc-cpu/cad-dashboard")
    try:
        url = f"https://raw.githubusercontent.com/{repo}/main/pipeline-state.json"
        r   = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# ── /Country command ───────────────────────────────────────────────────────────

def cmd_country(chat_id, args):
    if not args:
        send(chat_id,
             "Usage: <b>/Country &lt;name&gt;</b>\n\n"
             "Examples:\n"
             "/Country Jordan\n"
             "/Country Ethiopia\n"
             "/Country Yemen")
        return

    query = " ".join(args).strip().lower()
    state = load_state()

    if not state:
        send(chat_id, "⚠️ No pipeline data available. Export state from the dashboard.")
        return

    reqs     = state.get("requests", [])
    meta_map = state.get("requestMeta", {})
    exported = state.get("exportedAt", "")[:10]

    # Match country
    matches = [r for r in reqs if query in r.get("country", "").lower()]

    if not matches:
        # Try partial match
        countries = sorted(set(r.get("country","") for r in reqs))
        close = [c for c in countries if query[:3] in c.lower()]
        suggestion = f"\n\nDid you mean: {', '.join(close[:4])}?" if close else ""
        send(chat_id, f"❌ No projects found for <b>{' '.join(args)}</b>.{suggestion}")
        return

    country_name = matches[0].get("country", " ".join(args))
    lines = [
        f"🌍 <b>{country_name}</b>",
        f"<i>Pipeline data as of {exported}</i>",
        f"{'─' * 30}",
    ]

    for r in matches:
        mid  = str(r.get("id", ""))
        meta = meta_map.get(mid, {})
        sub  = r.get("substatus")
        st   = r.get("status", 0)
        step = STEP_NAMES[min(st, 5)]

        # Status icon
        if sub == "paused":      status = "⏸ Paused"
        elif sub == "cancelled": status = "❌ Cancelled"
        elif st >= 5:            status = "✅ Approved"
        elif st >= 3:            status = "🟡 Pending Review"
        else:                    status = "🔵 In Development"

        # Eval scores (if any)
        scores = meta.get("evalScores", [])
        score_line = ""
        if scores:
            icons = {"Strong":"🟢","Good":"🔵","Moderate":"🟡","Weak":"🔴"}
            score_line = "  " + " · ".join(
                f"{icons.get(s['rating'],'⚪')}{s['area'].split()[0]} {s['rating']}"
                for s in scores[:3]
            )

        lines += [
            f"",
            f"📋 <b>{r.get('titleEn','—')}</b>",
            f"  🏷 {r.get('sector','—')}  ·  "
            f"{'Sector Assessment' if r.get('path')=='B' else 'Program Evaluation'}",
            f"  📍 {step}  ·  {status}",
            f"  💰 {r.get('cost','—')}  ·  "
            f"👥 {meta.get('beneficiaries','—')}  ·  ⏱ {meta.get('duration','—')}",
        ]
        if score_line:
            lines.append(score_line)

    # Programs
    cp = state.get("countryPrograms", {}).get(country_name, {})
    total_progs = (len(cp.get("existing",[])) +
                   len(cp.get("proposed",[])) +
                   len(cp.get("evaluation",[])))
    if total_progs:
        lines += [
            f"",
            f"{'─' * 30}",
            f"📁 Country programs on record: <b>{total_progs}</b>",
        ]

    lines += [
        f"",
        f"{'─' * 30}",
        f"<i>Open the dashboard for full details and timelines.</i>",
    ]

    send(chat_id, "\n".join(lines))

# ── /report command — runs agent pipeline + delivers PPT to chat ──────────────

VALID_WORKFLOWS = {"needs", "proposal", "external"}


def _parse_report_args(args):
    """Parse `[country] [sector] [workflow]` from /report arguments.

    Flexible parsing:
      /report Kenya
      /report Kenya All sectors
      /report Kenya All sectors needs
      /report "Sierra Leone" Health needs
    Workflow (last token) is detected if it matches VALID_WORKFLOWS,
    otherwise defaults to 'needs'. Sector defaults to 'All sectors'.
    Country is the FIRST positional argument (required).
    """
    if not args:
        return None, None, None
    parts = list(args)
    workflow = "needs"
    if parts and parts[-1].lower() in VALID_WORKFLOWS:
        workflow = parts.pop().lower()
    country = parts[0] if parts else None
    sector  = " ".join(parts[1:]) if len(parts) > 1 else "All sectors"
    return country, sector, workflow


def _run_report_job(chat_id, country, sector, workflow):
    """Background worker: run the agent pipeline + send PPT back.

    Runs in a separate thread so the webhook handler can return 200
    immediately. Any failure here is reported back to the user as a
    text message — never go silent.
    """
    try:
        # Defer heavy imports — keep webhook startup fast
        import agents_pipeline as ap
        from verify_workflow import send_telegram_reply

        ctx = {
            "country":  country,
            "sector":   sector,
            "workflow": workflow,
            "audience": "Senior Leadership & Donor Partners",
            "budget":   "TBD",
            "horizon":  "3 years",
        }
        print(f"[/report] {chat_id} → start: {country} / {sector} / {workflow}")

        outputs = ap.run_pipeline(ctx)
        editor  = outputs.get("editor", "")
        verdict = ("NOT READY"          if "NOT READY" in editor.upper()
                   else "READY WITH CAVEATS" if "CAVEATS" in editor.upper()
                   else "READY")

        pptx_path = ap.generate_pptx(ctx, outputs, verdict)
        if not pptx_path or not Path(str(pptx_path)).exists():
            send(chat_id,
                 f"⚠️ <b>{country} {workflow} report generation failed.</b>\n\n"
                 f"Agents finished but the PPT file was not produced. "
                 f"Check Cloud Run logs for details.")
            return

        msg = (f"✅ *{country} — {workflow.title()} report*\n"
               f"Sector: {sector}\n"
               f"Verdict: *{verdict}*\n"
               f"Agents: {len(outputs)} ran successfully")
        ok = send_telegram_reply(str(chat_id), msg,
                                 attachment_path=Path(str(pptx_path)))
        if not ok:
            # send_telegram_reply already logged the failure; fall back to text
            send(chat_id,
                 f"⚠️ <b>Report built but document send failed.</b>\n\n"
                 f"The PPT was generated successfully but Telegram rejected the "
                 f"attachment. Path on server: <code>{pptx_path}</code>\n"
                 f"Try fetching by email instead.")
        else:
            print(f"[/report] {chat_id} → delivered {Path(str(pptx_path)).name}")
    except Exception as e:
        # Catch-all: never let an unhandled exception leave the user hanging
        import traceback
        tb = traceback.format_exc()
        print(f"[/report] {chat_id} → FAILED: {e}\n{tb}")
        try:
            send(chat_id,
                 f"❌ <b>Report failed</b>\n\n"
                 f"Country: <code>{country}</code>\n"
                 f"Workflow: <code>{workflow}</code>\n"
                 f"Error: <code>{type(e).__name__}: {str(e)[:200]}</code>\n\n"
                 f"Check Cloud Run logs for the full traceback.")
        except Exception:
            pass   # if we can't even send the error, just log it


def cmd_report(chat_id, args):
    """Handler for /report — spawns a worker thread and returns immediately."""
    country, sector, workflow = _parse_report_args(args)
    if not country:
        send(chat_id,
             "📊 <b>/report</b> — Run agent pipeline + deliver PPT\n\n"
             "<b>Usage:</b>\n"
             "<code>/report &lt;country&gt; [sector] [workflow]</code>\n\n"
             "<b>Workflow</b> options: <code>needs</code> (default), "
             "<code>proposal</code>, <code>external</code>\n\n"
             "<b>Examples:</b>\n"
             "<code>/report Kenya</code>\n"
             "<code>/report Kenya All sectors needs</code>\n"
             "<code>/report Ethiopia Health proposal</code>\n\n"
             "⏱ Pipeline takes ~3 minutes. I'll send the PPT when it's ready.")
        return

    send(chat_id,
         f"🚀 <b>Starting {workflow} report for {country}</b>\n"
         f"Sector: {sector}\n"
         f"This takes ~3 minutes — I'll send the PPT when it's ready.")

    # Fire-and-forget worker so the webhook returns quickly
    threading.Thread(
        target=_run_report_job,
        args=(chat_id, country, sector, workflow),
        daemon=True,
        name=f"cad-report-{chat_id}",
    ).start()


# ── Unknown message handler ────────────────────────────────────────────────────

def cmd_unknown(chat_id):
    send(chat_id,
         "🌍 <b>CAD Pipeline Bot</b>\n\n"
         "I respond to two commands:\n\n"
         "<b>/Country &lt;name&gt;</b> — pipeline status (instant)\n"
         "<b>/report &lt;country&gt; [sector] [workflow]</b> — full agent run + PPT (~3 min)\n\n"
         "Examples:\n"
         "<code>/Country Jordan</code>\n"
         "<code>/report Kenya</code>")

# ── Update processor ───────────────────────────────────────────────────────────

def process_updates(updates):
    for update in updates:
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            continue

        chat_id = msg["chat"]["id"]
        text    = (msg.get("text") or "").strip()

        if not is_allowed(chat_id):
            send(chat_id, "⛔ Unauthorised.")
            continue

        if not text:
            continue

        print(f"  [{chat_id}] {text}")

        if text.lower().startswith("/country"):
            args = text.split()[1:]
            cmd_country(chat_id, args)
        elif text.lower().startswith("/report"):
            args = text.split()[1:]
            cmd_report(chat_id, args)
        elif text.startswith("/start") or text.startswith("/help"):
            cmd_unknown(chat_id)
        else:
            cmd_unknown(chat_id)

# ── Run modes ──────────────────────────────────────────────────────────────────

def run_once():
    """Single poll, process, exit — for GitHub Actions."""
    token = ENV.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set.")
        return

    offset = get_offset()
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset

    result  = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
                           params=params, timeout=20).json()
    updates = result.get("result", [])

    if not updates:
        print("No new messages.")
        return

    print(f"{len(updates)} message(s).")
    process_updates(updates)
    save_offset(updates[-1]["update_id"] + 1)


def run_watch():
    """Long-poll loop — instant responses, runs forever (Railway / local)."""
    token = ENV.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not set.")
        sys.exit(1)

    print("CAD Telegram Bot — watching (Ctrl+C to stop)")
    offset = get_offset()

    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            result  = requests.get(
                f"https://api.telegram.org/bot{token}/getUpdates",
                params=params, timeout=40).json()
            updates = result.get("result", [])

            if updates:
                process_updates(updates)
                offset = updates[-1]["update_id"] + 1
                save_offset(offset)

        except requests.exceptions.ReadTimeout:
            pass    # normal — long-poll timeout, just retry
        except Exception as e:
            print(f"[ERR] {e}")
            time.sleep(5)


if __name__ == "__main__":
    if "--watch" in sys.argv:
        run_watch()
    else:
        run_once()
