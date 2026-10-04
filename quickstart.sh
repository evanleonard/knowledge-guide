#!/usr/bin/env bash
# ==============================================================================
# quickstart.sh - 1-Minute Antigravity & Knowledge Guide Quickstart
# ==============================================================================
# Automates environment setup, checks/installs Antigravity (Free Edition),
# verifies bundle integrity with presubmit, and launches the agent test drive.
# ==============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\n${BOLD}${CYAN}============================================================${NC}"
echo -e "${BOLD}${CYAN}   Google Antigravity + Knowledge Guide Quickstart 🚀       ${NC}"
echo -e "${BOLD}${CYAN}============================================================${NC}\n"

# 1. Run standard idempotent setup (environment, permissions, hooks, bundle test)
./setup.sh "$@"

# 2. Check for applications
HAS_ANTIGRAVITY=0
if [ -d "/Applications/Antigravity.app" ] || [ -d "$HOME/Applications/Antigravity.app" ]; then
    HAS_ANTIGRAVITY=1
elif command -v antigravity &>/dev/null; then
    HAS_ANTIGRAVITY=1
fi

HAS_OBSIDIAN=0
if [ -d "/Applications/Obsidian.app" ] || [ -d "$HOME/Applications/Obsidian.app" ]; then
    HAS_OBSIDIAN=1
elif command -v obsidian &>/dev/null; then
    HAS_OBSIDIAN=1
fi

# 3. Present the 4 Golden Test-Drive Prompts
echo -e "\n${BOLD}${CYAN}============================================================${NC}"
echo -e "${BOLD}${CYAN}   Ready for Testing! 4 Golden Prompts to Try               ${NC}"
echo -e "${BOLD}${CYAN}============================================================${NC}\n"
echo -e "In your Antigravity chat canvas, paste any of these prompts:\n"
echo -e "  ${BOLD}1. Domain Knowledge Retrieval:${NC}"
echo -e "     ${CYAN}/ask-kb What is the core architecture and purpose of this knowledge base?${NC}\n"
echo -e "  ${BOLD}2. Progressive Disclosure Exploration:${NC}"
echo -e "     ${CYAN}Summarize the core systems and ecosystem realities outlined in index.md${NC}\n"
echo -e "  ${BOLD}3. Autonomous Web Ingestion:${NC}"
echo -e "     ${CYAN}/ingest https://en.wikipedia.org/wiki/Virtue_ethics${NC}\n"
echo -e "  ${BOLD}4. Self-Healing Quality Gatekeeper:${NC}"
echo -e "     ${CYAN}Draft a new concept for an Autonomous Quality Auditor and verify with presubmit${NC}\n"
echo -e "------------------------------------------------------------"

if [ "$HAS_ANTIGRAVITY" -eq 1 ]; then
    if [ -t 0 ] && [ "${CI:-false}" != "true" ]; then
        echo -ne "\n${BOLD}Would you like to open this project in Antigravity now? [Y/n]: ${NC}"
        read -r launch_app || launch_app="y"
        if [[ "$launch_app" =~ ^[Yy]$ ]] || [ -z "$launch_app" ]; then
            echo -e "\n${GREEN}Opening Antigravity desktop application...${NC}\n"
            if [ -d "/Applications/Antigravity.app" ]; then
                open -a Antigravity "$SCRIPT_DIR"
            elif command -v antigravity &>/dev/null; then
                antigravity "$SCRIPT_DIR" &
            fi
        fi
    else
        echo -e "\nOpen this workspace in Antigravity with: ${BOLD}open -a Antigravity .${NC}"
    fi
else
    echo -e "\n${YELLOW}To install the free Antigravity desktop app:${NC}"
    echo -e "  • Download (.dmg):      ${BOLD}https://antigravity.google/download${NC}"
    echo -e "  • Or macOS Homebrew:    ${BOLD}brew install --cask antigravity${NC}\n"
fi

if [ "$HAS_OBSIDIAN" -eq 1 ]; then
    echo -e "  • Open in Obsidian:     ${BOLD}open -a Obsidian .${NC} (or open vault in Obsidian)\n"
fi
