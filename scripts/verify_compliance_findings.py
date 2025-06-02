#!/usr/bin/env python3
"""
Verify compliance findings against actual Ed Code text
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone


class ComplianceFindingVerifier:
    """Verifies compliance findings against actual Ed Code text"""
    
    def __init__(self, cache_dir="data/cache/edcode", analysis_dir="data/analysis"):
        self.cache_dir = Path(cache_dir)
        self.analysis_dir = Path(analysis_dir)
    
    def load_ed_code(self, section: str) -> dict:
        """Load Ed Code section from cache"""
        # Try full version first
        cache_file = self.cache_dir / f"edc_{section.replace('.', '_')}_full.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        
        # Fall back to partial version
        cache_file = self.cache_dir / f"edc_{section.replace('.', '_')}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        
        return None
    
    def verify_policy_findings(self, policy_code: str, compliance_version: str = "compliance_v2"):
        """Verify findings for a specific policy"""
        # Load compliance findings
        json_file = self.analysis_dir / compliance_version / "json_data" / f"{policy_code}.json"
        if not json_file.exists():
            print(f"No compliance findings found for {policy_code}")
            return
        
        with open(json_file) as f:
            data = json.load(f)
        
        print(f"\n{'='*80}")
        print(f"Verifying: {policy_code} - {data.get('policy', {}).get('title', 'Unknown')}")
        print(f"{'='*80}\n")
        
        # Check each material issue
        compliance = data.get("compliance", {})
        material_issues = [
            issue for issue in compliance.get("issues", [])
            if issue.get("priority") == "MATERIAL"
        ]
        
        if not material_issues:
            print("No material issues found.")
            return
        
        for i, issue in enumerate(material_issues, 1):
            print(f"Issue {i}: {issue.get('title', 'Untitled')}")
            print(f"Confidence: {issue.get('confidence', 0)}%")
            print(f"Missing from: {issue.get('missing_from', 'Unknown')}")
            print()
            
            # Check each legal citation
            for citation in issue.get("legal_citations", []):
                cite_num = citation.get("citation", "")
                cite_text = citation.get("text", "")
                
                # Extract Ed Code section number
                section_match = re.search(r'(\d{4,5}(?:\.\d+)?)', cite_num)
                if not section_match:
                    print(f"  ⚠️ Could not extract section number from: {cite_num}")
                    continue
                
                section = section_match.group(1)
                print(f"  Cited: Education Code Section {section}")
                print(f"  Claim: {cite_text[:100]}...")
                
                # Load actual Ed Code
                ed_code = self.load_ed_code(section)
                if not ed_code:
                    print(f"  ❌ UNVERIFIED - Ed Code {section} not in cache")
                elif not ed_code.get("content") or ed_code["content"] == f"{section}.":
                    print(f"  ❌ UNVERIFIED - No content available for Ed Code {section}")
                else:
                    # Check if the claimed requirement exists in actual code
                    actual_content = ed_code["content"].lower()
                    
                    # Extract key phrases from the claim
                    key_phrases = self.extract_key_phrases(cite_text)
                    
                    matches = []
                    for phrase in key_phrases:
                        if phrase.lower() in actual_content:
                            matches.append(phrase)
                    
                    if matches:
                        print(f"  ✓ PARTIALLY VERIFIED - Found references to: {', '.join(matches)}")
                    else:
                        print(f"  ❌ NOT VERIFIED - Could not find claimed requirement in Ed Code {section}")
                    
                    # Show relevant excerpt
                    if "two year" in cite_text.lower() or "term" in cite_text.lower():
                        # Look for term-related content
                        term_match = re.search(
                            r'(?:term|serve).*?(?:year|consecutive)',
                            ed_code["content"],
                            re.IGNORECASE | re.DOTALL
                        )
                        if term_match:
                            print(f"  Actual text: \"{term_match.group(0).strip()}\"")
                
                print()
            
            print("-" * 40)
            print()
    
    def extract_key_phrases(self, text: str) -> list:
        """Extract key phrases from compliance claim"""
        # Common compliance phrases to look for
        phrases = []
        
        # Look for specific requirements
        patterns = [
            r'(two.?year(?:s)?)',
            r'(three consecutive terms?)',
            r'(annual(?:ly)?)',
            r'(shall\s+\w+)',
            r'(must\s+\w+)',
            r'(require[sd]?\s+(?:to\s+)?\w+)',
            r'(at least \w+)',
            r'(within \d+ days?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            phrases.extend(matches)
        
        return phrases
    
    def generate_verification_report(self, policy_codes: list, compliance_version: str = "compliance_v2"):
        """Generate a comprehensive verification report"""
        report_file = self.analysis_dir / "compliance_verification_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Compliance Finding Verification Report\n\n")
            f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
            f.write(f"Compliance Version: {compliance_version}\n\n")
            
            verified_count = 0
            unverified_count = 0
            total_findings = 0
            
            for code in policy_codes:
                # This would need to be implemented to collect verification stats
                pass
            
            f.write(f"## Summary\n\n")
            f.write(f"- Total material findings reviewed: {total_findings}\n")
            f.write(f"- Verified against Ed Code: {verified_count}\n")
            f.write(f"- Could not verify: {unverified_count}\n\n")
            
            # Add detailed findings here
            
        print(f"\nReport saved to: {report_file}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify compliance findings against actual Ed Code text"
    )
    parser.add_argument(
        "--policy",
        required=True,
        help="Policy code to verify (e.g., 1221.4)"
    )
    parser.add_argument(
        "--version",
        default="compliance_v2",
        help="Compliance version to verify (default: compliance_v2)"
    )
    
    args = parser.parse_args()
    
    verifier = ComplianceFindingVerifier()
    verifier.verify_policy_findings(args.policy, args.version)


if __name__ == "__main__":
    main()