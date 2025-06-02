#!/usr/bin/env python3
"""
Batch fetch Ed Code sections that are missing from cache
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone


def get_sections_to_fetch():
    """Get prioritized list of Ed Code sections to fetch"""
    
    # High priority sections from problematic findings
    priority_sections = [
        # From BP 4200 - Classified Personnel
        ("45240", "EDC", "Merit System Requirements"),
        ("45122", "EDC", "Physical Examination Requirements"),
        ("45113", "EDC", "Probationary Period Requirements"),
        
        # From BP 3300 - Expenditures
        ("20111", "EDC", "Competitive Bidding Requirements"),
        ("20113", "EDC", "Emergency Purchase Procedures"),
        ("1090", "GC", "Conflict of Interest"),
        
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
        ("12517.2", "VC", "Medical Examination for Bus Drivers"),
        ("12523", "VC", "Training Hour Requirements"),
        ("35291", "EDC", "Student Discipline on Buses"),
        
        # From BP 4119.43 - Universal Precautions
        ("5193", "CCR", "Bloodborne Pathogens Exposure Control"),
        
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
        
        # From BP 6171 - Title I Programs
        ("6318", "USC", "Parent Engagement Requirements"),
        ("6321", "USC", "Supplement Not Supplant"),
        ("6315", "USC", "Targeted Assistance Programs"),
        
        # From BP 0420.4 - Charter School Authorization
        ("47607", "EDC", "Charter Renewal and Revocation"),
        
        # From BP 0460 - Local Control and Accountability Plan
        ("52064.3", "EDC", "IDEA Addendum Requirements"),
        ("52064.1", "EDC", "LCFF Budget Overview"),
        ("52063", "EDC", "Advisory Committee Requirements"),
        
        # From BP 0520.1 - School Improvement
        ("6311", "USC", "School Improvement Plan Requirements"),
        
        # From BP 1114 - District-Sponsored Social Media
        ("6250", "GC", "Public Records Act"),
        ("60200", "EDC", "Records Retention"),
        ("1232", "USC", "FERPA Requirements"),
        
        # From BP 1240 - Volunteer Assistance
        ("35021", "EDC", "Volunteer Procedures"),
    ]
    
    # Check what's already cached
    cache_dir = Path("data/cache/edcode")
    cached = set()
    for file in cache_dir.glob("*.json"):
        # Extract section from filename (e.g., "edc_45125_1_full.json" -> "45125.1")
        parts = file.stem.split('_')
        if len(parts) >= 3:
            section = parts[1]
            if len(parts) > 3 and parts[2] != "full":
                section = f"{section}.{parts[2]}"
            cached.add(section)
    
    # Filter out already cached sections
    to_fetch = []
    for section, law_code, description in priority_sections:
        if section not in cached:
            to_fetch.append((section, law_code, description))
    
    return to_fetch


def create_fetch_script(sections):
    """Create a shell script to fetch Ed Code sections using WebFetch"""
    
    script_lines = [
        "#!/bin/bash",
        "# Script to fetch missing Ed Code sections",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "# This script uses the WebFetch tool to retrieve Ed Code sections",
        "# Run with: bash scripts/fetch_edcodes_batch.sh",
        "",
        "set -e  # Exit on error",
        "",
        "echo 'Starting batch fetch of Ed Code sections...'",
        "echo",
        "",
    ]
    
    for i, (section, law_code, description) in enumerate(sections):
        if law_code == "EDC":
            url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC"
        elif law_code == "VC":
            url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=VEH"
        elif law_code == "GC":
            url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=GOV"
        elif law_code == "CCR":
            # California Code of Regulations is different
            continue  # Skip for now
        elif law_code == "USC":
            # US Code is different
            continue  # Skip for now
        else:
            continue
            
        prompt = f"Extract the complete text of {law_code} section {section} regarding {description}. Include all subdivisions, requirements, and the effective date."
        
        # Clean section for filename
        safe_section = section.replace(".", "_")
        output_file = f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json"
        
        script_lines.extend([
            f"echo 'Fetching {law_code} {section}: {description}...'",
            f"",
            f"# Create JSON for {law_code} {section}",
            f"cat > temp_fetch_{i}.json << 'EOF'",
            json.dumps({
                "url": url,
                "prompt": prompt,
                "output_file": output_file,
                "section": section,
                "law_code": law_code,
                "description": description
            }, indent=2),
            "EOF",
            "",
            f"# Fetch using WebFetch (this would need to be done through Claude)",
            f"echo '  -> Would fetch from: {url}'",
            f"echo '  -> Output to: {output_file}'",
            f"echo",
            "",
            "# Add a small delay to avoid rate limiting",
            "sleep 2",
            "",
        ])
    
    script_lines.extend([
        "echo 'Batch fetch complete!'",
        "echo",
        "echo 'Note: This script generates the fetch requests.'",
        "echo 'The actual fetching needs to be done through Claude Code using the WebFetch tool.'",
        "",
        "# Clean up temp files",
        "rm -f temp_fetch_*.json",
    ])
    
    return "\n".join(script_lines)


def main():
    """Generate fetch script for missing Ed Code sections"""
    
    sections = get_sections_to_fetch()
    
    print(f"Found {len(sections)} sections to fetch")
    print()
    
    # Group by law code
    by_code = {}
    for section, law_code, desc in sections:
        if law_code not in by_code:
            by_code[law_code] = []
        by_code[law_code].append((section, desc))
    
    print("Sections to fetch by law code:")
    for code, items in sorted(by_code.items()):
        print(f"\n{code}: {len(items)} sections")
        for section, desc in sorted(items)[:5]:  # Show first 5
            print(f"  - {section}: {desc}")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")
    
    # Create the fetch script
    script_content = create_fetch_script(sections)
    
    output_file = Path("scripts/fetch_edcodes_batch.sh")
    output_file.write_text(script_content)
    output_file.chmod(0o755)  # Make executable
    
    print(f"\nGenerated fetch script: {output_file}")
    print("\nTo use this script:")
    print("1. Review the generated requests in scripts/fetch_edcodes_batch.sh")
    print("2. Use the temp_fetch_*.json files with WebFetch to retrieve each section")
    print("3. Save the results in the specified output files")
    
    # Also create a Python script that can be used more easily
    py_script = Path("scripts/fetch_edcode_section.py")
    py_script.write_text('''#!/usr/bin/env python3
"""
Helper to fetch a single Ed Code section
Usage: python fetch_edcode_section.py <section> <law_code> <description>
"""

import sys
import json
from datetime import datetime, timezone

if len(sys.argv) < 4:
    print("Usage: python fetch_edcode_section.py <section> <law_code> <description>")
    sys.exit(1)

section = sys.argv[1]
law_code = sys.argv[2]
description = " ".join(sys.argv[3:])

# Generate URL based on law code
if law_code == "EDC":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=EDC"
elif law_code == "VC":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=VEH"
elif law_code == "GC":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=GOV"
elif law_code == "PEN":
    url = f"https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum={section}&lawCode=PEN"
else:
    print(f"Unknown law code: {law_code}")
    sys.exit(1)

# Create the fetch request
request = {
    "url": url,
    "prompt": f"Extract the complete text of {law_code} section {section} regarding {description}. Include all subdivisions, requirements, and the effective date.",
    "section": section,
    "law_code": law_code,
    "description": description
}

print(f"Fetch request for {law_code} {section}:")
print(json.dumps(request, indent=2))
print()
print("Use this with WebFetch to retrieve the section.")
''')
    py_script.chmod(0o755)
    
    print(f"\nAlso created helper script: {py_script}")


if __name__ == "__main__":
    main()