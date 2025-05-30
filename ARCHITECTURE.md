# RCSD Policy Compliance Analyzer - Architecture & Plan

## Current Architecture

### Overview

The system extracts RCSD policies from PDF documents, validates cross-references, and prepares for compliance analysis against California Education Code.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PDF Files     │────▶│   PDF Parser     │────▶│ Extracted Docs  │
│ (By Series)     │     │  (PyMuPDF/fitz)  │     │ (Text Files)    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                        ┌──────────────────┐               │
                        │ Cross-Reference  │◀──────────────┘
                        │   Validator      │
                        └────────┬─────────┘
                                │
                        ┌───────▼─────────┐
                        │   Compliance    │ (Planned)
                        │    Analyzer     │
                        └─────────────────┘
```

### Implemented Components

1. **PDF Parser (`pdf_parser.py`)**
   - Uses PyMuPDF (fitz) for robust PDF text extraction
   - Parses table of contents to identify document boundaries
   - Handles multi-line TOC entries (critical for documents like 4319.12)
   - Extracts metadata: dates, status, references
   - Outputs structured text files with consistent formatting

2. **Batch Extractor (`extract_all_policies.py`)**
   - Processes all PDF files by series (0000-7000, 9000)
   - Merges extractions while preventing overwrites
   - Generates summary statistics
   - Creates organized directory structure

3. **Cross-Reference Validator (`check_cross_references.py`)**
   - Parses all extracted documents for cross-references
   - Identifies missing referenced policies
   - Reports gaps in policy numbering
   - Validates extraction completeness

### Data Model

Each extracted document contains:
```
- Header
  - Document type (Policy/Regulation/Exhibit/Bylaw)
  - Code (e.g., 3550)
  - Title
  - Status (ADOPTED/etc.)
  - Original adoption date
  - Last reviewed date
  - Source PDF and page numbers
  
- Content
  - Main policy text
  
- References
  - State references (CA codes)
  - Federal references (USC)
  - Management resources
  - Cross-references to other policies
```

## Planned Architecture

### Phase 1: Compliance Analysis Engine (Next Step)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Extracted Docs  │────▶│ Compliance Rules │────▶│ Analysis Report │
│                 │     │   - Ed Code      │     │   - Material    │
│                 │     │   - CSBA         │     │   - Minor       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Components to Build:**

1. **Ed Code Database**
   - Comprehensive mapping of Ed Code requirements
   - Version tracking for legislative changes
   - Requirement categorization (mandatory/recommended)

2. **Compliance Rule Engine**
   - Pattern matching for required language
   - Date validation for outdated references
   - Cross-reference to Ed Code sections
   - CSBA best practice alignment

3. **Material Issue Detector**
   - Missing mandatory provisions
   - Outdated legal references (pre-2020)
   - Conflicts with current law
   - Missing required procedures
   - Discriminatory language detection

### Phase 2: Enhanced Analysis with AI

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Policy Content  │────▶│   LLM Analysis   │────▶│ Semantic Issues │
│                 │     │  - GPT-4/Claude  │     │ - Ambiguity     │
│                 │     │  - Fine-tuned    │     │ - Conflicts     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Enhancements:**
- Semantic analysis beyond keyword matching
- Policy coherence checking
- Conflict detection between policies
- Plain language assessment
- Accessibility evaluation

### Phase 3: Continuous Monitoring

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Official Site   │────▶│  Change Monitor  │────▶│  Update Alerts  │
│ (eboardsolutions)│     │  - Scheduled    │     │  - Diffs        │
│                 │     │  - API/Scraping │     │  - Analysis     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Technical Stack

### Current
- **Language**: Python 3.8+
- **PDF Processing**: PyMuPDF (fitz)
- **Data Format**: Plain text files with structured headers
- **Analysis**: Pattern matching, regex

### Planned Additions
- **Database**: SQLite for Ed Code requirements
- **AI/ML**: OpenAI API or local LLM for semantic analysis
- **Web Framework**: FastAPI for dashboard/API
- **Frontend**: React dashboard for compliance monitoring
- **Deployment**: Docker containers

## Data Flow

1. **Extraction Phase**
   ```
   PDFs → TOC Parsing → Document Boundaries → Text Extraction → Structured Files
   ```

2. **Validation Phase**
   ```
   Extracted Docs → Reference Parsing → Cross-Reference Check → Missing Policies Report
   ```

3. **Analysis Phase** (Planned)
   ```
   Extracted Docs → Rule Application → Issue Detection → Severity Classification → Report
   ```

## Key Design Decisions

### 1. PDF Table of Contents Parsing
- **Why**: Accurate document boundary detection
- **Alternative Considered**: Page-based heuristics
- **Decision**: TOC provides authoritative boundaries

### 2. Plain Text Storage
- **Why**: Universal compatibility, version control friendly
- **Alternative Considered**: Database storage
- **Decision**: Text files with structured headers for simplicity

### 3. Multi-Line TOC Handling
- **Why**: Some entries (like 4319.12) span multiple lines
- **Alternative Considered**: Single-line assumption
- **Decision**: Lookahead parsing for complete titles

### 4. Cross-Reference Validation
- **Why**: Ensure extraction completeness
- **Alternative Considered**: Trust extraction blindly
- **Decision**: Active validation identifies missing documents

## Challenges & Solutions

### 1. **TOC Format Variations**
- **Challenge**: Different series use different terms (Policy/Bylaw)
- **Solution**: Flexible regex patterns, series-specific handling

### 2. **Document Boundary Detection**
- **Challenge**: Determining where one policy ends and another begins
- **Solution**: TOC-based detection with page number mapping

### 3. **Reference Extraction**
- **Challenge**: Various reference formats and structures
- **Solution**: Section-based parsing with multiple patterns

### 4. **Scale**
- **Challenge**: 500+ documents across 9 PDF files
- **Solution**: Batch processing with merge strategy

## Future Considerations

### 1. **API Integration**
- Direct integration with eboardsolutions if API becomes available
- Eliminate PDF parsing step
- Real-time updates

### 2. **Multi-District Support**
- Generalize parser for other CA districts
- Build shared Ed Code compliance database
- Economies of scale

### 3. **Legal Update Service**
- Subscribe to legislative tracking services
- Automated Ed Code update integration
- Proactive compliance alerts

### 4. **Human Review Interface**
- Web dashboard for compliance officers
- Annotation and approval workflow
- Historical tracking

## Security & Privacy

- No PII in policies (public documents)
- Clear disclaimers about unofficial status
- No authentication required for public data
- PDF files stored locally with Git LFS for version control

## Performance Metrics

### Current Performance
- Extraction: ~5 minutes for 512 documents
- Cross-reference validation: <1 minute
- Storage: ~15MB extracted text

### Target Performance
- Compliance analysis: <10 minutes full scan
- Incremental updates: <1 minute
- Dashboard response: <100ms

## Conclusion

The current architecture successfully extracts and validates RCSD policies from PDFs. The modular design allows for incremental enhancement toward a comprehensive compliance monitoring system. Next steps focus on building the compliance analysis engine with Ed Code mapping and material issue detection.