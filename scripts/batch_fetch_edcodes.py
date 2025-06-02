#!/usr/bin/env python3
"""
Batch fetch Ed Codes with rate limiting and progress tracking
This script outputs WebFetch commands that can be executed by Claude Code
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def load_fetch_commands():
    """Load the fetch commands from the JSON file"""
    with open("scripts/fetch_commands.json") as f:
        return json.load(f)


def check_if_cached(section, law_code):
    """Check if a section is already cached"""
    safe_section = section.replace(".", "_")
    cache_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    return cache_file.exists()


def generate_claude_commands(commands, start_idx=0, count=5):
    """Generate Claude Code commands for fetching"""
    
    print(f"# Batch fetch Ed Code sections {start_idx + 1} to {start_idx + count}")
    print(f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print()
    
    fetched = 0
    for i, cmd in enumerate(commands[start_idx:start_idx + count]):
        if check_if_cached(cmd['section'], cmd['law_code']):
            print(f"# Skipping {cmd['law_code']} {cmd['section']} - already cached")
            continue
            
        fetched += 1
        print(f"# {fetched}. Fetch {cmd['law_code']} {cmd['section']}: {cmd['description']}")
        print(f"WebFetch url='{cmd['url']}' prompt='{cmd['prompt']}'")
        print()
        
        # Generate the save command
        safe_section = cmd['section'].replace(".", "_")
        output_file = f"data/cache/edcode/{cmd['law_code'].lower()}_{safe_section}_full.json"
        
        print(f"# Save the result to {output_file}")
        print(f"# Use the content from WebFetch to create the JSON file")
        print()
    
    print(f"# Fetched {fetched} sections in this batch")
    
    return fetched


def main():
    """Generate batch fetch commands"""
    
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
    else:
        start_idx = 0
    
    commands = load_fetch_commands()
    total = len(commands)
    
    print(f"# Total commands available: {total}")
    print(f"# Starting from index: {start_idx}")
    print("#" * 60)
    print()
    
    # Generate commands for the next batch
    count = 5  # Do 5 at a time to avoid rate limiting
    fetched = generate_claude_commands(commands, start_idx, count)
    
    print()
    print("#" * 60)
    print(f"# Next batch: python scripts/batch_fetch_edcodes.py {start_idx + count}")
    print(f"# Remaining: {total - start_idx - count} sections")


if __name__ == "__main__":
    main()