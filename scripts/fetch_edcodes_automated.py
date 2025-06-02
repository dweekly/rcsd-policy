#!/usr/bin/env python3
"""
Automated Ed Code fetcher that generates fetch commands for Claude Code
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone


# High priority sections from problematic findings
PRIORITY_SECTIONS = [
    # From BP 4200 - Classified Personnel
    ("45240", "EDC", "Merit System Requirements"),
    ("45122", "EDC", "Physical Examination Requirements"),
    ("45113", "EDC", "Probationary Period Requirements"),
    
    # From BP 3300 - Expenditures
    ("20111", "EDC", "Competitive Bidding Requirements"),
    ("20113", "EDC", "Emergency Purchase Procedures"),
    
    # From BP 3514.1 - Hazardous Substances
    ("49410.5", "EDC", "Asbestos Management Requirements"),
    ("17608", "EDC", "Indoor Air Quality Requirements"),
    ("13181", "EDC", "Integrated Pest Management"),
    
    # From BP 3515 - Campus Security
    ("32288", "EDC", "School Safety Plan Review Requirements"),
    ("32281", "EDC", "School Safety Planning Committee"),
    
    # From BP 3541.2 - Transportation for Students with Disabilities
    ("56001", "EDC", "Special Education Intent"),
    ("39831.3", "EDC", "Wheelchair Safety Requirements"),
    ("56341.1", "EDC", "IEP Transportation Requirements"),
    
    # From AR 3542 - School Bus Drivers
    ("35291", "EDC", "Student Discipline on Buses"),
    
    # From BP 4139 - Peer Assistance and Review
    ("44501", "EDC", "Consulting Teacher Requirements"),
    ("44503", "EDC", "Confidentiality Requirements"),
    
    # From BP 5142 - Safety
    ("35295", "EDC", "Comprehensive School Safety Plans"),
    ("44691", "EDC", "Mandated Reporter Training"),
    
    # From BP 5145.12 - Search and Seizure
    ("49050", "EDC", "Student Search Limitations"),
    ("48902", "EDC", "Law Enforcement Coordination"),
    ("44807", "EDC", "Emergency Authority"),
    
    # From BP 6142.8 - Comprehensive Health Education
    ("51210", "EDC", "Required Curriculum Areas"),
    ("51934", "EDC", "Sexual Health Content Standards"),
    
    # From BP 6157 - Distance Learning
    ("47612.5", "EDC", "Distance Learning Instructional Time"),
    ("43503", "EDC", "Daily Live Interaction Requirements"),
    
    # From BP 0420.4 - Charter School Authorization
    ("47607", "EDC", "Charter Renewal and Revocation"),
    
    # From BP 0460 - Local Control and Accountability Plan
    ("52064.3", "EDC", "IDEA Addendum Requirements"),
    ("52064.1", "EDC", "LCFF Budget Overview"),
    ("52063", "EDC", "Advisory Committee Requirements"),
    
    # From BP 1240 - Volunteer Assistance
    ("35021", "EDC", "Volunteer Procedures"),
    
    # Additional high-frequency sections
    ("60200", "EDC", "Records Retention"),
    ("20111", "PCC", "Public Contract Code - Bidding"),
]


def get_cached_sections():
    """Get list of already cached sections"""
    cache_dir = Path("data/cache/edcode")
    cached = set()
    
    for file in cache_dir.glob("*.json"):
        # Extract section from filename
        parts = file.stem.split('_')
        if len(parts) >= 3:
            section = parts[1]
            if len(parts) > 3 and parts[2] != "full":
                section = f"{section}.{parts[2]}"
            cached.add(section)
    
    return cached


def generate_webfetch_command(section, law_code, description):
    """Generate WebFetch command for a section"""
    
    # Map law codes to URLs
    if law_code == "EDC":
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC"
    elif law_code == "PCC":
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=PCC"
    elif law_code == "VC":
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=VEH"
    elif law_code == "GC":
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=GOV"
    elif law_code == "PEN":
        url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=PEN"
    else:
        return None
    
    prompt = f"Extract the complete text of {law_code} section {section} regarding {description}. Include all subdivisions, requirements, and the effective date."
    
    return {
        "url": url,
        "prompt": prompt,
        "section": section,
        "law_code": law_code,
        "description": description
    }


def save_fetched_content(section, law_code, content, title, url):
    """Save fetched content in the standard format"""
    
    safe_section = section.replace(".", "_")
    output_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    
    data = {
        "section": section,
        "content": content,
        "title": title,
        "law_code": law_code,
        "url": url,
        "fetched": datetime.now(timezone.utc).isoformat(),
        "verified_by": "WebFetch tool"
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return output_file


def main():
    """Generate commands to fetch missing sections"""
    
    cached = get_cached_sections()
    print(f"Currently have {len(cached)} sections cached")
    print()
    
    # Filter out already cached
    to_fetch = []
    for section, law_code, desc in PRIORITY_SECTIONS:
        if section not in cached:
            to_fetch.append((section, law_code, desc))
    
    print(f"Need to fetch {len(to_fetch)} sections")
    print()
    
    # Generate fetch commands
    commands = []
    for section, law_code, desc in to_fetch[:10]:  # Do 10 at a time
        cmd = generate_webfetch_command(section, law_code, desc)
        if cmd:
            commands.append(cmd)
            print(f"Ready to fetch: {law_code} {section} - {desc}")
    
    # Save commands to file for reference
    with open("scripts/fetch_commands.json", "w") as f:
        json.dump(commands, f, indent=2)
    
    print(f"\nGenerated {len(commands)} fetch commands")
    print("Saved to scripts/fetch_commands.json")
    print()
    print("Next steps:")
    print("1. Use WebFetch with each command to retrieve the content")
    print("2. Save using the save_fetched_content() function")


if __name__ == "__main__":
    main()