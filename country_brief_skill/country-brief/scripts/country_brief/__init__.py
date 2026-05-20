"""
country_brief — Render country briefs from markdown to styled PDF.

Public API:
    main()                                   # CLI entry point (argparse + orchestration)
    render_basic_markdown(md)                # core markdown -> HTML pipeline
    render_pdf(html_path, pdf_path)          # HTML -> PDF (WeasyPrint, with wkhtmltopdf fallback)
    validate_brief(md_text, strict=False)    # pre-render structural validation
    validate_manifest_against_markdown(...)  # manifest cross-check (when --manifest is set)

Most callers want main(). The lower-level functions are exposed for
programmatic embedding (notebooks, custom render pipelines).
"""
from .cli import main
from .pipeline import render_basic_markdown, render_pdf
from .validation import validate_brief, validate_manifest_against_markdown

__all__ = [
    "main",
    "render_basic_markdown",
    "render_pdf",
    "validate_brief",
    "validate_manifest_against_markdown",
]
