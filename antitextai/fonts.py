"""Font-family detection: flag non-standard fonts as AI tells.

Only five Google-sourced sans-serif fonts are considered human-curated:
  Roboto, Open Sans, Montserrat, Lato, Poppins

Any other font-family declaration found in CSS, HTML inline styles,
or Google Fonts <link> tags is reported as an AI-generated typography
choice and the scanner suggests one of the five allowed replacements.
"""
from __future__ import annotations

import re
from typing import Iterable, Optional

ALLOWED = frozenset({
    "roboto",
    "open sans",
    "montserrat",
    "lato",
    "poppins",
})

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# CSS font-family declarations — captures the full value after the colon.
_CSS_FONT_FAMILY = re.compile(
    r"font-family\s*:\s*([^;{}]+);",
    re.IGNORECASE,
)

# Google Fonts <link> tags — extracts the family name(s) from the URL.
_GFONT_LINK = re.compile(
    r'<link[^>]+href=["\']([^"\']*(?:fonts\.googleapis\.com)[^"\']*)["\'][^>]*>',
    re.IGNORECASE,
)

# Inline style font-family — works inside style="..." attributes.
_INLINE_FONT_FAMILY = re.compile(
    r'''style\s*=\s*["\']([^"\']*font-family\s*:\s*[^;"]+)["\']''',
    re.IGNORECASE,
)

# Generic fallback keywords that are NOT themselves fonts.
_GENERIC = frozenset({
    "sans-serif", "serif", "monospace", "cursive", "fantasy",
    "system-ui", "ui-serif", "ui-sans-serif", "ui-monospace",
    "emoji", "math", "fangsong",
})


def _tokenize_family(value: str) -> list[str]:
    """Split a font-family value into individual family names."""
    return [t.strip().strip("'\"").lower() for t in value.split(",") if t.strip()]


def _is_allowed(name: str) -> bool:
    if name in ALLOWED:
        return True
    # Partial match: "open sans" matches "Open Sans, Helvetica, sans-serif"
    for allowed in ALLOWED:
        if allowed in name or name in allowed:
            return True
    return False


def _recommend(family: str) -> str:
    """Pick the closest allowed replacement for display."""
    # Heuristic: pick based on keyword overlap.
    keywords = {
        "roboto": {"modern", "clean", "ui", "web", "android", "geometric", "sans"},
        "open sans": {"humanist", "friendly", "neutral", "versatile", "body", "serif-like"},
        "montserrat": {"geometric", "elegant", "heading", "branding", "display", "bold", "impact"},
        "lato": {"warm", "professional", "semi-rounded", "body text", "serious"},
        "poppins": {"rounded", "contemporary", "geometric", "modern", "design", "display"},
    }
    family_lower = family.lower()
    best = "Roboto"
    best_score = 0
    for allowed, kws in keywords.items():
        score = sum(1 for kw in kws if kw in family_lower)
        if score > best_score:
            best_score = score
            best = allowed.title() if allowed != "open sans" else "Open Sans"
    return best


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class FontFinding:
    """One non-standard font-family occurrence."""
    __slots__ = ("path", "line", "col", "value", "offender", "recommendation")

    def __init__(
        self,
        path: str,
        line: int,
        col: int,
        value: str,
        offender: str,
        recommendation: str,
    ) -> None:
        self.path = path
        self.line = line
        self.col = col
        self.value = value
        self.offender = offender
        self.recommendation = recommendation

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "col": self.col,
            "value": self.value.strip(),
            "offender": self.offender,
            "recommendation": self.recommendation,
        }


def scan_text(path: str, text: str) -> list[FontFinding]:
    """Scan a single file's text for non-standard font-family declarations.

    Returns a list of findings; empty list means all fonts are allowed.
    """
    findings: list[FontFinding] = []
    lines = text.split("\n")
    pos = 0

    for i, line in enumerate(lines, start=1):
        # CSS declarations
        for m in _CSS_FONT_FAMILY.finditer(line):
            families = _tokenize_family(m.group(1))
            for family in families:
                if family in _GENERIC:
                    continue
                if not _is_allowed(family):
                    findings.append(FontFinding(
                        path=path,
                        line=i,
                        col=m.start() + family.lower().find(family.lower()) + 1,
                        value=m.group(1).strip(),
                        offender=family,
                        recommendation=_recommend(family),
                    ))

        # Inline styles
        for m in _INLINE_FONT_FAMILY.finditer(line):
            inner = re.search(r"font-family\s*:\s*([^;]+)", m.group(1), re.IGNORECASE)
            if inner:
                families = _tokenize_family(inner.group(1))
                for family in families:
                    if family in _GENERIC:
                        continue
                    if not _is_allowed(family):
                        findings.append(FontFinding(
                            path=path,
                            line=i,
                            col=m.start() + 1,
                            value=m.group(1).strip(),
                            offender=family,
                            recommendation=_recommend(family),
                        ))

        # Google Fonts links (may span multiple lines, but catch single-line for now)
        for m in _GFONT_LINK.finditer(line):
            url = m.group(1)
            # Extract family names from URL: /family=Roboto:ital,wght...
            family_match = re.search(r"family=([^&:]+)", url)
            if family_match:
                raw = family_match.group(1).replace("+", " ")
                for family in _tokenize_family(raw):
                    if not _is_allowed(family):
                        findings.append(FontFinding(
                            path=path,
                            line=i,
                            col=m.start() + 1,
                            value=raw,
                            offender=family,
                            recommendation=_recommend(family),
                        ))

    return findings


def scan_paths(
    paths: Iterable[str],
    *,
    extensions: Optional[Iterable[str]] = None,
    exclude_dirs: Optional[Iterable[str]] = None,
    exclude_globs: Iterable[str] = (),
) -> list[dict]:
    """Scan every text file under `paths` for non-standard fonts."""
    from .files import iter_text_files

    kwargs: dict = {"exclude_globs": exclude_globs}
    if extensions is not None:
        kwargs["extensions"] = extensions
    if exclude_dirs is not None:
        kwargs["exclude_dirs"] = exclude_dirs

    reports = []
    for path, text in iter_text_files(paths, **kwargs):
        findings = scan_text(str(path), text)
        if findings:
            report = {
                "path": str(path),
                "findings": [f.to_dict() for f in findings],
                "count": len(findings),
            }
            reports.append(report)
    return reports


def format_report(reports: list[dict]) -> str:
    """Plain-text report. Files with no findings are omitted."""
    out = []
    for r in reports:
        out.append(f"{r['path']}")
        for f in r["findings"]:
            out.append(
                f"    line {f['line']}:{f['col']}  "
                f"font-family: {f['value']!r}  "
                f"→ replace {f['offender']!r} with {f['recommendation']!r}"
            )
        out.append("")
    total = sum(r["count"] for r in reports)
    out.append(f"{len(reports)} file(s) with non-standard fonts, {total} offending declaration(s)")
    return "\n".join(out)
