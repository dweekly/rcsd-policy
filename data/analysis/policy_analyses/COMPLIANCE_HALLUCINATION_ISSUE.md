# Compliance Checker Hallucination Issue

## Problem Identified

The compliance checker is generating false legal citations and requirements. Example:

**BP 1221.4 - Citizens' Bond Oversight Committees**
- AI claimed: "Education Code Section 15278(b) requires that committee members serve two-year terms"
- Reality: Ed Code 15278(b) discusses the committee's PURPOSE, not term lengths
- Actual requirement: Ed Code 15282 specifies "minimum term of two years" and "no more than three consecutive terms"

## Root Causes

1. **LLM Hallucination**: The AI model is generating plausible-sounding but incorrect legal citations
2. **No Verification**: The system doesn't verify citations against actual statutes
3. **Imprecise Prompting**: The prompt asks for compliance issues without requiring verified citations

## Proposed Solutions

### 1. Short-term: Add Citation Verification Warning

Update the compliance checker prompt to:
- Explicitly state when citing specific code sections
- Flag uncertainty about exact citations
- Distinguish between "general requirement" vs "specific statutory citation"

### 2. Medium-term: Legal Requirements Database

Create a verified database of actual CA Education Code requirements:
```json
{
  "15282": {
    "title": "Citizens' Oversight Committee Members",
    "requirements": [
      {
        "id": "term_length",
        "text": "shall serve for a minimum term of two years",
        "exact_quote": true
      },
      {
        "id": "term_limit", 
        "text": "for no more than three consecutive terms",
        "exact_quote": true
      }
    ]
  }
}
```

### 3. Long-term: Statute Verification System

- Integrate with CA Legislative Information API (if available)
- Web scraping of leginfo.legislature.ca.gov for verification
- Human review and validation of all material findings

## Impact Assessment

This issue affects the reliability of ALL compliance findings. We should:

1. **Re-review all high-confidence findings** - especially those citing specific code sections
2. **Add disclaimers** to all compliance reports about potential citation errors
3. **Prioritize human verification** of any findings before board action

## Immediate Action Items

1. Add warning to EXECUTIVE_SUMMARY.md about potential citation errors
2. Create a list of findings that cite specific Ed Code sections for manual verification
3. Update compliance checker v3 with better prompting to reduce hallucination

## Example of Corrected Finding

**Original (Incorrect)**:
```
Education Code Section 15278(b) requires that committee members serve two-year terms.
```

**Corrected**:
```
Education Code Section 15282 requires that committee members serve for a minimum 
term of two years and for no more than three consecutive terms. The AR mentions 
"two (2) or three (3) -year term" which is ambiguous and should be clarified to 
match the statutory requirement.
```