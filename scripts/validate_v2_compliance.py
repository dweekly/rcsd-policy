#!/usr/bin/env python3
"""
Validate v2 compliance findings against cached Ed Code sections
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone


def clean_json_content(content):
    """Clean JSON content that might have control characters"""
    # Replace common control characters that cause issues
    content = content.replace('\n', '\\n')
    content = content.replace('\r', '\\r')
    content = content.replace('\t', '\\t')
    return content


def load_ed_code_cache():
    """Load all cached Ed Code sections"""
    cache_dir = Path("data/cache/edcode")
    ed_code_cache = {}
    errors = []
    
    if not cache_dir.exists():
        return ed_code_cache, errors
    
    for cache_file in cache_dir.glob("*_full.json"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Try to parse as-is first
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # Clean and retry
                    content = clean_json_content(content)
                    data = json.loads(content)
                
                section = data["section"]
                law_code = data.get("law_code", "EDC")
                key = f"{law_code}_{section}"
                ed_code_cache[key] = data
                ed_code_cache[section] = data
        except Exception as e:
            errors.append(f"{cache_file.name}: {str(e)}")
    
    return ed_code_cache, errors


def load_v2_compliance_findings():
    """Load all v2 compliance findings"""
    v2_dir = Path("data/analysis/compliance_v2/json_data")
    findings = []
    
    if not v2_dir.exists():
        print(f"Directory not found: {v2_dir}")
        return findings
    
    for json_file in sorted(v2_dir.glob("*.json")):
        try:
            with open(json_file) as f:
                data = json.load(f)
                
                # Extract material issues from the compliance section
                if "compliance" in data and "issues" in data["compliance"]:
                    material_issues = []
                    
                    for issue in data["compliance"]["issues"]:
                        if issue.get("priority") == "MATERIAL":
                            material_issues.append(issue)
                    
                    if material_issues:
                        findings.append({
                            "code": data["code"],
                            "has_policy": data.get("has_policy", False),
                            "has_regulation": data.get("has_regulation", False),
                            "policy_title": data["policy"]["title"] if data.get("policy") else "No Policy",
                            "material_issues": material_issues,
                            "file": json_file.name
                        })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return findings


def extract_citations_from_issue(issue):
    """Extract legal citations from an issue"""
    citations = []
    
    # Direct legal citations in the structure
    if "legal_citations" in issue:
        for citation in issue["legal_citations"]:
            citation_text = citation.get("citation", "")
            claim_text = citation.get("text", "")
            
            # Parse Ed Code citations
            ed_patterns = [
                r'(?:Ed\.?\s*Code|Education\s*Code)\s+(\d+(?:\.\d+)?)',
                r'(?:Ed\.?\s*Code|Education\s*Code)\s+[Ss]ections?\s+(\d+(?:\.\d+)?)',
                r'§\s*(\d+(?:\.\d+)?)',
            ]
            
            for pattern in ed_patterns:
                matches = re.findall(pattern, citation_text, re.IGNORECASE)
                for match in matches:
                    citations.append({
                        "section": match,
                        "law_code": "EDC",
                        "claim": claim_text,
                        "source": citation_text
                    })
            
            # Parse other codes
            other_patterns = [
                (r'(?:Gov\.?\s*Code|Government\s*Code)\s+(\d+(?:\.\d+)?)', 'GOV'),
                (r'(?:Lab\.?\s*Code|Labor\s*Code)\s+(\d+(?:\.\d+)?)', 'LAB'),
                (r'(?:Pen\.?\s*Code|Penal\s*Code)\s+(\d+(?:\.\d+)?)', 'PEN'),
                (r'(?:HSC|Health\s*&\s*Safety\s*Code)\s+(\d+(?:\.\d+)?)', 'HSC'),
                (r'(?:PCC|Public\s*Contract\s*Code)\s+(\d+(?:\.\d+)?)', 'PCC'),
                (r'(?:VC|Vehicle\s*Code)\s+(\d+(?:\.\d+)?)', 'VC'),
            ]
            
            for pattern, code in other_patterns:
                matches = re.findall(pattern, citation_text, re.IGNORECASE)
                for match in matches:
                    citations.append({
                        "section": match,
                        "law_code": code,
                        "claim": claim_text,
                        "source": citation_text
                    })
    
    # Also check description text
    desc_text = issue.get("description", "")
    ed_matches = re.findall(r'Ed\.?\s*Code\s+(\d+(?:\.\d+)?)', desc_text, re.IGNORECASE)
    for match in ed_matches:
        citations.append({
            "section": match,
            "law_code": "EDC",
            "claim": desc_text,
            "source": "description"
        })
    
    return citations


def verify_citation(citation, ed_code_cache):
    """Verify if a citation matches the cached code"""
    section = citation["section"]
    law_code = citation["law_code"]
    claim = citation["claim"]
    
    # Try to find in cache
    keys = [f"{law_code}_{section}", section]
    
    cached = None
    for key in keys:
        if key in ed_code_cache:
            cached = ed_code_cache[key]
            break
    
    if not cached:
        return "NOT_CACHED", None
    
    # Compare claim with actual content
    actual_content = cached.get("content", "").lower()
    claim_lower = claim.lower()
    
    # Extract key phrases from claim
    key_phrases = []
    
    # Look for quoted requirements
    quoted = re.findall(r'"([^"]+)"', claim)
    key_phrases.extend(quoted)
    
    # Look for requirement keywords
    req_patterns = [
        r'(shall\s+\w+(?:\s+\w+){0,3})',
        r'(must\s+\w+(?:\s+\w+){0,3})',
        r'(require[sd]?\s+\w+(?:\s+\w+){0,3})',
        r'(at least\s+[\w\s]+)',
    ]
    
    for pattern in req_patterns:
        matches = re.findall(pattern, claim_lower)
        key_phrases.extend(matches)
    
    if not key_phrases:
        # If no specific phrases, check if general topic matches
        if any(word in actual_content for word in claim_lower.split()[:5]):
            return "TOPIC_MATCH", cached
        return "NO_KEY_PHRASES", cached
    
    # Check how many key phrases match
    matches = sum(1 for phrase in key_phrases if phrase.lower() in actual_content)
    match_ratio = matches / len(key_phrases) if key_phrases else 0
    
    if match_ratio >= 0.7:
        return "VERIFIED", cached
    elif match_ratio >= 0.3:
        return "PARTIAL_MATCH", cached
    else:
        return "NOT_VERIFIED", cached


def main():
    """Main validation function"""
    
    print("=" * 80)
    print("V2 COMPLIANCE FINDINGS VALIDATION")
    print("=" * 80)
    
    # Load Ed Code cache
    print("\nLoading Ed Code cache...")
    ed_code_cache, load_errors = load_ed_code_cache()
    print(f"Successfully loaded: {len(ed_code_cache)} sections")
    if load_errors:
        print(f"Errors loading {len(load_errors)} files")
    
    # Load v2 findings
    print("\nLoading v2 compliance findings...")
    findings = load_v2_compliance_findings()
    print(f"Loaded: {len(findings)} policy groups with material issues")
    
    if not findings:
        print("No findings to validate!")
        return
    
    # Process all findings
    all_validations = []
    validation_summary = defaultdict(list)
    
    total_issues = 0
    total_citations = 0
    
    for finding in findings:
        code = finding["code"]
        
        for issue in finding["material_issues"]:
            total_issues += 1
            issue_title = issue.get("title", "")
            
            # Extract citations
            citations = extract_citations_from_issue(issue)
            total_citations += len(citations)
            
            for citation in citations:
                status, cached = verify_citation(citation, ed_code_cache)
                
                validation = {
                    "policy_code": code,
                    "issue_title": issue_title,
                    "section": citation["section"],
                    "law_code": citation["law_code"],
                    "claim": citation["claim"][:200] + "..." if len(citation["claim"]) > 200 else citation["claim"],
                    "status": status,
                    "cached_title": cached.get("title") if cached else None
                }
                
                all_validations.append(validation)
                validation_summary[status].append(validation)
    
    # Print summary
    print(f"\nTotal material issues analyzed: {total_issues}")
    print(f"Total legal citations found: {total_citations}")
    print(f"Total citations validated: {len(all_validations)}")
    
    print("\nValidation Summary:")
    for status in ["VERIFIED", "TOPIC_MATCH", "PARTIAL_MATCH", "NOT_VERIFIED", "NO_KEY_PHRASES", "NOT_CACHED"]:
        count = len(validation_summary[status])
        if count > 0:
            percentage = (count / len(all_validations) * 100) if all_validations else 0
            print(f"  {status}: {count} ({percentage:.1f}%)")
    
    # Show verified citations
    if validation_summary["VERIFIED"]:
        print("\n" + "-" * 80)
        print("VERIFIED CITATIONS (High confidence matches)")
        print("-" * 80)
        for v in validation_summary["VERIFIED"][:10]:
            print(f"\nPolicy {v['policy_code']}: {v['law_code']} {v['section']}")
            print(f"Issue: {v['issue_title']}")
            print(f"Verified: {v['cached_title']}")
    
    # Show problematic citations
    if validation_summary["NOT_VERIFIED"]:
        print("\n" + "-" * 80)
        print("PROBLEMATIC CITATIONS (Claims don't match actual code)")
        print("-" * 80)
        for v in validation_summary["NOT_VERIFIED"][:10]:
            print(f"\nPolicy {v['policy_code']}: {v['law_code']} {v['section']}")
            print(f"Issue: {v['issue_title']}")
            print(f"Claim: \"{v['claim']}\"")
            print(f"Actual: {v['cached_title']}")
    
    # Show what's missing from cache
    if validation_summary["NOT_CACHED"]:
        print("\n" + "-" * 80)
        print("SECTIONS NOT IN CACHE")
        print("-" * 80)
        
        missing_counts = Counter()
        for v in validation_summary["NOT_CACHED"]:
            key = f"{v['law_code']} {v['section']}"
            missing_counts[key] += 1
        
        print("\nMost cited sections not cached:")
        for section, count in missing_counts.most_common(20):
            print(f"  {section}: {count} citations")
    
    # Save results
    output_dir = Path("data/analysis")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "v2_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "generated": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_issues": total_issues,
                "total_citations": total_citations,
                "total_validated": len(all_validations),
                "cached_sections": len(ed_code_cache),
                "validation_counts": {k: len(v) for k, v in validation_summary.items()}
            },
            "validations": all_validations
        }, f, indent=2)
    
    print(f"\n\nDetailed results saved to: {output_file}")
    
    # Generate priority list for fetching
    if validation_summary["NOT_CACHED"]:
        priority_file = output_dir / "priority_sections_to_fetch.txt"
        with open(priority_file, 'w') as f:
            f.write("Priority Ed Code Sections to Fetch\n")
            f.write("=" * 50 + "\n\n")
            
            for section, count in missing_counts.most_common():
                f.write(f"{section}: {count} citations\n")
        
        print(f"Priority fetch list saved to: {priority_file}")


if __name__ == "__main__":
    main()