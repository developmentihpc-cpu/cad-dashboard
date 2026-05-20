"""
maps.py — Geographic map rendering for the ::: map fenced div.

Loads Natural Earth admin0/admin1 boundary parquet files bundled in
assets/geo/, applies region/capital name normalization, and renders
reference or choropleth maps with leader-line label placement.

Depends on geopandas, matplotlib, shapely. No internal package deps.
"""
import base64
import hashlib
import io
import math
import os
import re
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Bundled geo data lives under assets/geo relative to the package.
# We compute the path lazily inside _load_admin_data to avoid forcing
# importers to set up the path before the package can be imported.
_PKG_ROOT = Path(__file__).resolve().parent.parent.parent  # country-brief/
_GEO_DIR = _PKG_ROOT / "assets" / "geo"
_FLAG_DIR = _PKG_ROOT / "assets" / "flags"

# Cache for loaded GeoDataFrames — read shapefiles once per process.
_geo_cache = {}

# Disk-backed cache for rendered map HTML (PNG embedded as base64).
# Honors XDG_CACHE_HOME on Linux/macOS; falls back to ~/.cache (on Windows
# resolves under the user profile). Same convention as the leader-photo
# cache in fenced_divs.py. Cache key is SHA1 of (inner block + parquet
# mtimes), so the cache invalidates automatically if the bundled boundary
# data is updated.
_MAP_CACHE_DIR = Path(
    os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache")
) / "country-brief" / "maps"


def _map_cache_path(inner: str):
    """Cache file path for this exact ::: map block, or None if unavailable.

    The key blends the raw inner block (which captures country, regions,
    title, color-scale, etc. exhaustively) with parquet mtimes so a skill
    update that ships new boundary data invalidates stale renders.
    """
    try:
        admin0_p = _GEO_DIR / "admin0.parquet"
        admin1_p = _GEO_DIR / "admin1.parquet"
        admin0_mtime = admin0_p.stat().st_mtime if admin0_p.exists() else 0
        admin1_mtime = admin1_p.stat().st_mtime if admin1_p.exists() else 0
        key_input = f"{inner}|{admin0_mtime}|{admin1_mtime}".encode("utf-8")
        h = hashlib.sha1(key_input).hexdigest()[:20]
        return _MAP_CACHE_DIR / f"{h}.html"
    except Exception:
        return None


def _load_admin_data(level: int):
    """Load and cache the admin-0 (level=0) or admin-1 (level=1) GeoParquet.

    Returns None if the file is missing or the geopandas stack isn't available,
    so callers can fall back gracefully.
    """
    if level in _geo_cache:
        return _geo_cache[level]
    try:
        import geopandas as gpd
    except ImportError:
        _geo_cache[level] = None
        return None
    fname = f"admin{level}.parquet"
    path = _GEO_DIR / fname
    if not path.exists():
        _geo_cache[level] = None
        return None
    _geo_cache[level] = gpd.read_parquet(path)
    return _geo_cache[level]


def _load_capitals_data():
    """Load and cache the bundled national capitals GeoParquet.

    Returns a GeoDataFrame with one row per sovereign country's capital
    (NAME, ADM0NAME, ISO_A2, ADM0_A3, geometry as Point). Source: Natural
    Earth populated places, filtered to FEATURECLA=Admin-0 capital.

    Returns None if the file is missing or geopandas isn't available, so
    callers can fall back gracefully (the map still renders without the
    capital marker).
    """
    cache_key = "capitals"
    if cache_key in _geo_cache:
        return _geo_cache[cache_key]
    try:
        import geopandas as gpd
    except ImportError:
        _geo_cache[cache_key] = None
        return None
    path = _GEO_DIR / "capitals.parquet"
    if not path.exists():
        _geo_cache[cache_key] = None
        return None
    _geo_cache[cache_key] = gpd.read_parquet(path)
    return _geo_cache[cache_key]


# Arabic country-name aliases for ADMIN-column lookups. Natural Earth's
# admin0 table uses English-language ADMIN strings, so Arabic country names
# passed via --country (Arabic briefs) won't match. This dict bridges the
# gap. Keys cover both the short Arabic form and the formal cover-page form.
# Add new entries when an Arabic brief surfaces a new country.
_ARABIC_COUNTRY_ALIASES = {
    "إيران": "Iran",
    "جمهورية إيران الإسلامية": "Iran",
    "الإمارات": "United Arab Emirates",
    "الإمارات العربية المتحدة": "United Arab Emirates",
    "السعودية": "Saudi Arabia",
    "المملكة العربية السعودية": "Saudi Arabia",
    "مصر": "Egypt",
    "جمهورية مصر العربية": "Egypt",
    "تركيا": "Turkey",
    "روسيا": "Russia",
    "سوريا": "Syria",
    "سورية": "Syria",
    "الجزائر": "Algeria",
    "العراق": "Iraq",
    "اليمن": "Yemen",
    "ليبيا": "Libya",
    "تونس": "Tunisia",
    "المغرب": "Morocco",
    "السودان": "Sudan",
    "الأردن": "Jordan",
    "لبنان": "Lebanon",
    "فلسطين": "Palestine",
    "قطر": "Qatar",
    "الكويت": "Kuwait",
    "البحرين": "Bahrain",
    "مملكة البحرين": "Bahrain",
    "عمان": "Oman",
    "سلطنة عمان": "Oman",
    "فيجي": "Fiji",
    "سريلانكا": "Sri Lanka",
    "جمهورية سريلانكا الديمقراطية الاشتراكية": "Sri Lanka",
    "إثيوبيا": "Ethiopia",
    "تشاد": "Chad",
    "جزر القمر": "Comoros",
    "جنوب أفريقيا": "South Africa",
    "الولايات المتحدة": "United States of America",
    "الولايات المتحدة الأمريكية": "United States of America",
}


def _country_flag_path(country: str):
    """Return the absolute path (as file:// URL) to the country's flag PNG,
    or None if no matching flag is bundled.

    Lookup strategy: country name → admin0 row → ISO_A2 code → `flags/{code}.png`.
    Falls back to the Arabic-alias map if the direct ADMIN-column match
    fails, so Arabic-language briefs ( `--country "جمهورية إيران الإسلامية"` )
    resolve to the same flag as the English form. The ISO_A2 codes match
    the lipis/flag-icons naming convention (lowercase).

    Returns the path as a `file://` URL string ready for embedding in an HTML
    `<img src>` attribute. Using a file URL rather than a relative path avoids
    WeasyPrint's silent failure mode where images don't resolve.
    """
    admin0 = _load_admin_data(0)
    if admin0 is None:
        return None
    # Match by ADMIN column (Natural Earth's primary country name field)
    col = "ADMIN" if "ADMIN" in admin0.columns else "admin"
    row = admin0[admin0[col] == country]
    # Fall back through the Arabic-alias map if the direct match misses.
    if row.empty and country in _ARABIC_COUNTRY_ALIASES:
        row = admin0[admin0[col] == _ARABIC_COUNTRY_ALIASES[country]]
    if row.empty:
        return None
    iso_a2 = str(row.iloc[0]["ISO_A2"]).strip().lower()
    if not iso_a2 or iso_a2 == "-99":  # Natural Earth uses -99 for unrecognized
        return None
    flag_path = _FLAG_DIR / f"{iso_a2}.png"
    if not flag_path.exists():
        return None
    return flag_path.resolve().as_uri()


# Predefined categorical color scales for maps.
# Keys are *already normalized* (lowercase, hyphens replaced with spaces)
# so they match the output of _normalize_region_name() for direct lookup.
# These intentionally reuse the brief's severity palette so a severity-box
# and a severity map use the same colors.


_MAP_COLOR_SCALES = {
    "severity": {
        "severe": "#b91c1c",
        "escalating": "#b91c1c",
        "re escalating": "#b91c1c",
        "high": "#ea580c",
        "deteriorating": "#ea580c",
        "medium": "#eab308",
        "moderate": "#eab308",
        "chronic": "#eab308",
        "contained": "#84cc16",
        "stable": "#15803d",
        "secure": "#15803d",
    },
    "electoral": {
        "green": "#15803d",
        "yellow": "#eab308",
        "amber": "#eab308",
        "red": "#b91c1c",
        "delayed": "#b91c1c",
    },
    "verdict": {
        "green": "#15803d",
        "amber": "#eab308",
        "red": "#b91c1c",
    },
}


def _normalize_region_name(name: str) -> str:
    """Normalize a region name for matching: lowercase, strip, remove
    punctuation, collapse whitespace. Used for fuzzy region matching since
    Natural Earth and analyst-supplied names often differ in spelling."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9 ]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


# Aliases for Natural Earth region names that don't match common analyst usage.
# Pre-applied at load time so user data like "Oromia" matches NE's "Oromiya".


_REGION_ALIASES = {
    # Ethiopia
    "oromia": "oromiya",
    "benishangul gumuz": "benshangul gumaz",
    "benishangulgumuz": "benshangul gumaz",
    "snnpr": "southern nations nationalities and peoples",
    "southern nations": "southern nations nationalities and peoples",
    "gambela": "gambela peoples",
    "harari": "harari people",
    # Sudan — Natural Earth uses some older / alternative spellings
    "north kordofan": "north kordufan",
    "south kordofan": "south kordufan",
    "south darfur": "southern darfur",
    "east darfur": "eastern darfur",
    "west darfur": "western darfur",
    "gedaref": "gedarif",
    "al jazirah": "gezira",
    "al gazira": "gezira",
    # Syria — Natural Earth uses parentheticals and apostrophes
    "hasaka": "hasaka al haksa",
    "al hasakah": "hasaka al haksa",
    "homs": "homs hims",
    "raqqa": "ar raqqah",
    "ar raqqa": "ar raqqah",
    "deir al zour": "dayr az zawr",
    "deir ez zor": "dayr az zawr",
    "deir ez-zor": "dayr az zawr",
    # Chad — Natural Earth uses prefixed form for the capital district
    "ndjamena": "ville de n djamena",
    "n djamena": "ville de n djamena",
    "bahr el ghazel": "barh el gazel",
    "ouaddai": "ouadda",
    # Add more as future briefs surface mismatches
}


_CAPITAL_OVERRIDES = {
    "Morocco": "Rabat",
    # Sri Lanka has two capitals in Natural Earth data: Sri Jayawardenepura Kotte
    # (legislative, where parliament sits) and Colombo (commercial, where most
    # ministries / embassies / commercial activity is). For analytical briefs
    # Colombo is the more useful marker — it is what readers expect on a map
    # of Sri Lanka and is where the country's economic geography is anchored.
    "Sri Lanka": "Colombo",
    # South Africa has the three-capital constitutional arrangement (Pretoria
    # executive, Cape Town legislative, Bloemfontein judicial) plus Johannesburg
    # as the largest city. Natural Earth has all four flagged. For a country-
    # brief reference map, Pretoria is the analytically-correct pick: it is
    # where the executive sits, where embassies accredit, where heads of state
    # visit, and is the de facto "national capital" in conventional usage.
    "South Africa": "Pretoria",
    # Add more as future briefs surface ambiguities
}


# Display-name overrides for admin-1 regions. Used when Natural Earth's
# `name` field is not analytically useful for an English-speaking reader —
# e.g., when NE uses transliterated local-language names (Sinhalese for
# Sri Lanka) instead of the English / conventional spellings.
#
# Structure: dict keyed by country name (as in ADM0NAME / "admin"), with
# nested dict mapping the NE name → the display name to use on map labels.
# The renderer looks up the override at label-drawing time; if not found,
# the original NE name is used (current default behavior).
#
# Note: this affects DISPLAY only — region matching against analyst-provided
# region names in the markdown still uses normalized matching against the
# NE name. Use _REGION_ALIASES for input matching (analyst-provided name →
# NE name) and this dict for output display (NE name → reader-friendly name).
_REGION_DISPLAY_OVERRIDES = {
    "United States of America": {
        # The standard 2-letter USPS postal codes. 50 states + DC = 51
        # entries. Replaces the full state names (which average ~12
        # characters and crowd the choropleth, especially the packed
        # Northeast) with the 2-letter abbreviations every published US
        # state map uses. The renderer's spiral label-placement handles
        # ~20-30 regions cleanly; at 50 entries we lean on the abbreviation
        # convention rather than algorithmic placement to keep the map
        # readable. The 2-letter labels fit inside even the smallest
        # states (RI, DE, DC) without leader lines.
        "Alabama":              "AL",
        "Alaska":               "AK",
        "Arizona":              "AZ",
        "Arkansas":             "AR",
        "California":           "CA",
        "Colorado":             "CO",
        "Connecticut":          "CT",
        "Delaware":             "DE",
        "District of Columbia": "DC",
        "Florida":              "FL",
        "Georgia":              "GA",
        "Hawaii":               "HI",
        "Idaho":                "ID",
        "Illinois":             "IL",
        "Indiana":              "IN",
        "Iowa":                 "IA",
        "Kansas":               "KS",
        "Kentucky":             "KY",
        "Louisiana":            "LA",
        "Maine":                "ME",
        "Maryland":             "MD",
        "Massachusetts":        "MA",
        "Michigan":             "MI",
        "Minnesota":            "MN",
        "Mississippi":          "MS",
        "Missouri":             "MO",
        "Montana":              "MT",
        "Nebraska":             "NE",
        "Nevada":               "NV",
        "New Hampshire":        "NH",
        "New Jersey":           "NJ",
        "New Mexico":           "NM",
        "New York":             "NY",
        "North Carolina":       "NC",
        "North Dakota":         "ND",
        "Ohio":                 "OH",
        "Oklahoma":             "OK",
        "Oregon":               "OR",
        "Pennsylvania":         "PA",
        "Rhode Island":         "RI",
        "South Carolina":       "SC",
        "South Dakota":         "SD",
        "Tennessee":            "TN",
        "Texas":                "TX",
        "Utah":                 "UT",
        "Vermont":              "VT",
        "Virginia":             "VA",
        "Washington":           "WA",
        "West Virginia":        "WV",
        "Wisconsin":            "WI",
        "Wyoming":              "WY",
    },
    "Sri Lanka": {
        # Natural Earth admin-1 data for Sri Lanka uses Sinhalese transliteration
        # at the district level (25 districts), not English province names.
        # These are unreadable for an English-speaking analyst. Map to the
        # conventional English district names. Note: this still renders at the
        # district level, not the more analytically useful 9-province level —
        # that would require either replacement geo data or runtime aggregation.
        "Yāpanaya":      "Jaffna",
        "Kilinŏchchi":   "Kilinochchi",
        "Mannārama":     "Mannar",
        "Mulativ":       "Mullaitivu",
        "Vavuniyāva":    "Vavuniya",
        "Trikuṇāmalaya": "Trincomalee",
        "Maḍakalapuva":  "Batticaloa",
        "Ampāra":        "Ampara",
        "Mŏṇarāgala":    "Monaragala",
        "Badulla":       "Badulla",
        "Mahanuvara":    "Kandy",
        "Mātale":        "Matale",
        "Nuvara Ĕliya":  "Nuwara Eliya",
        "Pŏḷŏnnaruva":   "Polonnaruwa",
        "Anurādhapura":  "Anuradhapura",
        "Kuruṇægala":    "Kurunegala",
        "Puttalama":     "Puttalam",
        "Gampaha":       "Gampaha",
        "Kŏḷamba":       "Colombo",
        "Kaḷutara":      "Kalutara",
        "Kægalla":       "Kegalle",
        "Ratnapura":     "Ratnapura",
        "Gālla":         "Galle",
        "Mātara":        "Matara",
        "Hambantŏṭa":    "Hambantota",
    },
}


def render_map(inner: str) -> str:
    """
    Render a choropleth (region-colored) map of a country's sub-national
    admin-1 regions, optionally with neighboring countries shown for context.

    Markdown syntax:
        ::: map
        type: choropleth                 # currently the only supported type
        title: Sub-national severity
        country: Ethiopia                # required: which country to focus on
        region: Amhara | escalating      # one per region, name | category
        region: Tigray | re-escalating
        region: Oromia | high
        region: Addis Ababa | stable
        color-scale: severity            # one of: severity, electoral, verdict
        show-neighbors: true             # optional, default true
        source: ACLED; ECHO; analyst assessment
        :::

    Returns an HTML <div class="map"> wrapping a PNG embedded as base64.
    Falls back to a styled error message if geopandas isn't available or
    the boundary data is missing.

    Known limitation: Natural Earth 10m data reflects pre-2020 Ethiopian
    administrative divisions, so newer regions (Sidama, South West, South
    Ethiopia) appear within the legacy SNNPR polygon. Document this when
    using maps for regions affected by recent restructuring.
    """
    # Cache check. Same block of markdown deterministically renders the same
    # HTML; skip matplotlib / geopandas / spiral-search entirely on hit.
    # Error fallbacks below are NOT cached — only the final successful path
    # writes to the cache, so fixing a missing country: parameter doesn't
    # require manual cache invalidation.
    cache_path = _map_cache_path(inner)
    if cache_path is not None and cache_path.exists():
        try:
            return cache_path.read_text(encoding="utf-8")
        except Exception:
            pass  # corrupt cache entry — fall through to fresh render

    # Lazy import — only load when a map is actually requested
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        return (
            '<div class="map-error">'
            'Map rendering requires matplotlib. Install with: '
            '<code>pip install matplotlib</code>'
            '</div>'
        )
    try:
        import geopandas as gpd
    except ImportError:
        return (
            '<div class="map-error">'
            'Map rendering requires geopandas. Install with: '
            '<code>pip install geopandas</code>'
            '</div>'
        )

    # Parse parameters
    params = {}
    region_data = []  # list of (region_name, category) tuples
    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([a-z-]+):\s*(.+)$", line)
        if not m:
            continue
        key, value = m.group(1).lower(), m.group(2).strip()
        if key == "region":
            parts = [p.strip() for p in value.split("|")]
            if len(parts) >= 2:
                region_data.append((parts[0], parts[1]))
        else:
            params[key] = value

    country = params.get("country", "")
    if not country:
        return (
            '<div class="map-error">'
            'Map requires <code>country:</code> parameter.'
            '</div>'
        )

    title = params.get("title", "")
    source = params.get("source", "")
    scale_name = params.get("color-scale", "severity")
    show_neighbors = params.get("show-neighbors", "true").lower() != "false"
    # Map type: "choropleth" (default, region-colored by category) or
    # "reference" (uniform muted fill, no legend — orientation only).
    # Reference mode is for shorter briefs that don't trigger thematic
    # maps in Section 4 or 11 but still want spatial orientation in the
    # snapshot.
    map_type = params.get("type", "choropleth").lower()

    # Load admin-1 boundaries
    admin1 = _load_admin_data(1)
    if admin1 is None:
        return (
            '<div class="map-error">'
            'Map rendering requires the Natural Earth boundary files at '
            '<code>assets/geo/admin1.parquet</code>. See SKILL.md for setup.'
            '</div>'
        )

    # Filter to country
    country_regions = admin1[admin1["admin"] == country].copy()
    if country_regions.empty:
        return (
            f'<div class="map-error">'
            f'No admin-1 regions found for country "{country}". '
            f'Check the country name spelling — must match Natural Earth\'s '
            f'<code>admin</code> column exactly (e.g., "Ethiopia", '
            f'"United States of America").'
            f'</div>'
        )

    # Set up the figure. 6.4 x 5.0 inches — taller than charts because
    # maps are usually portrait-oriented or near-square.
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#f8fafc")  # very light grey background for contrast

    # CONUS + insets layout for the United States. The full 50-state extent
    # spans 359° of longitude (Aleutians cross the antimeridian; Hawaii sits
    # at -158° while Maine is at -67°), which compresses the contiguous 48
    # to ~16% of the available frame and triggers the antimeridian fix.
    # Standard atlas treatment: render CONUS in the main axes; render
    # Alaska and Hawaii as small inset axes in the lower-left so they're
    # still visible and color-coded but don't distort the main map.
    is_usa_country = country.strip() in (
        "United States of America", "United States", "USA",
    )
    if is_usa_country:
        # Filter out AK and HI from the regions used for main-map bounds
        # and plotting. They remain in country_regions so labels/region-
        # category lookups still work; the insets re-use country_regions
        # filtered to each state.
        conus_regions = country_regions[
            ~country_regions["name"].isin(["Alaska", "Hawaii"])
        ].copy()
        main_plot_regions = conus_regions
    else:
        main_plot_regions = country_regions

    # Draw the country bounding region first (for the focus country)
    country_bounds = main_plot_regions.total_bounds  # [minx, miny, maxx, maxy]

    # Antimeridian-crossing detection: some countries (Fiji, Kiribati, Tuvalu,
    # Russia, NZ Chathams) have territory on both sides of the 180° meridian.
    # When a country's geometry crosses the antimeridian, naive total_bounds
    # returns minx=-180 and maxx=180, producing a world-spanning view rather
    # than a country-focused view. The fix: detect this case (longitude span
    # > 180°), shift negative longitudes by +360° to put all geometry in the
    # positive hemisphere, recompute bounds on the shifted geometry, and use
    # the shifted geometry for plotting.
    longitude_span = country_bounds[2] - country_bounds[0]
    crosses_antimeridian = longitude_span > 180.0
    if crosses_antimeridian:
        from shapely.affinity import translate as _shapely_translate
        from shapely.ops import unary_union as _unary_union
        def _shift_geometry_to_positive(geom):
            """Shift any part of a geometry with negative longitude by +360."""
            if geom is None or geom.is_empty:
                return geom
            # Split into negative-longitude and positive-longitude parts,
            # shift the negative part by +360, then reunion.
            from shapely.geometry import box, MultiPolygon, Polygon
            western_box = box(-180.001, -90.001, 0.0, 90.001)
            eastern_box = box(0.0, -90.001, 180.001, 90.001)
            try:
                western = geom.intersection(western_box)
                eastern = geom.intersection(eastern_box)
                if not western.is_empty:
                    western = _shapely_translate(western, xoff=360.0)
                if eastern.is_empty:
                    return western
                if western.is_empty:
                    return eastern
                return _unary_union([western, eastern])
            except Exception:
                # Fall back to original geometry on any error
                return geom

        # Apply shift to country_regions for both bounds recomputation and plotting
        country_regions = country_regions.copy()
        country_regions["geometry"] = country_regions["geometry"].apply(
            _shift_geometry_to_positive
        )
        country_bounds = country_regions.total_bounds

    # Add a small buffer so the country isn't right at the edge of the frame
    bx, by = country_bounds[2] - country_bounds[0], country_bounds[3] - country_bounds[1]
    pad_x, pad_y = bx * 0.15, by * 0.15
    view = [
        country_bounds[0] - pad_x,
        country_bounds[2] + pad_x,
        country_bounds[1] - pad_y,
        country_bounds[3] + pad_y,
    ]

    # Optionally draw neighbors as a contextual layer (light grey, no labels)
    if show_neighbors:
        admin0 = _load_admin_data(0)
        if admin0 is not None:
            # Determine column to filter by (Natural Earth uses ADMIN typically)
            col = "ADMIN" if "ADMIN" in admin0.columns else "admin"
            # Find neighbors that intersect the view rectangle
            from shapely.geometry import box
            # If we shifted country geometry across the antimeridian, we need
            # to shift the neighbors layer too — otherwise neighbors are drawn
            # in their original lat/lon and don't appear in the (shifted) view.
            if crosses_antimeridian:
                admin0 = admin0.copy()
                admin0["geometry"] = admin0["geometry"].apply(
                    _shift_geometry_to_positive
                )
            view_box = box(view[0], view[2], view[1], view[3])
            neighbors = admin0[admin0.geometry.intersects(view_box) & (admin0[col] != country)]
            # Skip plotting when there are no neighbors in the view box. This
            # happens for small isolated island countries (Comoros, Maldives,
            # Tuvalu) whose padded view box doesn't extend to any adjacent
            # landmass. Calling geopandas .plot() on an empty GeoDataFrame
            # produces a NaN-aspect-ratio error in modern geopandas/matplotlib.
            if not neighbors.empty:
                neighbors.plot(
                    ax=ax, color="#e2e8f0", edgecolor="#cbd5e0", linewidth=0.5,
                )
            # Add neighbor country labels near their centroid
            for _, row in neighbors.iterrows():
                # Only label neighbors with a meaningful intersection
                inter = row.geometry.intersection(view_box)
                if inter.is_empty or inter.area < 0.1:
                    continue
                # Use centroid of intersection so the label sits inside the view
                cx, cy = inter.centroid.x, inter.centroid.y
                name = row.get(col, "")
                if name:
                    ax.text(
                        cx, cy, name,
                        fontsize=7, color="#6b7280",
                        ha="center", va="center", style="italic",
                    )

    # Map each region in user data to a color via the chosen scale
    scale = _MAP_COLOR_SCALES.get(scale_name, _MAP_COLOR_SCALES["severity"])

    # Build the set of valid Natural Earth region names for this country
    # (normalized) so we can fuzzy-match user-supplied names that don't
    # exact-match. This handles three common error modes:
    #   1. Different spellings (Kordofan vs Kordufan)
    #   2. Word-order differences (East Darfur vs Eastern Darfur)
    #   3. Old/new administrative names (Al Jazirah vs Gezira)
    # Known aliases are handled via _REGION_ALIASES; fuzzy matching here
    # is the fallback for the long tail.
    ne_region_norms = {
        _normalize_region_name(name): name
        for name in country_regions["name"].tolist()
    }

    # Build a lookup from normalized NE region name → (user category, color)
    region_lookup = {}
    unmatched_user_regions = []  # accumulate warnings for end-of-render report
    fuzzy_matched_regions = []   # accumulate fuzzy-match notes
    for user_name, category in region_data:
        norm = _normalize_region_name(user_name)
        norm = _REGION_ALIASES.get(norm, norm)
        category_norm = _normalize_region_name(category)
        color = scale.get(category_norm, "#cbd5e0")  # default light grey

        # If this normalized name doesn't match any NE region, try fuzzy
        # matching against the country's actual admin-1 names.
        if norm not in ne_region_norms:
            import difflib
            candidates = difflib.get_close_matches(
                norm, list(ne_region_norms.keys()),
                n=1, cutoff=0.75,  # 0.75 catches Kordofan→Kordufan but not unrelated names
            )
            if candidates:
                fuzzy_match = candidates[0]
                fuzzy_matched_regions.append(
                    (user_name, ne_region_norms[fuzzy_match])
                )
                norm = fuzzy_match
            else:
                unmatched_user_regions.append(user_name)

        region_lookup[norm] = (category, color)

    # Emit warnings to stderr for analyst visibility. These are warnings
    # not errors — the map still renders, but the analyst sees what they
    # need to fix or what got auto-corrected.
    if fuzzy_matched_regions or unmatched_user_regions:
        import sys
        if fuzzy_matched_regions:
            print(
                f"Map note ({country}): fuzzy-matched {len(fuzzy_matched_regions)} region name(s):",
                file=sys.stderr,
            )
            for user_name, ne_name in fuzzy_matched_regions:
                print(f"  '{user_name}' → '{ne_name}'", file=sys.stderr)
        if unmatched_user_regions:
            print(
                f"Map WARNING ({country}): {len(unmatched_user_regions)} region(s) did not match any admin-1 name:",
                file=sys.stderr,
            )
            for r in unmatched_user_regions:
                print(f"  '{r}'", file=sys.stderr)
            available = sorted(country_regions["name"].tolist())
            print(f"  Available admin-1 regions: {', '.join(available)}", file=sys.stderr)

    # Color each region in the country_regions GeoDataFrame.
    # Choropleth mode: each region gets its category's color or a light-grey
    # fallback if unmapped. Reference mode: every region gets the same muted
    # navy-tint fill — the map is for orientation, not analysis.
    if map_type == "reference":
        colors = ["#dbe7f0"] * len(country_regions)  # muted navy tint
    else:
        colors = []
        matched = set()
        for _, row in country_regions.iterrows():
            ne_name_norm = _normalize_region_name(row["name"])
            if ne_name_norm in region_lookup:
                _, color = region_lookup[ne_name_norm]
                colors.append(color)
                matched.add(ne_name_norm)
            else:
                colors.append("#f1f5f9")  # unmapped — very light grey

    country_regions = country_regions.copy()
    country_regions["_fill"] = colors
    # Plot only main_plot_regions in the main axes. For non-USA countries
    # this is identical to country_regions; for the USA it excludes AK/HI
    # which are rendered as insets below.
    main_plot_regions = country_regions[country_regions["name"].isin(main_plot_regions["name"])]
    main_plot_regions.plot(
        ax=ax, color=main_plot_regions["_fill"],
        edgecolor="#1a3a52", linewidth=0.6,
    )

    # Overlay the national capital as a star marker. The capital comes from
    # the bundled Natural Earth populated-places extract (capitals.parquet).
    # Drawn before labels so labels can sit on top if there's overlap.
    #
    # Some countries (notably Morocco, where the dataset contains both
    # Rabat and Laayoune) have multiple entries. Without disambiguation
    # the lookup picks the alphabetically-first row, which can produce
    # the wrong national capital. We check _CAPITAL_OVERRIDES first for
    # an explicit canonical name; absent that, we pick the first row but
    # emit a stderr warning so the analyst sees the ambiguity and can
    # add an override.
    capitals = _load_capitals_data()
    capital_name = None
    if capitals is not None:
        country_capital = capitals[capitals["ADM0NAME"] == country]
        if not country_capital.empty:
            cap_row = None
            override = _CAPITAL_OVERRIDES.get(country)
            if override:
                # Apply the override — match by NAME
                preferred = country_capital[country_capital["NAME"] == override]
                if not preferred.empty:
                    cap_row = preferred.iloc[0]
                # If override didn't match (data drift), fall through to
                # default behavior below with a warning
            if cap_row is None:
                if len(country_capital) > 1:
                    import sys
                    candidate_names = country_capital["NAME"].tolist()
                    print(
                        f"Map note ({country}): multiple capital entries found "
                        f"({', '.join(candidate_names)}); "
                        f"using '{candidate_names[0]}'. If incorrect, add an "
                        f"entry to _CAPITAL_OVERRIDES in render_brief.py.",
                        file=sys.stderr,
                    )
                cap_row = country_capital.iloc[0]
            cap_pt = cap_row.geometry
            capital_name = cap_row["NAME"]
            # Outer ring (white halo) for legibility on any fill color
            ax.scatter(
                [cap_pt.x], [cap_pt.y],
                marker="*", s=260, color="white",
                edgecolors="none", zorder=4,
            )
            # Inner star (dark navy)
            ax.scatter(
                [cap_pt.x], [cap_pt.y],
                marker="*", s=180, color="#0f172a",
                edgecolors="white", linewidths=0.5, zorder=5,
            )

    # Find the capital point for this country (used both for the marker
    # and to detect overlap when labelling regions). Cached here so the
    # per-region loop below doesn't re-query the GeoDataFrame. Mirrors
    # the override logic above so the geometry matches the marker that
    # was actually drawn.
    capital_geom = None
    if capitals is not None:
        country_capital_rows = capitals[capitals["ADM0NAME"] == country]
        if not country_capital_rows.empty:
            override = _CAPITAL_OVERRIDES.get(country)
            chosen_row = None
            if override:
                preferred = country_capital_rows[country_capital_rows["NAME"] == override]
                if not preferred.empty:
                    chosen_row = preferred.iloc[0]
            if chosen_row is None:
                chosen_row = country_capital_rows.iloc[0]
            capital_geom = chosen_row.geometry

    # Label every focus-country region. The placement uses four techniques
    # to handle dense administrative geographies (Morocco's 16 small coastal
    # regions, etc.) cleanly without dropping information:
    #
    # 1. Long compound names get abbreviated to their first segment
    #    ("Marrakech - Tensift - Al Haouz" → "Marrakech"). On a choropleth
    #    the analytical signal is the color; the label only needs to
    #    orient the reader to which region they're looking at.
    # 2. Regions are sorted by polygon area (largest first) so the most
    #    visible regions claim their natural placement first; smaller
    #    regions defer to leader-line placement around them.
    # 3. Collision detection: each label's pixel-space bounding box is
    #    checked against already-placed labels. If overlap, the renderer
    #    searches outward in a spiral pattern (8 directions x increasing
    #    radii) for a clean position. Labels are NEVER skipped — every
    #    region gets a label so the reader can identify what each color
    #    represents.
    # 4. Leader lines: when a label ends up displaced more than a small
    #    threshold from its region's anchor point, a thin gray line is
    #    drawn from the label back to the anchor so the reader can see
    #    which region the label belongs to.
    #
    # The capital region gets special handling: its anchor is the capital
    # marker rather than the polygon's representative point, to bias the
    # label below the star and avoid colliding with it.
    country_height = country_bounds[3] - country_bounds[1]
    country_width = country_bounds[2] - country_bounds[0]
    label_offset_dy = country_height * 0.025  # ~2.5% of country height

    def _abbreviate_region_name(name: str) -> str:
        """Shorten compound hyphenated names for map display. The first
        segment is usually the most recognizable. Only abbreviates when
        the full name is long; short names stay intact."""
        if " - " in name and len(name) > 15:
            return name.split(" - ")[0].strip()
        return name

    # Force a draw so text bounding boxes can be computed in pixel space
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    placed_bboxes = []  # list of (x0, y0, x1, y1) in pixel space

    def _label_would_collide(text_obj):
        """Check if a text object's bounding box overlaps any already-placed
        label. Returns True if there's an overlap."""
        try:
            bbox = text_obj.get_window_extent(renderer=renderer)
        except Exception:
            return False
        for x0, y0, x1, y1 in placed_bboxes:
            if not (bbox.x1 < x0 or bbox.x0 > x1 or bbox.y1 < y0 or bbox.y0 > y1):
                return True
        return False

    # Sort regions by polygon area (largest first) so they claim natural
    # placements first; small regions then get leader-line placement.
    # The CRS warning is suppressed — we only need relative ordering,
    # not accurate area values, and projecting just for sorting is overkill.
    import warnings
    # Sort only the regions that appear in the main plot — for USA this
    # excludes AK and HI from the label-placement loop (they get their own
    # inset rendering below).
    sorted_regions = main_plot_regions.copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        sorted_regions["_area"] = sorted_regions.geometry.area
    sorted_regions = sorted_regions.sort_values("_area", ascending=False)

    # Spiral search pattern: 8 directions x increasing radii. The renderer
    # tries the natural position (radius 0) first, then expands outward
    # until it finds a clean spot. With this many candidates (1 + 8*4 = 33),
    # virtually every region will find a non-overlapping placement.
    import math
    search_radii = [
        country_width * 0.035,  # ~3.5% of country width
        country_width * 0.065,  # ~6.5%
        country_width * 0.10,   # ~10%
        country_width * 0.14,   # ~14%
    ]
    # 8 compass directions
    directions = [
        (math.cos(math.radians(a)), math.sin(math.radians(a)))
        for a in (0, 45, 90, 135, 180, 225, 270, 315)
    ]

    # Threshold: if the placed label is more than this far from its anchor,
    # draw a leader line. Below this, the label is "close enough" that the
    # reader can naturally associate it with its region.
    leader_threshold_data = country_width * 0.04

    for _, row in sorted_regions.iterrows():
        try:
            # Anchor point: where the label "belongs" — either the polygon's
            # representative point or, for the capital region, the capital
            # marker location (so labels sit below the star naturally).
            pt = row.geometry.representative_point()
            anchor_x, anchor_y = pt.x, pt.y
            if capital_geom is not None:
                try:
                    if row.geometry.contains(capital_geom):
                        anchor_x = capital_geom.x
                        anchor_y = capital_geom.y - label_offset_dy
                except Exception:
                    pass

            # Get the region's NE name and check for a country-specific
            # display override (used when NE labels are not analytically
            # useful in English — e.g., Sri Lanka's Sinhalese transliterations).
            ne_name = row["name"]
            country_overrides = _REGION_DISPLAY_OVERRIDES.get(country, {})
            display_name = country_overrides.get(ne_name, ne_name)
            display_name = _abbreviate_region_name(display_name)

            # Build the candidate position list: natural position first,
            # then spiral outward through all (radius, direction) combos.
            # Both choropleth and reference maps use the same search space
            # so most regions get labeled. The difference is in how they
            # handle displacement after placement (see leader-line logic
            # below): choropleth maps draw a leader line when a label is
            # displaced from its region; reference maps suppress leader
            # lines entirely to keep the orientation map visually clean.
            candidate_positions = [(anchor_x, anchor_y)]
            for r in search_radii:
                for dx, dy in directions:
                    candidate_positions.append((anchor_x + r * dx, anchor_y + r * dy))

            placed_position = None
            for cx, cy in candidate_positions:
                t = ax.text(
                    cx, cy, display_name,
                    fontsize=7, color="#0f172a",
                    ha="center", va="center",
                    bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1),
                    zorder=6,
                )
                fig.canvas.draw()
                if not _label_would_collide(t):
                    try:
                        bbox = t.get_window_extent(renderer=renderer)
                        placed_bboxes.append((bbox.x0, bbox.y0, bbox.x1, bbox.y1))
                    except Exception:
                        pass
                    placed_position = (cx, cy)
                    break
                t.remove()

            # If the entire search space collided (very dense layouts),
            # place at the furthest candidate anyway — never drop. This
            # is a defensive fallback; the search space is large enough
            # that it should rarely trigger.
            if placed_position is None:
                fallback_x, fallback_y = candidate_positions[-1]
                ax.text(
                    fallback_x, fallback_y, display_name,
                    fontsize=7, color="#0f172a",
                    ha="center", va="center",
                    bbox=dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1),
                    zorder=6,
                )
                placed_position = (fallback_x, fallback_y)

            # Label-placement policy differs by map type:
            #
            # CHOROPLETH MAPS: every region is data-bearing (its color
            # represents an analytical category). Every label needs to be
            # placed somewhere, even if displaced, with a leader line to
            # show the association. Missing labels would orphan the colors.
            #
            # REFERENCE MAPS: regions are uniform-filled; the map is for
            # orientation only. Labels that fit cleanly inside polygons
            # are useful; labels displaced far from their region with
            # leader lines crossing the country produce visual noise that
            # actively impairs readability (the Iran reference map at
            # 31 provinces packed tightly is the motivating case). For
            # reference maps, we suppress labels that would need leader
            # lines — the major provinces still get labeled (they're
            # larger and accommodate labels), the small densely-packed
            # provinces go unlabeled. The reader gets clean orientation
            # rather than a tangled crosshatch of leader lines.
            px, py = placed_position
            distance = math.hypot(px - anchor_x, py - anchor_y)
            if distance > leader_threshold_data:
                if map_type == "reference":
                    # Reference-map mode: remove this label rather than
                    # drawing a leader line. The matplotlib text object
                    # is still in the axes from earlier placement; remove
                    # it here.
                    try:
                        t.remove()
                    except Exception:
                        pass
                    continue
                # Draw a small dot at the anchor so the line has a clear
                # terminus, then a thin gray line from anchor to label.
                # Both sit beneath the label (lower zorder) so the label's
                # white background hides the line where they overlap.
                ax.plot(
                    [anchor_x, px], [anchor_y, py],
                    color="#64748b", linewidth=0.5, zorder=3,
                    solid_capstyle="round",
                )
                ax.scatter(
                    [anchor_x], [anchor_y],
                    s=8, color="#475569", zorder=3,
                    edgecolors="none",
                )

        except Exception:
            pass

    # Build a categorical legend from the user data. Skip entirely in
    # reference mode — there are no categories, only orientation.
    if region_data and map_type != "reference":
        # Get unique categories preserving order of first appearance
        seen = set()
        unique_cats = []
        for _, cat in region_data:
            cat_norm = _normalize_region_name(cat)
            if cat_norm not in seen:
                seen.add(cat_norm)
                unique_cats.append(cat)
        patches = []
        for cat in unique_cats:
            cat_norm = _normalize_region_name(cat)
            color = scale.get(cat_norm, "#cbd5e0")
            patches.append(mpatches.Patch(color=color, label=cat))
        ax.legend(
            handles=patches, loc="lower left", fontsize=8, frameon=True,
            facecolor="white", edgecolor="#cbd5e0", framealpha=0.9,
        )

    # Set view to focus on country with buffer
    ax.set_xlim(view[0], view[1])
    ax.set_ylim(view[2], view[3])

    # Hide axis ticks and frame — maps don't need axes
    ax.set_xticks([])
    ax.set_yticks([])

    # USA-only: render Alaska and Hawaii as small insets in the lower-left.
    # The main axes shows CONUS at proper scale; the insets show the two
    # non-contiguous states at their own scale, colored to match the
    # choropleth categories. This is the standard atlas treatment for US
    # state maps (every published US election / demographic map uses
    # CONUS + insets). Alaska bounds in the inset exclude the western
    # Aleutians that cross the antimeridian — the main Alaska landmass is
    # ~ -179 to -130 longitude, which is what we plot.
    if is_usa_country:
        ak_regions = country_regions[country_regions["name"] == "Alaska"]
        hi_regions = country_regions[country_regions["name"] == "Hawaii"]

        # Alaska inset: lower-left of figure, occupies ~22% width × 22% height
        ax_ak = fig.add_axes([0.04, 0.05, 0.22, 0.22])
        ax_ak.set_facecolor("#f8fafc")
        if not ak_regions.empty:
            ak_regions.plot(
                ax=ax_ak, color=ak_regions["_fill"],
                edgecolor="#1a3a52", linewidth=0.4,
            )
            # Bounds: exclude antimeridian-crossing Aleutians (lon > 0 piece)
            ax_ak.set_xlim(-180, -125)
            ax_ak.set_ylim(51, 72)
        ax_ak.set_xticks([]); ax_ak.set_yticks([])
        for s in ax_ak.spines.values():
            s.set_edgecolor("#94a3b8"); s.set_linewidth(0.5)
        ax_ak.text(0.5, -0.05, "Alaska",
                   transform=ax_ak.transAxes, ha="center", va="top",
                   fontsize=7, color="#475569")

        # Hawaii inset: just right of Alaska, smaller
        ax_hi = fig.add_axes([0.28, 0.05, 0.15, 0.15])
        ax_hi.set_facecolor("#f8fafc")
        if not hi_regions.empty:
            hi_regions.plot(
                ax=ax_hi, color=hi_regions["_fill"],
                edgecolor="#1a3a52", linewidth=0.4,
            )
            ax_hi.set_xlim(-161, -154)
            ax_hi.set_ylim(18.5, 22.5)
        ax_hi.set_xticks([]); ax_hi.set_yticks([])
        for s in ax_hi.spines.values():
            s.set_edgecolor("#94a3b8"); s.set_linewidth(0.5)
        ax_hi.text(0.5, -0.08, "Hawaii",
                   transform=ax_hi.transAxes, ha="center", va="top",
                   fontsize=7, color="#475569")
    for spine in ax.spines.values():
        spine.set_visible(False)

    # NOTE: We intentionally do NOT set the title via ax.set_title() here.
    # Matplotlib bakes the title into the PNG, which means it lacks proper
    # Arabic shaping support (Arabic letters need contextual forms — initial,
    # medial, final, isolated — and matplotlib's default text engine does
    # not handle Arabic shaping or bidirectional text). Instead, the title
    # is emitted as HTML below, where the WeasyPrint renderer handles RTL,
    # Arabic shaping, and the Amiri font correctly. This benefits all
    # languages by producing consistent typographic treatment of the title.

    plt.tight_layout()

    # Render to PNG
    import io
    import base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    png_bytes = buf.getvalue()
    png_b64 = base64.b64encode(png_bytes).decode("ascii")
    img_tag = f'<img src="data:image/png;base64,{png_b64}" alt="{title or country + " map"}" />'

    # Source caption: localized when source itself contains Arabic.
    def _src_has_arabic(s):
        if not s:
            return False
        return any(
            "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F"
            for ch in str(s)
        )
    source_label = "المصدر" if _src_has_arabic(source) else "Source"

    # Emit title as HTML heading above the image so the typography pipeline
    # (Amiri/Naskh for Arabic, Georgia for English) handles it consistently.
    title_html = f'<h3 class="map-title">{title}</h3>' if title else ""
    caption = f'<div class="map-source">{source_label}: {source}</div>' if source else ""
    result_html = f'<div class="map">{title_html}{img_tag}{caption}</div>'

    # Write to cache (atomic via tmp-file + rename) before returning, so the
    # next render of the same ::: map block skips the work above entirely.
    # Failure to cache is silent — it just means next time renders fresh.
    if cache_path is not None:
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = cache_path.with_suffix(".html.tmp")
            tmp_path.write_text(result_html, encoding="utf-8")
            tmp_path.replace(cache_path)
        except Exception:
            pass

    return result_html


