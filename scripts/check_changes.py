#!/usr/bin/env python3
"""
check_changes.py - Delta-Guide Content Changes & Team Updates Checker (OKF v0.2)

Designed for non-technical users and AI agents to check for content additions,
recent changes, and incoming team commits in the delta-guide repository.

Differentiates between:
1. Content changes & team notes in delta-guide (this script).
2. Platform software/engine upgrades from upstream knowledge-guide (upgrade_guide.py).
"""

import sys
import json
import datetime
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

def run_cmd(cmd: List[str], cwd: Path, timeout: Optional[int] = 30) -> Tuple[int, str, str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            env=env,
            text=True,
            timeout=timeout
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def get_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    while curr != curr.parent:
        if (curr / "knowledge.config.json").exists() or (curr / ".git").exists():
            return curr
        curr = curr.parent
    return Path.cwd()

def get_recent_changelog_entries(repo_root: Path, max_headings: int = 2) -> List[Dict[str, Any]]:
    log_file = repo_root / "log.md"
    if not log_file.exists():
        return []
        
    try:
        content = log_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        headings = []
        curr_heading = None
        curr_entries = []
        
        for line in lines:
            stripped = line.strip()
            if line.startswith("## "):
                if curr_heading and curr_entries:
                    headings.append({"date": curr_heading, "entries": curr_entries})
                    if len(headings) >= max_headings:
                        break
                curr_heading = line[3:].strip()
                curr_entries = []
            elif curr_heading:
                if stripped.startswith("* ") or stripped.startswith("- "):
                    item = stripped[2:].strip()
                    if item:
                        curr_entries.append(item)
                
        if curr_heading and curr_entries and (not headings or headings[-1]["date"] != curr_heading) and len(headings) < max_headings:
            headings.append({"date": curr_heading, "entries": curr_entries})
            
        return headings
    except Exception:
        return []

def check_content_changes(repo_root: Path) -> Dict[str, Any]:
    # 1. Fetch from team remote (origin)
    fetch_code, _, _ = run_cmd(["git", "fetch", "origin", "main"], repo_root)
    
    # 2. Check incoming team commits on origin/main
    incoming_commits = []
    if fetch_code == 0:
        code, out, _ = run_cmd(["git", "log", "HEAD..origin/main", "--oneline"], repo_root)
        if code == 0 and out:
            incoming_commits = [line for line in out.splitlines() if line.strip()]
            
    # 3. Check local uncommitted files
    uncommitted_files = []
    code, out, _ = run_cmd(["git", "status", "--porcelain"], repo_root)
    if code == 0 and out:
        for line in out.splitlines():
            line = line.strip()
            if line:
                status = line[:2].strip()
                fname = line[2:].strip()
                uncommitted_files.append({"status": status, "file": fname})
                
    # 4. Check recent local commits
    code, out, _ = run_cmd(["git", "log", "-n", "3", "--oneline"], repo_root)
    recent_commits = [line for line in out.splitlines() if line.strip()] if code == 0 and out else []
    
    # 5. Get recent changelog highlights
    changelog = get_recent_changelog_entries(repo_root, max_headings=2)

    return {
        "team_updates_available": len(incoming_commits) > 0,
        "incoming_team_commits": incoming_commits,
        "uncommitted_local_files": uncommitted_files,
        "recent_commits": recent_commits,
        "changelog": changelog
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check for Content Changes & Team Updates in delta-guide")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--pull", action="store_true", help="Pull incoming team updates from origin/main")
    args = parser.parse_args()

    repo_root = get_repo_root()
    report = check_content_changes(repo_root)

    if args.pull:
        if report["team_updates_available"]:
            print(f"📥 Pulling {len(report['incoming_team_commits'])} team update(s) from origin/main...")
            code, out, err = run_cmd(["git", "pull", "origin", "main"], repo_root)
            if code == 0:
                print("✅ Successfully updated local guide with team changes.")
            else:
                print(f"❌ Failed to pull team updates: {err}")
                sys.exit(1)
        else:
            print("✅ Already up to date with origin/main.")
        return

    if args.json:
        print(json.dumps(report, indent=2))
        return

    org_title = "Knowledge Base"
    config_file = repo_root / "knowledge.config.json"
    if config_file.exists():
        try:
            cfg = json.loads(config_file.read_text(encoding="utf-8"))
            org_title = cfg.get("organization", {}).get("name", "Knowledge Base")
        except Exception:
            pass

    print(f"📚 {org_title} Content & Activity Report\n" + "="*50)
    
    # Team remote updates
    if report["team_updates_available"]:
        print(f"\n👥 Team Updates on GitHub (origin/main): {len(report['incoming_team_commits'])} new commit(s) available")
        for c in report["incoming_team_commits"]:
            print(f"   • {c}")
        print("   👉 Run './scripts/check_changes.py --pull' or ask the agent to 'pull team changes'.")
    else:
        print("\n👥 Team Collaboration: Up to date with origin/main (all team notes synchronized).")

    # Local working tree status
    if report["uncommitted_local_files"]:
        print(f"\n📝 Local Working Drafts ({len(report['uncommitted_local_files'])} uncommitted file(s)):")
        for f in report["uncommitted_local_files"]:
            print(f"   • [{f['status'] or '?'}] {f['file']}")
    else:
        print("\n📝 Local Workspace: Clean (all local notes committed).")

    # Recent changelog highlights
    if report["changelog"]:
        print("\n✨ Recent Knowledge Base Additions:")
        for block in report["changelog"]:
            print(f"   📅 {block['date']}:")
            count = 0
            for entry in block["entries"]:
                # If it's a section header like "**Category**:", show it
                if entry.endswith(":"):
                    print(f"      📁 {entry.rstrip(':')}")
                else:
                    first_sentence = entry.split(". ")[0] + "." if ". " in entry else entry
                    # If sentence doesn't end with a dot, add ellipsis if long
                    if len(first_sentence) > 130:
                        first_sentence = first_sentence[:127] + "..."
                    print(f"      • {first_sentence}")
                    count += 1
                    if count >= 4:
                        break

if __name__ == "__main__":
    main()
