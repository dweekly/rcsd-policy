#!/usr/bin/env python3
"""
Build Ed Code database from citations in compliance findings
This will create a list of all Ed Code sections that need to be fetched
"""

import json
from pathlib import Path
from collections import defaultdict


def build_database():
    """Build list of all Ed Code sections to fetch"""
    
    # Load the citation summary
    with open("data/analysis/ed_code_citations_summary.json") as f:
        data = json.load(f)
    
    print("ED CODE DATABASE BUILD PLAN")
    print("="*80)
    print()
    
    total_unique = len(data["most_cited"])
    print(f"Total unique Ed Code sections to fetch: {total_unique}")
    print()
    
    # Group by frequency for prioritization
    frequency_groups = defaultdict(list)
    for section, count in data["most_cited"]:
        if count >= 10:
            frequency_groups["high"].append((section, count))
        elif count >= 5:
            frequency_groups["medium"].append((section, count))
        else:
            frequency_groups["low"].append((section, count))
    
    print(f"High frequency (10+ citations): {len(frequency_groups['high'])} sections")
    print(f"Medium frequency (5-9 citations): {len(frequency_groups['medium'])} sections")
    print(f"Low frequency (1-4 citations): {len(frequency_groups['low'])} sections")
    print()
    
    # Create fetch list files
    output_dir = Path("data/analysis/edcode_fetch_lists")
    output_dir.mkdir(exist_ok=True)
    
    # High priority sections
    high_file = output_dir / "high_priority_sections.txt"
    with open(high_file, 'w') as f:
        f.write("# High Priority Ed Code Sections (10+ citations)\n")
        f.write("# Format: section_number | citation_count | url\n\n")
        for section, count in frequency_groups["high"]:
            url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC"
            f.write(f"{section} | {count} | {url}\n")
    
    print(f"High priority list saved to: {high_file}")
    
    # Check what we already have cached
    cache_dir = Path("data/cache/edcode")
    cached_sections = set()
    if cache_dir.exists():
        for cache_file in cache_dir.glob("*.json"):
            if "_full" in cache_file.name:
                # Extract section from filename like "edc_15282_full.json"
                section = cache_file.stem.replace("edc_", "").replace("_full", "").replace("_", ".")
                cached_sections.add(section)
    
    print(f"\nAlready cached (full text): {len(cached_sections)} sections")
    if cached_sections:
        print("Cached sections:", ", ".join(sorted(cached_sections)[:10]), "...")
    
    # Sections still needed
    all_sections = [s for s, _ in data["most_cited"]]
    needed_sections = [s for s in all_sections if s not in cached_sections]
    print(f"\nStill need to fetch: {len(needed_sections)} sections")
    
    # Create a fetch script
    fetch_script = output_dir / "fetch_commands.txt"
    with open(fetch_script, 'w') as f:
        f.write("# Commands to fetch Ed Code sections\n")
        f.write("# Run these one at a time in Claude Code using WebFetch\n\n")
        
        # Start with high priority sections not yet cached
        high_priority_needed = [s for s, _ in frequency_groups["high"] if s not in cached_sections]
        
        f.write(f"# HIGH PRIORITY - {len(high_priority_needed)} sections\n")
        for section in high_priority_needed[:20]:  # First 20
            f.write(f"\n# Section {section}\n")
            f.write(f"WebFetch URL: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC\n")
            f.write(f"Prompt: Extract the complete text of Education Code Section {section}, including all subsections.\n")
    
    print(f"Fetch commands saved to: {fetch_script}")
    
    # Summary of what's needed
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Fetch high-priority Ed Code sections using WebFetch")
    print("2. Run verification on all compliance findings")
    print("3. Generate report showing which findings are verified vs. problematic")
    
    return needed_sections, cached_sections


if __name__ == "__main__":
    needed, cached = build_database()