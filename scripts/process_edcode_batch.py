#!/usr/bin/env python3
"""
Process a single batch of Ed Code sections
Shows WebFetch commands for execution
"""

import json
import sys
from pathlib import Path


def load_batch_manifest(batch_num):
    """Load a specific batch manifest"""
    manifest_file = Path(f"data/cache/edcode_manifests/batch_{batch_num:03d}.json")
    
    if not manifest_file.exists():
        print(f"Batch {batch_num} not found!")
        return None
    
    with open(manifest_file) as f:
        return json.load(f)


def display_batch_commands(manifest):
    """Display WebFetch commands for a batch"""
    
    batch_num = manifest["batch_number"]
    commands = manifest["commands"]
    
    print("=" * 80)
    print(f"ED CODE BATCH {batch_num} - {len(commands)} SECTIONS")
    print("=" * 80)
    print()
    
    # Group by priority (citation count)
    high_priority = [c for c in commands if c["count"] >= 5]
    medium_priority = [c for c in commands if 2 <= c["count"] < 5]
    low_priority = [c for c in commands if c["count"] < 2]
    
    if high_priority:
        print("HIGH PRIORITY (5+ citations):")
        print("-" * 40)
        for cmd in high_priority:
            print(f"\n# {cmd['law_code']} {cmd['section']} - {cmd['count']} citations")
            print(f"# {cmd['description']}")
            print()
    
    # Generate executable commands
    print("\n" + "=" * 80)
    print("WEBFETCH COMMANDS")
    print("=" * 80)
    print()
    
    for i, cmd in enumerate(commands, 1):
        print(f"# {i}. {cmd['law_code']} Section {cmd['section']} ({cmd['count']} citations)")
        print(f"WebFetch(")
        print(f'  url="{cmd["url"]}",')
        print(f'  prompt="{cmd["prompt"]}"')
        print(f")")
        print()
        print(f"# Save to: {cmd['output_file']}")
        print("-" * 60)
        print()
    
    print("=" * 80)
    print(f"Total sections in batch {batch_num}: {len(commands)}")
    
    # Show next batch info
    next_batch = Path(f"data/cache/edcode_manifests/batch_{batch_num+1:03d}.json")
    if next_batch.exists():
        print(f"\nNext: python scripts/process_edcode_batch.py {batch_num + 1}")


def save_batch_results(batch_num, results):
    """Save results after processing a batch"""
    results_dir = Path("data/cache/edcode_results")
    results_dir.mkdir(exist_ok=True)
    
    results_file = results_dir / f"batch_{batch_num:03d}_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """Main function"""
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/process_edcode_batch.py <batch_num>")
        print("\nAvailable batches:")
        
        manifest_dir = Path("data/cache/edcode_manifests")
        if manifest_dir.exists():
            batch_files = sorted(manifest_dir.glob("batch_*.json"))
            for bf in batch_files[:10]:
                batch_num = int(bf.stem.split("_")[1])
                with open(bf) as f:
                    data = json.load(f)
                print(f"  Batch {batch_num}: {data['count']} sections")
        return
    
    batch_num = int(sys.argv[1])
    manifest = load_batch_manifest(batch_num)
    
    if not manifest:
        return
    
    display_batch_commands(manifest)


if __name__ == "__main__":
    main()