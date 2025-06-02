#!/usr/bin/env python3
"""
Smart Ed Code fetcher that provides context about what each section might be
and handles cases where sections might be in different codes
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import re


# Known section mappings based on our discoveries
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
    "17608": ("EDC", "Healthy Schools Act of 2000 - Citation"),
    "20111": ("PCC", "School District Competitive Bidding Requirements"),
    "20113": ("PCC", "Emergency Purchase Procedures for School Districts"),
}


def get_section_context(section, claimed_code):
    """Get context about what a section might actually be"""
    
    # Check if we have a known mapping
    if section in KNOWN_MAPPINGS:
        actual_code, description = KNOWN_MAPPINGS[section]
        if actual_code != claimed_code:
            return {
                "likely_code": actual_code,
                "description": description,
                "note": f"This section is likely {actual_code} {section}, not {claimed_code} {section}"
            }
        else:
            return {
                "likely_code": actual_code,
                "description": description,
                "note": "Confirmed correct code"
            }
    
    # Try to guess based on section number ranges
    section_num = float(re.sub(r'[^\d.]', '', section))
    
    hints = []
    if 1000 <= section_num < 2000:
        hints.append("Could be Labor Code (LAB) if about employment")
    if 10000 <= section_num < 20000:
        hints.append("Could be Education Code (EDC) or Government Code (GOV)")
    if 12000 <= section_num < 13000:
        hints.append("Could be Vehicle Code (VC) if about transportation")
        hints.append("Could be Government Code (GOV) if about employment practices")
    if 20000 <= section_num < 30000:
        hints.append("Could be Public Contract Code (PCC) if about bidding/contracts")
    
    return {
        "likely_code": claimed_code,
        "description": "Unknown - verify actual code",
        "note": "; ".join(hints) if hints else "No hints available"
    }


def analyze_manifest(manifest_file):
    """Analyze a fetch manifest and provide enhanced information"""
    
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    enhanced_commands = []
    
    for cmd in manifest['commands']:
        section = cmd['section']
        law_code = cmd['law_code']
        
        # Get context
        context = get_section_context(section, law_code)
        
        # Check if already cached under different code
        already_cached = []
        for code in ['EDC', 'LAB', 'GOV', 'VC', 'PCC', 'FAC', 'PEN', 'HSC']:
            safe_section = section.replace(".", "_")
            cache_file = Path(f"data/cache/edcode/{code.lower()}_{safe_section}_full.json")
            if cache_file.exists():
                already_cached.append(code)
        
        enhanced_cmd = cmd.copy()
        enhanced_cmd['context'] = context
        enhanced_cmd['already_cached_as'] = already_cached
        
        enhanced_commands.append(enhanced_cmd)
    
    return enhanced_commands


def generate_smart_fetch_script(batch_num=0):
    """Generate a smart fetch script with context"""
    
    manifest_file = Path(f"scripts/fetch_manifest_batch_{batch_num}.json")
    if not manifest_file.exists():
        print(f"Manifest not found: {manifest_file}")
        print("Run batch_fetch_processor.py first")
        return
    
    enhanced_commands = analyze_manifest(manifest_file)
    
    print(f"Smart Analysis of Batch {batch_num}")
    print("=" * 60)
    
    for i, cmd in enumerate(enhanced_commands, 1):
        print(f"\n{i}. Section {cmd['section']} (claimed as {cmd['law_code']})")
        print(f"   Context: {cmd['context']['description']}")
        print(f"   Note: {cmd['context']['note']}")
        
        if cmd['already_cached_as']:
            print(f"   ⚠️  Already cached as: {', '.join(cmd['already_cached_as'])}")
        
        if cmd['context']['likely_code'] != cmd['law_code']:
            print(f"   🔍 Try fetching as {cmd['context']['likely_code']} instead:")
            url = cmd['url'].replace(f"lawCode={cmd['law_code']}", f"lawCode={cmd['context']['likely_code']}")
            print(f"      {url}")
    
    # Save enhanced manifest
    enhanced_file = Path(f"scripts/enhanced_manifest_batch_{batch_num}.json")
    with open(enhanced_file, 'w') as f:
        json.dump({
            "batch_number": batch_num,
            "generated": datetime.now(timezone.utc).isoformat(),
            "enhanced_commands": enhanced_commands
        }, f, indent=2)
    
    print(f"\nEnhanced manifest saved to: {enhanced_file}")


def main():
    """Main function"""
    import sys
    
    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    generate_smart_fetch_script(batch_num)


if __name__ == "__main__":
    main()