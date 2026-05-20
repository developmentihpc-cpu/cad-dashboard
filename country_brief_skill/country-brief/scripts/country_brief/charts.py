"""
charts.py — Matplotlib chart rendering for the ::: chart fenced div.

Supports bar, line, and scatter charts. Output is a base64-embedded PNG.
Depends only on matplotlib + numpy. No internal package dependencies.

Arabic text rendering: matplotlib does not perform Arabic text shaping
natively. Arabic glyphs require contextual forms (initial / medial / final
/ isolated) depending on position within a word, and Arabic words read
right-to-left within larger text. The arabic_reshaper + python-bidi
libraries handle both: reshaper joins letters into their contextual forms,
and bidi reverses the visual order so the rendered string reads correctly
in matplotlib's left-to-right rendering pipeline.
"""
import base64
import io
import re

# matplotlib must be imported with a non-interactive backend before any
# pyplot use, since rendering happens in a non-GUI script context.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Arabic text shaping. Both libraries are pure-Python and have no native
# dependencies. If unavailable for any reason, _shape_arabic falls back
# to the unshaped string — text will still render with correct glyphs
# (Amiri has all needed code points) but disconnected letterforms.
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _ARABIC_SHAPING_AVAILABLE = True
except ImportError:
    _ARABIC_SHAPING_AVAILABLE = False


# Cached result of the Arabic-font probe. The candidate scan over
# font_manager.fontManager.ttflist is non-trivial, so we do it once.
_ARABIC_FONT_CACHE = None


def _resolve_arabic_font_family():
    """Return a font-family list whose first entry is a known-installed
    Arabic-capable font (or the serif fallback if none is found).

    matplotlib's family-list fallthrough picks the first family that
    EXISTS at all, not the first that has the requested glyphs. A bare
    ``["Amiri", "serif"]`` therefore silently falls to DejaVu Serif on
    systems without Amiri — and DejaVu Serif has zero Arabic glyphs.
    We probe explicitly against the installed font list and pick the
    first hit from a prioritized chain:

      1. Amiri — the design intent for these briefs (print Naskh).
      2. Noto Naskh Arabic / Noto Sans Arabic — high-quality cross-
         platform Arabic from Google.
      3. Arial / Tahoma / Segoe UI — ship with Windows; all have Arabic.
      4. Helvetica Neue — macOS default.

    Cached at module scope after first probe; the font list doesn't
    change within a process.
    """
    global _ARABIC_FONT_CACHE
    if _ARABIC_FONT_CACHE is not None:
        return _ARABIC_FONT_CACHE
    candidates = [
        "Amiri",
        "Noto Naskh Arabic",
        "Noto Sans Arabic",
        "Arial",
        "Tahoma",
        "Segoe UI",
        "Helvetica Neue",
    ]
    try:
        from matplotlib import font_manager
        available = {f.name for f in font_manager.fontManager.ttflist}
        for cand in candidates:
            if cand in available:
                _ARABIC_FONT_CACHE = [cand, "serif"]
                return _ARABIC_FONT_CACHE
    except Exception:
        pass
    # No probe-able Arabic font found — fall back to "serif" (which on
    # most matplotlib installs resolves to DejaVu Serif and will emit
    # missing-glyph warnings on Arabic, but won't crash).
    _ARABIC_FONT_CACHE = ["serif"]
    return _ARABIC_FONT_CACHE


def _has_arabic_chars(s):
    """Return True if the string contains any Arabic-block characters."""
    if not s:
        return False
    return any(
        "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F"
        for ch in str(s)
    )


def _shape_arabic(text):
    """Reshape Arabic text for matplotlib rendering.

    Matplotlib does not perform Arabic shaping (joining isolated letters
    into their contextual forms) or bidi reordering. This function:
    1. Uses arabic_reshaper to convert isolated letters into contextual forms
    2. Uses python-bidi to reorder visually so RTL text reads correctly
       when rendered by matplotlib's LTR text engine.

    Mixed Arabic + Latin text (e.g., "نمو الناتج (%)") is handled
    correctly by the bidi algorithm.

    Returns the original string unchanged if Arabic shaping is unavailable
    or the text contains no Arabic characters.
    """
    if not text or not _has_arabic_chars(text):
        return text
    if not _ARABIC_SHAPING_AVAILABLE:
        return text
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return text


def _format_bar_value(value: float, all_values: list) -> str:
    """Format a bar's numeric value for use as a label above the bar.

    Smart formatting based on the chart's range of values:
    - If all values in the chart are whole numbers, render as integers
      (e.g., 62, 1300) — avoids "62.0" noise.
    - If any value is fractional, render with one decimal place.
    - For very large values (>= 1000), insert thousands separators
      (1,300 vs 1300) since dense numerals are hard to scan quickly.
    """
    all_integer = all(float(v).is_integer() for v in all_values if v is not None)
    if all_integer:
        as_int = int(round(value))
        return f"{as_int:,}" if abs(as_int) >= 1000 else str(as_int)
    return f"{value:,.1f}" if abs(value) >= 1000 else f"{value:.1f}"


def _label_bars(ax, bar_records) -> None:
    """Draw value labels above each bar in a bar chart.

    `bar_records` is a list of (x_position, height) tuples — one per bar.
    Labels are placed slightly above each bar (offset = 2% of the chart's
    y-range) so they sit just clear of the bar top without dominating it.
    The y-axis range is expanded by ~8% to make headroom for the labels.

    Design notes:
    - 7.5pt navy text, sans-serif, centered horizontally on each bar
    - For bars at height 0 (or near-zero), labels are drawn at a small
      positive offset so they remain visible above the x-axis line
    - For negative bars, labels go below the bar (centered around top edge)
    """
    if not bar_records:
        return
    heights = [h for _, h in bar_records]
    max_h = max(heights)
    min_h = min(heights)
    y_range = max(max_h - min(0, min_h), max_h, 1.0)
    offset = y_range * 0.02  # 2% of the y-range above the bar top

    for x_pos, h in bar_records:
        if h >= 0:
            label_y = h + offset
            va = "bottom"
        else:
            label_y = h - offset
            va = "top"
        label_text = _format_bar_value(h, heights)
        ax.text(
            x_pos, label_y, label_text,
            ha="center", va=va,
            fontsize=7.5, color="#0f172a",
        )

    # Expand the y-axis upper bound by ~8% so the labels have headroom.
    # Without this, the top label can collide with the chart's top edge
    # or the title above it.
    current_top = max(max_h, 0)
    current_bottom = min(min_h, 0)
    headroom = y_range * 0.08
    ax.set_ylim(current_bottom, current_top + headroom)


def render_chart(inner: str) -> str:
    """
    Render a chart from the parsed fenced-div content into an inline SVG
    embedded in HTML, suitable for WeasyPrint PDF rendering.

    Supported chart types: line, bar, stacked-bar, scatter.

    Markdown syntax:
        ::: chart
        type: line                     # required: line, bar, stacked-bar, scatter
        title: FX Reserves trajectory  # optional, chart title shown above
        x: 2020 | 2021 | 2022 | 2023   # required for line, bar, stacked-bar
        y: 0.8 | 1.0 | 0.9 | 1.2       # required, one or more series
        y: optional-series-name | values...  # multi-series: name first, then values
        x-label: Year                  # optional axis title
        y-label: Months of imports     # optional axis title
        source: NBE, IMF Article IV    # optional caption under chart
        :::

    For scatter plots, use:
        type: scatter
        points: label | x | y          # one point per line
        x-label: GDP per capita
        y-label: HDI

    Style: navy-led palette to match the brief's institutional aesthetic.
    """
    # Lazy import — only load matplotlib when a chart is actually requested.
    # This keeps render times fast for charts-free briefs.
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
    except ImportError:
        return (
            '<div class="chart-error">'
            'Chart rendering requires matplotlib. Install with: '
            '<code>pip install matplotlib</code>'
            '</div>'
        )

    # Parse the parameters
    params = {}
    series = []        # list of (name, [values]) tuples for line/bar charts
    points = []        # list of (label, x, y) for scatter

    for raw_line in inner.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Single-value parameter: "key: value"
        m = re.match(r"^([a-z-]+):\s*(.+)$", line)
        if not m:
            continue
        key, value = m.group(1).lower(), m.group(2).strip()

        if key == "y":
            # Multi-series parser. Three forms:
            #   y: 0.8 | 1.0 | 0.9                (single series, no name)
            #   y: base | 49 | 45 | 42            (named series; name is non-numeric)
            #   y: 2024 | 49 | 45 | ...           (single series with leading numeric -- treat as data)
            parts = [p.strip() for p in value.split("|")]
            # Determine if the first part is a series name or data.
            # Try to parse first part as a number; if it fails, treat it as a label.
            try:
                float(parts[0])
                name = ""
                values_str = parts
            except ValueError:
                name = parts[0]
                values_str = parts[1:]
            try:
                values = [float(v) for v in values_str if v != ""]
            except ValueError:
                # Non-numeric data; record as zeros to fail gracefully
                values = [0.0 for _ in values_str if _ != ""]
            series.append((name, values))
        elif key == "points":
            # Scatter point: "label | x | y"
            parts = [p.strip() for p in value.split("|")]
            if len(parts) >= 3:
                try:
                    points.append((parts[0], float(parts[1]), float(parts[2])))
                except ValueError:
                    pass
        elif key == "x":
            params["x"] = [p.strip() for p in value.split("|")]
        else:
            params[key] = value

    chart_type = params.get("type", "line").lower()
    title = params.get("title", "")
    x_label = params.get("x-label", "")
    y_label = params.get("y-label", "")
    source = params.get("source", "")

    # Arabic text shaping. If any of the text content contains Arabic
    # characters, pre-shape it for matplotlib. The shaped strings are used
    # only for matplotlib rendering; the HTML output (title, source caption)
    # uses the original unshaped strings since WeasyPrint handles Arabic
    # shaping natively.
    chart_has_arabic = (
        _has_arabic_chars(title) or _has_arabic_chars(x_label)
        or _has_arabic_chars(y_label) or _has_arabic_chars(inner)
    )

    # Shape series names (used for legend labels) and x-axis tick labels.
    series = [
        (_shape_arabic(name), values) for name, values in series
    ]
    # Shape x-axis values (tick labels). Both Arabic-tagged years like
    # "2026 توقع" and pure-numeric values are handled — _shape_arabic
    # returns numeric strings unchanged.
    for key in ("x",):
        if key in params and isinstance(params[key], list):
            params[key] = [_shape_arabic(str(v)) for v in params[key]]

    # Shape axis labels. The title is NOT shaped here because we emit it
    # as HTML below (where WeasyPrint handles shaping natively); the title
    # variable used inside matplotlib is only set when title is non-Arabic.
    x_label_shaped = _shape_arabic(x_label)
    y_label_shaped = _shape_arabic(y_label)

    # Set up the figure. Size in inches: 16cm x 8cm at 100dpi → ~6.3 x 3.2 in
    # but we render at vector resolution so dpi only affects font metrics.
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Brief palette — navy primary, then sensible secondaries
    palette = [
        "#1a3a52",  # navy primary
        "#d97706",  # amber (caution / base case)
        "#b91c1c",  # red (downside)
        "#15803d",  # green (upside)
        "#6366f1",  # indigo (neutral secondary)
        "#7c3aed",  # purple (tertiary)
    ]

    if chart_type == "line":
        x_vals = params.get("x", [])
        x_pos = list(range(len(x_vals)))
        for i, (name, ys) in enumerate(series):
            color = palette[i % len(palette)]
            label = name if name else None
            # Plot only as many points as we have on both axes
            n = min(len(x_pos), len(ys))
            ax.plot(
                x_pos[:n], ys[:n],
                color=color, linewidth=2.0, marker="o", markersize=4,
                label=label,
            )
        ax.set_xticks(x_pos)
        ax.set_xticklabels(x_vals, fontsize=8)
        if any(name for name, _ in series):
            ax.legend(loc="best", frameon=False, fontsize=8)

    elif chart_type == "bar":
        x_vals = params.get("x", [])
        x_pos = list(range(len(x_vals)))
        n_series = len(series)
        # Whether to draw value labels above each bar. Default: yes. Opt-out
        # via `show-values: false` in the chart markdown for cases where
        # labels would add visual noise (e.g., dozens of small bars).
        show_values = params.get("show-values", "true").lower() != "false"

        # Collect all bar (x_position, height) tuples for later labeling.
        # We label after drawing so we can compute a single offset based on
        # the final y-axis range. Two-stage approach keeps the existing
        # drawing logic intact.
        bar_records = []  # list of (x_position, height) tuples

        if n_series == 1:
            name, ys = series[0]
            n = min(len(x_pos), len(ys))
            ax.bar(x_pos[:n], ys[:n], color=palette[0], width=0.6)
            for i in range(n):
                bar_records.append((x_pos[i], ys[i]))
        else:
            # Grouped bars
            bar_width = 0.8 / n_series
            for i, (name, ys) in enumerate(series):
                offset = (i - (n_series - 1) / 2) * bar_width
                n = min(len(x_pos), len(ys))
                ax.bar(
                    [x + offset for x in x_pos[:n]], ys[:n],
                    bar_width, color=palette[i % len(palette)],
                    label=name if name else None,
                )
                for k in range(n):
                    bar_records.append((x_pos[k] + offset, ys[k]))
            if any(name for name, _ in series):
                ax.legend(loc="best", frameon=False, fontsize=8)

        # Draw value labels above each bar
        if show_values and bar_records:
            _label_bars(ax, bar_records)

        ax.set_xticks(x_pos)
        # Auto-rotate x-axis labels when they would overlap. The figure is
        # ~6.4 inches wide; at fontsize 8, roughly 80 character-widths fit
        # across the plot. If the total character count exceeds that, or
        # any individual label is longer than the available cell width,
        # rotate labels to angle so they don't collide.
        total_chars = sum(len(str(v)) for v in x_vals)
        max_label = max((len(str(v)) for v in x_vals), default=0)
        per_cell_chars = 80 / max(1, len(x_vals))
        if total_chars > 60 or max_label > per_cell_chars:
            ax.set_xticklabels(x_vals, fontsize=8, rotation=30, ha="right")
        else:
            ax.set_xticklabels(x_vals, fontsize=8)

    elif chart_type == "stacked-bar":
        x_vals = params.get("x", [])
        x_pos = list(range(len(x_vals)))
        # For stacked bars, value labels show the total at the top of each
        # stack (per-segment labels would crowd small segments).
        show_values = params.get("show-values", "true").lower() != "false"

        # Track cumulative height so each new layer stacks on top
        bottom = [0.0] * len(x_pos)
        for i, (name, ys) in enumerate(series):
            n = min(len(x_pos), len(ys))
            ax.bar(
                x_pos[:n], ys[:n], bottom=bottom[:n],
                color=palette[i % len(palette)], width=0.6,
                label=name if name else None,
            )
            for k in range(n):
                bottom[k] += ys[k]

        # Label totals at top of each stack
        if show_values:
            stack_totals = [(x_pos[k], bottom[k]) for k in range(len(x_pos))]
            _label_bars(ax, stack_totals)

        ax.set_xticks(x_pos)
        # Same auto-rotation logic for stacked bars
        total_chars = sum(len(str(v)) for v in x_vals)
        max_label = max((len(str(v)) for v in x_vals), default=0)
        per_cell_chars = 80 / max(1, len(x_vals))
        if total_chars > 60 or max_label > per_cell_chars:
            ax.set_xticklabels(x_vals, fontsize=8, rotation=30, ha="right")
        else:
            ax.set_xticklabels(x_vals, fontsize=8)
        if any(name for name, _ in series):
            # For stacked bars, place legend outside the plot area on the
            # right since stacks fill the full plot height
            ax.legend(
                loc="center left", bbox_to_anchor=(1.01, 0.5),
                frameon=False, fontsize=8,
            )

    elif chart_type == "scatter":
        if points:
            xs = [p[1] for p in points]
            ys = [p[2] for p in points]
            ax.scatter(xs, ys, color=palette[0], s=80, alpha=0.85, edgecolors="white", linewidths=1.5)
            # Label each point with its name to the right
            for label, x, y in points:
                ax.annotate(
                    label, (x, y),
                    xytext=(6, 0), textcoords="offset points",
                    fontsize=8, color="#1a1a1a", va="center",
                )

    # Axis styling — minimal chartjunk, light grey gridlines, navy axes
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#94a3b8")
    ax.spines["bottom"].set_color("#94a3b8")
    ax.tick_params(axis="both", colors="#555", labelsize=8)
    ax.grid(True, axis="y", linestyle="--", linewidth=0.5, color="#e2e8f0", zorder=0)
    ax.set_axisbelow(True)

    # Font family selection. When the chart contains Arabic, probe for the
    # first installed Arabic-capable font from a prioritized chain.
    # matplotlib's family-list fallthrough finds the first font that EXISTS
    # at all (not the first that has the requested glyphs), so a bare
    # ["Amiri", "serif"] silently falls to DejaVu Serif on systems without
    # Amiri — and DejaVu Serif has zero Arabic glyphs, producing tofu/boxes
    # at render time. We rely on arabic_reshaper + python-bidi (called via
    # _shape_arabic earlier) for letter joining and bidi — matplotlib itself
    # does not do Arabic shaping.
    chart_font_family = _resolve_arabic_font_family() if chart_has_arabic else ["serif"]

    if x_label_shaped:
        ax.set_xlabel(x_label_shaped, fontsize=9, color="#1a3a52", labelpad=8,
                      fontfamily=chart_font_family)
    if y_label_shaped:
        ax.set_ylabel(y_label_shaped, fontsize=9, color="#1a3a52", labelpad=8,
                      fontfamily=chart_font_family)
    # We intentionally do NOT set the title via ax.set_title() here when
    # it contains Arabic. For English titles, the in-figure title is fine.
    # For Arabic titles, we emit the title as HTML below where WeasyPrint
    # can shape the Arabic properly.
    if title and not _has_arabic_chars(title):
        ax.set_title(title, fontsize=11, color="#1a3a52",
                     fontweight="normal", pad=12, loc="left",
                     fontfamily=chart_font_family)

    # Apply the Arabic font to tick labels and any legend text. Tick labels
    # were set with shaped strings (via the params["x"] shaping above),
    # but they need the font family override to find Amiri's glyphs.
    if chart_has_arabic:
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontfamily(chart_font_family)
        leg = ax.get_legend()
        if leg is not None:
            for text in leg.get_texts():
                text.set_fontfamily(chart_font_family)

    plt.tight_layout()

    # Render to PNG (base64-encoded data URI) for embedding in HTML.
    # Why PNG, not SVG: matplotlib SVGs use defs/clip-paths/font references
    # that WeasyPrint doesn't always handle, producing blank or partial
    # output. A raster PNG at 200 DPI looks identical to SVG for a print
    # PDF and avoids every SVG-rendering pitfall.
    import io
    import base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    png_bytes = buf.getvalue()
    png_b64 = base64.b64encode(png_bytes).decode("ascii")
    img_tag = f'<img src="data:image/png;base64,{png_b64}" alt="{title or chart_type + " chart"}" />'

    # Emit Arabic titles as HTML above the figure (same pattern as maps.py).
    # English titles stay inside the figure via ax.set_title above.
    title_html = ""
    if title and _has_arabic_chars(title):
        title_html = f'<h3 class="chart-title">{title}</h3>'

    # Wrap in a container with optional source caption
    # Source caption: localized when source itself contains Arabic.
    source_label = "المصدر" if _has_arabic_chars(source) else "Source"
    caption = f'<div class="chart-source">{source_label}: {source}</div>' if source else ""
    return f'<div class="chart">{title_html}{img_tag}{caption}</div>'


# Cache for loaded GeoDataFrames — read shapefiles once per process.
_geo_cache = {}


