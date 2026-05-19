# Country Assessment Dashboard

## Project Overview
Single-file HTML/CSS/JS dashboard for managing international development program requests. No build system, no dependencies beyond CDN libraries.

## Files
- `index.html` — the entire application (~8,200+ lines of HTML + CSS + JS)
- `logo.png` — Office of Development Affairs bilingual logo (displayed in top header bar)
- `somaliland-flag.svg` — custom local flag for Somaliland (not on flagcdn.com)

## Architecture
- **No framework** — vanilla JS, DOM manipulation only
- **Leaflet.js 1.9.4** — interactive map (main map + per-project minimap, both CDN)
- **pptxgenjs 3.12.0** — PPT export for country profile reports (CDN)
- **html2canvas 1.4.1** — captures Leaflet map as JPEG for PPT slides 1 & 2 (loaded dynamically)
- **Google Fonts** — Inter (English only; bilingual toggle removed)
- **World Bank Open Data API** — live indicator data per country, cached in `countryDataCache`
- **flagcdn.com** — `https://flagcdn.com/w20/{iso2}.png` country flag images; overridden by `CUSTOM_FLAGS` for countries not on CDN
- **No backend** — all data hardcoded in JS; new requests pushed into live `requests` array at runtime

---

## Layout
```
[App Header 56px — logo.png | "Country Assessment Dashboard"]
[Sidebar 60px] [Pipeline Panel 360px, conditional] [Main Content flex:1]
```

### Header
- Left: `logo.png` image
- Right of logo: fixed text **"Country Assessment Dashboard"** separated by a vertical divider
- The `.sb-logo` CAD badge is hidden (`display:none`)

### Sidebar nav icons (top to bottom)
1. **Overview** (home/grid) — `view-overview`
2. **Pipeline** (list) — `view-pipeline`
3. **Analytics** (bar chart) — `view-analytics`
4. **Settings** (gear) — `view-settings`
5. **Documents** (folder+) — `view-documents` *(separated by divider)*

### Views
| ID | Content |
|---|---|
| `view-overview` | KPI cards + sector breakdown + recent activity |
| `view-pipeline` | Stats bar + Leaflet map + slide-up country drawer |
| `view-analytics` | KPI cards + 5 chart panels |
| `view-settings` | Sub-nav: General / Pipeline / Notifications / Export |
| `view-project` | Project detail: minimap + details grid + timeline + notes |
| `view-documents` | Tree (continent → country → year → folder) + file list |

---

## Paths (2 only — Path A removed)
| Key | Display Name |
|---|---|
| `B` | Sector Assessment |
| `C` | Program Evaluation |

---

## Pipeline Steps (6 stages, 0-indexed)
```
0·Intake → 1·Country Analysis → 2·Program Dev → 3·Stakeholder Eng. → 4·Leadership Review → 5·Approved
```
- Completion % = `Math.round(r.status / 5 * 100)`
- **Approved step** displays as teal/done (green ✓), not maroon

### Status groupings (used for cards, filters, budget bars)
| Group | Status values | Colour |
|---|---|---|
| In Development | 0–2 | Navy |
| Pending Review | 3–4 | Maroon |
| Approved | 5 | Teal |
| Paused | substatus='paused' | Slate |
| Cancelled | substatus='cancelled' | Maroon |

### Substatus icons
- **Paused**: `&#10074;&#10074;` (❚❚) — two slim vertical bars
- **Cancelled**: `&#10005;` (✕) — X mark
- Both icons appear in: timeline dot, substatus banner, status pills, Pause/Cancel buttons

### `cardStatusPill(r)` helper
Returns `{cls, label}` for any request — used on pipeline cards, project hero, and country program cards.

---

## Colour Tokens
| Token | Value | Usage |
|---|---|---|
| `--accent` | `#2D3F7B` | Navy — buttons, active states |
| `--teal` | `#2DB88A` | Done / approved / teal states |
| `--maroon` | `#9B120B` | Pending review / evaluation / current step / all former amber |
| `--maroon-lt` | `#FDECEA` | Maroon backgrounds |
| `--crimson` | `#E04444` | Error states |

**Amber (`--amber: #F59E0B`) is no longer used in any active UI** — all former amber elements now use `--maroon`.

---

## Country Registry
All four registries must be updated together when adding a new country:

| Object | Purpose |
|---|---|
| `COUNTRY_LATLNG` | Map centroid `[lat, lng]` |
| `COUNTRY_ISO2` | ISO2 code for flagcdn.com; use `CUSTOM_FLAGS` override if no ISO2 |
| `CONTINENT_MAP` | Continent string for Documents tree |
| `COUNTRY_INFO` | `{ capital, currency, languages }` for PPT export (inside `cd_exportCountryPPT`) |

### Custom flag overrides
```js
const CUSTOM_FLAGS = {
  'Somaliland': 'somaliland-flag.svg'   // local SVG, not on flagcdn.com
};
```
`flagImg()` checks `CUSTOM_FLAGS[country]` before falling back to flagcdn.com. Pipeline card inline flag rendering and PPT export also check `CUSTOM_FLAGS`.

---

## Data Objects

```js
// Core request record
{ id, titleEn, titleAr, country, countryAr, path, sector, sectorAr,
  status, substatus, reviewed, engaged, date, cost, lead, lat, lng }
// status: 0=Intake … 5=Approved
// substatus: null | 'paused' | 'cancelled'
// path: 'B' | 'C' only (Path A removed)

// Request metadata
requestMeta[id] = {
  impact, beneficiaries, duration,
  implementor, implName, implNameAr,
  history:    [{from, to, date}],          // status change log
  notes:      [{id, text, date}],          // free-text notes
  evalAreas:  ['Impact potential', ...],   // Path C only — checked criteria labels
  evalScores: [{area, score, rating}]      // Path C only — computed WB-data scores
}

// Country programs (static)
countryPrograms[countryName] = { existing:[], proposed:[], evaluation:[] }
// Each program: { nameEn, nameAr, type, sector, cost, start, status, path, lead, ben }
// Status displayed via programStatusPill(p) → cardStatusPill grouping

// City-level map coords
cityData[id] = { lat, lng, name, nameAr, zoom }

// Custom flag overrides (countries not on flagcdn.com)
CUSTOM_FLAGS[countryName] = 'relative/path/to/flag.svg'

// ISO2 codes for flag images
COUNTRY_ISO2[countryName] = 'XX'

// Continent mapping (for documents)
CONTINENT_MAP[countryName] = 'Africa' | 'Asia' | 'Americas' | 'Europe' | 'Pacific'

// Country metadata for PPT cover slide
COUNTRY_INFO[countryName] = { capital, currency, languages }

// Live WB data cache
countryDataCache[country][indicatorId] = { value, year } | null

// Documents
docsData    = [{id, country, continent, year, folderId, name, size, type, uploadedAt, dataUrl}]
docsFolders = [{id, name, country, continent, year, createdAt}]
```

---

## Runtime State Variables
| Variable | Purpose |
|---|---|
| `activeFilter` | Current pipeline filter chip ('all','B','C','review','active') |
| `mapFilterSector` | Active sector map filter |
| `mapFilterRegion` | Active country map filter (despite name, filters by country) |
| `searchQuery` | Live pipeline search string |
| `selectedRequest` | Currently open project object |
| `map` | Leaflet main map instance |
| `projMiniMap` | Current project minimap |
| `mapMarkers` | `{ country: { marker, el } }` |
| `mapInitialized` | Guards map re-init |
| `cdCountry` | Country currently shown in drawer |
| `cdActiveTab` | Active drawer tab |
| `cardFilter` | Active program filter in drawer ('all','in-development','pending-review','approved','paused','cancelled') |
| `docsTreeSel` | `{continent, country, year}` tree selection |
| `docsViewFolder` | Current open folder id (null = root) |
| `intakePath` | Selected path in intake form ('B' or 'C') |
| `pendingNewRequest` | Form data between analysis overlay and pipeline add |

---

## Key JS Functions

### Navigation
| Function | Purpose |
|---|---|
| `switchView(view, navEl)` | Activates a view; calls renderOverview/renderAnalytics/renderSettings/renderDocuments as needed |
| `openProject(id)` | Opens project detail view |
| `closeProject()` | Returns to pipeline |
| `openCountryProfile(countryEn)` | Opens country drawer from project hero flag link |
| `flagImg(country, w, h)` | Returns `<img>` flag HTML — checks CUSTOM_FLAGS first, then COUNTRY_ISO2/flagcdn |
| `cardStatusPill(r)` | Returns `{cls, label}` for grouped status display |
| `programStatusPill(p)` | Maps country program to grouped status (uses cardStatusPill for linked requests) |

### Pipeline
| Function | Purpose |
|---|---|
| `renderPipeline()` | Renders filtered+searched list; calls renderStatsBar + renderBudgetBars + populateSectorFilter |
| `renderStatsBar()` | Updates 6 stat numbers from live `requests` array |
| `renderBudgetBars()` | Updates 3 budget bar widgets |
| `setFilter(f, el)` | Sets activeFilter chip; calls renderPipeline + applyMapFilters |
| `setMapFilter(type, sel)` | Sets sector/country map filter; calls renderPipeline + applyMapFilters |
| `applyMapFilters()` | Fades non-matching map dots to 12% opacity |
| `populateSectorFilter()` | Populates both sector and country selects dynamically from requests |
| `onSearchInput(val)` | Sets searchQuery; calls renderPipeline |
| `clearSearch()` | Clears search input and query |
| `exportPipelineCSV()` | Exports filtered pipeline as pipeline_export.csv |

### Project Detail
| Function | Purpose |
|---|---|
| `renderProjectDetail()` | Renders hero, minimap, details grid, timeline, history, notes |
| `setRequestStatus(id, n)` | Advances/rolls back status; records in history; re-renders |
| `toggleSubstatus(val)` | Toggles paused/cancelled; records in history |
| `openEditPanel()` | Injects edit form at top of proj-body |
| `saveProjectEdit()` | Saves title/cost/sector/lead/beneficiaries/duration inline |
| `addNote(reqId)` | Adds note to requestMeta[id].notes |
| `deleteNote(reqId, noteId)` | Removes note by id |
| `buildHistoryHtml()` | Builds collapsible change history section |
| `buildNotesHtml()` | Builds notes section with textarea |

### Overview Page
| Function | Purpose |
|---|---|
| `renderOverview()` | Renders KPI row + sector breakdown bars + recent activity feed |

### Country Drawer
| Function | Purpose |
|---|---|
| `openCountryDrawer(country)` | Opens drawer; loads WB data; renders active tab |
| `cdSwitchTab(tab, btn)` | Switches tab: overview / indicators / programs / documents |
| `cdRenderPrograms()` | Renders status-grouped filter chips + program cards |
| `cdFilterPrograms(f, btn)` | Filters by: all / in-development / pending-review / approved / paused / cancelled |
| `cdBuildProgramCards()` | Renders cards with status-grouped label, bar colour, and pill |
| `cd_exportCountryPPT(country)` | Builds 12-slide country PPT |
| `cdRenderDocs()` | Renders Documents tab with folders + files grouped by year |
| `cdDocsCreateFolder()` | Inline folder creation form in drawer |

### Documents
| Function | Purpose |
|---|---|
| `renderDocuments()` | Renders tree + list |
| `docsRefreshAll()` | Calls both `renderDocuments()` + `cdRenderDocs()` — always use after any doc/folder mutation |
| `docsSelectNode(el)` | Selects tree node via data-* attributes |
| `docsCreateFolder()` | Inline folder form in main view |
| `docsConfirmFolder()` | Creates folder; calls docsRefreshAll() |
| `docsDeleteFolder(id)` | Removes folder; moves files to root; calls docsRefreshAll() |
| `docsOpenFolder(id)` | Navigates into folder |
| `docsHandleFiles(input)` | Reads files; stores with folderId; calls docsRefreshAll() |
| `docsDownload(id)` | Triggers file download from dataUrl |
| `docsDelete(id)` | Removes file; calls docsRefreshAll() |

### Intake Form & Analysis
| Function | Purpose |
|---|---|
| `intake_selectPath(p)` | Selects path B or C — iterates `['B','C']` only (A removed) |
| `imEntityChange(sel)` | Shows/hides free-text input when Entity = "Other" |
| `im_submit()` | Validates form; collects formData incl. evalAreas, progben, duration; calls runAnalysis |
| `runAnalysis(formData)` | Animates analysis overlay steps; on completion calls computeEvalScores (Path C) |
| `computeEvalScores(formData, cacheData)` | Scores each checked evalArea using live WB indicators; returns `[{area, score, rating, color, bg, rationale}]` |
| `addToNewPipeline()` | Creates request + requestMeta (incl. evalAreas, evalScores) + cityData; opens project |

---

## Intake Form — Entity Section
**Section 2 — Requesting Entity** fields:
- **Target country** (required select)
- **Entity** (required select): Erth Zayed Philanthropies / UAE Aid Agency / Other
  - Selecting "Other" reveals a free-text input (`im-entity-other`) below the dropdown
- **Primary contact** (optional text)
- **Contact phone** (optional text)
- **Contact email** (optional email)

---

## Program Evaluation Scoring (Path C)
`computeEvalScores()` runs after the analysis animation using `countryDataCache[country]`.

| Criterion | World Bank indicators used |
|---|---|
| Impact potential | SI.POV.DDAY (poverty), NY.GDP.PCAP.PP.CD (GDP/cap), SH.DYN.MORT (child mortality) |
| Cost-effectiveness | Budget ÷ stated beneficiaries ratio, NY.GDP.PCAP.PP.CD, FP.CPI.TOTL.ZG (inflation) |
| Feasibility | SE.ADT.LITR.ZS (literacy), EG.ELC.ACCS.ZS (electricity), NY.GDP.MKTP.KD.ZG (growth), inflation |
| Strategic alignment | Sector-matched indicator (health→mortality, education→literacy gap, WASH→water gap, etc.) + poverty |
| Sustainability | Literacy, GDP growth, electricity access, SI.POV.GINI (Gini index) |

Scores (0–100) map to: **Strong** (≥75) · **Good** (≥55) · **Moderate** (≥35) · **Weak** (<35)

Scores are stored in `requestMeta[id].evalScores` and rendered as progress bars on the project detail card.

---

## Pipeline Card Layout
```
[impl logo corner — top right]
[Request name  (padding-right:30px)]
[Flag+Country · Cost]
[6-segment stepper (teal=done, maroon=current, grey=future)]
[X% complete]
[Status pill (In Development / Pending Review / Approved / ❚❚ Paused / ✕ Cancelled)]
[L-dot  S-dot  Date]
```

---

## Project Detail Timeline
- **Click any step dot** to advance or roll back status
- **Next step**: dashed navy border — hover fills solid navy
- **Done steps**: teal ✓ — hover shows roll-back affordance
- **Approved step**: always renders as teal/done (not maroon)
- **Pause / Cancel buttons** in timeline header; clicking again resumes/reactivates
- Banner appears below timeline when paused/cancelled
- Status changes are recorded in `requestMeta[id].history`

---

## Pipeline Filters
**Status chips** (in panel header):
All · Sector Assessment · Program Evaluation · Review · Approved

**Map filter row** (below chips):
- Sector dropdown (dynamic from requests)
- Country dropdown (dynamic from requests)

When any filter is active, non-matching country dots fade to 12% opacity. Filters affect both the list and the map simultaneously.

---

## Country Drawer Program Cards
Filter chips: **All · In Development · Pending Review · Approved · Paused · Cancelled**

Card header label = status group (e.g. "In Development" in navy). Top bar colour matches the group. For cards linked to a pipeline request via `programToReqId`, the live request status drives the pill.

---

## Documents Feature
- **Main view**: tree (Continent → Country → Year → Folders → Files)
- **Drawer**: Documents tab on country profile; year selector + New Folder + Upload
- **Sync**: all mutations call `docsRefreshAll()` — both views always stay in sync regardless of which one triggered the change
- **Folder creation**: inline text input (no browser prompt); Enter confirms, Escape cancels
- **Persistence**: file metadata in `localStorage` (`ph_docs_meta`, `ph_docs_folders`); `dataUrl` is session-only
- Accepted types: PDF, DOC/X, XLS/X, PPT/X, TXT, CSV, ZIP

---

## Overview Page
Rendered by `renderOverview()`. Shows:
1. **6 KPI cards**: Total · In Development · Pending Review · Approved · Countries · Pipeline Value
2. **Sector Breakdown**: CSS horizontal bars, count per sector
3. **Recent Activity**: last 8 history entries across all requests (sorted desc), with `relTime()` labels

---

## Analytics Page (5 panels)
1. **Requests by Path** — B/C rows with count + fill bar
2. **Pipeline Completion** — SVG ring + per-project bars + days-in-stage
3. **Pending Stakeholder Response** — clickable list
4. **Pending Leadership Approval** — clickable list
5. **Submissions by Month** — full-width CSS bar chart grouped by `r.date` month

---

## PPT Export — Country Report (12 slides)
Triggered by **Export Report** in country drawer. Key features:
- Cover slide: flag image + left navy rail (DAC Class, Capital, GNI/cap, Currency, Languages) + 3-col snapshot + map + sector status
- Slides 1–2: Leaflet map capture (html2canvas, 6s timeout)
- Sector slides: benchmark bar charts (no maps on sector slides)
- Slide 11: Pipeline table — Sector · Project Name · Path · Status · Cost · Impact · Implementor
- All async calls have timeouts (flag: 4s, map: 6s, WB indicator: 8s, total: 10s)
- Custom flags fetched from local path (e.g. `somaliland-flag.svg`) instead of flagcdn.com

---

## Map
- `COUNTRY_LATLNG` — centroids for 80+ countries including Somaliland `[9.8, 44.0]`; all plotted at startup
- Dot states: grey (catalogue) · navy (pipeline) · teal (approved) · gold (selected)
- Clicks use `el.addEventListener('click')` on pin div (not `marker.on('click')`)
- `#map` CSS: `position:absolute; inset:0`
- `safeInitMap()`: 250ms setTimeout delay

---

## What NOT to do
- Do not use Path A — only B and C are valid for new requests
- Do not add amber colour for evaluation/pending review — use `--maroon`
- Do not use `&#9646;&#9646;` for pause — use `&#10074;&#10074;` (❚❚)
- Do not split into multiple files without a build step
- Do not call `L.map()` before `safeInitMap()`
- Do not call `map.invalidateSize()` without `if (map)` guard
- Do not add sidebar icons without a wired view
- Do not modify `requests` directly outside `addToNewPipeline()` — always add metadata + cityData
- Do not use `prompt()` for user input — use inline forms
- Do not hardcode stats bar numbers — always recalculate via `renderStatsBar()`
- Do not call `renderDocuments()` or `cdRenderDocs()` individually after doc mutations — always use `docsRefreshAll()`
- Do not iterate `['A','B','C']` in intake path logic — Path A elements do not exist in the DOM
- Do not add Country Analysis or Country Portfolio to project detail — these are in the country drawer only
