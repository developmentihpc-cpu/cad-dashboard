#!/usr/bin/env python3
"""
evaluator_score_server.py — local AI scoring endpoint for the Project Evaluator.

The evaluator (docs/evaluator.html) "AI" mode POSTs a project + the 22 criteria to
this endpoint and renders the returned scores. A static GitHub Pages site cannot
hold an API key or run Python, so — consistent with the GitHub-only architecture —
the scoring brain runs locally on your machine, reading ANTHROPIC_API_KEY from .env.
No cloud, no secrets in the repo.

Run:
    python evaluator_score_server.py            # listens on http://localhost:8787
    SCORE_PORT=9000 python evaluator_score_server.py
    SCORING_MODEL=claude-sonnet-4-20250514 python evaluator_score_server.py

Endpoints:
    GET  /health  -> {ok, model, key}
    POST /score   <- {project, classification, narrative, criteria:[{id,name,dimension,type,description,min}]}
                  -> {scores:{<id>:{score,confidence,rationale,evidence,redFlag,missingInfo}}}

The deterministic engine in the browser still owns weighting, thresholds, the
composite and the recommendation — this server only produces the per-criterion
score + prose, exactly as the AI-scoring spec requires.
"""
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PORT = int(os.environ.get("SCORE_PORT", "8787"))
MODEL = os.environ.get("SCORING_MODEL", "claude-opus-4-5")
MAX_TOKENS = int(os.environ.get("SCORING_MAX_TOKENS", "9000"))
# Web search lets the scorer verify partner track records (e.g. ECW), implementer
# reputation, and current country/sector context. On by default; SCORING_WEB_SEARCH=0 disables.
WEB_SEARCH = os.environ.get("SCORING_WEB_SEARCH", "1").lower() not in ("0", "false", "no", "off")
WEB_MAX_USES = int(os.environ.get("SCORING_WEB_MAX_USES", "5"))


def load_env():
    env = {}
    f = BASE_DIR / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    for k in ("ANTHROPIC_API_KEY",):
        if k not in env and k in os.environ:
            env[k] = os.environ[k]
    return env


ENV = load_env()

SYSTEM = """You are the Project Evaluation scorer for the Office of Development Affairs (ODA),
an international development funding body. You score a single submitted project against a
fixed set of criteria supplied in the user message. You return ONLY data — no prose outside JSON.

For every criterion produce: a 0–100 score, a confidence (high|medium|low), a one- to
two-sentence rationale, an evidence/source string, and two booleans (redFlag, missingInfo).

RUBRIC (apply per criterion):
  85–100  Strong — fully addressed, robust evidence
  65–84   Good — well addressed, minor gaps
  45–64   Moderate — partially addressed, notable gaps
  25–44   Weak — barely addressed, significant gaps
  0–24    Poor — not addressed or strong negative evidence

RISK criteria (the criterion's name/description references risk) are INVERTED:
  higher score = LOWER risk. 85–100 = negligible risk … 0–24 = severe risk.
  State the risk level in the rationale.

QUALITATIVE criteria (type = "qual"): score from the proposal narrative. The rationale must
  reference the specific part it relies on (quote a phrase or name the section). If the
  proposal is silent on the criterion, do NOT guess — give a low-confidence Moderate-or-below
  score, set missingInfo=true, and say what is missing.

QUANTITATIVE criteria (type = "quant"): the rationale must show a value, a benchmark/comparison,
  and a source. Use only numbers present in the project/narrative or that you can compute from
  the project's own figures. NEVER fabricate a statistic. If a required figure is unavailable,
  set "evidence":"Not available", set missingInfo=true, score at reduced confidence, and say so.

redFlag = true for a serious, decision-relevant concern (e.g. high political/financial risk,
  duplication, weak safeguards). missingInfo = true when the proposal lacks the information
  needed to score the criterion properly.

WEB SEARCH: You have a web_search tool. Use it sparingly and ONLY to verify decision-relevant
  external facts the proposal cannot supply — e.g. a proposed partner/implementer's track record
  and credibility (such as ECW / Education Cannot Wait), the implementing organisation's reputation
  or recent performance, or current country/sector context (recent conflict, displacement, economic
  shock). Do NOT search for figures the proposal already provides, and do not pad rationales with
  search results that don't change a score. When a score relies on a searched fact, the "evidence"
  string MUST name the source — publication or organisation plus a URL where available. An external
  claim with no cited source is treated as a fabrication and is not permitted. If a search returns
  nothing usable, fall back to the proposal and lower the confidence. All anti-fabrication rules
  above still apply in full. After searching, still return ONLY the JSON object — no other prose.

Return ONLY a JSON object, no markdown fences, of the exact form:
{"scores":{"<criterion_id>":{"score":<0-100 int>,"confidence":"high|medium|low",
"rationale":"...","evidence":"...","redFlag":false,"missingInfo":false}, ...}}
Include every criterion id given. Output nothing else."""


PARTNER_SYSTEM = """You are the Partnership & Strategic Due-Diligence layer for the Office of Development
Affairs (ODA), a neutral assessor. Given a proposed delivery PARTNER and the project it would deliver,
assess three things INDEPENDENTLY of the project's own merit: (1) the partner as a funding vehicle,
(2) the UAE's strategic value in funding through it, and (3) what each funding band unlocks.

Use the web_search tool to ground EVERY changeable fact (funding position, leadership, donors, results,
controversies) in PRIMARY sources — the entity's annual report, audited accounts, independent evaluations,
official donor lists — in preference to press aggregators. Record a source and a date for every figure.
Distinguish PLEDGED from RECEIVED. Treat every figure as as-of-its-date.

Discipline: neutral assessor voice; British spelling; concise. Where public evidence is thin, SAY SO —
never present inference as fact. Flag anything that should be confirmed directly with the entity.

Scoring 0–100: 85–100 strong, 65–84 good, 45–64 moderate, 25–44 weak, 0–24 poor.
Partner verdict: "sound" (score >=70), "acceptable-with-conditions" (45–69), or "avoid" (<45).

FUNDING RECOMMENDATION — base it on BOTH the partner (soundness + strategic value) AND the project's own
merit (the PROJECT EVALUATION supplied below). Evaluate each funding band's suitability given both, then
name one recommendedBand and explain it. A weak or risky project pulls toward a smaller, phased band (or
none); a strong project with a sound partner supports a larger band. If project merit is UNASSESSED (the
project is not yet defined), the funding options are the unit of decision: treat EACH funding band as a
DISTINCT CANDIDATE PROJECT — propose a concrete intervention this partner could credibly deliver at that
funding level (vary scope/ambition to fit the amount), assess its merit and partner-fit, and give it a
comparative score (0–100). Populate scenarios[].option (the proposed project), scenarios[].assessment
(its merit) and scenarios[].score for each. Then set recommendedBand to the strongest candidate and, in
"recommendation", explain why it beats the other two and that it remains provisional until the chosen
project is formally defined and scored.

If FUNDING BANDS are to be PROPOSED (the user has supplied none / asked you to propose), choose three
sensible funding amounts yourself — anchored to the partner's typical engagement/grant sizes and the
country/sector context — and use them as the scenario bands (set scenarios[].band to your chosen amounts,
e.g. "US$5M", and recommendedBand to one of them).

UAE HISTORICAL ENGAGEMENTS — research (web_search) the UAE's and Gulf donors' PAST engagements with this
partner, sector and country (prior grants, pledges, co-financing, MoUs). Use them to INFORM the
recommendation only — do not score them. List the key precedents in "uaePrecedents" and reference the most
relevant in the "recommendation" sentence (e.g. "consistent with the UAE's 2022 $X to …"). Distinguish
pledged from disbursed; if no precedent is found, say so and set uaePrecedents to [].

EVERY score — the two headline scores AND each factor score — MUST carry a justification that states
the evidence behind it (a figure, a date, a named source, or an explicit "no public evidence found").
A headline score must be consistent with its factors. Do not give a number without saying why.

Return ONLY a JSON object, no markdown fences, of exactly this shape:
{
 "soundness": {"score": <int 0-100>, "verdict": "sound|acceptable-with-conditions|avoid", "summary": "<=2 sentences explaining the headline score",
   "factors": [
     {"name":"Track record","score": <int>, "justification":"independently-verified results; figures + source + date"},
     {"name":"Financial resilience","score": <int>, "justification":"trajectory, reserves, donor concentration, unpaid-pledge/unfunded-plan history; figures + source"},
     {"name":"Governance & leadership","score": <int>, "justification":"stability; explicitly flag interim/transition status"},
     {"name":"Implementing ecosystem","score": <int>, "justification":"quality/breadth of delivery partners and oversight"}
   ]},
 "risks": [{"type":"Financial|Governance|Reputational|Access|Operating context","severity":"high|medium|low","note":"specific, with evidence"}],
 "uae": {"score": <int 0-100>, "summary":"<=2 sentences explaining the headline score",
   "factors": [
     {"name":"Strategic alignment","score": <int>, "justification":"fit with UAE foreign-policy geographies/sectors"},
     {"name":"Visibility & attribution","score": <int>, "justification":"named credit/board access/co-branding; note where pooled funding dilutes attribution"},
     {"name":"Differentiation","score": <int>, "justification":"lead vs join a crowded field"},
     {"name":"Complementarity","score": <int>, "justification":"fit with existing UAE channels; avoid cannibalising any foundation footprint"},
     {"name":"Risk by association","score": <int>, "justification":"reputational exposure from the partner/its other backers"}
   ]},
 "scenarios": [{"band":"<exactly as supplied>","option":"if project unassessed: the concrete candidate intervention this funding level would deliver (a distinct project); else ''","assessment":"merit & partner-fit of this option (impact, feasibility)","score": "comparative merit 0-100 when treated as a candidate project, else null","unlocks":"what this tranche unlocks","marginalValue":"marginal value vs the band below","influence":"level of visibility/governance influence secured"}],
 "phasing": "recommended headline-pledge vs milestone-disbursement structure where partner fragility warrants it, else 'Not required'",
 "milestones": ["3–5 concrete conditions the phased release is conditioned on — e.g. scope/results framework agreed, in-country access independently verified, named attribution confirmed, later tranches released only on verified results against a baseline"],
 "recommendedBand": "the single funding band you recommend (copied EXACTLY from a supplied band, or one you proposed if asked to propose; '' if none is justified)",
 "uaePrecedents": [{"engagement":"what the UAE/Gulf donor did","year":"YYYY","amount":"if known, pledged vs disbursed","note":"relevance to this decision","url":"source"}],
 "recommendation": "one reconciled sentence across project / partner / UAE lenses, naming the recommended funding band, any safeguards, and referencing the most relevant UAE precedent",
 "leadership": {
   "whyProceed": ["3 strongest reasons to proceed — the best version of the case, not buried sub-scores"],
   "whyHold": ["3 strongest reasons to hold back / the counter-case — the best version of it"],
   "topRiskMitigation": "one line: how the single biggest risk is mitigated",
   "strategicLead": "1–2 sentences: the positional 'why act now' case (read as a position, not a transaction)",
   "sequence": [{"tag":"NOW","title":"...","detail":"the entry move"},{"tag":"NEXT","title":"...","detail":"the leverage step"},{"tag":"BEYOND","title":"...","detail":"the leadership step"}],
   "confidenceNote": "what drives the confidence level and the single weakest-evidenced claim"
 },
 "verify": ["fact to confirm directly with the entity before commitment", "..."],
 "confidence": "high|medium|low",
 "sources": [{"title":"...","publisher":"...","date":"YYYY[-MM]","url":"...","for":"what claim it supports","independent": true}]
}
For each source set "independent": false when it is the partner's OWN publication (or an affiliate's) — i.e. self-reported — and true only for genuinely independent sources (audits, external evaluations, other donors, reputable press).
Include exactly one scenarios entry per funding band supplied, in order. Output nothing else."""


def get_client():
    import anthropic
    key = ENV.get("ANTHROPIC_API_KEY", "")
    if not key or key.startswith("sk-ant-xxx"):
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
    return anthropic.Anthropic(api_key=key)


def build_user(payload):
    p = payload.get("project", {}) or {}
    cl = payload.get("classification", {}) or {}
    narrative = (payload.get("narrative") or "").strip()
    crit = payload.get("criteria", []) or []

    lines = [
        "PROJECT",
        f"  Title: {p.get('title') or '—'}",
        f"  Country: {p.get('country') or '—'}",
        f"  Sector: {p.get('sector') or '—'}",
        f"  Total cost: {p.get('cost') or '—'}",
        f"  Beneficiaries: {p.get('ben') or '—'}",
        f"  Duration: {p.get('dur') or '—'}",
        f"  Stream: {cl.get('stream') or '—'} | Financing: {cl.get('finance') or '—'} | "
        f"Leadership gate: {cl.get('gate') or '—'}",
        "",
        "PROPOSAL NARRATIVE",
        narrative if narrative else "(no narrative provided)",
        "",
        "CRITERIA TO SCORE (score every id):",
    ]
    for c in crit:
        mn = c.get("min")
        knock = f" [knockout: min {mn}]" if mn not in (None, "") else ""
        lines.append(
            f"  - id={c.get('id')} | {c.get('name')} ({c.get('type')}) "
            f"| dimension={c.get('dimension')}{knock}\n      {c.get('description','')}"
        )
    lines.append("")
    lines.append('Return ONLY the JSON object {"scores":{...}} described in the system prompt.')
    return "\n".join(lines)


def _extract_json(text):
    """Pull the first balanced {...} object out of the model text."""
    text = text.strip()
    # strip accidental code fences
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in model output")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON in model output")


def _coerce(scores, criteria):
    """Normalise the model output to the exact shape the evaluator expects."""
    out = {}
    for c in criteria:
        cid = c.get("id")
        r = (scores or {}).get(cid, {}) or {}
        try:
            sc = int(round(float(r.get("score"))))
            sc = max(0, min(100, sc))
        except Exception:
            sc = None
        out[cid] = {
            "score": sc,
            "confidence": (r.get("confidence") or r.get("conf") or "low"),
            "rationale": (r.get("rationale") or "").strip(),
            "evidence": (r.get("evidence") or "").strip(),
            "redFlag": bool(r.get("redFlag")),
            "missingInfo": bool(r.get("missingInfo")) or sc is None,
        }
    return out


def _run(client, base, tools=None):
    """One logical turn. Transparently continues across `pause_turn`, which the API
    returns mid server-side web search. Returns (final_message, total_search_count)."""
    messages = [dict(m) for m in base["messages"]]
    searches = 0
    last = None
    for _ in range(5):
        kw = dict(base, messages=messages)
        if tools:
            kw["tools"] = tools
        last = client.messages.create(**kw)
        searches += sum(1 for b in last.content if getattr(b, "type", "") == "server_tool_use")
        if getattr(last, "stop_reason", None) == "pause_turn":
            messages.append({"role": "assistant", "content": last.content})
            continue
        break
    return last, searches


def score(payload):
    client = get_client()
    crit = payload.get("criteria", []) or []
    base = dict(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_user(payload)}],
    )
    used_web, searches = False, 0
    if WEB_SEARCH:
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": WEB_MAX_USES}]
        try:
            msg, searches = _run(client, base, tools)
            used_web = True
        except Exception as e:
            # SDK too old / model rejects the tool / search error → score without the web.
            sys.stderr.write(f"[score] web_search unavailable, scoring without it: {e}\n")
            msg, searches = _run(client, base)
    else:
        msg, searches = _run(client, base)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(text)
    scores = data.get("scores", data)
    return {"scores": _coerce(scores, crit), "model": MODEL,
            "webSearch": used_web, "searches": searches}


def _check_url(u):
    """True if the URL resolves (HEAD, then GET fallback). Bounded by a short timeout."""
    if not u or not str(u).startswith("http"):
        return False
    hdr = {"User-Agent": "Mozilla/5.0 (ODA-evaluator source check)"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers=hdr)
            with urllib.request.urlopen(req, timeout=5) as r:
                return 200 <= getattr(r, "status", r.getcode()) < 400
        except Exception:
            continue
    return False


def _validate_sources(srcs):
    """Mark each source ok (URL resolves) and ageing (>= 2 years old)."""
    if not isinstance(srcs, list):
        return
    urls = [(i, s.get("url")) for i, s in enumerate(srcs) if isinstance(s, dict) and s.get("url")]
    if urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            for i, ok in ex.map(lambda iu: (iu[0], _check_url(iu[1])), urls):
                srcs[i]["ok"] = ok
    yr = datetime.now(timezone.utc).year
    for s in srcs:
        if isinstance(s, dict):
            m = re.match(r"(\d{4})", str(s.get("date") or ""))
            if m:
                s["ageing"] = (yr - int(m.group(1))) >= 2


def build_partner_user(payload):
    p = payload.get("project", {}) or {}
    partner = (payload.get("partner") or p.get("partner") or "").strip()
    cl = payload.get("classification", {}) or {}
    pe = payload.get("projectEval") or {}
    propose = bool(payload.get("proposeAmounts")) and not payload.get("scenarios")
    bands = payload.get("scenarios") or ["US$5M", "US$25M", "US$100M"]
    bands_line = ("FUNDING BANDS: none supplied — PROPOSE three sensible funding amounts yourself "
                  "(anchored to the partner's typical engagement sizes and the context) and use them as the scenario bands."
                  if propose else
                  "FUNDING BANDS to run sensitivity on (one scenarios entry each, in order): " + ", ".join(bands))
    return "\n".join([
        f"PARTNER (delivery vehicle to assess): {partner or '(none named)'}",
        "",
        "PROJECT IT WOULD DELIVER",
        f"  Title: {p.get('title') or '—'}",
        f"  Country / scope: {p.get('country') or '—'}",
        f"  Sector: {p.get('sector') or '—'}",
        f"  Total cost: {p.get('cost') or '—'} | Beneficiaries: {p.get('ben') or '—'} | Duration: {p.get('dur') or '—'}",
        f"  Stream: {cl.get('stream') or '—'} | Financing: {cl.get('finance') or '—'}",
        "",
        "PROJECT EVALUATION (Layer 1, by ODA — weigh this in the funding recommendation):",
        ("  Project merit: UNASSESSED — the project is not yet defined; the funding options are the decision."
         if pe.get("unassessable") else
         f"  Project merit: {pe.get('composite')}/100 — {pe.get('verdict') or '—'}"),
        f"  Framework coverage: {pe.get('coverage', '—')}%",
        ("  Concerns flagged: " + ", ".join(pe.get("concerns", []))) if pe.get("concerns") else "  Concerns flagged: none",
        "",
        bands_line,
        "",
        "Research the partner AND the UAE's historical engagements live via web_search; return the JSON object specified in the system prompt.",
    ])


def partner(payload):
    client = get_client()
    base = dict(model=MODEL, max_tokens=MAX_TOKENS, system=PARTNER_SYSTEM,
                messages=[{"role": "user", "content": build_partner_user(payload)}])
    used_web, searches = False, 0
    # partner DD is inherently a research task — always attempt web search, with more budget.
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": max(WEB_MAX_USES, 8)}]
    try:
        msg, searches = _run(client, base, tools)
        used_web = True
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[partner] web_search unavailable, researching without it: {e}\n")
        msg, searches = _run(client, base)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(text)
    _validate_sources(data.get("sources"))
    data.update({"partner": (payload.get("partner") or "").strip(),
                 "model": MODEL, "webSearch": used_web, "searches": searches})
    return data


VERIFY_SYSTEM = """You are an INDEPENDENT ADVERSARIAL REVIEWER for the Office of Development Affairs (ODA).
You are handed a partner-and-strategic assessment another analyst produced. Your job is to try to REFUTE it,
not to agree with it. Identify the most decision-relevant factual claims (key figures, track record, financial
position, governance, the headline scores and the recommendation) and test each against PRIMARY, INDEPENDENT
sources using the web_search tool.

Be sceptical. Default to "unverified" when you cannot independently corroborate a claim. Treat the partner's
own publications as self-reported, not verification. Never invent a source. British spelling; neutral; concise.

Verdicts: "confirmed" (independent source agrees), "refuted" (independent source contradicts), "unverified"
(could not corroborate independently). Overall "verdict": does the recommendation survive scrutiny —
"holds", "holds-with-caveats", or "does-not-hold".

Return ONLY this JSON, no fences:
{
 "checks": [{"claim":"<quoted/paraphrased claim>","verdict":"confirmed|refuted|unverified","finding":"what independent evidence shows","source":{"title":"","url":"","date":"YYYY[-MM]"}}],
 "concerns": ["material problem a decision-maker must know before committing"],
 "overallConfidence": "high|medium|low",
 "verdict": "holds|holds-with-caveats|does-not-hold"
}
Cover the 5–8 most material claims. Output nothing else."""


def build_verify_user(payload):
    a = payload.get("assessment", {}) or {}
    p = payload.get("project", {}) or {}
    keep = {k: a.get(k) for k in ("soundness", "uae", "risks", "recommendation", "recommendedBand", "scenarios") if k in a}
    return "\n".join([
        f"PARTNER: {payload.get('partner') or a.get('partner') or '—'}",
        f"PROJECT: {p.get('title') or '—'} · {p.get('country') or '—'} · {p.get('sector') or '—'}",
        "",
        "ASSESSMENT TO SCRUTINISE (JSON):",
        json.dumps(keep, ensure_ascii=False)[:6000],
        "",
        "Attempt to refute the material claims and the recommendation. Return the JSON specified.",
    ])


def verify(payload):
    client = get_client()
    base = dict(model=MODEL, max_tokens=MAX_TOKENS, system=VERIFY_SYSTEM,
                messages=[{"role": "user", "content": build_verify_user(payload)}])
    used_web, searches = False, 0
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": max(WEB_MAX_USES, 8)}]
    try:
        msg, searches = _run(client, base, tools)
        used_web = True
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[verify] web_search unavailable, verifying without it: {e}\n")
        msg, searches = _run(client, base)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(text)
    for c in (data.get("checks") or []):
        if isinstance(c, dict) and isinstance(c.get("source"), dict) and c["source"].get("url"):
            c["source"]["ok"] = _check_url(c["source"]["url"])
    data.update({"model": MODEL, "webSearch": used_web, "searches": searches})
    return data


PROPOSE_SYSTEM = """You are a project-origination analyst for the Office of Development Affairs (ODA).
Given a delivery PARTNER and a SECTOR / area of interest (but no defined project), propose THREE DISTINCT,
credible candidate interventions this partner could deliver in that sector. Vary them meaningfully — by
geography, modality and scale — so they are genuinely different options, not three sizes of one project.

Use web_search to ground each proposal in the partner's real programmes/modalities and the country/sector
context, and to check the UAE's and Gulf donors' historical engagements — use the latter to INFORM which
option to recommend and cite the key precedents. Autofill plausible parameters but treat them as
PROPOSED/indicative; never present invented figures as committed. Distinguish pledged from disbursed.
British spelling; neutral; concise.

For each proposed project provide enough for ODA's 22-criteria evaluation to score it: a title, country,
sector, an indicative cost and beneficiary count (labelled indicative), a duration, and a 4–6 sentence
NARRATIVE covering need, theory of change, delivery/partner role, measurability and sustainability.

Return ONLY this JSON, no fences:
{
 "projects": [
   {"title":"...","country":"...","sector":"...","cost":"e.g. US$25M (indicative)","ben":"indicative number","dur":"e.g. 24 months","modality":"how delivered","narrative":"4–6 sentences for scoring"}
 ],
 "recommendedIndex": 0,
 "rationale":"why the recommended option beats the other two, informed by partner soundness and UAE precedent",
 "uaePrecedents":[{"engagement":"...","year":"YYYY","amount":"pledged vs disbursed if known","note":"relevance","url":"source"}],
 "sources":[{"title":"...","publisher":"...","date":"YYYY[-MM]","url":"...","for":"what it supports"}]
}
Exactly three projects. Output nothing else."""


def build_propose_user(payload):
    partner = (payload.get("partner") or "").strip()
    cl = payload.get("classification", {}) or {}
    p = payload.get("project", {}) or {}
    return "\n".join([
        f"PARTNER: {partner or '(none named)'}",
        f"SECTOR / area of interest: {p.get('sector') or '—'}",
        f"Country / region focus (if any): {p.get('country') or '(none — you may choose, vary across the three)'}",
        f"Stream: {cl.get('stream') or '—'} | Financing: {cl.get('finance') or '—'}",
        "",
        "Propose three distinct candidate projects (vary geography/modality/scale) and return the JSON specified.",
    ])


def propose(payload):
    client = get_client()
    base = dict(model=MODEL, max_tokens=MAX_TOKENS, system=PROPOSE_SYSTEM,
                messages=[{"role": "user", "content": build_propose_user(payload)}])
    used_web, searches = False, 0
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": max(WEB_MAX_USES, 8)}]
    try:
        msg, searches = _run(client, base, tools)
        used_web = True
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[propose] web_search unavailable: {e}\n")
        msg, searches = _run(client, base)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(text)
    _validate_sources(data.get("sources"))
    data.update({"model": MODEL, "webSearch": used_web, "searches": searches})
    return data


COUNTRY_MAX_TOKENS = int(os.environ.get("COUNTRY_MAX_TOKENS", "16000"))

COUNTRY_SYSTEM = """You are the Country Needs Assessment researcher for the Office of Development Affairs (ODA).
Given a country and a baseline of World Bank indicators, produce a rigorous, fully-sourced,
sector-by-sector assessment for a senior leadership audience (the ODA country-assessment deck).

RESEARCH LIVE. Use web search to gather the most recent figures from PRIMARY sources:
World Bank, IMF, WHO (incl. GHED), UNICEF / UN IGME, UNESCO UIS, FAO (incl. SOFI), WHO/UNICEF JMP,
ITU, IEA, ILO, OCHA / ReliefWeb, and the country's own national statistics office and central bank.
Treat the provided World Bank baseline as a floor; prefer and CITE the most recent primary figure.

RULES
- EVERY numeric stat MUST carry a real source and year. NEVER invent a figure. If a figure cannot be
  found, omit that stat rather than guess. Prefer figures from the last 3 years.
- Prose must be tight and analytical (leadership register): what the number means and where the gap is.
  Two to four sentences of substance per sector, distilled into the fields below.
- Interventions must be concrete and country-specific (name real programmes, regions, or instruments
  where possible), never generic boilerplate.
- LENGTH LIMITS (strict — these render into fixed slide space):
    * each sector "statement": ONE headline sentence, <= 16 words.
    * each "sectorStatus" note: <= 8 words (e.g. "U5 mortality 16/1,000; rural reach gaps").
    * each "crossSector" line: <= 9 words; "recommended": <= 16 words.
    * each "insights" item: <= 24 words. each "interventions" item: <= 14 words.
    * each stat "label": <= 5 words; "value": a short token (e.g. "16.3", "8.4%", "$18.5K").
- Return STRICT JSON ONLY — no prose outside the JSON, no markdown fences, no trailing commentary.

OUTPUT JSON SHAPE (use these exact keys):
{
 "subtitle": string,                     // e.g. "Republica del Paraguay - Heart of South America"
 "incomeClass": string,                  // e.g. "Developing - Upper-Middle Income"
 "sectorStatus": [                        // EXACTLY 6, in this order:
   {"sector":"Health","note":string,"status":"Improving"|"Developing"|"Weak"|"Severe"},
   {"sector":"Education", ...}, {"sector":"Food Security", ...},
   {"sector":"WASH", ...}, {"sector":"Economic", ...}, {"sector":"Infrastructure", ...} ],
 "sectors": {
   "economy":        {"statement":string,"stats":[{"value":string,"label":string,"source":string,"year":string} x3-4],"insights":[string x3],"interventions":[string x4]},
   "health":         {...}, "education": {...}, "food": {...}, "agriculture": {...},
   "infrastructure": {...}, "wash": {...}, "energy": {...}
 },
 "crossSector": [                         // EXACTLY 6 (Health, Education, Food Security, Agriculture, Infrastructure, WASH)
   {"sector":string,"status":"Improving"|"Developing"|"Weak"|"Severe","lines":[string,string],"recommended":string}, ... ],
 "sources": [ {"label":string,"url":string}, ... up to 12 primary sources actually consulted ],
 "confidence": "high"|"medium"|"low"
}"""


def country_research(payload):
    """Live, multi-source country needs assessment -> the enriched deck-research model
    consumed by docs/country_deck.js (buildCountryDeck opts.research)."""
    client = get_client()
    country = payload.get("country") or "the country"
    info = payload.get("countryInfo") or {}
    inds = payload.get("indicators") or {}
    lines = []
    for k, v in inds.items():
        if isinstance(v, dict) and v.get("value") is not None:
            lines.append("%s = %s (%s)" % (k, v.get("value"), v.get("year", "")))
    baseline = "\n".join(lines[:90]) or "(no baseline indicators supplied)"
    user = (
        "COUNTRY: %s\n"
        "Capital: %s | Currency: %s | Languages: %s\n\n"
        "WORLD BANK BASELINE INDICATORS (id = value (year)):\n%s\n\n"
        "Produce the ODA country needs assessment JSON for %s per your instructions. "
        "Research the latest primary-source figures across every sector and cite each one."
        % (country, info.get("capital", "—"), info.get("currency", "—"),
           info.get("languages", "—"), baseline, country)
    )
    base = dict(model=MODEL, max_tokens=COUNTRY_MAX_TOKENS, system=COUNTRY_SYSTEM,
                messages=[{"role": "user", "content": user}])
    used_web, searches = False, 0
    if WEB_SEARCH:
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": max(WEB_MAX_USES, 16)}]
        try:
            msg, searches = _run(client, base, tools)
            used_web = True
        except Exception as e:  # noqa: BLE001
            sys.stderr.write("[country] web_search unavailable, researching without it: %s\n" % e)
            msg, searches = _run(client, base)
    else:
        msg, searches = _run(client, base)
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    data = _extract_json(text)
    if isinstance(data.get("sources"), list):
        try:
            _validate_sources(data["sources"])
        except Exception:
            pass
    data.update({"country": country, "model": MODEL, "webSearch": used_web, "searches": searches})
    return data


def make_deck(payload):
    """Run the canonical generators on a posted deck-data model; save deck + one-pager to Downloads."""
    data = payload.get("deckData") or payload
    name = (data.get("partnerShort") or data.get("partner") or "partnership")
    slug = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_") or "partnership"
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    tmp = BASE_DIR / ("_deckdata_%s.json" % slug)
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    deck = os.path.join(downloads, slug + "_Leadership_Deck.pptx")
    onep = os.path.join(downloads, slug + "_Leadership_OnePager.pdf")
    out = {"ok": True}
    try:
        subprocess.run(["node", "generate_partnership_deck.js", str(tmp), deck],
                       cwd=str(BASE_DIR), check=True, capture_output=True, timeout=120)
        out["deck"] = deck
    except Exception as e:  # noqa: BLE001
        out["ok"] = False; out["deckError"] = (getattr(e, "stderr", b"") or b"").decode("utf-8", "ignore")[:400] or str(e)[:400]
    try:
        subprocess.run([sys.executable, "generate_partnership_onepager.py", str(tmp), onep],
                       cwd=str(BASE_DIR), check=True, capture_output=True, timeout=120)
        out["onepager"] = onep
    except Exception as e:  # noqa: BLE001
        out["ok"] = False; out["onepagerError"] = (getattr(e, "stderr", b"") or b"").decode("utf-8", "ignore")[:400] or str(e)[:400]
    return out


def country_report(payload):
    """Build the EXACT 23-slide ODA country-proposal deck by filling the bundled template
    (country_report/assets/country_proposal_template.pptx) via build_country_report.py:
    live research rewrites every slot, flag + ADM1 maps are fetched, fill_template builds it.
    Long-running (~15-25 min, multiple web-search passes). Saves to ~/Downloads."""
    country = (payload.get("country") or "").strip()
    if not country:
        return {"ok": False, "error": "no country supplied"}
    iso2 = (payload.get("iso2") or "").strip()
    iso3 = (payload.get("iso3") or "").strip()
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", country).strip("_") or "country"
    out = os.path.join(downloads, slug + "_Country_Proposal.pptx")
    cmd = [sys.executable, "build_country_report.py", country]
    if iso2:
        cmd += ["--iso2", iso2]
    if iso3:
        cmd += ["--iso3", iso3]
    cmd += ["--out", out]
    try:
        r = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           env={**os.environ, "PYTHONUTF8": "1"}, timeout=2400)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "report build timed out (>40 min)"}
    if r.returncode != 0:
        return {"ok": False, "error": ((r.stderr or "") + (r.stdout or ""))[-700:] or "build failed"}
    return {"ok": True, "file": out, "log": (r.stdout or "")[-500:]}


class Handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/health"):
            self._json(200, {"ok": True, "model": MODEL,
                             "key": bool(ENV.get("ANTHROPIC_API_KEY")),
                             "webSearch": WEB_SEARCH})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        route = ("score" if self.path.startswith("/score")
                 else "partner" if self.path.startswith("/partner")
                 else "verify" if self.path.startswith("/verify")
                 else "propose" if self.path.startswith("/propose")
                 else "country_report" if self.path.startswith("/country_report")
                 else "country" if self.path.startswith("/country")
                 else "deck" if self.path.startswith("/deck") else None)
        if not route:
            self._json(404, {"error": "not found"})
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            self._json(400, {"error": f"bad request: {e}"})
            return
        try:
            fn = {"score": score, "partner": partner, "verify": verify, "propose": propose, "country": country_research, "country_report": country_report, "deck": make_deck}[route]
            self._json(200, fn(payload))
        except Exception as e:
            self._json(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        sys.stderr.write("[score] " + (fmt % args) + "\n")


def main():
    print(f"[score] Project Evaluator scoring server")
    print(f"[score] listening on http://localhost:{PORT}/score   (model: {MODEL})")
    print(f"[score] API key loaded: {bool(ENV.get('ANTHROPIC_API_KEY'))}")
    print(f"[score] web search: {'ON (max %d/score)' % WEB_MAX_USES if WEB_SEARCH else 'OFF'}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
