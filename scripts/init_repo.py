#!/usr/bin/env python3
"""
init_repo.py - Fast onboarding and personalization script for new organizations.

Customizes organization name, titles, descriptions, upstream remote tracking,
optional sample concept archival, and regenerates index and configuration.
"""

import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from update_index import generate_index
from validate import validate_bundle

DEFAULT_UPSTREAM_URL = "https://github.com/evanleonard/knowledge-guide.git"

SAMPLE_FILES = [
    "concepts/cluster-intelligent-automation.md",
    "concepts/predictive-dispatch.md",
    "concepts/future-initiative.md",
    "systems/core-architecture.md",
    "ecosystem/industry-landscape.md",
    "research/user-interview-example.md",
]

def customize_repo(
    repo_dir: Path,
    org_name: str,
    kb_title: str,
    kb_desc: str,
    upstream_url: str = DEFAULT_UPSTREAM_URL,
    archive_samples: bool = False,
    clean_samples: bool = False
):
    print(f"⚙️  Customizing Knowledge Guide for: {org_name}...\n")
    
    # 1. Update knowledge.config.json
    cfg_file = repo_dir / "knowledge.config.json"
    cfg = {}
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
            
    cfg["org_name"] = org_name
    cfg["kb_title"] = kb_title
    cfg["kb_description"] = kb_desc
    if "upstream_repository" not in cfg or not cfg["upstream_repository"]:
        cfg["upstream_repository"] = upstream_url
    
    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("  ✔ Updated knowledge.config.json (configured upstream tracking)")
    
    # 2. Configure git remote 'upstream' if in a git repo
    git_dir = repo_dir / ".git"
    if git_dir.exists():
        try:
            res = subprocess.run(["git", "remote", "-v"], cwd=str(repo_dir), capture_output=True, text=True)
            if res.returncode == 0:
                remotes = {}
                for line in res.stdout.splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        remotes[parts[0]] = parts[1]
                if "upstream" not in remotes:
                    subprocess.run(["git", "remote", "add", "upstream", upstream_url], cwd=str(repo_dir), capture_output=True)
                    print(f"  ✔ Configured git remote 'upstream' -> {upstream_url}")
                elif remotes["upstream"] != upstream_url:
                    subprocess.run(["git", "remote", "set-url", "upstream", upstream_url], cwd=str(repo_dir), capture_output=True)
                    print(f"  ✔ Updated git remote 'upstream' -> {upstream_url}")
        except Exception:
            pass

    # 3. Handle sample concept placeholders if requested
    if archive_samples or clean_samples:
        archive_dir = repo_dir / "archive" / "samples"
        if archive_samples:
            archive_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for sample_rel in SAMPLE_FILES:
            sample_p = repo_dir / sample_rel
            if sample_p.exists():
                if archive_samples:
                    dest = archive_dir / sample_p.name
                    shutil.move(str(sample_p), str(dest))
                else:
                    sample_p.unlink()
                count += 1
        if count > 0:
            action = "Archived" if archive_samples else "Removed"
            target_desc = f"to {archive_dir.relative_to(repo_dir)}" if archive_samples else ""
            print(f"  ✔ {action} {count} sample placeholder document(s) {target_desc}")

    # 4. Update README.md title if template placeholder exists
    readme_file = repo_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text(encoding="utf-8")
        content = content.replace("Example Organization", org_name)
        content = content.replace("Organization Knowledge Base", kb_title)
        readme_file.write_text(content, encoding="utf-8")
        print("  ✔ Updated README.md")
        
    # 5. Update SETUP.md title if template placeholder exists
    setup_file = repo_dir / "SETUP.md"
    if setup_file.exists():
        content = setup_file.read_text(encoding="utf-8")
        content = content.replace("Example Organization", org_name)
        content = content.replace("Organization Knowledge Base", kb_title)
        setup_file.write_text(content, encoding="utf-8")
        print("  ✔ Updated SETUP.md")
        
    # 6. Append to log.md
    log_file = repo_dir / "log.md"
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_entry = f"## {today_str}\n* **Initialization**: Configured knowledge base template for **{org_name}**.\n\n"
    if log_file.exists():
        existing_log = log_file.read_text(encoding="utf-8")
        if not existing_log.startswith(f"## {today_str}"):
            log_file.write_text(log_entry + existing_log, encoding="utf-8")
        else:
            # Append under existing date heading
            lines = existing_log.splitlines(True)
            lines.insert(1, f"* **Initialization**: Configured knowledge base template for **{org_name}**.\n")
            log_file.write_text("".join(lines), encoding="utf-8")
    else:
        log_file.write_text(f"# Knowledge Base Changelog\n\n{log_entry}", encoding="utf-8")
    print("  ✔ Logged initialization event in log.md")
    
    # 7. Regenerate index.md
    generate_index(repo_dir)
    print("  ✔ Regenerated root index.md")
    
    # 8. Check email privacy settings
    if git_dir.exists():
        try:
            res = subprocess.run(["git", "config", "user.email"], cwd=str(repo_dir), capture_output=True, text=True)
            email = res.stdout.strip()
            if not email:
                print("  ℹ️ Tip: Configure your git user.email with your GitHub noreply email to prevent GH007 push blocks:")
                print("     git config user.email \"<username>@users.noreply.github.com\"")
        except Exception:
            pass

    # 9. Validate and auto-fix
    print("\n🔍 Validating bundle health...")
    ret = validate_bundle(repo_dir, fix=True)
    if ret == 0:
        print(f"\n🎉 Successfully initialized knowledge guide for {org_name}!")
        print("Next steps:")
        print("  1. Review knowledge.config.json for customized categories.")
        print("  2. Run ./setup.sh to install presubmit git hooks & agent discovery.")
        print("  3. Begin authoring in systems/, ecosystem/, concepts/, and playbooks/.")
        print("  4. Check upstream platform updates anytime via ./scripts/upgrade_guide.py --check")
    return ret

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize knowledge base for your organization.")
    parser.add_argument("--org", type=str, help="Organization Name (e.g. Acme Health)")
    parser.add_argument("--title", type=str, help="Knowledge Base Title (e.g. Acme Knowledge Guide)")
    parser.add_argument("--desc", type=str, help="Single-sentence summary of the knowledge base")
    parser.add_argument("--upstream", type=str, default=DEFAULT_UPSTREAM_URL, help="Upstream platform repository URL")
    parser.add_argument("--archive-samples", action="store_true", help="Move template sample concepts to archive/samples/")
    parser.add_argument("--clean-samples", action="store_true", help="Remove template sample concepts to start with an empty canvas")
    parser.add_argument("--repo-dir", type=Path, default=REPO_ROOT, help="Knowledge base root path")
    args = parser.parse_args()
    
    org = args.org
    if not org and sys.stdin.isatty():
        try:
            org = input("Enter your organization name [Example Organization]: ").strip()
        except EOFError:
            pass
    if not org:
        org = "Example Organization"
        
    title = args.title
    if not title:
        title = f"{org} Knowledge Base"
        
    desc = args.desc
    if not desc:
        desc = f"Canonical Open Knowledge Format (OKF v0.2) knowledge base for {org}."
        
    sys.exit(customize_repo(
        args.repo_dir,
        org,
        title,
        desc,
        upstream_url=args.upstream,
        archive_samples=args.archive_samples,
        clean_samples=args.clean_samples
    ))
