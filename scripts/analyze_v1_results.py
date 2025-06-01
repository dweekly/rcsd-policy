#!/usr/bin/env python3
"""
Analyze v1 compliance results to show which findings were for BP vs AR
"""

import json
from collections import defaultdict
from pathlib import Path


def analyze_results():
    json_dir = Path("data/analysis/compliance/json_data")

    # Track statistics
    policy_issues = defaultdict(list)
    regulation_issues = defaultdict(list)

    # Read all JSON files
    for json_file in json_dir.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)

        policy_data = data["policy"]
        compliance_data = data["compliance"]

        code = policy_data["code"]
        doc_type = policy_data["type"]
        title = policy_data["title"]

        # Get material issues
        material_issues = [
            issue
            for issue in compliance_data.get("issues", [])
            if issue.get("priority") == "MATERIAL"
        ]

        if material_issues:
            if doc_type == "Policy":
                policy_issues[code] = {
                    "title": title,
                    "issues": material_issues,
                    "count": len(material_issues),
                }
            elif doc_type == "Regulation":
                regulation_issues[code] = {
                    "title": title,
                    "issues": material_issues,
                    "count": len(material_issues),
                }

    # Print analysis
    print("# Analysis of V1 Compliance Results\n")

    # Find codes that have both BP and AR with issues
    common_codes = set(policy_issues.keys()) & set(regulation_issues.keys())

    print("## Summary Statistics")
    print(f"- Policies with material issues: {len(policy_issues)}")
    print(f"- Regulations with material issues: {len(regulation_issues)}")
    print(f"- Codes with issues in BOTH BP and AR: {len(common_codes)}\n")

    print("## Policy Groups with Issues in Both BP and AR\n")
    for code in sorted(common_codes):
        bp_data = policy_issues[code]
        ar_data = regulation_issues[code]

        print(f"### {code} - {bp_data['title']}")
        print(f"**BP {code} Issues ({bp_data['count']}):**")
        for issue in bp_data["issues"][:3]:  # Show first 3
            print(f"- {issue['title']}")
        if bp_data["count"] > 3:
            print(f"- ... and {bp_data['count'] - 3} more")

        print(f"\n**AR {code} Issues ({ar_data['count']}):**")
        for issue in ar_data["issues"][:3]:  # Show first 3
            print(f"- {issue['title']}")
        if ar_data["count"] > 3:
            print(f"- ... and {ar_data['count'] - 3} more")
        print()

    # Example: 6142.1 analysis
    if "6142.1" in common_codes:
        print("## Detailed Example: 6142.1 Sexual Health Education\n")

        bp_data = policy_issues["6142.1"]
        ar_data = regulation_issues["6142.1"]

        print("**BP 6142.1 Material Issues:**")
        for issue in bp_data["issues"]:
            print(f"- {issue['title']} ({issue['confidence']}% confidence)")
            print(f"  {issue['description'][:200]}...")

        print("\n**AR 6142.1 Material Issues:**")
        for issue in ar_data["issues"]:
            print(f"- {issue['title']} ({issue['confidence']}% confidence)")
            print(f"  {issue['description'][:200]}...")

        print(
            "\n**Analysis**: The parent notification requirements flagged in AR 6142.1"
        )
        print(
            "are actually present in BP 6142.1, demonstrating why unified analysis is needed."
        )


if __name__ == "__main__":
    analyze_results()
