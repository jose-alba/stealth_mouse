# Stealth Mouse Agent Skills Installer for Windows (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "`n[*] Installing Stealth Mouse & Autonomous Navigation Skills..." -ForegroundColor Cyan

$AntigravitySkills = "$env:USERPROFILE\.gemini\config\skills"
$ClaudeSkills = "$env:USERPROFILE\.claude\skills"
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

# 1. Determine source directories
if ($ScriptDir -and (Test-Path "$ScriptDir\skills\screen-actor")) {
    $SourceSkills = "$ScriptDir\skills"
} else {
    Write-Host "[!] Could not locate local skills folder. Using current directory." -ForegroundColor Yellow
    $SourceSkills = ".\skills"
}

$CommonSource = "$SourceSkills\stealth_mouse_common"
$SkillsToInstall = @("goto", "screen-sense", "screen-actor", "flowchart")

# 2. Install to Google Antigravity
if (Test-Path "$env:USERPROFILE\.gemini") {
    Write-Host "[>] Deploying to Google Antigravity ($AntigravitySkills)..." -ForegroundColor Yellow

    # Install stealth_mouse_common globally
    New-Item -ItemType Directory -Force -Path "$AntigravitySkills\stealth_mouse_common" | Out-Null
    Copy-Item "$CommonSource\*" "$AntigravitySkills\stealth_mouse_common\" -Recurse -Force

    foreach ($skill in $SkillsToInstall) {
        $targetDir = "$AntigravitySkills\$skill"
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Copy-Item "$SourceSkills\$skill\*" "$targetDir\" -Recurse -Force

        # Distribute stealth_mouse_common inside skill's scripts folder for 100% self-contained execution
        if (Test-Path "$targetDir\scripts") {
            $destCommon = "$targetDir\scripts\stealth_mouse_common"
            New-Item -ItemType Directory -Force -Path $destCommon | Out-Null
            Copy-Item "$CommonSource\*" "$destCommon\" -Recurse -Force
        }
    }
    Write-Host " [OK] Successfully installed skills into Google Antigravity!" -ForegroundColor Green
}

# 3. Install to Claude Code (if present)
if (Test-Path "$env:USERPROFILE\.claude") {
    Write-Host "[>] Deploying to Claude Code ($ClaudeSkills)..." -ForegroundColor Yellow

    New-Item -ItemType Directory -Force -Path "$ClaudeSkills\stealth_mouse_common" | Out-Null
    Copy-Item "$CommonSource\*" "$ClaudeSkills\stealth_mouse_common\" -Recurse -Force

    foreach ($skill in $SkillsToInstall) {
        $targetDir = "$ClaudeSkills\$skill"
        New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        Copy-Item "$SourceSkills\$skill\*" "$targetDir\" -Recurse -Force

        if (Test-Path "$targetDir\scripts") {
            $destCommon = "$targetDir\scripts\stealth_mouse_common"
            New-Item -ItemType Directory -Force -Path $destCommon | Out-Null
            Copy-Item "$CommonSource\*" "$destCommon\" -Recurse -Force
        }
    }
    Write-Host " [OK] Successfully installed skills into Claude Code!" -ForegroundColor Green
}

Write-Host "`n[DONE] Installation complete!" -ForegroundColor Cyan
Write-Host "Available Agent Capabilities:" -ForegroundColor White
Write-Host "  - /goto: <prompt>  (Autonomous step planner & visual navigator)" -ForegroundColor White
Write-Host "  - screen-sense     (Screenshot capture, resolution & cursor tracker)" -ForegroundColor White
Write-Host "  - screen-actor     (Human-like mouse movement, clicks, drag & keyboard)" -ForegroundColor White
Write-Host "  - flowchart        (Standardized Mermaid diagram & architecture maker)" -ForegroundColor White

