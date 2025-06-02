#!/usr/bin/env python3
"""
Verify all v2 compliance findings against available Ed Code sections
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone


class ComprehensiveVerifier:
    def __init__(self):
        self.cache_dir = Path("data/cache/edcode")
        self.analysis_dir = Path("data/analysis/compliance_v2")
        self.ed_code_cache = {}
        self.load_ed_code_cache()
    
    def load_ed_code_cache(self):
        """Load all cached Ed Code sections"""
        if not self.cache_dir.exists():
            return
        
        for cache_file in self.cache_dir.glob("*_full.json"):
            with open(cache_file) as f:
                data = json.load(f)
                section = data["section"]
                self.ed_code_cache[section] = data
        
        print(f"Loaded {len(self.ed_code_cache)} Ed Code sections from cache")
    
    def extract_key_claims(self, text):
        """Extract key compliance claims from text"""
        claims = []
        
        # Common patterns for requirements
        patterns = [
            r'(shall\s+[\w\s]+)',
            r'(must\s+[\w\s]+)',
            r'(require[sd]?\s+[\w\s]+)',
            r'(at least\s+[\w\s]+)',
            r'(minimum\s+[\w\s]+)',
            r'(within\s+\d+\s+days?)',
            r'(annual\w*\s+[\w\s]+)',
            r'(two[- ]year\s+term)',
            r'(consecutive\s+terms?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            claims.extend([m.strip() for m in matches])
        
        return claims
    
    def verify_citation(self, section, claim_text):
        """Verify if a claim exists in the Ed Code section"""
        if section not in self.ed_code_cache:
            return "NOT_CACHED", None
        
        ed_code = self.ed_code_cache[section]
        content = ed_code.get("content", "").lower()
        
        # Extract key phrases from claim
        key_claims = self.extract_key_claims(claim_text)
        
        # Check if any key claims appear in actual Ed Code
        found_claims = []
        for claim in key_claims:
            if claim in content:
                found_claims.append(claim)
        
        if found_claims:
            return "PARTIALLY_VERIFIED", found_claims
        else:
            # Check if the section number is even mentioned correctly
            if section in claim_text:
                return "SECTION_CITED_BUT_NOT_VERIFIED", None
            else:
                return "NOT_VERIFIED", None
    
    def analyze_all_findings(self):
        """Analyze all v2 compliance findings"""
        json_dir = self.analysis_dir / "json_data"
        
        if not json_dir.exists():
            print("No v2 compliance findings found")
            return
        
        # Statistics
        total_policies = 0
        total_material_issues = 0
        verified_issues = 0
        unverified_issues = 0
        not_cached_issues = 0
        problematic_findings = []
        
        # Process each policy
        for json_file in sorted(json_dir.glob("*.json")):
            total_policies += 1
            
            with open(json_file) as f:
                data = json.load(f)
            
            policy_code = data["code"]
            has_policy = data.get("has_policy", False)
            has_regulation = data.get("has_regulation", False)
            
            # Get title
            title = "Unknown"
            if data.get("policy"):
                title = data["policy"].get("title", title)
            elif data.get("regulation"):
                title = data["regulation"].get("title", title)
            
            # Check material issues
            compliance = data.get("compliance", {})
            policy_issues = []
            
            for issue in compliance.get("issues", []):
                if issue.get("priority") != "MATERIAL":
                    continue
                
                if issue.get("missing_from") != "BOTH":
                    continue
                
                total_material_issues += 1
                
                # Check each legal citation
                issue_verified = False
                issue_problems = []
                
                for citation in issue.get("legal_citations", []):
                    cite_num = citation.get("citation", "")
                    cite_text = citation.get("text", "")
                    
                    # Extract section number
                    section_match = re.search(r'(\d{4,5}(?:\.\d+)?)', cite_num)
                    if not section_match:
                        continue
                    
                    section = section_match.group(1)
                    status, found_claims = self.verify_citation(section, cite_text)
                    
                    if status == "NOT_CACHED":
                        not_cached_issues += 1
                        issue_problems.append({
                            "section": section,
                            "status": "NOT_CACHED",
                            "claim": cite_text[:100]
                        })
                    elif status in ["NOT_VERIFIED", "SECTION_CITED_BUT_NOT_VERIFIED"]:
                        unverified_issues += 1
                        issue_verified = False
                        issue_problems.append({
                            "section": section,
                            "status": status,
                            "claim": cite_text[:100]
                        })
                    else:
                        verified_issues += 1
                        issue_verified = True
                
                # Track problematic findings
                if issue_problems:
                    policy_issues.append({
                        "title": issue.get("title", "Unknown"),
                        "problems": issue_problems
                    })
            
            if policy_issues:
                problematic_findings.append({
                    "code": policy_code,
                    "title": title,
                    "type": "BP" if has_policy else "AR",
                    "issues": policy_issues
                })
        
        # Generate report
        self.generate_verification_report(
            total_policies, total_material_issues, verified_issues,
            unverified_issues, not_cached_issues, problematic_findings
        )
    
    def generate_verification_report(self, total_policies, total_issues, 
                                   verified, unverified, not_cached, problematic):
        """Generate comprehensive verification report"""
        
        report_file = self.analysis_dir.parent / "compliance_v2_verification_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Compliance V2 Verification Report\n\n")
            f.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n")
            
            f.write("## Summary Statistics\n\n")
            f.write(f"- Total policy groups analyzed: {total_policies}\n")
            f.write(f"- Total material issues (missing from BOTH BP and AR): {total_issues}\n")
            f.write(f"- Legal citations verified: {verified}\n")
            f.write(f"- Legal citations NOT verified: {unverified}\n")
            f.write(f"- Legal citations not in cache: {not_cached}\n")
            f.write(f"- Policy groups with problematic findings: {len(problematic)}\n\n")
            
            if problematic:
                f.write("## Problematic Findings Requiring Review\n\n")
                
                # Sort by number of problems
                problematic.sort(key=lambda x: sum(len(i["problems"]) for i in x["issues"]), reverse=True)
                
                for finding in problematic[:20]:  # Top 20
                    f.write(f"### {finding['type']} {finding['code']} - {finding['title']}\n\n")
                    
                    for issue in finding["issues"]:
                        f.write(f"**Issue:** {issue['title']}\n\n")
                        
                        for problem in issue["problems"]:
                            f.write(f"- Ed Code {problem['section']}: ")
                            if problem["status"] == "NOT_CACHED":
                                f.write("NOT IN CACHE - Cannot verify\n")
                            else:
                                f.write(f"{problem['status']}\n")
                            f.write(f"  Claim: \"{problem['claim']}...\"\n")
                        f.write("\n")
                    
                    f.write("---\n\n")
            
            # Summary of Ed Code coverage
            f.write("## Ed Code Cache Coverage\n\n")
            f.write(f"Currently cached sections: {', '.join(sorted(self.ed_code_cache.keys()))}\n\n")
            
            f.write("## Recommendations\n\n")
            f.write("1. **Immediate Action:** Review all findings with NOT_VERIFIED status\n")
            f.write("2. **High Priority:** Fetch Ed Code sections that are NOT_CACHED\n")
            f.write("3. **Systematic Review:** Manually verify problematic findings before board action\n")
            f.write("4. **Process Improvement:** Add Ed Code verification to compliance checking workflow\n")
        
        print(f"\nVerification report saved to: {report_file}")
        
        # Also save JSON summary
        json_file = self.analysis_dir.parent / "compliance_v2_verification_data.json"
        with open(json_file, 'w') as f:
            json.dump({
                "generated": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_policies": total_policies,
                    "total_issues": total_issues,
                    "verified": verified,
                    "unverified": unverified,
                    "not_cached": not_cached
                },
                "problematic_findings": problematic[:50],  # Top 50
                "cached_sections": list(self.ed_code_cache.keys())
            }, f, indent=2)


def main():
    verifier = ComprehensiveVerifier()
    verifier.analyze_all_findings()


if __name__ == "__main__":
    main()