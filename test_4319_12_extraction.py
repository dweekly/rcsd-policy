#!/usr/bin/env python3
"""Test extraction of 4319.12 with fixed parser"""

from pdf_parser_fixed import PDFPolicyParser
import os

def test_extraction():
    parser = PDFPolicyParser()
    
    # Parse just the 4000 series
    print("Testing extraction of RCSD Policies 4000.pdf with fixed parser...")
    parser.parse_pdf("policies/RCSD Policies 4000.pdf", "test_4000_fixed")
    
    # Check if 4319.12 was extracted
    reg_path = "test_4000_fixed/regulations/4319.12.txt"
    if os.path.exists(reg_path):
        print("\n✓ SUCCESS: 4319.12 was extracted!")
        print("\nContent preview:")
        with open(reg_path, 'r') as f:
            lines = f.readlines()[:20]
            for i, line in enumerate(lines, 1):
                print(f"  {i:2}: {line.rstrip()}")
    else:
        print("\n✗ FAILED: 4319.12 was not extracted")
        
        # Check what was in the TOC
        print("\nTOC entries found:")
        for key, entry in sorted(parser.toc_entries.items()):
            if '4319' in entry['code']:
                print(f"  - {entry['type']} {entry['code']}: {entry['title']} (page {entry['page']})")
    
    # Also check for 4219.12
    reg_path2 = "test_4000_fixed/regulations/4219.12.txt"
    if os.path.exists(reg_path2):
        print("\n✓ 4219.12 was also extracted")
    else:
        print("\n✗ 4219.12 was also missing")

if __name__ == "__main__":
    test_extraction()