# AI tells: clean before you commit

This project removes AI and LLM tells from generated text and code. Apply these rules whenever
you write, edit, or review prose, Markdown, or source files.

```bash
python -m antitextai scan PATH                 # inventory, nothing changes
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

## Never introduce

- Invisible characters: zero-width space/non-joiner/joiner, word joiner, soft hyphen, bidi marks.
- Smart quotes and primes, the ellipsis token, `×` and `−` in prose.
- Non-breaking or narrow spaces, especially in indentation.
- Banner separators built from `=` `-` `*` `_` repeated 5 or more times.
- Block-end markers: `# end of loop`, `// end function f`.
- Narration and step comments: `# Now we ...`, `# Step 1: ...`, `# Return the result`.
- Conversational frames: `Certainly!`, `Sure thing!`, `In today's ...`,
  `It's important to note that ...`, `Here is the complete ... script`, `Hope this helps!`.
- WHAT-comments that restate the syntax below them.

## Never remove without checking

- Em dash and en dash: a range, a compound noun, and a clause break each differ.
- Public API docstrings and any docstring with units, ranges, raises, or side effects.
- String literals and fixtures where the character is the data under test.
- Legitimate diagrams, checklists, math symbols, and non-Latin scripts.
- Line endings and YAML frontmatter: preserve both, and write files with `newline=""`.

## Style

One naming convention per file. One hedge per sentence. Do not pad list items to equal length,
do not bold the first word of every bullet, and merge one-sentence sections instead of adding
another heading.

Full ruleset: `SKILL.md` in the antitextai repository.
