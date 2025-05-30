# RCSD Policy Compliance Analyzer

This tool processes PDF documents containing Redwood City School District policies and analyzes them for compliance with California Education Code and CSBA best practices.

## Features

- **PDF Processing**: Extracts policies from PDF documents by policy number
- **Policy Research**: Analyzes each policy for legal references and compliance areas
- **Compliance Analysis**: Checks policies against CA Ed Code requirements
- **CSBA Alignment**: Evaluates alignment with CSBA best practices
- **Material Non-Compliance Detection**: Flags only significant compliance issues
- **Comprehensive Reporting**: Generates JSON and Excel reports

## Installation

1. Install Python 3.8 or higher
2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements-pdf.txt
```

## Usage

### Full Analysis (Parse + Research + Analyze)
```bash
python main_pdf.py --full
```

### Parse PDFs Only
```bash
python main_pdf.py --parse --pdf-dir policies/
```

### Research Policies Only (using existing parsed data)
```bash
python main_pdf.py --research
```

### Analyze Compliance Only (using existing parsed data)
```bash
python main_pdf.py --analyze
```

## Output Files

- `extracted_policies.json` - All extracted policies with content and metadata
- `policy_chunks/` - Individual text files for each policy
- `policy_research.json` - Research findings for each policy
- `research_summary.xlsx` - Excel summary of research findings
- `compliance_report.json` - Detailed compliance analysis
- `material_noncompliance_summary.xlsx` - Summary of material issues only

## Compliance Criteria

### Material Non-Compliance Indicators:
- Missing required legal provisions
- Outdated legal references (pre-2020)
- Conflicts with current Ed Code
- Missing mandated procedures
- Discriminatory language
- Lack of due process protections
- Missing required notifications
- Absence of required timelines

### Key Ed Code Areas Checked:
- Student attendance (46000-46394)
- Discipline procedures (48900-48927)
- Anti-bullying provisions (234-234.5)
- Special education (56000-56865)
- Employment requirements (44830-44986)
- Board governance (35000-35179)
- Fiscal management (41000-42650)
- Health and safety (32280-32289)

## Notes

- The scraper uses Selenium to handle JavaScript-rendered content
- Rate limiting is implemented to be respectful of the website
- Only material compliance issues are flagged to focus on significant problems
- The tool provides conservative analysis - when in doubt, it may not flag borderline issues