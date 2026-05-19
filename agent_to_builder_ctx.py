"""
agent_to_builder_ctx.py
=======================
Bridge between agents_pipeline.py and country_ppt_builder.py.

Converts the agent-run state (ctx, agent_outputs, verdict) into the rich
13-slide context shape expected by country_ppt_builder.build().

Reads <Country>_context.json exported from the dashboard when available;
otherwise falls back to defaults derived from agent text outputs.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent


# ─── Country defaults ─────────────────────────────────────────────────────────
COUNTRY_INFO = {
    "Ethiopia":   {"iso2":"et","lat":9.145,"lng":40.4897,
                   "capital":"Addis Ababa","currency":"Ethiopian Birr (ETB)",
                   "languages":"Amharic, Oromo, Tigrinya",
                   "subtitle":"Federal Democratic Republic of Ethiopia · Horn of Africa"},
    "Jordan":     {"iso2":"jo","lat":31.95,"lng":35.93,
                   "capital":"Amman","currency":"Jordanian Dinar (JOD)",
                   "languages":"Arabic"},
    "Kenya":      {"iso2":"ke","lat":-1.286,"lng":36.817,
                   "capital":"Nairobi","currency":"Kenyan Shilling (KES)",
                   "languages":"Swahili, English"},
    "Bangladesh": {"iso2":"bd","lat":23.685,"lng":90.356,
                   "capital":"Dhaka","currency":"Taka (BDT)",
                   "languages":"Bengali"},
    "Yemen":      {"iso2":"ye","lat":15.55,"lng":48.52,
                   "capital":"Sana'a","currency":"Yemeni Rial (YER)",
                   "languages":"Arabic"},
    "Somalia":    {"iso2":"so","lat":5.15,"lng":46.20,
                   "capital":"Mogadishu","currency":"Somali Shilling (SOS)",
                   "languages":"Somali, Arabic"},
    "Somaliland": {"iso2":"so","lat":9.80,"lng":44.00,
                   "capital":"Hargeisa","currency":"Somaliland Shilling",
                   "languages":"Somali, Arabic, English",
                   "flag_url":"somaliland-flag.svg"},
}


def _load_dashboard_export(country: str) -> dict | None:
    safe = country.replace(" ", "_")
    for p in [BASE_DIR / f"{safe}_context.json",
              BASE_DIR / "agent_outputs" / f"{safe}_context.json"]:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def _extract_bullets(text: str, max_bullets: int = 4) -> list[str]:
    if not text:
        return []
    bullets = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s[0] in "-*•·" or re.match(r"^\d+[.)]\s", s):
            s = re.sub(r"^[-*•·]\s*", "", s)
            s = re.sub(r"^\d+[.)]\s*", "", s)
            if 8 <= len(s) <= 240:
                bullets.append(s)
        if len(bullets) >= max_bullets:
            break
    if len(bullets) < max_bullets:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if 20 <= len(sent) <= 240 and sent not in bullets:
                bullets.append(sent)
            if len(bullets) >= max_bullets:
                break
    return bullets[:max_bullets]


def _ind(indicators: dict, code: str):
    rec = indicators.get(code) if isinstance(indicators, dict) else None
    if not rec:
        return None
    return rec.get("value")


def _fmt_pct(v, default="—"):
    try: return f"{float(v):.1f}%"
    except Exception: return default


def _fmt_pop(v, default="—"):
    try:
        f = float(v)
        if f >= 1e9: return f"{f/1e9:.1f}B"
        if f >= 1e6: return f"{f/1e6:.0f}M"
        return f"{f:,.0f}"
    except Exception:
        return default


def _fmt_money(v, default="—"):
    try:
        f = float(v)
        if f >= 1e12: return f"${f/1e12:.1f}T"
        if f >= 1e9:  return f"${f/1e9:.0f}B"
        return f"${f/1e6:.0f}M"
    except Exception:
        return default


def _status_for(v, weak, severe, *, inv=False):
    if v is None: return "developing"
    try: v = float(v)
    except Exception: return "developing"
    if inv:
        if v >= severe: return "severe"
        if v >= weak:   return "weak"
        return "developing"
    if v <= severe: return "severe"
    if v <= weak:   return "weak"
    return "developing"


def build_ctx_from_agent_run(agent_ctx: dict, agent_outputs: dict,
                              verdict: str) -> dict:
    country  = agent_ctx["country"]
    sector   = agent_ctx.get("sector", "Multi-sector")
    workflow = agent_ctx.get("workflow", "needs")

    info = COUNTRY_INFO.get(country, {})
    dash = _load_dashboard_export(country) or {}
    indicators   = dash.get("indicators", {}) or {}
    pipeline_raw = dash.get("pipeline", []) or []
    cinfo        = dash.get("countryInfo", {}) or {}

    capital   = cinfo.get("capital") or info.get("capital", "—")
    currency  = cinfo.get("currency") or info.get("currency", "—")
    languages = cinfo.get("languages") or info.get("languages", "—")

    gni = _ind(indicators, "NY.GNP.PCAP.CD")
    dac_class = (
        "—" if gni is None else
        "LEAST DEVELOPED · LOW INCOME" if gni < 1135 else
        "LOWER-MIDDLE INCOME"           if gni < 4465 else
        "UPPER-MIDDLE INCOME"           if gni < 13845 else
        "HIGH INCOME")
    gni_cap = f"${int(gni):,}" if gni is not None else "—"

    analyst    = agent_outputs.get("analyst", "")
    strategist = agent_outputs.get("strategist", "") or analyst
    fact_check = agent_outputs.get("fact_checker", "") or analyst
    design     = agent_outputs.get("proj_design", "") or analyst

    pop_v  = _ind(indicators, "SP.POP.TOTL")
    gdp_v  = _ind(indicators, "NY.GDP.MKTP.CD")
    growth = _ind(indicators, "NY.GDP.MKTP.KD.ZG")
    cpi    = _ind(indicators, "FP.CPI.TOTL.ZG")

    # ─── 3-column hero snapshot ───
    hero = [
        {
            "section":     "General",
            "hero_value":  _fmt_pop(pop_v),
            "hero_label":  "Population",
            "hero_source": "UN DESA",
            "sub_cells": [
                {"value": dac_class.split("·")[0].strip() or "—",
                 "label":"DAC Class", "source":"World Bank"},
                {"value": _fmt_pct(_ind(indicators, "SI.POV.DDAY")),
                 "label":"Poverty <$2.15", "source":"World Bank"},
            ],
        },
        {
            "section":     "Economic",
            "hero_value":  _fmt_money(gdp_v),
            "hero_label":  f"GDP · {_fmt_pct(growth)} growth",
            "hero_source": "IMF · World Bank",
            "sub_cells": [
                {"value": gni_cap, "label":"GNI / capita", "source":"World Bank"},
                {"value": _fmt_pct(cpi), "label":"Inflation (CPI)", "source":"IMF"},
            ],
        },
        {
            "section":     "Political & Humanitarian",
            "hero_value":  verdict.title(),
            "hero_label":  f"Agent verdict · {workflow} workflow",
            "hero_source": "CAD agent pipeline",
            "sub_cells": [
                {"value": str(len(pipeline_raw)), "label":"Pipeline projects",
                 "source":"CAD dashboard"},
                {"value": sector, "label":"Sector focus", "source":"Intake"},
            ],
        },
    ]

    kpi_pair = [
        {"label":"Population", "value":_fmt_pop(pop_v),
         "sublabel":"Latest available · UN DESA"},
        {"label":"GDP",        "value":_fmt_money(gdp_v),
         "sublabel":f"{_fmt_pct(growth)} growth"},
    ]

    sector_status = [
        {"name":"Health",
         "status": _status_for(_ind(indicators, "SH.DYN.MORT"), 40, 80, inv=True),
         "summary":f"U5MR {_ind(indicators,'SH.DYN.MORT') or '—'}/1k"},
        {"name":"Education",
         "status": _status_for(_ind(indicators, "SE.ADT.LITR.ZS"), 65, 40),
         "summary":f"Literacy {_fmt_pct(_ind(indicators,'SE.ADT.LITR.ZS'))}"},
        {"name":"Food Security",
         "status": _status_for(_ind(indicators, "SN.ITK.DEFC.ZS"), 15, 25, inv=True),
         "summary":f"Undernourish {_fmt_pct(_ind(indicators,'SN.ITK.DEFC.ZS'))}"},
        {"name":"WASH",
         "status": _status_for(_ind(indicators, "SH.H2O.SMDW.ZS"), 65, 40),
         "summary":f"Safe water {_fmt_pct(_ind(indicators,'SH.H2O.SMDW.ZS'))}"},
        {"name":"Economic",
         "status": _status_for(growth, 2, 0),
         "summary":f"Growth {_fmt_pct(growth)}"},
        {"name":"Governance",     "status":"developing", "summary":"Agent assessment"},
        {"name":"Infrastructure",
         "status": _status_for(_ind(indicators, "EG.ELC.ACCS.ZS"), 60, 30),
         "summary":f"Electricity {_fmt_pct(_ind(indicators,'EG.ELC.ACCS.ZS'))}"},
    ]

    aglance_stats = [
        {"val": _fmt_pop(pop_v),  "label":"Population — UN DESA latest"},
        {"val": str(len(pipeline_raw)), "label":"Pipeline projects in CAD"},
        {"val": _fmt_pct(growth), "label":"GDP growth — latest"},
        {"val": _fmt_pct(cpi),    "label":"Inflation (CPI) — latest", "neg":True},
    ]
    aglance_insights = _extract_bullets(fact_check, 3) or \
                       _extract_bullets(analyst, 3)

    def _sector_stub(label, neg_codes=(), source="World Bank"):
        return {
            "statement":     f"Indicators and analyst findings for {label}",
            "chart_title":   f"{label} Indicators",
            "stats":         [],
            "insights":      _extract_bullets(analyst, 3),
            "interventions": _extract_bullets(design, 3),
            "sources":       f"Sources: {source}",
        }

    sectors = {
        "at_a_glance": {
            "statement":     f"Agent verdict: {verdict}",
            "chart_title":   "Country Overview",
            "stats":         aglance_stats,
            "insights":      aglance_insights,
            "interventions": _extract_bullets(strategist, 3),
            "sources":       "Sources: dashboard export · agent pipeline",
        },
        "economy": {
            "statement":     "Macro context (live indicators)",
            "chart":         {
                "title":      "GDP growth vs. inflation (latest)",
                "x_labels":   ["Latest"],
                "bar_values": [float(growth) if growth is not None else 0],
                "line_values":[float(cpi) if cpi is not None else 0],
                "y_max":      40,
                "bar_label":  "GDP growth (%)",
                "line_label": "CPI inflation (%)",
            },
            "stats": [
                {"val": _fmt_pct(growth), "label":"GDP growth"},
                {"val": _fmt_pct(cpi),    "label":"Inflation", "neg":True},
                {"val": gni_cap,          "label":"GNI / capita"},
                {"val": _fmt_pct(_ind(indicators,"SI.POV.DDAY")),
                 "label":"Poverty <$2.15", "neg":True},
            ],
            "insights":      _extract_bullets(analyst, 3),
            "interventions": _extract_bullets(design, 3),
            "sources":       "Sources: World Bank · IMF · agent analysis",
        },
        "health":         _sector_stub("Health",        source="WHO · UNICEF"),
        "education":      _sector_stub("Education",     source="UNESCO UIS"),
        "nutrition":      _sector_stub("Food Security", source="FEWS NET · IPC"),
        "agriculture":    _sector_stub("Agriculture",   source="FAOSTAT"),
        "infrastructure": _sector_stub("Infrastructure",source="World Bank · ITU"),
        "climate":        _sector_stub("Environment & Climate", source="ND-GAIN"),
        "humanitarian":   _sector_stub("Humanitarian",  source="OCHA · IOM DTM"),
    }
    # Education needs grouped-bar shape
    sectors["education"]["chart"] = {
        "title": "Enrollment by Level & Gender",
        "x_labels": ["Primary","Lower-Sec.","Upper-Sec.","Tertiary"],
        "series_a": [90, 35, 20, 10],
        "series_b": [85, 30, 17, 8],
        "a_label": "Boys", "b_label": "Girls", "y_max": 100,
    }
    # Nutrition needs funnel
    sectors["nutrition"]["funnel"] = []
    # Infrastructure compare_rows
    sectors["infrastructure"]["compare_rows"] = [
        {"label":"Electricity",  "urban":80, "rural":20},
        {"label":"Safe water",   "urban":75, "rural":45},
        {"label":"Sanitation",   "urban":35, "rural":12},
        {"label":"Internet",     "urban":45, "rural":8},
    ]
    # Climate line chart
    sectors["climate"]["chart"] = {
        "title": "Climate risk trend (illustrative)",
        "x_labels": ["2000","2010","2020","2024"],
        "series": [{"label":"Risk index", "values":[20,40,60,70], "color":[155,18,11]}],
        "y_max": 100,
    }

    # ─── Pipeline projects → priorities (slide 12) ───
    priority_cards = []
    for i, row in enumerate(pipeline_raw[:8]):
        priority_cards.append({
            "num":      f"{i+1:02d} · {row.get('sector','—')}",
            "title":    row.get("title") or row.get("name", f"Project {i+1}"),
            "desc":     row.get("description") or
                        f"Path {row.get('path','—')} · Status: {row.get('statusLabel') or row.get('status','—')} · Cost: {row.get('cost','—')}.",
            "priority": "high" if i < 3 else ("medium" if i < 6 else "foundational"),
            "dark":     i == 7,
        })
    while len(priority_cards) < 8:
        priority_cards.append({
            "num":      f"{len(priority_cards)+1:02d} · TBD",
            "title":    "(open slot)",
            "desc":     "Add a pipeline project via the CAD dashboard intake form to populate this slot.",
            "priority": "foundational",
            "dark":     len(priority_cards) == 7,
        })

    bigstat = {
        "crumb":        f"11 · AGENT VERDICT · {workflow.upper()} WORKFLOW",
        "hero_value":   verdict.title(),
        "hero_label":   f"AGENT CONSENSUS  ·  {sector.upper()}",
        "statement":    (f"The {workflow} workflow ran {len(agent_outputs)} specialist agents "
                         f"against {country} indicators and pipeline state. "
                         f"Verdict: {verdict}."),
        "quote":        _extract_bullets(strategist, 1)[0] if _extract_bullets(strategist, 1) else
                        "See agent outputs for full analysis.",
        "quote_source": "— CAD agent pipeline",
        "strip": [
            {"value": str(len(agent_outputs)), "label":"Agents run"},
            {"value": str(len(indicators)),    "label":"Indicators ingested"},
            {"value": str(len(pipeline_raw)),  "label":"Pipeline projects"},
        ],
    }

    return {
        "country":   country,
        "iso2":      info.get("iso2", ""),
        "flag_url":  info.get("flag_url"),
        "lat":       info.get("lat"),
        "lng":       info.get("lng"),
        "date_str":  datetime.now().strftime("%B %Y"),
        "subtitle":  info.get("subtitle",
                       f"Country brief · {workflow} workflow"),
        "snapshot": {
            "capital":   capital,
            "currency":  currency,
            "languages": languages,
            "dac_class": dac_class,
            "gni_cap":   gni_cap,
        },
        "hero_snapshot": hero,
        "kpi_pair":      kpi_pair,
        "sector_status": sector_status,
        "cover_footer":  "Sources: Dashboard export · CAD agent pipeline · World Bank",
        "sectors":       sectors,
        "bigstat":       bigstat,
        "priorities_block": {
            "crumb":     f"12 · AGENT RECOMMENDATIONS",
            "topic":     "Priorities",
            "statement": "Pipeline projects ranked by tier",
            "cards":     priority_cards,
            "footer":    "Cards 1–3 = high priority; 4–6 = medium; 7 = optional; 8 = foundational data slot.",
        },
        "closing": {
            "subtitle": f"Country Brief · {workflow.title()} Workflow",
            "meta":     [datetime.now().strftime("%B %Y"),
                         f"Verdict: {verdict}",
                         f"{len(agent_outputs)} agents"],
            "sources":
                "Sources: World Bank · IMF · OCHA · WHO · UNICEF · UNESCO UIS · UNHCR · IOM DTM    "
                "CAD agent pipeline · dashboard export",
        },
    }
