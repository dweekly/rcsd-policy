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

### Key Scripts and Files

**Scripts Directory (`scripts/`)**
- `pdf_parser.py` - Core PDF extraction engine using PyMuPDF
- `extract_all_policies.py` - Batch extraction tool for processing all PDFs
- `check_cross_references.py` - Validates policy cross-references and finds missing documents
- `compliance_check_comprehensive.py` - Main compliance analysis tool using Claude AI
- `compliance_check_batch.py` - Batch compliance checking with priority-based processing
- `compliance_checker.py` - Core compliance checking module with caching
- `policy_researcher.py` - Research tools for policy analysis
- `main.py` - Main entry point for the application

**Documentation (`docs/`)**
- `AGENTS.md` - This file - AI assistant guidelines
- `ARCHITECTURE.md` - System design and technical architecture
- `COMPLIANCE_PLAN.md` - Detailed plan for compliance checking implementation
- `COMPLIANCE_USAGE.md` - How to use the compliance checking tools
- `CROSS_REFERENCE_ANALYSIS.md` - Analysis of missing cross-referenced policies
- `EMPTY_POLICIES_SUMMARY.md` - Documentation of policies with no content
- `PUBLICATION_README.md` - Summary for public consumption

### Directory Structure
```
rcsd-policy/
├── data/                          # All data files
│   ├── source/                    # Source documents
│   │   └── pdfs/                  # PDF files (tracked with Git LFS)
│   ├── extracted/                 # Extracted text documents
│   │   ├── policies/              # Policy documents
│   │   ├── regulations/           # Administrative regulations
│   │   └── exhibits/              # Exhibits and forms
│   ├── analysis/                  # Analysis results
│   │   └── compliance/            # Compliance check results
│   │       ├── COMPLIANCE_SUMMARY.md  # Executive summary
│   │       ├── json_data/         # Individual compliance data
│   │       └── material_issues/   # Material compliance issues
│   └── cache/                     # API response cache
├── scripts/                       # All Python scripts
├── docs/                          # Documentation
├── schemas/                       # Data schemas
│   └── compliance_output_schema.xml  # Compliance report format
└── Configuration files
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

# Extract all policies
python scripts/extract_all_policies.py

# Check cross-references
python scripts/check_cross_references.py

# Run compliance analysis on a single policy
python scripts/compliance_check_comprehensive.py --policy data/extracted/policies/1234.txt

# Run batch compliance analysis
python scripts/compliance_check_batch.py --max 100
```

### Common Mistakes to Avoid
1. **Forgetting to activate venv** - Always run `source venv/bin/activate` before any Python commands
2. **Not quoting file paths with spaces** - Use quotes: `"data/source/pdfs/RCSD Policies 1000.pdf"`
3. **Calling anything "final"** - Nothing is ever final in software development!
4. **Assuming duplicates** - Cross-references often link to both policies AND regulations with similar names
5. **Using chmod +x on Python scripts** - NEVER use chmod +x on Python scripts. Always run with `python script.py`
   - Python scripts should NOT have executable bits set in git
   - This is standard Python practice and avoids platform-specific issues

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
- Your priority-ordered task list for PENDING and IN-PROGRESS items only
- A place to note temporary changes that need reverting
- Session notes for important observations
- **DO NOT** keep completed tasks in TODO.md - remove them once done

**Before starting work**: Read TODO.md to understand current state and priorities
**During work**: Update TODO.md with new tasks, mark items as in-progress, and REMOVE completed items
**Before ending session**: Ensure TODO.md reflects only pending work and current context

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
- Successfully extracts policies from all series (0000-9000)
- 512 documents extracted including 308 policies, 192 regulations, and 12 exhibits
- Completed comprehensive compliance analysis identifying 292 material issues
- Repository reorganized with clear data/scripts/docs structure

### Recently Completed
1. ✅ Extracted all 512 documents from 9 PDF files
2. ✅ Validated cross-references and identified missing policies
3. ✅ Built comprehensive compliance analysis system
4. ✅ Generated executive summary with board recommendations
5. ✅ Reorganized repository structure for clarity

### Next Steps Typically Include
1. Re-running extraction after directory reorganization
2. Implementing CSBA best practice alignment
3. Adding Excel report generation
4. Creating visualization dashboard

## Git Workflow
- Repository initialized and pushed to GitHub (github.com/dweekly/rcsd-policy)
- Use meaningful commit messages describing policy-related changes
- PDFs are tracked with Git LFS (Large File Storage)
- **CRITICAL**: Always use `git mv` when relocating ANY tracked file
  - NEVER use cp/rm or manual move operations for tracked files
  - This is especially important for LFS-tracked files (PDFs)
  - Using `git mv` preserves file history and ensures proper LFS handling
- **IMPORTANT**: Before committing, check for temporary test files:
  - Exclude: test_*.py, *_test.py, scratch_*.py, temp_*.py
  - Exclude: proposed_updates_*.md, one-off analysis scripts
  - These patterns are in .gitignore but double-check before commits

## Dependencies
- PyMuPDF (fitz): PDF text extraction
- Anthropic: Claude AI API for compliance analysis
- python-dotenv: Environment variable management
- Standard library for other functionality