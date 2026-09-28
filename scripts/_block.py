#!/usr/bin/env python3
"""Insert or refresh a marked block inside a shared instruction file.

Used by scripts/install.sh and scripts/install.ps1 so that both behave the same way
when a tool already owns the file it reads (AGENTS.md, GEMINI.md,
.github/copilot-instructions.md). The block is delimited by HTML comments, so it is
invisible in rendered Markdown and safe to replace on a later run.

    python _block.py --file AGENTS.md --source instruction.md --marker antitextai

Behaviour:
  file missing            -> created with the block
  file has the markers    -> replaced in place, everything else untouched
  file has no markers     -> block appended, existing content untouched
Exit codes: 0 written or updated, 1 nothing to do (already current), 2 usage error.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

BEGIN = "<!-- {marker}:begin -->"
END = "<!-- {marker}:end -->"
NOTE = ("<!-- managed by antitextai (https://github.com/satriazoid/antitextai); "
        "edit between the markers and it will be replaced on the next install -->")


def block_for(marker: str, body: str) -> str:
    body = body.strip("\n")
    return "\n".join([BEGIN.format(marker=marker), NOTE, "", body, END.format(marker=marker)])


def merge(existing: str, marker: str, body: str) -> str:
    block = block_for(marker, body)
    begin = BEGIN.format(marker=marker)
    end = END.format(marker=marker)
    if begin in existing and end in existing:
        head, _, rest = existing.partition(begin)
        _, _, tail = rest.partition(end)
        return head.rstrip("\n") + "\n\n" + block + tail
    if not existing.strip():
        return block + "\n"
    return existing.rstrip("\n") + "\n\n" + block + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Insert or refresh a marked block inside a shared instruction file.")
    ap.add_argument("--file", required=True, help="instruction file to create or update")
    ap.add_argument("--source", required=True, help="markdown file holding the block body")
    ap.add_argument("--marker", default="antitextai", help="marker name (default: antitextai)")
    ap.add_argument("--dry-run", action="store_true", help="print the result, write nothing")
    args = ap.parse_args(argv)

    path = pathlib.Path(args.file)
    src = pathlib.Path(args.source)
    if not src.is_file():
        print(f"source not found: {src}", file=sys.stderr)
        return 2
    body = src.read_text(encoding="utf-8")
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    merged = merge(existing, args.marker, body)

    if args.dry_run:
        sys.stdout.write(merged)
        return 0
    if existing and merged == existing:
        print(f"up to date {path}")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    # open() rather than pathlib's write_text with a newline keyword: that keyword needs Python
    # 3.10, and without it Windows would rewrite the line endings of the file being merged into.
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(merged)
    print(f"{'updated' if existing else 'created'} {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
