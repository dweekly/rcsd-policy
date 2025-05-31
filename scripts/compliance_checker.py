import json
import re
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd


class PolicyComplianceChecker:
    def __init__(self):
        # Key California Ed Code requirements by policy area
        self.ed_code_requirements = {
            # Student policies
            "attendance": {
                "codes": ["46000-46394", "48200-48273"],
                "key_requirements": [
                    "Compulsory attendance ages 6-18",
                    "Truancy definitions and procedures",
                    "Chronic absenteeism tracking",
                    "SARB process requirements",
                ],
            },
            "discipline": {
                "codes": ["48900-48927", "49000-49079"],
                "key_requirements": [
                    "Grounds for suspension/expulsion clearly defined",
                    "Due process procedures",
                    "Alternative means of correction",
                    "Manifestation determination for special education",
                ],
            },
            "bullying": {
                "codes": ["234-234.5", "32261", "48900(r)"],
                "key_requirements": [
                    "Prohibition of discrimination and harassment",
                    "Cyberbullying provisions",
                    "Reporting and investigation procedures",
                    "Annual notification requirements",
                ],
            },
            "special_education": {
                "codes": ["56000-56865"],
                "key_requirements": [
                    "Child find obligations",
                    "IEP process and timelines",
                    "FAPE provisions",
                    "Least restrictive environment",
                ],
            },
            # Personnel policies
            "employment": {
                "codes": ["44830-44986", "45100-45450"],
                "key_requirements": [
                    "Credential requirements",
                    "Background check procedures",
                    "Mandated reporter training",
                    "Professional development requirements",
                ],
            },
            "evaluation": {
                "codes": ["44660-44665"],
                "key_requirements": [
                    "Evaluation criteria and procedures",
                    "Timeline requirements",
                    "Improvement plans",
                    "Due process rights",
                ],
            },
            # Governance policies
            "board_governance": {
                "codes": ["35000-35179"],
                "key_requirements": [
                    "Board meeting procedures",
                    "Brown Act compliance",
                    "Conflict of interest",
                    "Board member training requirements",
                ],
            },
            "fiscal": {
                "codes": ["41000-42650"],
                "key_requirements": [
                    "Budget adoption procedures",
                    "Fiscal accountability",
                    "Audit requirements",
                    "Reserve requirements",
                ],
            },
            # Health and safety
            "wellness": {
                "codes": ["49430-49436"],
                "key_requirements": [
                    "Wellness policy requirements",
                    "Nutrition standards",
                    "Physical education requirements",
                    "Health education mandates",
                ],
            },
            "safety": {
                "codes": ["32280-32289"],
                "key_requirements": [
                    "Comprehensive safety plan",
                    "Emergency procedures",
                    "Annual review and update",
                    "Stakeholder involvement",
                ],
            },
        }

        # CSBA best practices indicators
        self.csba_best_practices = {
            "policy_structure": [
                "Clear purpose statement",
                "Legal references cited",
                "Cross-references to related policies",
                "Implementation procedures defined",
            ],
            "equity_focus": [
                "Equity considerations addressed",
                "Disparate impact analysis",
                "Inclusive language",
                "Cultural responsiveness",
            ],
            "stakeholder_engagement": [
                "Parent/community input processes",
                "Student voice incorporated",
                "Staff consultation procedures",
                "Communication plans",
            ],
            "accountability": [
                "Monitoring procedures",
                "Data collection requirements",
                "Reporting timelines",
                "Review cycles specified",
            ],
        }

        # Material non-compliance indicators
        self.material_noncompliance_indicators = [
            "Missing required legal provisions",
            "Outdated legal references (pre-2020)",
            "Conflicts with current Ed Code",
            "Missing mandated procedures",
            "Discriminatory language or provisions",
            "Lack of due process protections",
            "Missing required notifications",
            "Absence of required timelines",
        ]

    def identify_policy_category(
        self, policy_title: str, policy_content: str
    ) -> List[str]:
        """Identify which Ed Code categories apply to this policy"""
        categories = []
        title_lower = policy_title.lower()
        content_lower = policy_content.lower()

        # Check for category keywords
        category_keywords = {
            "attendance": ["attendance", "truancy", "absent", "tardy"],
            "discipline": ["discipline", "suspension", "expulsion", "behavior"],
            "bullying": ["bullying", "harassment", "discrimination", "hazing"],
            "special_education": ["special education", "iep", "idea", "disability"],
            "employment": ["employment", "hiring", "personnel", "staff"],
            "evaluation": ["evaluation", "assessment", "performance review"],
            "board_governance": ["board", "governance", "meeting", "trustee"],
            "fiscal": ["budget", "fiscal", "financial", "audit"],
            "wellness": ["wellness", "nutrition", "health", "physical education"],
            "safety": ["safety", "emergency", "crisis", "security"],
        }

        for category, keywords in category_keywords.items():
            if any(
                keyword in title_lower or keyword in content_lower
                for keyword in keywords
            ):
                categories.append(category)

        return categories

    def check_ed_code_compliance(
        self, policy_content: str, categories: List[str]
    ) -> Dict:
        """Check compliance with Ed Code requirements"""
        compliance_issues = []
        applicable_codes = []

        for category in categories:
            if category in self.ed_code_requirements:
                cat_requirements = self.ed_code_requirements[category]
                applicable_codes.extend(cat_requirements["codes"])

                # Check for key requirements
                for requirement in cat_requirements["key_requirements"]:
                    # Simple keyword-based check (would be more sophisticated in production)
                    req_keywords = requirement.lower().split()
                    if not any(
                        keyword in policy_content.lower()
                        for keyword in req_keywords[:3]
                    ):
                        compliance_issues.append(
                            {
                                "category": category,
                                "requirement": requirement,
                                "severity": "potential_issue",
                            }
                        )

        # Check for outdated references
        old_code_pattern = r"(Education Code|Ed\.? Code|EC).*?(20[0-1]\d|199\d)"
        old_refs = re.findall(old_code_pattern, policy_content)
        if old_refs:
            compliance_issues.append(
                {
                    "category": "general",
                    "requirement": "Updated legal references",
                    "severity": "material",
                    "details": f"Found outdated references: {old_refs}",
                }
            )

        # Check for missing legal references
        if not re.search(r"(Education Code|Ed\.? Code|EC)", policy_content):
            compliance_issues.append(
                {
                    "category": "general",
                    "requirement": "Legal references",
                    "severity": "material",
                    "details": "No Education Code references found",
                }
            )

        return {
            "applicable_codes": applicable_codes,
            "compliance_issues": compliance_issues,
        }

    def check_csba_best_practices(self, policy_content: str) -> Dict:
        """Check alignment with CSBA best practices"""
        best_practice_gaps = []

        # Check policy structure
        if not re.search(r"(Purpose|Intent|Philosophy)", policy_content, re.IGNORECASE):
            best_practice_gaps.append(
                {"area": "policy_structure", "gap": "Missing clear purpose statement"}
            )

        if not re.search(
            r"(Legal Reference|Legal|Ref\.?:|Authority)", policy_content, re.IGNORECASE
        ):
            best_practice_gaps.append(
                {"area": "policy_structure", "gap": "Missing legal references section"}
            )

        # Check for equity considerations
        equity_keywords = [
            "equity",
            "equitable",
            "inclusive",
            "all students",
            "regardless of",
        ]
        if not any(keyword in policy_content.lower() for keyword in equity_keywords):
            best_practice_gaps.append(
                {
                    "area": "equity_focus",
                    "gap": "Limited equity language or considerations",
                }
            )

        # Check for monitoring/accountability
        monitoring_keywords = [
            "monitor",
            "review",
            "evaluate",
            "report",
            "data",
            "measure",
        ]
        if not any(
            keyword in policy_content.lower() for keyword in monitoring_keywords
        ):
            best_practice_gaps.append(
                {
                    "area": "accountability",
                    "gap": "Missing monitoring or evaluation procedures",
                }
            )

        return {"best_practice_gaps": best_practice_gaps}

    def determine_material_noncompliance(
        self, compliance_issues: List[Dict], best_practice_gaps: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """Determine if issues constitute material non-compliance"""
        material_issues = []

        # Check compliance issues
        for issue in compliance_issues:
            if issue["severity"] == "material":
                material_issues.append(
                    f"Ed Code: {issue['requirement']} - {issue.get('details', '')}"
                )

        # Material non-compliance if:
        # 1. Any material severity issues
        # 2. Multiple potential issues in same category
        # 3. Missing multiple key requirements

        category_issues = {}
        for issue in compliance_issues:
            cat = issue["category"]
            if cat not in category_issues:
                category_issues[cat] = 0
            category_issues[cat] += 1

        for cat, count in category_issues.items():
            if count >= 3:
                material_issues.append(
                    f"Multiple compliance gaps in {cat} requirements"
                )

        is_material = len(material_issues) > 0

        return is_material, material_issues

    def analyze_policy(self, policy: Dict) -> Dict:
        """Analyze a single policy for compliance"""
        policy_title = policy.get("title", "")
        policy_content = policy.get("content", "")
        policy_code = policy.get("code", "")

        # Identify applicable categories
        categories = self.identify_policy_category(policy_title, policy_content)

        # Check Ed Code compliance
        ed_code_results = self.check_ed_code_compliance(policy_content, categories)

        # Check CSBA best practices
        csba_results = self.check_csba_best_practices(policy_content)

        # Determine material non-compliance
        is_material, material_issues = self.determine_material_noncompliance(
            ed_code_results["compliance_issues"], csba_results["best_practice_gaps"]
        )

        return {
            "policy_code": policy_code,
            "policy_title": policy_title,
            "categories": categories,
            "ed_code_compliance": ed_code_results,
            "csba_alignment": csba_results,
            "material_noncompliance": is_material,
            "material_issues": material_issues,
            "analysis_date": datetime.now().isoformat(),
        }

    def analyze_all_policies(
        self, policies_file: str = "rcsd_policies.json"
    ) -> List[Dict]:
        """Analyze all policies from scraped data"""
        try:
            with open(policies_file, encoding="utf-8") as f:
                policies = json.load(f)
        except FileNotFoundError:
            print(f"Policies file {policies_file} not found")
            return []

        results = []
        material_noncompliance_policies = []

        print(f"Analyzing {len(policies)} policies for compliance...")

        for i, policy in enumerate(policies):
            print(
                f"Analyzing policy {i + 1}/{len(policies)}: {policy.get('title', 'Unknown')}"
            )

            analysis = self.analyze_policy(policy)
            results.append(analysis)

            if analysis["material_noncompliance"]:
                material_noncompliance_policies.append(analysis)

        print(
            f"\nAnalysis complete. Found {len(material_noncompliance_policies)} policies with material non-compliance issues."
        )

        return results, material_noncompliance_policies

    def generate_compliance_report(
        self,
        results: List[Dict],
        material_issues: List[Dict],
        output_file: str = "compliance_report.json",
    ):
        """Generate compliance report"""
        report = {
            "report_date": datetime.now().isoformat(),
            "total_policies_analyzed": len(results),
            "material_noncompliance_count": len(material_issues),
            "summary": {
                "policies_by_category": {},
                "common_issues": {},
                "material_noncompliance_policies": [],
            },
            "detailed_results": results,
            "material_noncompliance_details": material_issues,
        }

        # Summarize by category
        for result in results:
            for cat in result["categories"]:
                if cat not in report["summary"]["policies_by_category"]:
                    report["summary"]["policies_by_category"][cat] = 0
                report["summary"]["policies_by_category"][cat] += 1

        # List material non-compliance policies
        for issue in material_issues:
            report["summary"]["material_noncompliance_policies"].append(
                {
                    "code": issue["policy_code"],
                    "title": issue["policy_title"],
                    "issues": issue["material_issues"],
                }
            )

        # Save report
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Also create Excel summary
        self.create_excel_summary(material_issues)

        return report

    def create_excel_summary(
        self,
        material_issues: List[Dict],
        filename: str = "material_noncompliance_summary.xlsx",
    ):
        """Create Excel summary of material non-compliance issues"""
        if not material_issues:
            print("No material non-compliance issues to report")
            return

        # Prepare data for Excel
        summary_data = []
        for issue in material_issues:
            for material_issue in issue["material_issues"]:
                summary_data.append(
                    {
                        "Policy Code": issue["policy_code"],
                        "Policy Title": issue["policy_title"],
                        "Issue": material_issue,
                        "Categories": ", ".join(issue["categories"]),
                    }
                )

        df = pd.DataFrame(summary_data)
        df.to_excel(filename, index=False)
        print(f"Created Excel summary: {filename}")


if __name__ == "__main__":
    checker = PolicyComplianceChecker()
    results, material_issues = checker.analyze_all_policies()

    if results:
        report = checker.generate_compliance_report(results, material_issues)
        print("\nCompliance report generated: compliance_report.json")
        print("Material non-compliance summary: material_noncompliance_summary.xlsx")
