"""
CAD Dashboard — Telegram Webhook Handler
==========================================
Runs on Google Cloud Run.
Telegram sends POST requests here instantly when a message arrives.
No polling — zero latency, scales to zero when idle (free).

Deploy:
  gcloud run deploy cad-telegram-bot --source . --region us-central1 --allow-unauthenticated

Then set webhook:
  https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-url>.run.app/webhook
"""

import os, json, logging, io
from flask import Flask, request, jsonify, send_file, abort
import telegram_agent as ta
from country_ppt_builder import build as build_ppt

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Shared secret between Telegram setWebhook and this endpoint.
# Telegram includes it in the X-Telegram-Bot-Api-Secret-Token header on every
# inbound request. Anything missing or mismatching is dropped — this is the
# only thing standing between --allow-unauthenticated and the open internet.
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()


@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive update from Telegram, process immediately, return 200."""
    # ── Authentication via Telegram secret token ──
    if TELEGRAM_WEBHOOK_SECRET:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if header_token != TELEGRAM_WEBHOOK_SECRET:
            log.warning(
                f"webhook: rejected request with bad secret token "
                f"(remote={request.remote_addr}, header_len={len(header_token)})")
            return "Forbidden", 403
    else:
        # Refuse to run wide-open if the secret was never configured
        log.error("webhook: TELEGRAM_WEBHOOK_SECRET not configured — rejecting all requests")
        return "Service not configured", 503

    try:
        update = request.get_json(silent=True, force=True)
        if update:
            # Only log AFTER the secret check passes — otherwise an attacker can
            # fill Cloud Run logs cheaply by spraying junk POSTs.
            chat_id = (update.get("message", {}).get("chat", {}).get("id")
                       or update.get("edited_message", {}).get("chat", {}).get("id"))
            log.info(f"webhook: chat_id={chat_id} update_id={update.get('update_id')}")
            ta.process_updates([update])
    except Exception as e:
        log.error(f"webhook error: {e}")
    # Telegram retries on non-200; always return 200 on processing failure
    return "OK", 200


# ─── /generate-ppt — single source of truth for dashboard, agents, and chat ──
@app.route("/generate-ppt", methods=["POST", "OPTIONS"])
def generate_ppt():
    """Accept a country-brief context JSON; return a 12-slide PPTX."""
    # CORS — dashboard is on GitHub Pages, this is on Cloud Run
    if request.method == "OPTIONS":
        return _cors_preflight()
    try:
        ctx = request.get_json(silent=True, force=True) or {}
        if not ctx.get("country"):
            return _json_error("Missing 'country' in context", 400)
        country = ctx["country"]
        log.info(f"PPT request for {country}")

        # ─── Map rendering (best-effort, never blocks PPT build) ──────────
        # See docs/MAP_RENDERER_CONTRACT.md for the full integration spec.
        # Status is reported back in the X-Map-Status response header so the
        # dashboard / curl callers can see at a glance whether the renderer
        # fired without inspecting server logs.
        map_status = "none"   # ok | failed | skipped | none
        map_bytes  = 0
        if not (ctx.get("map") or {}).get("image_bytes"):
            try:
                from country_map_renderer import render as render_map
                png = render_map(
                    country=country,
                    iso2=ctx.get("iso2", ""),
                    lat=ctx.get("lat"),
                    lng=ctx.get("lng"),
                    type="reference",            # Option A per integration spec
                    indicators=ctx.get("indicators"),
                    subnational_indicators=ctx.get("subnational_indicators"),
                    color_scale="severity",
                    show_neighbors=True,
                )
                if png:
                    ctx.setdefault("map", {})
                    ctx["map"]["image_bytes"] = png
                    ctx["map"].setdefault("type",   "reference")
                    ctx["map"].setdefault("title",  f"{country} — Development Overview")
                    ctx["map"].setdefault("source", "World Bank WDI; Natural Earth boundaries")
                    map_status = "ok"
                    map_bytes  = len(png)
                    log.info(f"Map rendered for {country} ({map_bytes:,} bytes)")
                else:
                    map_status = "none"
                    log.info(f"Map renderer returned None for {country} — using placeholder")
            except ImportError:
                map_status = "skipped"
                log.info("country_map_renderer not installed — using placeholder")
            except Exception as e:
                map_status = "failed"
                log.warning(f"Map renderer failed for {country}: {e}")
        else:
            map_status = "ok"   # caller pre-supplied the map
            mb = (ctx.get("map") or {}).get("image_bytes")
            if isinstance(mb, (bytes, bytearray)):
                map_bytes = len(mb)
            elif isinstance(mb, str):
                # base64-encoded; estimate decoded length (~ 3/4 of string)
                try:
                    import base64 as _b64
                    s = mb.split(",", 1)[1] if mb.startswith("data:") else mb
                    map_bytes = len(_b64.b64decode(s))
                except Exception:
                    map_bytes = 0

        pptx_bytes = build_ppt(ctx, output=None)
        fname = f"{country.replace(' ','_')}_brief.pptx"
        resp = send_file(
            io.BytesIO(pptx_bytes),
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            as_attachment=True,
            download_name=fname,
        )
        # Debug headers — see docs/MAP_RENDERER_CONTRACT.md §8
        resp.headers["X-Map-Status"] = map_status
        if map_bytes:
            resp.headers["X-Map-Bytes"] = str(map_bytes)
        resp.headers["Access-Control-Allow-Origin"]   = "*"
        resp.headers["Access-Control-Expose-Headers"] = "Content-Disposition, X-Map-Status, X-Map-Bytes"
        return resp
    except Exception as e:
        log.exception("PPT generation failed")
        return _json_error(f"PPT build failed: {e}", 500)


def _cors_preflight():
    resp = jsonify({"ok": True})
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Max-Age"]       = "3600"
    return resp


def _json_error(msg, code):
    resp = jsonify({"error": msg})
    resp.status_code = code
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "CAD Telegram Bot"}), 200


@app.route("/", methods=["GET"])
def root():
    return "CAD Telegram Bot + PPT service is running.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
