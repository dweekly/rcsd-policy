#!/usr/bin/env python3
"""
Analyze TOC structure to understand why some entries might be missed
"""

import fitz
import re
import sys

def analyze_toc_structure(pdf_path):
    """Analyze the table of contents structure"""
    
    print(f"Analyzing TOC structure in: {pdf_path}")
    pdf_doc = fitz.open(pdf_path)
    
    # Check more pages for TOC
    print("\n1. Searching for TOC entries in first 30 pages...")
    
    # Original pattern from pdf_parser.py
    original_pattern = re.compile(
        r'^(Policy|Regulation|Exhibit(?:\s+\(PDF\))?|Bylaw)\s+'
        r'(\d{4}(?:\.\d+)?(?:-E\s+PDF\(\d+\))?)\s*:\s*'
        r'(.+?)\s+(\d+)\s*$',
        re.MULTILINE
    )
    
    # More flexible patterns to catch variations
    flexible_patterns = [
        # Pattern without strict start of line
        re.compile(
            r'(Policy|Regulation|Exhibit(?:\s+\(PDF\))?|Bylaw)\s+'
            r'(\d{4}(?:\.\d+)?)\s*:\s*'
            r'(.+?)\s+(\d+)',
            re.MULTILINE
        ),
        # Pattern with dots instead of spaces before page number
        re.compile(
            r'(Policy|Regulation|Exhibit(?:\s+\(PDF\))?|Bylaw)\s+'
            r'(\d{4}(?:\.\d+)?)\s*:\s*'
            r'(.+?)\.+\s*(\d+)',
            re.MULTILINE
        ),
        # Pattern allowing more variations
        re.compile(
            r'(Policy|Regulation|Exhibit|Bylaw)\s+'
            r'(\d{4}(?:\.\d+)?)\s*:?\s*'
            r'([^0-9]+?)\s+(\d{2,3})',
            re.MULTILINE | re.IGNORECASE
        )
    ]
    
    all_entries = {}
    missed_by_original = []
    
    for page_num in range(min(30, len(pdf_doc))):
        page = pdf_doc[page_num]
        text = page.get_text()
        
        # Find entries with original pattern
        original_matches = list(original_pattern.finditer(text))
        
        # Find entries with flexible patterns
        all_flexible_matches = []
        for pattern in flexible_patterns:
            all_flexible_matches.extend(list(pattern.finditer(text)))
        
        # Deduplicate flexible matches
        flexible_matches = []
        seen = set()
        for match in all_flexible_matches:
            key = (match.group(2), match.group(4))  # code and page
            if key not in seen:
                seen.add(key)
                flexible_matches.append(match)
        
        if original_matches or flexible_matches:
            print(f"\nPage {page_num + 1}:")
            print(f"  Original pattern matches: {len(original_matches)}")
            print(f"  Flexible pattern matches: {len(flexible_matches)}")
            
            # Check what original pattern missed
            original_codes = {m.group(2) for m in original_matches}
            for match in flexible_matches:
                code = match.group(2)
                if code not in original_codes and code not in all_entries:
                    missed_by_original.append({
                        'page': page_num + 1,
                        'code': code,
                        'type': match.group(1),
                        'title': match.group(3).strip(),
                        'target_page': match.group(4),
                        'raw_match': match.group(0)
                    })
        
        # Store all entries found
        for match in original_matches + flexible_matches:
            code = match.group(2)
            if code not in all_entries:
                all_entries[code] = {
                    'type': match.group(1),
                    'title': match.group(3).strip(),
                    'page': match.group(4),
                    'found_on': page_num + 1
                }
    
    # Look specifically for 4319.12
    print("\n2. Specifically searching for 4319.12...")
    found_4319_12 = False
    
    for page_num in range(min(30, len(pdf_doc))):
        page = pdf_doc[page_num]
        text = page.get_text()
        
        if '4319.12' in text:
            print(f"\nFound '4319.12' on page {page_num + 1}")
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if '4319.12' in line:
                    print(f"  Line: {line.strip()}")
                    # Check if it matches any pattern
                    for j, pattern in enumerate([original_pattern] + flexible_patterns):
                        if pattern.search(line):
                            print(f"    Matches pattern {j}")
                        else:
                            print(f"    Does NOT match pattern {j}")
                    
                    # Show context
                    print("  Context:")
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        print(f"    {j}: {lines[j]}")
                    
                    found_4319_12 = True
    
    if not found_4319_12:
        print("  4319.12 not found in first 30 pages")
    
    # Summary
    print(f"\n3. Summary:")
    print(f"  Total unique entries found: {len(all_entries)}")
    print(f"  Entries missed by original pattern: {len(missed_by_original)}")
    
    if missed_by_original:
        print("\n  Examples of missed entries:")
        for entry in missed_by_original[:10]:  # Show first 10
            print(f"    {entry['code']} ({entry['type']}) - {entry['title'][:50]}...")
            print(f"      Raw: {entry['raw_match']}")
    
    # Check if 4319.12 is in our entries
    if '4319.12' in all_entries:
        print(f"\n  4319.12 found in entries: {all_entries['4319.12']}")
    else:
        print("\n  4319.12 NOT found in TOC entries")
    
    # Analyze TOC page coverage
    print("\n4. TOC Page Coverage Analysis:")
    toc_pages = sorted(set(entry['found_on'] for entry in all_entries.values()))
    print(f"  TOC entries found on pages: {toc_pages}")
    
    if toc_pages and max(toc_pages) > 5:
        print(f"  WARNING: TOC extends beyond page 5 (up to page {max(toc_pages)})")
        print(f"  The parser only checks first 5 pages!")
    
    pdf_doc.close()

if __name__ == "__main__":
    import os
    
    pdf_paths = [
        "policies/RCSD_Policies_4000.pdf",
        "RCSD_Policies_4000.pdf",
        "extracted_policies/RCSD_Policies_4000.pdf"
    ]
    
    pdf_path = None
    for path in pdf_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if pdf_path:
        analyze_toc_structure(pdf_path)
    else:
        print("Could not find RCSD_Policies_4000.pdf")
        if len(sys.argv) > 1:
            analyze_toc_structure(sys.argv[1])