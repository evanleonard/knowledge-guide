---
type: Playbook
title: "Generating Audio Overviews & Podcasts Playbook"
description: "Standard operating procedure for authoring NotebookLM-style two-host audio overviews, conversational breakdowns, and synthetic podcast episodes from knowledge base documents."
tags: [playbook, podcast, audio-overview, notebooklm, voice-synthesis, conversational-ai]
status: stable
generated:
  by: agent:antigravity
  at: 2026-10-04T17:00:00Z
verified:
  - by: human:product-team
    at: 2026-10-04T17:00:00Z
sources:
  - id: source:create-podcast-skill
    resource: /skills/create-podcast/SKILL.md
    title: "Create Podcast Skill Specification"
---

# Generating Audio Overviews & Podcasts Playbook

This playbook establishes the standard operating procedure (SOP) for transforming technical specifications, architecture contracts, and product proposals into NotebookLM-style two-host conversational audio overviews and podcast episodes.

---

## 1. Objectives & Scope

Audio overviews unlock screen-free progressive disclosure across the organization. They are used to:
1. **Accelerate Engineering Onboarding**: Enable new team members to listen to architectural deep dives and invariant breakdowns during their first week.
2. **Bridge Cross-Functional Gaps**: Translate dense technical documentation into intuitive, analogy-driven discussions that product managers, designers, and executives can easily absorb.
3. **Explore Architectural Trade-Offs**: Dissect complex engineering debates (e.g. event-driven vs. request-response, sync vs. async caching) through authentic dialogue.
4. **Permanent Knowledge Archival**: Archive audio overviews in the canonical Open Knowledge Format (`/podcasts/`) alongside interactive web players.

---

## 2. The Two-Host Persona Architecture

NotebookLM-style podcasts rely on authentic conversational chemistry between two distinct personas:

```
┌────────────────────────────────────────────────────────┐
│                   Alex (Host 1)                        │
│   • Sets the stage & establishes the core hook         │
│   • Introduces relatable real-world analogies          │
│   • Represents the curious listener                    │
│   • Keeps momentum brisk and dynamic                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼ Conversational Banter & Interjections
                            ▲
┌───────────────────────────┴────────────────────────────┐
│                  Jordan (Host 2)                       │
│   • Unpacks architectural invariants & mechanics       │
│   • Details the pragmatic catch & edge cases           │
│   • Grounded in code, datastores, and latency checks   │
│   • Brings developer realism and trade-off analysis    │
└────────────────────────────────────────────────────────┘
```

---

## 3. Four Standard Episode Formats

| Format | Target Duration | Word Count | Key Output |
| :--- | :--- | :--- | :--- |
| **Deep Dive (Standard)** | 8–15 minutes | 1,200–2,000 words | Thorough exploration of system architectures, clusters, and operational models. |
| **Executive Brief** | 3–5 minutes | 500–800 words | Rapid synthesis of milestones, RFC conclusions, or incident postmortems. |
| **Debate & Critique** | 8–12 minutes | 1,200–1,600 words | Dual-perspective examination of competing architecture proposals. |
| **Foundational Explainer** | 8–10 minutes | 1,000–1,500 words | Introductory breakdown of domain-specific concepts for non-specialists. |

---

## 4. Voice Synthesis Engine Options

Episodes can be synthesized using any of five supported backends:
1. **Google Cloud / Gemini Neural TTS** (`--backend google`): Highest quality conversational tone via Google's Studio & Journey neural voices. Requires `GOOGLE_API_KEY` (saved in `.env` or environment).
2. **Microsoft Edge Neural TTS** (`--backend edge`): Free, high-fidelity neural voices (`Ava` and `Andrew`). Requires `pip install edge-tts`. Zero API keys needed.
3. **ElevenLabs Studio Voices** (`--backend elevenlabs`): Studio voice cloning (`Rachel` and `Adam`). Requires `ELEVENLABS_API_KEY`.
4. **macOS Native Speech** (`--backend macos`): High quality offline voices (`Samantha` and `Daniel`) with natural pauses. Built-in to macOS.
5. **Interactive Web Player Only** (`--backend web`): Generates a standalone HTML5 player using in-browser Web Speech API (`window.speechSynthesis`).

---

## 5. Operational Step-by-Step Procedure

### Step 1: Trigger the Skill
Invoke via chat slash command or CLI:
```text
/create-podcast systems/core-architecture.md
```

### Step 2: Conduct Pre-Production Editorial Discovery Interview
Before generating content, the agent asks key scoping questions:
1. **Narrative Angle & Focus**:
   * Architectural & Technical Deep Dive (Invariants, schemas, failure modes)
   * Executive & Strategic Summary (Business value, timeline, high-level mechanics)
   * Spirited Architectural Debate (Weighing competing approaches)
   * Educational Explainer (Demystifying concepts with real-world analogies)
2. **Content Scope & Key Emphasis**:
   * What specific subsystems, trade-offs, or recent decisions to highlight
3. **Target Audience & Technical Depth**:
   * Core Software Engineers vs. Cross-Functional Team vs. Leadership
4. **Preferred Voice Synthesis Engine**:
   * Edge Neural TTS vs. Google Cloud/Gemini TTS vs. ElevenLabs vs. macOS Offline vs. Web Player

### Step 3: Extract Architectural Invariants & Anchor Analogy
Based on the user's answers:
* Isolate the chosen subsystems and architectural invariants.
* Formulate an intuitive real-world analogy grounded in the audience's domain.

### Step 4: Author the Script in `podcasts/`
* Use `templates/podcast-template.md`.
* Declare `Narrative Focus` and `Target Audience` in the metadata block.
* Write turn-taking dialogue with timestamps (`[00:00]`) and vocal tone cues (`[curious]`, `[laughing]`, `[chuckles]`).

### Step 5: Synthesize Audio & Interactive Player
Run the generator tool:
```bash
# Interactive selection prompt
python3 scripts/generate_podcast.py podcasts/epXX-<topic>.md

# Direct backend
python3 scripts/generate_podcast.py podcasts/epXX-<topic>.md --backend google
```
This produces:
* An interactive HTML5 player: `podcasts/epXX-<topic>.html` with dual-voice speech synthesis and auto-scrolling karaoke highlights.
* Audio tracks (`.mp3` or `.m4a`) linked directly inside the web player.

### Step 6: Validate Knowledge Graph
Run the presubmit hook to update root `index.md`:
```bash
./scripts/presubmit.py
```
