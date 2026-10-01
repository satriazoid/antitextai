# antitextai for opencode

opencode loads Agent Skills: a folder containing `SKILL.md`. There is no tool-specific rule
file, so install the repository's root `SKILL.md` at one of these paths:

```text
.opencode/skills/antitextai/SKILL.md          # project
~/.config/opencode/skills/antitextai/SKILL.md # global
```

opencode also discovers `.claude/skills/` and `.agents/skills/`, so one copy can serve
several tools. Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.