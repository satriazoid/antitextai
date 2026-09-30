---
name: antitextai
description: Strip AI and LLM tells from text, Markdown, and source code.
license: MIT
compatibility: any agent that can run a shell command, or import Python directly
metadata:
  version: 1.0.0
  repository: https://github.com/satriazoid/antitextai
  tags: text-cleanup, unicode, de-ai, refactoring
---

# antitextai

Specification and executable ruleset for de-AI-ing generated text and code: invisible
Unicode, smart quotes, banner separators, end-of-block markers, narration comments,
conversational frames, NBSP indentation.

Use when the goal is text or code that does not read as machine-generated: humanizing LLM
output, anti-AI filters, preprocessing datasets, refactoring AI-written commits.

The deterministic half runs as a command. The judgment half is yours, and this document
says exactly which is which. Nothing here needs the network, and the tool has no
dependencies beyond the Python standard library.

## When to Use

- A file, diff, or document still carries LLM fingerprints: invisible characters, curly
  quotes, `# ====` banners, `# end function x`, NBSP indentation.
- Preparing LLM output for publication: commits, PRs, docs, datasets.
- Wiring a cleanup step into CI or a pre-commit hook.
- Checking CSS/HTML for AI-generated font-family declarations (non-standard fonts).
- Detecting AI-style linguistic tells in prose (hedging, fluff openers, sign-offs, bold-keyword lists, emoji headings).

## Font Detection

The `scan-fonts` subcommand detects non-standard font-family declarations in CSS and HTML files.
Only five Google-sourced sans-serif fonts are considered human-curated:

1. **Roboto** - Font sans-serif modern dari Google, clean dan mudah dibaca, cocok untuk UI/web design.
2. **Open Sans** - Font humanist sans-serif yang netral dan friendly, sangat versatile untuk berbagai keperluan.
3. **Montserrat** - Font geometric sans-serif dengan karakter elegan, sering digunakan untuk heading dan branding.
4. **Lato** - Font sans-serif semi-rounded yang hangat namun profesional, bagus untuk body text.
5. **Poppins** - Font geometric sans-serif dengan bentuk bulat dan modern, populer untuk desain contemporary.

If any other font is detected in `font-family` declarations or Google Fonts `<link>` tags,
it is flagged as an AI tell and the scanner recommends one of the five allowed fonts.

```bash
python -m antitextai scan-fonts .                           # detect non-standard fonts
python -m antitextai scan-fonts src --strict                # fail if any non-allowed font is found
python -m antitextai scan-fonts . --json > fonts.json       # machine-readable report
```

## Style Detection

The `scan-styles` subcommand detects AI-generated prose patterns in text files:

| Rule | Pattern | Action |
| --- | --- | --- |
| `HEDGING` | generally, typically, often, usually, somewhat, fairly, rather, pretty, quite, more or less, in general, on the whole | remove hedge or replace with direct statement |
| `TRANSITION` | furthermore, additionally, moreover, consequently, nevertheless, hence, thus, accordingly, meanwhile, subsequently, alternatively, specifically, notably, essentially, ultimately, therefore, similarly, however, although | consider removing or replacing with simpler link |
| `AI_OPENER` | Certainly!, Sure thing!, Of course!, Great question!, Happy to help!, etc. | delete entire line; AI filler |
| `AI_SIGNOFF` | Hope this helps!, Let me know if..., Feel free to ask..., Don't hesitate to reach out... | delete entire line; AI filler |
| `MID_GESTURE` | It's important to note that..., Please note that..., Needless to say..., In fact, Indeed... | delete the gesture clause |
| `BOLD_KEYWORD_LIST` | `- **Security:** value`, `* **Key:** value` | drop the bold keyword prefix, write as plain prose |
| `EMOJI_HEADING` | `## 🚀 Overview`, `### ✅ Summary` | remove emoji from heading |
| `FILLER_SECTION` | `## Overview`, `## Conclusion`, `## Summary` (empty sections) | delete empty filler section |

```bash
python -m antitextai scan-styles .                          # detect AI-style tells
python -m antitextai scan-styles src --strict               # fail if any tell is found
python -m antitextai scan-styles . --json > styles.json     # machine-readable report
```

## When NOT to use

- Inside string literals, fixtures, or test data where a character is **data** (Unicode
  compatibility tables, i18n corpora, encoding tests). Cleaning there breaks the program.
- Quoted third-party material, license headers, transcripts, cited text.
- Files that must stay non-UTF-8 or carry a BOM for a legacy consumer.
- A BOM anywhere except byte 0 of a file: never delete a mid-file BOM to "clean" it.

## Prerequisites

- Python 3.9 or newer. No packages to install.
- The tool, which is either this repository cloned locally (then `python -m antitextai`
  works from the repo root) or installed with
  `pipx install "git+https://github.com/satriazoid/antitextai"` (then `antitextai`).

## How to Run

Run these through `terminal`. Order matters: inventory, transform, prove.

```bash
python -m antitextai scan .                        # 1. what is in there, change nothing
python -m antitextai clean --write PATH...         # 2. rewrite the deterministic half
python -m antitextai verify PATH... --strict       # 4. prove it, exit 1 when still dirty
```

- `scan` reports every non-ASCII codepoint with count and first line:column, classified as
  `mapped` (the tool will fix it), `review` (a human must decide), `decorative` (likely
  formatting, check it), `keep` (real content: accented Latin, Greek, CJK), plus every rule
  hit with sample line numbers. `--json` for machine-readable output.
- `clean` prints to stdout by default and only rewrites with `--write`. `-` reads stdin.
- `verify` re-runs the cleaner's own assertions and exits 1 on a residual with `--strict`.
- Both walk directories recursively over known text extensions, skip `.git`, `node_modules`,
  `__pycache__`, `.venv`, `dist`, `build`, `target`, and drop binary or non-UTF-8 files.

As a library, when a single file or an in-memory string is in play:

```python
from antitextai import clean, assert_no_artifacts, scan_text
assert_no_artifacts(clean(open("draft.md", encoding="utf-8").read()))
```

## Quick Reference

### Characters: mapped automatically

| Character | Codepoint | Becomes |
| --- | --- | --- |
| Zero-width space / non-joiner / joiner / word joiner | `U+200B` `U+200C` `U+200D` `U+2060` | deleted |
| BOM at byte 0 | `U+FEFF` | deleted (a mid-file `U+FEFF` goes with the class below) |
| Soft hyphen, LRM, RLM | `U+00AD` `U+200E` `U+200F` | deleted |
| Non-breaking / narrow space | `U+00A0` `U+202F` | space |
| Smart quotes, primes | `U+201C` `U+201D` `U+2018` `U+2019` `U+2032` `U+2033` | `"` and `'` |
| Ellipsis token | `U+2026` | `...` |
| Multiplication sign, minus sign | `U+00D7` `U+2212` | `x`, `-` |
| Bullet | `U+2022` | `-` (`- ` at line start) |

### Characters: reported, never replaced

| Character | Why it needs you |
| --- | --- |
| Em dash `U+2014`, en dash `U+2013` | A dash can join a numeric range (`2019–2021`), a compound noun, a quotation, or a clause. Each has a different correct replacement, so every occurrence goes through review. Prefer splitting the sentence or a comma over a blind `-`, which is its own tic. |
| Box drawing `U+2500`-`U+257F`, arrows `U+2190`-`U+21FF`, dingbats `U+2600`-`U+27BF`, emoji `U+1F300`-`U+1FAFF` | Reported as `decorative`. Delete decorative banners and status glyphs on headings, but a real tree diagram or a checked checklist stays. |
| Anything classified `unclassified` | Look at it before deciding. Real content is classified `keep`. |

### Lines: whole-line rules

| Rule | Pattern shape | Action |
| --- | --- | --- |
| Separator / banner | a line that is only `=` `-` `*` `_` repeated 5+ times, optionally wrapped in comment markers | delete |
| End marker, standalone | `# end of loop`, `// end function f`, `-- end of block` | delete |
| End marker, trailing | code followed by `  # end function f` | delete the comment only, keep the code |
| Narration comment | `# Now we loop over the items`, `# Return the result` | delete |
| Step comment | `# Step 1: ...`, `# Step 2: ...` | delete unless the order is a protocol requirement |
| Pre-code meta-text | `Here is the complete Python script to achieve this:` alone before a fence | delete |
| Pure fluff line | `Certainly!`, `Hope this helps!`, `Thanks!` alone on a line | delete |
| Sign-off line or inline | `Let me know if ...`, `... is a solid choice. Hope this helps!` | delete the sign-off, keep the sentence before it |

### Frames: stripped, never deleted with their content

| Frame | Input becomes output |
| --- | --- |
| Interjection | `Certainly! The build passes.` to `The build passes.` |
| Adverbial opener | `In today's market, revenue grew 12%.` to `Revenue grew 12%.` |
| Complementizer | `It's important to note that the loop terminates.` to `The loop terminates.` |
| Mid-paragraph gesture | `Caching is essential. Please note that TTLs help.` to `Caching is essential. TTLs help.` |

Every frame rule consumes the following word character and recapitalizes it, so a stripped
frame never leaves a lowercase sentence start. Multi-word openers (`sure thing`,
`no problem`, `of course`, `great question`) are single alternatives, so nothing is orphaned.

## Procedure

1. **Inventory.** `python -m antitextai scan PATH`. Completion: you can name which files are
   dirty and which findings are `review` or `decorative` rather than `mapped`.
2. **Decide the exclusions** from "When NOT to use" per file. Completion: every file you are
   about to touch has a reason to be touched.
3. **Transform.** `python -m antitextai clean --write PATH...`. Completion: exit code 0 and
   no residual line on stderr.
4. **Hand-edit the judgment rules.** Em/en dashes, docstrings, banners that mark a real module
   boundary, WHAT-comments, hyper-descriptive identifiers, hedging stacks, emoji headings.
   Completion: no `review` finding left unexplained.
5. **Review the diff.** Every touched line must still say the same thing. A transformation
   that changed meaning is a bug, not a cleanup. Completion: encoding still UTF-8, no string
   literal changed, line endings unchanged, frontmatter byte-identical.
6. **Prove zero.** `python -m antitextai verify PATH --strict`. Completion: exit 0. Keep
   `--allow-dashes` only when the remaining dashes were individually reviewed.
7. **Build and test.** Run the project's own build and test command. Whitespace and identifier
   edits fail at runtime, not at parse time.

## Judgment work the tool refuses to do

- **Docstrings.** Strip them on internal, trivial helpers. Keep any docstring carrying contract
  information a signature cannot express (units, ranges, raises, side effects, ownership) and
  keep public or exported API docs; removing those is an API regression.
- **WHAT-comments vs WHY-comments.** Delete comments restating the syntax. Keep constraints,
  workarounds, bug references, invariants.
- **Banner labels.** Delete the decorative lines. Keep the label only if it names a real module
  boundary, then express it as a normal one-line comment or split the module.
- **Identifiers.** `processed_user_data_response_object` becomes `data` or `user_res`. Match the
  surrounding file's naming style exactly; a second convention in one file is worse.
- **Hedging stacks.** `generally typically often usually` loses all but one hedge.
- **Bold keyword prefixes** on every list item (`- **Security:** ...`): drop the forced bold term
  or rewrite as prose. Keep bold in a genuine definition list.
- **Subheading fragmentation.** Merge one-sentence sections under one heading.
- **Emoji section markers** (a rocket or chart glyph on a heading): delete unless the document's own
  style needs them.

## Pitfalls

1. **Deleting a frame's line destroys content.** `In today's market, revenue grew 12%.` must
   become `Revenue grew 12%.`, not vanish. This was the most damaging bug in the tool's history.
2. **Comment prefixes are anchored on purpose.** `x = "# end of loop"` and `url = 'http://x--y/z'`
   survive because a prefix counts as a comment only at line start or after whitespace. Regex
   cannot parse strings, so eyeball any file with comment-looking literals, then verify.
3. **Setext headings look like separators.** `Heading` over `------` is a heading. The tool masks
   those lines; if you hand-roll a pass, you will silently demote headings to body text.
4. **Order is the contract:** characters, then frames, then whole-line deletions, then whitespace
   collapse. Normalize NBSP after the line rules and every `^`-anchored pattern mis-anchors.
5. **Frontmatter is split off first.** YAML and `---` delimiters never see a line rule.
6. **Line endings are preserved.** CRLF in, CRLF out. Writing files with a text-mode newline
   translation on Windows will silently convert them; use `newline=""`.
7. **Binary files are skipped by content, not by extension.** Any NUL byte or non-UTF-8 means
   hands off. Non-ASCII inside a binary is normal.
8. **Font recommendations are heuristic.** The `scan-fonts` command suggests replacements based
   on keyword overlap (e.g., "geometric" → Montserrat, "humanist" → Open Sans). Review the output
   and adjust manually if the suggestion doesn't fit the context.
9. **Style detection is additive only.** `scan-styles` reports finds but does not auto-fix.
   Some patterns (like `HEDGING`, `TRANSITION`) are debatable — review before removing.
10. **Emoji detection uses Unicode ranges.** Some uncommon emoji outside the scanned ranges may slip through.

## Verification

- `python -m antitextai verify PATH --strict` exits 0.
- `python -m antitextai scan . --strict` finds nothing you did not expect, and every remaining
  finding is a reviewed em/en dash or a legitimate decorative glyph.
- `clean(clean(x)) == clean(x)` for any file you touched.
- The project's own test suite passes.
- `python -m unittest discover -s tests -t .` passes when you are working on this tool itself.
