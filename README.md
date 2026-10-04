---
type: Overview
title: "Knowledge Guide Starter Template (Google OKF v0.2)"
description: "A turnkey, self-contained, and self-maintaining knowledge base template for engineering, product, and operational teams."
tags: [readme, overview, template, okf, llm-wiki, agentic-docs]
status: stable
generated:
  by: agent:antigravity
  at: 2026-09-26T00:00:00Z
verified:
  - by: human:architecture-lead
    at: 2026-09-26T00:00:00Z
---

# Knowledge Guide Starter Template (Google OKF v0.2)

A production-grade, turnkey template for creating a **self-contained, self-healing, and self-maintaining knowledge base** for any organization. Adheres strictly to the **Google Cloud Open Knowledge Format (OKF v0.2)** standard.

Designed from the ground up for seamless collaboration between **human engineering teams** and **autonomous AI coding agents** (Antigravity, Claude Code, Cursor, Copilot, Cline, Aider, Devin).

---

## ⚡ Why This Knowledge Base Architecture Works

Traditional wikis (Confluence, Notion, Google Docs) fail for software teams because they drift from code, require proprietary sync pipelines, and confuse active reality with speculative proposals.

This template solves that by implementing the **Open Knowledge Format (OKF v0.2)** pattern:

1. **Zero External Dependencies**: Powered entirely by the Python 3 standard library and Git. No databases, vector stores, Node.js runtimes, or pip dependencies required.
2. **Self-Healing Presubmit Gatekeeper**: Git pre-commit and pre-push hooks automatically generate missing frontmatter, normalize statuses, fix broken relative links, synchronize `index.md`, and auto-stage repaired files.
3. **Architectural Demarcation**:
   * **"What Is"**: Operational reality, external regulations (`/ecosystem/`), and active production software (`/systems/`) with `status: stable`.
   * **"What Could Be"**: Future feature proposals and architectural RFCs (`/concepts/`) with `status: draft`.
   * **"How To" & Provenance**: Operational runbooks (`/playbooks/`), customer research (`/research/`), and standards (`/references/`).
4. **Progressive Disclosure**: Built for LLM context efficiency. Agents read [`index.md`](file:///index.md) first to scan categorized one-line summaries before traversing deep files.
5. **Living Agent Operating Contract**: Includes [`AGENTS.md`](file:///AGENTS.md) at repository root to govern autonomous AI agent interactions, non-negotiable compliance rules, and ground truth resolution.
6. **Turnkey AI Agent Skills**: Ships with built-in agent capabilities:
   * **`ask-kb`**: Instant architectural and domain consulting (`/ask-kb <query>` or CLI `python3 scripts/query_kb.py "<query>"`).
   * **`manage-knowledge-base`**: Standardized protocols for AI agents to navigate, author, update, and audit knowledge.
   * **`ingest`**: Command any AI agent to `ingest <URL>` or `ingest <YouTube_URL>`—it fetches web pages or YouTube video transcripts (via `youtube-transcript-api`), consults with you on placement, formats an OKF v0.2 document, and validates the bundle.
   * **`backout-source` & `backout-institution`**: Safely retract, substitute, or archive any external source, paper, or institutional container, evaluating concept grounding blast radius and cleaning reciprocal edges.
   * **`generate-storyboards`**: Author multi-panel visual storyboards and product concept specifications with export tools.
7. **Concept Graph & Relational Edge Validation**: Pre-configured presubmit hooks validate thematic cluster membership, typed relational edge matrices (*Grounds*, *Requires*, *Opposes*, *Operationalized as*, etc.), and primary external source provenance.

---

## ⚡ 3-Minute Antigravity Quickstart & Test Drive

Interact with the knowledge base inside the free **Google Antigravity** desktop application:

### 1. Install Google Antigravity (Free Desktop App)
* **Direct Download**: Download the installer from [antigravity.google/download](https://antigravity.google/download) and sign in with any Google account.
* **Or via Homebrew (macOS)**:
  ```bash
  brew install --cask antigravity
  ```

### 2. Clone & Open Repository
```bash
git clone https://github.com/evanleonard/knowledge-guide.git my-guide
cd my-guide && ./quickstart.sh
```
*(Or open the Antigravity desktop app and select **Open Project** $\rightarrow$ `my-guide`)*

Antigravity automatically discovers the registered agent skills in `.agents/skills` and the operating contract in [`AGENTS.md`](file:///AGENTS.md).

### 🎯 4 Golden Prompts to Test the Skills & Knowledge

In your Antigravity chat window, paste any of these prompts to test the agent capabilities:

| Capability | Prompt to Send Antigravity | What It Tests |
| :--- | :--- | :--- |
| **Domain Knowledge Retrieval** | `/ask-kb What is the core architecture and purpose of this knowledge base?` | Tests vectorless keyword search via `query_kb.py` and synthesis from `/systems/core-architecture.md`. |
| **Progressive Disclosure** | `Summarize the high-level ecosystem realities and production systems in index.md` | Tests efficient navigation of the root OKF index without context bloating. |
| **Autonomous Web Ingestion** | `/ingest https://en.wikipedia.org/wiki/Virtue_ethics` | Tests autonomous web fetching, interactive category placement, and OKF formatting. |
| **Self-Healing Quality Gatekeeper** | `Draft a new concept for an Autonomous Quality Auditor and verify with presubmit` | Tests the `scripts/presubmit.py` gatekeeper, frontmatter generation, and graph validation. |

*See [`playbooks/antigravity-test-drive.md`](file:///playbooks/antigravity-test-drive.md) for full walkthrough details.*

---

## 🚀 Quickstart: Setting Up a New Organization in 30 Seconds

### 1. Clone or Template
Clone this repository to your machine or workspace:
```bash
git clone <repository_url> my-org-guide
cd my-org-guide
```

### 2. Personalize / Brand for Your Organization
Run the single-command branding script:
```bash
./init.sh --org "Acme Health" --title "Acme Knowledge Base"
```
*(Interactively prompts for details if arguments are omitted. Configures `knowledge.config.json`, updates headers, rebuilds the index, and validates.)*

### 3. Run Automated Environment Setup
Installs Git presubmit hooks, verifies permissions, registers agent discovery, and runs self-test validation:
```bash
./setup.sh
```

---

## 🧭 Repository Structure

```text
knowledge-guide/
├── index.md                 # Root OKF index (progressive disclosure entry point)
├── log.md                   # Chronological update history (ISO 8601 YYYY-MM-DD)
├── AGENTS.md                # AI Agent Guidelines & Operating Contract
├── knowledge.config.json    # Organization name, title, and category mappings
├── init.sh                  # Interactive organization customizer
├── setup.sh                 # Environment setup and Git presubmit hook installer
├── SETUP.md                 # Autonomous AI agent and human onboarding runbook
│
├── 🏛️ ecosystem/            # "WHAT IS" - External Reality, Regulators & Partner Rails
│   ├── institutions/        # External research institutes, frontier labs & standards bodies
│   └── industry-landscape.md
│
├── 💻 systems/              # "WHAT IS" - Active Production Architecture & Services
│   └── core-architecture.md
│
├── 💡 concepts/             # Theoretical Concepts, Architectural Models & Thematic Clusters
│   └── future-initiative.md
│
├── 🚀 frontier/             # "WHAT COULD BE" - Horizon Scanning, Emerging Prototypes & Experiments
│   └── .gitkeep
│
├── 🎨 storyboards/          # "WHAT COULD BE" - Visual Storyboards & Sequential User Journeys
│
├── 📋 playbooks/            # Operational Runbooks, Setup Guides & SOPs
│   ├── onboarding-guide.md
│   ├── knowledge-driven-engineering.md
│   └── generating-product-storyboards.md
│
├── 🎙️ research/             # Customer Interviews, Field Observations & User Research
│   └── user-interview-example.md
│
├── 📖 references/           # Specifications, Schemas, Lineage & Standards
│   ├── okf-specification.md
│   └── provenance.md
│
├── 🛠️ scripts/              # Self-contained Python stdlib maintenance tools
│   ├── init_repo.py         # Org customizer / parameterizer
│   ├── presubmit.py         # Pre-commit & pre-push hook gatekeeper
│   ├── update_index.py      # Dynamic category-aware index generator
│   ├── query_kb.py          # Fast CLI keyword & relevance search tool
│   ├── validate.py          # OKF v0.2 schema, graph integrity & provenance validator
│   ├── backout_source.py    # Universal source retraction & archival engine
│   ├── backout_institution.py # Institutional container backout wrapper
│   └── reincorporate_source.py # Archive inspection & reincorporation engine
│
├── 🤖 skills/               # Reusable AI Agent Skills (.agents/skills)
│   ├── ask-kb/              # /ask-kb instant domain & architectural consulting
│   ├── manage-knowledge-base/ # Maintenance, authoring, and concept cluster management
│   ├── ingest/              # /ingest external URLs, YouTube transcripts & portals
│   ├── generate-storyboards/ # Visual storyboards and product concept specifications
│   ├── backout-source/      # /backout-source retraction, archival & substitution
│   └── backout-institution/ # /backout-institution institutional decoupling
│
├── 🧩 templates/            # Authoring starter templates
│   ├── concept-template.md
│   ├── concept-cluster-template.md
│   ├── ecosystem-template.md
│   ├── frontier-template.md
│   ├── institution-template.md
│   ├── playbook-template.md
│   ├── reference-template.md
│   ├── research-template.md
│   ├── storyboard-template.md
│   └── system-template.md
│
└── 🔮 .obsidian/            # Pre-configured Obsidian vault settings (Graph view)
```

---

## 🛠️ Maintenance Commands

All tools are standalone and require only standard Python 3.8+:

```bash
# 1. Run Presubmit Gatekeeper (auto-repairs frontmatter/links, rebuilds index, validates)
./scripts/presubmit.py

# 2. Search Knowledge Base via CLI
python3 scripts/query_kb.py "caching architecture"

# 3. Run Validator directly (with --fix to auto-repair issues)
python3 scripts/validate.py --fix

# 4. Retract a source and archive ungrounded concepts
python3 scripts/backout_source.py --target "source:paper-id" --action prune

# 5. Audit grounding blast radius without mutating files
python3 scripts/backout_source.py --target "source:paper-id" --dry-run

# 6. List and reincorporate archived sources
python3 scripts/reincorporate_source.py --list
python3 scripts/reincorporate_source.py --archive <archive-id>

# 7. Synchronize Root index.md from all concept files
python3 scripts/update_index.py

# 8. Ingest external documentation via AI agent
# In chat: "ingest https://example.com/api-spec"
```

---

## 📝 OKF v0.2 Frontmatter Contract

Every document in the knowledge base (except `log.md` and subdirectory `index.md`) begins with standard YAML frontmatter:

```yaml
---
type: System Component       # REQUIRED: e.g. Concept, Playbook, System Component
title: "Service Architecture" # Recommended: Human-readable title
description: "One-line summary for progressive disclosure index."
tags: [architecture, backend] # Optional: Tag list
status: stable               # Optional: draft | stable | deprecated (default: stable)
stale_after: 2027-01-01T00:00:00Z # Optional: Expiration threshold
generated:                   # Optional: Production metadata
  by: agent:antigravity
  at: 2026-09-26T00:00:00Z
verified:                    # Optional: Trust and audit events
  - by: human:architecture-lead
    at: 2026-09-26T00:00:00Z
sources:                     # Optional: Provenance citations
  - id: source:github-repo
    resource: https://github.com/my-org/my-service
    title: "Production Service Repository"
---
```

---

## 🌐 Obsidian Integration

This repository is ready to open directly in [Obsidian](https://obsidian.md/):
* `.obsidian/app.json` is configured for standard markdown links (`useMarkdownLinks: true`).
* `.obsidian/plugins/antigravity` provides autonomous vault management and agentic intelligence inside Obsidian.
* `.obsidian/community-plugins.json` is configured with `antigravity` and `obsidian-git`.
* Interactive graph view visualizes cross-references between `/systems/`, `/ecosystem/`, and `/concepts/` out of the box.
* Supported by `./setup.sh` with flexible flags (`--with-obsidian`, `--no-obsidian`).

---

## 📜 Specification & License

* Conforms to the [Google Cloud Open Knowledge Format (OKF v0.2)](https://github.com/GoogleCloudPlatform/open-knowledge-format).
* Freely reusable and distributable under Apache 2.0 / MIT.
