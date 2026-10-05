#!/usr/bin/env python3
"""
query_kb.py - Fast CLI & programmatic search tool for the OKF Knowledge Base.

Usage:
    python3 scripts/query_kb.py "architecture gateway"
    python3 scripts/query_kb.py "onboarding" --category playbooks
    python3 scripts/query_kb.py "queue" --json
"""

import sys
import re
import json
import argparse
from pathlib import Path

# Add scripts directory to path to import frontmatter parser
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate import parse_yaml_frontmatter

def load_categories(bundle_dir: Path) -> list:
    cfg_file = bundle_dir / "knowledge.config.json"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [c.get("id", c.get("path_prefix", "").rstrip("/")) for c in data.get("categories", [])]
        except Exception:
            pass
    # Fallback to scanning directories
    return [p.name for p in bundle_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]

def search_kb(bundle_dir: Path, query: str, category: str = None, limit: int = 5):
    keywords = [k.lower() for k in query.split() if len(k) > 2] or [query.lower()]
    query_lower = query.lower()
    
    results = []
    
    for file_path in sorted(bundle_dir.rglob("*.md")):
        if file_path.name in ["index.md", "log.md"]:
            continue
            
        rel_parts = file_path.relative_to(bundle_dir).parts
        if any(p in {"archive", "private"} or p.startswith(".") for p in rel_parts) or file_path.name.startswith("."):
            continue
            
        rel_path = file_path.relative_to(bundle_dir).as_posix()
        
        if category and not rel_path.startswith(category):
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
            
        meta, body = parse_yaml_frontmatter(content)
        if not meta:
            continue
            
        title = meta.get("title", file_path.stem.replace("-", " ").title())
        desc = meta.get("description", "")
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
            
        # Scoring
        score = 0
        title_lower = title.lower()
        desc_lower = desc.lower()
        body_lower = body.lower()
        tags_lower = [t.lower() for t in tags]
        
        # Exact query match
        if query_lower in title_lower:
            score += 100
        if query_lower in desc_lower:
            score += 50
        if any(query_lower in t for t in tags_lower):
            score += 40
        if query_lower in body_lower:
            score += 20
            
        # Keyword matches
        for kw in keywords:
            if kw in title_lower:
                score += 30
            if kw in desc_lower:
                score += 15
            if any(kw in t for t in tags_lower):
                score += 15
            count_in_body = body_lower.count(kw)
            score += min(count_in_body * 2, 20)
            
        if score > 0:
            # Extract excerpt
            excerpt = ""
            match_idx = -1
            for term in [query_lower] + keywords:
                idx = body_lower.find(term)
                if idx != -1:
                    match_idx = idx
                    break
                    
            if match_idx != -1:
                start = max(0, match_idx - 100)
                end = min(len(body), match_idx + 200)
                snip = body[start:end].replace("\n", " ").strip()
                # Clean markdown headers/links
                snip = re.sub(r"[#*`]", "", snip)
                excerpt = f"...{snip}..."
            else:
                excerpt = desc[:200]
                
            results.append({
                "score": score,
                "title": title,
                "path": f"/{rel_path}",
                "description": desc,
                "type": meta.get("type", "Document"),
                "status": meta.get("status", "stable"),
                "excerpt": excerpt
            })
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]

def main():
    bundle_dir = REPO_ROOT
    available_categories = load_categories(bundle_dir)
    
    parser = argparse.ArgumentParser(description="Query the OKF Knowledge Base")
    parser.add_argument("query", nargs="?", default="", help="Search query or question")
    parser.add_argument("--category", choices=available_categories, help="Filter by directory category")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to display")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--repo-dir", type=Path, default=bundle_dir, help="Bundle directory path")
    
    args = parser.parse_args()
    target_dir = args.repo_dir
    
    if not target_dir.exists():
        print(f"Error: Knowledge base directory not found at {target_dir}", file=sys.stderr)
        sys.exit(1)
        
    if not args.query:
        print(f"Knowledge Base ({target_dir.name}) - Available Categories:")
        for cat in available_categories:
            cat_dir = target_dir / cat
            count = len(list(cat_dir.rglob("*.md"))) if cat_dir.exists() else 0
            print(f"  • {cat:15} ({count} documents)")
        print("\nUsage: python3 scripts/query_kb.py <query> [--category <cat>]")
        sys.exit(0)
        
    results = search_kb(target_dir, args.query, args.category, args.limit)
    
    if args.json:
        print(json.dumps(results, indent=2))
        return
        
    if not results:
        print(f"No documents matched '{args.query}'. Try searching for broader terms.")
        return
        
    print(f"\n🔍 Found {len(results)} matching document(s) for: '{args.query}':\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['type']}] {r['title']}")
        print(f"   Link: {r['path']}")
        print(f"   Summary: {r['description']}")
        if r['excerpt']:
            print(f"   Excerpt: {r['excerpt']}")
        print()

if __name__ == "__main__":
    main()
