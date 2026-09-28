"""antitextai: strip AI text and code tells from prose, Markdown, and source code.

Library use:

    from antitextai import clean, assert_no_artifacts, scan_text

    text = clean(open("draft.md", encoding="utf-8").read())
    assert_no_artifacts(text)          # raises AssertionError with the residual
    report = scan_text(text)           # inventory before/after a pass

CLI use:

    python -m antitextai scan .
    python -m antitextai clean --write README.md
    python -m antitextai verify .
"""
from .cleaner import assert_no_artifacts, clean, setext_lines, split_frontmatter
from .scan import char_report, format_report, rule_report, scan_paths, scan_text
from .verify import verify_paths, verify_text

__version__ = "1.0.0"

__all__ = [
    "clean",
    "assert_no_artifacts",
    "split_frontmatter",
    "setext_lines",
    "scan_text",
    "scan_paths",
    "char_report",
    "rule_report",
    "format_report",
    "verify_text",
    "verify_paths",
    "__version__",
]
