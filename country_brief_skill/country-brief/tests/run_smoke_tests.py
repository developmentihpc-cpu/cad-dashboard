#!/usr/bin/env python3
"""
Smoke-test suite for the country-brief renderer.

Run with: python tests/run_smoke_tests.py

Tests render the three fixtures (minimal.md, full-stress.md, broken.md)
and check that the rendered output meets expectations specific to each
fixture. The goal is to catch regressions on the categories of bug we've
actually seen during this skill's development:

- Snapshot parser silent failures on separator mismatch
- Risk matrix vocabulary rejection
- Map region name silent mismatches
- Capital city ambiguity (Morocco bug)
- Label drop on collision (the over-correction)
- def render_toc clipped during str_replace (NameError)

Exits 0 if all tests pass, 1 if any fail.
"""
import subprocess
import sys
import time
from pathlib import Path

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
RENDER_SCRIPT = TESTS_DIR.parent / "scripts" / "render_brief.py"
OUTPUT_DIR = TESTS_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ANSI color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _pdf_page_count(pdf_path: Path) -> int:
    """Get the number of pages in a PDF.

    Tries pypdf first (pure-Python, no native deps) then falls back to
    pdf2image (needs poppler binaries — fine on Linux/Mac, painful on
    Windows). pypdf is preferred because it's lighter and portable.
    """
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        from pdf2image import convert_from_path
        return len(convert_from_path(str(pdf_path), dpi=50))


def _run_render(fixture: Path, country: str, output_pdf: Path,
                home_country: str = "UAE") -> tuple:
    """Run the renderer on a fixture. Returns (exit_code, stderr_text).
    home_country defaults to UAE to match production behavior; pass "none"
    for fixtures that deliberately omit Section 1.5."""
    result = subprocess.run(
        [
            sys.executable, str(RENDER_SCRIPT),
            "--input", str(fixture),
            "--output", str(output_pdf),
            "--country", country,
            "--date", "January 2026",
            "--home-country", home_country,
            "--toc",
        ],
        capture_output=True, text=True, timeout=60,
    )
    return result.returncode, result.stderr + result.stdout


def _assert(condition: bool, message: str, failures: list) -> bool:
    """Record a failure if the condition is false. Returns the condition
    so callers can short-circuit further checks that depend on it."""
    if not condition:
        failures.append(message)
    return condition


# -----------------------------------------------------------------------------
# Test cases
# -----------------------------------------------------------------------------

def test_structural_validation_checks():
    """The new structural-discipline validation checks (added after the
    Iran brief audit in May 2026) should fire on a brief that has
    substantive prose but is missing key structural components (map,
    chart, risk matrix, recommendations, footnotes, decision-implications
    per spine section, over-long bottom line). And they should NOT fire
    on a minimal-size brief that falls under the size gate, since those
    are test fixtures rather than real briefs.
    """
    import tempfile
    import sys
    failures = []

    # Build a substantive but structurally-broken brief: enough body
    # lines to clear the size gate, but missing the structural elements.
    # We need >120 body lines outside fenced blocks. Each "para line" is
    # one paragraph (one body line). 8 sections × 20 paragraphs = 160 lines.
    def _section(title, n_paras=20):
        lines = [f"## {title}", ""]
        for i in range(n_paras):
            lines.append(f"Paragraph {i} of {title}: this is an analytical sentence about a country topic.")
            lines.append("")
        return "\n".join(lines)

    long_bottom_line = " ".join([f"Sentence {i} that pads the bottom line beyond spec." for i in range(20)])
    bad_brief = f"""## Bottom line

{long_bottom_line}

{_section("1. Country Snapshot")}

{_section("2. Political Context")}

{_section("3. Economic Conditions")}

{_section("4. Security & Stability")}

{_section("5. Governance & Institutions")}

{_section("6. Social Dynamics")}

{_section("19. Outlook")}
"""

    # Import the validator directly
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import validate_brief
    finally:
        sys.path.pop(0)

    warnings, errors = validate_brief(bad_brief)

    # Should produce the structural warnings
    expected_patterns = [
        ("zero footnote references", "missing footnotes check not firing"),
        ("Bottom Line is", "long bottom line check not firing"),
        ("no ::: map block", "missing map check not firing"),
        ("no ::: chart blocks", "missing chart check not firing"),
        ("no ::: risk-matrix block", "missing risk matrix check not firing"),
        ("no Recommendations section", "missing recommendations check not firing"),
        ("decision-implication callouts", "missing decision-implications check not firing"),
    ]

    combined = "\n".join(warnings)
    for pattern, msg in expected_patterns:
        _assert(pattern in combined, f"{msg}: '{pattern}'", failures)

    # And confirm size gate works: an empty/tiny brief should NOT trigger
    # structural warnings (they're for substantive briefs, not test stubs)
    tiny_brief = "## Bottom line\n\nShort.\n"
    warnings_tiny, _ = validate_brief(tiny_brief)
    structural_warnings_tiny = [w for w in warnings_tiny if w.startswith("Structural:")]
    _assert(
        len(structural_warnings_tiny) == 0,
        f"size gate failed: tiny brief triggered structural warnings: {structural_warnings_tiny}",
        failures,
    )

    # Series-leakage check: comparative phrases like "in this brief series"
    # or "covered in earlier briefs" should fire a warning. The reader has
    # one brief in front of them and shouldn't see production-context references.
    leakage_body = "\n".join([f"Paragraph {i} of substantive prose about a country." for i in range(150)])
    leakage_brief = f"""## Bottom line

{leakage_body}

The bilateral relationship is thinner than the relationships covered in earlier briefs in this series.
Confidence is lower than for any other country in the brief series.
"""
    warnings_leakage, _ = validate_brief(leakage_brief)
    leakage_warnings = [w for w in warnings_leakage if "series-leakage" in w]
    _assert(
        len(leakage_warnings) >= 1,
        "series-leakage check did not fire on text containing 'in this series' and 'earlier briefs'",
        failures,
    )

    return failures


def test_minimal_renders():
    """The minimal fixture should render without errors and produce a
    reasonably-sized PDF. This catches the 'def render_toc clipped'
    class of bug — if any core function is broken, the simplest brief
    fails first."""
    failures = []
    output = OUTPUT_DIR / "minimal.pdf"
    # Minimal fixture deliberately omits Section 1.5 — pass --home-country none
    # to keep the test consistent.
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "minimal.md", "Ethiopia", output,
        home_country="none",
    )

    if _assert(exit_code == 0, f"render exited with code {exit_code}", failures):
        _assert(output.exists(), "output PDF was not created", failures)
        _assert(output.stat().st_size > 10_000, f"output PDF is suspiciously small ({output.stat().st_size} bytes)", failures)
        if output.exists():
            pages = _pdf_page_count(output)
            # Minimal brief: cover + TOC + ~10 pages of content
            _assert(5 <= pages <= 25, f"minimal brief page count out of range: {pages}", failures)

    # Should produce no validator warnings — minimal brief is well-formed
    _assert("Pre-render warnings" not in stderr, "minimal brief produced unexpected validator warnings", failures)
    # Should NOT produce a 'render_toc not defined' error
    _assert("render_toc" not in stderr or "NameError" not in stderr,
            "render_toc NameError detected — core function broken", failures)

    return failures


def test_full_stress_renders():
    """The full-stress fixture exercises every fenced-div component. If
    any component class produces empty HTML, broken HTML, or raises an
    exception, this test catches it."""
    failures = []
    output = OUTPUT_DIR / "full-stress.pdf"
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "full-stress.md", "Ethiopia", output,
    )

    if _assert(exit_code == 0, f"full-stress render exited with code {exit_code}", failures):
        _assert(output.exists(), "full-stress PDF was not created", failures)
        if output.exists():
            pages = _pdf_page_count(output)
            _assert(8 <= pages <= 35, f"full-stress page count out of range: {pages}", failures)

    # No validator warnings expected on a well-formed full-stress brief
    _assert("Pre-render warnings" not in stderr,
            f"full-stress produced unexpected validator warnings: {stderr[:200]}",
            failures)

    # Check stderr for matplotlib/weasyprint failures that would indicate
    # broken chart or map rendering
    fatal_patterns = [
        "Traceback", "Exception", "Error rendering",
        "could not be rendered", "matplotlib.error",
    ]
    for pattern in fatal_patterns:
        _assert(pattern not in stderr,
                f"detected '{pattern}' in stderr — rendering failure",
                failures)

    return failures


def test_broken_fixture_emits_warnings():
    """The broken fixture should still render (best-effort) but should
    produce specific validator warnings. This tests the validator's
    ability to catch the categories of error we care about."""
    failures = []
    output = OUTPUT_DIR / "broken.pdf"
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "broken.md", "Ethiopia", output,
    )

    # Broken brief should still complete rendering
    _assert(exit_code == 0, f"broken brief failed to render (exit {exit_code})", failures)

    # Specific warnings we expect the validator to emit
    expected_warnings = [
        # Undefined footnote refs
        ("[^missing-fn]", "undefined footnote not detected"),
        ("[^also-missing]", "second undefined footnote not detected"),
        # Unused definition
        ("used-but-defined", "unused footnote definition not detected"),
        # Typo'd class name with suggestion
        ("verditc-strip", "typo'd class name not detected"),
        ("verdict-strip", "no suggestion given for typo"),
        # Empty fenced div
        ("empty", "empty fenced-div not detected"),
        # Missing country parameter on map
        ("country:", "map missing country: parameter not detected"),
        # Spine sections missing
        ("Spine sections missing", "missing spine sections not detected"),
        # Malformed component lines
        ("missing '|' separator", "malformed stats-strip not detected"),
    ]

    for pattern, error_msg in expected_warnings:
        _assert(pattern in stderr, error_msg, failures)

    return failures


def test_map_labels_all_present():
    """Render the full-stress fixture and verify the choropleth map
    rendered successfully without falling back to an error placeholder.

    This catches the class of bug where the map renderer can't find its
    geo data (e.g., path resolution broken by a refactor) and silently
    writes a placeholder error to the HTML instead. The placeholder is
    NOT logged to stderr — it's embedded in the rendered PDF — so the
    only reliable way to detect it is by reading the rendered output.

    We use pdftotext to extract text from the PDF and assert that none
    of the placeholder error patterns appear anywhere.
    """
    failures = []
    output = OUTPUT_DIR / "full-stress.pdf"
    if not output.exists():
        failures.append("full-stress.pdf not present; run test_full_stress first")
        return failures

    # Re-render to a fresh PDF, then read its text.
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "full-stress.md", "Ethiopia",
        OUTPUT_DIR / "full-stress-map.pdf",
    )
    _assert(exit_code == 0, f"map test render failed (exit {exit_code})", failures)

    # Extract text from the rendered PDF
    pdf_path = OUTPUT_DIR / "full-stress-map.pdf"
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        failures.append(f"pdftotext failed: {result.stderr[:200]}")
        return failures
    pdf_text = result.stdout

    # The placeholder errors from maps.py — if any of these appear in
    # the rendered PDF, the map fell back to an error placeholder.
    placeholder_patterns = [
        ("Map rendering requires matplotlib",
         "matplotlib import failed during rendering"),
        ("Map rendering requires geopandas",
         "geopandas import failed during rendering"),
        ("Map rendering requires the Natural Earth boundary files",
         "admin boundary parquet files not found at expected path "
         "(check path resolution in maps.py — likely a refactor regression)"),
    ]
    for pattern, error_msg in placeholder_patterns:
        _assert(pattern not in pdf_text,
                f"map error placeholder in PDF: {error_msg}",
                failures)

    # Also check stderr for things that would indicate other map issues
    _assert("No admin-1 regions found" not in stderr,
            "map error: country name did not match Natural Earth admin column",
            failures)
    # The fuzzy matcher will emit notes if region names didn't exact-match,
    # which is fine — Ethiopia's regions in the fixture are already correctly
    # aliased so this should be silent.
    _assert("Map WARNING" not in stderr,
            f"map emitted region-not-found warning: {stderr[:300]}",
            failures)

    return failures


def test_capital_city_correct():
    """Render a brief for Morocco and verify the renderer chose Rabat
    (not Laayoune). This is a regression test for the capital-city
    ambiguity bug. We check by parsing stderr for the warning the renderer
    emits when there's ambiguity AND no override — if the override is
    working, no warning should be emitted.
    """
    failures = []

    # Use the minimal fixture but render with country=Morocco
    output = OUTPUT_DIR / "morocco-capital.pdf"
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "minimal.md", "Morocco", output,
    )

    # The renderer should silently pick Rabat via the override.
    # If the override is missing or broken, we'd see the ambiguity warning.
    _assert("multiple capital entries found" not in stderr,
            "capital city ambiguity warning emitted — _CAPITAL_OVERRIDES regression",
            failures)
    _assert(exit_code == 0, f"morocco render exited with code {exit_code}", failures)
    _assert(output.exists(), "morocco PDF was not created", failures)

    return failures


def test_snapshot_content_rendered():
    """The minimal fixture has a snapshot block with specific values
    (population, GDP, etc.). Verify those values appear in the rendered
    PDF text. This catches silent rendering failures where the snapshot
    parser falls through and produces empty output — the exact category
    of bug that hit during the Sudan brief (pipe separator not accepted)."""
    failures = []
    output = OUTPUT_DIR / "minimal.pdf"
    if not output.exists():
        failures.append("minimal.pdf not present; run test_minimal first")
        return failures

    # Extract text from the PDF
    result = subprocess.run(
        ["pdftotext", str(output), "-"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        failures.append(f"pdftotext failed: {result.stderr[:200]}")
        return failures

    text = result.stdout

    # The minimal fixture's snapshot has these specific values; if the
    # snapshot block silently fails to parse, these will be missing from
    # the rendered output.
    expected_snapshot_values = [
        "~10 million",      # Population value
        "Parliamentary republic",  # Government value
        "~$50B",            # GDP value
        "Generally stable", # Security value
    ]

    for value in expected_snapshot_values:
        _assert(value in text,
                f"snapshot value '{value}' not found in rendered PDF — snapshot parser regression",
                failures)

    # Also verify the snapshot section headers actually rendered.
    # CSS letter-spacing on the headers means "STABILITY" appears in
    # the PDF text as "S TA B I L I T Y" — so we check by stripping
    # whitespace and looking for the header substring.
    text_compact = "".join(text.split())
    for header in ["PEOPLE", "POLITICS", "ECONOMY", "STABILITY"]:
        _assert(header in text_compact,
                f"snapshot section header '{header}' not in rendered PDF",
                failures)

    return failures


def test_risk_matrix_content_rendered():
    """The full-stress fixture has 4 risks in its matrix, including ones
    with extended vocabulary ('very high', 'critical'). Verify the
    annotations actually appear in the rendered PDF. This catches the
    regression where extended vocabulary is silently rejected."""
    failures = []
    output = OUTPUT_DIR / "full-stress.pdf"
    if not output.exists():
        failures.append("full-stress.pdf not present; run test_full_stress first")
        return failures

    result = subprocess.run(
        ["pdftotext", str(output), "-"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        failures.append(f"pdftotext failed: {result.stderr[:200]}")
        return failures
    text = result.stdout

    # Each risk label should appear in the key list (canonical OR extended)
    expected_risk_labels = [
        "Risk A", "Risk B", "Risk C", "Risk D",
    ]
    for label in expected_risk_labels:
        _assert(label in text,
                f"risk label '{label}' missing from rendered PDF — risk matrix regression",
                failures)

    # The extended-vocabulary annotation should appear in the key list
    _assert("very high" in text.lower() or "critical" in text.lower(),
            "extended vocabulary annotations not in rendered PDF",
            failures)

    return failures



def test_manifest_validation():
    """Verify the --manifest flag validates correctly:
    - A correct manifest produces no manifest warnings
    - A wrong manifest produces specific warnings for each category of
      mismatch (typo, declared-but-missing, declared-false-but-present,
      invalid state, undeclared-but-present)
    - The three production-brief manifests (Sudan, Syria, Morocco) all
      validate cleanly against their corresponding production briefs.
      This catches drift if either the manifest or brief is later edited.

    This is a regression test for the manifest workflow: if the validator
    or module map is broken, this test catches it before users do.
    """
    failures = []

    # Use the minimal fixture, which has Section 1 + spine + Section 19.
    # Build a manifest matching it exactly — no warnings expected.
    minimal_manifest = OUTPUT_DIR / "manifest-minimal.yml"
    minimal_manifest.write_text("""country: Ethiopia
modules:
  country_snapshot: true
  political_context: true
  economic_conditions: true
  security_stability: true
  governance_rule_of_law: true
  social_human_development: true
  outlook: true
""")

    # Run with the manifest and check stderr for absence of manifest warnings
    result = subprocess.run(
        [
            sys.executable, str(RENDER_SCRIPT),
            "--input", str(FIXTURES_DIR / "minimal.md"),
            "--output", str(OUTPUT_DIR / "manifest-clean.pdf"),
            "--country", "Ethiopia",
            "--date", "May 2026",
            "--manifest", str(minimal_manifest),
        ],
        capture_output=True, text=True, timeout=60,
    )
    _assert(result.returncode == 0,
            f"manifest-clean render failed (exit {result.returncode})",
            failures)
    _assert("Manifest:" not in result.stderr,
            f"clean manifest produced unexpected warnings: {result.stderr[:300]}",
            failures)

    # Now test the broken manifest — should produce specific warnings
    broken_manifest = FIXTURES_DIR / "manifest-broken.yml"
    if not broken_manifest.exists():
        failures.append("manifest-broken.yml fixture not present")
        return failures

    # Use a brief with multiple sections so the broken-manifest warnings fire
    sudan_brief = TESTS_DIR.parent.parent / "sudan-brief.md"
    target_brief = str(sudan_brief) if sudan_brief.exists() else str(FIXTURES_DIR / "full-stress.md")

    result = subprocess.run(
        [
            sys.executable, str(RENDER_SCRIPT),
            "--input", target_brief,
            "--output", str(OUTPUT_DIR / "manifest-broken.pdf"),
            "--country", "Sudan",
            "--date", "May 2026",
            "--home-country", "UAE",
            "--manifest", str(broken_manifest),
        ],
        capture_output=True, text=True, timeout=60,
    )
    # Each category of manifest mismatch should produce a specific warning
    expected_patterns = [
        ("unknown module key 'macro_stres'", "typo detection regression"),
        ("did you mean 'macro_stress'", "typo suggestion regression"),
        ("unrecognized state 'maybe'", "invalid state detection regression"),
    ]
    for pattern, error_msg in expected_patterns:
        _assert(pattern in result.stderr,
                f"manifest validation: {error_msg}",
                failures)

    # Verify the three production-brief manifests validate cleanly.
    # This catches drift between manifest and brief if either is edited.
    for country, brief_name, manifest_name in [
        ("Sudan",   "sudan-brief.md",   "manifest-sudan.yml"),
        ("Syria",   "syria-brief.md",   "manifest-syria.yml"),
        ("Morocco", "morocco-brief.md", "manifest-morocco.yml"),
    ]:
        brief_path = TESTS_DIR.parent.parent / brief_name
        manifest_path = FIXTURES_DIR / manifest_name
        if not brief_path.exists() or not manifest_path.exists():
            # Production briefs may not be in this filesystem; skip gracefully
            continue
        result = subprocess.run(
            [
                sys.executable, str(RENDER_SCRIPT),
                "--input", str(brief_path),
                "--output", str(OUTPUT_DIR / f"manifest-{country.lower()}-prod.pdf"),
                "--country", country,
                "--date", "May 2026",
                "--home-country", "UAE",
                "--manifest", str(manifest_path),
            ],
            capture_output=True, text=True, timeout=60,
        )
        _assert(result.returncode == 0,
                f"{country} manifest-validated render failed",
                failures)
        _assert("Manifest:" not in result.stderr,
                f"{country} production manifest drifted from brief: {result.stderr[:300]}",
                failures)

    return failures



def test_extended_risk_vocabulary():
    """The full-stress fixture uses 'very high' and 'critical' in its
    risk matrix. The renderer should accept these without warnings and
    render the matrix with annotations. If the vocabulary check is
    regressed, the matrix will silently render as empty (risks dropped)
    or warnings will appear."""
    failures = []
    output = OUTPUT_DIR / "full-stress.pdf"
    if not output.exists():
        failures.append("full-stress.pdf not present; run test_full_stress first")
        return failures

    # The full-stress fixture has 'very high' and 'critical' — if these
    # are rejected, the risk matrix would have only 3 markers instead of 4.
    # We can't read inside the PDF easily, so we re-run with stderr capture
    # and check for any vocabulary-related warnings.
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "full-stress.md", "Ethiopia",
        OUTPUT_DIR / "vocab-test.pdf",
    )
    # If validator regression caused 'very high' to look malformed, we'd
    # see a warning about the risk-matrix line.
    _assert("In :::risk-matrix block" not in stderr,
            "risk-matrix validator regression — extended vocabulary not accepted",
            failures)

    return failures


def test_home_country_consistency_validation():
    """Verify the --home-country flag validates against markdown content:
    - A brief WITH a Section 1.5 heading but --home-country none → warning
    - A brief WITHOUT a Section 1.5 heading but --home-country UAE → warning
    - A brief WITH Section 1.5 + --home-country UAE → no warning
    - A brief WITHOUT Section 1.5 + --home-country none → no warning

    This is a regression test for the home-country consistency check
    introduced after the Sri Lanka country test surfaced that the
    --home-country parameter was parsed but never validated.
    """
    failures = []

    # Case 1: minimal fixture has no Section 1.5; default --home-country UAE
    # should fire a warning.
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "minimal.md", "Ethiopia",
        OUTPUT_DIR / "home-country-test-1.pdf",
        home_country="UAE",
    )
    _assert("--home-country is set to 'UAE'" in stderr,
            "home-country mismatch with UAE → missing Section 1.5 not caught",
            failures)

    # Case 2: full-stress fixture has Section 1.5; --home-country none should
    # fire a warning.
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "full-stress.md", "Ethiopia",
        OUTPUT_DIR / "home-country-test-2.pdf",
        home_country="none",
    )
    _assert("--home-country is 'none'" in stderr,
            "home-country mismatch with none → unexpected Section 1.5 not caught",
            failures)

    # Case 3: minimal fixture + --home-country none → no home-country warning
    exit_code, stderr = _run_render(
        FIXTURES_DIR / "minimal.md", "Ethiopia",
        OUTPUT_DIR / "hc-test-3.pdf",
        home_country="none",
    )
    # Check for the actual warning text, not the substring "home-country"
    # (which appears in the output filename itself)
    _assert("--home-country is" not in stderr,
            f"home-country consistency case produced unexpected warning: {stderr[:200]}",
            failures)

    return failures


def test_faction_box_extended_categories():
    """Verify the faction-box accepts the extended position categories
    for de facto power-holders: 'military', 'armed forces', 'praetorian',
    'religious-authority', 'religious authority', 'clerical'.

    Regression test for the May 2026 addition. Previously these positions
    would map to 'other' (gray badge), which loses the analytical signal
    that the military or religious authority is a distinct kind of actor
    from a civilian political party.

    Tests:
    1. All six new aliases render without falling into the 'other' bucket.
    2. The class names appear in the HTML produced by the renderer.
    """
    failures = []

    fixture_path = OUTPUT_DIR / "faction-extended-fixture.md"
    fixture_path.write_text("""# Test Brief

## 1. Country Snapshot

## 2. Political Context

::: faction-box
title: Extended categories test

- Army A | Military | Stance one
- Army B | Armed forces | Stance two
- Army C | Praetorian | Stance three
- Clerical body A | Religious-authority | Stance four
- Clerical body B | Religious authority | Stance five
- Clerical body C | Clerical | Stance six
- Ruling party | Ruling | Stance seven
:::

## 19. Outlook (12-24 months)

::: scenario
<span class="scenario-label">Base case</span> Some text.
:::
""")

    exit_code, stderr = _run_render(
        fixture_path, "Testland",
        OUTPUT_DIR / "faction-extended-test.pdf",
        home_country="none",
    )
    _assert(exit_code == 0,
            f"faction-box extended categories render failed (exit {exit_code})",
            failures)

    # Inspect the HTML produced by the renderer directly — most reliable
    # way to verify the position-class mapping is working (vs trying to
    # read pixel colors from a rendered PDF).
    import sys as _sys
    scripts_dir = TESTS_DIR.parent / "scripts"
    _sys.path.insert(0, str(scripts_dir))
    try:
        from country_brief.fenced_divs import render_faction_box
    finally:
        if str(scripts_dir) in _sys.path:
            _sys.path.remove(str(scripts_dir))

    test_input = """- Army A | Military | Stance one
- Clerical A | Religious-authority | Stance two
- Clerical B | Clerical | Stance three
- Army B | Armed forces | Stance four
- Army C | Praetorian | Stance five"""

    html = render_faction_box(test_input)

    # Every category must map to its canonical CSS class, not 'other'
    _assert('faction-position military' in html,
            "faction-box: 'Military' position did not map to .military CSS class",
            failures)
    _assert('faction-position religious-authority' in html,
            "faction-box: 'Religious-authority' position did not map to .religious-authority CSS class",
            failures)
    _assert(html.count('faction-position other') == 0,
            "faction-box: extended categories incorrectly fell back to .other class",
            failures)
    # Aliases must all map correctly
    army_classes = html.count('faction-position military')
    _assert(army_classes == 3,
            f"faction-box: expected 3 .military rows (Military/Armed forces/Praetorian), got {army_classes}",
            failures)
    clerical_classes = html.count('faction-position religious-authority')
    _assert(clerical_classes == 2,
            f"faction-box: expected 2 .religious-authority rows (Religious-authority/Clerical), got {clerical_classes}",
            failures)

    return failures


def test_leader_cards_renders():
    """Verify the leader-cards component renders correctly in three modes:
    1. Photo source absent → monogram placeholder
    2. Photo source is a local file path → photo embedded
    3. Photo source is invalid (file not found) → graceful fallback to monogram

    Tests also check:
    - Validator accepts leader-cards class name (would fail if not in
      known_classes)
    - Leader names extract correctly from rendered PDF
    """
    failures = []

    # Create a tiny test image file
    test_photo = OUTPUT_DIR / "test-leader.jpg"
    # Minimal valid JPEG (1x1 red pixel)
    test_photo.write_bytes(bytes.fromhex(
        'FFD8FFE000104A46494600010100000100010000FFDB004300080606070605'
        '08070708090908'
        '0A0C140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C20242E2720222C231C1C2837'
        '292C30313434341F27393D38323C2E333432FFC0000B080001000101011100FFC4'
        '001F0000010501010101010100000000000000000102030405060708090A0BFFC4'
        '003510000201030302040305050404000001020300041105213114061241510761'
        '711332813291A1F0233442B1C115526272F23373E29142E1F0FFC4001401010000'
        '00000000000000000000000000000000FFC400140101000000000000000000000'
        '0000000000000FFDA000C03010002110311003F00FBC8F1C7FFD9'
    ))

    # Build a fixture exercising all three modes
    fixture_path = OUTPUT_DIR / "leader-cards-fixture.md"
    fixture_path.write_text(f"""# Test Brief

## 1. Country Snapshot

::: leader-cards
title: Test Leadership

- Monogram Person | President since 2024 | Test Party |
- Photo Person | Prime Minister | Other Party | {test_photo}
- Missing Photo Person | Opposition Leader | Third Party | /nonexistent/path/photo.jpg
:::

Some body text.

## 19. Outlook (12-24 months)

::: scenario
<span class="scenario-label">Base case (probability ~60%)</span> Some scenario text.
:::
""")

    exit_code, stderr = _run_render(
        fixture_path, "Testland",
        OUTPUT_DIR / "leader-cards-test.pdf",
        home_country="none",
    )
    _assert(exit_code == 0,
            f"leader-cards test render failed (exit {exit_code})",
            failures)
    _assert(":::leader-cards' is not a recognized component" not in stderr,
            "leader-cards class is not in validator's known_classes set",
            failures)
    # The missing-photo case should trigger a "local photo not found" note
    _assert("local photo not found" in stderr,
            "leader-cards: missing local photo did not emit error note "
            "(graceful fallback may have masked the diagnostic)",
            failures)
    # The valid local photo should NOT trigger an error
    # (We check that there is only ONE 'local photo not found' message, not two)
    not_found_count = stderr.count("local photo not found")
    _assert(not_found_count == 1,
            f"leader-cards: expected 1 'local photo not found' message, "
            f"got {not_found_count} — valid local photo may be failing",
            failures)

    # Extract text from rendered PDF and verify leader names appear
    result = subprocess.run(
        ["pdftotext", str(OUTPUT_DIR / "leader-cards-test.pdf"), "-"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        failures.append(f"pdftotext failed: {result.stderr[:200]}")
        return failures
    pdf_text = result.stdout

    for expected_name in ["Monogram Person", "Photo Person", "Missing Photo Person"]:
        _assert(expected_name in pdf_text,
                f"leader-cards: expected name '{expected_name}' not found in rendered PDF",
                failures)
    # Title uses CSS text-transform: uppercase, so pdftotext extracts uppercase
    _assert("Test Leadership" in pdf_text or "TEST LEADERSHIP" in pdf_text,
            "leader-cards: title not rendered to PDF",
            failures)

    return failures


def test_strict_mode_promotes_binding_checks():
    """--strict promotes three structural warnings to render-blocking errors:
    zero footnote references, no risk-matrix, no Recommendations. Without
    --strict, the same brief produces only warnings and renders. The other
    structural warnings (footnote density, bottom-line length, series-leakage,
    decision-implication coverage) must stay as warnings even under --strict.
    """
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import validate_brief
    finally:
        sys.path.pop(0)

    # Build a substantive brief (>120 body lines) that misses all three
    # strict-promotable elements: no footnotes, no risk-matrix, no recs.
    paras = "\n\n".join(
        f"Paragraph {i}: an analytical claim about the country's political economy."
        for i in range(150)
    )
    bad_brief = f"## Bottom line\n\nShort enough.\n\n## 1. Country Snapshot\n\n{paras}\n"

    # Default mode: warnings, no errors.
    w_default, e_default = validate_brief(bad_brief, strict=False)
    _assert(len(e_default) == 0,
            f"default mode should not produce errors, got {len(e_default)}",
            failures)
    structural_warnings_default = [w for w in w_default if w.startswith("Structural:")]
    _assert(len(structural_warnings_default) >= 3,
            f"default mode missing structural warnings, got {len(structural_warnings_default)}: {structural_warnings_default}",
            failures)

    # Strict mode: same brief, but the three binding checks become errors.
    w_strict, e_strict = validate_brief(bad_brief, strict=True)
    error_text = "\n".join(e_strict)
    for expected_phrase in ("zero footnote references", "no ::: risk-matrix block", "no Recommendations section"):
        _assert(expected_phrase in error_text,
                f"strict mode missing promoted error containing '{expected_phrase}'",
                failures)
    # And confirm those warnings were removed from the warnings list, not duplicated.
    warning_text = "\n".join(w_strict)
    for expected_phrase in ("zero footnote references", "no ::: risk-matrix block", "no Recommendations section"):
        _assert(expected_phrase not in warning_text,
                f"strict mode left promoted warning duplicated in warnings: '{expected_phrase}'",
                failures)

    # A complete brief should produce no errors under --strict.
    good_brief = bad_brief + "\n## Recommendations\n\nDefer.[^1]\n\n::: risk-matrix\n- A risk | likelihood: low | impact: low\n:::\n\n[^1]: Test source.\n"
    w_good, e_good = validate_brief(good_brief, strict=True)
    _assert(len(e_good) == 0,
            f"strict mode produced errors on a complete brief: {e_good}",
            failures)

    return failures


def test_chart_recipe_registry():
    """The chart recipe registry detects which decision-relevant charts
    should be present based on the brief's content (keywords + section
    presence), and warns when a recipe's trigger fires but no matching
    chart is in the brief. Analyst writes the chart data; the registry
    just nudges toward common high-leverage charts for the country
    profile."""
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import (
            validate_brief,
            _CHART_RECIPES,
            _detect_chart_titles,
            _recipe_fires,
            _recipe_chart_present,
            _missing_chart_recipes,
        )
    finally:
        sys.path.pop(0)

    # Registry sanity: every recipe has the expected fields
    for name, recipe in _CHART_RECIPES.items():
        for key in ("trigger", "section_hint", "title_keywords", "template"):
            _assert(key in recipe,
                    f"recipe {name!r} missing field {key!r}",
                    failures)
        _assert("::: chart" in recipe["template"],
                f"recipe {name!r} template doesn't contain a ::: chart block",
                failures)

    # Title detection
    sample_md = """## 3. Economic Conditions

::: chart
type: line
title: Real GDP growth and Inflation
x: 2024 | 2025
y: GDP | 1 | 2
:::

::: chart
type: bar
title: Remittance Inflows
x: A | B
y: R | 1 | 2
:::
"""
    titles = _detect_chart_titles(sample_md)
    _assert("real gdp growth and inflation" in titles,
            f"_detect_chart_titles missed first chart: {titles}",
            failures)
    _assert("remittance inflows" in titles,
            f"_detect_chart_titles missed second chart: {titles}",
            failures)

    # Trigger semantics
    remittances_recipe = _CHART_RECIPES["remittances-trajectory"]
    _assert(_recipe_fires(remittances_recipe, "Remittances are 20% of GDP."),
            "remittances trigger did not fire on 'Remittances are 20% of GDP'",
            failures)
    _assert(not _recipe_fires(remittances_recipe, "Tourism is the dominant sector."),
            "remittances trigger fired spuriously on tourism prose",
            failures)

    # Section-present trigger
    bilateral_recipe = _CHART_RECIPES["bilateral-trade-trajectory"]
    _assert(_recipe_fires(bilateral_recipe, "## 1.5. Bilateral Relations\n\nContent here."),
            "bilateral trigger did not fire on Section 1.5 presence",
            failures)
    _assert(not _recipe_fires(bilateral_recipe, "## 2. Political Context\n\nContent here."),
            "bilateral trigger fired without Section 1.5",
            failures)

    # Chart-present detection
    titles_with_remittance = ["remittance inflows by year"]
    _assert(_recipe_chart_present(remittances_recipe, titles_with_remittance),
            "_recipe_chart_present missed a matching chart",
            failures)
    _assert(not _recipe_chart_present(remittances_recipe, ["gdp growth"]),
            "_recipe_chart_present matched an unrelated chart",
            failures)

    # End-to-end: substantive brief mentioning remittances + UN snapback
    # (a tightened sanctions trigger phrase) but missing those charts →
    # warning fires with both recipes.
    paras = "\n\n".join(f"Paragraph {i}." for i in range(150))
    brief = f"""## Bottom line

Short.

## 1. Country Snapshot

::: snapshot
### Economy
- Remittances / GDP | ~20%
- Sanctions | UN snapback active since Sept 2025
:::

## 14. Sanctions Exposure

Sanctions reimposed under UN snapback architecture.

{paras}
"""
    warnings, _ = validate_brief(brief)
    chart_recipe_warnings = [w for w in warnings if "chart recipe" in w.lower()]
    _assert(len(chart_recipe_warnings) >= 1,
            f"chart-recipe check did not fire on remittances+sanctions brief: warnings = {warnings[:5]}",
            failures)
    if chart_recipe_warnings:
        warning_text = chart_recipe_warnings[0]
        _assert("remittances-trajectory" in warning_text,
                f"warning missing remittances-trajectory recipe: {warning_text[:300]}",
                failures)
        _assert("sanctions-packages-timeline" in warning_text,
                f"warning missing sanctions-packages-timeline recipe: {warning_text[:300]}",
                failures)

    # Negative case: brief with remittances mentioned AND a remittance chart
    # present → recipe should NOT be flagged as missing
    brief_with_chart = f"""## Bottom line

Short.

## 3. Economic Conditions

Remittances are 20% of GDP.

::: chart
type: line
title: Remittance inflows over time
x: 2020 | 2021
y: Remittances | 100 | 110
:::

{paras}
"""
    warnings, _ = validate_brief(brief_with_chart)
    chart_recipe_warnings = [w for w in warnings if "chart recipe" in w.lower() and "remittances-trajectory" in w]
    _assert(len(chart_recipe_warnings) == 0,
            f"recipe flagged as missing even though matching chart is present: {chart_recipe_warnings}",
            failures)

    return failures


def test_chart_count_and_chronology_checks():
    """Two related under-delivery patterns in the May 2026 brief series:
       - charts dropped from 3-5 (earlier briefs) to 1-2 (current);
       - dated chronologies dropped to inline prose.
    Both should be caught at the validator level so future briefs are
    pushed toward the SKILL.md spec without per-brief intervention.
    """
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import validate_brief
    finally:
        sys.path.pop(0)

    paras = "\n\n".join(
        f"Paragraph {i} of analytical prose on this country."
        for i in range(150)
    )

    # ---- Chart count checks ----
    # Floor is 3 per SKILL.md spec; brief with 2 charts should warn.
    brief_two_charts = f"""## Bottom line

Short.

## 3. Economic Conditions

::: chart
type: line
title: GDP
x: 2024 | 2025
y: GDP | 1 | 2
:::

::: chart
type: bar
title: Sectors
x: A | B
y: GDP | 1 | 2
:::

{paras}
"""
    warnings, _ = validate_brief(brief_two_charts)
    matches = [w for w in warnings if "only 2 chart" in w]
    _assert(len(matches) >= 1,
            f"chart-count check did not fire on 2-chart brief (floor is 3): warnings sample = {warnings[:5]}",
            failures)

    # Brief with 3 charts should NOT fire the under-count warning
    brief_three_charts = f"""## Bottom line

Short.

## 3. Economic Conditions

::: chart
type: line
title: GDP
x: 2024 | 2025
y: GDP | 1 | 2
:::

::: chart
type: bar
title: Sectors
x: A | B
y: GDP | 1 | 2
:::

::: chart
type: line
title: Debt
x: 2024 | 2025
y: Debt | 1 | 2
:::

{paras}
"""
    warnings, _ = validate_brief(brief_three_charts)
    matches = [w for w in warnings if "chart" in w.lower() and ("only " in w or "spec floor" in w)]
    _assert(len(matches) == 0,
            f"chart-count check fired on 3-chart brief (at floor): {matches}",
            failures)

    # Brief with 9 charts should fire the soft-ceiling warning
    chart_block = "::: chart\ntype: line\ntitle: Chart {i}\nx: 2024 | 2025\ny: V | 1 | 2\n:::\n"
    nine_chart_body = "\n\n".join(chart_block.replace("{i}", str(i)) for i in range(9))
    brief_nine_charts = f"""## Bottom line

Short.

## 3. Economic Conditions

{nine_chart_body}

{paras}
"""
    warnings, _ = validate_brief(brief_nine_charts)
    matches = [w for w in warnings if "ceiling" in w.lower() and "chart" in w.lower()]
    _assert(len(matches) >= 1,
            f"chart-count soft-ceiling check did not fire on 9-chart brief: warnings sample = {warnings[:5]}",
            failures)

    # ---- Chronology checks ----
    # Case C: brief with Section 4 but no chronology should warn
    brief_no_chrono = f"""## Bottom line

Short.

## 4. Security & Stability

Some security prose with no dated events.

{paras}
"""
    warnings, _ = validate_brief(brief_no_chrono)
    matches = [w for w in warnings if "chronology" in w.lower()]
    _assert(len(matches) >= 1,
            f"chronology check did not fire on Section 4 without dated content: {warnings[:5]}",
            failures)

    # Case D: brief with Section 4 + Date-column table should NOT warn
    brief_with_date_table = f"""## Bottom line

Short.

## 4. Security & Stability

| Date | Event |
|------|-------|
| 2024-01 | Coup attempt |
| 2024-06 | Election held |
| 2025-03 | New government |

{paras}
"""
    warnings, _ = validate_brief(brief_with_date_table)
    matches = [w for w in warnings if "chronology" in w.lower()]
    _assert(len(matches) == 0,
            f"chronology check fired on brief with Date-column table: {matches}",
            failures)

    # Case E: brief with 3+ year-prefixed bullets should NOT warn
    brief_with_year_bullets = f"""## Bottom line

Short.

## 11. Election Cycle

- 2024-05: General election
- 2024-06: Coalition negotiations
- 2024-07: New government sworn in
- 2025-01: Parliamentary cycle

{paras}
"""
    warnings, _ = validate_brief(brief_with_year_bullets)
    matches = [w for w in warnings if "chronology" in w.lower()]
    _assert(len(matches) == 0,
            f"chronology check fired on brief with year-prefixed bullets: {matches}",
            failures)

    # Case F: brief with no Section 4 or 11 should NOT trigger chronology check
    brief_no_relevant_sections = f"""## Bottom line

Short.

## 6. Social & Human Development

Some prose with no dated events.

{paras}
"""
    warnings, _ = validate_brief(brief_no_relevant_sections)
    matches = [w for w in warnings if "chronology" in w.lower()]
    _assert(len(matches) == 0,
            f"chronology check fired despite no Section 4 or 11: {matches}",
            failures)

    # Case G: Section 1.5 present without chronology should warn
    brief_s15_no_chrono = f"""## Bottom line

Short.

## 1.5. Bilateral Relations: UAE

Some bilateral prose with no dated content.

{paras}
"""
    warnings, _ = validate_brief(brief_s15_no_chrono)
    matches = [w for w in warnings if "Section 1.5" in w and "chronology" in w.lower()]
    _assert(len(matches) >= 1,
            f"section-scoped chronology check did not fire on Section 1.5 without dates: {warnings[:5]}",
            failures)

    # Case H: Section 1.5 with year-bullets should NOT warn
    brief_s15_with_chrono = f"""## Bottom line

Short.

## 1.5. Bilateral Relations: UAE

- 2024-05: UAE FM visit to capital
- 2025-02: Bilateral committee
- 2025-11: Joint investment forum
- 2026-03: Working group session

{paras}
"""
    warnings, _ = validate_brief(brief_s15_with_chrono)
    matches = [w for w in warnings if "Section 1.5" in w and "chronology" in w.lower()]
    _assert(len(matches) == 0,
            f"section-scoped chronology check fired despite Section 1.5 having year-bullets: {matches}",
            failures)

    # Case I: section-scoped means a chronology in Section 4 doesn't cover Section 11
    brief_s4_chrono_but_s11_empty = f"""## Bottom line

Short.

## 4. Security & Stability

| Date | Event |
|------|-------|
| 2024-01 | Event |
| 2024-06 | Event |
| 2025-03 | Event |

## 11. Election Cycle

Election prose without dates.

{paras}
"""
    warnings, _ = validate_brief(brief_s4_chrono_but_s11_empty)
    s4_warnings = [w for w in warnings if "Section 4" in w and "chronology" in w.lower()]
    s11_warnings = [w for w in warnings if "Section 11" in w and "chronology" in w.lower()]
    _assert(len(s4_warnings) == 0,
            f"chronology check spuriously fired on Section 4 that has a Date table: {s4_warnings}",
            failures)
    _assert(len(s11_warnings) >= 1,
            f"section-scoped chronology check did not fire on Section 11 without dates "
            f"(despite Section 4 having dates — proves checks are independent): {warnings[:5]}",
            failures)

    return failures


def test_thematic_map_coverage_checks():
    """Catch the recurring failure mode where a brief carries sub-national
    data (severity-box, election section) but doesn't render a choropleth
    map. The reference map alone under-delivers on visualization compared
    to the SKILL.md spec calling for 1-2 maps per brief.
    """
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import validate_brief
    finally:
        sys.path.pop(0)

    paras = "\n\n".join(
        f"Paragraph {i} of substantive analytical prose on the country."
        for i in range(150)
    )

    # Case 1: severity-box present, only a reference map — should warn
    brief_severity_no_choropleth = f"""## Bottom line

Short.

## 1. Country Snapshot

::: map
type: reference
country: Testland
:::

## 4. Security & Stability

::: severity-box
- Province A | high | Conflict ongoing
- Province B | medium | Tensions
:::

{paras}
"""
    warnings, _ = validate_brief(brief_severity_no_choropleth)
    matches = [w for w in warnings if "severity-box" in w and "choropleth" in w]
    _assert(len(matches) >= 1,
            f"map-coverage check did not fire on severity-box + reference-only map. Warnings: {warnings}",
            failures)

    # Case 2: severity-box present, choropleth map present — should NOT warn
    brief_severity_with_choropleth = f"""## Bottom line

Short.

## 4. Security & Stability

::: map
type: choropleth
country: Testland
region: A | high
region: B | medium
:::

::: severity-box
- Province A | high | Conflict ongoing
- Province B | medium | Tensions
:::

{paras}
"""
    warnings, _ = validate_brief(brief_severity_with_choropleth)
    matches = [w for w in warnings if "severity-box" in w and "choropleth" in w]
    _assert(len(matches) == 0,
            f"map-coverage check fired on a brief with both severity-box and choropleth: {matches}",
            failures)

    # Case 3: Section 11 (elections) present, no choropleth — should warn
    brief_election_no_choropleth = f"""## Bottom line

Short.

## 1. Country Snapshot

::: map
type: reference
country: Testland
:::

## 11. Election Cycle and Political Transition

Election prose.

{paras}
"""
    warnings, _ = validate_brief(brief_election_no_choropleth)
    matches = [w for w in warnings if "Section 11" in w and "choropleth" in w]
    _assert(len(matches) >= 1,
            f"election-map check did not fire on Section 11 without choropleth: {warnings}",
            failures)

    return failures


def test_auto_cache_to_bundled():
    """Successful photo resolutions (explicit URL, Wikipedia hit) should
    auto-cache into assets/leaders/{slug}.{ext} so future briefs resolve
    locally. Analyst-curated photos (if a bundled file already exists for
    the slug) win over auto-cache — the function is a no-op in that case.
    Failures are logged, never raised.
    """
    import tempfile
    import base64
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief import fenced_divs
    finally:
        sys.path.pop(0)

    # 1x1 PNG
    tiny_png = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )
    tiny_png_b64 = base64.b64encode(tiny_png).decode("ascii")
    photo_data_png = ("image/png", tiny_png_b64)

    original_root = fenced_divs._PKG_ROOT_LEADERS
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        fenced_divs._PKG_ROOT_LEADERS = tmpdir_path
        try:
            # 1. Auto-cache writes the file when bundled directory is empty
            fenced_divs._maybe_cache_to_bundled("New Ambassador", photo_data_png)
            cached_path = tmpdir_path / "new-ambassador.png"
            _assert(cached_path.exists(),
                    f"auto-cache did not write file at {cached_path}",
                    failures)
            _assert(cached_path.read_bytes() == tiny_png,
                    "auto-cached file content differs from input",
                    failures)

            # 2. Honorific stripping applies — same call with honorific
            #    creates the same slug, so the bundled file already exists
            #    and no second write happens.
            mtime_before = cached_path.stat().st_mtime
            fenced_divs._maybe_cache_to_bundled("Dr. New Ambassador", photo_data_png)
            mtime_after = cached_path.stat().st_mtime
            _assert(mtime_before == mtime_after,
                    "auto-cache should not overwrite an existing bundled file",
                    failures)

            # 3. Analyst curation wins — different name, same slug after
            #    honorific strip; if curated file already exists, no overwrite
            (tmpdir_path / "curated-leader.jpg").write_bytes(b"FAKE_CURATED")
            fenced_divs._maybe_cache_to_bundled("Curated Leader", photo_data_png)
            curated = tmpdir_path / "curated-leader.jpg"
            _assert(curated.read_bytes() == b"FAKE_CURATED",
                    "auto-cache overwrote analyst-curated file",
                    failures)
            # No PNG sibling either
            _assert(not (tmpdir_path / "curated-leader.png").exists(),
                    "auto-cache wrote a duplicate when curated file existed",
                    failures)

            # 4. Empty / invalid input is a safe no-op
            fenced_divs._maybe_cache_to_bundled("", photo_data_png)
            fenced_divs._maybe_cache_to_bundled("Test", None)
            fenced_divs._maybe_cache_to_bundled("Test", ("image/unknown", "abc"))
            # None of the above should crash; none should write a file with
            # weird names.
            unexpected = list(tmpdir_path.glob("*"))
            # Expected: new-ambassador.png + curated-leader.jpg
            unexpected_names = {p.name for p in unexpected}
            _assert(unexpected_names == {"new-ambassador.png", "curated-leader.jpg"},
                    f"unexpected files in cache dir: {unexpected_names}",
                    failures)
        finally:
            fenced_divs._PKG_ROOT_LEADERS = original_root

    return failures


def test_honorific_stripping():
    """Honorifics on leader names (Dr., Sheikh, H.E., Hon., etc.) must be
    stripped before Wikipedia lookups and bundled-photo slug derivation,
    or the cascade systematically misses ministers and ambassadors whose
    Wikipedia article URLs don't carry the title. The card's display name
    is unchanged."""
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief import fenced_divs
    finally:
        sys.path.pop(0)

    cases = [
        # (input, expected stripped, expected slug)
        ("Dr. Thani bin Ahmed Al Zeyoudi", "Thani bin Ahmed Al Zeyoudi", "thani-bin-ahmed-al-zeyoudi"),
        ("H.E. Jumaa Rashed Al Remeithi", "Jumaa Rashed Al Remeithi", "jumaa-rashed-al-remeithi"),
        ("Sheikh Mohamed bin Zayed", "Mohamed bin Zayed", "mohamed-bin-zayed"),
        ("Hon. John Steenhuisen", "John Steenhuisen", "john-steenhuisen"),
        ("Prof. Mahmood Mamdani", "Mahmood Mamdani", "mahmood-mamdani"),
        ("Sir John Smith", "John Smith", "john-smith"),
        ("HRH Sheikh Hamdan bin Mohammed", "Hamdan bin Mohammed", "hamdan-bin-mohammed"),
        ("His Excellency Jumaa Al Remeithi", "Jumaa Al Remeithi", "jumaa-al-remeithi"),
        ("Cyril Ramaphosa", "Cyril Ramaphosa", "cyril-ramaphosa"),  # no honorific
        ("Ayatollah Khamenei", "Khamenei", "khamenei"),
        ("General Asim Munir", "Asim Munir", "asim-munir"),
    ]
    for raw, expected_stripped, expected_slug in cases:
        actual_stripped = fenced_divs._strip_honorific(raw)
        _assert(actual_stripped == expected_stripped,
                f"_strip_honorific({raw!r}) = {actual_stripped!r}, expected {expected_stripped!r}",
                failures)
        actual_slug = fenced_divs._leader_slug(raw)
        _assert(actual_slug == expected_slug,
                f"_leader_slug({raw!r}) = {actual_slug!r}, expected {expected_slug!r}",
                failures)

    # Honorific stripping is case-insensitive
    _assert(fenced_divs._strip_honorific("DR. SMITH") == "SMITH",
            "honorific stripping should be case-insensitive",
            failures)
    _assert(fenced_divs._strip_honorific("dr. smith") == "smith",
            "honorific stripping should be case-insensitive (lowercase)",
            failures)

    # Empty / None handled gracefully
    _assert(fenced_divs._strip_honorific("") == "",
            "empty input should return empty",
            failures)
    _assert(fenced_divs._strip_honorific("Honorable") == "Honorable",
            "bare honorific without space should NOT be stripped (not a prefix)",
            failures)

    return failures


def test_min_leader_card_count():
    """Section-aware floors on leader-cards block size:
       - Section 1.5 (bilateral): min 2 cards
       - Section 2 (political context): min 3 cards
       - Any other section: min 2 cards (generic floor)
    Each below-floor block produces a structural warning. This prevents the
    'trim for aesthetics' failure mode where key political figures get
    dropped to make the visual look cleaner."""
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import validate_brief
    finally:
        sys.path.pop(0)

    # Need a brief long enough to clear the 120-body-line structural-audit
    # gate, so the leader-cards checks actually fire.
    body_padding = "\n\n".join(
        f"Paragraph {i} of analytical prose on this country's situation."
        for i in range(150)
    )

    # Case 1: Section 2 with only 2 cards (below the 3-card floor)
    brief_undersized_s2 = f"""## Bottom line

Short.

## 1. Country Snapshot

::: snapshot
### People
- Population | 10M
:::

## 2. Political Context

::: leader-cards
title: Leadership

- Head of State | President | Ruling Party
- Prime Minister | PM | Ruling Party
:::

{body_padding}
"""
    warnings, _ = validate_brief(brief_undersized_s2)
    matches = [w for w in warnings if "Section 2 leader-cards" in w]
    _assert(len(matches) >= 1,
            f"min-cards check did not fire for 2-card Section 2 block. Warnings: {warnings}",
            failures)

    # Case 2: Section 1.5 with only 1 card (below the 2-card floor)
    brief_undersized_s15 = f"""## Bottom line

Short.

## 1.5. Bilateral Relations

::: leader-cards
title: Bilateral

- Sole Ambassador | UAE→Country | UAE Embassy
:::

{body_padding}
"""
    warnings, _ = validate_brief(brief_undersized_s15)
    matches = [w for w in warnings if "Section 1.5 leader-cards" in w and "only" in w]
    _assert(len(matches) >= 1,
            f"min-cards check did not fire for 1-card Section 1.5 block. Warnings: {warnings}",
            failures)

    # Case 2b: Section 1.5 with >2 cards (above the new upper bound)
    brief_oversized_s15 = f"""## Bottom line

Short.

## 1.5. Bilateral Relations

::: leader-cards
title: Bilateral

- UAE Ambassador | Role | UAE Embassy
- Host Ambassador | Role | Host Embassy
- UAE Trade Minister | Role | UAE MoE
- Host Trade Minister | Role | Host MoT
:::

{body_padding}
"""
    warnings, _ = validate_brief(brief_oversized_s15)
    matches = [w for w in warnings if "Section 1.5 leader-cards has 4 cards" in w]
    _assert(len(matches) >= 1,
            f"upper-bound check did not fire for 4-card Section 1.5 block. Warnings: {warnings}",
            failures)

    # Case 3: a properly-sized Section 2 (4 cards) and Section 1.5 (2 cards)
    # — should produce no min-cards warnings
    brief_ok = f"""## Bottom line

Short.

## 1.5. Bilateral Relations

::: leader-cards
title: Bilateral

- UAE Ambassador | Role | UAE Embassy
- Host-country Ambassador | Role | Host Embassy
:::

## 2. Political Context

::: leader-cards
title: Political leadership

- Head of State | President | Ruling
- PM | Prime Minister | Ruling
- Opposition Lead | Opposition | Opposition Party
- Key Minister | Minister | Ruling
:::

{body_padding}
"""
    warnings, _ = validate_brief(brief_ok)
    matches = [w for w in warnings if "leader-cards block" in w]
    _assert(len(matches) == 0,
            f"min-cards check fired on well-sized blocks: {matches}",
            failures)

    return failures


def test_bundled_leader_photo_cascade():
    """Photos dropped into assets/leaders/{slug}.{ext} should resolve before
    the Wikipedia cascade fires. Test does this without polluting the real
    bundled directory: creates a tempdir with a known PNG, monkey-patches
    the module's _PKG_ROOT_LEADERS, and verifies lookup."""
    import tempfile
    import shutil
    import base64

    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief import fenced_divs
    finally:
        sys.path.pop(0)

    # 1x1 transparent PNG (smallest valid PNG)
    tiny_png = base64.b64decode(
        b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )

    original_root = fenced_divs._PKG_ROOT_LEADERS
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Drop a test photo under a known slug
        (tmpdir_path / "test-curated-leader.png").write_bytes(tiny_png)
        # Point the module at the temp directory
        fenced_divs._PKG_ROOT_LEADERS = tmpdir_path
        try:
            # Slug derivation should produce 'test-curated-leader' from this name
            slug = fenced_divs._leader_slug("Test Curated Leader")
            _assert(slug == "test-curated-leader",
                    f"slug derivation wrong: got {slug!r}",
                    failures)

            # Lookup should find the photo
            result = fenced_divs._lookup_bundled_leader_photo("Test Curated Leader")
            _assert(result is not None,
                    "bundled-photo lookup returned None for known curated photo",
                    failures)
            if result is not None:
                mime, b64 = result
                _assert(mime == "image/png",
                        f"bundled-photo lookup returned wrong mime: {mime}",
                        failures)

            # Slug derivation handles diacritics + particles
            _assert(fenced_divs._leader_slug("Houmed M'saidié") == "houmed-msaidie",
                    "slug derivation didn't normalize diacritics + apostrophe",
                    failures)
            # "Sheikh" is now treated as an honorific and stripped; slug uses
            # the canonical name. This matches Wikipedia's article URL
            # convention (en.wikipedia.org/wiki/Mohamed_bin_Zayed_Al_Nahyan).
            _assert(fenced_divs._leader_slug("Sheikh Mohamed bin Zayed") == "mohamed-bin-zayed",
                    f"slug should strip Sheikh honorific: got {fenced_divs._leader_slug('Sheikh Mohamed bin Zayed')!r}",
                    failures)

            # Lookup for an uncurated name should miss
            miss = fenced_divs._lookup_bundled_leader_photo("Nonexistent Person 123")
            _assert(miss is None,
                    f"bundled-photo lookup returned hit for nonexistent name: {miss}",
                    failures)
        finally:
            fenced_divs._PKG_ROOT_LEADERS = original_root

    return failures


def test_metadata_block_wrappers():
    """Notes, Methodological back-matter, and Bibliography all render
    inside divs that carry both their specific class and the shared
    `metadata-block` class. The CSS gives all three the same small-font
    metadata-tier typography. The Methodological wrapper closes properly
    when Bibliography (or any subsequent H2) opens — no nesting."""
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.pipeline import render_basic_markdown
    finally:
        sys.path.pop(0)

    # 1. Methodological back-matter section wraps in correct div
    md = """## Recommendations

Some recs.

## Methodological back-matter

Vintage notes here.

## Bibliography

World Bank. WDI 2024.
"""
    html = render_basic_markdown(md)
    _assert('<div class="methodological metadata-block">' in html,
            f"methodological wrapper missing or wrong class: {html[:400]}",
            failures)
    _assert('<div class="bibliography metadata-block">' in html,
            f"bibliography wrapper missing the metadata-block class: {html[:400]}",
            failures)

    # 2. Methodological wrapper closes before bibliography opens — no nesting
    meth_start = html.find('<div class="methodological metadata-block">')
    bib_start = html.find('<div class="bibliography metadata-block">')
    if meth_start >= 0 and bib_start >= 0:
        # Between meth_start and bib_start, there should be a </div>
        # belonging to the methodological wrapper
        between = html[meth_start:bib_start]
        _assert('</div>' in between,
                "methodological wrapper not closed before bibliography opens",
                failures)

    # 3. Methodology alias also recognized
    md_alt = """## Methodology

Some methodology prose.
"""
    html_alt = render_basic_markdown(md_alt)
    _assert('<div class="methodological metadata-block">' in html_alt,
            "'## Methodology' (without 'back-matter') not recognized as methodological wrapper",
            failures)

    # 4. Regular H2 headings do NOT get a wrapper
    md_regular = """## 1. Country Snapshot

Regular content.
"""
    html_regular = render_basic_markdown(md_regular)
    _assert('metadata-block' not in html_regular,
            "regular H2 spuriously wrapped in metadata-block",
            failures)

    return failures


def test_bibliography_auto_numbers():
    """Bibliography section content should auto-render as a single numbered
    <ol>, regardless of whether the analyst wrote entries as paragraphs,
    as a markdown numbered list with blank lines between entries (which
    naively closes the <ol> on each blank line), or as a single tight
    numbered list. The _normalize_bibliography post-pass in pipeline.py
    handles all three cases."""
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.pipeline import render_basic_markdown
    finally:
        sys.path.pop(0)

    # Case 1: paragraphs (most common analyst-written form)
    md_paragraphs = """## Bibliography

World Bank. World Development Indicators, 2024.

IMF. World Economic Outlook, April 2026.

UNDP. Human Development Report 2024.
"""
    html = render_basic_markdown(md_paragraphs)
    _assert(html.count('<ol class="bibliography-list">') == 1,
            f"paragraph-form bibliography did not produce a single <ol>: html={html[:200]}",
            failures)
    _assert(html.count('<li>') == 3,
            f"paragraph-form bibliography did not produce 3 <li>s: html={html[:200]}",
            failures)

    # Case 2: numbered markdown list with blank lines between entries
    # (the case that produced one <ol> per entry before the post-pass)
    md_blank_sep = """## Bibliography

1. World Bank. WDI 2024.

2. IMF. WEO April 2026.

3. UNDP. HDR 2024.
"""
    html = render_basic_markdown(md_blank_sep)
    _assert(html.count('<ol class="bibliography-list">') == 1,
            "blank-separated numbered list did not consolidate to one <ol>",
            failures)
    _assert(html.count('<li>') == 3,
            "blank-separated numbered list did not produce 3 <li>s",
            failures)

    # Case 3: tight numbered list (single block, no blank lines between)
    md_tight = """## Bibliography

1. World Bank. WDI 2024.
2. IMF. WEO April 2026.
3. UNDP. HDR 2024.
"""
    html = render_basic_markdown(md_tight)
    _assert(html.count('<ol class="bibliography-list">') == 1,
            "tight numbered list did not produce one <ol>",
            failures)
    _assert(html.count('<li>') == 3,
            "tight numbered list did not produce 3 <li>s",
            failures)

    # Case 4: brief without a bibliography should not produce an
    # ol.bibliography-list anywhere
    md_no_bib = "## Section\n\nSome content.\n"
    html = render_basic_markdown(md_no_bib)
    _assert('ol class="bibliography-list"' not in html,
            "non-bibliography brief produced a bibliography-list",
            failures)

    return failures


def test_arabic_aware_validator_checks():
    """Validator must recognize the Arabic-language equivalents of three
    checks that previously hard-coded English literals:

      1. Section-scoped chronology (`_has_chronology_in`) — Arabic date-
         column table headers (التاريخ / الوقت / الفترة) and Arabic month
         names in bullet prefixes.
      2. Recommendations section — `## التوصيات` or `**التوصيات**` should
         satisfy the check that previously only matched `Recommendations`.
      3. Chart-recipe registry — Arabic keywords (keyword_ar) on recipe
         triggers and Arabic title keywords (title_keywords_ar) on recipe
         match-checks should suppress spurious "recipe X would fire" warnings
         for Arabic briefs whose content already covers the recipe.

    Without these fixes, every substantive Arabic brief emits a fixed set of
    false-positive warnings — chronology missing, recommendations missing,
    recipes unfulfilled — even when the analyst has done the work in Arabic.
    """
    failures = []
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    try:
        from country_brief.validation import (
            validate_brief, _has_chronology_in, _recipe_fires,
            _recipe_chart_present, _CHART_RECIPES,
        )
    finally:
        sys.path.pop(0)

    # ---- (1) Chronology: Arabic date column header ----
    arabic_date_table = """| التاريخ | الحدث |
|---------|--------|
| 2026-01-15 | حدث الأول |
| 2026-02-28 | حدث الثاني |
"""
    _assert(_has_chronology_in(arabic_date_table),
            "Arabic date-column header `التاريخ` should satisfy chronology check",
            failures)

    # English equivalent still works (no regression)
    english_date_table = """| Date | Event |
|------|-------|
| 2026-01-15 | First |
"""
    _assert(_has_chronology_in(english_date_table),
            "English `Date` column header regressed",
            failures)

    # Arabic month-name bullets should also satisfy the check
    arabic_month_bullets = """
- مايو 2024: حدث
- أبريل 2025: حدث آخر
- يونيو 2025: حدث ثالث
"""
    _assert(_has_chronology_in(arabic_month_bullets),
            "Arabic Gregorian month names in bullets should satisfy chronology",
            failures)

    # ---- (2) Recommendations: Arabic heading variant ----
    paras = "\n\n".join(f"فقرة تحليلية رقم {i} عن البلد." for i in range(150))
    brief_arabic_recs = f"""## خلاصة القول

نص قصير.

## 4. الأمن والاستقرار

::: severity-box
- المنطقة | تهديد عالٍ | وصف
:::

## التوصيات

> **توصية أولى** *المسؤول:* لجنة. *الإطار الزمني:* فوري.
> **توصية ثانية** *المسؤول:* فريق. *الإطار الزمني:* فوري.
> **توصية ثالثة** *المسؤول:* فريق. *الإطار الزمني:* فوري.

{paras}
"""
    warnings, _ = validate_brief(brief_arabic_recs)
    rec_missing = [w for w in warnings if "no Recommendations section found" in w]
    _assert(len(rec_missing) == 0,
            f"Recommendations check fired on Arabic `## التوصيات` heading "
            f"(found warnings: {rec_missing})",
            failures)

    # English form still passes (no regression)
    brief_english_recs = brief_arabic_recs.replace("## التوصيات", "## Recommendations")
    warnings, _ = validate_brief(brief_english_recs)
    rec_missing = [w for w in warnings if "no Recommendations section found" in w]
    _assert(len(rec_missing) == 0,
            "Recommendations check regressed on English `## Recommendations`",
            failures)

    # ---- (3) Chart-recipe registry: Arabic keywords ----
    # fx-trajectory should fire when "الريال" is in the body, and a chart
    # titled "سعر الصرف للريال" should satisfy the recipe.
    fx_recipe = _CHART_RECIPES["fx-trajectory"]
    arabic_fx_body = "تراجع الريال إلى مستوى قياسي منخفض في 2026."
    _assert(_recipe_fires(fx_recipe, arabic_fx_body),
            "fx-trajectory recipe should fire on Arabic 'الريال'",
            failures)
    _assert(_recipe_chart_present(fx_recipe, ["مسار سعر الصرف للريال الإيراني"]),
            "fx-trajectory should detect Arabic chart title with 'سعر الصرف'",
            failures)

    # sanctions-packages-timeline should fire on Arabic snapback wording
    sanc_recipe = _CHART_RECIPES["sanctions-packages-timeline"]
    arabic_sanc_body = "أعيد تفعيل آلية snapback؛ وفُرضت حزم عقوبات إضافية."
    _assert(_recipe_fires(sanc_recipe, arabic_sanc_body),
            "sanctions-packages-timeline should fire on Arabic snapback wording",
            failures)

    return failures


# -----------------------------------------------------------------------------
# Test runner
# -----------------------------------------------------------------------------

TESTS = [
    ("minimal renders cleanly", test_minimal_renders),
    ("full-stress exercises all components", test_full_stress_renders),
    ("broken fixture emits expected warnings", test_broken_fixture_emits_warnings),
    ("map labels are not silently dropped", test_map_labels_all_present),
    ("capital city override works (Morocco/Rabat)", test_capital_city_correct),
    ("extended risk vocabulary accepted", test_extended_risk_vocabulary),
    ("snapshot content renders (not silently empty)", test_snapshot_content_rendered),
    ("risk matrix content renders all risks", test_risk_matrix_content_rendered),
    ("manifest validation catches mismatches", test_manifest_validation),
    ("home-country flag validates against markdown", test_home_country_consistency_validation),
    ("faction-box extended categories (military/religious)", test_faction_box_extended_categories),
    ("leader-cards component renders correctly", test_leader_cards_renders),
    ("structural validation checks fire correctly", test_structural_validation_checks),
    ("--strict mode promotes binding structural checks", test_strict_mode_promotes_binding_checks),
    ("bibliography auto-numbers regardless of input form", test_bibliography_auto_numbers),
    ("metadata-block wrappers apply to notes / methodological / bibliography", test_metadata_block_wrappers),
    ("bundled leader-photo cascade resolves curated photos", test_bundled_leader_photo_cascade),
    ("minimum-card-count validator fires on undersized leader blocks", test_min_leader_card_count),
    ("honorific stripping for leader-card lookups", test_honorific_stripping),
    ("auto-cache successful photo fetches to bundled directory", test_auto_cache_to_bundled),
    ("thematic-map coverage checks fire on missing choropleth", test_thematic_map_coverage_checks),
    ("chart count and chronology checks fire on under-delivery", test_chart_count_and_chronology_checks),
    ("chart recipe registry detects missing decision-relevant charts", test_chart_recipe_registry),
    ("validator recognizes Arabic chronology / recommendations / recipes", test_arabic_aware_validator_checks),
]


def main():
    print(f"{BOLD}Running smoke tests for country-brief renderer{RESET}")
    print(f"  Fixtures: {FIXTURES_DIR}")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    total_start = time.time()
    passed = 0
    failed = 0

    for name, test_fn in TESTS:
        t0 = time.time()
        try:
            failures = test_fn()
        except Exception as e:
            failures = [f"exception during test: {e!r}"]
        elapsed = time.time() - t0

        if failures:
            failed += 1
            print(f"  {RED}✗{RESET} {name}  ({elapsed:.1f}s)")
            for f in failures:
                print(f"      {RED}- {f}{RESET}")
        else:
            passed += 1
            print(f"  {GREEN}✓{RESET} {name}  ({elapsed:.1f}s)")

    total_elapsed = time.time() - total_start
    print()
    print(f"{BOLD}Summary:{RESET} {passed} passed, {failed} failed in {total_elapsed:.1f}s")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
