#!/usr/bin/env python3
"""
Parallel fetch system for Ed Code sections
Generates batched commands for efficient fetching
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone


def get_missing_sections():
    """Extract missing sections from validation results"""
    
    # Load validation results
    validation_file = Path("data/analysis/v2_validation_results.json")
    if not validation_file.exists():
        print("Run validate_v2_compliance.py first!")
        return []
    
    with open(validation_file) as f:
        data = json.load(f)
    
    # Extract NOT_CACHED citations
    missing = []
    for validation in data["validations"]:
        if validation["status"] == "NOT_CACHED":
            missing.append({
                "section": validation["section"],
                "law_code": validation["law_code"],
                "policy": validation["policy_code"],
                "issue": validation["issue_title"]
            })
    
    return missing


def prioritize_sections(missing_list):
    """Group and prioritize sections by frequency"""
    
    # Count occurrences
    section_counts = Counter()
    section_details = {}
    
    for item in missing_list:
        key = f"{item['law_code']}_{item['section']}"
        section_counts[key] += 1
        
        if key not in section_details:
            section_details[key] = {
                "section": item["section"],
                "law_code": item["law_code"],
                "policies": set(),
                "issues": set()
            }
        
        section_details[key]["policies"].add(item["policy"])
        section_details[key]["issues"].add(item["issue"])
    
    # Create prioritized list
    prioritized = []
    for key, count in section_counts.most_common():
        details = section_details[key]
        prioritized.append({
            "section": details["section"],
            "law_code": details["law_code"],
            "count": count,
            "num_policies": len(details["policies"]),
            "sample_issue": list(details["issues"])[0] if details["issues"] else ""
        })
    
    return prioritized


def check_already_cached():
    """Get list of already cached sections"""
    cache_dir = Path("data/cache/edcode")
    cached = set()
    
    for file in cache_dir.glob("*.json"):
        # Extract law code and section from filename
        parts = file.stem.split("_")
        if len(parts) >= 2:
            law_code = parts[0].upper()
            section = parts[1]
            if len(parts) > 2 and parts[-1] != "full":
                section = f"{section}.{parts[2]}"
            cached.add(f"{law_code}_{section}")
    
    return cached


def generate_fetch_batches(sections, batch_size=20):
    """Generate fetch commands in batches"""
    
    cached = check_already_cached()
    to_fetch = []
    
    for section_info in sections:
        key = f"{section_info['law_code']}_{section_info['section']}"
        if key not in cached:
            to_fetch.append(section_info)
    
    # Create batches
    batches = []
    for i in range(0, len(to_fetch), batch_size):
        batch = to_fetch[i:i + batch_size]
        batches.append(batch)
    
    return batches


def create_webfetch_commands(batch, batch_num):
    """Create WebFetch commands for a batch"""
    
    commands = []
    
    for item in batch:
        section = item["section"]
        law_code = item["law_code"]
        
        # Generate URL based on law code
        law_code_map = {
            "EDC": "EDC",
            "GOV": "GOV",
            "LAB": "LAB",
            "PEN": "PEN",
            "HSC": "HSC",
            "PCC": "PCC",
            "VC": "VEH",
            "FAC": "FAC"
        }
        
        url_code = law_code_map.get(law_code, law_code)
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode={url_code}"
        
        # Create description from issue
        desc = item.get("sample_issue", "")[:80]
        if not desc:
            desc = f"Referenced in {item.get('num_policies', 1)} policies"
        
        prompt = f"Extract the complete text of {law_code} section {section}. Include all subdivisions, requirements, and the effective date."
        
        safe_section = section.replace(".", "_")
        output_file = f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json"
        
        commands.append({
            "section": section,
            "law_code": law_code,
            "url": url,
            "prompt": prompt,
            "output_file": output_file,
            "description": desc,
            "count": item.get("count", 1)
        })
    
    return commands


def save_batch_manifest(batch_commands, batch_num):
    """Save batch manifest file"""
    
    manifest_dir = Path("data/cache/edcode_manifests")
    manifest_dir.mkdir(exist_ok=True)
    
    manifest = {
        "batch_number": batch_num,
        "generated": datetime.now(timezone.utc).isoformat(),
        "count": len(batch_commands),
        "commands": batch_commands
    }
    
    manifest_file = manifest_dir / f"batch_{batch_num:03d}.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_file


def generate_master_script(num_batches):
    """Generate master script showing all batches"""
    
    script_lines = [
        "#!/bin/bash",
        "# Master script for fetching Ed Code sections",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        f"# Total batches: {num_batches}",
        "",
        "# To process a batch:",
        "# 1. Run: python scripts/process_edcode_batch.py <batch_num>",
        "# 2. Execute the WebFetch commands shown",
        "# 3. Move to next batch",
        "",
        "echo 'Ed Code Batch Fetching System'",
        "echo '============================='",
        "echo",
        f"echo 'Total batches to process: {num_batches}'",
        "echo",
        "",
        "# Process batches",
        f"for i in {{0..{num_batches-1}}}; do",
        "    echo \"Processing batch $i...\"",
        "    python scripts/process_edcode_batch.py $i",
        "    echo",
        "    echo 'Press Enter to continue to next batch...'",
        "    read",
        "done",
        "",
        "echo 'All batches processed!'"
    ]
    
    script_file = Path("scripts/fetch_all_edcodes.sh")
    with open(script_file, 'w') as f:
        f.write("\n".join(script_lines))
    
    return script_file


def main():
    """Main function"""
    
    print("=" * 80)
    print("PARALLEL ED CODE FETCH SYSTEM")
    print("=" * 80)
    
    # Get missing sections
    print("\nAnalyzing missing sections...")
    missing = get_missing_sections()
    print(f"Found {len(missing)} missing citations")
    
    # Prioritize by frequency
    print("\nPrioritizing sections...")
    prioritized = prioritize_sections(missing)
    print(f"Unique sections to fetch: {len(prioritized)}")
    
    # Show top sections
    print("\nTop 20 most-cited missing sections:")
    for item in prioritized[:20]:
        print(f"  {item['law_code']} {item['section']}: {item['count']} citations in {item['num_policies']} policies")
    
    # Generate batches
    batch_size = 20
    print(f"\nGenerating batches (size={batch_size})...")
    batches = generate_fetch_batches(prioritized, batch_size)
    print(f"Created {len(batches)} batches")
    
    # Save all batch manifests
    print("\nSaving batch manifests...")
    for i, batch in enumerate(batches):
        commands = create_webfetch_commands(batch, i)
        manifest_file = save_batch_manifest(commands, i)
        if i < 3:  # Show first few
            print(f"  Batch {i}: {len(commands)} sections -> {manifest_file}")
    
    # Generate master script
    master_script = generate_master_script(len(batches))
    print(f"\nMaster script: {master_script}")
    
    # Save summary
    summary = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "total_missing_citations": len(missing),
        "unique_sections": len(prioritized),
        "num_batches": len(batches),
        "batch_size": batch_size,
        "top_sections": prioritized[:50]
    }
    
    summary_file = Path("data/cache/edcode_fetch_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    
    # Show first batch as example
    if batches:
        print("\n" + "=" * 80)
        print("FIRST BATCH PREVIEW")
        print("=" * 80)
        
        first_batch_commands = create_webfetch_commands(batches[0], 0)
        for i, cmd in enumerate(first_batch_commands[:5], 1):
            print(f"\n{i}. {cmd['law_code']} {cmd['section']} ({cmd['count']} citations)")
            print(f"   {cmd['description']}")
            print(f"   URL: {cmd['url']}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Run: python scripts/process_edcode_batch.py 0")
    print("2. Execute the WebFetch commands for that batch")
    print("3. Continue with subsequent batches")
    print(f"4. Total sections to fetch: {sum(len(b) for b in batches)}")


if __name__ == "__main__":
    main()