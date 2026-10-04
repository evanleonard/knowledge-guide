#!/usr/bin/env bash
# ==============================================================================
# setup.sh - Environment Setup & Presubmit Hook Installer (OKF v0.2)
# ==============================================================================
# Verifies system prerequisites, installs Git pre-commit & pre-push hooks,
# configures AI agent discovery (.agents/skills.json), and executes a bundle
# self-test validation to ensure the knowledge base is fully self-maintaining.
# ==============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse optional flags early
INSTALL_DEPS=false
WITH_OBSIDIAN=""
INSTALL_OBSIDIAN=false

for arg in "$@"; do
    case "$arg" in
        --install-deps|-y|--yes)
            INSTALL_DEPS=true
            ;;
        --with-obsidian|--obsidian)
            WITH_OBSIDIAN="true"
            ;;
        --no-obsidian|--skip-obsidian)
            WITH_OBSIDIAN="false"
            ;;
        --install-obsidian)
            INSTALL_OBSIDIAN=true
            WITH_OBSIDIAN="true"
            ;;
        -h|--help)
            echo -e "${BOLD}Usage:${NC} ./setup.sh [OPTIONS]"
            echo -e "\n${BOLD}Options:${NC}"
            echo -e "  -y, --yes, --install-deps   Non-interactive mode, automatically install dependencies"
            echo -e "  --with-obsidian             Configure Obsidian vault settings and enable Antigravity plugin"
            echo -e "  --no-obsidian               Skip Obsidian checks and plugin configuration"
            echo -e "  --install-obsidian          Install Obsidian via Homebrew if not found"
            echo -e "  -h, --help                  Show this help message"
            exit 0
            ;;
    esac
done

echo -e "\n${BOLD}${BLUE}============================================================${NC}"
echo -e "${BOLD}${BLUE}  Knowledge Guide (OKF v0.2) Setup & Validation Checker     ${NC}"
echo -e "${BOLD}${BLUE}============================================================${NC}\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Detect Operating System
OS="$(uname -s)"
echo -e "${BLUE}[1/8]${NC} Detecting operating system: ${GREEN}$OS${NC}"

# 2. Check for Python 3 (Requirement: Python 3.8+)
echo -e "\n${BLUE}[2/8]${NC} Checking for Python 3 (required: >= 3.8)..."
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null && python --version 2>&1 | grep -q "Python 3"; then
    PYTHON_BIN="python"
fi

if [ -z "$PYTHON_BIN" ]; then
    echo -e "      ${RED}Error: Python 3 not found.${NC} Please install Python 3.8+."
    exit 1
fi

PY_VERSION="$($PYTHON_BIN -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
echo -e "      Found: ${GREEN}$PYTHON_BIN ($PY_VERSION)${NC}"

PY_CHECK="$($PYTHON_BIN -c 'import sys; print(1 if sys.version_info >= (3, 8) else 0)')"
if [ "$PY_CHECK" -ne 1 ]; then
    echo -e "      ${RED}Error:${NC} Python 3.8 or higher is required. Found $PY_VERSION."
    exit 1
fi

# Check optional libraries
YT_API_CHECK="$($PYTHON_BIN -c 'import youtube_transcript_api; print(1)' 2>/dev/null || echo 0)"
if [ "$YT_API_CHECK" -eq 1 ]; then
    echo -e "      ${GREEN}✓${NC} youtube-transcript-api installed (YouTube video ingestion enabled)"
else
    echo -e "      ${YELLOW}!${NC} youtube-transcript-api library not installed."
    DO_INSTALL=false
    if [ "$INSTALL_DEPS" = "true" ]; then
        DO_INSTALL=true
    elif [ -t 0 ] && [ "${CI:-false}" != "true" ]; then
        echo -ne "        Would you like to install youtube-transcript-api now? [Y/n]: "
        read -r reply || reply="y"
        if [[ "$reply" =~ ^[Yy]$ ]] || [ -z "$reply" ]; then
            DO_INSTALL=true
        fi
    fi

    if [ "$DO_INSTALL" = "true" ]; then
        echo -e "        Installing youtube-transcript-api via pip..."
        INSTALLED=0
        if $PYTHON_BIN -m pip install -r requirements.txt &>/dev/null; then
            INSTALLED=1
        elif $PYTHON_BIN -m pip install --user --break-system-packages -r requirements.txt &>/dev/null; then
            INSTALLED=1
        elif $PYTHON_BIN -m pip install --break-system-packages -r requirements.txt &>/dev/null; then
            INSTALLED=1
        elif command -v uv &>/dev/null && uv pip install --system -r requirements.txt &>/dev/null; then
            INSTALLED=1
        fi

        if [ "$INSTALLED" -eq 1 ]; then
            echo -e "        ${GREEN}✓${NC} youtube-transcript-api installed successfully!"
        else
            echo -e "        ${YELLOW}!${NC} Automatic install failed. Install manually:"
            echo -e "          • Standard pip:         ${BOLD}$PYTHON_BIN -m pip install -r requirements.txt${NC}"
            echo -e "          • macOS / Homebrew pip: ${BOLD}$PYTHON_BIN -m pip install --break-system-packages -r requirements.txt${NC}"
        fi
    else
        echo -e "        To enable YouTube video ingestion manually:"
        echo -e "          • Standard pip:         ${BOLD}$PYTHON_BIN -m pip install -r requirements.txt${NC}"
        echo -e "          • macOS / Homebrew pip: ${BOLD}$PYTHON_BIN -m pip install --break-system-packages -r requirements.txt${NC}"
    fi
fi

# 3. Check Version Control Tooling (Git / Jujutsu)
echo -e "\n${BLUE}[3/8]${NC} Checking version control tooling..."
if command -v git &>/dev/null; then
    GIT_VER="$(git --version)"
    echo -e "      ${GREEN}✓${NC} Git found: ${GREEN}$GIT_VER${NC}"
fi

if command -v jj &>/dev/null; then
    JJ_VER="$(jj version | head -n 1)"
    echo -e "      ${GREEN}✓${NC} Jujutsu (jj) found: ${GREEN}$JJ_VER${NC}"
else
    echo -e "      ${YELLOW}!${NC} Jujutsu (jj) optional modern VCS not detected."
fi

# 4. Check for Google Antigravity (Free Desktop Application)
echo -e "\n${BLUE}[4/8]${NC} Checking for Google Antigravity application..."
AGY_DETECTED=0
if [ -d "/Applications/Antigravity.app" ] || [ -d "$HOME/Applications/Antigravity.app" ]; then
    echo -e "      ${GREEN}✓${NC} Antigravity application found in /Applications"
    AGY_DETECTED=1
elif command -v antigravity &>/dev/null; then
    echo -e "      ${GREEN}✓${NC} Antigravity application found in PATH"
    AGY_DETECTED=1
fi

if [ "$AGY_DETECTED" -eq 0 ]; then
    echo -e "      ${YELLOW}!${NC} Antigravity application not detected."
    echo -e "        • Download Free App (.dmg): ${BOLD}https://antigravity.google/download${NC}"
    echo -e "        • macOS Homebrew:          ${BOLD}brew install --cask antigravity${NC}"
    if [ -t 0 ] && [ "${CI:-false}" != "true" ] && command -v brew &>/dev/null; then
        echo -ne "        Would you like to install Antigravity via Homebrew now? [y/N]: "
        read -r install_agy || install_agy="n"
        if [[ "$install_agy" =~ ^[Yy]$ ]]; then
            echo -e "        Installing Antigravity via Homebrew..."
            brew install --cask antigravity || true
            if [ -d "/Applications/Antigravity.app" ]; then
                echo -e "        ${GREEN}✓${NC} Antigravity installed successfully!"
            fi
        fi
    fi
fi

# 5. Check for Obsidian & Antigravity Obsidian Plugin (Optional)
echo -e "\n${BLUE}[5/8]${NC} Checking Obsidian & Antigravity plugin (optional)..."
if [ "$WITH_OBSIDIAN" = "false" ]; then
    echo -e "      ${YELLOW}!${NC} Skipped (--no-obsidian requested)"
else
    OBSIDIAN_DETECTED=0
    if [ -d "/Applications/Obsidian.app" ] || [ -d "$HOME/Applications/Obsidian.app" ]; then
        echo -e "      ${GREEN}✓${NC} Obsidian application found in /Applications"
        OBSIDIAN_DETECTED=1
    elif command -v obsidian &>/dev/null; then
        echo -e "      ${GREEN}✓${NC} Obsidian application found in PATH"
        OBSIDIAN_DETECTED=1
    fi

    if [ "$OBSIDIAN_DETECTED" -eq 0 ]; then
        echo -e "      ${YELLOW}!${NC} Obsidian application not detected (optional knowledge browser & graph viewer)."
        echo -e "        • Download Free App:   ${BOLD}https://obsidian.md/download${NC}"
        echo -e "        • macOS Homebrew:      ${BOLD}brew install --cask obsidian${NC}"

        DO_INSTALL_OBSIDIAN=false
        if [ "$INSTALL_OBSIDIAN" = "true" ]; then
            DO_INSTALL_OBSIDIAN=true
        elif [ -t 0 ] && [ "${CI:-false}" != "true" ] && command -v brew &>/dev/null; then
            echo -ne "        Would you like to install Obsidian via Homebrew now? [y/N]: "
            read -r reply_obsidian || reply_obsidian="n"
            if [[ "$reply_obsidian" =~ ^[Yy]$ ]]; then
                DO_INSTALL_OBSIDIAN=true
            fi
        fi

        if [ "$DO_INSTALL_OBSIDIAN" = "true" ] && command -v brew &>/dev/null; then
            echo -e "        Installing Obsidian via Homebrew..."
            brew install --cask obsidian || true
            if [ -d "/Applications/Obsidian.app" ] || [ -d "$HOME/Applications/Obsidian.app" ]; then
                OBSIDIAN_DETECTED=1
                echo -e "        ${GREEN}✓${NC} Obsidian installed successfully!"
            else
                echo -e "        ${YELLOW}!${NC} Obsidian installation did not complete."
            fi
        fi
    fi

    # Check plugin files
    PLUGIN_DIR=".obsidian/plugins/antigravity"
    if [ -f "$PLUGIN_DIR/manifest.json" ] && [ -f "$PLUGIN_DIR/main.js" ]; then
        echo -e "      ${GREEN}✓${NC} Antigravity Obsidian plugin files present ($PLUGIN_DIR)"
    else
        # Fallback copy from sibling guide if available
        FALLBACK_SRC=""
        if [ -d "../delta-guide/.obsidian/plugins/antigravity" ]; then
            FALLBACK_SRC="../delta-guide/.obsidian/plugins/antigravity"
        elif [ -d "../banda/guide/.obsidian/plugins/antigravity" ]; then
            FALLBACK_SRC="../banda/guide/.obsidian/plugins/antigravity"
        fi

        if [ -n "$FALLBACK_SRC" ] && [ -d "$FALLBACK_SRC" ]; then
            mkdir -p "$PLUGIN_DIR"
            cp -R "$FALLBACK_SRC"/* "$PLUGIN_DIR/" 2>/dev/null || true
            if [ -f "$PLUGIN_DIR/manifest.json" ]; then
                echo -e "      ${GREEN}✓${NC} Restored Antigravity Obsidian plugin files from local source"
            fi
        fi
    fi

    # Check if already registered in .obsidian/community-plugins.json
    ALREADY_ENABLED="$($PYTHON_BIN -c '
import json
from pathlib import Path
cfg = Path(".obsidian/community-plugins.json")
try:
    plugins = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else []
    print(1 if "antigravity" in plugins else 0)
except Exception:
    print(0)
' 2>/dev/null || echo 0)"

    if [ "$ALREADY_ENABLED" -eq 1 ]; then
        echo -e "      ${GREEN}✓${NC} Antigravity plugin already registered in .obsidian/community-plugins.json"
    else
        # Configure .obsidian/community-plugins.json
        ENABLE_PLUGIN=false
        if [ "$WITH_OBSIDIAN" = "true" ] || [ "$INSTALL_DEPS" = "true" ]; then
            ENABLE_PLUGIN=true
        elif [ "$OBSIDIAN_DETECTED" -eq 1 ]; then
            if [ -t 0 ] && [ "${CI:-false}" != "true" ]; then
                echo -ne "        Enable Antigravity plugin in Obsidian vault (.obsidian/community-plugins.json)? [Y/n]: "
                read -r reply_plugin || reply_plugin="y"
                if [[ "$reply_plugin" =~ ^[Yy]$ ]] || [ -z "$reply_plugin" ]; then
                    ENABLE_PLUGIN=true
                fi
            else
                # Non-interactive and Obsidian is detected: enable
                ENABLE_PLUGIN=true
            fi
        fi

        if [ "$ENABLE_PLUGIN" = "true" ]; then
            $PYTHON_BIN -c '
import json, sys
from pathlib import Path
cfg = Path(".obsidian/community-plugins.json")
try:
    plugins = json.loads(cfg.read_text(encoding="utf-8")) if cfg.exists() else []
    if not isinstance(plugins, list):
        plugins = []
    if "antigravity" not in plugins:
        plugins.append("antigravity")
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(plugins, indent=2) + "\n", encoding="utf-8")
        print("      \033[0;32m✓\033[0m Enabled Antigravity plugin in .obsidian/community-plugins.json")
    else:
        print("      \033[0;32m✓\033[0m Antigravity plugin already registered in .obsidian/community-plugins.json")
except Exception as e:
    print(f"      \033[1;33m!\033[0m Could not update community-plugins.json: {e}", file=sys.stderr)
' 2>/dev/null || true
        else
            echo -e "      ${YELLOW}!${NC} Antigravity plugin left unconfigured in community-plugins.json"
        fi
    fi
fi

# 6. Ensure Permissions on Maintenance and Skill Scripts & Install Git Hooks
echo -e "\n${BLUE}[6/8]${NC} Setting script permissions and configuring presubmit hooks..."
chmod +x init.sh 2>/dev/null || true
chmod +x quickstart.sh 2>/dev/null || true
if [ -d "scripts" ]; then
    chmod +x scripts/*.py 2>/dev/null || true
    echo -e "      ${GREEN}✓${NC} scripts/*.py are executable"
fi

if [ -d "skills" ]; then
    find skills -type f -name "*.py" -exec chmod +x {} + 2>/dev/null || true
    echo -e "      ${GREEN}✓${NC} skills/**/scripts/*.py are executable"
fi

# Configure Git hooks if .git directory exists
if [ -d ".git" ]; then
    mkdir -p .git/hooks

    # Install git pre-commit hook
    cat << 'EOF' > .git/hooks/pre-commit
#!/usr/bin/env bash
set -euo pipefail
GIT_DIR="$(git rev-parse --git-dir)"
REPO_ROOT="$(cd "$GIT_DIR/.." && pwd)"
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "ERROR: python3 not found. Presubmit hook cannot run." >&2
    exit 1
fi
exec "$PYTHON_BIN" "$REPO_ROOT/scripts/presubmit.py" "$REPO_ROOT"
EOF
    chmod +x .git/hooks/pre-commit

    # Install git pre-push hook
    cat << 'EOF' > .git/hooks/pre-push
#!/usr/bin/env bash
set -euo pipefail
GIT_DIR="$(git rev-parse --git-dir)"
REPO_ROOT="$(cd "$GIT_DIR/.." && pwd)"
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
    PYTHON_BIN="python"
else
    echo "ERROR: python3 not found. Presubmit hook cannot run." >&2
    exit 1
fi
exec "$PYTHON_BIN" "$REPO_ROOT/scripts/presubmit.py" "$REPO_ROOT"
EOF
    chmod +x .git/hooks/pre-push
    echo -e "      ${GREEN}✓${NC} Installed OKF presubmit hooks in .git/hooks/ (pre-commit, pre-push)"
else
    echo -e "      ${YELLOW}!${NC} .git directory not found (hooks will install when git init is run)"
fi

# 7. Verify Agent Discovery Configuration
echo -e "\n${BLUE}[7/8]${NC} Verifying AI agent workspace discovery configuration..."
mkdir -p .agents
if [ ! -f ".agents/skills.json" ]; then
    cat << 'EOF' > .agents/skills.json
{
  "skills": [
    { "path": "skills" }
  ]
}
EOF
    echo -e "      ${GREEN}✓${NC} Created .agents/skills.json"
else
    echo -e "      ${GREEN}✓${NC} .agents/skills.json exists"
fi

if [ -d "skills" ] && [ ! -e ".agents/skills" ]; then
    ln -sfn ../skills .agents/skills
    echo -e "      ${GREEN}✓${NC} Linked .agents/skills -> ../skills"
fi

# 8. Run Self-Test Validation & Re-indexing
echo -e "\n${BLUE}[8/8]${NC} Running self-test presubmit validation on OKF bundle..."
if $PYTHON_BIN scripts/presubmit.py; then
    echo -e "${BOLD}${GREEN}============================================================${NC}"
    echo -e "${BOLD}${GREEN}  Setup Complete! Knowledge Base is Operational & Verified   ${NC}"
    echo -e "${BOLD}${GREEN}============================================================${NC}"
    echo -e "\nQuick Run Commands:"
    echo -e "  • Launch Antigravity:  ${BOLD}open -a Antigravity .${NC} (or open folder in Antigravity app)"
    if [ -d "/Applications/Obsidian.app" ] || [ -d "$HOME/Applications/Obsidian.app" ]; then
        echo -e "  • Launch Obsidian:     ${BOLD}open -a Obsidian .${NC} (rich graph & vault browsing)"
    fi
    echo -e "  • Test Drive Prompts:  ${BOLD}cat playbooks/antigravity-test-drive.md${NC}"
    echo -e "  • Personalize / Brand: ${BOLD}./init.sh --org \"My Org\"${NC}"
    echo -e "  • Presubmit Check:     ${BOLD}./scripts/presubmit.py${NC} (auto-fix + validate)"
    echo -e "  • Validate Bundle:     ${BOLD}./scripts/validate.py${NC} (or ${BOLD}./scripts/validate.py --fix${NC})"
    echo -e "  • Refresh Index:       ${BOLD}./scripts/update_index.py${NC}"
    echo -e "  • Search Knowledge:    ${BOLD}./scripts/query_kb.py \"<query>\"${NC}\n"
    exit 0
else
    echo -e "\n${BOLD}${RED}Validation Failed. Please review errors above.${NC}\n"
    exit 1
fi
