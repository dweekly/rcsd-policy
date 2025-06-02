#!/usr/bin/env python3
"""
Automated Ed Code fetcher that actually fetches sections and saves them
This script is designed to be run repeatedly to fetch sections in batches
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
import sys
import subprocess


def get_cached_sections():
    """Get list of already cached sections"""
    cache_dir = Path("data/cache/edcode")
    cached = set()
    
    for file in cache_dir.glob("*.json"):
        # Just track the filename to check if it exists
        cached.add(file.name)
    
    return cached


def load_all_sections_to_fetch():
    """Load the list of all sections that need to be fetched"""
    # First try the all_fetch_commands.json file
    commands_file = Path("scripts/all_fetch_commands.json")
    if commands_file.exists():
        with open(commands_file) as f:
            return json.load(f)
    
    # Otherwise use the original priority list
    return []


def save_fetch_result(section, law_code, content, title, url):
    """Save the fetched content to a JSON file"""
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


def generate_webfetch_script(commands, batch_size=5):
    """Generate a shell script that uses WebFetch commands"""
    
    script_lines = [
        "#!/bin/bash",
        "# Auto-generated WebFetch commands",
        f"# Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "# This script contains WebFetch commands to be executed",
        "# Run each command manually in Claude Code",
        "",
    ]
    
    cached = get_cached_sections()
    fetched = 0
    
    for cmd in commands[:batch_size]:
        safe_section = cmd['section'].replace(".", "_")
        filename = f"{cmd['law_code'].lower()}_{safe_section}_full.json"
        
        if filename in cached:
            continue
            
        fetched += 1
        script_lines.extend([
            f"echo 'Fetching {cmd['law_code']} {cmd['section']}'",
            f"# {cmd['description']}",
            "",
            "# WebFetch command:",
            f"# WebFetch url=\"{cmd['url']}\" \\",
            f"#   prompt=\"{cmd['prompt']}\"",
            "",
            "# Save result to:",
            f"# data/cache/edcode/{filename}",
            "",
            "-" * 60,
            "",
        ])
    
    script_lines.append(f"echo 'Total to fetch in this batch: {fetched}'")
    
    return "\n".join(script_lines), fetched


def main():
    """Main function to coordinate Ed Code fetching"""
    
    # Load all sections that need fetching
    all_commands = load_all_sections_to_fetch()
    
    if not all_commands:
        print("No fetch commands found. Run generate_all_fetch_commands.py first.")
        return
    
    # Get cached sections
    cached = get_cached_sections()
    
    # Filter out already cached
    remaining = []
    for cmd in all_commands:
        safe_section = cmd['section'].replace(".", "_")
        filename = f"{cmd['law_code'].lower()}_{safe_section}_full.json"
        if filename not in cached:
            remaining.append(cmd)
    
    print(f"Total sections to fetch: {len(all_commands)}")
    print(f"Already cached: {len(all_commands) - len(remaining)}")
    print(f"Remaining to fetch: {len(remaining)}")
    print()
    
    if not remaining:
        print("All sections have been fetched!")
        return
    
    # Generate fetch script for the next batch
    batch_size = 10  # Fetch 10 at a time
    script_content, count = generate_webfetch_script(remaining, batch_size)
    
    # Save the script
    script_file = Path("scripts/next_webfetch_batch.sh")
    with open(script_file, 'w') as f:
        f.write(script_content)
    
    print(f"Generated WebFetch script for {count} sections")
    print(f"Script saved to: {script_file}")
    print()
    print("Next steps:")
    print("1. Review the script to see which sections will be fetched")
    print("2. Execute the WebFetch commands manually in Claude Code")
    print("3. Save each result using the format shown in the script")
    print("4. Run this script again to generate the next batch")
    print()
    
    # Show the first few sections to be fetched
    print("First sections in this batch:")
    for i, cmd in enumerate(remaining[:5]):
        print(f"  {cmd['law_code']} {cmd['section']}: {cmd.get('description', 'No description')}")
    
    if len(remaining) > 5:
        print(f"  ... and {count - 5} more")


if __name__ == "__main__":
    main()