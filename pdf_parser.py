#!/usr/bin/env python3
"""
PDF Policy Parser for RCSD Policy Compliance Analyzer
Uses PyMuPDF (fitz) for robust PDF text extraction
"""

import os
import re
import json
import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass
class PolicyDocument:
    """Represents a single policy, regulation, or exhibit document"""
    code: str
    title: str
    doc_type: str  # 'Policy', 'Regulation', 'Exhibit'
    status: str
    original_adopted_date: Optional[str]
    last_reviewed_date: Optional[str]
    content: str
    references: Dict[str, List[str]]
    source_file: str
    page_numbers: List[int]
    extraction_date: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PDFPolicyParser:
    """Extract policies from PDF documents using PyMuPDF"""
    
    def __init__(self):
        self.documents: List[PolicyDocument] = []
        self.toc_entries: Dict[str, Dict] = {}
        
    def parse_pdf(self, pdf_path: str, output_dir: str = 'extracted_policies') -> List[PolicyDocument]:
        """Parse a PDF file and extract all policies"""
        logger.info(f"\nProcessing: {pdf_path}")
        
        # Clear previous state for this PDF
        self.documents = []
        self.toc_entries = {}
        
        # Create output directories
        self._create_output_dirs(output_dir)
        
        try:
            # Open PDF with PyMuPDF
            pdf_doc = fitz.open(pdf_path)
            
            # Step 1: Parse table of contents
            logger.info("  Parsing table of contents...")
            self._parse_toc(pdf_doc)
            
            # Step 2: Extract documents based on TOC
            logger.info(f"  Extracting {len(self.toc_entries)} documents...")
            for key, toc_entry in sorted(self.toc_entries.items()):
                code = toc_entry['code']
                doc = self._extract_document(pdf_doc, code, toc_entry, os.path.basename(pdf_path))
                if doc:
                    self.documents.append(doc)
                    logger.info(f"    Extracted {doc.doc_type} {doc.code}: {doc.title}")
            
            pdf_doc.close()
            
            # Step 3: Save documents
            logger.info("  Saving documents...")
            self._save_documents(output_dir)
            
            # Step 4: Generate summary
            self._save_summary(output_dir)
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {str(e)}")
            raise
            
        return self.documents
    
    def _create_output_dirs(self, output_dir: str) -> None:
        """Create output directory structure"""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'policies'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'regulations'), exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'exhibits'), exist_ok=True)
    
    def _parse_toc(self, pdf_doc: fitz.Document) -> None:
        """Parse table of contents from first few pages"""
        # Pattern for TOC entries
        toc_pattern = re.compile(
            r'^(Policy|Regulation|Exhibit(?:\s+\(PDF\))?)\s+'
            r'(\d{4}(?:\.\d+)?(?:-E\s+PDF\(\d+\))?)\s*:\s*'
            r'(.+?)\s+(\d+)\s*$',
            re.MULTILINE
        )
        
        # Check first 3 pages for TOC
        for page_num in range(min(3, len(pdf_doc))):
            page = pdf_doc[page_num]
            text = page.get_text()
            
            for match in toc_pattern.finditer(text):
                doc_type = match.group(1).replace(' (PDF)', '')
                code = match.group(2).replace('-E PDF(1)', '-E')
                title = match.group(3).strip().lstrip('^')  # Remove leading ^ from titles
                page = int(match.group(4))
                
                # Determine which series this PDF contains based on filename
                series_match = re.search(r'(\d)000', os.path.basename(pdf_doc.name))
                if series_match:
                    series_prefix = series_match.group(1)
                    # Only include policies from the matching series
                    if code.startswith(series_prefix):
                        # Use a unique key that combines code and type to handle same numbers
                        key = f"{code}_{doc_type}"
                        self.toc_entries[key] = {
                            'type': doc_type,
                            'code': code,
                            'title': title,
                            'page': page - 1  # Convert to 0-based index
                        }
                else:
                    # If we can't determine series from filename, include all
                    key = f"{code}_{doc_type}"
                    self.toc_entries[key] = {
                        'type': doc_type,
                        'code': code,
                        'title': title,
                        'page': page - 1  # Convert to 0-based index
                    }
        
        logger.info(f"    Found {len(self.toc_entries)} entries")
    
    def _extract_document(self, pdf_doc: fitz.Document, code: str, 
                         toc_entry: Dict, source_file: str) -> Optional[PolicyDocument]:
        """Extract a single document based on TOC entry"""
        try:
            start_page = toc_entry['page']
            doc_type = toc_entry['type']
            title = toc_entry['title']
            
            # Find the next document's page to determine end
            end_page = self._find_next_document_page(start_page)
            if end_page is None:
                end_page = len(pdf_doc)
            
            # Extract text from relevant pages
            full_text = ""
            pages = []
            
            for page_num in range(start_page, min(end_page, len(pdf_doc))):
                page = pdf_doc[page_num]
                page_text = page.get_text()
                full_text += page_text + "\n"
                pages.append(page_num + 1)  # Convert back to 1-based
                
                # Stop if we hit another document (safety check)
                if page_num > start_page and self._is_new_document(page_text):
                    break
            
            # Parse the document content
            return self._parse_document_content(
                code, title, doc_type, full_text, pages, source_file
            )
            
        except Exception as e:
            logger.error(f"    Error extracting {code}: {str(e)}")
            return None
    
    def _find_next_document_page(self, current_page: int) -> Optional[int]:
        """Find the page number of the next document"""
        next_page = None
        for entry in self.toc_entries.values():
            if entry['page'] > current_page:
                if next_page is None or entry['page'] < next_page:
                    next_page = entry['page']
        return next_page
    
    def _is_new_document(self, text: str) -> bool:
        """Check if text contains the start of a new document"""
        patterns = [
            r'^Policy\s+\d{4}.*?Status:',
            r'^Regulation\s+\d{4}.*?Status:',
            r'^Exhibit.*?\d{4}.*?Status:'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                return True
        return False
    
    def _parse_document_content(self, code: str, title: str, doc_type: str,
                               full_text: str, pages: List[int], 
                               source_file: str) -> PolicyDocument:
        """Parse document content and extract metadata"""
        
        # Extract status
        status_match = re.search(r'Status:\s*(\w+)', full_text, re.IGNORECASE)
        status = status_match.group(1) if status_match else "ADOPTED"
        
        # Extract dates
        dates = self._extract_dates(full_text)
        
        # Find content boundaries
        content_start = self._find_content_start(full_text, doc_type, code)
        ref_start = self._find_references_start(full_text)
        
        # Extract main content
        main_content = full_text[content_start:ref_start].strip()
        # Remove the disclaimer if it's at the end of content
        main_content = re.sub(r'These references are not intended to be part of the policy itself.*?of the policy\.\s*$', 
                             '', main_content, flags=re.DOTALL | re.IGNORECASE)
        main_content = self._clean_content(main_content)
        
        # Extract references
        ref_text = full_text[ref_start:] if ref_start < len(full_text) else ""
        references = self._extract_references(ref_text)
        
        return PolicyDocument(
            code=code,
            title=title,
            doc_type=doc_type,
            status=status,
            original_adopted_date=dates.get('original'),
            last_reviewed_date=dates.get('reviewed'),
            content=main_content,
            references=references,
            source_file=source_file,
            page_numbers=pages,
            extraction_date=datetime.now().isoformat()
        )
    
    def _extract_dates(self, text: str) -> Dict[str, Optional[str]]:
        """Extract adoption and review dates"""
        dates = {'original': None, 'reviewed': None}
        
        date_pattern = re.compile(
            r'(Original\s+Adopted\s+Date:|Last\s+Reviewed\s+Date:)\s*'
            r'(\d{1,2}/\d{1,2}/\d{4})',
            re.IGNORECASE
        )
        
        for match in date_pattern.finditer(text[:1000]):  # Check first 1000 chars
            date_type = match.group(1).lower()
            date_value = match.group(2)
            
            if 'original' in date_type:
                dates['original'] = date_value
            elif 'reviewed' in date_type:
                dates['reviewed'] = date_value
        
        return dates
    
    def _find_content_start(self, text: str, doc_type: str, code: str) -> int:
        """Find where the main content starts"""
        content_start = 0
        
        # Skip the header disclaimer if present
        header_disclaimer = re.search(r'^Policy Reference Disclaimer:\s*\n', text)
        if header_disclaimer:
            content_start = header_disclaimer.end()
        
        # Try different patterns to find end of header
        patterns = [
            # Handle dates with | separator or newline
            r'Last\s+Reviewed\s+Date:\s*\d{1,2}/\d{1,2}/\d{4}\s*(?:\||\n)',
            r'Original\s+Adopted\s+Date:\s*\d{1,2}/\d{1,2}/\d{4}\s*\|\s*Last\s+Reviewed\s+Date:\s*\d{1,2}/\d{1,2}/\d{4}\s*\n',
            r'Status:\s*\w+\s*\n',
            rf'{doc_type}\s+{re.escape(code)}.*?\n\n'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text[content_start:2000], re.IGNORECASE)
            if match and (match.end() + content_start) > content_start:
                content_start = match.end() + content_start
        
        return content_start
    
    def _find_references_start(self, text: str) -> int:
        """Find where references section starts"""
        ref_start = len(text)
        
        # Look for reference section markers - but skip the header disclaimer
        markers = [
            # More specific pattern to avoid matching header
            r'These references are not intended to be part of the policy itself',
            r'State\s+Description',
            r'Federal\s+Description',  
            r'Management\s+Resources\s+Description'
        ]
        
        for marker in markers:
            match = re.search(marker, text, re.IGNORECASE)
            if match and match.start() < ref_start:
                ref_start = match.start()
        
        return ref_start
    
    def _clean_content(self, content: str) -> str:
        """Clean extracted content"""
        # Remove page headers/footers
        content = re.sub(r'^Board\s*Policy\s*Manual\s*$', '', content, 
                        flags=re.MULTILINE | re.IGNORECASE)
        content = re.sub(r'^Redwood\s*City\s*School\s*District\s*$', '', content, 
                        flags=re.MULTILINE | re.IGNORECASE)
        
        # Remove standalone numbers (page numbers)
        content = re.sub(r'^\d+$', '', content, flags=re.MULTILINE)
        
        
        # Clean excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Fix common OCR/extraction issues
        content = re.sub(r'(\d+)\s*\n\s*\.\s*\n', r'\1. ', content)  # Fix numbered lists
        content = re.sub(r'([a-z])\s*\n\s*\.\s*\n', r'\1. ', content)  # Fix lettered lists
        
        return content.strip()
    
    def _extract_references(self, ref_text: str) -> Dict[str, List[str]]:
        """Extract categorized references"""
        references = {
            'state': [],
            'federal': [],
            'management': [],
            'cross_references': []
        }
        
        # Remove policy reference disclaimer
        ref_text = re.sub(r'Policy Reference Disclaimer.*?of the policy\.', '', 
                         ref_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Define sections with their patterns
        sections = {
            'state': r'State\s*\n?\s*Description\s*\n(.*?)(?=Federal|Management|Cross|$)',
            'federal': r'Federal\s*\n?\s*Description\s*\n(.*?)(?=Management|Cross|$)',
            'management': r'Management\s+Resources\s*\n?\s*Description\s*\n(.*?)(?=Cross|$)',
            'cross_references': r'Cross\s+References\s*\n?\s*Description\s*\n(.*?)$'
        }
        
        for ref_type, pattern in sections.items():
            match = re.search(pattern, ref_text, re.DOTALL | re.IGNORECASE)
            if match:
                ref_content = match.group(1).strip()
                
                # Special handling for cross references
                if ref_type == 'cross_references':
                    refs_seen = set()
                    current_code = None
                    
                    for line in ref_content.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Check if this line is a policy code (4 digits, possibly with decimals)
                        code_match = re.match(r'^(\d{4}(?:\.\d+)?(?:-E)?)$', line)
                        if code_match:
                            current_code = code_match.group(1)
                        elif current_code and line and not line.lower().startswith('cross references'):
                            # This is the title for the previous code
                            ref_entry = f"{current_code} ({line})"
                            if ref_entry not in refs_seen:
                                references[ref_type].append(ref_entry)
                                refs_seen.add(ref_entry)
                            current_code = None
                else:
                    # For other reference types, just extract and deduplicate
                    refs_seen = set()
                    for line in ref_content.split('\n'):
                        line = line.strip()
                        # Filter out non-reference lines
                        if (line and 
                            not line.lower().startswith('website') and 
                            line.lower() != 'description' and
                            len(line) > 5 and
                            not line.startswith('Board Policy Manual') and
                            not line.startswith('Policy Reference Disclaimer') and
                            not line.startswith('These references are not intended')):
                            if line not in refs_seen:
                                references[ref_type].append(line)
                                refs_seen.add(line)
        
        return references
    
    def _save_documents(self, output_dir: str) -> None:
        """Save documents as structured text files"""
        for doc in self.documents:
            # Determine subdirectory
            subdir = {
                'Policy': 'policies',
                'Regulation': 'regulations',
                'Exhibit': 'exhibits'
            }.get(doc.doc_type, 'other')
            
            # Create filename
            filename = f"{doc.code}.txt"
            filepath = os.path.join(output_dir, subdir, filename)
            
            # Format content
            content = self._format_document(doc)
            
            # Save file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def _format_document(self, doc: PolicyDocument) -> str:
        """Format document for saving"""
        content = f"""RCSD {doc.doc_type} {doc.code}
================================================================================
Title: {doc.title}
Status: {doc.status}
Original Adopted Date: {doc.original_adopted_date or 'Not specified'}
Last Reviewed Date: {doc.last_reviewed_date or 'Not specified'}
Source: {doc.source_file} (Pages {', '.join(map(str, doc.page_numbers))})
================================================================================

{doc.content}

================================================================================
REFERENCES
================================================================================
"""
        
        # Add references by category
        ref_categories = [
            ('State References', 'state'),
            ('Federal References', 'federal'),
            ('Management Resources', 'management'),
            ('Cross References', 'cross_references')
        ]
        
        for category_name, ref_key in ref_categories:
            if doc.references.get(ref_key):
                content += f"\n{category_name}:\n"
                for ref in doc.references[ref_key]:
                    content += f"  - {ref}\n"
        
        return content
    
    def _save_summary(self, output_dir: str) -> None:
        """Save extraction summary"""
        summary = {
            'extraction_date': datetime.now().isoformat(),
            'total_documents': len(self.documents),
            'by_type': {
                'policies': len([d for d in self.documents if d.doc_type == 'Policy']),
                'regulations': len([d for d in self.documents if d.doc_type == 'Regulation']),
                'exhibits': len([d for d in self.documents if d.doc_type == 'Exhibit'])
            },
            'documents': [doc.to_dict() for doc in self.documents]
        }
        
        output_file = os.path.join(output_dir, 'extraction_summary.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nExtraction complete!")
        logger.info(f"Total documents: {summary['total_documents']}")
        logger.info(f"  - Policies: {summary['by_type']['policies']}")
        logger.info(f"  - Regulations: {summary['by_type']['regulations']}")
        logger.info(f"  - Exhibits: {summary['by_type']['exhibits']}")
        logger.info(f"\nSummary saved to: {output_file}")


def main():
    """CLI interface for PDF parser"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Extract policies from RCSD PDF files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_parser.py policies/RCSD_Policies_1000.pdf
  python pdf_parser.py policies/ --output-dir extracted
        """
    )
    
    parser.add_argument('pdf_path', help='Path to PDF file or directory')
    parser.add_argument('--output-dir', default='extracted_policies', 
                       help='Output directory (default: extracted_policies)')
    
    args = parser.parse_args()
    
    parser = PDFPolicyParser()
    
    if os.path.isfile(args.pdf_path) and args.pdf_path.endswith('.pdf'):
        # Single PDF file
        parser.parse_pdf(args.pdf_path, args.output_dir)
    elif os.path.isdir(args.pdf_path):
        # Directory of PDFs
        pdf_files = [f for f in os.listdir(args.pdf_path) if f.endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in sorted(pdf_files):
            pdf_path = os.path.join(args.pdf_path, pdf_file)
            parser.parse_pdf(pdf_path, args.output_dir)
    else:
        logger.error(f"Invalid path: {args.pdf_path}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())