"""
Country Assessment Dashboard — Pipeline Digest Agent
=====================================================
Reads pipeline-state.json, identifies stalled / at-risk projects,
and sends a formatted HTML digest email via Gmail SMTP.

Setup (one-time):
  1. Enable 2-Step Verification on your Gmail account.
  2. Go to https://myaccount.google.com/apppasswords
  3. Create an App Password (name it "CAD Digest").
  4. Copy the 16-char password into .env  (GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx)
  5. Run:  python digest_agent.py
  6. Schedule with Windows Task Scheduler (see run_digest.bat).
"""

import json, os, smtplib, sys
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
STATE_FILE   = BASE_DIR / "pipeline-state.json"
ENV_FILE     = BASE_DIR / ".env"

# Stall thresholds (days at same status before flagging)
STALL_DAYS = {
    0: 7,   # Intake
    1: 14,  # Country Analysis
    2: 21,  # Program Dev
    3: 10,  # Stakeholder Eng  ← Pending Review
    4: 10,  # Leadership Review ← Pending Review
}
DEFAULT_STALL = 14

STEP_NAMES = [
    "Intake", "Country Analysis", "Program Dev",
    "Stakeholder Eng.", "Leadership Review", "Approved"
]

PATH_NAMES = {"B": "Sector Assessment", "C": "Program Evaluation"}  # Path A retired

# ── Load .env ─────────────────────────────────────────────────────────────────
def load_env():
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Fall back to real env vars
    for key in ("GMAIL_SENDER", "GMAIL_APP_PASSWORD", "DIGEST_RECIPIENT"):
        if key not in env and key in os.environ:
            env[key] = os.environ[key]
    return env

# ── Load state ────────────────────────────────────────────────────────────────
def load_state():
    if not STATE_FILE.exists():
        print(f"[ERROR] {STATE_FILE} not found.")
        print("  → Open the dashboard, go to Settings → Export → Digest Export")
        print("    and save pipeline-state.json to this folder.")
        sys.exit(1)
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)

# ── Analysis ──────────────────────────────────────────────────────────────────
def days_since(date_str):
    """Return days since a date string (ISO or DD Mon YYYY)."""
    if not date_str:
        return 0
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", ""))
        return (datetime.now() - dt.replace(tzinfo=None)).days
    except ValueError:
        pass
    # Dashboard date format e.g. "12 May 2025"
    try:
        dt = datetime.strptime(date_str, "%d %b %Y")
        return (datetime.now() - dt).days
    except ValueError:
        return 0

def last_status_change(meta):
    """Return (days_ago, date_str) of the last status change."""
    history = meta.get("history", [])
    status_changes = [h for h in history if "to" in h or "from" in h]
    if status_changes:
        last = status_changes[-1]
        return days_since(last.get("date", "")), last.get("date", "—")
    return None, None  # no history — use submission date

def analyse(state):
    requests  = state.get("requests", [])
    meta_map  = state.get("requestMeta", {})

    stalled, at_risk, approved_recent, paused, cancelled, active = [], [], [], [], [], []

    for r in requests:
        mid  = str(r.get("id", ""))
        meta = meta_map.get(mid, {})
        sub  = r.get("substatus")
        st   = r.get("status", 0)

        if sub == "cancelled":
            cancelled.append(r); continue
        if sub == "paused":
            paused.append(r); continue
        if st >= 5:
            days_approved, _ = last_status_change(meta)
            if days_approved is not None and days_approved <= 30:
                approved_recent.append(r)
            continue

        # Calculate days at current status
        days_ago, changed_date = last_status_change(meta)
        if days_ago is None:
            # No history — use submission date
            days_ago = days_since(r.get("date", ""))
            changed_date = r.get("date", "—")

        threshold = STALL_DAYS.get(st, DEFAULT_STALL)
        entry = {**r, "_days": days_ago, "_changed": changed_date, "_threshold": threshold}

        if days_ago >= threshold:
            stalled.append(entry)
        elif days_ago >= threshold * 0.7:
            at_risk.append(entry)
        else:
            active.append(r)

    stalled.sort(key=lambda x: x["_days"], reverse=True)
    at_risk.sort(key=lambda x: x["_days"], reverse=True)

    return {
        "stalled": stalled,
        "at_risk": at_risk,
        "approved_recent": approved_recent,
        "paused": paused,
        "cancelled": cancelled,
        "active": active,
        "total": len(requests),
    }

# ── HTML builder ──────────────────────────────────────────────────────────────
def pill(label, bg, color):
    return f'<span style="display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700;background:{bg};color:{color}">{label}</span>'

def status_pill(r):
    sub = r.get("substatus")
    st  = r.get("status", 0)
    if sub == "paused":    return pill("❚❚ Paused",    "#EEF0FB", "#4B5EA8")
    if sub == "cancelled": return pill("✕ Cancelled",  "#FDECEA", "#9B120B")
    if st >= 5:            return pill("Approved",      "#E6F7F2", "#1E9E74")
    if st >= 3:            return pill("Pending Review","#FDECEA", "#9B120B")
    return pill("In Development", "#E8EBF5", "#2D3F7B")

def req_row(r, show_days=False):
    days   = r.get("_days", "")
    step   = STEP_NAMES[min(r.get("status", 0), 5)]
    path   = PATH_NAMES.get(r.get("path", "B"), r.get("path", ""))
    days_badge = (f'<span style="float:right;font-size:11px;font-weight:700;color:#9B120B">'
                  f'{days}d stalled</span>') if show_days and days else ""
    return f"""
    <tr>
      <td style="padding:10px 12px;border-bottom:1px solid #E5E8EF">
        {days_badge}
        <div style="font-weight:600;font-size:13px;color:#111827">{r.get("titleEn","—")}</div>
        <div style="font-size:11px;color:#6B7280;margin-top:2px">{r.get("country","—")} &middot; {r.get("sector","—")} &middot; {path}</div>
      </td>
      <td style="padding:10px 12px;border-bottom:1px solid #E5E8EF;white-space:nowrap">{step}</td>
      <td style="padding:10px 12px;border-bottom:1px solid #E5E8EF;white-space:nowrap">{r.get("cost","—")}</td>
      <td style="padding:10px 12px;border-bottom:1px solid #E5E8EF">{status_pill(r)}</td>
    </tr>"""

def section(title, color, icon, rows_html, note=""):
    return f"""
  <div style="margin-bottom:28px">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
      <span style="font-size:18px">{icon}</span>
      <span style="font-size:14px;font-weight:700;color:{color}">{title}</span>
    </div>
    {f'<p style="font-size:12px;color:#6B7280;margin:0 0 10px">{note}</p>' if note else ""}
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border:1px solid #E5E8EF;border-radius:8px;overflow:hidden;font-family:Arial,sans-serif">
      <thead>
        <tr style="background:#F4F5F8">
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600">PROJECT</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600">STAGE</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600">COST</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600">STATUS</th>
        </tr>
      </thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>"""

def build_html(analysis, exported_at):
    stalled  = analysis["stalled"]
    at_risk  = analysis["at_risk"]
    approved = analysis["approved_recent"]
    paused   = analysis["paused"]
    total    = analysis["total"]
    active_c = len(analysis["active"])
    now      = datetime.now().strftime("%A, %d %B %Y")
    exp_str  = exported_at[:10] if exported_at else "—"

    def kpi(val, label, color="#2D3F7B"):
        return f"""<td style="text-align:center;padding:0 20px">
          <div style="font-size:28px;font-weight:800;color:{color}">{val}</div>
          <div style="font-size:11px;color:#6B7280;margin-top:2px">{label}</div>
        </td>"""

    kpi_row = f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px">
      <tr>
        {kpi(total, "Total projects")}
        {kpi(active_c, "On track", "#2DB88A")}
        {kpi(len(at_risk), "At risk", "#AD833B")}
        {kpi(len(stalled), "Stalled", "#9B120B")}
        {kpi(len(approved), "Approved (30d)", "#2DB88A")}
      </tr>
    </table>"""

    body_sections = kpi_row

    if stalled:
        rows = "".join(req_row(r, show_days=True) for r in stalled)
        body_sections += section(
            f"Stalled Projects ({len(stalled)})", "#9B120B", "🔴", rows,
            note="These projects have not advanced in longer than the expected window. Action required."
        )

    if at_risk:
        rows = "".join(req_row(r, show_days=True) for r in at_risk)
        body_sections += section(
            f"At Risk ({len(at_risk)})", "#AD833B", "🟡", rows,
            note="Approaching the stall threshold — follow up soon."
        )

    if approved:
        rows = "".join(req_row(r) for r in approved)
        body_sections += section(f"Recently Approved ({len(approved)})", "#2DB88A", "✅", rows)

    if paused:
        rows = "".join(req_row(r) for r in paused)
        body_sections += section(f"Paused ({len(paused)})", "#4B5EA8", "⏸", rows)

    if not stalled and not at_risk:
        body_sections += """<div style="text-align:center;padding:32px;background:#E6F7F2;border-radius:10px;margin-bottom:28px">
          <div style="font-size:32px">✅</div>
          <div style="font-size:15px;font-weight:700;color:#2F7F58;margin-top:8px">Pipeline is healthy</div>
          <div style="font-size:13px;color:#6B7280;margin-top:4px">All projects are progressing within expected timelines.</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F4F5F8;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F5F8;padding:32px 0">
<tr><td align="center">
<table width="620" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)">

  <!-- Header -->
  <tr><td style="background:#2D3F7B;padding:24px 28px">
    <div style="font-size:18px;font-weight:800;color:#fff">Country Assessment Dashboard</div>
    <div style="font-size:13px;color:rgba(255,255,255,.7);margin-top:4px">Pipeline Digest &mdash; {now}</div>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:28px">
    <p style="margin:0 0 20px;font-size:13px;color:#6B7280">
      Data exported: <strong>{exp_str}</strong> &nbsp;&middot;&nbsp;
      Stall thresholds: Intake 7d &middot; Analysis 14d &middot; Program Dev 21d &middot; Review 10d
    </p>
    {body_sections}
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#F4F5F8;padding:16px 28px;border-top:1px solid #E5E8EF">
    <p style="margin:0;font-size:11px;color:#9CA3AF">
      Generated by the CAD Pipeline Digest Agent &middot; Office of Development Affairs<br>
      To update project statuses, open the dashboard and use the progress timeline.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""

# ── Send email ────────────────────────────────────────────────────────────────
def send_email(html_body, env, analysis):
    sender    = env.get("GMAIL_SENDER", "")
    password  = env.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    recipient = env.get("DIGEST_RECIPIENT", sender)

    if not sender or not password:
        # Save to file instead
        out = BASE_DIR / "digest_preview.html"
        out.write_text(html_body, encoding="utf-8")
        print(f"[INFO] No email credentials found — digest saved to: {out}")
        print("       Set GMAIL_SENDER and GMAIL_APP_PASSWORD in .env to enable email sending.")
        return

    stalled_count = len(analysis["stalled"])
    subject = (
        f"🔴 CAD Digest — {stalled_count} project{'s' if stalled_count!=1 else ''} stalled"
        if stalled_count else
        f"✅ CAD Digest — Pipeline healthy ({analysis['total']} projects)"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"CAD Digest <{sender}>"
    msg["To"]      = recipient
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, recipient, msg.as_string())
        print(f"[OK] Digest sent to {recipient}")
        print(f"     Subject: {subject}")
    except smtplib.SMTPAuthenticationError:
        out = BASE_DIR / "digest_preview.html"
        out.write_text(html_body, encoding="utf-8")
        print(f"[WARN] Gmail authentication failed — check your App Password in .env")
        print(f"       Digest saved to: {out} (open in browser to preview)")
    except Exception as e:
        out = BASE_DIR / "digest_preview.html"
        out.write_text(html_body, encoding="utf-8")
        print(f"[WARN] Could not send email ({e})")
        print(f"       Digest saved to: {out}")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 52)
    print("  CAD Pipeline Digest Agent")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 52)

    env   = load_env()
    state = load_state()
    exported_at = state.get("exportedAt", "")

    print(f"  Loaded {len(state.get('requests', []))} requests from pipeline-state.json")
    if exported_at:
        print(f"  State exported: {exported_at[:16]}")

    analysis = analyse(state)
    print(f"\n  Stalled:  {len(analysis['stalled'])}")
    print(f"  At risk:  {len(analysis['at_risk'])}")
    print(f"  On track: {len(analysis['active'])}")
    print(f"  Approved: {len(analysis['approved_recent'])} (last 30d)")

    html = build_html(analysis, exported_at)
    send_email(html, env, analysis)

if __name__ == "__main__":
    main()
