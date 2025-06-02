#!/usr/bin/env python3
"""
Extract Ed Code citations from compliance findings without fetching
"""

import json
import re
from pathlib import Path
from collections import Counter


def extract_citations():
    """Extract all Ed Code citations from compliance findings"""
    
    # Pattern to match Ed Code citations
    citation_pattern = re.compile(
        r'(?:Education Code|Ed\.?\s*Code|Section|§)\s*(\d{4,5}(?:\.\d+)?)',
        re.IGNORECASE
    )
    
    all_citations = []
    citations_by_policy = {}
    
    # Check v2 compliance findings
    json_dir = Path("data/analysis/compliance_v2/json_data")
    
    if not json_dir.exists():
        print(f"Directory {json_dir} not found")
        return
    
    print("Extracting Ed Code citations from compliance_v2 findings...\n")
    
    file_count = 0
    for json_file in sorted(json_dir.glob("*.json")):
        file_count += 1
        
        with open(json_file) as f:
            data = json.load(f)
        
        policy_code = data.get("code", "unknown")
        policy_citations = set()
        
        # Look through compliance issues
        compliance = data.get("compliance", {})
        material_issue_count = 0
        
        for issue in compliance.get("issues", []):
            # Only process material issues
            if issue.get("priority") != "MATERIAL":
                continue
            
            material_issue_count += 1
            
            # Check description
            if desc := issue.get("description"):
                found = citation_pattern.findall(desc)
                policy_citations.update(found)
                all_citations.extend(found)
            
            # Check legal citations
            for legal_cite in issue.get("legal_citations", []):
                if cite_num := legal_cite.get("citation"):
                    # Extract just the number
                    if match := re.search(r'(\d{4,5}(?:\.\d+)?)', cite_num):
                        policy_citations.add(match.group(1))
                        all_citations.append(match.group(1))
                
                if cite_text := legal_cite.get("text"):
                    found = citation_pattern.findall(cite_text)
                    policy_citations.update(found)
                    all_citations.extend(found)
        
        if policy_citations:
            citations_by_policy[policy_code] = {
                "citations": sorted(list(policy_citations)),
                "material_issues": material_issue_count,
                "title": (data.get("policy") or {}).get("title") or (data.get("regulation") or {}).get("title") or "Unknown"
            }
    
    print(f"Processed {file_count} policy files\n")
    
    # Count citation frequency
    citation_counts = Counter(all_citations)
    
    # Generate report
    print("="*80)
    print("ED CODE CITATION ANALYSIS")
    print("="*80)
    print()
    
    print(f"Total policies with material issues: {len(citations_by_policy)}")
    print(f"Total Ed Code citations: {len(all_citations)}")
    print(f"Unique Ed Code sections cited: {len(citation_counts)}")
    print()
    
    print("Top 20 Most Cited Ed Code Sections:")
    print("-"*40)
    for section, count in citation_counts.most_common(20):
        print(f"  Section {section}: {count} times")
    print()
    
    # Save detailed results
    output_file = Path("data/analysis/ed_code_citations_summary.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "summary": {
                "total_policies": len(citations_by_policy),
                "total_citations": len(all_citations),
                "unique_sections": len(citation_counts)
            },
            "most_cited": citation_counts.most_common(50),
            "by_policy": citations_by_policy
        }, f, indent=2)
    
    print(f"Detailed results saved to: {output_file}")
    
    # Create a list of sections to fetch
    sections_file = Path("data/analysis/ed_code_sections_to_fetch.txt")
    with open(sections_file, 'w') as f:
        for section, count in citation_counts.most_common():
            f.write(f"{section}\n")
    
    print(f"List of sections to fetch saved to: {sections_file}")
    
    # Show some problem areas
    print("\nPotential Problem Areas (based on citation patterns):")
    print("-"*60)
    
    # Look for 15278 citations (we know this is wrong for terms)
    if "15278" in citation_counts:
        policies_citing_15278 = [
            code for code, data in citations_by_policy.items()
            if "15278" in data["citations"]
        ]
        print(f"\n⚠️  Section 15278 cited {citation_counts['15278']} times by:")
        for p in policies_citing_15278[:10]:
            print(f"    - {p}: {citations_by_policy[p]['title']}")
        if len(policies_citing_15278) > 10:
            print(f"    ... and {len(policies_citing_15278) - 10} more")


if __name__ == "__main__":
    extract_citations()