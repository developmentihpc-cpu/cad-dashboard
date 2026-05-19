"""
verify_workflow.py
====================
End-to-end orchestrator for the country needs-assessment QA workflow.

  1. Receives a verification request (country, optional sectors, reply channel)
  2. Triggers the dashboard via headless browser → exports country PPT
  3. Runs ppt_factcheck (Claude-powered) → applies minor fixes in place
  4. Returns the verified PPT to the original sender (email or Telegram)
  5. If major changes pending, sends an approval request with the diff

Called by:
    - agents_pipeline.py email watcher (when subject matches RUN: <Country> / verify)
    - telegram_bot.py (when /verify command received)
"""

import json
import os
import smtplib
import time
from dataclasses import dataclass, field
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional, Callable

from dashboard_export import export_country_ppt
from ppt_factcheck import factcheck_pptx, FactCheckResult, Finding


BASE_DIR     = Path(__file__).parent
ENV_FILE     = BASE_DIR / ".env"
PENDING_DIR  = BASE_DIR / "agent_outputs" / "pending_approvals"
PENDING_DIR.mkdir(parents=True, exist_ok=True)


# ── Channel-agnostic request/response model ───────────────────────────────────

@dataclass
class VerifyRequest:
    country: str
    sectors: str = "All sectors"
    reply_channel: str = "email"        # "email" or "telegram"
    reply_to: str = ""                   # email address or telegram chat_id (string)
    original_subject: str = ""           # for email replies
    request_id: str = field(default_factory=lambda: time.strftime("%Y%m%d-%H%M%S"))


# ── Env loader ─────────────────────────────────────────────────────────────────

def _load_env() -> dict:
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for k in ("GMAIL_SENDER", "GMAIL_APP_PASSWORD", "ANTHROPIC_API_KEY",
              "TELEGRAM_BOT_TOKEN"):
        if k not in env and k in os.environ:
            env[k] = os.environ[k]
    return env


ENV = _load_env()


# ── Email reply helper ────────────────────────────────────────────────────────

def send_email_reply(to_address: str, subject: str, body_html: str,
                     attachment_path: Optional[Path] = None) -> bool:
    sender   = ENV.get("GMAIL_SENDER", "")
    password = ENV.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    if not sender or not password:
        print("[verify] No email credentials — saving body to file instead")
        out = BASE_DIR / "agent_outputs" / f"reply_{int(time.time())}.html"
        out.write_text(body_html, encoding="utf-8")
        return False

    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = f"CAD Agent <{sender}>"
    msg["To"]      = to_address

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(body_html, "html"))
    msg.attach(alt)

    if attachment_path and Path(attachment_path).exists():
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application",
                            "vnd.openxmlformats-officedocument.presentationml.presentation")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{Path(attachment_path).name}"')
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, to_address, msg.as_string())
        print(f"[verify] Email sent → {to_address}")
        return True
    except Exception as e:
        print(f"[verify] Email send failed: {e}")
        return False


# ── Telegram reply helper ─────────────────────────────────────────────────────

def send_telegram_reply(chat_id: str, text: str,
                        attachment_path: Optional[Path] = None) -> bool:
    """Use Telegram HTTP API directly (no extra library needed)."""
    import urllib.request
    import urllib.parse

    token = ENV.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[verify] No Telegram token configured")
        return False

    base = f"https://api.telegram.org/bot{token}"

    # Send the text message
    try:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()
        urllib.request.urlopen(f"{base}/sendMessage", data=data, timeout=15)
    except Exception as e:
        print(f"[verify] Telegram text send failed: {e}")

    # Send the document
    if attachment_path and Path(attachment_path).exists():
        try:
            from urllib.request import urlopen, Request
            import mimetypes, uuid
            boundary = f"----CAD{uuid.uuid4().hex}"
            file_bytes = Path(attachment_path).read_bytes()
            body  = []
            body.append(f"--{boundary}\r\n".encode())
            body.append(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode())
            body.append(f"{chat_id}\r\n".encode())
            body.append(f"--{boundary}\r\n".encode())
            body.append(f'Content-Disposition: form-data; name="document"; filename="{Path(attachment_path).name}"\r\n'.encode())
            body.append(b'Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation\r\n\r\n')
            body.append(file_bytes)
            body.append(f"\r\n--{boundary}--\r\n".encode())
            payload = b"".join(body)
            req = Request(f"{base}/sendDocument", data=payload,
                          headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            urlopen(req, timeout=60)
            print(f"[verify] Telegram document sent → {chat_id}")
            return True
        except Exception as e:
            print(f"[verify] Telegram document send failed: {e}")
            return False
    return True


# ── Reply formatting ──────────────────────────────────────────────────────────

def build_success_html(req: VerifyRequest, result: FactCheckResult) -> str:
    minor_rows = "".join(
        f"<tr><td style='padding:6px 10px;border-bottom:1px solid #E5E8EF'>"
        f"Slide {f.slide_index}</td><td style='padding:6px 10px;border-bottom:1px solid #E5E8EF;color:#6B7280'>"
        f"<s>{f.old_text}</s> → <strong>{f.new_text}</strong><br>"
        f"<em style='font-size:11px'>{f.rationale}</em></td></tr>"
        for f in result.minor_log
    )
    return f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#F4F5F8;padding:24px">
<table width="640" align="center" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06)">
<tr><td style="background:#2D3F7B;padding:18px 24px;color:#fff">
  <div style="font-size:11px;color:#C99A2E;letter-spacing:2px;font-weight:700">CAD AGENT · VERIFIED</div>
  <div style="font-size:18px;font-weight:700;margin-top:4px">{req.country} · {req.sectors}</div>
</td></tr>
<tr><td style="padding:20px 24px">
  <p style="margin:0 0 12px;font-size:14px"><strong>{result.summary}</strong></p>
  <p style="margin:0 0 16px;font-size:13px;color:#6B7280">
    The verified country PPT is attached. Layout and structure unchanged — only fact corrections were applied to existing text.
  </p>
  {f'<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E5E8EF;border-radius:6px;font-size:13px;margin-top:12px"><tr><td colspan="2" style="background:#F4F5F8;padding:8px 10px;font-size:11px;font-weight:700;color:#6B7280;letter-spacing:1px">FIXES APPLIED</td></tr>{minor_rows}</table>' if minor_rows else ''}
</td></tr>
<tr><td style="background:#F4F5F8;padding:12px 24px;font-size:11px;color:#9CA3AF;border-top:1px solid #E5E8EF">
  Request {req.request_id} · CAD Verification Agent · Office of Development Affairs
</td></tr></table></body></html>"""


def build_approval_html(req: VerifyRequest, result: FactCheckResult, approval_id: str) -> str:
    rows = "".join(
        f"<tr><td style='padding:8px 10px;border-bottom:1px solid #E5E8EF;vertical-align:top'>"
        f"<strong>Slide {f.slide_index}</strong><br>"
        f"<span style='font-size:11px;color:#9B120B;font-weight:700;text-transform:uppercase'>{f.category.replace('_',' ')}</span></td>"
        f"<td style='padding:8px 10px;border-bottom:1px solid #E5E8EF;font-size:13px'>"
        f"<div style='color:#6B7280;text-decoration:line-through'>{f.old_text}</div>"
        f"<div style='color:#1A1F36;font-weight:600;margin-top:4px'>{f.new_text}</div>"
        f"<div style='font-size:11px;color:#6B7280;font-style:italic;margin-top:4px'>{f.rationale}</div></td></tr>"
        for f in result.major_pending
    )
    return f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#F4F5F8;padding:24px">
<table width="640" align="center" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.06)">
<tr><td style="background:#9B120B;padding:18px 24px;color:#fff">
  <div style="font-size:11px;color:#FBF3E0;letter-spacing:2px;font-weight:700">CAD AGENT · APPROVAL REQUIRED</div>
  <div style="font-size:18px;font-weight:700;margin-top:4px">{req.country} · {req.sectors}</div>
</td></tr>
<tr><td style="padding:20px 24px">
  <p style="margin:0 0 12px;font-size:14px">
    Found <strong>{len(result.major_pending)} major change(s)</strong> that need your approval before being applied.
  </p>
  <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E5E8EF;border-radius:6px;font-size:13px;margin:12px 0">
    {rows}
  </table>
  <p style="margin:16px 0 0;font-size:13px;color:#1A1F36">
    To approve all and apply, reply with subject: <code style="background:#E8ECF8;padding:2px 6px;border-radius:3px">APPROVE-{approval_id}</code><br>
    To reject, reply with: <code style="background:#FDECEA;padding:2px 6px;border-radius:3px">REJECT-{approval_id}</code>
  </p>
</td></tr>
<tr><td style="background:#F4F5F8;padding:12px 24px;font-size:11px;color:#9CA3AF;border-top:1px solid #E5E8EF">
  Approval ID {approval_id} · Request {req.request_id}
</td></tr></table></body></html>"""


# ── Main orchestrator ─────────────────────────────────────────────────────────

def run_verification(req: VerifyRequest) -> dict:
    """End-to-end run. Returns a dict with status + paths."""
    print(f"\n{'═' * 60}\n  VERIFY · {req.country} · {req.sectors}\n  Request ID: {req.request_id}\n{'═' * 60}")

    # Step 1: Trigger dashboard export
    print(f"[step 1/3] Triggering dashboard export …")
    export_result = export_country_ppt(req.country)
    if not export_result.success:
        print(f"[FAIL] {export_result.error_type}: {export_result.message}")
        _send_failure(req, export_result.message,
                      error_type=export_result.error_type,
                      suggestions=export_result.suggestions)
        return {"status": export_result.error_type, "error": export_result.message}
    pptx_path = export_result.path

    # Step 2: Fact-check.
    # Telegram replies auto-apply ALL fixes (no approval queue).
    # Email replies keep the minor-auto / major-approve split.
    print(f"[step 2/3] Fact-checking PPT …")
    auto_all = (req.reply_channel == "telegram")
    result = factcheck_pptx(pptx_path, country=req.country,
                            apply_minor=True, apply_all_fixes=auto_all)

    # Step 3: Reply
    print(f"[step 3/3] Sending reply via {req.reply_channel} …")
    if req.reply_channel == "telegram":
        # All fixes already applied — just send the result + summary.
        text = f"✓ *{req.country}* verified.\n{result.summary}"
        send_telegram_reply(req.reply_to, text, attachment_path=result.pptx_path)
    elif result.major_pending:
        approval_id = f"{req.request_id}-{req.country.replace(' ', '')[:6].upper()}"
        pending_file = PENDING_DIR / f"{approval_id}.json"
        pending_file.write_text(json.dumps({
            "approval_id": approval_id,
            "request": req.__dict__,
            "pptx_path": str(result.pptx_path),
            "pending": [f.__dict__ for f in result.major_pending],
        }, indent=2))
        print(f"[verify] Saved pending approval → {pending_file.name}")
        send_email_reply(
            req.reply_to,
            f"APPROVAL NEEDED · {req.country} fact-check",
            build_approval_html(req, result, approval_id),
            attachment_path=result.pptx_path,
        )
    else:
        send_email_reply(
            req.reply_to,
            f"VERIFIED · {req.country} country profile",
            build_success_html(req, result),
            attachment_path=result.pptx_path,
        )

    return {
        "status": "ok",
        "pptx_path": str(result.pptx_path),
        "minor_applied": result.minor_applied,
        "major_pending": len(result.major_pending),
    }


def _send_failure(req: VerifyRequest, message: str,
                  error_type: str = "", suggestions: list = None) -> None:
    suggestions = suggestions or []

    # ---- Telegram ----
    if req.reply_channel == "telegram":
        if error_type == "unknown_country":
            text = (f"❌ Country not recognised: *{req.country}*\n\n"
                    f"{message}\n\n"
                    f"_Available countries (sample):_\n"
                    f"`{'  ·  '.join(suggestions[:15])}`")
        elif error_type == "data_load_failed":
            text = (f"⚠️ *{req.country}* — World Bank data didn't load in time.\n\n"
                    f"{message}\n\n"
                    f"Send `/country {req.country}` again to retry.")
        elif error_type == "export_failed":
            text = (f"⚠️ *{req.country}* — the dashboard couldn't generate the PPT.\n\n"
                    f"{message}")
        else:
            text = f"❌ *{req.country}* failed.\n\n{message}"
        send_telegram_reply(req.reply_to, text)
        return

    # ---- Email ----
    if error_type == "unknown_country":
        body = (f"<p>The verification request for <strong>{req.country}</strong> "
                f"could not be processed because that country is not recognised "
                f"by the dashboard.</p>"
                f"<p>{message}</p>"
                f"<p><strong>Available countries (sample):</strong><br>"
                f"<code>{', '.join(suggestions[:20])}</code></p>")
        subject = f"FAILED · Unknown country: {req.country}"
    elif error_type == "data_load_failed":
        body = (f"<p>The verification request for <strong>{req.country}</strong> "
                f"could not be processed.</p><p>{message}</p>"
                f"<p>Reply to retry, or wait a few minutes and resend the original trigger.</p>")
        subject = f"FAILED · Data load timeout: {req.country}"
    else:
        body = (f"<p>The verification request for <strong>{req.country}</strong> "
                f"failed.</p><p>{message}</p>")
        subject = f"FAILED · {req.country}"
    send_email_reply(req.reply_to, subject, body)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python verify_workflow.py <Country> <reply_email> [sectors]")
        sys.exit(1)
    req = VerifyRequest(
        country=sys.argv[1],
        reply_to=sys.argv[2],
        sectors=sys.argv[3] if len(sys.argv) > 3 else "All sectors",
    )
    result = run_verification(req)
    print(f"\nResult: {json.dumps(result, indent=2)}")
