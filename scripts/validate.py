#!/usr/bin/env python3
"""
validate.py - Self-contained validator and auto-fixer for Google Open Knowledge Format (OKF v0.2).

Ensures the knowledge base is fully self-maintaining:
1. Validates reserved files (index.md, log.md)
2. Validates frontmatter presence, YAML syntax, and required 'type'
3. Checks lifecycle state (status in draft|stable|deprecated, stale_after expiration)
4. Evaluates trust tiers (human-reviewed, machine-confirmed, unverified)
5. Validates internal link integrity (bundle-relative /... and relative ./...)
6. Supports --fix to automatically repair schema errors, missing frontmatter, links, and index.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone

def parse_yaml_frontmatter(text):
    if not text.startswith("---"):
        return None, text
    
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    
    raw_yaml = parts[1]
    body = parts[2]
    
    metadata = {}
    lines = raw_yaml.splitlines()
    i = 0
    current_key = None
    
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line or line.strip().startswith("#"):
            continue
        
        match = re.match(r"^([a-zA-Z0-9_\-]+):\s*(.*)$", line)
        if match:
            key, val = match.groups()
            key = key.strip()
            val = val.strip()
            current_key = key
            
            if not val:
                metadata[key] = []
                continue
            
            # Inline list e.g. [a, b, c]
            if val.startswith("[") and val.endswith("]"):
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                metadata[key] = items
            # Inline dict e.g. { by: foo, at: bar }
            elif val.startswith("{") and val.endswith("}"):
                d = {}
                pairs = val[1:-1].split(",")
                for pair in pairs:
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        d[k.strip()] = v.strip().strip("\"'")
                metadata[key] = d
            # Quoted string
            elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                metadata[key] = val[1:-1]
            else:
                metadata[key] = val
        elif line.startswith("  - ") and current_key:
            # List item
            item_val = line[4:].strip()
            if not isinstance(metadata.get(current_key), list):
                metadata[current_key] = []
            if item_val.startswith("{") and item_val.endswith("}"):
                d = {}
                pairs = item_val[1:-1].split(",")
                for pair in pairs:
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        d[k.strip()] = v.strip().strip("\"'")
                metadata[current_key].append(d)
            elif ":" in item_val:
                sub_k, sub_v = item_val.split(":", 1)
                metadata[current_key].append({sub_k.strip(): sub_v.strip().strip("\"'")})
            else:
                metadata[current_key].append(item_val.strip("\"'"))
        elif line.startswith("    ") and current_key and isinstance(metadata.get(current_key), list) and metadata[current_key]:
            # Nested dict key in list item
            sub_line = line.strip()
            if ":" in sub_line:
                sub_k, sub_v = sub_line.split(":", 1)
                if isinstance(metadata[current_key][-1], dict):
                    metadata[current_key][-1][sub_k.strip()] = sub_v.strip().strip("\"'")
                else:
                    metadata[current_key][-1] = {sub_k.strip(): sub_v.strip().strip("\"'")}
        elif line.startswith("  ") and current_key:
            # Nested mapping under dict
            sub_line = line.strip()
            if ":" in sub_line:
                sub_k, sub_v = sub_line.split(":", 1)
                if not isinstance(metadata[current_key], dict):
                    metadata[current_key] = {}
                metadata[current_key][sub_k.strip()] = sub_v.strip().strip("\"'")
                
    return metadata, body


def infer_doc_type(rel_path: Path) -> str:
    parts = rel_path.parts
    if len(parts) > 1:
        folder = parts[0]
        if folder == "concepts" and rel_path.name.startswith("cluster-"):
            return "Concept Cluster"
        mapping = {
            "systems": "System Component",
            "ecosystem": "Ecosystem Context",
            "concepts": "Concept",
            "frontier": "Frontier Exploration",
            "storyboards": "Product Storyboard",
            "podcasts": "Podcast Episode",
            "playbooks": "Playbook",
            "research": "Research Notes",
            "interviews": "Interview Notes",
            "references": "Reference",
            "skills": "Skill",
            "templates": "Template"
        }
        if folder in mapping:
            return mapping[folder]
    return "Concept"


def infer_title(content: str, fallback_stem: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return fallback_stem.replace("-", " ").replace("_", " ").title()


def infer_description(content: str, title: str) -> str:
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith("---") or stripped.startswith("```"):
            continue
        if stripped.startswith("* ") or stripped.startswith("- "):
            stripped = stripped[2:].strip()
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", stripped)
        if len(cleaned) > 10:
            return cleaned[:150].replace('"', '\\"')
    return f"Documentation and specification for {title}."


def fix_frontmatter(content: str, rel_path: Path):
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_type = infer_doc_type(rel_path)
    default_status = "stable" if str(rel_path).startswith(("ecosystem/", "systems/", "references/")) else "draft"
    
    fixes_applied = []
    
    # Case 1: No frontmatter block
    if not content.startswith("---"):
        title = infer_title(content, rel_path.stem)
        desc = infer_description(content, title)
        fm = f"""---
type: {doc_type}
title: "{title}"
description: "{desc}"
status: {default_status}
generated:
  by: agent:antigravity
  at: {now_iso}
verified: []
---

"""
        fixes_applied.append(f"Added OKF v0.2 frontmatter block (type: {doc_type})")
        return fm + content, fixes_applied

    # Case 2: Unclosed or malformed frontmatter block
    parts = content.split("---", 2)
    if len(parts) < 3:
        title = infer_title(content, rel_path.stem)
        desc = infer_description(content, title)
        fm = f"""---
type: {doc_type}
title: "{title}"
description: "{desc}"
status: {default_status}
generated:
  by: agent:antigravity
  at: {now_iso}
verified: []
---

"""
        fixes_applied.append("Fixed unclosed/malformed frontmatter block")
        return fm + parts[-1].lstrip(), fixes_applied
        
    raw_yaml = parts[1]
    body = parts[2]
    meta, _ = parse_yaml_frontmatter(content)
    
    yaml_lines = raw_yaml.splitlines()
    
    # Check type
    if not meta or "type" not in meta or not meta["type"]:
        insert_idx = 1 if len(yaml_lines) > 0 and not yaml_lines[0].strip() else 0
        yaml_lines.insert(insert_idx, f"type: {doc_type}")
        fixes_applied.append(f"Added missing required 'type: {doc_type}'")
        
    # Check title
    if not meta or "title" not in meta:
        title = infer_title(body, rel_path.stem)
        yaml_lines.append(f'title: "{title}"')
        fixes_applied.append("Added missing 'title'")
        
    # Check description
    if not meta or "description" not in meta:
        title = meta.get("title") if meta else None
        if not title:
            title = infer_title(body, rel_path.stem)
        desc = infer_description(body, title)
        yaml_lines.append(f'description: "{desc}"')
        fixes_applied.append("Added missing 'description'")
        
    # Check status
    if meta and "status" in meta and meta["status"] not in ["draft", "stable", "deprecated"]:
        for idx, line in enumerate(yaml_lines):
            if re.match(r"^status\s*:", line):
                yaml_lines[idx] = f"status: {default_status}"
                fixes_applied.append(f"Normalized invalid status to '{default_status}'")
                break
    elif not meta or "status" not in meta:
        yaml_lines.append(f"status: {default_status}")
        fixes_applied.append(f"Added status: {default_status}")
        
    new_yaml = "\n".join(yaml_lines)
    if not new_yaml.startswith("\n"):
        new_yaml = "\n" + new_yaml
    if not new_yaml.endswith("\n"):
        new_yaml = new_yaml + "\n"
        
    return f"---{new_yaml}---{body}", fixes_applied


def fix_links_in_markdown(text: str, bundle_dir: Path, file_path: Path):
    changed = False
    parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
    
    def replace_link(match):
        nonlocal changed
        link_text = match.group(1)
        raw_url = match.group(2)
        
        if raw_url.startswith(("http://", "https://", "mailto:", "file://", "#")):
            return match.group(0)
            
        anchor = ""
        url = raw_url
        if "#" in raw_url:
            url, anchor = raw_url.split("#", 1)
            anchor = "#" + anchor
            
        if not url:
            return match.group(0)
            
        # Target path resolution
        if url.startswith("/"):
            target_path = bundle_dir / url.lstrip("/")
        else:
            target_path = (file_path.parent / url).resolve()
            
        if target_path.exists():
            return match.group(0)
            
        # Check missing .md extension
        if not target_path.suffix:
            candidate = target_path.with_suffix(".md")
            if candidate.exists():
                changed = True
                return f"[{link_text}]({url}.md{anchor})"
                
        # Check if relative should be bundle-relative
        if not url.startswith("/"):
            bundle_candidate = bundle_dir / url.lstrip("./")
            if bundle_candidate.exists():
                changed = True
                return f"[{link_text}](/{url.lstrip('./')}{anchor})"
            elif not bundle_candidate.suffix and bundle_candidate.with_suffix(".md").exists():
                changed = True
                return f"[{link_text}](/{url.lstrip('./')}.md{anchor})"
                
        return match.group(0)
        
    for i in range(len(parts)):
        # Even indices are outside code blocks
        if i % 2 == 0:
            inline_parts = re.split(r"(`[^`\n]+`)", parts[i])
            for j in range(len(inline_parts)):
                if j % 2 == 0:
                    inline_parts[j] = re.sub(r"\[([^\]]+)\]\((/[^)]+|\.[^)]+)\)", replace_link, inline_parts[j])
            parts[i] = "".join(inline_parts)
            
    return "".join(parts), changed


def fix_bundle(bundle_dir: Path) -> list:
    """Automatically fixes schema issues, missing frontmatter, links, and refreshes index."""
    fixes = []
    
    # 1. Synchronize root index.md
    try:
        script_dir = Path(__file__).resolve().parent
        if (script_dir / "update_index.py").exists():
            sys.path.insert(0, str(script_dir))
            from update_index import generate_index
            generate_index(bundle_dir)
            fixes.append("[index.md] Synchronized root index with all concept documents.")
    except Exception as ex:
        fixes.append(f"[index.md] Failed to update index: {ex}")
        
    # 2. Iterate all markdown files (exempting archive and hidden files)
    for file_path in sorted(bundle_dir.rglob("*.md")):
        if "archive" in file_path.parts or file_path.name.startswith("."):
            continue
        rel = file_path.relative_to(bundle_dir)
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue
        original_content = content
        
        # Reserved: index.md
        if file_path.name == "index.md":
            if file_path != bundle_dir / "index.md":
                # Subdirectory index must NOT have frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        content = parts[2].lstrip()
                        fixes.append(f"[{rel}] Stripped illegal frontmatter from subdirectory index.md (OKF §8).")
        # Reserved: log.md
        elif file_path.name == "log.md":
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].lstrip()
                    fixes.append(f"[{rel}] Stripped illegal frontmatter from log.md (OKF §9).")
            if not re.search(r"^## (\d{4}-\d{2}-\d{2})", content, re.MULTILINE):
                today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                content = f"## {today_str}\n* Automated sync & maintenance.\n\n" + content
                fixes.append(f"[{rel}] Added missing ISO 8601 date heading.")
        # Concept files
        else:
            fixed_fm, fm_fixes = fix_frontmatter(content, rel)
            if fm_fixes:
                content = fixed_fm
                for msg in fm_fixes:
                    fixes.append(f"[{rel}] {msg}")
                    
            fixed_links, link_ch = fix_links_in_markdown(content, bundle_dir, file_path)
            if link_ch:
                content = fixed_links
                fixes.append(f"[{rel}] Repaired broken links (missing .md extension or relative path).")
                
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
            
    return fixes


def validate_concept_graph(bundle_dir: Path, errors: list, warnings: list) -> dict:
    """
    Validates concept graph integrity:
    1. Cluster membership (no orphan concepts outside cluster matrices when clusters are defined).
    2. Typed relational edge indices in concept documents.
    3. Cross-cluster edge mapping in cluster documents.
    4. Primary source provenance (sources: frontmatter block) for stable concepts.
    """
    concepts_dir = bundle_dir / "concepts"
    stats = {
        "clusters_count": 0,
        "nodes_count": 0,
        "concept_edges": 0,
        "cluster_edges": 0,
        "orphans_count": 0
    }
    if not concepts_dir.is_dir():
        return stats
        
    cluster_files = []
    concept_files = []
    cluster_members = set()
    
    for f in sorted(concepts_dir.glob("*.md")):
        if f.name.startswith("cluster-"):
            cluster_files.append(f)
        elif f.name != ".gitkeep":
            concept_files.append(f)
            
    stats["clusters_count"] = len(cluster_files)
    stats["nodes_count"] = len(concept_files)
    
    # 1. Parse cluster documents for constituent concept membership
    for cf in cluster_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except Exception:
            continue
        targets = re.findall(r"\[.*?\]\((/concepts/[a-zA-Z0-9_\-]+(?:\.md)?)\)", content)
        for t in targets:
            slug = t.split("/")[-1]
            if not slug.endswith(".md"):
                slug += ".md"
            cluster_members.add(slug)
            
        # Parse cross-cluster edges
        cross_rows = re.findall(r"\|\s*\*{0,2}\[.*?\]\((/[^)]+)\)\*{0,2}\s*\|\s*\*([^*]+)\*\s*\|\s*\*{0,2}\[.*?\]\((/[^)]+)\)\*{0,2}\s*\|", content)
        stats["cluster_edges"] += len(cross_rows)

    # 2. Check for orphan concepts (only if cluster files are actively defined)
    if cluster_files:
        for cf in concept_files:
            try:
                c_content = cf.read_text(encoding="utf-8")
                c_meta, _ = parse_yaml_frontmatter(c_content)
                if c_meta and (c_meta.get("is_anchor") or c_meta.get("role") == "anchor"):
                    continue
            except Exception:
                pass
            if cf.name not in cluster_members:
                warnings.append(f"[concepts/{cf.name}] Orphan Concept: not registered in any Concept Cluster constituent matrix.")
                stats["orphans_count"] += 1

    # 3. Check typed relational edge indices in concept documents
    for cf in concept_files:
        try:
            content = cf.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = cf.relative_to(bundle_dir)
        
        # Check edge rows e.g. | **Outbound** | **[Title](/concepts/slug.md)** | *Verb* | ...
        rows = re.findall(r"\|\s*\*{0,2}(?:Outbound|Inbound)\*{0,2}\s*\|\s*\*{0,2}\[.*?\]\((/[^)]+)\)\*{0,2}\s*\|\s*\*([^*]+)\*\s*\|", content)
        stats["concept_edges"] += len(rows)
        for target_link, rel_type in rows:
            clean_verb = rel_type.strip()
            if len(clean_verb) < 2:
                warnings.append(f"[{rel}] Empty or invalid relationship type verb '{rel_type}' in Relational Edge Index.")

        # 4. Check external source provenance on stable concepts
        meta, _ = parse_yaml_frontmatter(content)
        if meta and meta.get("status") == "stable":
            sources = meta.get("sources")
            if not sources:
                warnings.append(f"[{rel}] Missing 'sources:' frontmatter block. Stable concept nodes must declare primary external sources.")
            elif isinstance(sources, list):
                for s in sources:
                    if isinstance(s, dict):
                        if not s.get("id") or not s.get("resource"):
                            warnings.append(f"[{rel}] Malformed entry in 'sources:' block (requires 'id' and 'resource').")

    return stats


def validate_bundle(bundle_dir: Path, fix: bool = False):
    if not bundle_dir.is_dir():
        print(f"ERROR: Bundle directory {bundle_dir} does not exist.")
        return 1

    if fix:
        print("🔧 Auto-fixing OKF bundle...")
        applied_fixes = fix_bundle(bundle_dir)
        if applied_fixes:
            print(f"Applied {len(applied_fixes)} fix(es):")
            for fix_item in applied_fixes:
                print(f"  ✔ {fix_item}")
            print()
        else:
            print("  ✔ No fixes needed (bundle structure is clean).\n")

    errors = []
    warnings = []
    concepts_count = 0
    trust_tiers = {"human-reviewed": 0, "machine-confirmed": 0, "unverified": 0}

    md_files = [f for f in bundle_dir.rglob("*.md") if "archive" not in f.parts and not f.name.startswith(".")]
    print(f"🔍 Validating self-contained OKF bundle at: {bundle_dir} ({len(md_files)} active markdown files)\n")

    for file_path in md_files:
        rel_path = file_path.relative_to(bundle_dir)
        content = file_path.read_text(encoding="utf-8")
        
        # Check reserved file: index.md
        if file_path.name == "index.md":
            meta, body = parse_yaml_frontmatter(content)
            if file_path == bundle_dir / "index.md":
                # Root index.md: may have okf_version
                if meta and "okf_version" not in meta:
                    warnings.append(f"[{rel_path}] Root index.md frontmatter should declare 'okf_version' (e.g. '0.2').")
            else:
                if meta:
                    errors.append(f"[{rel_path}] Subdirectory index.md MUST NOT have frontmatter (OKF §8).")
            continue
            
        # Check reserved file: log.md
        if file_path.name == "log.md":
            meta, body = parse_yaml_frontmatter(content)
            if meta:
                errors.append(f"[{rel_path}] log.md MUST NOT contain YAML frontmatter (OKF §9).")
            # Verify date headings
            date_headings = re.findall(r"^## (\d{4}-\d{2}-\d{2})", body, re.MULTILINE)
            if not date_headings:
                warnings.append(f"[{rel_path}] log.md contains no ISO 8601 date headings (## YYYY-MM-DD).")
            continue
            
        # All other files are Concept documents (§4)
        concepts_count += 1
        meta, body = parse_yaml_frontmatter(content)
        
        if not meta:
            errors.append(f"[{rel_path}] Missing YAML frontmatter block delimited by '---'.")
            continue
            
        # REQUIRED: type
        if "type" not in meta or not meta["type"]:
            errors.append(f"[{rel_path}] Missing REQUIRED 'type' field in frontmatter.")
            
        # RECOMMENDED: title, description
        if "title" not in meta:
            warnings.append(f"[{rel_path}] Recommended field 'title' is missing.")
        if "description" not in meta:
            warnings.append(f"[{rel_path}] Recommended field 'description' is missing.")
            
        # Status check
        status = meta.get("status", "stable")
        if status not in ["draft", "stable", "deprecated"]:
            errors.append(f"[{rel_path}] Invalid status '{status}'. Must be draft, stable, or deprecated.")
            
        # Stale after check
        if "stale_after" in meta:
            try:
                stale_dt = datetime.fromisoformat(meta["stale_after"].replace("Z", "+00:00"))
                if datetime.now(stale_dt.tzinfo) >= stale_dt:
                    warnings.append(f"[{rel_path}] Concept is STALE (stale_after: {meta['stale_after']}).")
            except Exception:
                errors.append(f"[{rel_path}] Malformed stale_after datetime: {meta['stale_after']}.")
                
        # Trust tier determination
        verified = meta.get("verified")
        if not verified:
            trust_tiers["unverified"] += 1
        else:
            ver_list = verified if isinstance(verified, list) else [verified]
            has_human = any(isinstance(v, dict) and v.get("by", "").startswith("human:") for v in ver_list)
            if has_human:
                trust_tiers["human-reviewed"] += 1
            else:
                trust_tiers["machine-confirmed"] += 1

        # Link validation in body (excluding code blocks and inline code)
        clean_body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        clean_body = re.sub(r"`[^`\n]+`", "", clean_body)
        links = re.findall(r"\[.*?\]\((/[^)]+|\.[^)]+)\)", clean_body)
        for link in links:
            # Strip anchors e.g. #section
            clean_link = link.split("#")[0]
            if not clean_link:
                continue
            if clean_link.startswith("/"):
                target = bundle_dir / clean_link.lstrip("/")
            else:
                target = (file_path.parent / clean_link).resolve()
                
            if not target.exists():
                # Starter templates and skill templates contain illustrative example links for authors;
                # exempt templates from target existence checks to prevent false positives when samples are removed.
                if "templates" not in file_path.parts:
                    warnings.append(f"[{rel_path}] Broken link to '{link}'. Target does not exist.")

    # Concept Graph Validation
    graph_stats = validate_concept_graph(bundle_dir, errors, warnings)

    # Summary
    print("=" * 60)
    print("OKF BUNDLE VALIDATION REPORT")
    print("=" * 60)
    print(f"Total Concept Documents: {concepts_count}")
    print(f"Trust Tiers:")
    print(f"  • Human-reviewed:   {trust_tiers['human-reviewed']}")
    print(f"  • Machine-confirmed: {trust_tiers['machine-confirmed']}")
    print(f"  • Unverified:        {trust_tiers['unverified']}")
    if graph_stats.get("clusters_count") or graph_stats.get("nodes_count"):
        print("-" * 60)
        print("Concept Graph & Mind Map Integrity:")
        print(f"  • Thematic Clusters:     {graph_stats['clusters_count']}")
        print(f"  • Concept Nodes:         {graph_stats['nodes_count']}")
        print(f"  • Typed Concept Edges:   {graph_stats['concept_edges']}")
        print(f"  • Cluster Cross-Edges:   {graph_stats['cluster_edges']}")
        print(f"  • Orphan Concepts:       {graph_stats['orphans_count']}")
    print("-" * 60)
    
    if warnings:
        print(f"⚠️  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"❌ ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print("\nResult: FAILED ❌")
        return 1

    print("Result: PASSED ✅ (Fully conformant with OKF v0.2)")
    return 0


if __name__ == "__main__":
    default_bundle_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Validate and repair Google OKF v0.2 bundle.")
    parser.add_argument("bundle_root", nargs="?", default=default_bundle_root, type=Path, help="Path to bundle root")
    parser.add_argument("--fix", action="store_true", help="Automatically repair frontmatter, links, reserved files, and index")
    args = parser.parse_args()
    
    sys.exit(validate_bundle(args.bundle_root, fix=args.fix))
