# Agent instructions

This repository removes AI and LLM tells from text, Markdown, and source code.

When a task involves cleaning generated text or code, read `SKILL.md` first: it holds the full
ruleset, the workflow, and the rules the tool deliberately refuses to apply. Then use the CLI
rather than hand-editing:

```bash
python -m antitextai scan PATH                 # inventory first, changes nothing
python -m antitextai clean --write PATH        # deterministic passes only
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Rules that matter for every task in this repo:

- Em dash `U+2014` and en dash `U+2013` are never replaced automatically. Report them, decide
  each one, or run `verify --allow-dashes` only after reviewing them.
- Never edit inside string literals, test fixtures, or i18n data to remove characters that are
  the data under test.
- Preserve line endings and YAML frontmatter byte for byte. Write files with `newline=""`.
- Add a regression test to `tests/` for every behavior you change, then run
  `python -m unittest discover -s tests -t .`.
- Keep `SKILL.md`, `README.md`, and `examples/demo_after.md` in agreement with the code in the
  same change, since the tests pin that example.

Deep dives: `docs/architecture.md` (rule ordering, failure modes) and
`docs/ai-signatures-manual.md` (the full signature catalog).
