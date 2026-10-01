# antitextai for Agent Skills readers

Tools that read the `.agents` convention load Agent Skills: a folder containing `SKILL.md`.
Install the repository's root `SKILL.md` at one of these paths:

```text
.agents/skills/antitextai/SKILL.md          # project
~/.agents/skills/antitextai/SKILL.md        # global
```

Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.