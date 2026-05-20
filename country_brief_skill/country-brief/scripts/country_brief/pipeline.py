"""
pipeline.py — Main render pipeline.

render_basic_markdown() converts the brief's markdown to HTML, calling
out to the fenced-div dispatcher, footnote handler, anchor injector,
and other utilities. render_pdf() takes the HTML and produces a PDF
via WeasyPrint.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from .inline import (
    extract_footnotes, render_footnote_refs,
    inject_heading_anchors, wrap_trajectory_arrows, wrap_table_arrows,
)
from .fenced_divs import render_fenced_divs
from .toc import render_toc


def render_basic_markdown(md: str) -> str:
    """
    Minimal markdown-to-HTML converter — covers headings, bold, italics,
    bullets, numbered lists, paragraphs, simple tables, and horizontal rules.

    This intentionally avoids a heavy dependency. Country briefs use a
    restricted markdown vocabulary, so a focused converter is reliable.
    """
    # First: fenced divs (do this before paragraph splitting)
    md = render_fenced_divs(md)

    # Page break marker
    md = re.sub(r"^---PAGE---\s*$", '<div class="page-break"></div>', md, flags=re.MULTILINE)

    lines = md.split("\n")
    out = []
    in_list = None  # 'ul' or 'ol'
    in_table = False
    table_header_done = False
    paragraph_buffer = []
    # Tracks which end-matter wrapper div is currently open (bibliography
    # or methodological). The next H2 closes the prior wrapper before
    # opening its own. Single-state because end-matter sections don't nest.
    open_wrapper = None  # one of None, "bibliography", "methodological"

    def flush_paragraph():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            text = " ".join(paragraph_buffer).strip()
            if text:
                # Inline transforms
                text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
                text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
                out.append(f"<p>{text}</p>")
            paragraph_buffer = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>")
            in_list = None

    def close_table():
        nonlocal in_table, table_header_done
        if in_table:
            out.append("</tbody></table>")
            in_table = False
            table_header_done = False

    for raw in lines:
        line = raw.rstrip()

        # Empty line -> flush paragraph, close lists/tables
        if not line.strip():
            flush_paragraph()
            close_list()
            close_table()
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            flush_paragraph()
            close_list()
            close_table()
            level = len(m.group(1))
            text = m.group(2).strip()
            text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
            text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
            # Special: bibliography and methodological back-matter sections
            # get class wrappers so they pick up metadata-block typography.
            # Both end-matter sections render at the same visual register as
            # Notes (smaller font, denser line-height) — see brief-template.html
            # .metadata-block CSS rule and .bibliography / .methodological
            # layout rules that extend it.
            #
            # Any new H2 closes the currently-open wrapper before opening
            # its own (no nesting of end-matter sections). H3+ headings don't
            # close wrappers because they're sub-headings within a section.
            text_lower = text.strip().lower()
            text_clean = text.strip()
            # Language-aware bibliography heading detection. English variants:
            # "Bibliography" (US/UK). Arabic variants: المراجع (the references)
            # and المصادر والمراجع (sources and references), both standard
            # institutional forms.
            is_bib_heading = (
                text_lower.startswith("bibliography")
                or text_clean.startswith("المراجع")
                or text_clean.startswith("المصادر والمراجع")
                or text_clean.startswith("المصادر")
            )
            # Language-aware methodology heading detection. English variants:
            # "Methodological back-matter" / "Methodology". Arabic variants:
            # منهجية التقرير (the report's methodology — preferred institutional
            # form per arabic-glossary.md), منهجية الموجز, and the calque
            # الذيل المنهجي (kept for backward compatibility with earlier briefs
            # but the glossary now recommends منهجية التقرير).
            is_method_heading = (
                text_lower.startswith("methodological")
                or text_lower.startswith("methodology")
                or text_clean.startswith("منهجية التقرير")
                or text_clean.startswith("منهجية الموجز")
                or text_clean.startswith("المنهجية")
                or text_clean.startswith("الذيل المنهجي")
            )
            if level == 2:
                if open_wrapper is not None:
                    out.append("</div>")
                    open_wrapper = None
                if is_bib_heading:
                    out.append('<div class="bibliography metadata-block">')
                    out.append(f"<h{level}>{text}</h{level}>")
                    open_wrapper = "bibliography"
                elif is_method_heading:
                    out.append('<div class="methodological metadata-block">')
                    out.append(f"<h{level}>{text}</h{level}>")
                    open_wrapper = "methodological"
                else:
                    out.append(f"<h{level}>{text}</h{level}>")
            else:
                out.append(f"<h{level}>{text}</h{level}>")
            continue

        # Horizontal rule (acts as a soft section break)
        if re.match(r"^---+$", line):
            flush_paragraph()
            close_list()
            close_table()
            out.append("<hr>")
            continue

        # Bullet list
        if re.match(r"^[\-\*]\s+", line):
            flush_paragraph()
            close_table()
            if in_list != "ul":
                close_list()
                out.append("<ul>")
                in_list = "ul"
            item = re.sub(r"^[\-\*]\s+", "", line).strip()
            item = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", item)
            out.append(f"<li>{item}</li>")
            continue

        # Numbered list
        if re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            close_table()
            if in_list != "ol":
                close_list()
                out.append("<ol>")
                in_list = "ol"
            item = re.sub(r"^\d+\.\s+", "", line).strip()
            item = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", item)
            item = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", item)
            out.append(f"<li>{item}</li>")
            continue

        # Table row (pipe-delimited)
        if "|" in line and line.strip().startswith("|"):
            flush_paragraph()
            close_list()

            # Header separator row (|---|---|)
            if re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
                # Convert previously-buffered header to <th>
                # (we handled the header on the previous line as <td>; rewrite)
                if out and out[-1].startswith("<tr><td"):
                    out[-1] = out[-1].replace("<td", "<th").replace("</td>", "</th>")
                if not table_header_done:
                    out.append("</tr></thead><tbody>")
                    table_header_done = True
                continue

            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            def _fmt_cell(c):
                c = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", c)
                c = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", c)
                return f"<td>{c}</td>"
            cells_html = "".join(_fmt_cell(c) for c in cells)

            if not in_table:
                out.append('<table class="compare-table"><thead>')
                in_table = True
                table_header_done = False
            out.append(f"<tr>{cells_html}</tr>")
            continue

        # Default: paragraph text (accumulate)
        # Allow inline HTML (e.g., from fenced divs) to pass through
        if line.lstrip().startswith("<") and ">" in line:
            flush_paragraph()
            close_list()
            close_table()
            out.append(line)
            continue

        paragraph_buffer.append(line.strip())

    # Final flush
    flush_paragraph()
    close_list()
    close_table()

    # Close any still-open end-matter wrapper at document end.
    if open_wrapper is not None:
        out.append("</div>")
        open_wrapper = None

    html = "\n".join(out)

    # Bibliography auto-numbering: the analyst may write entries as paragraphs
    # ("World Bank. WDI 2024."), as a numbered markdown list ("1. World Bank..."),
    # or as a mix with blank lines between entries (which the minimal markdown
    # parser closes <ol>s on, producing many one-item lists each numbered "1.").
    # Regardless of input form, the rendered bibliography should be a single
    # numbered list. This post-pass normalizes all three cases by collecting
    # every <p> and <li> child inside the bibliography div and emitting one
    # <ol> with sequential numbering.
    html = _normalize_bibliography(html)

    return html


def _normalize_bibliography(html: str) -> str:
    """Convert the contents of the bibliography div into one numbered list.

    Operates on the rendered HTML (post-paragraph-flush, post-list-close).
    Pulls every <p>...</p> and <li>...</li> inside the bibliography div, in
    document order, and emits a single <ol> of <li> items. Idempotent for
    bibliographies already authored as one numbered markdown list.
    """
    # Match the bibliography div and capture (head, body, trailing closer if any).
    # The renderer emits <div class="bibliography metadata-block"><h2>Bibliography</h2>...
    # — second class added so the section inherits shared end-matter
    # typography. Pattern accepts either single or compound class attribute.
    pattern = re.compile(
        r'(<div class="bibliography(?:\s+metadata-block)?">\s*<h2[^>]*>[^<]*</h2>)(.*?)(\Z|</div>)',
        re.DOTALL,
    )
    m = pattern.search(html)
    if not m:
        return html
    head, body, tail = m.group(1), m.group(2), m.group(3)

    # Collect entries: every <p>...</p> and every <li>...</li>, in order.
    entries = re.findall(r'<(?:p|li)>(.*?)</(?:p|li)>', body, re.DOTALL)
    entries = [e.strip() for e in entries if e.strip()]
    if not entries:
        return html

    ol_items = "\n".join(f"<li>{e}</li>" for e in entries)
    new_body = f"\n<ol class=\"bibliography-list\">\n{ol_items}\n</ol>\n"
    # Reattach with the original trailing closer (either </div> or end-of-string).
    closer = "</div>" if tail == "" else tail
    return html[:m.start()] + head + new_body + closer + html[m.end():]


def render_footnotes_section(footnotes: dict, order: list, language: str = "en") -> str:
    """Render the numbered footnotes block in Chicago style.

    The heading defaults to "Notes" but switches to "ملاحظات" for Arabic
    briefs (language='ar'). To add another language, extend the dictionary
    below; analysts should never see English heading on a non-English brief.
    """
    if not order:
        return ""
    heading_by_lang = {
        "en": "Notes",
        "ar": "ملاحظات",
    }
    heading = heading_by_lang.get(language, "Notes")
    items = []
    for i, fn_id in enumerate(order, start=1):
        content = footnotes[fn_id]
        # Light inline transforms
        content = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", content)
        back = f' <a href="#fnref-{i}-1" style="text-decoration:none;color:#1a3a52;">↩</a>'
        items.append(f'<li id="fn-{i}">{content}{back}</li>')
    return (
        '<div class="footnotes metadata-block">\n'
        f"<h3>{heading}</h3>\n"
        "<ol>\n" + "\n".join(items) + "\n</ol>\n"
        "</div>"
    )


def render_pdf(html_path: str, pdf_path: str):
    """
    Render HTML to PDF. Try WeasyPrint first (best CSS support including
    @page rules and footnote-area features), fall back to wkhtmltopdf.
    """
    try:
        from weasyprint import HTML
        HTML(filename=html_path).write_pdf(pdf_path)
        return "weasyprint"
    except ImportError:
        pass
    except Exception as e:
        print(f"WeasyPrint failed: {e}", file=sys.stderr)

    # Fallback: wkhtmltopdf
    import subprocess
    try:
        subprocess.run(
            ["wkhtmltopdf", "--enable-local-file-access",
             "--margin-top", "20mm", "--margin-bottom", "20mm",
             "--margin-left", "18mm", "--margin-right", "18mm",
             html_path, pdf_path],
            check=True
        )
        return "wkhtmltopdf"
    except Exception as e:
        raise RuntimeError(
            "PDF rendering failed. Install WeasyPrint "
            "(`pip install weasyprint --break-system-packages`) "
            "or wkhtmltopdf."
        ) from e


