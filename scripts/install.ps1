<#
antitextai installer: put SKILL.md and the per-tool rule files where your agent looks.

  pwsh scripts/install.ps1 -Target claude-code,opencode,cursor,copilot
  pwsh scripts/install.ps1 -Target all -Global -Force
  pwsh scripts/install.ps1 -Target hermes -Dest C:\path\to\project -DryRun

Project targets write into -Dest (default: the current directory).
-Global targets the user-level config of each tool. Hermes and omp have no global variant
here: pass the profile or skill directory as -Dest instead.
#>
param(
    [string[]]$Target = @(),
    [string]$Dest = (Get-Location).Path,
    [switch]$Global,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$RepoDir = Split-Path -Parent $PSScriptRoot
$Skill = Join-Path $RepoDir 'SKILL.md'
$Instruction = Join-Path $RepoDir 'integrations/copilot/copilot-instructions.md'
$BlockScript = Join-Path $RepoDir 'scripts/_block.py'
$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) { $Python = (Get-Command python3 -ErrorAction SilentlyContinue).Source }

$AllTargets = @('claude-code', 'opencode', 'agents', 'hermes', 'omp',
                'cursor', 'windsurf', 'cline', 'aider', 'copilot', 'codex', 'gemini')
if ($Target.Count -eq 1 -and $Target[0] -eq 'all') { $Target = $AllTargets }

if (-not (Test-Path $Skill)) { throw "SKILL.md not found next to this script; run it from the clone" }
if ($Target.Count -eq 0) { Write-Error 'no -Target given. Valid targets: ' -ErrorAction Continue; $AllTargets; exit 2 }

$script:Skipped = 0

function Copy-Rule([string]$Src, [string]$Dst, [string]$Label) {
    if ($DryRun) { Write-Host "would write $Dst"; return }
    $dir = Split-Path -Parent $Dst
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    if ((Test-Path $Dst) -and (-not $Force)) {
        if ((Get-FileHash $Src).Hash -eq (Get-FileHash $Dst).Hash) { Write-Host "up to date  $Dst"; return }
        Write-Warning "skipped     $Dst (exists and differs; use -Force)"
        $script:Skipped++
        return
    }
    Copy-Item -Path $Src -Destination $Dst -Force
    Write-Host "wrote       $Dst   ($Label)"
}

function Merge-InstrFile([string]$Dst, [string]$Label) {
    if (-not $Python) { Write-Warning "python not found; cannot merge into $Dst"; $script:Skipped++; return }
    if ($DryRun) {
        Write-Host "would merge the instruction block into $Dst"
        & $Python $BlockScript --file $Dst --source $Instruction --marker antitextai --dry-run | ForEach-Object { "    | $_" }
        return
    }
    $dir = Split-Path -Parent $Dst
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    & $Python $BlockScript --file $Dst --source $Instruction --marker antitextai | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Host "wrote       $Dst   ($Label)" }
    else { Write-Host "up to date  $Dst   ($Label)" }
}

function Home-SkillDir([string]$Tool) {
    switch ($Tool) {
        'claude-code' { Join-Path $HOME '.claude/skills/antitextai' }
        'opencode'    { Join-Path $HOME '.config/opencode/skills/antitextai' }
        'agents'      { Join-Path $HOME '.agents/skills/antitextai' }
        'hermes'      { Join-Path $(if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:LOCALAPPDATA 'hermes' }) 'skills/antitextai' }
        'omp'         { Join-Path $(if ($env:OMP_HOME) { $env:OMP_HOME } else { Join-Path $HOME '.omp' }) 'skills/antitextai' }
    }
}

foreach ($t in $Target) {
    switch ($t) {
        'claude-code' { $base = if ($Global) { Home-SkillDir 'claude-code' } else { Join-Path $Dest '.claude/skills/antitextai' }; Copy-Rule $Skill (Join-Path $base 'SKILL.md') 'Claude Code skill' }
        'opencode'    { $base = if ($Global) { Home-SkillDir 'opencode' } else { Join-Path $Dest '.opencode/skills/antitextai' }; Copy-Rule $Skill (Join-Path $base 'SKILL.md') 'opencode skill' }
        'agents'      { $base = if ($Global) { Home-SkillDir 'agents' } else { Join-Path $Dest '.agents/skills/antitextai' }; Copy-Rule $Skill (Join-Path $base 'SKILL.md') 'Agent Skills convention' }
        'hermes'      { Copy-Rule $Skill (Join-Path (Home-SkillDir 'hermes') 'SKILL.md') 'Hermes Agent skill' }
        'omp'         { Copy-Rule $Skill (Join-Path $Dest '.omp/skills/antitextai/SKILL.md') 'omp skill' }
        'cursor'      { Copy-Rule (Join-Path $RepoDir 'integrations/cursor/antitextai.mdc') (Join-Path $Dest '.cursor/rules/antitextai.mdc') 'Cursor project rule' }
        'windsurf'    { Copy-Rule (Join-Path $RepoDir 'integrations/windsurf/antitextai.md') (Join-Path $Dest '.windsurf/rules/antitextai.md') 'Windsurf rule' }
        'cline'       { Copy-Rule (Join-Path $RepoDir 'integrations/cline/antitextai.md') (Join-Path $Dest '.clinerules/antitextai.md') 'Cline rule' }
        'aider'       { Copy-Rule (Join-Path $RepoDir 'integrations/aider/CONVENTIONS.md') (Join-Path $Dest 'CONVENTIONS.md') 'Aider conventions' }
        'copilot'     { Copy-Rule $Instruction (Join-Path $Dest '.github/copilot-instructions.md') 'Copilot repository instructions' }
        'codex'       { $f = if ($Global) { Join-Path $HOME '.codex/AGENTS.md' } else { Join-Path $Dest 'AGENTS.md' }; Merge-InstrFile $f 'AGENTS.md readers (Codex and others)' }
        'gemini'      { $f = if ($Global) { Join-Path $HOME '.gemini/GEMINI.md' } else { Join-Path $Dest 'GEMINI.md' }; Merge-InstrFile $f 'Gemini CLI context' }
        default       { Write-Warning "unknown target: $t"; $script:Skipped++ }
    }
}

Write-Host ''
$cli = Get-Command antitextai -ErrorAction SilentlyContinue
if ($cli) {
    Write-Host "CLI on PATH: $($cli.Source)"
} else {
    Write-Host 'reminder: the skill tells an agent to run the tool. Either keep this clone and run'
    Write-Host "          'python -m antitextai' from $RepoDir, or install the CLI system-wide:"
    Write-Host '          pipx install "git+https://github.com/satriazoid/antitextai"'
}
if ($script:Skipped -gt 0) { Write-Warning "$script:Skipped file(s) skipped; re-run with -Force to overwrite."; exit 1 }
