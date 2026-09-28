# Conventions

This project removes AI and LLM tells from generated text and code. Follow these before you
write or edit prose, Markdown, or source files.

Run the tool rather than hand-editing:

```bash
python -m antitextai scan PATH                 # inventory, nothing changes
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before reporting success
```

## Do not write

- Invisible characters: zero-width space, non-joiner, joiner, word joiner, soft hyphen, bidi marks.
- Smart quotes and primes, the ellipsis token, `×` and `−` in prose.
- Non-breaking or narrow spaces, especially in indentation.
- Banner separators: lines of `=` `-` `*` `_` repeated 5 or more times.
- Block-end markers: `# end of loop`, `// end function f`.
- Narration comments: `# Now we ...`, `# Step 1: ...`, `# Return the result`.
- Conversational frames: `Certainly!`, `Sure thing!`, `In today's ...`,
  `It's important to note that ...`, `Here is the complete ... script`, `Hope this helps!`.
- WHAT-comments that restate the syntax of the line below.

## Do not touch

- Em dash and en dash. A numeric range, a compound noun, and a clause break each take a
  different replacement, so every occurrence is a decision, not a rule.
- Docstrings on public APIs and any docstring carrying units, ranges, raises, or side effects.
- String literals, fixtures, and i18n data in which the character is the data under test.
- Legitimate diagrams, checklists, math symbols, and non-Latin scripts.
- Line endings and YAML frontmatter: byte for byte, and write files with `newline=""`.

## Style

One naming convention per file. One hedge per sentence. No padding list items to equal length.
No bolding the first word of every bullet. Merge one-sentence sections instead of adding
another heading.
