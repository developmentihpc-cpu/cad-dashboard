"""
cli.py — Command-line entry point.

Parses arguments, reads the input markdown, runs validation, hands off
to the pipeline, writes the PDF. Imported by render_brief.py shim for
backward compatibility.
"""
import argparse
import os
import re
import sys
from pathlib import Path

from .validation import validate_brief, validate_manifest_against_markdown
from .pipeline import render_basic_markdown, render_pdf, render_footnotes_section
from .toc import render_toc
from .inline import (
    extract_footnotes, render_footnote_refs,
    inject_heading_anchors, wrap_trajectory_arrows, wrap_table_arrows,
)
from .maps import _country_flag_path


def main():
    parser = argparse.ArgumentParser(
        description="Render a country brief from markdown to styled PDF."
    )
    parser.add_argument("--input", required=True, help="Path to the markdown brief.")
    parser.add_argument("--output", required=True, help="Path for the output PDF.")
    parser.add_argument("--country", required=True, help="Country name for cover and header.")
    parser.add_argument("--subtitle", default="", help="Subtitle (optional, e.g., the brief's angle).")
    parser.add_argument("--date", default="", help="Date of brief (e.g., 'May 2026').")
    parser.add_argument("--audience", default="", help="Intended audience.")
    parser.add_argument("--angle", default="", help="Brief's specific angle / purpose.")
    parser.add_argument("--author", default="", help="Preparer / author / unit.")
    parser.add_argument(
        "--home-country", default="UAE",
        help=(
            "Home country / institutional perspective the brief is read from. "
            "When set, the brief includes a bilateral-relations section at "
            "position 1.5 (between Snapshot and Political Context). "
            "Pass 'none' to suppress this section entirely. Default: UAE."
        ),
    )
    parser.add_argument("--template",
                        default=str(Path(__file__).parent.parent.parent / "assets" / "brief-template.html"),
                        help="Path to the HTML template.")
    parser.add_argument(
        "--manifest", default="",
        help=(
            "Optional path to a YAML manifest declaring which modules fire. "
            "When provided, the validator cross-checks the manifest against "
            "the section headers in the markdown and warns on inconsistency. "
            "See tests/fixtures/manifest-example.yml for the schema."
        ),
    )
    parser.add_argument("--keep-html", action="store_true",
                        help="Keep the intermediate HTML file (for debugging).")
    parser.add_argument("--toc", action="store_true",
                        help=(
                            "Include a clickable table of contents page "
                            "between the cover and the executive summary. "
                            "Recommended for briefs longer than ~15 pages. "
                            "Default: off."
                        ))
    parser.add_argument(
        "--no-disclaimer", action="store_true",
        help=(
            "Suppress the AI-provenance disclaimer on the cover page. "
            "Use only when the brief has been substantially edited or "
            "reviewed by humans such that the AI-generated framing no "
            "longer applies. Default: disclaimer is shown."
        ),
    )
    parser.add_argument(
        "--disclaimer-text", default="",
        help=(
            "Override the default disclaimer text with custom wording "
            "(e.g., for a producing organization's specific legal language). "
            "When set, this text replaces the default. Ignored if "
            "--no-disclaimer is also set."
        ),
    )
    parser.add_argument(
        "--no-flag", action="store_true",
        help=(
            "Suppress the country flag on the cover page. By default, "
            "the flag is auto-resolved from the country name and "
            "rendered below the title. Default: flag is shown when available."
        ),
    )
    parser.add_argument(
        "--flag-path", default="",
        help=(
            "Override the default flag with a specific image file. "
            "Path is resolved relative to the working directory. Useful "
            "for custom flags (sub-national entities, regional unions, "
            "historical flags). Ignored if --no-flag is also set."
        ),
    )
    parser.add_argument(
        "--language", default="en", choices=["en", "ar"],
        help=(
            "Output language for the brief. 'en' (default) produces an "
            "English brief with LTR layout. 'ar' produces an Arabic brief "
            "with RTL layout, Arabic textbook fonts, and language-aware "
            "rendering. The Arabic version must be composed natively in "
            "Arabic (not translated from English) using the references "
            "in references/arabic-style.md, arabic-glossary.md, and "
            "arabic-names.md."
        ),
    )
    parser.add_argument(
        "--strict", action="store_true",
        help=(
            "Promote three structural warnings to render-blocking errors: "
            "zero footnote references, no ::: risk-matrix block, no "
            "Recommendations section. Use for production renders where an "
            "incomplete brief should refuse to render rather than ship "
            "with a missing core component. Default (warn-only) preserves "
            "analyst autonomy for iterative drafts. Other warnings "
            "(footnote density, bottom-line length, series-leakage) stay "
            "as warnings even in strict mode — those involve judgment "
            "calls the analyst should make."
        ),
    )

    args = parser.parse_args()

    if not args.date:
        from datetime import datetime
        args.date = datetime.now().strftime("%B %Y")

    # Read brief
    md_text = Path(args.input).read_text(encoding="utf-8")

    # Run pre-render validation. Warnings go to stderr so the analyst sees
    # them but they don't block rendering. The principle: noisy failure
    # beats silent failure — a missing footnote should generate a visible
    # warning, not just a dangling reference in the final PDF.
    #
    # --strict flips warn → error for three "binding" structural checks
    # (zero footnotes, no risk-matrix, no Recommendations). See
    # validate_brief() docstring for the rationale.
    warnings, errors = validate_brief(md_text, strict=args.strict)

    # If a manifest was provided, cross-check it against the markdown.
    # Manifest validation is purely additive — it never blocks rendering,
    # only surfaces declared-vs-actual inconsistencies.
    if args.manifest:
        try:
            import yaml
            manifest_text = Path(args.manifest).read_text(encoding="utf-8")
            manifest = yaml.safe_load(manifest_text) or {}
            manifest_warnings = validate_manifest_against_markdown(manifest, md_text)
            warnings.extend(manifest_warnings)
        except ImportError:
            warnings.append(
                "--manifest provided but PyYAML is not installed. "
                "Install with: pip install pyyaml"
            )
        except FileNotFoundError:
            warnings.append(f"--manifest path not found: {args.manifest}")
        except yaml.YAMLError as e:
            warnings.append(f"--manifest YAML parse error: {e}")

    # Validate --home-country consistency against the markdown's section 1.5.
    # The brief should have a `## 1.5. Bilateral Relations` heading (or its
    # Arabic equivalent `## 1.5. العلاقات الثنائية`, or any other language)
    # when --home-country is set to a real country, and should NOT have one
    # when --home-country is "none". This catches the most common CLI/markdown
    # inconsistency: writing a UAE-focused brief but passing --home-country
    # India, or omitting section 1.5 but forgetting to pass --home-country
    # none.
    #
    # Detection is by section number (1.5), not by the heading's text content.
    # This makes the check language-agnostic — Arabic, French, or other
    # language briefs are detected as having Section 1.5 if they have a
    # heading numbered "1.5".
    import re
    has_bilateral_section = bool(re.search(
        r"^##\s+1\.5\.?\s+\S", md_text, re.MULTILINE
    ))
    home_country_norm = (args.home_country or "").strip().lower()
    if home_country_norm in ("none", "", "n/a"):
        if has_bilateral_section:
            warnings.append(
                "--home-country is 'none' but markdown contains a Section 1.5 "
                "(Bilateral Relations) heading. Either pass --home-country with a "
                "country name or remove the Section 1.5 heading from the markdown."
            )
    else:
        if not has_bilateral_section:
            warnings.append(
                f"--home-country is set to '{args.home_country}' but markdown "
                "has no Section 1.5 (Bilateral Relations) heading. Either add "
                "the section to the markdown or pass --home-country none."
            )

    if warnings or errors:
        import sys
        if warnings:
            print(f"Pre-render warnings ({len(warnings)}):", file=sys.stderr)
            for w in warnings:
                print(f"  - {w}", file=sys.stderr)
        if errors:
            print(f"Pre-render errors ({len(errors)}):", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
        print("", file=sys.stderr)  # blank line before render output

    # Errors block rendering. Under default mode the errors list is empty
    # (validate_brief only populates it under strict=True for now); under
    # --strict the three promoted checks become render-blocking. Either way,
    # the principle is: errors → no PDF; warnings → noisy success.
    if errors:
        print(
            f"Refusing to render: {len(errors)} blocking error(s) above. "
            f"Fix the listed issues, or remove --strict to render anyway.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Extract footnotes
    md_body, footnotes, fn_order = extract_footnotes(md_text)

    # Render markdown to HTML
    body_html = render_basic_markdown(md_body)
    body_html = wrap_trajectory_arrows(body_html)
    body_html = wrap_table_arrows(body_html)
    body_html = render_footnote_refs(body_html, fn_order)
    # Inject anchor IDs onto every <h2> so the TOC (and any other
    # cross-references) can link to sections.
    body_html = inject_heading_anchors(body_html)

    # Append footnotes block (will appear just before bibliography or at end)
    fn_html = render_footnotes_section(footnotes, fn_order, language=args.language)

    # Splice footnotes before bibliography if present, else append.
    # Pattern accounts for the bibliography div carrying the metadata-block
    # second class (see pipeline.py rendering).
    bib_div_pattern = re.compile(r'<div class="bibliography(?:\s+metadata-block)?">')
    bib_match = bib_div_pattern.search(body_html)
    if bib_match:
        body_html = (
            body_html[:bib_match.start()]
            + fn_html + "\n"
            + body_html[bib_match.start():]
        )
    else:
        body_html = body_html + "\n" + fn_html

    # If --toc is set, generate the TOC HTML from the markdown source
    # and prepend it to the body. The TOC lands on its own page (CSS
    # page-break-after) between the cover and the executive summary.
    if args.toc:
        toc_html = render_toc(md_body, language=args.language)
        if toc_html:
            body_html = toc_html + "\n" + body_html

    # Load template
    template = Path(args.template).read_text(encoding="utf-8")

    # Conditionally render meta rows — empty values mean the row is omitted
    # entirely rather than showing a placeholder. This keeps the cover clean
    # when the user hasn't supplied an audience or angle.
    def _meta_row(label: str, value: str) -> str:
        if not value or not value.strip():
            return ""
        return f'<div class="row"><span class="label-sm">{label}</span> {value}</div>'

    audience_row = _meta_row("Prepared for", args.audience)
    angle_row = _meta_row("Angle", args.angle)
    author_row = _meta_row("Prepared by", args.author)

    subtitle_block = (
        f'<div class="subtitle">{args.subtitle}</div>'
        if args.subtitle and args.subtitle.strip()
        else ""
    )

    # AI-provenance disclaimer block. Default wording discloses (1) AI
    # generation, (2) public-source basis, (3) non-attribution to any
    # producing organization, and (4) reader-verification guidance.
    # The --no-disclaimer flag suppresses the block; --disclaimer-text
    # overrides the default wording.
    DEFAULT_DISCLAIMER_EN = (
        "This brief is AI-generated using publicly available sources. "
        "Judgments and analytical framings reflect the AI system's "
        "synthesis, not the views of any producing organization or its "
        "employees. Readers should verify specific claims against the "
        "cited sources before relying on them for decisions."
    )
    DEFAULT_DISCLAIMER_AR = (
        "أُعد هذا الموجز بواسطة منظومة ذكاء اصطناعي اعتماداً على مصادر "
        "متاحة للعموم. تعكس الأحكام والأطر التحليلية الواردة فيه اجتهاد "
        "المنظومة، لا آراء أي مؤسسة منتجة أو العاملين فيها. ويُستحسن أن "
        "يتحقق القارئ من الادعاءات المحددة بمراجعة المصادر المذكورة "
        "قبل الاعتماد عليها في اتخاذ القرارات."
    )
    if args.no_disclaimer:
        disclaimer_block = ""
    else:
        if args.disclaimer_text.strip():
            text = args.disclaimer_text.strip()
        elif args.language == "ar":
            text = DEFAULT_DISCLAIMER_AR
        else:
            text = DEFAULT_DISCLAIMER_EN
        disclaimer_block = f'<div class="cover-disclaimer">{text}</div>'

    # Country flag block. By default, the renderer looks up the country's
    # ISO 3166-1 alpha-2 code from Natural Earth admin0 data, then loads
    # the matching flag PNG from assets/flags/. The --no-flag flag
    # suppresses; --flag-path provides a custom image (file path).
    flag_block = ""
    if not args.no_flag:
        if args.flag_path.strip():
            # User-provided override path (Path is already imported at module level)
            custom_path = Path(args.flag_path).expanduser().resolve()
            if custom_path.exists():
                flag_uri = custom_path.as_uri()
                flag_block = f'<img class="cover-flag" src="{flag_uri}" alt="{args.country} flag" />'
        else:
            # Auto-resolve from country name
            flag_uri = _country_flag_path(args.country)
            if flag_uri:
                flag_block = f'<img class="cover-flag" src="{flag_uri}" alt="{args.country} flag" />'

    # Language-aware substitutions. For Arabic, the template uses dir="rtl",
    # Arabic fonts, and Arabic strings for fixed UI elements ("Country Brief"
    # heading, page numbering separator, etc.). The brief body itself comes
    # from the markdown file, which the analyst is responsible for writing
    # in the correct language per the references/arabic-*.md guidance.
    is_arabic = args.language == "ar"
    lang_attr = "ar" if is_arabic else "en"
    dir_attr = "rtl" if is_arabic else "ltr"
    body_font_stack = (
        "'Amiri', 'Noto Naskh Arabic', 'Scheherazade New', 'Traditional Arabic', serif"
        if is_arabic
        else "'Georgia', 'Times New Roman', serif"
    )
    heading_font_stack = (
        "'Amiri', 'Noto Naskh Arabic', 'Scheherazade New', serif"
        if is_arabic
        else "'Georgia', serif"
    )
    sans_font_stack = (
        "'Noto Sans Arabic', 'Cairo', 'Helvetica', 'Arial', sans-serif"
        if is_arabic
        else "'Helvetica', 'Arial', sans-serif"
    )
    # UI strings that the template renders directly
    cover_label = "موجز قُطري" if is_arabic else "COUNTRY BRIEF"
    date_label = "التاريخ" if is_arabic else "DATE"
    header_running_title = (
        f"{args.country} — موجز قُطري" if is_arabic else f"{args.country} — Country Brief"
    )
    page_of_separator = " من " if is_arabic else " / "

    final_html = (
        template
        .replace("{{TITLE}}", f"Country Brief: {args.country}")
        .replace("{{COUNTRY}}", args.country)
        .replace("{{FLAG_BLOCK}}", flag_block)
        .replace("{{SUBTITLE_BLOCK}}", subtitle_block)
        .replace("{{DATE}}", args.date)
        .replace("{{AUDIENCE_ROW}}", audience_row)
        .replace("{{ANGLE_ROW}}", angle_row)
        .replace("{{AUTHOR_ROW}}", author_row)
        .replace("{{DISCLAIMER_BLOCK}}", disclaimer_block)
        .replace("{{BODY}}", body_html)
        .replace("{{LANG}}", lang_attr)
        .replace("{{DIR}}", dir_attr)
        .replace("{{BODY_FONT}}", body_font_stack)
        .replace("{{HEADING_FONT}}", heading_font_stack)
        .replace("{{SANS_FONT}}", sans_font_stack)
        .replace("{{COVER_LABEL}}", cover_label)
        .replace("{{DATE_LABEL}}", date_label)
        .replace("{{HEADER_RUNNING_TITLE}}", header_running_title)
        .replace("{{PAGE_OF_SEP}}", page_of_separator)
    )

    # Write HTML
    html_path = args.output.replace(".pdf", ".html")
    Path(html_path).write_text(final_html, encoding="utf-8")

    # Render PDF
    engine = render_pdf(html_path, args.output)
    print(f"PDF rendered with {engine}: {args.output}")

    if not args.keep_html:
        try:
            os.remove(html_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()


