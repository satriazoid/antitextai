# Integrations

Ready-to-copy rule files for the tools that read instructions from a file instead of running a
command. `SKILL.md` at the repository root is the full ruleset; these are the trimmed versions
each tool's loader expects.

| Directory | Tool | Install as |
| --- | --- | --- |
| `cursor/` | Cursor | `.cursor/rules/antitextai.mdc` |
| `copilot/` | GitHub Copilot | `.github/copilot-instructions.md` |
| `windsurf/` | Windsurf | `.windsurf/rules/antitextai.md` |
| `cline/` | Cline | `.clinerules/antitextai.md` |
| `aider/` | Aider | `CONVENTIONS.md` (add `read: CONVENTIONS.md` to `.aider.conf.yml`) |
| `codex/` | Codex CLI | `AGENTS.md` (project) or `~/.codex/AGENTS.md` (global) |
| `gemini/` | Gemini CLI | `GEMINI.md` (project) or `~/.gemini/GEMINI.md` (global) |
| `roo-code/` | Roo Code | `.roo/rules/antitextai.md` or `~/.roo/rules/antitextai.md` |
| `goose/` | goose | `.goosehints` (project) or `~/.config/goose/.goosehints` (global) |
| `warp/` | Warp | `WARP.md` (project) or `~/.agents/AGENTS.md` (global) |
| `claude-code/` | Claude Code | see below, or run the installer |
| `opencode/` | opencode | see below, or run the installer |
| `agents/` | `.agents` convention readers | see below, or run the installer |
| `hermes/` | Hermes Agent | see below, or run the installer |
| `omp/` | omp (oh-my-pi) | see below, or run the installer |
| `qwen-code/` | Qwen Code | see below, or run the installer |
| `crush/` | Crush | see below, or run the installer |
| `kilo-code/` | Kilo Code | see below, or run the installer |

## Skill-based tools

Claude Code, opencode, the `.agents` convention, Hermes Agent, omp, Qwen Code, Crush, and
Kilo Code load a folder containing `SKILL.md`, so there is nothing tool-specific to copy:
point them at the repository's own `SKILL.md`.

```bash
mkdir -p .claude/skills/antitextai    && cp ../SKILL.md .claude/skills/antitextai/    # Claude Code
mkdir -p .opencode/skills/antitextai  && cp ../SKILL.md .opencode/skills/antitextai/  # opencode
mkdir -p .agents/skills/antitextai    && cp ../SKILL.md .agents/skills/antitextai/    # .agents convention
mkdir -p .qwen/skills/antitextai      && cp ../SKILL.md .qwen/skills/antitextai/      # Qwen Code
mkdir -p .crush/skills/antitextai     && cp ../SKILL.md .crush/skills/antitextai/     # Crush
mkdir -p .kilo/skills/antitextai      && cp ../SKILL.md .kilo/skills/antitextai/      # Kilo Code
```

Or let the installer resolve every path for you:

```bash
bash scripts/install.sh --target all --dry-run     # see what would happen
bash scripts/install.sh --target all               # do it in the current project
bash scripts/install.sh --target claude-code --global
pwsh scripts/install.ps1 -Target all -DryRun
```

## Shared instruction files

`AGENTS.md`, `GEMINI.md`, and `.github/copilot-instructions.md` are often already in use, so the
installer does not clobber them. It inserts the rules from the tool's own file under
`integrations/` (`codex/antitextai.md`, `gemini/antitextai.md`, or
`copilot/copilot-instructions.md`) between HTML comment markers and replaces only that block on
a later run. Everything outside the markers is left alone.

```markdown
<!-- antitextai:begin -->
<!-- managed by antitextai ... -->
... the rules ...
<!-- antitextai:end -->
```

To do it by hand instead, copy the file under `integrations/<tool>/` to the file your tool
reads (`roo-code/`, `goose/`, and `warp/` write dedicated files rather than merging).

Details, including the paths each tool uses at project and user level, are in
[../docs/agent-integration.md](../docs/agent-integration.md).
