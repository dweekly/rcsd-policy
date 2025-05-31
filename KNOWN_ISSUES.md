# Known Issues

## Parser Bugs

### 1. Policy/Regulation 6164.6 Extraction Failure
- **Issue**: Policy and Regulation 6164.6 are extracted with truncated titles and no content
- **Expected**: "Identification And Education Under Section 504" with full policy text
- **Actual**: "Identification And Education Under Section" with empty content
- **Verified**: Content exists in source PDF (Policy on page 231 of 6000.pdf)
- **Impact**: Makes these policies appear empty when they actually have content
- **Root Cause**: Likely an issue with document boundary detection or title parsing in the TOC

### 2. Empty Policies (15 documents)
- **Issue**: 15 policies/regulations contain only disclaimer text and legal references
- **Examples**: Policy 4119.11 (Sex Discrimination), Policy 5131.9 (Academic Honesty)
- **Note**: This appears to be how these were actually created, not a parser bug
- **Impact**: Significant compliance risk as these acknowledge legal requirements without providing policy guidance

## Compliance Checking Issues

### 1. Policy/Regulation Awareness
- **Initial Issue**: System was flagging missing requirements that were actually in administrative regulations
- **Solution**: Created `compliance_check_policy_regulation.py` that checks both documents
- **Example**: Foster Youth policy appeared non-compliant but regulation had all requirements

### 2. Cross-Reference Extraction
- **Issue**: Cross-references embedded in policy text aren't always extracted
- **Impact**: Related policies might not be identified for context
- **Workaround**: System uses both explicit cross-references and numbering patterns