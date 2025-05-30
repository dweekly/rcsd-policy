# RCSD Policy Compliance Analyzer - Agent Guidance

## Project Overview

This project is a PDF-based policy extraction and analysis system for the Redwood City School District (RCSD). It processes large PDF documents containing district policies, regulations, and exhibits, extracting individual documents and organizing them for compliance analysis.

## Project History

### Initial Approach (Abandoned)
- Originally designed as a web scraping tool using Selenium and CloudScraper
- Web scraping was blocked by the district website, requiring a pivot to PDF processing

### Current Architecture
- PDF-based extraction using PyMuPDF (fitz) library
- Processes ~10 large PDFs (15-300 pages each) containing district policies
- Extracts policies by their four-digit codes (e.g., 1313) with decimal variations (e.g., 1312.4)
- Creates organized file structure with metadata and cross-references

### Technical Evolution
1. **First Attempt**: Used pdfplumber - had text doubling issues ("PPoolliiccyy" instead of "Policy")
2. **Second Attempt**: Tried PyPDF2 - cleaner but still had issues
3. **Final Solution**: PyMuPDF (fitz) - provides robust, clean text extraction
4. **Key Innovation**: TOC-based navigation to accurately locate and extract individual policies

## Key Components

### Main Parser: `pdf_parser.py`
- Uses PyMuPDF for text extraction
- Implements TOC parsing for document location
- Extracts policies with full metadata (title, dates, references)
- Validates policy boundaries using status lines and reference sections

### Directory Structure
```
rcsd-policy/
├── policies/              # Source PDF files
├── extracted_policies/    # Extracted policy text files
│   ├── policies/         # Policy documents
│   ├── regulations/      # Regulation documents
│   └── exhibits/         # Exhibit documents
├── pdf_parser.py         # Main extraction script
└── requirements.txt      # Python dependencies
```

## Working with This Repository

### Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`

### Running the Parser
**IMPORTANT**: Always activate the virtual environment before running Python scripts!
```bash
# ALWAYS START WITH:
cd /Users/dew/dev/rcsd-policy && source venv/bin/activate

# Single PDF
python pdf_parser.py "policies/RCSD Policies 1000.pdf"

# All PDFs in directory
python pdf_parser.py policies/ --output-dir extracted_policies
```

### Common Mistakes to Avoid
1. **Forgetting to activate venv** - Always run `source venv/bin/activate` before any Python commands
2. **Not quoting file paths with spaces** - Use quotes: `"policies/RCSD Policies 1000.pdf"`
3. **Calling anything "final"** - Nothing is ever final in software development!
4. **Assuming duplicates** - Cross-references often link to both policies AND regulations with similar names

### Key Technical Decisions

1. **PyMuPDF over alternatives**: Chosen for clean text extraction without character doubling
2. **TOC-based extraction**: More reliable than pattern matching for document boundaries
3. **Structured output format**: Each policy saved with metadata header for easy parsing
4. **Reference extraction**: Captures state, federal, management, and cross-references

### Common Issues and Solutions

1. **Text doubling**: Solved by switching from pdfplumber to PyMuPDF
2. **Wrong policy extraction**: Solved by validating policy number ranges per PDF
3. **TOC vs content confusion**: Solved by implementing proper TOC parsing logic
4. **Policy boundary detection**: Uses status lines and reference sections as markers

## For AI Agents

### Critical: TODO.md Usage
**IMPORTANT**: Always maintain and update the `TODO.md` file as your primary memory and state preservation mechanism between sessions. This file serves as:
- Your scratchpad for remembering tasks and context
- A priority-ordered task list
- A place to note temporary changes that need reverting
- Session notes for important observations

**Before starting work**: Read TODO.md to understand current state and priorities
**During work**: Update TODO.md with new tasks, completed items, and observations
**Before ending session**: Ensure TODO.md reflects all pending work and context

### Important Context
- This is a compliance analysis tool for educational policies
- Focus on accuracy in extraction - policy numbers and content must be exact
- Cross-references are critical for compliance checking
- Each PDF contains a specific number series (0000, 1000, 2000, etc.)

### Best Practices
1. Always read existing code before making changes
2. Test extraction on sample PDFs before bulk processing
3. Preserve the structured metadata format in extracted files
4. Validate cross-references exist when implementing analysis features
5. Keep TODO.md updated as your primary state preservation tool

### Current State
- Successfully extracts policies from 1000 series
- 27 documents extracted including policies, regulations, and exhibits
- Ready for expansion to other number series and compliance analysis features

### Next Steps Typically Include
1. Processing remaining PDF series (2000, 3000, etc.)
2. Implementing cross-reference validation
3. Building compliance analysis features
4. Creating summary reports and dashboards

## Git Workflow
- Repository initialized but not yet pushed to remote
- Use meaningful commit messages describing policy-related changes
- Keep PDFs out of version control (already in .gitignore)

## Dependencies
- PyMuPDF (fitz): PDF text extraction
- Standard library only for other functionality
- No web scraping libraries needed anymore