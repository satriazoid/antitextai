"""File discovery and text decoding shared by scan, clean, and verify.

A file is treated as text when it decodes as UTF-8 and holds no NUL byte. That rule
keeps binaries (images, .ibd, xlsx, compiled objects) out of every pass without an
extension list to maintain; non-ASCII inside a real binary is normal and must not be
"cleaned".
"""
from __future__ import annotations

import fnmatch
import pathlib
from typing import Iterable, Iterator, Optional

DEFAULT_EXCLUDE_DIRS = frozenset({
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", "out", "target", "vendor", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".gradle", ".idea", ".vscode-test", ".next", ".nuxt",
    "coverage", "htmlcov", "site-packages",
})

# Extensions worth walking when a directory is given. Files named explicitly on the
# command line are always considered, whatever their extension.
DEFAULT_EXTENSIONS = frozenset({
    ".md", ".markdown", ".mdx", ".txt", ".rst", ".adoc", ".org", ".tex",
    ".py", ".pyi", ".pyw", ".ipynb", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx",
    ".vue", ".svelte", ".astro", ".php", ".rb", ".go", ".rs", ".java", ".kt", ".kts",
    ".cs", ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".swift", ".dart", ".lua", ".pl",
    ".r", ".jl", ".hs", ".ml", ".ex", ".exs", ".erl", ".scala", ".clj", ".sql",
    ".json", ".jsonc", ".json5", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".properties", ".env", ".editorconfig", ".css", ".scss", ".sass", ".less",
    ".html", ".htm", ".xml", ".svg", ".xsl", ".csv", ".tsv", ".gradle", ".cmake",
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1", ".bat", ".cmd", ".tf", ".hcl",
    ".proto", ".graphql", ".gql", ".asm", ".s", ".dockerfile", ".service", ".rules",
})

EXTENSIONLESS_TEXT_NAMES = frozenset({
    "dockerfile", "makefile", "cmakelists.txt", "gemfile", "rakefile", "procfile",
    "justfile", "license", "licence", "notice", "authors", "readme", "changelog",
})


def is_probably_text(data: bytes) -> bool:
    """True when `data` is UTF-8 text. NUL bytes mean binary (UTF-16 included)."""
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def read_text(path: pathlib.Path) -> Optional[str]:
    """Decoded text, or None when the file is binary or not valid UTF-8."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not is_probably_text(data):
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:  # pragma: no cover - is_probably_text already guards
        return None


def write_text(path: pathlib.Path, text: str) -> None:
    """Write UTF-8 with newline translation disabled.

    pathlib's write_text gained the newline keyword only in Python 3.10, and without it Windows
    turns every LF into CRLF, which would rewrite the line endings the cleaner promises to
    preserve. Use this helper instead of pathlib's write_text inside the package.
    """
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def is_wanted(path: pathlib.Path, extensions: Iterable[str] = DEFAULT_EXTENSIONS) -> bool:
    suffix = path.suffix.lower()
    if suffix in set(extensions):
        return True
    return not suffix and path.name.lower() in EXTENSIONLESS_TEXT_NAMES


def iter_files(
    paths: Iterable[str],
    *,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    exclude_globs: Iterable[str] = (),
) -> list[pathlib.Path]:
    """Expand files and directories into a de-duplicated, sorted file list.

    A path named directly is always taken (extension filter skipped); a directory is
    walked recursively and filtered. `exclude_globs` are fnmatch patterns matched
    against both the path and the file name.
    """
    exclude_dirs = set(DEFAULT_EXCLUDE_DIRS if exclude_dirs is None else exclude_dirs)
    globs = tuple(exclude_globs)
    extensions = DEFAULT_EXTENSIONS if extensions is None else extensions
    found: list[pathlib.Path] = []
    seen: set[pathlib.Path] = set()

    def blocked(path: pathlib.Path) -> bool:
        return any(fnmatch.fnmatch(str(path), g) or fnmatch.fnmatch(path.name, g) for g in globs)

    for raw in paths:
        p = pathlib.Path(raw)
        if p.is_file():
            if not blocked(p) and p not in seen:
                seen.add(p)
                found.append(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if not f.is_file() or f in seen or blocked(f):
                    continue
                if any(part in exclude_dirs for part in f.parts):
                    continue
                if not is_wanted(f, extensions):
                    continue
                seen.add(f)
                found.append(f)
    return found


def iter_text_files(paths: Iterable[str], **kwargs) -> Iterator[tuple[pathlib.Path, str]]:
    """Yield (path, text) for every readable text file under `paths`."""
    for f in iter_files(paths, **kwargs):
        text = read_text(f)
        if text is not None:
            yield f, text
