#!/usr/bin/env python3
"""
Verify v2 compliance findings against cached Ed Code sections
Handles JSON parsing errors gracefully
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone


def load_ed_code_cache():
    """Load all cached Ed Code sections"""
    cache_dir = Path("data/cache/edcode")
    ed_code_cache = {}
    
    if not cache_dir.exists():
        return ed_code_cache
    
    for cache_file in cache_dir.glob("*_full.json"):
        try:
            with open(cache_file) as f:
                data = json.load(f)
                section = data["section"]
                law_code = data.get("law_code", "EDC")
                # Store with both section and law code
                key = f"{law_code}_{section}"
                ed_code_cache[key] = data
                # Also store by section alone for backward compatibility
                ed_code_cache[section] = data
        except json.JSONDecodeError as e:
            print(f"Error parsing {cache_file}: {e}")
        except Exception as e:
            print(f"Error loading {cache_file}: {e}")
    
    return ed_code_cache


def load_v2_findings():
    """Load all v2 compliance findings"""
    v2_dir = Path("data/analysis/compliance_v2/json_data")
    findings = []
    
    if not v2_dir.exists():
        return findings
    
    for json_file in v2_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                if data.get("material_issues"):
                    findings.append({
                        "policy": data["policy_code"],
                        "title": data.get("title", ""),
                        "issues": data["material_issues"],
                        "file": json_file.name
                    })
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return findings


def extract_ed_code_citations(issue_text):
    """Extract Ed Code citations from issue text"""
    citations = []
    
    # Patterns for Ed Code citations
    patterns = [
        r'Ed\.?\s*Code\s+(\d+(?:\.\d+)?)',
        r'Education\s+Code\s+[Ss]ection\s+(\d+(?:\.\d+)?)',
        r'§\s*(\d+(?:\.\d+)?)',
        r'Section\s+(\d+(?:\.\d+)?)\s+of\s+the\s+Education\s+Code',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, issue_text, re.IGNORECASE)
        citations.extend(matches)
    
    # Also check for other code citations
    other_patterns = [
        (r'Gov\.?\s*Code\s+(\d+(?:\.\d+)?)', 'GOV'),
        (r'Lab\.?\s*Code\s+(\d+(?:\.\d+)?)', 'LAB'),
        (r'Pen\.?\s*Code\s+(\d+(?:\.\d+)?)', 'PEN'),
        (r'H&S\s*Code\s+(\d+(?:\.\d+)?)', 'HSC'),
        (r'PCC\s+(\d+(?:\.\d+)?)', 'PCC'),
        (r'Vehicle\s+Code\s+(\d+(?:\.\d+)?)', 'VC'),
    ]
    
    other_citations = []
    for pattern, code in other_patterns:
        matches = re.findall(pattern, issue_text, re.IGNORECASE)
        other_citations.extend([(m, code) for m in matches])
    
    return citations, other_citations


def verify_citation(section, law_code, claim_text, ed_code_cache):
    """Verify if a citation's claim matches the actual code"""
    
    # Try to find the section in cache
    keys_to_try = [
        f"{law_code}_{section}",
        section,
        f"EDC_{section}",
    ]
    
    cached_section = None
    for key in keys_to_try:
        if key in ed_code_cache:
            cached_section = ed_code_cache[key]
            break
    
    if not cached_section:
        return "NOT_CACHED", None
    
    # Extract key phrases from the claim
    key_phrases = []
    
    # Look for quoted text
    quoted = re.findall(r'"([^"]+)"', claim_text)
    key_phrases.extend(quoted)
    
    # Look for key requirement words
    requirement_patterns = [
        r'(shall\s+\w+(?:\s+\w+){0,5})',
        r'(must\s+\w+(?:\s+\w+){0,5})',
        r'(require[sd]?\s+\w+(?:\s+\w+){0,5})',
        r'(at least\s+[\w\s]+)',
        r'(minimum\s+[\w\s]+)',
        r'(annual\w*\s+[\w\s]+)',
    ]
    
    for pattern in requirement_patterns:
        matches = re.findall(pattern, claim_text, re.IGNORECASE)
        key_phrases.extend(matches)
    
    # Check if key phrases appear in the actual code
    actual_content = cached_section.get("content", "").lower()
    
    matches_found = 0
    for phrase in key_phrases:
        if phrase.lower() in actual_content:
            matches_found += 1
    
    if not key_phrases:
        return "NO_KEY_PHRASES", cached_section
    
    match_ratio = matches_found / len(key_phrases)
    
    if match_ratio >= 0.7:
        return "VERIFIED", cached_section
    elif match_ratio >= 0.3:
        return "PARTIAL_MATCH", cached_section
    else:
        return "NOT_VERIFIED", cached_section


def main():
    """Main verification function"""
    
    print("Loading Ed Code cache...")
    ed_code_cache = load_ed_code_cache()
    print(f"Loaded {len(ed_code_cache)} Ed Code sections")
    
    print("\nLoading v2 compliance findings...")
    findings = load_v2_findings()
    print(f"Loaded {len(findings)} policies with material issues")
    
    # Analyze all findings
    all_citations = []
    verification_results = defaultdict(list)
    
    for finding in findings:
        policy = finding["policy"]
        
        for issue in finding["issues"]:
            issue_text = issue.get("issue", "")
            details = issue.get("details", "")
            full_text = f"{issue_text} {details}"
            
            # Extract citations
            ed_citations, other_citations = extract_ed_code_citations(full_text)
            
            # Process Ed Code citations
            for section in ed_citations:
                # Extract any quoted claim
                claim_match = re.search(rf'{section}[^"]*"([^"]+)"', full_text)
                claim = claim_match.group(1) if claim_match else ""
                
                status, cached = verify_citation(section, "EDC", claim, ed_code_cache)
                
                result = {
                    "policy": policy,
                    "issue": issue_text,
                    "section": section,
                    "law_code": "EDC",
                    "claim": claim,
                    "status": status,
                    "cached_title": cached.get("title") if cached else None
                }
                
                verification_results[status].append(result)
                all_citations.append(result)
            
            # Process other code citations
            for section, law_code in other_citations:
                claim_match = re.search(rf'{section}[^"]*"([^"]+)"', full_text)
                claim = claim_match.group(1) if claim_match else ""
                
                status, cached = verify_citation(section, law_code, claim, ed_code_cache)
                
                result = {
                    "policy": policy,
                    "issue": issue_text,
                    "section": section,
                    "law_code": law_code,
                    "claim": claim,
                    "status": status,
                    "cached_title": cached.get("title") if cached else None
                }
                
                verification_results[status].append(result)
                all_citations.append(result)
    
    # Generate report
    print("\n" + "=" * 80)
    print("V2 COMPLIANCE FINDINGS VERIFICATION REPORT")
    print("=" * 80)
    
    print(f"\nTotal citations analyzed: {len(all_citations)}")
    print(f"Unique sections referenced: {len(set(c['section'] for c in all_citations))}")
    
    print("\nVerification Status Summary:")
    for status, results in sorted(verification_results.items()):
        print(f"  {status}: {len(results)}")
    
    # Show verified findings
    if verification_results["VERIFIED"]:
        print("\n" + "-" * 80)
        print("VERIFIED CITATIONS (Claim matches actual code)")
        print("-" * 80)
        for r in verification_results["VERIFIED"][:10]:
            print(f"\n{r['policy']}: {r['law_code']} {r['section']}")
            print(f"  Issue: {r['issue'][:80]}...")
            if r['claim']:
                print(f"  Claim: \"{r['claim'][:100]}...\"")
            print(f"  Actual: {r['cached_title']}")
    
    # Show problematic findings
    if verification_results["NOT_VERIFIED"]:
        print("\n" + "-" * 80)
        print("PROBLEMATIC CITATIONS (Claim does NOT match actual code)")
        print("-" * 80)
        for r in verification_results["NOT_VERIFIED"][:20]:
            print(f"\n{r['policy']}: {r['law_code']} {r['section']}")
            print(f"  Issue: {r['issue'][:80]}...")
            if r['claim']:
                print(f"  Claim: \"{r['claim'][:100]}...\"")
            print(f"  Actual: {r['cached_title']}")
    
    # Show what's not cached
    if verification_results["NOT_CACHED"]:
        print("\n" + "-" * 80)
        print("CITATIONS NOT IN CACHE")
        print("-" * 80)
        
        # Count by section
        section_counts = Counter()
        for r in verification_results["NOT_CACHED"]:
            key = f"{r['law_code']} {r['section']}"
            section_counts[key] += 1
        
        print("\nMost cited sections not in cache:")
        for section, count in section_counts.most_common(20):
            print(f"  {section}: {count} citations")
    
    # Save detailed results
    output_file = Path("data/analysis/v2_verification_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "generated": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_citations": len(all_citations),
                "unique_sections": len(set(c['section'] for c in all_citations)),
                "verification_counts": {k: len(v) for k, v in verification_results.items()},
                "cached_sections": len(ed_code_cache)
            },
            "verification_results": dict(verification_results)
        }, f, indent=2)
    
    print(f"\n\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()