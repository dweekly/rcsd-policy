#!/usr/bin/env python3
"""
Batched compliance check that processes documents in smaller groups
to avoid timeouts and ensure progress is saved regularly.
"""

import os
import json
import time
from pathlib import Path
from compliance_check_comprehensive import ComplianceChecker

def get_completed_documents():
    """Get set of documents that have already been processed"""
    completed = set()
    json_dir = Path("data/analysis/compliance/json_data")
    
    if json_dir.exists():
        for file in json_dir.glob("*.json"):
            # Extract document code from filename
            code = file.stem.replace("compliance_", "")
            completed.add(code)
    
    return completed

def main():
    print("Starting batched compliance check...")
    
    # Configuration
    BATCH_SIZE = 20  # Process 20 documents at a time
    BATCH_DELAY = 5  # Seconds between batches
    
    # Get all policy files
    all_files = []
    for subdir in ["policies", "regulations"]:
        dir_path = Path("data/extracted") / subdir
        if dir_path.exists():
            all_files.extend(list(dir_path.glob("*.txt")))
    
    # Get completed documents
    completed = get_completed_documents()
    print(f"Already completed: {len(completed)} documents")
    
    # Filter out completed documents
    remaining_files = []
    for file in all_files:
        code = file.stem
        if code not in completed:
            remaining_files.append(file)
    
    print(f"Remaining to check: {len(remaining_files)} documents")
    print(f"Total documents: {len(all_files)}")
    
    if not remaining_files:
        print("All documents have been checked!")
        # Generate summary if all complete
        checker = ComplianceChecker()
        print("\nGenerating executive summary...")
        checker.generate_summary()
        print(f"\nExecutive summary: {checker.output_dir}/EXECUTIVE_SUMMARY.md")
        return
    
    # Process in batches
    total_batches = (len(remaining_files) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num in range(total_batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, len(remaining_files))
        batch_files = remaining_files[batch_start:batch_end]
        
        print(f"\n--- Batch {batch_num + 1}/{total_batches} ---")
        print(f"Processing documents {batch_start + 1} to {batch_end} of {len(remaining_files)} remaining")
        
        # Initialize checker for this batch
        checker = ComplianceChecker()
        
        # Process batch
        for i, file_path in enumerate(batch_files, 1):
            current_total = len(completed) + batch_start + i
            print(f"\n[{i}/{len(batch_files)}] (Document {current_total}/{len(all_files)} total)")
            print(f"Processing: {file_path.name}")
            
            try:
                checker.process_policy(str(file_path))
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        # Save API usage stats after each batch
        print(f"\nBatch {batch_num + 1} complete.")
        
        # Wait between batches if not the last batch
        if batch_num < total_batches - 1:
            print(f"Waiting {BATCH_DELAY} seconds before next batch...")
            time.sleep(BATCH_DELAY)
    
    # All batches complete - generate executive summary
    print("\n=== All batches complete! ===")
    print("Generating executive summary...")
    
    # Use a fresh checker instance for summary generation
    final_checker = ComplianceChecker()
    final_checker.generate_summary()
    
    print("\nCompliance check complete!")
    print(f"Results saved to: {final_checker.output_dir}")
    print(f"Executive summary: {final_checker.output_dir}/EXECUTIVE_SUMMARY.md")

if __name__ == "__main__":
    main()