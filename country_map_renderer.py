"""
country_map_renderer.py — REAL IMPLEMENTATION (skill-backed)
=============================================================
Adapter around the `country_brief` skill's `render_map()` function.

The skill is shipped as a self-contained folder at:
    country_brief_skill/country-brief/scripts/country_brief/maps.py

It bundles Natural Earth admin0/admin1/capitals parquet files at:
    country_brief_skill/country-brief/assets/geo/{admin0,admin1,capitals}.parquet

This adapter:
  1. Translates our render(country, iso2, ...) contract into the skill's
     fenced-div markdown input format
  2. Calls country_brief.maps.render_map(inner) -> HTML string
  3. Extracts the base64 PNG embedded in the HTML
  4. Returns raw PNG bytes (matches docs/MAP_RENDERER_CONTRACT.md §2)

See docs/MAP_RENDERER_CONTRACT.md for the full interface spec.
"""
from __future__ import annotations
import base64
import re
import sys
from pathlib import Path
from typing import Optional

# ── Add the skill's scripts/ folder to sys.path so we can import it ───────────
_SKILL_ROOT = Path(__file__).parent / "country_brief_skill" / "country-brief"
_SKILL_SCRIPTS = _SKILL_ROOT / "scripts"
if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))


# ─── Indicator priority for choropleth shading (kept for contract parity) ────
RELEVANT_CHOROPLETH_INDICATORS = (
    "EG.ELC.ACCS.ZS",
    "SH.DYN.MORT",
    "SI.POV.DDAY",
    "SH.STA.STNT.ZS",
    "SE.ADT.LITR.ZS",
    "SH.H2O.SMDW.ZS",
)


def best_choropleth_indicator(indicators: Optional[dict]) -> Optional[str]:
    """Pick the WDI code most useful for shading given what's available."""
    if not indicators:
        return None
    for code in RELEVANT_CHOROPLETH_INDICATORS:
        rec = indicators.get(code)
        if rec and rec.get("value") is not None:
            return code
    return None


# ── Map this project's "severity" scale to the skill's category names ────────
# Skill expects categories per the color-scale chosen:
#   severity:  escalating | re-escalating | high | stable | improving
#   electoral: government | opposition | contested | swing | abstain
#   verdict:   ready | conditional | not-ready | unclear
# We default to "severity" since it's the most general.
_SEVERITY_DEFAULT_CATEGORY = "stable"


def _value_to_severity_category(value, indicator_code: str) -> str:
    """Map an indicator value to a severity category for choropleth shading."""
    inv = indicator_code in ("SH.DYN.MORT", "SI.POV.DDAY", "SH.STA.STNT.ZS")
    if value is None:
        return _SEVERITY_DEFAULT_CATEGORY
    try:
        v = float(value)
    except (TypeError, ValueError):
        return _SEVERITY_DEFAULT_CATEGORY
    if inv:
        # Higher = worse
        if v >= 50:  return "escalating"
        if v >= 30:  return "re-escalating"
        if v >= 20:  return "high"
        if v >= 10:  return "stable"
        return "improving"
    # Higher = better
    if v >= 80:  return "improving"
    if v >= 60:  return "stable"
    if v >= 40:  return "high"
    if v >= 20:  return "re-escalating"
    return "escalating"


def _build_fenced_div(
    country: str,
    *,
    type: str = "reference",
    indicators: Optional[dict] = None,
    subnational_indicators: Optional[dict] = None,
    color_scale: str = "severity",
    show_neighbors: bool = True,
    title: str = "",
    source: str = "",
) -> str:
    """Build the ::: map fenced-div input string for the skill."""
    lines = [
        f"type: {type}",
        f"country: {country}",
        f"color-scale: {color_scale}",
        f"show-neighbors: {'true' if show_neighbors else 'false'}",
    ]
    if title:
        lines.append(f"title: {title}")
    if source:
        lines.append(f"source: {source}")

    # If we have sub-national data, emit one `region:` line per region
    if subnational_indicators:
        for region, data in subnational_indicators.items():
            if isinstance(data, dict):
                category = (data.get("category")
                            or data.get("severity")
                            or data.get("status"))
                if not category:
                    code = next(iter(data.keys()), None)
                    if code and isinstance(data[code], (int, float)):
                        category = _value_to_severity_category(data[code], code or "")
                    else:
                        category = _SEVERITY_DEFAULT_CATEGORY
            else:
                category = str(data) or _SEVERITY_DEFAULT_CATEGORY
            lines.append(f"region: {region} | {category}")

    return "\n".join(lines)


def _extract_png_from_html(html: str) -> Optional[bytes]:
    """Pull the base64 PNG out of the skill's HTML output and decode it."""
    m = re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', html)
    if not m:
        return None
    try:
        return base64.b64decode(m.group(1))
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point — satisfies docs/MAP_RENDERER_CONTRACT.md §2
# ═══════════════════════════════════════════════════════════════════════════════

def render(
    country: str,
    iso2: str,
    lat: float,
    lng: float,
    *,
    type: str = "reference",
    indicators: Optional[dict] = None,
    subnational_indicators: Optional[dict] = None,
    color_scale: str = "severity",
    show_neighbors: bool = True,
    width: int = 1200,
    height: int = 800,
) -> Optional[bytes]:
    """Render a country map as PNG bytes. Returns None on failure.

    Delegates to the country_brief skill's render_map(). Lat/lng/width/height
    are ignored by the skill (it auto-fits the country bounding box from the
    Natural Earth admin1 dataset).
    """
    try:
        from country_brief.maps import render_map
    except ImportError as e:
        print(f"[country_map_renderer] skill not available: {e}")
        return None
    except Exception as e:
        builtins_type = __builtins__['type'] if isinstance(__builtins__, dict) else __builtins__.type
        print(f"[country_map_renderer] skill import failed: {builtins_type(e).__name__}: {e}")
        return None

    # Build the fenced-div input
    inner = _build_fenced_div(
        country=country,
        type=type,
        indicators=indicators,
        subnational_indicators=subnational_indicators,
        color_scale=color_scale,
        show_neighbors=show_neighbors,
        title=f"{country} — Country Overview",
        source="World Bank WDI; Natural Earth boundaries",
    )

    try:
        html = render_map(inner)
    except Exception as e:
        import builtins
        print(f"[country_map_renderer] render_map() crashed: {builtins.type(e).__name__}: {e}")
        return None

    # Detect skill-side errors (rendered as <div class="map-error">...)
    if 'class="map-error"' in html:
        em = re.search(r'<div class="map-error">(.*?)</div>',
                       html, flags=re.DOTALL)
        msg = re.sub(r'<[^>]+>', ' ', em.group(1)).strip() if em else "unknown error"
        print(f"[country_map_renderer] skill returned error: {msg[:200]}")
        return None

    png = _extract_png_from_html(html)
    if png is None:
        print("[country_map_renderer] could not extract PNG from skill HTML")
        return None
    return png
