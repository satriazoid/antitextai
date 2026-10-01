# antitextai for Hermes Agent

Hermes Agent loads skills from a profile directory. There is no tool-specific rule file, so
install the repository's root `SKILL.md` here:

```text
~/.hermes/skills/antitextai/SKILL.md
```

On Windows the profile lives under `%LOCALAPPDATA%\hermes\skills\`. Run the tool instead of
editing by hand:

```bash
python -m antitextai scan PATH                 # inventory, changes nothing
python -m antitextai clean --write PATH        # deterministic passes
python -m antitextai verify PATH --strict      # must exit 0 before you report success
```

Full ruleset: [`SKILL.md`](../../SKILL.md) at the repository root.