# Compliance Verification Proposal

## Current Status

We've created a v3 compliance checker that attempts to verify Ed Code citations before making recommendations. However, programmatic web scraping of the CA Legislative website is proving unreliable.

## Problems Identified

1. **V1/V2 Issues**: AI hallucinates legal requirements (e.g., citing Ed Code 15278(b) for term requirements that don't exist there)
2. **V3 Issue**: Web scraping the leginfo.legislature.ca.gov site is technically challenging and unreliable

## Proposed Solutions

### Option 1: Curated Legal Database (Recommended)

Create a manually verified database of actual California Education Code requirements:

```json
{
  "15282": {
    "title": "Citizens' Oversight Committee - Members",
    "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=15282.&lawCode=EDC",
    "last_verified": "2025-06-01",
    "requirements": {
      "composition": {
        "minimum_members": 7,
        "required_categories": [
          "One active in business organization",
          "One active in senior citizens' organization", 
          "One active in taxpayers' organization",
          "One parent/guardian (for school district)",
          "One student (for community college)"
        ]
      },
      "terms": {
        "minimum_term": "2 years",
        "maximum_consecutive_terms": 3,
        "exact_text": "shall serve for a minimum term of two years without compensation and for no more than three consecutive terms"
      },
      "prohibitions": [
        "No district employees or officials",
        "No vendors, contractors, or consultants"
      ]
    }
  }
}
```

### Option 2: Semi-Automated Verification

1. First pass: AI identifies potential issues and guesses Ed Code sections
2. Human review: Manually verify each Ed Code citation using the website
3. Second pass: AI uses verified citations to generate final compliance report

### Option 3: API Integration

Research if California provides an official API for accessing Education Code. Some states offer legislative data APIs.

### Option 4: Pre-Verified Prompts

Instead of real-time verification, use prompts that include verified Ed Code excerpts for common compliance areas:

```python
VERIFIED_ED_CODES = {
    "bond_oversight": {
        "15282": """(a) The citizens' oversight committee shall consist of at least seven members 
        who shall serve for a minimum term of two years without compensation and for no more 
        than three consecutive terms..."""
    }
}
```

## Immediate Recommendations

1. **Stop using v1/v2 results** - They contain hallucinated legal requirements
2. **For critical compliance work**: Manually verify all Ed Code citations
3. **Build a small verified database** for the most common compliance areas
4. **Add disclaimers** to all AI-generated compliance reports

## Example: BP 1221.4 Corrected Finding

**What v2 Said (INCORRECT)**:
"Education Code Section 15278(b) requires that committee members serve two-year terms"

**What v3 Found (CORRECT)**:
"Could not verify Ed Code requirements - no compliance issues confirmed"

**What Manual Verification Shows**:
- Ed Code 15282 (not 15278) specifies: "minimum term of two years" and "no more than three consecutive terms"
- The AR's language "two (2) or three (3) -year term" is ambiguous and should be clarified

## Next Steps

1. Create a pilot verified database for 10-20 common Ed Code sections
2. Test the compliance checker using this verified database
3. Gradually expand the database based on district needs
4. Consider hiring legal intern to verify all Ed Code citations used in policies