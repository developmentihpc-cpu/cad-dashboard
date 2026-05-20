"""
validation.py — Pre-render validation for the country-brief markdown.

validate_brief() runs a battery of checks against a brief and returns
(warnings, errors). Warnings don't block rendering; errors do.

validate_manifest_against_markdown() cross-checks a manifest's declared
module selection against the section headers actually present in the
markdown. Used when --manifest is passed to the CLI.
"""
import difflib
import re


_MANIFEST_MODULE_MAP = {
    # Spine (always expected)
    "country_snapshot":       (1,    "Country Snapshot"),
    "bilateral_relations":    (1.5,  "Bilateral Relations"),
    "political_context":      (2,    "Political Context"),
    "economic_conditions":    (3,    "Economic Conditions"),
    "security_stability":     (4,    "Security & Stability"),
    "governance_rule_of_law": (5,    "Governance & Rule of Law"),
    "social_human_development": (6,  "Social & Human Development"),
    # Optional modules
    "development_project":    (7,    "Development Project"),
    "humanitarian":           (8,    "Humanitarian Severity"),
    "macro_stress":           (9,    "Macro Stress / Debt"),
    "climate":                (10,   "Climate Risk"),
    "elections":              (11,   "Election Cycle"),
    "civil_society_media":    (12,   "Civil Society & Media"),
    "diaspora":               (13,   "Diaspora & Remittances"),
    "sanctions":              (14,   "Sanctions Exposure"),
    "market_entry":           (15,   "Market Entry"),
    "regulatory":             (16,   "Regulatory Regime"),
    "project_operating":      (17,   "Project Operating Environment"),
    "comparative":            (18,   "Comparative Benchmarking"),
    "outlook":                (19,   "Outlook"),
}


# ─────────────────────────────────────────────────────────────────────
# Structural-audit thresholds
# ─────────────────────────────────────────────────────────────────────
# Single source of truth for the numbers that govern the structural-
# discipline audit. Tuning the audit strictness is a one-place change.
# These came from auditing the May 2026 brief series (Ethiopia, Sudan,
# Syria, Morocco, Sri Lanka, Iran) where well-structured briefs comfortably
# exceed the floors below.
_THRESHOLDS = {
    # Size gate: structural audit only fires on substantive briefs.
    "structural_audit_min_body_lines":    120,
    # Footnote density.
    "footnote_density_gate_body_lines":   60,    # below this, density check is skipped
    "footnote_density_body_lines_per_fn": 40,    # expect >=1 footnote per N body lines
    # Bottom Line length (spec target: 2-3 sentences, ~60-80 words).
    "bottom_line_max_words":              120,
    # Chronology: a section is considered chronologically anchored when it
    # has a date-bearing table OR this many year-prefixed bullets.
    "chronology_year_bullet_floor":       3,
    # Chart count bounds (spec: 3-8, 4-6 typical).
    "chart_count_floor":                  3,
    "chart_count_soft_ceiling":           8,
    # Leader-card section-aware bounds.
    "leader_cards_section_15_exact":      2,     # bilateral: exactly 2
    "leader_cards_section_2_floor":       3,     # political context: >=3
    "leader_cards_default_floor":         2,     # other sections: >=2
    # Decision-implication coverage — tolerated gap between spine sections
    # and decision-implication callouts before warning.
    "decision_implication_gap_tolerance": 1,
    # Series-leakage examples shown in the aggregated warning.
    "series_leakage_example_max":         3,
}


# ─────────────────────────────────────────────────────────────────────
# Chart recipe registry
# ─────────────────────────────────────────────────────────────────────
# Each recipe encodes "this chart is decision-relevant when X is true."
# The validator detects whether the trigger fires and whether a matching
# chart is already in the brief; if the trigger fires but no chart
# matches, it surfaces the recipe as a suggestion.
#
# Recipes are intentionally additive, not prescriptive. The validator
# warns; the analyst decides. Most briefs will fire 3-5 recipes; the
# analyst typically picks 2-3 of them based on the brief's specific
# analytical argument.
#
# Each recipe has:
#   - trigger: dict describing when the recipe fires. Supports:
#       - "keyword": list of strings; any case-insensitive ASCII-word-
#         boundaried match in the brief body fires the trigger
#       - "keyword_ar": list of Arabic strings; any substring match in the
#         brief body fires the trigger (no \b boundaries because Python's
#         \b is ASCII-only and doesn't apply to Arabic letters)
#       - "section_present": section number (e.g., "8" or "1.5"); fires
#         if a "## N." heading is in the brief
#     Trigger fields combine with OR semantics — any condition satisfies.
#   - section_hint: text where this chart usually belongs (advisory)
#   - title_keywords: lowercase English keywords used to detect whether the
#     brief already has a chart for this recipe (matched against chart titles)
#   - title_keywords_ar: Arabic keywords used the same way; both lists are
#     checked against every chart title so Arabic briefs are first-class
#   - template: a copy-paste-ready ::: chart block stub for the analyst
#
# Extending: add new entries here. New recipes benefit every future brief.
_CHART_RECIPES = {
    "fx-trajectory": {
        # Fire only on signals of meaningful FX volatility, not generic
        # mentions of "exchange rate" or "FATF". Require currency-collapse
        # markers or wartime/sanctions context.
        "trigger": {
            "keyword": ["currency collapse", "free-market rate", "record low against the dollar", "hyperinflation", "rial", "lira crisis", "naira", "rand depreciation"],
            "keyword_ar": ["الريال", "الليرة", "النيرة", "الراند", "انهيار العملة", "تضخم جامح", "تخفيض قيمة العملة"],
        },
        "section_hint": "Section 3 (Economic Conditions)",
        "title_keywords": ["exchange rate", "rial", "rand vs", "lira", "currency trajectory", "fx ", "rial vs", "free-market", "free market"],
        "title_keywords_ar": ["سعر الصرف", "الريال", "الليرة", "العملة"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: National currency vs USD (free-market or official)\n"
            "x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: <Currency> / USD | ... | ... | ... | ... | ... | ...\n"
            "y-label: Currency per USD\n"
            "source: central bank; market reporting\n"
            ":::"
        ),
    },
    "debt-trajectory": {
        "trigger": {
            "keyword": ["debt distress", "high risk of debt", "Debt Sustainability Analysis", "in IMF program", "primary surplus", "debt restructuring"],
            "keyword_ar": ["إعادة هيكلة الدين", "الدين السيادي", "ضائقة الدين", "تخلف عن السداد", "التخلّف السيادي", "برنامج صندوق النقد"],
        },
        "section_hint": "Section 3 (Economic Conditions) or Section 9 (Macro Stress)",
        "title_keywords": ["debt", "debt/gdp", "public debt", "debt to gdp"],
        "title_keywords_ar": ["الدين", "الدين العام", "الدين السيادي", "نسبة الدين"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Public debt as % of GDP\n"
            "x: 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: Debt / GDP (%) | ... | ... | ... | ... | ... | ... | ...\n"
            "y-label: Percent of GDP\n"
            "source: IMF Article IV; National Treasury / Finance Ministry\n"
            ":::"
        ),
    },
    "remittances-trajectory": {
        "trigger": {
            "keyword": ["remittance"],
            "keyword_ar": ["تحويلات المغتربين", "حوالات", "تحويلات الجالية"],
        },
        "section_hint": "Section 13 (Diaspora & Remittances) or Section 3",
        "title_keywords": ["remittance", "diaspora flow"],
        "title_keywords_ar": ["تحويلات", "التحويلات"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Remittance inflows (USD millions)\n"
            "x: 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024\n"
            "y: Remittances ($M) | ... | ... | ... | ... | ... | ... | ...\n"
            "y-label: USD millions\n"
            "source: World Bank Migration and Remittances Data; central bank\n"
            ":::"
        ),
    },
    "unemployment-trajectory": {
        "trigger": {
            "keyword": ["unemployment ~3", "unemployment 3", "unemployment 4", "youth unemployment", "labor force"],
            "keyword_ar": ["البطالة", "بطالة الشباب", "سوق العمل", "القوى العاملة"],
        },
        "section_hint": "Section 3 (Economic Conditions) or Section 6 (Social & Human Development)",
        "title_keywords": ["unemployment", "labor force", "jobless"],
        "title_keywords_ar": ["البطالة", "سوق العمل", "بطالة"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Unemployment rate trajectory\n"
            "x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: Unemployment (%) | ... | ... | ... | ... | ... | ...\n"
            "y-label: Percent of labor force\n"
            "source: national statistics office; ILO\n"
            ":::"
        ),
    },
    "energy-availability-factor": {
        "trigger": {
            "keyword": ["loadshedding", "load shedding", "EAF", "energy availability", "Eskom", "blackout", "power supply"],
            "keyword_ar": ["انقطاع الكهرباء", "تقنين الكهرباء", "أزمة الطاقة", "انقطاعات التيار"],
        },
        "section_hint": "Section 3 (Economic Conditions) or a dedicated energy/infrastructure section",
        "title_keywords": ["energy availability", "loadshedding", "load shedding", "eaf", "power supply", "electricity supply"],
        "title_keywords_ar": ["إمداد الكهرباء", "توافر الطاقة", "انقطاع الكهرباء"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Energy Availability Factor (EAF) trajectory\n"
            "x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: EAF (%) | ... | ... | ... | ... | ... | ...\n"
            "y-label: Percent\n"
            "source: state utility System Status reports\n"
            ":::"
        ),
    },
    "oil-exports-trajectory": {
        "trigger": {
            "keyword": ["oil exports", "crude exports", "hydrocarbon", "petroleum exports", "shadow fleet", "OPEC"],
            "keyword_ar": ["صادرات النفط", "البترول", "أوبك", "الأسطول الشبحي", "صادرات الخام"],
        },
        "section_hint": "Section 3 (Economic Conditions)",
        "title_keywords": ["oil export", "crude export", "hydrocarbon", "petroleum", "shadow fleet"],
        "title_keywords_ar": ["النفط", "صادرات النفط", "البترول", "الأسطول الشبحي"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Oil exports trajectory (volume or value)\n"
            "x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: Oil exports | ... | ... | ... | ... | ... | ...\n"
            "y-label: million barrels per day OR USD billions\n"
            "source: state oil company; IEA; trade data\n"
            ":::"
        ),
    },
    "humanitarian-population": {
        "trigger": {"section_present": "8"},
        "section_hint": "Section 8 (Humanitarian Severity)",
        "title_keywords": ["humanitarian", "displaced", "idp", "pin ", "people in need", "affected population", "refugee", "refugees"],
        "title_keywords_ar": ["إنسانية", "النازحون", "النازحين", "اللاجئين", "احتياجات إنسانية", "السكان المتضررين"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: People in humanitarian need / IDPs over time\n"
            "x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: PIN (millions) | ... | ... | ... | ... | ... | ...\n"
            "y-label: Millions of people\n"
            "source: OCHA Humanitarian Needs Overview; UNHCR; IOM DTM\n"
            ":::"
        ),
    },
    "bilateral-trade-trajectory": {
        "trigger": {"section_present": "1.5"},
        "section_hint": "Section 1.5 (Bilateral Relations) or Section 3",
        "title_keywords": ["bilateral trade", "trade with", "two-way trade", "non-oil trade", "trade volume with", "bilateral engagement", "bilateral relations trajectory", "bilateral investment", "uae-"],
        "title_keywords_ar": ["تجارة ثنائية", "تبادل تجاري", "التبادل التجاري", "تجارة الإمارات", "العلاقات الثنائية"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Bilateral trade with home country (USD billions)\n"
            "x: 2019 | 2020 | 2021 | 2022 | 2023 | 2024\n"
            "y: Two-way trade ($B) | ... | ... | ... | ... | ... | ...\n"
            "y-label: USD billions\n"
            "source: home-country Ministry of Economy / national customs\n"
            ":::"
        ),
    },
    "sanctions-packages-timeline": {
        # Fire only when the brief's country itself is sanctioned, not when
        # it merely discusses sanctions elsewhere. Section 14 presence is
        # the cleanest signal; specific phrases like "UN snapback" or
        # "FATF blacklist" applied to the country also fire.
        "trigger": {
            "section_present": "14",
            "keyword": ["UN snapback", "FATF blacklist", "sanctions reimposed", "secondary-sanctions designations", "primary sanctions on"],
            "keyword_ar": ["العقوبات الثانوية", "القائمة السوداء لمجموعة العمل المالي", "إعادة فرض العقوبات", "تفعيل آلية snapback", "حزم عقوبات"],
        },
        "section_hint": "Section 14 (Sanctions Exposure)",
        "title_keywords": ["sanctions package", "ofac action", "designations", "sanctions imposed", "sanctions architecture"],
        "title_keywords_ar": ["العقوبات", "حزم العقوبات", "تصنيفات", "بنية العقوبات"],
        "template": (
            "::: chart\n"
            "type: bar\n"
            "title: New sanctions packages / designations by year\n"
            "x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: New designations | ... | ... | ... | ... | ... | ...\n"
            "y-label: Count\n"
            "source: OFAC SDN list; EU Council sanctions; UN Security Council\n"
            ":::"
        ),
    },
    "comparative-peers": {
        "trigger": {"section_present": "18"},
        "section_hint": "Section 18 (Comparative Benchmarking)",
        "title_keywords": ["peer comparison", "comparator", "cross-country", " vs ", "compared to"],
        "title_keywords_ar": ["مقارنة", "مرجعية", "مقارنة بين", "مقارن"],
        "template": (
            "::: chart\n"
            "type: bar\n"
            "title: <Indicator> — country vs peer comparators\n"
            "x: <Country> | <Peer 1> | <Peer 2> | <Peer 3>\n"
            "y: Indicator value | ... | ... | ... | ...\n"
            "y-label: <units>\n"
            "source: IMF WEO; World Bank WDI\n"
            ":::"
        ),
    },
    "climate-events-frequency": {
        "trigger": {
            "keyword": ["ND-GAIN", "ND GAIN", "climate vulnerability", "cyclone", "drought", "Day Zero"],
            "keyword_ar": ["تغير المناخ", "إعصار", "جفاف", "هشاشة مناخية", "الضعف المناخي"],
        },
        "section_hint": "Section 10 (Climate Vulnerability) or Section 8 (Humanitarian)",
        "title_keywords": ["climate", "nd-gain", "cyclone", "drought", "flood", "extreme weather"],
        "title_keywords_ar": ["المناخ", "إعصار", "جفاف", "أحداث مناخية"],
        "template": (
            "::: chart\n"
            "type: bar\n"
            "title: Major climate / extreme-weather events by year\n"
            "x: 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025\n"
            "y: Events | ... | ... | ... | ... | ... | ... | ... | ...\n"
            "y-label: Count of major events\n"
            "source: EM-DAT (CRED); national disaster agency\n"
            ":::"
        ),
    },
    "conflict-events-trajectory": {
        # Fire only on signals of actual armed conflict, not metaphorical
        # casualties (e.g., crime murder counts in stable countries).
        "trigger": {
            "keyword": ["ACLED", "active armed conflict", "wartime", "insurgency", "ceasefire", "ENDF", "conflict fatalities", "war casualties"],
            "keyword_ar": ["وقف إطلاق النار", "النزاع المسلح", "الحرب الأهلية", "حرب نشطة", "تمرد مسلح", "ضحايا الحرب"],
        },
        "section_hint": "Section 4 (Security & Stability)",
        "title_keywords": ["acled", "conflict events", "war casualties", "fatalities by", "violence trajectory"],
        "title_keywords_ar": ["النزاع", "أحداث الصراع", "ضحايا الحرب", "أحداث أمنية"],
        "template": (
            "::: chart\n"
            "type: line\n"
            "title: Conflict events and fatalities (monthly or quarterly)\n"
            "x: Q1-24 | Q2-24 | Q3-24 | Q4-24 | Q1-25 | Q2-25 | Q3-25 | Q4-25\n"
            "y: Events | ... | ... | ... | ... | ... | ... | ... | ...\n"
            "y: Fatalities | ... | ... | ... | ... | ... | ... | ... | ...\n"
            "y-label: Count\n"
            "source: ACLED; UCDP\n"
            ":::"
        ),
    },
}


def _detect_chart_titles(md_text: str) -> list:
    """Return lowercase chart titles present in the brief (one per `::: chart` block)."""
    titles = []
    for m in re.finditer(
        r"^:::[ \t]*chart[ \t]*$\n(.*?)^:::[ \t]*$",
        md_text, re.MULTILINE | re.DOTALL,
    ):
        body = m.group(1)
        title_m = re.search(r"^\s*title\s*:\s*(.+)$", body, re.MULTILINE)
        if title_m:
            titles.append(title_m.group(1).strip().lower())
    return titles


def _recipe_fires(recipe: dict, md_text: str) -> bool:
    """Decide whether a recipe's trigger condition is met (OR semantics across fields).

    Keyword matching uses word boundaries to avoid substring false-positives
    (e.g., 'rial' matching 'ministerial', 'oil' matching 'boil'). Multi-word
    keywords are matched as exact phrases; both single-word and multi-word
    forms require alphanumeric word boundaries on either side.
    """
    trig = recipe.get("trigger", {})
    # Keyword check with left-boundary semantics. We use \b on the LEFT
    # side only (the match must start at a word boundary), but allow any
    # suffix on the right. This matches:
    #   keyword "remittance"   -> "remittance", "remittances", "remittancing"
    #   keyword "rial"          -> "rial", "rials"      BUT NOT "ministerial"
    #   keyword "oil"           -> "oil", "oils"        BUT NOT "boil", "spoil"
    # Multi-word keywords ("UN snapback") are escaped and matched as phrases.
    for kw in trig.get("keyword", []):
        kw_pattern = r"\b" + re.escape(kw)
        if re.search(kw_pattern, md_text, re.IGNORECASE):
            return True
    # Arabic keyword check — plain substring match. Python's \b is ASCII-
    # based and doesn't form valid word boundaries on Arabic letters, so a
    # boundary-anchored regex would produce false negatives. Arabic keywords
    # in this registry are picked to be distinctive enough that substring
    # collisions aren't a practical concern.
    for kw in trig.get("keyword_ar", []):
        if kw in md_text:
            return True
    # Section-present check
    sect = trig.get("section_present")
    if sect:
        pattern = rf"^##\s+{re.escape(sect)}[\.\s]"
        if re.search(pattern, md_text, re.MULTILINE):
            return True
    return False


def _recipe_chart_present(recipe: dict, chart_titles: list) -> bool:
    """Check whether the brief already has a chart matching this recipe.

    Matches both English `title_keywords` and Arabic `title_keywords_ar`
    against each chart title (which `_detect_chart_titles` returns lower-
    cased; Arabic letters are case-invariant so the lowercase doesn't harm
    Arabic matching).
    """
    en_kws = recipe.get("title_keywords", [])
    ar_kws = recipe.get("title_keywords_ar", [])
    for title in chart_titles:
        for kw in en_kws:
            if kw.lower() in title:
                return True
        for kw in ar_kws:
            if kw in title:
                return True
    return False


def _section_body(md_text: str, section_num) -> str:
    """Return the markdown body between '## N.' heading and the next '## '.

    Line-based scan: anchor on the heading line that starts with '## <num>.'
    (or '## <num>.<sub>'), then collect lines up to the next H2. Avoids the
    earlier DOTALL regex's failure mode where a '##' inside a fenced code
    block would prematurely truncate the section.

    section_num may be an int ("4") or a dotted string ("1.5").
    """
    target = str(section_num).strip()
    # Match the heading line: "## <target>." or "## <target> " (allow either
    # trailing punctuation, but require the next char after target be . or
    # whitespace so "1" doesn't swallow "1.5" or "10").
    head_re = re.compile(rf"^##\s+{re.escape(target)}[\.\s]")
    next_h2_re = re.compile(r"^##\s+\S")
    lines = md_text.splitlines()
    out = []
    in_section = False
    for line in lines:
        if not in_section:
            if head_re.match(line):
                in_section = True
                out.append(line)
            continue
        if next_h2_re.match(line):
            break
        out.append(line)
    return "\n".join(out)


def _has_chronology_in(text: str) -> bool:
    """True iff text contains a date-bearing table or 3+ year-prefixed bullets.

    Language-aware: matches English (`Date`, `When`) and Arabic (`التاريخ`,
    `الوقت`, `الفترة`) date-column headers in tables, plus English month
    names and Arabic Gregorian month names in bullet prefixes. Year markers
    (`\\d{4}`) work in both since Arabic briefs use Western-Arabic numerals
    for dates by convention (see arabic-style.md).
    """
    if not text:
        return False
    has_date_table = bool(re.search(
        r"^\|\s*(?:Date|When|التاريخ|الوقت|الفترة)\s*\|",
        text, re.MULTILINE | re.IGNORECASE
    ))
    year_bullet_count = len(re.findall(
        r"^\s*[-*]\s+(?:\*{1,2})?(?:"
        r"\d{4}"
        r"|January|February|March|April|May|June|July|August|September|October|November|December"
        # Arabic Gregorian month names (Egyptian/Maghrebi convention)
        r"|يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر"
        # Levantine/Iraqi calendar names
        r"|كانون الثاني|شباط|آذار|نيسان|أيار|حزيران|تموز|آب|أيلول|تشرين الأول|تشرين الثاني|كانون الأول"
        r")\b",
        text, re.MULTILINE | re.IGNORECASE,
    ))
    return has_date_table or year_bullet_count >= _THRESHOLDS["chronology_year_bullet_floor"]


def _missing_chart_recipes(md_text: str) -> list:
    """Return list of (recipe_name, recipe_dict) pairs whose triggers fire
    but for which no matching chart is present in the brief."""
    chart_titles = _detect_chart_titles(md_text)
    missing = []
    for name, recipe in _CHART_RECIPES.items():
        if _recipe_fires(recipe, md_text) and not _recipe_chart_present(recipe, chart_titles):
            missing.append((name, recipe))
    return missing


def validate_manifest_against_markdown(manifest: dict, md_text: str) -> list:
    """
    Cross-check a manifest's declared module selection against the section
    headers actually present in the markdown. Returns a list of warning
    strings describing inconsistencies.

    A module declared `true` or `partial` MUST have a corresponding section.
    A module declared `false` should NOT have a corresponding section.
    A `stub` declaration is permissive — the section may or may not be
    present, and if present may have minimal content (the placeholder
    convention is fine).

    The manifest is optional. When omitted, this function isn't called and
    the renderer simply uses whatever sections appear in the markdown.
    Provided manifests act as a second source of truth that catches:

    - Forgotten sections (declared `true` but section missing in markdown)
    - Unintended sections (declared `false` but section present in markdown)
    - Typos in module keys (key not in the canonical map)
    """
    import re

    warnings = []
    modules = manifest.get("modules", {})

    # Find all section numbers present in the markdown. Headers look like
    # "## 1. Country Snapshot" or "## 1.5. Bilateral Relations" — extract
    # the leading numeric part. The validator already does this for spine
    # gap detection; we replicate it here for the manifest check.
    present_section_nums = set()
    for m in re.finditer(r"^##\s+(\d+(?:\.\d+)?)\.?\s+", md_text, re.MULTILINE):
        num_str = m.group(1)
        num = float(num_str) if "." in num_str else int(num_str)
        present_section_nums.add(num)

    # Check 1: typo'd module keys
    canonical_keys = set(_MANIFEST_MODULE_MAP.keys())
    for declared_key in modules.keys():
        if declared_key not in canonical_keys:
            # Find a likely intended match
            import difflib
            suggestions = difflib.get_close_matches(declared_key, canonical_keys, n=1, cutoff=0.6)
            suggestion_msg = f" (did you mean '{suggestions[0]}'?)" if suggestions else ""
            warnings.append(
                f"Manifest: unknown module key '{declared_key}'{suggestion_msg}. "
                f"See _MANIFEST_MODULE_MAP for the canonical list."
            )

    # Check 2: declared modules vs section presence
    for module_key, state in modules.items():
        if module_key not in canonical_keys:
            continue  # already warned about typos
        section_num, section_name = _MANIFEST_MODULE_MAP[module_key]
        section_present = section_num in present_section_nums

        if state in (True, "true", "partial", "stub"):
            if not section_present and state != "stub":
                warnings.append(
                    f"Manifest declares module '{module_key}' = {state!r} (Section {section_num}, "
                    f"{section_name}) but no '## {section_num}. ...' header found in the markdown. "
                    f"Either add the section or change the manifest declaration."
                )
        elif state in (False, "false"):
            if section_present:
                warnings.append(
                    f"Manifest declares module '{module_key}' = false (Section {section_num}, "
                    f"{section_name}) but a '## {section_num}. ...' header IS present in the markdown. "
                    f"Either remove the section or change the manifest declaration."
                )
        else:
            warnings.append(
                f"Manifest: module '{module_key}' has unrecognized state {state!r}. "
                f"Use true, false, partial, or stub."
            )

    # Check 3: sections present in markdown that aren't declared in the manifest
    # (helps catch a section added without updating the manifest)
    key_for_section = {v[0]: k for k, v in _MANIFEST_MODULE_MAP.items()}
    declared_section_nums = set()
    for module_key in modules.keys():
        if module_key in canonical_keys:
            declared_section_nums.add(_MANIFEST_MODULE_MAP[module_key][0])
    undeclared = present_section_nums - declared_section_nums
    # Don't warn about the bibliography or other non-numbered headers
    undeclared = {n for n in undeclared if n in key_for_section}
    for n in sorted(undeclared):
        warnings.append(
            f"Manifest: Section {n} ({_MANIFEST_MODULE_MAP[key_for_section[n]][1]}) is present "
            f"in the markdown but not declared in the manifest. Add '{key_for_section[n]}: true' "
            f"to the manifest, or remove the section."
        )

    return warnings


def _run_structural_audit(md_text: str, body_lines: int) -> tuple:
    """Post-size-gate structural-discipline audit.

    Runs the structural checks that are only meaningful for substantive
    briefs (body length above _THRESHOLDS["structural_audit_min_body_lines"]).
    The caller — validate_brief — is responsible for the size gate.

    Returns (warnings, strict_promotable):
      - warnings: list of structural-discipline warning strings
      - strict_promotable: list of (warning_text, key) pairs that --strict
        mode promotes from warning to error. Key is one of "footnotes" |
        "risk-matrix" | "recommendations".

    Lives at module scope so the two phases of validate_brief() are
    visually distinct: pre-gate syntax-integrity checks (always run) live
    inline in validate_brief; post-gate structural-discipline checks
    (substantive briefs only) live here.
    """
    warnings = []
    strict_promotable = []

    # ─────────────────────────────────────────────────────────────────
    # Structural-discipline checks: warn when the brief departs from
    # the SKILL.md spec in ways that experience shows produce poor
    # deliverables. These are soft warnings — the renderer continues.
    # Thresholds came from auditing the May 2026 brief series where
    # well-structured briefs comfortably exceed the floors below.
    # ─────────────────────────────────────────────────────────────────

    # Check 1: Footnote density.
    inline_footnote_refs = len(re.findall(r'\[\^[^\]]+\]', md_text)) // 2
    if inline_footnote_refs == 0:
        msg = (
            "Structural: brief contains zero footnote references. "
            "Every consequential factual claim should be source-attributed. "
            "Use [^N] inline references and [^N]: source-text definitions at the end."
        )
        warnings.append(msg)
        strict_promotable.append((msg, "footnotes"))
    else:
        density_gate = _THRESHOLDS["footnote_density_gate_body_lines"]
        density_floor = _THRESHOLDS["footnote_density_body_lines_per_fn"]
        if body_lines > density_gate and inline_footnote_refs < (body_lines / density_floor):
            warnings.append(
                f"Structural: footnote density is low ({inline_footnote_refs} footnotes "
                f"for ~{body_lines} body lines). Briefs with substantive prose should "
                f"have claim-level source attribution. Consider whether key factual "
                f"claims need [^N] references."
            )

    # Check 2: Bottom Line length.
    bottom_line_match = re.search(
        r'^##\s+Bottom\s+line\s*\n(.+?)(?=\n##|\n:::|\Z)',
        md_text, re.MULTILINE | re.DOTALL | re.IGNORECASE
    )
    if bottom_line_match:
        bl_text = bottom_line_match.group(1).strip()
        bl_words = len(bl_text.split())
        if bl_words > _THRESHOLDS["bottom_line_max_words"]:
            warnings.append(
                f"Structural: Bottom Line is ~{bl_words} words. Spec target is "
                f"2-3 sentences (~60-80 words). Long bottom lines indicate the "
                f"prioritization work wasn't done — cut to the most decision-relevant "
                f"claims and move depth into the relevant sections."
            )

    # Check 3: Map presence.
    has_map = ":::map" in md_text.replace(" ", "") or "::: map" in md_text
    if not has_map:
        warnings.append(
            "Structural: no ::: map block found. Country briefs benefit from a "
            "reference map for geographic orientation. Add a `::: map` block "
            "(typically after Section 1) unless there's a specific reason to omit."
        )

    # Check 3.6: Section-scoped chronology coverage.
    time_anchored_sections = [
        ("1.5", "Section 1.5 (Bilateral Relations)",
         "bilateral visits and engagements"),
        ("4",   "Section 4 (Security & Stability)",
         "conflict events, security incidents, ceasefire architecture"),
        ("11",  "Section 11 (Election Cycle)",
         "electoral cycle, political-transition events"),
    ]
    for sect_num, sect_name, content_hint in time_anchored_sections:
        section_text = _section_body(md_text, sect_num)
        if section_text and not _has_chronology_in(section_text):
            warnings.append(
                f"Structural: {sect_name} present but no dated chronology "
                f"inside the section (markdown table with `| Date |` column, "
                f"or 3+ year-prefixed bullets). The convention is to surface "
                f"the time-anchored content ({content_hint}) visually rather "
                f"than burying it in prose. The deprecated `::: election-"
                f"timeline` component was replaced by inline tables and "
                f"dated bullet lists; use one of those inside this section."
            )

    # Check 3.5: Thematic-map coverage.
    has_choropleth = bool(re.search(
        r"^:::\s*map\s*$\n[^:]*?^\s*type\s*:\s*choropleth",
        md_text, re.MULTILINE | re.DOTALL,
    ))
    has_severity_box = ":::severity-box" in md_text.replace(" ", "") or "::: severity-box" in md_text
    has_section_11 = bool(re.search(r"^##\s+11\.", md_text, re.MULTILINE))
    if has_severity_box and not has_choropleth:
        warnings.append(
            "Structural: brief has a ::: severity-box (sub-national severity "
            "data) but no ::: map type: choropleth block. The same regional "
            "categorization can be rendered as a choropleth map alongside the "
            "text severity box — same data, complementary visualization. "
            "Earlier briefs in the skill's reference set (Ethiopia, Sudan, "
            "Iran v1, Syria) shipped both."
        )
    if has_section_11 and not has_choropleth:
        warnings.append(
            "Structural: brief has Section 11 (Election Cycle / Political "
            "Transition) but no choropleth map. Electoral briefs typically "
            "benefit from a province- or district-level results map. Add a "
            "`::: map type: choropleth color-scale: electoral` block."
        )

    # Check 3.7: Chart-recipe suggestions.
    missing_recipes = _missing_chart_recipes(md_text)
    if missing_recipes:
        lines = []
        for name, recipe in missing_recipes:
            trig = recipe.get("trigger", {})
            md_lower = md_text.lower()
            hit_reason = None
            for kw in trig.get("keyword", []):
                if kw.lower() in md_lower:
                    hit_reason = f"keyword '{kw}' present"
                    break
            if not hit_reason and trig.get("section_present"):
                hit_reason = f"Section {trig['section_present']} present"
            section_hint = recipe.get("section_hint", "")
            lines.append(f"  - {name} ({hit_reason}) → {section_hint}")
        warnings.append(
            "Structural: " + str(len(missing_recipes)) + " chart recipe(s) would "
            "fire for this brief but no matching chart is present. Consider 1-2 of "
            "the following based on the brief's analytical thesis (the goal is "
            "decision-relevance, not coverage of all recipes). Templates are in "
            "validation.py's _CHART_RECIPES.\n" + "\n".join(lines)
        )

    # Check 4: Chart presence and count.
    chart_blocks = re.findall(r"^:::\s*chart\s*$", md_text, re.MULTILINE)
    n_charts = len(chart_blocks)
    chart_floor = _THRESHOLDS["chart_count_floor"]
    chart_ceiling = _THRESHOLDS["chart_count_soft_ceiling"]
    if n_charts == 0:
        warnings.append(
            "Structural: no ::: chart blocks found. SKILL.md spec calls for "
            f"{chart_floor}-{chart_ceiling} charts per brief (4-6 typical), "
            "illustrating trajectory, comparison, or composition across the "
            "brief's main analytical dimensions. Consult the chart-recipe "
            "registry suggestions above."
        )
    elif n_charts < chart_floor:
        warnings.append(
            f"Structural: brief has only {n_charts} chart(s); SKILL.md spec "
            f"floor is {chart_floor} (4-6 typical). Add charts in different "
            f"spine sections to give every major dimension of the analysis "
            f"visual support — FX/debt trajectory in Section 3; security "
            f"events over time in Section 4; comparative benchmark in Section "
            f"18; humanitarian population in Section 8. Consult the chart-"
            f"recipe registry above."
        )
    elif n_charts > chart_ceiling:
        warnings.append(
            f"Structural: brief has {n_charts} charts; SKILL.md spec soft "
            f"ceiling is {chart_ceiling}. Beyond this, charts compete for "
            f"reader attention and start to feel like wallpaper rather than "
            f"decision support. Audit each chart against the 'shows something "
            f"prose can't' test; merge or cut the weakest candidates."
        )

    # Check 5: Risk matrix presence.
    has_risk_matrix = (
        ":::risk-matrix" in md_text.replace(" ", "")
        or "::: risk-matrix" in md_text
    )
    if not has_risk_matrix:
        msg = (
            "Structural: no ::: risk-matrix block found. Most country briefs "
            "benefit from a 2x2 risk plot identifying the most decision-relevant "
            "tail risks. Add a `::: risk-matrix` block (typically before Section "
            "19 Outlook)."
        )
        warnings.append(msg)
        strict_promotable.append((msg, "risk-matrix"))

    # Check 6: Recommendations section. Language-aware — matches the English
    # heading and the standard Arabic equivalent (التوصيات).
    has_recs = bool(
        re.search(r'^\*\*(?:Recommendations|التوصيات)\*\*\s*$', md_text, re.MULTILINE)
        or re.search(r'^##\s+(?:Recommendations|التوصيات)', md_text, re.MULTILINE)
    )
    if not has_recs:
        msg = (
            "Structural: no Recommendations section found. The skill spec calls "
            "for 3-5 portfolio-level recommendations with explicit Owner and "
            "Timeline labels. Add a **Recommendations** section near the end of "
            "the brief, before the methodological back-matter."
        )
        warnings.append(msg)
        strict_promotable.append((msg, "recommendations"))

    # Check 6.5: Section-aware leader-cards bounds.
    leader_cards_pattern = re.compile(
        r'^:::[ \t]*leader-cards[ \t]*$\n(.*?)^:::[ \t]*$',
        re.MULTILINE | re.DOTALL,
    )
    s15_exact = _THRESHOLDS["leader_cards_section_15_exact"]
    s2_floor = _THRESHOLDS["leader_cards_section_2_floor"]
    default_floor = _THRESHOLDS["leader_cards_default_floor"]
    for m in leader_cards_pattern.finditer(md_text):
        block_body = m.group(1)
        block_start = m.start()
        preceding_headings = re.findall(
            r'^##\s+(\d+(?:\.\d+)?)[\.\s]',
            md_text[:block_start],
            re.MULTILINE,
        )
        section_num = preceding_headings[-1] if preceding_headings else None
        rows = [
            line for line in block_body.splitlines()
            if line.strip().startswith("-")
        ]
        n_rows = len(rows)
        if section_num == "1.5":
            if n_rows < s15_exact:
                warnings.append(
                    f"Structural: Section 1.5 leader-cards block has only "
                    f"{n_rows} card(s). The bilateral section is the heads-"
                    f"of-mission view; show exactly two cards — the UAE "
                    f"ambassador to the country and the country's ambassador "
                    f"to the UAE."
                )
            elif n_rows > s15_exact:
                warnings.append(
                    f"Structural: Section 1.5 leader-cards has {n_rows} "
                    f"cards. The bilateral section is the heads-of-mission "
                    f"view; show only the two ambassadors. Ministerial "
                    f"leads (trade ministers, NSAs, special envoys, joint-"
                    f"commission chairs) belong in the visits-and-engagements "
                    f"timeline by name, or as full leader-cards in Section 2 "
                    f"if politically central to the country itself. Keeping "
                    f"Section 1.5 to exactly the two ambassadors makes every "
                    f"bilateral section consistent at a glance."
                )
        elif section_num == "2":
            if n_rows < s2_floor:
                warnings.append(
                    f"Structural: Section 2 leader-cards block has only "
                    f"{n_rows} card(s). Political-context blocks should "
                    f"show the real power configuration (head of state + "
                    f"prime minister or successor + opposition / faction "
                    f"leaders) — at least {s2_floor} figures. Trimming below "
                    f"this strips the brief's ability to communicate de "
                    f"facto power dynamics."
                )
        else:
            if n_rows < default_floor:
                warnings.append(
                    f"Structural: a leader-cards block has only {n_rows} "
                    f"card(s). A single-card block almost always indicates "
                    f"incomplete content. Either expand to >={default_floor} "
                    f"cards or remove the block."
                )

    # Check 7: Decision-implication coverage.
    spine_section_pattern = re.compile(
        r'^##\s+(?:1\.|1\.5\.|2\.|3\.|4\.|5\.|6\.)',
        re.MULTILINE
    )
    spine_section_count = len(spine_section_pattern.findall(md_text))
    decision_impl_count = md_text.count(":::decision-implication") + md_text.count("::: decision-implication")
    di_tolerance = _THRESHOLDS["decision_implication_gap_tolerance"]
    if spine_section_count >= 5 and decision_impl_count < spine_section_count - di_tolerance:
        warnings.append(
            f"Structural: brief has {spine_section_count} spine sections but only "
            f"{decision_impl_count} ::: decision-implication callouts. The spec "
            f"calls for one per spine section. Consider whether each major section "
            f"is concluding with explicit 'so-what for the portfolio' framing."
        )

    # Check 8: Series-leakage phrases.
    series_leakage_patterns = [
        r"brief series",
        r"earlier brief(?:s)?\b",
        r"other brief(?:s)?\b(?! \()",
        r"covered in (?:earlier|prior|other) brief",
        r"in this series\b",
        r"countries in (?:this |the )?series\b",
        r"سلسلة الموجزات",
        r"الموجزات السابقة",
        r"موجزات سابقة",
        r"موجزات أخرى",
        r"في هذه السلسلة",
        r"في موجزات سابقة",
    ]
    series_leakage_hits = []
    for pattern in series_leakage_patterns:
        for match in re.finditer(pattern, md_text, re.IGNORECASE):
            start = max(0, match.start() - 40)
            end = min(len(md_text), match.end() + 40)
            snippet = md_text[start:end].replace("\n", " ").strip()
            series_leakage_hits.append((match.group(0), snippet))
    filtered_hits = []
    for matched_text, snippet in series_leakage_hits:
        idx = md_text.find(snippet)
        if idx >= 0:
            preceding = md_text[max(0, idx - 500):idx]
            if "delta-summary" in preceding and ":::" not in md_text[idx:idx + 50]:
                continue
        filtered_hits.append((matched_text, snippet))
    if filtered_hits:
        max_examples = _THRESHOLDS["series_leakage_example_max"]
        examples = "; ".join(f"'{m}' in: ...{s}..." for m, s in filtered_hits[:max_examples])
        warnings.append(
            f"Structural: possible series-leakage language detected "
            f"({len(filtered_hits)} instance{'s' if len(filtered_hits) != 1 else ''}). "
            f"Each brief is standalone; the reader has one brief in front of them "
            f"and doesn't know what other briefs exist. Replace comparative language "
            f"like 'of any country in this brief series' with absolute descriptions. "
            f"Examples: {examples}"
        )

    return warnings, strict_promotable


def validate_brief(md_text: str, strict: bool = False) -> tuple:
    """Run pre-render validation on the brief markdown.

    This catches common errors before rendering so the analyst sees them
    as actionable warnings rather than silent failures or confusing output.

    Returns a tuple (warnings, errors):
    - warnings: list of strings — issues that should be flagged but don't
      block rendering (typos, possible problems, deprecation notices)
    - errors: list of strings — issues that produce broken output if not
      fixed (truly missing data, malformed syntax in core components)

    Default mode (strict=False) is warn-only — every check emits a warning
    and the render proceeds. The principle: noisy failure > silent failure,
    and the analyst keeps autonomy over what counts as "done."

    Strict mode (strict=True) promotes three structural checks from warning
    to error, on the grounds that a brief without them is not analytically
    complete and should not be rendered to PDF for a portfolio audience:

      - Zero footnote references in a substantive brief (>120 body lines)
      - No `::: risk-matrix` block in a substantive brief
      - No Recommendations section

    These three were chosen because (a) each is unambiguously specified by
    SKILL.md as a required component of any complete brief, and (b) each is
    detectable structurally without semantic judgment. Other warnings
    (footnote density, bottom-line length, series-leakage phrases) remain
    warnings even in strict mode because they involve judgment calls the
    analyst should make rather than a mechanical block.

    Checks performed:
    1. Footnote reference / definition mismatch
    2. Fenced-div blocks with unrecognized class names
    3. Stats-strip / risk-matrix / verdict-strip lines that don't parse
    4. Section number gaps that look like typos vs. intentional omissions
    5. Map blocks missing required `country:` parameter
    6. Empty fenced-div blocks (open but no content)
    7. Structural-audit checks gated at 120 body lines
    """
    warnings = []
    errors = []
    # Tags structural checks for optional promotion under strict=True.
    # Populated as warnings[] grows; each entry is a (warning_text, check_key)
    # so cli.py / strict mode can later move specific ones to errors.
    strict_promotable = []  # list of (warning_text, key) where key is 'footnotes' | 'risk-matrix' | 'recommendations'

    # --- Check 1: Footnote references vs. definitions ---
    # A definition is `[^foo]:` at the start of a line.
    # A reference is `[^foo]` NOT followed by `:` (in the body).
    # Use negative lookahead so we don't double-count `[^foo]:` as both.
    refs = set(re.findall(r"\[\^([a-zA-Z0-9_-]+)\](?!:)", md_text))
    defs = set(re.findall(r"^\[\^([a-zA-Z0-9_-]+)\]:", md_text, re.MULTILINE))
    undefined = refs - defs
    if undefined:
        for fn in sorted(undefined):
            warnings.append(
                f"Footnote [^{fn}] referenced but never defined. "
                f"Add a line: [^{fn}]: <citation>"
            )
    # Unused definitions are usually fine (analyst may have removed text
    # that referenced them) but worth a soft note
    unused = defs - refs
    if unused:
        for fn in sorted(unused):
            warnings.append(
                f"Footnote [^{fn}] is defined but never referenced in body text."
            )

    # --- Check 2: Fenced-div class names ---
    # The set of recognized class names. Adding a new component requires
    # adding it here so typos in existing ones get flagged.
    known_classes = {
        "exec-summary", "snapshot", "stats-strip", "bilateral-stats",
        "verdict-strip", "thesis", "bottom-line", "key-judgment",
        "counterfactual", "known-unknowns",
        "risk-matrix", "scenario", "faction-box", "severity-box",
        "chart", "map", "decision-implication", "leader-cards",
        "delta-summary", "scoring-summary",
    }
    # Inline whitespace only ([ \t]*, not \s*) so the match stays on a single
    # line. With re.MULTILINE alone, `\s*` matches across newlines because
    # Python's \s includes \n — so a stray "---" horizontal rule following a
    # blank line after a "::: close" would get spuriously captured as a fenced
    # class name. Using [ \t]* anchors the whole match to one line.
    fenced_classes = re.findall(r"^:::[ \t]*([\w-]+)[ \t]*$", md_text, re.MULTILINE)
    for cls in fenced_classes:
        if cls not in known_classes:
            # Find a likely intended match if any
            import difflib
            suggestion = difflib.get_close_matches(
                cls, list(known_classes), n=1, cutoff=0.7
            )
            hint = f" Did you mean ':::{suggestion[0]}'?" if suggestion else ""
            warnings.append(
                f"Fenced div class ':::{cls}' is not a recognized component.{hint}"
            )

    # --- Check 3: Empty fenced-div blocks ---
    # Match ::: cls ... ::: where the body is whitespace-only
    empty_pattern = re.compile(
        # Inline parts use [ \t]* so the opener/closer stays single-line;
        # the body group uses \s* deliberately (multi-line whitespace).
        r"^:::[ \t]*([\w-]+)[ \t]*$\n(\s*)^:::[ \t]*$",
        re.MULTILINE,
    )
    for m in empty_pattern.finditer(md_text):
        cls = m.group(1)
        warnings.append(f"Fenced div ':::{cls}' is empty (no content between markers).")

    # --- Check 4: Map blocks missing country parameter ---
    # Find every map block and check if it has a country line
    map_pattern = re.compile(
        # Opener/closer must stay on a single line (use [ \t]*); the body
        # between them spans multiple lines via DOTALL.
        r"^:::[ \t]*map[ \t]*$\n(.*?)^:::[ \t]*$",
        re.MULTILINE | re.DOTALL,
    )
    for m in map_pattern.finditer(md_text):
        body = m.group(1)
        if not re.search(r"^[ \t]*country[ \t]*:", body, re.MULTILINE):
            warnings.append(
                "A map block is missing the 'country:' parameter. "
                "The map will render an error placeholder. Add a line: country: <CountryName>"
            )

    # --- Check 5: Section number gaps ---
    # Extract section numbers from H2 headings like "## 1. Country Snapshot"
    section_nums = []
    for m in re.finditer(r"^##\s+(\d+)(?:\.\d+)?\.?\s+", md_text, re.MULTILINE):
        section_nums.append(int(m.group(1)))
    # Look for gaps that might indicate a forgotten section. A "gap" here
    # means jumping by more than 1, EXCEPT when skipping a known optional
    # module range (7-18). Skipping from 6 to 8 is a fine omission of
    # Section 7. Skipping from 6 to 12 is also fine (multiple module
    # omissions). Skipping from 1 to 5 IS suspicious because 2-4 are spine.
    if section_nums:
        spine_sections = {1, 2, 3, 4, 5, 6, 19}
        present = set(section_nums)
        missing_spine = spine_sections - present
        if missing_spine:
            warnings.append(
                f"Spine sections missing from brief: {sorted(missing_spine)}. "
                f"Spine sections (1-6, 19) should always be present in a complete brief."
            )

    # --- Check 6: Stats-strip / verdict-strip / risk-matrix parse cleanly ---
    # Best-effort parse check. Find each block, try parsing its content,
    # and flag lines that look like they should match but don't.
    strip_pattern = re.compile(
        # Same single-line anchoring on opener/closer; multi-line body via DOTALL.
        r"^:::[ \t]*(stats-strip|bilateral-stats|verdict-strip|risk-matrix|severity-box|faction-box)[ \t]*$\n(.*?)^:::[ \t]*$",
        re.MULTILINE | re.DOTALL,
    )
    for m in strip_pattern.finditer(md_text):
        cls = m.group(1)
        body = m.group(2)
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line or not line.startswith("-"):
                continue
            content = line.lstrip("-").strip()
            # Each component has specific expectations:
            if cls in ("stats-strip", "bilateral-stats"):
                # Expect: "<number> | <label> | <source>"  (3 parts via pipe)
                if content.count("|") < 1:
                    warnings.append(
                        f"In :::{cls} block, line missing '|' separator: '{content[:60]}'"
                    )
            elif cls == "verdict-strip":
                # Expect: "<label>: <color> | <caption>"
                if ":" not in content or "|" not in content:
                    warnings.append(
                        f"In :::verdict-strip block, line not in 'Label: color | Caption' format: '{content[:60]}'"
                    )
            elif cls == "risk-matrix":
                # Expect: "<label> | likelihood: X | impact: Y"
                if content.count("|") < 2 or "likelihood" not in content.lower():
                    warnings.append(
                        f"In :::risk-matrix block, line not in 'Label | likelihood: X | impact: Y' format: '{content[:60]}'"
                    )
            elif cls in ("severity-box", "faction-box"):
                # Expect: "<region/actor> | <category> | <description>"
                if content.count("|") < 1:
                    warnings.append(
                        f"In :::{cls} block, line missing '|' separator: '{content[:60]}'"
                    )

    # ─────────────────────────────────────────────────────────────────
    # Structural-discipline checks: warn when the brief departs from
    # the SKILL.md spec in ways that experience shows produce poor
    # deliverables. These are soft warnings (not errors) — the renderer
    # continues. The goal is to surface drift so the analyst can fix it
    # before declaring a brief done.
    #
    # Calibration: each check has a threshold tuned to flag genuinely
    # problematic cases without spamming warnings for stylistic choices.
    # Thresholds came from auditing the May 2026 brief series (Ethiopia,
    # Sudan, Syria, Morocco, Sri Lanka, Iran) where the well-structured
    # briefs comfortably exceed the floors below.
    #
    # Size gate: structural audits only fire on substantive briefs
    # (>120 body lines, ≈8+ pages). Test fixtures and minimal smoke
    # briefs are by design too small to warrant these audits — flagging
    # them would create noise without analytical value.
    # ─────────────────────────────────────────────────────────────────

    # First, count body lines (used both for the size gate and for
    # the footnote-density check below).
    body_lines = 0
    in_fence = False
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith(":::"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped and not stripped.startswith("#"):
            body_lines += 1

    # Size gate: only run structural-discipline audit on substantive briefs.
    # Test fixtures and minimal briefs skip this entirely; flagging them
    # would create noise without analytical value.
    if body_lines >= _THRESHOLDS["structural_audit_min_body_lines"]:
        audit_warnings, audit_strict = _run_structural_audit(md_text, body_lines)
        warnings.extend(audit_warnings)
        strict_promotable.extend(audit_strict)

    # Strict mode: promote the three "binding" structural warnings to errors.
    # Tagged at emission time via strict_promotable; here we move them out of
    # warnings[] and into errors[]. Other warnings (footnote density, bottom-
    # line length, series-leakage, decision-implication coverage) stay as
    # warnings even under strict, because they involve judgment calls the
    # analyst should make rather than a mechanical block.
    if strict and strict_promotable:
        for msg, key in strict_promotable:
            if msg in warnings:
                warnings.remove(msg)
                errors.append(f"[--strict] {msg}")

    return warnings, errors


