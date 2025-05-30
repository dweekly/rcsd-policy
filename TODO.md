# TODO List - RCSD Policy Compliance Analyzer

## Active Tasks

### High Priority
- [ ] Process remaining PDF series (2000, 3000, 4000, etc.)
- [ ] Implement cross-reference validation to ensure referenced policies exist
- [ ] Handle special cases in PDF extraction (e.g., exhibits with -E suffixes)

### Medium Priority
- [ ] Create summary statistics for all extracted policies
- [ ] Build compliance analysis features
- [ ] Implement policy change tracking (compare versions over time)
- [ ] Add error handling for malformed PDFs

### Low Priority
- [ ] Create visualization dashboard for policy relationships
- [ ] Add full-text search capability across all policies
- [ ] Generate compliance reports in various formats (PDF, Excel, etc.)

## Completed Tasks
- [x] Switch from web scraping to PDF processing approach
- [x] Resolve text doubling issue (switched from pdfplumber to PyMuPDF)
- [x] Implement TOC-based extraction for accurate policy boundaries
- [x] Successfully extract 1000 series policies
- [x] Create AGENTS.md for AI tool guidance
- [x] Consolidate requirements files
- [x] Remove unused dependencies
- [x] Update pip in virtual environment

## Technical Debt
- [ ] Add comprehensive unit tests for pdf_parser.py
- [ ] Add logging configuration options (currently hardcoded)
- [ ] Consider chunking very large PDFs for memory efficiency
- [ ] Add progress bars for long-running extractions

## Notes and Observations

### PDF Structure Patterns
- Each PDF contains policies from a specific number series (0000, 1000, 2000, etc.)
- TOC typically appears in first 3 pages
- Policy boundaries marked by "Status:" lines and reference sections
- Some policies have decimal codes (e.g., 1312.4) and exhibit suffixes (e.g., 1313-E)

### Known Issues
- Some PDFs may have different formatting that could break current parser
- Cross-references sometimes point to non-existent policies (need validation)
- Exhibit documents with -E suffix need special handling

### Temporary Changes / Experiments
- None currently

## Future Enhancements
- [ ] Add OCR capability for scanned PDFs
- [ ] Implement diff viewer for policy changes
- [ ] Create API for policy access
- [ ] Add natural language search using embeddings
- [ ] Build compliance scoring system

## Session Notes
*Use this section to capture important context from current work session*

- Successfully pivoted from web scraping to PDF processing
- PyMuPDF (fitz) chosen as the most reliable PDF extraction library
- 27 documents extracted from 1000 series PDF
- Project structure established with proper .gitignore and requirements