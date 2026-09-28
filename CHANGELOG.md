# Changelog

All notable changes to this project. Format follows [Keep a Changelog](https://keepachangelog.com/),
versioning follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-28

First public release.

### Added

- `antitextai` package with `clean()`, `assert_no_artifacts()`, `scan_text()`, `verify_paths()`
  and friends. Standard library only, no dependencies.
- CLI with three subcommands: `scan` (inventory), `clean` (transform), `verify` (prove), with
  `--write`, `--strict`, `--json`, `--ext`, `--exclude`, `--exclude-dir`, `--allow-dashes`,
  `--no-bom`, `--quiet`.
- Scanner that classifies every non-ASCII codepoint as `mapped`, `review`, `decorative`,
  `keep`, or `unclassified`, with counts, first line:column, and per-rule line numbers.
- `SKILL.md`, an Agent Skills compatible ruleset covering the full character table, the line
  rules, the frame rules, the workflow, and the judgment calls the tool refuses to make.
- Integration files and installers for Claude Code, opencode, Codex and other `AGENTS.md`
  readers, GitHub Copilot, Cursor, Windsurf, Cline, Aider, Gemini CLI, Hermes Agent, and omp.
- `scripts/install.sh` and `scripts/install.ps1`, including non-destructive block merging into
  shared instruction files.
- `.pre-commit-hooks.yaml` with a rewriting hook and a verify-only hook.
- 59 unittest cases runnable with `unittest` or `pytest`, covering frame stripping, content
  preservation, code safety, line endings, frontmatter bytes, setext headings, idempotence,
  scanner classification, and every CLI exit code.
- CI on Linux, macOS, and Windows across Python 3.9 to 3.13, including a self-scan of the
  repository.

### Notes

- Em dash `U+2014` and en dash `U+2013` are reported, never replaced. A numeric range, a
  compound noun, and a clause break each require a different replacement.
- Conservative by construction: binary files, non-UTF-8 files, string literals that look like
  comments, YAML frontmatter, and setext headings are all protected by tests.
