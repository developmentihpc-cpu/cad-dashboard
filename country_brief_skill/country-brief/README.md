# Country Brief skill

A Claude skill for producing analytical country briefs as PDFs from markdown source files.

## What it does

Produces 20-40 page PDF country briefs with:

- Cover page with country flag, title, subtitle, date, AI-provenance disclaimer
- Optional table of contents
- **Executive summary**: verdict strip (4 color-coded tiles), bottom-line synthesis, 4-7 key judgments with confidence calibration, counterfactual block, optional scoring-summary across portfolio-decision dimensions
- **Country spine** (always present): Section 1 snapshot, Section 1.5 bilateral relations (home-country), Section 2 political context, Section 3 economic conditions, Section 4 security & stability, Section 5 governance, Section 6 social dynamics
- **Optional modules**: humanitarian (Sect 8), diaspora (Sect 13), infrastructure (Sect 17), comparative regional (Sect 18), etc.
- **Outlook**: Section 19 with 3-5 scenarios at explicit probabilities, monitoring indicators, risk matrix, recommendations with owner+timeline labels
- **Bibliography**: auto-generated from footnote references using Chicago notes-and-bibliography style

## Languages

- **English** (default): produced for 11 countries — Ethiopia, Sudan, Syria, Morocco, Sri Lanka, Iran (wartime variant), Fiji, Comoros, South Africa, Chad, USA.
- **Arabic** (`--language ar`): produced for Sri Lanka as the first demonstration. Composed natively in textbook MSA from source research — not translated from English. Uses Amiri Naskh typography, full RTL layout, Arabic glossary and proper-name register.

## Quick start

```bash
python scripts/render_brief.py \
    --input my-brief.md \
    --output my-brief.pdf \
    --country "Sri Lanka" \
    --date "May 2026" \
    --home-country "UAE" \
    --toc
```

For Arabic:

```bash
python scripts/render_brief.py \
    --input my-brief-ar.md \
    --output my-brief-ar.pdf \
    --country "سريلانكا" \
    --date "مايو 2026" \
    --language ar
```

See **INSTALL.md** for system dependencies. Read **SKILL.md** for full documentation.

## Component vocabulary (cheat sheet)

```
::: verdict-strip       four colored-dot tiles (status / exposure / access / outlook)
::: bottom-line         the 80-word synthesis paragraph
::: key-judgment        4-7 directional claims with confidence levels
::: counterfactual      what would invalidate the judgments
::: scoring-summary     0-100 quantitative table across decision dimensions
::: delta-summary       what's changed since prior brief (for repeat readers)
::: snapshot            country basics (capital, population, GDP, currency, etc.)
::: stats-strip         3-4 stat cards in a horizontal strip
::: bilateral-stats     stats with source attribution per cell
::: faction-box         political/armed actors with party / role / stance
::: leader-cards        photo cards for political leaders or bilateral counterparts
::: severity-box        graded severity assessment (risk axis × geography)
::: chart               matplotlib line/bar/stacked-bar charts
::: map                 country reference map or choropleth
::: scenario            outlook scenario with probability and portfolio implication
::: risk-matrix         risks plotted on a 2×2 likelihood × impact grid
::: decision-implication callout box ending each spine section with portfolio guidance
```

## Production discipline

- **Native composition, not translation.** Each brief composed from source research, not translated from a different-language version. Translation produces detectable artifacts even at high model capability.
- **Standalone briefs.** Each brief written for a reader who only has this brief. No references to "other briefs in this series" — describe the country on its own terms.
- **Length and decision-density discipline.** Per-section length budgets enforced by structural validator. Sections that read as descriptive rather than analytical should be cut or merged.
- **Honest confidence calibration.** Match confidence level to source quality. Wartime briefs carry explicitly lower confidence than stable-country briefs. War-contingent labels on individual judgments where appropriate.
- **Chicago notes-and-bibliography citations.** Every substantive empirical claim carries a footnote reference. Auto-generated bibliography from `[^N]` references.

## Limitations

- Photo auto-fetch in fully sandboxed environments (no outbound HTTPS) is limited to figures already cached in `assets/leaders/`; new figures fall back to monogram placeholders. The bundled cascade (explicit URL → `assets/leaders/{slug}.{ext}` → en/fr/ar Wikipedia → monogram) plus auto-cache to the bundled directory means coverage compounds: every successfully resolved figure persists to disk for future briefs.
- Arabic district/region labels on maps not yet localized (English Latin script). Requires per-country extension of `_REGION_DISPLAY_OVERRIDES`.
- Series-leakage validator check is English-only. Arabic equivalents not detected. Low priority since native composition doesn't produce leakage.

## Test status

`python tests/run_smoke_tests.py` → 23 passed, 0 failed in ~170 seconds.
