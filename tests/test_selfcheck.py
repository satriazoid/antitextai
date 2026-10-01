"""The repository must pass its own check, on the files where a tell would be an accident.

`SKILL.md`, the READMEs, `docs/ai-signatures-manual.md`, `antitextai/cleaner.py` and `tests/`
quote the patterns the tool looks for, as data: that is what a spec, a manual, a fixture, and a
regression suite are. The same concession a linter makes for its own test suite. Everything
listed here must stay clean, so a stray zero-width space in the package or in the project docs
fails the suite instead of shipping.
"""
import pathlib
import re
import unittest

from antitextai.verify import verify_paths

ROOT = pathlib.Path(__file__).resolve().parent.parent

CLEAN_FILES = [
    "antitextai/__init__.py",
    "antitextai/__main__.py",
    "antitextai/files.py",
    "antitextai/scan.py",
    "antitextai/verify.py",
    "antitextai/cli.py",
    "antitextai/fonts.py",
    "antitextai/styles.py",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "integrations/README.md",
    "integrations/cursor/antitextai.mdc",
    "integrations/copilot/copilot-instructions.md",
    "integrations/aider/CONVENTIONS.md",
    "integrations/windsurf/antitextai.md",
    "integrations/cline/antitextai.md",
    "integrations/codex/antitextai.md",
    "integrations/gemini/antitextai.md",
    "integrations/roo-code/antitextai.md",
    "integrations/goose/antitextai.md",
    "integrations/warp/WARP.md",
    "integrations/claude-code/README.md",
    "integrations/opencode/README.md",
    "integrations/agents/README.md",
    "integrations/hermes/README.md",
    "integrations/omp/README.md",
    "integrations/qwen-code/README.md",
    "integrations/crush/README.md",
    "integrations/kilo-code/README.md",
    ".github/workflows/ci.yml",
    ".pre-commit-hooks.yaml",
    "pyproject.toml",
]


class SelfCheckTest(unittest.TestCase):
    def test_every_listed_file_exists(self):
        missing = [f for f in CLEAN_FILES if not (ROOT / f).is_file()]
        self.assertEqual(missing, [], "the self-check list references files that are gone")

    def test_listed_files_are_clean(self):
        reports = verify_paths([str(ROOT / f) for f in CLEAN_FILES], allow_dashes=True)
        dirty = [f"{r['path']}: {r['detail']}" for r in reports if r["status"] == "dirty"]
        self.assertEqual(dirty, [], "AI tells leaked into files that must stay clean")

    def test_package_never_uses_the_3_10_only_write_text_kwarg(self):
        # Path.write_text(newline=...) arrived in Python 3.10; on 3.9 it is a TypeError, which
        # is exactly how the first CI run failed on three operating systems at once.
        pattern = re.compile(r"write_text\([^)]*newline=")
        offenders = [p.name for p in sorted((ROOT / "antitextai").glob("*.py"))
                     if pattern.search(p.read_text(encoding="utf-8"))]
        offenders += [p.name for p in sorted((ROOT / "scripts").glob("*.py"))
                      if pattern.search(p.read_text(encoding="utf-8"))]
        self.assertEqual(offenders, [], "3.10-only Path.write_text kwarg leaked back in")

    def test_package_sources_have_no_non_ascii_beyond_documented_symbols(self):
        # The scanner classifies; this asserts nothing sneaked in unclassified.
        from antitextai.scan import scan_text
        for name in ("files.py", "scan.py", "verify.py", "cli.py"):
            text = (ROOT / "antitextai" / name).read_text(encoding="utf-8")
            report = scan_text(text)
            self.assertEqual(report["unclassified"], 0, f"{name} has unclassified non-ASCII")
            self.assertEqual(report["kinds"], 0, f"{name} should be pure ASCII")


if __name__ == "__main__":
    unittest.main(verbosity=2)
