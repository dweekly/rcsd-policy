#!/usr/bin/env python3
"""
Generate fetch commands for ALL Ed Code sections cited in compliance findings
"""

import json
from pathlib import Path
from collections import Counter


def extract_all_edcode_citations():
    """Extract all Ed Code citations from compliance findings"""
    
    # Load the compliance verification data
    ver_file = Path("data/analysis/compliance_v2_verification_data.json")
    if not ver_file.exists():
        print("Verification data not found")
        return []
    
    with open(ver_file) as f:
        data = json.load(f)
    
    # Extract all unique Ed Code sections
    sections = set()
    section_details = {}
    
    for finding in data.get("problematic_findings", []):
        policy = finding.get("policy", "")
        
        for issue in finding.get("issues", []):
            issue_title = issue.get("issue", "")
            
            for problem in issue.get("problems", []):
                section = problem.get("section", "")
                law_code = problem.get("law_code", "EDC")
                claim = problem.get("claim", "")[:100] + "..."
                
                if section and law_code in ["EDC", "PCC", "GC", "VC", "PEN"]:
                    sections.add((section, law_code))
                    
                    # Store details for description
                    key = (section, law_code)
                    if key not in section_details:
                        section_details[key] = {
                            "policies": set(),
                            "issues": set(),
                            "claims": []
                        }
                    
                    section_details[key]["policies"].add(policy)
                    section_details[key]["issues"].add(issue_title)
                    section_details[key]["claims"].append(claim)
    
    # Create comprehensive list with descriptions
    all_sections = []
    for (section, law_code), details in section_details.items():
        # Generate description from issue titles
        issues = list(details["issues"])
        if issues:
            description = issues[0]
        else:
            description = f"Referenced in {len(details['policies'])} policies"
        
        all_sections.append((section, law_code, description))
    
    return sorted(all_sections)


def get_cached_sections():
    """Get list of already cached sections"""
    cache_dir = Path("data/cache/edcode")
    cached = set()
    
    for file in cache_dir.glob("*.json"):
        parts = file.stem.split('_')
        if len(parts) >= 3:
            law_code = parts[0].upper()
            section = parts[1]
            if len(parts) > 3 and parts[2] != "full":
                section = f"{section}.{parts[2]}"
            cached.add(f"{law_code}_{section}")
    
    return cached


def generate_all_commands():
    """Generate fetch commands for all missing sections"""
    
    all_sections = extract_all_edcode_citations()
    cached = get_cached_sections()
    
    print(f"Total unique Ed Code sections cited: {len(all_sections)}")
    print(f"Already cached: {len(cached)}")
    
    commands = []
    missing = []
    
    for section, law_code, description in all_sections:
        cache_key = f"{law_code}_{section}"
        
        if cache_key in cached:
            continue
        
        missing.append((section, law_code, description))
        
        # Generate URL based on law code
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
            continue
        
        prompt = f"Extract the complete text of {law_code} section {section} regarding {description}. Include all subdivisions, requirements, and the effective date."
        
        commands.append({
            "url": url,
            "prompt": prompt,
            "section": section,
            "law_code": law_code,
            "description": description
        })
    
    print(f"Missing sections to fetch: {len(missing)}")
    print()
    
    # Show breakdown by law code
    by_code = Counter(law_code for _, law_code, _ in missing)
    print("Missing sections by law code:")
    for code, count in by_code.most_common():
        print(f"  {code}: {count}")
    
    # Save all commands
    with open("scripts/all_fetch_commands.json", "w") as f:
        json.dump(commands, f, indent=2)
    
    print(f"\nSaved {len(commands)} fetch commands to scripts/all_fetch_commands.json")
    
    # Show first few missing
    print("\nFirst 10 missing sections:")
    for section, law_code, desc in missing[:10]:
        print(f"  {law_code} {section}: {desc}")


if __name__ == "__main__":
    generate_all_commands()