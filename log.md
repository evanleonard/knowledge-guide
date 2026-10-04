# Knowledge Base Changelog

## 2026-10-04
* **Obsidian & Antigravity Plugin Integration**:
  - **Bundled Plugin**: Installed the Antigravity Obsidian plugin into [`.obsidian/plugins/antigravity`](/.obsidian/plugins/antigravity) and registered it in [`.obsidian/community-plugins.json`](/.obsidian/community-plugins.json) for instant out-of-the-box agentic vault intelligence.
  - **Fault-Tolerant Setup & Flexible Flags**: Enhanced [`setup.sh`](/setup.sh) and [`quickstart.sh`](/quickstart.sh) to detect Obsidian and configure the plugin with graceful opt-out flags (`--no-obsidian`), explicit opt-in (`--with-obsidian`), automated installation (`--install-obsidian`), and non-interactive safeguards.
  - **Documentation Updated**: Reflected Obsidian vault plugin integration in [`SETUP.md`](/SETUP.md) and [`README.md`](/README.md).
* **Plain Language Publishing, Sharing & Content Checking**:
  - **Publish & Share Engine**: Added [`scripts/publish_changes.py`](/scripts/publish_changes.py) translating everyday phrases like *"share my changes"*, *"publish my updates"*, *"save and share"*, *"push my notes"*, and *"publish this page"* into verified Git commits and pushes with presubmit gatekeeping and automatic conflict-free teammate sync.
  - **Content & Team Updates Checker**: Added [`scripts/check_changes.py`](/scripts/check_changes.py) providing non-technical inspection of collaborator commits on `origin/main`, local working drafts, and recent changelog additions in `log.md` without Git jargon.
  - **Skill Scope Demarcation**: Clarified [`skills/upgrade-guide`](/skills/upgrade-guide/SKILL.md) to trigger strictly on platform software/tooling upgrades from upstream, while [`skills/manage-knowledge-base`](/skills/manage-knowledge-base/SKILL.md) handles content changes and collaborative sharing.
* **Upstream Upgrade Engine & Skill Added**:
  - **Skill Created**: Implemented [`skills/upgrade-guide`](/skills/upgrade-guide/SKILL.md) enabling non-technical users to upgrade the knowledge base software, tooling, and skills by simply saying "upgrade the guide", "upgrade version", or "update system". Includes interactive confirmation modal (`ask_question`), zero-git-knowledge abstraction, automated dependency installation, and bundle re-verification. Registered `/upgrade-guide` in [`AGENTS.md`](/AGENTS.md) and [`SETUP.md`](/SETUP.md).
  - **Automated Sync Engine**: Developed [`scripts/upgrade_guide.py`](/scripts/upgrade_guide.py) with `--check` preview and `--apply` safe update mechanisms, safeguarding uncommitted local drafts via stash, preserving local configurations (`knowledge.config.json`), running `setup.sh` to install new dependencies, and executing presubmit validation.
* **YouTube Video & Transcript Ingestion**:
  - **Transcript Extraction Tooling**: Added [`skills/ingest/scripts/fetch_youtube_transcript.py`](/skills/ingest/scripts/fetch_youtube_transcript.py) powered by `youtube-transcript-api`, supporting full URL/ID parsing, public oEmbed metadata extraction (title, channel, URL, duration), language priority selection, and timestamped paragraph chunking.
  - **Integrated Web & Video Fetcher**: Enhanced [`skills/ingest/scripts/fetch_content.py`](/skills/ingest/scripts/fetch_content.py) to automatically route YouTube URLs to the transcript extractor and format video metadata.
  - **Ingest Skill Workflow**: Updated [`skills/ingest/SKILL.md`](/skills/ingest/SKILL.md) with YouTube invocation triggers, classification guidance (tech talks $\rightarrow$ concepts/systems, customer interviews $\rightarrow$ research, tutorials $\rightarrow$ playbooks), and structural guidelines.
  - **Video Authoring Template**: Added [`skills/ingest/templates/ingested-youtube-template.md`](/skills/ingest/templates/ingested-youtube-template.md) for structuring video metadata, speaker attribution, agenda tables, and transcript excerpts.
  - **Environment & Setup Verification**: Updated [`setup.sh`](/setup.sh) to detect `youtube-transcript-api`, and updated [`SETUP.md`](/SETUP.md) and [`README.md`](/README.md).

## 2026-10-02
* **Concept Pages, Linking & Interactive Graph Engine**:
  - **Relational Edge Architecture**: Enhanced [`templates/concept-template.md`](/templates/concept-template.md) and [`skills/manage-knowledge-base/templates/concept_template.md`](/skills/manage-knowledge-base/templates/concept_template.md) with standardized `## 2. Conceptual Mind Map & Relational Edges` (Mermaid) and `## 6. Relational Edge Index` tables.
  - **Thematic Cluster Matrix**: Created exemplary cluster [`concepts/cluster-intelligent-automation.md`](/concepts/cluster-intelligent-automation.md) and linked concept nodes [`concepts/future-initiative.md`](/concepts/future-initiative.md) and [`concepts/predictive-dispatch.md`](/concepts/predictive-dispatch.md).
  - **Graph Compiler**: Added [`scripts/compile_graph.py`](/scripts/compile_graph.py) to compile concept nodes, clusters, and typed relational edges into [`viewer/graph-data.json`](/viewer/graph-data.json), integrated directly into presubmit.
  - **Interactive SPA Viewer & Design Spec**: Added [`scripts/build_viewer.py`](/scripts/build_viewer.py), standalone [`viewer/index.html`](/viewer/index.html), and [`DESIGN.md`](/DESIGN.md) visual design specification.
* **Antigravity Quickstart & Test Drive**: Added automated [`quickstart.sh`](/quickstart.sh), enhanced [`setup.sh`](/setup.sh) with Antigravity desktop application detection and installation prompts, authored [`playbooks/antigravity-test-drive.md`](/playbooks/antigravity-test-drive.md), and expanded [`README.md`](/README.md) and [`SETUP.md`](/SETUP.md) with 3-minute test drive guides and the 4 Golden Prompts.

## 2026-10-01
* **Source Retraction & Decoupler Engine**: Added [`scripts/backout_source.py`](/scripts/backout_source.py), [`scripts/backout_institution.py`](/scripts/backout_institution.py), [`scripts/reincorporate_source.py`](/scripts/reincorporate_source.py), and autonomous agent skills [`/backout-source`](/skills/backout-source/SKILL.md) and [`/backout-institution`](/skills/backout-institution/SKILL.md) for safely auditing, retracting, archiving, substituting, and restoring external sources and institutional containers.
* **Concept Graph & Relational Edge Engine**: Enhanced [`scripts/validate.py`](/scripts/validate.py) with `validate_concept_graph()` to verify cluster membership, typed relational edges, and source provenance, while exempting `archive/` and hidden directories from presubmit.
* **Ontology & Taxonomy Demarcation**: Formally expanded OKF layout into a 3-tier ontological separation: "What Is" (`/systems/`, `/ecosystem/`, `/ecosystem/institutions/`), "Theoretical Frameworks" (`/concepts/`), and "What Could Be" (`/frontier/`, `/storyboards/`).
* **Authoring Templates & Observatories**: Added [`templates/concept-cluster-template.md`](/templates/concept-cluster-template.md), [`templates/frontier-template.md`](/templates/frontier-template.md), and [`templates/institution-template.md`](/templates/institution-template.md).
* **Obsidian Graph Optimization**: Added [`.obsidian/graph.json`](/.obsidian/graph.json) with tuned graph physics for knowledge base visualization.

## 2026-09-30
* **Storyboarding Skill**: Added [`/generate-storyboards`](/skills/generate-storyboards/SKILL.md) skill, [`templates/storyboard-template.md`](/templates/storyboard-template.md), and [`playbooks/generating-product-storyboards.md`](/playbooks/generating-product-storyboards.md) for authoring sequential visual storyboards and product concept specifications.

## 2026-09-26
* **Agent Guidelines**: Added [`AGENTS.md`](/AGENTS.md) repository-wide operating contract for autonomous AI agents.
* **Knowledge Advisor Skill**: Added [`/ask-kb`](/skills/ask-kb/SKILL.md) and [`scripts/query_kb.py`](/scripts/query_kb.py) CLI & programmatic search tool.
* **Knowledge-Driven Engineering**: Added [`playbooks/knowledge-driven-engineering.md`](/playbooks/knowledge-driven-engineering.md) defining spec-driven development, AI pair programming, compliance PR reviews, and concept graduation.
* **Repository Initialized**: Extracted self-contained, self-maintaining knowledge base template conforming to Google OKF v0.2.
* **Architecture Groundwork**: Established core taxonomies across `/systems/`, `/ecosystem/`, `/concepts/`, `/playbooks/`, `/research/`, and `/references/`.
* **Tooling Configured**: Automated presubmit gatekeeper, bundle validator, and dynamic index generator verified.
