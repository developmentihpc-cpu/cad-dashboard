# Country Assessment Dashboard (CAD)

## Project Overview
A bilingual (English / Arabic) dashboard for the Office of Development Affairs that shows
development needs across 132 tracked countries — every World Bank low- and middle-income economy, plus Somaliland (high-income countries are excluded) — and builds country and regional
assessment reports (PowerPoint or PDF) in the browser. Data comes from a pre-baked World Bank
snapshot plus live API calls. No build step, no backend for the public site.

**Live site:** https://developmentihpc-cpu.github.io/cad-dashboard/ — GitHub Pages serves the
`docs/` folder of `main`. Pushing to `main` deploys it.

> The pipeline / intake form / Path B–C / documents features were **removed on 2026-10-08**.
> Do not reintroduce them unless asked. The root `index.html` is the **old pipeline version and is
> not deployed** — all dashboard work happens in `docs/`.

---

## Files (dashboard — `docs/`)
| File | Purpose |
|---|---|
| `index.html` | The app: HTML + CSS + JS (~4,300 lines) |
| `i18n_ar.js` | Arabic names: `AR_COUNTRY`, `AR_REGION`, `AR_INCOME`, etc. Keys are the English display names |
| `severity.js` | **The one severity scale** used everywhere: `SEV_RULES`, `sevLevel()`, `SEV_COLORS`, `SEV_LABELS` (0 Severe · 1 High concern · 2 Moderate · 3 On track) |
| `ind_defs.js` | `IND_DEFS[id] = [English, Arabic]` plain-language indicator definitions |
| `deck_kit.js` | `DK` — shared deck palette, fonts, value hygiene (missing / impossible / outdated), RTL mirroring, `STALE_YEARS = 8`, map slots |
| `country_deck.js` | `buildCountryDeck(opts)` — 12-slide country report: cover, overview, executive summary, eight sector slides, method (+ DHS "where the need is" map slides) |
| `region_deck.js` | `buildRegionDeck(opts)` — regional needs-assessment report |
| `pdf_deck.js` | `PdfDeck` — drop-in stand-in for the PptxGenJS constructor that renders the same deck to PDF (canvas + jsPDF, loaded on demand) |
| `evaluator.html` | Program Evaluation tool, loaded lazily in an iframe by the Evaluation view |
| `ownership_process.html` | Standalone process-flow slide (not linked from the app) |
| `logo.png`, `somaliland-flag.svg` | Header logo; custom flag |
| `reports/manifest.json` + `*.pptx` | Published full-format (23-slide) AI decks, e.g. India, Paraguay |

### Data (`docs/data/`)
| File | Source | How it is refreshed |
|---|---|---|
| `indicators.json` | World Bank WDI (+ IMF WEO government debt). Includes `_meta` and `_regions` | `build_indicators.py`, monthly GitHub Action (`refresh_indicators.yml`) and whenever that script changes |
| `trade_partners.json` | World Bank WITS / UN Comtrade | One-off download (no script in repo) |
| `environment.json` | Yale EPI 2026 + WorldRiskReport 2025 | One-off download |
| `uis.json` | UNESCO UIS (out-of-school, school basic services, trained teachers) | One-off download |
| `sme_jobs.json` | ILOSTAT "Employment by sex and establishment size" (labour force surveys): share of workers in businesses under 50 workers, by size band; only countries where size is known for ≥ 50% of workers (67) | `build_indicators.py` (`build_sme_jobs`), with the monthly refresh; keeps the previous file if ILO is unreachable. ILO bands stop at 50+, so medium firms (50–249) are counted with large |
| `leader_terms.json` | Researched (web, with a source URL per entry), as of 2026-10-14: year in office, term length, year the current term ends | Manual — **review after elections / changes of government**. Reconciled with Wikidata in `applyLeaderTerms`: same person → term added; different people → whichever reports the more recent start in office wins; Wikidata empty → table fills in |
| `subnational/{ISO3}.json` + `index.json` | DHS Program regional survey data and outlines (30 countries) | One-off download; used when the live DHS API is slow |

`build_indicators.py` parses `COUNTRY_ISO` and `CA_INDICATORS` **directly out of `docs/index.html`**,
so adding an indicator there is enough for the next snapshot to include it.

---

## Architecture
- **Vanilla JS**, DOM manipulation, inline `onclick` handlers. No framework.
- CDN libraries: Leaflet 1.9.4, topojson-client 3, pptxgenjs 3.12.0, jsPDF 2.5.1 (loaded on demand by `pdf_deck.js`).
- Map outlines: Natural Earth via `world-atlas@2` TopoJSON (`loadWorld()` / `addWorldLayer()`), Esri light-gray tiles underneath.
- Fonts (Google): Lora (serif headings), Montserrat / Inter (text), IBM Plex Sans Arabic + Noto Naskh Arabic (Arabic UI / PDF). Decks use Sakkal Majalla for Arabic per ODA brand.
- Flags: `flagcdn.com`, overridden by `CUSTOM_FLAGS` (Somaliland).
- Live sources called from the browser: World Bank API (indicators, WGI governance scores), Wikidata (leaders), DHS Program API (sub-national data).
- Persistence is **per browser only**: `localStorage` (`cad_lang`, `cad_view`, `oda_rep_format`, `oda_eval_endpoint`) and **IndexedDB** `cad_reports` (saved report library, via `RepStore`).

---

## Layout
```
[Header 56px — logo | "Country Assessment Dashboard" | country search | date | EN / عربي]
[Sidebar 60px] [Main content]
```

### Sidebar → views
| Order | `data-view` | View id | Content |
|---|---|---|---|
| 1 | `executive` | `view-executive` | **Landing page.** "Global South at a Glance": KPIs (countries, low-income, population, no electricity, no basic water, reports saved), need-index mini map, regions, recent reports |
| 2 | `countries` | `view-countries` | Full Leaflet map shaded by need tier; click a country → country drawer |
| 3 | `reports` | `view-reports` | Build country / batch / regional reports; saved-reports library; published decks |
| 4 | `evaluation` | `view-evaluation` | `evaluator.html` in an iframe (lazy-loaded, cache-busted) |

`switchView(view, navEl)` activates a view and remembers it in `cad_view`. `restoreView()` returns a
user to their last view; a URL ending `#executive` always opens the landing page. `goView(v)` is the
shortcut when you don't have the nav element.

### Country drawer
`openCountryDrawer(country)` — subtitle shows region · income group · need index and rank.
Tabs (`cdSwitchTab`):
- **Overview** (`cdRenderOverview`) — accurate country map + flag, capital, population, leaders (Wikidata) and governance (WGI), need-index panel, saved/published reports.
- **Indicators** (`cdRenderIndicators`) — sub-tabs from `CA_TABS`: Overview + the eight ODA sectors (water, energy, agrifood, education, health, econ, business, trade). Cards show value, year, severity pill, regional median; outdated figures are flagged. Clicking a card opens `cdIndDetail(id)` (definition, source, sparkline series). Trade, environment/risk and UIS cards come from the extra data files (`loadExtras()`).

---

## Country registries
Keep these in sync when adding a country (all keyed by the **English display name**):

| Object | Where | Purpose |
|---|---|---|
| `COUNTRY_LATLNG` | `index.html` | Map centroid — also defines the tracked country list |
| `COUNTRY_ISO` | `index.html` | ISO3 for World Bank / DHS (read by `build_indicators.py`) |
| `COUNTRY_ISO2` | `index.html` | ISO2 for flags and Wikidata |
| `COUNTRY_INCOME` | `index.html` | `'LIC' / 'LMIC' / 'UMIC'` |
| `COUNTRY_INFO` | `index.html` | `{ capital, currency, languages }` for reports |
| `AR_COUNTRY` | `i18n_ar.js` | Arabic name |
| `GEO_NAME` | `index.html` | Only if the world-atlas name differs (e.g. `'Congo, Dem. Rep.' → 'Dem. Rep. Congo'`) |

Countries with no outline in the 50m world map (Tuvalu) show as a dot on the map and "Map unavailable" in reports.
Regions come from `indicators.json → _regions` (World Bank regions) into `REGION_MEMBERS`.
After adding a country, re-run the snapshot (Actions → "CAD — Refresh Indicator Snapshot").

---

## Key concepts

### Indicator data flow
`loadPrebakedIndicators()` loads the snapshot at startup → `ca_loadCountryData(country)` seeds
`countryDataCache[country]` from the snapshot, then refreshes from the live World Bank API and calls
`ca_rerenderIfOpen()`. Shape: `countryDataCache[country][id] = { value, year }`.
`ca_formatValue(raw, ind)` formats values; `isStale(d)` flags figures older than the window.

### Need index
`needScores()` ranks all tracked countries on `NEED_INDS` (under-5 mortality, maternal mortality,
undernourishment, basic water, basic sanitation, electricity) **from the snapshot**, so rankings are
stable between page loads. `needTier(c)` → `hi / mid / lo / none`, coloured by `NEED_SHADES`.
The method is explained in the drawer (`needPanelHtml`, `cdOpenNeedHow`).

### Severity
Always use `severity.js` (`sevLevel(id, v)`, `indSeverity`, `sevPill`). Thresholds follow SDG / WHO /
UNESCO / IMF benchmarks; indicators marked `peers: true` are compared with other tracked countries
in the dashboard and skipped in reports. Dashboard cards, the region popup and both decks must
agree — never add a separate colour scale.

### Reports (`view-reports`)
- **Country report** — `repRunSingle` → `repBuildCountryBlob` gathers data (`repCountryData`), flag,
  map (`repMapImage`), leaders/WGI (`repPolitics`), DHS sub-national maps (`repSubnational`: live
  `subLive`, falling back to `subSnapshot`), then calls `buildCountryDeck`.
- **Batch** — `repRunBatch(countries)`; **Region** — `repRunRegion(region)` → `buildRegionDeck`.
- Format: `repAskFormat()` asks PPTX or PDF (remembered); `repDeckCtor(fmt)` returns `PptxGenJS` or `PdfDeck`.
- Every generated report is saved to the IndexedDB library (`repSave`) and `onReportsChanged()` refreshes all views that list reports.
- **Full AI reports** (`repRunAIBatch`, `repRunRegionAI`) need the local research server
  `evaluator_score_server.py` on port 8787 (endpoint overridable via `oda_eval_endpoint`); they do
  not work from the public site.
- Every async step has a timeout — keep it that way so one slow API never hangs a report.

### The eight sectors (dashboard tabs and report slides use the same list)
Water · Energy · Agriculture & Food Security · Education · Health · Economic Empowerment · Business Enablement · Trade.
There is **no governance sector**: WGI governance scores appear only in the overview slide's political-situation box and the
drawer overview. Digital and environment indicators were removed on purpose. Report sector keys: `wash`, `energy`, `food`,
`education`, `health`, `econ`, `business`, `trade` (`wash`/`food`/`education`/`health` also key the DHS maps in `SUBNAT`).
The Trade slide also shows the top export markets and import sources (`repTrade` → `opts.trade`, from `trade_partners.json`).
When adding an indicator: `CA_INDICATORS` (index.html), a benchmark in `severity.js` (or `peers:true`), a definition in
`ind_defs.js`, and for the report the catalogue `I`, `SRC`, and `WHY`/`DP` in `country_deck.js`.

### Deck rules (country_deck.js / region_deck.js)
- 13.333 × 7.5 in grid. Arabic decks mirror every element (`x → W − x − w`), right-align text and use Sakkal Majalla +2 pt.
- Narrative sentences are generated from each value's severity, so wording can't contradict the data.
- Missing, impossible (e.g. 0% spending) and outdated (> `DK.STALE_YEARS` = 8 years) values are shown as "—" or with their year and **kept out of ratings and narrative**.
- Sub-national maps only appear when a DHS survey within the stale window covers ≥ 80% of regions; regions are linked by DHS region ID, not name.
- A "where the need is" map slide is added **only** when its indicator (`SUB_LINK`: DHS id → national id) is severe/high concern and one of the sector's two most critical issues (`s.mapId`). That issue then leads the sector slide (first card, first insight, "next slide" pointer) so the map continues the story.
- Indicators with no data are **left off** slides (no "—" cards, no empty facts). Where ≥ 2 are missing, a short "Limited data" note names them.
- Stat cards carry the benchmark and gap (`gap()`: points for shares of people and 0–100 scores, relative % for % of GDP, × for higher-is-worse). There are no separate benchmark charts.
- Key insights explain the "so what": `WHY[id]` lists linked indicators (only named when they are also off track in that country's data, via `DP` phrases) plus what the gap means. Add new indicators to `WHY`/`DP` in both languages.
- Interventions: `acts` (aid, triggered by off-track indicators) + `inv` (development-investment angle, e.g. offtake agreements for agriculture), shown only when its condition holds.
- Executive summary = overall picture + priority-sector columns, each with its most urgent gaps, people affected (`people()`) and "why it matters". No strengths or data-notes blocks.
- Overview slide: report map names neighbouring countries (`mapNameCountries`, Arabic via `AR_NE_NAME` in `i18n_ar.js`); leaders show term years (`hosSince/hosUntil`, `hogSince/hogUntil` from Wikidata P580/P582); governance bars have a severity colour key; the need index has a footnote (`NEED_NOTE`).

### Arabic / RTL
`setLang('en' | 'ar')` switches `dir="rtl"`, labels, country/region names, map labels and report
language. Helpers: `tr(en, ar)`, `cN(country)`, `rN(region)`, `incN(code)`, `unitN(unit)`,
`LOCALE()` (Arabic months, Western digits). Static markup uses `data-ar="…"`.
**Every new user-facing string needs an Arabic version.**

### Leaders
From Wikidata (language-neutral labels). `LEADER_OVERRIDE` pins the UN-recognised office holder
where two administrations claim the same office (currently Libya) — review if the situation changes.

---

## Colour tokens (CSS `:root`)
Dashboard: `--accent #2D3F7B` (navy), `--teal #2DB88A`, `--maroon #9B120B`, `--crimson #E04444`,
`--bg #F4F5F8`. Executive / reports pages use the `ex-` classes (white / sky / gold, serif headings).
Decks: `DK.C` (INK, NAVY, SKY, GOLD …). Severity: `SEV_COLORS` from `severity.js` (red, orange, yellow, green).

---

## Rest of the repo (Python agents — separate from the Pages site)
| File / workflow | Purpose |
|---|---|
| `build_indicators.py` | Builds `docs/data/indicators.json` (see above) |
| `build_country_report.py`, `country_ppt_builder.py`, `country_map_renderer.py`, `combine_reports.py` | Server-side 23-slide country-proposal decks and multi-country combiner |
| `evaluator_score_server.py` | Local research / scoring server (port 8787) used by the evaluator and full AI reports |
| `agents_pipeline.py`, `verify_workflow.py`, `agent_to_builder_ctx.py` | Email-triggered report pipeline (`email_watch.yml`, every 5 min) |
| `telegram_*.py` | Telegram bot (Cloud Run webhook + polling fallback) |
| `digest_agent.py` | Weekly digest (`daily_digest.yml`, Mondays) |
| `deploy.yml` | Deploys the agent container to Fly.io on push (ignores `docs/**`) |
| `country_brief_skill/` | Packaged country-brief skill and flag assets |

---

## What NOT to do
- Don't edit a `docs/*.js` file without bumping the `?v=` tag on its `<script>` in index.html (all share one value, e.g. `?v=20261016a`); otherwise browsers keep the old cached copy and downloads use old report code.
- Don't edit the root `index.html` expecting it to go live — edit `docs/index.html`.
- Don't bring back the pipeline, intake form, Path A/B/C or documents views.
- Don't add a second severity scale or hard-code severity colours — use `severity.js`.
- Don't add a user-facing string without its Arabic version, or a layout that breaks in RTL.
- Don't compute the need index from live data — it uses the snapshot so ranks stay stable.
- Don't put data in a report narrative that is missing, impossible or older than `DK.STALE_YEARS`.
- Don't add an API call without a timeout and a fallback (snapshot or "—").
- Don't add a country to only some registries (see the table above).
- Don't add a sidebar icon without a wired view.
- Don't call `map.invalidateSize()` without an `if (map)` guard, or create the map before `safeInitMap()`.
- Don't use `prompt()` for input — use inline forms or the modal (`cdModal`).
- Don't split `index.html` into a bundled build — extra plain `<script src>` files in `docs/` are fine (that is how the deck modules work).
