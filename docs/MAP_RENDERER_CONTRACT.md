# Map Renderer — Integration Contract

This document describes the interface between the **CAD pipeline** (this repo) and
the **map-rendering skill** being implemented Cowork-side. CAD owns the contract;
Cowork owns the implementation. Either side can be updated independently as long
as this contract holds.

Last updated: 2026-05-18

---

## 1. Module

```
country_map_renderer.py     ← Cowork-implemented; CAD ships a stub
```

The stub returns `None` for every call. The CAD pipeline imports the module
inside a `try/except ImportError`; if the module is missing or its `render()`
returns `None`, every slide falls back to a coloured-rectangle placeholder.
**No call site crashes when the renderer is unavailable.**

---

## 2. Function signature

```python
def render(
    country: str,                       # "Ethiopia" — must match Natural Earth ADM0NAME
    iso2:    str,                       # "et"
    lat:     float,
    lng:     float,
    *,
    type:                   str  = "reference",   # "reference" | "choropleth"
    indicators:             dict | None = None,   # Schema A indicators (WDI codes)
    subnational_indicators: dict | None = None,   # Region-keyed, Option B
    color_scale:            str  = "severity",    # "severity" | "diverging" | "sequential"
    show_neighbors:         bool = True,
    width:                  int  = 1200,
    height:                 int  = 800,
) -> bytes | None
```

**Returns:** PNG bytes, or `None` on failure / when the requested mode isn't
supported. Builder will `add_picture()` directly — any reasonable PNG size works
(builder scales to fit). Recommended ~1200×800 for the cover map; sector slides
crop the same image so a single map is reused across slides 1, 2, 4, 7, 10.

---

## 3. What CAD passes in

### Schema A → renderer (server-side, inside `/generate-ppt`)

```jsonc
{
  "country":  "Ethiopia",
  "iso2":     "et",
  "lat":      9.145,
  "lng":      40.4897,

  "indicators": {
    "SH.DYN.MORT":       { "value": 47,  "year": 2022 },
    "EG.ELC.ACCS.ZS":    { "value": 55,  "year": 2023 },
    "SI.POV.DDAY":       { "value": 27,  "year": 2023 },
    "NY.GDP.MKTP.KD.ZG": { "value": 7.3, "year": 2024 },
    ...
  },

  "subnational_indicators": {}   // Option B — empty for now
}
```

The renderer's `country_map_renderer.best_choropleth_indicator(indicators)`
helper picks the WDI code most useful for shading from the available set.
Priority list (`RELEVANT_CHOROPLETH_INDICATORS`):

| Code            | Description                          |
|-----------------|--------------------------------------|
| `EG.ELC.ACCS.ZS`| Electricity access (%)               |
| `SH.DYN.MORT`   | Child mortality (per 1,000)          |
| `SI.POV.DDAY`   | Poverty headcount <$2.15/day (%)     |
| `SH.STA.STNT.ZS`| Stunting (%)                          |
| `SE.ADT.LITR.ZS`| Adult literacy (%)                   |
| `SH.H2O.SMDW.ZS`| Safely managed water (%)             |

---

## 4. What the renderer hands back

The PNG bytes returned are injected into the builder context as:

```jsonc
"map": {
  "image_bytes": <PNG bytes>,
  "type":   "reference",
  "title":  "Ethiopia — Development Overview",
  "source": "World Bank WDI; Natural Earth boundaries"
}
```

`country_ppt_builder.py` reads `ctx['map']['image_bytes']` once per slide that
has a map placeholder (slides 1, 2, 4, 7, 10) and calls `add_picture()` instead
of drawing the placeholder rectangle. The builder also accepts a **base64-encoded
string** in `image_bytes` (for JSON transport), decoded automatically via
`_decode_image_bytes()`.

---

## 5. Where the renderer is called

`telegram_webhook.py::generate_ppt` — between context receipt and
`build_ppt()`. Wrapped:

```python
try:
    from country_map_renderer import render as render_map
    png = render_map(country=ctx["country"], iso2=ctx["iso2"],
                     lat=ctx["lat"], lng=ctx["lng"],
                     indicators=ctx.get("indicators"),
                     subnational_indicators=ctx.get("subnational_indicators"))
    if png:
        ctx.setdefault("map", {})["image_bytes"] = png
except ImportError:
    pass            # module not deployed → placeholder
except Exception:
    pass            # runtime error → placeholder
```

Failure is silent (logged only). The PPT always builds.

---

## 6. Modes — Option A vs Option B

### Option A — Reference map (default)
- Country outline + neighbors + capital marker + scale bar
- No regional data required
- Always renderable

### Option B — Choropleth
- Country outline shaded by region/admin-1 polygon
- Requires `subnational_indicators` populated with region-keyed values:

```jsonc
"subnational_indicators": {
  "Tigray":   { "stunting": 42, "u5mr": 58 },
  "Amhara":   { "stunting": 39, "u5mr": 54 },
  "Oromia":   { "stunting": 35, "u5mr": 49 },
  ...
}
```

- Region names must fuzzy-match Natural Earth admin-1 (e.g. ADM1_EN)
- Sources to populate from: OCHA HDX API, ACLED, WHO SCORE
- Sub-national fetch is **not yet implemented** on the CAD side

If `type='choropleth'` is requested but `subnational_indicators` is empty,
fall back to `type='reference'` (do not return None — just downgrade).

---

## 7. Verification agent (Cowork-side, optional)

A Cowork agent may verify Schema A **before** render:

- `country` matches Natural Earth `ADM0NAME` spelling
- If `subnational_indicators` populated: region names fuzzy-match the
  Natural Earth admin-1 names for the country
- Flags mismatches back to CAD pre-PNG so CAD can correct or skip

**The agent does NOT write `::: map` markdown blocks.** That syntax is for the
markdown renderer; the PPT pipeline operates on PNG bytes via
`add_map_placeholder(image_bytes=...)`.

---

## 8. Response headers (debugging)

`/generate-ppt` exposes the renderer status on every successful response:

| Header        | Values                          | Meaning                          |
|---------------|---------------------------------|----------------------------------|
| `X-Map-Status`| `ok` \| `failed` \| `skipped` \| `none` | See below                |
| `X-Map-Bytes` | integer (PNG length)            | Only present when status=`ok`    |

- `ok` — renderer returned PNG bytes, embedded successfully
- `failed` — renderer raised an exception (logged server-side)
- `skipped` — renderer module not installed
- `none` — renderer returned `None` (Option B requested without data, etc.)

These headers are exposed via `Access-Control-Expose-Headers` so the dashboard
console can read them with the response.

---

## 9. Files touched by this contract

| File                        | Role                                            |
|-----------------------------|-------------------------------------------------|
| `country_map_renderer.py`   | Cowork-implemented module (stub in repo)        |
| `country_ppt_builder.py`    | Consumes `ctx['map']['image_bytes']`             |
| `telegram_webhook.py`       | Calls renderer inside `/generate-ppt`           |
| `docs/index.html`           | Schema B carries raw `indicators` + `map` slot  |
| `requirements.txt`          | Cowork adds map dependencies (cartopy, etc.)    |
| `Dockerfile`                | Cowork adds Natural Earth shapefiles + COPY     |

---

## 10. Testing

```bash
# 1. Stub renderer returns None (default state)
python -c "from country_map_renderer import render; print(render('Ethiopia','et',9.1,40.5))"
# -> None

# 2. Builder works with no map
python generate_ethiopia_ppt.py
# -> Ethiopia_brief.pptx with placeholders on 5 map slots

# 3. Builder with injected PNG bytes
python -c "
from country_ppt_builder import build
from generate_ethiopia_ppt import build_context
from PIL import Image; import io
img = Image.new('RGB', (1200, 800), (180, 130, 60))
buf = io.BytesIO(); img.save(buf, 'PNG')
ctx = build_context()
ctx['map'] = {'image_bytes': buf.getvalue(), 'type':'reference'}
build(ctx, 'with_map.pptx')
"

# 4. /generate-ppt end-to-end (Flask test client)
python -c "
import os; os.environ['TELEGRAM_WEBHOOK_SECRET']='test'
import telegram_webhook as tw
from generate_ethiopia_ppt import build_context
r = tw.app.test_client().post('/generate-ppt', json=build_context())
print('status:', r.status_code, 'map-status:', r.headers.get('X-Map-Status'))
"
```

---

## 11. Migration notes

Cowork replaces the body of `country_map_renderer.render()` and adds any
new dependencies to `requirements.txt` + base map data to `Dockerfile`.
**No CAD-side changes required** — the integration point is finalized.
