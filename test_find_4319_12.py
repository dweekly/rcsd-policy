#!/usr/bin/env python3
"""
Test script to find regulation 4319.12 in the 4000 series PDF
"""

import fitz  # PyMuPDF
import re
import sys

def find_regulation_4319_12(pdf_path):
    """Search for regulation 4319.12 in the PDF"""
    
    print(f"Opening PDF: {pdf_path}")
    pdf_doc = fitz.open(pdf_path)
    
    # First, let's check all TOC pages (not just first 5)
    print("\n1. Searching Table of Contents (first 20 pages)...")
    toc_pattern = re.compile(
        r'(Policy|Regulation|Exhibit(?:\s+\(PDF\))?|Bylaw)\s+'
        r'(4319\.12)\s*:\s*'
        r'(.+?)\s+(\d+)\s*$',
        re.MULTILINE
    )
    
    for page_num in range(min(20, len(pdf_doc))):
        page = pdf_doc[page_num]
        text = page.get_text()
        
        # Look for any mention of 4319.12
        if '4319.12' in text:
            print(f"\nFound '4319.12' on page {page_num + 1}!")
            
            # Try to find it with the TOC pattern
            matches = toc_pattern.finditer(text)
            for match in matches:
                print(f"  TOC Match: {match.group(0)}")
                print(f"    Type: {match.group(1)}")
                print(f"    Code: {match.group(2)}")
                print(f"    Title: {match.group(3)}")
                print(f"    Page: {match.group(4)}")
            
            # Also show context around 4319.12
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if '4319.12' in line:
                    print(f"\n  Context (lines {i-2} to {i+2}):")
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        print(f"    {j}: {lines[j]}")
    
    # Now check page 339 specifically
    print(f"\n2. Checking page 339 directly...")
    if len(pdf_doc) >= 339:
        page = pdf_doc[338]  # 0-based index
        text = page.get_text()
        
        if '4319.12' in text:
            print("Found '4319.12' on page 339!")
            # Show first 500 characters
            print("\nFirst 500 characters of page 339:")
            print(text[:500])
        else:
            print("'4319.12' not found on page 339")
            # Check nearby pages
            print("\nChecking nearby pages...")
            for offset in [-2, -1, 1, 2]:
                page_num = 338 + offset
                if 0 <= page_num < len(pdf_doc):
                    if '4319.12' in pdf_doc[page_num].get_text():
                        print(f"  Found on page {page_num + 1}")
    
    # Search entire document for 4319.12
    print("\n3. Searching entire document for '4319.12'...")
    found_pages = []
    for page_num in range(len(pdf_doc)):
        page = pdf_doc[page_num]
        text = page.get_text()
        if '4319.12' in text:
            found_pages.append(page_num + 1)
    
    if found_pages:
        print(f"Found '4319.12' on pages: {found_pages}")
        
        # Show details for first occurrence
        first_page = found_pages[0] - 1
        page = pdf_doc[first_page]
        text = page.get_text()
        
        print(f"\nDetails from page {found_pages[0]}:")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if '4319.12' in line:
                print(f"\n  Line {i}: {line}")
                # Show surrounding lines
                for j in range(max(0, i-3), min(len(lines), i+4)):
                    if j != i:
                        print(f"  Line {j}: {lines[j]}")
                break
    else:
        print("'4319.12' not found anywhere in the document")
    
    # Check if it might be a formatting issue
    print("\n4. Checking for potential formatting issues...")
    # Look for variations
    variations = [
        r'4319\.12',
        r'4319\s*\.\s*12',
        r'4319\s+12',
        r'4319-12',
        r'Regulation\s+4319\.12',
        r'Reg\s*\.?\s*4319\.12'
    ]
    
    for pattern in variations:
        regex = re.compile(pattern, re.IGNORECASE)
        for page_num in range(min(20, len(pdf_doc))):
            page = pdf_doc[page_num]
            text = page.get_text()
            matches = regex.findall(text)
            if matches:
                print(f"  Found pattern '{pattern}' on page {page_num + 1}: {matches}")
    
    pdf_doc.close()

if __name__ == "__main__":
    # Look for 4000 series PDF
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
        find_regulation_4319_12(pdf_path)
    else:
        print("Could not find RCSD_Policies_4000.pdf")
        print("Please provide the path as an argument:")
        print("  python test_find_4319_12.py /path/to/RCSD_Policies_4000.pdf")
        if len(sys.argv) > 1:
            find_regulation_4319_12(sys.argv[1])