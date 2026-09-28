# antitextai

Strip the machine tells out of LLM-written text and code: invisible Unicode, smart quotes,
banner separators, end-of-block markers, conversational frames, NBSP indentation.

One small Python package. No dependencies, no network, no API key.

[![CI](https://github.com/satriazoid/antitextai/actions/workflows/ci.yml/badge.svg)](https://github.com/satriazoid/antitextai/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

It ships two things that stay in sync:

| Piece | What it is |
| --- | --- |
| `antitextai/` | An installable Python package and CLI that applies the deterministic half of the rules |
| `SKILL.md` | An [Agent Skills](https://agentskills.io) compatible skill so Claude Code, opencode, Cursor, Copilot, Codex, Windsurf, Cline, Aider, Hermes, omp and friends know how to use it, including the judgment calls a regex cannot make |

## Why this exists

Model output carries fingerprints. They survive into commits, docs, and pull requests:

- Zero-width spaces and byte-0 BOMs pasted from a chat UI.
- `“smart quotes”` and `…` in source files, which break string literals and shell scripts.
- `# ======================================` banners and `# end of function add` markers.
- `Certainly! Here is the complete breakdown:` before anything useful starts.
- Non-breaking spaces inside indentation, which raise `IndentationError` in Python.

Those are mechanical. A program should handle them the same way every time, and it should
be able to prove the file is clean afterwards. That is this repository.

The judgment half stays with you: whether a docstring carries a contract, whether a dash
joins a numeric range or a clause, whether a banner marks a real module boundary. The tool
flags those and refuses to guess.

## What it removes, and what it refuses to touch

| Removed or normalized | Becomes |
| --- | --- |
| `U+200B/200C/200D/2060/FEFF/00AD/200E/200F` (zero width, BOM mid-file, soft hyphen, bidi marks) | deleted |
| `U+00A0`, `U+202F` (non-breaking and narrow spaces) | plain space |
| `U+201C/201D/2018/2019`, `U+2032/2033` (smart quotes, primes) | `"` and `'` |
| `U+2026` (ellipsis token) | `...` |
| `U+00D7`, `U+2212` in prose and comments | `x`, `-` |
| `U+2022` bullets | `-` (`- ` at line start) |
| `# ====...` / `// ----...` banner and separator lines | deleted |
| `# end of loop`, `// end function f`, including a trailing `  # end function f` | deleted, code kept |
| `# Step 1: ...`, `# now, we ...`, `# Return the result` narration | deleted |
| `Certainly!`, `Sure thing!`, `No problem!` line openers | frame dropped, sentence kept and recapitalized |
| `In today's ... , ...`, `Overall, ...`, `That said, ...` openers | frame dropped, clause kept |
| `It's important to note that ...`, `Note that ...` (line start or mid-paragraph) | frame dropped, clause kept |
| `Here is the complete Python script to achieve this:` before a fence | deleted |
| `Hope this helps!`, `Let me know if ...` as a sign-off, line or inline | deleted, the sentence before it kept |
| Trailing whitespace, runs of 3+ blank lines | collapsed |

Deliberately kept:

| Kept | Why |
| --- | --- |
| Em dash `U+2014`, en dash `U+2013` | A dash can join a numeric range (`2019–2021`), a compound noun (`Jean–Luc`), a quotation, or a clause. Each case has a different correct replacement, so **every occurrence is reported for review and never auto-replaced.** |
| Math symbols: `Σ Π λ ± × ≥` and other Greek used in formulas | They are content, not decoration. |
| Accented Latin, Cyrillic, Hebrew, Arabic, CJK | Real writing. The scanner classifies them as `keep`. |
| YAML frontmatter | Split off before the line rules, so `---` delimiters and frontmatter bytes survive unchanged. |
| Setext headings (`Heading` over `------`) | A run of dashes under a text line is a heading, not a banner. Detected and held out of the separator rule. |
| Comment-looking string literals | `x = "# end of loop"` and `url = 'http://x--y/z'` are covered by tests and survive byte-identical. |
| Line endings | CRLF in, CRLF out. LF in, LF out. |

## Install

Three ways, from lightest to most permanent.

```bash
# 1. Clone and run. Nothing to install: the package sits at the repo root,
#    so `python -m antitextai` works straight after cloning.
git clone https://github.com/satriazoid/antitextai.git
cd antitextai
python -m antitextai scan .

# 2. Install the CLI into an isolated environment (recommended for daily use).
pipx install "git+https://github.com/satriazoid/antitextai"
# or, with uv:
uv tool install "git+https://github.com/satriazoid/antitextai"

# 3. Editable install, if you want the library on your path while hacking on it.
python -m venv .venv
.venv/Scripts/python -m pip install -e .        # Windows
# .venv/bin/python -m pip install -e .          # Linux and macOS
```

Requires Python 3.8 or newer. The package has no runtime dependencies.

## Quickstart

```bash
python -m antitextai scan .                    # 1. inventory, changes nothing
python -m antitextai clean --write README.md   # 2. rewrite in place
python -m antitextai verify . --strict         # 3. prove it is clean, exit 1 if not
```

`scan` reports, `clean` rewrites, `verify` proves. Run them in that order.

### Real output

`examples/demo_before.md` is a fixture with genuine tells in it. Scanning it:

```text
$ python -m antitextai scan examples/demo_before.md
examples\demo_before.md
    U+00A0 x2    mapped       first 16:8     NO-BREAK SPACE
    U+200B x1    mapped       first 31:7     ZERO WIDTH SPACE
    U+2013 x1    review       first 30:32    EN DASH
    U+2014 x2    review       first 30:8     EM DASH
    U+201C x3    mapped       first 18:12    LEFT DOUBLE QUOTATION MARK
    U+201D x3    mapped       first 18:15    RIGHT DOUBLE QUOTATION MARK
    U+2022 x2    mapped       first 31:14    BULLET
    U+2026 x1    mapped       first 31:27    HORIZONTAL ELLIPSIS
    rule INVISIBLE       x1   lines 31  '\u200b'
    rule NBSP            x2   lines 16,16  '\xa0''\xa0'
    rule SALUTATION      x1   lines 33  "Let me know if you'd like more detail.\n"
    rule INTERJECT       x1   lines 6  'Certainly! H'
    rule CLAUSE          x1   lines 8  "In today's fast-paced digital landscape, t"
    rule SUBORDINATE     x1   lines 10  "It's important to note that r"
    rule GESTURE_INLINE  x1   lines 10  '. That said, w'
    rule PRECODE         x1   lines 12  'Here is the complete Python script to achieve this:\n'
    rule END_WHOLE       x1   lines 27  '# end of function add\n'
    rule END_TRAIL       x1   lines 23  '  # end function add'
    rule NARRATION       x1   lines 24  '-- now, we print the result\n'
    rule STEPNARR        x1   lines 17  '-- Step 1: build the payload\n'
    rule SEPARATOR       x2   lines 19,21  '# ==========================================\n''# ==========================================\n'

1 of 1 files carry AI tells: 15 non-ASCII characters (3 need review), 15 rule hits
```

Cleaning the same file. Before, with the invisible characters shown as codepoints so they
stay visible in a diff of this README:

~~~text
---
title: Migration notes
tags: [api, rollout]
---

Certainly! Here is the complete breakdown of the migration plan:

In today's fast-paced digital landscape, teams ship faster when the pipeline is boring.

It's important to note that retries are capped at three. That said, we keep the flag on.

Here is the complete Python script to achieve this:

```python
-- Increment the retry counter
retries\u00a0+=\u00a01
-- Step 1: build the payload
payload = {\u201cid\u201d: 7, \u201cname\u201d: \u201cdemo\u201d}
# ==========================================
# HELPERS
# ==========================================
def add(a, b):
    return a + b  # end function add
-- now, we print the result
print(add(1, 2))

# end of function add
```

The API\u2014which is v2\u2014serves 2019\u20132021 clients.
Notes:\u200b alpha\u2022 beta\u2022 gamma\u2026

Let me know if you'd like more detail.
~~~

After (`examples/demo_after.md`, byte for byte):

~~~text
---
title: Migration notes
tags: [api, rollout]
---
Teams ship faster when the pipeline is boring.

Retries are capped at three. We keep the flag on.

```python
-- Increment the retry counter
retries += 1
payload = {"id": 7, "name": "demo"}
# HELPERS
def add(a, b):
    return a + b
print(add(1, 2))

```

The API—which is v2—serves 2019–2021 clients.
Notes: alpha- beta- gamma...
~~~

Three things to notice. The frames are gone but the sentences they wrapped are kept and
recapitalized. The em dash and en dash survive on purpose, because they sit in the `review`
bucket rather than the `mapped` one. The frontmatter is byte-identical. `tests/test_examples.py`
fails if the cleaner and this documented example ever drift apart.

## Use it from an agent

Any agent that can run a shell command can use the CLI. Agents that read `SKILL.md` or
`AGENTS.md` pick the rules up automatically, straight from the clone.

```bash
# Skill-aware agents: copy SKILL.md into the place your tool looks.
cp -r SKILL.md antitextai/ ~/.claude/skills/antitextai/     # Claude Code (global)
mkdir -p .opencode/skills/antitextai && cp -r SKILL.md .opencode/skills/antitextai/   # opencode (project)

# Or run the installer, which knows the paths for ten tools:
bash scripts/install.sh --target claude-code,cursor,copilot,codex,gemini,opencode,hermes
pwsh scripts/install.ps1 -Target claude-code,cursor,copilot,codex,gemini,opencode,hermes
```

| Tool | Where the skill or rules go |
| --- | --- |
| Claude Code | `.claude/skills/antitextai/SKILL.md` (project) or `~/.claude/skills/antitextai/SKILL.md` (global) |
| opencode | `.opencode/skills/antitextai/SKILL.md`, also reads `.claude/skills/` and `.agents/skills/` |
| Codex CLI and other AGENTS.md readers | `AGENTS.md` in the repo root, `~/.codex/AGENTS.md` for global |
| GitHub Copilot | `.github/copilot-instructions.md`, path-scoped `.github/instructions/*.instructions.md` |
| Cursor | `.cursor/rules/antitextai.mdc`, or `AGENTS.md` |
| Windsurf | `.windsurf/rules/antitextai.md` |
| Cline | `.clinerules/antitextai.md` |
| Aider | `CONVENTIONS.md` (referenced from `.aider.conf.yml`) |
| Gemini CLI | `GEMINI.md` in the project root, or `~/.gemini/GEMINI.md` |
| Hermes Agent | `~/.hermes/skills/antitextai/SKILL.md`, on Windows `%LOCALAPPDATA%\hermes\skills\` |
| omp (oh-my-pi) | `.omp/skills/antitextai/SKILL.md` in the project |

Copy-paste-ready files for each of those live in [`integrations/`](integrations), and
[`docs/agent-integration.md`](docs/agent-integration.md) explains the install and the
prompts that make an agent use the tool the same way twice.

## Use it as a library

```python
from antitextai import clean, assert_no_artifacts, scan_text, verify_paths

text = open("draft.md", encoding="utf-8").read()

print(scan_text(text)["review"])        # em/en dashes that need a human, before touching anything
cleaned = clean(text)                   # deterministic passes only
assert_no_artifacts(cleaned)            # raises AssertionError with the residual, or returns None
open("draft.md", "w", encoding="utf-8", newline="").write(cleaned)
```

| Function | Purpose |
| --- | --- |
| `clean(text, strip_bom=True)` | Run every deterministic pass. Returns new text; no I/O. |
| `assert_no_artifacts(text)` | Raise unless the text is free of tells. Same rules the cleaner uses, so they cannot disagree. |
| `scan_text(text)` | Inventory: per-codepoint counts, first location, classification, rule hits. |
| `scan_paths(paths)` | The same, over files, with binary and non-UTF-8 files skipped. |
| `verify_text(text)` / `verify_paths(paths)` | The proof pass, plus a note when em/en dashes still need review. |
| `split_frontmatter(text)` / `setext_lines(text)` | The two structural escapes the ruleset needs; useful if you write your own pass. |

## CLI reference

```text
antitextai scan   PATHS... [--strict] [--json] [--ext .md] [--exclude GLOB] [--exclude-dir NAME]
antitextai clean  PATHS... [--write] [--no-bom] [--quiet] [--json] [--ext .md] [--exclude GLOB]
antitextai verify PATHS... [--strict] [--allow-dashes] [--show-clean] [--json]
```

- `PATHS` accepts files or directories; `-` reads stdin and writes stdout (`clean` only).
- Directories are walked recursively, filtered to known text extensions, and skip
  `.git`, `node_modules`, `__pycache__`, `.venv`, `dist`, `build`, `target` and friends.
  A file named explicitly on the command line is always taken, whatever its extension.
- Binary files (any NUL byte) and files that are not valid UTF-8 are skipped, not mangled.
- `clean` without `--write` prints the result and leaves the file alone, so it is safe by default.
- `--quiet` silences per-file progress on stderr; the cleaned text still goes to stdout.
- Exit codes: `0` success, `1` findings or a residual, `2` usage error. `--strict` turns a
  report into a failure, which is what a CI step wants.

CI example:

```yaml
- name: No AI tells
  run: |
    python -m antitextai verify . --strict \
      --exclude "examples/**" --exclude "docs/**" --exclude "tests/**" \
      --exclude "SKILL.md" --exclude "README*.md"
```

Exclude the files that quote tells as data (a spec, a manual, a before/after example, test
fixtures) and let the rest fail the build.

## Design decisions worth knowing

1. **Em and en dashes are never replaced automatically.** The replacement depends on meaning.
   Flip that switch at your own risk; the tests assert the current behavior.
2. **Frames are stripped, not deleted.** `In today's market, revenue grew 12%.` becomes
   `Revenue grew 12%.` Deleting the line was the worst bug in this codebase's history: it
   emptied files whose only fault was an opener.
3. **Frames end where the grammar says they end.** Interjections (`Certainly!`) and adverbial
   openers (`In today's ...`) end at punctuation. Complementizers (`note that`) have no comma,
   so the rule stops at `that` and keeps the clause it introduces.
4. **Multi-word openers are atomic.** `Sure thing!` is one alternative, because matching a bare
   `sure` first produced the orphan `Thing! Below is a walkthrough.`.
5. **The separator rule must not eat headings.** Setext underlines are detected and masked, and
   the verifier applies the same mask, or it would report a legitimately kept heading as dirty.
6. **Comment prefixes are anchored.** A `#` is a comment only at line start or after whitespace,
   which is what keeps `x = "# end of loop"` and `url = 'http://x--y/z'` intact. Regex cannot
   parse strings, so inspect any file that embeds comment-looking literals.
7. **Order is the contract:** characters, then frames, then whole-line deletions, then whitespace.
   Normalize NBSP after the line rules and every `^`-anchored pattern mis-anchors.
8. **Line endings and frontmatter are preserved byte for byte.** Frontmatter never sees a line
   rule. A `--no-bom` run detaches the byte-0 BOM for the passes and re-attaches it at the end,
   so a deliberate BOM does not hide the first line from the rules.

## Repository layout

```text
antitextai/            the package: cleaner, scanner, verifier, CLI (no dependencies)
tests/                 57 unittest cases, runnable with unittest or pytest
SKILL.md               the Agent Skills compatible skill: full ruleset and workflow
AGENTS.md              short pointer for AGENTS.md-reading agents
docs/                  agent integration, architecture, and the AI signature manual
integrations/          ready-to-copy rule files for ten tools
examples/              a dirty fixture and the exact output of cleaning it
scripts/               install.sh and install.ps1
```

## Development

```bash
python -m unittest discover -s tests -t . -v     # full suite, no pytest needed
python -m antitextai verify CONTRIBUTING.md CHANGELOG.md integrations \
  antitextai/files.py antitextai/scan.py antitextai/verify.py antitextai/cli.py --strict
```

Everything is stdlib. `tests/` holds the regression suite, and every assertion in it is a
defect that was observed in practice, not a hypothetical. See
[`docs/architecture.md`](docs/architecture.md) for the rule ordering and the failure modes
the code is shaped around.

The command above deliberately lists files rather than whole directories. `SKILL.md`, the
READMEs, `docs/ai-signatures-manual.md`, `antitextai/cleaner.py`, and `tests/` all quote the
patterns the tool looks for, as the data they are: the same concession a linter makes for its
own test suite. Everything else in this repository has to pass clean, and `tests/test_selfcheck.py`
enforces exactly that.

Pull requests welcome. Run the suite and the self-scan before opening one; CI runs both on
Linux, macOS, and Windows across Python 3.9 to 3.13.

## Compatibility

`SKILL.md` follows the Agent Skills standard (`name` and `description` frontmatter in a
`SKILL.md` inside a folder named after the skill), which is what Claude Code, opencode, and
other readers of `.claude/skills/`, `.opencode/skills/`, and `.agents/skills/` expect.
Nothing in the package needs an agent to run: the CLI and the library stand alone.

## License

MIT. See [LICENSE](LICENSE).

Built by [Akujejo](https://github.com/satriazoid), with Hermes Agent.
