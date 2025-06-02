#!/usr/bin/env python3
"""
Fetch all Ed Code sections needed to validate material errors
This script processes the sections in batches and handles different law codes
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import time
import sys


# Known section mappings discovered during our analysis
KNOWN_MAPPINGS = {
    "1031": ("LAB", "Lactation Accommodation Requirements"),
    "1032": ("LAB", "Lactation Accommodation - Serious Disruption Exception"), 
    "1033": ("LAB", "Lactation Accommodation - Enforcement and Penalties"),
    "11165.7": ("PEN", "Mandated Reporter Definition"),
    "12517.2": ("VC", "Medical Examination Requirements for School Bus Drivers"),
    "12523": ("VC", "Training Hour Requirements for School Bus Drivers"),
    "12945.2": ("GOV", "California Family Rights Act"),
    "12950.1": ("GOV", "Sexual Harassment Prevention Training Requirements"),
    "13181": ("FAC", "Integrated Pest Management Definition"),
    "20111": ("PCC", "School District Competitive Bidding Requirements"),
    "20113": ("PCC", "Emergency Purchase Procedures for School Districts"),
}


def get_all_needed_sections():
    """Extract all Ed Code sections from compliance findings that need verification"""
    
    # Load from the all_fetch_commands.json if it exists
    commands_file = Path("scripts/all_fetch_commands.json")
    if commands_file.exists():
        with open(commands_file) as f:
            commands = json.load(f)
        
        # Process and fix known mappings
        processed = []
        for cmd in commands:
            section = cmd['section']
            if section in KNOWN_MAPPINGS:
                actual_code, description = KNOWN_MAPPINGS[section]
                cmd['law_code'] = actual_code
                cmd['description'] = description
                cmd['url'] = cmd['url'].replace('lawCode=EDC', f'lawCode={actual_code}')
                cmd['prompt'] = f"Extract the complete text of {actual_code} section {section} regarding {description}. Include all subdivisions, requirements, and the effective date."
            processed.append(cmd)
        
        return processed
    
    return []


def check_if_cached(section, law_code):
    """Check if a section is already cached"""
    safe_section = section.replace(".", "_")
    cache_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    return cache_file.exists()


def get_fetch_progress():
    """Get current fetch progress"""
    cache_dir = Path("data/cache/edcode")
    if not cache_dir.exists():
        return 0
    
    return len(list(cache_dir.glob("*.json")))


def generate_fetch_batch(all_sections, batch_size=10):
    """Generate next batch of sections to fetch"""
    
    to_fetch = []
    for cmd in all_sections:
        if not check_if_cached(cmd['section'], cmd['law_code']):
            to_fetch.append(cmd)
            if len(to_fetch) >= batch_size:
                break
    
    return to_fetch


def create_fetch_commands(batch):
    """Create structured fetch commands for the batch"""
    
    commands = []
    for cmd in batch:
        safe_section = cmd['section'].replace(".", "_")
        output_file = f"data/cache/edcode/{cmd['law_code'].lower()}_{safe_section}_full.json"
        
        commands.append({
            "section": cmd['section'],
            "law_code": cmd['law_code'],
            "url": cmd['url'],
            "prompt": cmd['prompt'],
            "description": cmd.get('description', ''),
            "output_file": output_file
        })
    
    return commands


def save_batch_manifest(batch_num, commands):
    """Save batch manifest for tracking"""
    
    manifest = {
        "batch_number": batch_num,
        "generated": datetime.now(timezone.utc).isoformat(),
        "count": len(commands),
        "commands": commands
    }
    
    manifest_file = Path(f"data/cache/manifests/batch_{batch_num:03d}.json")
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_file


def process_batch_with_webfetch(commands):
    """Process a batch of commands using WebFetch
    Note: This is a placeholder - actual WebFetch calls need to be made through Claude
    """
    
    print("\nFetch Commands for this batch:")
    print("=" * 60)
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i}. {cmd['law_code']} Section {cmd['section']}")
        if cmd['description']:
            print(f"   Description: {cmd['description']}")
        print(f"   URL: {cmd['url']}")
        print(f"   Output: {cmd['output_file']}")
        print("\n   WebFetch command:")
        print(f"   WebFetch(")
        print(f'     url="{cmd["url"]}",')
        print(f'     prompt="{cmd["prompt"]}"')
        print(f"   )")
    
    print("\n" + "=" * 60)
    print(f"Total sections in this batch: {len(commands)}")


def main():
    """Main function to coordinate fetching"""
    
    print("Ed Code Fetcher for Material Error Validation")
    print("=" * 60)
    
    # Get all sections needed
    all_sections = get_all_needed_sections()
    if not all_sections:
        print("No sections found to fetch. Run generate_all_fetch_commands.py first.")
        return
    
    # Get current progress
    initial_count = get_fetch_progress()
    total_needed = len(all_sections)
    
    print(f"Total sections needed: {total_needed}")
    print(f"Already cached: {initial_count}")
    
    # Check how many still need fetching
    remaining = []
    for section in all_sections:
        if not check_if_cached(section['section'], section['law_code']):
            remaining.append(section)
    
    print(f"Sections to fetch: {len(remaining)}")
    
    if not remaining:
        print("\nAll sections have been fetched!")
        return
    
    # Process in batches
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    batch_num = 0
    
    while remaining:
        batch = remaining[:batch_size]
        remaining = remaining[batch_size:]
        
        print(f"\n\nBatch {batch_num + 1}")
        print("-" * 40)
        
        # Create fetch commands
        commands = create_fetch_commands(batch)
        
        # Save manifest
        manifest_file = save_batch_manifest(batch_num, commands)
        print(f"Manifest saved: {manifest_file}")
        
        # Show fetch commands
        process_batch_with_webfetch(commands)
        
        batch_num += 1
        
        if remaining:
            print(f"\n{len(remaining)} sections remaining in future batches")
            response = input("\nPress Enter to see next batch, or 'q' to quit: ")
            if response.lower() == 'q':
                break
    
    print("\n\nSummary:")
    print(f"Generated {batch_num} batch manifests")
    print(f"Total sections to fetch: {sum(len(c) for c in [remaining[:batch_size] for _ in range(0, len(remaining), batch_size)])}")
    print("\nNext steps:")
    print("1. Use the WebFetch commands above to fetch each section")
    print("2. Save results in the specified output files using standard format")
    print("3. Run verification scripts once all sections are fetched")


if __name__ == "__main__":
    main()