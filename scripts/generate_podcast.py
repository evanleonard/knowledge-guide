#!/usr/bin/env python3
"""
generate_podcast.py - OKF Podcast & Audio Overview Generator.

Generates NotebookLM-style interactive audio players and synthetic audio tracks
for Open Knowledge Format (OKF v0.2) podcast episodes.

Usage:
    python3 scripts/generate_podcast.py podcasts/my-episode.md
    python3 scripts/generate_podcast.py podcasts/my-episode.md --open
    python3 scripts/generate_podcast.py podcasts/my-episode.md --audio
"""

import sys
from pathlib import Path

# Add skill script to path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
SKILL_SCRIPT = REPO_ROOT / "skills" / "create-podcast" / "scripts" / "generate_podcast_audio.py"

if not SKILL_SCRIPT.exists():
    print(f"Error: Podcast skill script not found at {SKILL_SCRIPT}")
    sys.exit(1)

import importlib.util
spec = importlib.util.spec_from_file_location("generate_podcast_audio", SKILL_SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules["generate_podcast_audio"] = mod
spec.loader.exec_module(mod)

if __name__ == "__main__":
    mod.main()
