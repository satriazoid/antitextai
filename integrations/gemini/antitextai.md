# antitextai for Gemini CLI

Gemini CLI reads `GEMINI.md` in the project root, or `~/.gemini/GEMINI.md` for every project.
This repository removes AI and LLM tells from generated text and code. Apply these rules
whenever you write, edit, or review prose, Markdown, or source files.

Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
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
- Legitimate diagrams, checklists, math symbols, and non-Latin scripts.
- Line endings and YAML frontmatter: preserve both byte for byte, and write files with `newline=""`.

Gemini CLI also reads Agent Skills from `.gemini/skills/` or `.agents/skills/`; the repository
root `SKILL.md` is the full ruleset.