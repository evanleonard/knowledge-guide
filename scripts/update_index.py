#!/usr/bin/env python3
"""
update_index.py - Dynamic generator and synchronizer for the OKF root index.md.

Reads knowledge.config.json (if present) to dynamically group concept documents
by categorized paths and frontmatter, producing a clean progressive-disclosure index.
"""

import sys
import json
import argparse
from pathlib import Path

# Add script dir to path to import validate's frontmatter parser
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate import parse_yaml_frontmatter

DEFAULT_CONFIG = {
    "org_name": "Organization Name",
    "kb_title": "Organization Knowledge Base",
    "kb_description": "Canonical Open Knowledge Format (OKF v0.2) repository: separating operational & system reality ('What Is') from proposed product innovations ('What Could Be').",
    "okf_version": "0.2",
    "categories": [
        {
            "id": "systems",
            "title": "Production Systems & Architecture ('What Is')",
            "path_prefix": "systems/",
            "description": "Active production software, backend services, client apps, data stores, and internal workflows."
        },
        {
            "id": "ecosystem",
            "title": "External Ecosystem & Industry Reality ('What Is')",
            "path_prefix": "ecosystem/",
            "description": "External regulatory environment, industry standards, third-party APIs, and partner rails."
        },
        {
            "id": "concepts",
            "title": "Product Concepts & Explorations ('What Could Be')",
            "path_prefix": "concepts/",
            "description": "Proposed features, architectural RFCs, exploratory initiatives, and future innovations."
        },
        {
            "id": "frontier",
            "title": "Frontier & Emerging Ideas ('What Could Be')",
            "path_prefix": "frontier/",
            "description": "Exploratory horizon-scanning initiatives, emerging prototypes, experimental ideas, and nascent proposals."
        },
        {
            "id": "storyboards",
            "title": "Visual Storyboards & User Journeys ('What Could Be')",
            "path_prefix": "storyboards/",
            "description": "Sequential visual narrative storyboards illustrating product features, user journeys, and partner integrations."
        },
        {
            "id": "podcasts",
            "title": "Audio Overviews & Podcasts ('What Could Be')",
            "path_prefix": "podcasts/",
            "description": "NotebookLM-style two-host deep dive audio overviews, conversational breakdowns, and synthetic podcast episodes."
        },
        {
            "id": "playbooks",
            "title": "Operational Playbooks & Runbooks",
            "path_prefix": "playbooks/",
            "description": "Standard operating procedures, incident guides, and team runbooks."
        },
        {
            "id": "research",
            "title": "Field Research & User Interviews",
            "path_prefix": "research/",
            "description": "Customer interviews, field observations, survey data, and qualitative provenance."
        },
        {
            "id": "skills",
            "title": "Agent Skills & Automation Capabilities",
            "path_prefix": "skills/",
            "description": "Reusable AI agent capabilities, maintenance tools, and automation workflows."
        },
        {
            "id": "references",
            "title": "Standards, Specifications & References",
            "path_prefix": "references/",
            "description": "Format specifications, schemas, data contracts, and knowledge base audit logs."
        },
        {
            "id": "templates",
            "title": "Knowledge Document Starter Templates",
            "path_prefix": "templates/",
            "description": "Standardized templates for creating new concepts, systems, playbooks, and research notes."
        }
    ]
}


def load_config(bundle_dir: Path) -> dict:
    cfg_file = bundle_dir / "knowledge.config.json"
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception as e:
            print(f"Warning: Failed to parse knowledge.config.json ({e}). Using default configuration.")
    return DEFAULT_CONFIG


def generate_index(bundle_dir: Path):
    cfg = load_config(bundle_dir)
    categories_cfg = cfg.get("categories", DEFAULT_CONFIG["categories"])
    
    # Map category id -> items list
    category_buckets = {c["id"]: [] for c in categories_cfg}
    unmapped_items = []
    
    # Scan all markdown files (exempting archive and hidden files)
    for file_path in sorted(bundle_dir.rglob("*.md")):
        if "archive" in file_path.parts or file_path.name.startswith("."):
            continue
        if file_path.name in ["index.md", "log.md"]:
            continue
            
        rel = file_path.relative_to(bundle_dir)
        rel_str = rel.as_posix()
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
            
        meta, _ = parse_yaml_frontmatter(content)
        if not meta:
            continue
            
        title = meta.get("title", file_path.stem.replace("-", " ").replace("_", " ").title())
        desc = meta.get("description", "")
        link = f"/{rel_str}"
        item_text = f"* [{title}]({link}) - {desc}" if desc else f"* [{title}]({link})"
        
        # Place in appropriate category
        matched = False
        for cat in categories_cfg:
            prefix = cat.get("path_prefix", "")
            if prefix and rel_str.startswith(prefix):
                category_buckets[cat["id"]].append(item_text)
                matched = True
                break
                
        if not matched:
            unmapped_items.append(item_text)
            
    # Ensure log.md is listed in references or first available section
    log_item = "* [Bundle Update Log](/log.md) - Chronological record of additions, modifications, and verifications in this bundle."
    if "references" in category_buckets:
        category_buckets["references"].append(log_item)
    elif unmapped_items:
        unmapped_items.append(log_item)
    else:
        unmapped_items.append(log_item)
        
    # Construct index.md content
    title = cfg.get("kb_title", "Knowledge Base")
    desc = cfg.get("kb_description", "Canonical Open Knowledge Format repository.")
    okf_ver = cfg.get("okf_version", "0.2")
    
    lines = [
        "---",
        f'okf_version: "{okf_ver}"',
        f'title: "{title}"',
        f'description: "{desc}"',
        "---",
        "",
        f"# {title}",
        "",
        f"{desc}",
        "",
        "Knowledge in this bundle is organized with clear demarcation between:",
        "1. **\"What Is\"**: Operational realities, external ecosystem context (`/ecosystem/`), key institutions (`/ecosystem/institutions/`), and active production systems (`/systems/`).",
        "2. **Theoretical Concepts & Architectural Models**: Foundational concepts, thematic clusters, and relational graphs (`/concepts/`).",
        "3. **\"What Could Be\"**: Visual storyboards (`/storyboards/`), audio overviews (`/podcasts/`), emerging innovations, exploratory prototypes, and horizon scanning (`/frontier/`).",
        "4. **\"How To\" & Provenance**: Operational runbooks (`/playbooks/`), field research (`/research/`), and standards (`/references/`).",
        "",
        "---",
        ""
    ]
    
    total_indexed = 0
    for cat in categories_cfg:
        cat_id = cat["id"]
        cat_title = cat.get("title", cat_id.title())
        items = category_buckets.get(cat_id, [])
        if items:
            total_indexed += len(items)
            lines.append(f"## {cat_title}")
            lines.append("")
            if cat_id == "concepts":
                clusters = [it for it in items if "/cluster-" in it]
                nodes = [it for it in items if "/cluster-" not in it]
                
                if clusters:
                    lines.append("### Thematic Concept Clusters & Mind Maps")
                    lines.append("")
                    for it in clusters:
                        lines.append(it)
                    lines.append("")
                    if nodes:
                        lines.append("### Constituent Concept Nodes & Relational Edges")
                        lines.append("")
                        for it in nodes:
                            lines.append(it)
                        lines.append("")
                else:
                    for it in items:
                        lines.append(it)
                    lines.append("")
            else:
                for it in items:
                    lines.append(it)
                lines.append("")
            
    if unmapped_items:
        total_indexed += len(unmapped_items)
        lines.append("## General Documents")
        lines.append("")
        for it in unmapped_items:
            lines.append(it)
        lines.append("")
        
    index_path = bundle_dir / "index.md"
    index_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"✅ Successfully updated {index_path} ({total_indexed} indexed resources).")


if __name__ == "__main__":
    default_bundle_root = SCRIPT_DIR.parent
    parser = argparse.ArgumentParser(
        description="Dynamic generator and synchronizer for the OKF root index.md."
    )
    parser.add_argument(
        "bundle_root",
        nargs="?",
        default=default_bundle_root,
        type=Path,
        help="Path to the OKF bundle root directory (default: repository root)",
    )
    args = parser.parse_args()
    generate_index(args.bundle_root.resolve())

