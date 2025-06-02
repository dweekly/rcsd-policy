#!/usr/bin/env python3
"""
Analyze citation accuracy based on known Ed Code content
"""

import json
from pathlib import Path


# Known Ed Code content summaries
KNOWN_ED_CODES = {
    "15278": {
        "title": "Citizens' Oversight Committee - Establishment and Purpose",
        "key_requirements": [
            "Establish committee within 60 days of election results",
            "Committee purpose: inform public about bond expenditures",
            "Review and report on taxpayer money spending",
            "Ensure bond revenues used only for approved purposes"
        ],
        "does_NOT_contain": [
            "Term length requirements",
            "Number of consecutive terms",
            "Committee composition requirements"
        ]
    },
    "15280": {
        "title": "Citizens' Oversight Committee - Support and Proceedings",
        "key_requirements": [
            "District must provide technical/administrative assistance",
            "Proceedings must be open to public",
            "Must issue regular reports, at least annually",
            "Documents must be publicly available on website"
        ],
        "does_NOT_contain": [
            "Specific publication deadlines beyond 'annually'"
        ]
    },
    "15282": {
        "title": "Citizens' Oversight Committee - Membership",
        "key_requirements": [
            "Minimum 7 members",
            "Minimum term of two years",
            "No more than three consecutive terms",
            "Specific membership categories (business, senior, taxpayer, parent)",
            "No district employees, vendors, or contractors"
        ],
        "does_NOT_contain": [
            "Maximum term length (only minimum specified)"
        ]
    },
    "35160": {
        "title": "Powers of Governing Boards",
        "key_requirements": [
            "Board may initiate any program/activity not in conflict with law",
            "Actions must not conflict with purposes of school districts"
        ],
        "does_NOT_contain": [
            "Specific program requirements",
            "Mandatory actions"
        ]
    }
}


def analyze_citations():
    """Analyze citation accuracy"""
    
    # Load citation summary
    with open("data/analysis/ed_code_citations_summary.json") as f:
        data = json.load(f)
    
    print("CITATION ACCURACY ANALYSIS")
    print("="*80)
    print()
    
    # Check for known problematic citations
    problematic_policies = []
    
    for policy_code, policy_data in data["by_policy"].items():
        citations = policy_data["citations"]
        
        # Check for 15278 being used for terms
        if "15278" in citations:
            # Load the actual compliance finding to check context
            json_file = Path(f"data/analysis/compliance_v2/json_data/{policy_code}.json")
            if json_file.exists():
                with open(json_file) as f:
                    compliance_data = json.load(f)
                
                # Check if 15278 is cited for term requirements
                for issue in compliance_data.get("compliance", {}).get("issues", []):
                    if issue.get("priority") != "MATERIAL":
                        continue
                    
                    for legal_cite in issue.get("legal_citations", []):
                        if "15278" in legal_cite.get("citation", ""):
                            cite_text = legal_cite.get("text", "").lower()
                            if any(term in cite_text for term in ["term", "year", "consecutive"]):
                                problematic_policies.append({
                                    "policy": policy_code,
                                    "title": policy_data["title"],
                                    "issue": "Cites 15278 for term requirements (should be 15282)",
                                    "citation_text": legal_cite.get("text", "")[:100] + "..."
                                })
    
    # Print findings
    if problematic_policies:
        print("PROBLEMATIC CITATIONS FOUND:")
        print("-"*80)
        for prob in problematic_policies:
            print(f"\nPolicy: {prob['policy']} - {prob['title']}")
            print(f"Issue: {prob['issue']}")
            print(f"Citation: {prob['citation_text']}")
    
    # Summary of citation patterns
    print("\n\nCITATION PATTERNS:")
    print("-"*80)
    
    # Most cited sections
    print("\nMost Frequently Cited Ed Code Sections:")
    for section, count in data["most_cited"][:10]:
        section_info = KNOWN_ED_CODES.get(section, {})
        if section_info:
            print(f"\n{section} ({count} citations) - {section_info['title']}")
            print(f"  Key requirements: {', '.join(section_info['key_requirements'][:2])}...")
        else:
            print(f"\n{section} ({count} citations) - [Content not verified]")
    
    # Recommendations
    print("\n\nRECOMMENDATIONS:")
    print("-"*80)
    print("\n1. IMMEDIATE ACTIONS:")
    print("   - Review all findings citing Ed Code 15278 for accuracy")
    print("   - Verify term requirements should reference 15282, not 15278")
    print("   - Note that 15282 specifies MINIMUM term of 2 years (not exact)")
    
    print("\n2. HIGH PRIORITY VERIFICATIONS:")
    print("   - Section 35160 (51 citations) - Board powers")
    print("   - Section 44050 (20 citations) - [Needs verification]")
    print("   - Section 35160.5 (13 citations) - [Needs verification]")
    
    print("\n3. SYSTEM IMPROVEMENTS:")
    print("   - Build comprehensive Ed Code database before next compliance run")
    print("   - Add automatic citation verification to compliance checker")
    print("   - Flag when citing general authority (35160) vs specific requirements")
    
    # Save detailed report
    report = {
        "problematic_citations": problematic_policies,
        "citation_frequency": data["most_cited"][:50],
        "known_ed_codes": KNOWN_ED_CODES,
        "recommendations": [
            "Review all 15278 citations for accuracy",
            "Build comprehensive Ed Code database",
            "Add citation verification to compliance process"
        ]
    }
    
    output_file = Path("data/analysis/citation_accuracy_report.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n\nDetailed report saved to: {output_file}")


if __name__ == "__main__":
    analyze_citations()