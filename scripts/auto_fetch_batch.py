#!/usr/bin/env python3
"""
Automatically fetch a batch of Ed Code sections
This script generates all the WebFetch commands for efficient execution
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def load_batch_manifest(batch_num):
    """Load a specific batch manifest"""
    manifest_file = Path(f"data/cache/edcode_manifests/batch_{batch_num:03d}.json")
    
    if not manifest_file.exists():
        return None
    
    with open(manifest_file) as f:
        return json.load(f)


def check_already_fetched(commands):
    """Filter out already fetched sections"""
    to_fetch = []
    
    for cmd in commands:
        output_file = Path(cmd["output_file"])
        if not output_file.exists():
            to_fetch.append(cmd)
    
    return to_fetch


def save_fetch_result(section, law_code, content, title, url):
    """Save fetched content in standard format"""
    safe_section = section.replace(".", "_")
    output_file = Path(f"data/cache/edcode/{law_code.lower()}_{safe_section}_full.json")
    
    # Ensure content is properly escaped
    if isinstance(content, str):
        # Escape newlines and other control characters
        content = content.replace('\\', '\\\\')
        content = content.replace('\n', '\\n')
        content = content.replace('\r', '\\r')
        content = content.replace('\t', '\\t')
        content = content.replace('"', '\\"')
    
    data = {
        "section": section,
        "content": content,
        "title": title,
        "law_code": law_code,
        "url": url,
        "fetched": datetime.now(timezone.utc).isoformat(),
        "verified_by": "WebFetch tool"
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with proper JSON encoding
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return output_file


def process_batch(batch_num):
    """Process a single batch"""
    
    manifest = load_batch_manifest(batch_num)
    if not manifest:
        print(f"Batch {batch_num} not found")
        return 0
    
    commands = manifest["commands"]
    to_fetch = check_already_fetched(commands)
    
    if not to_fetch:
        print(f"Batch {batch_num}: All {len(commands)} sections already fetched")
        return 0
    
    print(f"\nBatch {batch_num}: {len(to_fetch)} of {len(commands)} sections to fetch")
    print("=" * 80)
    
    # Show commands for the highest priority sections
    high_priority = sorted(to_fetch, key=lambda x: x["count"], reverse=True)[:10]
    
    for cmd in high_priority:
        print(f"\n{cmd['law_code']} {cmd['section']} ({cmd['count']} citations)")
        print(f"Description: {cmd['description']}")
    
    return len(to_fetch)


def generate_all_fetch_commands():
    """Generate commands for all unfetched sections"""
    
    manifest_dir = Path("data/cache/edcode_manifests")
    if not manifest_dir.exists():
        print("No manifests found. Run parallel_fetch_edcodes.py first")
        return
    
    all_commands = []
    batch_status = []
    
    # Process all batches
    for manifest_file in sorted(manifest_dir.glob("batch_*.json")):
        with open(manifest_file) as f:
            manifest = json.load(f)
        
        batch_num = manifest["batch_number"]
        commands = manifest["commands"]
        to_fetch = check_already_fetched(commands)
        
        batch_status.append({
            "batch": batch_num,
            "total": len(commands),
            "to_fetch": len(to_fetch),
            "fetched": len(commands) - len(to_fetch)
        })
        
        all_commands.extend(to_fetch)
    
    # Summary
    print("=" * 80)
    print("ED CODE FETCH STATUS")
    print("=" * 80)
    
    total_sections = sum(b["total"] for b in batch_status)
    total_fetched = sum(b["fetched"] for b in batch_status)
    total_remaining = sum(b["to_fetch"] for b in batch_status)
    
    print(f"\nTotal sections: {total_sections}")
    print(f"Already fetched: {total_fetched}")
    print(f"Remaining: {total_remaining}")
    
    print("\nBatch Status:")
    for b in batch_status[:10]:
        if b["to_fetch"] > 0:
            print(f"  Batch {b['batch']}: {b['fetched']}/{b['total']} done ({b['to_fetch']} remaining)")
    
    if total_remaining == 0:
        print("\nAll sections have been fetched!")
        return
    
    # Show next sections to fetch
    print(f"\nNext {min(20, total_remaining)} sections to fetch:")
    print("-" * 80)
    
    for cmd in all_commands[:20]:
        print(f"\n{cmd['law_code']} {cmd['section']} ({cmd['count']} citations)")
        print(f"URL: {cmd['url']}")
    
    return all_commands


def main():
    """Main function"""
    
    import sys
    
    if len(sys.argv) > 1:
        # Process specific batch
        batch_num = int(sys.argv[1])
        process_batch(batch_num)
    else:
        # Show overall status
        commands = generate_all_fetch_commands()
        
        if commands:
            print(f"\n\nTo fetch the next batch, run:")
            print("python scripts/process_edcode_batch.py 0")
            print("\nOr to see all remaining sections:")
            print("python scripts/auto_fetch_batch.py > remaining_sections.txt")


if __name__ == "__main__":
    main()