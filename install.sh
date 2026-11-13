#!/usr/bin/env bash
set -e

echo -e "\n\033[36m[*] Installing Stealth Mouse & Autonomous Navigation Skills...\033[0m"

ANTIGRAVITY_SKILLS="$HOME/.gemini/config/skills"
CLAUDE_SKILLS="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SKILLS="$SCRIPT_DIR/skills"
COMMON_SOURCE="$SOURCE_SKILLS/stealth_mouse_common"
SKILLS=("goto" "screen-sense" "screen-actor" "flowchart")

# 1. Antigravity
if [ -d "$HOME/.gemini" ]; then
    echo -e "\033[33m[>] Deploying to Google Antigravity ($ANTIGRAVITY_SKILLS)...\033[0m"
    mkdir -p "$ANTIGRAVITY_SKILLS/stealth_mouse_common"
    cp -r "$COMMON_SOURCE/"* "$ANTIGRAVITY_SKILLS/stealth_mouse_common/"

    for skill in "${SKILLS[@]}"; do
        target="$ANTIGRAVITY_SKILLS/$skill"
        mkdir -p "$target"
        cp -r "$SOURCE_SKILLS/$skill/"* "$target/"
        if [ -d "$target/scripts" ]; then
            mkdir -p "$target/scripts/stealth_mouse_common"
            cp -r "$COMMON_SOURCE/"* "$target/scripts/stealth_mouse_common/"
        fi
    done
    echo -e " \033[32m[OK] Successfully installed into Google Antigravity!\033[0m"
fi

# 2. Claude Code
if [ -d "$HOME/.claude" ]; then
    echo -e "\033[33m[>] Deploying to Claude Code ($CLAUDE_SKILLS)...\033[0m"
    mkdir -p "$CLAUDE_SKILLS/stealth_mouse_common"
    cp -r "$COMMON_SOURCE/"* "$CLAUDE_SKILLS/stealth_mouse_common/"

    for skill in "${SKILLS[@]}"; do
        target="$CLAUDE_SKILLS/$skill"
        mkdir -p "$target"
        cp -r "$SOURCE_SKILLS/$skill/"* "$target/"
        if [ -d "$target/scripts" ]; then
            mkdir -p "$target/scripts/stealth_mouse_common"
            cp -r "$COMMON_SOURCE/"* "$target/scripts/stealth_mouse_common/"
        fi
    done
    echo -e " \033[32m[OK] Successfully installed into Claude Code!\033[0m"
fi

echo -e "\n\033[36m[DONE] Installation complete!\033[0m"

