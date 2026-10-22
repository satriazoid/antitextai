"""Word documents (.docx): scan the text inside.

A .docx is a zip of XML, so the file walkers classify it as binary and skip
it, while AI-written prose lives happily inside it. The text sits in
word/document.xml in <w:t> runs, and pulling it out takes only zipfile and
a regex, which keeps the package stdlib-only.

Report-only. Rewriting a .docx from here would put this code in charge of
the document formatting, so the workflow for Word files is: scan here,
export or copy the text out, clean it as plain text, paste it back.
"""
from __future__ import annotations

import html
import io
import re
import zipfile
from typing import Iterable, Optional

from . import styles as S
from .scan import scan_text as scan_core

RUN = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.S)
PARAGRAPH_END = "</w:p>"
JUSTIFY = re.compile(r'<w:jc\s+w:val="(distribute|both)"')
# Character spacing lives in run properties as a lone w:val; paragraph spacing
# uses w:before / w:after / w:line instead, so the lone-val shape is unambiguous.
CHAR_SPACING = re.compile(r'<w:spacing\s+w:val="(-?\d+)"\s*/>')
SPACE_CPS = frozenset({0x00A0, 0x1680, 0x202F, 0x205F, 0x3000}
                      | set(range(0x2000, 0x200B)))


def document_xml(data: bytes) -> Optional[str]:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as docx:
            return docx.read("word/document.xml").decode("utf-8", "replace")
    except (zipfile.BadZipFile, KeyError, OSError):
        return None


def extract_text(data: bytes) -> Optional[str]:
    xml = document_xml(data)
    if xml is None:
        return None
    paragraphs = []
    for chunk in xml.split(PARAGRAPH_END):
        text = html.unescape("".join(RUN.findall(chunk))).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def scan_data(path: str, data: bytes) -> Optional[dict]:
    xml = document_xml(data)
    if xml is None:
        return None
    text = extract_text(data)
    if text is None:
        return None
    core = scan_core(text)
    findings = []
    for c in core["chars"]:
        if c["category"] in ("mapped", "review"):
            findings.append({
                "line": int(c["first"].split(":")[0]), "rule": c["codepoint"],
                "text": f"{c['name']} x{c['count']}", "suggestion": c["category"],
            })
    for r in core["rules"]:
        findings.append({
            "line": r["lines"][0] if r["lines"] else 1, "rule": r["rule"],
            "text": r["sample"][:60], "suggestion": "frame or line rule hit",
        })
    wide = [c for c in core["chars"]
            if int(c["codepoint"][2:], 16) in SPACE_CPS]
    if wide:
        total = sum(c["count"] for c in wide)
        findings.append({
            "line": int(wide[0]["first"].split(":")[0]), "rule": "WIDE_SPACES",
            "text": f"{total} wide or non-breaking spaces "
                    f"(first: {wide[0]['name']})",
            "suggestion": "normalize to plain spaces before editing in Word; "
                          "justified text stretches them into wide gaps",
        })
        jc = JUSTIFY.findall(xml)
        if jc:
            findings.append({
                "line": 1, "rule": "WORD_JUSTIFY",
                "text": f"{len(jc)} paragraph(s) fully justified ({jc[0]})",
                "suggestion": "full justification stretches the wide spaces; "
                              "normalize the spaces or set alignment to left",
            })
    stretched = [v for v in CHAR_SPACING.findall(xml) if int(v) != 0]
    if stretched:
        findings.append({
            "line": 1, "rule": "WORD_CHAR_SPACING",
            "text": f"{len(stretched)} run(s) with character spacing, "
                    f"first {stretched[0]} (1/20 pt)",
            "suggestion": "expanded character spacing makes text look "
                          "stretched; set character spacing back to 0",
        })
    for f in S.scan_text(path, text):
        findings.append({
            "line": f.line, "rule": f.rule, "text": f.text[:60],
            "suggestion": f.suggestion,
        })
    findings.sort(key=lambda f: (f["line"], f["rule"]))
    return {
        "path": path,
        "paragraphs": text.count("\n") + 1 if text else 0,
        "findings": findings,
        "count": len(findings),
    }


def scan_paths(
    paths: Iterable[str],
    *,
    extensions: Optional[Iterable[str]] = None,
    exclude_dirs: Optional[Iterable[str]] = None,
    exclude_globs: Iterable[str] = (),
) -> list:
    from .files import iter_files

    kwargs: dict = {"exclude_globs": exclude_globs,
                    "extensions": frozenset({".docx"})}
    if exclude_dirs is not None:
        kwargs["exclude_dirs"] = exclude_dirs
    reports = []
    for f in iter_files(paths, **kwargs):
        if f.suffix.lower() != ".docx":
            continue
        try:
            data = f.read_bytes()
        except OSError:
            continue
        report = scan_data(str(f), data)
        if report is None:
            reports.append({"path": str(f), "paragraphs": 0,
                            "findings": [], "count": 0, "status": "skipped"})
        elif report["count"]:
            reports.append(report)
    return reports


def format_report(reports: list) -> str:
    out = []
    shown = 0
    for r in reports:
        if r.get("status") == "skipped":
            out.append(f"{r['path']}  (skipped: not a readable .docx)")
            continue
        shown += 1
        out.append(f"{r['path']}  ({r['paragraphs']} paragraphs)")
        for f in r["findings"]:
            out.append(
                f"    paragraph {f['line']} [{f['rule']}]  {f['text']!r}"
                + (f"  -> {f['suggestion']}" if f.get("suggestion") else "")
            )
        out.append("")
    total = sum(r["count"] for r in reports)
    out.append(f"{shown} .docx file(s) with AI tells, {total} finding(s)")
    return "\n".join(out)
