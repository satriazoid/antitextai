"""Proof pass: assert that a file now carries no AI tells.

`assert_no_artifacts()` from clean.py is the single source of truth here, so the
verifier and the cleaner can never disagree about what "clean" means. Run this on the
output, never on the input.
"""
from __future__ import annotations

import pathlib
from typing import Iterable, Optional

from . import cleaner as C
from .files import iter_files, read_text


def verify_text(text: str) -> Optional[str]:
    """None when clean, else the reason the text still counts as dirty."""
    try:
        C.assert_no_artifacts(text)
    except AssertionError as exc:
        return str(exc)
    if "\u2013" in text or "\u2014" in text:
        return "dash review pending: U+2013/U+2014 present and deliberately not auto-fixed"
    return None


def verify_paths(
    paths: Iterable[str],
    *,
    extensions: Optional[Iterable[str]] = None,
    exclude_dirs: Optional[Iterable[str]] = None,
    exclude_globs: Iterable[str] = (),
    allow_dashes: bool = False,
) -> list[dict]:
    """Verify each text file under `paths`. `allow_dashes` silences the em/en dash note."""
    kwargs: dict = {"exclude_globs": exclude_globs}
    if extensions is not None:
        kwargs["extensions"] = extensions
    if exclude_dirs is not None:
        kwargs["exclude_dirs"] = exclude_dirs
    reports = []
    for f in iter_files(paths, **kwargs):
        text = read_text(f)
        if text is None:
            reports.append({"path": str(f), "status": "skipped",
                            "detail": "binary or not UTF-8"})
            continue
        reason = verify_text(text)
        if reason and allow_dashes and reason.startswith("dash review"):
            reason = None
        has_bom = f.read_bytes()[:3] == b"\xef\xbb\xbf"
        reports.append({
            "path": str(f),
            "status": "dirty" if reason else "clean",
            "detail": reason or (f"leading BOM present" if has_bom else ""),
        })
    return reports


def format_report(reports: list[dict], *, show_clean: bool = False) -> str:
    dirty = [r for r in reports if r["status"] == "dirty"]
    skipped = [r for r in reports if r["status"] == "skipped"]
    lines = []
    for r in reports:
        if r["status"] == "clean" and not show_clean:
            continue
        detail = f": {r['detail']}" if r["detail"] else ""
        lines.append(f"{r['status']:<8} {r['path']}{detail}")
    checked = len(reports) - len(skipped)
    lines.append(f"{checked} text files checked, {len(dirty)} still dirty, "
                 f"{len(skipped)} skipped (binary)")
    return "\n".join(lines)
