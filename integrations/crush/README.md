# antitextai for Crush

Crush loads Agent Skills: a folder containing `SKILL.md`. Install the repository's root
`SKILL.md` at one of these paths:

```text
.crush/skills/antitextai/SKILL.md          # project
~/.config/crush/skills/antitextai/SKILL.md # global
```

Crush also reads `.agents/skills/` and a global `~/.config/crush/CRUSH.md`, but a skill is
the right home for the tool's procedural rules. Run the tool instead of editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.