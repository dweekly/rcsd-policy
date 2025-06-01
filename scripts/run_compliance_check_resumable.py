#!/usr/bin/env python3
"""
Resumable compliance check that tracks progress and can continue from where it left off
"""

import os
import json
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
    print("Starting resumable compliance check...")
    
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
        return
    
    # Initialize checker
    checker = ComplianceChecker()
    
    # Process remaining files
    for i, file_path in enumerate(remaining_files, 1):
        print(f"\n[{i}/{len(remaining_files)}] ({len(completed) + i}/{len(all_files)} total)")
        
        try:
            checker.process_policy(str(file_path))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    # Generate executive summary
    print("\nGenerating executive summary...")
    checker.generate_summary()
    
    print("\nCompliance check complete!")
    print(f"Results saved to: {checker.output_dir}")
    print(f"Executive summary: {checker.output_dir}/EXECUTIVE_SUMMARY.md")

if __name__ == "__main__":
    main()