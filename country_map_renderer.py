"""
country_map_renderer.py — REAL IMPLEMENTATION
==============================================
GeoPandas + matplotlib + Natural Earth 1:110m.
See docs/MAP_RENDERER_CONTRACT.md for the contract this module satisfies.

Returns PNG bytes for a given country at the requested size.
Falls back gracefully (returns None) on any failure.

Build deps (in requirements.txt):
    geopandas>=0.14
    matplotlib>=3.8
    shapely>=2.0
    pyproj>=3.6
    pyogrio>=0.7

Build data:
    map_data/ne_110m_admin_0_countries.{shp,shx,dbf,prj,cpg}
    (Natural Earth 1:110m countries — ~215 KB total)
"""
from __future__ import annotations
import io
from pathlib import Path
from typing import Optional

# Lazy imports — kept inside the body so a missing dep returns None
# from render() rather than crashing the whole webhook module on import.
_DEPS_OK = None
def _ensure_deps():
    global _DEPS_OK
    if _DEPS_OK is None:
        try:
            import geopandas  # noqa
            import matplotlib  # noqa
            matplotlib.use('Agg')   # headless backend (no display)
            import shapely  # noqa
            _DEPS_OK = True
        except ImportError:
            _DEPS_OK = False
    return _DEPS_OK


# ─── Data location ────────────────────────────────────────────────────────────
DATA_DIR  = Path(__file__).parent / "map_data"
SHAPEFILE = DATA_DIR / "ne_110m_admin_0_countries.shp"

_WORLD = None
def _load_world():
    """Read the Natural Earth shapefile once and cache it."""
    global _WORLD
    if _WORLD is not None:
        return _WORLD
    if not SHAPEFILE.exists():
        return None
    import geopandas as gpd
    _WORLD = gpd.read_file(SHAPEFILE)
    return _WORLD


# ─── CAD palette (matches country_ppt_builder.py + dashboard) ────────────────
NAVY      = '#333F64'
GOLD      = '#AD833B'
GOLD_LT   = '#C7A877'
BLUE      = '#678CA5'
CREAM     = '#F4F1EA'
WATER     = '#D8E7F0'
LAND      = '#E8E2D2'
LAND_EDGE = '#C9C0AC'
NEG       = '#9B120B'
NEUTRAL   = '#F39B26'
SEMI_NEG  = '#BA492F'
SEMI_POS  = '#9CBB5D'
POS       = '#00BC8B'
FG        = '#1C2433'
FG2       = '#5B6A7E'


# ─── Indicator priority for choropleth shading ───────────────────────────────
RELEVANT_CHOROPLETH_INDICATORS = (
    "EG.ELC.ACCS.ZS",
    "SH.DYN.MORT",
    "SI.POV.DDAY",
    "SH.STA.STNT.ZS",
    "SE.ADT.LITR.ZS",
    "SH.H2O.SMDW.ZS",
)

def best_choropleth_indicator(indicators: Optional[dict]) -> Optional[str]:
    if not indicators:
        return None
    for code in RELEVANT_CHOROPLETH_INDICATORS:
        rec = indicators.get(code)
        if rec and rec.get("value") is not None:
            return code
    return None


# Inverse-good indicators (lower value = better)
_INVERSE = {"SH.DYN.MORT", "SI.POV.DDAY", "SH.STA.STNT.ZS"}

def _severity_color(value: float, code: str) -> str:
    """Map a value to one of the 5 severity colours given indicator direction."""
    if value is None:
        return GOLD
    inv = code in _INVERSE
    if inv:
        # higher = worse
        if value >= 50: return NEG
        if value >= 30: return SEMI_NEG
        if value >= 20: return NEUTRAL
        if value >= 10: return SEMI_POS
        return POS
    # higher = better
    if value >= 80: return POS
    if value >= 60: return SEMI_POS
    if value >= 40: return NEUTRAL
    if value >= 20: return SEMI_NEG
    return NEG


# ─── Lookup helpers ──────────────────────────────────────────────────────────
def _find_country(world, country: str, iso2: str):
    """Return GeoDataFrame row(s) for the target country."""
    if iso2:
        m = world[world['ISO_A2'].str.upper() == iso2.upper()]
        if not m.empty:
            return m
        m = world[world['ISO_A2_EH'].str.upper() == iso2.upper()] if 'ISO_A2_EH' in world.columns else None
        if m is not None and not m.empty:
            return m
    if country:
        m = world[world['NAME'].str.lower() == country.lower()]
        if not m.empty:
            return m
        m = world[world['NAME_LONG'].str.lower() == country.lower()] if 'NAME_LONG' in world.columns else None
        if m is not None and not m.empty:
            return m
        m = world[world['SOVEREIGNT'].str.lower() == country.lower()] if 'SOVEREIGNT' in world.columns else None
        if m is not None and not m.empty:
            return m
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
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
    """Render a country map as PNG bytes. Returns None on failure."""
    if not _ensure_deps():
        return None
    world = _load_world()
    if world is None:
        return None
    try:
        import geopandas as gpd
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from shapely.geometry import box

        target = _find_country(world, country, iso2)
        if target is None or target.empty:
            return None

        # Country bounding box + 40% padding for context
        minx, miny, maxx, maxy = target.total_bounds
        span_x = maxx - minx
        span_y = maxy - miny
        # Use the larger span to keep aspect roughly preserved
        pad_x = max(span_x * 0.45, span_y * 0.45 * (width / height))
        pad_y = max(span_y * 0.45, span_x * 0.45 * (height / width))
        view_minx = minx - pad_x
        view_maxx = maxx + pad_x
        view_miny = miny - pad_y
        view_maxy = maxy + pad_y

        # Neighbors = intersect padded bbox
        if show_neighbors:
            bbox = box(view_minx, view_miny, view_maxx, view_maxy)
            neighbors = world[world.geometry.intersects(bbox)]
            neighbors = neighbors[~neighbors.index.isin(target.index)]
        else:
            neighbors = world.iloc[0:0]

        # Pick country fill colour
        fill_color = GOLD
        indicator_label = None
        if type == "choropleth" and indicators:
            code = best_choropleth_indicator(indicators)
            if code:
                rec = indicators.get(code) or {}
                val = rec.get("value")
                fill_color = _severity_color(val, code)
                indicator_label = (
                    f"{_human_label(code)}: {val:.1f}{_unit(code)} "
                    f"({rec.get('year','')})"
                )

        # ─── Draw ───
        dpi = 100
        fig, ax = plt.subplots(figsize=(width/dpi, height/dpi), dpi=dpi)
        ax.set_facecolor(WATER)

        # Neighbours
        if not neighbors.empty:
            neighbors.plot(ax=ax, color=LAND, edgecolor=LAND_EDGE, linewidth=0.6)

        # Target country
        target.plot(ax=ax, color=fill_color, edgecolor=NAVY, linewidth=2.0)

        # Country label
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        ax.text(cx, cy, country.upper(),
                fontsize=22, fontweight='bold', color='white',
                ha='center', va='center',
                path_effects=_text_outline(),
                zorder=5)

        # Capital marker
        if lat is not None and lng is not None:
            ax.plot(lng, lat, 'o', markersize=18,
                    markerfacecolor='white', markeredgecolor=NEG,
                    markeredgewidth=2.5, zorder=10)
            ax.plot(lng, lat, 'o', markersize=8,
                    markerfacecolor=NEG, markeredgecolor='none',
                    zorder=11)
            # Caption to the right of the marker
            offset = span_x * 0.025
            ax.text(lng + offset, lat,
                    'CAPITAL',
                    fontsize=10, fontweight='bold', color=NAVY,
                    va='center', zorder=12)

        # Neighbour labels (sovereignty names, only those whose centroid is in view)
        if not neighbors.empty:
            for _, row in neighbors.iterrows():
                c = row.geometry.representative_point()
                if view_minx < c.x < view_maxx and view_miny < c.y < view_maxy:
                    name = row.get('NAME') or row.get('NAME_LONG') or ''
                    if name and name != country:
                        ax.text(c.x, c.y, name.upper(),
                                fontsize=8, color=FG2, ha='center', va='center',
                                style='italic')

        # Frame
        ax.set_xlim(view_minx, view_maxx)
        ax.set_ylim(view_miny, view_maxy)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(GOLD_LT)
            spine.set_linewidth(1.5)

        # Title strip
        title = f"{country}"
        if indicator_label:
            title = f"{country}  ·  {indicator_label}"
        fig.suptitle(title, fontsize=16, fontweight='bold',
                     color=NAVY, y=0.96, x=0.05, ha='left')

        # Subtitle
        sub = "Reference map" if type == "reference" else "Indicator map"
        fig.text(0.05, 0.92, sub.upper(),
                 fontsize=9, color=GOLD, fontweight='bold')

        # Source footer
        fig.text(0.05, 0.04,
                 "Source: Natural Earth 1:110m  ·  World Bank WDI",
                 fontsize=8, color=FG2, style='italic')

        # Save
        buf = io.BytesIO()
        plt.savefig(buf, format='PNG', bbox_inches='tight',
                    facecolor=CREAM, dpi=dpi)
        plt.close(fig)
        return buf.getvalue()
    except Exception as e:
        # NOTE: `type` is shadowed by the parameter, use builtins.type
        import builtins
        print(f"[country_map_renderer] error: {builtins.type(e).__name__}: {e}")
        return None


# ─── Helpers ─────────────────────────────────────────────────────────────────

_LABELS = {
    "EG.ELC.ACCS.ZS":  "Electricity access",
    "SH.DYN.MORT":     "U5 mortality (per 1k)",
    "SI.POV.DDAY":     "Poverty <$2.15",
    "SH.STA.STNT.ZS":  "Stunting under-5",
    "SE.ADT.LITR.ZS":  "Adult literacy",
    "SH.H2O.SMDW.ZS":  "Safely managed water",
}
_UNITS = {
    "SH.DYN.MORT": "",
}

def _human_label(code):
    return _LABELS.get(code, code)

def _unit(code):
    return _UNITS.get(code, "%")


def _text_outline():
    """Return matplotlib path-effects giving white text a dark outline."""
    try:
        from matplotlib import patheffects as pe
        return [pe.Stroke(linewidth=3, foreground='black', alpha=0.5),
                pe.Normal()]
    except Exception:
        return []
