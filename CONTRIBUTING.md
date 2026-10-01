# Contributing

Thanks for considering it. Two things make a change easy to accept: the suite passes, and the
repository passes its own check.

```bash
git clone https://github.com/satriazoid/antitextai.git
cd antitextai
python -m unittest discover -s tests -t . -v          # 111 cases, no pytest needed
python -m antitextai scan antitextai tests --strict    # the tool applied to itself
```

Nothing to install: the package sits at the repo root, so `python -m antitextai` runs it, and
`python -m pytest` works too if you prefer it. Python 3.9+ is required and the package has no
runtime dependencies, which is a rule rather than a preference.

## What a good change looks like

- **Add a regression test for every behavior change.** Every assertion in `tests/test_clean.py`
  is a defect that was observed in practice. A fix without a test that failed before it will be
  asked for one.
- **Keep the tool conservative.** When a rule needs a decision, report instead of rewriting. The
  em/en dash exclusion is the model: the tool says what it found, the human decides.
- **Never lose content.** Frames are stripped and their substance kept. A rule that deletes a
  whole line must justify why the line had no information in it.
- **Respect the ordering contract** in `clean()`: characters, frames, whole-line deletions,
  whitespace. Reordering it breaks `^`-anchored rules in ways that are hard to see.
- **Keep `SKILL.md` and the code in agreement.** If you change what the tool does, the spec, the
  README table, and the example fixture all move in the same pull request.
- **No dependencies.** Standard library only. A new import needs a strong argument.
- **Match the prose style of the repo.** Short sentences, no marketing adjectives, no em dash
  where a comma or a period works.

## Adding support for another tool

1. Add a rule file under `integrations/<tool>/`, matching what that tool loads (`.mdc`, a plain
   markdown rule, `CONVENTIONS.md`, and so on).
2. Add the target to both installers (`scripts/install.sh` and `scripts/install.ps1`) and to the
   target list in their help text.
3. Add the row to `integrations/README.md`, `docs/agent-integration.md`, and the table in
   `README.md`.
4. If the tool reads a file that commonly already exists (`AGENTS.md`, `GEMINI.md`,
   `copilot-instructions.md`), use the block merge via `scripts/_block.py` instead of
   overwriting. Never clobber a user's file.

## Reporting a bug

Include the input file or the smallest text that shows the problem, the exact command, the
output you got, and the output you expected. A character that survives a pass, or content that
disappeared, is a bug worth a fixture in `examples/` or a case in `tests/test_clean.py`.

## Commit messages

One line of what changed, then why if it is not obvious. Conventional Commits prefixes are
welcome: `feat:`, `fix:`, `docs:`, `test:`, `chore:`. Do not describe the diff line by line; the
diff already does that.

## License

Contributions are accepted under the MIT license, see [LICENSE](LICENSE).
