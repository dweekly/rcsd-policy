# RCSD Policy Compliance Analyzer

⚠️ **IMPORTANT DISCLAIMER** ⚠️

**This repository is NOT OFFICIAL and may contain material errors.** The extracted policies are provided for analysis purposes only and should not be considered authoritative.

**For the official, authoritative, and up-to-date RCSD policies, please consult:**  
**https://simbli.eboardsolutions.com/Policy/PolicyListing.aspx?S=36030397**

---

## Overview

This project extracts and analyzes Redwood City School District (RCSD) policies from PDF documents to support compliance tracking and cross-referencing. It processes policy documents organized by series (0000-7000 and 9000) and extracts individual policies, regulations, and exhibits.

**Policy Currency:** The PDF files in the `policies/` folder were downloaded from the official RCSD website on **May 30, 2025**. They may be outdated after this date. Always check the official website for the most current versions.

## Current Status

- ✅ **PDF Extraction**: Successfully extracted 512 documents from RCSD policy PDFs
- ✅ **Cross-Reference Validation**: Identified and validated policy cross-references
- ✅ **Multi-format Support**: Handles policies, regulations, and exhibits
- ✅ **Compliance Analysis**: Completed - analyzed all 512 documents against CA Education Code
- 🚧 **CSBA Alignment**: Future feature to evaluate alignment with CSBA best practices

### Compliance Analysis Results
- **292 material compliance issues** identified across all documents
- **97 documents (61%)** require updates to meet legal requirements
- **61 documents (39%)** are fully compliant
- See `COMPLIANCE_SUMMARY.md` for detailed findings and board recommendations

## Features

### Implemented Features
- **PDF Table of Contents Parsing**: Accurately identifies document boundaries using TOC
- **Multi-line Entry Support**: Handles TOC entries that span multiple lines
- **Document Type Recognition**: Distinguishes between policies, regulations, exhibits, and bylaws
- **Metadata Extraction**: Captures adoption dates, status, and source information
- **Reference Extraction**: Parses state, federal, and cross-references
- **Cross-Reference Validation**: Identifies missing or broken policy references
- **Compliance Analysis**: Analyzes policies against California Education Code requirements
- **Material Non-Compliance Detection**: Identifies issues requiring board action
- **Comprehensive Reporting**: Generates detailed reports in JSON and text formats
- **Batch Processing**: Efficiently processes hundreds of documents

### Future Enhancements
- CSBA best practice alignment checking
- Excel report generation
- Policy change tracking over time
- Interactive visualization dashboard
- See `TODO.md` for complete roadmap

## Installation

1. Clone the repository with Git LFS support:
```bash
# Ensure Git LFS is installed
git lfs install

# Clone the repository (this will also download the PDF files)
git clone https://github.com/dweekly/rcsd-policy.git
cd rcsd-policy
```

**Note:** The PDF files in the `policies/` folder are stored using Git LFS (Large File Storage). If you don't have Git LFS installed, you can install it from https://git-lfs.github.com/

If you've already cloned the repository without Git LFS, you can fetch the PDF files with:
```bash
git lfs fetch
git lfs checkout
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment for compliance checking (optional):
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Get your API key from: https://console.anthropic.com/
```

## Usage

### Extract All Policies
```bash
python scripts/extract_all_policies.py
```

This will:
- Process all PDF files in the `data/source/pdfs/` directory
- Extract individual policies to `data/extracted/`
- Generate an extraction summary with statistics

### Validate Cross-References
```bash
python scripts/check_cross_references.py
```

This will:
- Analyze all extracted policies for cross-references
- Identify any missing referenced policies
- Report gaps in policy numbering by series

### Run Compliance Analysis
```bash
python scripts/compliance_check_comprehensive.py --policy data/extracted/policies/1234.txt
```

Or for batch analysis:
```bash
python scripts/compliance_check_batch.py --max 100
```

This will:
- Analyze policies for compliance with current CA Education Code
- Identify material compliance issues requiring board action
- Use Claude AI to provide specific legal citations and required language
- Generate detailed compliance reports in JSON and text formats

**Results**: See `data/analysis/compliance/COMPLIANCE_SUMMARY.md` for the complete analysis of all 512 RCSD documents.

## Project Structure

```
rcsd-policy/
├── data/                           # All data files (input and output)
│   ├── source/                     # Original source files
│   │   └── pdfs/                   # PDF source files (tracked with Git LFS)
│   │       ├── RCSD Policies 0000.pdf     # Board Bylaws
│   │       ├── RCSD Policies 1000.pdf     # Community Relations
│   │       ├── RCSD Policies 2000.pdf     # Administration
│   │       ├── RCSD Policies 3000.pdf     # Business and Non-instructional Operations
│   │       ├── RCSD Policies 4000.pdf     # Personnel
│   │       ├── RCSD Policies 5000.pdf     # Students
│   │       ├── RCSD Policies 6000.pdf     # Instruction
│   │       ├── RCSD Policies 7000.pdf     # Facilities
│   │       └── RCSD Policies 9000.pdf     # Board Bylaws (continued)
│   │
│   ├── extracted/                  # Extracted text documents (512 total)
│   │   ├── policies/               # Policy documents (308 files)
│   │   ├── regulations/            # Administrative regulations (192 files)
│   │   └── exhibits/               # Exhibits and forms (12 files)
│   │
│   ├── analysis/                   # Analysis results
│   │   └── compliance/             # Compliance check results
│   │       ├── COMPLIANCE_SUMMARY.md      # Executive summary for board
│   │       ├── json_data/          # Individual compliance reports (356 files)
│   │       └── material_issues/    # Material issues summaries (293 files)
│   │
│   └── cache/                      # API response cache for compliance checks
│
├── scripts/                        # All Python scripts
│   ├── pdf_parser.py               # Core PDF extraction engine using PyMuPDF
│   ├── extract_all_policies.py     # Batch extraction tool for all PDFs
│   ├── check_cross_references.py   # Validates cross-references, finds missing policies
│   ├── compliance_checker.py       # Core compliance module with caching support
│   ├── compliance_check_comprehensive.py # Main compliance analysis using Claude AI
│   ├── compliance_check_batch.py   # Batch processing with priority-based ordering
│   ├── policy_researcher.py        # Research and analysis utilities
│   └── main.py                     # Main entry point for the application
│
├── docs/                           # Documentation
│   ├── AGENTS.md                   # Guidelines for AI assistants working on this repo
│   ├── ARCHITECTURE.md             # System design and technical architecture
│   ├── COMPLIANCE_PLAN.md          # Detailed compliance checking implementation plan
│   ├── COMPLIANCE_USAGE.md         # How to use the compliance checking tools
│   ├── CROSS_REFERENCE_ANALYSIS.md # Analysis of missing cross-referenced policies
│   ├── EMPTY_POLICIES_SUMMARY.md   # Documentation of policies with no content
│   └── PUBLICATION_README.md       # Summary for public consumption
│
├── schemas/                        # Data schemas
│   └── compliance_output_schema.xml # XML schema for compliance report format
│
└── Configuration:
    ├── README.md                   # Project overview (this file)
    ├── TODO.md                     # Known issues and future enhancements
    ├── requirements.txt            # Python dependencies
    ├── pyproject.toml              # Python project configuration (ruff settings)
    ├── .gitignore                  # Git ignore rules
    ├── .gitattributes              # Git LFS configuration for PDFs
    └── .env.example                # Example environment configuration
```

### Script → Output Mapping

| Script | Purpose | Output Location |
|--------|---------|-----------------|
| `scripts/extract_all_policies.py` | Extract all policies from PDFs | `data/extracted/` |
| `scripts/pdf_parser.py` | Core extraction module | Used by other scripts |
| `scripts/check_cross_references.py` | Find missing referenced policies | Console output + `docs/CROSS_REFERENCE_ANALYSIS.md` |
| `scripts/compliance_check_comprehensive.py` | Analyze policy compliance | `data/analysis/compliance/` |
| `scripts/compliance_check_batch.py` | Batch compliance checking | Same as above + summary reports |

### Key Directories

**Source Data:**
- `data/source/pdfs/` - Original PDF files from RCSD website (May 30, 2025)

**Extracted Data:**
- `data/extracted/` - All extracted documents organized by type

**Analysis Output:**
- `data/analysis/compliance/` - All compliance analysis results
- `data/cache/` - Cached API responses to avoid redundant calls

**Which Script to Use:**
- **For extraction:** Use `scripts/extract_all_policies.py`
- **For compliance:** Use `scripts/compliance_check_comprehensive.py` (most complete)
- **For cross-references:** Use `scripts/check_cross_references.py`

## Technical Details

The PDF parser uses PyMuPDF (fitz) to:
1. Extract text from PDF documents
2. Parse table of contents to identify document boundaries
3. Handle multi-line TOC entries (e.g., titles split across lines)
4. Extract metadata (dates, status, references)
5. Save individual documents with consistent formatting

## Output Format

Each extracted document includes:
- Header with title, status, and dates
- Main policy/regulation content
- Reference section with:
  - State references (CA codes)
  - Federal references (USC)
  - Management resources
  - Cross-references to other policies

## Known Limitations

- Some policies referenced by others may not exist in the source PDFs
- The extraction relies on consistent TOC formatting
- Manual updates to the official website are not automatically reflected

## Development

### Code Quality

This project uses `ruff` for linting and formatting Python code:

```bash
# Run linter with auto-fix
ruff check --fix .

# Format code
ruff format .
```

Configuration is in `pyproject.toml`. The linter enforces:
- PEP 8 style guidelines
- Modern Python practices (Python 3.9+)
- Import sorting
- Common bug prevention
- Consistent formatting

## Contributing

This project is primarily for analysis purposes. If you notice extraction errors or have suggestions for the compliance analysis features, please open an issue.

## License

This project is for educational and analysis purposes only. The policies themselves remain the property of the Redwood City School District.