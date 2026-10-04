---
type: Playbook
title: "Knowledge Guide Setup & Onboarding Guide (Human & AI Agent Instructions)"
description: "Idempotent, step-by-step instructions for humans and autonomous AI agents to clone, configure, personalize, and verify the OKF v0.2 knowledge base."
tags: [setup, onboarding, agent-instructions, okf, knowledge-guide]
status: stable
generated:
  by: agent:antigravity
  at: 2026-09-26T00:00:00Z
verified:
  - by: human:architecture-lead
    at: 2026-09-26T00:00:00Z
sources:
  - "/setup.sh"
  - "/scripts/presubmit.py"
  - "/scripts/validate.py"
---

# Knowledge Guide — Setup & Verification Guide

> [!IMPORTANT]
> **For AI Agents**: If your user instructed you to *"set this up <url>"*, proceed directly to the [🤖 Autonomous Agent Instructions](#-autonomous-agent-instructions) section below. Follow each bash block sequentially, verify that the bundle passes validation, and confirm readiness to your user.

---

## 🌍 Overview

This repository is a turnkey, self-contained, and self-maintaining knowledge base template structured according to the **Google Open Knowledge Format (OKF v0.2)**. It provides organizations with a standardized, audit-ready architecture for managing institutional knowledge with both human engineers and autonomous AI agents.

The repository strictly demarcates:
1. **"What Is" (Current Reality)**:
   * External environment, laws, partner platforms, and third-party rails (`ecosystem/`).
   * Active production software, services, database schemas, and workflows (`systems/`).
2. **"What Could Be" (Proposals & Innovations)**:
   * Product concepts, feature proposals, and architectural RFCs (`concepts/`).
3. **"How To" & Ground Truth**:
   * Operational runbooks and developer setup procedures (`playbooks/`).
   * Field research, customer interviews, and user feedback (`research/`).
   * Formal specifications and audit provenance (`references/`).

---

## 🤖 Autonomous Agent Instructions

When an AI coding assistant (Antigravity, Claude Code, Cursor, Copilot, Cline, Aider, Devin, etc.) is asked to set up this knowledge base, execute the following steps in order:

### Step 1: Clone the Repository
Run the following command to clone the knowledge base into the workspace:

```bash
git clone <repository_url>
cd knowledge-guide
```

---

### Step 2: Personalize for Your Organization (Optional)
If setting up for a specific organization or company, brand the repository with a single command:

```bash
./init.sh --org "My Organization" --title "My Organization Knowledge Guide"
```
*(This automatically updates `knowledge.config.json`, adjusts README/SETUP headers, regenerates `index.md`, and runs self-test validation.)*

---

### Step 3: Run Automated Environment Setup
The repository includes an idempotent setup script that verifies prerequisites, configures permissions, installs Git presubmit hooks, links agent skills, and runs a bundle self-test:

```bash
./setup.sh
```

**What `./setup.sh` handles automatically:**
1. **OS Detection**: Detects macOS or Linux.
2. **Python 3 & Dependency Check**: Confirms Python 3.8+ is installed and prompts/installs optional dependencies from `requirements.txt` (including `youtube-transcript-api` for YouTube video transcript ingestion, with automatic PEP 668 `--break-system-packages` handling; pass `-y` to auto-install non-interactively).
3. **VCS Tooling Audit**: Detects Git and Jujutsu (`jj`).
4. **Permissions & Git Hooks**:
   * Sets executable permissions (`chmod +x`) on all maintenance and skill scripts.
   * Installs pre-commit and pre-push presubmit hooks in `.git/hooks/` to gatekeep commits.
5. **Agent Discovery**: Creates `.agents/skills.json` and symlinks the `manage-knowledge-base` and `ingest` skills into `.agents/skills`.
6. **Self-Test Validation**: Runs `scripts/presubmit.py` with auto-fix enabled to verify bundle health.

---

### Step 4: Verification Checks
Verify that the setup succeeded by confirming the following 3 checks:

```bash
# 1. Run the bundle presubmit validator
python3 scripts/presubmit.py
# Expected output: "Result: PASSED ✅ (Fully conformant with OKF v0.2)"

# 2. Verify agent skill configuration exists
test -f .agents/skills.json && echo "✓ Agent discovery configured"

# 3. Verify git presubmit hooks are executable
test -x .git/hooks/pre-commit && test -x .git/hooks/pre-push && echo "✓ Presubmit hooks installed"
```

If all three checks output green checkmarks / pass, report to the user:
> *"Knowledge Base has been successfully set up and verified. OKF v0.2 validation passed with 0 errors. Presubmit hooks and agent skills are registered."*

---

## 👤 Human Quickstart Guide

If you are a human setting up the repository manually:

### 1. Prerequisites
Ensure you have the following installed on your machine:
* **Python 3.8+** (`python3 --version`)
* **Git 2.20+** (`git --version`)
* *(Recommended)* **Google Antigravity (Free Desktop Application)**:
  * Direct installer: [antigravity.google/download](https://antigravity.google/download)
  * macOS Homebrew: `brew install --cask antigravity`
* *(Optional)* **Jujutsu (jj)**: A modern Git-compatible version control tool (`brew install jj` or `cargo install jujutsu`).
* *(Optional)* **Obsidian**: For rich graph visualization and knowledge browsing. `setup.sh` automatically detects Obsidian and configures the Antigravity Obsidian plugin (`.obsidian/plugins/antigravity`). Use `--no-obsidian` to skip Obsidian setup.

### 2. Single-Command Setup & Test Drive
```bash
git clone https://github.com/evanleonard/knowledge-guide.git
cd knowledge-guide
./quickstart.sh
```
*(Or open the Antigravity desktop app or Obsidian and choose **Open Project / Open Vault** $\rightarrow$ `knowledge-guide`)*

#### Optional Setup Flags
```bash
./setup.sh --help               # Show all options
./setup.sh -y                   # Non-interactive automated install
./setup.sh --no-obsidian        # Skip Obsidian checks and plugin configuration
./setup.sh --with-obsidian      # Ensure Obsidian integration and Antigravity plugin are enabled
./setup.sh --install-obsidian   # Auto-install Obsidian via Homebrew if missing
```

---

## 🛠️ Maintenance & Presubmit Gatekeeper

The knowledge base is **self-healing and self-maintaining**:

### The Presubmit Hook (`scripts/presubmit.py`)
A gatekeeper script that runs before any commit or push:
* **Auto-generates Frontmatter**: If you create a new `.md` file without frontmatter, the hook infers the document type, title, and description, and injects compliant OKF v0.2 frontmatter (`type`, `status: draft`, `generated`, `verified`).
* **Repairs Schema Errors**: Adds missing fields and normalizes invalid statuses.
* **Repairs Links**: Automatically adds missing `.md` extensions or fixes malformed relative paths to bundle resources.
* **Synchronizes Root Index**: Re-indexes all concepts in `index.md` based on `knowledge.config.json`.
* **Automatic Staging**: During `git commit`, any auto-fixed files are staged with `git add` automatically.

```bash
# Run presubmit manual check (auto-fix + validate):
./scripts/presubmit.py

# Or run validator directly with auto-fix flag:
python3 scripts/validate.py --fix
```

### Upstream Upgrades & Sync (`scripts/upgrade_guide.py`)
Non-technical team members can upgrade the knowledge base software, tooling, and skills at any time without touching git:
* **In Antigravity Chat**: Just say *"upgrade the guide"*, *"upgrade version"*, or *"update system"*. The agent will check for updates, ask for confirmation, and apply everything cleanly.
* **Via Terminal**:
  ```bash
  # Check for upstream updates:
  ./scripts/upgrade_guide.py --check

  # Apply updates and install new dependencies:
  ./scripts/upgrade_guide.py --apply
  ```


---

## 🧭 How to Work With the Knowledge Base

### 1. Reading & Exploring (Progressive Disclosure)
* **Always begin at `index.md`**. Do not scan every file at once; read the categorized one-line summaries first.
* Follow bundle-relative links: links starting with `/` (e.g. `/systems/core-architecture.md`) resolve relative to the bundle root.

### 2. Authoring New Concepts
Every concept document must reside in the correct folder:
* External partner or regulatory environment $\rightarrow$ `ecosystem/` (`status: stable`)
* Existing production software & architecture $\rightarrow$ `systems/` (`status: stable`)
* Future feature ideas or architectural RFCs $\rightarrow$ `concepts/` (`status: draft`)
* Standard operating procedures & guides $\rightarrow$ `playbooks/` (`status: stable`)
* User research notes & interviews $\rightarrow$ `research/` (`status: stable`)

### 3. Ingesting Web Content & YouTube Videos
To add external articles, regulatory documents, API documentation, or YouTube videos:
* Say to your agent: `ingest <URL>` or `ingest <YouTube_URL>`
* For standard web pages, the agent extracts clean markdown and metadata.
* For YouTube videos (requires `pip install youtube-transcript-api`), the agent extracts timestamped transcripts, channel attribution, duration, and video descriptions.
* The agent asks you where to place it via an interactive prompt, formats an OKF v0.2 document, updates `index.md` and `log.md`, and validates the bundle!
