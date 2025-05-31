#!/usr/bin/env python3
"""
Batch compliance checking for all RCSD policies with structured output
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from compliance_check_structured import (
    check_compliance_structured,
    generate_update_report,
    parse_compliance_report,
    parse_policy_to_xml,
)


def calculate_policy_priority(code, title, last_reviewed):
    """Calculate priority score for a policy (higher = more urgent)"""
    priority = 0

    # Age factor (most important)
    if last_reviewed and last_reviewed != "Unknown":
        try:
            review_date = datetime.strptime(last_reviewed, "%m/%d/%Y")
            age_years = (datetime.now() - review_date).days / 365.25
            priority += age_years * 5  # 5 points per year
        except:
            priority += 25  # Unknown date = assume old
    else:
        priority += 25

    # Series factor (4000/5000 series are personnel/student policies - high priority)
    try:
        series = int(code) // 1000 * 1000
        if series in [4000, 5000]:
            priority += 20
        elif series in [3000, 6000]:  # Business/instruction
            priority += 15
        elif series in [1000, 2000]:  # Community/administration
            priority += 10
    except:
        pass

    # Specific high-risk areas
    high_risk_keywords = [
        "nutrition",
        "meal",
        "wellness",
        "discrimination",
        "harassment",
        "bullying",
        "safety",
        "Title IX",
        "special education",
        "discipline",
    ]
    if any(keyword in title.lower() for keyword in high_risk_keywords):
        priority += 15

    return priority


def get_policies_to_check(base_dir="extracted_policies_all"):
    """Get all policies sorted by priority"""
    policies = []

    for subdir in ["policies", "regulations"]:
        dir_path = os.path.join(base_dir, subdir)
        if not os.path.exists(dir_path):
            continue

        for file in os.listdir(dir_path):
            if not file.endswith(".txt"):
                continue

            file_path = os.path.join(dir_path, file)

            # Quick parse to get metadata
            try:
                with open(file_path) as f:
                    content = f.read(1000)  # Just read header

                # Extract code
                code = file.replace(".txt", "")

                # Extract title
                title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", content)
                title = title_match.group(1) if title_match else "Unknown"

                # Extract last reviewed date
                reviewed_match = re.search(
                    r"Last Reviewed Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})", content
                )
                last_reviewed = reviewed_match.group(1) if reviewed_match else None

                # Skip recently updated policies (2024 or later)
                if last_reviewed:
                    try:
                        review_date = datetime.strptime(last_reviewed, "%m/%d/%Y")
                        if review_date.year >= 2024:
                            print(
                                f"Skipping {code} - Recently updated ({last_reviewed})"
                            )
                            continue
                    except:
                        pass

                priority = calculate_policy_priority(code, title, last_reviewed)

                policies.append(
                    {
                        "file_path": file_path,
                        "code": code,
                        "title": title,
                        "last_reviewed": last_reviewed,
                        "priority": priority,
                        "type": subdir[:-1].capitalize(),  # 'Policy' or 'Regulation'
                    }
                )

            except Exception as e:
                print(f"Error processing {file}: {e}")

    # Sort by priority (highest first)
    policies.sort(key=lambda x: x["priority"], reverse=True)

    return policies


def batch_check_compliance(max_policies=None, output_dir="compliance_reports"):
    """Run compliance checks on multiple policies"""

    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)

    # Get prioritized list of policies
    policies = get_policies_to_check()

    if max_policies:
        policies = policies[:max_policies]

    print(f"\nFound {len(policies)} policies to check")
    print("Top 10 by priority:")
    for p in policies[:10]:
        age = "Unknown"
        if p["last_reviewed"] and p["last_reviewed"] != "Unknown":
            try:
                review_date = datetime.strptime(p["last_reviewed"], "%m/%d/%Y")
                age = f"{(datetime.now() - review_date).days / 365.25:.1f} years"
            except:
                pass
        print(
            f"  {p['code']}: {p['title']} (Last reviewed: {p['last_reviewed']} - {age} ago, Priority: {p['priority']:.1f})"
        )

    print(f"\nProcessing {len(policies)} policies...")

    results = []
    material_issues_count = 0

    for idx, policy in enumerate(policies):
        print(
            f"\n[{idx + 1}/{len(policies)}] Processing {policy['code']} - {policy['title']}"
        )

        try:
            # Parse policy
            policy_xml, code, title, last_reviewed = parse_policy_to_xml(
                policy["file_path"]
            )

            # Check compliance
            xml_response = check_compliance_structured(
                policy_xml, code, title, last_reviewed
            )

            # Parse response
            report_data = parse_compliance_report(xml_response)

            # Count material issues
            material_issues = [
                i
                for i in report_data.get("issues", [])
                if i.get("priority") == "MATERIAL"
            ]
            material_issues_count += len(material_issues)

            # Save individual report
            report_file = os.path.join(output_dir, f"{code}_report.json")
            with open(report_file, "w") as f:
                json.dump(
                    {
                        "policy": policy,
                        "report": report_data,
                        "checked_date": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            # Generate human-readable report
            text_report = generate_update_report(code, title, report_data)
            text_file = os.path.join(output_dir, f"{code}_report.txt")
            with open(text_file, "w") as f:
                f.write(text_report)

            results.append(
                {
                    "code": code,
                    "title": title,
                    "last_reviewed": last_reviewed,
                    "material_issues": len(material_issues),
                    "total_issues": len(report_data.get("issues", [])),
                    "report_file": report_file,
                }
            )

            print(f"  Found {len(material_issues)} material issues")

            # Rate limiting
            time.sleep(2)  # Be nice to the API

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append(
                {"code": policy["code"], "title": policy["title"], "error": str(e)}
            )

    # Generate summary report
    summary = {
        "run_date": datetime.now().isoformat(),
        "policies_checked": len(policies),
        "total_material_issues": material_issues_count,
        "results": results,
    }

    summary_file = os.path.join(output_dir, "compliance_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Generate executive summary
    exec_summary = f"""
RCSD Policy Compliance Check - Executive Summary
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Policies Analyzed: {len(policies)}
Total Material Issues Found: {material_issues_count}

Top Issues by Policy:
"""

    # Sort by number of material issues
    results_with_issues = [r for r in results if r.get("material_issues", 0) > 0]
    results_with_issues.sort(key=lambda x: x.get("material_issues", 0), reverse=True)

    for r in results_with_issues[:20]:
        exec_summary += f"\n{r['code']} - {r['title']}"
        exec_summary += f"\n  Last reviewed: {r.get('last_reviewed', 'Unknown')}"
        exec_summary += f"\n  Material issues: {r['material_issues']}"
        exec_summary += "\n"

    exec_file = os.path.join(output_dir, "executive_summary.txt")
    with open(exec_file, "w") as f:
        f.write(exec_summary)

    print("\n\nCompliance check complete!")
    print(f"Reports saved to: {output_dir}/")
    print(f"Summary saved to: {summary_file}")
    print(f"Executive summary: {exec_file}")

    return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Batch compliance checking for RCSD policies"
    )
    parser.add_argument("--max", type=int, help="Maximum number of policies to check")
    parser.add_argument(
        "--output", default="compliance_reports", help="Output directory"
    )

    args = parser.parse_args()

    batch_check_compliance(max_policies=args.max, output_dir=args.output)


if __name__ == "__main__":
    main()
