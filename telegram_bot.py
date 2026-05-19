"""
telegram_bot.py
================
Minimal Telegram polling bot for the CAD verification agent.
Uses Telegram's HTTP API directly via stdlib — no external library required.

Listens for messages of the form:
    /country Ethiopia
    /country Ethiopia Health & Nutrition
    /country Ethiopia All sectors

…and triggers the verify_workflow on each. Replies via Telegram with status
and the verified PPT. All fact-check fixes (minor AND major) auto-apply —
the PPT comes back fully corrected, no approval prompt.

Setup (one-time):
    1. In Telegram, message @BotFather, send /newbot, follow prompts
    2. Copy the token it gives you
    3. Add to .env:  TELEGRAM_BOT_TOKEN=123456:abcdef...
    4. Find your own Telegram numeric chat_id (message @userinfobot)
    5. Optional: add TELEGRAM_ALLOWED_CHATS=<your_chat_id> to .env (comma-sep
       list to lock down the bot to specific users; leave unset = open)

Usage:
    python telegram_bot.py            # runs forever, polls every 3 sec
"""

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from threading import Thread
from typing import Optional

from verify_workflow import VerifyRequest, run_verification, _load_env


BASE_DIR    = Path(__file__).parent
PENDING_DIR = BASE_DIR / "agent_outputs" / "pending_approvals"

POLL_INTERVAL_SEC = 3
ENV = _load_env()
TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED = set(filter(None, ENV.get("TELEGRAM_ALLOWED_CHATS", "").split(",")))


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _api(method: str, params: dict = None, timeout: int = 30) -> dict:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in .env")
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read())


def send_message(chat_id: str, text: str) -> None:
    try:
        _api("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"[telegram] sendMessage failed: {e}")


# ── Command parsing ───────────────────────────────────────────────────────────

def parse_command(text: str):
    text = text.strip()
    if not text.startswith("/"):
        return None, None

    # Split into command + args
    parts = text.split(maxsplit=1)
    cmd  = parts[0].lstrip("/").lower().split("@")[0]   # /verify@MyBot → verify
    args = parts[1].strip() if len(parts) > 1 else ""
    return cmd, args


def parse_verify_args(args: str):
    """`Ethiopia Health & Nutrition` → ("Ethiopia", "Health & Nutrition")
       `Ethiopia` → ("Ethiopia", "All sectors")"""
    if not args:
        return None, None
    bits = args.split(maxsplit=1)
    country = bits[0]
    sectors = bits[1] if len(bits) > 1 else "All sectors"
    return country, sectors


# ── Approval handling ─────────────────────────────────────────────────────────

def apply_approval(approval_id: str) -> Optional[dict]:
    """Load pending file, apply major changes, save final PPTX. Returns metadata."""
    pending_file = PENDING_DIR / f"{approval_id}.json"
    if not pending_file.exists():
        return None
    data = json.loads(pending_file.read_text())

    from pptx import Presentation
    from ppt_factcheck import Finding, apply_fix

    prs = Presentation(data["pptx_path"])
    applied = 0
    for raw in data["pending"]:
        f = Finding(**{k: v for k, v in raw.items() if k != "shape_id"}, shape_id=None)
        if apply_fix(prs, f):
            applied += 1
    final_path = Path(data["pptx_path"]).with_name(
        Path(data["pptx_path"]).stem + "_approved.pptx"
    )
    prs.save(str(final_path))
    pending_file.unlink()
    return {"applied": applied, "final_path": final_path,
            "request": data["request"]}


# ── Message dispatcher ────────────────────────────────────────────────────────

def handle_message(msg: dict) -> None:
    chat_id = str(msg["chat"]["id"])
    text    = msg.get("text", "")
    sender  = msg.get("from", {}).get("username", "?")

    if ALLOWED and chat_id not in ALLOWED:
        send_message(chat_id, "🔒 This bot is not authorised for this chat.")
        return

    cmd, args = parse_command(text)
    if not cmd:
        send_message(chat_id, "Send `/country <Country>` to start a verification, "
                              "or `/help` for usage.")
        return

    print(f"[telegram] @{sender} ({chat_id}): /{cmd} {args}")

    if cmd in ("start", "help"):
        send_message(chat_id,
            "*CAD Verification Agent*\n\n"
            "Trigger a country PPT verification:\n"
            "`/country Ethiopia`\n"
            "`/country Ethiopia Health & Nutrition`\n"
            "`/country Yemen WASH & Food Security`\n\n"
            "The agent will export the country profile from the dashboard, "
            "fact-check it, fix any errors in place, and send back a verified "
            "`.pptx`. All fixes apply automatically — no approval needed."
        )
        return

    if cmd == "country":
        country, sectors = parse_verify_args(args)
        if not country:
            send_message(chat_id, "Usage: `/country <Country> [sectors]`")
            return
        send_message(chat_id, f"⏳ Working on *{country}* ({sectors}) — this takes ~1–2 minutes …")
        Thread(target=_run_verify_thread,
               args=(country, sectors, chat_id), daemon=True).start()
        return

    send_message(chat_id, f"Unknown command: /{cmd}. Send `/help` for usage.")


def _run_verify_thread(country: str, sectors: str, chat_id: str) -> None:
    try:
        req = VerifyRequest(country=country, sectors=sectors,
                            reply_channel="telegram", reply_to=chat_id)
        run_verification(req)
    except Exception as e:
        send_message(chat_id, f"❌ Error: {e}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def run_bot() -> None:
    if not TOKEN:
        print("[telegram] TELEGRAM_BOT_TOKEN not set — exiting.")
        return
    print(f"[telegram] Starting bot (polling every {POLL_INTERVAL_SEC}s) …")
    if ALLOWED:
        print(f"[telegram] Restricted to chats: {ALLOWED}")
    last_update_id = 0
    while True:
        try:
            data = _api("getUpdates", {
                "offset": last_update_id + 1,
                "timeout": 25,
            }, timeout=30)
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message")
                if msg and "text" in msg:
                    handle_message(msg)
        except Exception as e:
            print(f"[telegram] poll error: {e}")
            time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    run_bot()
