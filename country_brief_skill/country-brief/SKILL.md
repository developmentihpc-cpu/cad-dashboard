---
name: country-brief
description: Produce deep, print-ready country briefs as styled PDFs — covering politics, economy, security, governance, and any user-specified angle (development, humanitarian, market entry, regulatory, sanctions). Always trigger this skill when the user asks for a "country brief," "country profile," "country assessment," "country analysis," "situation report on [country]," "background on [country]," or any deliverable summarizing a country for decision-makers. Trigger even when the user names a country and asks for a "deep dive," "writeup," or "memo" without using the word "brief," as long as the request is country-level analysis. Do not trigger for single-question lookups ("what's the GDP of X?"), travel advisories, news summaries, or comparative reports about a topic across many countries.
---

# Country Brief

This skill produces deep, decision-grade country briefs (10–15+ pages) with a 2–3 page executive summary on top that stands alone for skim-readers. Output is a styled, print-ready PDF with Chicago-style numbered footnotes.

The skill is general-purpose: the same backbone supports development-project evaluation, humanitarian assessment, market-entry analysis, political risk monitoring, regulatory due diligence, and academic country profiles. The user's framing determines which optional modules to pull in — the spine stays the same.

> **Verify your install before relying on a brief render.** Run `python tests/run_smoke_tests.py` from the skill root. The canonical pass is `23 passed, 0 failed` in ~170 seconds. Any failure here means the renderer is mis-installed (typically missing `pyarrow`, missing GTK/Pango on Windows or macOS, or stale Pandoc) and brief renders will produce silent gaps. See **INSTALL.md** for the per-OS dependency list.

## When you should reach for this skill

If the user says any of "country brief," "country profile," "country assessment," "country analysis," "background on [country X]," "situation report on [country X]," "deep dive on [country X]," or asks for a memo/writeup that summarizes a country for someone making a decision — use this skill. The skill is also right when the user describes the audience (e.g., "for our portfolio committee," "for a senior team unfamiliar with the region") and the deliverable is country-level.

Do not use it for single-question lookups ("what's Egypt's GDP?"), pure travel advisories, current-events news summaries, or cross-country comparative reports where the unit of analysis is a topic rather than a country.

## How to start

When invoked, take these steps in order. Skip steps only when the user has already supplied the answer.

> **🔴 REQUIRED READING — BEFORE WRITING ANY MODULE.**
>
> Before drafting any spine section beyond Section 1, AND before selecting which optional modules fire, you MUST view these two references in full:
>
> 1. **`references/section-library.md`** — the canonical menu of optional modules with per-module preconditions, content checklists, and source priorities. Skipping this leads to missed modules and reinvented section content.
> 2. **`references/section-quality.md`** — per-section analytical-discipline guidance. Defines the central question each section must answer, signs of strong vs weak content, source priority, and the specific failure modes that produce weak briefs.
>
> These are not optional. Drift in module selection and analytical depth has been traced directly to skipping these files. Read them before writing, not after the validator warns you.
>
> For Arabic briefs, also read `references/arabic-style.md` BEFORE Phase 2 translation. The three-phase discipline (Compose-English → Translate-Adapt → Institutional-Editorial-Pass) does not work without it.

**1. Establish purpose and angle (for internal use, not for the cover).** Country briefs serve different decisions and different readers, and the angle determines which optional sections matter. Get clear internally on: *what decision the brief informs*, and *what specific angle the user cares about* (e.g., "should we proceed with a $5M education project in country X" vs. "is country Y a viable export market for our products").

If the user supplies an angle, use it. If the user just names a country with no angle, **infer the default** rather than asking. The decision rule:

| Country signal (observable) | Default angle |
|---|---|
| Active military conflict, ceasefire-but-imminent-resumption, regime crisis | **Wartime variant** (see Wartime brief section). No angle question. |
| INFORM Risk "High" / "Very High" OR aid >5% GDP | **Humanitarian / development** weight: spine + sections 8 (Humanitarian) and 7 (Development Project). |
| OFAC / EU / UN sanctioned (broad) | **Political risk + sanctions** weight: spine + sections 14 (Sanctions) and 16 (Regulatory). |
| Banking / financial-services hub, special economic zone identity, or sovereign-wealth-fund-active GCC state | **Commercial / regulatory** weight: spine + sections 15 (Market Entry) and 16 (Regulatory). |
| Election within 12 months OR recent transition (<24 months) | **Political risk** weight: spine + sections 2 (Political) and 11 (Election cycle). |
| Multiple signals fire OR none strongly | **General portfolio brief** — balanced spine, no single weighted angle. This is the safe default. |

After inferring, **state the inference up front in one line** so the user can redirect cheaply: "Producing a *[inferred angle]* brief for [Country] because [observable signal]. Reply with a different angle if needed; otherwise I'll proceed." Then continue without waiting for confirmation unless the user objects — the skill defaults to forward motion, not blocking on confirmation.

Ask the user only when (a) the user's framing is unusually narrow ("I need the regulatory chapter for our 10-K"), (b) multiple strong signals conflict in a way the rule above doesn't disambiguate, or (c) the angle would meaningfully change scope (e.g., a 5-page sector deep-dive vs. a 30-page general brief).

Crucially, the angle and intended audience inform *your section selection and emphasis*, not the cover page. Do not put "Prepared for: [audience]" or "Angle: [purpose]" on the cover unless the user explicitly supplies these as cover-page metadata. Defaulting these to invented values like "Internal" or "General" makes the cover look templated and is worse than leaving them off. The cover should show date, country, and an optional subtitle only — nothing fabricated.

**2. Pick the modules.** The skill has a fixed spine and a library of optional modules in `references/section-library.md`. Read that file now to see the full menu, then pick the modules that match the stated purpose. A development brief pulls in governance, fragility, project-environment, and donor-landscape modules. A market-entry brief pulls in market-size, regulatory, and competitive-landscape modules. A humanitarian brief pulls in severity, displacement, and access modules. Don't include every module — irrelevant sections make briefs feel padded and hide the analysis.

**3. Read the section-quality reference for the modules you've picked.** `references/section-quality.md` codifies what separates strong analytical content from weak content for each section, grounded in failures and successes observed across five country briefs. Read at minimum the entries for: Executive Summary, Country Snapshot, the four-five sections that will carry the most analytical weight for this brief, and the Outlook section. Each entry specifies the central question the section must answer, signs of strong vs weak content, source priority, and common analytical traps. Going to write a Political Context section? Read its entry. Going to write a Macro Stress section? Read its entry. The reference exists because following it is the difference between a brief that *looks* analytical and a brief that *is* analytical.

**4. Plan source coverage.** Before writing, sketch which authoritative sources will anchor the brief. `references/data-sources.md` lists the trusted catalog by domain. The aim is breadth (don't lean on one source for everything) plus recency (data more than 3 years old needs a flag).

**5. Search for current information.** The brief must reflect the present, not a 12-month-old snapshot. Use web search aggressively for: current head of state and government, latest elections, most recent IMF Article IV or World Bank Country Economic Memorandum, current sanctions regime, recent security incidents, latest fragility/governance scores. Anything time-bound needs a search.

**6. Draft to the structure below.** Don't invent your own structure — the architecture is the product of practice across the World Bank, S&P, EIU, Crisis Group, and intelligence-community writing standards. The discipline is what makes the brief legible at a glance.

**7. Render to PDF.** Use the bundled HTML→PDF workflow in `assets/brief-template.html` and `scripts/render_brief.py`. Save the final PDF to `/mnt/user-data/outputs/` and present it.

**8. Run the structural-audit checklist before declaring the brief done.** The renderer's pre-render validator catches most structural issues automatically, but a human-readable audit against the SKILL.md spec is the final discipline. Failures of this discipline produced visible quality regressions in the May 2026 brief series (notably the first Iran draft, which shipped without a map, multiple charts, a risk matrix, or footnote sourcing despite the skill spec calling for all of these). Before declaring any brief done, confirm:

- **Verdict strip** with 4 status tiles is present near the top.
- **Bottom Line** is 2-3 sentences (~60-80 words), not 2 dense paragraphs. If the bottom line exceeds ~100 words, the prioritization work wasn't done.
- **Key Judgments** block contains 4-7 bulleted claims, each with a directional arrow (↑/↓/→) and an optional confidence level.
- **Counterfactual** block is present and identifies what would invalidate the key judgments.
- **Reference map** (or at least one thematic choropleth map) is present. Most country briefs benefit from a map for geographic orientation.
- **Charts** — at least 3 per brief, 4-6 typical, soft ceiling of 8 (validator emits an under-count warning <3 and a soft-ceiling warning >8). Use the documented pipe-delimited syntax. Consult the chart-recipe registry (`_CHART_RECIPES` in `validation.py`) for country-specific high-leverage picks beyond generic GDP-and-inflation. If your chart renders empty, the YAML-style `data:` format is the most common mistake — see the chart syntax section for the correct format and explicit anti-pattern.
- **Risk matrix** plots 5-9 tail risks on a 2×2 of likelihood vs impact.
- **Every spine section** (1, 1.5 if bilateral, 2, 3, 4, 5, 6) ends with its own `::: decision-implication` callout connecting the section's content to the brief's portfolio relevance.
- **Outlook section** uses scenario boxes for any country with material uncertainty (wartime, post-default, transition, etc.) rather than a single-track forecast.
- **Recommendations** section is present with 3-6 portfolio-level recommendations, each with explicit Owner and Timeline.
- **Footnotes** are present and dense enough to substantiate the consequential factual claims (typically 1 per ~30-40 lines of body prose). The renderer auto-generates the bibliography from `[^N]: source-text` definitions at the end of the markdown.
- **Methodological back-matter** acknowledges brief vintage, source-quality limitations, and confidence calibration.

If the brief is wartime, post-default, regime crisis, or otherwise exceptional, follow the **Wartime brief variant** guidance below — the variant flexes the spec to handle exceptional content but does not abandon the structure. The temptation to treat exceptional countries as license to depart from the skill is the most common discipline failure observed across the May 2026 brief series; the structural-audit checklist is the antidote.

## The structure (always use this spine)

Country briefs work because readers know what to expect and where to find it. Use this exact spine, with module sections inserted where indicated.

```
# Country Brief: [Country Name]
## Date: [Month YYYY]  |  Prepared for: [Audience]  |  Angle: [Purpose]

---
EXECUTIVE SUMMARY (target 1 page, allow up to 2 if visuals require it; must stand alone)
  - Verdict strip (4 angle-dependent dimensions, traffic-light colors, one-line caption each)
  - Bottom line (2–3 sentences — the single sentence a senior reader would quote)
  - Key judgments (4 bullets, each with a required trajectory arrow ↑ → ↓ or ⇅, 1–2 sentences, no supporting detail)
  - Risk matrix (2×2 Likelihood × Impact with the 3 critical risks plotted; narrative labels, not a ranked list)
  - Recommendations / implications (3, one line each, actionable)

---
1. COUNTRY SNAPSHOT (½–¾ page; 4 sub-blocks in a 2×2 grid: People / Politics / Economy / Stability; trend arrows on direction-sensitive economic and stability indicators only; "Last reviewed" date inline; single source line at bottom — see dedicated section below for full structure)

1.5. HOME-COUNTRY BILATERAL RELATIONS (1–1.5 pages; included when `--home-country` is set to a country name; default UAE; suppressed when `--home-country none` is passed) — bilateral-stats strip + 6 subsections covering diplomatic relationship, senior visits, treaties, home-country investment in target, target-country presence in home country, and aid cooperation. See dedicated section below.

2. POLITICAL CONTEXT (1.5–2 pages) — standard visual: faction box (situational)
   - Power structure and key actors (who actually decides)
   - Recent political trajectory (last 3–5 years)
   - Elections cycle, opposition, civil society space
   - Civil-military relations where relevant

3. ECONOMIC CONDITIONS (1.5–2 pages) — standard visual: macro indicators table (current / prior period / trend)
   - Structure of the economy (sectoral composition, drivers)
   - Recent macro performance and outlook
   - Fiscal position, debt sustainability, FX regime
   - External accounts, key trade partners

4. SECURITY & STABILITY (1–2 pages) — standard visuals: stats strip + severity-box
   - Threat landscape (state, non-state, criminal, terrorist as applicable)
   - Conflict drivers and sub-national variation
   - Recent incidents and trend lines (ACLED, UCDP)
   - Forecasting based on observable indicators

5. GOVERNANCE & RULE OF LAW (1 page) — standard visual: WGI scorecard table
   - WGI scores trend, V-Dem indices if available
   - Corruption (CPI), regulatory quality, judicial independence
   - Implementation gap (what's on paper vs. what happens)

6. SOCIAL & HUMAN DEVELOPMENT (¾–1 page) — standard visual: stats strip
   - HDI position and trajectory
   - Key social indicators (poverty, health, education) relative to peers
   - Sub-national disparities

7. [INSERT RELEVANT MODULES HERE — pulled from section-library.md]
   - Humanitarian severity (if applicable) — standard visual: stats strip
   - Market entry / business environment (if applicable)
   - Sanctions exposure (if applicable)
   - Project / operating environment (if applicable) — standard visual: scenario boxes for lessons-learned
   - Macro stress / debt deep-dive (if applicable) — standard visuals: stats strip + timeline + stress scenario boxes
   - Climate vulnerability (if applicable)
   - Regulatory regime (if applicable)

8. COMPARATIVE BENCHMARKING (½–1 page) — standard visual: cross-country indicator table
   - 2–4 peer countries (regional, income-group, or analytically chosen)
   - Side-by-side on 6–10 indicators
   - Where the country leads or lags, and why it matters

9. OUTLOOK (½–1 page) — standard visual: scenario boxes (base / upside / downside)
   - 6–12 month base case
   - Upside / downside drivers
   - Indicators to watch

10. BIBLIOGRAPHY (full list, Chicago style)
```

## When each optional module fires

The 11 optional modules in `references/section-library.md` are not a menu to pick from arbitrarily — each has analytical preconditions. A module fires when the country has the characteristic the module is designed to surface. If you find yourself stretching to make a module fit, that's a signal to drop it, not include it.

### Canonical section-slot numbering (use these on first pass — do NOT renumber later)

Every brief uses the same section numbers for the same modules. **Use these exact numbers from the start; do not number sequentially through whichever modules you happen to include.** Renumbering after the validator warns about "Section 19 missing" is a quality regression — it indicates the canonical map below wasn't followed.

| # | Section / Module | When it appears |
|---|---|---|
| **1** | Country Snapshot | Always (spine) |
| **1.5** | Bilateral Relations | When `--home-country` is set (default UAE) |
| **2** | Political Context | Always (spine) |
| **3** | Economic Conditions | Always (spine) |
| **4** | Security & Stability | Always (spine) |
| **5** | Governance & Rule of Law | Always (spine) |
| **6** | Social & Human Development | Always (spine) |
| **7** | Development Project Environment | Optional — fires per preconditions below |
| **8** | Humanitarian Severity | Optional |
| **9** | Macro Stress / Debt Sustainability | Optional |
| **10** | Climate Vulnerability | Optional |
| **11** | Election Cycle / Political Transition | Optional |
| **12** | Civil Society & Media Environment | Optional |
| **13** | Diaspora & Remittances | Optional |
| **14** | Sanctions Exposure | Optional |
| **15** | Market Entry / Business Environment (Re-entry for wartime) | Optional |
| **16** | Regulatory Regime | Optional |
| **17** | Project & Operating Environment | Optional |
| **18** | Comparative Benchmarking | Optional |
| **19** | Outlook | Always (closes the brief) |

If a module doesn't fire, skip its number entirely — go from Section 6 to whichever optional fires first (e.g., 6 → 8 → 13 → 14 → 18 → 19). Don't renumber to make sections sequential; the canonical numbers are what the validator and the analyst's mental model both depend on.

### When each module fires

| Module | Fires when... |
|--------|---------------|
| **7 — Development Project Environment** | Country is IDA-eligible or significant aid recipient (aid >5% of GDP) |
| **8 — Humanitarian Severity** | INFORM Risk Index "High" or "Very High" |
| **9 — Macro Stress / Debt Sustainability** | Country in IMF program OR IMF DSA rating "high risk" or "in distress" |
| **10 — Climate Vulnerability** | Country in top quartile of ND-GAIN vulnerability OR brief is climate-finance |
| **11 — Election Cycle / Political Transition** | Election within 18 months OR recent transition <24 months ago |
| **12 — Civil Society & Media Environment** | CIVICUS rating "obstructed" or worse OR brief angle is rights/governance |
| **13 — Diaspora & Remittances** | Remittances >5% of GDP OR diaspora >5% of population. **For UAE home-country briefs: also fires by default for any country with diaspora >100k in the UAE** (Iran, India, Pakistan, Bangladesh, Philippines, Egypt, Lebanon, Sri Lanka, Nepal, and similar). The UAE-resident diaspora is typically the most operationally material Iran/India/Pakistan dimension for a UAE portfolio — substantially more so than UAE-in-target investment. |
| **14 — Sanctions Exposure** | Country is on UN/EU/US/UK sanctions lists (broad or targeted) |
| **15 — Market Entry / Business Environment** | Brief angle is private-sector or commercial expansion (becomes "Re-entry scenarios" in wartime variant) |
| **16 — Regulatory Regime** | Brief angle is deal-level due diligence or sector-specific |
| **17 — Project / Operating Environment** | Brief angle is operational for development implementers |
| **18 — Comparative Benchmarking** | Almost always when there are meaningful peer comparators (most briefs) |

**Order in the brief.** Modules that fire go between Section 6 (Social & Human Development) and Section 19 (Outlook) — populating the 7-18 slots per the canonical numbering above. When multiple modules fire, present them in canonical-number order (not in "decision-relevance" order). Decision-relevance shapes which sections get more analytical depth, not which slot number they occupy.

**Negative findings.** If a module fires but the country's situation is relatively benign on that dimension (e.g., Sanctions Exposure for a country with only targeted UN sanctions on individuals), still include the section but write it as a "limited applicability" finding. Sometimes the analytical signal *is* "this isn't a major exposure" — and a portfolio analyst benefits from seeing that explicitly rather than from the module being silently omitted.

**Don't force fit.** If three modules fire naturally but a fourth would require stretching, leave it out. The skill is not graded on module count. A focused 4-module brief reads better than a 7-module brief padded with weak content.

## Wartime brief variant

When the country is in active war, fragile post-conflict transition, or under acute regime crisis, the brief structure adapts but **does not abandon the skill scaffolding**. The temptation is to treat exceptional countries as license to depart from the spine — that produces idiosyncratic deliverables that can't be compared against the rest of the series. The correct response is to use the existing structure to communicate wartime conditions rigorously.

**When this variant applies.** The wartime variant fires for countries meeting any of: (a) active military conflict (interstate or major civil war); (b) ceasefire conditions where resumption is plausibly imminent; (c) regime crisis with succession uncertainty (e.g., recently-killed leader, contested succession); (d) acute political-military-economic compound crisis where conventional planning horizons (12-24 months) are not meaningful. The Iran brief (May 2026, active Iran-US-Israel war + IRGC operational takeover + fragile ceasefire) is the canonical case.

**Section adaptations under wartime.**

- *Section 4 (Security & Stability)* expands substantially and becomes the brief's longest analytical section. Required content: chronology of the conflict with dated milestones; current operational state with explicit "as of [date]" stamp; military capability assessment for the country's own forces and relevant external actors; nuclear/sanctions/blockade conditions where relevant; severity-box covering regional security gradient; internal-security dimensions including protests, repression, and dissident treatment; regional realignment dynamics. The standard Section 4 covers some of this; the wartime variant goes deeper on all of it.

- *Section 15 (Market Entry)* reframes from "current market entry conditions" to "re-entry scenarios and prerequisites." The current country is closed; the analytically useful content is what would have to be true for engagement to become possible. Document Tier 1 prerequisites (durable ceasefire, sanctions clarification, currency stabilization, banking access, political consolidation) and Tier 2 sector-by-sector difficulty assessment.

- *Section 16 (Regulatory & Sanctions)* expands the sanctions discussion into its full architecture (primary, secondary, UN, EU, FATF). The sanctions environment IS the binding constraint, not a peripheral consideration.

- *Section 19 (Outlook)* uses 4-5 scenario boxes with explicit probability weights and per-scenario portfolio implications. A single-track forecast is irresponsible for an active-war country where outcomes are genuinely indeterminate. Use scenarios A through D (or E) covering the realistic outcome space: continued conflict, ceasefire holds with normalization, ceasefire holds without normalization, internal regime crisis, negotiated settlement. Each scenario gets its own scenario-box with probability and portfolio implications.

- *Bottom Line and back-matter* explicitly acknowledge shorter shelf life. Wartime briefs have useful life measured in days to weeks rather than months. Methodological back-matter should specify what changes would trigger a re-validation (ceasefire collapse, succession developments, sanctions architecture changes, etc.).

**Every judgment carries explicit war-contingent labels.** In Key Judgments, in section prose, in scenario boxes, in recommendations — wartime briefs should make it visible to the reader which claims hold under all scenarios and which are scenario-specific. The skill's confidence levels (`high`, `moderate`, `low`) remain in use, but supplement with scenario-conditional language ("under Scenario A, X; under Scenario B, not-X").

**Confidence calibration is explicitly lower.** A wartime brief should state in its methodological back-matter that analytical confidence is lower than for comparable briefs on stable countries. This is not a hedge — it is honest source acknowledgment. Wartime sources have known reliability issues: state media propaganda, opposition source overreach, satellite-only verification gaps, sanctions-evading flows that are by design unmeasurable.

**Recommendations are typically defensive.** For UAE-domiciled (or other home-country) portfolios, wartime-country recommendations should typically include: defer new direct engagement; map existing exposures; stress-test against scenario set; tighten sanctions compliance for any adjacent positions; monitor home-country policy posture toward the wartime country; preserve optionality on humanitarian-relevant engagement where appropriate. The portfolio question is "how to manage existing exposure" not "whether to engage."

### Canonical wartime case study: Iran (May 2026)

**The Iran brief produced in May 2026 is the canonical wartime case study for this skill.** Before producing any new wartime brief, read [`iran-brief-may-2026.md`](iran-brief-may-2026.md) in the reference set if available, paying particular attention to:

- **The leader-cards / faction-box pairing in Section 2.** Iran's civilian-military divergence — Mojtaba Khamenei as Supreme Leader after father-to-son transfer, Ahmad Vahidi commanding the IRGC as the de facto operational authority, Pezeshkian as visibly-sidelined civilian president — is exactly the kind of political situation where the faction-box maps the power-center taxonomy and leader-cards put faces on the specific individuals. Wartime political reads need both.

- **Chronology-table density in Section 4.1.** A wartime brief's Section 4 chronology should carry 10+ dated rows covering the precipitating events, snapback architecture, regime decisions, and ceasefire mechanics. Sparse chronology in a wartime brief is a discipline failure — the events are *the* analytical anchor.

- **Four-scenario probability-weighted outlook in Section 19.** Iran's outlook uses five scenarios (A: continued conflict 30%, B: ceasefire-no-normalization 35%, C: ceasefire-with-limited-normalization 15%, D: internal regime crisis 15%, E: comprehensive settlement 5%). Each scenario explicitly names its monitoring indicators and portfolio implications. Single-track wartime forecasts are irresponsible; 4-5 explicit probability-weighted scenarios is the spec.

- **The Section 14 sanctions architecture treatment.** Multi-jurisdictional layering (UN snapback + EU reinstatement + OFAC + FATF blacklist) with explicit Resolution numbers and the "snapback's specific character" subsection (the architecture is a floor not a ceiling, no off-ramp under existing terms).

- **The Section 15 Tier-1/Tier-2 re-entry framework.** Wartime Market Entry reframes from "current entry conditions" to "what must be true for re-entry to become possible." Tier 1: durable ceasefire, sanctions clarification, currency stabilization, banking access, political consolidation. Tier 2: sector-by-sector difficulty assessment conditional on Tier 1.

If `iran-brief-may-2026.md` is not in the reference set on this install, treat the bullets above as the wartime structural checklist directly.

## Arabic-version production

The skill can produce country briefs in Arabic when requested (CLI flag `--language ar`, or markdown frontmatter `language: ar`). Arabic version is **produced via a three-phase discipline**: compose analytically in English, translate-and-adapt to Arabic at the paragraph level, then editorial-pass the result against Arabic institutional reference style. The quality bar is "indistinguishable from native institutional analytical writing" (IMF Arabic editions, World Bank Arabic, Brookings Doha, Crisis Group Arabic) — not from native journalism or classical scholarship. The earlier "native composition, not translation" rule was aspirational fiction; the three-phase discipline is honest about Claude's English-vs-Arabic depth asymmetry and produces stronger output.

**When to produce an Arabic version:** the user explicitly asks for it. Don't produce both versions by default — the Arabic brief is substantially more work and shouldn't be generated speculatively. If the user is ambiguous ("do you have this in Arabic?"), ask whether they want Arabic-only or both versions before proceeding.

**Required reading before producing an Arabic brief.** Three reference documents must be read before writing any Arabic content:

1. **`references/arabic-style.md`** — register, rhetorical conventions, sentence structure, signposting patterns, AND the three-phase discipline with named institutional reference sources for the Phase 3 editorial pass. This is the analytical anchor.
2. **`references/arabic-glossary.md`** — curated terminology for the brief's standard concepts (macroeconomics, sanctions, climate, governance, portfolio decision-making). Consistent terminology across all sections is the single most important quality discipline.
3. **`references/arabic-names.md`** — standardized Arabic forms for leaders, places, and institutions. Use the form listed for each country and add new names when first encountered.

**Production discipline (three phases).**

- **Phase 1 — Compose in English.** Produce the full English brief at full depth from source research. Section selection, chart picks, judgment calibration, decision-implication framing — all analytical work happens here, in the language where Claude's analytical depth is highest.
- **Phase 2 — Translate and adapt at paragraph level.** Translate to Arabic *paragraph by paragraph*, never sentence by sentence. Sentence-by-sentence translation produces calques and English-syntax-in-Arabic (the real failure mode the rule must prevent). Paragraph-level adaptation preserves analytical content while restructuring prose for Arabic rhetoric: verbal vs. nominal patterns, connector choice (إذ / حيث / بحيث / وعليه), hedging elaboration, calibrated rhythm. The glossary and proper-name registers apply throughout.
- **Phase 3 — Editorial pass against institutional reference style.** Read the Arabic for sentences that feel stilted, journalistic, or translated. Check each flagged sentence against an analogous passage in an institutional source — IMF Arabic Article IV editions for macro/financial language, World Bank Arabic country reports for development/governance, Brookings Doha / Crisis Group Arabic for political analysis, Al-Sharq Al-Awsat business sections for general register. Adjust toward the institutional norm. This catches calques the translation alone wouldn't fix.

**Terminology and naming consistency.** Use the glossary for every term it covers; add new terms when first encountered. Use the proper-name register for every name; add new names when first encountered. Calibrated hedging matches the English brief's confidence level but uses Arabic-natural elaboration (بدرجة عالية من الثقة, not just "high confidence"). One hedge layer; don't stack.

**Layout and rendering.** The Arabic version uses an RTL-aware variant of the brief template:
- `dir="rtl"` on the root document; all components mirror layout (verdict-strip flows right-to-left, leader-cards grid right-anchored, decision-implication callout border on the right side)
- Font stack switches to Arabic textbook fonts (Amiri Quran / Amiri / Cairo / Noto Naskh Arabic) for body text; numerals use Western-Arabic by default (1, 2, 3) for financial data consistency
- Charts produced by matplotlib have RTL-aware axis labels and Arabic-readable title positioning when chart titles are in Arabic
- Maps use Arabic region/country names where available via the `_REGION_DISPLAY_OVERRIDES` mechanism, otherwise transliterated

**Mixed-direction content.** Arabic professional documents routinely contain embedded English (company names, currency codes, technical acronyms). The renderer handles bidirectional text via Unicode handling; the analyst's job is to make the right choices about when to use Arabic vs. retain English:
- Person names: Arabic transliteration with English in parentheses on first reference for traceability
- Company/organization names: keep in original Latin script unless an established Arabic form exists
- Currency codes: keep in Latin script (USD, AED, IRR) for financial-data convention consistency
- Acronyms: use Arabic full form on first use with English acronym in parentheses, then choose either to continue with Arabic short form or to use the acronym depending on what's clearer

**Common quality failures specific to Arabic version.**

- *Translation tone leakage.* When the analyst writes in Arabic but mentally composes in English, the Arabic syntax follows English word order. Discipline: write each paragraph in Arabic syntax from the start, not English structure with Arabic vocabulary.
- *Inconsistent terminology.* The same concept appearing as multiple Arabic forms across the brief. Discipline: use the glossary; add new entries when needed but use one form throughout.
- *Mistranslated names.* Pezeshkian rendered three different ways. Discipline: use the name register.
- *Cultural-context flattening.* Compressed English terms (e.g., "hijab politics") rendered literally lose specific local meaning. Discipline: expand or specify when the context demands it (سياسات الحجاب الإلزامي in Iranian context).
- *Hedge inflation.* Multiple stacked hedges where English has one. Discipline: match the English calibration, don't multiply.

**Bilingual production** (both Arabic and English produced from the same request) is supported but should only be done when explicitly requested. Both versions are composed from the same source research; neither is a translation of the other. The Arabic version may legitimately differ in framing, signposting density, or rhetorical emphasis even while preserving identical analytical content.

## The executive summary: structure and discipline

The exec summary is the highest-leverage page in the brief. Senior decision-makers will read page 1; whether they read further is optional. The discipline is to do the prioritization work upfront — pick the four judgments that matter most, call the directional read on each, plot the risks, recommend three actions — so the reader doesn't have to.

Target length is one page. Allow up to two if the visuals push it; never more. If the brief is overflowing two pages, the analyst hasn't prioritized hard enough — cut content, don't shrink the font.

### Verdict strip (top of page)

Four angle-dependent dimensions, each with a traffic-light color and a one-line caption. The reader sees the shape of the country in two seconds before reading a word.

Pick the four dimensions that matter most for the brief's angle. Examples:

- **Development portfolio brief:** Macro / Security / Governance / Debt (or Operating Environment)
- **Humanitarian brief:** Severity / Access / Funding / Protection
- **Market entry brief:** Market Size / Regulation / Operating Costs / FX & Repatriation
- **Political risk brief:** Politics / Security / Civic Space / External Relations
- **Sanctions / compliance brief:** Sanctions Regime / Enforcement / Secondary Risk / Licensing

Color rules — be honest and consistent across the brief:
- **Green** — favorable, low concern, trending positive, or working as designed
- **Amber** — material concern, deteriorating, or contested but not acute
- **Red** — acute concern, deteriorating sharply, or actively impeding the user's likely decision

The caption is one analytic sentence — never just the color name. "Security: Red — two active conflicts, one re-escalating" is honest; "Security: Red — bad" is useless.

### Bottom line (2–3 sentences)

The single most important framing for this audience and this decision. The sentence the reader will quote in a meeting. It's a *judgment*, not a summary.

### Headline thesis (1–2 sentences, optional)

For longer briefs (15+ pages) or where the analytical situation is genuinely complex, open with a single italic-serif paragraph that captures the directional read in 1–2 sentences. The thesis should be comparative ("the widest of any major Sub-Saharan economy") and directional ("the gap is unlikely to close in the next 12 months"), not descriptive. It sits above the verdict strip and reads as the sentence a senior decision-maker would quote in a meeting.

```html
<div class="thesis">
Ethiopia's macroeconomic reform program is delivering and is now genuinely
competitive with regional peers — while security re-escalates, debt
restructuring stalls, and a contested June 2026 election approaches.
The range between the upside and downside scenarios is the widest of any
major Sub-Saharan economy.
</div>
```

Skip the thesis block for shorter briefs (under ~15 pages) — the verdict strip and bottom-line italic do the work in that range.

### Key judgments (4–7 bullets, each with arrow and optional confidence level)

Each bullet leads with a directional arrow, then a bold headline finding, then one anchor fact with a footnote. Optionally tag each judgment with a confidence level in italic — `*(high confidence)*`, `*(moderate confidence)*`, `*(low confidence)*` — to signal which judgments are most settled versus most provisional. No supporting prose — that's body content.

Trajectory arrows are required on every key judgment. Pick the one that's most defensible:

- **↑ Improving** — the dimension is trending more favorable; recent observable changes go in the right direction
- **→ Stable** — neither getting better nor worse on observable indicators; flat trajectory
- **↓ Deteriorating** — the dimension is trending less favorable; recent changes go in the wrong direction
- **⇅ Volatile / contested** — genuine bidirectional movement, factional dispute, or the analyst has insufficient signal to call direction confidently

⇅ is an honest out for situations that don't have a clean direction. Use it when the data genuinely supports it; don't use it as a default to avoid making a call.

4 judgments is the floor; 5–7 is appropriate for briefs over ~20 pages where multiple distinct issues need surfacing. More than 7 dilutes; if you need 8+, the brief's central tension probably isn't clear.

### Counterfactual block (optional, "what would invalidate these judgments")

For briefs where analytical rigor matters and judgments may be challenged, add a small block immediately after key judgments listing what specific event or threshold would invalidate each judgment. This:
- Surfaces the *reasoning* behind judgments rather than just the conclusions
- Signals analyst rigor to senior readers
- Gives the reader specific things to watch for that would change the analysis

```html
<div class="counterfactual">
<strong>What would invalidate these judgments.</strong>
<ul>
<li><em>Macro reform:</em> IMF Fifth Review (mid-2026) misses targets or program suspends.</li>
<li><em>Debt restructuring:</em> Eurobond deal closes before Q3 2026.</li>
<!-- one bullet per key judgment -->
</ul>
</div>
```

Use HTML directly (not markdown) so the structured format renders consistently.

### Risk matrix (3–5 risks plotted on a 2×2)

Critical risks are presented as a 2×2 Likelihood × Impact matrix, not a ranked list. The reader sees the *shape* of the risk landscape — clustered high-likelihood-high-impact risks signal a crisis brief; scattered risks signal a complex but not acute situation. The renderer supports up to 7 risks; 5 is the sweet spot for a 20-30 page brief.

For each critical risk, assign:
- **Likelihood:** low / medium / high (over the brief's time horizon, typically 6–12 months)
- **Impact:** low / medium / high (severity of consequences if the risk materializes)

Markers in the matrix appear as numbered dots; the key list below the matrix carries the full risk descriptions. This convention matches IMF Risk Assessment Matrix style.

When multiple risks share a likelihood/impact cell, the renderer automatically offsets the markers so they're individually visible.

### Recommendations (3–5, with owner and timeline)

Specific, actionable implications. Each must have an addressee, a specific action, and a time horizon. Use the format:

> **Action.** *Owner:* [who]. *By:* [when]. [Optional brief justification.]

For example:
> **Sequence new project commitments around the June 2026 election.** *Owner:* Investment Committee. *By:* defer Q3 2026 starts pending post-election review at Q4 2026 cycle.

The owner names a specific role or committee, not a vague "we" or "the team". The timeline gives a concrete operational date or cycle. "Engage thoughtfully" is not a recommendation; "Engage UAE-Ethiopia bilateral channel for project sequencing; Country Lead; quarterly" is.

### Known unknowns block (optional)

For briefs where analytical uncertainty is real and worth surfacing, close the exec summary with a "Known unknowns" block that lists the specific gaps in current analytical confidence. This:
- Signals analytical honesty
- Helps the reader calibrate how to weigh the brief's judgments
- Identifies specific questions that would change the analysis if answered

```html
<div class="known-unknowns">
<strong>Known unknowns.</strong> Honest gaps in current analytical confidence:
<ul>
<li><em>Post-election political legitimacy:</em> whether Prosperity accepts a managed but flawed process or pushes for a clean sweep.</li>
<!-- 3-5 honest gaps -->
</ul>
</div>
```

Use sparingly — typically 3-5 items. The known-unknowns block is not a license to dodge analytical commitment; it surfaces genuine uncertainty, not laziness.

### Markdown conventions for visual elements

The render script parses three fenced div conventions plus unicode arrows in key judgments:

**Verdict strip:**
```
::: verdict-strip
- Macro: green | Strong reform momentum, IMF-validated
- Security: red | Two active conflicts, one re-escalating
- Governance: amber | Reform institutions strong; rights/civic space deteriorating
- Debt: amber | Restructuring stalled with private creditors
:::
```

**Trajectory arrows on key judgments:**
```
- ↑ **Macroeconomic reform momentum is real and IMF-validated.** [anchor fact][^1]
- ↓ **Debt restructuring is unresolved and likely to slip past mid-2026.** [anchor fact][^2]
- ⇅ **Security is deteriorating in Amhara, fragile in Oromia, re-escalating in Tigray.** [anchor fact][^3]
- → **Humanitarian needs remain at scale against contracting funding.** [anchor fact][^4]
```

**Risk matrix:**
```
::: risk-matrix
- Renewed northern war | likelihood: medium | impact: high
- Electoral disruption | likelihood: high | impact: medium
- Eurobond restructuring failure | likelihood: medium | impact: medium
:::
```

The risk-matrix entries can use any of `low`, `medium`, `high` for both axes; the script positions them on the 2×2 accordingly.

## The country snapshot: structure and discipline

The snapshot sits at the top of section 1 of the body and serves a specific function — it's the shared factual baseline every reader needs before any analytic claim in the body sections makes sense. It is *not* a data dump or a "country facts" list. It is a structured reference card optimized for fast scanning by readers who already understand what the indicators mean.

### Structure: 2×2 grid of sub-blocks

The snapshot box uses a 2×2 grid of four thematic sub-blocks:

```
┌──────────────────────┬──────────────────────┐
│ PEOPLE               │ POLITICS             │
│  - Population        │  - Government type   │
│  - Demographics      │  - Head of state     │
│  - HDI               │  - Head of govt      │
│                      │  - Ruling party      │
├──────────────────────┼──────────────────────┤
│ ECONOMY              │ STABILITY            │
│  - GDP nominal       │  - WGI Gov Eff       │
│  - GDP per capita    │  - INFORM Risk       │
│  - Real growth ↑/→/↓ │  - Fragility (FSI)   │
│  - Inflation ↑/→/↓   │  - IMF program       │
│  - Debt/GDP ↑/→/↓    │  - Active sanctions  │
└──────────────────────┴──────────────────────┘
Last reviewed: [Month YYYY]
Sources: [single line, alphabetical]
```

Each block holds 3–6 indicators. Pick indicators by what matters most for the brief's angle, not by what's available — a humanitarian brief will weight Stability heavier and Economy lighter; a market-entry brief will reverse that. The aim is roughly equal visual weight across the four blocks, which generally means 4 indicators per block.

### Trend arrows: only on direction-sensitive indicators

Trend arrows (↑ improving / → stable / ↓ deteriorating) appear only on indicators where direction is meaningful and the analyst has a defensible call. Apply them to:

- **Economy block:** real GDP growth, inflation, debt/GDP, current account balance, FX reserves
- **Stability block:** WGI dimensions if multi-year change is observable, INFORM Risk, fragility scores

Do NOT apply arrows to:
- Static counts (population, head of state, ruling party seat counts)
- Categorical labels (government type, IMF program name)
- Single-point indicators where direction has no meaning (e.g., a one-time HDI rank)

The discipline matches the exec summary's trajectory arrows: don't add an arrow unless you can defend the directional call from the data. When in doubt, leave it off.

### "Last reviewed" date

Place a `Last reviewed: [Month YYYY]` line below the grid and above the source line. This is the date the analyst confirmed the snapshot's indicator values, not the cover date — it tells a reader returning to the brief six months later whether the figures may have stale. Even a 1–2 month gap behind the cover date can matter for fast-moving indicators (FX reserves, conflict event counts, sanctions listings).

### Single source line

Cite the snapshot's sources in a single line at the bottom of the box rather than footnoting individual indicators. The source line is alphabetized by institution and lists publication vintages:

`Sources: IMF WEO October 2025; IMF Article IV Fourth Review January 2026; UNDP HDR 2024; World Bank WGI 2024 release; INFORM Risk Index 2025.`

This is the institutional convention (EIU, S&P, World Bank country pages all do it). It keeps the box visually clean — every indicator looks the same, nothing has a superscript number pulling the eye. If a specific indicator is contested or unusual, that detail belongs in the body section, not in the snapshot.

Footnotes elsewhere in the brief work as before (numbered Chicago style); the source line is a snapshot-specific convention.

### Markdown convention for the snapshot

```
::: snapshot
### People
- Population: ~112 million
- HDI: 0.498 (lower deciles globally)

### Politics
- Government type: Federal parliamentary republic
- Head of state: President Taye Atske Selassie
- Head of government: PM Abiy Ahmed (since April 2018)
- Ruling party: Prosperity Party (410/547 seats, June 2021)

### Economy
- GDP (nominal): ~$170 billion (FY25/26)
- GDP per capita: ~$1,500
- Real GDP growth: 9.2% ↑
- Inflation: 12.0% ↓
- Public debt / GDP: ~45% ↓

### Stability
- WGI Government Effectiveness: ~25th percentile (2024)
- INFORM Risk Index: Very High
- IMF program: ECF $3.4B (July 2024); 4th Review Jan 2026
- Active conflicts: 3+ (Amhara, Oromia, Tigray)

Last reviewed: May 2026
Sources: IMF WEO October 2025; IMF Article IV Fourth Review January 2026; UNDP HDR 2024; World Bank WGI 2024 release; INFORM Risk Index 2025.
:::
```

Trend arrows can be `↑`, `→`, or `↓`, placed at the end of the value with a single space.

## The political context section: visual elements

The Political Context section (body section 2) is the longest narrative section in the first half of the brief because politics drives most other dimensions. To help senior readers absorb the political picture without reading every paragraph, the faction box visual element supports the prose: a small box listing 2–4 main political factions and their key positions on the brief's dimensions of interest.

The faction box is *optional* — use it when the country has coalition politics, contested elite alliances, or factional dynamics inside the ruling apparatus. Skip for personalist regimes where factions aren't analytically meaningful.

### Visual element: Faction box

A compact list of 2–4 political factions or coalitions with their key positions. Use for countries with coalition politics, contested elite alliances, or factional dynamics inside the ruling apparatus. Skip for personalist regimes where factions aren't analytically meaningful.

**Markdown convention:**

```
::: faction-box
- Prosperity Party leadership | Ruling | Pro-reform on economy; centralizing on security
- Tigray (TPLF factions) | Opposition / extra-system | Internally split; western Tigray claim drives confrontation
- Amhara (Fano militias) | Insurgent | Fragmented; resists federal disarmament; no single political vehicle
- Oromo (OLA + Oromo Federalist Congress) | Mixed | OLA partial peace; OFC marginalized in formal politics
:::
```

Each line is `Faction name | Position | Key stance`. Keep stances under ~15 words. The default header is "Key Factions"; override with an optional `title:` line.

**Position vocabulary (extended for de facto power-holders).** Beyond the civilian-political categories (`ruling`, `opposition`, `insurgent`, `mixed`), the renderer accepts two additional positions for countries where formal authority and operational power diverge:

- `military` (also `armed forces`, `praetorian`) — for cases where the armed forces operate as an independent political-economic actor, not just an institution under civilian control. Use for Pakistan, Egypt, Algeria, Myanmar, Sudan, pre-2011 Tunisia, Thailand during military-government periods.
- `religious-authority` (also `religious authority`, `clerical`) — for theocratic or semi-theocratic systems where clerical bodies hold independent decision-making power that constrains or supersedes civilian government. Use for Iran (Supreme Leader + Assembly of Experts), and (with judgment) for cases where religious establishments hold substantive political authority.

The selection of categories carries analytical weight: tagging Pakistan's Army as `military` rather than `ruling` or `mixed` is itself a substantive claim about the country's power structure, and the visual treatment (olive/khaki background, distinct from civilian-party colors) signals this to the reader.

**Worked example: military-primacy state.**

```
::: faction-box
title: Key political actors (Pakistan, hypothetical example)

- Pakistan Army (Chief: General Asim Munir) | Military | Controls foreign and security policy; substantial economic-sector presence via DHA, Fauji Foundation; the binding constraint on civilian government
- PML-N government (PM Shehbaz Sharif) | Ruling | Formal authority over economy, social policy; constrained on foreign and security policy
- PTI (Imran Khan, imprisoned) | Opposition | Popular mandate but excluded from formal politics; mobilization capacity limited by detentions
- Religious-political parties (JUI-F, Jamaat-e-Islami) | Mixed | Provincial strongholds; coalition leverage on specific policy domains
:::
```

The military gets its own row, its own visual category, and an explicit framing as "the binding constraint" — making the analytical claim visible rather than burying it in prose.

**Worked example: religious-authority state.**

```
::: faction-box
title: Key political actors (Iran, hypothetical example)

- Supreme Leader (Ayatollah Khamenei) + Assembly of Experts | Religious-authority | Apex authority on foreign policy, nuclear, security, judiciary appointments
- IRGC (Major General Hossein Salami) | Military | Independent military, intelligence, and economic actor; commands Quds Force for regional operations
- Elected presidency (Masoud Pezeshkian) | Ruling | Constrained executive; controls cabinet and domestic economic management within Supreme Leader's parameters
- Reformist civilian opposition | Opposition | Periodically organized; subject to disqualification cycles by Guardian Council
:::
```

For Iran, both `religious-authority` and `military` categories appear — reflecting the analytical reality that the Supreme Leader is the apex but the IRGC is an independent power center, not merely an institution under his control.

**Companion leader-cards.** When Section 2 has a faction-box reflecting de facto power-holders, the leader-cards in the same section should include those actors visibly, not only the constitutional figureheads:

```
::: leader-cards
title: De facto power-holders (Pakistan, hypothetical example)

- General Asim Munir | Chief of Army Staff | Pakistan Army (de facto foreign and security policy authority) |
- Shehbaz Sharif | Prime Minister | PML-N (formal head of government) |
- Asif Ali Zardari | President | PPP (largely ceremonial under the 18th Amendment) |
:::
```

The selection signals the analysis: putting the Army Chief first, naming his role explicitly as "de facto foreign and security policy authority," tells a portfolio reader exactly who they need to understand to make decisions about Pakistan. A brief that only showed the President and Prime Minister would be analytically incomplete in a way that the faction-box tagging system makes harder to miss.

**Variant: Severity box for sub-national conflict assessment.** The same component renders sub-national conflict severity (Section 4) under the name `severity-box`. Same row structure (`Zone | Severity | One-line driver`), but the position field accepts severity categories: `severe` (red), `high` (amber), `medium` (yellow), `contained` (light green), `stable` (green). The default header is "Sub-National Severity"; override with `title:`.

```
::: severity-box
title: Sub-National Conflict Severity (May 2026)
- Amhara | Escalating | ENDF–Fano clashes intensifying; drone strikes; humanitarian access severely restricted.
- Tigray | Re-escalating | TDF western Tigray operation Jan 2026; Eritrean forces present.
- Oromia (Wollega + Arsi) | High | OLA insurgency chronic.
- Sidama, southern regions, Dire Dawa, Harari | Contained | Comparatively stable.
- Addis Ababa | Stable | Federal capital; secured corridor.
:::
```

The renderer also accepts trend-style category labels (`escalating`, `re-escalating`, `chronic`, `deteriorating`) and maps them to the appropriate severity color automatically.

## Home-country bilateral relations (section 1.5)

Country briefs are always read from a specific institutional perspective, not a neutral global vantage point. A UAE-based portfolio analyst reads Ethiopia very differently from a London-based analyst. Section 1.5 makes that perspective explicit by including a structured bilateral-relations section between the country snapshot and the political context.

### When this section is included

The section is generated whenever the `--home-country` flag is set to a country name. The flag defaults to `UAE`, so any brief produced without explicit override gets a UAE bilateral section. Pass `--home-country none` to suppress the section entirely (useful when producing a generic brief for a non-aligned audience).

The flag also informs Claude's research process: when set, Claude searches for bilateral data between the home country and the target country, not just country-internal data.

### Structure of the section

The section opens with a 4-tile **bilateral-stats strip** showing headline numbers at a glance, then proceeds through six subsections in fixed order:

1. **Diplomatic relationship overview** — when relations were established, current ambassador, embassy presence, level of representation. Cover in prose, with a markdown bullet list for the most decision-relevant figures (name, title, brief context).

2. **Senior visits and engagements** — recent high-level visits in both directions over 18–24 months. Cover in prose with a tight bullet list of dates, principals, and themes.

3. **Treaties and formal agreements** — bilateral investment treaties (BITs), double taxation agreements (DTAs), sector MoUs, defense cooperation if applicable, currency swap arrangements. Render as a markdown table.

4. **Home-country investment in target country** — major projects with sectors, scale, dates; sovereign wealth fund involvement (ADQ, Mubadala, IHC, ADIA, DP World, AD Ports for UAE); private-sector flagship deals.

5. **Target country's presence in home country** — diaspora population and concentration, remittance flows, commercial activity, target country's government investments in the home country.

6. **Aid and development cooperation** — humanitarian and development financing, OCHA Financial Tracking Service data, project portfolio, multilateral channels.

### The bilateral-stats strip — what goes in the 4 tiles

The 4-tile strip at the top of the bilateral relations section is a `stats-strip` component (formerly named `bilateral-stats`; both names still work). It's a generic component reused across many sections — see "Reusable visual components" below for the full reference. This subsection just covers the bilateral-specific picks.

Pick the 4 headline numbers that most concisely describe the bilateral relationship. Typical picks for UAE briefs:

- **Two-way trade volume** (latest annual, with year and source)
- **FDI stock** (cumulative home-country investment in target)
- **Diaspora population** (target nationals in home country)
- **Aid disbursed** (cumulative or recent annual)

For some country pairs the data won't support 4 strong tiles — e.g., a country with minimal UAE diaspora or no significant investment. Don't pad with weak numbers. Either drop weak tiles (the strip handles 1–4 tiles) or substitute alternative metrics that are stronger for this pair: defense cooperation rank, energy import share, remittances, sector-specific exposure, etc. Better 3 strong tiles than 4 padded ones.

### Research priorities

When data quality varies, prioritize in this order: **visits and engagements** (most current-events relevant) → **investment in target country** (most portfolio-actionable) → **aid cooperation** → **diplomatic overview** → **treaties** → **target country in home country**.

If a subsection has fewer than two material data points after honest research, drop it rather than padding. Better a tight 4-subsection section than a padded 6-subsection one.

### Source catalog for UAE bilateral relations

When `--home-country UAE`, prioritize these sources for the section's content:

- **UAE Ministry of Foreign Affairs and International Cooperation (MoFAIC)** — press releases, official statements
- **WAM (Emirates News Agency)** — official UAE news flow
- **UAE Embassy in [target country]** website — current ambassador, recent activity
- **Khaleej Times, The National, Gulf News** — UAE-side coverage
- **Target country government sources** — foreign ministry press, head-of-state office
- **Mubadala, ADQ, IHC, ADIA, DP World, AD Ports** — annual reports and major announcements for UAE sovereign and quasi-sovereign investments
- **OCHA Financial Tracking Service (FTS)** — humanitarian funding data, structured and downloadable
- **UN Comtrade** — trade flow data
- **World Bank Migration & Remittances data** — diaspora and remittance flows
- **Reuters, FT, Bloomberg** — third-party verification of major deals

For other home countries, swap to that country's official channels and analogous sources.

### Honest data and confidentiality rules

Three constraints on what the section contains:

1. **Publicly verifiable only.** Don't speculate about confidential cooperation (defense, intelligence, financial flows not in public disclosure). If the brief needs to mention sensitive cooperation, do so in narrative terms with a clear "publicly reported" or "press accounts indicate" framing.

2. **Date everything.** Bilateral data changes faster than country-internal data — relationships warm and cool, deals are announced and renegotiated, visits happen monthly. Include an explicit "Information current as of [Month YYYY]" line below the bilateral-stats strip.

3. **Note what's not in scope.** If defense cooperation or specific deal terms are excluded for confidentiality, say so explicitly in a single sentence rather than implying full coverage.

### Markdown convention

```
## 1.5. Bilateral Relations: [Home Country]

::: stats-strip
- $1.5B | Two-way trade (2024) | UAE Stats Centre
- $4.2B | UAE FDI stock | Mubadala / ADQ disclosures
- 250K | Diaspora in UAE | Embassy estimate
- $310M | UAE aid disbursed (2020-25) | OCHA FTS
:::

*Information current as of [Month YYYY].*

**Diplomatic relationship.** [narrative — name the current ambassador, embassy date, level of representation]

**Senior visits and engagements.** [narrative with bullet list of dates and principals]

- 2024-05: PM visit to UAE — investment focus
- 2024-09: UAE FM to [capital] — strategic dialogue
- 2025-02: Joint Investment Committee
- 2026-04: President-level summit (upcoming)

**Treaties and agreements.** [narrative + markdown table]

| Agreement | Signed | Status |
|-----------|--------|--------|
| Bilateral Investment Treaty | 2022 | In force |
| Double Taxation Agreement | 2023 | In force |
| MoU on aviation | 2024 | In force |

**UAE investment in [target country].** [narrative]

**[Target country] in the UAE.** [narrative]

**Aid and development cooperation.** [narrative, optionally with a small table]
```

### Implementation notes

- The stats strip component renders 1–4 tiles. If fewer than 4 are provided, the strip layout still works; do not pad to fill space. (The component is called `stats-strip`; `bilateral-stats` is kept as an alias.)
- The treaties table is plain markdown; the standard table renderer handles it.
- If `--home-country none` is passed, the entire section is omitted; subsequent section numbers do not shift.

## Reusable visual components (used across multiple sections)

Several components are not tied to a single section — they were designed for one section and then reused wherever they served the analysis. Knowing which components are reusable and where they fit prevents inventing new components when an existing one would do.

### Stats strip (`stats-strip`)

A 4-tile horizontal strip showing headline numbers. Used at the top of:

- **Section 1.5 (Bilateral Relations)** — 4 bilateral headline numbers (trade, FDI stock, diaspora, aid)
- **Section 4 (Security & Stability)** — 4 conflict headline numbers (active conflicts, IDPs, fatalities, occupation)
- **Section 6 (Social & Human Development)** — 4 human development indicators (HDI, out-of-school children, youth share, hunger index)
- **Section 8 (Humanitarian Severity)** — 4 humanitarian headline numbers (PIN, IDPs, funding tracked, INFORM Risk Index)
- **Section 9 (Macro Stress / Debt)** — 4 debt headline numbers (PPG external, commercial, relief required, debt/GDP)

```
::: stats-strip
- Value | Label | Optional source
- 18.9M | People in need (2025) | OCHA HNO
- 3.3M | IDPs nationally | IOM DTM May 2024
- $311M | Funding tracked Jan–Jun 2025 | OCHA FTS
- Very High | INFORM Risk Index | 2025 release
:::
```

The component is also addressable as `::: bilateral-stats` for backwards compatibility with existing briefs.

**Discipline for choosing the 4 tiles:**

1. Each tile must carry a number the reader would otherwise have to dig out of the prose.
2. Each tile must have a defensible source. If you can't cite where it came from, drop it.
3. Don't pad to 4 if only 3 strong tiles are available. The strip handles 1–4 cleanly.
4. The labels are read fast — keep them under ~30 characters.

### Leader-cards (`leader-cards`) — political power-holders AND bilateral counterparts

This is the *single component that covers two distinct use cases*. Knowing which to deploy when is a recurring quality discipline:

- **Section 1.5 (Bilateral Relations)** — use leader-cards as the *bilateral-counterparts* view: **exactly the two heads of mission** (the home-country ambassador in the target country, and the target country's ambassador in the home country). No more, no less. The validator emits warnings at both ends — fewer than 2 (incomplete) and more than 2 (bloated). Ministerial bilateral leads, special envoys, and Joint Commission chairs belong in the visits-and-engagements timeline by name, not as additional leader-cards in Section 1.5.

- **Section 2 (Political Context)** — use leader-cards as the *named power-holders* view: **3–5 figures** conveying the real power configuration. Head of state, prime minister or successor figure, key faction or opposition leader, plus 1–2 others as the political situation demands. **Pair the leader-cards with the `::: faction-box`** that maps the broader power-center taxonomy — the faction-box names the categories of power, the leader-cards put faces on the individuals who actually hold it. **Wartime and political-transition briefs especially need both**: when civilian and military authority diverge (Iran's Mojtaba Khamenei / IRGC's Ahmad Vahidi pattern), the faction-box explains the divergence and the leader-cards show the specific people.

- **Section 7 / module-slot use** — only when a development-project module names specific signing principals or lead negotiators (rare; usually inappropriate).

When the brief features named power-holders in faction-box but does NOT add the parallel leader-cards block, that's a structural failure even if every other discipline is met. Faces alongside the taxonomy is what makes the political read concrete for the analyst-reader.

See the full leader-cards reference further down in this document (zero-config cascade, honorific stripping, bundled-photo lookup, auto-cache to bundled directory) for the rendering side. The composition discipline is summarized above; the rendering machinery is downstream.

### Scenario boxes (`scenario`)

Boxed callout that highlights a single labeled paragraph. Used for:

- **Section 7 (Development Project Environment)** — three lessons-learned patterns (Working / Mixed / Stalled)
- **Section 9 (Macro Stress)** — three stress scenarios (Base / Stalled / Adverse)
- **Section 11 (Outlook)** — three outlook scenarios (Base / Upside / Downside)

```
::: scenario
<span class="scenario-label">Base case</span> Continued reform momentum; managed but flawed election; debt restructuring concludes late 2026; northern conflict active but contained.
:::
```

The `<span class="scenario-label">` carries the label (usually 1–2 words). The text after the closing `</span>` is the scenario description. Keep each box to one paragraph.

Use scenario boxes when the analysis has multiple parallel outcomes or patterns. Don't use them as decorative callouts for single ideas — that dilutes the visual vocabulary.

### Indicator tables (markdown tables with embedded trend arrows)

Standard markdown tables where one column contains a trend arrow (↑ → ↓ ⇅). The renderer automatically wraps the arrows in colored spans (green ↑, red ↓, blue →, amber ⇅) and centers the trend column. Used for:

- **Section 3 (Economic Conditions)** — macro indicators table with current value, prior period, and trend
- **Section 5 (Governance & Rule of Law)** — WGI scorecard with rating and 5-year trend
- **Section 10 (Comparative Benchmarking)** — cross-country comparison (no trends, just side-by-side values)

```
| Indicator | Current | Prior period | Trend |
|-----------|---------|--------------|-------|
| **Real GDP growth** | 9.2% (FY25/26 proj.) | 6.1% (FY24/25 est.) | ↑ |
| **Headline inflation** | 12.0% (end-FY25/26 proj.) | 28.7% (end-2024) | ↓ |
```

**Discipline:**

1. The trend arrow direction follows the *indicator's analytical meaning*, not the numeric direction. For inflation, debt, FX premium, etc., where smaller is better, a ↓ means improving. For growth, reserves, etc., where larger is better, ↑ means improving. Add a clarifying italic line under the table when this is ambiguous.
2. Bold the indicator name in the first column for scannability.
3. 6–8 rows is a good ceiling. Beyond that the table becomes a wall of data that the reader skims.

### Charts (`chart`)

Inline static charts rendered server-side via matplotlib and embedded as PNG. Four chart types are supported: `line`, `bar`, `stacked-bar`, and `scatter`. Charts use the brief's navy-led palette (navy primary, amber/red/green/indigo/purple for additional series) and minimal chartjunk — no top/right spines, light dotted gridlines on the y-axis only, serif chart titles consistent with section headings.

**Chart selection happens upfront, not reactively.** Before drafting Section 3 (Economic Conditions) and Section 4 (Security & Stability) — and before drafting any module section that the chart-recipe registry suggests (Section 8 humanitarian, 13 diaspora, 14 sanctions, 18 comparative) — open `validation.py::_CHART_RECIPES` and pick the 2-3 recipes whose trigger matches the brief's analytical thesis. **Write the section prose around those charts**, not the charts around the prose. Adding charts at the end to satisfy chart-count warnings produces visually weaker charts because they're decorative rather than analytically anchored.

The recipes are decision-relevance prompts — country-specific data the analyst already has surfaces naturally when the recipe is identified upfront. A wartime brief on a sanctioned oil producer should anchor Section 3 around the `fx-trajectory` + `oil-exports-trajectory` recipes; a brief with a high-diaspora country should anchor Section 13 around `remittances-trajectory`; a brief with active conflict data should anchor Section 4 around `conflict-events-trajectory`. The validator catches the absence of these — but the better discipline is to identify them before drafting, not after.

**Single-series line chart:**

```
::: chart
type: line
title: FX reserves trajectory (months of import cover)
x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025
y: Reserves | 0.8 | 1.0 | 0.9 | 1.2 | 2.8 | 3.4
y-label: Months
source: NBE; IMF Article IV (January 2026)
:::
```

**Multi-series line chart** (each `y:` line is a separate series):

```
::: chart
type: line
title: GDP growth and inflation (2020-26)
x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 proj
y: GDP growth (%) | -4.6 | 3.5 | -7.3 | -2.3 | 5.0 | 5.0 | 4.5
y: Inflation (%, avg) | 4.6 | 6.0 | 46.4 | 17.4 | 1.2 | 2.0 | 5.4
y-label: Percent (annual)
source: CBSL; IMF EFF Reviews
:::
```

**Single-series bar chart:**

```
::: chart
type: bar
title: War costs by party — May 2026 estimates ($B)
x: Iran (low est.) | Iran (high est.) | Arab states | US war cost
y: USD billion | 300 | 1000 | 120 | 29
y-label: USD billion
source: Iranian state media; Reuters; US Pentagon Comptroller (May 12, 2026)
:::
```

**ANTI-PATTERN — does NOT work:**

```
::: chart
title: Example
type: line
data:
  - {year: 2020, value: 130000, label: "JCPOA withdrawal"}
  - {year: 2025, value: 929000, label: ""}
yaxis: IRR per USD (free market)
:::
```

The renderer silently produces an empty chart container for the above because it expects pipe-delimited `x:` and `y:` lines, NOT a YAML `data:` array. If your chart renders empty, the syntax is the first thing to check. Use only the documented pipe-delimited format above.

**Syntax**:
- `type:` — one of `line`, `bar`, `stacked-bar`, `scatter`. Required.
- `title:` — chart title shown above. Optional but strongly recommended.
- `x:` — x-axis labels separated by `|`. Required for line/bar/stacked-bar.
- `y:` — one or more series. Each line is one series. If the first `|`-separated value is non-numeric, it becomes the series name; otherwise the line is a single unnamed series of values.
- `points:` — for scatter only: `label | x | y` (one point per line).
- `x-label:` / `y-label:` — axis titles. Optional.
- `source:` — italic source caption below the chart. Optional but strongly recommended for analytical credibility.
- `show-values:` — `true` (default) or `false`. Applies only to `bar` and `stacked-bar`. Default behavior draws a value label above each bar (the total at top of stack for `stacked-bar`). Set to `false` for charts with many small bars where labels would crowd, or for charts where the pattern matters more than precise values (e.g., a wide distribution).

**Value labels on bar charts.** Default-on for `bar` and `stacked-bar` because most analytical bar charts in country briefs serve as comparison tools where specific values are citeable insights — readers want to know "$1.3B from US vs $300M from EU" without estimating from the y-axis. Labels are formatted intelligently (integers if all values are whole; one decimal otherwise; thousands separators for values ≥1000) and positioned just above each bar with 8% headroom added to the y-axis. Skip via `show-values: false` only when the bar count is high (>15) or the pattern matters more than precision.

**When to use each chart type:**

| Chart type | Use when... | Example from Ethiopia brief |
|------------|-------------|------------------------------|
| `line` | Time-series trajectory with 4+ points | FX reserves over 2020–2025; DSA debt trajectories |
| `bar` | Cross-entity comparison (countries, sectors) at a point in time | G20 CF time-to-completion across cases |
| `stacked-bar` | Composition over time (each bar sums to a meaningful whole) | Sectoral GDP composition |
| `scatter` | Position on two correlated dimensions | Climate vulnerability vs. readiness |

**Discipline:**

1. **Every chart needs a source.** Without it, a senior reader can't assess credibility. Charts without sources read as opinion.
2. **Don't render decoration.** A chart is justified when it shows something prose can't — trajectory, range, divergence, composition. If the chart restates a single number, skip it and use a stats-strip tile instead.
3. **3-8 charts per brief, 4-6 typical.** The floor of 3 ensures every substantive brief has charts distributed across spine sections (macro trajectory in Section 3, security or humanitarian count in Section 4/8, comparative or sector-specific elsewhere). The soft ceiling of 8 reflects that beyond this count charts start competing for reader attention rather than supporting decisions. Audit each chart against the "shows something prose can't" test; if a chart restates a single number, replace it with a stats-strip tile.
4. **Keep chart titles directional.** "FX reserves trajectory" tells the reader what to look for; "FX reserves over time" doesn't.
5. **Prefer 5–10 data points on x-axis for line charts.** Fewer than 5 doesn't show trajectory; more than 10 crowds the labels.
6. **Charts render at print resolution (PNG at 200 DPI)** and embed as base64-encoded data URIs. This is robust through WeasyPrint and avoids the SVG-rendering pitfalls that plague matplotlib SVG output.

### Maps (`map`)

Inline choropleth maps of a country's sub-national admin-1 regions, with neighboring countries rendered as light-grey context. Maps share styling conventions with charts (centered, source caption, page-break-inside avoidance) and use the same categorical palette as the severity-box for consistency.

```
::: map
type: choropleth
title: Sub-national conflict severity (May 2026)
country: Ethiopia
region: Amhara | escalating
region: Tigray | re-escalating
region: Oromia | high
region: Somali | high
region: Addis Ababa | stable
color-scale: severity
show-neighbors: true
source: ACLED; ECHO; analyst assessment
:::
```

**Syntax:**
- `type:` — `choropleth` (default, region-colored by category) or `reference` (uniform muted fill, no legend, for orientation only). Required.
- `title:` — chart title above the map. Optional but strongly recommended.
- `country:` — country name as it appears in Natural Earth's `admin` field (e.g., "Ethiopia", "Kenya", "United States of America"). Required.
- `region:` — one line per region: `name | category`. Required for `choropleth`; ignored in `reference` mode. The skill fuzzy-matches region names against Natural Earth's spelling (e.g., "Oromia" matches NE's "Oromiya").
- `color-scale:` — one of `severity` (red/orange/yellow/green spectrum), `electoral` (green/yellow/red), `verdict` (green/amber/red). Defaults to severity. Ignored in `reference` mode.
- `show-neighbors:` — `true` (default) or `false`. When true, neighboring countries appear in light grey for spatial context.
- `source:` — italic caption below the map.

**Two map modes:**

*Choropleth* (analytical) — admin-1 regions colored by category. Use in Section 4 (security) or Section 11 (election cycle) when sub-national variation is the analytical story. Generates a categorical legend bottom-left.

*Reference* (orientation only) — admin-1 regions filled with a uniform muted navy tint, boundaries drawn in navy, capital star overlaid, neighbors labeled. No legend. Use in the country snapshot of shorter briefs (under ~15 pages) that don't trigger thematic Section 4 or Section 11 maps — these briefs would otherwise have no map at all, leaving the reader without spatial orientation. Skip the reference map when the brief already contains one or more thematic maps; it would be visually redundant.

**Reference map: density limitations.** Reference maps produce visually clean output for countries with up to roughly 20 first-level administrative divisions. For countries with 30+ provinces (Iran's 31 provinces motivated this note; Russia, China, India would have similar issues), expect that the most densely-packed regions will have labels placed close to or slightly overlapping other labels. As of May 2026, the renderer suppresses leader lines for reference maps (the alternative would be a crosshatch of lines crossing the country, which actively impairs readability). The trade-off: some labels are slightly displaced from their actual region; readers identify regions primarily through map position and surrounding context rather than precise label-to-region matching. For countries where province-level identification is analytically critical, use `type: choropleth` instead — choropleth maps retain leader-line behavior because the colors are data-bearing and must be unambiguously associated with their regions.

```
::: map
type: reference
title: Country reference
country: Botswana
source: Natural Earth admin-1 boundaries
:::
```

**Color-scale categories:**
- `severity`: severe / escalating / re-escalating (red), high / deteriorating (orange), medium / moderate / chronic (yellow), contained (light green), stable / secure (green)
- `electoral`: green / yellow / amber / red / delayed
- `verdict`: green / amber / red

**Capital city marker:** Maps automatically overlay a navy filled-star at the country's national capital, sourced from a bundled extract of Natural Earth populated places (`assets/geo/capitals.parquet`, ~18 KB, covers 215 sovereign states). The capital's admin-1 label is offset below the star to avoid visual collision. No user action required — the marker appears automatically for any country whose name matches Natural Earth's `ADM0NAME` field.

**Data and limitations:**
- Boundaries come from Natural Earth 10m admin-1 (sub-national) and 50m admin-0 (countries), bundled in `assets/geo/` as GeoParquet (~16MB total).
- The skill ships with one curated boundary file — Natural Earth public domain data. If a country's most recent admin division isn't reflected (e.g., Ethiopia's Sidama region split from SNNPR in 2020), the legacy boundary applies and the map source caption should disclose this.
- Region-name aliases (`assets/geo/region-aliases`, or inline in `render_brief.py`) handle common spelling differences; add new aliases when a fresh country surfaces a mismatch.

**Discipline:**

1. **One map per brief is the typical maximum.** Maps are the most expensive visual to read — every map demands the reader trace polygons. Two maps in a 20-page brief is the upper limit; more than two becomes noise.
2. **Maps go where sub-national variation is the analytical story.** Section 4 (Security) and Section 11 (Election Cycle) are the natural candidates for most country briefs; other sections rarely benefit.
3. **Always disclose boundary vintage** when the country has had recent administrative reorganization. The Ethiopia brief notes "Pre-2020 admin boundaries; Sidama and South West Ethiopia appear within legacy SNNPR" in the source line.
4. **Maps render at PNG 200 DPI** like charts, via the same matplotlib pipeline.

### Decision-implication callouts (`decision-implication`)

Tinted-background callout box at the end of every section that gives the senior reader an explicit "so what for the portfolio" statement. The callout uses navy left-border and a small-caps "DECISION IMPLICATION" header, matching the IMF Article IV "Box" pattern. The visual treatment makes the callout scannable across pages: a reader who flips through the brief reading only the implication blocks gets the entire portfolio takeaway.

```
::: decision-implication
Ethiopia is a structurally high-growth, high-complexity market: 112 million
people (Africa's second-largest), a state-led reform program in execution,
but with low absolute development indicators (HDI 0.498) and active
sub-national conflict. For UAE portfolio decisions, this positioning calls
for development-stage assumptions on absolute indicators paired with
market-stage assumptions on reform trajectory.
:::
```

**Where to place:**
- **Every spine section (1–6)** should end with one decision-implication block. This is the most-disciplined version of the skill.
- **Every optional module** that fires should end with one. The body content explains the dimension; the callout explains what the dimension means for the portfolio.
- **Comparative Benchmarking (Section 18)** ends with one capturing the comparative-position implication.

**Discipline:**

1. **Lead with the directional read.** First sentence: what does this section mean for the portfolio? Not what's *in* the section — what does it *imply*.
2. **Name the specific decision lever.** "Position-sizing", "sequencing", "due-diligence depth", "operational structuring" — not "consideration" or "factors". The reader should leave with a concrete handle.
3. **Calibrate to the brief's angle.** A portfolio brief's callouts should reference portfolio decisions; a development-program brief's callouts should reference program design; a deal-level brief's callouts should reference deal-structure choices.
4. **2–5 sentences.** Long enough to land the implication, short enough to scan.
5. **No new evidence.** The callout synthesizes the section; if you find yourself introducing new data points, that data belongs in the body, not the callout.

### When to use which component

A quick decision tree:

- **4 headline numbers a reader should see at a glance** → stats strip
- **Sequence of dated events** → bullet list with dates inline (the dedicated timeline component was deprecated; prose bullets cover the same need)
- **2–4 named figures with notes** → bullet list or markdown table (the dedicated actor-cards component was deprecated; lists cover the same need without photo-fetch complexity)
- **2–4 named factions with positions** → faction-box
- **2–6 zones/regions with severity ratings** → severity-box
- **Multiple parallel outcomes with labels** → scenario boxes
- **Indicator-by-indicator comparison with trends** → indicator table
- **Trajectory over time** → line chart
- **Cross-entity comparison** → bar chart
- **Composition over time** → stacked-bar chart
- **Two-dimensional positioning** → scatter chart
- **Sub-national variation by category** → choropleth map (`type: choropleth`)
- **Spatial orientation in a short brief without thematic maps** → reference map (`type: reference`)
- **"So what for the portfolio" at section close** → decision-implication callout

Don't invent new components when one of these will do. The visual vocabulary should stay small enough that a reader recognizes each pattern.

## Writing discipline: how the brief should read

Most country briefs fail not on what they include but on how they're written. The fixes below are the difference between a brief that gets read and one that gets skimmed and shelved.

### Lead with the judgment

Each section, and ideally each paragraph, should open with the analytical finding — not background. Background and evidence follow the judgment, not the other way around. This is the Bottom Line Up Front discipline, borrowed from intelligence writing. The reason: senior readers skim, and they should be able to harvest the brief's argument by reading first sentences alone.

Bad opener: *"Country X has held elections every five years since 1995. The most recent was in 2024…"*

Good opener: *"Country X's political system remains procedurally stable but increasingly captured by the ruling party; recent elections, while regular, no longer offer meaningful competition."*

### Calibrated narrative language (no probability terms)

The user's preference is narrative analysis — no ICD 203 likelihood scale, no "almost certain / very likely / unlikely" tags. This means hedging is done through language, not vocabulary lists. The discipline matters because narrative analysis can drift in two bad directions: mushy ("some observers note…", "there are reports that…") or overconfident ("the regime will collapse," "elections will deliver change").

Calibrated hedging looks like:
- *"Evidence points to…"* — strong, but not certain
- *"Trends suggest…"* — directional finding from multiple indicators
- *"On current trajectory…"* — conditional projection
- *"Remains uncertain…"* — acknowledged unknown
- *"Disputed among observers…"* — flag of analytic disagreement
- *"Without further information, the most defensible reading is…"* — when forced to call it

Avoid: *"some say,"* *"it has been argued,"* *"reportedly"* without a source, *"experts believe,"* and any hedge that hides the analyst behind an unnamed crowd. If the analyst is uncertain, say so plainly.

Also avoid the opposite trap: do not state forecasts as inevitabilities. A six-month political projection is a judgment under uncertainty, not a fact.

### Topic sentences carry analytic weight

Each paragraph should begin with a sentence that, on its own, conveys an analytic finding. The rest of the paragraph supports it. If a topic sentence is purely descriptive ("Country X borders three states…"), the paragraph is description, not analysis, and probably belongs in the snapshot or an appendix.

### Specificity beats abstraction

"Significant inflation" is weaker than "inflation reached 38% YoY in March 2026, the highest since 1995." Specific numbers, dates, and named actors make briefs credible; vague qualifiers make them feel like the analyst didn't do the work.

### Sub-national variation is almost always present

Treating a country as monolithic ("Country X is stable / unstable / growing") is one of the most common failure modes. Most countries have meaningful variation across regions, urban/rural, ethnic, or sectoral lines. Wherever the data supports it, name the variation explicitly. This is especially important for security, economic performance, and humanitarian conditions.

### Watch for these failure modes

- **Mirror imaging** — assuming actors in the target country reason the way the analyst does. Cultural and political logic often differs sharply.
- **Stale anchors** — leaning on facts that were true 5 years ago but no longer are. Check dates on every claim.
- **Single-source dependency** — one think tank or one news outlet doing all the lifting. Triangulate across institutional, news, and local sources.
- **False precision** — turning a range estimate into a point estimate, or assigning a 73% to something you actually just feel is "likely."
- **Conclusion-first-then-evidence trap** — settling on a view and only including supporting evidence. Force yourself to surface the strongest counter-evidence.
- **Recency bias** — overweighting the past month's headlines against a longer trajectory.
- **Missing actor analysis** — describing what happened without naming who decided it and why.

`references/failure-modes.md` has expanded examples and how to dodge each one.

### Distribute visual investment evenly across the brief

A common failure mode is to invest heavily in visuals for the first few sections (exec summary, snapshot, political context) and then let the back half become a wall of prose. A senior reader who flips past the front half then sees a different document — one that signals "the analyst ran out of energy."

Counter this by checking: does every spine section have at least one visual element? The components above cover most cases:

- **Sections that benefit from a stats strip:** any section with 3–4 quantitative headline numbers worth surfacing
- **Sections that benefit from an indicator table:** any section that walks through 5–8 metrics
- **Sections that benefit from scenario boxes:** any section with multiple parallel patterns, scenarios, or lessons
- **Sections that benefit from severity grids:** any section with sub-national variation worth surfacing

The goal isn't visual decoration. It's reader scannability — a reader should be able to flip through the brief and pick up the major signals from the visuals alone, then dig into prose for the sections that matter to them.

### Avoid forced page breaks

The renderer handles page flow automatically. Resist the temptation to insert `---PAGE---` markers between sections "for cleanliness" — they usually create orphan paragraphs and large whitespace gaps when the preceding section doesn't fill the page. Section headings already create their own visual break through styling (navy underline). Let content flow naturally; the renderer is better at avoiding orphans than the analyst is at predicting them.

The one good use of a forced page break is between the executive summary and Section 1 — but this is now handled automatically by the renderer's CSS, so you don't need to mark it manually.

## Frameworks (use one, not several stacked)

Pick a single organizing framework for the analysis and stick with it. Stacking PESTLE on top of a country-risk taxonomy on top of fragility lenses produces a brief that feels like a checklist rather than a piece of analysis.

- **PESTLE** (Political, Economic, Social, Technological, Legal, Environmental) — good for market entry and business expansion. Comprehensive but generic.
- **Country risk taxonomy** (political, economic, legal, tax, operational, security — the S&P / EIU lineage) — good for investment, portfolio, and operating-environment briefs.
- **Fragility lens** (Fund for Peace clusters: cohesion, economic, political, social, cross-cutting) — good for development and humanitarian work in challenging contexts.
- **Pure narrative** — for political risk and strategic briefs where the analyst's argument carries the structure. Use the spine above without a labeled framework.

The spine above already covers the same ground; the framework choice mostly shapes terminology and emphasis. Don't bolt a framework onto the spine — pick one or the other.

## Comparative-country module

Always include comparative benchmarking unless the user explicitly excludes it. Comparison is what makes country data interpretable — saying "GDP per capita is $3,400" means little until the reader knows whether that's high or low for the relevant peer group.

Choose 2–4 comparators based on context:
- **Regional peers** (e.g., for Kenya: Tanzania, Uganda, Ethiopia)
- **Income-group peers** (low-income, lower-middle, upper-middle, high-income)
- **Analytically chosen** (e.g., for a post-conflict country, compare with other post-conflict transitions)
- **Aspirational benchmark** (the country the host wants to emulate)

Present comparisons in a compact table, then 2–3 paragraphs of interpretation. Don't just list the numbers — explain what the gaps and convergences mean.

Recommended comparison indicators (pick 6–10 relevant to the brief's angle): GDP per capita, real GDP growth, inflation, government debt/GDP, current account/GDP, HDI rank, WGI Government Effectiveness, WGI Control of Corruption, CPI score, Doing Business successor metrics, INFORM Risk index, fragility score.

## Citations: Chicago notes-and-bibliography

Use numbered footnotes throughout, with a full bibliography at the end. This is the default expectation for serious country-level analysis and matches the conventions of most institutional briefs.

Key rules:
- Footnote any claim that isn't general knowledge — every statistic, every direct attribution, every contested judgment.
- Cite the most authoritative available source. World Bank > news aggregator. IMF Article IV > investment bank note.
- Cite the date of the data, not the date you accessed it (e.g., "World Bank, World Development Indicators, 2024 update").
- For news, prefer the original outlet over an aggregator.
- Avoid sources that aren't traceable ("a senior official told the analyst") unless explicitly using primary research.
- In the bibliography, alphabetize by author/institution; group by type only if the bibliography exceeds ~30 entries.

**Bibliography auto-numbering.** The renderer wraps the contents of any `## Bibliography` section in a single numbered `<ol>` regardless of how the analyst writes the entries — paragraphs, a tight numbered list, a numbered list with blank lines between entries, or a mix. The post-pass in `pipeline.py::_normalize_bibliography` collects every paragraph and list-item child of the `<div class="bibliography metadata-block">` element and emits one `<ol class="bibliography-list">` with sequential numbering. Analysts should not have to worry about list-formatting conventions; just write entries one per logical line and the renderer normalizes.

**Shared `metadata-block` typography for end-matter sections.** Three sections at the end of every brief — Notes (auto-generated footnotes), Methodological back-matter (vintage + confidence + source-quality + AI-provenance), and Bibliography — share a single visual register defined by a `.metadata-block` CSS class in `brief-template.html`. All three render at 9pt with 1.35 line-height in muted text color, signaling "this is metadata, not analytical argument." Each section extends the shared class with its specific layout: Notes uses an `<ol>` with numbered hanging indent; Bibliography uses an `<ol class="bibliography-list">` with hanging indent; Methodological back-matter uses flowing paragraphs. Implementation: `pipeline.py` wraps `## Bibliography` in `<div class="bibliography metadata-block">` and `## Methodological back-matter` (or `## Methodology`) in `<div class="methodological metadata-block">`; `render_footnotes_section` already emits `<div class="footnotes metadata-block">`. The H2 inside each wrapper is re-sized to 12pt (down from body H2 ~14pt) for proportional balance with the smaller body text.

Example footnote (Chicago notes-and-bibliography, full form on first citation, short form thereafter):

```
First citation:
1. World Bank, "Worldwide Governance Indicators: Country Data Report for Ethiopia," 2024
   release, https://www.worldbank.org/en/publication/worldwide-governance-indicators.

Subsequent citation:
12. World Bank, "WGI: Ethiopia," 2024.
```

## Data sources (the trusted catalog)

`references/data-sources.md` has the full catalog organized by domain. The short version of what to use where:

- **Macroeconomic** — IMF World Economic Outlook, IMF Article IV, World Bank Country Economic Memorandum, World Bank WDI
- **Governance** — Worldwide Governance Indicators (WGI), V-Dem, Bertelsmann Transformation Index (BTI), Freedom House
- **Corruption** — Transparency International CPI, Control of Corruption (WGI)
- **Fragility** — Fragile States Index (Fund for Peace), CPIA (World Bank), OECD States of Fragility
- **Conflict** — ACLED, UCDP, Crisis Group, ICG CrisisWatch
- **Humanitarian** — INFORM Risk index, IPC food security phases, OCHA Humanitarian Needs Overview, UNHCR data
- **Development** — UNDP HDI, World Bank country pages, OECD DAC for donor flows
- **Business environment** — successor metrics to the Doing Business Index (B-READY), WEF Global Competitiveness, MIGA political risk
- **Sanctions** — OFAC (US), EU Council sanctions, UN Security Council sanctions
- **Climate** — ND-GAIN country index, World Bank Climate Change Knowledge Portal

Read `references/data-sources.md` before drafting — picking the right source per claim is what separates a credible brief from one that looks credible.

## Optional risk scoring (use sparingly)

Numeric risk scoring is optional and should be used only when (a) the user requests it, (b) the brief compares multiple countries, or (c) the deliverable is for a portfolio process that requires scoring. When you do score, follow these rules to avoid false precision:

- Use a 1–5 scale (not 1–10 or 1–100 — extra granularity is fake granularity).
- Define each level explicitly ("3 = moderate risk: observable challenges, no current operational impact").
- Score across no more than 6–8 dimensions. More than that, and readers can't hold the picture.
- Always pair the score with a one-sentence narrative justification — never let a number stand alone.
- If rendering a heatmap for the PDF, use color sparingly (red/amber/green only) and ensure print-readability in grayscale.

For default briefs (no scoring), do narrative risk discussion with clearly named drivers — that's more useful for most decisions and avoids false confidence.

## Rendering to PDF

Country briefs are delivered as styled, print-ready PDFs.

1. Write the full brief in markdown first. This makes it easy to revise and to track the structure.
2. Read `assets/brief-template.html` to understand the print styling (typography, footnote handling, page breaks, margins).
3. Use `scripts/render_brief.py` to convert markdown → styled HTML → PDF. The script handles Chicago footnote rendering, page-break hints, and a clean cover page.
4. Save the final PDF to `/mnt/user-data/outputs/` and call `present_files` to share it.

**Cover-page metadata flags.** The render script accepts `--audience`, `--angle`, `--author`, and `--subtitle` flags, but only pass these when the user has explicitly supplied them. The cover should display the country name and date by default — nothing else. Adding fabricated defaults like "Prepared for: Internal" or "Angle: General" makes the cover look templated and worse than leaving them off. If the user names a specific audience ("for our board"), an explicit angle ("for the Q3 portfolio review"), or an author/unit, pass those values; otherwise omit the flags entirely and the script will hide those rows.

**Table of contents (`--toc`).** Pass `--toc` to insert a clickable contents page between the cover and the executive summary. The TOC lists every top-level section (numbered sections plus Executive Summary and Bibliography), auto-fills page numbers via WeasyPrint's `target-counter` mechanism, and renders entries as PDF internal hyperlinks — clicking an entry in Acrobat, Preview, Chrome, or any standard PDF viewer jumps directly to that section. The flag is opt-in (default off) because short briefs don't benefit from it. Recommended threshold: include a TOC for any brief longer than ~15 pages or with more than ~10 top-level sections. The skill exercises only top-level sections (h2 headings); sub-sections are not included by design, since the TOC's purpose is fast navigation rather than full document outline.

**AI-provenance disclaimer.** Every cover page renders an AI-provenance disclaimer at the bottom by default. The default wording discloses (1) AI generation, (2) public-source basis, (3) non-attribution to any producing organization, and (4) a reader-verification instruction. This is responsible disclosure for AI-generated analytical content and protects both the reader (who can calibrate trust appropriately) and the producing organization (which is not bound to the AI's specific judgments). Two override flags exist:

- `--no-disclaimer` — suppresses the disclaimer entirely. Use only when a human has substantially edited or reviewed the output to the point that the AI-generated framing no longer applies. Misusing this flag undermines reader trust.
- `--disclaimer-text "..."` — replaces the default wording with custom text (e.g., for an organization's specific legal disclaimer language). The custom text receives the same italic, muted styling as the default.

The default disclaimer is appropriate for most briefs and should not be overridden without reason.

**Country flag.** Every cover renders the country's national flag below the title by default. The renderer auto-resolves the flag by looking up the country's ISO 3166-1 alpha-2 code from the bundled Natural Earth admin0 data, then loading the matching PNG from `assets/flags/`. The bundle covers ~270 sovereign states using flags from the lipis/flag-icons open-source dataset (MIT licensed), converted from SVG to PNG at 600px width for reliable WeasyPrint rendering. The flag renders at 5cm wide with a thin white border (handles flags with dark or navy elements that would otherwise bleed into the cover background). Two override flags:

- `--no-flag` — suppresses the flag entirely. Use for thematic briefs that aren't country-specific (regional analyses, comparative studies).
- `--flag-path /path/to/custom.png` — substitutes a custom flag image. Useful for sub-national entities, regional unions (e.g., African Union, ASEAN), or historical flags. Path is resolved relative to the working directory.

**Important note on flag rendering.** WeasyPrint silently fails on complex SVG features (clipPath, gradients, intricate transforms) — many national flag SVGs use these. The skill bundles PNGs rather than SVGs to ensure reliable rendering. If extending the flag bundle for new entities, pre-rasterize SVGs to PNG (e.g., via `cairosvg.svg2png(output_width=600)`) rather than embedding raw SVG.

Read those two files before drafting if you haven't recently — small details (footnote placement, page breaks at section boundaries) make the difference between a brief that prints cleanly and one that doesn't.

## Final-pass quality checklist

Before delivering, do a fresh-eyes pass against these checks. If any answer is "no," fix before delivering.

- Does the executive summary stand alone? A reader who only reads page 1 should walk away with the bottom line, key judgments, risks, and recommendations.
- Does every paragraph open with an analytic finding, not background?
- Is every statistic dated and sourced? Anything older than 3 years flagged?
- Is hedging calibrated — not mushy, not overconfident?
- Is sub-national variation surfaced wherever the data supports it?
- Are at least 3 different categories of sources used (multilateral data, news, primary documents)?
- Are recommendations specific and actionable, not generic ("the country should reform governance")?
- Does the bibliography render cleanly with no broken cross-references to footnotes?
- Does the PDF print cleanly — no orphan headers, footnotes on the right pages, no overflowing tables?

## When in doubt

If the request is partially specified, default to the development/political-risk angle, the standard spine above, and the trusted data source catalog. It's easier for the user to redirect from a competent first draft than to fill in the blanks from a list of questions.

## Deferred enhancements (planned work)

These are agreed-upon features that aren't yet implemented because of external blockers. They are recorded here so a future iteration of this skill, or a future Claude, knows the intent.

### Sub-national reference map in the country snapshot

**Status:** **shipped** as the `::: map` choropleth component. Natural Earth 10m admin-1 + 50m admin-0 boundaries are bundled under `assets/geo/` as GeoParquet (~16MB). The render script uses GeoPandas + matplotlib to produce choropleth maps for any country and admin-1 categorization. Region-name aliases handle common spelling differences between Natural Earth and analyst usage.

**Original design:** A reference map below the 2×2 indicator grid in the snapshot box. This original design wasn't built; instead the implemented version is a more flexible thematic-overlay map used in Section 4 (security severity) and Section 11 (electoral). The reference-map use case can be added later by extending `render_map` with a `style: reference` parameter that suppresses categorical coloring.

**Implementation choices made:**
- Path B (generate at render time from bundled boundary data) — implemented.
- Color scales currently: `severity`, `electoral`, `verdict`. Add new scales by extending `_MAP_COLOR_SCALES` in `render_brief.py`.
- Region name aliases are inline in `_REGION_ALIASES` — extend when a new country surfaces a mismatch.

**Known limitation:** Natural Earth's admin-1 polygons reflect pre-2020 partitions for Ethiopia and several other countries. Recently-created regions (e.g., Sidama, South West Ethiopia, South Ethiopia) appear within their legacy parent polygons. Maps should disclose boundary vintage in the source caption when relevant.

**Known limitation (surfaced by the Sri Lanka country test):** Natural Earth's admin-1 data quality varies dramatically by country. Most countries get English-language names at analytically useful administrative levels (provinces, governorates, states). But for Sri Lanka, Natural Earth provides DISTRICT-level data (25 districts) rather than the analytically more useful PROVINCE-level (9 provinces), AND the names are in Sinhalese transliteration ("Kŏḷamba" not "Colombo", "Yāpanaya" not "Jaffna"). The `_REGION_DISPLAY_OVERRIDES` mechanism in `country_brief/maps.py` solves the language issue (displaying English names on the map) but does NOT solve the aggregation issue (the map still shows 25 districts rather than 9 provinces). A future enhancement would build a country-keyed `_ADMIN1_AGGREGATIONS` dict that maps district names to province names and does runtime dissolution in GeoPandas. For Sri Lanka specifically the aggregation table is straightforward (Northern Province = Jaffna + Kilinochchi + Mannar + Mullaitivu + Vavuniya; Eastern Province = Trincomalee + Batticaloa + Ampara; etc.). Until this is implemented, country briefs for Sri Lanka should rely on prose (not choropleth) for sub-national analysis when province-level granularity matters.

**Future enhancement opportunities:**
- Add a `--no-map` CLI flag to skip map rendering when speed matters.
- Support additional point overlays (e.g., named secondary cities, conflict event clusters) on top of choropleth or reference fill — the capital marker is the first such overlay; the same pattern can be extended.
- Higher-resolution custom boundary data for countries where 10m Natural Earth is insufficient (e.g., island states, micro-territories).
- Province-level aggregation dict for Sri Lanka (described above) and any other country where Natural Earth's admin-1 granularity doesn't match the analytical conventional level.

---

### Source-language coverage and English-bias acknowledgment

**Status:** documented as a known limitation; no code-level mitigation planned.

**The issue (surfaced by the Sri Lanka and Morocco country tests):** The skill's source priority hierarchy (`references/data-sources.md`) leans heavily on English-language sources — IMF, World Bank, OECD, OCHA, ICG, BTI, Reuters, Crisis Group, ORF, etc. For most countries this is fine: the IMF and World Bank publish in English, and English-language commentary aggregates significant local-language reporting. For countries where the most decision-relevant analysis is in another language (French and Arabic for Morocco, Sinhala and Tamil for Sri Lanka, Spanish for Latin America, Bahasa for Indonesia), the skill's default workflow systematically under-uses local-language sources.

**Why this matters:** Local-language political reporting often captures dynamics that English-language sources miss or simplify. For Sri Lanka, the most analytically rich political-context reporting on the NPP government's internal dynamics is in Sinhala and Tamil. For Morocco, French-language reporting (Le Matin, L'Économiste, TelQuel) and Arabic-language reporting (Hespress) provide texture that English-language sources lack.

**What the analyst should do:** When producing a brief on a country where significant analytical sources are not in English, explicitly:
1. Note in the "Sources and vintage" paragraph that the brief leans on English-accessible sources and that some local-language commentary may not be reflected.
2. Search local-language sources (or use a translation workflow) when the brief is high-stakes.
3. Cite local-language sources by name when used, with translation in parentheses, so a future reader can verify.

**What the skill won't do automatically:** Switch to a non-English search workflow. The decision to engage local-language sources is the analyst's, and the cost-benefit depends on stakes. Documenting the gap honestly is more valuable than pretending the skill solves it.

---

### Effort estimates by brief type

**Status:** documented as guidance for analyst calibration; no code-level mitigation.

**The issue (surfaced by the Sri Lanka country test):** Different brief contexts require dramatically different effort. The skill has been silent on this, which makes effort estimation hard for analysts new to country briefing.

**Calibration based on the five country briefs produced during skill development:**

| Brief type | Typical effort | What drives it |
|------------|---------------|----------------|
| Follow-up brief on country analyst knows well | ~1.5–2 hours | Updates to existing knowledge; current sources only |
| New brief on a country with strong English-source coverage | ~3 hours | Substantial source research before writing |
| New brief on a country with significant non-English sources | ~4–5 hours | Source research + language navigation |
| Crisis-context brief (rapidly evolving situation) | ~3–4 hours | Need to verify each fact against most recent sources |
| Comprehensive commercial-context brief (many modules) | ~4–6 hours | Each module requires its own source research |

These are realistic estimates for AI-assisted production with appropriate web search; a human analyst writing the same brief without AI assistance would typically need 3-5x longer. The estimates assume the analyst has done their own due diligence on key facts before submitting the draft, not that they are accepting AI-generated content blindly.

**For high-stakes briefs:** double these estimates and incorporate a separate fact-verification pass against primary sources before delivery. Country briefs that inform portfolio decisions worth >$10M should not be produced in a single sitting; the cost of a wrong analytical takeaway dwarfs the cost of the additional verification.

---

## Country brief production: realistic limits

The skill produces briefs that look polished. The polish should not be confused with comprehensive analysis. Specifically:

1. **Single-author depth limit.** A country brief produced by a single Claude instance reflects available open-source intelligence and the analyst's domain knowledge. For specialized sections (security analysis, technical regulatory matters, sectoral deep-dives) a brief is no substitute for a co-author with field expertise.

2. **Recency boundary.** The skill produces briefs current to the date of search. Events the analyst doesn't know about don't appear in the brief; the brief should never be treated as comprehensive of recent events.

3. **Analytical-vs-descriptive risk.** The most common quality failure across the five tested briefs is sections that look analytically rigorous but are actually descriptive. `references/section-quality.md` codifies the test (could this paragraph be deleted with no analytical loss? if yes, it's description). Use it.

4. **The "this is AI-generated" honesty.** The cover page disclaimer ("This brief is AI-generated using publicly available sources. Judgments and analytical framings reflect the AI system's synthesis, not the views of any producing organization or its employees. Readers should verify specific claims against the cited sources before relying on them for decisions.") exists for a reason. It is not boilerplate. Readers should genuinely verify, especially for high-stakes claims.

---

## Syntax reference: component cheat sheet

This section is the canonical reference for the exact markdown syntax of every fenced-div component. The skill's renderer accepts pipe (`|`) as the separator across all component data lines; snapshot also accepts colon (`:`) for historical compatibility, but pipe is recommended for new content.

### Snapshot

```
::: snapshot
### People
- Population | ~112 million
- HDI | 0.498 (lower deciles)
- Demographics | ~70% under age 29
- Refugees hosted | >1 million

### Politics
- Government | Federal parliamentary republic
- ...

### Economy
- ...

### Stability
- ...
:::
```

Notes:
- Up to 4 `###` sub-blocks (People / Politics / Economy / Stability is the convention).
- Bullet items use `Key | Value` (preferred) or `Key: Value`.
- Trend arrows (↑ → ↓ ⇅) at the end of values get auto-colored.

### Stats strip / bilateral stats

```
::: stats-strip
- 3 | Active armed conflicts | ACLED / ECHO
- 3.3M | IDPs (May 2024) | IOM DTM
- 430+ | Drone-strike fatalities, Amhara | Since Oct 2024
- 40% | Tigray under non-federal occupation | Regional admin estimate
:::
```

Each line: `<bold number> | <label> | <source caption>` (3 pipe-separated parts).

### Verdict strip (exec summary)

```
::: verdict-strip
- Macro: green | Strong reform momentum, IMF-validated
- Security: red | Two active conflicts; Tigray re-escalating
- Governance: amber | Reform institutions strong; civic space deteriorating
- Debt: amber | OCC deal closed; Eurobond restructuring stalled
:::
```

Each line: `<Label>: <color> | <caption>`. Color is one of `green | amber | red`. Up to 4 cells.

### Risk matrix

```
::: risk-matrix
- Renewed northern war | likelihood: medium | impact: high
- Electoral disruption | likelihood: high | impact: medium
- Famine deepening | likelihood: very high | impact: critical
:::
```

Each line: `<label> | likelihood: X | impact: Y`. Both X and Y accept `low | medium | high | very high | critical`. Extended values (`very high`, `critical`) annotate the key list but render in the high-corner cell.

### Severity box / faction box

```
::: severity-box
title: Sub-National Conflict Severity (May 2026)
- Amhara | escalating | ENDF–Fano clashes intensifying; access restricted.
- Tigray | re-escalating | TDF western Tigray operation Jan 2026.
- Oromia | high | OLA insurgency chronic.
- Addis Ababa | stable | Federal capital; secured corridor.
:::
```

Severity categories: `severe | escalating | re-escalating | high | deteriorating | medium | moderate | chronic | contained | stable | secure`. Color-coded by tier.

### Scenario boxes (outlook section)

```
::: scenario
<span class="scenario-label">Base case (probability ~55%)</span> Narrative...
:::
```

The `scenario-label` span carries the label; the rest is narrative prose. Inline markdown (`**bold**`, `*italic*`) works inside scenario blocks.

### Delta summary (what's changed since prior brief)

Useful for repeat readers maintaining country watch lists. Goes near the top of the brief (after Bottom Line, before Key Judgments) when applicable — not in every brief, only when a prior brief exists for comparison.

```
::: delta-summary
title: Changes since prior brief (May 2026)
- ↓ Coalition stability: Both Deputy PMs resigned after FICAC charges
- → Macro: IMF Article IV maintained 2.5% growth projection
- ↑ Security: Vuvale Union signed with Australia (May 8, 2026)
- → Climate finance: UAE bilateral engagement continues at pace
:::
```

Each row: `arrow | category: description`. Arrow options: `↑` (improving), `↓` (deteriorating), `→` (stable), `⇅` (contested/mixed). Arrow color-codes the row. Category is bolded as a clickable mental anchor; description is the substance.

When to use: any time a brief is being produced as an update to a prior brief on the same country. The delta-summary tells repeat readers which sections most warrant re-reading. When to skip: standalone briefs with no prior version, or first-time briefs on a country.

### Scoring summary (quantitative decision-relevance dimensions)

A bridge between the brief's qualitative prose and quantitative portfolio decision models. Goes near the top of the brief (after Key Judgments, before Section 1) when applicable, or near Section 18 (Comparative) for portfolio-decision-heavy briefs.

```
::: scoring-summary
title: Portfolio decision-relevance scoring (May 2026)
- Macro stability | 55 | → | Tourism deceleration; fiscal pressure; debt 80% GDP
- Political risk | 60 | ↓ | Coalition fraying; election uncertainty 2026-27
- Sanctions exposure | 95 | → | No sanctions; clean compliance profile
- Climate risk | 25 | ↓ | High vulnerability; 1.8% GDP annual SLR losses
- ESG framework | 70 | → | Strong climate institutional architecture
- Operational risk | 65 | → | Small market; labor shortages; capacity constraints
:::
```

Each row: `dimension | score 0-100 | trend arrow | one-line justification`. Score bars are colored by quartile (0-30 red, 30-60 amber, 60-80 olive, 80-100 green). Trend arrows match delta-summary conventions.

Score interpretation:
- **0-30:** unfavorable / high risk
- **30-60:** mixed / moderate
- **60-80:** favorable
- **80-100:** strongly favorable

When to use: any brief where the country is being evaluated for portfolio decisions and the reader benefits from a quantitative cross-dimensional view. Particularly useful for portfolios that aggregate country scores into a model. When to skip: humanitarian or development briefs where quantitative scoring would feel reductive.

Calibration discipline: the scores should reflect the brief's analytical content, not be invented. If the brief's prose argues "macro is stable but slowing," the macro stability score should be in the 50-65 range. If the prose argues "macro is in crisis," the score should be below 30. Inconsistency between the prose and the scoring table is the most common quality failure for this component.

### Charts

```
::: chart
type: line
title: FX reserves trajectory (months of import cover)
x: 2020 | 2021 | 2022 | 2023 | 2024 | 2025
y: Reserves | 0.8 | 1.0 | 0.9 | 1.2 | 2.8 | 3.4
y-label: Months
source: NBE; IMF Article IV (January 2026)
:::
```

Required: `type:` (one of `line | bar | stacked-bar | scatter`), `x:` (axis labels pipe-separated), `y:` (one or more series, each line is a series with optional name prefix).

Optional: `title:`, `x-label:`, `y-label:`, `source:`, `show-values:` (true/false for bar charts).

### Maps

```
::: map
type: choropleth
title: Sub-national conflict severity (May 2026)
country: Ethiopia
region: Amhara | escalating
region: Tigray | re-escalating
region: Oromia | high
region: Addis Ababa | stable
color-scale: severity
source: ACLED; ECHO.
:::
```

Required: `type:` (`choropleth` or `reference`) and `country:` (must match Natural Earth `admin` column).

For choropleth: one `region: <name> | <category>` line per region. Region names are normalized and aliased; the pre-render validator will fuzzy-match near-misses with a stderr note (e.g., "North Kordofan" → "North Kordufan") and warn loudly if a region can't be matched at all.

`color-scale:` is one of `severity | electoral | verdict`. Categories for each scale:
- `severity`: severe / escalating / high / medium / contained / stable
- `electoral`: red / amber / green / delayed
- `verdict`: red / amber / green

### Decision-implication callouts

```
::: decision-implication
For UAE-portfolio decisions, **the macro reform trajectory is real** but
*operational complexity* remains elevated...
:::
```

Plain narrative prose. Inline markdown (bold, italic) works. One callout at the end of each section is the convention.

### Other components

- `::: thesis` — italic serif block with amber left-border (exec summary headline thesis)
- `::: bottom-line` — italic prose paragraph (exec summary closer)
- `::: key-judgment` — for stand-alone judgments
- `::: counterfactual` — small amber-bordered "the case against"
- `::: exec-summary` — wraps the whole exec summary block
- `::: faction-box` — list of political/armed actors with descriptions (see `references/section-library.md`)

---

## Pre-render validation

Every brief render now runs a pre-render validation pass that emits warnings (to stderr) for common errors:

1. **Footnote references without definitions** — `[^foo]` used in body but no `[^foo]: citation` defined
2. **Unused footnote definitions** — definition exists but no body reference (usually safe to delete)
3. **Typo'd fenced-div class names** — suggests the closest valid component (e.g., `verditc-strip` → `verdict-strip`)
4. **Empty fenced-div blocks** — open/close markers with no content between
5. **Map blocks missing `country:` parameter**
6. **Spine sections missing** — sections 1-6 and 19 should always be present
7. **Malformed component lines** — stats-strip / verdict-strip / risk-matrix / severity-box / faction-box lines that don't parse cleanly
8. **Section-aware leader-card count bounds** — both floors and a Section-1.5 upper bound:
   - **Section 1.5 (bilateral): exactly 2 cards** — the UAE ambassador to the country, and the country's ambassador to the UAE. The validator warns at both ends: <2 (incomplete) and >2 (bloated). Ministerial leads, NSAs, special envoys, and Joint Commission chairs belong *in the visits-and-engagements timeline by name*, or as full leader-cards in Section 2 if they are politically central to the country itself. Keeping Section 1.5 to exactly the two ambassadors makes every bilateral section visually consistent — readers know they're seeing the heads of mission.
   - **Section 2 (political context): minimum 3 cards** — head of state + at least two other figures conveying the de facto power configuration (PM, opposition lead, key faction leader, succession figure). Trim-for-aesthetics drops below this floor get caught.
   - **Other sections: minimum 2 cards** — a single-card block is almost always incomplete.

   The validator scans each leader-cards block, identifies its containing section by the closest preceding `## N.` heading, and warns when the row count falls outside the section-specific bounds.

9. **Under-mapped briefs with sub-national data** — SKILL.md calls for 1–2 maps per brief: a reference map for orientation plus a thematic choropleth where sub-national variation is the analytical story. The validator catches the case where the *data* is in the brief but the *map* is not:
   - A `::: severity-box` block is present (sub-national severity data) but no `::: map type: choropleth` block exists. The same regional categorization should be rendered as a map alongside the text severity box.
   - Section 11 (Election Cycle / Political Transition) is present but no choropleth map exists anywhere in the brief. Electoral briefs typically benefit from a province- or district-level results map.

   This catches the silent under-delivery against the spec — earlier briefs in the skill's reference set (Ethiopia, Sudan, Iran, Syria) shipped both reference and thematic choropleth maps; recent briefs were silently under-mapped because the validator only verified *some* map existed.

10. **Chart count bounds** — SKILL.md spec is **3-8 charts per brief, 4-6 typical**. The floor of 3 reflects what earlier production briefs (Ethiopia, Sudan, Syria, Iran v1) routinely shipped; the soft ceiling of 8 reflects that beyond that count charts start competing for reader attention. The validator emits an under-count warning when <3, and a soft-ceiling warning when >8 (framed as "audit each chart against the 'shows something prose can't' test"). Substantive briefs should have charts distributed across spine sections — FX/debt trajectory in Section 3, security events over time in Section 4, humanitarian population in Section 8, comparative benchmark in Section 18, etc. Consult the chart-recipe registry to identify decision-relevant additions.

11. **Missing dated chronologies in time-anchored sections (section-scoped)** — three sections are analytically time-anchored and should each carry their own dated chronology:
    - **Section 1.5 (Bilateral)** — visits-and-engagements timeline (which heads of state / ministers / ambassadors met when, what each visit produced)
    - **Section 4 (Security & Stability)** — conflict events, security incidents, ceasefire architecture
    - **Section 11 (Election Cycle)** — electoral cycle, political-transition events

    The deprecated `::: election-timeline` component was replaced by inline markdown tables (with a `| Date | Event |` header) or dense clusters of year-prefixed bullets (e.g., `- 2024-05: Election held`). The check is **section-scoped** — each section is inspected independently for content between its `## N.` heading and the next H2. A chronology in Section 4 does not satisfy the requirement for Section 11 or Section 1.5. Three or more year-prefixed bullets, or any markdown table with a Date / When column, satisfies the check within a section.

12. **Decision-relevant chart suggestions (recipe registry)** — `validation.py` ships a `_CHART_RECIPES` registry of ~12 chart "recipes," each with a trigger condition that detects when the chart is decision-relevant for the brief's country profile (e.g., `remittances-trajectory` fires when "remittance" appears; `energy-availability-factor` fires on "loadshedding" / "EAF"; `oil-exports-trajectory` fires on "shadow fleet" / "petroleum exports"; `conflict-events-trajectory` fires on "ACLED" / "ceasefire"). The validator detects which recipes fire and which already have matching charts in the brief, then emits a single aggregated warning listing the *missing* recipes. The analyst keeps full judgment over what to include — recipes are suggestions, not prescriptions — but the registry pushes briefs toward country-specific high-leverage charts instead of the same generic GDP-and-inflation chart on every brief.

   **Extending the registry.** Each recipe is a dict with `trigger` (keyword list and/or section presence), `section_hint` (where the chart usually goes), `title_keywords` (used to detect whether a matching chart is already present), and `template` (a ready-to-paste `::: chart` block stub). Adding a new recipe takes ~10 lines and benefits every future brief whose country fits the trigger.

   **What the registry doesn't do.** It doesn't fetch chart data. The analyst still web-searches for actual numbers, picks the right time range, and writes the `::: chart` body. The registry only points at which charts are decision-relevant given the country profile, with a starting template for each.

By default the validator does not block rendering — it surfaces issues for the analyst to fix. If a brief renders with warnings, the PDF is still produced, but the warnings indicate work needed.

The map renderer separately emits two kinds of region-matching notes:
- **Fuzzy-match notes** — when an analyst's region name doesn't exact-match but a close match exists (e.g., "Nort Darfur" → "North Darfur"). These auto-correct silently in the output but log to stderr.
- **No-match warnings** — when no plausible match exists; the region is skipped and stderr lists available regions for the country.

### Strict mode (`--strict`)

For production renders where an incomplete brief should refuse to ship rather than silently render without core analytical components, pass `--strict`. This promotes three structural warnings to render-blocking errors and the CLI exits non-zero without producing a PDF:

1. **Zero footnote references** in a substantive brief (>120 body lines) — every consequential claim should be source-attributed.
2. **No `::: risk-matrix` block** — the brief's tail-risk plot is a required component per SKILL.md.
3. **No Recommendations section** — every brief must close with portfolio-level recommendations carrying Owner and Timeline.

Other warnings (footnote density, bottom-line length, series-leakage phrases, decision-implication coverage per spine section, missing map or chart) remain *warnings* even under `--strict` — those checks involve judgment calls the analyst should make, not mechanical blocks. The promoted errors are prefixed with `[--strict]` in stderr so they're easy to spot.

**When to use:** CI pipelines, scheduled production renders, or any context where shipping a structurally-incomplete brief would be worse than shipping nothing.

**When to skip:** iterative drafting, where rendering an in-progress brief to inspect layout is useful even before all components are present.

The choice between warn-only (default) and `--strict` is the skill's stated answer to a recurring discipline failure: the SKILL.md structural-audit checklist exists because briefs have shipped without a map, chart, risk-matrix, or footnotes despite the spec calling for them. `--strict` is the automated counterpart to that manual checklist.

---

## Optional: declare module selection with a manifest

For briefs where explicit module declaration matters (consistency across a country series, formal review processes, or when a future analyst will pick up the brief), pass a YAML manifest file via `--manifest path.yml`. The manifest declares which modules fire and the validator cross-checks it against the markdown's actual section headers.

**Minimal manifest example:**

```yaml
country: Sudan
home_country: UAE
brief_type: crisis  # commercial | crisis | post-conflict | reform

modules:
  # Spine (sections 1-6, 19) — always true
  country_snapshot: true
  political_context: true
  economic_conditions: true
  security_stability: true
  governance_rule_of_law: true
  social_human_development: true
  outlook: true

  # Bilateral (section 1.5) — typically true for UAE briefs
  bilateral_relations: true

  # Optional modules — declare each as true | false | partial | stub
  development_project: false   # section 7
  humanitarian: true           # section 8
  macro_stress: partial        # section 9 — limited data
  climate: false               # section 10
  elections: false             # section 11
  civil_society_media: true    # section 12
  diaspora: true               # section 13
  sanctions: true              # section 14
  market_entry: false          # section 15
  regulatory: false            # section 16
  project_operating: false     # section 17
  comparative: true            # section 18
```

**Module values:**
- `true` — module fires fully; a corresponding section IS required in the markdown
- `false` — module is intentionally omitted; no corresponding section should appear
- `partial` — module fires partially (e.g., limited data); section present with limited coverage
- `stub` — section present but explicitly placeholder; the validator won't insist on substantive content

**What the validator catches:**
1. Typo'd module keys (with suggestions via `difflib`)
2. Declared `true` but section missing from markdown
3. Declared `false` but section IS present in markdown
4. Invalid state values (anything other than the four above)
5. Sections in markdown not declared in the manifest

**When to use a manifest:**
- A formal country-brief series where you want explicit declaration of module selection
- A brief that will be reviewed by another analyst — the manifest is a fast way to communicate "I deliberately omitted X, Y, Z"
- Briefs in a project where consistency across countries matters

**When NOT to bother:**
- Ad-hoc one-off briefs — the validator already covers the most important checks without a manifest
- Early-stage exploration where the module selection is still being decided

The manifest is **purely additive** — it never blocks rendering, only surfaces declared-vs-actual inconsistencies as warnings. See `tests/fixtures/manifest-example.yml` for the canonical schema.

---

## Changelog: Tier 2 hardening (May 2026)

### Smoke-test suite (`tests/run_smoke_tests.py`)
Nine regression tests covering the categories of bug that hit during the skill's development (snapshot parser silent failures, risk-matrix vocabulary, map region mismatches, capital-city ambiguity, label drops, broken function references, manifest validation). Runs in ~20 seconds after the renderer split (was ~55s monolithic). Test fixtures live in `tests/fixtures/` (`minimal.md`, `full-stress.md`, `broken.md`, `manifest-example.yml`, `manifest-broken.yml`). Run before committing any renderer change.

### Renderer split into a package
The 2,800-line monolithic `render_brief.py` was split into the `country_brief/` package with focused modules: `cli.py` (CLI entry, 269 lines), `pipeline.py` (orchestration, 238), `validation.py` (pre-render + manifest validation, 295), `inline.py` (markdown utilities, footnotes, anchors, 246), `toc.py` (TOC + cover, 99), `fenced_divs.py` (dispatcher + all ::: components, 586), `charts.py` (matplotlib chart rendering, 362), `maps.py` (geopandas rendering, 744). Each module is under 750 lines and has a focused responsibility. The original `render_brief.py` is now a 24-line shim that imports `main()` from the package for backward compatibility — existing invocations of `python scripts/render_brief.py ...` continue to work. New code should import from the package: `from country_brief import main, render_basic_markdown, validate_brief`.

### Manifest-driven module declaration (optional)
A brief can optionally be accompanied by a YAML manifest file (`--manifest path.yml`) declaring which modules fire. When provided, the validator cross-checks declared modules against the section headers actually present in the markdown and warns on inconsistency. Module values are: `true` (fires fully, section required), `false` (omitted, no section should appear), `partial` (fires with limited coverage), `stub` (placeholder content acceptable). The manifest catches four categories of mismatch: typo'd module keys (with `difflib`-based suggestions), declared-true-but-section-missing, declared-false-but-section-present, and unrecognized state values. See `tests/fixtures/manifest-example.yml` for the canonical schema and `_MANIFEST_MODULE_MAP` in `country_brief/validation.py` for the canonical module keys.

The manifest is **optional**. When omitted, the renderer simply uses whatever sections appear in the markdown — the existing workflow continues unchanged. Manifests add value when (a) the analyst wants explicit declaration of which modules apply for a given country context, (b) the brief is part of a series where consistency matters, or (c) a future "module library expansion" wants a structured way to declare new section types.

### Visual vocabulary cleanup
Removed three components that didn't generalize across four country tests (Ethiopia, Sudan, Syria, Morocco): `actor-cards`, `election-timeline`, `power-actors`. These were Ethiopia-specific and represented ~280 lines of renderer code + 163 lines of CSS + 207 lines of Wikipedia photo-fetch infrastructure. For dated event sequences (previously `election-timeline`), use bullet lists with dates inline. The validator now flags use of these deprecated names with warnings.

For political/armed actor listings, the primary replacement is `::: faction-box` (text-only, with party / role / stance).

### Leader-cards: photos for political leaders, bilateral counterparts, project principals

The `::: leader-cards` component renders a grid of named figures with photos (where resolvable) or stylized monogram placeholders (where not). It replaces the deprecated Ethiopia-specific `actor-cards` component.

**What the renderer actually does (May 2026).** Four photo-source resolvers are implemented, evaluated by prefix in this order, with a monogram fallback when all fail:

1. **`wiki:Page Title`** — English Wikipedia REST API summary lookup. Uses the page's canonical `originalimage.source` (or `thumbnail.source`) URL, which Wikipedia generates with the correct MD5-hash prefix so we don't have to. Works for any public figure with an English Wikipedia article in an environment that can reach `en.wikipedia.org`. The renderer sends an identifying User-Agent per Wikimedia's policy.
2. **`wiki-{lang}:Page Title`** — non-English Wikipedia lookup. Same mechanism, different language edition. Useful for Francophone African leaders (`wiki-fr:`), Arabophone figures (`wiki-ar:`), Lusophone (`wiki-pt:`), Hispanophone (`wiki-es:`), etc. The two-letter code after `wiki-` is the Wikipedia subdomain.
3. **`commons:Filename.jpg`** — Wikimedia Commons file lookup via `Special:FilePath`, which redirects to the canonical hashed Commons URL. Use when the figure has a Commons photo but no Wikipedia article.
4. **`http://...` / `https://...`** — direct URL fetch. Escape hatch for known-good URLs from government or organizational sites; fragile because such URLs change.
5. **Local file path** (anything else) — resolved against the working directory. Always works, requires the analyst to have the image on disk.
6. **Zero-config (blank `photo_source` field)** — the renderer tries an automatic cascade:
   1. **Honorific stripping** — before any lookup, the renderer strips leading honorifics (`Dr.`, `Sheikh`, `H.E.`, `H.R.H.`, `Hon.`, `Ambassador`, `Minister`, `Ayatollah`, `Sir`, `Lady`, `Prof.`, `Rev.`, military ranks, etc.) from the `name` field. The card still displays the original name; only the lookup query is normalized. This is essential for bilateral sections where titles like `Dr. Thani bin Ahmed Al Zeyoudi` are correct on the card but would 404 against the Wikipedia article (`Thani bin Ahmed Al Zeyoudi`). Stacked honorifics (`H.R.H. Sheikh Mohamed bin Zayed`) are iteratively stripped.
   2. **Bundled `assets/leaders/{slug}.{ext}`** — analyst-curated or auto-cached photo from the skill's leaders directory under a deterministic slug derived from the stripped name (lowercase, ASCII, hyphens; intra-token punctuation like apostrophes stripped). Examples: `azali-assoumani.jpg`, `nour-el-fath-azali.jpg`, `mohamed-bin-zayed.jpg`. Once a file exists at the slug, the photo works for every future brief that names the figure — no markdown changes, no network access required. This is the official-source path that gives proper coverage to ambassadors and mid-tier officials who have no Wikipedia article.
   3. **English Wikipedia** — `en.wikipedia.org` REST API lookup of the stripped name as a page title.
   4. **French Wikipedia** — `fr.wikipedia.org`, same mechanism. Catches Francophone African leaders.
   5. **Arabic Wikipedia** — `ar.wikipedia.org`, same mechanism. Catches Arabophone-region figures.
   First success wins; all-miss falls through to the monogram placeholder.

**Auto-cache to bundled directory.** Whenever ANY of the cascade tiers (explicit URL, Wikipedia, etc.) successfully resolves a photo, the renderer writes the image bytes into `assets/leaders/{slug}.{ext}` if no file already exists at that slug. The next brief that names the same figure hits the bundled directory in tier 2 and resolves locally without any network access. This means the analyst's one-time effort to find an official-source URL (UAE MoFA news article, WAM photo, government press release) compounds: every future brief gets the photo for free, and Wikipedia-resolved photos also persist so the skill becomes increasingly offline-capable as briefs are produced. Analyst-curated photos always win — if a file exists at the slug, the auto-cache is a no-op and the curated photo is used.

**Where official-source photos actually live (UAE-specific reality check).** The UAE MoFA "About the Ambassador" mission pages (`mofa.gov.ae/en/Missions/{City}/The-Embassy/About-the-Ambassador`) carry the ambassador's name and biography but **do not host portrait photos** as of May 2026. Where UAE MoFA photos do appear is in the news/credentials-presentation pages (e.g., `mofa.gov.ae/-/media/Feature/News/{date}-uae-{country}.jpg`), but those URLs are event-specific. For UAE ambassadors with no Wikipedia coverage, the practical workflow is: find a single news/press URL with the portrait once, paste it as `photo_source` in the markdown, and the auto-cache makes it permanent. Other foreign ministries vary; expect each country's MoFA to be different.

If all of the above fail (no source provided and no Wikipedia article matches; or network is restricted; or the response isn't an image), the card renders a deterministic-color monogram with the leader's initials (lowercase name-particles like "bin", "al", "de", "van" skipped).

Successful fetches are cached both in-process and on disk at `$XDG_CACHE_HOME/country-brief/photos/` (Linux/macOS, falls back to `~/.cache/country-brief/photos/`; on Windows resolves under the user profile, e.g. `C:\Users\<name>\.cache\country-brief\photos\`), keyed by SHA-1 of the canonical URL.

**Behavior in sandboxed environments.** The renderer attempts each resolver and emits a diagnostic to stderr on failure, but it never raises — a broken photo source must not break a brief render. Environments with no outbound HTTPS access to `en.wikipedia.org` / `commons.wikimedia.org` produce monogram placeholders for any figure that's not already cached in `assets/leaders/`. The bundled-photo tier of the cascade (tier 2 in the zero-config chain) means that figures resolved by earlier briefs persist to disk and work fully offline thereafter — the skill becomes incrementally more offline-capable as briefs are produced.

**Not yet implemented** (deliberate gaps; safe to add if a future brief surfaces a real need):
- `unavatar.io/twitter/{handle}` resolver for social-media profile pictures. Useful where Wikipedia coverage is thin (mid-rank diplomats, technical advisors). Would extend the prefix-routing table in `_fetch_leader_photo`.
- Photo-content validation (resolution floor, aspect-ratio check) — currently accepts any `image/*` content-type.

**Three use cases.** (a) Country political leadership in Section 2 (head of state, PM, opposition leader, key faction leaders); (b) bilateral counterparts in Section 1.5 (home-country side + host-country side, typically ambassadors plus relevant ministerial leads); (c) project counterparts in Section 7 (named signing principals or lead negotiators).

**Composition discipline: official sources first, Wikipedia as fallback.** Photos of state actors carry authority weight — a portrait from a foreign ministry's official page or an AU/UN press hub is analytically more appropriate than a Wikipedia thumbnail. When composing a brief, the order of preference for the `photo_source` field is:

1. **Official government / foreign-ministry page** (UAE MoFAIC, target-country MFA, AU/UN press hubs) — fetched as `https://...`. These are the authoritative portraits for any sitting official.
2. **Wikimedia Commons** (`commons:Filename.jpg`) — useful when an official Commons-licensed photo exists outside Wikipedia article scope.
3. **Wikipedia** (`wiki:Name` or `wiki-{lang}:Name`) — convenient and high-coverage for major political figures, but a tertiary source. Use as the fallback when no authoritative URL is found.
4. **Local file** — for analyst-curated photo libraries.
5. **Zero-config** — let the renderer try `en → fr → ar` Wikipedia. Use only when authoritative-source research has not been performed.

Ambassadors and working-level diplomats are the most common gap: they usually do not have Wikipedia articles, but their foreign ministry's "About the Ambassador" page typically has an official portrait. When that URL is stable, paste it into the markdown directly. When it is not stable or no portrait is publicly hosted, accept the monogram fallback — the card still conveys name + role + affiliation, which is the analytical content. Do not fabricate or guess URLs to avoid monograms.

Component syntax (zero-config — recommended default):

```markdown
::: leader-cards
title: Bilateral counterparts — heads of mission (May 2026)

- Khaled Nasser AlAmeri | UAE Ambassador to Sri Lanka | UAE Embassy, Colombo |
- Arusha Cooray | Sri Lankan Ambassador to the UAE | Embassy of Sri Lanka, Abu Dhabi |
:::
```

Just type names in the first field — the renderer attempts Wikipedia lookup automatically. For figures without Wikipedia articles, falls back to a monogram placeholder.

Component syntax (with explicit photo sources):

```markdown
::: leader-cards
title: Mixed sources example

- Public Figure | Role | Affiliation |                              # auto: wiki lookup by name
- Custom Wiki Name | Role | Affiliation | wiki:Their Wikipedia Title
- Commons-only Person | Role | Affiliation | commons:Their_File.jpg
- Direct URL Person | Role | Affiliation | https://gov.example/photo.jpg
- Local Photo Person | Role | Affiliation | photos/local.jpg
:::
```

Pipe-separated fields per row: `name | role | affiliation | photo_source`. The `photo_source` field is **optional** — its accepted forms are the five resolvers listed at the top of this section. Supported local-file extensions: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`. Title line is optional; defaults to "Key leaders".

**Use-case guidance for bilateral sections specifically:** Section 1.5 leader-cards = **exactly the two heads of mission**, no more and no less. The UAE ambassador to the country, and the country's ambassador to the UAE. Period. This keeps every bilateral section visually consistent across briefs — readers see the heads-of-mission view at the same position every time.

Ministerial bilateral leads (trade ministers, NSAs, special envoys, Joint Commission chairs), heads of state and government, and other notable figures *should appear by name in the visits-and-engagements timeline* (the markdown table or dated bullet list in Section 1.5), not as separate leader-cards. If a figure is politically central to the country itself (head of state, ruling party leader, opposition leader, key successor) they belong in the **Section 2 leader-cards block**, not in Section 1.5.

The validator enforces this with both a floor (<2 warns "incomplete") and a ceiling (>2 warns "bloated, move to visits timeline or Section 2").

Cards render in a wrapping grid (typically 3 per row at brief width, with cards at fixed 5cm width so they wrap to row-of-2 in narrower contexts like a 4-card bilateral block, or 2-of-2 in a pure-ambassador layout). Square photos (4.5cm × 4.5cm), name bold below, role in lighter weight, affiliation italicized smallest.

### Capital city override pattern
Added `_CAPITAL_OVERRIDES` dict alongside `_REGION_ALIASES` in the renderer. The bundled Natural Earth `capitals.parquet` has been stripped to a minimal schema with no discriminator between national capitals and sub-national capitals. Countries with multiple entries (Morocco has both Rabat and Laayoune) now require an explicit override; absent that, the renderer emits a stderr warning listing the candidates and picks alphabetically-first. Add new entries when future briefs surface ambiguity.

### Leader-line label placement
Map labels never get silently dropped. The renderer uses a spiral search (8 directions × 4 radii = 33 candidate positions) and places the label at the first non-colliding position. If the placed position is displaced significantly from the region's anchor, a thin gray leader line is drawn from the label back to the anchor with a small dot marker. Every region gets identified.

---

## Changelog: Sri Lanka country test + content critique (May 2026)

### 5th country test (Sri Lanka)
Sri Lanka was selected as the 5th country test to probe the skill's generalization beyond the four MENA/Sub-Saharan Africa cases. The test surfaced five real structural findings, three of which were fixed in code (capital city override for Colombo, region display overrides for Sri Lanka's 25 Sinhalese district names, and validation of the `--home-country` flag against markdown content) and two of which are documented as known limitations (Natural Earth district-vs-province aggregation gap; English-language source bias).

The brief itself (28 pages, India as the bilateral lens — first non-UAE bilateral test) is in the production-output set and rendered cleanly after the structural fixes.

### Region display overrides
Added `_REGION_DISPLAY_OVERRIDES` mechanism in `country_brief/maps.py` for cases where Natural Earth's admin-1 names are not analytically useful in English (e.g., Sri Lanka's Sinhalese transliterations). The override is country-keyed and maps NE name → display name; applied at label-drawing time. Purely additive — won't affect any country without an entry. Sri Lanka's 25 districts now display in English (Jaffna, Colombo, Kandy, etc. rather than Yāpanaya, Kŏḷamba, Mahanuvara).

### `--home-country` consistency validation
The Sri Lanka test surfaced that the `--home-country` parameter was parsed by `argparse` but never used downstream. The documentation described auto-suppression behavior that didn't actually happen. Fixed by adding a validation pass in `cli.py` that cross-checks the flag against whether the markdown contains a `## 1.5.` heading. Two warning cases caught: `--home-country` set to a country but Section 1.5 missing from markdown, OR `--home-country none` but Section 1.5 present. Added `test_home_country_consistency_validation` regression test.

### Section-quality reference (`references/section-quality.md`)
~12,500-word reference document codifying what separates strong analytical content from weak content for each of the brief's 21 sections (Executive Summary + Sections 1, 1.5, 2-19 + cross-cutting principles). Grounded in specific analytical failures and successes observed across the five country briefs produced during skill development. Each section entry covers: central question the section must answer, signs of strong content, signs of weak content (with specific failures observed), source priority, data quality framing, common analytical traps. SKILL.md step 3 of the production workflow now points analysts to this reference before they begin writing sections.

### Test count and runtime
Smoke test suite now at 10 tests, all passing in ~225 seconds. Each test guards against a specific category of regression observed during the skill's development. The home-country validation test was the most recent addition.

### Honest limits documented
The "Country brief production: realistic limits" section in SKILL.md now codifies four constraints the skill should be honest about: single-author depth limit, recency boundary, analytical-vs-descriptive risk, and the AI-generated content honesty principle. The "Effort estimates by brief type" table provides realistic time estimates for analyst calibration (1.5h follow-up → 4-5h new-country with non-English sources).

## Changelog: post-Tier 2 additions (continuation, May 2026)

### Wartime brief variant (Iran)
Documented as a top-level section in SKILL.md. Wartime fires when the country is in active armed conflict at the time of writing. Adaptations: Section 4 leads the analytical narrative (not Section 3); Section 15 reframes to "re-entry scenarios and prerequisites" rather than current market access; Section 16 carries elevated weight; Section 19 produces 4-5 scenarios with explicit probability assignments; Key Judgments carry war-contingent labels; confidence calibration is explicitly lower; recommendations are typically defensive. Iran brief (37 pages, 36 footnotes, Feb-May 2026 war coverage) is the canonical case.

### Antimeridian-crossing fix in maps
Countries spanning the 180° meridian (Fiji, Kiribati, Tuvalu, parts of Russia, NZ Chathams) previously produced world-spanning bounds and unreadable maps. Detection: if longitude span exceeds 180°, the renderer applies a shapely-based geometry transformation that shifts negative-longitude geometry by +360° before computing bounds and plotting. Neighbors layer shifted to match. Result: Fiji map renders correctly with Rotuma, Viti Levu, Vanua Levu, and Lau Group all visible at the proper scale.

### New components: delta-summary and scoring-summary
`::: delta-summary` produces a "what's changed since prior brief" block with directional arrows (↑↓→⇅) and color-coded category labels — for repeat readers maintaining country watch lists. `::: scoring-summary` produces a quantitative 0-100 table across portfolio-decision dimensions with quartile-colored bars (red <30, amber 30-60, olive 60-80, green 80-100), trend arrows, and one-line justifications. Both bridge qualitative prose to quantitative portfolio decision models. Both registered in the validator's known-classes set.

### Structural validation checks (8 total)
The validator now runs 8 structural checks gated at 120 body lines (so test fixtures aren't false-flagged): footnote-definition density, bottom-line length (>120 words warning), map presence, chart presence, risk-matrix presence, recommendations section presence, decision-implication callouts per spine section, and series-leakage phrase detection (catches "brief series", "earlier briefs", "covered in earlier", "in this series" — each brief is standalone and shouldn't reference others). The size gate is essential to prevent test fixture false positives.

### Length-discipline guidance in section-quality.md
Per-section length budgets calibrated against the May 2026 brief series (Ethiopia, Sudan, Syria, Morocco, Sri Lanka, Iran, Fiji). Sections 5/6/17/18 identified as routinely overlong with descriptive rather than analytical content; explicit guidance on when to cut entirely vs. compress vs. merge. "Could this paragraph be deleted with no analytical loss?" test articulated. Chart-decision-relevance test: charts that restate single numbers should be replaced with charts showing trajectory, comparison, or composition.

### Standalone-brief discipline
Documented as a fundamental principle alongside "describe-vs-analyze": each brief is standalone. The reader has one brief in front of them and shouldn't have to acquire context from other briefs in the series. Phrases like "thinner than the relationships covered in earlier briefs" leak production context. Absolute language only — describe the country on its own terms. Exception: explicit delta-summary blocks where comparison is the legitimate purpose. The series-leakage check enforces this at validation time.

### Arabic-version production (Path B implementation)
Skill can now produce Arabic country briefs (`--language ar`). **Native composition discipline:** the brief is composed in Arabic from source research, not translated from English. Translation produces detectable artifacts (calques, English-syntax-in-Arabic, false friends) even at high model capability. Three reference documents support production: `references/arabic-style.md` (register, rhetorical conventions, sentence structure, signposting), `references/arabic-glossary.md` (~250 curated terms across macro, governance, security, climate, portfolio domains), `references/arabic-names.md` (standardized Arabic forms for proper nouns per country). SKILL.md Arabic-production section documents when and how.

**Rendering infrastructure:**
- HTML `lang` and `dir` attributes switch by `--language`
- Font stacks swap to Amiri Naskh / Cairo / Noto Sans Arabic via template placeholders
- UI labels (cover eyebrow, date label, page-of separator, running header) localize
- Disclaimer text professionally written in Arabic, not translated
- RTL stylesheet block mirrors component borders, flips verdict-strip/stats-strip/leader-cards/scoring-summary direction, neutralizes letter-spacing for Arabic (letter-spacing breaks Arabic word shaping)
- Map and chart titles emit as HTML above their figures rather than baking into the PNG, so WeasyPrint handles Arabic shaping natively
- `arabic_reshaper` + `python-bidi` libraries reshape Arabic before matplotlib renders axis labels, ticks, and legends (matplotlib doesn't do Arabic shaping natively)
- `decision-implication` callout header auto-switches to "التداعيات على القرار" via body-content detection
- `scoring-summary` headers auto-switch to "البُعد / الدرجة / الاتجاه / المبرر"
- Map/chart source captions auto-switch to "المصدر"
- Validator's Section 1.5 detection made language-agnostic (number-based, not English-title-based)

**Required apt packages for Arabic rendering:** `fonts-hosny-amiri`, `fonts-sil-scheherazade`, `fonts-kacst`. Matplotlib font cache must be cleared after font install (`rm /root/.cache/matplotlib/fontlist-v390.json`). Python packages: `arabic-reshaper`, `python-bidi`.

**First production Arabic brief:** Sri Lanka (23 pages), composed natively in textbook MSA from the same source research as the English version. Demonstrates the pipeline end-to-end including chart with Arabic legend and axis labels, map with Arabic title, all components, full bibliography.

### Smoke-test count and runtime
23 smoke tests, all passing in ~170 seconds. Tests added since the initial Tier 2 set: chart-recipe registry, chart count / chronology checks, thematic-map coverage, `--strict` mode promotion, bundled-photo cascade, honorific stripping, auto-cache, min leader-card count, metadata-block wrappers, bibliography auto-numbering. Each test guards a specific regression observed during development.

### Documented production briefs
English: Ethiopia, Sudan, Syria, Morocco, Sri Lanka, Iran (wartime), Fiji (Pacific climate + antimeridian fix), Comoros (SIDS / climate-vulnerable), South Africa (GNU + post-loadshedding), Chad (refugee crisis + UAE-RSF complexity), USA (CONUS+insets atlas treatment).
Arabic: Sri Lanka.
