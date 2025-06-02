#!/usr/bin/env python3
"""
Process Ed Code fetches in batches with proper tracking
This generates a structured JSON file with all the WebFetch commands needed
"""

import json
from pathlib import Path
from datetime import datetime, timezone
import sys


def get_progress():
    """Load or initialize progress tracking"""
    progress_file = Path("scripts/fetch_progress_v2.json")
    
    if progress_file.exists():
        with open(progress_file) as f:
            return json.load(f)
    
    return {
        "started": datetime.now(timezone.utc).isoformat(),
        "total_processed": 0,
        "total_fetched": 0,
        "last_batch": 0,
        "completed_sections": []
    }


def save_progress(progress):
    """Save progress tracking"""
    with open("scripts/fetch_progress_v2.json", 'w') as f:
        json.dump(progress, f, indent=2)


def check_if_cached(section, law_code):
    """Check if a section is already cached"""
    safe_section = section.replace(".", "_")
    cache_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    return cache_file.exists()


def generate_batch(batch_num, batch_size=5):
    """Generate a batch of fetch commands"""
    
    # Load all commands
    with open("scripts/all_fetch_commands.json") as f:
        all_commands = json.load(f)
    
    # Load progress
    progress = get_progress()
    
    # Calculate batch range
    start_idx = batch_num * batch_size
    end_idx = min(start_idx + batch_size, len(all_commands))
    
    if start_idx >= len(all_commands):
        print("All batches have been processed!")
        return None
    
    batch_commands = []
    
    for i in range(start_idx, end_idx):
        cmd = all_commands[i]
        
        # Skip if already cached
        if check_if_cached(cmd['section'], cmd['law_code']):
            progress['completed_sections'].append(f"{cmd['law_code']}_{cmd['section']}")
            continue
        
        # Add output file info
        safe_section = cmd['section'].replace(".", "_")
        cmd['output_file'] = f"data/cache/edcode/{cmd['law_code'].lower()}_{safe_section}_full.json"
        
        batch_commands.append(cmd)
    
    # Update progress
    progress['last_batch'] = batch_num
    progress['total_processed'] = end_idx
    save_progress(progress)
    
    return batch_commands


def create_fetch_manifest(batch_num=0):
    """Create a manifest file with all fetch commands for the batch"""
    
    batch_commands = generate_batch(batch_num)
    
    if not batch_commands:
        return None
    
    manifest = {
        "batch_number": batch_num,
        "generated": datetime.now(timezone.utc).isoformat(),
        "commands": batch_commands,
        "instructions": [
            "Use WebFetch to retrieve each section",
            "Save the content to the specified output_file",
            "Use the standard JSON format with section, content, title, law_code, url, fetched, verified_by fields"
        ]
    }
    
    # Save manifest
    manifest_file = Path(f"scripts/fetch_manifest_batch_{batch_num}.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest_file, len(batch_commands)


def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        batch_num = int(sys.argv[1])
    else:
        # Get next batch number from progress
        progress = get_progress()
        batch_num = progress.get('last_batch', -1) + 1
    
    print(f"Processing batch {batch_num}")
    
    manifest_file, count = create_fetch_manifest(batch_num)
    
    if not manifest_file:
        print("No more sections to fetch!")
        return
    
    print(f"Created manifest with {count} sections to fetch")
    print(f"Manifest file: {manifest_file}")
    print()
    print("To fetch these sections:")
    print(f"1. Open {manifest_file}")
    print("2. For each command in the manifest:")
    print("   - Use WebFetch with the provided URL and prompt")
    print("   - Save the result to the specified output_file")
    print()
    print(f"After completing this batch, run: python scripts/batch_fetch_processor.py {batch_num + 1}")


if __name__ == "__main__":
    main()