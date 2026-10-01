# Architecture

How the cleaner is built, why the rules are ordered the way they are, and the failure modes
the code is shaped to avoid. Every claim here is enforced by a test in `tests/`.

## Shape

```text
antitextai/
  cleaner.py   the passes and the assertions; no I/O
  scan.py      inventory: per-codepoint classification, rule hits, line numbers
  verify.py    the proof pass, built on cleaner.assert_no_artifacts
  files.py     file discovery, binary and non-UTF-8 rejection
  fonts.py     scan-fonts: font-family declarations that read as AI typography
  styles.py    scan-styles: linguistic tells, report-only
  cli.py       scan | clean | verify | scan-fonts | scan-styles
```

`cleaner.py` has no dependency on the others, so it can be vendored into another project as a
single file. `scan.py` and `verify.py` import from it rather than reimplementing the rules,
which is what makes "the verifier says clean" and "the cleaner produced clean output" the same
statement instead of two hopeful ones.

## The passes, in order

`clean(text)` runs exactly this sequence. Order is the contract.

1. **BOM handling.** The byte-0 `U+FEFF` is removed by default. With `strip_bom=False` it is
   detached, the passes run on the body, and the BOM is re-attached at the end. Leaving it in
   place would hide the first line from every `^`-anchored rule, and `INVISIBLE` would delete it
   as an ordinary `U+FEFF` anyway.
2. **Line-ending detection, then normalization to `\n`.** The original CRLF or LF choice is
   recorded and restored at the end. Detection requires a real `\r\n` count, so newline-free
   input is never misread as CRLF.
3. **Frontmatter split.** `\A--- ... ---` is cut off before any line rule runs, so YAML and its
   delimiters are safe by construction rather than by luck.
4. **Character passes.** `INVISIBLE`, leading bullets (`\1- `), remaining `U+2022`, `NBSP`, then
   the `SMART` translation table. Setext underlines are masked out here, before the line rules.
5. **Frames, to a fixpoint.** `INTERJECT`, `CLAUSE`, `SUBORDINATE`, `GESTURE_INLINE` run in a
   loop until the text stops changing, because stripping one frame can expose another.
6. **Whole-line deletions.** Fluff lines, sign-offs, inline sign-offs, pre-code meta-text,
   end markers (standalone and trailing), narration, step comments, separators.
7. **Whitespace.** Trailing spaces per line, then runs of 3+ newlines collapsed to one blank line.
8. **Restore.** Masked setext underlines, the original line-ending style, and the kept BOM.

## Why the rules look like this

**Frames wrap substance, so the frame is stripped, not the line.** `In today's market, revenue
grew 12%.` must become `Revenue grew 12%.` The first implementation deleted the line and emptied
files whose only fault was an opener. `tests/test_clean.py::FrameTest` pins the behavior.

**Frames end where the grammar ends.** Interjections (`Certainly!`) and adverbial openers
(`In today's ...`) terminate at punctuation. Complementizers (`note that`) have no comma, so the
rule consumes only through `that` and keeps the clause, which is the sentence's actual content.
Every frame rule consumes one following word character and uppercases it, so a stripped frame
never leaves `the loop terminates.` with a lowercase start.

**Multi-word openers are single alternatives.** Matching a bare `sure` first turned
`Sure thing! Below is a walkthrough.` into `Thing! Below is a walkthrough.`. `sure thing`,
`no problem`, `of course` and `great question` are listed as atomic alternatives, and the
interjection rule requires trailing punctuation so that content like `Got it working now.`
is not truncated.

**Comment markers are anchored.** `CP = (?://|#|--|\*)` counts as a comment only at line start
or after whitespace. That single anchoring is what keeps `x = "# end of loop"`,
`url = 'http://x--y/z'` and `"-" * 8` intact. Regex cannot parse strings, so the scan treats any
file with comment-looking literals as a manual-review candidate.

**Trailing end markers need a lookbehind.** `return 1  # end` is not at line start, so a
`^`-anchored rule misses it; deleting the whole line would destroy the code. `END_TRAIL` uses
`(?<=\S)` so it removes only the comment and never consumes the code's last character.

**Setext headings must be masked twice.** A run of `=` or `-` alone on a line is either a banner
or a heading underline, and `SEPARATOR` cannot tell. `setext_lines()` detects the heading case
(text line directly above, unindented, previous line not itself a rule) and both the cleaner and
`assert_no_artifacts()` apply the same mask. Without that shared mask the verifier reports a
legitimately kept heading as a residual.

**Em and en dashes are excluded on purpose.** `2019–2021`, `Jean–Luc`, and `word—word` need three
different replacements. The dashes are therefore reported by `scan` and flagged by `verify`
(with `--allow-dashes` to silence it after review), never rewritten. The tests assert the dashes
survive a clean pass even inside prose.

## Failure modes found during construction

Each of these was reproduced, fixed, and locked behind a regression test:

| Defect | Guard |
| --- | --- |
| Line-deleting frame rules destroyed substantive content | `FrameTest`, and the "strip the frame, keep the substance" wording in `SKILL.md` |
| Non-atomic `sure` alternative orphaned `Thing! Below is ...` | `test_multi_word_openers_are_atomic` |
| `GESTURE_INLINE` missed the whole `note that` family mid-paragraph | `test_mid_paragraph_gesture` |
| `SEPARATOR` silently demoted setext headings to body text | `test_setext_underline_survives` |
| The verifier then flagged those kept headings as residuals | shared `setext_lines()` mask |
| Trailing end markers both missed and destructively deleted | `test_trailing_end_marker_drops_comment_only` |
| `--` comments were not covered | `CP` includes `--` |
| Frames left lowercase sentence starts | every frame rule consumes and uppercases a word character |
| CRLF detection misfired on newline-free input | `test_line_endings_preserved` |
| `strip_bom=False` still deleted the BOM (it is in `INVISIBLE`) | `test_strip_bom_can_be_disabled` |
| `--quiet` swallowed stdout, so `clean` printed nothing | `test_clean_prints_to_stdout_by_default` |
| Rule hits reported line 0 because only line starts were indexed | `test_line_numbers_point_at_the_match` |
| Windows `write_text` translated `\n` to `\r\n`, making tests platform-bound | fixtures in `tests/` write bytes |

## Verification model

Three layers, and they check different things:

1. **Unit and regression tests** (`tests/`, 111 cases): exact expected output for a mixed document,
   content preservation for each frame, code-safety fixtures, line endings, frontmatter bytes,
   idempotence, CLI exit codes, scanner classification, and the documented example.
2. **`assert_no_artifacts(text)`**: the cleaner's own rules applied to its output. Idempotence
   (`clean(clean(x)) == clean(x)`) is asserted separately, because a rule set that keeps finding
   work is a rule set that is wrong.
3. **`verify --strict` in CI**: the same assertion over the repository's own files, plus a
   self-scan, on Linux, macOS, and Windows across Python 3.9 to 3.13.

### Why this repository cannot verify itself wholesale

A de-AI tool ships next to the tells it looks for. `SKILL.md` is a specification full of example
inputs, the READMEs contain a before/after pair, `docs/ai-signatures-manual.md` catalogs the
literal codepoints, `cleaner.py` documents the exact phrases its patterns match, and `tests/` is
a suite of dirty fixtures. Running `verify --strict` over the whole tree therefore reports the
data, not a defect, which is exactly the distinction the tool draws everywhere else: a character
inside a string literal is data.

So CI verifies an explicit list (`tests/test_selfcheck.py` runs the same check in-process) and
covers the files where a leftover tell would be an accident: the package modules, the project
docs, the integration rule files, `pyproject.toml`, and the workflow itself. `--allow-dashes`
stays on for the project docs, because the prose uses em dashes deliberately, which is the
living example of the review rule.

The example fixture is part of the contract: `examples/demo_before.md` deliberately contains
every tell the tool claims to remove, `examples/demo_after.md` is the exact output, and
`tests/test_examples.py` fails if a rule change makes those two disagree.
