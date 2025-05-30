#!/usr/bin/env python3
"""
Check for missing cross-referenced policies
"""

import os
import re
import json
from collections import defaultdict

def extract_policy_codes_from_references(references):
    """Extract policy codes from cross-references"""
    codes = set()
    if 'cross_references' in references:
        for ref in references['cross_references']:
            # Extract code from format "CODE (Title)"
            match = re.match(r'^(\d{4}(?:\.\d+)?(?:-E)?)', ref)
            if match:
                codes.add(match.group(1))
    return codes

def get_all_extracted_codes(base_dir='extracted_policies_all'):
    """Get all policy codes that were successfully extracted"""
    extracted_codes = set()
    
    # Check all subdirectories
    for subdir in ['policies', 'regulations', 'exhibits']:
        dir_path = os.path.join(base_dir, subdir)
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.txt'):
                    # Extract code from filename
                    code = filename.replace('.txt', '')
                    # Handle special cases like "3320-E PDF(2)"
                    code = re.sub(r'\s+PDF\(\d+\)', '', code)
                    extracted_codes.add(code)
    
    return extracted_codes

def check_missing_references(base_dir='extracted_policies_all'):
    """Check for cross-referenced policies that weren't extracted"""
    
    # Get all extracted codes
    extracted_codes = get_all_extracted_codes(base_dir)
    print(f"Total extracted documents: {len(extracted_codes)}")
    
    # Read the summary to get all references
    summary_path = os.path.join(base_dir, 'extraction_summary.json')
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Track all cross-referenced codes and where they're referenced from
    all_referenced_codes = defaultdict(list)
    
    for doc in summary['documents']:
        doc_code = doc['code']
        doc_type = doc['doc_type']
        
        # Get cross-referenced codes
        referenced_codes = extract_policy_codes_from_references(doc.get('references', {}))
        
        for ref_code in referenced_codes:
            all_referenced_codes[ref_code].append(f"{doc_type} {doc_code}")
    
    # Find missing codes
    missing_codes = set(all_referenced_codes.keys()) - extracted_codes
    
    print(f"\nTotal unique cross-referenced codes: {len(all_referenced_codes)}")
    print(f"Missing cross-referenced codes: {len(missing_codes)}")
    
    if missing_codes:
        print("\nMissing policies/regulations:")
        print("="*60)
        
        # Group by series
        missing_by_series = defaultdict(list)
        for code in sorted(missing_codes):
            series = code[0] + "000"
            missing_by_series[series].append(code)
        
        for series in sorted(missing_by_series.keys()):
            print(f"\n{series} Series:")
            for code in sorted(missing_by_series[series]):
                print(f"  - {code} (referenced by: {', '.join(sorted(all_referenced_codes[code])[:3])}"
                      f"{' and others' if len(all_referenced_codes[code]) > 3 else ''})")
    
    # Also check for codes referenced in specific ranges that might be missing
    print("\n\nChecking for potentially missing series...")
    series_coverage = defaultdict(set)
    
    for code in extracted_codes:
        if re.match(r'^\d{4}', code):
            series = code[0]
            series_coverage[series].add(code)
    
    for series in sorted(series_coverage.keys()):
        codes = sorted(series_coverage[series])
        print(f"\n{series}000 series: {len(codes)} documents extracted")
        
        # Check for gaps in numbering
        numeric_codes = []
        for code in codes:
            match = re.match(r'^(\d{4})', code)
            if match:
                numeric_codes.append(int(match.group(1)))
        
        if numeric_codes:
            numeric_codes.sort()
            gaps = []
            for i in range(len(numeric_codes)-1):
                if numeric_codes[i+1] - numeric_codes[i] > 1:
                    gap_start = numeric_codes[i] + 1
                    gap_end = numeric_codes[i+1] - 1
                    if gap_start == gap_end:
                        gaps.append(str(gap_start))
                    else:
                        gaps.append(f"{gap_start}-{gap_end}")
            
            if gaps:
                print(f"  Gaps in numbering: {', '.join(gaps)}")

if __name__ == "__main__":
    check_missing_references()