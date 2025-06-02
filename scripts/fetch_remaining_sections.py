#!/usr/bin/env python3
"""
Fetch the remaining sections that aren't cached
"""

import json
from pathlib import Path
import sys

# Add the remaining sections from the priority list
remaining_sections = [
    ("45125.1", "EDC", "Criminal background check requirements"),
    ("32282", "EDC", "Comprehensive school safety plan requirements"),
    ("44030.5", "EDC", "Mandatory reporting to CTC"),
    ("48852.7", "EDC", "Educational rights of homeless children"),
    ("49406", "EDC", "Tuberculosis testing requirements"),
    ("32001", "EDC", "Fire alarm and drill requirements"),
    ("39831.5", "EDC", "School bus safety requirements"),
    ("44500", "EDC", "Peer assistance and review"),
    ("11165.7", "PEN", "Mandated reporter definition"),
    ("48852.5", "EDC", "Homeless student liaison"),
    ("51938", "EDC", "Parent inspection rights - sex ed"),
    ("51747.5", "EDC", "Independent study attendance"),
    ("51747", "EDC", "Independent study"),
    ("39831", "EDC", "School bus requirements"),
    ("45125", "EDC", "Fingerprinting requirements"),
    ("12945", "GOV", "Family leave"),
    ("51937", "EDC", "Parent notification - sex ed"),
]

def generate_fetch_commands():
    """Generate commands for fetching remaining sections"""
    
    commands = []
    
    for section, law_code, description in remaining_sections:
        # Check if already cached
        safe_section = section.replace(".", "_")
        cache_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
        
        if cache_file.exists():
            # Check if it's one of the corrupted files
            try:
                with open(cache_file) as f:
                    json.load(f)
                continue  # File is good
            except:
                print(f"Corrupted file: {cache_file}")
                # Continue to re-fetch
        
        # Map law codes to URL format
        url_map = {
            "EDC": "EDC",
            "GOV": "GOV", 
            "PEN": "PEN",
            "VC": "VEH",
            "LAB": "LAB",
            "PCC": "PCC"
        }
        
        url_code = url_map.get(law_code, law_code)
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode={url_code}"
        
        commands.append({
            "section": section,
            "law_code": law_code,
            "url": url,
            "description": description
        })
    
    return commands

# Generate and save commands
commands = generate_fetch_commands()

if commands:
    print(f"Sections to fetch: {len(commands)}")
    for cmd in commands:
        print(f"  {cmd['law_code']} {cmd['section']}: {cmd['description']}")
    
    # Save for bulk fetcher
    with open("scripts/remaining_sections.json", "w") as f:
        json.dump([{
            "section": cmd["section"],
            "law_code": cmd["law_code"],
            "url": cmd["url"],
            "count": 1,
            "description": cmd["description"]
        } for cmd in commands], f, indent=2)
    
    print(f"\nSaved to scripts/remaining_sections.json")
    print("Run: python scripts/bulk_edcode_fetcher.py")
else:
    print("All sections are cached!")