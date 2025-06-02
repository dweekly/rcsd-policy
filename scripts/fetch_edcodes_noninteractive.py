#!/usr/bin/env python3
"""
Non-interactive version of Ed Code fetcher
Generates all batches at once for systematic processing
"""

import json
from pathlib import Path
from datetime import datetime, timezone


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


def generate_all_batches():
    """Generate all fetch batches at once"""
    
    all_sections = get_all_needed_sections()
    if not all_sections:
        print("No sections found to fetch.")
        return
    
    # Filter out already cached
    to_fetch = []
    cached_count = 0
    
    for section in all_sections:
        if check_if_cached(section['section'], section['law_code']):
            cached_count += 1
        else:
            to_fetch.append(section)
    
    print(f"Total sections: {len(all_sections)}")
    print(f"Already cached: {cached_count}")
    print(f"To fetch: {len(to_fetch)}")
    
    if not to_fetch:
        print("\nAll sections are already cached!")
        return
    
    # Generate batches
    batch_size = 5
    batches = []
    
    for i in range(0, len(to_fetch), batch_size):
        batch = to_fetch[i:i + batch_size]
        batch_commands = []
        
        for cmd in batch:
            safe_section = cmd['section'].replace(".", "_")
            output_file = f"data/cache/edcode/{cmd['law_code'].lower()}_{safe_section}_full.json"
            
            batch_commands.append({
                "section": cmd['section'],
                "law_code": cmd['law_code'],
                "url": cmd['url'],
                "prompt": cmd['prompt'],
                "description": cmd.get('description', ''),
                "output_file": output_file
            })
        
        batches.append(batch_commands)
    
    # Save master batch file
    master_file = Path("scripts/edcode_fetch_batches.json")
    with open(master_file, 'w') as f:
        json.dump({
            "generated": datetime.now(timezone.utc).isoformat(),
            "total_sections": len(to_fetch),
            "batch_size": batch_size,
            "num_batches": len(batches),
            "batches": batches
        }, f, indent=2)
    
    print(f"\nGenerated {len(batches)} batches")
    print(f"Master batch file: {master_file}")
    
    # Show first batch as example
    print("\nFirst batch example:")
    print("=" * 60)
    for cmd in batches[0]:
        print(f"\n{cmd['law_code']} {cmd['section']}: {cmd['description']}")
        print(f"URL: {cmd['url']}")


def main():
    generate_all_batches()


if __name__ == "__main__":
    main()