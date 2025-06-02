#!/usr/bin/env python3
"""
Fetch the next batch of Ed Code sections
Tracks progress and generates WebFetch commands for Claude Code
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def get_progress():
    """Get current progress from tracking file"""
    progress_file = Path("scripts/fetch_progress.json")
    
    if progress_file.exists():
        with open(progress_file) as f:
            return json.load(f)
    else:
        return {"last_index": 0, "total_fetched": 0, "started": datetime.now(timezone.utc).isoformat()}


def save_progress(progress):
    """Save progress to tracking file"""
    with open("scripts/fetch_progress.json", "w") as f:
        json.dump(progress, f, indent=2)


def check_if_cached(section, law_code):
    """Check if a section is already cached"""
    safe_section = section.replace(".", "_")
    cache_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    return cache_file.exists()


def main():
    """Generate commands for the next batch"""
    
    # Load all commands
    with open("scripts/all_fetch_commands.json") as f:
        all_commands = json.load(f)
    
    # Get progress
    progress = get_progress()
    start_idx = progress["last_index"]
    
    print("Ed Code Batch Fetcher")
    print("=" * 60)
    print(f"Total sections to fetch: {len(all_commands)}")
    print(f"Current position: {start_idx}")
    print(f"Total fetched so far: {progress['total_fetched']}")
    print("=" * 60)
    print()
    
    # Process next batch
    batch_size = 5
    batch_fetched = 0
    
    print("# Commands for this batch:")
    print("# Copy and paste these into Claude Code")
    print()
    
    for i in range(start_idx, min(start_idx + batch_size, len(all_commands))):
        cmd = all_commands[i]
        
        # Skip if already cached
        if check_if_cached(cmd['section'], cmd['law_code']):
            print(f"# Skipping {cmd['law_code']} {cmd['section']} - already cached")
            continue
        
        batch_fetched += 1
        safe_section = cmd['section'].replace(".", "_")
        
        print(f"# {batch_fetched}. {cmd['law_code']} Section {cmd['section']}")
        print(f"# {cmd['description']}")
        print()
        
        # Generate WebFetch command
        print(f"# Fetch {cmd['law_code']} {cmd['section']}")
        print(f"WebFetch(")
        print(f'  url="{cmd["url"]}",')
        print(f'  prompt="{cmd["prompt"]}"')
        print(f")")
        print()
        
        # Generate save command
        print(f"# Save to cache")
        print(f"# Create file: data/cache/edcode/{cmd['law_code'].lower()}_{safe_section}_full.json")
        print(f"# with the fetched content in standard format")
        print()
        print("-" * 60)
        print()
    
    # Update progress
    progress["last_index"] = min(start_idx + batch_size, len(all_commands))
    progress["total_fetched"] += batch_fetched
    save_progress(progress)
    
    print("# Batch complete!")
    print(f"# Fetched {batch_fetched} sections in this batch")
    print(f"# Total progress: {progress['total_fetched']} / {len(all_commands)}")
    print()
    
    if progress["last_index"] < len(all_commands):
        print(f"# Run again for next batch: python scripts/fetch_next_batch.py")
        print(f"# Remaining: {len(all_commands) - progress['last_index']} sections")
    else:
        print("# All sections have been processed!")


if __name__ == "__main__":
    main()