# antitextai: strip AI tells from generated text and code

This project treats machine-written text as something to clean, not to ship. Apply these rules
whenever you write, edit, or review prose, Markdown, or source code.

## Run the tool

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes only
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full spec: `SKILL.md` at the repository root. Architecture and failure modes:
`docs/architecture.md`.

## Never write these

- Invisible characters: zero-width space/non-joiner/joiner, word joiner, soft hyphen, bidi marks.
- Smart quotes and primes (`“ ” ‘ ’ ′ ″`), the ellipsis token, `×` and `−` in prose.
- Non-breaking or narrow spaces, especially in indentation or before code.
- Banner separators made of `=` `-` `*` `_` repeated 5+ times.
- Block-end markers: `# end of loop`, `// end function f`, `/* end class X */`.
- Narration comments: `# Now we ...`, `# Step 1: ...`, `# Return the result`.
- Conversational frames: `Certainly!`, `Sure thing!`, `In today's ...`,
  `It's important to note that ...`, `Here is the complete ... script`, `Hope this helps!`.

## Never touch these

- Em dash `—` and en dash `–`. A numeric range, a compound noun, and a clause break each need a
  different replacement, so each occurrence is a human decision.
- Docstrings on public or exported APIs, and any docstring carrying contract information: units,
  ranges, raises, side effects, ownership.
- Legitimate decorative structure: a real tree diagram, a checked checklist, math symbols
  (`Σ Π λ ± × ≥`), accented Latin, Cyrillic, Hebrew, Arabic, CJK.
- String literals and test fixtures where the character is the data under test.
- Line endings and YAML frontmatter: preserve both byte for byte, and write files with
  `newline=""` so nothing is translated.

## Style rules that follow from the same principle

- Delete WHAT-comments, keep WHY-comments (constraints, workarounds, bug references, invariants).
- One naming convention per file. Match the file you are editing.
- One hedge per sentence, not `generally typically often usually`.
- Do not fragment short explanations into more headings, and do not bold-prefix every list item.
- Do not pad a bullet list so every item is the same length.
