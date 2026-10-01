# antitextai for Claude Code

Claude Code loads Agent Skills: a folder containing `SKILL.md`. There is no tool-specific
rule file, so install the repository's root `SKILL.md` at one of these paths:

```text
.claude/skills/antitextai/SKILL.md          # project
~/.claude/skills/antitextai/SKILL.md        # global
```

Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.