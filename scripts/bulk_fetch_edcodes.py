#!/usr/bin/env python3
"""
Bulk fetch Ed Codes - processes sections efficiently
Generates commands for fetching multiple sections at once
"""

import json
from pathlib import Path
import sys


def load_batch_data():
    """Load the batch data"""
    batch_file = Path("scripts/edcode_fetch_batches.json")
    if not batch_file.exists():
        print("Run fetch_edcodes_noninteractive.py first to generate batches")
        return None
    
    with open(batch_file) as f:
        return json.load(f)


def check_cached():
    """Get list of already cached sections"""
    cache_dir = Path("data/cache/edcode")
    cached = set()
    
    for file in cache_dir.glob("*.json"):
        cached.add(file.name)
    
    return cached


def get_next_sections(batch_data, num_sections=20):
    """Get the next N sections that need fetching"""
    
    cached = check_cached()
    to_fetch = []
    
    for batch in batch_data['batches']:
        for cmd in batch:
            safe_section = cmd['section'].replace(".", "_")
            filename = f"{cmd['law_code'].lower()}_{safe_section}_full.json"
            
            if filename not in cached:
                to_fetch.append(cmd)
                
                if len(to_fetch) >= num_sections:
                    return to_fetch
    
    return to_fetch


def generate_fetch_script(sections):
    """Generate a script with WebFetch commands"""
    
    print(f"# Bulk Ed Code Fetch - {len(sections)} sections")
    print(f"# Copy and execute these WebFetch commands")
    print("=" * 60)
    print()
    
    for i, cmd in enumerate(sections, 1):
        print(f"# {i}. {cmd['law_code']} Section {cmd['section']}")
        if cmd['description']:
            print(f"#    {cmd['description']}")
        print()
        print(f"WebFetch(")
        print(f'  url="{cmd["url"]}",')
        print(f'  prompt="{cmd["prompt"]}"')
        print(f")")
        print()
        print(f"# Save to: {cmd['output_file']}")
        print("-" * 40)
        print()
    
    print(f"\n# Total sections: {len(sections)}")
    
    # Also save to a file for reference
    output_file = Path("scripts/current_fetch_batch.json")
    with open(output_file, 'w') as f:
        json.dump({
            "sections": sections,
            "count": len(sections)
        }, f, indent=2)
    
    print(f"# Commands also saved to: {output_file}")


def main():
    """Main function"""
    
    batch_data = load_batch_data()
    if not batch_data:
        return
    
    # Get number of sections to fetch
    num_sections = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    
    # Get cached count
    cached_count = len(check_cached())
    total_needed = batch_data['total_sections']
    
    print(f"# Progress: {cached_count} cached, {total_needed} total needed")
    print()
    
    # Get next sections
    sections = get_next_sections(batch_data, num_sections)
    
    if not sections:
        print("All sections have been fetched!")
        return
    
    generate_fetch_script(sections)


if __name__ == "__main__":
    main()