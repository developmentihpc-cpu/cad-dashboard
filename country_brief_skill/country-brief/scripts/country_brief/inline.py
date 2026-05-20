"""
inline.py — Inline markdown processing: footnotes, anchors, trajectory arrows.

These are utilities used across the rendering pipeline. They have no
dependencies on other modules in this package — only stdlib (re).
"""
import re


def extract_footnotes(md: str):
    """
    Pull out Pandoc-style footnote definitions ([^N]: ...) and return:
      - body markdown with definitions removed
      - dict mapping footnote id -> content
      - ordered list of ids in order of first reference
    """
    fn_def_pattern = re.compile(r"^\[\^([^\]]+)\]:\s*(.+(?:\n[ \t]+.+)*)", re.MULTILINE)
    footnotes = {}
    for m in fn_def_pattern.finditer(md):
        fn_id = m.group(1)
        content = m.group(2).strip()
        # Strip leading whitespace from continuation lines
        content = re.sub(r"\n[ \t]+", " ", content)
        footnotes[fn_id] = content

    body = fn_def_pattern.sub("", md)

    # Order by first reference
    ref_pattern = re.compile(r"\[\^([^\]]+)\]")
    order = []
    seen = set()
    for m in ref_pattern.finditer(body):
        fn_id = m.group(1)
        if fn_id not in seen and fn_id in footnotes:
            order.append(fn_id)
            seen.add(fn_id)

    return body, footnotes, order


def render_footnote_refs(html: str, order: list):
    """
    Replace [^id] with numbered superscript references, where the number
    corresponds to the order of first appearance.

    Also inserts a small superscript comma between truly-adjacent footnote
    refs so [^36][^37] reads as "36,37" rather than "3637". This is done
    via regex post-pass on the rendered HTML rather than CSS, because the
    CSS adjacent-sibling combinator (.footnote-ref + .footnote-ref) treats
    refs in the same paragraph as adjacent siblings even when prose text
    separates them.
    """
    id_to_num = {fn_id: i + 1 for i, fn_id in enumerate(order)}
    seen_first = set()

    def repl(m):
        fn_id = m.group(1)
        if fn_id not in id_to_num:
            return m.group(0)
        num = id_to_num[fn_id]
        anchor = f"fn-{num}"
        ref_anchor = f"fnref-{num}-{len([x for x in seen_first if x == fn_id]) + 1}"
        seen_first.add(fn_id)
        return f'<sup class="footnote-ref"><a id="{ref_anchor}" href="#{anchor}">{num}</a></sup>'

    html = re.sub(r"\[\^([^\]]+)\]", repl, html)

    # Insert a comma between truly-adjacent footnote refs (no whitespace
    # or other content between them). Matches "</sup><sup class=...>"
    # and replaces with "</sup><sup class='footnote-sep'>,</sup><sup ...>".
    # The inserted span is styled minimally — same superscript position,
    # small comma.
    html = re.sub(
        r'(</sup>)(<sup class="footnote-ref">)',
        r'\1<sup class="footnote-sep">,</sup>\2',
        html
    )
    return html


def _process_inline_markdown(text: str) -> str:
    """Apply minimal inline markdown processing — bold and italic — for use
    inside fenced-div content. Order matters: bold before italic so that
    **text** doesn't get partially eaten by the italic pattern.

    This exists because WeasyPrint receives an HTML document where fenced
    divs were already rewritten to <div> wrappers. Markdown parsers
    typically treat content inside <div> as raw HTML and skip inline
    formatting, so any *italic* or **bold** inside scenario/decision-
    implication/etc. blocks would render as literal asterisks unless we
    pre-process them here.
    """
    # Bold: **text** -> <strong>text</strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # Italic: *text* -> <em>text</em>
    text = re.sub(r"\*([^*\n]+?)\*", r"<em>\1</em>", text)
    return text


def wrap_trajectory_arrows(html: str) -> str:
    """
    Find list items that begin with a trajectory arrow (↑ → ↓ ⇅) and
    wrap the arrow in a styled span for color/sizing.
    """
    arrow_class = {
        "↑": "traj-up",
        "→": "traj-stable",
        "↓": "traj-down",
        "⇅": "traj-volatile",
    }

    def repl(m):
        arrow = m.group(1)
        rest = m.group(2)
        cls = arrow_class.get(arrow, "traj-stable")
        return f'<li><span class="traj-arrow {cls}">{arrow}</span>{rest}</li>'

    pattern = re.compile(r"<li>([↑→↓⇅])\s+(.+?)</li>", re.DOTALL)
    return pattern.sub(repl, html)


def wrap_table_arrows(html: str) -> str:
    """
    Find trend arrows (↑ → ↓ ⇅) anywhere inside <td> cells and wrap them
    in styled spans. Used to color-code trend directions in the macro
    indicators table (Section 3) and any future table that uses arrows.

    Reuses the .snapshot-trend.* CSS classes from the country snapshot
    (those classes are general-purpose styled arrows, not snapshot-only).
    """
    arrow_class = {
        "↑": "up",
        "→": "stable",
        "↓": "down",
        "⇅": "volatile",
    }

    def repl_cell(m):
        cell_content = m.group(1)
        # Wrap each arrow occurrence in this cell
        for arrow, cls in arrow_class.items():
            cell_content = cell_content.replace(
                arrow,
                f'<span class="snapshot-trend {cls}">{arrow}</span>'
            )
        return f'<td{m.group(0)[3:m.group(0).index(">")]}>{cell_content}</td>'

    # Simpler approach: just find arrows inside <td>...</td> blocks
    # and wrap them. The pattern is non-greedy to handle one cell at a time.
    def repl_arrow_in_td(match):
        full_cell = match.group(0)
        opening = match.group(1)
        content = match.group(2)
        for arrow, cls in arrow_class.items():
            content = content.replace(
                arrow,
                f'<span class="snapshot-trend {cls}">{arrow}</span>'
            )
        return f'{opening}{content}</td>'

    pattern = re.compile(r"(<td[^>]*>)(.*?)</td>", re.DOTALL)
    return pattern.sub(repl_arrow_in_td, html)


def slugify_heading(text: str) -> str:
    """
    Convert a heading title into a URL-safe anchor ID.

    Examples:
        "Executive Summary"              → "section-executive-summary"
        "1. Country Snapshot"            → "section-1-country-snapshot"
        "1.5. Bilateral Relations: UAE"  → "section-1-5-bilateral-relations-uae"
        "10. Climate Vulnerability"      → "section-10-climate-vulnerability"

    The "section-" prefix is added to avoid collisions with other IDs
    in the document and to make the purpose explicit when inspecting HTML.
    """
    # Lowercase
    slug = text.lower()
    # Replace non-alphanumeric with hyphens
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return f"section-{slug}"


def inject_heading_anchors(html: str) -> str:
    """
    Find every top-level <h2> in the HTML and inject an id attribute
    derived from the heading text. Used so the TOC can hyperlink to
    each section via #section-... anchors.

    Sub-headings (h3, h4) are not anchored — the TOC covers top-level
    sections only.
    """
    def repl(m):
        opening_tag = m.group(1)  # full opening tag, e.g. "<h2>" or "<h2 class='foo'>"
        text = m.group(2)
        # Skip if already has an id (defensive)
        if "id=" in opening_tag:
            return m.group(0)
        # Strip HTML tags from text for slug generation (e.g., inline formatting)
        plain_text = re.sub(r"<[^>]+>", "", text).strip()
        if not plain_text:
            return m.group(0)
        anchor = slugify_heading(plain_text)
        # Insert id attribute before the closing > of the opening tag
        new_opening = opening_tag.rstrip(">") + f' id="{anchor}">'
        return f'{new_opening}{text}</h2>'

    pattern = re.compile(r"(<h2[^>]*>)(.*?)</h2>", re.DOTALL)
    return pattern.sub(repl, html)


def extract_top_level_headings(md: str) -> list:
    """
    Scan markdown source for top-level (## ) headings and return a list
    of (title, anchor) pairs, in document order.

    Used by the TOC generator. Operates on raw markdown rather than
    rendered HTML so it doesn't have to parse around fenced divs or
    other structural elements.
    """
    headings = []
    in_code_block = False
    for line in md.split("\n"):
        # Skip headings inside fenced code blocks
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        # Match "## " at the start of the line (top-level section heading)
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            title = m.group(1).strip()
            anchor = slugify_heading(title)
            headings.append((title, anchor))
    return headings


# Mapping from manifest module keys to (section number, human-readable name).
# Used by validate_manifest to cross-check declared module intent against the
# section headers actually present in the markdown.


