"""
toc.py — Table of contents rendering.

render_toc() inspects the markdown to find top-level headings and
classifies them into spine sections (always present) vs optional
modules (which appear under the "OPTIONAL MODULES" subheader). The
resulting HTML uses CSS counter-reset for the leader dots and right-
aligned page numbers.
"""
import re

from .inline import extract_top_level_headings, slugify_heading


def render_toc(md: str, language: str = "en") -> str:
    """
    Generate the table of contents HTML from the markdown source.

    Produces a TOC page that lists every top-level section with a
    clickable hyperlink to its anchor, plus an auto-filled page number.
    Page numbers are resolved by WeasyPrint at render time using
    target-counter (see CSS in brief-template.html).

    The TOC is a separate page with its own page-break-after rule so
    Section 1 starts fresh.

    Visual structure: spine sections (1-6 plus 19 Outlook) render in
    stronger weight; optional modules (7-18) are visually slightly
    muted. A single "Optional modules" group header sits between the
    last spine section and the first module — when the style returns
    to spine weight at Section 19, the reader sees "back to core"
    without a redundant second header. Executive Summary and
    Bibliography sit at the boundaries as front/back matter.
    """
    headings = extract_top_level_headings(md)
    if not headings:
        return ""

    # Classify each heading by section number prefix:
    #   no number, before first numbered  → frontmatter (Executive Summary)
    #   no number, after last numbered    → backmatter  (Bibliography)
    #   1, 1.5, 2-6, 19                    → spine (core analysis)
    #   7-18                               → module
    def classify(title: str) -> str:
        m = re.match(r"^\s*(\d+)(?:\.\d+)?\.", title)
        if not m:
            return "unnumbered"  # frontmatter or backmatter; resolved below
        n = int(m.group(1))
        if n in (1, 2, 3, 4, 5, 6, 19):
            return "spine"
        if 7 <= n <= 18:
            return "module"
        return "spine"  # fallback for any future numbered section

    # First pass: classify; convert unnumbered entries to frontmatter or
    # backmatter based on their position relative to numbered entries.
    classes = [classify(t) for t, _ in headings]
    first_numbered = next(
        (i for i, c in enumerate(classes) if c in ("spine", "module")),
        len(classes)
    )
    last_numbered = next(
        (i for i in range(len(classes) - 1, -1, -1)
         if classes[i] in ("spine", "module")),
        -1
    )
    for i, c in enumerate(classes):
        if c == "unnumbered":
            classes[i] = "frontmatter" if i < first_numbered else "backmatter"

    # Second pass: emit rows, injecting the "Optional modules" header
    # before the first module entry.
    rows = []
    module_header_emitted = False
    for (title, anchor), css_class in zip(headings, classes):
        if css_class == "module" and not module_header_emitted:
            rows.append(
                '<li class="toc-group-header">Optional modules</li>'
            )
            module_header_emitted = True
        rows.append(
            f'<li class="toc-entry toc-{css_class}">'
            f'<a class="toc-link" href="#{anchor}">'
            f'<span class="toc-title-text">{title}</span>'
            f'<span class="toc-leader"></span>'
            '</a>'
            '</li>'
        )

    heading_by_lang = {
        "en": "Contents",
        "ar": "المحتويات",
    }
    toc_heading = heading_by_lang.get(language, "Contents")
    return (
        '<div class="toc">'
        f'<h2 class="toc-title">{toc_heading}</h2>'
        '<ol class="toc-list">'
        + "".join(rows) +
        '</ol>'
        '</div>'
    )


