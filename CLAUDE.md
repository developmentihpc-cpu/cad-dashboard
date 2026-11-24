# Country Needs Dashboard (CAD — formerly Country Assessment Dashboard)

## Project Overview
A bilingual (English / Arabic) dashboard for the Office of Development Affairs that shows
development needs across 132 tracked countries — every World Bank low- and middle-income economy, plus Somaliland (high-income countries are excluded) — and builds country and regional
assessment reports (PowerPoint or PDF) in the browser. Data comes from a pre-baked World Bank
snapshot plus live API calls. No build step, no backend for the public site.

**Live site (shared, sign-in required):** https://country-assessment-dashboard.pages.dev (Cloudflare project `country-assessment-dashboard`; the earlier `cad-dashboard` project is to be deleted) — Cloudflare Pages builds from
`main` (no build command, output directory `docs`, env var `SKIP_DEPENDENCY_INSTALL=1` so the root
`requirements.txt` is ignored). Pushing to `main` deploys it in about a minute.
- Sign-in: `functions/_middleware.js` (Pages Function) gates every request. Cloudflare Zero Trust / Access
  is **not** used (needs a card). Two modes:
  - **Request and approve** (when the KV binding `CAD_KV` (the live project uses `cad_kv`, namespace `cad-access`) and an email sender exist: secrets `MAIL_RELAY_URL` + `MAIL_RELAY_TOKEN` for the Google Apps Script relay `mail_relay.gs`, deployed from developmentihpc@gmail.com as a web app with a `TOKEN` script property; or `BREVO_API_KEY`): people request
    access at `/__request`; admins (`ADMIN_EMAILS`, default developmentihpc@gmail.com) get an email and
    approve / decline / remove at `/__admin` (a "Manage access" pill shows on the dashboard for admins).
    Sign-in: approved people enter their email only (no code; chosen by the user 2026-10-22). Admins still get a
    6-digit code by email (needed for /__admin). Secret `SIGNIN_MODE=code` brings codes back for everyone. Codes are emailed through the relay (from that Gmail). Sessions:
    7 days, signed with `SESSION_KEY` (or the relay token), re-checked against KV on every request.
  - **Passwords** (fallback until the above is set up): secret `CAD_USERS` = `email:password, …`.
    In code mode the emails in `CAD_USERS` still count as approved.
- GitHub Pages was unpublished and the repo made **private** on 2026-10-21; the old github.io address no longer works.
- A Claude-artifact test copy exists (https://claude.ai/artifact/7SwNV8j8SBAsBf82iqKAUJ, built by a scratch
  script); downloads don't work there for viewers outside the organisation, so it is not the shared version.

> The pipeline / intake form / Path B–C / documents features were **removed on 2026-10-08**.
> Do not reintroduce them unless asked. The root `index.html` is the **old pipeline version and is
> not deployed** — all dashboard work happens in `docs/`.

---

## Files (dashboard — `docs/`)
| File | Purpose |
|---|---|
| `index.html` | The app: HTML + CSS + JS (~4,300 lines) |
| `i18n_ar.js` | Arabic names: `AR_COUNTRY`, `AR_REGION`, `AR_INCOME`, etc. Keys are the English display names |
| `sub_ar.js` | `AR_SUB`: Arabic names for every DHS survey region in `data/subnational/` (report maps and "where the need is" slides), used via `subN()` in index.html. Add names when a new survey country is downloaded |
| `focus_areas.js` | `FOCUS_AREAS[country]`: sub-national focus areas added to that country's report (currently Jordan → Al Aqabah). Each has a map point (`ll`, drawn by `drawFocusPlaces` on the report's country map), researched facts/overview/sector notes/needs/investment angle in English and Arabic with sources and an `asOf` date, and `dhs` (the area's name in `data/subnational/`) so the survey comparison uses DHS data. `repFocusAreas()` adds survey figures, governorate rank (ties shown with “=”) and a highlighted area map; `buildCountryDeck` renders two slides before the method slide: overview (map, key facts, overview bullets, “Announced in 2026” box) and key sectors + priority needs (bullets). Survey comparisons were dropped at the user’s request (Aqaba is mostly at or above the national average; vaccination is cited in the needs). **Review the facts when sources update** |
| `country_packs.js` | `COUNTRY_PACKS[country]`: researched extra slides for one country (currently Jordan, asOf 2026-11). `drivers` + `opportunities` (2 context slides after the executive summary), `refugees` (refugee-situation slide right after the executive summary: facts, a `maps` key, points, support); `drivers.points` take an optional third item, an icon key from `DK.ICONS` (Lucide line icons, rasterised by `repIcons()` in index.html), `aid` (humanitarian-aid slide after it: facts, appeal coverage bars [name, received, required in US$M], donors, points, support), `atlas` + `maps` (governorate map pages of one or two maps; `after: sectorKey` puts a page right after that sector's slide, otherwise after the sector slides; one-map pages take `points` — values inline or `dhs:` sector from data/subnational; built by `repCountryPack()` in index.html, map slot `DK.MAP_SLOTS.atlas`), `focusSectors[focusKey]` (8-sector Strength/Mixed/Gap slide for a focus area, sorted gap â mixed â strength), optional `data` (extra figures merged into the report data, e.g. `POP.YOUTH`), optional `sectorActs[sectorKey]` ([EN, AR] interventions shown first on that sector slide â Jordan: child vaccination on Health), optional `sectorStats[sectorKey]` (replaces that sector's stat cards â Jordan drops `ILO.SME.U50` from econ) and optional `recommendations` (slide before the method slide; Jordan has none since Nov 2026). Jordan sources: DoS Labour Force Survey Q3 2025 (unemployment by governorate, Jordanians), UNHCR data portal 31 Oct 2026 (Syrian refugees by governorate, camps within Mafraq/Zarqa; returns and funding), DHS 2023 API (anaemia women/children, piped vs bottled drinking water by governorate), IMF, MoP, Ministry of Water; youth share 15â24 = 18.7% (2025) from UN WPP via World Bank (SP.POP.1519/2024 .MA/.FE.5Y weighted by SP.POP.TOTL.MA/FE.IN). **Review when sources update** |
| `severity.js` | **The one severity scale** used everywhere: `SEV_RULES`, `sevLevel()`, `SEV_COLORS`, `SEV_LABELS` (0 Severe · 1 High concern · 2 Moderate · 3 On track). Water scarcity: `ER.H2O.INTR.PC` (Falkenmark 500/1,000/1,700 m³) and `ER.H2O.FWST.ZS` (SDG 6.4.2: 100/75/25%), always on the report Water slide (the sector's `keep` list). Education report cards add `uis:ROFST.1.CP`/`uis:ROFST.2.CP` (passed in by `uisData()` from uis.json) and `SE.PRM.UNER`. Report sector rating = worst indicator level, except spending (`INPUTS` in country_deck.js: `SE.XPD.TOTL.GD.ZS`, `SH.XPD.CHEX.GD.ZS`) counts as Moderate at most; Sector slides run in order of need (same order as slide 2: level, then number of severe gaps); Trade is `noPriority:true` (rated and listed on slide 2, but never one of the slide 3 priority sectors) |
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
| `trade_partners.json` | UN Comtrade public API: top 5 export markets and import sources per country, plus the UAE's rank and share; mirror data (partner-reported) for countries that do not report | Built with trade_products.json by `build_indicators.py --trade` (workflow `refresh_trade.yml`). The Trade slide shows a "UAE" line from it |
| `environment.json` | Yale EPI 2026 + WorldRiskReport 2025 | One-off download |
| `governance.json` | Fragile States Index (The Fund for Peace, 2024 edition, 0–120, 179 countries) and Corruption Perceptions Index (Transparency International, 2025 edition, 0–100, 182 countries): score + rank per ISO3, with `_meta` (publisher, edition, scale, URL, licence) | **Manual, once a year.** FSI: the official spreadsheet download stops at 2023, so the 2024 scores were transcribed (via the Wikipedia table that copies FFP’s Global Data) and spot-checked against FFP figures; CPI: `CPI2025_Results.xlsx` from transparency.org (CC BY-ND — show scores unchanged, with attribution). Read by `govData()` (ids `GOV_FSI`, `GOV_CPI`; severity rules in `severity.js`). Shown with WGI political stability, government effectiveness and rule of law in the report’s slide-2 “Political situation” panel and the drawer overview |
| `trade_barriers.json` | Trade Barrier Index 2025 (Tholos Foundation, tradebarrierindex.org; 0–10, higher = more barriers, 122 countries — 68 of ours) per ISO3: `tbi`/`tariffs`/`ntb`/`services`/`facilitation` = [score, global rank], `sub` sub-scores, `prev` earlier editions. Scraped from the country pages (no download); refresh by hand when a new edition is out. Used on the report Trade slide (card, "Barriers to trade" insight, interventions when a pillar ranks 82nd or worse) |
| `uis.json` | UNESCO UIS: out-of-school, school basic services, trained teachers | `build_indicators.py` (`build_uis`), monthly |
| `sme_jobs.json` | ILOSTAT "Employment by sex and establishment size" (labour force surveys): share of workers in businesses under 50 workers, by size band; only countries where size is known for ≥ 50% of workers (67) | `build_indicators.py` (`build_sme_jobs`), with the monthly refresh; keeps the previous file if ILO is unreachable. ILO bands stop at 50+, so medium firms (50–249) are counted with large |
| `trade_products.json` | UN Comtrade public API: each country's goods exports and imports by HS chapter (top 6 with % share, plus food / fuel / mining shares), latest complete year | `build_indicators.py --trade` (`build_trade_data`), its own monthly workflow `refresh_trade.yml` (can take hours; saves progress every 10 countries), paced ~1 request per 2 s; countries that fail keep their previous entry. Short names for HS chapters: `docs/hs_labels.js` (`HS2`, English + Arabic). Used in the Trade slide's "Main products traded" insight |
| `power_mix.json` | Ember yearly electricity data via Our World in Data: share of generation by source (solar, wind, hydro, geothermal & other, bioenergy, gas, coal, oil, nuclear), latest year | `build_indicators.py` (`build_power_mix`), monthly. Used on the report's Energy slide |
| `leader_terms.json` | Researched (web, with a source URL per entry), as of 2026-10-14: year in office, term length, year the current term ends | Manual — **review after elections / changes of government**. Reconciled with Wikidata in `applyLeaderTerms`: same person → term added; different people → whichever reports the more recent start in office wins; Wikidata empty → table fills in |
| `subnational/{ISO3}.json` + `index.json` | DHS Program regional survey data and outlines (30 countries pre-downloaded) | One-off download. Countries not in index.json are looked up live from the DHS API (down at times since 2025) |

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
| 1 | `executive` | `view-executive` | **Landing page.** "Countries at a Glance": KPIs (countries, low-income, population, no electricity, no basic water, reports saved), need-index mini map, regions, recent reports |
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
- Indicators with no data are **left off** slides (no "—" cards, no empty facts). Outdated figures (older than `DK.STALE_YEARS`) are left off too. Where ≥ 2 are missing or outdated, a short "Limited data" note names them.
- Stat cards carry the benchmark and gap (`gap()`: points for shares of people and 0–100 scores, relative % for % of GDP, × for higher-is-worse). There are no separate benchmark charts.
- Key insights explain the "so what": `WHY[id]` lists linked indicators (only named when they are also off track in that country's data, via `DP` phrases) plus what the gap means. Add new indicators to `WHY`/`DP` in both languages.
- Interventions: `acts` (aid, triggered by off-track indicators, or by a condition function such as `fossilHeavy`) + `inv` (development-investment angle, e.g. offtake agreements for agriculture, renewable IPPs for fossil-heavy grids), shown only when its condition holds. `fossilHeavy` = renewables < 40% of final energy use and electricity access ≥ 70% (the renewables share counts firewood, so low-access countries are excluded).
- Executive summary = overall picture + priority-sector columns, each with its most urgent gaps, people affected (`people()`) and "why it matters". No strengths or data-notes blocks.
- Overview slide: report map names neighbouring countries (`mapNameCountries`, Arabic via `AR_NE_NAME` in `i18n_ar.js`); leaders show term years (`hosSince/hosUntil`, `hogSince/hogUntil` from Wikidata P580/P582); governance bars have a severity colour key and a referenced footnote under the map (`WGI_DEF`: source, year and a definition of each indicator shown); status by sector spans the full width.
- **The need index is dashboard-only (since 2026-11-24): no report shows it.** Country deck: no need box, summary sentence or footnote (`n = null`). Regional deck: map shaded by World Bank income group (`incomeShades`), countries in alphabetical order, no ranking slide, table column or profile badge.

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
