"""antitextai: strip AI text and code tells from prose, Markdown, and source code.

    from antitextai import clean, assert_no_artifacts, scan_text
    assert_no_artifacts(clean(open("draft.md", encoding="utf-8").read()))
"""
from .cleaner import assert_no_artifacts, clean, setext_lines, split_frontmatter
from .fonts import format_report as format_font_report, scan_paths as scan_font_paths
from .comments import format_report as format_comment_report, scan_paths as scan_comment_paths, scrub_text
from .word import format_report as format_word_report, scan_paths as scan_word_paths
from .styles import format_report as format_style_report, scan_paths as scan_style_paths
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
    "scan_font_paths",
    "format_font_report",
    "scan_style_paths",
    "format_style_report",
    "scan_comment_paths",
    "format_comment_report",
    "scrub_text",
    "scan_word_paths",
    "format_word_report",
    "__version__",
]
