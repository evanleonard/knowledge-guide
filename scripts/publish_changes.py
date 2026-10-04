#!/usr/bin/env python3
"""
publish_changes.py - Publish & Share Knowledge Base Changes (OKF v0.2)

Translates non-technical requests like "publish my updates", "share my changes",
or "save and publish" into the verified Git workflow:
1. Runs presubmit validation & index synchronization (presubmit.py).
2. Syncs incoming teammate updates from origin if needed.
3. Stages and commits local changes with an automated or custom message.
4. Pushes changes to origin/main.
5. Returns a clear, non-technical plain-English summary.
"""

import sys
import os
import re
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional

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

def get_current_branch(repo_root: Path) -> str:
    code, out, _ = run_cmd(["git", "branch", "--show-current"], repo_root)
    return out if code == 0 and out else "main"

def get_changed_files(repo_root: Path) -> List[Tuple[str, str]]:
    code, out, _ = run_cmd(["git", "status", "--porcelain"], repo_root)
    if code != 0 or not out:
        return []
    changes = []
    for line in out.splitlines():
        line = line.strip()
        if line:
            status = line[:2].strip()
            fname = line[2:].strip()
            changes.append((status, fname))
    return changes

def check_unpushed_commits(repo_root: Path, branch: str) -> List[str]:
    code, out, _ = run_cmd(["git", "log", f"origin/{branch}..HEAD", "--oneline"], repo_root)
    if code == 0 and out:
        return [l.strip() for l in out.splitlines() if l.strip()]
    return []

def generate_default_message(changes: List[Tuple[str, str]]) -> str:
    if not changes:
        return "docs: update knowledge base"
    
    # Filter markdown/doc files
    doc_files = [f for _, f in changes if f.endswith(".md")]
    other_files = [f for _, f in changes if not f.endswith(".md")]
    
    if len(doc_files) == 1 and not other_files:
        stem = Path(doc_files[0]).stem.replace("-", " ")
        return f"docs: update {stem}"
    elif len(doc_files) > 1 and not other_files:
        if len(doc_files) <= 3:
            names = ", ".join(Path(f).stem.replace("-", " ") for f in doc_files)
            return f"docs: update {names}"
        return f"docs: publish updates to {len(doc_files)} notes"
    else:
        total = len(changes)
        return f"docs: publish updates to {total} file(s)"

def publish(repo_root: Path, message: Optional[str] = None, dry_run: bool = False) -> int:
    branch = get_current_branch(repo_root)
    
    # 1. Check current status
    changes_before = get_changed_files(repo_root)
    run_cmd(["git", "fetch", "origin", branch], repo_root)
    unpushed_before = check_unpushed_commits(repo_root, branch)

    if not changes_before and not unpushed_before:
        print("✅ Everything is already published! Your local notes are completely up to date with the team.")
        return 0

    print("🚀 Preparing to publish and share changes with the team...\n")

    # 2. Run presubmit gatekeeper
    print("🔍 Running presubmit validation & index synchronization...")
    presubmit_script = repo_root / "scripts" / "presubmit.py"
    if presubmit_script.exists():
        code, out, err = run_cmd([sys.executable, str(presubmit_script)], repo_root)
        if code != 0:
            print("❌ Presubmit validation failed. Please fix validation errors before publishing:")
            print(out)
            if err:
                print(err)
            return 1
        print("✅ Presubmit validation passed (0 defects).\n")
    
    # Check changes again after presubmit (which may have auto-repaired or updated index.md)
    changes = get_changed_files(repo_root)

    # 3. Pull/rebase remote changes if any
    code, incoming, _ = run_cmd(["git", "log", f"HEAD..origin/{branch}", "--oneline"], repo_root)
    if code == 0 and incoming:
        incoming_commits = [l.strip() for l in incoming.splitlines() if l.strip()]
        print(f"📥 Syncing {len(incoming_commits)} teammate update(s) from GitHub...")
        pull_code, _, pull_err = run_cmd(["git", "pull", "--rebase", "origin", branch], repo_root)
        if pull_code != 0:
            print(f"⚠️ Notice: Unable to automatically rebase with incoming team updates: {pull_err}")
            print("Please resolve conflicting notes before publishing.")
            return 1
        print("✅ Teammate updates integrated smoothly.\n")

    # 4. Preview if dry-run
    if dry_run:
        print("🔎 Dry run mode - previewing changes to publish:")
        for status, fname in changes:
            print(f"   • [{status}] {fname}")
        commit_msg = message or generate_default_message(changes)
        print(f"\nPlanned commit message: {commit_msg}")
        return 0

    # 5. Commit if there are uncommitted files
    commit_msg = message
    if changes:
        if not commit_msg:
            commit_msg = generate_default_message(changes)
        elif not re.match(r"^(docs|feat|fix|chore|refactor|test|style|ci|perf)(\([^)]+\))?:\s*", commit_msg):
            commit_msg = f"docs: {commit_msg}"
            
        print(f"📦 Saving changes: \"{commit_msg}\"")
        run_cmd(["git", "add", "-A"], repo_root)
        code, _, err = run_cmd(["git", "commit", "-m", commit_msg], repo_root)
        if code != 0:
            print(f"❌ Failed to save changes: {err}")
            return 1

    # 6. Push to origin/main
    print(f"📤 Sharing changes to GitHub (origin/{branch})...")
    code, out, err = run_cmd(["git", "push", "origin", branch], repo_root)
    if code != 0:
        print(f"❌ Failed to share changes to GitHub: {err}")
        return 1

    # 7. Print friendly confirmation
    print("\n" + "="*55)
    print("🎉 Success! Your changes have been published and shared with the team.")
    print("="*55)
    if changes:
        print(f"\n📝 Published {len(changes)} file(s):")
        for status, fname in changes:
            print(f"   • {fname}")
    if commit_msg:
        print(f"\n💬 Summary: {commit_msg}")
    print(f"🌐 Remote: Synchronized with origin/{branch} on GitHub.\n")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Publish & Share Knowledge Base Changes (Git Commit & Push in Plain English)")
    parser.add_argument("-m", "--message", type=str, default=None, help="Optional summary message describing your changes")
    parser.add_argument("--dry-run", action="store_true", help="Preview what would be published without committing or pushing")
    args = parser.parse_args()

    repo_root = get_repo_root()
    ret = publish(repo_root, message=args.message, dry_run=args.dry_run)
    sys.exit(ret)

if __name__ == "__main__":
    main()
