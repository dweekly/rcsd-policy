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

- ✅ **PDF Extraction**: Successfully extracts 512 documents from RCSD policy PDFs
- ✅ **Cross-Reference Validation**: Identifies and validates policy cross-references
- ✅ **Multi-format Support**: Handles policies, regulations, and exhibits
- 🚧 **Compliance Analysis**: Planned feature to analyze policies against CA Education Code
- 🚧 **CSBA Alignment**: Planned feature to evaluate alignment with CSBA best practices

## Features

### Implemented
- **PDF Table of Contents Parsing**: Accurately identifies document boundaries using TOC
- **Multi-line Entry Support**: Handles TOC entries that span multiple lines
- **Document Type Recognition**: Distinguishes between policies, regulations, exhibits, and bylaws
- **Metadata Extraction**: Captures adoption dates, status, and source information
- **Reference Extraction**: Parses state, federal, and cross-references
- **Cross-Reference Validation**: Identifies missing or broken policy references

### Planned
- Compliance analysis against California Education Code
- CSBA best practice alignment checking
- Material non-compliance detection
- Comprehensive reporting in JSON and Excel formats

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

## Usage

### Extract All Policies
```bash
python extract_all_policies.py
```

This will:
- Process all PDF files in the `policies/` directory
- Extract individual policies to `extracted_policies_all/`
- Generate an extraction summary with statistics

### Validate Cross-References
```bash
python check_cross_references.py
```

This will:
- Analyze all extracted policies for cross-references
- Identify any missing referenced policies
- Report gaps in policy numbering by series

## Project Structure

```
rcsd-policy/
├── policies/                    # Source PDF files (tracked with Git LFS)
│   ├── RCSD Policies 0000.pdf
│   ├── RCSD Policies 1000.pdf
│   └── ...
├── extracted_policies_all/      # Extracted policy documents
│   ├── policies/               # Policy documents
│   ├── regulations/            # Administrative regulations
│   └── exhibits/               # Exhibits and forms
├── pdf_parser.py               # PDF extraction engine
├── extract_all_policies.py     # Batch extraction script
├── check_cross_references.py   # Cross-reference validation
└── README.md                   # This file
```

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

## Contributing

This project is primarily for analysis purposes. If you notice extraction errors or have suggestions for the compliance analysis features, please open an issue.

## License

This project is for educational and analysis purposes only. The policies themselves remain the property of the Redwood City School District.