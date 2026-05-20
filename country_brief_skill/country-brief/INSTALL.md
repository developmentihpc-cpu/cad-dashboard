# Country Brief skill — installation

This skill produces analytical country briefs in PDF format from markdown source files. It supports English and Arabic output via the `--language` flag.

The renderer pipeline is: pandoc (footnote → HTML conversion) → custom Python renderer (`scripts/country_brief/`) → WeasyPrint (HTML → PDF). WeasyPrint depends on a native rendering stack (Pango / Cairo / GDK-PixBuf), which is the main per-OS install variable.

## System dependencies

Pick the section that matches your OS. After install, jump to **Python dependencies** below.

### Linux (Debian / Ubuntu)

```bash
# Core rendering pipeline
apt-get install -y \
    pandoc \
    weasyprint \
    python3-pip

# Arabic typography (only needed for Arabic briefs)
apt-get install -y \
    fonts-hosny-amiri \
    fonts-sil-scheherazade \
    fonts-kacst
```

After installing Arabic fonts for the first time, clear matplotlib's font cache so it picks them up:

```bash
rm -f ~/.cache/matplotlib/fontlist-*.json
```

### Windows

WeasyPrint needs the GTK3 runtime for Pango / Cairo / GDK-PixBuf. The simplest path:

```powershell
# GTK3 runtime (required for WeasyPrint to render anything)
winget install tschoonj.GTKForWindows.Runtime

# Pandoc
winget install JohnMacFarlane.Pandoc
```

After installing GTK, open a fresh terminal so the new `PATH` is picked up. Verify with `python -c "import weasyprint; print(weasyprint.__version__)"`.

For Arabic briefs, install **Amiri** (or another Arabic-capable font) — the renderer probes a chain of common system fonts (Amiri → Noto Naskh Arabic → Noto Sans Arabic → Arial → Tahoma → Segoe UI) and uses the first one found. Windows ships with Arial which has Arabic glyphs, so the absolute floor is "your charts work but use Arial"; for print-quality typography matching the body text, install Amiri:

```powershell
# Download Amiri from amirifont.org or via winget if a package is available;
# otherwise drag the .ttf files into system → Settings → Personalization → Fonts
```

After installing fonts, clear matplotlib's font cache:

```powershell
Remove-Item "$env:LOCALAPPDATA\matplotlib\fontlist-*.json" -Force -ErrorAction SilentlyContinue
```

### macOS

```bash
brew install pandoc weasyprint pango cairo gdk-pixbuf

# Arabic typography (only needed for Arabic briefs)
brew tap homebrew/cask-fonts
brew install --cask font-amiri font-scheherazade-new
```

After installing fonts, clear matplotlib's font cache:

```bash
rm -f ~/Library/Caches/matplotlib/fontlist-*.json
```

## Python dependencies

```bash
pip install \
    weasyprint \
    matplotlib \
    geopandas \
    pyarrow \
    shapely \
    pyyaml \
    pypdf

# Arabic shaping for matplotlib chart labels (only needed for Arabic briefs)
pip install \
    arabic-reshaper \
    python-bidi
```

Add `--break-system-packages` on Linux distros that enforce PEP 668.

- `pyarrow` is required for geopandas to read the bundled `assets/geo/*.parquet` files.
- `pypdf` is used by the smoke-test suite for page counting (cross-platform; the older `pdf2image` is no longer required).

## Verify the install

```bash
cd country-brief
python tests/run_smoke_tests.py
```

Should complete in ~170 seconds with `23 passed, 0 failed`. This is the canonical "is my install sound?" check — run it any time the renderer behaves unexpectedly.

## Directory layout

```
country-brief/
├── SKILL.md                     ← Primary skill documentation; read first
├── INSTALL.md                   ← This file
├── README.md                    ← Quick-start summary
├── assets/
│   ├── brief-template.html      ← Master print stylesheet (LTR + RTL)
│   ├── flags/                   ← Country flag PNGs (242 flags, ~5 MB)
│   ├── geo/                     ← Natural Earth admin0/admin1 + capitals parquet (~16 MB)
│   └── leaders/                 ← Curated + auto-cached leader portraits (grows over time)
├── references/
│   ├── data-sources.md          ← Trusted data sources catalog
│   ├── failure-modes.md         ← Known analytical failure patterns
│   ├── section-library.md       ← Per-section content guidance
│   ├── section-quality.md       ← Length and decision-density discipline
│   ├── arabic-style.md          ← Arabic register and rhetoric guide
│   ├── arabic-glossary.md       ← ~250 curated Arabic terms
│   └── arabic-names.md          ← Standardized Arabic proper-name register
├── scripts/
│   ├── render_brief.py          ← Backward-compatibility CLI shim
│   └── country_brief/           ← Renderer package
│       ├── __init__.py
│       ├── cli.py               ← Argument parsing, template substitution, --strict
│       ├── pipeline.py          ← Render orchestration, metadata-block wrapping
│       ├── validation.py        ← Pre-render + manifest validation, chart-recipe registry
│       ├── inline.py            ← Markdown utilities (footnotes, anchors)
│       ├── toc.py               ← Table of contents + cover
│       ├── fenced_divs.py       ← ::: component dispatch, leader photo cascade
│       ├── charts.py            ← Matplotlib chart rendering
│       └── maps.py              ← Geopandas map rendering (incl. CONUS+insets for USA)
└── tests/
    ├── run_smoke_tests.py       ← 23 regression tests
    └── fixtures/                ← Test manifests and minimal briefs
```

## Rendering a brief

```bash
# English (default)
python scripts/render_brief.py \
    --input my-country-brief.md \
    --output my-country-brief.pdf \
    --country "Sri Lanka" \
    --subtitle "Post-default recovery and bilateral acceleration" \
    --date "May 2026" \
    --home-country "UAE" \
    --toc

# Arabic
python scripts/render_brief.py \
    --input my-country-brief-ar.md \
    --output my-country-brief-ar.pdf \
    --country "سريلانكا" \
    --subtitle "تعافٍ بعد التعثر السيادي" \
    --date "مايو 2026" \
    --language ar \
    --toc

# Production-grade: refuse to render if structural-audit binding checks fail
python scripts/render_brief.py --input brief.md --output brief.pdf --strict ...
```

## Working with the skill

Read `SKILL.md` first. It documents:

1. When to use this skill (and when not to)
2. The brief structure: cover, verdict strip, bottom line, key judgments, country spine sections 1-6, optional modules 7-18, outlook 19, risk matrix, recommendations, bibliography
3. Wartime brief variant (for countries in active conflict)
4. Arabic-version production (when and how)
5. The component vocabulary (verdict-strip, snapshot, key-judgment, counterfactual, faction-box, leader-cards, stats-strip, bilateral-stats, severity-box, risk-matrix, scenario, decision-implication, scoring-summary, delta-summary, chart, map)
6. Writing discipline (describe-vs-analyze, standalone-brief, length-discipline)
7. Footnote citations (Chicago-style) and auto-numbered bibliography
8. Pre-render validation: structural checks, chart-recipe registry (12 country-specific chart recipes), section-scoped chronology, leader-cards section-aware bounds, `--strict` mode
9. Leader photo cascade: explicit URL → bundled `assets/leaders/{slug}.{ext}` → en/fr/ar Wikipedia → monogram, with honorific stripping and auto-cache to the bundled directory on successful network resolution
10. Production realism (effort estimates, recency boundaries)

The `references/` directory expands on specific topics — read the relevant reference document before composing content in that area.

## Limitations

- **Sandboxed environments:** Wikipedia photo auto-fetch fails when outbound HTTPS is blocked. The bundled cascade falls through to monogram placeholders for figures not already cached in `assets/leaders/`. Coverage compounds: each successfully resolved figure persists to `assets/leaders/{slug}.{ext}` for future briefs.
- **Matplotlib Arabic shaping:** Requires `arabic-reshaper` and `python-bidi` packages. Without them, Arabic in chart labels renders as disconnected isolated letterforms.
- **Map projections:** Most countries render correctly. Countries crossing the 180° meridian (Fiji, Kiribati, Tuvalu) are handled by an antimeridian fix. The USA uses a CONUS+insets layout (lower-48 main view, Alaska and Hawaii as small inset axes) to avoid the longitude-span blowout from Aleutian-spanning bounds.
- **Pandoc dependency:** Pandoc must be on PATH (tested with Pandoc 3.0+). The renderer shells out to it for footnote conversion. Check with `pandoc --version`.

## Asset bundle

Total assets ~48 MB. Flags (~5 MB) and geo (~16 MB) are upstream-stable and bundled. The `assets/leaders/` directory (~26 MB and growing) accumulates curated + auto-cached portraits. For fork hygiene, decide whether the leaders directory should ship with your fork or be `.gitignore`d — both are valid choices.

## Version

May 2026. Active feature set: smoke-test suite (23 tests), package-split renderer, manifest validation, structural validation, `--strict` mode, chart-recipe registry (~12 recipes), bundled leader photo cascade with auto-cache and honorific stripping, section-scoped chronology check, section-aware leader-card bounds, thematic-map coverage check, metadata-block CSS pattern for end-matter typography, CONUS+insets USA atlas treatment, wartime brief variant, antimeridian fix, delta-summary and scoring-summary components, Arabic production support, standalone-brief discipline.

11 English country briefs produced (Ethiopia, Sudan, Syria, Morocco, Sri Lanka, Iran wartime, Fiji, Comoros, South Africa, Chad, USA). 1 Arabic country brief produced (Sri Lanka).
