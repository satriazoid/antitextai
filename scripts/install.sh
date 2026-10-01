#!/usr/bin/env bash
# antitextai installer: put SKILL.md and the per-tool rule files where your agent looks.
#
#   bash scripts/install.sh --target claude-code,opencode,cursor,copilot
#   bash scripts/install.sh --target all --global --force
#   bash scripts/install.sh --target hermes --dest /path/to/project --dry-run
#
# Project targets write into --dest (default: the current directory).
# --global targets the user-level config of each tool. Hermes and omp have no global
# variant here: pass the profile or skill directory as --dest instead.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$REPO_DIR/SKILL.md"
INSTRUCTION="$REPO_DIR/integrations/copilot/copilot-instructions.md"
PY="$(command -v python3 || command -v python || true)"

# A native interpreter (python.exe on Windows) cannot read an MSYS path like /c/foo, so
# paths handed to it are converted first. cygpath is present in Git Bash and MSYS2.
native_path() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -w "$1"; else printf '%s' "$1"; fi
}

TARGETS=""
DEST="$PWD"
GLOBAL=0
FORCE=0
DRY=0

usage() {
  cat <<'EOF'
antitextai installer

  --target, -t LIST   comma-separated tools, or "all"
                      claude-code opencode agents hermes omp
                      cursor windsurf cline aider copilot codex gemini
                      qwen-code crush kilo-code roo-code goose warp
  --dest,   -d DIR    project directory to install into (default: current directory)
  --global, -g        install into the user-level config for each tool
  --force,  -f        overwrite files that already exist and differ
  --dry-run           print what would happen, write nothing
  -h, --help          this text
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target|-t) TARGETS="${2:-}"; shift 2 ;;
    --dest|-d)   DEST="${2:-}"; shift 2 ;;
    --global|-g) GLOBAL=1; shift ;;
    --force|-f)  FORCE=1; shift ;;
    --dry-run)   DRY=1; shift ;;
    -h|--help)   usage; exit 0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

[ -f "$SKILL" ] || { echo "SKILL.md not found next to this script; run it from the clone" >&2; exit 2; }
[ -n "$TARGETS" ] || { usage >&2; exit 2; }
case "$TARGETS" in all) TARGETS="claude-code,opencode,agents,hermes,omp,cursor,windsurf,cline,aider,copilot,codex,gemini,qwen-code,crush,kilo-code,roo-code,goose,warp" ;; esac

FAILED=0

copy_file() {                       # copy_file SRC DST LABEL
  src="$1"; dst="$2"; label="$3"
  if [ "$DRY" = 1 ]; then echo "would write $dst"; return 0; fi
  mkdir -p "$(dirname "$dst")"
  if [ -e "$dst" ] && [ "$FORCE" != 1 ]; then
    if cmp -s "$src" "$dst"; then echo "up to date  $dst"; return 0; fi
    echo "skipped     $dst (exists and differs; use --force)" >&2; FAILED=$((FAILED+1)); return 0
  fi
  cp "$src" "$dst"
  echo "wrote       $dst   ($label)"
}

block_file() {                      # block_file SRC DST MARKER LABEL
  src="$1"; dst="$2"; marker="$3"; label="$4"
  if [ -z "$PY" ]; then echo "python not found; cannot merge into $dst" >&2; FAILED=$((FAILED+1)); return 0; fi
  src_n="$(native_path "$src")"; dst_n="$(native_path "$dst")"
  script_n="$(native_path "$REPO_DIR/scripts/_block.py")"
  if [ "$DRY" = 1 ]; then
    echo "would merge $src into $dst"
    "$PY" "$script_n" --file "$dst_n" --source "$src_n" --marker "$marker" --dry-run 2>/dev/null | sed 's/^/    | /'
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  set +e
  "$PY" "$script_n" --file "$dst_n" --source "$src_n" --marker "$marker" >/dev/null
  rc=$?
  set -e
  case "$rc" in
    0) echo "wrote       $dst   ($label)" ;;
    1) echo "up to date  $dst   ($label)" ;;
    *) echo "failed      $dst   ($label); see scripts/_block.py" >&2; FAILED=$((FAILED+1)) ;;
  esac
}

home_skill_dir() {                  # global skills directory for tool $1
  case "$1" in
    claude-code) echo "$HOME/.claude/skills/antitextai" ;;
    opencode)    echo "$HOME/.config/opencode/skills/antitextai" ;;
    agents)      echo "$HOME/.agents/skills/antitextai" ;;
    hermes)      echo "${HERMES_HOME:-$HOME/.hermes}/skills/antitextai" ;;
    omp)         echo "${OMP_HOME:-$HOME/.omp}/skills/antitextai" ;;
    qwen-code)   echo "$HOME/.qwen/skills/antitextai" ;;
    crush)       echo "$HOME/.config/crush/skills/antitextai" ;;
    kilo-code)   echo "$HOME/.kilo/skills/antitextai" ;;
    roo-code)    echo "$HOME/.roo/rules" ;;
    goose)       echo "$HOME/.config/goose" ;;
    warp)        echo "$HOME/.agents" ;;
  esac
}

install_target() {                  # install_target TOOL
  tool="$1"
  case "$tool" in
    claude-code) copy_file "$SKILL" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir claude-code; else echo "$DEST/.claude/skills/antitextai"; fi)/SKILL.md" "Claude Code skill" ;;
    opencode)    copy_file "$SKILL" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir opencode; else echo "$DEST/.opencode/skills/antitextai"; fi)/SKILL.md" "opencode skill" ;;
    agents)      copy_file "$SKILL" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir agents; else echo "$DEST/.agents/skills/antitextai"; fi)/SKILL.md" "Agent Skills convention" ;;
    hermes)      copy_file "$SKILL" "$(home_skill_dir hermes)/SKILL.md" "Hermes Agent skill" ;;
    omp)         copy_file "$SKILL" "$DEST/.omp/skills/antitextai/SKILL.md" "omp skill" ;;
    cursor)      copy_file "$REPO_DIR/integrations/cursor/antitextai.mdc" "$DEST/.cursor/rules/antitextai.mdc" "Cursor project rule" ;;
    windsurf)    copy_file "$REPO_DIR/integrations/windsurf/antitextai.md" "$DEST/.windsurf/rules/antitextai.md" "Windsurf rule" ;;
    cline)       copy_file "$REPO_DIR/integrations/cline/antitextai.md" "$DEST/.clinerules/antitextai.md" "Cline rule" ;;
    aider)       copy_file "$REPO_DIR/integrations/aider/CONVENTIONS.md" "$DEST/CONVENTIONS.md" "Aider conventions" ;;
    copilot)     copy_file "$INSTRUCTION" "$DEST/.github/copilot-instructions.md" "Copilot repository instructions" ;;
    codex)       block_file "$REPO_DIR/integrations/codex/antitextai.md" "$(if [ "$GLOBAL" = 1 ]; then echo "$HOME/.codex/AGENTS.md"; else echo "$DEST/AGENTS.md"; fi)" "antitextai" "AGENTS.md readers (Codex and others)" ;;
    gemini)      block_file "$REPO_DIR/integrations/gemini/antitextai.md" "$(if [ "$GLOBAL" = 1 ]; then echo "$HOME/.gemini/GEMINI.md"; else echo "$DEST/GEMINI.md"; fi)" "antitextai" "Gemini CLI context" ;;
    qwen-code)   copy_file "$SKILL" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir qwen-code; else echo "$DEST/.qwen/skills/antitextai"; fi)/SKILL.md" "Qwen Code skill" ;;
    crush)       copy_file "$SKILL" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir crush; else echo "$DEST/.crush/skills/antitextai"; fi)/SKILL.md" "Crush skill" ;;
    kilo-code)   copy_file "$SKILL" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir kilo-code; else echo "$DEST/.kilo/skills/antitextai"; fi)/SKILL.md" "Kilo Code skill" ;;
    roo-code)    copy_file "$REPO_DIR/integrations/roo-code/antitextai.md" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir roo-code; else echo "$DEST/.roo/rules"; fi)/antitextai.md" "Roo Code rule" ;;
    goose)       copy_file "$REPO_DIR/integrations/goose/antitextai.md" "$(if [ "$GLOBAL" = 1 ]; then home_skill_dir goose; else echo "$DEST"; fi)/.goosehints" "goose hints" ;;
    warp)        if [ "$GLOBAL" = 1 ]; then block_file "$REPO_DIR/integrations/warp/WARP.md" "$HOME/.agents/AGENTS.md" "antitextai" "Warp global rules"; else copy_file "$REPO_DIR/integrations/warp/WARP.md" "$DEST/WARP.md" "Warp project rules"; fi ;;
    *) echo "unknown target: $tool" >&2; FAILED=$((FAILED+1)); return 0 ;;
  esac
}

IFS=',' read -r -a LIST <<< "$TARGETS"
for t in "${LIST[@]}"; do install_target "$(echo "$t" | tr -d ' ')"; done

echo
if command -v antitextai >/dev/null 2>&1; then
  echo "CLI on PATH: $(command -v antitextai)"
else
  echo "reminder: the skill tells an agent to run the tool. Either keep this clone and run"
  echo "          'python -m antitextai' from $REPO_DIR, or install the CLI system-wide:"
  echo "          pipx install \"git+https://github.com/satriazoid/antitextai\""
fi
[ "$FAILED" = 0 ] || { echo "$FAILED file(s) skipped; re-run with --force to overwrite." >&2; exit 1; }
