#!/usr/bin/env python3
"""
render_brief.py — Backward-compatibility shim.

The renderer was split into a package (country_brief/) as part of Tier 2
maintainability work. This shim preserves the original CLI invocation
so existing scripts and documentation continue to work:

    python scripts/render_brief.py --input brief.md --output brief.pdf ...

New code should import from the package directly:

    from country_brief import main, render_basic_markdown, validate_brief
"""
import sys
from pathlib import Path

# Make the package importable when this script is invoked directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from country_brief import main

if __name__ == "__main__":
    main()
