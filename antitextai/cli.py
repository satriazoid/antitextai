"""Command line interface: scan, clean, verify.

    python -m antitextai scan  docs/
    python -m antitextai clean --write docs/
    python -m antitextai verify .

Exit codes: 0 success, 1 findings or a residual, 2 bad usage.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Optional, Sequence

from . import __version__
from . import cleaner as C
from .files import DEFAULT_EXCLUDE_DIRS, DEFAULT_EXTENSIONS, read_text, write_text
from .scan import format_report as format_scan, scan_paths
from .verify import format_report as format_verify, verify_paths

EPILOG = """\
examples:
  antitextai scan .                       inventory AI tells in the repo
  antitextai scan src --json > tells.json machine-readable inventory
  antitextai clean --write README.md      rewrite one file in place
  antitextai clean - < draft.md           read stdin, write stdout
  antitextai verify . --strict            fail if any file is still dirty

scan reports, clean rewrites, verify proves. Run all three in that order.
"""


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("paths", nargs="+", help="files or directories; '-' means stdin")
    parser.add_argument("--ext", action="append", default=None, metavar=".EXT",
                        help=f"extension to include (repeatable, default: {len(DEFAULT_EXTENSIONS)} known text types)")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB",
                        help="fnmatch pattern to skip (repeatable)")
    parser.add_argument("--exclude-dir", action="append", default=None, metavar="NAME",
                        help=f"directory name to skip (repeatable, default: {len(DEFAULT_EXCLUDE_DIRS)} known)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")


def _kwargs(args: argparse.Namespace) -> dict:
    return {
        "extensions": args.ext if args.ext else None,
        "exclude_dirs": args.exclude_dir if args.exclude_dir else None,
        "exclude_globs": args.exclude,
    }


def _cmd_scan(args: argparse.Namespace) -> int:
    reports = scan_paths(args.paths, **_kwargs(args))
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print(format_scan(reports))
    flagged = [r for r in reports if r["kinds"] or r["rule_hits"]]
    if args.strict and flagged:
        return 1
    return 0


def _cmd_clean(args: argparse.Namespace) -> int:
    if args.paths == ["-"]:
        src = sys.stdin.read()
        out = C.clean(src, strip_bom=not args.no_bom)
        sys.stdout.write(out)
        try:
            C.assert_no_artifacts(out)
        except AssertionError as exc:
            print(f"stdin: {exc}", file=sys.stderr)
            return 1
        return 0

    rc = 0
    changed = 0
    cleaned = 0
    for f in _expand(args):
        text = read_text(f)
        if text is None:
            print(f"skip    {f} (binary or not UTF-8)", file=sys.stderr)
            continue
        out = C.clean(text, strip_bom=not args.no_bom)
        cleaned += 1
        if args.write:
            if out != text:
                write_text(f, out)
                changed += 1
                if not args.quiet:
                    print(f"cleaned {f}", file=sys.stderr)
        else:
            # --quiet silences per-file progress on stderr; the cleaned text still goes
            # to stdout, that is the result, not noise.
            sys.stdout.write(out)
        try:
            C.assert_no_artifacts(out)
        except AssertionError as exc:
            print(f"{f}: {exc}", file=sys.stderr)
            rc = 1
    if args.write and not args.quiet:
        print(f"{changed} file(s) rewritten, {cleaned} cleaned", file=sys.stderr)
    return rc


def _cmd_verify(args: argparse.Namespace) -> int:
    reports = verify_paths(args.paths, allow_dashes=args.allow_dashes, **_kwargs(args))
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print(format_verify(reports, show_clean=args.show_clean))
    dirty = [r for r in reports if r["status"] == "dirty"]
    if args.strict and dirty:
        return 1
    return 0


def _expand(args: argparse.Namespace) -> list[pathlib.Path]:
    from .files import iter_files
    return iter_files(args.paths, **_kwargs(args))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="antitextai",
        description="Strip AI text and code tells: invisible Unicode, smart quotes, "
                    "banner separators, end-of-block markers, conversational frames.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--version", action="version", version=f"antitextai {__version__}")
    sub = ap.add_subparsers(dest="command")

    p_scan = sub.add_parser("scan", help="inventory tells, change nothing",
                            description="Report AI tells per file. Nothing is modified.")
    _common(p_scan)
    p_scan.add_argument("--strict", action="store_true", help="exit 1 when anything was found")
    p_scan.set_defaults(func=_cmd_scan)

    p_clean = sub.add_parser("clean", help="apply the deterministic rules",
                             description="Print cleaned text, or rewrite with --write. "
                                         "Em/en dashes are never touched: they need a human.")
    _common(p_clean)
    p_clean.add_argument("--write", action="store_true", help="rewrite files in place")
    p_clean.add_argument("--no-bom", action="store_true", help="keep a leading U+FEFF")
    p_clean.add_argument("--quiet", action="store_true", help="no per-file progress on stderr")
    p_clean.set_defaults(func=_cmd_clean)

    p_verify = sub.add_parser("verify", help="prove a file is clean",
                              description="Run the cleaner's own assertions over files.")
    _common(p_verify)
    p_verify.add_argument("--strict", action="store_true", help="exit 1 when a file is still dirty")
    p_verify.add_argument("--allow-dashes", action="store_true",
                          help="treat an unreviewed em/en dash as acceptable")
    p_verify.add_argument("--show-clean", action="store_true", help="list clean files too")
    p_verify.set_defaults(func=_cmd_verify)
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if not getattr(args, "command", None):
        ap.print_help()
        return 0
    if args.paths == ["-"] and args.command != "clean":
        args.paths = []  # stdin only makes sense for clean; avoid a '-' path lookup
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
