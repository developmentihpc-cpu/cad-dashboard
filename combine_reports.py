#!/usr/bin/env python3
"""combine_reports.py — assemble a multi-country combined report from per-country ODA
country-proposal decks: a summary/contents front page, then each country's NEEDS ASSESSMENT
(the diagnostic slides + GPS matrix), with the Proposed-Programmes section removed.

    python combine_reports.py --title "Global South Country Assessment Report" \
        --out "_report_build/Global_South.pptx" --countries India Paraguay ...

Each country deck is read from docs/reports/<slug>_Country_Proposal.pptx (the hosted,
pre-generated exact-format decks). Slides are merged with PowerPoint COM's InsertFromFile,
which preserves every deck's flag, choropleth maps and formatting natively.
"""
import argparse, os, re, sys, shutil, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPORTS = BASE / "docs" / "reports"
WORK = BASE / "_report_build" / "_combine"
os.environ.setdefault("PYTHONUTF8", "1")

# Slides that make up the Proposed-Programmes / projects back-half of the template — dropped so
# the combined report is a pure needs assessment. Keeps 1-15 (diagnosis) + 23 (GPS matrix).
DROP_SLIDES = [16, 17, 18, 19, 20, 21, 22]
SECTORS = ["Economy", "Health", "Education", "Food Security", "Agriculture",
           "Infrastructure", "WASH", "Energy"]

# ── ODA brand ──
INK = "1D252C"; GOLD = "AD833B"; GOLD_LT = "C7A877"; NAVY = "333F64"; SLATE = "2F586E"
CREAM = "F7F5EF"; SKY = "CBDCE6"; FG2 = "5B6A7E"; WHITE = "FFFFFF"


def slug_of(country):
    return re.sub(r"[^a-z0-9]+", "_", country.lower()).strip("_")


def deck_path(country):
    return REPORTS / ("%s_Country_Proposal.pptx" % country.replace(" ", "_"))


def drop_proposed(src, dst):
    """Copy a country deck and remove the Proposed-Programmes slides."""
    from pptx import Presentation
    prs = Presentation(str(src))
    xml_slides = prs.slides._sldIdLst
    slides = list(xml_slides)
    ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    for n in sorted(DROP_SLIDES, reverse=True):
        if n - 1 < len(slides):
            sid = slides[n - 1]
            rId = sid.get(ns)
            try:
                prs.part.drop_rel(rId)
            except Exception:
                pass
            xml_slides.remove(sid)
    prs.save(str(dst))
    return dst


def _tb(slide, x, y, w, h, runs, size, color, *, bold=False, italic=False, font="Montserrat",
        align=None, spacing=None, anchor="t", wrap=True):
    """Add a text box (runs = str or list of strings for multiple lines)."""
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    try:
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "m": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
    except Exception:
        pass
    lines = runs if isinstance(runs, list) else [runs]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align:
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
        r = p.add_run(); r.text = str(ln)
        f = r.font
        f.size = Pt(size); f.bold = bold; f.italic = italic; f.name = font
        f.color.rgb = RGBColor.from_string(color)
        if spacing is not None:
            from pptx.oxml.ns import qn
            rpr = r._r.get_or_add_rPr(); rpr.set("spc", str(int(spacing * 100)))
    return tb


def _rect(slide, x, y, w, h, color):
    from pptx.util import Inches
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.dml.color import RGBColor
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor.from_string(color)
    sh.line.fill.background(); sh.shadow.inherit = False
    return sh


def build_summary(title, countries, dst):
    """A one-slide ODA-branded summary/contents page (13.333 x 7.5)."""
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6] if len(prs.slide_layouts) > 6 else prs.slide_layouts[-1]
    s = prs.slides.add_slide(blank)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    _rect(s, 0, 0, 13.333, 7.5, CREAM)
    _rect(s, 0, 0, 13.333, 0.12, GOLD)
    date = datetime.date.today().strftime("%B %Y")
    _tb(s, 0.6, 0.55, 12, 0.3, "OFFICE OF DEVELOPMENT AFFAIRS · COUNTRY ANALYSIS · %s" % date.upper(),
        11, GOLD, bold=True, spacing=2.4)
    _tb(s, 0.57, 0.9, 12.2, 1.0, title, 34, INK, bold=True, font="Lora")
    _rect(s, 0.6, 1.95, 0.9, 0.035, GOLD)

    _tb(s, 0.6, 2.2, 12.1, 0.25, "IN THIS REPORT", 11, SLATE, bold=True, spacing=1.6)
    intro = ("This report compiles the ODA country needs assessment for %d countries of the Global South. "
             "Each country is diagnosed across eight sectors — %s — with a national snapshot, cross-sector "
             "overview, key actors, shock geography, national development strategy, and a GPS severity/triage "
             "matrix. Every figure is sourced. Proposed programmes are excluded — this is diagnosis only."
             % (len(countries), ", ".join(SECTORS)))
    _tb(s, 0.6, 2.46, 12.1, 0.95, intro, 12, INK)

    # countries in columns
    _tb(s, 0.6, 3.5, 12.1, 0.25, "COUNTRIES COVERED (%d)" % len(countries), 11, SLATE, bold=True, spacing=1.6)
    cols = 4 if len(countries) <= 40 else 5
    per = -(-len(countries) // cols)
    cw = 12.1 / cols
    ordered = sorted(countries)
    for ci in range(cols):
        chunk = ordered[ci * per:(ci + 1) * per]
        if not chunk:
            continue
        lines = ["•  " + c for c in chunk]
        _tb(s, 0.6 + ci * cw, 3.78, cw - 0.15, 2.5, lines, 10.5 if len(countries) <= 44 else 9, INK)

    # assessments per country
    ay = 6.35
    _tb(s, 0.6, ay, 12.1, 0.25, "EACH COUNTRY SECTION CONTAINS", 11, SLATE, bold=True, spacing=1.6)
    contents = ("Cover & national snapshot  ·  Cross-sector snapshot  ·  Key actors & engagement  ·  "
                "Shock & recovery geography  ·  National development strategy  ·  8 sector deep-dives with "
                "state/province choropleths  ·  GPS severity matrix")
    _tb(s, 0.6, ay + 0.26, 12.1, 0.5, contents, 10.5, INK)

    _tb(s, 0.6, 7.16, 12.1, 0.25,
        "Sources per slide: World Bank · IMF · WHO · UNICEF/UN IGME · UNESCO UIS · FAO · WHO/UNICEF JMP · ITU · IEA · OCHA · national statistics.",
        8, FG2)
    prs.save(str(dst))
    return dst


def renumber_footers(path):
    """Rewrite each slide's 'NN / NN' footer run to its position in the combined deck."""
    from pptx import Presentation
    prs = Presentation(path)
    total = len(prs.slides)
    pat = re.compile(r"^\s*\d+\s*/\s*\d+\s*$")
    for i, s in enumerate(prs.slides, start=1):
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if pat.match(r.text or ""):
                        r.text = "   %d / %d" % (i, total)
    prs.save(path)


def combine(title, countries, out):
    import win32com.client
    WORK.mkdir(parents=True, exist_ok=True)
    # 1) needs-only copies (proposed programmes dropped)
    have, missing = [], []
    for c in countries:
        src = deck_path(c)
        if not src.exists():
            missing.append(c); continue
        dst = WORK / ("needs_%s.pptx" % slug_of(c))
        drop_proposed(src, dst); have.append((c, dst))
    if not have:
        sys.exit("No source decks found for: %s (looked in %s)" % (", ".join(countries), REPORTS))
    # 2) summary page (only for the countries we actually have)
    summary = WORK / "_summary.pptx"
    build_summary(title, [c for c, _ in have], summary)
    # 3) merge with PowerPoint COM (preserves flags/maps/formatting)
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(summary.resolve()), WithWindow=False)
    idx = pres.Slides.Count  # after the summary slide
    for c, dpath in have:
        pres.Slides.InsertFromFile(str(dpath.resolve()), idx)
        idx = pres.Slides.Count
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    pres.SaveAs(str(Path(out).resolve()))
    total = pres.Slides.Count
    pres.Close(); app.Quit()
    renumber_footers(str(Path(out).resolve()))
    return {"out": out, "slides": total, "countries": [c for c, _ in have], "missing": missing}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="Global South Country Assessment Report")
    ap.add_argument("--out", default=str(BASE / "_report_build" / "Combined_Report.pptx"))
    ap.add_argument("--countries", nargs="+", required=True)
    args = ap.parse_args()
    res = combine(args.title, args.countries, args.out)
    print("WROTE %s | %d slides | countries: %s%s" %
          (res["out"], res["slides"], ", ".join(res["countries"]),
           (" | MISSING (no deck yet): " + ", ".join(res["missing"])) if res["missing"] else ""))


if __name__ == "__main__":
    main()
