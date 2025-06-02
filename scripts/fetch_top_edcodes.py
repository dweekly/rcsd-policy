#!/usr/bin/env python3
"""
Script to help fetch top Ed Code sections using WebFetch
This generates the commands needed to fetch each section
"""

import json
from pathlib import Path


def main():
    # Load the citation summary
    with open("data/analysis/ed_code_citations_summary.json") as f:
        data = json.load(f)
    
    print("Top Ed Code Sections to Fetch")
    print("="*60)
    print()
    
    # Get top 20 most cited sections
    top_sections = data["most_cited"][:20]
    
    print("To fetch these sections, use WebFetch with these URLs:")
    print()
    
    for section, count in top_sections:
        print(f"# Section {section} (cited {count} times)")
        print(f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC")
        print()
    
    # Also show sections we know are problematic
    print("\nProblematic Sections to Verify:")
    print("-"*40)
    
    known_issues = {
        "15278": "Incorrectly cited for term requirements (should be 15282)",
        "15282": "Contains actual term requirements for bond oversight committees",
        "15280": "Contains report publication requirements",
        "44050": "Often cited - verify actual requirements",
        "35160": "Most cited section - board authority"
    }
    
    for section, note in known_issues.items():
        print(f"\nSection {section}: {note}")
        print(f"URL: https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC")


if __name__ == "__main__":
    main()