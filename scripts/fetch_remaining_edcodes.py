#!/usr/bin/env python3
"""
Generate a prioritized list of Ed Code sections that still need to be fetched
"""

import json
from pathlib import Path
from collections import Counter


def get_remaining_sections():
    # Load citation data
    with open("data/analysis/ed_code_citations_summary.json") as f:
        citation_data = json.load(f)
    
    # Get cached sections
    cache_dir = Path("data/cache/edcode")
    cached = set()
    for file in cache_dir.glob("*_full.json"):
        section = file.stem.replace("edc_", "").replace("_full", "").replace("_", ".")
        cached.add(section)
    
    print(f"Currently cached: {len(cached)} sections")
    print(f"Cached: {', '.join(sorted(cached))}\n")
    
    # Get sections from v2 verification report
    verification_file = Path("data/analysis/compliance_v2_verification_data.json")
    if verification_file.exists():
        with open(verification_file) as f:
            ver_data = json.load(f)
        
        # Count sections that appear in problematic findings
        problem_sections = Counter()
        for finding in ver_data.get("problematic_findings", []):
            for issue in finding.get("issues", []):
                for problem in issue.get("problems", []):
                    section = problem.get("section")
                    if section and section not in cached:
                        problem_sections[section] += 1
        
        print("TOP PRIORITY - Sections in problematic findings (not cached):")
        print("-" * 60)
        for section, count in problem_sections.most_common(20):
            print(f"{section}: {count} problematic citations")
            print(f"  URL: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC")
            print()
    
    # Also show overall most cited that aren't cached
    print("\nHIGH PRIORITY - Most cited overall (not cached):")
    print("-" * 60)
    
    needed_count = 0
    for section, count in citation_data["most_cited"]:
        if section not in cached:
            if needed_count < 10:
                print(f"{section}: {count} total citations")
                print(f"  URL: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC")
                print()
            needed_count += 1
    
    print(f"\nTotal sections still needed: {needed_count}")
    
    # Save prioritized fetch list
    output_file = Path("data/analysis/edcode_fetch_lists/priority_fetch_list.txt")
    with open(output_file, 'w') as f:
        f.write("# Priority Ed Code Sections to Fetch\n")
        f.write(f"# Generated with {len(cached)} sections already cached\n\n")
        
        f.write("## TOP PRIORITY - In Problematic Findings\n")
        for section, count in problem_sections.most_common():
            f.write(f"{section} | {count} problems | https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC\n")
        
        f.write("\n## HIGH PRIORITY - Most Cited Overall\n")
        for section, count in citation_data["most_cited"]:
            if section not in cached and section not in problem_sections:
                f.write(f"{section} | {count} citations | https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC\n")
    
    print(f"\nPriority fetch list saved to: {output_file}")


if __name__ == "__main__":
    get_remaining_sections()