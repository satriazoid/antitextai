"""AI-style prose detection: hedging, fluff openers, sign-offs, bold-keyword lists.

These are not invisible characters. They are linguistic tells that LLMs
produce at high frequency, and humans rarely repeat them in the same density.
Finding them in bulk is a strong signal of machine authorship.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

HEDGING = re.compile(
    r"\b(?:generally|typically|often|usually|somewhat|fairly|rather|pretty|quite"
    r"|more or less|in general|on the whole)\b",
    re.IGNORECASE,
)

TRANSITIONS = re.compile(
    r"\b(?:furthermore|additionally|moreover|consequently|nevertheless|hence"
    r"|thus|accordingly|meanwhile|subsequently|alternatively|specifically"
    r"|notably|essentially|ultimately|therefore|similarly|however|although)\b",
    re.IGNORECASE,
)

AI_OPENER = re.compile(
    r"(?im)^[ \t]*(?:certainly|sure thing|sure|of course|absolutely|great question"
    r"|excellent question|no problem|got it|happy to help|glad to help)[,.!]?[ \t]*$",
)

AI_SIGNOFF = re.compile(
    r"(?im)^[ \t]*(?:hope (?:this|that) helps|let me know if|feel free to ask"
    r"|don't hesitate to reach out|feedback welcome|let me know if you need anything else"
    r"|reach out if you have questions|happy to help with anything else)[,.!]?[ \t]*$",
)

# Key insight: "it's important to note that" may NOT be followed by punctuation
# (e.g., "It's important to note that TTLs prevent stale data.")
MID_GESTURE = re.compile(
    r"(?i)(?:it'?s (?:important|worth|crucial|essential) to (?:note|mention) that"
    r"|please note that|note that|needless to say|that said|it goes without saying"
    r"|as an aside|in fact|indeed)[ \t]+[A-Za-z]",
)

BOLD_KEYWORD_LIST = re.compile(
    r"(?m)^[ \t]*[-*+] [ \t]*\*\*[^*]*:\*\*\s+",
)

EMOJI_HEADING = re.compile(r"(?m)^#{1,6}[ \t]+[🀄-🃏\U0001F000-\U0001FFFF\u2600-\u27BF\u2700-\u27BF]\s+")

FILLER_SECTION = re.compile(
    r"(?im)^(?:##\s+)?(?:overview|introduction|conclusion|summary|closing|final thoughts"
    r"\|next steps|key takeaways|bottom line|the end|wrap-up)\s*$",
    re.IGNORECASE,
)


@dataclass
class StyleFinding:
    path: str
    line: int
    rule: str
    text: str
    suggestion: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "rule": self.rule,
            "text": self.text.strip(),
            "suggestion": self.suggestion,
        }


def scan_text(path: str, text: str) -> list[StyleFinding]:
    findings: list[StyleFinding] = []
    lines = text.split("\n")

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        m = HEDGING.search(stripped)
        if m:
            findings.append(StyleFinding(
                path=path, line=i, rule="HEDGING",
                text=m.group(0), suggestion="remove hedge or replace with direct statement"
            ))

        m = TRANSITIONS.search(stripped)
        if m:
            findings.append(StyleFinding(
                path=path, line=i, rule="TRANSITION",
                text=m.group(0), suggestion="consider removing or replacing with simpler link"
            ))

        if AI_OPENER.match(stripped):
            findings.append(StyleFinding(
                path=path, line=i, rule="AI_OPENER",
                text=stripped, suggestion="delete entire line; AI filler"
            ))

        if AI_SIGNOFF.match(stripped):
            findings.append(StyleFinding(
                path=path, line=i, rule="AI_SIGNOFF",
                text=stripped, suggestion="delete entire line; AI filler"
            ))

        # Strategy: repeatedly find gesture + trailing sentence, record each,
        # advance past it. This avoids the finditer offset problem.
        remaining = stripped
        while True:
            m = MID_GESTURE.search(remaining)
            if not m:
                break
            matched_text = m.group(0)
            gesture_phrase = re.search(
                r"(?i)(?:it'?s (?:important|worth|crucial|essential) to (?:note|mention) that"
                r"\|please note that|note that|needless to say|that said|it goes without saying"
                r"\|as an aside|in fact|indeed)",
                matched_text,
            )
            if gesture_phrase:
                findings.append(StyleFinding(
                    path=path, line=i, rule="MID_GESTURE",
                    text=matched_text.rstrip(), suggestion="delete the gesture clause"
                ))
            remaining = remaining[m.end():]

        if BOLD_KEYWORD_LIST.search(line):
            findings.append(StyleFinding(
                path=path, line=i, rule="BOLD_KEYWORD_LIST",
                text=stripped[:80], suggestion="drop the bold keyword prefix, write as plain prose"
            ))

        if EMOJI_HEADING.search(line):
            findings.append(StyleFinding(
                path=path, line=i, rule="EMOJI_HEADING",
                text=stripped[:80], suggestion="remove emoji from heading"
            ))

        if FILLER_SECTION.search(line):
            findings.append(StyleFinding(
                path=path, line=i, rule="FILLER_SECTION",
                text=stripped[:80], suggestion="delete empty filler section"
            ))

    return findings


def scan_paths(
    paths: Iterable[str],
    *,
    extensions: Optional[Iterable[str]] = None,
    exclude_dirs: Optional[Iterable[str]] = None,
    exclude_globs: Iterable[str] = (),
) -> list[dict]:
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
                "rules_hit": sorted({f.rule for f in findings}),
            }
            reports.append(report)
    return reports


def format_report(reports: list[dict]) -> str:
    out = []
    for r in reports:
        out.append(f"{r['path']}")
        for f in r["findings"]:
            out.append(
                f"    line {f['line']} [{f['rule']}]  {f['text']!r}"
                + (f"  → {f['suggestion']}" if f.get("suggestion") else "")
            )
        out.append("")
    total = sum(r["count"] for r in reports)
    out.append(f"{len(reports)} file(s) with AI-style tells, {total} finding(s)")
    return "\n".join(out)
