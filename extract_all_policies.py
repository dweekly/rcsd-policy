#!/usr/bin/env python3
"""
Extract all policies from available PDFs into separate directories
Then merge them intelligently without overwriting
"""

import os
import json
import shutil
from pdf_parser import PDFPolicyParser
from datetime import datetime


def extract_all_policies():
    """Extract policies from all PDFs and merge intelligently"""
    
    # Extract each PDF to its own directory
    pdf_files = sorted([f for f in os.listdir('policies') if f.endswith('.pdf')])
    
    for pdf_file in pdf_files:
        # Determine series from filename
        series_match = pdf_file.replace('.pdf', '').split()[-1]  # Gets "0000", "1000", etc.
        output_dir = f'extracted_{series_match}'
        
        print(f"\n{'='*60}")
        print(f"Extracting {pdf_file} to {output_dir}")
        print(f"{'='*60}")
        
        parser = PDFPolicyParser()
        pdf_path = os.path.join('policies', pdf_file)
        parser.parse_pdf(pdf_path, output_dir)
    
    # Now merge all extracted policies intelligently
    print(f"\n{'='*60}")
    print("Merging all extracted policies...")
    print(f"{'='*60}")
    
    merge_all_policies()


def merge_all_policies():
    """Merge policies from all series directories into final output"""
    
    # Create final output directory
    final_dir = 'extracted_policies_all'
    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(os.path.join(final_dir, 'policies'), exist_ok=True)
    os.makedirs(os.path.join(final_dir, 'regulations'), exist_ok=True)
    os.makedirs(os.path.join(final_dir, 'exhibits'), exist_ok=True)
    
    all_documents = []
    policy_sources = {}  # Track which PDF each policy came from
    
    # Process each series directory
    series_dirs = sorted([d for d in os.listdir('.') if d.startswith('extracted_') and os.path.isdir(d)])
    
    for series_dir in series_dirs:
        series = series_dir.replace('extracted_', '')
        summary_file = os.path.join(series_dir, 'extraction_summary.json')
        
        if not os.path.exists(summary_file):
            continue
            
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        print(f"\nProcessing {series_dir}: {summary['total_documents']} documents")
        
        # Process each document
        for doc in summary['documents']:
            code = doc['code']
            doc_type = doc['doc_type'].lower()
            
            # Only include if it's from the right series (first digit matches)
            if code[0] == series[0]:
                # Determine subdirectory
                if doc_type == 'policy':
                    subdir = 'policies'
                elif doc_type == 'regulation':
                    subdir = 'regulations'
                elif doc_type == 'exhibit':
                    subdir = 'exhibits'
                else:
                    continue
                
                # Copy the file
                source_file = os.path.join(series_dir, subdir, f"{code}.txt")
                dest_file = os.path.join(final_dir, subdir, f"{code}.txt")
                
                if os.path.exists(source_file):
                    shutil.copy2(source_file, dest_file)
                    all_documents.append(doc)
                    policy_sources[code] = series
                    print(f"  - Copied {doc_type} {code} from {series} series")
    
    # Create final summary
    final_summary = {
        'extraction_date': datetime.now().isoformat(),
        'total_documents': len(all_documents),
        'by_type': {
            'policies': len([d for d in all_documents if d['doc_type'] == 'Policy']),
            'regulations': len([d for d in all_documents if d['doc_type'] == 'Regulation']),
            'exhibits': len([d for d in all_documents if d['doc_type'] == 'Exhibit'])
        },
        'by_series': {},
        'documents': all_documents
    }
    
    # Count by series
    for series in ['0000', '1000', '2000', '3000', '4000', '5000', '6000', '7000', '8000', '9000']:
        count = len([code for code in policy_sources.values() if code == series])
        if count > 0:
            final_summary['by_series'][series] = count
    
    # Save final summary
    with open(os.path.join(final_dir, 'extraction_summary.json'), 'w') as f:
        json.dump(final_summary, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Extraction complete!")
    print(f"Total documents: {final_summary['total_documents']}")
    print(f"  - Policies: {final_summary['by_type']['policies']}")
    print(f"  - Regulations: {final_summary['by_type']['regulations']}")
    print(f"  - Exhibits: {final_summary['by_type']['exhibits']}")
    print(f"\nBy series:")
    for series, count in sorted(final_summary['by_series'].items()):
        print(f"  - {series}: {count} documents")
    print(f"\nFinal output in: {final_dir}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    extract_all_policies()