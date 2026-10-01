# antitextai for Qwen Code

Qwen Code loads Agent Skills: a folder containing `SKILL.md`. Install the repository's root
`SKILL.md` at one of these paths:

```text
.qwen/skills/antitextai/SKILL.md          # project
~/.qwen/skills/antitextai/SKILL.md        # global
```

Qwen Code also reads a `QWEN.md` context file and `.qwen/rules/`, but a skill is the right
home for the tool's procedural rules. Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.