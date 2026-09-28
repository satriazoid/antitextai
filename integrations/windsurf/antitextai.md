# Rule: strip AI tells from generated text and code

Trigger: scraping, generating, refactoring, or reviewing any prose, Markdown, or source file.

Run the tool instead of editing by hand:

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

## Never remove without checking

- Em dash and en dash: ranges, compound nouns, and clause breaks differ.
- Public API docstrings and any docstring with units, ranges, raises, or side effects.
- String literals and fixtures where the character is the data under test.
- Legitimate diagrams, checklists, math symbols, non-Latin scripts.
- Line endings and YAML frontmatter: preserve both, and write files with `newline=""`.

Full spec: `SKILL.md` in the antitextai repository.
