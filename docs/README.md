# Documentation Directory
## Technical Documentation for RCSD Policy Compliance Analyzer

This directory contains technical documentation about the source code, architecture, and processes used in the RCSD Policy Compliance Analyzer. 

**For analysis results and findings, see the `/reports/` directory.**

## Contents

### `AGENTS.md`
Guidelines for AI assistants working with this repository. Includes:
- Project history and evolution
- Key technical decisions
- Common pitfalls to avoid
- Git workflow best practices
- Current state and next steps

### `ARCHITECTURE.md`
System design and technical architecture documentation:
- Component overview
- Data flow diagrams
- Technology stack
- Lessons learned from validation phase

### `COMPLIANCE_PLAN.md`
Original planning document for the compliance checking implementation:
- Requirements analysis
- Proposed approach
- Technical specifications
- (Historical document - see COMPLIANCE_USAGE.md for current usage)

### `COMPLIANCE_USAGE.md`
How to use the compliance checking tools:
- Installation and setup
- Running compliance checks
- Understanding output formats
- **Important warnings about AI hallucination rates**

### `COMPLIANCE_CHECKER_V2.md`
Technical documentation for the V2 compliance checker:
- Improvements over V1
- How it groups BP/AR documents
- Implementation details

## Key Technical Concepts

1. **PDF Extraction**: Using PyMuPDF to extract policies from district PDFs
2. **Compliance Analysis**: Using Claude AI to analyze policies against Ed Code
3. **Validation**: Fetching actual Ed Code text to verify AI findings
4. **Caching**: Storing API responses to avoid redundant calls

## For Developers

When working on this project:
1. Read `AGENTS.md` first for context and best practices
2. Review `ARCHITECTURE.md` to understand system design
3. Follow `COMPLIANCE_USAGE.md` for running the tools
4. Always update documentation when making significant changes

## Important Discovery

The validation phase revealed that AI compliance checkers have a **73% hallucination rate** when analyzing legal requirements. This is documented in detail in `/reports/validation/`. Always verify AI findings against actual legal text.