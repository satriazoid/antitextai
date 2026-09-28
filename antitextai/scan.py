"""Inventory pass: report AI tells without changing a single byte.

Read this before cleaning. The scan exists to answer two questions per file: which
characters are safe to map automatically, and which ones need a human decision
(em/en dashes above all). Skipping it is how a legitimate math symbol, a numeric
range dash, or an i18n test fixture gets destroyed.
"""
from __future__ import annotations

import bisect
import collections
import pathlib
import unicodedata
from typing import Iterable, Optional

from . import cleaner as C
from .files import iter_text_files

# Characters clean() maps deterministically. Finding these means "run the cleaner".
MAPPED_CODEPOINTS = frozenset(
    {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD, 0x200E, 0x200F,  # invisible / bidi
     0x00A0, 0x202F,                                                  # space variants
     0x2022}                                                          # bullet
) | frozenset(C.SMART)

# Characters clean() deliberately leaves alone: a rule cannot decide between a numeric
# range, a clause break, or a quotation. Every hit needs a human read.
REVIEW_CODEPOINTS = frozenset({0x2013, 0x2014})

# Decorative glyph families that read as generated formatting. Report-only: some are
# legitimate (a real tree diagram, a checked checklist), so the scan flags, never fixes.
DECORATIVE_RANGES = (
    (0x2500, 0x257F, "box drawing"),
    (0x2580, 0x259F, "block element"),
    (0x2190, 0x21FF, "arrow"),
    (0x2600, 0x27BF, "misc symbol / dingbat"),
    (0x1F300, 0x1FAFF, "emoji"),
    (0x1F000, 0x1F2FF, "enclosed / pictograph"),
)

# Legitimate non-ASCII that must survive a cleanup: math and Greek used in formulas,
# accented letters in real prose, CJK, currency.
KEEP_RANGES = (
    (0x00C0, 0x024F, "latin accented"),
    (0x0370, 0x03FF, "greek"),
    (0x0400, 0x04FF, "cyrillic"),
    (0x05D0, 0x05EA, "hebrew"),
    (0x0600, 0x06FF, "arabic"),
    (0x3000, 0x30FF, "cjk / kana"),
    (0x4E00, 0x9FFF, "cjk unified"),
    (0x2200, 0x22FF, "math operator"),
    (0x2260, 0x226F, "math relation"),
    (0x00B1, 0x00B1, "plus-minus"),
    (0x2265, 0x2265, "greater-or-equal"),
    (0x20AC, 0x20AC, "euro sign"),
)

RULE_GROUPS = (
    ("INVISIBLE", C.INVISIBLE),
    ("NBSP", C.NBSP),
    ("BULLET", C.BULLET_LEAD),
    ("BARE_FLUFF", C.BARE_FLUFF),
    ("SALUTATION", C.SALUTATION),
    ("INLINE_OUTRO", C.INLINE_OUTRO),
    ("INTERJECT", C.INTERJECT),
    ("CLAUSE", C.CLAUSE),
    ("SUBORDINATE", C.SUBORDINATE),
    ("GESTURE_INLINE", C.GESTURE_INLINE),
    ("PRECODE", C.PRECODE),
    ("END_WHOLE", C.END_WHOLE),
    ("END_TRAIL", C.END_TRAIL),
    ("NARRATION", C.NARRATION),
    ("STEPNARR", C.STEPNARR),
    ("SEPARATOR", C.SEPARATOR),
)

MAX_EXAMPLES = 5


def _classify(cp: int) -> str:
    if cp in MAPPED_CODEPOINTS:
        return "mapped"
    if cp in REVIEW_CODEPOINTS:
        return "review"
    for lo, hi, _ in DECORATIVE_RANGES:
        if lo <= cp <= hi:
            return "decorative"
    for lo, hi, _ in KEEP_RANGES:
        if lo <= cp <= hi:
            return "keep"
    return "unclassified"


def _family(cp: int) -> str:
    for lo, hi, name in DECORATIVE_RANGES:
        if lo <= cp <= hi:
            return name
    for lo, hi, name in KEEP_RANGES:
        if lo <= cp <= hi:
            return name
    return ""


def char_report(text: str) -> list[dict]:
    """One entry per distinct non-ASCII codepoint, with count and first location."""
    counts: collections.Counter[int] = collections.Counter()
    first: dict[int, tuple[int, int]] = {}
    line = 1
    col = 0
    for ch in text:
        col += 1
        if ch == "\n":
            line += 1
            col = 0
            continue
        cp = ord(ch)
        if cp < 128:
            continue
        counts[cp] += 1
        first.setdefault(cp, (line, col))
    out = []
    for cp, n in sorted(counts.items()):
        lno, cno = first[cp]
        out.append({
            "codepoint": f"U+{cp:04X}",
            "char": chr(cp),
            "name": unicodedata.name(chr(cp), "<unnamed>"),
            "category": _classify(cp),
            "family": _family(cp),
            "count": n,
            "first": f"{lno}:{cno}",
        })
    return out


def rule_report(text: str) -> list[dict]:
    """Match counts and sample line numbers for every rule in the ruleset."""
    head, body = C.split_frontmatter(text)
    keep = C.setext_lines(body)
    lines = body.split("\n")
    masked = "\n".join("" if i in keep else ln for i, ln in enumerate(lines))
    offset = head.count("\n")
    # Offsets of each line start, so a match anywhere on a line maps back to its number.
    line_starts: list[int] = []
    pos = 0
    for ln in lines:
        line_starts.append(pos)
        pos += len(ln) + 1

    out = []
    for name, pat in RULE_GROUPS:
        hits = list(pat.finditer(masked))
        if not hits:
            continue
        numbers = [bisect.bisect_right(line_starts, m.start()) + offset for m in hits]
        out.append({
            "rule": name,
            "count": len(hits),
            "sample": "".join(f"{m.group(0)!r}" for m in hits[:3]),
            "lines": numbers[:MAX_EXAMPLES],
        })
    return out


def scan_text(text: str) -> dict:
    chars = char_report(text)
    rules = rule_report(text)
    return {
        "chars": chars,
        "rules": rules,
        "mapped": sum(c["count"] for c in chars if c["category"] == "mapped"),
        "review": sum(c["count"] for c in chars if c["category"] == "review"),
        "decorative": sum(c["count"] for c in chars if c["category"] == "decorative"),
        "unclassified": sum(c["count"] for c in chars if c["category"] == "unclassified"),
        "kinds": sum(c["count"] for c in chars),
        "rule_hits": sum(r["count"] for r in rules),
    }


def scan_paths(
    paths: Iterable[str],
    *,
    extensions: Optional[Iterable[str]] = None,
    exclude_dirs: Optional[Iterable[str]] = None,
    exclude_globs: Iterable[str] = (),
) -> list[dict]:
    """Scan every text file under `paths`; return one report per file with findings."""
    kwargs: dict = {"exclude_globs": exclude_globs}
    if extensions is not None:
        kwargs["extensions"] = extensions
    if exclude_dirs is not None:
        kwargs["exclude_dirs"] = exclude_dirs
    reports = []
    for path, text in iter_text_files(paths, **kwargs):
        report = {"path": str(path)}
        report.update(scan_text(text))
        reports.append(report)
    return reports


def format_report(reports: list[dict]) -> str:
    """Plain-text table. Files with nothing to report collapse to one line."""
    out = []
    flagged = [r for r in reports if r["kinds"] or r["rule_hits"]]
    for r in flagged:
        out.append(f"{r['path']}")
        for c in r["chars"]:
            fam = f" [{c['family']}]" if c["family"] else ""
            out.append(f"    {c['codepoint']} x{c['count']:<4} {c['category']:<13}"
                       f"first {c['first']:<8} {c['name']}{fam}")
        for rule in r["rules"]:
            out.append(f"    rule {rule['rule']:<15} x{rule['count']:<4}lines "
                       f"{','.join(str(n) for n in rule['lines'])}  {rule['sample']}")
        out.append("")
    total_files = len(reports)
    dirty = len(flagged)
    kinds = sum(r["kinds"] for r in reports)
    hits = sum(r["rule_hits"] for r in reports)
    review = sum(r["review"] for r in reports)
    out.append(f"{dirty} of {total_files} files carry AI tells: "
               f"{kinds} non-ASCII characters ({review} need review), {hits} rule hits")
    return "\n".join(out)
