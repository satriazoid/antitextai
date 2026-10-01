# antitextai for omp

omp (oh-my-pi) loads skills from its config directory. There is no tool-specific rule file,
so install the repository's root `SKILL.md` here:

```text
.omp/skills/antitextai/SKILL.md
```

Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.