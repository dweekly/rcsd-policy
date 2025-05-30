#!/usr/bin/env python3
"""
Fixed PDF Policy Parser for RCSD Policy Compliance Analyzer
Handles multi-line TOC entries like 4319.12
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
            self._parse_toc_improved(pdf_doc)
            
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
    
    def _parse_toc_improved(self, pdf_doc: fitz.Document) -> None:
        """Parse table of contents handling multi-line entries"""
        # Check first 10 pages for TOC (increased from 5)
        for page_num in range(min(10, len(pdf_doc))):
            page = pdf_doc[page_num]
            text = page.get_text()
            lines = text.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Check if this line starts with a document type
                doc_type_match = re.match(r'^(Policy|Regulation|Exhibit(?:\s+\(PDF\))?|Bylaw)\s+(\d{4}(?:\.\d+)?(?:-E(?:\s+PDF\(\d+\))?)?)\s*:\s*(.+?)(?:\s+(\d+))?$', line)
                
                if doc_type_match:
                    doc_type = doc_type_match.group(1).replace(' (PDF)', '')
                    code = doc_type_match.group(2).replace('-E PDF(1)', '-E')
                    title = doc_type_match.group(3).strip().lstrip('^')
                    page_num_str = doc_type_match.group(4)
                    
                    # If no page number on this line, check next lines
                    if not page_num_str and i + 1 < len(lines):
                        # Check if title continues on next line(s)
                        j = i + 1
                        while j < len(lines) and j < i + 5:  # Check up to 5 lines ahead
                            next_line = lines[j].strip()
                            
                            # Check if this line is just a page number
                            if re.match(r'^\d+$', next_line):
                                page_num_str = next_line
                                break
                            # Check if this line ends with a page number
                            elif re.match(r'^(.+?)\s+(\d+)$', next_line):
                                match = re.match(r'^(.+?)\s+(\d+)$', next_line)
                                title += " " + match.group(1)
                                page_num_str = match.group(2)
                                break
                            # Otherwise, it's a continuation of the title
                            elif next_line and not re.match(r'^(Policy|Regulation|Exhibit|Bylaw)\s+\d{4}', next_line):
                                title += " " + next_line
                            else:
                                break
                            j += 1
                    
                    if page_num_str:
                        page = int(page_num_str)
                        
                        # Determine which series this PDF contains
                        series_match = re.search(r'(\d)000', os.path.basename(pdf_doc.name))
                        if series_match:
                            series_prefix = series_match.group(1)
                            if code.startswith(series_prefix):
                                key = f"{code}_{doc_type}"
                                self.toc_entries[key] = {
                                    'type': doc_type,
                                    'code': code,
                                    'title': title,
                                    'page': page - 1  # Convert to 0-based
                                }
                        else:
                            key = f"{code}_{doc_type}"
                            self.toc_entries[key] = {
                                'type': doc_type,
                                'code': code,
                                'title': title,
                                'page': page - 1
                            }
                
                i += 1
        
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
            match = re.search(marker, text[1000:], re.IGNORECASE)  # Skip first 1000 chars
            if match:
                potential_start = match.start() + 1000
                if potential_start < ref_start:
                    ref_start = potential_start
        
        return ref_start
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content text"""
        # Remove excessive whitespace while preserving paragraph breaks
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r' {2,}', ' ', content)
        
        # Remove page numbers (standalone numbers on lines)
        content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
        
        # Remove header/footer artifacts
        content = re.sub(r'^RCSD.*?$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Page \d+ of \d+$', '', content, flags=re.MULTILINE)
        
        return content.strip()
    
    def _extract_references(self, ref_text: str) -> Dict[str, List[str]]:
        """Extract and categorize references"""
        references = {
            'state': [],
            'federal': [],
            'management': [],
            'cross_references': []
        }
        
        if not ref_text:
            return references
        
        # Split by reference type sections
        sections = {
            'state': re.search(r'State\s+(?:References|Description)(.*?)(?=Federal|Management|Cross|$)', 
                              ref_text, re.IGNORECASE | re.DOTALL),
            'federal': re.search(r'Federal\s+(?:References|Description)(.*?)(?=State|Management|Cross|$)', 
                                ref_text, re.IGNORECASE | re.DOTALL),
            'management': re.search(r'Management\s+Resources?\s*(?:Description)?(.*?)(?=State|Federal|Cross|$)', 
                                   ref_text, re.IGNORECASE | re.DOTALL),
            'cross_references': re.search(r'Cross\s+References?(.*?)(?=State|Federal|Management|$)', 
                                         ref_text, re.IGNORECASE | re.DOTALL)
        }
        
        for ref_type, match in sections.items():
            if match:
                section_text = match.group(1)
                # Extract individual references
                refs = self._parse_reference_section(section_text, ref_type)
                references[ref_type] = refs
        
        return references
    
    def _parse_reference_section(self, section_text: str, ref_type: str) -> List[str]:
        """Parse individual references from a section"""
        refs = []
        
        if ref_type == 'cross_references':
            # Pattern for cross references like "0415 (Equity)"
            pattern = re.compile(r'(\d{4}(?:\.\d+)?)\s*\(([^)]+)\)')
            for match in pattern.finditer(section_text):
                refs.append(f"{match.group(1)} ({match.group(2)})")
        else:
            # Split by common delimiters and clean
            lines = section_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.lower().startswith(('description', 'references')):
                    # Remove leading dashes or bullets
                    line = re.sub(r'^[-•]\s*', '', line)
                    if line:
                        refs.append(line)
        
        return refs
    
    def _save_documents(self, output_dir: str) -> None:
        """Save extracted documents to files"""
        for doc in self.documents:
            # Determine subdirectory based on document type
            if doc.doc_type == 'Policy' or doc.doc_type == 'Bylaw':
                subdir = 'policies'
            elif doc.doc_type == 'Regulation':
                subdir = 'regulations'
            else:
                subdir = 'exhibits'
            
            # Create filename
            filename = f"{doc.code}.txt"
            filepath = os.path.join(output_dir, subdir, filename)
            
            # Format content for saving
            content_lines = [
                f"RCSD {doc.doc_type} {doc.code}",
                "=" * 80,
                f"Title: {doc.title}",
                f"Status: {doc.status}",
                f"Original Adopted Date: {doc.original_adopted_date or 'Not specified'}",
                f"Last Reviewed Date: {doc.last_reviewed_date or 'Not specified'}",
                f"Source: {doc.source_file} (Pages {', '.join(map(str, doc.page_numbers))})",
                "=" * 80,
                "",
                doc.content,
                ""
            ]
            
            # Add references if they exist
            if any(doc.references.values()):
                content_lines.extend([
                    "=" * 80,
                    "REFERENCES",
                    "=" * 80,
                    ""
                ])
                
                if doc.references['state']:
                    content_lines.append("State References:")
                    for ref in doc.references['state']:
                        content_lines.append(f"  - {ref}")
                    content_lines.append("")
                
                if doc.references['federal']:
                    content_lines.append("Federal References:")
                    for ref in doc.references['federal']:
                        content_lines.append(f"  - {ref}")
                    content_lines.append("")
                
                if doc.references['management']:
                    content_lines.append("Management Resources:")
                    for ref in doc.references['management']:
                        content_lines.append(f"  - {ref}")
                    content_lines.append("")
                
                if doc.references['cross_references']:
                    content_lines.append("Cross References:")
                    for ref in doc.references['cross_references']:
                        content_lines.append(f"  - {ref}")
                    content_lines.append("")
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))
    
    def _save_summary(self, output_dir: str) -> None:
        """Save extraction summary as JSON"""
        summary = {
            'extraction_date': datetime.now().isoformat(),
            'total_documents': len(self.documents),
            'by_type': {},
            'by_series': {},
            'documents': [doc.to_dict() for doc in self.documents]
        }
        
        # Count by type
        for doc in self.documents:
            doc_type = 'policies' if doc.doc_type in ['Policy', 'Bylaw'] else doc.doc_type.lower() + 's'
            summary['by_type'][doc_type] = summary['by_type'].get(doc_type, 0) + 1
        
        # Count by series
        for doc in self.documents:
            series = doc.code[:1] + '000'
            summary['by_series'][series] = summary['by_series'].get(series, 0) + 1
        
        # Save summary
        summary_path = os.path.join(output_dir, 'extraction_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        logger.info(f"\nExtraction complete!")
        logger.info(f"Total documents: {summary['total_documents']}")
        for doc_type, count in summary['by_type'].items():
            logger.info(f"  - {doc_type.capitalize()}: {count}")
        logger.info(f"\nSummary saved to: {summary_path}")